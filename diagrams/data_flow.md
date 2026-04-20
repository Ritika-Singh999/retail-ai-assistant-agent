# Data Flow Diagram

```mermaid
graph TD
  User[User] --> CLI[main.py\n(CLI)]
  CLI --> Agent[Agent Controller\n(agent/agent.py)]

  Agent -->|Tool selection prompt| LLM[Generative Model]
  LLM -->|Tool JSON (tool + args)| Agent

  Agent --> Executor[Tool Executor\n(main.execute_tool)]

  Executor --> ProductsTool[search_products\n(tools/product_tools.py)]
  Executor --> OrdersTool[get_order\n(tools/order_tools.py)]
  Executor --> ReturnTool[evaluate_return\n(tools/return_tools.py)]

  ProductsTool --> DataLoader[utils/data_loader.py]
  OrdersTool --> DataLoader
  ReturnTool --> DataLoader

  DataLoader --> Inventory[product_inventory.csv]
  DataLoader --> OrdersCSV[orders.csv]
  DataLoader --> Policy[policy.txt]

  ProductsTool -->|structured JSON| Agent
  OrdersTool -->|structured JSON| Agent
  ReturnTool -->|structured JSON| Agent

  Agent --> Validator[validate_tool_output]
  Validator -->|valid| LLM_Final[Generative Model\n(final explanation)]
  Validator -->|invalid| Fallback[Deterministic Fallback\n(parse_shopper_query / deterministic_final_response)]

  LLM_Final -->|uses only tool fields| User
  Fallback -->|deterministic evidence-based reply| User

  Agent -->|evidence block| AgentWork[Agent Work / Evidence]
  AgentWork --> User

  style User fill:#f9f,stroke:#333,stroke-width:1px
  style CLI fill:#ccf,stroke:#333
  style Agent fill:#cfc,stroke:#333
  style LLM fill:#ffc,stroke:#333
  style DataLoader fill:#efe,stroke:#333
  style ProductsTool fill:#eef,stroke:#333
  style Validator fill:#fdd,stroke:#333
  style Fallback fill:#ffd,stroke:#333
```
