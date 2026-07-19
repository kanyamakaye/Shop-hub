import random
import time
import urllib.error
import urllib.request
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from categories.models import Category
from products.models import Product
from subscriptions.models import SubscriptionPlan
from tenants.models import Tenant

USER_AGENT = 'Mozilla/5.0 (compatible; ShopHubDemoSeed/1.0)'

# Curated, individually-verified Unsplash photos, grouped by top-level fashion
# category. Shared across every product in that group (not one download per
# product) — practical at 100k-row scale, and each is a real, on-topic photo.
CATEGORY_PHOTOS = {
    'Clothing': [
        '1602810318383-e386cc2a3ccf', '1441984904996-e0b6ba687e04',
        '1562157873-818bc0726f68', '1489987707025-afc232f7ea0f', '1667284152861-36e03571486a',
    ],
    'Footwear': [
        '1542291026-7eec264c27ff', '1606107557195-0e29a4b5b4aa',
        '1571008887538-b36bb32f4571', '1614252235316-8c857d38b5f4',
    ],
    'Watches': [
        '1523170335258-f5ed11844a49', '1524805444758-089113d48a6d',
        '1620625515032-6ed0c1790c75', '1542496658-e33a6d0d50f6', '1547996160-81dfa63595aa',
    ],
    'Jewelry': [
        '1617038220319-276d3cfab638', '1633934542430-0905ccb5f050',
        '1611652022419-a9419f74343d', '1602173574767-37ac01994b2a', '1599643478518-a784e5dc4c8f',
    ],
    'Bags': [
        '1553062407-98eeb64c6a62', '1622560480605-d83c853bc5c3', '1581605405669-fcdf81165afa',
    ],
    'Accessories': [
        '1511499767150-a48a237f0083', '1572635196237-14b3f281503f',
        '1577803645773-f96470509666', '1584036553516-bf83210aa16c',
    ],
    'Beauty & Personal Care': [
        '1523293182086-7651a899d37f', '1541643600914-78b084683601',
        '1594035910387-fea47794261f', '1458538977777-0549b2370168',
    ],
    'Luxury Fashion': [
        '1617038220319-276d3cfab638', '1523170335258-f5ed11844a49',
        '1602810318383-e386cc2a3ccf', '1553062407-98eeb64c6a62',
    ],
    'Sports & Fitness Fashion': [
        '1542291026-7eec264c27ff', '1606107557195-0e29a4b5b4aa', '1441984904996-e0b6ba687e04',
    ],
    "Kids' Fashion": [
        '1441984904996-e0b6ba687e04', '1542291026-7eec264c27ff', '1489987707025-afc232f7ea0f',
    ],
    'Travel & Lifestyle Fashion': [
        '1639598003276-8a70fcaaad6c', '1502301197179-65228ab57f78',
        '1718702662411-11d9672eb179', '1622560480654-d96214fdc887',
    ],
}

# Main category -> subcategories, from sample data.md
CATEGORY_TREE = {
    'Clothing': [
        'T-shirts', 'Shirts', 'Polo shirts', 'Hoodies', 'Sweatshirts', 'Sweaters',
        'Jackets', 'Coats', 'Blazers', 'Suits', 'Dresses', 'Skirts', 'Jeans',
        'Trousers/Pants', 'Shorts', 'Leggings', 'Jumpsuits', 'Rompers', 'Sleepwear',
        'Underwear', 'Socks', 'Activewear', 'Swimwear', 'Traditional wear',
    ],
    'Footwear': [
        'Sneakers', 'Running shoes', 'Dress shoes', 'Boots', 'Sandals',
        'Slippers', 'Loafers', 'Heels', 'Flats', 'Flip-flops',
    ],
    'Watches': [
        'Analog watches', 'Digital watches', 'Smartwatches',
        'Luxury watches', 'Sports watches', 'Casual watches',
    ],
    'Jewelry': [
        'Necklaces', 'Rings', 'Earrings', 'Bracelets', 'Bangles',
        'Anklets', 'Chains', 'Pendants', 'Brooches',
    ],
    'Bags': [
        'Handbags', 'Backpacks', 'Tote bags', 'Shoulder bags', 'Crossbody bags',
        'Clutches', 'Wallets', 'Duffel bags', 'Travel bags', 'Briefcases',
    ],
    'Accessories': [
        'Sunglasses', 'Eyeglasses', 'Belts', 'Hats', 'Caps', 'Beanies',
        'Scarves', 'Gloves', 'Ties', 'Bow ties', 'Hair accessories', 'Key holders',
    ],
    'Beauty & Personal Care': [
        'Perfumes', 'Colognes', 'Makeup', 'Skincare products',
        'Hair care products', 'Nail care products',
    ],
    'Luxury Fashion': [
        'Designer clothing', 'Fine jewelry', 'Designer handbags', 'Premium footwear',
    ],
    'Sports & Fitness Fashion': [
        'Gym wear', 'Yoga wear', 'Compression clothing', 'Sports shoes', 'Fitness accessories',
    ],
    "Kids' Fashion": [
        'Baby clothing', "Boys' clothing", "Girls' clothing", "Kids' shoes", "Kids' accessories",
    ],
    'Travel & Lifestyle Fashion': [
        'Luggage', 'Travel backpacks', 'Passport holders', 'Cosmetic bags', 'Travel organizers',
    ],
}

