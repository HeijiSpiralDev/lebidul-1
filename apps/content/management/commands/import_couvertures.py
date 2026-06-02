"""Importe les couvertures de Bidul + le hero depuis le dossier img local."""
import os
from django.core.management.base import BaseCommand
from django.core.files.images import ImageFile
from wagtail.images.models import Image
from apps.content.models import BidulPage, HomePage
from PIL import Image as PILImage


class Command(BaseCommand):
    help = "Importe les couvertures de Bidul et l image hero"

    def add_arguments(self, parser):
        parser.add_argument("--dir", type=str, default=r"C:\Users\compteadmin\lebidul\img")
        parser.add_argument("--confirm", action="store_true")

    def _make_image(self, path, title, filename):
        with PILImage.open(path) as pil:
            width, height = pil.size
        with open(path, "rb") as fh:
            img = Image(title=title, width=width, height=height)
            img.file.save(filename, ImageFile(fh), save=True)
        return img

    def handle(self, *args, **options):
        base_dir = options["dir"]
        couv_dir = os.path.join(base_dir, "couv")

        if not os.path.isdir(couv_dir):
            self.stdout.write(self.style.ERROR(f"Dossier non trouve: {couv_dir}"))
            return

        if not options["confirm"]:
            if input("Continuer? (oui/Non) ").lower() != "oui":
                return

        self.stdout.write("Import des couvertures...")
        imported = 0
        assigned = 0
        for filename in sorted(os.listdir(couv_dir)):
            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            name_part = os.path.splitext(filename)[0]
            try:
                numero = int(name_part)
            except ValueError:
                continue

            path = os.path.join(couv_dir, filename)
            try:
                img = self._make_image(path, f"Couverture Bidul n {numero}", f"bidul-couv-{numero:03d}.jpg")
                imported += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Erreur {filename}: {str(e)[:60]}"))
                continue

            bidul_page = BidulPage.objects.filter(bidul__numero=numero).first()
            if bidul_page:
                bidul_page.couverture = img
                bidul_page.save_revision().publish()
                assigned += 1

        self.stdout.write(self.style.SUCCESS(f"  Couvertures: {imported} importees, {assigned} assignees"))

        landing = os.path.join(base_dir, "landingpage.jpg")
        if os.path.exists(landing):
            try:
                hero_img = self._make_image(landing, "Hero accueil", "hero-accueil.jpg")
                home = HomePage.objects.first()
                if home:
                    home.hero_image = hero_img
                    home.save_revision().publish()
                    self.stdout.write(self.style.SUCCESS("  Hero assigne a la HomePage"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Erreur hero: {str(e)[:60]}"))

        self.stdout.write(self.style.SUCCESS("Termine!"))
        self.stdout.write(f"Total images Wagtail: {Image.objects.count()}")
