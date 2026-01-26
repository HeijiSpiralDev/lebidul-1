"""
Paramètres de thème personnalisables.
"""

from django.db import models

from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting


@register_setting
class ThemeSettings(BaseSiteSetting):
    """Paramètres de thème personnalisables depuis l'admin."""

    # Couleurs
    couleur_primaire = models.CharField(
        max_length=7,
        default="#E63946",
        help_text="Couleur principale",
    )
    couleur_secondaire = models.CharField(
        max_length=7,
        default="#1D3557",
        help_text="Couleur secondaire",
    )
    couleur_accent = models.CharField(
        max_length=7,
        default="#F4A261",
        help_text="Couleur d'accent",
    )
    couleur_fond = models.CharField(
        max_length=7,
        default="#F1FAEE",
        help_text="Couleur de fond",
    )
    couleur_texte = models.CharField(
        max_length=7,
        default="#1D3557",
        help_text="Couleur du texte",
    )

    # Typographie
    police_titres = models.CharField(
        max_length=100,
        default="Montserrat",
        help_text="Police Google Fonts pour les titres",
    )
    police_corps = models.CharField(
        max_length=100,
        default="Open Sans",
        help_text="Police Google Fonts pour le corps de texte",
    )

    # Logos
    logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Logo header",
    )
    logo_footer = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Logo footer (optionnel)",
    )
    favicon = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Favicon 32x32",
    )

    # CSS personnalisé
    css_custom = models.TextField(
        blank=True,
        help_text="CSS additionnel (avancé)",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldRowPanel([
                    FieldPanel("couleur_primaire"),
                    FieldPanel("couleur_secondaire"),
                    FieldPanel("couleur_accent"),
                ]),
                FieldRowPanel([
                    FieldPanel("couleur_fond"),
                    FieldPanel("couleur_texte"),
                ]),
            ],
            heading="Couleurs",
        ),
        MultiFieldPanel(
            [
                FieldPanel("police_titres"),
                FieldPanel("police_corps"),
            ],
            heading="Typographie",
        ),
        MultiFieldPanel(
            [
                FieldPanel("logo"),
                FieldPanel("logo_footer"),
                FieldPanel("favicon"),
            ],
            heading="Logos",
        ),
        FieldPanel("css_custom"),
    ]

    class Meta:
        verbose_name = "Paramètres du thème"

    @property
    def google_fonts_url(self):
        """Retourne l'URL Google Fonts pour les polices configurées."""
        fonts = []
        if self.police_titres:
            fonts.append(self.police_titres.replace(" ", "+"))
        if self.police_corps and self.police_corps != self.police_titres:
            fonts.append(self.police_corps.replace(" ", "+"))
        
        if fonts:
            return f"https://fonts.googleapis.com/css2?family={'&family='.join(fonts)}&display=swap"
        return None

    @property
    def css_variables(self):
        """Retourne les variables CSS pour le thème."""
        return {
            "--color-primary": self.couleur_primaire,
            "--color-secondary": self.couleur_secondaire,
            "--color-accent": self.couleur_accent,
            "--color-background": self.couleur_fond,
            "--color-text": self.couleur_texte,
            "--font-headings": f"'{self.police_titres}', sans-serif",
            "--font-body": f"'{self.police_corps}', sans-serif",
        }
