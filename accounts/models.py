import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


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


class PlatformSettings(models.Model):
    """Single-row, platform-wide settings, editable by the System Owner."""
    two_factor_enabled = models.BooleanField(
        default=False,
        help_text='Require an emailed 6-digit code after password login, for every account with an email on file.',
    )

    class Meta:
        verbose_name = 'Platform settings'
        verbose_name_plural = 'Platform settings'

    def __str__(self):
        return 'Platform settings'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class EmailOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_otps')
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    @classmethod
    def generate_for(cls, user):
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        raw_code = ''.join(secrets.choice(string.digits) for _ in range(6))
        otp = cls.objects.create(
            user=user,
            code_hash=make_password(raw_code),
            expires_at=timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
        )
        return otp, raw_code

    def verify_code(self, code):
        self.attempts += 1
        self.save(update_fields=['attempts'])
        if self.is_used or self.attempts > settings.OTP_MAX_ATTEMPTS or timezone.now() > self.expires_at:
            return False
        if not check_password(code, self.code_hash):
            return False
        self.is_used = True
        self.save(update_fields=['is_used'])
        return True
