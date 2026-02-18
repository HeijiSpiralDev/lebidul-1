from django.core.management.base import BaseCommand
from wagtail.images.models import Image
from wagtail.documents.models import Document
from apps.agenda.models import Auteur, Categorie
from apps.content.models import ArticlePage

class Command(BaseCommand):
    help = "Supprime toutes les données importées"

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true')

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                'Cette commande va SUPPRIMER toutes les donnees importees!\n'
                'Utilisez --confirm pour confirmer'
            ))
            return

        self.stdout.write('Suppression des donnees...')
        
        # Supprimer les articles
        result = ArticlePage.objects.all().delete()
        count = result[0] if result else 0
        self.stdout.write(f'  OK {count} articles supprimes')
        
        # Supprimer les images
        result = Image.objects.all().delete()
        count = result[0] if result else 0
        self.stdout.write(f'  OK {count} images supprimees')
        
        # Supprimer les documents
        result = Document.objects.all().delete()
        count = result[0] if result else 0
        self.stdout.write(f'  OK {count} documents supprimes')
        
        # Supprimer les catégories
        result = Categorie.objects.all().delete()
        count = result[0] if result else 0
        self.stdout.write(f'  OK {count} categories supprimees')
        
        # Supprimer les auteurs
        result = Auteur.objects.all().delete()
        count = result[0] if result else 0
        self.stdout.write(f'  OK {count} auteurs supprimes')
        
        self.stdout.write(self.style.SUCCESS('\nOK Toutes les donnees ont ete supprimees'))