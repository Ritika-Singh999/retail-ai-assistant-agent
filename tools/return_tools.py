from datetime import datetime


def evaluate_return(order_id, orders, products, policy=None):
    
    # get order first
    try:
        order_match = orders[orders["order_id"] == int(order_id)]
    except Exception:
        # if casting fails, try matching as-is
        order_match = orders[orders["order_id"] == order_id]

    if order_match.empty:
        return None

    order = order_match.iloc[0]

    # get product linked to this order
    product_match = products[products["product_id"] == order["product_id"]]

    if product_match.empty:
        return None

    product = product_match.iloc[0]

    # calculate days difference
    try:
        order_date = datetime.strptime(order["order_date"], "%Y-%m-%d")
    except Exception:
        return {
            "eligible": False,
            "outcome": "no_return",
            "reason": "invalid_order_date",
            "explanation": "There was an issue reading the order date.",
            "evidence": {"order_id": int(order_id) if str(order_id).isdigit() else order_id}
        }

    days_passed = (datetime.now() - order_date).days

    evidence = {
        "days_passed": days_passed,
        "order_id": int(order_id) if str(order_id).isdigit() else order_id,
        "product_id": product["product_id"],
        "product_title": product.get("title") if "title" in product.index else None,
    }

    # business rules 

    # Policy-driven defaults
    normal_days = 14
    sale_days = 7
    clearance_no_return = True
    vendor_exceptions = {}

    if isinstance(policy, dict):
        normal_days = policy.get("normal_days", normal_days)
        sale_days = policy.get("sale_days", sale_days)
        clearance_no_return = policy.get("clearance_no_return", clearance_no_return)
        vendor_exceptions = policy.get("vendor_exceptions", {})

    # clearance items (no return)
    if product.get("is_clearance") and clearance_no_return:
        return {
            "eligible": False,
            "outcome": "no_return",
            "reason": "clearance",
            "explanation": "This item is on clearance, so returns are not allowed.",
            "evidence": evidence,
        }
    # sale items (short window)
    if product.get("is_sale"):
        if days_passed <= sale_days:
            return {
                "eligible": True,
                "outcome": "store_credit",
                "reason": "sale_within_window",
                "explanation": f"This sale item can be returned within {sale_days} days for store credit.",
                "evidence": evidence,
            }
        else:
            return {
                "eligible": False,
                "outcome": "no_return",
                "reason": "sale_window_expired",
                "explanation": f"The {sale_days}-day return window for sale items has already passed.",
                "evidence": evidence,
            }

    # vendor specific rules
    vendor = product.get("vendor")
    vrule = vendor_exceptions.get(vendor)
    if vrule:
        if vrule.get("type") == "exchange_only":
            return {
                "eligible": False,
                "outcome": "exchange_only",
                "reason": "vendor_exchanges_only",
                "explanation": "This brand only allows exchanges, not full returns.",
                "evidence": evidence,
            }
        if vrule.get("type") == "window":
            days = vrule.get("days", normal_days)
            if days_passed <= days:
                return {
                    "eligible": True,
                    "outcome": "full_refund",
                    "reason": f"vendor_{days}_day",
                    "explanation": f"This item falls under a {days}-day vendor return policy and is still eligible.",
                    "evidence": evidence,
                }
            else:
                return {
                    "eligible": False,
                    "outcome": "no_return",
                    "reason": f"vendor_{days}_day_expired",
                    "explanation": f"The {days}-day return window has expired.",
                    "evidence": evidence,
                }

    # normal return policy
    if days_passed <= normal_days:
        return {
            "eligible": True,
            "outcome": "full_refund",
            "reason": "standard_window",
            "explanation": f"This item is eligible for return within {normal_days} days for a full refund.",
            "evidence": evidence,
        }

    return {
        "eligible": False,
        "outcome": "no_return",
        "reason": "standard_window_expired",
        "explanation": "The return window has expired for this item.",
        "evidence": evidence,
    }