from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User
from products.models import Product

from .models import Cart
from .utils import group_items_by_store


@role_required(User.Role.USER)
def cart_list(request):
    items = list(Cart.objects.filter(user=request.user).select_related('product', 'product__tenant'))
    store_groups = group_items_by_store(items)
    total = sum((item.subtotal for item in items), 0)
    grand_total_estimate = sum((g['estimated_total'] for g in store_groups), 0)
    return render(request, 'cart/cart.html', {
        'items': items, 'store_groups': store_groups,
        'total': total, 'grand_total_estimate': grand_total_estimate,
        'show_sidebar': True,
    })


@role_required(User.Role.SYSTEM_OWNER, User.Role.SYSTEM_ADMIN)
def cart_overview(request):
    """Read-only view of active carts: platform-wide for the Owner, store-scoped for a System Admin."""
    is_owner = request.user.role == User.Role.SYSTEM_OWNER
    scoped_items = Cart.objects.all()
    if not is_owner:
        scoped_items = scoped_items.filter(product__tenant_id=request.user.tenant_id)

    stats = scoped_items.aggregate(
        total_carts=Count('user', distinct=True),
        total_items=Sum('quantity'),
        estimated_value=Sum(F('quantity') * Coalesce('product__discount_price', 'product__price')),
    )

    items = scoped_items.select_related('user', 'product', 'product__tenant').order_by('-added_date')
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
    title = 'Platform Carts' if is_owner else f"{request.user.tenant.business_name} Carts"
    return render(request, 'cart/cart_overview.html', {
        'page_obj': page_obj,
        'query': query,
        'title': title,
        'is_owner': is_owner,
        'show_sidebar': True,
        'stats': stats,
    })


@role_required(User.Role.USER)
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, status=Product.Status.ACTIVE)
    if product.is_out_of_stock:
        messages.warning(request, f'{product.product_name} is out of stock.')
        return redirect('products:detail', pk=product.pk)

    quantity = max(1, int(request.POST.get('quantity', 1)))
    item, created = Cart.objects.get_or_create(user=request.user, product=product, defaults={'quantity': quantity})
    if not created:
        item.quantity += quantity
        item.save()
    if item.quantity > product.stock_quantity:
        item.quantity = product.stock_quantity
        item.save()
        messages.warning(request, f'Only {product.stock_quantity} of {product.product_name} in stock — your cart was capped at that amount.')
    else:
        messages.success(request, f'{product.product_name} added to cart.')
    return redirect('cart:list')


@role_required(User.Role.USER)
@require_POST
def update_cart(request, pk):
    item = get_object_or_404(Cart, pk=pk, user=request.user)
    quantity = int(request.POST.get('quantity', item.quantity))
    if quantity < 1:
        item.delete()
        messages.success(request, 'Item removed from cart.')
    elif quantity > item.product.stock_quantity:
        item.quantity = item.product.stock_quantity
        item.save()
        messages.warning(request, f'Only {item.product.stock_quantity} of {item.product.product_name} in stock — capped at that amount.')
    else:
        item.quantity = quantity
        item.save()
        messages.success(request, 'Cart updated.')
    return redirect('cart:list')


@role_required(User.Role.USER)
@require_POST
def remove_cart(request, pk):
    item = get_object_or_404(Cart, pk=pk, user=request.user)
    item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart:list')
