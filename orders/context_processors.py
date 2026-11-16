def cart_context(request):
    """Exposes cart item count to all templates."""
    try:
        cart = request.session.get('cart', {})
        if isinstance(cart, dict):
            # Sum quantities, ignoring non-numeric values safely
            total_items = sum(int(qty) for qty in cart.values() if isinstance(qty, (int, str)) and str(qty).isdigit())
        else:
            total_items = 0
    except Exception:
        total_items = 0
    return {
        'cart_count': total_items
    }
