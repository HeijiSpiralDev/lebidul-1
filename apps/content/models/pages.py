"""
Pages CMS pour le site Le Bidul.

Ces pages contiennent le contenu éditorial et sont liées aux Snippets
pour les données métier.
"""

from django import forms
from django.db import models
from django.utils import timezone

from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from taggit.models import TaggedItemBase

from wagtail import blocks
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.embeds.blocks import EmbedBlock
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Page
from wagtail.search import index
from wagtail.documents.models import Document


# ===== STREAM BLOCKS =====
class ContentStreamBlock(blocks.StreamBlock):
    """Blocks de contenu réutilisables."""
    
    texte = blocks.RichTextBlock(
        features=["h2", "h3", "bold", "italic", "link", "ul", "ol", "blockquote"],
        label="Texte riche",
    )
    image = ImageChooserBlock(label="Image")
    galerie = blocks.ListBlock(
        ImageChooserBlock(),
        label="Galerie d'images",
    )
    citation = blocks.BlockQuoteBlock(label="Citation")
    embed = EmbedBlock(
        label="Média embarqué",
        help_text="YouTube, Vimeo, SoundCloud, etc.",
    )


# ===== ARTICLE TAG =====
class ArticleTag(TaggedItemBase):
    """Relation M2M pour les tags d'articles."""
    
    content_object = ParentalKey(
        "content.ArticlePage",
        on_delete=models.CASCADE,
        related_name="tagged_items",
    )


# ===== INDEX PAGES =====
class BidulIndexPage(Page):
    """Page d'index listant tous les numéros du Bidul."""
    
    introduction = models.TextField(blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel("introduction"),
    ]
    
    parent_page_types = ["content.HomePage"]
    subpage_types = ["content.BidulPage"]
    
    class Meta:
        verbose_name = "Index des Biduls"
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["biduls"] = (
            BidulPage.objects.live()
            .public()
            .order_by("-bidul__numero")
        )
        return context


class LieuxIndexPage(Page):
    """Page d'index listant tous les lieux."""
    
    introduction = models.TextField(blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel("introduction"),
    ]
    
    parent_page_types = ["content.HomePage"]
    subpage_types = ["content.LieuPage"]
    
    class Meta:
        verbose_name = "Index des Lieux"


class ArticleIndexPage(Page):
    """Page d'index listant tous les articles."""
    
    introduction = models.TextField(blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel("introduction"),
    ]
    
    parent_page_types = ["content.HomePage"]
    subpage_types = ["content.ArticlePage"]
    
    class Meta:
        verbose_name = "Index des Articles"
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["articles"] = (
            ArticlePage.objects.live()
            .public()
            .order_by("-date_publication")
        )
        return context


# ===== CONTENT PAGES =====
class BidulPage(Page):
    """
    Page CMS pour afficher un numéro du Bidul.
    
    Contient uniquement le contenu éditorial.
    Les données métier sont dans le Snippet Bidul associé.
    """
    
    # Lien vers les données métier
    bidul = models.OneToOneField(
        "agenda.Bidul",
        on_delete=models.PROTECT,
        related_name="page",
        help_text="Sélectionner le numéro du Bidul",
    )
    
    # Contenu éditorial
    couverture = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Image de couverture",
    )
    pdf = models.ForeignKey(
        "wagtaildocs.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="PDF téléchargeable",
    )
    editorial = models.TextField(
        blank=True,
        help_text="Texte d'introduction / édito",
    )
    contenu = StreamField(
        ContentStreamBlock(),
        blank=True,
        use_json_field=True,
    )
    
    # Search
    search_fields = Page.search_fields + [
        index.SearchField("editorial"),
    ]
    
    # Panels
    content_panels = Page.content_panels + [
        FieldPanel("bidul"),
        MultiFieldPanel(
            [
                FieldPanel("couverture"),
                FieldPanel("pdf"),
            ],
            heading="Médias",
        ),
        FieldPanel("editorial"),
        FieldPanel("contenu"),
    ]
    
    parent_page_types = ["content.BidulIndexPage"]
    subpage_types = []
    
    class Meta:
        verbose_name = "Page Bidul"
        verbose_name_plural = "Pages Bidul"
    
    def get_url_parts(self, request=None):
        """URL personnalisée basée sur les données du Bidul."""
        site = self.get_site()
        if site:
            return (
                site.id,
                site.root_url,
                f"/le-bidul-de-{self.bidul.mois_nom}-{self.bidul.annee}-{self.bidul.numero}/",
            )
        return None
    
    @property
    def numero(self):
        return self.bidul.numero
    
    @property
    def mois(self):
        return self.bidul.mois

    @property
    def mois_nom(self):
        return self.bidul.mois_nom
    
    @property
    def annee(self):
        return self.bidul.annee
    
    @property
    def evenements(self):
        """Événements associés à ce numéro."""
        from apps.agenda.models import Evenement
        return Evenement.objects.filter(
            source_bidul=self.bidul,
            statut="publie",
        )


