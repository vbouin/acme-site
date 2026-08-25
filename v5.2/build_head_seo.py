#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pose l'hygiène SEO/GEO sur les pages qui ne sont pas générées par
build_contenus.py : canonical, Open Graph, et JSON-LD.

    python3 build_head_seo.py

Idempotent : relancer ne duplique rien. Les pages générées sont ignorées,
elles portent déjà leur en-tête.

Pourquoi ça compte : sans Open Graph, chaque lien partagé sur LinkedIn
s'affiche dégradé — or LinkedIn est le premier levier d'acquisition d'un
cabinet dont le cycle de décision est long. Et le balisage n'apporte pas
d'autorité, mais il lève l'ambiguïté sur ce que dit la page, ce qui sert
autant les moteurs classiques que les moteurs génératifs.
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
SITE = "https://acmeconsultants.fr"

# Les pages produites par build_contenus.py portent déjà leur en-tête complet.
GENEREES = {"contenus.html", "faq.html", "livre-blanc.html"}

ORG = {
    "@context": "https://schema.org",
    "@type": ["Organization", "ProfessionalService"],
    "name": "ACMÉ Consultants",
    "url": SITE + "/",
    "telephone": "+33 1 72 76 26 53",
    "description": "Cabinet d'études qualitatives à Lyon : focus groups, entretiens "
                   "individuels et analyse de verbatim, du cadrage jusqu'à la décision.",
    "address": {"@type": "PostalAddress", "streetAddress": "24 rue Turbil",
                "postalCode": "69003", "addressLocality": "Lyon", "addressCountry": "FR"},
    "areaServed": ["FR", "EU"],
    "knowsAbout": ["étude qualitative", "focus group", "entretien individuel",
                   "analyse de verbatim", "car clinic", "test de concept"],
}

# Descriptions de repli pour les pages qui n'en ont pas ou dont la longueur
# est hors cible (70-165 caractères : au-delà, la SERP tronque).
DESCRIPTIONS = {
 "index.html": "Cabinet d'études qualitatives à Lyon : focus groups, entretiens individuels et analyse de verbatim, du cadrage jusqu'à la décision.",
 "qui-sommes-nous.html": "Des consultants seniors qui conduisent eux-mêmes le terrain. Quarante ans d'études qualitatives auprès de constructeurs, marques et institutions.",
 "secteur-mobilite.html": "Car clinic, expérience embarquée, électrification, prospective : nos études qualitatives pour les constructeurs et les acteurs de la mobilité.",
 "secteur-retail-fmcg.html": "Shopper research, test de concept, rayon simulé, tracking de marque : nos études qualitatives pour le retail et la grande consommation.",
 "secteur-sante-cosmetiques.html": "Test produit et batterie sensorielle, claims cosmétiques, parcours patient : nos études qualitatives en santé et en cosmétique.",
 "secteur-batiment.html": "Usages et attentes habitat, prescripteurs, points de vente, DIY : nos études qualitatives pour le bâtiment et la distribution de matériaux.",
 "secteur-territoires.html": "Concertation citoyenne, tourisme durable, RSE, cartographie des fragilités : nos études qualitatives pour les territoires et les institutions.",
 "secteur-mode-luxe.html": "Codes du désir, clientèle patrimoniale, expérience boutique, durabilité : nos études qualitatives pour les maisons de mode et de luxe.",
}

# Un service décrit en JSON-LD sur les pages secteur : c'est ce qui lève
# l'ambiguïté entre « page qui parle d'automobile » et « prestataire d'études
# qui intervient dans l'automobile ».
SECTEURS = {
 "secteur-mobilite.html": "Mobilité et automobile",
 "secteur-retail-fmcg.html": "Retail et grande consommation",
 "secteur-sante-cosmetiques.html": "Santé et cosmétiques",
 "secteur-batiment.html": "Bâtiment et distribution de matériaux",
 "secteur-territoires.html": "Territoires, tourisme et RSE",
 "secteur-mode-luxe.html": "Mode et luxe",
}


def lire_meta(s, attr, val):
    for p in (rf'<meta[^>]+{attr}=["\']{re.escape(val)}["\'][^>]*?content=(["\'])(.*?)\1',
              rf'<meta[^>]+content=(["\'])(.*?)\1[^>]*?{attr}=["\']{re.escape(val)}["\']'):
        m = re.search(p, s, re.I | re.S)
        if m:
            return html.unescape(m.group(2))
    return ""


def traiter(f):
    s = f.read_text(encoding="utf-8")
    if "og:title" in s:
        return "déjà fait"

    titre = ""
    m = re.search(r"<title>(.*?)</title>", s, re.S | re.I)
    if m:
        titre = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
    desc = DESCRIPTIONS.get(f.name) or lire_meta(s, "name", "description")

    # Remplacer une description absente ou hors cible
    if f.name in DESCRIPTIONS:
        if re.search(r'<meta\s+name=["\']description["\']', s, re.I):
            s = re.sub(r'<meta\s+name=["\']description["\'][^>]*>',
                       f'<meta name="description" content="{html.escape(desc, quote=True)}" />', s, count=1, flags=re.I)
        else:
            s = s.replace("<title>", f'<meta name="description" content="{html.escape(desc, quote=True)}" />\n<title>', 1)

    blocs = [ORG]
    if f.name in SECTEURS:
        blocs.append({
            "@context": "https://schema.org", "@type": "Service",
            "serviceType": "Étude qualitative — " + SECTEURS[f.name],
            "provider": {"@type": "Organization", "name": "ACMÉ Consultants"},
            "areaServed": ["FR", "EU"],
            "url": f"{SITE}/{f.name}",
        })
    ld = "\n".join('<script type="application/ld+json">%s</script>'
                   % json.dumps(b, ensure_ascii=False, separators=(",", ":")) for b in blocs)

    tete = f'''<link rel="canonical" href="{SITE}/{f.name}" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="ACMÉ Consultants" />
<meta property="og:locale" content="fr_FR" />
<meta property="og:title" content="{html.escape(titre, quote=True)}" />
<meta property="og:description" content="{html.escape(desc, quote=True)}" />
<meta property="og:url" content="{SITE}/{f.name}" />
<meta property="og:image" content="{SITE}/assets/v4/decision.jpg" />
<meta name="twitter:card" content="summary_large_image" />
{ld}
'''
    assert "</head>" in s, f.name
    s = s.replace("</head>", tete + "</head>", 1)
    f.write_text(s, encoding="utf-8")
    return "posé"


def main():
    for f in sorted(ROOT.glob("*.html")):
        if f.name in GENEREES or f.name.startswith(("article-", "cas-")):
            continue
        print(f"  {f.name:34s} {traiter(f)}")


if __name__ == "__main__":
    main()
