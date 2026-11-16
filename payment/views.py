import secrets
from django.shortcuts import render, redirect
from django.contrib import messages
from orders.models import Order
from orders.views import _cart_items


def process_payment(request):
    items, total = _cart_items(request)

    if not items:
        messages.warning(request, 'Your cart is empty. Please add smartphones before checkout.')
        return redirect('products')

    checkout_data = request.session.get('checkout_data')
    if not checkout_data:
        messages.info(request, 'Please provide your delivery details first.')
        return redirect('checkout')

    return render(request, 'payment/gateway.html', {
        'items': items,
        'total': total,
        'checkout_data': checkout_data,
    })


def confirm_payment(request):
    if request.method != 'POST':
        return redirect('process_payment')

    items, total = _cart_items(request)
    if not items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('products')

    checkout_data = request.session.get('checkout_data')
    if not checkout_data:
        return redirect('checkout')

    raw_method = request.POST.get('payment_method', 'UPI').upper()
    payment_status = 'Paid'
    method_display = 'UPI Payment'

    if raw_method == 'CARD':
        card_num = request.POST.get('card_number', '').replace(' ', '')
        last4 = card_num[-4:] if len(card_num) >= 4 else '8920'
        card_holder = request.POST.get('card_holder', 'Cardholder').strip()
        method_display = f"Credit/Debit Card (•••• {last4})"
    elif raw_method == 'NETBANKING':
        bank_name = request.POST.get('bank_name', 'HDFC Bank')
        method_display = f"Net Banking ({bank_name})"
    elif raw_method == 'COD':
        method_display = 'Cash on Delivery (COD)'
        payment_status = 'Pending (COD)'
    else:
        upi_id = request.POST.get('upi_id', '').strip()
        if upi_id:
            method_display = f"UPI ({upi_id})"
        else:
            method_display = "UPI (Instant App Pay)"

    txn_id = f"TXN_{secrets.randbelow(90000000) + 10000000}"

    customer_name = checkout_data.get('customer_name', 'Customer')
    phone = checkout_data.get('phone', '')
    address = checkout_data.get('address', '')

    for item in items:
        product = item['product']
        qty = item['quantity']

        Order.objects.create(
            customer_name=customer_name,
            phone=phone,
            address=address,
            product=product,
            quantity=qty,
            payment_method=method_display,
            payment_status=payment_status,
            transaction_id=txn_id,
            total_amount=item['subtotal']
        )

        if product.stock >= qty:
            product.stock -= qty
        else:
            product.stock = 0
        product.save(update_fields=['stock'])

    # Save summary for receipt
    request.session['last_payment'] = {
        'txn_id': txn_id,
        'payment_method': method_display,
        'payment_status': payment_status,
        'total': float(total),
        'customer_name': customer_name,
        'phone': phone,
        'address': address,
        'items': [
            {
                'name': i['product'].name,
                'qty': i['quantity'],
                'price': float(i['product'].price),
                'subtotal': float(i['subtotal']),
                'brand': i['product'].brand
            }
            for i in items
        ]
    }

    # Clear cart and checkout data
    request.session['cart'] = {}
    request.session.pop('checkout_data', None)

    messages.success(request, f'Payment successful! Transaction ID: {txn_id}')
    return redirect('bill')
