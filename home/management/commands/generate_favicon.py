from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image


class Command(BaseCommand):
    help = 'Derives the favicon (PNG + multi-size ICO) and icon PNG sizes from static/images/logo/shophub-icon.png.'

    def handle(self, *args, **options):
        logo_dir = Path(settings.BASE_DIR) / 'static' / 'images' / 'logo'
        source_path = logo_dir / 'shophub-icon.png'
        if not source_path.exists():
            self.stderr.write(self.style.ERROR(f'{source_path} not found — nothing to derive icons from.'))
            return

        source = Image.open(source_path).convert('RGB')

        for size in (512, 256, 128, 64, 32, 16):
            source.resize((size, size), Image.LANCZOS).save(logo_dir / f'shophub-icon-{size}.png')

        source.resize((256, 256), Image.LANCZOS).save(logo_dir / 'favicon.png')
        sizes = [16, 32, 48, 64, 128, 256]
        base = source.resize((256, 256), Image.LANCZOS)
        base.save(logo_dir / 'favicon.ico', sizes=[(s, s) for s in sizes])

        self.stdout.write(self.style.SUCCESS(f'Derived favicon and icon sizes from {source_path.name} into {logo_dir}'))
