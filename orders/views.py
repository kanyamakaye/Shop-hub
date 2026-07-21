from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User
from cart.models import Cart
from cart.utils import group_items_by_store
from config.csv_utils import csv_response
from config.query_utils import is_decimal_string
from coupons.models import Coupon
from notifications.models import Notification
from notifications.services import notify
from products.models import Product

from .forms import CheckoutForm, OrderStatusForm, ReturnRequestForm
from .models import Order, OrderItem


def _visible_orders(user):
    if user.role == User.Role.SYSTEM_ADMIN:
        return Order.objects.filter(tenant_id=user.tenant_id)
    if user.role == User.Role.USER:
        return Order.objects.filter(user=user)
    return Order.objects.all()


def _send_mail_silently(subject, message, recipient):
    if not recipient:
        return
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=True)


@role_required(User.Role.SYSTEM_ADMIN, User.Role.USER, User.Role.SYSTEM_OWNER)
def order_list(request):
    base_orders = _visible_orders(request.user)
    stats = None
    if request.user.role != User.Role.USER:
        stats = base_orders.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(order_status=Order.OrderStatus.PENDING)),
            revenue=Sum('total_amount', filter=Q(payment_status=Order.PaymentStatus.PAID)),
        )
    orders = base_orders.select_related('tenant', 'user')

    order_status = request.GET.get('order_status', '').strip()
    payment_status = request.GET.get('payment_status', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    min_total = request.GET.get('min_total', '').strip()
    max_total = request.GET.get('max_total', '').strip()

    if order_status:
        orders = orders.filter(order_status=order_status)
    if payment_status:
        orders = orders.filter(payment_status=payment_status)
    if date_from:
        orders = orders.filter(order_date__date__gte=date_from)
    if date_to:
        orders = orders.filter(order_date__date__lte=date_to)
    if is_decimal_string(min_total):
        orders = orders.filter(total_amount__gte=min_total)
    if is_decimal_string(max_total):
        orders = orders.filter(total_amount__lte=max_total)

    if request.GET.get('export') == 'csv':
        rows = (
            [
                o.pk, o.order_date.strftime('%Y-%m-%d %H:%M'), o.tenant.business_name,
                o.user.get_full_name() or o.user.username, o.subtotal_amount, o.discount_amount,
                o.tax_amount, o.shipping_amount, o.total_amount, o.payment_method,
                o.payment_status, o.order_status,
            ]
            for o in orders
        )
        return csv_response('orders.csv', [
            'Order #', 'Date', 'Store', 'Customer', 'Subtotal (RWF)', 'Discount (RWF)',
            'Tax (RWF)', 'Shipping (RWF)', 'Total (RWF)', 'Payment Method', 'Payment Status', 'Order Status',
        ], rows)
    querydict = request.GET.copy()
    querydict.pop('page', None)
    base_query = querydict.urlencode()

    paginator = Paginator(orders, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'orders/order_list.html', {
        'page_obj': page_obj, 'show_sidebar': True, 'base_query': base_query, 'stats': stats,
        'order_status': order_status, 'payment_status': payment_status,
        'date_from': date_from, 'date_to': date_to, 'min_total': min_total, 'max_total': max_total,
        'order_status_choices': Order.OrderStatus.choices, 'payment_status_choices': Order.PaymentStatus.choices,
    })


@role_required(User.Role.SYSTEM_ADMIN, User.Role.USER, User.Role.SYSTEM_OWNER)
def order_detail(request, pk):
    order = get_object_or_404(_visible_orders(request.user).select_related('tenant', 'user').prefetch_related('items__product'), pk=pk)
    status_form = None
    if request.user.role == User.Role.SYSTEM_ADMIN:
        status_form = OrderStatusForm(request.POST or None, instance=order)
        if request.method == 'POST' and 'order_status' in request.POST and status_form.is_valid():
            status_form.save()
            notify(
                order.user, 'Order status updated',
                f'Your order #{order.pk} is now {order.order_status}.',
                Notification.NotificationType.ORDER, tenant=order.tenant,
            )
            _send_mail_silently(
                f'Order #{order.pk} update',
                f'Your order #{order.pk} is now {order.order_status}.',
                order.user.email,
            )
            messages.success(request, 'Order updated.')
            return redirect('orders:detail', pk=order.pk)
    return_form = ReturnRequestForm(request.POST or None) if request.user.role == User.Role.USER else None
    return render(request, 'orders/order_detail.html', {
        'order': order, 'status_form': status_form, 'return_form': return_form, 'show_sidebar': True,
    })


@role_required(User.Role.USER)
def request_return(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.order_status != Order.OrderStatus.DELIVERED:
        messages.error(request, 'Only delivered orders can be returned.')
        return redirect('orders:detail', pk=order.pk)
    form = ReturnRequestForm(request.POST or None, instance=order)
    if request.method == 'POST' and form.is_valid():
        order = form.save(commit=False)
        order.order_status = Order.OrderStatus.RETURN_REQUESTED
        order.save()
        for admin in User.objects.filter(tenant_id=order.tenant_id, role=User.Role.SYSTEM_ADMIN):
            notify(
                admin, 'Return requested',
                f'{request.user.get_full_name() or request.user.username} requested a return for order #{order.pk}.',
                Notification.NotificationType.ORDER, tenant=order.tenant,
            )
            _send_mail_silently(f'Return requested — order #{order.pk}', order.return_reason, admin.email)
        messages.success(request, 'Return requested. The store will review it shortly.')
    return redirect('orders:detail', pk=order.pk)


@role_required(User.Role.SYSTEM_ADMIN)
def process_return(request, pk):
    order = get_object_or_404(Order, pk=pk, tenant_id=request.user.tenant_id)
    if order.order_status != Order.OrderStatus.RETURN_REQUESTED:
        messages.error(request, 'This order has no pending return request.')
        return redirect('orders:detail', pk=order.pk)
    if request.method == 'POST':
        decision = request.POST.get('decision')
        if decision == 'approve':
            order.order_status = Order.OrderStatus.RETURNED
            order.save(update_fields=['order_status'])
            for item in order.items.select_related('product'):
                Product.objects.filter(pk=item.product_id).update(stock_quantity=F('stock_quantity') + item.quantity)
            notify(order.user, 'Return approved', f'Your return for order #{order.pk} was approved.', Notification.NotificationType.ORDER, tenant=order.tenant)
            _send_mail_silently(f'Return approved — order #{order.pk}', 'Your return has been approved.', order.user.email)
            messages.success(request, 'Return approved and stock restored.')
        else:
            order.order_status = Order.OrderStatus.DELIVERED
            order.save(update_fields=['order_status'])
            notify(order.user, 'Return rejected', f'Your return for order #{order.pk} was not approved.', Notification.NotificationType.ORDER, tenant=order.tenant)
            _send_mail_silently(f'Return rejected — order #{order.pk}', 'Your return request was not approved.', order.user.email)
            messages.success(request, 'Return rejected.')
    return redirect('orders:detail', pk=order.pk)


def _apply_coupon(tenant, subtotal, coupon_code):
    """Try to redeem `coupon_code` against one store's subtotal.
    Returns (coupon_or_None, discount_amount, problem_message_or_None)."""
    if not coupon_code:
        return None, 0, None
    candidate = Coupon.objects.filter(tenant=tenant, code=coupon_code).first()
    if candidate is None:
        return None, 0, 'Coupon code not recognized for one or more stores in your cart.'
    valid, reason = candidate.is_valid_for(subtotal)
    if not valid:
        return None, 0, reason
    return candidate, candidate.compute_discount(subtotal), None


def _create_order_for_group(group, user, coupon_code, payment_method, shipping_address):
    """Creates one Order (+ its OrderItems) for a single store's cart items and
    decrements stock. Returns (order, newly_low_or_out_of_stock_products, coupon_problem_or_None)."""
    tenant = group['tenant']
    subtotal = group['subtotal']
    coupon, discount, coupon_note = _apply_coupon(tenant, subtotal, coupon_code)
    tax = round(subtotal * tenant.tax_rate / 100, 2)
    shipping = tenant.shipping_fee

    order = Order.objects.create(
        tenant=tenant,
        user=user,
        subtotal_amount=subtotal,
        discount_amount=discount,
        tax_amount=tax,
        shipping_amount=shipping,
        total_amount=subtotal - discount + tax + shipping,
        coupon=coupon,
        payment_method=payment_method,
        payment_status=Order.PaymentStatus.PENDING,
        order_status=Order.OrderStatus.PENDING,
        shipping_address=shipping_address,
    )
    if coupon:
        Coupon.objects.filter(pk=coupon.pk).update(used_count=F('used_count') + 1)

    low_stock_products = []
    for item in group['items']:
        OrderItem.objects.create(
            order=order, product=item.product,
            quantity=item.quantity, unit_price=item.product.display_price,
        )
        Product.objects.filter(pk=item.product_id).update(stock_quantity=F('stock_quantity') - item.quantity)
        item.product.refresh_from_db(fields=['stock_quantity'])
        if item.product.is_low_stock or item.product.is_out_of_stock:
            low_stock_products.append(item.product)

    return order, low_stock_products, coupon_note


def _notify_new_order(order, buyer, low_stock_products):
    """Notifies the buyer, the store's admins, and flags any products that just ran low."""
    tenant = order.tenant
    notify(
        buyer, 'Order placed',
        f'Your order #{order.pk} for {order.total_amount:,.0f} RWF has been placed.',
        Notification.NotificationType.ORDER, tenant=tenant,
    )
    _send_mail_silently(
        f'Order confirmation — #{order.pk}',
        f'Thanks for your order! #{order.pk} totalling {order.total_amount:,.0f} RWF has been placed with {tenant.business_name}.',
        buyer.email,
    )

    admins = list(User.objects.filter(tenant_id=tenant.pk, role=User.Role.SYSTEM_ADMIN))
    for admin in admins:
        notify(
            admin, 'New order',
            f'Order #{order.pk} has been placed by {buyer.get_full_name() or buyer.username}.',
            Notification.NotificationType.ORDER, tenant=tenant,
        )
        _send_mail_silently(f'New order — #{order.pk}', f'A new order #{order.pk} was placed.', admin.email)

    for product in low_stock_products:
        level = 'out of stock' if product.is_out_of_stock else f'only {product.stock_quantity} left'
        for admin in admins:
            notify(
                admin, 'Low stock alert', f'{product.product_name} is {level}.',
                Notification.NotificationType.GENERAL, tenant=tenant,
            )
            _send_mail_silently(f'Low stock — {product.product_name}', f'{product.product_name} is {level}.', admin.email)


@role_required(User.Role.USER)
def checkout(request):
    items = list(Cart.objects.filter(user=request.user).select_related('product', 'product__tenant'))
    if not items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart:list')

    store_groups = group_items_by_store(items)
    grand_total_estimate = sum((g['estimated_total'] for g in store_groups), 0)

    form = CheckoutForm(request.POST or None, initial={'shipping_address': request.user.postal_address})

    if request.method == 'POST' and form.is_valid():
        coupon_code = form.cleaned_data.get('coupon_code', '')
        coupon_note = None
        with transaction.atomic():
            created_orders = []
            for group in store_groups:
                order, low_stock_products, group_coupon_note = _create_order_for_group(
                    group, request.user, coupon_code,
                    form.cleaned_data['payment_method'], form.cleaned_data['shipping_address'],
                )
                # A later group's success should never clear an earlier group's warning.
                coupon_note = group_coupon_note or coupon_note
                created_orders.append(order)
                _notify_new_order(order, request.user, low_stock_products)

            Cart.objects.filter(user=request.user).delete()

        if coupon_note:
            messages.warning(request, coupon_note)
        messages.success(request, 'Order placed successfully.')
        if len(created_orders) == 1:
            return redirect('orders:detail', pk=created_orders[0].pk)
        return redirect('orders:list')

    return render(request, 'orders/checkout.html', {
        'store_groups': store_groups,
        'grand_total_estimate': grand_total_estimate,
        'form': form,
        'show_sidebar': True,
    })
