import re
import argparse
from utils.data_loader import load_data
from tools.product_tools import search_products, get_product
from tools.order_tools import get_order
from tools.return_tools import evaluate_return
from agent.agent import run_agent

# LOAD DATA
products, orders, policy = load_data()

# TOOL EXECUTION LAYER
def execute_tool(name, args):

    if name == "search_products":
        return search_products(
            products,
            max_price=args.get("max_price"),
            size=args.get("size"),
            on_sale=args.get("on_sale"),
            tag=args.get("tag")
        )

    elif name == "get_product":
        return get_product(products, args.get("product_id"))

    elif name == "get_order":
        return get_order(orders, args.get("order_id"))

    elif name == "evaluate_return":
        return evaluate_return(
            args.get("order_id"),
            orders,
            products,
            policy
        )

    return None


# EXTRACTION HELPERS
def extract_order_id(text):
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None


def extract_price(text):
    m = re.search(r"\$?(\d+)", text)
    return int(m.group(1)) if m else 300


def extract_size(text):
    m = re.search(r"size\s*(\d+|[SML])", text, re.IGNORECASE)
    return m.group(1) if m else None


# FALLBACK LOGIC
def fallback_logic(query):

    q = query.lower()

    # SUPPORT 
    if "order" in q:
        order_id = extract_order_id(query)

        if not order_id:
            return "Please provide a valid order ID."

        result = execute_tool("evaluate_return", {"order_id": order_id})

        if result is None:
            return "Order not found. Please check the order ID."

        return f"""
Return Decision:

Eligible: {"Yes" if result.get("eligible") else "No"}

Reason:
{result.get("reason")}
"""

    # SHOPPER 
    else:
        max_price = extract_price(query)
        size = extract_size(query)

        products_list = execute_tool("search_products", {
            "max_price": max_price,
            "size": size
        })

        if not products_list:
            return "No products found matching your criteria."

        # STEP 1: Check stock availability
        in_stock = [
            p for p in products_list
            if p.get("stock_per_size", {}).get(str(size), 0) > 0
        ]

        if not in_stock:
            return f"No products available in stock for size {size}."

        # STEP 2: Prioritize sale items
        sale_items = [p for p in in_stock if p.get("is_sale")]

        candidates = sale_items if sale_items else in_stock

        # STEP 3: Rank by bestseller_score
        candidates = sorted(
            candidates,
            key=lambda x: x.get("bestseller_score", 0),
            reverse=True
        )

        top = candidates[0]

        return f"""
Recommended Product:

{top['title']}
Price: ${top['price']}

Why this fits your request:
- Under your budget (${max_price})
- Available in size {size} and currently in stock
- {"On sale (prioritized)" if top.get("is_sale") else "Best available option"}
- High popularity (bestseller score: {top.get("bestseller_score")})
- Matches your requested style constraints
"""


# SAFE AGENT WRAPPER
def safe_run_agent(user_input):
    try:
        return run_agent(user_input, execute_tool)
    except Exception:
        print("\n[LLM unavailable → using fallback logic]\n")
        return fallback_logic(user_input)


# MAIN AGENT LOOP
def main():

    print("\n" + "="*70)
    print("  RETAIL AI ASSISTANT - Intelligent Agent")
    print("="*70)

    print("\nYou can ask anything:\n")
    print("Examples:")
    print("- I need a modest gown under $300 in size 6")
    print("- Show me casual items on sale")
    print("- Can I return order 1043?")
    print("\nType 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("\nGoodbye!\n")
            break

        if not user_input:
            continue

        print("\nAssistant: Processing...\n")
        response = safe_run_agent(user_input)
        print(response)
        print("\n" + "-"*70 + "\n")

if __name__ == "__main__":
    main()