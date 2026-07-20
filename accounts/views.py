from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordChangeDoneView, PasswordChangeView,
    PasswordResetCompleteView, PasswordResetConfirmView,
    PasswordResetDoneView, PasswordResetView,
)
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from config.csv_utils import csv_response
from tenants.models import Tenant

from .decorators import role_required
from .forms import (
    AdminUserForm, OTPVerificationForm, ProfileForm, RegisterForm,
    StyledAuthenticationForm, StyledPasswordChangeForm, StyledPasswordResetForm,
    StyledSetPasswordForm,
)
from .models import EmailOTP, User


def _send_otp_email(user, code):
    send_mail(
        'Your ShopHub login code',
        f'Hi {user.first_name or user.username},\n\n'
        f'Your ShopHub login code is: {code}\n\n'
        f'This code expires in {settings.OTP_EXPIRY_MINUTES} minutes. '
        'If you did not try to log in, you can safely ignore this email.\n\n'
        '— The ShopHub team',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )


def _begin_session_or_challenge(request, user, backend, welcome_message):
    """Log the user straight in if they have no email on file (nothing to
    verify an OTP against); otherwise stash a pending challenge in the
    session and require a code before establishing the real session."""
    if not user.email:
        auth_login(request, user, backend=backend)
        messages.success(request, welcome_message)
        return redirect('dashboard:redirect')

    request.session.cycle_key()
    otp, raw_code = EmailOTP.generate_for(user)
    _send_otp_email(user, raw_code)
    request.session['pending_2fa_user_id'] = user.pk
    request.session['pending_2fa_backend'] = backend
    request.session['pending_2fa_welcome_message'] = welcome_message
    return redirect('accounts:verify_otp')


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:redirect')
    form = StyledAuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        welcome_message = f'Welcome back, {user.first_name or user.username}!'
        return _begin_session_or_challenge(request, user, user.backend, welcome_message)
    return render(request, 'accounts/login.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def verify_otp_view(request):
    user_id = request.session.get('pending_2fa_user_id')
    backend = request.session.get('pending_2fa_backend')
    welcome_message = request.session.get('pending_2fa_welcome_message', 'Welcome back!')
    if not user_id or not backend:
        messages.error(request, 'Please log in again.')
        return redirect('accounts:login')

    try:
        user = User.objects.get(pk=user_id, status=User.Status.ACTIVE)
    except User.DoesNotExist:
        request.session.pop('pending_2fa_user_id', None)
        request.session.pop('pending_2fa_backend', None)
        request.session.pop('pending_2fa_welcome_message', None)
        messages.error(request, 'Please log in again.')
        return redirect('accounts:login')

    otp = EmailOTP.objects.filter(
        user=user, is_used=False, expires_at__gt=timezone.now(),
    ).order_by('-created_at').first()

    form = OTPVerificationForm(request.POST or None)
    if request.method == 'POST':
        if otp is None:
            messages.error(request, 'That code has expired. Request a new one below.')
        elif form.is_valid() and otp.verify_code(form.cleaned_data['code']):
            request.session.pop('pending_2fa_user_id', None)
            request.session.pop('pending_2fa_backend', None)
            request.session.pop('pending_2fa_welcome_message', None)
            auth_login(request, user, backend=backend)
            messages.success(request, welcome_message)
            return redirect('dashboard:redirect')
        elif form.is_valid():
            if otp.attempts > settings.OTP_MAX_ATTEMPTS:
                messages.error(request, 'Too many incorrect attempts. Request a new code below.')
            else:
                form.add_error('code', 'Incorrect code.')

    domain = user.email.split('@', 1)[1] if '@' in user.email else ''
    masked_email = f'{user.email[0]}***@{domain}'
    return render(request, 'accounts/verify_otp.html', {
        'form': form, 'masked_email': masked_email, 'otp_expired': otp is None,
    })


@require_http_methods(['POST'])
def resend_otp_view(request):
    user_id = request.session.get('pending_2fa_user_id')
    if not user_id:
        messages.error(request, 'Please log in again.')
        return redirect('accounts:login')

    try:
        user = User.objects.get(pk=user_id, status=User.Status.ACTIVE)
    except User.DoesNotExist:
        request.session.pop('pending_2fa_user_id', None)
        request.session.pop('pending_2fa_backend', None)
        request.session.pop('pending_2fa_welcome_message', None)
        messages.error(request, 'Please log in again.')
        return redirect('accounts:login')

    last_otp = EmailOTP.objects.filter(user=user).order_by('-created_at').first()
    if last_otp and timezone.now() - last_otp.created_at < timedelta(seconds=settings.OTP_RESEND_COOLDOWN_SECONDS):
        messages.error(request, 'Please wait a bit before requesting another code.')
        return redirect('accounts:verify_otp')

    otp, raw_code = EmailOTP.generate_for(user)
    _send_otp_email(user, raw_code)
    messages.success(request, 'A new code was sent to your email.')
    return redirect('accounts:verify_otp')


@require_http_methods(['POST'])
def logout_view(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home:index')


def _send_welcome_email(user):
    if not user.email:
        return
    send_mail(
        'Welcome to ShopHub — your account is ready',
        f'Hi {user.first_name or user.username},\n\n'
        'Your ShopHub account has been created. Here are your login details:\n\n'
        f'Username: {user.username}\n'
        f'Email: {user.email}\n\n'
        'Use the password you set during sign-up to log in at any time.\n\n'
        '— The ShopHub team',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )


@require_http_methods(['GET', 'POST'])
def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:redirect')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        _send_welcome_email(user)
        return _begin_session_or_challenge(
            request, user, 'accounts.backends.EmailOrUsernameModelBackend',
            'Welcome to ShopHub! Your account has been created.',
        )
    return render(request, 'accounts/register.html', {'form': form})


class StyledPasswordResetView(PasswordResetView):
    template_name = 'accounts/forgot_password.html'
    email_template_name = 'accounts/password_reset_email.txt'
    success_url = reverse_lazy('accounts:password_reset_done')
    form_class = StyledPasswordResetForm


class StyledPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class StyledPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    form_class = StyledSetPasswordForm


class StyledPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


class StyledPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('accounts:change_password_done')
    form_class = StyledPasswordChangeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_sidebar'] = True
        return context


class StyledPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'accounts/change_password_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_sidebar'] = True
        return context


@login_required
def user_profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated.')
        return redirect('accounts:profile')
    return render(request, 'accounts/user_profile.html', {'form': form, 'show_sidebar': True})


def _visible_users(user):
    if user.role == User.Role.SYSTEM_OWNER:
        return User.objects.select_related('tenant').all()
    return User.objects.select_related('tenant').filter(tenant_id=user.tenant_id)


@role_required(User.Role.SYSTEM_OWNER, User.Role.SYSTEM_ADMIN)
def user_list(request):
    users = _visible_users(request.user).order_by('-created_at')
    query = request.GET.get('q', '').strip()
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )
    filter_tenant = None
    tenant_param = request.GET.get('tenant', '').strip()
    if request.user.role == User.Role.SYSTEM_OWNER and tenant_param.isdigit():
        filter_tenant = get_object_or_404(Tenant, pk=tenant_param)
        users = users.filter(tenant_id=filter_tenant.pk)

    role = request.GET.get('role', '').strip()
    status = request.GET.get('status', '').strip()
    if role:
        users = users.filter(role=role)
    if status:
        users = users.filter(status=status)

    if request.GET.get('export') == 'csv':
        rows = (
            [u.username, u.get_full_name(), u.email, u.role, u.tenant.business_name if u.tenant else '', u.status]
            for u in users
        )
        return csv_response('users.csv', ['Username', 'Full Name', 'Email', 'Role', 'Organization', 'Status'], rows)

    querydict = request.GET.copy()
    querydict.pop('page', None)
    base_query = querydict.urlencode()

    paginator = Paginator(users, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounts/user_list.html', {
        'page_obj': page_obj, 'query': query, 'filter_tenant': filter_tenant, 'show_sidebar': True,
        'base_query': base_query, 'role': role, 'status': status,
        'role_choices': User.Role.choices, 'status_choices': User.Status.choices,
    })


