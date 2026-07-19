from django import forms

from .models import Order


class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-input'}))
    coupon_code = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional'}),
    )
    payment_method = forms.ChoiceField(choices=Order.PaymentMethod.choices, widget=forms.RadioSelect)

    def clean_coupon_code(self):
        return self.cleaned_data['coupon_code'].strip().upper()


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_status', 'payment_status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-input')


class ReturnRequestForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['return_reason']
        widgets = {
            'return_reason': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': "What's wrong with the order?"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['return_reason'].required = True
