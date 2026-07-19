import hashlib
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont

from products.models import Product
from tenants.models import Tenant

ACCENTS = [
    '#1f4fe0',  # brand blue
    '#0a9c60',  # brand green
    '#1a3fb3',
    '#0a7b4e',
    '#3366ff',
    '#0fbf76',
]

BACKGROUND = '#fafafa'
BORDER = '#e5e7eb'

FONT_BOLD = 'C:/Windows/Fonts/arialbd.ttf'
FONT_REGULAR = 'C:/Windows/Fonts/arial.ttf'


def pick_accent(key):
    index = int(hashlib.md5(key.encode()).hexdigest(), 16) % len(ACCENTS)
    return ACCENTS[index]


def make_product_image(key):
    """Clean white-background product thumbnail (Amazon-style): a simple
    centered accent-colored icon, no baked-in text — the product name/price
    are already rendered as HTML below the image in every template."""
    size = (800, 800)
    img = Image.new('RGB', size, BACKGROUND)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline=BORDER, width=3)

    accent = pick_accent(key)
    cx, cy = size[0] / 2, size[1] / 2

    # Stylized "gift box" icon: rounded box with a cross-shaped ribbon.
    box_w, box_h = 340, 280
    left, top = cx - box_w / 2, cy - box_h / 2
    right, bottom = cx + box_w / 2, cy + box_h / 2
    draw.rounded_rectangle([left, top, right, bottom], radius=20, fill=accent)
    ribbon = 26
    draw.rectangle([cx - ribbon / 2, top, cx + ribbon / 2, bottom], fill=BACKGROUND)
    draw.rectangle([left, cy - ribbon / 2, right, cy + ribbon / 2], fill=BACKGROUND)

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return ContentFile(buffer.getvalue())


def make_logo_image(business_name, key):
    size = (400, 400)
    accent = pick_accent(key)
    img = Image.new('RGB', size, '#ffffff')
    draw = ImageDraw.Draw(img)
    draw.ellipse([20, 20, size[0] - 20, size[1] - 20], outline=accent, width=10)
    initials = ''.join(word[0].upper() for word in business_name.split()[:2])
    font = ImageFont.truetype(FONT_BOLD, 150)
    w = draw.textlength(initials, font=font)
    bbox = font.getbbox(initials)
    h = bbox[3] - bbox[1]
    draw.text(((size[0] - w) / 2, (size[1] - h) / 2 - bbox[1]), initials, font=font, fill=accent)

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    help = 'Generates clean white-background placeholder images for products and tenant logos that have none.'

    def add_arguments(self, parser):
        parser.add_argument('--replace', action='store_true', help='Regenerate images even if one already exists.')

    def handle(self, *args, **options):
        products = Product.objects.all() if options['replace'] else Product.objects.filter(image='')
        product_count = 0
        for product in products:
            content = make_product_image(product.sku)
            product.image.save(f'{product.sku}.png', content, save=True)
            product_count += 1

        tenants = Tenant.objects.all() if options['replace'] else Tenant.objects.filter(logo='')
        logo_count = 0
        for tenant in tenants:
            content = make_logo_image(tenant.business_name, tenant.business_name)
            tenant.logo.save(f'{tenant.pk}.png', content, save=True)
            logo_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Generated {product_count} product images and {logo_count} tenant logos.'
        ))
