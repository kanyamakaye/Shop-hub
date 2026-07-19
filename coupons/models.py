from django.db import models
from django.utils import timezone

from tenants.models import Tenant


class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'Percentage', 'Percentage'
        FIXED = 'Fixed', 'Fixed Amount'

    class Status(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=30)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices, default=DiscountType.PERCENTAGE)
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text='Percent (e.g. 10) or a flat RWF amount, depending on the type above.',
    )
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True, help_text='Leave blank for unlimited uses.')
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'code')

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def is_valid_for(self, subtotal):
        """Returns (is_valid, reason_if_not)."""
        today = timezone.now().date()
        if self.status != self.Status.ACTIVE:
            return False, 'This coupon is no longer active.'
        if self.valid_from and today < self.valid_from:
            return False, 'This coupon is not active yet.'
        if self.valid_until and today > self.valid_until:
            return False, 'This coupon has expired.'
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False, 'This coupon has reached its usage limit.'
        if subtotal < self.min_order_amount:
            return False, f'A minimum order of {self.min_order_amount:,.0f} RWF is required for this coupon.'
        return True, ''

    def compute_discount(self, subtotal):
        if self.discount_type == self.DiscountType.PERCENTAGE:
            return round(subtotal * self.discount_value / 100, 2)
        return min(self.discount_value, subtotal)
