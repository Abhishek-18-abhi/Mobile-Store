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
        messages.success(request, 'Thank you! Your message has been received. Our team will contact you shortly.')
        return redirect('contact')
    return render(request, 'customer/contact.html')


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    key = str(product.id)
    cart[key] = cart.get(key, 0) + 1
    request.session['cart'] = cart
    messages.success(request, f'Added "{product.name}" to your cart!')
    # Redirect back to referring page if available, else cart
    next_url = request.META.get('HTTP_REFERER')
    if next_url and 'cart' not in next_url:
        return redirect(next_url)
    return redirect('cart')
