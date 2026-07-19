from django.contrib import admin

from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'plan', 'email', 'country', 'status')
    list_filter = ('status', 'plan', 'country')
    search_fields = ('business_name', 'email')
