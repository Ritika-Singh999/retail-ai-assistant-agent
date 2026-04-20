import pandas as pd
import ast


def search_products(products, max_price=None, size=None, on_sale=None, tag=None):
    results = []

    for _, row in products.iterrows():

        # Price filter
        if max_price is not None and row["price"] > max_price:
            continue

        # Sale filter
        if on_sale is not None and row["is_sale"] != on_sale:
            continue

        # Tag filter 
        if tag:
            if tag.lower() not in str(row["tags"]).lower():
                continue

        # Size + stock handling
        try:
            stock = ast.literal_eval(row.get("stock_per_size", "{}"))
        except Exception:
            stock = {}

        if size:
            sizes = [s.strip() for s in str(row.get("sizes_available", "")).split("|") if s]
            if str(size) not in sizes:
                continue
            if stock.get(str(size), 0) <= 0:
                continue
        else:
            # If no size requested, ensure there is some stock available
            total_stock = sum([int(v) for v in stock.values()]) if isinstance(stock, dict) else 0
            if total_stock <= 0:
                continue

        # Add to results 
        results.append({
            "product_id": row["product_id"],
            "title": row["title"],
            "price": row["price"],
            "vendor": row["vendor"],
            "is_sale": row["is_sale"],
            "bestseller_score": row.get("bestseller_score", 0),
            "sizes_available": row.get("sizes_available", ""),
            "stock_per_size": stock,
        })

    # Sorting
    results = sorted(
        results,
        key=lambda x: (
            not x["is_sale"],
            -x["bestseller_score"]
        )
    )

    # Return 
    return results[:3]


def get_product(products, product_id):
    match = products[products["product_id"] == product_id]

    if match.empty:
        return None

    return match.iloc[0].to_dict()