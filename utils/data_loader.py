import pandas as pd

def load_data():
    products = pd.read_csv("data/product_inventory.csv")
    orders = pd.read_csv("data/orders.csv")
    with open("data/policy.txt", "r") as f:
        policy_text = f.read()

    policy = parse_policy(policy_text)

    return products, orders, policy


def parse_policy(text: str) -> dict:
    """Parse the human-readable policy text into a simple dict.

    This is a lightweight parser tailored for the provided `policy.txt` format.
    It extracts numeric windows and vendor exceptions into structured fields.
    """
    import re

    policy = {
        "normal_days": 14,
        "sale_days": 7,
        "clearance_no_return": True,
        "vendor_exceptions": {},
        "exchange_rules": {},
    }

    # Normalize whitespace and split lines
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for i, line in enumerate(lines):
        # Normal Items: Returns accepted within 14 days
        m = re.search(r"Normal Items:.*?(\d+) days", line, re.IGNORECASE)
        if m:
            policy["normal_days"] = int(m.group(1))

        m = re.search(r"Sale Items:.*?(\d+) days", line, re.IGNORECASE)
        if m:
            policy["sale_days"] = int(m.group(1))

        if "Clearance Items" in line:
            # If next lines mention 'Final sale' assume no returns
            if i + 1 < len(lines) and "final" in lines[i + 1].lower():
                policy["clearance_no_return"] = True

        if "Vendor Exceptions" in line:
            # Read following lines until a blank or next section
            j = i + 1
            while j < len(lines) and ":" in lines[j]:
                parts = lines[j].split(":", 1)
                vendor = parts[0].strip()
                rule = parts[1].strip()
                # handle common cases
                if "exchanges only" in rule.lower():
                    policy["vendor_exceptions"][vendor] = {"type": "exchange_only"}
                else:
                    # extract numeric window if present
                    mm = re.search(r"(\d+) day", rule)
                    if mm:
                        policy["vendor_exceptions"][vendor] = {"type": "window", "days": int(mm.group(1))}
                    else:
                        policy["vendor_exceptions"][vendor] = {"type": "other", "text": rule}
                j += 1

        if "Exchange Rules" in line:
            # capture simple exchange rules
            k = i + 1
            while k < len(lines) and ":" not in lines[k]:
                l = lines[k].lower()
                if "size exchanges allowed" in l:
                    policy["exchange_rules"]["size_exchanges"] = True
                k += 1

    return policy