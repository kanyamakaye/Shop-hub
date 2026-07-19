from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        SYSTEM_OWNER = 'System Owner', 'System Owner'
        SYSTEM_ADMIN = 'System Admin', 'System Admin'
        USER = 'User', 'User'

    class Status(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    tenant = models.ForeignKey(
        'tenants.Tenant', on_delete=models.CASCADE, null=True, blank=True,
        related_name='users',
        help_text='Left blank for the System Owner; required for System Admin and tenant customers.',
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    phone = models.CharField(max_length=20, blank=True)
    province = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=100, blank=True)
    cell = models.CharField(max_length=100, blank=True)
    village = models.CharField(max_length=100, blank=True)
    postal_address = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_system_owner(self):
        return self.role == self.Role.SYSTEM_OWNER

    @property
    def is_system_admin(self):
        return self.role == self.Role.SYSTEM_ADMIN

    @property
    def is_customer(self):
        return self.role == self.Role.USER
