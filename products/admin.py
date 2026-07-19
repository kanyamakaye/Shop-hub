from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'sku', 'tenant', 'category', 'price', 'discount_price', 'status')
    list_filter = ('status', 'tenant', 'category')
    search_fields = ('product_name', 'sku')
