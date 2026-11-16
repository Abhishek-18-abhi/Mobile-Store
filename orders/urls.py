from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart, name='cart'),
    path('update/<int:product_id>/<str:action>/', views.update_cart, name='update_cart'),
    path('remove/<int:product_id>/', views.remove_cart, name='remove_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('history/', views.order_history, name='order_history'),
    path('bill/', views.bill, name='bill'),
    path('bill/<int:order_id>/', views.bill, name='order_bill'),
]

