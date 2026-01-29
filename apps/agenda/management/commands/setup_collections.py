"""
Création des collections de médias.
"""

from django.core.management.base import BaseCommand

from wagtail.models import Collection


class Command(BaseCommand):
    help = "Crée les collections de médias de base"

    def handle(self, *args, **options):
        root_collection = Collection.get_first_root_node()

        collections = [
            ("Photos", "Photos et images du site"),
            ("Couvertures Bidul", "Couvertures des numéros du Bidul"),
            ("PDFs Bidul", "PDFs des numéros du Bidul"),
            ("Logos", "Logos et identité visuelle"),
            ("Articles", "Images des articles et chroniques"),
        ]

        for name, description in collections:
            if not Collection.objects.filter(name=name).exists():
                root_collection.add_child(name=name)
                self.stdout.write(f"Collection '{name}' créée")
            else:
                self.stdout.write(f"Collection '{name}' existe déjà")

        self.stdout.write(self.style.SUCCESS("Collections configurées"))