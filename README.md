# Retail AI Assistant

## Overview
Retail AI Assistant is a simulation-based, tool-driven AI system that models two real-world roles:

- **Personal Shopper (Revenue Agent)**
- **Customer Support Assistant (Operations Agent)**

The system operates entirely on structured local data (CSV files and policy text) and is designed with a strict **no-hallucination architecture**.

No external store integration is used.

---

## Objective

Build a single intelligent agent that can:

- Recommend products using multiple constraints  
- Reason about return eligibility using policies  
- Dynamically select tools based on user intent  
- Avoid hallucination by relying only on structured data  

---

## Quick Start

### 1. Create and activate virtual environment
```powershell
python -m venv venv
& venv\Scripts\Activate.ps1
````

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run the assistant

```powershell
python main.py
```

---

## Data Sources

### Product Inventory (products.csv)

* product_id
* title
* vendor
* price
* compare_at_price
* tags (modest, casual, evening, etc.)
* sizes_available
* stock_per_size
* is_sale
* is_clearance
* bestseller_score

### Orders (orders.csv)

* order_id
* order_date
* product_id
* size
* price_paid
* customer_id

### Policy (policy.txt)

* return window
* sale item rules
* clearance rules
* vendor exceptions
* exchange rules

These files act as the **single source of truth**.

---

## Tools

The agent dynamically selects and executes structured tools:

* `search_products(filters)`
* `get_product(product_id)`
* `get_order(order_id)`
* `evaluate_return(order_id)`

Hardcoded responses are not used. All outputs are derived from tool results.

---

## Data Flow

```
User Input → main.py → agent.py (Tool Selection)
→ Tool Call → execute_tool()
→ tools/ → CSV Data → Structured Output
→ agent.py (Reasoning) → Final Response
```

---

## Agent Behavior

### Personal Shopper

Example:
"I need a modest evening gown under $300 in size 8 on sale"

The agent:

* Filters by price, size, and tags
* Checks stock availability for the requested size
* Prioritizes sale items
* Considers bestseller_score
* Explains why the recommendation fits

Focus:

* Multi-constraint reasoning
* Business awareness
* Stock awareness

---

### Customer Support Assistant

Example:
"Can I return order 1043?"

The agent:

* Retrieves the order
* Fetches product details
* Applies return policy rules
* Decides YES or NO
* Explains the decision with evidence

Focus:

* Policy-based reasoning
* Accurate decision-making
* No guessing

---

## System Requirements (Implemented)

* Tool calling (function-based architecture)
* Separation of reasoning and data retrieval
* Strict hallucination prevention
* Refusal when:

  * order ID is invalid
  * product does not exist

---

## Project Structure

```
project/
│
├── main.py
├── agent/
│   ├── agent.py
│   └── prompts.py
│
├── tools/
│   ├── product_tools.py
│   ├── order_tools.py
│   └── return_tools.py
│
├── utils/
│   └── data_loader.py
│
├── data/
│   ├── products.csv
│   ├── orders.csv
│   └── policy.txt
│
└── requirements.txt
```

---

## LLM Reasoning

The LLM is used for:

* Tool selection based on user intent
* Generating explanations from structured tool outputs

It does not:

* Access raw data directly
* Invent products, prices, or policies

---

## Hallucination Prevention

* All data comes from tools (CSV + policy)
* Tool outputs follow strict schemas
* Responses are restricted to tool data only
* Validation layer ensures correctness
* Clear refusal for invalid inputs

---

## Summary

This project demonstrates a production-style agentic AI system that:

* Uses structured tools for all data access
* Performs multi-step reasoning for shopping and support
* Applies real-world business and policy logic
* Ensures reliability through strict validation

It is designed to reflect how real AI systems operate in e-commerce and customer support environments.

```

