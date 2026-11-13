from django.shortcuts import render, redirect, get_object_or_404
from .models import Product

def home(request):
    products = Product.objects.all()
    return render(
        request,
        'customer/home.html',
        {
            'products': products
        })
def products(request):
    products = Product.objects.all()
    return render(
        request,
        'customer/product.html',
        {'products': products})
def about(request): return render(request, 'customer/about.html')
def contact(request): return render(request, 'customer/contact.html')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    key = str(product.id); cart[key] = cart.get(key, 0) + 1
    request.session['cart'] = cart
    return redirect('cart')
