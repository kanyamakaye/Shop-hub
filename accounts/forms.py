from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm,
    UserCreationForm,
)

from tenants.models import Tenant
from .models import User

INPUT_CLASS = 'form-input'

CASCADE_FIELDS = ['province', 'district', 'sector', 'cell', 'village']
LOCATION_FIELDS = [*CASCADE_FIELDS, 'postal_address']
# Village is the finest-grained level and not everyone knows/has one on hand,
# so it's the one cascade field that stays optional while the rest are required.
OPTIONAL_LOCATION_FIELDS = {'village'}

PASSWORD_HINT = (
    'At least 8 characters. Avoid common passwords, all-numeric passwords, '
    'or ones too similar to your username.'
)


def require_location_fields(form):
    for name in LOCATION_FIELDS:
        form.fields[name].required = name not in OPTIONAL_LOCATION_FIELDS


def apply_password_strength(field, help_text=PASSWORD_HINT):
    classes = field.widget.attrs.get('class', '')
    field.widget.attrs['class'] = f'{classes} js-pw-strength'.strip()
    field.help_text = help_text


def apply_location_cascade_widgets(form):
    """Render province/district/sector/cell/village as <select> elements populated
    client-side from static/data/rwanda_locations.json (see location-cascade.js).
    The fields stay plain CharFields so any value (including non-Rwanda locations
    left blank) is accepted server-side."""
    for field_name in CASCADE_FIELDS:
        field = form.fields[field_name]
        initial = form.initial.get(field_name) or getattr(form.instance, field_name, '') or ''
        field.widget = forms.Select(
            choices=[('', f'Select {field_name}...')],
            attrs={'class': INPUT_CLASS, 'data-level': field_name, 'data-initial': initial},
        )


class StyledAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': (
            'We couldn’t find an account with that username/email and password combination. '
            'Please double-check and try again — both fields are case-sensitive.'
        ),
        'inactive': 'This account has been deactivated. Contact your organization admin for help.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Username or email'
        self.fields['username'].widget.attrs['placeholder'] = 'yourname or you@example.com'
        self.fields['password'].widget.attrs['placeholder'] = 'Your password'
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', INPUT_CLASS)

    def confirm_login_allowed(self, user):
        # `status` is this app's own Active/Inactive flag — separate from Django's
        # built-in is_active — so it needs its own check here to actually block login.
        if user.status == User.Status.INACTIVE:
            raise forms.ValidationError(self.error_messages['inactive'], code='inactive')
        super().confirm_login_allowed(user)


class StyledPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.setdefault('class', INPUT_CLASS)
        self.fields['email'].widget.attrs['placeholder'] = 'you@example.com'


class RegisterForm(UserCreationForm):
    """Customers are marketplace-wide shoppers, not tied to any one tenant —
    they browse and order across every store from a single account."""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'username',
            *LOCATION_FIELDS,
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', INPUT_CLASS)
        require_location_fields(self)
        apply_location_cascade_widgets(self)
        apply_password_strength(self.fields['password1'])

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.USER
        user.status = User.Status.ACTIVE
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', *LOCATION_FIELDS]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', INPUT_CLASS)
        require_location_fields(self)
        apply_location_cascade_widgets(self)


class AdminUserForm(forms.ModelForm):
    """Used by System Owner / System Admin to create or edit staff & customer accounts."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
        required=False,
        help_text='Leave blank to keep the current password when editing.',
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone',
            'tenant', 'role', 'status', *LOCATION_FIELDS,
        ]

    def __init__(self, *args, actor=None, lock_tenant=None, hide_tenant=False, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', INPUT_CLASS)
        require_location_fields(self)
        apply_location_cascade_widgets(self)

        is_new = self.instance.pk is None
        if is_new:
            self.fields['password'].required = True
            apply_password_strength(self.fields['password'], help_text=f'Sets the login password for this account. {PASSWORD_HINT}')
        else:
            apply_password_strength(self.fields['password'], help_text=self.fields['password'].help_text)

        if hide_tenant:
            # Used when creating an organization and its first admin in one step —
            # there's no Tenant row yet to point the field at, so the view sets
            # `.tenant` on the saved instance itself once the org exists.
            del self.fields['tenant']
            if is_new:
                self.fields['role'].initial = User.Role.SYSTEM_ADMIN
                self.fields['role'].choices = [(User.Role.SYSTEM_ADMIN, User.Role.SYSTEM_ADMIN.label)]
        # A System Admin can only create/edit users within their own tenant, as Users.
        elif actor is not None and actor.role == User.Role.SYSTEM_ADMIN:
            self.fields['tenant'].queryset = Tenant.objects.filter(pk=actor.tenant_id)
            self.fields['tenant'].initial = actor.tenant_id
            self.fields['tenant'].disabled = True
            self.fields['role'].choices = [
                (User.Role.USER, User.Role.USER.label),
            ]

        # Owner creating the admin for a specific, just-created (or existing) organization.
        elif lock_tenant is not None:
            self.fields['tenant'].queryset = Tenant.objects.filter(pk=lock_tenant.pk)
            self.fields['tenant'].initial = lock_tenant.pk
            self.fields['tenant'].disabled = True
            if is_new:
                self.fields['role'].initial = User.Role.SYSTEM_ADMIN

    def save(self, commit=True):
        user = super().save(commit=False)
        raw_password = self.cleaned_data.get('password')
        if raw_password:
            user.set_password(raw_password)
        if commit:
            user.save()
        return user


class OTPVerificationForm(forms.Form):
    code = forms.CharField(
        min_length=6, max_length=6,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'placeholder': '123456',
        }),
    )

    def clean_code(self):
        code = self.cleaned_data['code'].strip()
        if not code.isdigit():
            raise forms.ValidationError('Enter the 6-digit code exactly as sent.')
        return code


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', INPUT_CLASS)
        apply_password_strength(self.fields['new_password1'])


class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', INPUT_CLASS)
        apply_password_strength(self.fields['new_password1'])
