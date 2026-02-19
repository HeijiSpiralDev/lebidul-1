# Documentation : Snippets, StreamField et Settings dans Wagtail

---

## 📋 Vue d'ensemble

Cette documentation couvre trois fonctionnalités essentielles de Wagtail au-delà des collections et groupes :

- **Snippets** — Contenus réutilisables sur plusieurs pages (auteurs, boutons, alertes…)
- **StreamField** — Pages à blocs modulaires et flexibles
- **Settings** — Paramètres globaux du site (nom, email, réseaux sociaux…)

---

## 🚨 Important : Migrations obligatoires

⚠️ **Attention** : Toute modification de modèle nécessite une migration. Ne jamais oublier :

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 🧩 Partie 1 — Snippets

Un **Snippet** est un morceau de contenu réutilisable (auteur, bouton, bandeau…) gérable depuis l'admin Wagtail, indépendamment des pages.

### Créer un Snippet

Dans `myapp/models.py` :

```python
from django.db import models
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel

@register_snippet
class Auteur(models.Model):
    nom = models.CharField(max_length=100)
    bio = models.TextField(blank=True)

    panels = [FieldPanel("nom"), FieldPanel("bio")]

    def __str__(self):
        return self.nom
```

Puis appliquez les migrations :

```bash
python manage.py makemigrations
python manage.py migrate
```

Résultat attendu :

```
Migrations for 'myapp':
  myapp/migrations/0001_initial.py
    - Create model Auteur

Running migrations:
  Applying myapp.0001_initial... OK
```

### Créer un Snippet via le shell

```bash
python manage.py shell
```

```python
from myapp.models import Auteur

auteur = Auteur.objects.create(nom="Marie Curie", bio="Physicienne et chimiste.")
print(f"✅ Auteur créé : {auteur.nom} (ID: {auteur.id})")

exit()
```

---

## 🏗️ Partie 2 — StreamField

Le **StreamField** permet de construire des pages à partir de blocs modulaires (texte, image, citation…) que l'éditeur assemble librement depuis l'admin, sans toucher au code.

### Créer une page avec StreamField

Dans `myapp/models.py` :

```python
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.blocks import CharBlock, RichTextBlock, ImageChooserBlock
from wagtail.admin.panels import FieldPanel

class ArticlePage(Page):
    contenu = StreamField(
        [
            ("titre", CharBlock(label="Titre de section")),
            ("texte", RichTextBlock(label="Texte riche")),
            ("image", ImageChooserBlock(label="Image")),
        ],
        blank=True,
        use_json_field=True,
    )

    content_panels = Page.content_panels + [FieldPanel("contenu")]
```

Puis appliquez les migrations :

```bash
python manage.py makemigrations
python manage.py migrate
```

### Afficher le StreamField dans le template

Créez `myapp/templates/myapp/article_page.html` :

```html
{% extends "base.html" %}
{% load wagtailcore_tags %}

{% block content %}
  <h1>{{ page.title }}</h1>

  {% for bloc in page.contenu %}
    {% if bloc.block_type == "titre" %}
      <h2>{{ bloc.value }}</h2>
    {% elif bloc.block_type == "texte" %}
      <div>{{ bloc.value|richtext }}</div>
    {% elif bloc.block_type == "image" %}
      {% image bloc.value width-800 %}
    {% endif %}
  {% endfor %}
{% endblock %}
```

---

## ⚙️ Partie 3 — Settings

Les **Settings** permettent de stocker des paramètres globaux du site (nom, email, réseaux sociaux…) modifiables depuis l'admin sans redéployer le code.

### Activer l'application

Dans `settings.py` :

```python
INSTALLED_APPS = [
    ...
    "wagtail.contrib.settings",
]

TEMPLATES = [{
    ...
    "OPTIONS": {
        "context_processors": [
            ...
            "wagtail.contrib.settings.context_processors.settings",
        ],
    },
}]
```

### Déclarer le modèle de Settings

Dans `myapp/models.py` :

```python
from django.db import models
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.admin.panels import FieldPanel

@register_setting
class ParametresSite(BaseSiteSetting):
    nom_site = models.CharField(max_length=100, blank=True)
    email_contact = models.EmailField(blank=True)
    url_instagram = models.URLField(blank=True)

    panels = [
        FieldPanel("nom_site"),
        FieldPanel("email_contact"),
        FieldPanel("url_instagram"),
    ]
```

Puis appliquez les migrations :

```bash
python manage.py makemigrations
python manage.py migrate
```

### Utiliser les Settings dans un template

```html
{% load wagtailsettings_tags %}
{% get_settings %}

<footer>
  <p>{{ settings.myapp.ParametresSite.nom_site }}</p>
  <a href="{{ settings.myapp.ParametresSite.url_instagram }}">Instagram</a>
</footer>
```

---

## 🔍 Vérifier le résultat

Après les migrations, vérifiez dans l'admin Wagtail :

1. **Les Snippets**

    `http://127.0.0.1:8000/admin/snippets/`

    Vous devriez voir votre modèle (ex : Auteurs) dans la liste.

2. **Les pages StreamField**

    `http://127.0.0.1:8000/admin/pages/`

    Créez une nouvelle page de type `ArticlePage` — les blocs doivent apparaître dans l'éditeur.

3. **Les Settings**

    `http://127.0.0.1:8000/admin/` > Paramètres

    Vous devriez voir **Paramètres du site** dans le menu.