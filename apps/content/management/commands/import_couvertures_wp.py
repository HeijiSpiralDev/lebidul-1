import requests
from io import BytesIO
from PIL import Image as PILImage
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from wagtail.images.models import Image as WagtailImage
from apps.content.models import BidulPage

MOIS_FR = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
}

class Command(BaseCommand):
    help = "Import missing Bidul covers from WordPress"

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true")
        parser.add_argument("--dry-run", action="store_true")

    def _try_url(self, url):
        try:
            r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                return r.content
        except Exception:
            pass
        return None

    def _find_content(self, numero, annee, mois_num):
        y = str(annee)
        m = f"{mois_num:02d}"
        for url in [
            f"https://lebidul.com/wp-content/uploads/{y}/{m}/{y}{m}_{numero}.jpg",
            f"https://lebidul.com/wp-content/uploads/{y}/{m}/{y}{m}_{numero}-scaled.jpg",
        ]:
            content = self._try_url(url)
            if content:
                return url, content
        return None, None

    def _get_mois_num(self, mois):
        s = str(mois).strip()
        if s.isdigit():
            return int(s)
        return MOIS_FR.get(s.lower())

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if not dry_run and not options["confirm"]:
            if input("Continue? (oui/Non) ").lower() != "oui":
                return

        pages = BidulPage.objects.filter(couverture__isnull=True).select_related("bidul").order_by("bidul__numero")
        self.stdout.write(f"{pages.count()} pages sans couverture")
        ok = 0
        missing = 0

        for page in pages:
            b = page.bidul
            mois_num = self._get_mois_num(b.mois)
            if not mois_num:
                self.stdout.write(self.style.WARNING(f"  mois inconnu: '{b.mois}' #{b.numero}"))
                continue

            if dry_run:
                y, m = str(b.annee), f"{mois_num:02d}"
                self.stdout.write(f"  #{b.numero} -> https://lebidul.com/wp-content/uploads/{y}/{m}/{y}{m}_{b.numero}.jpg")
                continue

            url, content = self._find_content(b.numero, b.annee, mois_num)
            if not content:
                self.stdout.write(self.style.WARNING(f"  not found: #{b.numero} ({b.mois} {b.annee})"))
                missing += 1
                continue

            try:
                title = f"Couverture Bidul n{b.numero}"
                existing = WagtailImage.objects.filter(title=title).first()
                if existing:
                    img = existing
                else:
                    pil = PILImage.open(BytesIO(content))
                    pil.load()
                    width, height = pil.size
                    img = WagtailImage(title=title)
                    img.file.save(f"couv-{b.numero:03d}.jpg", ContentFile(content), save=False)
                    img.width = width
                    img.height = height
                    img.save()
                page.couverture = img
                page.save_revision().publish()
                self.stdout.write(self.style.SUCCESS(f"  ok #{b.numero}"))
                ok += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  error #{b.numero}: {str(e)[:80]}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone! {ok} assigned, {missing} not found."))
