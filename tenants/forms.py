from django import forms

from .models import Tenant


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = [
            'plan', 'business_name', 'email', 'phone', 'whatsapp_number', 'country', 'address',
            'logo', 'tax_rate', 'shipping_fee', 'status',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'logo':
                field.widget.attrs.setdefault('class', 'form-input')
        self.fields['logo'].widget.attrs.setdefault('class', 'file-input')
