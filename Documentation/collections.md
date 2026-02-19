# Documentation : Collections dans Wagtail

---

## 📋 Vue d'ensemble

Cette documentation explique comment créer et gérer les **collections** dans Wagtail. Cela permet de :

- Organiser les médias (images, documents) en dossiers logiques
- Restreindre l'accès à certains médias selon les groupes
- Structurer le contenu en arborescence hiérarchique

---

## 🚨 Important : Les collections sont hiérarchiques

⚠️ **Attention** :

- Toute collection est rattachée à une collection parente
- La collection racine **Root** ne peut pas être supprimée
- Supprimer une collection **ne supprime pas** les médias — ils remontent vers la collection parente

---

## 📂 Créer une collection

### Méthode 1 — Via l'interface d'administration

1. Connectez-vous à `http://127.0.0.1:8000/admin`
2. Aller dans **Paramètres > Collections**
3. Cliquer sur **Ajouter une collection enfant** sous `Root`
4. Saisir le nom (ex : `Images de blog`) puis **Enregistrer**

---

### Méthode 2 — Via une commande personnalisée

Créez `myapp/management/commands/create_collections.py` :

```python
from django.core.management.base import BaseCommand
from wagtail.models import Collection

class Command(BaseCommand):
    help = "Crée les collections Wagtail par défaut"

    def handle(self, *args, **options):
        root = Collection.get_first_root_node()
        collections = ["Images de blog", "Vidéos", "Documents PDF"]

        for name in collections:
            if not Collection.objects.filter(name=name).exists():
                root.add_child(name=name)
                self.stdout.write(self.style.SUCCESS(f"    OK {name} créée"))
            else:
                self.stdout.write(self.style.WARNING(f"    ⚠️  {name} existe déjà"))

        self.stdout.write(self.style.SUCCESS("\nOK Toutes les collections ont été traitées"))
```

Lancez ensuite :

```bash
python manage.py create_collections
```

Résultat attendu :

```
    OK Images de blog créée
    OK Vidéos créée
    OK Documents PDF créée

OK Toutes les collections ont été traitées
```

---

## 🔄 Opérations courantes

---

### Supprimer une collection


Connectez-vous à http://127.0.0.1:8000/admin
Aller dans Paramètres > Collections
Cliquer sur le nom de la collection à supprimer
En haut de la page, cliquer sur les 3 petits points et "supprimer"
Confirmer la suppression dans la fenêtre de confirmation

---

## 🔍 Vérifier le résultat

Après la création, vérifiez dans l'admin Wagtail :

1. **Les collections**

    `http://127.0.0.1:8000/admin/` > Paramètres > Collections

    Vous devriez voir vos nouvelles collections dans l'arborescence.

2. **Les médias**

    `http://127.0.0.1:8000/admin/images/`

    Le filtre par collection doit être disponible dans la barre latérale.