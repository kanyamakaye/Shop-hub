from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from products.models import Product


class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    review_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-review_date']

    def __str__(self):
        return f'{self.rating}★ {self.product.product_name} by {self.user}'
