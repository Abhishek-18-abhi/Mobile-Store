from django.db import models
from products.models import Product


class Order(models.Model):
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    order_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, default='UPI')
    payment_status = models.CharField(max_length=50, default='Paid')
    transaction_id = models.CharField(max_length=100, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"{self.customer_name} - {self.product.name} (Qty: {self.quantity})"
