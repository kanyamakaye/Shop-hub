from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.forms import AdminUserForm
from accounts.models import User
from subscriptions.models import SubscriptionPlan

from .forms import TenantForm
from .models import Tenant


@role_required(User.Role.SYSTEM_OWNER)
def tenant_list(request):
    tenants = Tenant.objects.select_related('plan').all()
    query = request.GET.get('q', '').strip()
    plan_id = request.GET.get('plan', '').strip()
    status = request.GET.get('status', '').strip()

    if query:
        tenants = tenants.filter(Q(business_name__icontains=query) | Q(email__icontains=query))
    if plan_id.isdigit():
        tenants = tenants.filter(plan_id=plan_id)
    if status:
        tenants = tenants.filter(status=status)

    querydict = request.GET.copy()
    querydict.pop('page', None)
    base_query = querydict.urlencode()

    paginator = Paginator(tenants, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'tenants/tenant_list.html', {
        'page_obj': page_obj, 'query': query, 'show_sidebar': True, 'base_query': base_query,
        'plans': SubscriptionPlan.objects.all(), 'plan_id': plan_id, 'status': status,
        'status_choices': Tenant.Status.choices,
    })


@role_required(User.Role.SYSTEM_OWNER)
def tenant_create(request):
    form = TenantForm(request.POST or None, request.FILES or None, prefix='org')
    admin_form = AdminUserForm(request.POST or None, hide_tenant=True, prefix='admin')
    if request.method == 'POST' and form.is_valid() and admin_form.is_valid():
        with transaction.atomic():
            tenant = form.save()
            admin = admin_form.save(commit=False)
            admin.tenant = tenant
            admin.save()
        messages.success(request, f'{tenant.business_name} created with an admin login for {admin.username}. Share the credentials with them so they can log in.')
        return redirect('tenants:detail', pk=tenant.pk)
    return render(request, 'tenants/tenant_form.html', {'form': form, 'admin_form': admin_form, 'show_sidebar': True})


@role_required(User.Role.SYSTEM_OWNER)
def tenant_update(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    form = TenantForm(request.POST or None, request.FILES or None, instance=tenant)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tenant updated.')
        return redirect('tenants:list')
    return render(request, 'tenants/tenant_form.html', {'form': form, 'tenant': tenant, 'show_sidebar': True})


@role_required(User.Role.SYSTEM_OWNER)
def tenant_detail(request, pk):
    tenant = get_object_or_404(Tenant.objects.select_related('plan'), pk=pk)
    admins = User.objects.filter(tenant=tenant, role=User.Role.SYSTEM_ADMIN)
    return render(request, 'tenants/tenant_detail.html', {'tenant': tenant, 'admins': admins, 'show_sidebar': True})


@role_required(User.Role.SYSTEM_OWNER)
def tenant_delete(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    if request.method == 'POST':
        tenant.delete()
        messages.success(request, 'Tenant deleted.')
        return redirect('tenants:list')
    return render(request, 'tenants/tenant_delete.html', {'tenant': tenant, 'show_sidebar': True})
