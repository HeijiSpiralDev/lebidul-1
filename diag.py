from wagtail.models import Page, Site
from apps.content.models import HomePage

print("=== ARBRE DES PAGES ===")
for p in Page.objects.all().order_by("path"):
    indent = "  " * (p.depth - 1)
    print(f"{indent}[{p.depth}] {p.title} (type: {p.specific_class.__name__ if p.specific_class else '?'}) slug={p.slug}")

print("\n=== SITES ===")
for s in Site.objects.all():
    print(f"  {s.hostname}:{s.port} -> root_page: {s.root_page.title} (id={s.root_page.id})")

print("\n=== HOMEPAGES content ===")
for h in HomePage.objects.all():
    print(f"  {h.title} (id={h.id}, path={h.path})")
