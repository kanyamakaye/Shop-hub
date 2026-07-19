from django.db import models

# Curated headline features per tier, from pricing doc.md (each plan's full
# feature list runs 20-30 items; these are the ones worth surfacing on a
# pricing card — "everything in the previous tier" is implied, not repeated).
PLAN_FEATURES = {
    'Basic': [
        'Online store & product management',
        'Inventory & stock monitoring',
        'Shopping cart & order management',
        'Wishlist, reviews & ratings',
        'Sales dashboard & basic reports',
        'Discount & coupon management',
        'Secure cloud hosting & SSL',
        'Basic technical support',
    ],
    'Professional': [
        'Everything in Basic, plus:',
        'Product variants & attributes',
        'Bulk import/export & barcode/SKU tools',
        'Advanced discounts & coupon rules',
        'Customer segmentation & analytics',
        'Executive dashboard & revenue analytics',
        'Multi-branch & multiple payment gateways',
        'SMS & WhatsApp notifications',
        'Priority technical support',
    ],
    'Enterprise': [
        'Everything in Professional, plus:',
        'Multi-store & multi-company management',
        'AI sales, inventory & revenue forecasting',
        'AI business intelligence dashboard',
        'Workflow automation & custom dashboards',
        'REST API, webhooks & ERP integration',
        'Mobile app, SSO & multi-factor auth',
        'Dedicated support & SLA',
    ],
}


class SubscriptionPlan(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    plan_name = models.CharField(max_length=100)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    yearly_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_products = models.IntegerField(help_text='Use -1 for unlimited.')
    max_users = models.IntegerField(help_text='Use -1 for unlimited.')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ['monthly_price']

    def __str__(self):
        return self.plan_name

    @property
    def max_products_display(self):
        return 'Unlimited' if self.max_products < 0 else self.max_products

    @property
    def max_users_display(self):
        return 'Unlimited' if self.max_users < 0 else self.max_users

    @property
    def features(self):
        return PLAN_FEATURES.get(self.plan_name, [])
