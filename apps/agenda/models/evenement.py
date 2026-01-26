"""
Modèle Evenement pour l'agenda culturel.

Model Django (pas Snippet) car :
- Volume important (~10k entrées)
- Requêtes complexes (dates, géo)
- API REST dédiée

Géré via SnippetViewSet pour UI Wagtail.
"""

from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .snippets import Bidul, Categorie, Lieu


class Evenement(models.Model):
    """Événement culturel de l'agenda."""

    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        PUBLIE = "publie", "Publié"
        ANNULE = "annule", "Annulé"

    # Identité
    titre = models.CharField(max_length=255)
    slug = models.SlugField(blank=True, max_length=100)
    description = models.TextField(blank=True)

    # Temporalité
    date_debut = models.DateField(db_index=True)
    date_fin = models.DateField(null=True, blank=True)
    heure_debut = models.TimeField(null=True, blank=True)
    heure_fin = models.TimeField(null=True, blank=True)

    # Relations vers Snippets
    lieu = models.ForeignKey(
        Lieu,
        on_delete=models.CASCADE,
        related_name="evenements",
    )
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evenements",
    )
    source_bidul = models.ForeignKey(
        Bidul,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evenements_source",
        help_text="Numéro du Bidul d'où provient cet événement",
    )

    # Infos pratiques
    prix = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ex: Gratuit, 5€, 10-15€"
    )
    url = models.URLField(blank=True, help_text="Lien vers plus d'infos")
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # Import / Source
    data_source = models.JSONField(
        default=dict,
        blank=True,
        help_text="Données brutes de l'import (Bidul Indexer)",
    )

    # Statut
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.BROUILLON,
        db_index=True,
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        ordering = ["date_debut", "heure_debut"]
        indexes = [
            models.Index(fields=["date_debut"]),
            models.Index(fields=["statut", "date_debut"]),
            models.Index(fields=["lieu", "date_debut"]),
            models.Index(fields=["source_bidul"]),
        ]

    def __str__(self):
        return f"{self.titre} - {self.date_debut}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.titre)[:50]
            self.slug = f"{base_slug}-{self.date_debut}"
        super().save(*args, **kwargs)

    @property
    def is_past(self):
        """Retourne True si l'événement est passé."""
        return self.date_debut < timezone.now().date()

    @property
    def is_today(self):
        """Retourne True si l'événement est aujourd'hui."""
        return self.date_debut == timezone.now().date()

    @property
    def is_multiday(self):
        """Retourne True si l'événement dure plusieurs jours."""
        return self.date_fin and self.date_fin != self.date_debut

    @property
    def is_published(self):
        """Retourne True si l'événement est publié."""
        return self.statut == self.Statut.PUBLIE


# ===== VIEWSET WAGTAIL 5+ =====
class EvenementViewSet(SnippetViewSet):
    """Administration des événements dans Wagtail."""
    
    model = Evenement
    icon = "date"
    menu_label = "Événements"
    menu_name = "evenements"
    menu_order = 200
    add_to_admin_menu = True
    
    list_display = ["titre", "date_debut", "lieu", "categorie", "statut"]
    list_filter = ["statut", "lieu__ville", "categorie"]
    search_fields = ["titre", "description", "lieu__nom"]
    ordering = ["-date_debut"]

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("titre"),
                FieldPanel("slug"),
                FieldPanel("description"),
            ],
            heading="Contenu",
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([
                    FieldPanel("date_debut"),
                    FieldPanel("date_fin"),
                ]),
                FieldRowPanel([
                    FieldPanel("heure_debut"),
                    FieldPanel("heure_fin"),
                ]),
            ],
            heading="Date & Heure",
        ),
        MultiFieldPanel(
            [
                FieldPanel("lieu"),
                FieldPanel("categorie"),
            ],
            heading="Classification",
        ),
        MultiFieldPanel(
            [
                FieldPanel("prix"),
                FieldPanel("url"),
                FieldPanel("image"),
            ],
            heading="Infos pratiques",
        ),
        MultiFieldPanel(
            [
                FieldPanel("statut"),
                FieldPanel("source_bidul"),
            ],
            heading="Publication",
        ),
    ]


# Enregistrement du ViewSet (fait via wagtail_hooks.py)
