def get_order(orders, order_id):

    # sometimes order_id comes as string, so converting both sides
    try:
        order_id = int(order_id)
    except:
        pass

    match = orders[orders["order_id"] == order_id]

    if match.empty:
        return None

    # returning first match 
    order_data = match.iloc[0].to_dict()

    return order_data