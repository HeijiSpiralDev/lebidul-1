import os, re
from django.core.management.base import BaseCommand
from django.core.files.images import ImageFile
from wagtail.images.models import Image
from apps.content.models import BidulPage
from PIL import Image as PILImage

class Command(BaseCommand):
    help = "Importe les couvertures restantes par recherche dans dossier mois"
    def add_arguments(self, parser):
        parser.add_argument("--dir", type=str, default=r"C:\Users\compteadmin\stage\img\other img")
        parser.add_argument("--dry", action="store_true")
    def _best(self, folder, N):
        if not os.path.isdir(folder):
            return None
        candidates = []
        for f in os.listdir(folder):
            low = f.lower()
            if not low.endswith((".jpg",".jpeg",".png")):
                continue
            if re.search(r"-\d+x\d+\.", f):
                continue
            if "-pdf" in low:
                continue
            path = os.path.join(folder, f)
            size = os.path.getsize(path)
            score = size
            if "bidul" in low:
                score += 10000000
            if "couv" in low or "une" in low:
                score += 5000000
            if str(N) in f:
                score += 8000000
            candidates.append((score, path, f))
        if not candidates:
            return None
        candidates.sort(reverse=True)
        return candidates[0][1], candidates[0][2]
    def handle(self, *args, **options):
        base = options["dir"]
        pages = BidulPage.objects.filter(couverture__isnull=True).select_related("bidul")
        self.stdout.write(f"Restantes sans couverture: {pages.count()}")
        ok = 0
        fail = []
        for page in pages:
            b = page.bidul
            if not b or not b.annee or not b.mois:
                continue
            Y, M, N = int(b.annee), int(b.mois), int(b.numero)
            folder = os.path.join(base, str(Y), f"{M:02d}")
            found = self._best(folder, N)
            if not found:
                fail.append(f"#{N} ({M}/{Y}) - rien dans {Y}/{M:02d}/")
                continue
            path, fname = found
            if options["dry"]:
                self.stdout.write(f"  #{N} ({M}/{Y}) -> {fname}")
                ok += 1
                continue
            try:
                with PILImage.open(path) as pil:
                    w, h = pil.size
                with open(path, "rb") as fh:
                    img = Image(title=f"Couverture Bidul n{N}", width=w, height=h)
                    img.file.save(f"bidul-couv-{N:03d}.jpg", ImageFile(fh), save=True)
                page.couverture = img
                page.save_revision().publish()
                ok += 1
                self.stdout.write(self.style.SUCCESS(f"  OK #{N} -> {fname}"))
            except Exception as e:
                fail.append(f"#{N}: {str(e)[:50]}")
        self.stdout.write(f"\nImportees: {ok}")
        if fail:
            self.stdout.write(f"Echouees ({len(fail)}):")
            for f in fail:
                self.stdout.write(f"  {f}")
