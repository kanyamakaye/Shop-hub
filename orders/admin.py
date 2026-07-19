from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'user', 'total_amount', 'payment_status', 'order_status', 'order_date')
    list_filter = ('order_status', 'payment_status', 'tenant')
    inlines = [OrderItemInline]
