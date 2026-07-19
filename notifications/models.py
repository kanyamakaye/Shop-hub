from django.conf import settings
from django.db import models

from tenants.models import Tenant


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        ORDER = 'Order', 'Order'
        PAYMENT = 'Payment', 'Payment'
        SHIPPING = 'Shipping', 'Shipping'
        GENERAL = 'General', 'General'

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.GENERAL)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
