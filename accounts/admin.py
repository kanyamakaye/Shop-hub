from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'tenant', 'status', 'is_staff')
    list_filter = ('role', 'status', 'tenant')
    fieldsets = UserAdmin.fieldsets + (
        ('Tenant & Role', {'fields': ('tenant', 'role', 'status', 'phone')}),
        ('Location', {'fields': ('province', 'district', 'sector', 'cell', 'village', 'postal_address')}),
    )
