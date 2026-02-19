CopierDocumentation : Réimporter les données WordPress vers Wagtail

📋 Vue d'ensemble
-

Cette documentation explique comment réimporter complètement les données depuis le dump SQL WordPress vers votre site Wagtail. Cela permet de :

    Mettre à jour le contenu après des modifications dans WordPress
    Corriger des erreurs d'import précédent
    Repartir de zéro avec des données propres


🚨 Important : Ce processus supprime TOUTES les données
⚠️ Attention : La réimportation supprime :

    Tous les articles
    Toutes les images
    Tous les documents (PDFs, Word, Excel, etc.)
    Toutes les catégories
    Tous les auteurs

Les données seront recréées à partir du fichier SQL, mais toute modification manuelle dans l'admin Wagtail sera perdue.


📂 Prérequis
-

Avant de commencer, vérifiez que vous avez :

1. Les fichiers sources

✅ Le dump SQL WordPress : Dump20260209.sql
✅ Le dossier des images : media/images/
✅ Le dossier des documents : media/documents/

2. L'environnement virtuel activé

    ```.venv\Scripts\activate```

    Vous devriez voir (.venv) au début de votre ligne de commande.

3. Les dépendances installées

    ```pip install beautifulsoup4 lxml rarfile python-dotenv```

4. 7-Zip installé (pour les fichiers RAR)

    Télécharger : https://www.7-zip.org/download.html

    Vérifier que ```C:\Program Files\7-Zip\7z.exe existe```

🔄 Processus de réimportation

Étape 1 : Supprimer les données existantes
-

Cette commande supprime toutes les données importées de la base de données.

    python manage.py clear_import --confirm

Ce qui est supprimé :

    ✓ Articles (ArticlePage)
    ✓ Images (Image)
    ✓ Documents (Document)
    ✓ Catégories (Categorie)
    ✓ Auteurs (Auteur)

Résultat attendu :

```
Suppression des donnees...
    OK 122 articles supprimes
    OK 851 images supprimees
    OK 527 documents supprimes
    OK 8 categories supprimees
    OK 2 auteurs supprimes
```

OK Toutes les donnees ont ete supprimees

Étape 2 : Réimporter les données
-

Cette commande lit le dump SQL et réimporte tout dans Wagtail.

```
python manage.py import_from_sql --sql="C:\Chemin\vers\Dump20260209.sql" --prefix="f4yxrr34kc_" --media="C:\Chemin\vers\media\images" --documents="C:\Chemin\vers\media\documents"
```


| Arguments | Description | Exemple |
|----------|-------|-------------|
| `--sql` | Chemin vers le fichier SQL WordPress | C:\...\Dump20260209.sql |
| `--prefix` | Préfixe des tables WordPress dans le SQL | f4yxrr34kc_ |
| `--media` | Dossier contenant les images WordPress | C:\...\media\images |
| `--documents` | Dossier contenant les documents WordPress | C:\...\media\documents |

Résultat attendu :
-
```
========================================
RÉSUMÉ DE L'IMPORT
========================================

categories: 0
authors: 0
articles: à
media: 0
documents: 0
skipped: 0
errors: 0
```

🔍 Vérifier le résultat
-

Après l'import, vérifiez dans l'admin Wagtail :
1. Les images.

    ```http://127.0.0.1:8000/admin/images/```

    Vous devriez voir le nombre d'images importé.

2. Les documents

    ```http://127.0.0.1:8000/admin/documents/```

    Vous devriez voir le nombre de documents importé (PDFs, Word, Excel, etc.).
3. Les articles

    ```http://127.0.0.1:8000/admin/pages/```
    
    Allez dans Chroniques → vous devriez voir le nombre d'articles qui a été importé.

4. Les catégories

    Visibles dans les articles, section "Classification".
5. Le site public

    ```http://127.0.0.1:8000/```
    
    Vérifiez que les articles s'affichent correctement avec leurs images.



🎯 Cas d'usage
-

#### Cas 1 :Mise à jour après modifications WordPress

Si vous avez modifié du contenu dans WordPress et exporté un nouveau dump SQL :

```
1. Supprimer les anciennes données :
python manage.py clear_import --confirm

2. Réimporter avec le nouveau dump :
python manage.py import_from_sql --sql="C:\...\Nouveau_Dump.sql" --prefix="f4yxrr34kc_" --media="C:\...\media\images" --documents="C:\...\media\documents"
```