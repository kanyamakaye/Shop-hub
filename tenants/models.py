from django.db import models

from subscriptions.models import SubscriptionPlan


class Tenant(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'
        SUSPENDED = 'Suspended', 'Suspended'

    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='tenants')
    business_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    whatsapp_number = models.CharField(max_length=20, blank=True, help_text='Include country code, e.g. +250788111111')
    country = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='tenant_logos/', blank=True, null=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Percentage tax/VAT applied to orders from this store, e.g. 18 for 18%.')
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Flat shipping fee (RWF) added to orders from this store.')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['business_name']

    def __str__(self):
        return self.business_name

    @property
    def whatsapp_link(self):
        if not self.whatsapp_number:
            return ''
        digits = ''.join(ch for ch in self.whatsapp_number if ch.isdigit())
        return f'https://wa.me/{digits}' if digits else ''
