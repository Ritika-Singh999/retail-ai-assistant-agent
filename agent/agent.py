import google.generativeai as genai
from config.settings import GEMINI_API_KEY
from agent.prompts import (
    SYSTEM_PROMPT,
    FINAL_RESPONSE_PROMPT,
    SEARCH_PRODUCTS_GUIDE,
    CONTENT_SCHEMA
)
import json
import re


def parse_shopper_query(text: str):
    
    lower = text.lower()
    args = {}

    m = re.search(r'under\s*\$?(\d+)', text, re.IGNORECASE) or re.search(r'below\s*\$?(\d+)', text, re.IGNORECASE)
    if m:
        try:
            args["max_price"] = int(m.group(1))
        except Exception:
            pass

    m = re.search(r'size\s*(?:is\s*)?(\d+)', text, re.IGNORECASE)
    if m:
        args["size"] = m.group(1)

    if re.search(r'\b(sale|on sale|discount|discounted)\b', lower):
        args["on_sale"] = True

    for tag in ("modest", "evening", "formal", "cocktail", "prom", "bridal"):
        if tag in lower:
            args["tag"] = tag
            break

    if not args:
        return None

    return {"tool": "search_products", "args": args}


genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "models/gemini-1.5-flash"

ALLOWED_TOOLS = {
    "search_products",
    "get_product",
    "get_order",
    "evaluate_return"
}

def clean_json(text):
    if "```" in text:
        parts = text.split("```")
        # get the JSON part
        for part in parts:
            part = part.strip()
            if part.startswith("{") and part.endswith("}"):
                return part
    return text.strip()

def validate_tool_choice(choice: dict) -> bool:
    if not isinstance(choice, dict):
        return False

    if choice.get("tool") not in ALLOWED_TOOLS:
        return False

    if not isinstance(choice.get("args", {}), dict):
        return False

    return True


def validate_tool_output(tool_name: str, result) -> bool:

    if tool_name == "search_products":
        if not isinstance(result, list):
            return False
        for item in result:
            if not isinstance(item, dict):
                return False
            for k in [
                "product_id",
                "title",
                "price",
                "vendor",
                "is_sale",
                "bestseller_score",
                "sizes_available",
                "stock_per_size"
            ]:
                if k not in item:
                    return False
        return True

    elif tool_name == "get_product":
        return isinstance(result, dict) and all(
            k in result for k in ["product_id", "title", "price"]
        )

    elif tool_name == "get_order":
        return isinstance(result, dict) and all(
            k in ["order_id", "order_date", "product_id", "size", "price_paid"]
            for k in result
        )

    elif tool_name == "evaluate_return":
        if not isinstance(result, dict):
            return False
        required = ["eligible", "outcome", "reason", "explanation", "evidence"]
        return all(k in result for k in required) and isinstance(result["evidence"], dict)

    return False

# MAIN AGENT FUNCTION
def run_agent(user_input, execute_tool):

    m = re.search(r"order\s*(?:#|:)?\s*(O?\d+)", user_input, re.IGNORECASE)
    if m and any(k in user_input.lower() for k in ("return", "refund", "exchange", "returnable", "can i return")):
        order_id = m.group(1)
        try:
            result = execute_tool("evaluate_return", {"order_id": order_id})
        except Exception:
            return "There was an error processing the return request."

        if result is None:
            return "Order not found. Please check the order ID."

        if not validate_tool_output("evaluate_return", result):
            return "Unexpected data format from system."

        if result.get("eligible"):
            return f"Yes — {result.get('explanation')}\nEvidence: {json.dumps(result.get('evidence'), default=str)}"
        else:
            return f"No — {result.get('explanation')}\nEvidence: {json.dumps(result.get('evidence'), default=str)}"

    model = genai.GenerativeModel(MODEL_NAME)

    # STEP 1: TOOL SELECTION
    tool_prompt = (
        SYSTEM_PROMPT
        + "\n\n"
        + SEARCH_PRODUCTS_GUIDE
        + f"\n\nUser query: {user_input}\n\nReturn JSON only."
    )

    selection = None
    choice = None

    for _ in range(2):
        try:
            selection = model.generate_content(tool_prompt)
            text = clean_json(selection.text)
            choice = json.loads(text)
            break
        except Exception:
            continue

    if choice is None:
        try:
            fallback = parse_shopper_query(user_input)
            if fallback:
                choice = fallback
        except Exception:
            choice = None

    if choice is None:
        return "I couldn’t understand your request. Please try again."

    if not validate_tool_choice(choice):
        return "Invalid request format. Please try again."

    tool_name = choice["tool"]
    args = choice.get("args", {})


    # STEP 2: TOOL EXECUTION
    try:
        result = execute_tool(tool_name, args)
    except Exception:
        return "There was an error processing your request."

    if result is None or (isinstance(result, list) and len(result) == 0):
        if tool_name in ("get_order", "evaluate_return"):
            return "Order not found. Please check the order ID."
        elif tool_name == "get_product":
            return "That product does not exist."
        else:
            return "No products matched your request."

    if not validate_tool_output(tool_name, result):
        return "Unexpected data format from system."

    # STEP 3: FINAL RESPONSE
    try:
        final_prompt = (
            CONTENT_SCHEMA
            + "\n\n"
            + FINAL_RESPONSE_PROMPT.format(
                user_query=user_input,
                tool_name=tool_name,
                tool_result=json.dumps(result, indent=2, default=str),
            )
        )

        response = model.generate_content(final_prompt)
        return response.text.strip()

    except Exception:
        
        try:
            return deterministic_final_response(user_input, tool_name, args, result)
        except Exception:
            return "Error generating response."


