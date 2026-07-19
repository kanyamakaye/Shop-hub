from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User
from products.models import Product

from .models import Wishlist


@role_required(User.Role.USER)
def wishlist(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product', 'product__tenant')
    return render(request, 'wishlist/wishlist.html', {'items': items, 'show_sidebar': True})


@role_required(User.Role.SYSTEM_OWNER, User.Role.SYSTEM_ADMIN)
def wishlist_overview(request):
    """Read-only view of wishlist activity: platform-wide for the Owner, store-scoped for a System Admin."""
    is_owner = request.user.role == User.Role.SYSTEM_OWNER
    items = Wishlist.objects.select_related('user', 'product', 'product__tenant').order_by('-added_date')
    if not is_owner:
        items = items.filter(product__tenant_id=request.user.tenant_id)

    query = request.GET.get('q', '').strip()
    if query:
        items = items.filter(
            Q(product__product_name__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
        )

    paginator = Paginator(items, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    title = 'Platform Wishlist Activity' if is_owner else f"{request.user.tenant.business_name} Wishlist Activity"
    return render(request, 'wishlist/wishlist_overview.html', {
        'page_obj': page_obj,
        'query': query,
        'title': title,
        'is_owner': is_owner,
        'show_sidebar': True,
    })


@role_required(User.Role.USER)
@require_POST
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, status=Product.Status.ACTIVE)
    _, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    messages.success(request, 'Added to wishlist.' if created else 'Already in your wishlist.')
    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(referer)
    return redirect('wishlist:list')


@role_required(User.Role.USER)
@require_POST
def wishlist_remove(request, pk):
    item = get_object_or_404(Wishlist, pk=pk, user=request.user)
    item.delete()
    messages.success(request, 'Removed from wishlist.')
    return redirect('wishlist:list')
