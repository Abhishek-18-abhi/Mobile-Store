def num_to_words_inr(n):
    """Converts a number to Indian Rupee words (Lakhs, Crores format)."""
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
            'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
            'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    try:
        n = int(round(float(n)))
    except (ValueError, TypeError):
        return "Zero Rupees Only"

    if n <= 0:
        return "Zero Rupees Only"

    def helper(num):
        if num < 20:
            return ones[num]
        elif num < 100:
            return tens[num // 10] + (' ' + ones[num % 10] if num % 10 != 0 else '')
        elif num < 1000:
            return ones[num // 100] + ' Hundred' + (' ' + helper(num % 100) if num % 100 != 0 else '')
        elif num < 100000:
            return helper(num // 1000) + ' Thousand' + (' ' + helper(num % 1000) if num % 1000 != 0 else '')
        elif num < 10000000:
            return helper(num // 100000) + ' Lakh' + (' ' + helper(num % 100000) if num % 100000 != 0 else '')
        else:
            return helper(num // 10000000) + ' Crore' + (' ' + helper(num % 10000000) if num % 10000000 != 0 else '')

    return helper(n).strip() + ' Rupees Only'


def build_invoice_context(order_or_orders, last_payment_dict=None):
    """
    Constructs a complete, authentic GST commercial tax invoice dictionary.
    Handles single Order, list of Orders, or session dictionary fallback.
    """
    items_out = []
    grand_total = 0.0

    if order_or_orders:
        orders_list = [order_or_orders] if not hasattr(order_or_orders, '__iter__') else list(order_or_orders)
        first_order = orders_list[0]

        invoice_no = f"INV/2026-27/{first_order.id:05d}"
        invoice_date = first_order.order_date.strftime("%d %b %Y, %I:%M %p")
        order_ref = f"#ORD-{first_order.id:04d}"
        customer_name = first_order.customer_name or "Valued Customer"
        phone = first_order.phone or "N/A"
        address = first_order.address or "Standard Shipping Address"
        payment_method = first_order.payment_method or "Online Payment"
        payment_status = first_order.payment_status or "Paid"
        txn_id = first_order.transaction_id or f"TXN_{first_order.id:08d}"

        idx = 1
        for ord_item in orders_list:
            unit_price = float(ord_item.product.price)
            qty = int(ord_item.quantity)
            subtotal = float(ord_item.total_amount) if ord_item.total_amount and ord_item.total_amount > 0 else (unit_price * qty)
            grand_total += subtotal

            # 18% GST calculation (inclusive)
            base_rate = round(unit_price / 1.18, 2)
            taxable_val = round(base_rate * qty, 2)
            tax_diff = subtotal - taxable_val
            cgst = round(tax_diff / 2.0, 2)
            sgst = round(tax_diff - cgst, 2)

            items_out.append({
                'sr_no': idx,
                'name': ord_item.product.name,
                'brand': ord_item.product.brand,
                'hsn_code': '8517 12 00',
                'qty': qty,
                'unit_price': f"{unit_price:,.2f}",
                'base_rate': f"{base_rate:,.2f}",
                'taxable_val': f"{taxable_val:,.2f}",
                'cgst': f"{cgst:,.2f}",
                'sgst': f"{sgst:,.2f}",
                'subtotal': f"{subtotal:,.2f}",
                'raw_taxable': taxable_val,
                'raw_cgst': cgst,
                'raw_sgst': sgst,
                'raw_subtotal': subtotal
            })
            idx += 1

    elif last_payment_dict:
        customer_name = last_payment_dict.get('customer_name', 'Valued Customer')
        phone = last_payment_dict.get('phone', 'N/A')
        address = last_payment_dict.get('address', 'Standard Shipping Address')
        payment_method = last_payment_dict.get('payment_method', 'UPI / Online')
        payment_status = last_payment_dict.get('payment_status', 'Paid')
        txn_id = last_payment_dict.get('txn_id', 'TXN_ONLINE')
        invoice_no = f"INV/2026-27/{txn_id.replace('TXN_', '')[:6]}"
        import datetime
        invoice_date = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
        order_ref = f"#ORD-{txn_id.replace('TXN_', '')[:4]}"

        idx = 1
        raw_items = last_payment_dict.get('items', [])
        for itm in raw_items:
            qty = int(itm.get('qty', 1))
            unit_price = float(itm.get('price', 0.0))
            subtotal = float(itm.get('subtotal', unit_price * qty))
            grand_total += subtotal

            base_rate = round(unit_price / 1.18, 2)
            taxable_val = round(base_rate * qty, 2)
            tax_diff = subtotal - taxable_val
            cgst = round(tax_diff / 2.0, 2)
            sgst = round(tax_diff - cgst, 2)

            items_out.append({
                'sr_no': idx,
                'name': itm.get('name', 'Smartphone'),
                'brand': itm.get('brand', 'Mobile'),
                'hsn_code': '8517 12 00',
                'qty': qty,
                'unit_price': f"{unit_price:,.2f}",
                'base_rate': f"{base_rate:,.2f}",
                'taxable_val': f"{taxable_val:,.2f}",
                'cgst': f"{cgst:,.2f}",
                'sgst': f"{sgst:,.2f}",
                'subtotal': f"{subtotal:,.2f}",
                'raw_taxable': taxable_val,
                'raw_cgst': cgst,
                'raw_sgst': sgst,
                'raw_subtotal': subtotal
            })
            idx += 1
    else:
        return None

    total_taxable = sum(i['raw_taxable'] for i in items_out)
    total_cgst = sum(i['raw_cgst'] for i in items_out)
    total_sgst = sum(i['raw_sgst'] for i in items_out)
    total_tax = total_cgst + total_sgst

    return {
        'invoice_no': invoice_no,
        'invoice_date': invoice_date,
        'order_ref': order_ref,
        'customer_name': customer_name,
        'phone': phone,
        'address': address,
        'payment_method': payment_method,
        'payment_status': payment_status,
        'txn_id': txn_id,
        'items': items_out,
        'taxable_total': f"{total_taxable:,.2f}",
        'cgst_total': f"{total_cgst:,.2f}",
        'sgst_total': f"{total_sgst:,.2f}",
        'total_tax': f"{total_tax:,.2f}",
        'grand_total': f"{grand_total:,.2f}",
        'amount_in_words': num_to_words_inr(grand_total),
    }
