import time
import urllib.error
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from categories.models import Category
from products.models import Product

# Curated, manually-verified Unsplash photo IDs (real, on-topic product photography),
# one list per category, cycled across the products in that category.
CATEGORY_PHOTO_IDS = {
    'Smartphones': [
        '1511707171634-5f897ff02aa9',
        '1598327105666-5b89351aff97',
        '1592890288564-76628a30a657',
        '1634403665481-74948d815f03',
        '1523206489230-c012c64b2b48',
    ],
    'Laptops': [
        '1541807084-5c52b6b3adef',
        '1525547719571-a2d4ac8945e2',
        '1496181133206-80ce9b88a853',
        '1486312338219-ce68d2c6f44d',
    ],
    'Accessories': [
        '1572569511254-d8f925fe2cbb',
        '1505740420928-5e560c06d30e',
        '1546435770-a3e426bf472b',
        '1590658268037-6bf12165a8df',
        '1606841837239-c5a1a4a07af7',
    ],
    'Shoes': [
        '1542291026-7eec264c27ff',
        '1606107557195-0e29a4b5b4aa',
        '1571008887538-b36bb32f4571',
        '1614252235316-8c857d38b5f4',
    ],
    'Clothing': [
        '1602810318383-e386cc2a3ccf',
        '1441984904996-e0b6ba687e04',
        '1562157873-818bc0726f68',
        '1489987707025-afc232f7ea0f',
        '1667284152861-36e03571486a',
    ],
    'Bags': [
        '1553062407-98eeb64c6a62',
        '1622560480605-d83c853bc5c3',
        '1581605405669-fcdf81165afa',
    ],
}

USER_AGENT = 'Mozilla/5.0 (compatible; ShopHubDemoSeed/1.0)'


def download(photo_id, retries=3):
    url = f'https://images.unsplash.com/photo-{photo_id}?w=900&q=80&fit=crop'
    last_error = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            time.sleep(1)
    raise last_error


class Command(BaseCommand):
    help = 'Downloads verified Unsplash product photos and assigns them per category.'

    def add_arguments(self, parser):
        parser.add_argument('--replace', action='store_true', help='Re-download and replace images that already exist.')

    def handle(self, *args, **options):
        cache = {}
        assigned = 0
        skipped_no_category = 0

        for category_name, photo_ids in CATEGORY_PHOTO_IDS.items():
            categories = Category.objects.filter(category_name=category_name)
            products = Product.objects.filter(category__in=categories).order_by('pk')
            if not options['replace']:
                products = products.filter(image='')

            for index, product in enumerate(products):
                photo_id = photo_ids[index % len(photo_ids)]
                if photo_id not in cache:
                    self.stdout.write(f'Downloading {photo_id}...')
                    cache[photo_id] = download(photo_id)
                product.image.save(f'{product.sku}.jpg', ContentFile(cache[photo_id]), save=True)
                assigned += 1

        remaining = Product.objects.filter(image='') if not options['replace'] else Product.objects.none()
        skipped_no_category = remaining.count()

        self.stdout.write(self.style.SUCCESS(f'Assigned real sample photos to {assigned} products.'))
        if skipped_no_category:
            self.stdout.write(self.style.WARNING(
                f'{skipped_no_category} product(s) still have no image (category not in the curated list).'
            ))
