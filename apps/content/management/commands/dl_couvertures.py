import os, re
from django.core.management.base import BaseCommand
from django.core.files.images import ImageFile
from wagtail.images.models import Image
from apps.content.models import BidulPage
from PIL import Image as PILImage

BONS = {200,214,229,231,234,239,240,241,243,251,252,254,265,267,268,269,272,273,274,275,277,281,282,283,285,286,289,297,304,306,307,311}

class Command(BaseCommand):
    help = "Importe uniquement les couvertures verifiees"

    def add_arguments(self, parser):
        parser.add_argument("--dir", type=str, default=r"C:\Users\compteadmin\stage\img\other img")

    def _best_candidate(self, folder, N):
        if not os.path.isdir(folder):
            return None
        candidates = []
        for f in os.listdir(folder):
            low = f.lower()
            if not low.endswith((".jpg", ".jpeg", ".png")):
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
            candidates.append((score, path, f))
        if not candidates:
            return None
        candidates.sort(reverse=True)
        return candidates[0][1], candidates[0][2]

    def handle(self, *args, **options):
        base = options["dir"]
        pages = BidulPage.objects.filter(couverture__isnull=True, bidul__isnull=False).select_related("bidul")

        ok = 0
        skip = 0
        for p in pages:
            b = p.bidul
            N = int(b.numero)
            if N not in BONS:
                skip += 1
                continue
            Y, M = int(b.annee), int(b.mois)
            folder = os.path.join(base, str(Y), f"{M:02d}")
            found = self._best_candidate(folder, N)
            if not found:
                self.stdout.write(self.style.WARNING(f"  SKIP #{N} - rien trouve"))
                continue
            path, fname = found
            try:
                with PILImage.open(path) as pil:
                    w, h = pil.size
                with open(path, "rb") as fh:
                    img = Image(title=f"Couverture Bidul n{N}", width=w, height=h)
                    img.file.save(f"bidul-couv-{N:03d}.jpg", ImageFile(fh), save=True)
                p.couverture = img
                p.save_revision().publish()
                ok += 1
                self.stdout.write(self.style.SUCCESS(f"  OK #{N} -> {fname}"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ERR #{N}: {str(e)[:50]}"))

        self.stdout.write(f"\nImportees: {ok} | Skippees (manuelles): {skip}")
