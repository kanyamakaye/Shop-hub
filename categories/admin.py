from django.contrib import admin

from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'tenant')
    list_filter = ('tenant',)
    search_fields = ('category_name',)