def deterministic_final_response(user_query, tool_name, args, result):
        
    if tool_name == "search_products":
        candidates = result if isinstance(result, list) else []

        size = args.get("size") if isinstance(args, dict) else None
        max_price = args.get("max_price") if isinstance(args, dict) else None

        filtered = []
        for p in candidates:
            if max_price is not None and p.get("price") is not None:
                try:
                    if float(p.get("price")) > float(max_price):
                        continue
                except Exception:
                    pass

            if size:
                sizes = [s.strip() for s in str(p.get("sizes_available", "")).split("|") if s]
                if str(size) not in sizes:
                    continue
                stock = p.get("stock_per_size", {}) or {}
                if int(stock.get(str(size), 0)) <= 0:
                    continue

            filtered.append(p)

        if not filtered:
            body = "No products found matching your criteria."
            agent_work = f"Agent Work:\n- Tool used: {tool_name}\n- Tool result: {json.dumps(result, default=str)}"
            model_role = "Model Role:\n- I used the tool result to produce this message without calling the LLM."
            return f"{body}\n\n{agent_work}\n\n{model_role}"

        def score(p):
            return (1 if p.get("is_sale") else 0, p.get("bestseller_score") or 0)

        best = sorted(filtered, key=lambda x: (not x.get("is_sale"), -(x.get("bestseller_score") or 0)))[0]

        expl_lines = []
        expl_lines.append(f"Recommended product — {best.get('title')} ({best.get('product_id')})")
        expl_lines.append("\nWhy this fits:")
        if max_price is not None:
            expl_lines.append(f"- Price: {best.get('price')} (below ${max_price}).")
        else:
            expl_lines.append(f"- Price: {best.get('price')}.")
        if size:
            expl_lines.append(f"- Size availability: {best.get('sizes_available')} (requested size {size}).")
            expl_lines.append(f"- Stock for requested size: {best.get('stock_per_size', {}).get(str(size), 0)}.")
        else:
            expl_lines.append(f"- Sizes available: {best.get('sizes_available')}")
        expl_lines.append(f"- Sale status: {best.get('is_sale')}")
        expl_lines.append(f"- Popularity score: {best.get('bestseller_score')}")

        agent_work = f"Agent Work:\n- Tool used: {tool_name}\n- Fields used: {json.dumps({'product_id': best.get('product_id'), 'price': best.get('price'), 'sizes_available': best.get('sizes_available'), 'stock_per_size': best.get('stock_per_size'), 'is_sale': best.get('is_sale'), 'bestseller_score': best.get('bestseller_score')}, default=str)}"
        model_role = "Model Role:\n- I selected `search_products` to fetch product inventory and used the returned fields to generate this recommendation without invoking the LLM."

        return "\n".join(expl_lines) + "\n\n" + agent_work + "\n\n" + model_role

    if tool_name == "get_product":
        p = result if isinstance(result, dict) else {}
        body = f"Product details: {p.get('title')} ({p.get('product_id')}), price {p.get('price')}"
        agent_work = f"Agent Work:\n- Tool used: get_product\n- Tool result: {json.dumps(p, default=str)}"
        model_role = "Model Role:\n- I used the tool result to produce this message without calling the LLM."
        return f"{body}\n\n{agent_work}\n\n{model_role}"

    return ""