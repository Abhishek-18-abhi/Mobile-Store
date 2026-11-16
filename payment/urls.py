from django.urls import path
from . import views

urlpatterns = [
    path('', views.process_payment, name='process_payment'),
    path('confirm/', views.confirm_payment, name='confirm_payment'),
]
