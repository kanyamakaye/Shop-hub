from datetime import datetime, time, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from accounts.models import User
from cart.models import Cart
from orders.models import Order, OrderItem
from products.models import Product
from reviews.models import Review
from subscriptions.models import SubscriptionPlan
from tenants.models import Tenant
from wishlist.models import Wishlist

MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


@login_required
def redirect_to_dashboard(request):
    role_to_url = {
        User.Role.SYSTEM_OWNER: 'dashboard:owner',
        User.Role.SYSTEM_ADMIN: 'dashboard:tenant',
        User.Role.USER: 'dashboard:customer',
    }
    return redirect(role_to_url.get(request.user.role, 'dashboard:customer'))


def _last_n_months(n=6):
    """Returns a list of (year, month) tuples for the last n months, oldest first."""
    today = timezone.now().date().replace(day=1)
    months = []
    for i in range(n - 1, -1, -1):
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1
        months.append((year, month))
    return months


def _day_start(date_obj):
    """Convert a plain date to a tz-aware midnight datetime. Filtering a DateTimeField
    with a naive date directly silently means 'midnight only' on that day, which
    undercounts anything that happened later that same day — always convert first."""
    return timezone.make_aware(datetime.combine(date_obj, time.min))


def _monthly_series(queryset, date_field, value_field=None):
    """Aggregates a queryset into a 6-month (label, value) series, filling in zero for empty months."""
    months = _last_n_months(6)
    start = timezone.now().date().replace(day=1) - timedelta(days=31 * 5)
    start = start.replace(day=1)
    annotated = (
        queryset.filter(**{f'{date_field}__gte': _day_start(start)})
        .annotate(month=TruncMonth(date_field))
        .values('month')
        .annotate(total=Sum(value_field) if value_field else Count('id'))
        .order_by('month')
    )
    lookup = {(item['month'].year, item['month'].month): item['total'] for item in annotated if item['month']}
    labels = [MONTH_LABELS[m - 1] for _, m in months]
    values = [int(lookup.get(key, 0) or 0) for key in months]
    return labels, values


def _percent_change(current, previous):
    if not previous:
        return None
    return round(((current - previous) / previous) * 100, 1)


def _this_and_last_month(queryset, date_field, value_field=None):
    now = timezone.now().date()
    this_month_start = now.replace(day=1)
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    def total_for(start, end):
        # __lte with a bare date means "up to midnight of that day", which would
        # silently exclude everything from later that day — use an exclusive
        # upper bound at the start of the following day instead.
        qs = queryset.filter(**{
            f'{date_field}__gte': _day_start(start),
            f'{date_field}__lt': _day_start(end + timedelta(days=1)),
        })
        if value_field:
            return qs.aggregate(total=Sum(value_field))['total'] or 0
        return qs.count()

    this_month = total_for(this_month_start, now)
    last_month = total_for(last_month_start, last_month_end)
    return this_month, _percent_change(this_month, last_month)


def _status_progress(queryset):
    """Ordered Pending->Cancelled breakdown with percentages, for a horizontal progress-bar panel."""
    counts = dict(queryset.values_list('order_status').annotate(c=Count('id')))
    total = sum(counts.values())
    rows = []
    for value, label in Order.OrderStatus.choices:
        count = counts.get(value, 0)
        percent = round((count / total) * 100, 1) if total else 0
        rows.append({'label': label, 'count': count, 'percent': percent})
    return rows, total


