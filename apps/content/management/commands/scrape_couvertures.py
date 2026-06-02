import os
import requests
from io import BytesIO
from PIL import Image as PILImage
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from wagtail.images.models import Image as WagtailImage
from apps.content.models import BidulPage

COVERS = {
    156: 'https://i0.wp.com/www.lebidul.com/wp-content/uploads/2011/04/156.jpg',
    172: 'https://i0.wp.com/www.lebidul.com/wp-content/uploads/2012/11/1721.jpg',
    182: 'https://i0.wp.com/www.lebidul.com/wp-content/uploads/2013/10/Bidul-Octobre-20131.png',
    184: 'https://i0.wp.com/www.lebidul.com/wp-content/uploads/2013/12/Image11.png',
    229: 'https://lebidul.com/wp-content/uploads/2018/01/201801_229.jpg',
    230: 'https://lebidul.com/wp-content/uploads/2018/02/201802_230.jpg',
    231: 'https://lebidul.com/wp-content/uploads/2018/03/201803_231.jpg',
    232: 'https://lebidul.com/wp-content/uploads/2018/04/201804_232.jpg',
    233: 'https://lebidul.com/wp-content/uploads/2018/05/201805_233.jpg',
    234: 'https://lebidul.com/wp-content/uploads/2018/06/201806_234.jpg',
    235: 'https://lebidul.com/wp-content/uploads/2018/07/201807_235.jpg',
    236: 'https://lebidul.com/wp-content/uploads/2018/09/201809_236.jpg',
    237: 'https://lebidul.com/wp-content/uploads/2018/10/201810_237.jpg',
    238: 'https://lebidul.com/wp-content/uploads/2018/11/201811_238.jpg',
    239: 'https://lebidul.com/wp-content/uploads/2018/12/201812_239.jpg',
    240: 'https://lebidul.com/wp-content/uploads/2019/01/201901_240.jpg',
    241: 'https://lebidul.com/wp-content/uploads/2019/02/201902_241.jpg',
    242: 'https://lebidul.com/wp-content/uploads/2019/03/201903_242.jpg',
    243: 'https://lebidul.com/wp-content/uploads/2019/04/201904_243.jpg',
    245: 'https://lebidul.com/wp-content/uploads/2019/06/201906_245.jpg',
    246: 'https://lebidul.com/wp-content/uploads/2019/07/201907_246.jpg',
    248: 'https://lebidul.com/wp-content/uploads/2019/10/201910_248.jpg',
    249: 'https://lebidul.com/wp-content/uploads/2019/11/201911_249.jpg',
    250: 'https://lebidul.com/wp-content/uploads/2019/12/201912_250.jpg',
    251: 'https://lebidul.com/wp-content/uploads/2020/01/202001_251.jpg',
    252: 'https://lebidul.com/wp-content/uploads/2020/02/202002_252.jpg',
    253: 'https://lebidul.com/wp-content/uploads/2020/03/202003_253.jpg',
    254: 'https://lebidul.com/wp-content/uploads/2020/04/202004_254.jpg',
    261: 'https://lebidul.com/wp-content/uploads/2021/09/202109_261.jpg',
    263: 'https://lebidul.com/wp-content/uploads/2021/11/202111_263.jpg',
    265: 'https://lebidul.com/wp-content/uploads/2022/01/202201_265.jpg',
    267: 'https://lebidul.com/wp-content/uploads/2022/03/202203_267.jpg',
    268: 'https://lebidul.com/wp-content/uploads/2022/04/202204_268.jpg',
    269: 'https://lebidul.com/wp-content/uploads/2022/05/202205_269.jpg',
    270: 'https://lebidul.com/wp-content/uploads/2022/06/202206_270.jpg',
    271: 'https://lebidul.com/wp-content/uploads/2022/07/202207_271.jpg',
    272: 'https://lebidul.com/wp-content/uploads/2022/09/202209_272.jpg',
    273: 'https://lebidul.com/wp-content/uploads/2022/10/202210_273.jpg',
    274: 'https://lebidul.com/wp-content/uploads/2022/11/202211_274.jpg',
    275: 'https://lebidul.com/wp-content/uploads/2022/12/202212_275.jpg',
    276: 'https://lebidul.com/wp-content/uploads/2023/01/202301_276.jpg',
    277: 'https://lebidul.com/wp-content/uploads/2023/02/202302_277.jpg',
    278: 'https://lebidul.com/wp-content/uploads/2023/03/202303_278.jpg',
    279: 'https://lebidul.com/wp-content/uploads/2023/04/202304_279.jpg',
    280: 'https://lebidul.com/wp-content/uploads/2023/05/202305_280.jpg',
    281: 'https://lebidul.com/wp-content/uploads/2023/06/202306_281.jpg',
    282: 'https://lebidul.com/wp-content/uploads/2023/07/202307_282.jpg',
    283: 'https://lebidul.com/wp-content/uploads/2023/09/202309_283.jpg',
    284: 'https://lebidul.com/wp-content/uploads/2023/10/202310_284.jpg',
    285: 'https://lebidul.com/wp-content/uploads/2023/11/202311_285.jpg',
    286: 'https://lebidul.com/wp-content/uploads/2023/12/202312_286.jpg',
    287: 'https://lebidul.com/wp-content/uploads/2024/01/202401_287.jpg',
    288: 'https://lebidul.com/wp-content/uploads/2024/02/202402_288.jpg',
    289: 'https://lebidul.com/wp-content/uploads/2024/03/202403_289.jpg',
    290: 'https://lebidul.com/wp-content/uploads/2024/04/202404_290.jpg',
    292: 'https://lebidul.com/wp-content/uploads/2024/06/202406_292.jpg',
    296: 'https://lebidul.com/wp-content/uploads/2024/11/202411_296.jpg',
    297: 'https://lebidul.com/wp-content/uploads/2024/12/202412_297.jpg',
    303: 'https://lebidul.com/wp-content/uploads/2025/06/202506_303.jpg',
    304: 'https://lebidul.com/wp-content/uploads/2025/07/202507_304.jpg',
    305: 'https://lebidul.com/wp-content/uploads/2025/09/202509_305.jpg',
    306: 'https://lebidul.com/wp-content/uploads/2025/10/202510_306.jpg',
    307: 'https://lebidul.com/wp-content/uploads/2025/11/202511_307.jpg',
    308: 'https://lebidul.com/wp-content/uploads/2025/12/202512_308.jpg',
    311: 'https://lebidul.com/wp-content/uploads/2026/03/202603_311.jpg',
}

