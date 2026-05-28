from apps.content.models import BidulIndexPage, BidulPage
from apps.agenda.models.snippets import Bidul

index = BidulIndexPage.objects.first()
MOIS = ["", "janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout", "septembre", "octobre", "novembre", "decembre"]

created = 0
for b in Bidul.objects.all().order_by("numero"):
    if BidulPage.objects.filter(bidul=b).exists():
        continue
    try:
        mois_nom = MOIS[b.mois] if 1 <= b.mois <= 12 else str(b.mois)
    except:
        mois_nom = str(b.mois)
    title = f"Le Bidul de {mois_nom} {b.annee} #{b.numero}"
    page = BidulPage(title=title, slug=f"bidul-{b.numero}", bidul=b, editorial="")
    index.add_child(instance=page)
    page.save_revision().publish()
    created += 1

print(f"BidulPages creees: {created}")
print(f"Total BidulPages: {BidulPage.objects.count()}")
