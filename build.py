#!/usr/bin/env python3
"""Genera la web en tots els idiomes a partir d'una sola plantilla.

  src/template.html   plantilla amb marcadors {{clau}}
  src/lang/<idioma>.json   textos de cada idioma (mateixes claus a tots)

Ús:  python3 build.py
Sortida: index.html (ca), es/index.html, en/index.html

Per afegir un text nou: posa {{clau_nova}} a la plantilla i afegeix
"clau_nova" als tres JSON. Els valors poden contenir HTML (<em>, <i>, &amp;...).
Per afegir un idioma: crea src/lang/<codi>.json i afegeix-lo a LANGS.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE_URL = "https://ccdeltae.com"
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

def lang_nav(lang, label):
    links = "".join(
        f'<a href="{href(lang, l)}" hreflang="{l}" lang="{l}"'
        + (' aria-current="page"' if l == lang else "")
        + f">{l.upper()}</a>"
        for l in LANGS
    )
    return f'<nav class="lang" aria-label="{label}">{links}</nav>'

def main():
    template = (ROOT / "src/template.html").read_text(encoding="utf-8")
    used = set(re.findall(r"\{\{(\w+)\}\}", template)) - {"head_links", "lang_nav"}
    texts = {l: json.loads((ROOT / f"src/lang/{l}.json").read_text(encoding="utf-8")) for l in LANGS}

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
        values = {**t, "head_links": head_links(l), "lang_nav": lang_nav(l, t.get("_label_lang_nav", "Idioma"))}
        html = re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], template)
        p = out_path(l)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")
        print(f"✓ {p.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
