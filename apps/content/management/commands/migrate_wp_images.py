import re
import os
import requests
from io import BytesIO
from urllib.parse import urlparse
from PIL import Image as PILImage
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from wagtail.images.models import Image as WagtailImage
from wagtail.rich_text import RichText
from apps.content.models import ArticlePage


class Command(BaseCommand):
    help = "Migrate WP images to Wagtail"

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true")
        parser.add_argument("--dry-run", action="store_true")

    def _download_image(self, url, title):
        existing = WagtailImage.objects.filter(title=title).first()
        if existing:
            return existing, False
        filename = os.path.basename(urlparse(url).path)
        resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        content = resp.content
        try:
            pil = PILImage.open(BytesIO(content))
            pil.load()
            width, height = pil.size
        except Exception:
            width, height = 1, 1
        img = WagtailImage(title=title)
        img.file.save(filename, ContentFile(content), save=False)
        img.width = width
        img.height = height
        img.save()
        return img, True

    def _process_html(self, html, dry_run):
        pattern = r'https?://(?:www\.)?lebidul\.com/wp-content/uploads/[^\s"\'<>]+'
        urls = list(set(re.findall(pattern, html, re.I)))
        if not urls:
            return html, 0
        replacements = 0
        for url in urls:
            filename = os.path.basename(urlparse(url).path)
            title = f"wp-{filename}"
            if dry_run:
                self.stdout.write(f"    [DRY-RUN] {url}")
                replacements += 1
                continue
            try:
                img, created = self._download_image(url, title)
                local_url = img.file.url
                html = html.replace(url, local_url)
                replacements += 1
                status = "downloaded" if created else "reused"
                self.stdout.write(self.style.SUCCESS(f"    ok {filename} ({status})"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"    error {filename}: {str(e)[:80]}"))
        return html, replacements

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if not dry_run and not options["confirm"]:
            if input("Continue? (oui/Non) ").lower() != "oui":
                return

        total_pages = 0
        total_replacements = 0

        pages = ArticlePage.objects.all()
        self.stdout.write(f"\n=== ArticlePage: {pages.count()} pages ===")
        for page in pages:
            page_changed = False
            new_blocks = []
            for block in page.contenu:
                val = block.value
                if hasattr(val, "source"):
                    html = val.source
                    new_html, count = self._process_html(html, dry_run)
                    if count:
                        self.stdout.write(f"  Page: {page.title[:50]}")
                        total_replacements += count
                    if not dry_run and new_html != html:
                        new_blocks.append((block.block_type, RichText(new_html)))
                        page_changed = True
                    else:
                        new_blocks.append((block.block_type, val))
                else:
                    new_blocks.append((block.block_type, val))

            if page_changed and not dry_run:
                page.contenu = new_blocks
                page.save_revision().publish()
                total_pages += 1
                self.stdout.write(self.style.SUCCESS(f"  -> Saved: {page.title[:50]}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! {total_replacements} images migrated in {total_pages} pages."
        ))
        self.stdout.write(f"Total Wagtail images: {WagtailImage.objects.count()}")
