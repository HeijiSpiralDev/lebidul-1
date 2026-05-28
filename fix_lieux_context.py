path = "apps/content/models/pages.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """    parent_page_types = ["content.HomePage"]
    subpage_types = ["content.LieuPage"]

    class Meta:
        verbose_name = "Index des Lieux\""""

new = old + """

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["lieux"] = (
            LieuPage.objects.live().public().order_by("lieu__nom")
        )
        return context"""

if old in content:
    content = content.replace(old, new)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("OK get_context ajoute!")
else:
    print("Pattern non trouve")
    idx = content.find("Index des Lieux")
    print(repr(content[idx-250:idx+120]))
