import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from coupons.models import Coupon
from notifications.models import Notification
from orders.models import Order, OrderItem
from products.models import Product
from reviews.models import Review
from tenants.models import Tenant

DEMO_PASSWORD = 'Passw0rd!'

FIRST_NAMES = [
    'Jean', 'Marie', 'Eric', 'Claudine', 'Emmanuel', 'Divine', 'Aline', 'Yvan', 'Solange', 'Fabrice',
    'Grace', 'Olivier', 'Josiane', 'Innocent', 'Clarisse', 'Vincent', 'Chantal', 'Bruce', 'Vanessa', 'Herve',
    'Aimee', 'Christian', 'Nadine', 'Patrick', 'Sandrine', 'Cedric', 'Belise', 'Theogene', 'Lea', 'Marcel',
    'Wanjiru', 'Otieno', 'Amina', 'Kofi', 'Zawadi', 'Adaeze', 'Kwame', 'Nia', 'Tunde', 'Fatima',
]
LAST_NAMES = [
    'Uwimana', 'Mukamana', 'Niyonsenga', 'Habimana', 'Uwase', 'Ishimwe', 'Nkurunziza', 'Mugisha', 'Ingabire', 'Bizimana',
    'Kayitesi', 'Nsengimana', 'Umutoni', 'Hakizimana', 'Iradukunda', 'Twagirayezu', 'Mutesi', 'Ndayisenga', 'Uwera', 'Nzeyimana',
    'Otieno', 'Wanjiru', 'Mensah', 'Okafor', 'Abara', 'Kimani', 'Njoroge', 'Chukwu', 'Adeyemi', 'Diallo',
]
DISTRICTS = ['Gasabo', 'Kicukiro', 'Nyarugenge', 'Musanze', 'Huye', 'Rubavu', 'Rwamagana', 'Muhanga']
PROVINCES = ['Kigali City', 'Northern', 'Southern', 'Western', 'Eastern']

REVIEW_COMMENTS = [
    'Great quality, exactly as described. Would buy again.',
    'Fast delivery and the product works perfectly.',
    'Good value for the price. Happy with this purchase.',
    'Decent product but packaging could be better.',
    'Exceeded my expectations, very satisfied!',
    'Solid choice, does what it says.',
    'Nice finish and comfortable to use daily.',
    'Works well, matches the photos on the listing.',
    "It's okay, took a bit longer to arrive than expected.",
    'Excellent customer service and quick response from the store.',
]

ORDER_STATUS_WEIGHTS = [
    (Order.OrderStatus.PENDING, 10),
    (Order.OrderStatus.PROCESSING, 15),
    (Order.OrderStatus.SHIPPED, 15),
    (Order.OrderStatus.DELIVERED, 45),
    (Order.OrderStatus.RETURN_REQUESTED, 3),
    (Order.OrderStatus.RETURNED, 5),
    (Order.OrderStatus.CANCELLED, 7),
]
PAYMENT_STATUS_BY_ORDER_STATUS = {
    Order.OrderStatus.PENDING: [(Order.PaymentStatus.PENDING, 80), (Order.PaymentStatus.PAID, 20)],
    Order.OrderStatus.CANCELLED: [(Order.PaymentStatus.FAILED, 60), (Order.PaymentStatus.PENDING, 40)],
}


def weighted_choice(pairs):
    values, weights = zip(*pairs)
    return random.choices(values, weights=weights, k=1)[0]


