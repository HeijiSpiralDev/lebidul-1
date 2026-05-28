from apps.agenda.models.snippets import Lieu
from apps.content.models import LieuPage
print("Lieux (snippets):", Lieu.objects.count())
print("LieuPages:", LieuPage.objects.count())
