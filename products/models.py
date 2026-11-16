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
    image_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Direct image URL (optional)"
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    @property
    def get_image_url(self):
        if self.image_url:
            return self.image_url
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        return None