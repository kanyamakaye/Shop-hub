from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User

from .forms import CouponForm
from .models import Coupon


@role_required(User.Role.SYSTEM_ADMIN)
def coupon_list(request):
    coupons = Coupon.objects.filter(tenant_id=request.user.tenant_id)
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    discount_type = request.GET.get('discount_type', '').strip()

    if query:
        coupons = coupons.filter(Q(code__icontains=query))
    if status:
        coupons = coupons.filter(status=status)
    if discount_type:
        coupons = coupons.filter(discount_type=discount_type)

    querydict = request.GET.copy()
    querydict.pop('page', None)
    base_query = querydict.urlencode()

    paginator = Paginator(coupons, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'coupons/coupon_list.html', {
        'page_obj': page_obj, 'query': query, 'show_sidebar': True, 'base_query': base_query,
        'status': status, 'discount_type': discount_type,
        'status_choices': Coupon.Status.choices, 'discount_type_choices': Coupon.DiscountType.choices,
    })


@role_required(User.Role.SYSTEM_ADMIN)
def coupon_create(request):
    form = CouponForm(request.POST or None, tenant=request.user.tenant)
    if request.method == 'POST' and form.is_valid():
        coupon = form.save(commit=False)
        coupon.tenant_id = request.user.tenant_id
        coupon.save()
        messages.success(request, f'Coupon {coupon.code} created.')
        return redirect('coupons:list')
    return render(request, 'coupons/coupon_form.html', {'form': form, 'show_sidebar': True})


@role_required(User.Role.SYSTEM_ADMIN)
def coupon_update(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk, tenant_id=request.user.tenant_id)
    form = CouponForm(request.POST or None, instance=coupon, tenant=request.user.tenant)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Coupon updated.')
        return redirect('coupons:list')
    return render(request, 'coupons/coupon_form.html', {'form': form, 'coupon': coupon, 'show_sidebar': True})


@role_required(User.Role.SYSTEM_ADMIN)
def coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk, tenant_id=request.user.tenant_id)
    if request.method == 'POST':
        coupon.delete()
        messages.success(request, 'Coupon deleted.')
        return redirect('coupons:list')
    return render(request, 'coupons/coupon_delete.html', {'coupon': coupon, 'show_sidebar': True})
