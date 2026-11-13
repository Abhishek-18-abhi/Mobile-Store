from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name