from django import forms

from .models import ContactMessage, NewsletterSubscriber

INPUT_CLASS = 'form-input'


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'you@example.com'}),
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', INPUT_CLASS)
        self.fields['message'].widget = forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4})
