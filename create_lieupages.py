from apps.content.models import LieuxIndexPage, LieuPage
from apps.agenda.models.snippets import Lieu
from apps.agenda.models.evenement import Evenement

index = LieuxIndexPage.objects.first()

lieu_ids = set(Evenement.objects.values_list("lieu_id", flat=True).distinct())
lieu_ids.discard(None)
lieux = Lieu.objects.filter(id__in=lieu_ids).order_by("nom")
print("Lieux avec evenements:", lieux.count())

created = 0
errors = 0
for lieu in lieux:
    if LieuPage.objects.filter(lieu=lieu).exists():
        continue
    slug = (lieu.slug or "").strip()[:255] or f"lieu-{lieu.id}"
    try:
        page = LieuPage(title=lieu.nom[:255], slug=slug, lieu=lieu)
        index.add_child(instance=page)
        page.save_revision().publish()
        created += 1
    except Exception as e:
        errors += 1
        if errors <= 3:
            print(f"  Erreur {lieu.nom[:30]}: {str(e)[:50]}")

print("LieuPages creees:", created, "Erreurs:", errors)
print("Total LieuPages:", LieuPage.objects.count())
