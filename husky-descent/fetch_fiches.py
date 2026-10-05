#!/usr/bin/env python3
"""Récupère les résumés Wikipédia (API REST officielle) et les injecte dans les pages du jeu.

Usage :
    python3 fetch_fiches.py index.html [autre.html ...]      # réseau requis (fr.wikipedia.org et en.wikipedia.org)
    python3 fetch_fiches.py --mock mock.json index.html      # test hors réseau, avec des réponses simulées

Le texte de Wikipédia est sous licence CC BY-SA 4.0 : le jeu affiche la source, le titre de l'article
et la licence. Le script garde des phrases entières (2 ou 3 au plus) et ne reformule rien.
"""
import json, os, re, ssl, sys, time, urllib.parse, urllib.request

UA = "HuskyDescent/2.0 (prototype pedagogique Exoflow; contact@exoflow.fr)"

# clé du jeu -> {langue: [titres d'article essayés dans l'ordre]}
CANDIDATES = {
    "husky": {"fr": ["Husky sibérien"], "en": ["Siberian Husky"]},
    "chien": {"fr": ["Chien"], "en": ["Dog"]},
    "chat": {"fr": ["Chat"], "en": ["Cat"]},
    "lapin": {"fr": ["Lapin", "Lapin européen"], "en": ["Rabbit", "European rabbit"]},
    "souris": {"fr": ["Souris commune", "Souris (animal)"], "en": ["House mouse", "Mouse"]},
    "elephant": {"fr": ["Éléphant d'Afrique", "Éléphantidés"], "en": ["African elephant", "Elephant"]},
    "girafe": {"fr": ["Girafe"], "en": ["Giraffe"]},
    "tortue": {"fr": ["Tortue"], "en": ["Turtle"]},
    "grenouille": {"fr": ["Grenouille"], "en": ["Frog"]},
    "canard": {"fr": ["Canard"], "en": ["Duck"]},
    "cochon": {"fr": ["Cochon"], "en": ["Domestic pig", "Pig"]},
    "pingouin": {"fr": ["Manchot", "Spheniscidae"], "en": ["Penguin"]},
    "renard": {"fr": ["Renard roux", "Renard"], "en": ["Red fox", "Fox"]},
    "lion": {"fr": ["Lion"], "en": ["Lion"]},
    "tigre": {"fr": ["Tigre"], "en": ["Tiger"]},
    "panda": {"fr": ["Panda géant"], "en": ["Giant panda"]},
    "vache": {"fr": ["Vache", "Bœuf domestique"], "en": ["Cattle", "Cow"]},
    "mouton": {"fr": ["Mouton"], "en": ["Sheep"]},
    "cheval": {"fr": ["Cheval"], "en": ["Horse"]},
    "zebre": {"fr": ["Zèbre"], "en": ["Zebra"]},
    "ours": {"fr": ["Ours", "Ursidae"], "en": ["Bear"]},
    "loup": {"fr": ["Loup"], "en": ["Wolf"]},
    "hibou": {"fr": ["Hibou"], "en": ["Owl"]},
    "crocodile": {"fr": ["Crocodile"], "en": ["Crocodile"]},
    "koala": {"fr": ["Koala"], "en": ["Koala"]},
}

MAX_CHARS = 330


def fetch(lang, title, mock):
    key = f"{lang}:{title}"
    if mock is not None:
        return mock.get(key)
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title.replace(' ', '_'), safe='')}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    cafile = os.environ.get("SSL_CERT_FILE") or ("/root/.ccr/ca-bundle.crt" if os.path.exists("/root/.ccr/ca-bundle.crt") else None)
    ctx = ssl.create_default_context(cafile=cafile) if cafile else ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:  # réseau bloqué, article absent, etc.
        print(f"  ! {key} : {e}", file=sys.stderr)
        return None


def first_sentences(text):
    """Garde 2 ou 3 phrases entières, sans modifier le texte."""
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?…])\s+(?=[A-ZÀ-ÖØ-Þ«\"'(])", text)
    out = ""
    for p in parts:
        if out and len(out) + 1 + len(p) > MAX_CHARS:
            break
        out = f"{out} {p}".strip()
        if len(out) >= 160:
            break
    if len(out) > MAX_CHARS:  # première phrase trop longue : coupe au mot
        out = out[:MAX_CHARS].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return out


def build(mock):
    fw, missing = {}, []
    for key, langs in CANDIDATES.items():
        entry = {}
        for lang, titles in langs.items():
            for title in titles:
                d = fetch(lang, title, mock)
                time.sleep(0 if mock is not None else 0.25)
                if not d or d.get("type") == "disambiguation" or not d.get("extract"):
                    continue
                url = (d.get("content_urls", {}).get("desktop", {}) or {}).get("page") or f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                entry[lang] = {"t": first_sentences(d["extract"]), "u": url, "n": d.get("title", title)}
                break
            else:
                missing.append(f"{key}/{lang}")
        if entry:
            fw[key] = entry
    return fw, missing


def inject(path, fw):
    html = open(path, encoding="utf-8").read()
    new = "/*FW:BEGIN*/var FW=" + json.dumps(fw, ensure_ascii=False, separators=(",", ":")) + ";/*FW:END*/"
    out, n = re.subn(r"/\*FW:BEGIN\*/.*?/\*FW:END\*/", lambda m: new, html, count=1, flags=re.S)
    if n != 1:
        sys.exit(f"Marqueurs FW introuvables dans {path}")
    open(path, "w", encoding="utf-8").write(out)
    print(f"Injecté dans {path}")


def main(argv):
    mock = None
    if argv and argv[0] == "--mock":
        mock = json.load(open(argv[1], encoding="utf-8"))
        argv = argv[2:]
    if not argv:
        sys.exit(__doc__)
    fw, missing = build(mock)
    print(f"{len(fw)}/{len(CANDIDATES)} animaux avec au moins une langue ; manquants : {missing or 'aucun'}")
    if not fw:
        sys.exit("Aucun extrait récupéré : rien n'est modifié (réseau bloqué ?).")
    json.dump(fw, open(os.path.join(os.path.dirname(os.path.abspath(argv[0])), "fiches.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for p in argv:
        inject(p, fw)


if __name__ == "__main__":
    main(sys.argv[1:])
