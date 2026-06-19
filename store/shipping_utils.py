def calculate_shipping(cart_items, subtotal):
    """
    Calculates the total chargeable weight and shipping cost.
    DIM factor is 5000.
    """
    total_weight = 0.0

    # Calculate total chargeable weight
    for cart_item in cart_items:
        product = cart_item.product
        # Volumetric weight = (L * W * H) / 5000
        volumetric_weight = (product.length * product.width * product.height) / 5000.0
        # Chargeable weight is the max between gross weight and volumetric weight
        chargeable_weight = max(product.gross_weight, volumetric_weight)
        
        total_weight += chargeable_weight * cart_item.quantity

    # Determine shipping cost
    shipping_cost = 0.0

    if subtotal >= 500:
        shipping_cost = 0.0
    else:
        if total_weight <= 500:
            shipping_cost = 10.0
        else:
            shipping_cost = 10.0 + (total_weight - 500) * 0.02

    return round(total_weight, 2), round(shipping_cost, 2)