# (min_price, max_price) per main category, in whole dollars.
PRICE_RANGES = {
    'Clothing': (10, 90),
    'Footwear': (20, 160),
    'Watches': (25, 2500),
    'Jewelry': (12, 1800),
    'Bags': (18, 320),
    'Accessories': (8, 110),
    'Beauty & Personal Care': (9, 140),
    'Luxury Fashion': (200, 5000),
    'Sports & Fitness Fashion': (15, 130),
    "Kids' Fashion": (8, 65),
    'Travel & Lifestyle Fashion': (25, 420),
}

ADJECTIVES = [
    'Classic', 'Modern', 'Elegant', 'Premium', 'Casual', 'Vintage', 'Sporty',
    'Slim-Fit', 'Oversized', 'Everyday', 'Trendy', 'Chic', 'Bold', 'Comfort',
    'Minimalist', 'Signature', 'Urban', 'Essential',
]
COLORS = [
    'Black', 'White', 'Navy', 'Beige', 'Red', 'Blue', 'Grey', 'Brown',
    'Pink', 'Green', 'Gold', 'Silver', 'Khaki', 'Maroon', 'Ivory', 'Charcoal',
]
MATERIALS = [
    'Cotton', 'Leather', 'Denim', 'Silk', 'Wool', 'Polyester',
    'Suede', 'Linen', 'Cashmere', 'Canvas', 'Satin', 'Mesh',
]

TOTAL_PRODUCTS = 100_000
BATCH_SIZE = 5000
FASHION_TENANTS = [
    ('Rwanda Fashion Store', None),  # reuse existing tenant if present
    ('Urban Threads Co.', 'Professional'),
    ('Milano Luxe Boutique', 'Enterprise'),
    ('StreetStyle Collective', 'Basic'),
]


def download(photo_id, retries=3):
    url = f'https://images.unsplash.com/photo-{photo_id}?w=900&q=80&fit=crop'
    last_error = None
    for _ in range(retries):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            time.sleep(1)
    raise last_error


