from django.shortcuts import render, redirect
from django.contrib import messages
from products.models import Product
from .models import Order


def _cart_items(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0

    if not isinstance(cart, dict):
        return items, total

    for pid, qty in list(cart.items()):
        try:
            qty_int = int(qty)
            if qty_int <= 0:
                continue
            product = Product.objects.get(id=pid)
            subtotal = product.price * qty_int
            total += subtotal

            items.append({
                'product': product,
                'quantity': qty_int,
                'subtotal': subtotal
            })

        except (Product.DoesNotExist, ValueError):
            cart.pop(str(pid), None)
            request.session['cart'] = cart

    return items, total


def cart(request):
    items, total = _cart_items(request)

    return render(request, 'customer/cart.html', {
        'items': items,
        'total': total
    })


def update_cart(request, product_id, action):
    cart = request.session.get('cart', {})
    key = str(product_id)

    if key in cart:
        if action == 'plus':
            cart[key] = int(cart[key]) + 1
        elif action == 'minus':
            cart[key] = int(cart[key]) - 1

        if cart[key] <= 0:
            cart.pop(key, None)

    request.session['cart'] = cart
    return redirect('cart')


def remove_cart(request, product_id):
    cart = request.session.get('cart', {})
    key = str(product_id)
    if key in cart:
        cart.pop(key, None)
        request.session['cart'] = cart
        messages.info(request, 'Item removed from your cart.')

    return redirect('cart')


def checkout(request):
    items, total = _cart_items(request)

    if not items:
        messages.warning(request, 'Your cart is empty. Please add items before checking out.')
        return redirect('products')

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        if not customer_name:
            customer_name = request.user.username if request.user.is_authenticated else 'Customer'

        for item in items:
            product = item['product']
            quantity = item['quantity']

            Order.objects.create(
                customer_name=customer_name,
                product=product,
                quantity=quantity
            )

            # Reduce product stock safely
            if product.stock >= quantity:
                product.stock -= quantity
            else:
                product.stock = 0
            product.save(update_fields=['stock'])

        # Clear cart
        request.session['cart'] = {}
        messages.success(request, 'Order placed successfully!')
        return redirect('bill')

    return render(request, 'customer/checkout.html', {
        'items': items,
        'total': total
    })


def order_history(request):
    orders = Order.objects.all().order_by('-order_date')
    return render(request, 'customer/order_history.html', {
        'orders': orders
    })


def bill(request):
    return render(request, 'customer/bill.html')
