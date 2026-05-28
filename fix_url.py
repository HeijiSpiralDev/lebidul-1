path = "apps/content/models/pages.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """        url_parts = super().get_url_parts(request=request)
        if url_parts is None:
            return None
        site_id, root_url, _ = url_parts
        return (
            site_id,
            root_url,
            f"/le-bidul-de-{self.bidul.mois}-{self.bidul.annee}-{self.bidul.numero}/",
        )"""

new = """        return super().get_url_parts(request=request)"""

if old in content:
    content = content.replace(old, new)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("OK corrige!")
else:
    print("Pattern non trouve. Contexte:")
    idx = content.find("def get_url_parts")
    print(repr(content[idx:idx+500]))
