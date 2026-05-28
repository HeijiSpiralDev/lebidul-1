path = "apps/content/models/pages.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = "        verbose_name = \"Index des Lieux\""

new = """        verbose_name = "Index des Lieux"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["lieux"] = (
            LieuPage.objects.live().public().order_by("lieu__nom")
        )
        return context"""

if "context[\"lieux\"]" in content:
    print("Deja present!")
elif old in content:
    content = content.replace(old, new)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("OK get_context ajoute!")
else:
    print("Pattern non trouve")