class Command(BaseCommand):
    help = 'Seeds a large batch of realistic demo activity: customers, coupons, stock variety, orders (with tax/shipping/discount), returns, reviews and notifications.'

    def add_arguments(self, parser):
        parser.add_argument('--customers', type=int, default=50)
        parser.add_argument('--orders', type=int, default=200)
        parser.add_argument('--reviews', type=int, default=120)

    def handle(self, *args, **options):
        random.seed(42)
        tenants = list(Tenant.objects.all())
        if not tenants:
            self.stdout.write(self.style.ERROR('No tenants found — seed tenants first.'))
            return

        customers = self._seed_customers(options['customers'])
        self._seed_coupons(tenants)
        self._adjust_stock_for_demo(tenants)
        orders = self._seed_orders(tenants, customers, options['orders'])
        self._seed_reviews(orders, options['reviews'])
        self._seed_notifications(orders)

        self.stdout.write(self.style.SUCCESS('Demo activity seeded successfully.'))
        self.stdout.write(f'New customers share the password: {DEMO_PASSWORD}')

    def _seed_customers(self, count):
        existing = set(User.objects.values_list('username', flat=True))
        created = []
        now = timezone.now()
        for i in range(count):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            username = f'{first.lower()}.{last.lower()}{i}'
            if username in existing:
                continue
            user = User(
                username=username,
                email=f'{username}@example.com',
                first_name=first,
                last_name=last,
                role=User.Role.USER,
                tenant=None,
                phone=f'+2507{random.randint(80000000, 89999999)}',
                province=random.choice(PROVINCES),
                district=random.choice(DISTRICTS),
                status=User.Status.ACTIVE,
            )
            user.set_password(DEMO_PASSWORD)
            created.append(user)
        User.objects.bulk_create(created, batch_size=500)
        # Spread created_at over the last 180 days (bulk_create ignores auto_now_add overrides).
        new_users = list(User.objects.filter(username__in=[u.username for u in created]))
        for user in new_users:
            days_ago = random.randint(1, 180)
            User.objects.filter(pk=user.pk).update(created_at=now - timedelta(days=days_ago))
        self.stdout.write(f'Seeded {len(created)} new customers.')
        return list(User.objects.filter(role=User.Role.USER))

    def _seed_coupons(self, tenants):
        today = timezone.now().date()
        templates = [
            ('WELCOME10', Coupon.DiscountType.PERCENTAGE, 10, 0, None, Coupon.Status.ACTIVE, None, None),
            ('SAVE5K', Coupon.DiscountType.FIXED, 5000, 20000, None, Coupon.Status.ACTIVE, None, None),
            ('VIP20', Coupon.DiscountType.PERCENTAGE, 20, 50000, 100, Coupon.Status.ACTIVE, today - timedelta(days=10), today + timedelta(days=60)),
            ('EXPIRED15', Coupon.DiscountType.PERCENTAGE, 15, 0, None, Coupon.Status.ACTIVE, today - timedelta(days=90), today - timedelta(days=30)),
            ('OLDPROMO', Coupon.DiscountType.FIXED, 2000, 0, 50, Coupon.Status.INACTIVE, None, None),
        ]
        count = 0
        for tenant in tenants:
            for code, dtype, value, min_order, max_uses, status, valid_from, valid_until in templates:
                _, made = Coupon.objects.get_or_create(
                    tenant=tenant, code=code,
                    defaults={
                        'discount_type': dtype, 'discount_value': value, 'min_order_amount': min_order,
                        'max_uses': max_uses, 'status': status, 'valid_from': valid_from, 'valid_until': valid_until,
                        'used_count': random.randint(0, 5) if status == Coupon.Status.ACTIVE else 0,
                    },
                )
                count += made
        self.stdout.write(f'Seeded {count} new coupons across {len(tenants)} organizations.')

    def _adjust_stock_for_demo(self, tenants):
        """Carve out a slice of each store's catalog into out-of-stock / low-stock examples."""
        total_touched = 0
        for tenant in tenants:
            ids = list(Product.objects.filter(tenant=tenant, status=Product.Status.ACTIVE).values_list('id', flat=True)[:5000])
            if not ids:
                continue
            sample_size = min(len(ids), 40)
            sample = random.sample(ids, sample_size)
            out_of_stock = sample[: sample_size // 4]
            low_stock = sample[sample_size // 4:]
            Product.objects.filter(id__in=out_of_stock).update(stock_quantity=0)
            for pid in low_stock:
                Product.objects.filter(id=pid).update(stock_quantity=random.randint(1, 5))
            total_touched += len(sample)
        self.stdout.write(f'Adjusted stock levels on {total_touched} products for low/out-of-stock demo states.')

    def _seed_orders(self, tenants, customers, count):
        if not customers:
            self.stdout.write(self.style.WARNING('No customers available — skipping order seeding.'))
            return []

        product_pool = {
            t.pk: list(Product.objects.filter(tenant=t, status=Product.Status.ACTIVE).values_list('id', 'price', 'discount_price')[:8000])
            for t in tenants
        }
        active_coupons_by_tenant = {
            t.pk: list(Coupon.objects.filter(tenant=t, status=Coupon.Status.ACTIVE)) for t in tenants
        }

        now = timezone.now()
        orders = []
        order_items_to_create = []

        with transaction.atomic():
            for _ in range(count):
                tenant = random.choice(tenants)
                pool = product_pool.get(tenant.pk) or []
                if not pool:
                    continue
                customer = random.choice(customers)
                line_count = random.randint(1, 4)
                lines = random.sample(pool, min(line_count, len(pool)))

                subtotal = 0
                line_data = []
                for product_id, price, discount_price in lines:
                    unit_price = discount_price if discount_price else price
                    quantity = random.randint(1, 3)
                    subtotal += unit_price * quantity
                    line_data.append((product_id, quantity, unit_price))

                order_status = weighted_choice(ORDER_STATUS_WEIGHTS)
                payment_status_weights = PAYMENT_STATUS_BY_ORDER_STATUS.get(
                    order_status, [(Order.PaymentStatus.PAID, 90), (Order.PaymentStatus.PENDING, 10)],
                )
                payment_status = weighted_choice(payment_status_weights)

                discount = 0
                coupon = None
                if random.random() < 0.25:
                    candidates = [c for c in active_coupons_by_tenant.get(tenant.pk, []) if subtotal >= c.min_order_amount]
                    if candidates:
                        coupon = random.choice(candidates)
                        discount = coupon.compute_discount(subtotal)

                tax = round(subtotal * tenant.tax_rate / 100, 2)
                shipping = tenant.shipping_fee
                total = subtotal - discount + tax + shipping

                return_reason = ''
                if order_status in (Order.OrderStatus.RETURN_REQUESTED, Order.OrderStatus.RETURNED):
                    return_reason = random.choice([
                        'Item arrived damaged.', 'Wrong size/color received.',
                        'Changed my mind about the purchase.', 'Product did not match the description.',
                    ])

                order = Order.objects.create(
                    tenant=tenant, user=customer,
                    subtotal_amount=subtotal, discount_amount=discount, tax_amount=tax,
                    shipping_amount=shipping, total_amount=total, coupon=coupon,
                    payment_method=random.choice(list(Order.PaymentMethod.values)),
                    payment_status=payment_status, order_status=order_status,
                    shipping_address=f"{random.choice(DISTRICTS)}, {customer.province or 'Kigali City'}",
                    return_reason=return_reason,
                )
                days_ago = random.randint(0, 180)
                order_date = now - timedelta(days=days_ago, hours=random.randint(0, 23))
                Order.objects.filter(pk=order.pk).update(order_date=order_date)
                order.order_date = order_date

                for product_id, quantity, unit_price in line_data:
                    order_items_to_create.append(OrderItem(order=order, product_id=product_id, quantity=quantity, unit_price=unit_price))

                orders.append(order)

            OrderItem.objects.bulk_create(order_items_to_create, batch_size=1000)

        self.stdout.write(f'Seeded {len(orders)} new orders with {len(order_items_to_create)} line items.')
        return orders

    def _seed_reviews(self, orders, count):
        candidates = []
        for order in orders:
            if order.order_status in (Order.OrderStatus.DELIVERED, Order.OrderStatus.RETURNED):
                for item in OrderItem.objects.filter(order=order).select_related('product'):
                    candidates.append((order.user_id, item.product_id))

        random.shuffle(candidates)
        seen = set()
        to_create = []
        now_date = timezone.now().date()
        for user_id, product_id in candidates:
            if len(to_create) >= count:
                break
            key = (user_id, product_id)
            if key in seen or Review.objects.filter(user_id=user_id, product_id=product_id).exists():
                continue
            seen.add(key)
            rating = random.choices([3, 4, 5], weights=[15, 35, 50])[0]
            to_create.append(Review(user_id=user_id, product_id=product_id, rating=rating, comment=random.choice(REVIEW_COMMENTS)))

        Review.objects.bulk_create(to_create, batch_size=500)
        self.stdout.write(f'Seeded {len(to_create)} new reviews.')

    def _seed_notifications(self, orders):
        to_create = []
        sample = random.sample(orders, min(len(orders), 150)) if orders else []
        for order in sample:
            to_create.append(Notification(
                tenant=order.tenant, user=order.user, title='Order placed',
                message=f'Your order #{order.pk} for {order.total_amount:,.0f} RWF has been placed.',
                notification_type=Notification.NotificationType.ORDER,
                is_read=random.random() < 0.6,
            ))
            admin = User.objects.filter(tenant_id=order.tenant_id, role=User.Role.SYSTEM_ADMIN).first()
            if admin:
                to_create.append(Notification(
                    tenant=order.tenant, user=admin, title='New order',
                    message=f'Order #{order.pk} has been placed by {order.user.get_full_name() or order.user.username}.',
                    notification_type=Notification.NotificationType.ORDER,
                    is_read=random.random() < 0.4,
                ))
        Notification.objects.bulk_create(to_create, batch_size=1000)
        self.stdout.write(f'Seeded {len(to_create)} new notifications.')
