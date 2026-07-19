from datetime import date, datetime

from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware

from accounts.models import User
from cart.models import Cart
from categories.models import Category
from notifications.models import Notification
from orders.models import Order, OrderItem
from products.models import Product
from reviews.models import Review
from subscriptions.models import SubscriptionPlan
from tenants.models import Tenant
from wishlist.models import Wishlist

DEMO_PASSWORD = 'Passw0rd!'


class Command(BaseCommand):
    help = 'Loads the sample SaaS e-commerce dataset from start.md for local demo/testing.'

    def handle(self, *args, **options):
        plans = self._seed_plans()
        tenants = self._seed_tenants(plans)
        users = self._seed_users(tenants)
        categories = self._seed_categories(tenants)
        products = self._seed_products(tenants, categories)
        self._seed_cart(users, products)
        orders = self._seed_orders(tenants, users)
        self._seed_order_items(orders, products)
        self._seed_reviews(users, products)
        self._seed_wishlist(users, products)
        self._seed_notifications(tenants, users)

        self.stdout.write(self.style.SUCCESS('Demo data loaded successfully.'))
        self.stdout.write(f'All seeded users share the password: {DEMO_PASSWORD}')

    def _seed_plans(self):
        data = [
            ('Basic', '20.00', '200.00', 100, 5),
            ('Professional', '50.00', '500.00', 1000, 20),
            ('Enterprise', '150.00', '1500.00', -1, -1),
        ]
        plans = {}
        for plan_name, monthly, yearly, max_products, max_users in data:
            plan, _ = SubscriptionPlan.objects.get_or_create(
                plan_name=plan_name,
                defaults={
                    'monthly_price': monthly, 'yearly_price': yearly,
                    'max_products': max_products, 'max_users': max_users,
                    'status': SubscriptionPlan.Status.ACTIVE,
                },
            )
            plans[plan_name] = plan
        self.stdout.write(f'Seeded {len(plans)} subscription plans.')
        return plans

    def _seed_tenants(self, plans):
        data = [
            ('Kigali Electronics Ltd', plans['Professional'], 'info@kigalielectronics.rw', '+250788111111', 'Rwanda', 'Kigali City'),
            ('Rwanda Fashion Store', plans['Basic'], 'sales@rwfashion.rw', '+250788222222', 'Rwanda', 'Musanze'),
        ]
        tenants = {}
        for business_name, plan, email, phone, country, address in data:
            tenant, _ = Tenant.objects.get_or_create(
                business_name=business_name,
                defaults={
                    'plan': plan, 'email': email, 'phone': phone,
                    'country': country, 'address': address,
                    'status': Tenant.Status.ACTIVE,
                },
            )
            tenants[business_name] = tenant
        self.stdout.write(f'Seeded {len(tenants)} tenants.')
        return tenants

    def _seed_users(self, tenants):
        kigali = tenants['Kigali Electronics Ltd']
        fashion = tenants['Rwanda Fashion Store']
        data = [
            dict(email='owner@eshop.com', first_name='James', last_name='Smith', tenant=None,
                 role=User.Role.SYSTEM_OWNER, phone='+250788000001', province='Kigali City', district='Gasabo',
                 sector='Remera', cell='Rukiri II', village='Nyabisindu', created=date(2026, 1, 1)),
            dict(email='admin@kigalielectronics.rw', first_name='Jean', last_name='Niyonsenga', tenant=kigali,
                 role=User.Role.SYSTEM_ADMIN, phone='+250788100001', province='Kigali City', district='Gasabo',
                 sector='Kimironko', cell='Bibare', village='Kibagabaga', created=date(2026, 1, 5)),
            dict(email='admin@rwfashion.rw', first_name='Eric', last_name='Habimana', tenant=fashion,
                 role=User.Role.SYSTEM_ADMIN, phone='+250788100002', province='Northern', district='Musanze',
                 sector='Muhoza', cell='Cyabararika', village='Kabazungu', created=date(2026, 1, 6)),
            dict(email='patrick@gmail.com', first_name='Patrick', last_name='Uwimana', tenant=kigali,
                 role=User.Role.USER, phone='+250788100003', province='Kigali City', district='Kicukiro',
                 sector='Kagarama', cell='Kanserege', village='Nyenyeri', created=date(2026, 2, 10)),
            dict(email='alice@gmail.com', first_name='Alice', last_name='Mukamana', tenant=kigali,
                 role=User.Role.USER, phone='+250788100004', province='Eastern', district='Rwamagana',
                 sector='Kigabiro', cell='Sovu', village='Cyanya', created=date(2026, 2, 15)),
            dict(email='diane@gmail.com', first_name='Diane', last_name='Uwase', tenant=fashion,
                 role=User.Role.USER, phone='+250788100005', province='Western', district='Rubavu',
                 sector='Gisenyi', cell='Amahoro', village='Bugoyi', created=date(2026, 3, 1)),
            dict(email='peter@gmail.com', first_name='Peter', last_name='Otieno', tenant=fashion,
                 role=User.Role.USER, phone='+254712345678', postal_address='Nairobi', created=date(2026, 3, 15)),
        ]
        users = {}
        for entry in data:
            created_date = entry.pop('created')
            email = entry['email']
            user, made = User.objects.get_or_create(
                username=email,
                defaults={**entry, 'status': User.Status.ACTIVE},
            )
            if made:
                user.set_password(DEMO_PASSWORD)
                user.save()
                User.objects.filter(pk=user.pk).update(
                    created_at=make_aware(datetime.combine(created_date, datetime.min.time())),
                )
            users[email] = user
        self.stdout.write(f'Seeded {len(users)} users.')
        return users

    def _seed_categories(self, tenants):
        kigali = tenants['Kigali Electronics Ltd']
        fashion = tenants['Rwanda Fashion Store']
        data = [
            ('Smartphones', kigali, 'Mobile phones'),
            ('Laptops', kigali, 'Computers and laptops'),
            ('Accessories', kigali, 'Electronic accessories'),
            ('Shoes', fashion, "Men's and Women's shoes"),
            ('Clothing', fashion, 'Clothes and fashion'),
            ('Bags', fashion, 'Fashion bags'),
        ]
        categories = {}
        for name, tenant, description in data:
            category, _ = Category.objects.get_or_create(
                tenant=tenant, category_name=name, defaults={'description': description},
            )
            categories[name] = category
        self.stdout.write(f'Seeded {len(categories)} categories.')
        return categories

    def _seed_products(self, tenants, categories):
        kigali = tenants['Kigali Electronics Ltd']
        fashion = tenants['Rwanda Fashion Store']
        data = [
            ('IP15', kigali, categories['Smartphones'], 'Apple iPhone 15', '128GB Black', '1200', '1100'),
            ('SGS24', kigali, categories['Smartphones'], 'Samsung Galaxy S24', '256GB Gray', '950', '900'),
            ('DELL15', kigali, categories['Laptops'], 'Dell Inspiron 15', 'Intel Core i7 Laptop', '800', '760'),
            ('AIRP01', kigali, categories['Accessories'], 'Apple AirPods Pro', 'Wireless Earbuds', '250', '220'),
            ('NK001', fashion, categories['Shoes'], 'Nike Air Max', 'Running Shoes', '150', '130'),
            ('TS001', fashion, categories['Clothing'], 'Cotton T-Shirt', 'Blue Cotton Shirt', '25', '20'),
            ('BG001', fashion, categories['Bags'], 'Leather Backpack', 'Brown Backpack', '80', '70'),
        ]
        products = {}
        for sku, tenant, category, name, description, price, discount_price in data:
            product, _ = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'tenant': tenant, 'category': category, 'product_name': name,
                    'description': description, 'price': price, 'discount_price': discount_price,
                    'status': Product.Status.ACTIVE,
                },
            )
            products[sku] = product
        self.stdout.write(f'Seeded {len(products)} products.')
        return products

    def _seed_cart(self, users, products):
        data = [
            (users['patrick@gmail.com'], products['SGS24'], 1),
            (users['patrick@gmail.com'], products['AIRP01'], 2),
            (users['alice@gmail.com'], products['DELL15'], 1),
            (users['diane@gmail.com'], products['NK001'], 2),
            (users['peter@gmail.com'], products['BG001'], 1),
        ]
        count = 0
        for user, product, quantity in data:
            _, made = Cart.objects.get_or_create(user=user, product=product, defaults={'quantity': quantity})
            count += made
        self.stdout.write(f'Seeded {count} new cart entries.')

    def _seed_orders(self, tenants, users):
        kigali = tenants['Kigali Electronics Ltd']
        fashion = tenants['Rwanda Fashion Store']
        data = [
            ('TXN100001', kigali, users['patrick@gmail.com'], '1100', Order.PaymentMethod.VISA_CARD,
             Order.PaymentStatus.PAID, Order.OrderStatus.DELIVERED, 'Kagarama, Kicukiro', datetime(2026, 7, 12)),
            ('TXN100002', kigali, users['alice@gmail.com'], '760', Order.PaymentMethod.MOBILE_MONEY,
             Order.PaymentStatus.PAID, Order.OrderStatus.PROCESSING, 'Kigabiro, Rwamagana', datetime(2026, 7, 13)),
            ('TXN100003', fashion, users['diane@gmail.com'], '260', Order.PaymentMethod.BANK_TRANSFER,
             Order.PaymentStatus.PENDING, Order.OrderStatus.PENDING, 'Gisenyi, Rubavu', datetime(2026, 7, 14)),
            ('TXN100004', fashion, users['peter@gmail.com'], '70', Order.PaymentMethod.CREDIT_CARD,
             Order.PaymentStatus.PAID, Order.OrderStatus.SHIPPED, 'Nairobi, Kenya', datetime(2026, 7, 15)),
        ]
        orders = {}
        for ref, tenant, user, total, method, pay_status, order_status, address, order_date in data:
            order, made = Order.objects.get_or_create(
                transaction_reference=ref,
                defaults={
                    'tenant': tenant, 'user': user, 'total_amount': total,
                    'payment_method': method, 'payment_status': pay_status,
                    'order_status': order_status, 'shipping_address': address,
                },
            )
            if made:
                Order.objects.filter(pk=order.pk).update(order_date=make_aware(order_date))
            orders[ref] = order
        self.stdout.write(f'Seeded {len(orders)} orders.')
        return orders

    def _seed_order_items(self, orders, products):
        data = [
            ('TXN100001', products['IP15'], 1, '1100'),
            ('TXN100002', products['DELL15'], 1, '760'),
            ('TXN100003', products['NK001'], 2, '130'),
            ('TXN100004', products['BG001'], 1, '70'),
        ]
        count = 0
        for ref, product, quantity, unit_price in data:
            _, made = OrderItem.objects.get_or_create(
                order=orders[ref], product=product,
                defaults={'quantity': quantity, 'unit_price': unit_price},
            )
            count += made
        self.stdout.write(f'Seeded {count} new order items.')

    def _seed_reviews(self, users, products):
        data = [
            (users['patrick@gmail.com'], products['IP15'], 5, 'Excellent phone with great battery life.', date(2026, 7, 15)),
            (users['alice@gmail.com'], products['DELL15'], 4, 'Very good laptop for office work.', date(2026, 7, 16)),
            (users['diane@gmail.com'], products['NK001'], 5, 'Comfortable shoes.', date(2026, 7, 17)),
            (users['peter@gmail.com'], products['BG001'], 4, 'Nice quality backpack.', date(2026, 7, 18)),
        ]
        count = 0
        for user, product, rating, comment, review_date in data:
            review, made = Review.objects.get_or_create(
                user=user, product=product, defaults={'rating': rating, 'comment': comment},
            )
            if made:
                Review.objects.filter(pk=review.pk).update(review_date=review_date)
            count += made
        self.stdout.write(f'Seeded {count} new reviews.')

    def _seed_wishlist(self, users, products):
        data = [
            (users['patrick@gmail.com'], products['SGS24']),
            (users['patrick@gmail.com'], products['AIRP01']),
            (users['alice@gmail.com'], products['IP15']),
            (users['diane@gmail.com'], products['TS001']),
            (users['peter@gmail.com'], products['NK001']),
        ]
        count = 0
        for user, product in data:
            _, made = Wishlist.objects.get_or_create(user=user, product=product)
            count += made
        self.stdout.write(f'Seeded {count} new wishlist entries.')

    def _seed_notifications(self, tenants, users):
        kigali = tenants['Kigali Electronics Ltd']
        fashion = tenants['Rwanda Fashion Store']
        data = [
            (kigali, users['admin@kigalielectronics.rw'], 'New Order', 'Order #1 has been placed by Patrick Uwimana.',
             Notification.NotificationType.ORDER, False, datetime(2026, 7, 12, 9, 30)),
            (kigali, users['patrick@gmail.com'], 'Payment Successful', 'Your payment for Order #1 was successful.',
             Notification.NotificationType.PAYMENT, True, datetime(2026, 7, 12, 9, 35)),
            (kigali, users['alice@gmail.com'], 'Order Processing', 'Your laptop order is being processed.',
             Notification.NotificationType.ORDER, False, datetime(2026, 7, 13, 14, 0)),
            (fashion, users['admin@rwfashion.rw'], 'New Order', 'Order #3 has been received.',
             Notification.NotificationType.ORDER, False, datetime(2026, 7, 14, 11, 20)),
            (fashion, users['diane@gmail.com'], 'Payment Pending', 'Please complete your payment to process the order.',
             Notification.NotificationType.PAYMENT, False, datetime(2026, 7, 14, 11, 25)),
            (fashion, users['peter@gmail.com'], 'Order Shipped', 'Your backpack has been shipped.',
             Notification.NotificationType.SHIPPING, True, datetime(2026, 7, 15, 16, 40)),
        ]
        count = 0
        for tenant, user, title, message, ntype, is_read, created_at in data:
            notification, made = Notification.objects.get_or_create(
                user=user, title=title, message=message,
                defaults={'tenant': tenant, 'notification_type': ntype, 'is_read': is_read},
            )
            if made:
                Notification.objects.filter(pk=notification.pk).update(created_at=make_aware(created_at))
            count += made
        self.stdout.write(f'Seeded {count} new notifications.')
