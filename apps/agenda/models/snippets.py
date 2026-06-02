"""
Snippets pour l'agenda culturel Le Bidul.

Ces modèles sont les données métier réutilisables :
- Bidul : numéros du magazine
- Lieu : lieux culturels géolocalisés
- Categorie : catégorisation événements/articles
- Auteur : auteurs des chroniques
"""

from django.db import models
from django.utils.text import slugify

from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class Bidul(models.Model):
    """
    Données métier d'un numéro du Bidul.
    
    Séparé de BidulPage pour :
    - Import Bidul Indexer indépendant du CMS
    - Référence stable pour les Evenements
    - API données sans exposer le contenu éditorial
    """

    # Identification
    numero = models.PositiveIntegerField(
        unique=True,
        help_text="Numéro unique du Bidul"
    )
    mois = models.CharField(
        max_length=20,
        help_text="Nom du mois (ex: décembre)"
    )
    annee = models.PositiveIntegerField()
    date_publication = models.DateField()

    # Données extraites par Bidul Indexer
    nb_evenements = models.PositiveIntegerField(
        default=0,
        help_text="Nombre d'événements extraits"
    )
    data_indexer = models.JSONField(
        default=dict,
        blank=True,
        help_text="Données brutes de l'extraction (métadonnées, stats)"
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("numero"),
                FieldRowPanel([
                    FieldPanel("mois"),
                    FieldPanel("annee"),
                ]),
                FieldPanel("date_publication"),
            ],
            heading="Identification",
        ),
        MultiFieldPanel(
            [
                FieldPanel("nb_evenements", read_only=True),
                FieldPanel("data_indexer", read_only=True),
            ],
            heading="Données Indexer (lecture seule)",
        ),
    ]

    class Meta:
        verbose_name = "Bidul"
        verbose_name_plural = "Biduls"
        ordering = ["-numero"]

    def __str__(self):
        return f"Bidul #{self.numero} - {self.mois} {self.annee}"

    @property
    def has_page(self):
        """Vérifie si une BidulPage est associée."""
        return hasattr(self, "page") and self.page is not None

    @property
    def evenements(self):
        """Raccourci vers les événements de ce numéro."""
        return self.evenements_source.all()


@register_snippet
class Lieu(models.Model):
    """
    Lieu culturel où se déroulent les événements.
    
    Snippet pour :
    - Chooser dans l'admin Evenement
    - Réutilisation dans LieuPage
    - Gestion centralisée des lieux
    """

    # Identité
    nom = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)

    # Adresse
    adresse = models.CharField(max_length=255, blank=True)
    code_postal = models.CharField(max_length=10, blank=True)
    ville = models.CharField(max_length=100)

    # Géolocalisation
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude (ex: 47.9960)"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude (ex: 0.1926)"
    )

    # Contact
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    site_web = models.URLField(blank=True)

    # Contenu
    description = models.TextField(blank=True)
    photo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # Métadonnées
    actif = models.BooleanField(
        default=True,
        help_text="Décocher pour masquer ce lieu"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("nom"),
                FieldPanel("slug"),
                FieldPanel("actif"),
            ],
            heading="Identité",
        ),
        MultiFieldPanel(
            [
                FieldPanel("adresse"),
                FieldRowPanel([
                    FieldPanel("code_postal"),
                    FieldPanel("ville"),
                ]),
                FieldRowPanel([
                    FieldPanel("latitude"),
                    FieldPanel("longitude"),
                ]),
            ],
            heading="Localisation",
        ),
        MultiFieldPanel(
            [
                FieldPanel("telephone"),
                FieldPanel("email"),
                FieldPanel("site_web"),
            ],
            heading="Contact",
        ),
        MultiFieldPanel(
            [
                FieldPanel("description"),
                FieldPanel("photo"),
            ],
            heading="Présentation",
        ),
    ]

    class Meta:
        verbose_name = "Lieu"
        verbose_name_plural = "Lieux"
        ordering = ["nom"]
        indexes = [
            models.Index(fields=["ville"]),
            models.Index(fields=["actif", "ville"]),
        ]

    def __str__(self):
        return f"{self.nom} ({self.ville})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    @property
    def adresse_complete(self):
        """Retourne l'adresse formatée."""
        parts = [self.adresse, self.code_postal, self.ville]
        return ", ".join(filter(None, parts))

    @property
    def has_coordinates(self):
        """Vérifie si les coordonnées GPS sont définies."""
        return self.latitude is not None and self.longitude is not None

    @property
    def coordinates(self):
        """Retourne les coordonnées au format [lng, lat] pour GeoJSON."""
        if self.has_coordinates:
            return [float(self.longitude), float(self.latitude)]
        return None


@register_snippet
class Categorie(models.Model):
    """
    Catégorie pour événements et articles.
    Partagée entre les deux types de contenu.
    """

    nom = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)

    # Apparence
    couleur = models.CharField(
        max_length=7,
        default="#E63946",
        help_text="Code couleur hex (ex: #E63946)"
    )
    icone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Nom icône Lucide (ex: music, theater, film)"
    )

    # Ordre d'affichage
    ordre = models.PositiveIntegerField(default=0)

    panels = [
        FieldPanel("nom"),
        FieldPanel("slug"),
        FieldPanel("description"),
        FieldRowPanel([
            FieldPanel("couleur"),
            FieldPanel("icone"),
        ]),
        FieldPanel("ordre"),
    ]

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["ordre", "nom"]

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)


@register_snippet
class Auteur(models.Model):
    """Auteur de chroniques et articles."""

    nom = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    bio = models.TextField(blank=True)

    photo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # Contact
    email = models.EmailField(blank=True)
    site_web = models.URLField(blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    instagram = models.CharField(max_length=100, blank=True)

    panels = [
        FieldPanel("nom"),
        FieldPanel("slug"),
        FieldPanel("bio"),
        FieldPanel("photo"),
        MultiFieldPanel(
            [
                FieldPanel("email"),
                FieldPanel("site_web"),
                FieldRowPanel([
                    FieldPanel("twitter"),
                    FieldPanel("instagram"),
                ]),
            ],
            heading="Contact & Réseaux",
        ),
    ]

    class Meta:
        verbose_name = "Auteur"
        verbose_name_plural = "Auteurs"
        ordering = ["nom"]

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)
