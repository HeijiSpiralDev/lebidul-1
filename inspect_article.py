import re
from apps.content.models import ArticlePage

a = ArticlePage.objects.filter(title__icontains="312").first()
print("=" * 50)
print("TITRE:", a.title)
print("TYPE contenu:", type(a.contenu).__name__)
print("IMAGE_PRINCIPALE:", a.image_principale)
print("=" * 50)
for i, block in enumerate(a.contenu):
    val = block.value
    html = val.source if hasattr(val, "source") else str(val)
    print(f"\n--- Bloc {i}: block_type=" + repr(block.block_type) + " value_type=" + type(val).__name__)
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
    if imgs:
        print("  IMAGES:")
        for u in imgs:
            print("   -", u)
    print("  HTML (300 car):", html[:300])