@role_required(User.Role.SYSTEM_OWNER, User.Role.SYSTEM_ADMIN)
def user_create(request):
    lock_tenant = None
    tenant_param = request.GET.get('tenant', '').strip()
    if request.user.role == User.Role.SYSTEM_OWNER and tenant_param.isdigit():
        lock_tenant = get_object_or_404(Tenant, pk=tenant_param)

    form = AdminUserForm(request.POST or None, actor=request.user, lock_tenant=lock_tenant)
    if request.method == 'POST' and form.is_valid():
        form.save()
        if lock_tenant:
            messages.success(request, f'Admin account created for {lock_tenant.business_name}. Share the username and password with them so they can log in.')
            return redirect('tenants:detail', pk=lock_tenant.pk)
        messages.success(request, 'User created.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'lock_tenant': lock_tenant, 'show_sidebar': True})


@role_required(User.Role.SYSTEM_OWNER, User.Role.SYSTEM_ADMIN)
def user_update(request, pk):
    target = get_object_or_404(_visible_users(request.user), pk=pk)
    form = AdminUserForm(request.POST or None, instance=target, actor=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'User updated.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'target': target, 'show_sidebar': True})


@role_required(User.Role.SYSTEM_OWNER, User.Role.SYSTEM_ADMIN)
def user_delete(request, pk):
    target = get_object_or_404(_visible_users(request.user), pk=pk)
    if request.method == 'POST':
        target.delete()
        messages.success(request, 'User deleted.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_delete.html', {'target': target, 'show_sidebar': True})
