# Documentation : Groupes et Permissions dans Wagtail


---


## 📋 Vue d'ensemble


Cette documentation explique comment créer et gérer les **groupes** dans Wagtail. Cela permet de :


- Contrôler qui peut accéder à quelles sections de l'administration
- Restreindre l'accès aux collections de médias par équipe
- Définir des rôles clairs (éditeurs, modérateurs, administrateurs)


---


## 🚨 Important : Groupes Django + Permissions Wagtail


⚠️ **Attention** :


- Les groupes Wagtail s'appuient sur le système de groupes Django natif
- Supprimer un groupe **ne supprime pas** les utilisateurs qui en font partie
- Les collections doivent exister **avant** de leur assigner des permissions


---


## 📂 Créer un groupe


### Méthode 1 — Via l'interface d'administration


1. Connectez-vous à `http://127.0.0.1:8000/admin`
2. Aller dans **Paramètres > Groupes**
3. Cliquer sur **Ajouter un groupe**
4. Saisir le nom (ex : `Éditeurs de blog`)
5. Dans **Permissions sur les collections**, sélectionner la collection et les droits souhaités : `Choisir`, `Ajouter`, `Modifier`, `Supprimer`
6. Cliquer sur **Enregistrer**


---


### Méthode 2 — Via une commande personnalisée


Créez `myapp/management/commands/setup_groups.py` :


```python
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from wagtail.images.models import Image
from wagtail.models import Collection, GroupCollectionPermission


class Command(BaseCommand):
    help = "Crée les groupes Wagtail et leurs permissions"


    def handle(self, *args, **options):
        self.stdout.write("Création des groupes...\n")
        collection = Collection.objects.filter(name="Images de blog").first()
        image_ct = ContentType.objects.get_for_model(Image)


        groupes = {
            "Éditeurs": ["add_image", "change_image"],
            "Modérateurs": ["add_image", "change_image", "delete_image", "choose_image"],
        }


        for nom, codenames in groupes.items():
            group, _ = Group.objects.get_or_create(name=nom)
            for codename in codenames:
                perm = Permission.objects.get(codename=codename, content_type=image_ct)
                GroupCollectionPermission.objects.get_or_create(
                    group=group, collection=collection, permission=perm
                )
            self.stdout.write(self.style.SUCCESS(f"    OK Groupe '{nom}' configuré"))


        self.stdout.write(self.style.SUCCESS("\nOK Tous les groupes ont été configurés"))
```


Lancez ensuite :


```bash
python manage.py setup_groups
```


Résultat attendu :


```
Création des groupes...


    OK Groupe 'Éditeurs' configuré
    OK Groupe 'Modérateurs' configuré


OK Tous les groupes ont été configurés
```


---


## 🔄 Opérations courantes


### Ajouter un utilisateur à un groupe


1. Aller dans **Paramètres > Utilisateurs**
2. Cliquer sur l'utilisateur concerné
3. Dans la section **Rôles**, cocher le groupe souhaité (ex : `Éditeurs de blog`)
4. Cliquer sur **Enregistrer**


---


### Modifier les permissions d'un groupe


1. Aller dans **Paramètres > Groupes**
2. Cliquer sur le groupe à modifier
3. Ajuster les droits dans la section **Permissions sur les collections**
4. Cliquer sur **Enregistrer**


---


### Supprimer un groupe


1. Aller dans **Paramètres > Groupes**
2. Cliquer sur le groupe à supprimer
3. En bas de la page, cliquer sur le bouton rouge **Supprimer**
4. Confirmer la suppression dans la fenêtre de confirmation


---


## 🔍 Vérifier le résultat


Après la création, vérifiez dans l'admin Wagtail :


1. **Les groupes**


    `http://127.0.0.1:8000/admin/` > Paramètres > Groupes


    Vous devriez voir vos groupes avec leurs permissions sur les collections.


2. **Les utilisateurs**


    `http://127.0.0.1:8000/admin/users/`


    Vérifiez que les utilisateurs sont bien rattachés au bon groupe.




