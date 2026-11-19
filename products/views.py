from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product


def home(request):
    all_products = Product.objects.all()
    brands = Product.objects.values_list('brand', flat=True).distinct()
    return render(
        request,
        'customer/home.html',
        {
            'products': all_products,
            'brands': [b for b in brands if b],
        }
    )


def products(request):
    query = request.GET.get('q', '').strip()
    brand = request.GET.get('brand', '').strip()

    products_qs = Product.objects.all()

    if query:
        products_qs = products_qs.filter(name__icontains=query) | products_qs.filter(description__icontains=query)

    if brand:
        products_qs = products_qs.filter(brand__iexact=brand)

    all_brands = Product.objects.values_list('brand', flat=True).distinct()

    return render(
        request,
        'customer/product.html',
        {
            'products': products_qs,
            'query': query,
            'selected_brand': brand,
            'brands': [b for b in all_brands if b],
            'total_count': products_qs.count(),
        }
    )


def about(request):
    return render(request, 'customer/about.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()

        if not name or not email or not message:
            messages.error(request, 'Please fill in all required fields (Name, Email, and Message).')
            return render(request, 'customer/contact.html')

        if '@' not in email or '.' not in email:
            messages.error(request, 'Please provide a valid email address.')
            return render(request, 'customer/contact.html')

        messages.success(request, f'Thank you, {name}! Your message has been received. Our priority support team will contact you at {email} within 24 hours.')
        return redirect('contact')
    return render(request, 'customer/contact.html')


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Inventory Guard: Out of stock check
    if product.stock <= 0:
        messages.error(request, f'Sorry, "{product.name}" is currently out of stock and cannot be added.')
        next_url = request.META.get('HTTP_REFERER')
        return redirect(next_url or 'products')

    cart = request.session.get('cart', {})
    key = str(product.id)
    current_qty = cart.get(key, 0)

    # Inventory Guard: Do not exceed available inventory
    if current_qty >= product.stock:
        messages.warning(request, f'Cannot add more. You already have all {product.stock} available units of "{product.name}" in your cart.')
        return redirect('cart')

    cart[key] = current_qty + 1
    request.session['cart'] = cart
    messages.success(request, f'Added "{product.name}" to your cart!')

    # Redirect back to referring page if available, else cart
    next_url = request.META.get('HTTP_REFERER')
    if next_url and 'cart' not in next_url:
        return redirect(next_url)
    return redirect('cart')
