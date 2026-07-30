#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exporte une variante v4 en UN SEUL fichier HTML autoportant.

Cible : un collègue reçoit le fichier, l'ouvre par double-clic, et tout marche
hors ligne — zéro requête réseau.

Ce que l'export fait, dans l'ordre :

1. INLINE tout ce qui est local — CSS, JS, vidéos, images, logo — en <style>,
   <script> et data: URI.
2. INLINE les polices. Les woff2 latin sont récupérées une fois chez Google et
   mises en cache dans .fonts-cache/ : sans elles, Archivo tomberait sur
   Helvetica et le display perdrait son dessin. Si le réseau manque, on continue
   sans (les piles de repli de styles.css font le travail) et on le dit.
3. ALLÈGE : three.js (600 Ko de CDN) et ses dix boucles WebGL toujours actives
   sautent. C'était le plus gros coût CPU/GPU permanent de la page, et la seule
   dépendance réseau restante. Les deux conteneurs devenus vides sont masqués ;
   .expertise-visual reste, il porte encore son bloc-portrait.
4. NEUTRALISE ce qui n'a pas de sens dans un fichier isolé : la pilule de
   variantes (elle pointerait vers des fichiers absents) et les liens vers les
   pages sœurs — contact devient un mailto, le reste un ancrage mort.

Usage :  python3 export_standalone.py [v4-2|v4-3|all]
"""
import base64
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

DIR = Path(__file__).resolve().parent
CACHE = DIR / ".fonts-cache"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
GF = ("https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800"
      "&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap")

MIME = {".mp4": "video/mp4", ".webp": "image/webp", ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg", ".png": "image/png", ".svg": "image/svg+xml"}


def data_uri(path):
    mime = MIME.get(path.suffix.lower(), "application/octet-stream")
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def cached(url):
    """Télécharge une fois, garde sous .fonts-cache/ : un ré-export est hors ligne."""
    CACHE.mkdir(exist_ok=True)
    key = CACHE / (re.sub(r"[^A-Za-z0-9._-]", "_", url)[-120:])
    if not key.exists():
        key.write_bytes(fetch(url))
    return key.read_bytes()


def inline_fonts():
    """Renvoie un <style> de @font-face en base64, ou '' si le réseau manque."""
    try:
        css = cached(GF).decode("utf-8")
    except (urllib.error.URLError, OSError) as e:
        print(f"[!] polices non récupérées ({e}) — repli sur les piles système")
        return ""
    # on ne garde que le latin : le reste (cyrillique, grec, vietnamien)
    # quadruplerait le poids pour des glyphes que ce site n'écrit jamais
    blocks = [b for b in re.findall(r"/\* (\S+) \*/\s*(@font-face \{.*?\})", css, re.S)
              if b[0] == "latin"]
    out, total = [], 0
    for _, block in blocks:
        m = re.search(r"url\((https://[^)]+\.woff2)\)", block)
        if not m:
            continue
        try:
            raw = cached(m.group(1))
        except (urllib.error.URLError, OSError):
            return ""
        total += len(raw)
        b64 = base64.b64encode(raw).decode("ascii")
        block = block.replace(m.group(0), f"url(data:font/woff2;base64,{b64})")
        out.append(re.sub(r"unicode-range:[^;]+;\s*", "", block))
    print(f"    polices : {len(out)} coupes latin · {total/1024:.0f} Ko")
    return "<style>\n" + "\n".join(out) + "\n</style>\n"


def export(variant):
    src = DIR / f"index-{variant}.html"
    html = src.read_text(encoding="utf-8")

    # ── 1. dépendances réseau : polices inlinées, three.js supprimé ────────
    html = re.sub(r'\s*<link rel="preconnect"[^>]*>', "", html)
    html = re.sub(r'\s*<link href="https://fonts\.googleapis\.com[^>]*>', "", html)
    html = re.sub(r'\s*<script src="https://cdnjs\.cloudflare\.com[^>]*></script>', "", html)
    html = html.replace("</head>", inline_fonts() + "</head>")

    # ── 2. sans three.js, plus de canvas à animer ─────────────────────────
    # On retire l'attribut plutôt que l'élément : main.js ne trouve plus rien à
    # initialiser (donc aucune erreur), et la mise en page ne bouge pas.
    n_canvas = html.count("data-three")
    html = html.replace(" data-three=", " data-was-three=")
    html = html.replace("</head>", """<style>
/* export autoportant : les vitrines 3D sautent avec three.js */
.pillar-viz, .tier-visual { display: none; }
</style>
</head>""")

    # ── 3. CSS et JS locaux inlinés ───────────────────────────────────────
    def css_repl(m):
        return "<style>\n" + (DIR / m.group(1)).read_text(encoding="utf-8") + "\n</style>"
    html = re.sub(r'<link rel="stylesheet" href="([^":]+\.css)"\s*/?>', css_repl, html)

    # variant.js est retiré : sa pilule pointerait vers des fichiers absents
    html = re.sub(r'\s*<script src="variant\.js"></script>', "", html)

    def js_repl(m):
        return "<script>\n" + (DIR / m.group(1)).read_text(encoding="utf-8") + "\n</script>"
    html = re.sub(r'<script src="([^":]+\.js)"></script>', js_repl, html)

    # ── 4. médias en data: URI ────────────────────────────────────────────
    media = sorted(set(re.findall(r'(?:src|poster)="(assets/[^"]+)"', html)))
    total = 0
    for rel in media:
        path = DIR / rel
        total += path.stat().st_size
        html = html.replace(f'"{rel}"', f'"{data_uri(path)}"')
    print(f"    médias : {len(media)} fichiers · {total/1e6:.1f} Mo source")

    # ── 5. liens qui n'existent pas dans un fichier isolé ─────────────────
    html = html.replace('href="contact.html"', 'href="mailto:contact@acme-consultant.fr"')
    for page in ("index.html", "references.html", "territoires.html"):
        html = html.replace(f'href="{page}"', 'href="#" aria-disabled="true"')

    out = DIR / f"ACME-{variant.replace('-', '.')}-autoportant.html"
    out.write_text(html, encoding="utf-8")
    size = out.stat().st_size / 1e6
    left = re.findall(r'(?:src|href)="(?:https?:)?//[^"]+"', html)
    print(f"[écrit] {out.name} — {size:.1f} Mo · canvas 3D retirés : {n_canvas} · "
          f"requêtes réseau restantes : {len(left)} {'✓ autoportant' if not left else left}")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for v in (["v4-2", "v4-3"] if which == "all" else [which]):
        print(f"— {v}")
        export(v)