class Command(BaseCommand):
    help = 'Seeds ~100,000 dummy fashion products across a fashion category tree and multiple tenants.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=TOTAL_PRODUCTS)

    def handle(self, *args, **options):
        total = options['count']

        tenants = self._ensure_tenants()
        image_paths = self._ensure_shared_images()
        categories_by_tenant = self._ensure_categories(tenants)

        self.stdout.write(f'Generating {total:,} products...')
        self._generate_products(total, tenants, categories_by_tenant, image_paths)
        self.stdout.write(self.style.SUCCESS(f'Done. {Product.objects.count():,} total products in database.'))

    def _ensure_tenants(self):
        professional = SubscriptionPlan.objects.filter(plan_name='Professional').first()
        enterprise = SubscriptionPlan.objects.filter(plan_name='Enterprise').first()
        basic = SubscriptionPlan.objects.filter(plan_name='Basic').first()
        plan_lookup = {'Professional': professional, 'Enterprise': enterprise, 'Basic': basic}

        tenants = []
        for name, plan_name in FASHION_TENANTS:
            existing = Tenant.objects.filter(business_name=name).first()
            if existing:
                tenants.append(existing)
                continue
            plan = plan_lookup.get(plan_name) or professional or enterprise or basic
            slug = name.lower().replace(' ', '').replace('.', '').replace("'", '')
            tenant = Tenant.objects.create(
                business_name=name, plan=plan,
                email=f'contact@{slug}.example.com', phone='+250788999000',
                country='Rwanda', address='Kigali City',
                status=Tenant.Status.ACTIVE,
            )
            tenants.append(tenant)
        self.stdout.write(f'Using {len(tenants)} fashion tenants.')
        return tenants

    def _ensure_shared_images(self):
        images_dir = Path(settings.MEDIA_ROOT) / 'products' / 'fashion'
        images_dir.mkdir(parents=True, exist_ok=True)
        paths = {}
        for category_name, photo_ids in CATEGORY_PHOTOS.items():
            group_paths = []
            for i, photo_id in enumerate(photo_ids, start=1):
                slug = category_name.lower().replace(' ', '-').replace('&', 'and').replace("'", '')
                filename = f'{slug}-{i}.jpg'
                filepath = images_dir / filename
                if not filepath.exists():
                    self.stdout.write(f'Downloading shared image for {category_name} ({i}/{len(photo_ids)})...')
                    filepath.write_bytes(download(photo_id))
                group_paths.append(f'products/fashion/{filename}')
            paths[category_name] = group_paths
        return paths

    def _ensure_categories(self, tenants):
        categories_by_tenant = {}
        for tenant in tenants:
            tenant_categories = {}
            for main_name, sub_names in CATEGORY_TREE.items():
                main_cat, _ = Category.objects.get_or_create(
                    tenant=tenant, category_name=main_name, parent=None,
                    defaults={'description': f'{main_name} for {tenant.business_name}'},
                )
                subcats = []
                for sub_name in sub_names:
                    subcat, _ = Category.objects.get_or_create(
                        tenant=tenant, category_name=sub_name, parent=main_cat,
                    )
                    subcats.append(subcat)
                tenant_categories[main_name] = subcats
            categories_by_tenant[tenant.pk] = tenant_categories
        total_cats = sum(len(v) for tc in categories_by_tenant.values() for v in tc.values()) + \
            sum(len(tc) for tc in categories_by_tenant.values())
        self.stdout.write(f'Ensured category tree ({total_cats:,} category rows across all tenants).')
        return categories_by_tenant

    def _generate_products(self, total, tenants, categories_by_tenant, image_paths):
        main_names = list(CATEGORY_TREE.keys())
        existing_count = Product.objects.filter(sku__startswith='FSH-').count()
        start_index = existing_count + 1

        batch = []
        created = 0
        for i in range(start_index, start_index + total):
            tenant = random.choice(tenants)
            main_name = random.choice(main_names)
            subcats = categories_by_tenant[tenant.pk][main_name]
            category = random.choice(subcats)

            adjective = random.choice(ADJECTIVES)
            color = random.choice(COLORS)
            material = random.choice(MATERIALS)
            name = f'{adjective} {color} {material} {category.category_name.rstrip("s") if category.category_name.endswith("s") else category.category_name}'

            low, high = PRICE_RANGES[main_name]
            price = round(random.uniform(low, high), 2)
            has_discount = random.random() < 0.4
            discount_price = round(price * random.uniform(0.6, 0.9), 2) if has_discount else None

            image = random.choice(image_paths[main_name])
            status = Product.Status.ACTIVE if random.random() < 0.9 else Product.Status.INACTIVE

            batch.append(Product(
                tenant=tenant, category=category, sku=f'FSH-{i:06d}',
                product_name=name, description=f'{name} — a {material.lower()} {category.category_name.lower()} in {color.lower()}.',
                image=image, price=price, discount_price=discount_price, status=status,
            ))

            if len(batch) >= BATCH_SIZE:
                with transaction.atomic():
                    Product.objects.bulk_create(batch)
                created += len(batch)
                self.stdout.write(f'  {created:,} / {total:,} products created...')
                batch = []

        if batch:
            with transaction.atomic():
                Product.objects.bulk_create(batch)
            created += len(batch)
            self.stdout.write(f'  {created:,} / {total:,} products created...')
