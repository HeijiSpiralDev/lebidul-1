from wagtail.models import Page, Site
from apps.content.models import HomePage, AgendaPage, BidulIndexPage, LieuxIndexPage, ArticleIndexPage

# 1. HomePage Accueil
home = HomePage.objects.get(slug="accueil")

# 2. Pointer le Site vers Accueil
site = Site.objects.first()
old = site.root_page.title
site.root_page = home
site.save()
print(f"Site: {old} -> {home.title}")

# 3. Creer les pages dindex manquantes
def ensure_page(model, title, slug, parent):
    existing = model.objects.filter(slug=slug).first()
    if existing:
        print(f"  Existe deja: {title}")
        return existing
    p = model(title=title, slug=slug, introduction="")
    parent.add_child(instance=p)
    p.save_revision().publish()
    print(f"  Cree: {title}")
    return p

ensure_page(AgendaPage, "Agenda", "agenda", home)
ensure_page(BidulIndexPage, "Les Biduls", "biduls", home)
ensure_page(LieuxIndexPage, "Lieux", "lieux", home)
print("OK repare")