class Command(BaseCommand):
    help = "Import couvertures manquantes depuis dictionnaire statique"

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if not dry_run and not options["confirm"]:
            if input("Continue? (oui/Non) ").lower() != "oui":
                return

        missing = set(BidulPage.objects.filter(couverture__isnull=True).values_list('bidul__numero', flat=True))
        to_import = {n: u for n, u in COVERS.items() if n in missing}
        self.stdout.write(f"A importer: {len(to_import)} couvertures")

        if dry_run:
            for n, url in sorted(to_import.items()):
                self.stdout.write(f"  #{n} -> {url}")
            return

        ok = 0
        error = 0
        for numero, url in sorted(to_import.items()):
            page = BidulPage.objects.filter(bidul__numero=numero, couverture__isnull=True).first()
            if not page:
                continue
            try:
                resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                content = resp.content
                pil = PILImage.open(BytesIO(content))
                pil.load()
                width, height = pil.size
                title = f"Couverture Bidul n{numero}"
                filename = os.path.basename(url.split("?")[0])
                if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    filename = f"couv-{numero:03d}.jpg"
                img_obj = WagtailImage(title=title)
                img_obj.file.save(filename, ContentFile(content), save=False)
                img_obj.width = width
                img_obj.height = height
                img_obj.save()
                page.couverture = img_obj
                page.save_revision().publish()
                self.stdout.write(self.style.SUCCESS(f"  ok #{numero}"))
                ok += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  error #{numero}: {str(e)[:80]}"))
                error += 1

        self.stdout.write(self.style.SUCCESS(f"\nDone! {ok} importees, {error} erreurs."))
