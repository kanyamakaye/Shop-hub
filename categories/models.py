from django.db import models

from tenants.models import Tenant


class Category(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='categories')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    category_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['category_name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.category_name
