from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import models
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
        try:
            product = Product.objects.get(id=product_id)
            current_qty = int(cart[key])
            if action == 'plus':
                if current_qty < product.stock:
                    cart[key] = current_qty + 1
                else:
                    messages.warning(request, f'Maximum available stock for "{product.name}" is {product.stock} units.')
            elif action == 'minus':
                cart[key] = current_qty - 1

            if cart[key] <= 0:
                cart.pop(key, None)
        except Product.DoesNotExist:
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

    # Inventory Stock Guard: ensure no cart item exceeds available stock
    out_of_stock_items = []
    for item in items:
        if item['quantity'] > item['product'].stock:
            out_of_stock_items.append(
                f"{item['product'].name} (Requested: {item['quantity']}, Available: {item['product'].stock})"
            )

    if out_of_stock_items:
        messages.error(
            request,
            f"Some items in your cart exceed available stock: {', '.join(out_of_stock_items)}. Please adjust your cart before checking out."
        )
        return redirect('cart')

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        if not customer_name:
            customer_name = request.user.username if request.user.is_authenticated else 'Customer'

        if not phone or not address:
            messages.error(request, 'Please provide both phone number and delivery address.')
            return render(request, 'customer/checkout.html', {'items': items, 'total': total})

        # Phone length and character sanity check
        digits_only = ''.join(c for c in phone if c.isdigit())
        if len(digits_only) < 10 or len(digits_only) > 15:
            messages.error(request, 'Please enter a valid 10-digit mobile phone number.')
            return render(request, 'customer/checkout.html', {'items': items, 'total': total})

        request.session['checkout_data'] = {
            'customer_name': customer_name,
            'phone': phone,
            'address': address
        }
        return redirect('process_payment')

    return render(request, 'customer/checkout.html', {
        'items': items,
        'total': total
    })


def order_history(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(
            models.Q(user=request.user) |
            models.Q(customer_name__iexact=request.user.username) |
            models.Q(customer_name__iexact=request.user.email)
        ).select_related('product').order_by('-order_date')
    else:
        last_payment = request.session.get('last_payment')
        if last_payment and last_payment.get('txn_id'):
            orders = Order.objects.filter(transaction_id=last_payment['txn_id']).select_related('product').order_by('-order_date')
        else:
            orders = Order.objects.none()

    return render(request, 'customer/order_history.html', {
        'orders': orders
    })


from .invoice_helper import build_invoice_context


def bill(request, order_id=None):
    invoice = None
    last_payment = request.session.get('last_payment')

    if order_id:
        try:
            order = Order.objects.select_related('product', 'user').get(id=order_id)

            # Security / IDOR Guard: Verify requester ownership
            is_owner = (request.user.is_authenticated and order.user_id == request.user.id)
            is_matching_session = bool(last_payment and order.transaction_id == last_payment.get('txn_id'))
            is_staff = bool(request.user.is_authenticated and request.user.is_staff)

            if not (is_owner or is_matching_session or is_staff):
                messages.error(request, 'You do not have permission to view this invoice.')
                return redirect('order_history')

            if order.transaction_id:
                related_orders = Order.objects.filter(transaction_id=order.transaction_id).select_related('product')
            else:
                related_orders = [order]
            invoice = build_invoice_context(related_orders)
        except Order.DoesNotExist:
            messages.error(request, 'The requested invoice could not be found.')
            return redirect('order_history')

    if not invoice:
        if last_payment:
            invoice = build_invoice_context(None, last_payment_dict=last_payment)
        elif request.user.is_authenticated:
            user_order = Order.objects.filter(user=request.user).select_related('product').first()
            if user_order:
                if user_order.transaction_id:
                    related = Order.objects.filter(transaction_id=user_order.transaction_id).select_related('product')
                else:
                    related = [user_order]
                invoice = build_invoice_context(related)

    if not invoice:
        messages.info(request, 'No active order invoice found. Please complete an order first.')
        return redirect('products')

    return render(request, 'customer/bill.html', {
        'invoice': invoice
    })



