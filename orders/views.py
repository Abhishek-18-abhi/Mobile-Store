from django.shortcuts import render, redirect
from products.models import Product
from .models import Order


def _cart_items(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0

    for pid, qty in cart.items():
        try:
            product = Product.objects.get(id=pid)
            subtotal = product.price * qty
            total += subtotal

            items.append({
                'product': product,
                'quantity': qty,
                'subtotal': subtotal
            })

        except Product.DoesNotExist:
            pass

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
            cart[key] += 1

        elif action == 'minus':
            cart[key] -= 1

        if cart[key] <= 0:
            cart.pop(key, None)

    request.session['cart'] = cart

    return redirect('cart')


def remove_cart(request, product_id):
    cart = request.session.get('cart', {})

    cart.pop(str(product_id), None)

    request.session['cart'] = cart

    return redirect('cart')


def checkout(request):
    items, total = _cart_items(request)

    if request.method == 'POST':

        customer_name = request.POST.get('customer_name')

        for item in items:

            Order.objects.create(
                customer_name=customer_name,
                product=item['product'],
                quantity=item['quantity']
            )

        request.session['cart'] = {}

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