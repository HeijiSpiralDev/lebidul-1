import re, json

SQL = "import_data/20260521_bakcup_lebidul.com.sql"

def parse_values(s):
    rows = []
    i = 0
    n = len(s)
    while i < n:
        if s[i] == "(":
            i += 1
            fields = []
            cur = []
            in_str = False
            while i < n:
                c = s[i]
                if in_str:
                    if c == "\\":
                        if i+1 < n:
                            nxt = s[i+1]
                            mapping = {"n":"\n","r":"\r","t":"\t","0":"\0","\\":"\\","'":"'",'"':'"'}
                            cur.append(mapping.get(nxt, nxt))
                            i += 2
                            continue
                        else:
                            i += 1
                            continue
                    elif c == "'":
                        if i+1 < n and s[i+1] == "'":
                            cur.append("'")
                            i += 2
                            continue
                        in_str = False
                        i += 1
                        continue
                    else:
                        cur.append(c)
                        i += 1
                        continue
                else:
                    if c == "'":
                        in_str = True
                        i += 1
                        continue
                    elif c == ",":
                        fields.append("".join(cur))
                        cur = []
                        i += 1
                        continue
                    elif c == ")":
                        fields.append("".join(cur))
                        rows.append(fields)
                        i += 1
                        break
                    else:
                        cur.append(c)
                        i += 1
                        continue
        else:
            i += 1
    return rows

buffer = []
collecting = False
with open(SQL, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        if line.startswith("INSERT INTO `f4yxrr34kc_posts`"):
            collecting = True
            idx = line.find("VALUES")
            buffer.append(line[idx+6:])
        elif collecting:
            buffer.append(line)
            if line.rstrip().endswith(";"):
                collecting = False

raw = "".join(buffer)
all_rows = parse_values(raw)
print(f"Rows parsees: {len(all_rows)}")

def clean_html(html):
    html = re.sub(r"<!--\s*/?wp:.*?-->", "", html)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()

seen_slugs = {}
clean_arts = []
for r in all_rows:
    if len(r) < 23:
        continue
    if r[20] in ("post","page") and r[7] == "publish":
        title = (r[5] or "Sans titre").strip()[:255]
        slug = (r[11] or "").strip()[:50]
        if not slug:
            slug = re.sub(r"[^a-z0-9]+","-", title.lower())[:50]
        slug = slug.strip("-") or "article"
        if slug in seen_slugs:
            seen_slugs[slug] += 1
            slug = f"{slug}-{seen_slugs[slug]}"
        else:
            seen_slugs[slug] = 0
        date = r[2][:10]
        if date == "0000-00-00" or not date:
            date = "2011-01-01"
        clean_arts.append({
            "wp_id": r[0],
            "title": title,
            "slug": slug,
            "date": date,
            "content": clean_html(r[4]),
            "excerpt": clean_html(r[6])[:500],
            "type": r[20],
        })

with open("import_data/articles_clean.json", "w", encoding="utf-8") as f:
    json.dump(clean_arts, f, ensure_ascii=False, indent=2)

print(f"OK {len(clean_arts)} articles ecrits dans import_data/articles_clean.json")
