"""
Création des groupes et permissions de base.
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from wagtail.models import Page


class Command(BaseCommand):
    help = "Crée les groupes et permissions de base"

    def handle(self, *args, **options):
        # Groupe Administrateurs (accès total)
        admin_group, created = Group.objects.get_or_create(name="Administrateurs")
        if created:
            self.stdout.write(f"Groupe '{admin_group.name}' créé")
            # Donner toutes les permissions Wagtail
            admin_permissions = Permission.objects.filter(
                content_type__app_label__in=[
                    "wagtailadmin", "wagtailcore", "wagtailimages", 
                    "wagtaildocs", "agenda", "content"
                ]
            )
            admin_group.permissions.set(admin_permissions)

        # Groupe Éditeurs (créer/modifier, pas supprimer)
        editor_group, created = Group.objects.get_or_create(name="Éditeurs")
        if created:
            self.stdout.write(f"Groupe '{editor_group.name}' créé")
            editor_permissions = Permission.objects.filter(
                codename__in=[
                    "access_admin",
                    "add_image", "change_image",
                    "add_document", "change_document",
                ]
            )
            editor_group.permissions.set(editor_permissions)

        # Groupe Contributeurs (lecture + ajout limité)
        contrib_group, created = Group.objects.get_or_create(name="Contributeurs")
        if created:
            self.stdout.write(f"Groupe '{contrib_group.name}' créé")
            contrib_permissions = Permission.objects.filter(
                codename__in=["access_admin"]
            )
            contrib_group.permissions.set(contrib_permissions)

        self.stdout.write(self.style.SUCCESS("Groupes configurés avec succès"))