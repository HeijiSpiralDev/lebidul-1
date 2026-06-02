import os
import json
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from wagtail.rich_text import RichText
from wagtail.models import Page
from apps.content.models import HomePage, ArticleIndexPage, ArticlePage


class Command(BaseCommand):
    help = "Importe les articles WordPress"

    def add_arguments(self, parser):
        parser.add_argument("--json", type=str, default="import_data/articles_clean.json")
        parser.add_argument("--confirm", action="store_true")

    def handle(self, *args, **options):
        json_path = options["json"]
        if not os.path.exists(json_path):
            raise CommandError(f"Fichier non trouve: {json_path}")

        self.stdout.write(self.style.SUCCESS(f"JSON trouve: {json_path}"))

        if not options["confirm"]:
            if input("Continuer? (oui/Non) ").lower() != "oui":
                return

        with open(json_path, encoding="utf-8") as f:
            articles = json.load(f)

        home = HomePage.objects.first()
        if not home:
            root = Page.objects.filter(depth=1).first()
            home = HomePage(title="Accueil", slug="accueil", introduction="")
            root.add_child(instance=home)
            home.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("  HomePage creee"))
        else:
            self.stdout.write(f"  HomePage: {home.title}")

        index = ArticleIndexPage.objects.first()
        if not index:
            index = ArticleIndexPage(title="Articles", slug="articles", introduction="")
            home.add_child(instance=index)
            index.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("  ArticleIndexPage creee"))
        else:
            self.stdout.write(f"  Index: {index.title}")

        self.stdout.write("\nImport des articles...")
        created = 0
        skipped = 0
        for a in articles:
            try:
                if ArticlePage.objects.filter(slug=a["slug"]).exists():
                    skipped += 1
                    continue

                content = a["content"] or "<p></p>"
                try:
                    date = datetime.strptime(a["date"], "%Y-%m-%d").date()
                except:
                    date = datetime(2011, 1, 1).date()

                article = ArticlePage(
                    title=a["title"],
                    slug=a["slug"],
                    date_publication=date,
                    introduction=a["excerpt"][:500],
                    contenu=[("texte", RichText(content))],
                )
                index.add_child(instance=article)
                article.save_revision().publish()
                created += 1

                if created % 20 == 0:
                    self.stdout.write(f"    ... {created} articles")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"    {a['title'][:30]}: {str(e)[:50]}"))

        self.stdout.write(self.style.SUCCESS(f"\n  {created} articles crees ({skipped} ignores)"))
        self.stdout.write(f"Total ArticlePages: {ArticlePage.objects.count()}")