class LieuPage(Page):
    """
    Page publique pour un lieu culturel.
    
    Les données de base sont dans le Snippet Lieu associé.
    """
    
    lieu = models.OneToOneField(
        "agenda.Lieu",
        on_delete=models.PROTECT,
        related_name="page",
        help_text="Sélectionner le lieu",
    )
    
    # Contenu éditorial supplémentaire
    contenu = StreamField(
        ContentStreamBlock(),
        blank=True,
        use_json_field=True,
    )
    
    # Search
    search_fields = Page.search_fields + [
        index.RelatedFields("lieu", [
            index.SearchField("nom"),
            index.SearchField("description"),
        ]),
    ]
    
    content_panels = Page.content_panels + [
        FieldPanel("lieu"),
        FieldPanel("contenu"),
    ]
    
    parent_page_types = ["content.LieuxIndexPage"]
    subpage_types = []
    
    class Meta:
        verbose_name = "Page Lieu"
        verbose_name_plural = "Pages Lieux"
    
    @property
    def evenements_a_venir(self):
        """Événements à venir dans ce lieu."""
        from apps.agenda.models import Evenement
        return Evenement.objects.filter(
            lieu=self.lieu,
            statut="publie",
            date_debut__gte=timezone.now().date(),
        ).order_by("date_debut")
    
    @property
    def evenements_passes(self):
        """Événements passés dans ce lieu."""
        from apps.agenda.models import Evenement
        return Evenement.objects.filter(
            lieu=self.lieu,
            statut="publie",
            date_debut__lt=timezone.now().date(),
        ).order_by("-date_debut")


class ArticlePage(Page):
    """Page pour une chronique ou un article."""
    
    auteur = models.ForeignKey(
        "agenda.Auteur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    date_publication = models.DateField()
    
    image_principale = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    
    # ← NOUVEAU CHAMP PDF
    fichier_pdf = models.ForeignKey(
        "wagtaildocs.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Fichier PDF",
        help_text="PDF téléchargeable lié à cet article",
    )
    
    introduction = models.TextField(
        blank=True,
        help_text="Chapô affiché en liste",
    )
    
    contenu = StreamField(
        ContentStreamBlock(),
        use_json_field=True,
    )
    
    categories = ParentalManyToManyField(
        "agenda.Categorie",
        blank=True,
        related_name="articles",
    )
    
    tags = ClusterTaggableManager(
        through=ArticleTag,
        blank=True,
    )
    
    mise_en_avant = models.BooleanField(
        default=False,
        help_text="Afficher en une",
    )
    
    search_fields = Page.search_fields + [
        index.SearchField("introduction"),
        index.RelatedFields("auteur", [
            index.SearchField("nom"),
        ]),
    ]
    
    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("auteur"),
                FieldPanel("date_publication"),
            ],
            heading="Metadonnees",
        ),
        FieldPanel("image_principale"),
        FieldPanel("fichier_pdf"),  # ← NOUVEAU PANEL
        FieldPanel("introduction"),
        FieldPanel("contenu"),
        MultiFieldPanel(
            [
                FieldPanel("categories", widget=forms.CheckboxSelectMultiple),
                FieldPanel("tags"),
            ],
            heading="Classification",
        ),
        FieldPanel("mise_en_avant"),
    ]
    
    parent_page_types = ["content.ArticleIndexPage"]
    subpage_types = []
    
    class Meta:
        verbose_name = "Article"
        ordering = ["-date_publication"]


class FlexiblePage(Page):
    """Page flexible pour contenu libre (À propos, Contact, etc.)."""
    
    contenu = StreamField(
        ContentStreamBlock(),
        blank=True,
        use_json_field=True,
    )
    
    content_panels = Page.content_panels + [
        FieldPanel("contenu"),
    ]
    
    parent_page_types = ["content.HomePage", "content.FlexiblePage"]
    subpage_types = ["content.FlexiblePage"]
    
    class Meta:
        verbose_name = "Page flexible"


class AgendaPage(Page):
    """Page conteneur pour l'agenda culturel."""
    
    introduction = models.TextField(blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel("introduction"),
    ]
    
    parent_page_types = ["content.HomePage"]
    subpage_types = []
    
    class Meta:
        verbose_name = "Page Agenda"
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        from apps.agenda.models import Evenement, Lieu
        
        context["evenements"] = Evenement.objects.filter(
            statut="publie",
            date_debut__gte=timezone.now().date(),
        ).select_related("lieu", "categorie").order_by("date_debut")[:50]
        
        context["lieux"] = Lieu.objects.filter(actif=True)
        return context


class HomePage(Page):
    """Page d'accueil du site."""
    
    introduction = models.TextField(blank=True)
    
    # Image de fond ou hero
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    
    content_panels = Page.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("hero_image"),
    ]
    
    parent_page_types = ["wagtailcore.Page"]  # Only root
    subpage_types = [
        "content.BidulIndexPage",
        "content.LieuxIndexPage",
        "content.ArticleIndexPage",
        "content.AgendaPage",
        "content.FlexiblePage",
    ]
    
    class Meta:
        verbose_name = "Page d'accueil"
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        from apps.agenda.models import Evenement
        
        # Derniers Biduls
        context["derniers_biduls"] = (
            BidulPage.objects.live()
            .public()
            .order_by("-bidul__numero")[:3]
        )
        
        # Prochains événements
        context["prochains_evenements"] = Evenement.objects.filter(
            statut="publie",
            date_debut__gte=timezone.now().date(),
        ).select_related("lieu", "categorie").order_by("date_debut")[:5]
        
        # Articles mis en avant
        context["articles_une"] = (
            ArticlePage.objects.live()
            .public()
            .filter(mise_en_avant=True)
            .order_by("-date_publication")[:3]
        )
        
        return context