@role_required(User.Role.SYSTEM_OWNER)
def owner_dashboard(request):
    paid_orders = Order.objects.filter(payment_status=Order.PaymentStatus.PAID)
    # Only the month-over-month percentage is used here — the raw totals below are all-time.
    _, revenue_change = _this_and_last_month(paid_orders, 'order_date', 'total_amount')
    _, tenants_change = _this_and_last_month(Tenant.objects.all(), 'created_at')

    revenue_labels, revenue_values = _monthly_series(paid_orders, 'order_date', 'total_amount')

    plan_distribution = list(
        Tenant.objects.values('plan__plan_name').annotate(count=Count('id')).order_by('-count')
    )
    total_tenants = Tenant.objects.count()
    for row in plan_distribution:
        row['label'] = row.pop('plan__plan_name') or 'No plan'
        row['percent'] = round((row['count'] / total_tenants) * 100, 1) if total_tenants else 0

    total_revenue = paid_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    total_orders = paid_orders.count()
    avg_order_value = round(total_revenue / total_orders) if total_orders else 0

    top_tenants = list(
        paid_orders.values('tenant__id', 'tenant__business_name')
        .annotate(revenue=Sum('total_amount'), orders=Count('id'))
        .order_by('-revenue')[:5]
    )

    active_tenants = Tenant.objects.filter(status=Tenant.Status.ACTIVE).count()
    active_users = User.objects.filter(status=User.Status.ACTIVE).count()
    context = {
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'organizations_display': f"{active_tenants} / {total_tenants}",
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'paid_orders_sub': f"avg {avg_order_value:,} RWF",
        'avg_order_sub': f"across {total_orders} paid orders",
        'active_plans': SubscriptionPlan.objects.filter(status=SubscriptionPlan.Status.ACTIVE).count(),
        'active_users': active_users,
        'platform_wishlist_count': Wishlist.objects.count(),
        'platform_cart_count': Cart.objects.count(),
        'banner_subtitle': f"{total_tenants} organizations · {active_users} users",
        'recent_tenants': Tenant.objects.select_related('plan').order_by('-created_at')[:5],
        'top_tenants': top_tenants,
        'plan_distribution': plan_distribution,
        'revenue_change': revenue_change,
        'tenants_change': tenants_change,
        'revenue_labels': revenue_labels,
        'revenue_values': revenue_values,
        'show_sidebar': True,
    }
    return render(request, 'dashboard/owner_dashboard.html', context)


@role_required(User.Role.SYSTEM_ADMIN)
def tenant_dashboard(request):
    tenant_id = request.user.tenant_id
    orders = Order.objects.filter(tenant_id=tenant_id)
    paid_orders = orders.filter(payment_status=Order.PaymentStatus.PAID)

    # Only the month-over-month percentage is used here — the raw totals below are all-time.
    _, revenue_change = _this_and_last_month(paid_orders, 'order_date', 'total_amount')
    _, orders_change = _this_and_last_month(orders, 'order_date')

    revenue_labels, revenue_values = _monthly_series(paid_orders, 'order_date', 'total_amount')
    status_rows, status_total = _status_progress(orders)

    order_count = orders.count()
    revenue = paid_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    sales_count = paid_orders.count()
    avg_order_value = round(revenue / sales_count) if sales_count else 0

    top_products = list(
        OrderItem.objects.filter(order__tenant_id=tenant_id)
        .values('product__id', 'product__product_name')
        .annotate(qty=Sum('quantity'), revenue=Sum(F('unit_price') * F('quantity')))
        .order_by('-revenue')[:5]
    )
    product_count = Product.objects.filter(tenant_id=tenant_id).count()

    context = {
        'product_count': product_count,
        'order_count': order_count,
        'customer_count': User.objects.filter(tenant_id=tenant_id, role=User.Role.USER).count(),
        'sales_count': sales_count,
        'sales_sub': f"avg {avg_order_value:,} RWF",
        'revenue': revenue,
        'avg_order_value': avg_order_value,
        'wishlist_count': Wishlist.objects.filter(product__tenant_id=tenant_id).count(),
        'cart_count': Cart.objects.filter(product__tenant_id=tenant_id).count(),
        'recent_orders': orders.select_related('user').order_by('-order_date')[:5],
        'top_products': top_products,
        'status_rows': status_rows,
        'status_total': status_total,
        'revenue_change': revenue_change,
        'orders_change': orders_change,
        'revenue_labels': revenue_labels,
        'revenue_values': revenue_values,
        'banner_subtitle': f"{product_count} products · {order_count} orders",
        'show_sidebar': True,
    }
    return render(request, 'dashboard/tenant_dashboard.html', context)


@role_required(User.Role.USER)
def customer_dashboard(request):
    orders = Order.objects.filter(user=request.user)
    status_rows, status_total = _status_progress(orders)
    order_labels, order_values = _monthly_series(orders, 'order_date')
    order_count = orders.count()
    wishlist_count = Wishlist.objects.filter(user=request.user).count()

    context = {
        'order_count': order_count,
        'wishlist_count': wishlist_count,
        'cart_count': Cart.objects.filter(user=request.user).count(),
        'review_count': Review.objects.filter(user=request.user).count(),
        'notification_count': request.user.notifications.filter(is_read=False).count(),
        'recent_orders': orders.select_related('tenant').order_by('-order_date')[:5],
        'status_rows': status_rows,
        'status_total': status_total,
        'order_labels': order_labels,
        'order_values': order_values,
        'banner_title': f"Welcome, {request.user.first_name or request.user.username}",
        'banner_subtitle': f"{order_count} orders · {wishlist_count} wishlist items",
        'show_sidebar': True,
    }
    return render(request, 'dashboard/customer_dashboard.html', context)
