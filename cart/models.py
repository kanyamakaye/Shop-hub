from django.conf import settings
from django.db import models

from products.models import Product


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_entries')
    quantity = models.PositiveIntegerField(default=1)
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-added_date']

    def __str__(self):
        return f'{self.quantity} x {self.product.product_name}'

    @property
    def subtotal(self):
        return self.product.display_price * self.quantity
