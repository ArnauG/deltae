#!/usr/bin/env python3
"""Genera la web en tots els idiomes a partir d'una sola plantilla.

  src/template.html   plantilla amb marcadors {{clau}}
  src/lang/<idioma>.json   textos de cada idioma (mateixes claus a tots)

Ús:  python3 build.py
Sortida: index.html (ca), es/index.html, en/index.html, sitemap.xml, robots.txt

Per afegir un text nou: posa {{clau_nova}} a la plantilla i afegeix
"clau_nova" als tres JSON. Els valors poden contenir HTML (<em>, <i>, &amp;...).
Per afegir un idioma: crea src/lang/<codi>.json i afegeix-lo a LANGS.
"""
import json, re, sys
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE_URL = "https://ccdeltae.cat"
OG_IMAGE = f"{BASE_URL}/og-image.png"
EMAIL = "info@ccdeltae.cat"
DEFAULT = "ca"
LANGS = ["ca", "es", "en"]  # el primer va a l'arrel

def out_path(lang):
    return ROOT / ("index.html" if lang == DEFAULT else f"{lang}/index.html")

def url(lang):
    return f"{BASE_URL}/" if lang == DEFAULT else f"{BASE_URL}/{lang}/"

def href(frm, to):
    if frm == to:
        return "./"
    up = "" if frm == DEFAULT else "../"
    return up + ("" if to == DEFAULT else f"{to}/") or "./"

def head_links(lang):
    lines = [f'<link rel="canonical" href="{url(lang)}">']
    lines += [f'<link rel="alternate" hreflang="{l}" href="{url(l)}">' for l in LANGS]
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{url(DEFAULT)}">')
    return "\n".join(lines)

def strip_tags(text):
    return re.sub(r"<[^>]+>", "", text)

def social_meta(lang, t):
    title = escape(strip_tags(t["meta_title"]), quote=True)
    desc = escape(strip_tags(t["meta_description"]), quote=True)
    alt = escape(t.get("_og_image_alt", "Deltae Consulting Color"), quote=True)
    lines = [
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Deltae Consulting Color">',
        f'<meta property="og:locale" content="{t.get("_og_locale", lang)}">',
    ]
    for l in LANGS:
        if l != lang:
            lines.append(f'<meta property="og:locale:alternate" content="{TEXTS[l].get("_og_locale", l)}">')
    lines += [
        f'<meta property="og:url" content="{url(lang)}">',
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{desc}">',
        f'<meta property="og:image" content="{OG_IMAGE}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{alt}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{title}">',
        f'<meta name="twitter:description" content="{desc}">',
        f'<meta name="twitter:image" content="{OG_IMAGE}">',
    ]
    return "\n".join(lines)

def json_ld(lang, t):
    org = f"{BASE_URL}/#org"
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": ["Organization", "LocalBusiness"],
                "@id": org,
                "name": "Deltae Consulting Color",
                "legalName": "Consulting Color Deltae S.L.",
                "alternateName": ["Deltae", "CC Deltae"],
                "url": f"{BASE_URL}/",
                "logo": OG_IMAGE,
                "image": OG_IMAGE,
                "email": EMAIL,
                "description": strip_tags(t["meta_description"]),
                "address": {
                    "@type": "PostalAddress",
                    "postalCode": "08737",
                    "addressLocality": "Torrelles de Foix",
                    "addressRegion": "Barcelona",
                    "addressCountry": "ES",
                },
                "areaServed": {"@type": "AdministrativeArea", "name": "Catalunya"},
                "knowsLanguage": LANGS,
                "sameAs": ["https://portantveus.cat", "https://activapp.cat"],
            },
            {
                "@type": "WebSite",
                "@id": f"{BASE_URL}/#website",
                "url": f"{BASE_URL}/",
                "name": "Deltae Consulting Color",
                "inLanguage": LANGS,
                "publisher": {"@id": org},
            },
            {
                "@type": "WebPage",
                "@id": f"{url(lang)}#webpage",
                "url": url(lang),
                "name": strip_tags(t["meta_title"]),
                "description": strip_tags(t["meta_description"]),
                "inLanguage": lang,
                "isPartOf": {"@id": f"{BASE_URL}/#website"},
                "about": {"@id": org},
            },
        ],
    }
    body = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{body}\n</script>'

def write_sitemap():
    today = date.today().isoformat()
    alts = "".join(
        f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{url(l)}"/>' for l in LANGS
    ) + f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{url(DEFAULT)}"/>'
    urls = "".join(
        f"\n  <url>\n    <loc>{url(l)}</loc>\n    <lastmod>{today}</lastmod>{alts}\n  </url>" for l in LANGS
    )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
           '        xmlns:xhtml="http://www.w3.org/1999/xhtml">'
           f"{urls}\n</urlset>\n")
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")
    print("✓ sitemap.xml")

def write_robots():
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
    print("✓ robots.txt")

def lang_nav(lang, label):
    links = "".join(
        f'<a href="{href(lang, l)}" hreflang="{l}" lang="{l}"'
        + (' aria-current="page"' if l == lang else "")
        + f">{l.upper()}</a>"
        for l in LANGS
    )
    return f'<nav class="lang" aria-label="{label}">{links}</nav>'

GENERATED = {"head_links", "lang_nav", "social_meta", "json_ld"}
TEXTS = {}

def main():
    template = (ROOT / "src/template.html").read_text(encoding="utf-8")
    used = set(re.findall(r"\{\{(\w+)\}\}", template)) - GENERATED
    texts = TEXTS
    texts.update({l: json.loads((ROOT / f"src/lang/{l}.json").read_text(encoding="utf-8")) for l in LANGS})

    errors = []
    for l, t in texts.items():
        keys = {k for k in t if not k.startswith("_")}
        if used - keys:
            errors.append(f"{l}.json: falten claus {sorted(used - keys)}")
        if keys - used:
            errors.append(f"{l}.json: claus que la plantilla no fa servir {sorted(keys - used)}")
    if any("falten" in e for e in errors):
        sys.exit("\n".join(errors))
    for e in errors:
        print("Avís:", e)

    for l in LANGS:
        t = texts[l]
        values = {**t, "head_links": head_links(l), "lang_nav": lang_nav(l, t.get("_label_lang_nav", "Idioma")),
                  "social_meta": social_meta(l, t), "json_ld": json_ld(l, t)}
        html = re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], template)
        p = out_path(l)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")
        print(f"✓ {p.relative_to(ROOT)}")

    write_sitemap()
    write_robots()

if __name__ == "__main__":
    main()
