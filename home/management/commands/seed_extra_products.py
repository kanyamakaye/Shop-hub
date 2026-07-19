from django.core.management.base import BaseCommand

from categories.models import Category
from products.models import Product
from tenants.models import Tenant

EXTRA_PRODUCTS = [
    # sku, tenant business_name, category name, product name, description, price, discount_price
    ('GPX8', 'Kigali Electronics Ltd', 'Smartphones', 'Google Pixel 8', '128GB Obsidian', '699', '649'),
    ('OP12', 'Kigali Electronics Ltd', 'Smartphones', 'OnePlus 12', '256GB Silky Black', '799', '750'),
    ('XRN13', 'Kigali Electronics Ltd', 'Smartphones', 'Xiaomi Redmi Note 13', '128GB Midnight Black', '299', '270'),
    ('HP15', 'Kigali Electronics Ltd', 'Laptops', 'HP Pavilion 15', 'Intel Core i5, 8GB RAM, 512GB SSD', '650', '600'),
    ('LNV14', 'Kigali Electronics Ltd', 'Laptops', 'Lenovo ThinkPad E14', 'Intel Core i7, 16GB RAM, 512GB SSD', '950', '890'),
    ('ASZ14', 'Kigali Electronics Ltd', 'Laptops', 'ASUS ZenBook 14', 'AMD Ryzen 7, 16GB RAM, 1TB SSD', '1050', ''),
    ('BTSPK', 'Kigali Electronics Ltd', 'Accessories', 'Portable Bluetooth Speaker', '360-degree sound, waterproof', '45', '39'),
    ('WCPAD', 'Kigali Electronics Ltd', 'Accessories', 'Wireless Charging Pad', '15W fast charge, non-slip', '25', ''),
    ('USBHUB', 'Kigali Electronics Ltd', 'Accessories', 'USB-C Hub 7-in-1', 'HDMI, USB 3.0, SD card reader', '35', '30'),
    ('LTSLV', 'Kigali Electronics Ltd', 'Accessories', 'Laptop Sleeve 15-inch', 'Padded, water-resistant', '20', ''),
    ('ADUB', 'Rwanda Fashion Store', 'Shoes', 'Adidas Ultraboost', "Men's running shoes", '180', '160'),
    ('RNSNK', 'Rwanda Fashion Store', 'Shoes', 'Classic Running Sneakers', "Women's lightweight sneakers", '95', '85'),
    ('LTHLF', 'Rwanda Fashion Store', 'Shoes', 'Leather Loafers', "Men's formal leather loafers", '110', ''),
    ('DNMJK', 'Rwanda Fashion Store', 'Clothing', "Men's Denim Jacket", 'Classic blue denim, all sizes', '65', '55'),
    ('SMDRS', 'Rwanda Fashion Store', 'Clothing', "Women's Summer Dress", 'Floral print, breathable fabric', '48', '40'),
    ('HDSWT', 'Rwanda Fashion Store', 'Clothing', 'Hooded Sweatshirt', 'Unisex fleece hoodie', '38', ''),
    ('CTVEST', 'Rwanda Fashion Store', 'Clothing', 'Cotton Polo Shirt', "Men's short-sleeve polo", '30', '25'),
    ('CVTOTE', 'Rwanda Fashion Store', 'Bags', 'Canvas Tote Bag', 'Durable everyday tote', '28', ''),
    ('TRDFL', 'Rwanda Fashion Store', 'Bags', 'Travel Duffel Bag', '40L weekend travel bag', '75', '65'),
    ('LTBP01', 'Rwanda Fashion Store', 'Bags', 'Laptop Backpack', 'Anti-theft, USB charging port', '55', '48'),
]


class Command(BaseCommand):
    help = 'Adds a supplemental catalog of demo products so the storefront has 20+ items.'

    def handle(self, *args, **options):
        created = 0
        for sku, tenant_name, category_name, name, description, price, discount_price in EXTRA_PRODUCTS:
            tenant = Tenant.objects.get(business_name=tenant_name)
            category = Category.objects.get(tenant=tenant, category_name=category_name)
            _, was_created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'tenant': tenant, 'category': category, 'product_name': name,
                    'description': description, 'price': price,
                    'discount_price': discount_price or None,
                    'status': Product.Status.ACTIVE,
                },
            )
            created += was_created

        self.stdout.write(self.style.SUCCESS(f'Added {created} new demo products.'))
