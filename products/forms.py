from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'sku', 'product_name', 'description', 'image',
            'price', 'discount_price', 'stock_quantity', 'low_stock_threshold', 'status',
        ]

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'image':
                field.widget.attrs.setdefault('class', 'form-input')
        self.fields['image'].widget.attrs.setdefault('class', 'file-input')
        if tenant is not None:
            self.fields['category'].queryset = self.fields['category'].queryset.model.objects.filter(tenant=tenant)

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        discount_price = cleaned_data.get('discount_price')
        if price is not None and discount_price is not None and discount_price >= price:
            self.add_error('discount_price', 'Discount price must be lower than the regular price.')
        return cleaned_data
