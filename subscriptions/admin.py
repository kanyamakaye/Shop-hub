from django.contrib import admin

from .models import SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'monthly_price', 'yearly_price', 'max_products', 'max_users', 'status')
    list_filter = ('status',)
    search_fields = ('plan_name',)
