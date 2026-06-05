import os, re
from django.core.management.base import BaseCommand
from django.core.files.images import ImageFile
from wagtail.images.models import Image
from apps.content.models import BidulPage
from PIL import Image as PILImage

class Command(BaseCommand):
    help = "Importe les couvertures manquantes"
    def add_arguments(self, parser):
        parser.add_argument("--dir", type=str, default=r"C:\Users\compteadmin\stage\img\other img")
        parser.add_argument("--dry", action="store_true")
    def _scan(self, base):
        index = {}
        for root, dirs, files in os.walk(base):
            for f in files:
                if not f.lower().endswith((".jpg",".jpeg",".png")):
                    continue
                if re.search(r"-\d+x\d+\.", f):
                    continue
                path = os.path.join(root, f)
                num = None
                m = re.match(r"bidul_0*(\d+)_", f, re.IGNORECASE)
                if m:
                    num = int(m.group(1))
                else:
                    m2 = re.match(r"\d{6}_(\d+)\.(?:jpg|jpeg|png)$", f, re.IGNORECASE)
                    if m2:
                        num = int(m2.group(1))
                if num and (num not in index or os.path.getsize(path) > os.path.getsize(index[num])):
                    index[num] = path
        return index
    def handle(self, *args, **options):
        base = options["dir"]
        self.stdout.write("Scan...")
        index = self._scan(base)
        self.stdout.write(f"Trouvees dans dossier: {len(index)}")
        pages = BidulPage.objects.filter(couverture__isnull=True).select_related("bidul")
        self.stdout.write(f"Sans couverture: {pages.count()}")
        if options["dry"]:
            ok = sum(1 for p in pages if p.bidul and int(p.bidul.numero) in index)
            self.stdout.write(f"Matchees: {ok}")
            return
        ok = 0
        for page in pages:
            b = page.bidul
            if not b:
                continue
            N = int(b.numero)
            if N not in index:
                continue
            try:
                path = index[N]
                with PILImage.open(path) as pil:
                    w, h = pil.size
                with open(path, "rb") as fh:
                    img = Image(title=f"Couverture Bidul n{N}", width=w, height=h)
                    img.file.save(f"bidul-couv-{N:03d}.jpg", ImageFile(fh), save=True)
                page.couverture = img
                page.save_revision().publish()
                ok += 1
                if ok % 20 == 0:
                    self.stdout.write(f"  ...{ok}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ERR #{N}: {str(e)[:50]}"))
        self.stdout.write(self.style.SUCCESS(f"Importees: {ok}"))
