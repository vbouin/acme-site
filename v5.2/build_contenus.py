#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACMÉ — générateur des pages de contenu (blog, études de cas, livre blanc, FAQ).

Les pages de contenu ne s'écrivent pas à la main : elles partagent toutes le
même chrome (nav, pied de page, Open Graph, JSON-LD) et seul leur corps change.
Un générateur garantit qu'une correction de nav ou de balisage se propage
partout, et que personne n'oublie un JSON-LD.

    python3 build_contenus.py

Sources de vérité :
  - CHIFFRES : « 40 ans » et « 4 000 études » viennent de l'ancien site
    acmeconsultants.fr. Le « 50 ans / 3 500 projets / 400 études » de la
    maquette n'est documenté nulle part — il n'est PAS repris ici.
  - CLIENTS : jamais nommés dans les études de cas. L'accord écrit du client
    est un préalable à toute levée d'anonymat (cf. RECOMMANDATIONS.md).
"""
import html, json, re, sys, pathlib

ROOT = pathlib.Path(__file__).parent
SITE = "https://acmeconsultants.fr"          # domaine à trancher avant mise en ligne

# ── Faits d'entreprise, en un seul endroit ──────────────────────────────
ORG = {
    "name": "ACMÉ Consultants",
    "legalName": "ACMÉ Consultants",
    "tel": "+33 1 72 76 26 53",              # relevé sur acmeconsultants.fr
    "street": "24 rue Turbil",
    "postal": "69003",
    "city": "Lyon",
    "country": "FR",
    "founded": "1985",                        # « +40 ans » sur l'ancien site
    "sameAs": [],
}

SECTEURS = [
    ("secteur-mobilite.html",           "Mobilité &amp; Automobile"),
    ("secteur-retail-fmcg.html",        "Retail et FMCG"),
    ("secteur-sante-cosmetiques.html",  "Santé &amp; Cosmétiques"),
    ("secteur-batiment.html",           "Bâtiment"),
    ("secteur-territoires.html",        "Territoires, Tourisme &amp; RSE"),
    ("secteur-mode-luxe.html",          "Mode &amp; Luxe"),
]

NAV = """<header class="nav">
  <div class="container nav-inner">
    <a href="index.html" class="nav-logo"><img src="assets/logo/logo-noir.png" alt="ACMÉ" /></a>
    <nav class="nav-menu">
      <div class="nav-dd">
      <a href="index.html#sectors" class="nav-dd-trigger"><span data-i18n="nav.sectors">Secteurs</span><span class="nav-dd-caret" aria-hidden="true">&#9662;</span></a>
      <div class="nav-dd-menu">
{secteurs}
      </div>
    </div>
      <a href="decision-rapide.html"{cur_dr} data-i18n="nav.quick">Décision rapide</a>
      <a href="contenus.html"{cur_ct} data-i18n="nav.content">Contenus</a>
      <a href="etudes-et-ia.html"{cur_ia} data-i18n="nav.ia">Études &amp; IA</a>
      <a href="qui-sommes-nous.html"{cur_ab} data-i18n="nav.about">Qui sommes-nous</a>
    </nav>
    <div class="nav-right">
      <div class="lang-toggle" role="group" aria-label="Language">
        <button data-lang="fr" type="button">FR</button>
        <span class="lang-sep">/</span>
        <button data-lang="en" type="button">EN</button>
      </div>
      <a href="contact.html" class="btn btn-primary-dark" style="padding: 12px 20px;">
        <span data-i18n="nav.cta">Démarrer un projet</span>
        <svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none"><path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg>
      </a>
      <button class="nav-burger" aria-label="Menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>"""

FOOTER = """<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <div style="font-family: var(--font-display); font-weight: 700; letter-spacing: 0.22em; font-size: 18px; margin-bottom: 20px;">ACMÉ</div>
        <p data-i18n="footer.about">50 ans d'expertise dans la connaissance client. Siège : 24 rue Turbil, 69003 Lyon, France.</p>
      </div>
      <div>
        <h4 data-i18n="footer.sectors">Secteurs</h4>
        <ul>
{secteurs_footer}
        </ul>
      </div>
      <div>
        <h4 data-i18n="footer.content">Contenus</h4>
        <ul>
          <li><a href="contenus.html" data-i18n="content.nav.articles">Articles</a></li>
          <li><a href="contenus.html#cas" data-i18n="content.nav.cases">Études de cas</a></li>
          <li><a href="livre-blanc.html" data-i18n="content.nav.wp">Livre blanc</a></li>
          <li><a href="faq.html">FAQ</a></li>
        </ul>
      </div>
      <div>
        <h4 data-i18n="footer.contact">Contact</h4>
        <ul>
          <li><a href="mailto:contact@acme-consultant.fr">contact@acme-consultant.fr</a></li>
          <li><a href="contact.html" data-i18n="footer.form">Formulaire</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-esomar">
      <span data-i18n="esomar.member">Membre corporate</span>
      <img src="assets/logos/esomar.png" alt="ESOMAR" loading="lazy">
    </div>
    <div class="footer-legal">
      <div>© <span data-year></span> ACMÉ Consultants · <span data-i18n="footer.legal">Tous droits réservés</span></div>
      <div data-i18n="footer.offices">Lyon · Paris · Munich · Milan</div>
    </div>
  </div>
</footer>"""


def org_jsonld():
    """Organization + LocalBusiness — absents du site, signalés comme manque
    SEO local ET GEO par l'étude concurrentielle."""
    return {
        "@context": "https://schema.org",
        "@type": ["Organization", "ProfessionalService"],
        "name": ORG["name"],
        "url": SITE + "/",
        "telephone": ORG["tel"],
        "foundingDate": ORG["founded"],
        "description": "Cabinet d'études qualitatives à Lyon : focus groups, entretiens individuels et analyse de verbatim, du cadrage jusqu'à la décision.",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": ORG["street"],
            "postalCode": ORG["postal"],
            "addressLocality": ORG["city"],
            "addressCountry": ORG["country"],
        },
        "areaServed": ["FR", "EU"],
        "knowsAbout": [
            "étude qualitative", "focus group", "entretien individuel",
            "analyse de verbatim", "car clinic", "test de concept",
        ],
    }


def breadcrumb(items):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n,
             "item": SITE + "/" + u} for i, (n, u) in enumerate(items)
        ],
    }


# Les pages qui existent dans les deux langues : chacune déclare l'autre.
EN_ALTERNATES = {
    "marche-citadines-france-uk.html": "city-cars-france-uk.html",
    "marche-luxe-clients-perdus.html": "luxury-lost-customers.html",
    "marche-bricolage-peur-de-mal-faire.html": "diy-fear-of-getting-it-wrong.html",
    "contenus.html": "index.html",
}


def page(slug, title, desc, body, extra_jsonld=None, current="", css_extra="",
         breadcrumbs=None, og_type="website", og_image="assets/v4/decision.jpg"):
    sect_nav = "\n".join(
        f'        <a href="{u}" data-i18n="sec5.{k}.title">{lbl}</a>'
        for (u, lbl), k in zip(SECTEURS, ["mob", "fmcg", "sante", "bat", "terr", "mode"]))
    sect_foot = "\n".join(
        f'          <li><a href="{u}" data-i18n="sec5.{k}.title">{lbl}</a></li>'
        for (u, lbl), k in zip(SECTEURS, ["mob", "fmcg", "sante", "bat", "terr", "mode"]))

    nav = NAV.format(
        secteurs=sect_nav,
        cur_dr=' class="current"' if current == "dr" else "",
        cur_ct=' class="current"' if current == "ct" else "",
        cur_ia=' class="current"' if current == "ia" else "",
        cur_ab=' class="current"' if current == "ab" else "",
    )
    foot = FOOTER.format(secteurs_footer=sect_foot)

    blocks = [org_jsonld()]
    if breadcrumbs:
        blocks.append(breadcrumb(breadcrumbs))
    if extra_jsonld:
        blocks.append(extra_jsonld)
    ld = "\n".join(
        '<script type="application/ld+json">%s</script>' %
        json.dumps(b, ensure_ascii=False, separators=(",", ":")) for b in blocks)

    alternates = ""
    if slug in EN_ALTERNATES:
        alternates = (
            f'\n<link rel="alternate" hreflang="fr" href="{SITE}/{slug}" />'
            f'\n<link rel="alternate" hreflang="en" href="{SITE}/en/{EN_ALTERNATES[slug]}" />'
            f'\n<link rel="alternate" hreflang="x-default" href="{SITE}/{slug}" />')

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet" />
<title>{title}</title>
<meta name="description" content="{html.escape(desc, quote=True)}" />
<link rel="canonical" href="{SITE}/{slug}" />{alternates}
<!-- Open Graph : absent du site aujourd'hui, chaque lien partagé sur LinkedIn
     s'affichait dégradé — or LinkedIn est le premier levier d'acquisition. -->
<meta property="og:type" content="{og_type}" />
<meta property="og:site_name" content="ACMÉ Consultants" />
<meta property="og:locale" content="fr_FR" />
<meta property="og:title" content="{html.escape(title, quote=True)}" />
<meta property="og:description" content="{html.escape(desc, quote=True)}" />
<meta property="og:url" content="{SITE}/{slug}" />
<meta property="og:image" content="{SITE}/{og_image}" />
<meta name="twitter:card" content="summary_large_image" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css" />
<link rel="stylesheet" href="styles-v3.css" />
<link rel="stylesheet" href="styles-contenus.css" />{css_extra}
{ld}
</head>
<body class="v3 v3-1">
<script src="variant.js"></script>

{nav}

{body}

{foot}

<script src="i18n.js"></script>
<script src="main.js"></script>
<script>
/* Les boucles d'illustration sont décoratives : sous « mouvement réduit »,
   elles s'arrêtent sur leur poster. `autoplay` ne se désactive pas en CSS,
   d'où ces trois lignes. */
(function () {{
  var vids = document.querySelectorAll('.ct-feature-media video, .wb-media video, .ct-hero-media video');
  if (!vids.length) return;

  // Mouvement réduit : on s'arrête sur le poster. `autoplay` ne se désactive
  // pas en CSS, d'où ces lignes.
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) {{
    vids.forEach(function (v) {{ v.removeAttribute('autoplay'); v.autoplay = false; v.pause(); }});
    return;
  }}

  // `autoplay` seul ne suffit pas toujours : selon le navigateur et l'état de
  // l'onglet au chargement, la lecture reste en pause. On relance à l'entrée
  // dans le viewport, et on met en pause hors champ — inutile de décoder une
  // image qu'on ne voit pas.
  if (!('IntersectionObserver' in window)) return;
  var io = new IntersectionObserver(function (entries) {{
    entries.forEach(function (e) {{
      if (e.isIntersecting) {{
        var pr = e.target.play();
        if (pr && pr.catch) pr.catch(function () {{}});
      }} else {{
        e.target.pause();
      }}
    }});
  }}, {{ threshold: 0.15 }});
  vids.forEach(function (v) {{ io.observe(v); }});
}})();
</script>
</body>
</html>
"""



# ═══════════════════════════════════════════════════════════════════════
#  FIGURES — schémas et infographies en SVG inline
#  Strictement monochrome, comme le reste de l'identité : l'accent est un
#  aplat d'encre ou un trait plus épais, jamais une couleur. Le SVG est
#  inline (pas de fichier) pour rester dans le flux du texte, hériter des
#  tokens CSS et suivre le thème.
#  Chaque figure porte un <title> : c'est ce que lit un lecteur d'écran, et
#  c'est aussi ce qu'un moteur extrait quand il ne rend pas l'image.
# ═══════════════════════════════════════════════════════════════════════

_FIG_N = [0]


def fig(titre, legende, contenu, h=260):
    _FIG_N[0] += 1
    i = _FIG_N[0]
    return (
        # Une ancre par figure : elle permet un lien profond vers un schéma
        # précis, ce qui sert autant en rendez-vous qu'en partage social.
        f'<figure class="fg" id="fig-{i}">\n'
        f'  <svg viewBox="0 0 720 {h}" role="img" aria-labelledby="figt{i}" class="fg-svg">\n'
        f'    <title id="figt{i}">{titre}</title>\n'
        f'{contenu}\n'
        '  </svg>\n'
        f'  <figcaption>{legende}</figcaption>\n'
        '</figure>')


def fig_barres(titre, legende, series, max_val=None):
    """Barres horizontales comparées. series = [(label, valeur, note), ...]"""
    max_val = max_val or max(v for _, v, _ in series)
    out, y = [], 26
    for lab, val, note in series:
        # 340 et non 400 : au-delà, une valeur longue en bout de barre
        # (« ≈ 7 sur 10 ») déborde du viewBox.
        w = 0 if not max_val else (val / max_val) * 340
        out.append(f'<text x="0" y="{y+12}" class="fg-lab">{lab}</text>')
        out.append(f'<rect x="230" y="{y}" width="{w:.1f}" height="17" class="fg-bar"/>')
        out.append(f'<text x="{230+w+10:.1f}" y="{y+13}" class="fg-val">{note}</text>')
        y += 40
    return fig(titre, legende, "\n".join(out), h=y)


def fig_chaine(titre, legende, etapes, pleines=0):
    """Chaîne de maillons. `pleines` = nombre de maillons pleins en tête."""
    n = len(etapes)
    w = (700 - (n - 1) * 12) / n
    # La taille du titre suit la largeur disponible : à cinq maillons, une
    # boîte fait ~132 px et un titre en 13,5 px déborde de son cadre.
    ft = 13.5 if n <= 4 else 12
    fs = 11.5 if n <= 4 else 10.5
    out = []
    for i, (nom, sous) in enumerate(etapes):
        x = i * (w + 12)
        plein = i < pleines
        cls = "fg-box is-full" if plein else "fg-box is-dash"
        tc = "fg-in" if plein else "fg-on"
        sc = "fg-in-s" if plein else "fg-on-s"
        out.append(f'<rect x="{x:.1f}" y="30" width="{w:.1f}" height="94" class="{cls}"/>')
        out.append(f'<text x="{x+14:.1f}" y="54" class="fg-n {tc}">0{i+1}</text>')
        out.append(f'<text x="{x+14:.1f}" y="80" class="{tc} fg-t" style="font-size:{ft}px">{nom}</text>')
        out.append(f'<text x="{x+14:.1f}" y="100" class="{sc} fg-s" style="font-size:{fs}px">{sous}</text>')
        if i:
            out.append(f'<line x1="{x-12:.1f}" y1="77" x2="{x:.1f}" y2="77" class="fg-link"/>')
    return fig(titre, legende, "\n".join(out), h=150)


def _wrap(txt, n=40, lignes=3):
    mots, out, buf = txt.split(), [], ""
    for m in mots:
        if len(buf + " " + m) > n:
            out.append(buf)
            buf = m
        else:
            buf = (buf + " " + m).strip()
    out.append(buf)
    return out[:lignes]


def fig_matrice(titre, legende, axe_x, axe_y, cases):
    """Matrice 2x2. cases = [(col, ligne, titre, texte), ...], col/ligne dans {0,1}"""
    out = [f'<text x="0" y="14" class="fg-ax">{axe_y}</text>',
           f'<text x="716" y="252" class="fg-ax" text-anchor="end">{axe_x}</text>']
    for col, lig, t, txt in cases:
        x, y = 24 + col * 348, 24 + lig * 106
        out.append(f'<rect x="{x}" y="{y}" width="338" height="96" class="fg-box is-dash"/>')
        out.append(f'<text x="{x+16}" y="{y+26}" class="fg-on fg-t">{t}</text>')
        for k, l in enumerate(_wrap(txt, 42, 3)):
            out.append(f'<text x="{x+16}" y="{y+48+k*17}" class="fg-on-s fg-s">{l}</text>')
    out.append('<line x1="18" y1="130" x2="702" y2="130" class="fg-axis"/>')
    out.append('<line x1="360" y1="16" x2="360" y2="234" class="fg-axis"/>')
    return fig(titre, legende, "\n".join(out), h=262)


def fig_jauge(titre, legende, part, texte_dedans, texte_dehors):
    """Une proportion, en un seul trait segmenté de 10 carrés."""
    out = []
    pleins = round(part * 10)
    for i in range(10):
        x = i * 40
        cls = "fg-bar" if i < pleins else "fg-box is-dash"
        out.append(f'<rect x="{x}" y="24" width="30" height="30" class="{cls}"/>')
    out.append(f'<text x="0" y="82" class="fg-on fg-t">{texte_dedans}</text>')
    out.append(f'<text x="0" y="104" class="fg-on-s fg-s">{texte_dehors}</text>')
    return fig(titre, legende, "\n".join(out), h=120)


def stats(items):
    """Bandeau de chiffres sourcés. items = [(valeur, libellé, source), ...]
    Ajouter des statistiques attribuées est l'une des trois tactiques les
    mieux mesurées pour être cité par un moteur génératif."""
    return '<div class="stat-row">' + "".join(
        f'<div><span class="stat-v">{v}</span><span class="stat-l">{l}</span>'
        f'<span class="stat-s">{s}</span></div>' for v, l, s in items) + '</div>'

# ═══════════════════════════════════════════════════════════════════════
#  ARTICLES DE MARCHÉ
#  Le format au meilleur rendement selon l'étude concurrentielle : il
#  produit des reprises, il donne un prétexte de reprise de contact sur
#  tout le portefeuille, et il se cite. Trois secteurs de prédilection.
#  Tous les chiffres sont datés et attribués — c'est la condition pour
#  être repris, par un journaliste comme par un moteur génératif.
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
#  COCON SÉMANTIQUE
#  Un arbre strict, et des règles de liage tenues par le code plutôt que
#  par la discipline : une page cible en tête de silo, des pages
#  intermédiaires, des feuilles. Chaque page lie SON parent et SES frères,
#  jamais une page d'un autre silo.
#
#  C'est ce qui concentre l'autorité thématique sur la page cible, au lieu
#  de la diluer sur vingt-huit pages qui se pointent toutes les unes les
#  autres. Et c'est la même mécanique qui aide un moteur génératif à
#  comprendre de quoi le site fait autorité.
#
#  Les liens en pleine prose restent libres : ils sont contextuels et un
#  lecteur les suit. Ce qui est tenu, c'est le bloc structurel de fin.
# ═══════════════════════════════════════════════════════════════════════

COCONS = {
 "quali": {
   "titre": "L'étude qualitative",
   "cible": "etude-qualitative.html",
   "branches": {
     "Choisir un dispositif": ["article-entretiens-ou-groupes.html",
                               "article-car-clinic.html",
                               "article-focus-group-lyon.html"],
     "Cadrer et budgéter":    ["article-brief-etude-qualitative.html",
                               "article-prix-etude-qualitative.html",
                               "article-decider-vite.html"],
     "Tenir la rigueur":      ["article-declare-observe.html",
                               "article-biais-etude.html",
                               "article-packaging-avant-lecture.html"],
   }},
 "ia": {
   "titre": "L'IA et vos données",
   "cible": "article-ia-etudes-qualitatives.html",
   "branches": {
     "Ce qu'on n'automatise pas": ["article-repondants-synthetiques.html",
                                   "article-verbatims-donnees-personnelles.html",
                                   "livre-blanc.html"],
   }},
 "mobilite": {
   "titre": "Mobilité & Automobile", "cible": "secteur-mobilite.html",
   "branches": {"Le secteur": ["parcours-mobilite.html",
                               "marche-citadines-france-uk.html",
                               "cas-clinique-electrique.html",
                               "cas-utilitaire-artisans.html"]}},
 "fmcg": {
   "titre": "Retail & FMCG", "cible": "secteur-retail-fmcg.html",
   "branches": {"Le secteur": ["parcours-retail-fmcg.html"]}},
 "sante": {
   "titre": "Santé & Cosmétiques", "cible": "secteur-sante-cosmetiques.html",
   "branches": {"Le secteur": ["parcours-sante-cosmetiques.html"]}},
 "batiment": {
   "titre": "Bâtiment", "cible": "secteur-batiment.html",
   "branches": {"Le secteur": ["parcours-batiment.html",
                               "marche-bricolage-peur-de-mal-faire.html",
                               "cas-fichier-client-materiaux.html"]}},
 "luxe": {
   "titre": "Mode & Luxe", "cible": "secteur-mode-luxe.html",
   "branches": {"Le secteur": ["parcours-mode-luxe.html",
                               "marche-luxe-clients-perdus.html"]}},
 "territoires": {
   "titre": "Territoires & RSE", "cible": "secteur-territoires.html",
   "branches": {"Le secteur": ["parcours-territoires.html"]}},
}

# Index inverse : slug → (clé du cocon, nom de branche)
_POS = {}
for _k, _c in COCONS.items():
    _POS[_c["cible"]] = (_k, None)
    for _b, _pages in _c["branches"].items():
        for _p in _pages:
            _POS[_p] = (_k, _b)

# Le titre lisible d'une page, pour construire les libellés de liens
TITRES_COURTS = {}


def cocon_de(slug):
    return _POS.get(slug)


def liens_cocon(slug):
    """Le bloc structurel : le parent, puis les frères de la même branche.
    Rien d'un autre silo — c'est toute la règle."""
    pos = _POS.get(slug)
    if not pos:
        return []
    cle, branche = pos
    c = COCONS[cle]
    liens = []
    if branche is None:
        # Une page cible lie ses enfants directs, branche par branche.
        for pages in c["branches"].values():
            liens += [(TITRES_COURTS.get(p, p), p) for p in pages]
    else:
        liens.append((TITRES_COURTS.get(c["cible"], c["cible"]), c["cible"]))
        liens += [(TITRES_COURTS.get(p, p), p) for p in c["branches"][branche] if p != slug]
    return liens

# ═══════════════════════════════════════════════════════════════════════
#  SIGNATURES
#  Les bylines nommées sont l'un des rares usages d'Ipsos réellement
#  transposables : une prise de position vaut par celui qui la tient.
#  L'attribution suit la compétence réelle, telle que les bios de
#  qui-sommes-nous.html la décrivent.
#
#  ⚠️ Chaque consultant doit relire et valider les articles qui portent sa
#  signature avant publication. Une signature engage une personne.
# ═══════════════════════════════════════════════════════════════════════

AUTEURS = {
 "VJ": {"nom": "Virginie Jost", "role": "Directrice Associée",
        "role_en": "Associate Director", "note": "Quarante ans d'études qualitatives, spécialisée sur la mobilité et les enjeux industriels du secteur automobile."},
 "CC": {"nom": "Céline Crété", "role": "Senior Qualitative Researcher",
        "role_en": "Senior Qualitative Researcher", "note": "Double formation en philosophie et en journalisme. Vingt ans à saisir les attentes profondes au-delà des discours convenus."},
 "TN": {"nom": "Thuy Nguyen", "role": "Project Director",
        "role_en": "Project Director", "note": "Quinze ans de terrains d'études multi-pays. Rigueur d'organisation et accompagnement sur mesure."},
 "VB": {"nom": "Victor Bouin", "role": "Président — Directeur Général",
        "role_en": "Chairman & CEO", "note": "Toujours sur le terrain auprès des utilisateurs. Enseigne le design thinking et l'expérience client à l'emlyon business school."},
}

# ═══════════════════════════════════════════════════════════════════════
#  ARTICLES
#  Angles choisis d'après l'étude concurrentielle : local Lyon (priorité 1),
#  quali + IA en français (priorité 3), et la posture « après N missions,
#  voilà ce qu'on a appris » — la seule qui batte le contenu générique des
#  sites pédagogiques, parce qu'elle ne s'écrit pas sans avoir fait le terrain.
#  Chaque section ouvre sur une réponse directe : c'est ce que les moteurs
#  génératifs citent.
# ═══════════════════════════════════════════════════════════════════════

ARTICLES = [
{
 "slug": "article-focus-group-lyon.html",
 "auteur": "CC",
 "illus": "groupes.webp",
 "faq_titre": 'Questions fréquentes sur les focus groups',
 "faq": [
  ('Combien de temps dure un focus group ?', "Deux heures, rarement plus. Au-delà, l'attention baisse et les participants commencent à répéter ce qu'ils ont déjà dit. Un groupe d'une heure trente bien mené produit davantage qu'un groupe de trois heures."),
  ('Peut-on assister à un focus group en tant que client ?', "Oui, et c'est vivement recommandé — mais derrière une glace sans tain ou par retour vidéo, jamais dans la salle. Cinq personnes en costume au fond de la pièce transforment un groupe en présentation."),
  ('Faut-il enregistrer les groupes ?', "Systématiquement, en audio au minimum, avec le consentement écrit des participants. Sans enregistrement horodaté, aucune conclusion n'est vérifiable — et c'est le premier reproche qu'un comité fera à votre restitution."),
  ("Combien coûte l'organisation d'un focus group à Lyon ?", 'Les repères publics situent un groupe entre 3 000 et 10 000 € tout compris pour 6 à 10 participants, selon la difficulté de recrutement et le niveau de livrable attendu. Le recrutement en représente souvent le premier poste.'),
  ('Peut-on faire un focus group en visioconférence ?', "Oui, et ça fonctionne bien sur des publics dispersés ou difficiles à réunir. Mais l'interaction est plus pauvre&nbsp;: les participants se coupent moins, se relancent moins, et le non-verbal disparaît presque entièrement. À éviter dès qu'il y a du matériel à manipuler."),
 ],
 "aide": {"titre": 'Organiser vos groupes, sans les organiser vous-même', "chapo": "Nous animons des focus groups depuis quarante ans, à Lyon et ailleurs. Le terrain est notre socle&nbsp;: c'est ce qui ne se délègue pas, et c'est ce que nous ne déléguons jamais.", "points": [
   'Recrutement sur critères vérifiés un à un, ou qualification dans votre propre fichier client',
   'Animation par un consultant senior, jamais par un vacataire ni un dispositif automatisé',
   'Salle équipée avec observation, à Lyon comme dans les autres villes de terrain',
   'Transcripts intégraux horodatés, qui vous appartiennent — le reste est à la carte',
 ]},
 "loin": [
  ('Entretiens individuels ou focus groups : comment choisir', 'article-entretiens-ou-groupes.html'),
  ('Combien coûte une étude qualitative ?', 'article-prix-etude-qualitative.html'),
  ("Comment rédiger un brief d'étude qualitative", 'article-brief-etude-qualitative.html'),
 ],

 "sources": [
  ("Espace Rhône", "salles qualitatives lyonnaises équipées (glace sans tain, retour vidéo), en presqu'île depuis 2003", "https://www.espacerhone.com/"),
  ("Lyon Marketing Services", "coordination de terrains qualitatifs à Lyon, en présentiel comme à distance", "https://lyon-marketing-services.fr/etudes-qualitatives/"),
  ("Square Cocoon — Prix d'un focus group", "repères de budget par groupe, 2026", "https://www.squarecocoon.fr/prix-d-un-focus-group/"),
 ],

 "cat": "Terrain",
 "date": "2026-08-25",
 "read": "7 min",
 "title": "Organiser un focus group à Lyon : le guide d'un praticien",
 "h1": 'Huit personnes, deux heures,<br>une salle. Et tout ce<br>qui peut mal tourner.',
 "desc": "Salle, recrutement, taille de groupe, animation : le guide pratique d'un cabinet d'études qualitatives lyonnais, fondé sur les erreurs qu'on a payées.",
 "kw": "focus group Lyon, institut d'études Lyon, étude qualitative Lyon, salle focus group",
 "chapo": "Un focus group raté ne se voit pas le jour même. Il se voit trois semaines plus tard, quand l'analyse ne dit rien qu'on ne savait déjà. Voici où ça se joue — et ce qui, à Lyon, change la donne.",
 "body": """
<h2>Combien de participants dans un focus group ?</h2>
<p><strong>Six à huit personnes, rarement plus.</strong> C'est le point d'équilibre entre deux échecs symétriques : en dessous de cinq, un participant dominant confisque la parole et le groupe devient un entretien à témoins ; au-delà de neuf, la durée de parole individuelle tombe sous les cinq minutes et vous n'obtenez plus que des positions de principe.</p>
<p>Le chiffre qui compte n'est pas le nombre d'inscrits mais le nombre de présents. Sur un recrutement grand public, tablez sur 15 à 20&nbsp;% de défection malgré la confirmation la veille. Nous recrutons donc systématiquement deux personnes de plus que la cible, et nous les indemnisons toutes, y compris celles que nous renvoyons — c'est le coût de la sécurité du dispositif, et il est très inférieur à celui d'un groupe à quatre.</p>

<h2>Faut-il une salle spécialisée ou une salle de réunion suffit-elle ?</h2>
<p><strong>Une salle spécialisée se justifie dès qu'il y a des observateurs.</strong> Si votre équipe marketing veut assister, une salle avec glace sans tain ou retour vidéo change tout : sans elle, vous mettez cinq personnes en costume au fond de la pièce et vous obtenez un groupe qui se surveille.</p>
<p>À Lyon, plusieurs prestataires équipés opèrent en presqu'île, avec streaming et prise de son multipiste — <a href="https://www.espacerhone.com/" rel="nofollow noopener" target="_blank">Espace Rhône</a> y loue des salles qualitatives depuis 2003, et <a href="https://lyon-marketing-services.fr/etudes-qualitatives/" rel="nofollow noopener" target="_blank">Lyon Marketing Services</a> coordonne des terrains en présentiel comme à distance. C'est une commodité réelle du bassin lyonnais : sur beaucoup de villes de taille comparable, il faut monter le dispositif de toutes pièces. Si personne n'observe et que le sujet n'exige pas de matériel, une salle neutre bien insonorisée suffit — et vous économisez un poste.</p>
<p>Deux points que l'on néglige et qui coûtent cher&nbsp;: la table doit être ronde ou ovale (une table rectangulaire crée un bout de table, donc un chef), et la pièce ne doit pas avoir de fenêtre sur rue passante. On a perdu une heure exploitable sur un tramway.</p>

<h2>Comment recruter les bons participants ?</h2>
<p><strong>Le recrutement est le poste où se joue la qualité de l'étude, et c'est aussi le plus cher.</strong> Comptez 200 à 300&nbsp;€ par personne pour un recrutement complet sur critères, indemnisation comprise. C'est souvent le premier poste du budget, avant l'animation elle-même.</p>
<p>Trois leviers pour le maîtriser&nbsp;:</p>
<ul>
  <li><strong>Recruter dans votre propre fichier client.</strong> Si vous disposez d'une base, nous qualifions et prenons les rendez-vous — l'économie est immédiate et le profil est exact. Un distributeur de matériaux nous a un jour transmis deux cents contacts en nous demandant d'en retenir quatre-vingts&nbsp;: c'est le meilleur terrain que nous ayons fait cette année-là.</li>
  <li><strong>Écrire un questionnaire de recrutement qui élimine les professionnels du panel.</strong> Une question sur la dernière participation à une étude, et une question ouverte dont la réponse doit être rédigée&nbsp;: les deux filtres les plus rentables du métier.</li>
  <li><strong>Ne pas sur-spécifier.</strong> Chaque critère ajouté multiplie le coût. Un critère qui n'aura aucun effet sur l'analyse est un critère à retirer.</li>
</ul>

<h2>Focus group ou entretiens individuels ?</h2>
<p><strong>Le groupe révèle les normes, l'entretien révèle les écarts.</strong> Si vous voulez savoir ce qui est acceptable de dire dans un milieu — ce qui se valorise, ce qui se moque —, prenez le groupe&nbsp;: l'interaction fait le travail. Si vous voulez comprendre un parcours réel, une hésitation d'achat, un sujet gênant ou une décision B2B complexe, prenez l'entretien.</p>
<p>Sur les sujets sensibles, le groupe produit une vérité collective très propre et très fausse. Nous l'écartons systématiquement sur la santé, l'argent et tout ce qui touche à la compétence professionnelle de la personne interrogée.</p>
<p class="art-more">Nous avons détaillé cet arbitrage dans un article dédié&nbsp;: <a href="article-entretiens-ou-groupes.html">entretiens individuels ou focus groups, comment choisir</a>.</p>

<h2>Combien de groupes faut-il ?</h2>
<p><strong>Deux groupes par segment que vous voulez pouvoir opposer, jamais un seul.</strong> Un groupe unique ne se lit pas&nbsp;: vous ne savez pas si ce que vous entendez tient au segment ou à la dynamique de cette salle-là. Deux groupes suffisent à distinguer les deux, et c'est la raison pour laquelle un dispositif honnête commence rarement en dessous de quatre groupes s'il compare deux publics.</p>

<h2>Ce que l'animation change réellement</h2>
<p>Un animateur expérimenté ne se reconnaît pas au nombre de questions posées mais au nombre de silences tenus. Les trois secondes qui suivent une réponse convenue sont l'endroit où le participant se reprend et dit la chose intéressante. Un modérateur pressé — ou une relance automatique — comble ce silence et perd la phrase.</p>
<p>C'est aussi pourquoi nous confions l'animation à des consultants seniors&nbsp;: sur un groupe de deux heures, la différence entre un animateur qui suit son guide et un animateur qui suit le groupe représente à peu près la moitié du matériau exploitable.</p>

""" + fig_chaine(
  "Calendrier type d'un dispositif de quatre focus groups",
  "Cinq à sept semaines entre le brief et la restitution. Le recrutement est le seul poste qui se comprime vraiment — et uniquement si vous fournissez le fichier.",
  [("Cadrage", "1 semaine"), ("Recrutement", "2 semaines"),
   ("Terrain", "1 semaine"), ("Analyse et restitution", "1 à 2 semaines")],
  pleines=0) + """<h2>Le calendrier réaliste</h2>
<p><strong>Comptez cinq à sept semaines entre le brief et la restitution</strong> pour un dispositif de quatre groupes&nbsp;: une semaine de cadrage et d'écriture du guide, deux semaines de recrutement, une semaine de terrain, une à deux semaines d'analyse et de restitution. Le recrutement est le seul poste qui se comprime vraiment — et uniquement si vous fournissez le fichier.</p>
<p class="art-more">Vous pouvez composer un dispositif et obtenir son calendrier sur notre <a href="decision-rapide.html#configurateur">configurateur Décision rapide</a>.</p>
""",
},
{
 "slug": "article-ia-etudes-qualitatives.html",
 "auteur": "VB",
 "illus": "ia.webp",
 "faq_titre": "Questions fréquentes sur l'IA dans les études",
 "faq": [
  ("L'IA va-t-elle remplacer les instituts d'études ?", "Elle remplace des tâches, pas un métier. La transcription, la structuration et le premier balayage thématique ont basculé pour de bon. Le cadrage, la conduite du terrain et l'arbitrage entre interprétations concurrentes ne montrent aucun signe de bascule."),
  ("Comment savoir si mon prestataire utilise de l'IA ?", 'Demandez-le, par écrit. La transparence sur les outils employés est un engagement professionnel en France depuis 2025, pas une faveur. Une réponse vague sur ce point est en soi une réponse.'),
  ("L'IA fait-elle baisser le prix d'une étude ?", "Sur certains postes, oui — la transcription ne coûte plus rien. Mais ces postes ne représentaient pas l'essentiel du budget&nbsp;: le recrutement et le temps de consultant, eux, n'ont pas bougé. Une baisse de 80&nbsp;% suppose qu'on a retiré autre chose."),
  ('Mes verbatims servent-ils à entraîner des modèles ?', "Chez nous, non&nbsp;: la transcription passe par un fournisseur français, avec l'entraînement désactivé et sans rétention au-delà du traitement. C'est une question à poser systématiquement, surtout si votre corpus contient des données sensibles."),
  ("Que dit la réglementation sur l'IA en études ?", "Le cadre professionnel français impose une supervision humaine à chaque étape et la transparence sur les outils. S'y ajoutent le RGPD pour les données personnelles des participants et, progressivement, les obligations européennes sur l'IA."),
 ],
 "aide": {"titre": "L'IA chez nous : ce qu'elle fait, par écrit", "chapo": "Nous remettons en avant-vente la répartition exacte entre ce qui est automatisé et ce qui ne l'est jamais. C'est vérifiable, et c'est fait pour l'être.", "points": [
   "Une note écrite sur nos outils, leur rôle et l'endroit où sont vos données",
   "Chaque conclusion remontable jusqu'au verbatim source, horodaté et attribué",
   'Transcription par un fournisseur français, sans entraînement ni rétention',
   'Aucun répondant synthétique dans un corpus livré — jamais',
 ]},
 "loin": [
  ("Peut-on remplacer les répondants par de l'IA ?", 'article-repondants-synthetiques.html'),
  ("Le livre blanc : la parole client jusqu'à la décision", 'livre-blanc.html'),
  ('Décider vite sans décider mal', 'article-decider-vite.html'),
 ],

 "sources": [
  ("Syntec Conseil", "sept engagements pour un usage responsable de l'IA dans les études, mai 2025 — supervision humaine et transparence sur les outils", "https://syntec-conseil.fr/"),
  ("Ipsos — Interviews qualitatives : la révolution IA entre opportunités et limites", "le point de vue d'un grand institut sur l'entretien modéré par IA", "https://www.ipsos.com/fr-fr/interviews-qualitatives-la-revolution-ia-entre-opportunites-et-limites"),
  ("Market Research News — Quelle place donner à l'IA dans les études qualitatives ?", "dossier professionnel en deux volets, 2026", "https://www.mrnews.fr/2026/03/09/dossier-quelle-place-donner-a-l-ia-dans-les-etudes-qualitatives-volet-2/"),
  ("Agalma Études — IA générative et études qualitatives", "analyse détaillée des données synthétiques et des panels simulés", "https://agalma-etudes.com/blog/insights-ia/ia-generative-etudes-qualitatives/"),
 ],

 "cat": "Méthode",
 "date": "2026-08-25",
 "read": "9 min",
 "title": "IA et études qualitatives : ce qu'elle rate encore",
 "h1": "La machine transcrit<br>en deux minutes. Elle<br>n'entend toujours pas<br>l'hésitation.",
 "desc": "Transcription, codage, entretien modéré par IA : ce que l'automatisation apporte vraiment à une étude qualitative, et où elle coûte plus qu'elle ne rapporte.",
 "kw": "IA études qualitatives, IA générative études qualitatives, analyse verbatim IA, répondants synthétiques",
 "chapo": "« Huit fois plus vite, quatre-vingts pour cent moins cher. » La promesse circule, et elle n'est pas entièrement fausse. Elle est vraie sur certains maillons de la chaîne, et franchement dangereuse sur d'autres. Voici lesquels.",
 "body": """
<h2>Où l'IA fait vraiment gagner du temps</h2>
<p><strong>Sur tout ce qui est mécanique et vérifiable.</strong> Trois postes ont basculé pour de bon&nbsp;:</p>
<ul>
  <li><strong>La transcription.</strong> Elle coûtait 20&nbsp;€ de l'heure d'enregistrement, elle en coûte quelques dizaines de centimes. Ce n'est plus un poste de facturation, et prétendre le contraire ne tiendra pas trois questions chez un acheteur informé.</li>
  <li><strong>La structuration du corpus.</strong> Découper, horodater, attribuer les tours de parole, aligner les guides sur les réponses&nbsp;: quelques minutes au lieu d'une journée.</li>
  <li><strong>Le premier balayage thématique.</strong> Sortir les récurrences d'un corpus de trente entretiens, repérer ce qui revient et où, proposer des regroupements. C'est un point de départ d'analyse, pas une analyse.</li>
</ul>
<p>Le gain est réel et nous le prenons&nbsp;: il libère le temps du consultant pour la partie qui ne s'automatise pas. Nous ne le facturons pas comme s'il coûtait encore ce qu'il coûtait.</p>

<h2>Où elle échoue encore</h2>
<p><strong>Partout où il faut arbitrer entre deux lectures également plausibles.</strong> C'est la définition même de l'analyse qualitative, et c'est exactement ce que les modèles font mal&nbsp;: ils produisent une synthèse cohérente, fluide, et qui lisse précisément la contradiction sur laquelle reposait l'intérêt du corpus.</p>
<p>Trois échecs récurrents, observés sur nos propres corpus&nbsp;:</p>
<ul>
  <li><strong>Le nivellement du signal faible.</strong> Ce qui n'est dit que par deux personnes sur trente disparaît de la synthèse. Or c'est souvent là qu'est l'information neuve&nbsp;: la majorité confirme ce que vous saviez.</li>
  <li><strong>La confusion entre ce qui est dit et ce qui est fait.</strong> Un participant qui explique son choix d'achat produit une reconstruction rationnelle. Un analyste entend l'écart entre le récit et le comportement décrit trente secondes plus tard. Le modèle prend les deux pour des faits.</li>
  <li><strong>L'hallucination de citation.</strong> Une synthèse générative produit des verbatims plausibles qui ne figurent pas dans le corpus. C'est la raison pour laquelle nous ne livrons aucune conclusion qui ne soit remontable jusqu'à sa source horodatée.</li>
</ul>

<h2>Et l'entretien modéré par une IA ?</h2>
<p><strong>Il fonctionne sur des sujets simples, à faible enjeu, avec des participants coopératifs — et il s'effondre partout ailleurs.</strong> Sur un test de concept grand public sans matériel, un entretien automatisé produit une matière lisible. Sur un sujet sensible, sur un dirigeant, sur du B2B technique, il ne relance pas au bon endroit parce qu'il ne perçoit ni la gêne, ni l'orgueil professionnel, ni le moment où la personne cherche ses mots.</p>
<p>Le vrai problème n'est pas la qualité de la question suivante&nbsp;: c'est que personne n'était dans la pièce. Ce que l'on perd n'est pas dans la transcription — c'est justement ce qui n'y est pas.</p>

<h2>Les répondants synthétiques sont-ils utilisables ?</h2>
<p><strong>Non, pas comme substitut de terrain.</strong> La profession française a tranché avant nous&nbsp;: <a href="https://syntec-conseil.fr/" rel="nofollow noopener" target="_blank">Syntec Conseil</a> a publié en mai 2025 sept engagements d'usage responsable de l'IA dans les études — supervision humaine à chaque étape, transparence totale sur les outils employés. Et la direction générale d'OpinionWay a publiquement qualifié les entretiens synthétiques de « mirage dangereux » en novembre 2025.</p>
<p>Le débat n'est pas franco-français, et il n'est pas clos&nbsp;: <a href="https://agalma-etudes.com/blog/insights-ia/ia-generative-etudes-qualitatives/" rel="nofollow noopener" target="_blank">Agalma Études</a> accorde aux répondants synthétiques une utilité de pré-test tout en constatant qu'ils échouent à restituer l'émotion, l'hésitation et le silence&nbsp;; <a href="https://www.ipsos.com/fr-fr/interviews-qualitatives-la-revolution-ia-entre-opportunites-et-limites" rel="nofollow noopener" target="_blank">Ipsos</a> parle d'opportunités et de limites. Côté adoption, une enquête Qualtrics citée par la presse professionnelle en 2026 relève que <strong>15 % des chargés d'études déclarent déjà utiliser des agents IA</strong>, et que 78 % estiment qu'ils traiteront plus de la moitié des projets d'ici trois ans. C'est une prévision de praticiens, pas une mesure&nbsp;: à lire comme un climat, pas comme un fait.</p>
<p>La raison est simple&nbsp;: un modèle génère la réponse la plus probable. Une étude qualitative sert à trouver l'improbable — la personne qui n'utilise pas votre produit comme prévu, celle qui a un usage que personne n'avait imaginé. Interroger un modèle revient à interroger la moyenne de ce qui a déjà été écrit, c'est-à-dire exactement ce que vous savez déjà.</p>
<p>Les répondants synthétiques ont un usage honnête et étroit&nbsp;: pré-tester un guide d'entretien, repérer une question mal formulée avant d'engager du terrain réel. Nous les utilisons pour ça, et pour rien d'autre.</p>

""" + fig_chaine(
  "Où l'automatisation mord réellement, maillon par maillon",
  "Les maillons pleins sont ceux que l'IA traite chez nous, parce qu'ils sont mécaniques et vérifiables. Les maillons en pointillé restent humains — non par principe, mais parce que ce sont ceux où il faut arbitrer.",
  [("Transcription", "automatisée"), ("Structuration", "automatisée"),
   ("Premier balayage", "assisté"), ("Analyse", "humaine"),
   ("Recommandation", "humaine")],
  pleines=2) + """<h2>Notre règle : ce que l'IA fait, ce qu'elle ne fait jamais</h2>
<div class="tw">
<table>
<thead><tr><th>Étape</th><th>Ce que l'IA fait chez nous</th><th>Ce qu'elle ne fait jamais</th></tr></thead>
<tbody>
<tr><td>Cadrage</td><td>Rien</td><td>Traduire un enjeu business en dispositif</td></tr>
<tr><td>Recrutement</td><td>Aide au filtrage des candidatures</td><td>Valider un profil sans contrôle humain</td></tr>
<tr><td>Terrain</td><td>Rien</td><td>Animer un groupe ou conduire un entretien</td></tr>
<tr><td>Transcription</td><td>Tout, avec relecture humaine</td><td>Être livrée sans vérification</td></tr>
<tr><td>Analyse</td><td>Premier balayage, regroupements proposés</td><td>Trancher entre deux interprétations</td></tr>
<tr><td>Restitution</td><td>Mise en forme, variantes de formulation</td><td>Écrire la recommandation</td></tr>
</tbody>
</table>
</div>
<p>Cette table n'est pas une précaution rhétorique&nbsp;: c'est la transparence que demandent les engagements Syntec, et c'est ce que nous remettons par écrit en avant-vente.</p>

<h2>Où sont vos données ?</h2>
<p><strong>Chez un fournisseur de transcription français, sans entraînement des modèles sur vos corpus et sans rétention au-delà du traitement.</strong> C'est un point que peu d'acteurs écrivent noir sur blanc, et c'est pourtant la première question d'un service juridique quand le corpus contient des données sensibles.</p>
<p class="art-more">Le détail du protocole figure dans notre livre blanc&nbsp;: <a href="livre-blanc.html">la parole client, structurée jusqu'à la décision</a>.</p>
""",
},
]

ARTICLES += [
{
 "slug": "article-prix-etude-qualitative.html",
 "auteur": "TN",
 "illus": "donnees.webp",
 "faq_titre": "Questions fréquentes sur le budget d'une étude",
 "faq": [
  ('Quel est le budget minimum pour une étude qualitative sérieuse ?', "En dessous de six entretiens ou de deux groupes, le corpus ne se lit plus&nbsp;: vous ne pouvez pas distinguer ce qui tient au public de ce qui tient à la personne. C'est le vrai plancher, et il est méthodologique avant d'être financier."),
  ('Le recrutement peut-il vraiment coûter plus cher que le terrain ?', "Oui, régulièrement. À 200-300 € par participant recruté sur critères, douze entretiens représentent déjà 2 500 à 3 500 € avant qu'un mot n'ait été prononcé. Sur une cible rare, ce montant double."),
  ("Pourquoi les instituts n'affichent-ils pas leurs prix ?", "Parce qu'une étude n'est pas un produit&nbsp;: le même dispositif varie d'un facteur cinq selon la difficulté de recrutement, le nombre de pays et le livrable. C'est une convention de marché — avec l'effet pervers de faire renoncer les acheteurs qui n'ont aucun ordre de grandeur."),
  ('Une étude moins chère est-elle forcément moins bonne ?', "Non, si ce qu'on enlève, ce sont des livrables. Oui, si ce qu'on enlève, c'est le recrutement sur critères ou le nombre de voix. La question à poser n'est pas «&nbsp;pourquoi est-ce moins cher&nbsp;» mais «&nbsp;qu'est-ce qui a été retiré&nbsp;»."),
  ('Comment se déroule un premier échange avec vous ?', 'Une heure de cadrage pour traduire votre décision en question de terrain, puis un chiffrage sous 48 heures, ligne par ligne. Nous donnons un ordre de grandeur dès ce premier échange&nbsp;: c\'est ce qui évite trois propositions calibrées sur trois hypothèses différentes. La préparation de cet échange est détaillée dans notre article sur <a href="article-brief-etude-qualitative.html">le brief d\'étude</a>.'),
 ],
 "aide": {"titre": 'Un chiffrage sous 48 heures, sans engagement', "chapo": "Nous ne pratiquons pas de barème, parce qu'il n'y en a pas d'honnête. Nous chiffrons sur votre question réelle, et nous disons ce que nous retirons quand le budget est contraint.", "points": [
   'Chiffrage ligne par ligne — terrain, transcripts, analyse, atelier — pour que vous puissiez arbitrer',
   'Le levier du fichier client identifié dès le cadrage, quand vous en avez un',
   'Un dispositif alternatif proposé si votre budget ne permet pas celui que vous imaginiez',
   "Et un « passez votre tour » assumé si la question ne justifie pas l'étude",
 ]},
 "loin": [
  ('Décider vite sans décider mal', 'article-decider-vite.html'),
  ("Comment rédiger un brief d'étude qualitative", 'article-brief-etude-qualitative.html'),
  ('Notre offre Décision rapide', 'decision-rapide.html'),
 ],

 "sources": [
  ("Square Cocoon — Prix d'un focus group", "budget moyen 3 000 à 10 000 € par groupe de 6 à 10 personnes (2026)", "https://www.squarecocoon.fr/prix-d-un-focus-group/"),
  ("IntoTheMinds — Combien coûte une étude de marché", "entretien individuel : environ 600 € en B2C, 750 € en B2B", "https://www.intotheminds.com/blog/combien-coute-une-etude-de-marche/"),
  ("Yield Studio", "seul prix d'entrée public du panel observé : UX research à partir de 10 000 € HT", "https://www.yieldstudio.fr/"),
  ("Gladia — tarifs", "transcription automatique à 0,20 $ l'heure d'enregistrement en plan Growth", "https://www.gladia.io/pricing"),
 ],

 "cat": "Repères",
 "date": "2026-08-25",
 "read": "8 min",
 "title": "Combien coûte une étude qualitative ? Les repères 2026",
 "h1": "Le premier poste d'une<br>étude, c'est de trouver<br>les gens.",
 "desc": "Recrutement, terrain, analyse, restitution : ce qui fait réellement le prix d'une étude qualitative, avec les repères publics du marché français en 2026.",
 "kw": "prix étude qualitative, tarif focus group, budget étude qualitative, coût entretien qualitatif",
 "chapo": "Presque aucun institut n'affiche ses prix. Le résultat, c'est un acheteur qui ne sait pas s'il regarde un devis à 8 000 ou à 80 000 euros, et qui renonce à demander. Voici la structure de coût, poste par poste, et les repères publics qui existent.",
 "body": """
<h2>Pourquoi personne n'affiche de prix</h2>
<p><strong>Parce qu'une étude qualitative n'est pas un produit, et que les instituts facturent le même dispositif à des niveaux différents selon le client.</strong> C'est une convention de marché, pas une conspiration&nbsp;: le coût réel dépend de la difficulté de recrutement, du nombre de pays, du matériel à manipuler et du livrable attendu, qui varient d'un facteur cinq.</p>
<p>Cette opacité a toutefois un effet pervers documenté&nbsp;: elle fait renoncer les acheteurs qui n'ont aucune idée de l'ordre de grandeur, et elle laisse le champ libre au premier acteur qui affiche un prix — même s'il ne vend pas la même chose.</p>

""" + fig_barres(
  "Poids relatif des postes dans une étude qualitative resserrée",
  "Ordres de grandeur pour un dispositif de douze entretiens avec livrables intermédiaires. Le recrutement domine, et c'est le seul poste qu'un fichier client fait tomber franchement.",
  [("Recrutement", 34, "le premier poste"),
   ("Terrain", 28, "conduite et captation"),
   ("Analyse et livrables", 26, "selon ce que vous prenez"),
   ("Cadrage", 10, "le plus déterminant"),
   ("Transcription", 2, "devenu marginal")]) + """<h2>Les cinq postes qui font le prix</h2>
<h3>1. Le recrutement — souvent le premier poste</h3>
<p><strong>200 à 300&nbsp;€ par participant</strong> pour un recrutement complet sur critères, indemnisation comprise. Sur douze entretiens, c'est déjà 2 500 à 3 500&nbsp;€ avant qu'un seul mot n'ait été prononcé. Sur une cible rare — un dirigeant, un professionnel de santé, un possesseur d'un équipement précis —, ce montant peut doubler.</p>
<p>C'est le seul poste que vous pouvez faire tomber franchement&nbsp;: si vous fournissez votre fichier client, il ne reste que la qualification et la prise de rendez-vous.</p>

<h3>2. Le terrain</h3>
<p>Un entretien individuel d'une heure, conduit par un consultant senior, coûte nettement moins qu'un groupe de deux heures avec salle, intendance et observateurs. La modalité pèse autant que le volume&nbsp;: le distanciel supprime le déplacement, la salle et une partie de la logistique.</p>

<h3>3. La transcription — un poste qui a disparu</h3>
<p><strong>Il coûtait une vingtaine d'euros par heure d'enregistrement, il en coûte aujourd'hui quelques dizaines de centimes.</strong> Si un devis vous facture encore la transcription au tarif d'avant, c'est une ligne à discuter. Nous l'intégrons au forfait plutôt que de la faire apparaître comme un service.</p>

<h3>4. L'analyse</h3>
<p>C'est le poste le plus élastique, parce qu'il dépend entièrement de ce que vous voulez recevoir. Des transcripts bruts et un corpus structuré ne coûtent pas la même chose qu'un rapport argumenté avec typologies. C'est aussi le poste sur lequel un client capable de travailler lui-même a le plus à gagner à ne pas acheter.</p>

<h3>5. La restitution</h3>
<p>Un document se produit vite. Un atelier de décision animé avec vos équipes demande une préparation spécifique et une demi-journée de deux personnes. C'est aussi, d'expérience, le poste dont le retour est le plus élevé&nbsp;: une étude qui n'est pas discutée en salle ne produit pas de décision.</p>

<h2>Les repères publics du marché français</h2>
<div class="tw">
<table>
<thead><tr><th>Repère</th><th>Niveau publié</th><th>Source</th></tr></thead>
<tbody>
<tr><td>Focus group, tout compris</td><td>3 000 à 10 000&nbsp;€ pour 6 à 10 participants</td><td><a href="https://www.squarecocoon.fr/prix-d-un-focus-group/" rel="nofollow noopener" target="_blank">Square Cocoon</a>, 2026</td></tr>
<tr><td>Entretien individuel B2C</td><td>~600&nbsp;€</td><td><a href="https://www.intotheminds.com/blog/combien-coute-une-etude-de-marche/" rel="nofollow noopener" target="_blank">IntoTheMinds</a></td></tr>
<tr><td>Entretien individuel B2B</td><td>~750&nbsp;€</td><td><a href="https://www.intotheminds.com/blog/combien-coute-une-etude-de-marche/" rel="nofollow noopener" target="_blank">IntoTheMinds</a></td></tr>
<tr><td>Recrutement sur critères</td><td>200 à 300&nbsp;€ par participant</td><td>Fourchette de marché, notre expérience terrain</td></tr>
<tr><td>Entrée UX research affichée</td><td>à partir de 10 000&nbsp;€ HT</td><td><a href="https://www.yieldstudio.fr/" rel="nofollow noopener" target="_blank">Yield Studio</a> — seul prix public du panel</td></tr>
<tr><td>Transcription automatique</td><td>0,20&nbsp;$ / heure d'enregistrement</td><td><a href="https://www.gladia.io/pricing" rel="nofollow noopener" target="_blank">Gladia</a>, plan Growth</td></tr>
<tr><td>Instituts d'études qualitatives</td><td>Aucun prix public</td><td>L'opacité reste la norme du secteur</td></tr>
</tbody>
</table>
</div>
<p class="art-note">Repères relevés en août 2026 sur des sources publiques. Ce sont des ordres de grandeur de marché, pas des tarifs ACMÉ. Un point de repère utile&nbsp;: à 3 000–10 000&nbsp;€ le groupe et 600–750&nbsp;€ l'entretien, un dispositif de quatre groupes ou de douze entretiens se situe dans les mêmes eaux — ce qui explique qu'on arbitre rarement sur le seul prix unitaire.</p>

<h2>Comment faire baisser un budget sans abîmer l'étude</h2>
<ol>
  <li><strong>Fournir votre fichier client.</strong> C'est de loin le levier le plus efficace, et il améliore la qualité du profil au passage.</li>
  <li><strong>Passer en distanciel quand le sujet le permet.</strong> À proscrire dès qu'il y a un produit à manipuler.</li>
  <li><strong>Retirer un critère de recrutement.</strong> Chaque critère ajouté renchérit le sourcing ; certains n'auront aucun effet sur l'analyse.</li>
  <li><strong>Acheter le terrain, pas l'analyse.</strong> Si vos équipes veulent creuser elles-mêmes, prenez les transcripts et une plateforme interrogeable, et gardez l'analyse pour plus tard.</li>
  <li><strong>Ne pas raboter le nombre de groupes en dessous de deux par segment.</strong> C'est la seule économie qui rend l'étude illisible.</li>
</ol>

<h2>Et chez nous ?</h2>
<p>Le chiffrage dépend du secteur, de la difficulté de recrutement et du livrable&nbsp;; nous le remettons sous 48 heures après un échange de cadrage, sans engagement. Vous pouvez composer un dispositif et obtenir son calendrier et sa liste de livrables sur notre <a href="decision-rapide.html#configurateur">configurateur Décision rapide</a> — le chiffrage suit par retour.</p>
""",
},
{
 "slug": "article-entretiens-ou-groupes.html",
 "auteur": "CC",
 "illus": "bulles.webp",
 "faq_titre": 'Questions fréquentes',
 "faq": [
  ("Combien d'entretiens faut-il pour atteindre la saturation ?", "Entre douze et dix-huit sur une cible homogène. La saturation est le moment où un entretien supplémentaire n'apporte plus d'information neuve&nbsp;; elle arrive plus tard dès qu'on croise deux profils ou deux marchés."),
  ('Peut-on mélanger des profils différents dans un même groupe ?', "C'est risqué. Un écart de statut, d'expertise ou d'âge crée une hiérarchie de parole en quelques minutes, et le groupe s'aligne sur le plus assuré. Mieux vaut deux groupes homogènes qu'un groupe mixte."),
  ('Les entretiens en ligne valent-ils les entretiens en face-à-face ?', "Sur un sujet sans matériel, oui, et ils permettent d'atteindre des professionnels qui ne se déplaceraient jamais. Sur un objet à manipuler ou un sujet où le non-verbal porte du sens, non."),
  ('Combien de groupes pour comparer deux cibles ?', "Quatre, soit deux par cible. Avec un seul groupe par cible, vous ne pouvez pas savoir si l'écart observé tient à la cible ou à la dynamique de cette salle-là."),
 ],
 "aide": {"titre": 'Choisir le dispositif avec vous, pas à votre place', "chapo": "Le choix se fait au cadrage, à partir de votre décision — pas à partir d'un catalogue. Il nous arrive de proposer moins que ce qui était demandé.", "points": [
   'Un cadrage qui traduit votre décision en question de terrain avant de choisir la méthode',
   'Le volume calé sur la saturation attendue, pas sur un chiffre rond',
   'Un dispositif mixte quand la question le demande, et seulement dans ce cas',
   'Le calendrier et les livrables arrêtés avec vous, ligne par ligne',
 ]},
 "loin": [
  ("Organiser un focus group : le guide d'un praticien", 'article-focus-group-lyon.html'),
  ("Qu'est-ce qu'une car clinic ?", 'article-car-clinic.html'),
  ('Composer votre dispositif', 'decision-rapide.html#configurateur'),
 ],

 "sources": [
  ("IntoTheMinds — Études qualitatives : aperçu de 3 types d'interviews", "une typologie complémentaire, côté institut belge", "https://www.intotheminds.com/blog/etudes-qualitatives-3-types-interviews/"),
  ("IntoTheMinds — Combien coûte une étude de marché", "les ordres de grandeur par méthode", "https://www.intotheminds.com/blog/combien-coute-une-etude-de-marche/"),
 ],

 "cat": "Méthode",
 "date": "2026-08-25",
 "read": "6 min",
 "title": "Entretiens individuels ou focus groups : comment choisir",
 "h1": "Le groupe révèle<br>une norme. L'entretien<br>révèle un écart.",
 "desc": "Le groupe révèle les normes, l'entretien révèle les écarts. La grille de décision pour choisir selon votre question, votre cible et votre budget.",
 "kw": "entretien individuel ou focus group, choisir méthode qualitative, focus group avantages inconvénients",
 "chapo": "La question revient à chaque cadrage, et la mauvaise réponse ne se paie pas tout de suite. Elle se paie à l'analyse, quand le corpus ne répond pas à la question posée.",
 "body": """
<h2>La règle en une phrase</h2>
<p><strong>Le groupe révèle les normes d'un milieu ; l'entretien révèle les écarts individuels.</strong> Tout le reste — coût, délai, logistique — est secondaire par rapport à cet arbitrage.</p>
<p>Si votre question est « qu'est-ce qui se dit, se valorise ou se moque dans ce milieu&nbsp;? », le groupe fait le travail tout seul&nbsp;: l'interaction produit la norme sous vos yeux. Si votre question est « comment cette personne a-t-elle réellement décidé&nbsp;? », l'entretien est le seul dispositif honnête.</p>

<h2>Ce que le groupe fait mieux</h2>
<ul>
  <li><strong>Faire émerger le vocabulaire spontané d'un milieu.</strong> Les mots que les gens emploient entre eux, et qui ne sont jamais ceux de votre brief.</li>
  <li><strong>Confronter des concepts.</strong> Trois directions créatives posées sur la table, et le désaccord entre participants vous apprend plus que trois notations individuelles.</li>
  <li><strong>Faire apparaître ce qui est socialement acceptable de dire.</strong> Utile quand vous lancez un produit qui touche à un statut.</li>
  <li><strong>Aller vite en volume.</strong> Quatre groupes, c'est vingt-quatre personnes en une semaine.</li>
</ul>

<h2>Ce que l'entretien fait mieux</h2>
<ul>
  <li><strong>Reconstituer un parcours réel.</strong> Le détail des hésitations, les renoncements, ce qui a failli se passer autrement.</li>
  <li><strong>Traiter un sujet sensible.</strong> Santé, argent, compétence professionnelle, échec&nbsp;: en groupe, vous obtiendrez une version présentable.</li>
  <li><strong>Interroger des dirigeants ou des experts.</strong> Ils ne se déplacent pas pour un groupe, et ils ne se livrent pas devant des pairs.</li>
  <li><strong>Suivre un usage dans la durée</strong>, ou revenir sur un même profil après un test.</li>
</ul>

""" + fig_matrice(
  "Ce que révèle chaque dispositif",
  "Le groupe et l'entretien ne donnent pas accès à la même chose. Choisir, c'est d'abord décider si l'on cherche une norme collective ou un écart individuel.",
  "Nature de la question", "Ce que vous obtenez",
  [(0, 0, "Focus group", "La norme d'un milieu : ce qui se valorise, ce qui se moque, le vocabulaire spontané."),
   (1, 0, "Entretien individuel", "L'écart individuel : le parcours réel, les hésitations, ce qui a failli se passer autrement."),
   (0, 1, "À prendre pour", "Concept, packaging, discours de marque, positionnement."),
   (1, 1, "À prendre pour", "Prix, parcours d'achat, sujet sensible, décision B2B complexe.")]) + """<h2>La grille de décision</h2>
<div class="tw">
<table>
<thead><tr><th>Si votre question porte sur…</th><th>Dispositif</th><th>Pourquoi</th></tr></thead>
<tbody>
<tr><td>Un concept, un packaging, un nom</td><td>Groupes</td><td>La confrontation fait ressortir ce qui accroche vraiment.</td></tr>
<tr><td>Un prix, une structure d'offre</td><td>Entretiens</td><td>En groupe, personne n'assume ce qu'il est prêt à payer.</td></tr>
<tr><td>Un parcours d'achat ou d'usage</td><td>Entretiens</td><td>Le détail se perd dès qu'il y a un public.</td></tr>
<tr><td>Un positionnement, un discours de marque</td><td>Groupes</td><td>Vous testez une norme sociale, pas une préférence privée.</td></tr>
<tr><td>Une décision B2B complexe</td><td>Entretiens</td><td>Plusieurs rôles, plusieurs enjeux, jamais dans la même salle.</td></tr>
<tr><td>Un sujet sensible ou intime</td><td>Entretiens</td><td>Le groupe produit une vérité collective très propre et très fausse.</td></tr>
<tr><td>Une exploration large en amont</td><td>Les deux</td><td>Groupes pour la carte, entretiens pour la profondeur.</td></tr>
</tbody>
</table>
</div>

<h2>Combien, dans chaque cas ?</h2>
<p><strong>Deux groupes par segment à comparer ; douze à dix-huit entretiens pour une exploration.</strong> En dessous de deux groupes par segment, vous ne pouvez pas distinguer ce qui tient au public de ce qui tient à la dynamique de la salle. En entretiens, la saturation — le moment où les nouveaux entretiens n'apportent plus rien — arrive généralement entre douze et dix-huit sur une cible homogène, et plus tard dès que vous croisez deux profils.</p>

<h2>Le dispositif mixte, et quand il vaut le coup</h2>
<p>Combiner quelques entretiens en amont puis deux groupes fonctionne très bien quand vous ne savez pas encore quoi demander&nbsp;: les entretiens écrivent le guide des groupes. L'inverse — groupes d'abord, entretiens de confirmation — sert quand un groupe a fait apparaître un profil inattendu qu'il faut aller creuser.</p>
<p>Dans les deux cas, le surcoût est réel&nbsp;: deux recrutements, deux logistiques. Ne le prenez que si la question le demande.</p>
<p class="art-more">Vous pouvez tester les deux configurations, avec leur calendrier, sur le <a href="decision-rapide.html#configurateur">configurateur Décision rapide</a>.</p>
""",
},
]

ARTICLES += [
{
 "slug": "article-decider-vite.html",
 "auteur": "TN",
 "illus": "courbes.webp",
 "faq_titre": 'Questions fréquentes sur les dispositifs courts',
 "faq": [
  ('Quel est le délai minimum réaliste pour une étude qualitative ?', "Quatre semaines, à trois conditions&nbsp;: une question unique, un recrutement dans votre propre base client, et un terrain à distance. En dessous, ce qu'on gagne se prend sur le recrutement ou sur le nombre de voix, c'est-à-dire sur la validité."),
  ('Un dispositif court est-il moins fiable ?', "Pas s'il retire des livrables plutôt que du terrain. Un dispositif court honnête garde le recrutement sur critères et le nombre minimal de voix&nbsp;; il enlève le rapport complet, les typologies ou la restitution formelle."),
  ("Peut-on démarrer un terrain sans guide d'entretien finalisé ?", "Non. La semaine de cadrage est la seule qu'il ne faut jamais comprimer&nbsp;: c'est elle qui détermine la valeur de tout ce qui suit. Un terrain lancé sur un guide bâclé produit vite un matériau inexploitable."),
  ("Comment vérifier qu'un prestataire rapide ne bâcle pas ?", 'Trois questions&nbsp;: qui a recruté les participants et sur quels critères vérifiés&nbsp;; qui était dans la pièce&nbsp;; et cette conclusion précise, elle remonte à quel verbatim, à quel horodatage.'),
 ],
 "aide": {"titre": 'Décision rapide : un socle, des options', "chapo": 'Notre offre courte est construite exactement sur ce principe&nbsp;: le terrain ne bouge pas, les livrables se choisissent. Vous ne payez que ce dont vous avez besoin pour décider.', "points": [
   'Cadrage, recrutement, terrain et transcripts intégraux : toujours inclus',
   'Plateforme verbatim, top lines, analyse complète, typologies, atelier : à la carte',
   'Le configurateur vous donne le calendrier et les livrables en deux minutes',
   'Chiffrage sous 48 heures, sans engagement',
 ]},
 "loin": [
  ('Notre offre Décision rapide', 'decision-rapide.html'),
  ('Combien coûte une étude qualitative ?', 'article-prix-etude-qualitative.html'),
  ("Peut-on remplacer les répondants par de l'IA ?", 'article-repondants-synthetiques.html'),
 ],

 "sources": [
  ("Market Research News", "dossiers professionnels sur l'automatisation de la chaîne d'étude", "https://www.mrnews.fr/"),
  ("IntoTheMinds — Peut-on remplacer les répondants par l'IA ?", "l'état du débat côté institut", "https://www.intotheminds.com/blog/en/qualitative-interviews-ai/"),
  ("Gladia — tarifs", "l'ordre de grandeur qui a fait disparaître la transcription des postes facturables", "https://www.gladia.io/pricing"),
 ],

 "cat": "Point de vue",
 "date": "2026-08-25",
 "read": "8 min",
 "title": "Décider vite sans décider mal : le dispositif court",
 "h1": "Six semaines, ce n'est pas<br>six mois compressés.",
 "desc": "« 8× plus vite, 80 % moins cher » : ce que ces promesses compressent, ce qu'elles sacrifient, et comment cadrer un dispositif court qui tienne.",
 "kw": "étude qualitative rapide, quick study, dispositif court étude, décision rapide étude marché",
 "chapo": "Le marché des études s'est mis à vendre de la vitesse. La question n'est pas de savoir si c'est possible — c'est de savoir ce qu'on enlève pour y arriver, et si ce qu'on enlève est ce dont on avait besoin.",
 "body": """
<h2>Que compresse-t-on réellement quand on va plus vite ?</h2>
<p><strong>Sur une étude qualitative, quatre postes se compriment sans dommage, et trois ne se compriment pas.</strong> Confondre les deux listes, c'est produire vite un matériau qui ne répond pas à la question.</p>
<p>Se compriment&nbsp;: la transcription (aujourd'hui quasi instantanée), la structuration du corpus, le premier balayage thématique, et la mise en forme du livrable. Ensemble, ces quatre postes représentaient il y a cinq ans une part considérable du délai d'une étude. Les récupérer est un gain net, et tout le monde devrait le prendre.</p>
<p>Ne se compriment pas&nbsp;: le recrutement d'une cible difficile, la conduite du terrain, et l'arbitrage entre deux interprétations concurrentes. Ces trois-là sont des durées incompressibles parce qu'elles dépendent de disponibilités humaines et de jugement, pas de puissance de calcul.</p>

<h2>D'où vient le « quatre-vingts pour cent moins cher »</h2>
<p>Il vient presque entièrement de la suppression du terrain humain&nbsp;: pas de recrutement sur critères vérifiés, pas d'animateur, pas d'indemnisation — ou un panel propriétaire déjà amorti. C'est une économie réelle, et sur certaines questions elle est parfaitement légitime.</p>
<p>Elle cesse de l'être dès que l'un de ces trois cas se présente&nbsp;:</p>
<ul>
  <li><strong>La cible est rare ou professionnelle.</strong> Un panel généraliste vous donnera des gens qui ressemblent à votre cible, ce qui est exactement le problème.</li>
  <li><strong>Le sujet est sensible.</strong> Un dispositif sans humain dans la pièce ne perçoit ni la gêne, ni le moment où quelqu'un se reprend.</li>
  <li><strong>Il y a du matériel à manipuler.</strong> Un produit se touche, un véhicule se regarde de trois quarts arrière, une maquette se prend en main.</li>
</ul>

<h2>La bonne question n'est pas « combien de temps » mais « quoi en moins »</h2>
<p>Un dispositif court honnête ne raccourcit pas le terrain&nbsp;: il <strong>retire des livrables</strong>. C'est la différence entre une étude compressée et une étude amputée.</p>
<p>Concrètement, la liste de ce qu'on peut retirer sans abîmer la validité&nbsp;:</p>
<ul>
  <li>Le rapport complet, si vos équipes préfèrent travailler sur le corpus elles-mêmes.</li>
  <li>Les typologies, si vous ne comptez pas les réutiliser en ciblage.</li>
  <li>La restitution formelle, si un atelier de travail suffit.</li>
  <li>Le multi-pays, si la décision porte d'abord sur un marché.</li>
</ul>
<p>Et la liste de ce qu'il ne faut pas retirer&nbsp;: le recrutement sur critères vérifiés, le nombre minimal de voix pour que le corpus se lise (deux groupes par segment, ou une douzaine d'entretiens), et le cadrage — qui prend une semaine et qui détermine la valeur de tout le reste.</p>

""" + fig_chaine(
  "Ce qui se comprime, et ce qui ne se comprime pas",
  "Les maillons pleins se compriment sans dommage. Les maillons en pointillé dépendent de disponibilités humaines et de jugement : les raccourcir, c'est retirer de la validité, pas du délai.",
  [("Transcription", "quasi instantanée"), ("Structuration", "automatisée"),
   ("Recrutement", "incompressible"), ("Terrain", "incompressible"),
   ("Arbitrage", "incompressible")],
  pleines=2) + """<h2>À quoi ressemble un dispositif court qui tient</h2>
<p><strong>Quatre à sept semaines, une seule question, un terrain réel, des livrables choisis.</strong> Le calendrier type&nbsp;:</p>
<div class="tw">
<table>
<thead><tr><th>Phase</th><th>Durée</th><th>Ce qui la raccourcit</th></tr></thead>
<tbody>
<tr><td>Cadrage et guide</td><td>1 semaine</td><td>Une question unique, pas trois.</td></tr>
<tr><td>Recrutement</td><td>1 à 2 semaines</td><td>Votre fichier client — le seul vrai levier.</td></tr>
<tr><td>Terrain</td><td>1 à 2 semaines</td><td>Le distanciel, quand le sujet le permet.</td></tr>
<tr><td>Livrables</td><td>1 à 2 semaines</td><td>Le choix de ce que vous prenez.</td></tr>
</tbody>
</table>
</div>
<p>C'est le principe de notre offre <a href="decision-rapide.html">Décision rapide</a>&nbsp;: un socle qui ne bouge jamais — cadrage, recrutement, terrain, transcripts intégraux — et des livrables à la carte.</p>

<h2>Les trois questions à poser à n'importe quel prestataire rapide</h2>
<ol>
  <li><strong>« Qui a recruté les participants, et sur quels critères vérifiés ? »</strong> Si la réponse est « notre panel », demandez le taux de participation aux études antérieures des répondants.</li>
  <li><strong>« Qui était dans la pièce ? »</strong> Et, si personne&nbsp;: comment les relances ont-elles été décidées&nbsp;?</li>
  <li><strong>« Cette conclusion, je peux remonter à quel verbatim ? »</strong> C'est la question qui distingue une synthèse d'une reconstruction plausible. Elle doit avoir une réponse en trois secondes, horodatée.</li>
</ol>

<h2>Quand un dispositif court n'est-il pas la bonne réponse ?</h2>
<p>Nous le disons en cadrage plutôt qu'en fin de mission&nbsp;: une question qui porte sur plusieurs marchés, une refonte de positionnement, une exploration sans hypothèse de départ ou un sujet où l'entreprise est divisée en interne ne se traitent pas en cinq semaines. Le format court sert à trancher une question précise, pas à remplacer une étude de fond — et le vendre comme tel serait exactement le raccourci que nous reprochons au reste du marché.</p>
""",
},
]

# ═══════════════════════════════════════════════════════════════════════
#  ÉTUDES DE CAS
#  Trois missions réelles, ANONYMISÉES. Le dispositif est exact ; aucun
#  résultat chiffré n'est avancé. Le nom du client ne peut être publié
#  qu'avec son accord écrit — cf. RECOMMANDATIONS.md.
# ═══════════════════════════════════════════════════════════════════════

CAS = [
{
 "slug": "cas-utilitaire-artisans.html",
 "auteur": "VJ",
 "illus": "terrain.webp",
 "sources": [
  ('Marché automobile français S1 2026', "le contexte de marché dans lequel s'inscrit ce type d'arbitrage produit", 'https://www.cartegrise.com/blog/2026/07/marche-automobile-francais-s1-2026-le-grand-bilan-dun-semestre-de-bascule'),
 ],

 "impact": {"titre": 'Ce que ça a changé', "chapo": "Une étude ne vaut que par les décisions qu'elle permet. Voici où celle-ci a pesé, et à quel moment.", "note": "Les effets décrits sont ceux constatés avec les équipes du client. Aucun chiffre d'affaires ni indicateur commercial n'est publié ici — ils appartiennent au client.", "cartes": [
   ('Décision engagée', "Les arbitrages d'aménagement intérieur ont été repris avant le gel du cahier des charges — donc avant que la modification ne coûte un outillage."),
   ('Ce qui a été évité', 'Une hiérarchie de fonctions établie sur des remontées après-vente plates, qui ne signalaient aucune insatisfaction alors que les parts de marché bougeaient.'),
   ('Ce qui a été gagné', "Un vocabulaire d'usage réutilisable en brief créatif et en argumentaire réseau, dans les mots des artisans plutôt que dans ceux du marketing."),
   ('Effet de levier', "Le troisième groupe, composé de participants réinvités, n'a coûté aucun recrutement supplémentaire et a produit la matière la plus dense du dispositif."),
 ]},
 "faq": [
  ('Pourquoi réinviter un groupe déjà interrogé ?', "Parce que le premier passage sensibilise. Entre les deux séances, les participants portent attention à des choses qu'ils ne remarquaient plus, et reviennent avec des observations précises. Le coût est marginal — pas de nouveau recrutement — et le rendement est le meilleur du dispositif."),
  ('Comment interroger des professionnels qui ne se plaignent jamais ?', "En ne posant aucune question de satisfaction. On fait raconter une journée type, minute par minute&nbsp;: le chargement, le trajet, la recherche d'un outil, l'arrivée chez le client. Les contraintes apparaissent d'elles-mêmes, hiérarchisées par la fréquence à laquelle elles reviennent."),
  ('Faut-il faire du terrain dans plusieurs pays ?', "Dès que la décision porte sur plusieurs marchés, oui. C'est le seul moyen de séparer ce qui relève d'un usage professionnel universel de ce qui relève d'habitudes locales — et les arbitrages produit dépendent directement de cette distinction."),
 ],
 "aide": {"titre": 'Interroger des professionnels difficiles à faire parler', "chapo": "Artisans, TPE, prescripteurs, chefs de chantier : ce sont des publics qui n'ont ni le temps ni l'habitude de l'étude. C'est une part importante de notre terrain.", "points": [
   'Recrutement sur activité réelle, vérifié, ou qualification dans votre fichier client',
   "Guides construits sur le récit d'usage plutôt que sur l'évaluation",
   'Terrain en présentiel comme à distance, selon la disponibilité de la cible',
   "Restitution en atelier avec vos équipes produit et marketing, jusqu'à l'arbitrage",
 ]},
 "loin": [
  ("Qu'est-ce qu'une car clinic ?", 'article-car-clinic.html'),
  ('Citadines : France et Royaume-Uni', 'marche-citadines-france-uk.html'),
  ('Notre secteur Mobilité & Automobile', 'secteur-mobilite.html'),
 ],

 "cat": "Mobilité & Automobile",
 "date": "2026-08-25",
 "read": "5 min",
 "title": "Cas — Un utilitaire pour artisans qui ne se plaignent jamais",
 "h1": "Concevoir un utilitaire<br>pour des artisans qui<br>ne se plaignent jamais.",
 "desc": "Étude de cas anonymisée : trois focus groups et des entretiens dans deux pays pour cadrer la prochaine génération d'un utilitaire léger.",
 "kw": "étude qualitative automobile, focus group artisans, étude véhicule utilitaire",
 "meta": [("Secteur", "Mobilité &amp; Automobile"), ("Dispositif", "3 focus groups + entretiens"),
          ("Terrain", "France et Italie"), ("Livrables", "Rapport, typologies, atelier")],
 "chapo": "Un constructeur européen préparait la génération suivante de son utilitaire léger. Le brief tenait en une phrase : « nos clients nous disent que tout va bien, et ils achètent ailleurs. »",
 "body": """
<h2>Le problème</h2>
<p>Les artisans et très petites entreprises constituent un public d'étude difficile pour une raison précise&nbsp;: le véhicule est un outil de travail, pas un objet de désir, et l'insatisfaction ne s'exprime pas spontanément. Interrogés directement, ils déclarent que le véhicule « fait le job ». Les remontées après-vente étaient plates, et pourtant les parts de marché bougeaient.</p>

<h2>Le dispositif</h2>
<p>Trois groupes segmentés — artisans et TPE d'un côté, PME structurées de l'autre, puis un troisième groupe de participants réinvités après un temps de latence — complétés par des entretiens individuels dans un second marché européen pour tester la robustesse des constats hors de France.</p>
<p>Le troisième groupe, réinvité, est le choix qui a fait la différence&nbsp;: revoir les mêmes personnes après quelques semaines, une fois qu'elles ont eu l'occasion de porter attention à leur usage, produit un matériau que le premier passage ne donne jamais.</p>

<h2>Ce que le terrain a fait apparaître</h2>
<p>L'écart tenait à la façon de poser la question. Tant qu'on interroge la satisfaction, on obtient une évaluation. Dès qu'on fait raconter une journée — le chargement à 6 h 30, le passage sous un porche, la recherche d'un outil au fond du véhicule, le client qui regarde la camionnette se garer devant chez lui —, on obtient des contraintes précises, hiérarchisées, et qui n'apparaissaient dans aucun questionnaire.</p>
<p>La comparaison entre les deux marchés a par ailleurs séparé nettement ce qui relevait d'un usage professionnel universel de ce qui relevait d'habitudes locales — une distinction dont les arbitrages produit dépendaient directement.</p>

<h2>Ce qui a été livré</h2>
<ul>
  <li>Un corpus complet de transcripts horodatés, remis intégralement.</li>
  <li>Une analyse structurée par moment d'usage plutôt que par fonction du véhicule.</li>
  <li>Des typologies d'usage professionnel réutilisables en ciblage.</li>
  <li>Un atelier de travail avec les équipes produit et marketing pour transformer les constats en arbitrages.</li>
</ul>

<h2>Que retenir pour d'autres missions ?</h2>
<p>Sur un public professionnel, la question « êtes-vous satisfait » ne produit rien. La question « racontez-moi votre mardi » produit tout. Et le réinvitation d'un groupe est le meilleur rapport qualité-prix d'un dispositif qualitatif&nbsp;: pas de nouveau recrutement, un matériau nettement plus profond.</p>
""",
},
{
 "slug": "cas-clinique-electrique.html",
 "auteur": "VJ",
 "illus": "objet.webp",
 "sources": [
  ("Atlas Automobiles — marché français, record pour l'électrique", "la dynamique de l'électrique sur le marché français en 2026", 'https://atlas-automobiles.com/articles/aamarche-automobile-france-mai-2026-3-7-d-immatriculations-et-record-historique-pour-l-electrique'),
 ],

 "impact": {"titre": 'Ce que ça a changé', "chapo": "La clinique existe pour un usage précis : rendre visible l'écart entre ce qui se dit et ce qui se fait, au moment où l'on peut encore corriger.", "note": "Les effets décrits sont ceux constatés avec les équipes du client. Aucune donnée produit ni commerciale n'est publiée ici.", "cartes": [
   ('Décision engagée', "L'arbitrage entre les directions a été rendu avant le gel du projet, avec les verbatims sources à l'appui de chaque recommandation."),
   ('Ce qui a été évité', "Un choix fondé sur la hiérarchie déclarée des critères — qui ne coïncidait pas avec la hiérarchie observée devant l'objet."),
   ('Ce qui a été gagné', "Une lecture séparée du déclaré et de l'observé, poste par poste, que les équipes design ont pu opposer aux convictions internes."),
   ('Effet de levier', 'Le recrutement sur véhicule concurrent réellement possédé — le critère le plus coûteux à sourcer, et celui qui a rendu les avis opérants.'),
 ]},
 "faq": [
  ("Pourquoi n'interroger que des possesseurs de véhicules concurrents ?", "Parce que l'avis d'un conducteur qui ne possède pas la catégorie porte sur ses représentations — l'autonomie fantasmée, la recharge redoutée. Celui d'un possesseur porte sur l'usage réel, et c'est le seul qui permette d'arbitrer un design ou une interface."),
  ("Le présentiel est-il indispensable pour ce type d'étude ?", "Oui, sans exception. Les réactions les plus utiles ont lieu pendant les déplacements autour du véhicule, pas pendant les questions. Aucun dispositif à distance ne restitue les trente secondes où quelqu'un tourne autour d'une voiture."),
  ('À quoi servent les entretiens individuels après une clinique ?', "À revenir, hors du regard des autres participants, sur les points où la dynamique de salle a produit un consensus trop rapide. C'est souvent là que l'on récupère les objections que personne n'a osé formuler devant les autres."),
 ],
 "aide": {"titre": 'Monter une clinique produit', "chapo": "C'est notre dispositif de signature, sur le secteur le plus exigeant que nous connaissions. Nous en animons depuis quarante ans.", "points": [
   'Recrutement sur véhicule réellement possédé, vérifié un à un',
   'Protocole de passage écrit à la minute, avec les relances par station',
   'Logistique produit, confidentialité et gardiennage pris en charge',
   "Analyse qui sépare explicitement le déclaré de l'observé",
 ]},
 "loin": [
  ("Qu'est-ce qu'une car clinic ?", 'article-car-clinic.html'),
  ('Citadines : France et Royaume-Uni', 'marche-citadines-france-uk.html'),
  ('Composer votre dispositif', 'decision-rapide.html#configurateur'),
 ],

 "cat": "Mobilité & Automobile",
 "date": "2026-08-25",
 "read": "5 min",
 "title": "Cas — Arbitrer un design par les conducteurs de la concurrence",
 "h1": "Faire arbitrer un design<br>par ceux qui conduisent<br>déjà la concurrence.",
 "desc": "Étude de cas anonymisée : une clinique produit auprès de possesseurs de véhicules électriques concurrents, pour arbitrer avant le gel du projet.",
 "kw": "car clinic, test de concept automobile, étude design véhicule électrique",
 "meta": [("Secteur", "Mobilité &amp; Automobile"), ("Dispositif", "Clinique produit + entretiens"),
          ("Terrain", "Deux villes françaises"), ("Livrables", "Rapport, restitution animée")],
 "chapo": "Un constructeur devait trancher entre plusieurs directions de design et d'interface avant le gel du projet. La contrainte : n'interroger que des gens qui roulent déjà en électrique, chez la concurrence.",
 "body": """
<h2>Le problème</h2>
<p>Sur un véhicule électrique, l'avis d'un conducteur thermique porte surtout sur ses représentations de l'électrique — l'autonomie fantasmée, la recharge redoutée. L'avis d'un conducteur qui en possède déjà un porte sur l'usage réel, et il est infiniment plus opérant pour arbitrer un design ou une interface.</p>
<p>Le recrutement devenait donc le point dur&nbsp;: il fallait des possesseurs de modèles concurrents précis, disponibles sur une plage courte, et prêts à venir en salle.</p>

<h2>Le dispositif</h2>
<p>Une clinique produit organisée sur deux sites, avec présentation physique des directions à arbitrer, complétée d'entretiens individuels d'une heure conduits par des consultants seniors. Chaque participant a été recruté sur son modèle possédé, avec vérification, afin de couvrir un éventail de marques concurrentes plutôt qu'un profil moyen.</p>
<p>Le choix du présentiel n'était pas négociable&nbsp;: l'objet devait être vu à l'échelle, sous plusieurs angles, et les réactions les plus utiles ont eu lieu pendant les déplacements autour du véhicule — pas pendant les questions.</p>

<h2>Ce que le terrain a fait apparaître</h2>
<p>La hiérarchie des critères déclarés et la hiérarchie des critères observés ne coïncidaient pas. Interrogés, les participants classaient en tête des arguments rationnels d'usage&nbsp;; devant l'objet, leurs premières réactions et leurs premiers gestes portaient sur d'autres registres. C'est précisément l'écart que la clinique existe pour rendre visible, et c'est ce qui a orienté l'arbitrage.</p>
<p>Les entretiens individuels ont servi à un second usage&nbsp;: revenir, hors du regard des autres participants, sur des points où la dynamique de salle avait produit un consensus trop rapide.</p>

<h2>Ce qui a été livré</h2>
<ul>
  <li>Une analyse séparant explicitement le déclaré de l'observé, poste par poste.</li>
  <li>Des recommandations d'arbitrage hiérarchisées, avec les verbatims sources à l'appui.</li>
  <li>Une restitution animée avec les équipes design et produit, avant décision.</li>
</ul>

<h2>Que retenir pour d'autres missions ?</h2>
<p>Quand il y a un objet, il faut être devant l'objet&nbsp;: aucun dispositif à distance ne restitue ce qui se joue dans les trente secondes où quelqu'un tourne autour d'une voiture. Et le critère de recrutement le plus rentable est souvent le plus contraignant à sourcer.</p>
""",
},
{
 "slug": "cas-fichier-client-materiaux.html",
 "auteur": "TN",
 "illus": "ecriture-band.webp",
 "sources": [
  ('Points de Vente — marché du bricolage', "21,8 Mds € de chiffre d'affaires GSB en 2025, troisième année de recul", 'https://pointsdevente.fr/fil-info/2026-06-15-le-marche-du-bricolage-toujours-en-recul-malgre-le-rebond-de-limmobilier/'),
 ],

 "impact": {"titre": 'Ce que ça a changé', "chapo": "Un levier de coût qui améliore la qualité au passage — c'est assez rare pour être signalé.", "note": "Les effets décrits sont ceux constatés avec les équipes du client. Aucun montant ni indicateur commercial n'est publié ici.", "cartes": [
   ('Décision engagée', "Les priorités d'aménagement des agences ont été arbitrées sur des motifs de retour exprimés par de vrais clients, avec un historique d'achat vérifiable."),
   ('Ce qui a été évité', "Un sourcing en panel généraliste, qui aurait produit des gens ressemblant à la cible plutôt que de vrais clients de l'enseigne."),
   ('Ce qui a été gagné', "Une à deux semaines de calendrier, et un budget réinvesti dans le nombre d'entretiens plutôt que rendu."),
   ('Limite assumée', "La base ne contient que des clients actifs. Sur une question d'attrition, il faut compléter par un sourcing externe — nous le disons au cadrage, pas à la restitution."),
 ]},
 "faq": [
  ('Comment se passe le recrutement dans un fichier client ?', "Le client transmet une liste de contacts&nbsp;; nous qualifions sur les critères d'étude, prenons les rendez-vous et conduisons les entretiens. Le poste passe d'un sourcing complet à une qualification, ce qui divise son coût et raccourcit le calendrier."),
  ('Quelles précautions RGPD faut-il prendre ?', "Une base légale claire pour la transmission, une information des personnes contactées, un consentement recueilli avant l'entretien, et une anonymisation du corpus livré. Ces points se règlent au cadrage&nbsp;; ils ne se rattrapent pas après."),
  ('Le fichier client biaise-t-il les résultats ?', "Il oriente, et il faut le savoir&nbsp;: une base client ne contient que des clients actifs. Les partants et les perdus n'y sont pas. Sur une question de fidélité ou d'attrition, il faut impérativement compléter par un sourcing externe."),
 ],
 "aide": {"titre": 'Exploiter votre base client comme terrain', "chapo": "C'est la première question que nous posons en cadrage, parce que la réponse change le budget, le calendrier et la qualité du matériau dans le même mouvement.", "points": [
   "Qualification sur vos critères d'étude et prise de rendez-vous prises en charge",
   'Cadre RGPD réglé au cadrage : base légale, information, consentement, anonymisation',
   'Complément par sourcing externe quand la question porte sur les partants',
   "Corpus interrogeable remis à vos équipes, pour qu'elles y reviennent sur leurs propres angles",
 ]},
 "loin": [
  ('Bricolage : neuf Français sur dix, sept ont peur', 'marche-bricolage-peur-de-mal-faire.html'),
  ('Combien coûte une étude qualitative ?', 'article-prix-etude-qualitative.html'),
  ('Notre secteur Bâtiment', 'secteur-batiment.html'),
 ],

 "cat": "Bâtiment",
 "date": "2026-08-25",
 "read": "4 min",
 "title": "Cas — Diviser le coût d'un terrain grâce au fichier client",
 "h1": "Diviser le coût d'un terrain<br>en recrutant dans<br>le fichier du client.",
 "desc": "Étude de cas anonymisée : un distributeur de matériaux fournit sa base client. Ce que ça change au budget comme à la qualité du terrain.",
 "kw": "recrutement étude sur fichier client, étude qualitative bâtiment, étude distribution matériaux",
 "meta": [("Secteur", "Bâtiment"), ("Dispositif", "Entretiens sur fichier client"),
          ("Terrain", "France"), ("Livrables", "Top lines, corpus interrogeable")],
 "chapo": "Un réseau de distribution de matériaux de construction voulait comprendre ce qui faisait revenir ses clients professionnels en agence. Le budget était serré. La solution est venue du client lui-même.",
 "body": """
<h2>Le problème</h2>
<p>Le recrutement sur critères d'une cible professionnelle — artisans du bâtiment, chefs de chantier, acheteurs — est le poste le plus lourd d'une étude qualitative&nbsp;: 200 à 300&nbsp;€ par personne recrutée, et un sourcing long parce que ces profils sont peu présents dans les panels généralistes.</p>
<p>Sur un budget contraint, ce poste seul menaçait de consommer la moitié de l'enveloppe avant qu'un mot n'ait été prononcé.</p>

<h2>Le dispositif</h2>
<p>Le client a transmis une liste de contacts issue de sa propre base, en nous demandant d'en retenir une fraction correspondant aux critères d'étude. Nous avons pris en charge la qualification, la prise de rendez-vous et la conduite des entretiens.</p>
<p>Le poste « recrutement » est passé d'un sourcing complet à une qualification. L'économie a été immédiate — et elle a été réinvestie dans le nombre d'entretiens plutôt que rendue.</p>

<h2>Les deux effets qu'on n'attendait pas</h2>
<p><strong>Le profil était plus juste.</strong> Un recrutement en panel produit des gens qui correspondent aux critères déclarés. Un recrutement en base client produit de vrais clients, avec un historique d'achat réel — donc une conversation ancrée dans des faits vérifiables plutôt que dans des souvenirs approximatifs.</p>
<p><strong>Le calendrier s'est raccourci d'une à deux semaines.</strong> Le sourcing est le seul poste vraiment incompressible d'un terrain&nbsp;; le retirer déplace la date de restitution d'autant.</p>
<p>Un effet de bord à connaître, en revanche&nbsp;: recruter dans la base client biaise vers les clients actifs. Les partants et les perdus n'y sont pas. Si la question porte sur l'attrition, il faut compléter par un sourcing externe — nous le disons en cadrage.</p>

<h2>Ce qui a été livré</h2>
<ul>
  <li>Les transcripts intégraux, horodatés.</li>
  <li>Un corpus structuré et interrogeable, pour que les équipes puissent y revenir sur leurs propres questions.</li>
  <li>Des top lines courtes, orientées décision.</li>
</ul>

<h2>Que retenir pour d'autres missions ?</h2>
<p>C'est la première question que nous posons désormais en cadrage&nbsp;: « avez-vous une base client exploitable&nbsp;? » Quand la réponse est oui, elle change le budget, le calendrier et la qualité du matériau — dans le même mouvement.</p>
""",
},
]

# ═══════════════════════════════════════════════════════════════════════
#  FAQ
#  Écrite pour être citée : une question en titre, une réponse directe en
#  première phrase, puis le détail. C'est ce que les moteurs génératifs
#  reprennent, et ce dont un acheteur pressé a besoin.
#  Balisée FAQPage — le site n'avait aucune donnée structurée.
# ═══════════════════════════════════════════════════════════════════════

FAQ = [
("Méthodes", [
 ("Qu'est-ce qu'une étude qualitative ?",
  "Une étude qualitative cherche à comprendre <em>pourquoi</em> les gens font ce qu'ils font, là où une étude quantitative mesure <em>combien</em> le font. Elle repose sur un petit nombre d'entretiens ou de groupes conduits en profondeur, dont on analyse le contenu — les mots employés, les hésitations, les contradictions — plutôt que des scores. On y recourt en amont d'une décision, quand la question n'est pas encore assez claire pour être posée en questionnaire."),
 ("Combien de participants faut-il pour une étude qualitative ?",
  "Douze à dix-huit entretiens sur une cible homogène, ou deux groupes de six à huit personnes par segment à comparer. Le seuil qui compte est la saturation&nbsp;: le moment où les entretiens supplémentaires n'apportent plus d'information neuve. Il arrive plus tard dès qu'on croise plusieurs profils ou plusieurs marchés."),
 ("Faut-il choisir des focus groups ou des entretiens individuels ?",
  "Le groupe révèle les normes d'un milieu, l'entretien révèle les écarts individuels. Prenez le groupe pour tester un concept, un packaging ou un discours&nbsp;; prenez l'entretien pour un parcours d'achat, un prix, un sujet sensible ou une décision B2B. Nous détaillons l'arbitrage dans un <a href=\"article-entretiens-ou-groupes.html\">article dédié</a>."),
 ("Faites-vous des cliniques produit ?",
  "Oui, c'est notre dispositif de signature et nous en animons depuis quarante ans, principalement dans l'automobile. Le principe&nbsp;: des participants recrutés sur critères évaluent l'objet réel, en salle ou avec essai. Le protocole, le recrutement et le budget sont détaillés dans notre article <a href=\"article-car-clinic.html\">qu'est-ce qu'une car clinic</a>."),
 ("Peut-on faire une étude qualitative à distance ?",
  "Oui, et c'est souvent le bon choix pour des professionnels difficiles à réunir ou pour une cible dispersée géographiquement. À éviter dès qu'il y a du matériel à manipuler, un objet à voir à l'échelle, ou un sujet où le non-verbal porte une part de l'information."),
]),
("Délais et budget", [
 ("Combien de temps prend une étude qualitative ?",
  "Quatre à sept semaines pour un dispositif resserré, huit à douze pour une étude complète multi-cibles. La répartition type&nbsp;: une semaine de cadrage, une à trois semaines de recrutement, une à deux semaines de terrain, une à trois semaines d'analyse et de restitution. Le recrutement est le poste le plus long et le seul qui se raccourcisse vraiment, si vous fournissez votre fichier client."),
 ("Combien coûte une étude qualitative ?",
  "Le prix dépend d'abord du recrutement — 200 à 300&nbsp;€ par participant sur critères —, puis de la modalité de terrain et surtout des livrables demandés. Un terrain seul avec transcripts et un rapport complet avec typologies et atelier n'ont pas le même prix, et il n'y a aucune raison qu'ils l'aient. Nous remettons un chiffrage sous 48 heures après un échange de cadrage. Les repères publics du marché sont détaillés dans notre <a href=\"article-prix-etude-qualitative.html\">article sur le sujet</a>."),
 ("Peut-on obtenir des résultats en moins d'un mois ?",
  "Oui, à trois conditions&nbsp;: une question unique et bien cadrée, un recrutement dans votre propre base client, et un terrain à distance. En dessous de quatre semaines, ce qu'on gagne se prend sur le recrutement ou sur le nombre de voix — c'est-à-dire sur la validité. Notre offre <a href=\"decision-rapide.html\">Décision rapide</a> est construite pour ce cas de figure."),
 ("Qu'est-ce qui fait le plus varier le budget ?",
  "La difficulté de recrutement, de loin. Une cible grand public large et une cible professionnelle rare peuvent varier d'un facteur trois sur le seul poste de sourcing. Viennent ensuite la modalité — le présentiel ajoute déplacement, salle et intendance — puis le périmètre des livrables."),
]),
("Terrain et recrutement", [
 ("Qui recrute les participants ?",
  "Nous, sur critères écrits et vérifiés un à un&nbsp;; ou vous — si vous disposez d'une base client exploitable, nous prenons en charge la qualification et la prise de rendez-vous. Le recrutement en base client est plus rapide, moins cher et produit un profil plus juste, avec une réserve&nbsp;: il ne contient que des clients actifs, jamais les partants."),
 ("Comment évitez-vous les « professionnels du panel » ?",
  "Par deux filtres au questionnaire de recrutement&nbsp;: une question sur la participation à des études récentes, et une question ouverte dont la réponse doit être rédigée. Ce sont les deux contrôles les plus rentables du métier. Nous vérifions ensuite chaque profil individuellement avant confirmation."),
 ("Les participants sont-ils indemnisés ?",
  "Oui, systématiquement, y compris les personnes recrutées en sur-nombre que nous ne retenons pas le jour même. C'est une exigence déontologique et une condition de qualité&nbsp;: un participant non indemnisé se désiste, et un groupe à quatre ne se lit pas."),
 ("Qui anime les entretiens et les groupes ?",
  "Des consultants seniors, jamais des vacataires ni un dispositif automatisé. Sur un groupe de deux heures, l'écart entre un animateur qui suit son guide et un animateur qui suit le groupe représente environ la moitié du matériau exploitable."),
 ("Travaillez-vous en dehors de la France ?",
  "Oui. Nous conduisons régulièrement des terrains multi-pays en Europe, et nous avons l'habitude des dispositifs comparés entre deux marchés — le point délicat étant moins la logistique que l'équivalence des guides et des profils recrutés."),
]),
("IA, données et déontologie", [
 ("Utilisez-vous l'intelligence artificielle ?",
  "Oui, sur les tâches mécaniques et vérifiables&nbsp;: transcription, structuration du corpus, premier balayage thématique. Jamais sur le cadrage, la conduite du terrain, l'arbitrage entre interprétations ni la rédaction de la recommandation. Nous remettons cette répartition par écrit en avant-vente, et elle est détaillée dans notre <a href=\"article-ia-etudes-qualitatives.html\">article sur le sujet</a>."),
 ("Utilisez-vous des répondants synthétiques ?",
  "Non, jamais comme substitut de terrain. Un modèle génère la réponse la plus probable&nbsp;; une étude qualitative sert à trouver l'improbable. Nous les employons uniquement pour pré-tester un guide d'entretien avant d'engager du terrain réel. Cette position rejoint celle de la profession française, qui a publiquement écarté l'usage des entretiens synthétiques comme source de données."),
 ("À qui appartient le corpus d'une étude ?", 'À vous, intégralement et sans exception&nbsp;: transcripts complets et horodatés, remis même si vous ne prenez pas l\'analyse. Sur l\'hébergement, la sous-traitance et l\'entraînement des modèles, la chaîne complète figure dans notre article <a href="article-ia-etudes-qualitatives.html">sur l\'IA et les études qualitatives</a>.'),
 ("Comment garantissez-vous qu'une conclusion n'est pas inventée ?",
  "Chaque phrase de synthèse est remontable jusqu'au verbatim qui la fonde, horodaté et attribué à un participant identifié. C'est le principe de notre protocole&nbsp;: aucune synthèse intermédiaire qui ne soit traçable. Vous pouvez vérifier, et vos équipes aussi."),
 ("Respectez-vous un cadre déontologique ?",
  "Oui&nbsp;: supervision humaine à chaque étape, transparence sur les outils employés, indemnisation des participants, consentement éclairé et anonymisation des corpus livrés. Ces engagements suivent le cadre professionnel français en vigueur pour les études."),
]),
("Livrables", [
 ("Que reçoit-on à la fin d'une étude ?",
  "Au minimum, les transcripts intégraux horodatés — ils vous appartiennent, sans exception. Ensuite, à la carte&nbsp;: un corpus interrogeable, des top lines de cinq à huit pages, un rapport complet argumenté, des typologies réutilisables, et un atelier de décision animé avec vos équipes."),
 ("Peut-on n'acheter que le terrain ?",
  "Oui, et c'est un cas fréquent pour les équipes qui ont leurs propres analystes. Nous faisons le cadrage, le recrutement et le terrain, nous livrons le corpus structuré, et vous travaillez dessus. Vous pouvez décider plus tard d'ajouter des top lines ou un atelier."),
 ("Qu'est-ce qu'un atelier de décision ?",
  "Une demi-journée animée avec vos équipes, où l'on travaille sur les constats de l'étude jusqu'à un arbitrage écrit. C'est une réponse directe au problème le plus courant des études&nbsp;: un rapport lu par trois personnes et jamais transformé en décision."),
]),
]

# ═══════════════════════════════════════════════════════════════════════
#  LIVRE BLANC
#  Il porte le positionnement recommandé par l'étude concurrentielle
#  (« la parole client, structurée jusqu'à la décision ») et il NOMME le
#  protocole — Enov a CUBE, H2 a DECODia, Market Vision a IEMOSENS. Un nom
#  rend la méthode citable en réunion chez le client, sans nous dans la
#  pièce. « ANCRAGE » est une proposition, à valider avant publication.
# ═══════════════════════════════════════════════════════════════════════

LIVRE_BLANC = {
 "slug": "livre-blanc.html",
 "title": "Livre blanc — La parole client jusqu'à la décision",
 "h1": "La parole client,<br>structurée jusqu'à<br>la décision.",
 "desc": "Livre blanc : un protocole d'analyse de verbatim traçable, où l'IA fait le travail mécanique et où chaque conclusion reste remontable jusqu'à sa source.",
 "kw": "analyse de verbatim, protocole étude qualitative, traçabilité verbatim, méthode qualitative IA",
 "chapo": "Comment passer de quarante heures d'enregistrement à une décision que l'on peut défendre — sans perdre en route ce qui rendait le corpus intéressant.",
 "sommaire": [
   ("01", "Pourquoi une conclusion devient invérifiable", "pb"),
   ("02", "Quatre principes", "principes"),
   ("03", "Le protocole, phase par phase", "phases"),
   ("04", "Ce que l'IA fait, et ne fait jamais", "ia"),
   ("05", "La traçabilité, concrètement", "trace"),
   ("06", "Le cadre déontologique", "cadre"),
   ("07", "Ce que ça change pour vous", "vous"),
 ],
 "body": """
<section id="pb">
<h2><span class="wb-n">01</span> Pourquoi une conclusion d'étude devient-elle invérifiable ?</h2>
<p class="wb-lede">Entre le moment où quelqu'un dit quelque chose d'important en entretien et le moment où une décision est prise en comité, il y a quatre ou cinq réécritures successives. À chacune, quelque chose se perd — et personne ne sait quoi.</p>
<p>Le chemin habituel d'une étude qualitative ressemble à ceci&nbsp;: l'entretien est enregistré, puis transcrit, puis codé, puis synthétisé par thème, puis résumé en slides, puis présenté oralement, puis reformulé par celui qui a assisté à la présentation pour ceux qui n'y étaient pas. Sept étapes, sept occasions de lisser une nuance.</p>
<p>Ce n'est pas un problème de rigueur individuelle&nbsp;: c'est un problème de structure. Chaque étape produit un document autonome qui remplace le précédent au lieu de s'y ajouter. Au bout de la chaîne, plus personne ne peut répondre à la question&nbsp;: « cette conclusion, elle vient de qui&nbsp;? »</p>
<p>L'arrivée des modèles génératifs a rendu ce problème à la fois plus aigu et plus traitable. Plus aigu, parce qu'une synthèse automatique est <em>fluide</em>&nbsp;: elle produit un texte cohérent qui ne signale jamais ses propres approximations, et qui fabrique parfois des citations plausibles absentes du corpus. Plus traitable, parce que la machine sait faire ce que personne n'a jamais eu le budget de faire à la main&nbsp;: maintenir un lien mécanique entre chaque phrase de synthèse et la seconde d'enregistrement dont elle provient.</p>
</section>

<section id="principes">
<h2><span class="wb-n">02</span> Quatre principes</h2>
<div class="wb-princ">
  <div><h3>Aucune synthèse intermédiaire opaque</h3><p>Chaque niveau d'agrégation conserve le lien vers le niveau inférieur. On ne remplace jamais le matériau, on l'empile.</p></div>
  <div><h3>La machine sur le mécanique, l'humain sur le jugement</h3><p>La ligne de partage n'est pas négociable et elle est écrite. Ce qui se vérifie s'automatise&nbsp;; ce qui s'arbitre ne s'automatise pas.</p></div>
  <div><h3>Le corpus appartient au client</h3><p>Intégralement, horodaté, même si le client n'achète pas l'analyse. Ce n'est pas une faveur commerciale, c'est la condition de la vérifiabilité.</p></div>
  <div><h3>La restitution est un moment, pas un fichier</h3><p>Une étude qui n'est pas discutée en salle avec ceux qui décident ne produit pas de décision. Le livrable final est un arbitrage, pas un document.</p></div>
</div>
</section>

<section id="phases">
<h2><span class="wb-n">03</span> Le protocole, phase par phase</h2>
<p class="wb-lede">Cinq phases. Chacune produit un artefact qui reste consultable jusqu'à la fin — et au-delà.</p>

<h3>Phase 1 — Cadrer la décision, pas le sujet</h3>
<p>La première question n'est jamais « que voulez-vous savoir&nbsp;? » mais « qu'allez-vous décider, et quand&nbsp;? ». Les deux formulations donnent des dispositifs différents&nbsp;: la première produit une exploration, la seconde produit un arbitrage.</p>
<p>Cette phase produit trois choses&nbsp;: la question de terrain, les critères de recrutement, et — c'est le plus important — la liste écrite des hypothèses concurrentes que l'étude doit départager. Sans cette liste, l'analyse confirmera l'hypothèse dominante de l'entreprise, parce que c'est ce que fait naturellement un corpus qu'on interroge sans contradicteur.</p>

<h3>Phase 2 — Recruter et vérifier</h3>
<p>Chaque profil est vérifié individuellement avant confirmation. Deux filtres éliminent les répondants professionnels&nbsp;: une question sur les participations récentes, et une question ouverte à rédiger. Les participants sont indemnisés, y compris ceux recrutés en sur-nombre.</p>
<p>Quand le client dispose d'une base exploitable, le recrutement s'y fait — plus rapide, moins cher, profil plus juste. La limite est énoncée en cadrage&nbsp;: une base client ne contient que des clients actifs.</p>

<h3>Phase 3 — Conduire le terrain</h3>
<p>Consultant senior, guide écrit, silences tenus. L'enregistrement est intégral et horodaté dès la captation&nbsp;: c'est ce qui rend tout le reste possible.</p>

<h3>Phase 4 — Structurer, puis analyser</h3>
<p>Deux opérations distinctes qu'on a longtemps confondues.</p>
<p><strong>Structurer</strong> est mécanique&nbsp;: transcrire, horodater, attribuer les tours de parole, aligner les réponses sur les items du guide, faire remonter les récurrences. C'est automatisé, vérifié par relecture, et ça ne prend plus des jours.</p>
<p><strong>Analyser</strong> est un jugement&nbsp;: choisir entre deux lectures possibles d'un même passage, décider qu'un signal porté par deux personnes sur trente est le signal important, entendre l'écart entre ce qu'un participant explique et ce qu'il décrit trente secondes plus tard. Cette phase est conduite par un consultant, contre les hypothèses écrites en phase 1.</p>

<h3>Phase 5 — Restituer jusqu'à l'arbitrage</h3>
<p>Le format par défaut n'est pas un rapport mais un atelier&nbsp;: une demi-journée où les équipes travaillent les constats jusqu'à une décision écrite. Le document existe, mais il vient après, et il consigne l'arbitrage plutôt que de le préparer.</p>
</section>

<section id="ia">
<h2><span class="wb-n">04</span> Que fait l'IA, et que ne fait-elle jamais ?</h2>
<p class="wb-lede">Cette table n'est pas une précaution rhétorique. C'est la transparence sur les outils que demande le cadre professionnel français, et c'est ce que nous remettons par écrit en avant-vente.</p>
<div class="tw">
<table>
<thead><tr><th>Étape</th><th>Automatisé</th><th>Jamais automatisé</th></tr></thead>
<tbody>
<tr><td>Cadrage</td><td>—</td><td>Traduire un enjeu business en dispositif ; écrire les hypothèses concurrentes</td></tr>
<tr><td>Recrutement</td><td>Pré-tri des candidatures</td><td>Valider un profil sans contrôle humain</td></tr>
<tr><td>Terrain</td><td>—</td><td>Animer un groupe, conduire un entretien, décider d'une relance</td></tr>
<tr><td>Transcription</td><td>Intégrale, avec relecture</td><td>Livraison sans vérification humaine</td></tr>
<tr><td>Structuration</td><td>Horodatage, tours de parole, alignement sur le guide</td><td>—</td></tr>
<tr><td>Analyse</td><td>Premier balayage, regroupements proposés</td><td>Arbitrer entre deux interprétations ; écarter un signal faible</td></tr>
<tr><td>Restitution</td><td>Mise en forme</td><td>Écrire la recommandation</td></tr>
</tbody>
</table>
</div>
<p><strong>Sur les répondants synthétiques&nbsp;:</strong> ils ne remplacent aucun terrain. Un modèle produit la réponse la plus probable&nbsp;; une étude qualitative existe pour trouver l'improbable. Leur seul usage honnête est le pré-test d'un guide avant d'engager du terrain réel.</p>
</section>

<section id="trace">
<h2><span class="wb-n">05</span> La traçabilité, concrètement</h2>
<p class="wb-lede">« Chaque conclusion est remontable » est une phrase facile à écrire. Voici à quoi elle engage.</p>
<ol class="wb-steps">
  <li><strong>Toute phrase de synthèse porte au moins une référence</strong> — participant, horodatage, extrait. Une phrase sans référence est une opinion de consultant, et elle est signalée comme telle.</li>
  <li><strong>Le corpus reste interrogeable après la mission.</strong> Vos équipes posent leurs propres questions, sur leurs propres angles, sans repasser par nous.</li>
  <li><strong>Les signaux minoritaires sont conservés, pas moyennés.</strong> Ce qui n'est dit que par deux personnes est indiqué comme tel — et souvent commenté, parce que c'est là que se trouve l'information neuve.</li>
  <li><strong>Le désaccord entre analystes est consigné</strong> quand il existe, plutôt que résolu en coulisses par la formulation la plus lisse.</li>
</ol>
<p>L'effet pratique est simple&nbsp;: quand un membre de votre comité conteste une conclusion, la réponse est un extrait daté, pas une reformulation. C'est ce qui fait la différence entre une étude qui tient en réunion et une étude qui s'effrite.</p>
</section>

<section id="cadre">
<h2><span class="wb-n">06</span> Le cadre déontologique</h2>
<p class="wb-lede">Nous n'avons pas inventé ces règles&nbsp;: la profession française les a posées, et elles nous donnent raison.</p>
<ul>
  <li><strong>Supervision humaine à chaque étape</strong> et transparence complète sur les outils employés — les deux engagements structurants du cadre professionnel français publié en 2025.</li>
  <li><strong>Consentement éclairé et indemnisation</strong> de tous les participants.</li>
  <li><strong>Anonymisation des corpus livrés</strong>, et consignes explicites de non-diffusion des matériaux nominatifs.</li>
  <li><strong>Souveraineté des données</strong>&nbsp;: transcription par un fournisseur français, sans entraînement des modèles sur les corpus clients, sans rétention au-delà du traitement.</li>
</ul>
</section>

<section id="vous">
<h2><span class="wb-n">07</span> Ce que ça change pour vous</h2>
<div class="wb-princ">
  <div><h3>Vous pouvez vérifier</h3><p>Toute conclusion se remonte à sa source en quelques secondes. Vos équipes aussi — c'est fait pour.</p></div>
  <div><h3>Vous achetez ce dont vous avez besoin</h3><p>Le terrain est le socle. L'analyse, les typologies, la plateforme et l'atelier sont des options, pas un forfait imposé.</p></div>
  <div><h3>Le corpus vous survit</h3><p>Une étude cesse d'être un document daté&nbsp;: elle devient une base à laquelle vos équipes reviennent six mois plus tard avec une autre question.</p></div>
  <div><h3>La décision est le livrable</h3><p>Pas le rapport. C'est la seule mesure qui compte, et c'est celle sur laquelle nous acceptons d'être jugés.</p></div>
</div>
<aside class="art-sources" style="max-width:68ch;">
  <h2>Sources</h2>
  <ul>
    <li><a href="https://syntec-conseil.fr/" rel="nofollow noopener" target="_blank">Syntec Conseil</a> — sept engagements pour un usage responsable de l'IA dans les études, mai 2025 : supervision humaine à chaque étape et transparence sur les outils employés.</li>
    <li><a href="https://esomar.org/" rel="nofollow noopener" target="_blank">ESOMAR</a> — cadre déontologique international des études de marché et de l'opinion.</li>
    <li><a href="https://www.mrnews.fr/" rel="nofollow noopener" target="_blank">Market Research News</a> — dossiers professionnels sur la place de l'IA dans les études qualitatives, 2026.</li>
    <li><a href="https://www.gladia.io/pricing" rel="nofollow noopener" target="_blank">Gladia</a> — fournisseur français de transcription : désactivation de l'entraînement des modèles dès le plan Growth, rétention nulle en Enterprise.</li>
  </ul>
  <p class="art-sources-note">Références relevées en août 2026.</p>
</aside>

<div class="wb-cta">
  <h3>Discuter d'un dispositif</h3>
  <p>Composez votre configuration et obtenez son calendrier en deux minutes, ou écrivez-nous votre question en trois lignes.</p>
  <div class="ctas">
    <a href="decision-rapide.html#configurateur" class="btn btn-primary-dark"><span>Composer un dispositif</span><svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none"><path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg></a>
    <a href="contact.html" class="btn btn-outline-dark">Nous écrire</a>
  </div>
</div>
</section>
""",
}


# ═══════════════════════════════════════════════════════════════════════
#  RENDU
# ═══════════════════════════════════════════════════════════════════════

MOIS = ["janvier","février","mars","avril","mai","juin","juillet","août",
        "septembre","octobre","novembre","décembre"]

def date_fr(iso):
    y, m, d = iso.split("-")
    return "%d %s %s" % (int(d), MOIS[int(m) - 1], y)


def article_jsonld(a, kind="Article"):
    return {
        "@context": "https://schema.org",
        "@type": kind,
        "headline": re.sub(r"<[^>]+>", " ", a["h1"]).replace("&nbsp;", " ").strip(),
        "description": a["desc"],
        "datePublished": a["date"],
        "dateModified": a["date"],
        "inLanguage": "fr-FR",
        "keywords": a["kw"],
        "author": ({"@type": "Person", "name": AUTEURS[a["auteur"]]["nom"],
                    "jobTitle": AUTEURS[a["auteur"]]["role"],
                    "worksFor": {"@type": "Organization", "name": ORG["name"]}}
                   if a.get("auteur") else {"@type": "Organization", "name": ORG["name"]}),
        "publisher": {"@type": "Organization", "name": ORG["name"]},
        "mainEntityOfPage": {"@type": "WebPage", "@id": SITE + "/" + a["slug"]},
    }


def faq_jsonld():
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer",
                                "text": re.sub(r"<[^>]+>", "", r).replace("&nbsp;", " ")}}
            for _, qs in FAQ for q, r in qs
        ],
    }


def fil_ariane(a):
    """Le fil d'Ariane dit la place de la page dans l'arbre. C'est le même
    signal que le cocon, rendu explicite pour les moteurs."""
    titre = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", a["h1"]).replace("&nbsp;", " ")).strip()
    pos = cocon_de(a["slug"])
    fil = [("Accueil", ""), ("Contenus", "contenus.html")]
    if pos:
        c = COCONS[pos[0]]
        fil.append((c["titre"], c["cible"]))
    fil.append((titre, a["slug"]))
    return fil


def render_article(a, kind="Article", back=("contenus.html", "Tous les contenus")):
    meta = ""
    if a.get("meta"):
        meta = '<dl class="art-facts">' + "".join(
            f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in a["meta"]) + "</dl>"
    anon = ""
    if kind == "Article" and a.get("meta"):
        anon = ('<p class="art-anon"><strong>Cas anonymisé.</strong> Le dispositif décrit est réel ; '
                'le client n\'est pas nommé et aucun résultat chiffré n\'est publié. '
                'La levée d\'anonymat suppose son accord écrit.</p>')
    src = ""
    if a.get("sources"):
        # Citer des sources externes identifiables, en ligne dans le texte, est la
        # tactique la mieux mesurée en GEO (+30 à 40 % de visibilité, et jusqu'à
        # +115 % pour un site faiblement positionné). Elle sert aussi le lecteur.
        items = "".join(
            f'<li><a href="{u}" rel="nofollow noopener" target="_blank">{n}</a> — {q}</li>'
            for n, q, u in a["sources"])
        src = ('<aside class="art-sources"><h2>Sources</h2><ul>' + items + '</ul>'
               '<p class="art-sources-note">Repères relevés en août 2026. Les tarifs de '
               'marché évoluent&nbsp;: vérifiez la date de la source avant de vous en servir '
               'comme référence.</p></aside>')
    # Impact : une étude de cas qui n'énonce pas ce qui a changé reste une
    # description de dispositif. C'est la section que lit un décideur.
    impact = ""
    if a.get("impact"):
        cartes = "".join(
            f'<div><span class="imp-k">{k}</span><p>{v}</p></div>' for k, v in a["impact"]["cartes"])
        impact = (f'<section class="art-impact"><h2>{a["impact"]["titre"]}</h2>'
                  f'<p class="imp-lede">{a["impact"]["chapo"]}</p>'
                  f'<div class="imp-g">{cartes}</div>'
                  f'<p class="imp-note">{a["impact"]["note"]}</p></section>')

    # FAQ d'article : elle répond aux questions qui restent après la lecture,
    # et son balisage FAQPage est ce que les moteurs génératifs reprennent le
    # plus volontiers — une question, une réponse directe.
    faq = ""
    if a.get("faq"):
        items = "".join(
            f'<details class="faq-i"><summary><h3>{q}</h3></summary>'
            f'<div class="faq-a"><p>{r}</p></div></details>' for q, r in a["faq"])
        faq = (f'<section class="art-faq"><h2>{a.get("faq_titre", "Questions fréquentes")}</h2>'
               f'{items}</section>')

    # Bloc d'activation : un article qui explique sans dire ce qu'on peut en
    # faire ensemble laisse le lecteur au milieu du gué.
    act = ""
    if a.get("aide"):
        puces = "".join(f"<li>{x}</li>" for x in a["aide"]["points"])
        act = f'''<section class="art-help">
  <div class="art-help-in">
    <div class="eyebrow">— Comment ACMÉ peut vous aider</div>
    <h2>{a["aide"]["titre"]}</h2>
    <p class="lead">{a["aide"]["chapo"]}</p>
    <ul class="art-help-list">{puces}</ul>
    <div class="ctas">
      <a href="decision-rapide.html#configurateur" class="btn btn-primary-light"><span>Composer un dispositif</span><svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none"><path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg></a>
      <a href="contact.html" class="btn btn-outline-light">Parler de votre question</a>
    </div>
  </div>
</section>'''

    # Aller plus loin : le maillage interne fait circuler l'autorité entre les
    # pages et retient le lecteur sur le site.
    # Le bloc structurel suit le cocon, pas une liste écrite à la main :
    # une règle tenue par le code ne dérive pas au fil des ajouts.
    liste_loin = liens_cocon(a["slug"]) or a.get("loin") or []
    loin = ""
    if liste_loin:
        liens = "".join(f'<a href="{u}"><span>{t}</span>'
                        f'<svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none">'
                        f'<path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg></a>'
                        for t, u in liste_loin)
        pos = cocon_de(a["slug"])
        titre_loin = ("Dans « %s »" % COCONS[pos[0]]["titre"]) if pos else "Aller plus loin"
        loin = f'<section class="art-loin"><h2>{titre_loin}</h2><div class="art-loin-g">{liens}</div></section>'

    # Signature. Une prise de position vaut par celui qui la tient — et une
    # page signée est aussi ce qu'un moteur génératif reprend plus volontiers
    # qu'une page anonyme.
    byline = ""
    if a.get("auteur"):
        au = AUTEURS[a["auteur"]]
        byline = (
            f'<div class="art-by"><span class="art-by-i" aria-hidden="true">{a["auteur"]}</span>'
            f'<span class="art-by-t">Par <a href="qui-sommes-nous.html"><strong>{au["nom"]}</strong></a>'
            f'<span class="art-by-r">{au["role"]}</span></span></div>')

    # Bandeau d'illustration. Décoratif : alt vide plutôt qu'une description
    # redondante avec le titre — un lecteur d'écran n'a rien à y gagner.
    illus = ""
    if a.get("illus"):
        illus = (f'<div class="art-illus"><img src="assets/illus/{a["illus"]}" alt="" '
                 f'width="1600" height="600" loading="lazy" decoding="async"></div>')

    body = f"""<article class="art">
  <header class="art-head">
    <div class="container art-w">
      <div class="art-kicker"><a href="{back[0]}">{back[1]}</a><span>·</span><span>{a['cat']}</span></div>
      <h1 class="display">{a['h1']}</h1>
      <p class="art-chapo">{a['chapo']}</p>
      <div class="art-meta"><time datetime="{a['date']}">{date_fr(a['date'])}</time><span>·</span><span>{a['read']} de lecture</span></div>
      {byline}
      {meta}
      {anon}
    </div>
  </header>
  {illus}
  <div class="container art-w art-body" lang="fr">
{a['body']}
{impact}
{faq}
{src}
{loin}
  </div>
</article>
{act}
<article class="art art-tail">
  <div class="container art-w">
    <div class="art-foot">
      <a href="{back[0]}" class="btn btn-outline-dark">{back[1]}</a>
      <a href="contact.html" class="btn btn-primary-dark"><span data-i18n="nav.cta">Démarrer un projet</span><svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none"><path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg></a>
    </div>
  </div>
</article>"""
    ld = article_jsonld(a, kind)
    if a.get("faq"):
        # Un @graph plutôt que deux blocs : la page est UNE entité qui est à la
        # fois un article et une FAQ, et le lien entre les deux reste explicite.
        ld = {"@context": "https://schema.org", "@graph": [
            {k: v for k, v in ld.items() if k != "@context"},
            {"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer",
                                    "text": re.sub(r"<[^>]+>", "", r).replace("&nbsp;", " ")}}
                for q, r in a["faq"]]}]}
    return page(a["slug"], a["title"], a["desc"], body,
                extra_jsonld=ld, current="ct", og_type="article",
                og_image=f'assets/illus/{a["illus"]}' if a.get("illus") else "assets/v4/decision.jpg",
                breadcrumbs=fil_ariane(a))


def render_faq():
    secs, nav = [], []
    for i, (cat, qs) in enumerate(FAQ):
        cid = "faq-%d" % i
        nav.append(f'<a href="#{cid}">{cat}</a>')
        items = "".join(
            f'<details class="faq-i"><summary><h3>{q}</h3></summary><div class="faq-a"><p>{r}</p></div></details>'
            for q, r in qs)
        secs.append(f'<section class="faq-sec" id="{cid}"><h2 class="faq-cat">{cat}</h2>{items}</section>')
    body = f"""<section class="hero-compact">
  <div class="container hero-compact-inner">
    <div class="eyebrow" style="margin-bottom:14px;">— Questions fréquentes</div>
    <h1 class="display">Ce qu'on nous demande<br>le plus souvent.</h1>
    <p class="lead">Méthodes, délais, budget, données, livrables. Des réponses courtes et directes — et le détail juste en dessous quand il est utile.</p>
  </div>
</section>
<section class="section-pad">
  <div class="container">
    <nav class="faq-nav" aria-label="Rubriques">{''.join(nav)}</nav>
    {''.join(secs)}
    <aside class="art-sources" style="max-width:860px;">
      <h2>Sur quoi s'appuient ces réponses</h2>
      <ul>
        <li><a href="https://syntec-conseil.fr/" rel="nofollow noopener" target="_blank">Syntec Conseil</a> — engagements d'usage responsable de l'IA dans les études, mai 2025.</li>
        <li><a href="https://esomar.org/" rel="nofollow noopener" target="_blank">ESOMAR</a> — cadre déontologique international.</li>
        <li><a href="https://www.squarecocoon.fr/prix-d-un-focus-group/" rel="nofollow noopener" target="_blank">Square Cocoon</a> et <a href="https://www.intotheminds.com/blog/combien-coute-une-etude-de-marche/" rel="nofollow noopener" target="_blank">IntoTheMinds</a> — repères publics de budget, 2026.</li>
        <li>Le reste vient de notre pratique de terrain. Quand une réponse relève de notre expérience et non d'une source publique, elle est formulée à la première personne.</li>
      </ul>
      <p class="art-sources-note">Réponses à jour au 25 août 2026.</p>
    </aside>

    <div class="faq-cta">
      <h2 class="display">Votre question<br>n'y est pas ?</h2>
      <p class="lead">Écrivez-nous en trois lignes. Nous répondons sous 48 heures.</p>
      <div class="ctas"><a href="contact.html" class="btn btn-primary-dark"><span data-i18n="nav.cta">Démarrer un projet</span><svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none"><path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg></a></div>
    </div>
  </div>
</section>"""
    return page("faq.html", "FAQ — étude qualitative : méthode, délais, budget, données",
                "Combien coûte une étude qualitative, combien de temps prend-elle, qui recrute, où sont les données : 22 réponses directes aux questions les plus fréquentes.",
                body, extra_jsonld=faq_jsonld(), current="ct",
                breadcrumbs=[("Accueil", ""), ("Contenus", "contenus.html"), ("FAQ", "faq.html")])


def render_livre_blanc():
    wb = LIVRE_BLANC
    rail = "".join(
        f'<a href="#{i}"><span class="n">{n}</span><span class="t">{t}</span></a>'
        for n, t, i in wb["sommaire"])
    body = f"""<article class="wb">
  <header class="wb-head">
    <div class="container">
      <div class="art-kicker"><a href="contenus.html">Tous les contenus</a><span>·</span><span>Livre blanc</span></div>
      <h1 class="display">{wb['h1']}</h1>
      <p class="art-chapo">{wb['chapo']}</p>
      <div class="art-meta"><time datetime="2026-08-25">25 août 2026</time><span>·</span><span>20 min de lecture</span></div>
    </div>
    <div class="container wb-media">
      <video src="assets/illus/stylos.mp4" poster="assets/illus/stylos.webp"
             muted loop playsinline autoplay preload="metadata" disablepictureinpicture
             aria-label="Plusieurs mains annotent le même corpus, chacune avec son stylo" tabindex="-1"></video>
    </div>
  </header>
  <div class="container wb-grid">
    <nav class="wb-rail" aria-label="Sommaire">{rail}</nav>
    <div class="wb-body" lang="fr">
{wb['body']}
    </div>
  </div>
</article>"""
    return page(wb["slug"], wb["title"], wb["desc"], body,
                extra_jsonld=article_jsonld(dict(wb, cat="Livre blanc", date="2026-08-25",
                                                 read="20 min"), "Article"),
                current="ct", og_type="article",
                breadcrumbs=[("Accueil", ""), ("Contenus", "contenus.html"),
                             ("Livre blanc", wb["slug"])])


def card(a, tag):
    t = re.sub(r"<[^>]+>", " ", a["h1"]).replace("&nbsp;", " ").strip()
    t = re.sub(r"\s+", " ", t)
    return f"""<a class="ct-card" href="{a['slug']}" data-kind="{tag}">
      <div class="ct-card-top"><span class="ct-tag">{a['cat']}</span><span class="ct-read">{a['read']}</span></div>
      <h3>{t}</h3>
      <p>{a['desc']}</p>
      <div class="ct-card-foot"><time datetime="{a['date']}">{date_fr(a['date'])}</time><span class="ct-go">Lire →</span></div>
    </a>"""


def render_hub():
    # Les articles d'observatoire sont mis à part : c'est le format au meilleur
    # rendement (reprises presse, prétexte de reprise de contact), et il ne se
    # lit pas comme un article de méthode.
    obs = [a for a in ARTICLES if a["cat"].startswith("Observatoire")]
    autres = [a for a in ARTICLES if not a["cat"].startswith("Observatoire")]
    arts = "".join(card(a, "article") for a in autres)
    obss = "".join(card(a, "obs") for a in obs)
    cass = "".join(card(c, "cas") for c in CAS)
    # Hero simple : le texte à gauche, le plan à fond perdu à droite. Pas de
    # machinerie de scroll — c'est une page d'entrée, elle doit se lire tout
    # de suite. La vidéo se remplace en changeant le seul nom de fichier.
    body = f"""<section class="ct-hero">
  <div class="container ct-hero-in">
    <div class="ct-hero-txt">
      <div class="eyebrow" style="margin-bottom:14px;" data-i18n="content.eyebrow">— Contenus</div>
      <h1 class="display" data-i18n="content.h1">Ce qu'on a appris,<br>et qu'on peut écrire.</h1>
      <p class="lead" data-i18n="content.lead">Des articles de praticiens plutôt que des définitions, des études de cas anonymisées plutôt que des logos, et les réponses aux questions qu'on nous pose vraiment.</p>
      <p class="ct-frnote" data-i18n="content.frnote"></p>
      <p class="ct-frnote"><a href="en/index.html" style="border-bottom:1px solid currentColor" data-i18n="content.enlink">Market watch, in English →</a></p>
    </div>
  </div>
  <div class="ct-hero-media" aria-hidden="true">
    <video src="assets/illus/hero-contenus.mp4" poster="assets/illus/hero-contenus.webp"
           muted loop playsinline autoplay preload="metadata" disablepictureinpicture tabindex="-1"></video>
  </div>
</section>

<section class="section-pad" id="une">
  <div class="container">
    <a class="ct-feature" href="livre-blanc.html">
      <div class="ct-feature-txt">
        <div class="eyebrow" style="margin-bottom:18px;" data-i18n="content.nav.wp">— Livre blanc</div>
        <h2 class="display" data-i18n="content.wp.h2">La parole client,<br>structurée jusqu'à<br>la décision.</h2>
        <p class="lead" data-i18n="content.wp.lead">Un protocole d'analyse de verbatim traçable, où l'IA fait le travail mécanique et où chaque conclusion reste remontable jusqu'à sa source. Sept chapitres, vingt minutes.</p>
        <span class="btn btn-primary-dark"><span data-i18n="content.wp.cta">Lire le livre blanc</span> <svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none"><path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg></span>
      </div>
      <div class="ct-feature-media" aria-hidden="true">
        <video src="assets/illus/ecriture.mp4" poster="assets/illus/ecriture.webp"
               muted loop playsinline autoplay preload="metadata" disablepictureinpicture tabindex="-1"></video>
      </div>
    </a>
  </div>
</section>

<section class="section-pad" id="articles" style="padding-top:0;">
  <div class="container">
    <div class="missions-head reveal">
      <div class="eyebrow" style="margin-bottom:20px;" data-i18n="content.art.eyebrow">— Articles</div>
      <h2 class="display" data-i18n="content.art.h2">Des praticiens,<br>pas des définitions.</h2>
    </div>
    <div class="ct-grid reveal">{arts}</div>
  </div>
</section>

<section class="section-pad" id="observatoire">
  <div class="container">
    <div class="missions-head reveal">
      <div class="eyebrow" style="margin-bottom:20px;" data-i18n="content.obs.eyebrow">— Observatoire</div>
      <h2 class="display" data-i18n="content.obs.h2">L'état de nos<br>marchés.</h2>
      <p class="lead" style="margin-top:20px;" data-i18n="content.obs.lead">Des chiffres datés et attribués sur les secteurs que nous travaillons — et, en dessous des chiffres, ce que le terrain dit et qu'aucune donnée de marché ne montre.</p>
    </div>
    <div class="ct-grid reveal">{obss}</div>
  </div>
</section>

<section class="section-pad" id="cas" style="background:var(--offwhite);">
  <div class="container">
    <div class="missions-head reveal">
      <div class="eyebrow" style="margin-bottom:20px;" data-i18n="content.nav.cases">— Études de cas</div>
      <h2 class="display" data-i18n="content.cas.h2">Des missions,<br>anonymisées.</h2>
      <p class="lead" style="margin-top:20px;" data-i18n="content.cas.lead">Le dispositif est réel, le client n'est pas nommé et aucun résultat chiffré n'est publié. C'est le prix d'une publication honnête — et ça n'enlève rien à ce qu'il y a à apprendre.</p>
    </div>
    <div class="ct-grid reveal">{cass}</div>
  </div>
</section>

<section class="section-pad" id="faq">
  <div class="container">
    <a class="ct-feature ct-feature-alt" href="faq.html">
      <div class="ct-feature-txt">
        <div class="eyebrow" style="margin-bottom:18px;">— FAQ</div>
        <h2 class="display" data-i18n="content.faq.h2">Vingt-deux questions,<br>vingt-deux réponses.</h2>
        <p class="lead" data-i18n="content.faq.lead">Combien de participants, combien de temps, combien ça coûte, qui recrute, où sont les données. Des réponses courtes, sans détour.</p>
        <span class="btn btn-outline-dark"><span data-i18n="content.faq.cta">Ouvrir la FAQ</span> <svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none"><path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg></span>
      </div>
    </a>
  </div>
</section>

<section class="cta-block dark">
  <div class="container">
    <h2 class="display reveal" data-i18n="content.cta.h2">Une question<br>à éclairer ?</h2>
    <p class="lead reveal" data-i18n="content.cta.lead">Composez un dispositif en deux minutes, ou écrivez-nous votre question en trois lignes.</p>
    <div class="ctas reveal">
      <a href="decision-rapide.html#configurateur" class="btn btn-primary-light"><span data-i18n="drh.cta1">Composer un dispositif</span><svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none"><path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg></a>
      <a href="contact.html" class="btn btn-outline-light" data-i18n="content.write">Nous écrire</a>
    </div>
  </div>
</section>"""
    ld = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "Contenus — ACMÉ Consultants",
        "hasPart": [article_jsonld(a) for a in ARTICLES + CAS],
        "description": "Articles de praticiens, observatoire de marchés, études de cas anonymisées, livre blanc et FAQ.",
    }
    return page("contenus.html",
                "Contenus — articles, études de cas et livre blanc",
                "Articles de praticiens sur les études qualitatives, études de cas anonymisées, livre blanc sur l'analyse de verbatim traçable et FAQ complète.",
                body, extra_jsonld=ld, current="ct",
                breadcrumbs=[("Accueil", ""), ("Contenus", "contenus.html")])


def _remplir_titres_courts():
    """Le libellé d'un lien de cocon : ni le slug, ni le h1 éditorial (trop
    oblique hors contexte), mais un titre court et clair."""
    for a in ARTICLES + CAS:
        t = a.get("court") or a["title"]
        # « Titre : sous-titre » → on garde la partie qui porte le sujet
        if " : " in t and len(t) > 40:
            g, d = t.split(" : ", 1)
            t = g if len(g) >= 18 else t
        TITRES_COURTS[a["slug"]] = t
    TITRES_COURTS.update({
        "livre-blanc.html": "Le livre blanc : la parole client jusqu'à la décision",
        "secteur-mobilite.html": "Notre secteur Mobilité & Automobile",
        "secteur-retail-fmcg.html": "Notre secteur Retail et FMCG",
        "secteur-sante-cosmetiques.html": "Notre secteur Santé & Cosmétiques",
        "secteur-batiment.html": "Notre secteur Bâtiment",
        "secteur-mode-luxe.html": "Notre secteur Mode & Luxe",
        "secteur-territoires.html": "Notre secteur Territoires, Tourisme & RSE",
        "etude-qualitative.html": "L'étude qualitative, du cadrage à la décision",
        "article-ia-etudes-qualitatives.html": "IA et études qualitatives : ce qu'elle rate encore",
    })


def main():
    _remplir_titres_courts()
    out = []
    # Version anglaise, sous en/, sur des URL distinctes.
    en = ROOT / "en"
    en.mkdir(exist_ok=True)
    for a in ARTICLES_EN:
        (en / a["slug"]).write_text(render_article_en(a), encoding="utf-8")
        out.append("en/" + a["slug"])
    (en / "index.html").write_text(render_index_en(), encoding="utf-8")
    out.append("en/index.html")
    for a in ARTICLES:
        (ROOT / a["slug"]).write_text(render_article(a), encoding="utf-8")
        out.append(a["slug"])
    for c in CAS:
        (ROOT / c["slug"]).write_text(
            render_article(c, back=("contenus.html#cas", "Toutes les études de cas")),
            encoding="utf-8")
        out.append(c["slug"])
    (ROOT / "faq.html").write_text(render_faq(), encoding="utf-8"); out.append("faq.html")
    (ROOT / LIVRE_BLANC["slug"]).write_text(render_livre_blanc(), encoding="utf-8")
    out.append(LIVRE_BLANC["slug"])
    (ROOT / "contenus.html").write_text(render_hub(), encoding="utf-8"); out.append("contenus.html")
    print("%d pages générées :" % len(out))
    for s in out:
        print("  ", s, "%6.1f Ko" % ((ROOT / s).stat().st_size / 1024))


# ═══════════════════════════════════════════════════════════════════════
#  ARTICLES ISSUS DU TEST DE PROMPTS GEO
#  Trois angles repérés en interrogeant les moteurs sur le corpus :
#  - « peut-on remplacer les répondants par l'IA » : occupé par deux
#    concurrents, sur un sujet où Acmé a une position tranchée à opposer ;
#  - « car clinic » : quasiment personne ne l'explique en français, alors
#    que c'est la signature du cabinet ;
#  - « brief d'étude qualitative » : personne ne l'occupe, et l'intention
#    est exactement celle d'un acheteur en train de cadrer.
# ═══════════════════════════════════════════════════════════════════════

ARTICLES += [
{
 "slug": "article-repondants-synthetiques.html",
 "auteur": "VB",
 "illus": "conversation.webp",
 "faq_titre": 'Questions fréquentes sur les répondants synthétiques',
 "faq": [
  ("Un répondant synthétique, est-ce la même chose qu'un persona ?", "Non. Un persona est une synthèse de terrain réel, construite pour représenter un segment observé. Un répondant synthétique génère des réponses nouvelles à partir d'un modèle&nbsp;: il produit de la donnée qui n'a jamais été recueillie."),
  ('Peut-on les utiliser pour compléter un échantillon trop petit ?', "Non, et c'est l'usage le plus tentant. Compléter douze entretiens réels par vingt entretiens simulés ne donne pas trente-deux entretiens&nbsp;: ça donne douze entretiens noyés dans du consensus."),
  ('Comment savoir si un corpus contient des réponses générées ?', "Demandez les enregistrements sources et les horodatages. Une réponse synthétique n'a ni l'un ni l'autre. C'est le contrôle le plus simple et le plus efficace."),
  ('Y a-t-il des cas où ils sont utiles ?', "Un seul, solide&nbsp;: pré-tester un guide d'entretien avant d'engager du terrain réel. Deux autres, avec réserve&nbsp;: préparer un animateur à des objections imprévues, et simuler un scénario extrême pour vérifier qu'un dispositif tiendrait."),
  ('Que dit la profession française à ce sujet ?', "Le cadre professionnel publié en 2025 impose la supervision humaine à chaque étape et la transparence sur les outils. Plusieurs dirigeants d'instituts ont publiquement écarté l'usage des entretiens synthétiques comme source de données."),
 ],
 "aide": {"titre": "Du terrain réel, et la preuve que c'en est", "chapo": "Notre socle est le terrain, et il est vérifiable. C'est ce qui distingue un corpus qu'on peut défendre en comité d'une synthèse qu'on peut seulement croire.", "points": [
   'Participants recrutés sur critères et vérifiés un à un, jamais un panel auto-administré',
   'Entretiens et groupes conduits par un consultant senior',
   'Enregistrements horodatés et transcripts intégraux remis, sans exception',
   "Chaque phrase de synthèse remontable jusqu'à sa source",
 ]},
 "loin": [
  ("IA et études qualitatives : ce qu'elle rate encore", 'article-ia-etudes-qualitatives.html'),
  ("Le livre blanc : la parole client jusqu'à la décision", 'livre-blanc.html'),
  ("Comment rédiger un brief d'étude qualitative", 'article-brief-etude-qualitative.html'),
 ],

 "cat": "Point de vue",
 "date": "2026-08-25",
 "read": "7 min",
 "title": "Peut-on remplacer les répondants par de l'IA ?",
 "h1": "Un modèle donne la réponse<br>la plus probable. On cherche<br>l'improbable.",
 "desc": "Répondants synthétiques, personas génératifs, panels simulés : ce qu'ils savent faire, ce qu'ils ne feront pas, et le seul usage que nous leur reconnaissons.",
 "kw": "répondants synthétiques, personas IA, panel synthétique, IA remplacer participants étude",
 "sources": [
  ("Agalma Études — données synthétiques et panels", "un institut français reconnaît l'utilité de pré-test tout en constatant l'échec sur l'émotion et l'hésitation", "https://agalma-etudes.com/blog/insights-ia/donnees-synthetiques-panels/"),
  ("IntoTheMinds — peut-on remplacer les répondants par l'IA ?", "l'état du débat côté institut", "https://www.intotheminds.com/blog/en/qualitative-interviews-ai/"),
  ("Syntec Conseil", "sept engagements d'usage responsable de l'IA dans les études, mai 2025", "https://syntec-conseil.fr/"),
  ("Market Research News", "dossier professionnel sur la place de l'IA dans les études qualitatives, 2026", "https://www.mrnews.fr/2026/03/09/dossier-quelle-place-donner-a-l-ia-dans-les-etudes-qualitatives-volet-2/"),
 ],
 "chapo": "La question revient à chaque cadrage depuis dix-huit mois, et elle est légitime : si un modèle sait imiter un consommateur, pourquoi payer pour en interroger de vrais ? Voici la réponse honnête, y compris sur ce que ces outils savent faire.",
 "body": """
<h2>Qu'appelle-t-on un répondant synthétique ?</h2>
<p><strong>Un profil simulé par un modèle de langage, à qui l'on pose les questions d'un guide d'entretien comme s'il s'agissait d'une personne.</strong> On le paramètre avec un âge, un métier, des habitudes de consommation, parfois des données de panel réelles, et il répond.</p>
<p>Le produit final ressemble beaucoup à un corpus d'entretiens. C'est précisément ce qui rend la question difficile&nbsp;: le livrable est plausible, lisible, et il coûte presque rien.</p>

<h2>Pourquoi ça ne remplace pas un terrain</h2>
<p><strong>Parce qu'un modèle génère la réponse la plus probable, et qu'une étude qualitative existe pour trouver l'improbable.</strong> C'est l'argument central, et il n'est pas rhétorique&nbsp;: il décrit exactement ce que fait la machine.</p>
<p>Un modèle produit la moyenne pondérée de ce qui a déjà été écrit sur un sujet. Or ce que vous cherchez en qualitatif, c'est la personne qui n'utilise pas votre produit comme prévu, celle qui a inventé un usage que personne n'avait imaginé, celle dont l'objection ne figure dans aucun article. Interroger un modèle revient à interroger le consensus — c'est-à-dire ce que vos équipes savent déjà, reformulé avec assurance.</p>
<p>Trois manques précis, constatés en confrontant des corpus simulés à des corpus réels sur les mêmes guides&nbsp;:</p>
<ul>
  <li><strong>L'hésitation disparaît.</strong> Un vrai participant se reprend, se contredit à trois minutes d'intervalle, dit « enfin, non, en fait… ». C'est souvent là qu'est l'information. Le modèle, lui, est cohérent du début à la fin.</li>
  <li><strong>Le silence n'existe pas.</strong> Les trois secondes après une question gênante ne se simulent pas, et elles portent une part du sens.</li>
  <li><strong>L'écart entre le dit et le fait s'efface.</strong> Un participant explique rationnellement un choix, puis décrit trente secondes plus tard un comportement qui le contredit. Un analyste entend l'écart. Un modèle produit une version cohérente des deux.</li>
</ul>
<p>Ce constat n'est pas isolé&nbsp;: <a href="https://agalma-etudes.com/blog/insights-ia/donnees-synthetiques-panels/" rel="nofollow noopener" target="_blank">Agalma Études</a>, qui travaille pourtant activement le sujet, relève que ces dispositifs échouent à restituer les émotions authentiques, les hésitations, les contradictions involontaires et les silences significatifs. Et la profession française s'est dotée en mai 2025 d'un cadre — les engagements <a href="https://syntec-conseil.fr/" rel="nofollow noopener" target="_blank">Syntec Conseil</a> — qui impose une supervision humaine à chaque étape et la transparence sur les outils employés.</p>

<h2>Le risque qu'on sous-estime : la boucle de confirmation</h2>
<p>Un répondant synthétique est entraîné sur du contenu public. Votre marque, votre catégorie et vos concurrents y sont décrits par… du marketing. Vous interrogez donc un miroir de votre propre discours, et vous en ressortez conforté.</p>
<p>C'est le pire résultat possible d'une étude&nbsp;: pas une erreur visible, mais une confirmation confortable qui coûtera cher au lancement.</p>

""" + fig_matrice(
  "Répondants synthétiques : le seul usage défendable",
  "Un modèle génère la réponse la plus probable ; une étude qualitative existe pour trouver l'improbable. D'où une zone d'usage étroite — la préparation — et une zone interdite : la production de données.",
  "Statut de la sortie", "Moment du projet",
  [(0, 0, "Avant le terrain — utile", "Pré-tester un guide, repérer une question mal formulée, préparer un animateur à des objections."),
   (1, 0, "Pendant le terrain — jamais", "Aucune réponse générée n'entre dans un corpus. Pas d'enregistrement, pas d'horodatage, pas de source."),
   (0, 1, "Ce que ça produit", "Du débogage de dispositif, en vingt minutes, avant d'engager 200 à 300 € par personne recrutée."),
   (1, 1, "Ce que ça produirait", "Une confirmation confortable de ce que vous saviez déjà — le pire résultat possible d'une étude.")]) + """<h2>Alors, à quoi ça sert vraiment ?</h2>
<p><strong>À une chose, et nous l'utilisons pour ça : pré-tester un guide d'entretien.</strong> Faire tourner un guide sur quelques profils simulés révèle en vingt minutes les questions mal formulées, les enchaînements qui ne tiennent pas, les termes ambigus. C'est du débogage de guide, avant d'engager du terrain réel qui, lui, coûte 200 à 300&nbsp;€ par personne.</p>
<p>Deux autres usages nous paraissent défendables, avec réserve&nbsp;: préparer un animateur à des objections auxquelles il n'a pas pensé, et simuler un scénario extrême pour vérifier qu'un dispositif tiendrait. Dans les deux cas, ce sont des <em>outils de préparation</em>, jamais des sources de données.</p>

<h2>Comment poser la question à un prestataire</h2>
<p>Si un devis vous paraît anormalement bas, trois questions tranchent en une minute&nbsp;:</p>
<ol>
  <li><strong>« Combien de personnes réelles seront interrogées, et comment sont-elles recrutées ? »</strong> Une réponse en nombre de « répondants » sans précision de recrutement mérite une relance.</li>
  <li><strong>« Y a-t-il de l'IA dans la production des réponses, et où exactement ? »</strong> La transparence sur ce point est un engagement professionnel, pas une faveur.</li>
  <li><strong>« Cette phrase de synthèse, elle vient de quel verbatim, à quel horodatage ? »</strong> C'est la question à laquelle un corpus synthétique ne peut pas répondre autrement qu'en fabriquant.</li>
</ol>

<h2>Notre position, en une phrase</h2>
<p>Nous utilisons l'IA sur tout ce qui est mécanique et vérifiable — transcription, structuration, premier balayage — et jamais pour produire de la parole client. Le terrain est le seul endroit où l'on apprend quelque chose qu'on ne savait pas, et c'est exactement pour ça qu'il est le socle de nos dispositifs, y compris les plus courts.</p>
<p class="art-more">La répartition complète entre ce qui est automatisé et ce qui ne l'est jamais figure dans notre <a href="article-ia-etudes-qualitatives.html">article sur l'IA et les études qualitatives</a> et dans le <a href="livre-blanc.html">livre blanc</a>.</p>
""",
},
{
 "slug": "article-car-clinic.html",
 "auteur": "VJ",
 "illus": "demontage.webp",
 "faq_titre": 'Questions fréquentes sur les cliniques produit',
 "faq": [
  ('Combien de participants pour une car clinic ?', "Entre trente et soixante selon le nombre de directions à arbitrer et de segments à comparer. C'est plus qu'un dispositif qualitatif classique, parce qu'on cherche aussi à hiérarchiser des préférences, pas seulement à comprendre."),
  ('Combien de temps dure un passage ?', "Quarante-cinq minutes à une heure trente selon qu'il y a essai ou non. Le protocole s'écrit à la minute&nbsp;: l'ordre des expositions détermine les résultats."),
  ('Peut-on faire une clinique sur un prototype confidentiel ?', "Oui, c'est même le cas le plus fréquent. Cela suppose un lieu fermé, des accords de confidentialité signés, la confiscation des téléphones et un protocole de gardiennage. Ces contraintes se chiffrent et doivent figurer au brief."),
  ('Clinique ou test de concept : quelle différence ?', "La clinique suppose un objet réel, à l'échelle. Un test de concept travaille sur des représentations — planches, images de synthèse, maquettes numériques. Il coûte nettement moins cher, et il faut l'appeler par son nom."),
  ('Peut-on comparer avec des véhicules concurrents ?', "Oui, et c'est ce qui produit le matériau le plus utile. Une préférence exprimée dans l'absolu vaut peu&nbsp;; une préférence exprimée devant deux alternatives présentes vaut une décision."),
 ],
 "aide": {"titre": 'Quarante ans de cliniques produit', "chapo": "L'automobile est le secteur le plus exigeant que nous connaissions, et c'est celui sur lequel nous travaillons depuis le plus longtemps. La clinique est notre dispositif de signature.", "points": [
   'Recrutement sur véhicule réellement possédé, vérifié — le critère qui change tout',
   'Protocole de passage écrit à la minute, avec les relances par station',
   'Logistique produit et confidentialité prises en charge',
   "Analyse qui sépare explicitement le déclaré de l'observé",
 ]},
 "loin": [
  ('Un cas réel, anonymisé : arbitrer un design', 'cas-clinique-electrique.html'),
  ('Entretiens individuels ou focus groups', 'article-entretiens-ou-groupes.html'),
  ('Notre secteur Mobilité & Automobile', 'secteur-mobilite.html'),
 ],

 "cat": "Méthode",
 "date": "2026-08-25",
 "read": "8 min",
 "title": "Qu'est-ce qu'une car clinic et à quoi ça sert ?",
 "h1": "Trente secondes autour<br>d'une voiture valent<br>une heure de questions.",
 "desc": "Clinique statique ou dynamique, recrutement sur véhicule possédé, protocole de passage : comment se conduit un test produit automobile.",
 "kw": "car clinic, clinique produit automobile, test véhicule consommateurs, clinique statique dynamique",
 "sources": [
  ("Square Cocoon — Prix d'un focus group", "repères de budget pour un dispositif en salle, 2026", "https://www.squarecocoon.fr/prix-d-un-focus-group/"),
  ("Espace Rhône", "exemple d'infrastructure qualitative équipée pour l'observation", "https://www.espacerhone.com/"),
 ],
 "chapo": "C'est le dispositif le plus coûteux du qualitatif automobile, et celui qui produit le plus d'écart entre ce que les gens disent et ce qu'ils font. Voici comment il se monte, et quand il ne faut pas le monter.",
 "body": """
<h2>Qu'est-ce qu'une car clinic ?</h2>
<p><strong>Un dispositif d'étude où des participants recrutés sur critères évaluent un véhicule, un prototype ou des directions de design en présence physique de l'objet.</strong> Le principe tient en une phrase&nbsp;: on ne demande pas aux gens ce qu'ils pensent d'une voiture, on les met devant et on observe ce qu'ils font.</p>
<p>Elle se pratique aussi hors automobile — sur de l'électroménager, du mobilier, de l'équipement professionnel. Le nom est resté attaché au secteur qui l'a inventé.</p>

<h2>Statique ou dynamique : quelle différence ?</h2>
<p><strong>La clinique statique évalue l'objet à l'arrêt ; la dynamique ajoute l'essai.</strong></p>
<ul>
  <li><strong>Statique</strong> — le véhicule est en salle ou sous hall. On travaille l'extérieur, les proportions, la posture, l'intérieur, l'ergonomie de poste, la perception de qualité. C'est la forme la plus fréquente parce qu'elle autorise le prototype non homologué et la comparaison directe entre plusieurs directions.</li>
  <li><strong>Dynamique</strong> — le participant conduit. On accède au comportement routier perçu, au bruit, au confort réel, à l'usage des commandes en situation. Beaucoup plus lourd&nbsp;: homologation, assurance, circuit ou parcours, encadrement.</li>
</ul>
<p>Un dispositif mixte — statique le matin, essai l'après-midi — est fréquent quand le véhicule est roulant, et c'est celui qui produit le matériau le plus riche&nbsp;: la personne revient sur ses premiers jugements après avoir conduit, et cet écart-là vaut cher.</p>

<h2>Qui faut-il recruter ?</h2>
<p><strong>Des gens qui possèdent aujourd'hui un véhicule concurrent précis, pas des « intentionnistes » en général.</strong> C'est le critère qui coûte le plus à sourcer et qui change tout.</p>
<p>L'avis d'un conducteur qui ne possède pas la catégorie porte sur ses représentations. Celui d'un possesseur porte sur l'usage réel — l'ouverture du coffre les bras chargés, la place de recharge, le siège enfant, la visibilité trois-quarts arrière. C'est opérant pour arbitrer&nbsp;; l'autre ne l'est pas.</p>
<p>Sur un véhicule électrique, la règle est encore plus nette&nbsp;: n'interroger que des possesseurs d'électrique, sous peine de recueillir des craintes d'autonomie fantasmées plutôt que des contraintes vécues.</p>

""" + fig_chaine(
  "Le protocole de passage d'une clinique produit",
  "L'ordre des expositions détermine les résultats, d'où un protocole écrit à la minute. Le premier maillon est plein parce que c'est le plus informatif de la journée : on observe, on ne parle pas.",
  [("Approche libre", "sans consigne"), ("Réaction à chaud", "avant toute question"),
   ("Parcours guidé", "relances par station"), ("Comparaison", "concurrents présents"),
   ("Entretien", "hors du groupe")],
  pleines=1) + """<h2>Comment se déroule un passage ?</h2>
<p>Un protocole de clinique s'écrit à la minute, parce que l'ordre des expositions détermine les résultats.</p>
<ol>
  <li><strong>Approche libre, sans consigne.</strong> Les trente premières secondes sont les plus informatives de la journée&nbsp;: par où la personne entre, ce qu'elle touche, ce qu'elle contourne. On observe, on ne parle pas.</li>
  <li><strong>Réaction à chaud</strong>, avant toute question orientée.</li>
  <li><strong>Parcours guidé</strong> — extérieur, ouvrants, poste de conduite, places arrière, coffre. Chaque station a ses relances écrites.</li>
  <li><strong>Comparaison</strong> avec une ou deux références concurrentes présentes. C'est là que la hiérarchie réelle des critères apparaît.</li>
  <li><strong>Entretien individuel</strong> en fin de passage, hors du regard des autres participants, pour revenir sur ce qu'un consensus de salle a lissé.</li>
</ol>

<h2>Ce que la clinique révèle et que rien d'autre ne révèle</h2>
<p><strong>L'écart entre la hiérarchie déclarée et la hiérarchie observée.</strong> Interrogés en amont, les participants classent en tête des critères rationnels d'usage — coût, autonomie, volume de coffre. Devant l'objet, leurs premiers gestes et leurs premières réactions portent régulièrement sur d'autres registres.</p>
<p>Aucun questionnaire ne fait apparaître cet écart, parce qu'un questionnaire n'a que le déclaratif. C'est la raison d'être du dispositif, et c'est ce qui justifie son coût.</p>

<h2>Combien ça coûte, et pourquoi c'est cher</h2>
<p>Trois postes s'additionnent&nbsp;: le recrutement sur critère de possession (le plus difficile à sourcer, 200 à 300&nbsp;€ par personne et souvent davantage), la logistique de l'objet (transport, hall, gardiennage, confidentialité), et le temps de consultants seniors sur plusieurs jours consécutifs. À titre de repère, un dispositif en salle se situe déjà entre <a href="https://www.squarecocoon.fr/prix-d-un-focus-group/" rel="nofollow noopener" target="_blank">3 000 et 10 000&nbsp;€ par groupe</a> sans contrainte produit&nbsp;; une clinique ajoute la logistique par-dessus.</p>
<p>Le calendrier suit&nbsp;: comptez une semaine de préparation supplémentaire pour la logistique produit, ce qui porte un dispositif complet autour de huit à dix semaines.</p>

<h2>Quand il ne faut PAS faire de clinique</h2>
<p>Nous le disons en cadrage plutôt qu'en fin de mission&nbsp;:</p>
<ul>
  <li><strong>Quand l'objet n'existe pas encore sous une forme montrable.</strong> Une clinique sur des planches ne vaut pas une clinique&nbsp;: c'est un test de concept, moins cher, et il faut l'appeler ainsi.</li>
  <li><strong>Quand la question porte sur l'usage dans la durée.</strong> Une clinique capte la première rencontre. Pour l'usage, il faut du terrain chez les gens.</li>
  <li><strong>Quand la confidentialité interdit de sortir l'objet.</strong> Mieux vaut un dispositif adapté qu'une clinique amputée.</li>
</ul>
<p class="art-more">Un exemple de dispositif réel, anonymisé&nbsp;: <a href="cas-clinique-electrique.html">arbitrer un design par les conducteurs de la concurrence</a>.</p>
""",
},
{
 "slug": "article-brief-etude-qualitative.html",
 "auteur": "TN",
 "illus": "brief.webp",
 "faq_titre": 'Questions fréquentes sur le brief',
 "faq": [
  ("Quelle longueur doit faire un brief d'étude ?", "Deux à quatre pages. Au-delà, il contient des choses qui n'orientent aucune décision&nbsp;; en deçà, il oblige le prestataire à deviner, et vous recevrez des propositions incomparables."),
  ('Faut-il envoyer le même brief à tous les prestataires ?', "Oui, mot pour mot. C'est la seule façon de comparer des propositions, et c'est aussi une question d'équité vis-à-vis de gens qui vont y consacrer plusieurs jours."),
  ('Combien de prestataires consulter ?', "Trois. Deux ne donnent pas de point de comparaison, cinq vous feront perdre plus de temps en lecture que vous n'en gagnerez en négociation — et découragera les meilleurs de répondre sérieusement."),
  ('Que faire si aucune proposition ne rentre dans le budget ?', "Rouvrir la question plutôt que raboter le dispositif. Le plus souvent, c'est que le brief demandait de répondre à trois questions au lieu d'une."),
  ('Faut-il demander une méthodologie détaillée ?', 'Demandez plutôt le raisonnement&nbsp;: pourquoi ce dispositif pour cette décision. Une méthodologie détaillée sans raisonnement est un catalogue&nbsp;; un raisonnement clair vous dit avec qui vous allez travailler.'),
 ],
 "aide": {"titre": 'On peut aussi écrire le brief avec vous', "chapo": "Le cadrage est la partie de notre métier qui a le plus de valeur, et c'est celle que tout le monde offre en avant-vente. Nous y consacrons du temps, y compris si vous ne travaillez pas avec nous ensuite.", "points": [
   "Un échange d'une heure pour traduire votre décision en question de terrain",
   "Les hypothèses concurrentes écrites, pour que l'étude puisse les départager",
   'Un ordre de grandeur budgétaire donné dès le premier échange',
   'Le configurateur pour esquisser un dispositif et son calendrier avant de nous parler',
 ]},
 "loin": [
  ('Combien coûte une étude qualitative ?', 'article-prix-etude-qualitative.html'),
  ('Entretiens individuels ou focus groups', 'article-entretiens-ou-groupes.html'),
  ('Composer votre dispositif', 'decision-rapide.html#configurateur'),
 ],

 "cat": "Repères",
 "date": "2026-08-25",
 "read": "7 min",
 "title": "Comment rédiger un brief d'étude qualitative",
 "h1": 'Un brief flou ne donne pas<br>des devis flous. Il les<br>rend incomparables.',
 "desc": "Les huit rubriques d'un brief qui permet de comparer des devis, les erreurs qui font dériver le budget, et les questions qu'un bon prestataire vous posera en retour.",
 "kw": "brief étude qualitative, cahier des charges étude de marché, appel d'offres institut études, rédiger un brief",
 "sources": [
  ("IntoTheMinds — Combien coûte une étude de marché", "les ordres de grandeur à connaître avant de briefer", "https://www.intotheminds.com/blog/combien-coute-une-etude-de-marche/"),
  ("ESOMAR", "cadre déontologique international : ce qu'un prestataire s'engage à respecter", "https://esomar.org/"),
 ],
 "chapo": "Un brief flou ne produit pas des devis flous : il produit des devis incomparables. Voici ce qu'il faut y mettre pour que trois propositions se lisent côte à côte — et ce qu'il vaut mieux ne pas y mettre.",
 "body": """
<h2>À quoi sert vraiment un brief ?</h2>
<p><strong>À rendre trois devis comparables, et à faire remonter les désaccords internes avant de dépenser.</strong> La seconde fonction est la plus utile et la moins recherchée&nbsp;: écrire la décision à prendre oblige à constater que le marketing et le produit n'attendent pas la même chose de l'étude.</p>

<h2>Les huit rubriques</h2>

<h3>1. La décision, pas le sujet</h3>
<p>Écrivez ce que vous allez décider et quand. « Comprendre les attentes des 25-35 ans » n'est pas une décision&nbsp;: « choisir entre deux directions de packaging avant le comité du 15 novembre » en est une. Cette seule ligne change le dispositif proposé.</p>

<h3>2. Ce que vous savez déjà</h3>
<p>Études antérieures, données de vente, retours SAV, hypothèses internes. C'est contre-intuitif de le donner — beaucoup craignent d'orienter le prestataire — mais l'effet inverse est bien plus coûteux&nbsp;: sans ce contexte, vous financez la redécouverte de ce que vous saviez.</p>

<h3>3. Les hypothèses concurrentes à départager</h3>
<p>La rubrique qui manque presque toujours, et la plus utile. Listez les deux ou trois explications que vos équipes défendent. Une étude qui doit départager des hypothèses écrites revient rarement confirmer l'opinion du plus gradé.</p>

<h3>4. La cible, avec ses critères durs et ses critères souples</h3>
<p>Distinguez explicitement ce qui est indispensable de ce qui est souhaitable. Chaque critère dur renchérit le recrutement&nbsp;; un critère souple mal signalé se paie au prix d'un critère dur.</p>
<p>Et signalez tout de suite si vous disposez d'une base client exploitable&nbsp;: c'est le levier de coût le plus puissant du dispositif.</p>

<h3>5. Le matériel à faire réagir</h3>
<p>Rien, des stimuli papier ou écran, un produit physique, un prototype confidentiel&nbsp;? Précisez aussi la date à laquelle il sera disponible — un matériel qui glisse de deux semaines décale tout le terrain.</p>

<h3>6. Les livrables attendus, séparément</h3>
<p>Demandez le chiffrage <strong>ligne par ligne</strong>&nbsp;: terrain seul, transcripts, top lines, rapport complet, typologies, atelier de restitution. Un prix global vous empêche d'arbitrer, et empêche aussi de comparer deux propositions qui ne contiennent pas la même chose.</p>

<h3>7. Le calendrier, avec la date qui ne bouge pas</h3>
<p>Donnez la date de décision, pas la date de restitution souhaitée. Un prestataire honnête vous dira si elle est tenable, et ce qu'il faut retirer pour qu'elle le devienne.</p>

<h3>8. Les contraintes</h3>
<p>Confidentialité, données sensibles, langues, pays, secteur réglementé, obligation de passer par un référencement achats. Ce sont les points qui font exploser un budget quand ils arrivent en cours de mission.</p>

<h2>Faut-il annoncer son budget ?</h2>
<p><strong>Oui, au moins une fourchette.</strong> C'est le point sur lequel les acheteurs hésitent le plus, et à tort. Sans ordre de grandeur, vous recevrez trois propositions calibrées sur trois hypothèses différentes, dont aucune ne correspondra à ce que vous pouviez dépenser.</p>
<p>Annoncer une fourchette ne vous fait pas payer plus&nbsp;: ça vous fait recevoir des dispositifs adaptés, et ça déplace la discussion sur ce que vous obtenez plutôt que sur ce que ça coûte. À titre de repère avant de fixer cette fourchette&nbsp;: <a href="https://www.intotheminds.com/blog/combien-coute-une-etude-de-marche/" rel="nofollow noopener" target="_blank">les ordres de grandeur publiés</a> situent un entretien individuel autour de 600&nbsp;€ en B2C et 750&nbsp;€ en B2B.</p>

""" + fig_barres(
  "Ce qui fait le plus varier un devis d'étude qualitative",
  "Avant de raboter un budget, il vaut mieux savoir sur quoi on agit. La difficulté de recrutement domine largement les autres leviers.",
  [("Difficulté de recrutement", 100, "jusqu'à x3 sur le sourcing"),
   ("Modalité de terrain", 55, "déplacement, salle, intendance"),
   ("Périmètre des livrables", 45, "ce que vous prenez"),
   ("Nombre de marchés", 40, "guides et échantillons à doubler"),
   ("Matériel à manipuler", 25, "logistique et confidentialité")]) + """<h2>Les quatre erreurs qui coûtent le plus cher</h2>
<ol>
  <li><strong>Empiler les questions.</strong> Un brief qui pose sept questions produit une étude qui en traite sept superficiellement. Une question par étude, les autres attendront.</li>
  <li><strong>Sur-spécifier la cible.</strong> Chaque critère ajouté multiplie le coût de sourcing. Demandez-vous, critère par critère&nbsp;: est-ce que ça changera l'analyse&nbsp;?</li>
  <li><strong>Imposer la méthode.</strong> « Nous voulons quatre focus groups » ferme la discussion. Décrivez la décision et laissez le prestataire proposer&nbsp;; s'il propose la même chose que vous, tant mieux.</li>
  <li><strong>Oublier qui décidera.</strong> Si les décideurs n'assistent ni au terrain ni à la restitution, l'étude sera reformulée par un tiers avant d'arriver jusqu'à eux — et elle perdra en route ce qui la rendait utile.</li>
</ol>

<h2>Les questions qu'un bon prestataire vous posera</h2>
<p>Elles sont un bon test. Si personne ne vous demande&nbsp;:</p>
<ul>
  <li>ce que vous ferez du résultat si l'étude dit l'inverse de ce que vous espérez,</li>
  <li>qui, nommément, sera dans la salle au moment de décider,</li>
  <li>si vous avez une base client exploitable,</li>
  <li>et quelle est la seule question à laquelle il faut absolument répondre,</li>
</ul>
<p>…c'est que la proposition que vous recevrez sera un catalogue, pas un dispositif.</p>
<p class="art-more">Vous pouvez esquisser un dispositif et son calendrier en deux minutes sur notre <a href="decision-rapide.html#configurateur">configurateur</a>, puis nous l'envoyer comme base de discussion.</p>
""",
},
]


ARTICLES += [
{
 "slug": "marche-citadines-france-uk.html",
 "auteur": "VJ",
 "illus": "voiture.webp",
 "cat": "Observatoire · Mobilité",
 "date": "2026-08-25",
 "read": "10 min",
 "title": "Citadines : la France et le Royaume-Uni divergent",
 "h1": 'Une promesse qui marche<br>à Lyon peut tomber<br>à plat à Manchester.',
 "desc": "Deux marchés d'entrée de gamme, deux mécaniques opposées : le prix affiché en France, la remise au Royaume-Uni. Ce que ça change pour qui lance une citadine.",
 "kw": "marché citadines France, supermini UK, segment B Europe, acheteurs voitures urbaines",
 "sources": [
  ("Marché automobile français S1 2026", "857 177 immatriculations au premier semestre, +1,8 % sur un an", "https://www.cartegrise.com/blog/2026/07/marche-automobile-francais-s1-2026-le-grand-bilan-dun-semestre-de-bascule"),
  ("SMMT via Carwow — ventes d'occasion T1 2026", "les superminis représentent 648 229 transactions, soit 32,2 % du marché de l'occasion britannique", "https://www.carwow.co.uk/news/10706/used-car-sales-q1-2026"),
  ("GEM — prix moyen d'une voiture neuve au Royaume-Uni", "une remise moyenne approchant 6 000 £ début 2026", "https://www.motoringassist.com/news/new-car-prices-whats-the-uk-average"),
  ("Atlas Automobiles — marché français mai 2026", "+3,7 % d'immatriculations et record historique pour l'électrique", "https://atlas-automobiles.com/articles/aamarche-automobile-france-mai-2026-3-7-d-immatriculations-et-record-historique-pour-l-electrique"),
 ],
 "chapo": "Sur le papier, c'est le même segment : une petite voiture, quatre à cinq places, un budget contraint. Dans les faits, les deux marchés ne se règlent pas du tout de la même façon — et une promesse qui marche à Lyon peut tomber à plat à Manchester.",
 "body": """
<h2>Où en est le marché français ?</h2>
<p><strong>Il remonte lentement, et l'entrée de gamme le tire.</strong> Le premier semestre 2026 affiche 857 177 immatriculations, en hausse de 1,8 % sur un an — mais toujours en retrait de 26,5 % par rapport au premier semestre 2019. Le marché ne s'est pas remis&nbsp;; il s'est réorganisé.</p>
""" + stats([
  ("857 177", "immatriculations en France au S1 2026", "Carte Grise, juillet 2026"),
  ("+6,5 %", "de progression des citadines au T1 2026", "Presse spécialisée, 2026"),
  ("−26,5 %", "de volume par rapport au S1 2019", "Carte Grise, juillet 2026"),
]) + """
<p>Dans ce marché contraint, la citadine reprend la première place. Elle progresse de 6,5 % au premier trimestre, portée par l'arrivée de modèles électriques dans le segment, et la Peugeot 208 reste la référence avec 62 847 immatriculations sur les cinq premiers mois. La Renault 5 E-Tech, elle, dépasse les 20 000 unités depuis janvier.</p>

<h2>Ce qui structure vraiment le choix en France : le prix affiché</h2>
<p><strong>Le seuil des 20 000 € est devenu le vrai découpage du marché.</strong> Dacia Sandero Stepway autour de 17 900 €, Citroën C3 autour de 18 900 €, Peugeot 208 autour de 19 500 € : la catégorie la plus vivace du marché français se joue en dessous d'un chiffre rond, et cela n'a rien d'un hasard.</p>
<p>Ce que nous entendons en entretien depuis plusieurs années, c'est que ce seuil ne fonctionne pas comme un calcul mais comme une <em>frontière morale</em>. Au-dessus, l'achat change de nature : il devient une décision qu'il faut justifier — devant son conjoint, devant soi-même. En dessous, il reste un achat raisonnable.</p>
""""" + fig_barres(
  "Prix d'entrée des principales citadines françaises, 2026",
  "Les prix d'entrée se concentrent juste sous le seuil des 20 000 €, qui structure la catégorie la plus dynamique du marché français. Prix d'appel constructeurs relevés en 2026.",
  [("Dacia Sandero Stepway", 17900, "≈ 17 900 €"),
   ("Citroën C3", 18900, "≈ 18 900 €"),
   ("Peugeot 208", 19500, "≈ 19 500 €"),
   ("Seuil psychologique", 20000, "20 000 €")]) + """

<h2>Et au Royaume-Uni ?</h2>
<p><strong>Le marché est deux fois plus gros, et il se règle par la remise, pas par le prix affiché.</strong> La SMMT anticipe 2,048 millions d'unités en 2026, soit une croissance de 1,4 %. Mais le chiffre qui change tout est ailleurs : la remise moyenne sur une voiture neuve approchait 6 000 £ début 2026, tous carburants confondus.</p>
""" + stats([
  ("2,048 M", "d'unités attendues au Royaume-Uni en 2026", "SMMT, prévision"),
  ("≈ 6 000 £", "de remise moyenne sur une voiture neuve", "GEM, début 2026"),
  ("32,2 %", "du marché de l'occasion britannique tenu par les superminis", "SMMT via Carwow, T1 2026"),
]) + """
<p>Conséquence directe : au Royaume-Uni, <strong>le prix affiché n'est pas le prix</strong>. Il est un point de départ de négociation, et l'acheteur le sait. Un travail sur le prix catalogue y produit donc beaucoup moins d'effet qu'en France, où l'affichage <em>est</em> la promesse.</p>
<p>Second écart, plus structurant encore : le supermini britannique vit largement sur le marché de l'occasion. Il représente 648 229 transactions au premier trimestre 2026, soit 32,2 % de l'occasion — de loin la catégorie la plus achetée. En neuf, les superminis dépassent désormais régulièrement 20 000 £.</p>

<h2>Deux mécaniques opposées, résumées</h2>
""""" + fig_matrice(
  "France et Royaume-Uni : deux mécaniques de marché d'entrée de gamme",
  "Le même segment, deux façons opposées de rendre une voiture accessible. La conséquence porte moins sur le produit que sur la manière d'en parler.",
  "Comment l'accessibilité se fabrique", "Ce que l'acheteur regarde",
  [(0, 0, "France — le prix affiché", "Le seuil des 20 000 € fait la frontière. L'affichage est la promesse, et la remise reste marginale dans le discours."),
   (1, 0, "Royaume-Uni — la remise", "Le prix catalogue est un point de départ. Environ 6 000 £ de remise moyenne : l'acheteur négocie et le sait."),
   (0, 1, "France — le neuf électrifié", "L'entrée de gamme se renouvelle par des citadines électriques, qui entrent dans le haut du classement."),
   (1, 1, "Royaume-Uni — l'occasion récente", "Le supermini se joue d'abord en occasion : 32,2 % des transactions du T1 2026.")]) + """

<h2>Ce que ça change pour qui lance une citadine</h2>
<p>Trois conséquences opérationnelles, que nous voyons se vérifier en clinique produit :</p>
<ul>
  <li><strong>Un même argument de prix ne se teste pas de la même façon.</strong> En France, il faut tester le prix affiché, parce que c'est lui qui déclenche ou bloque. Au Royaume-Uni, il faut tester le prix <em>attendu après négociation</em> — sinon vous mesurez une réaction à un chiffre auquel personne ne croit.</li>
  <li><strong>Le référentiel de comparaison n'est pas le même.</strong> L'acheteur français compare des véhicules neufs entre eux. L'acheteur britannique compare régulièrement un neuf remisé à une occasion récente très bien équipée. Un test de concept qui ne met pas l'occasion dans le jeu concurrentiel passe à côté de l'arbitrage réel.</li>
  <li><strong>L'électrification ne se raconte pas pareil.</strong> En France, elle entre par le haut du classement des citadines et bénéficie d'un récit de renouveau. Au Royaume-Uni, la question du coût total et de la valeur de revente arrive beaucoup plus tôt dans la conversation.</li>
</ul>

<h2>Ce que les chiffres ne disent pas</h2>
<p>Ces données décrivent un marché ; elles n'expliquent pas une décision. Un tableau d'immatriculations ne dit ni pourquoi quelqu'un renonce au modèle qu'il préférait, ni ce qui se joue dans le garage quand un couple arbitre entre deux versions, ni ce que le voisinage pense d'une voiture garée devant la maison.</p>
<p>C'est exactement l'écart que le qualitatif existe pour combler — et sur un lancement multi-marchés, c'est l'écart le plus coûteux à ignorer, parce qu'il ne se voit qu'après.</p>
""",
 "faq_titre": "Questions fréquentes sur le marché des citadines",
 "faq": [
  ("Quelle est la citadine la plus vendue en France en 2026 ?",
   "La Peugeot 208, avec 62 847 immatriculations sur les cinq premiers mois de 2026. Elle est suivie par les modèles d'entrée de gamme positionnés sous 20 000 €, et par des citadines électriques comme la Renault 5 E-Tech, au-delà de 20 000 unités depuis janvier."),
  ("Pourquoi le seuil de 20 000 € compte-t-il autant en France ?",
   "Parce qu'il fonctionne comme une frontière et non comme un calcul. En dessous, l'achat reste raisonnable&nbsp;; au-dessus, il devient une décision à justifier. C'est ce que l'on entend en entretien, et c'est ce qui explique la concentration des prix d'appel juste sous ce seuil."),
  ("Le marché britannique est-il comparable au marché français ?",
   "En volume, il est environ deux fois plus grand — 2,048 millions d'unités attendues en 2026. En mécanique, il diffère profondément&nbsp;: la remise moyenne y approche 6 000 £, ce qui fait du prix affiché un point de départ plutôt qu'une promesse."),
  ("Faut-il mener des études séparées sur chaque marché ?",
   "Un guide commun, oui&nbsp;; un terrain commun, non. Les deux marchés partagent la catégorie mais pas les référentiels de comparaison. Un dispositif comparé, avec le même guide et des échantillons équivalents, permet de séparer ce qui relève de l'usage universel de ce qui relève d'habitudes locales."),
  ("Ces chiffres sont-ils suffisants pour arbitrer un lancement ?",
   "Non. Ils cadrent le marché, ils ne décrivent aucune décision individuelle. Pour arbitrer un design, un prix ou une version, il faut mettre des acheteurs réels devant l'objet et les alternatives — c'est l'objet d'une clinique produit."),
 ],
 "aide": {"titre": "Tester une citadine sur deux marchés",
  "chapo": "Nous conduisons des terrains comparés France–Royaume-Uni et France–Italie depuis des années, sur le segment le plus disputé du marché européen.",
  "points": ["Recrutement sur véhicule réellement possédé, marché par marché",
             "Guide commun et échantillons équivalents, pour que la comparaison soit valide",
             "Clinique produit statique ou dynamique, avec les alternatives concurrentes présentes",
             "Analyse qui sépare l'usage universel des habitudes locales — la distinction dont dépendent vos arbitrages produit"]},
 "loin": [("Qu'est-ce qu'une car clinic ?", "article-car-clinic.html"),
          ("Un cas réel, anonymisé : arbitrer un design", "cas-clinique-electrique.html"),
          ("Notre secteur Mobilité & Automobile", "secteur-mobilite.html")],
},
]

ARTICLES += [
{
 "slug": "marche-luxe-clients-perdus.html",
 "auteur": "CC",
 "illus": "fuite.webp",
 "cat": "Observatoire · Mode & Luxe",
 "date": "2026-08-25",
 "read": "9 min",
 "title": "Le luxe a perdu 20 millions de clients en un an",
 "h1": "Le luxe a perdu<br>vingt millions<br>de clients.",
 "desc": "La clientèle mondiale du luxe est passée de 400 à 330 millions de personnes en trois ans. Ce que le qualitatif dit de ceux qui sont partis — et de ceux qui restent.",
 "kw": "marché du luxe 2026, clientèle luxe, Gen Z luxe, biens personnels de luxe",
 "sources": [
  ("Bain & Company — étude sur le marché mondial du luxe", "1 443 Mds € de dépenses mondiales en 2025 ; biens personnels à 358 Mds €, attendus 365-373 Mds € en 2026", "https://www.journalduluxe.fr/fr/business/luxe-bain-stabilisation-marche-mondial-2026"),
  ("Bain — transformation de la clientèle", "près de 20 millions de consommateurs perdus en 2025 ; 330 millions de clients actifs contre 400 millions trois ans plus tôt", "https://www.clubpatrimoine.com/contenus/marche-luxe-mondial"),
  ("BCG", "Millennials et Génération Z représentent environ 75 % du marché du luxe", "https://www.bcg.com/press/19july2023-dici-2026-les-millennials-et-la-generation-z-representeront-75-du-marche-du-luxe"),
  ("Altagamma — prévisions 2026", "reprise modérée attendue pour la joaillerie, les cosmétiques et la haute couture", "https://www.luxurytribune.com/previsions-du-luxe-pour-2026-une-croissance-moderee-de-3-a-5-est-elle-realiste"),
 ],
 "chapo": "Le chiffre d'affaires se stabilise, et c'est ce que tout le monde retient. Le chiffre qui compte est ailleurs : le nombre de personnes qui achètent du luxe s'est effondré d'un quart en trois ans. Ce n'est pas un problème de conjoncture, c'est un problème de recrutement.",
 "body": """
<h2>Que disent les chiffres de 2026 ?</h2>
<p><strong>Le marché se stabilise en valeur et se contracte en nombre de clients.</strong> Les deux mouvements sont simultanés, et c'est ce qui rend la lecture délicate.</p>
""" + stats([
  ("330 M", "de clients actifs du luxe dans le monde, contre 400 M trois ans plus tôt", "Bain & Company, 2026"),
  ("−20 M", "de consommateurs perdus sur la seule année 2025", "Bain & Company, 2026"),
  ("+2 à 4 %", "de croissance attendue sur les biens personnels de luxe en 2026", "Bain & Company, 2026"),
  ("≈ 75 %", "du marché porté par les Millennials et la Génération Z", "BCG"),
]) + """
<p>Les dépenses mondiales de luxe ont atteint 1 443 milliards d'euros en 2025 et devraient se tenir entre 1 440 et 1 470 milliards en 2026. Les biens personnels — maroquinerie, mode, joaillerie, beauté — sont attendus entre 365 et 373 milliards d'euros, en progression de 2 à 4 % après un recul de 2 % en 2025.</p>
<p>Autrement dit : <strong>la valeur tient parce que ceux qui restent dépensent davantage.</strong> C'est une stabilisation par concentration, pas par recrutement.</p>

""""" + fig_jauge(
  "Érosion de la clientèle mondiale du luxe en trois ans",
  "Environ un client sur six a quitté la catégorie en trois ans, alors que la valeur du marché se maintient. La croissance vient de la dépense des clients restants, pas de nouveaux entrants.",
  0.82,
  "330 millions de clients actifs aujourd'hui, contre 400 millions il y a trois ans",
  "Source : Bain & Company, 2026") + """

<h2>Qui est parti, exactement ?</h2>
<p><strong>Le client d'entrée de catégorie — celui qui achetait une pièce par an, parfois moins.</strong> C'est la population la plus sensible au prix, et c'est aussi celle qui alimentait le renouvellement générationnel de la clientèle.</p>
<p>Sa disparition pose un problème que le chiffre d'affaires ne montre pas : une maison de luxe ne recrute pas ses clients patrimoniaux directement. Elle les recrute par le bas, sur un premier achat, souvent un accessoire ou un parfum, puis les fait monter sur dix ou vingt ans. Quand la marche d'entrée devient trop haute, on ne perd pas seulement le chiffre d'affaires de l'année — <strong>on perd la cohorte de 2040</strong>.</p>

<h2>Trois choses que les chiffres ne disent pas, et que le terrain dit</h2>
<h3>1. Le renoncement ne se vit pas comme un arbitrage budgétaire</h3>
<p>En entretien, les personnes qui ont cessé d'acheter du luxe l'expliquent rarement par le prix seul. Elles décrivent un basculement de sens : le sentiment que le rapport entre ce qui est payé et ce qui est reçu a changé, et que l'objet ne « vaut plus » ce qu'il coûte. C'est un jugement sur la légitimité, pas sur le montant — et cela ne se corrige pas avec une promotion.</p>

<h3>2. L'expérience en boutique est devenue un filtre, pas un accueil</h3>
<p>Le client d'entrée de catégorie décrit régulièrement une gêne : ne pas savoir comment se comporter, être identifié comme non-acheteur, ne pas oser demander un prix. Cette gêne ne figure dans aucun baromètre de satisfaction, parce que les gens qui la ressentent ne remplissent pas les questionnaires — ils ne reviennent pas.</p>

<h3>3. La Génération Z ne remplace pas mécaniquement la clientèle sortante</h3>
<p>Millennials et Génération Z représentent environ trois quarts du marché, mais leur rapport à la catégorie est différent : la seconde main est légitime, le neuf n'est pas un impératif, et l'attachement à une maison se construit sur d'autres signaux. Compter sur eux pour reconstituer la clientèle perdue suppose de comprendre ce qui, chez eux, déclenche un premier achat — et ce n'est pas la même chose qu'il y a quinze ans.</p>

<h2>Le point de bascule européen</h2>
<p>L'Europe est le point faible du marché, avec un recul d'environ 20 % des dépenses des touristes internationaux relevé en février, tandis que les Amériques redeviennent le principal moteur du luxe personnel. Pour une maison européenne, cela déplace la question : <strong>la clientèle locale, longtemps considérée comme un socle, redevient un enjeu de conquête.</strong></p>

""""" + fig_chaine(
  "Le parcours de recrutement d'un client de maison de luxe",
  "Une maison ne recrute pas ses clients patrimoniaux directement : elle les fait monter. Quand la première marche devient trop haute, c'est la cohorte de dans quinze ans qui manque, pas seulement le chiffre d'affaires de l'année.",
  [("Premier achat", "accessoire, parfum"),
   ("Répétition", "un achat par an"),
   ("Attachement", "la maison est un choix"),
   ("Clientèle installée", "plusieurs univers"),
   ("Client patrimonial", "relation longue")],
  pleines=1) + """

<h2>Ce qu'il faut aller chercher sur le terrain</h2>
<p>Quatre questions, qu'aucune donnée de vente ne peut renseigner :</p>
<ul>
  <li><strong>Ce qui a fait basculer les partants.</strong> Les interroger est difficile — ils ne sont plus dans les fichiers — mais c'est la population la plus informative du marché.</li>
  <li><strong>Ce que la première marche représente vraiment.</strong> Le prix d'entrée est un chiffre ; ce qu'il signifie pour quelqu'un qui hésite est une autre affaire.</li>
  <li><strong>Ce qui se passe dans les huit premières secondes en boutique.</strong> C'est là que se décide le retour, et cela ne s'observe qu'en étant présent.</li>
  <li><strong>Ce qui rend une maison désirable pour quelqu'un de vingt-cinq ans</strong> qui a grandi avec la seconde main et n'a jamais considéré le neuf comme la norme.</li>
</ul>
""",
 "faq_titre": "Questions fréquentes sur le marché du luxe",
 "faq": [
  ("Le marché du luxe est-il en crise en 2026 ?",
   "En valeur, non&nbsp;: les biens personnels de luxe sont attendus en progression de 2 à 4 %, après un recul de 2 % en 2025. En clientèle, oui&nbsp;: le nombre de clients actifs est passé d'environ 400 à 330 millions en trois ans. La valeur tient parce que ceux qui restent dépensent davantage."),
  ("Pourquoi la perte de clients d'entrée de gamme est-elle grave ?",
   "Parce qu'une maison recrute sa clientèle patrimoniale par le bas, sur un premier achat, puis la fait monter sur dix ou vingt ans. Perdre la marche d'entrée, ce n'est pas perdre le chiffre d'affaires de l'année&nbsp;: c'est perdre la cohorte de dans quinze ans."),
  ("La Génération Z peut-elle compenser cette érosion ?",
   "Elle représente déjà, avec les Millennials, environ 75 % du marché — mais son rapport à la catégorie diffère&nbsp;: la seconde main est légitime, le neuf n'est pas un impératif. Compter sur elle suppose de comprendre ce qui déclenche un premier achat aujourd'hui, ce qui n'est pas ce qui le déclenchait il y a quinze ans."),
  ("Comment interroger des clients qui ont arrêté d'acheter ?",
   "C'est le point dur&nbsp;: ils ne sont plus dans les fichiers actifs. Il faut les recruter sur critère de comportement passé plutôt que sur un fichier client, ce qui renchérit le sourcing — mais c'est la population la plus informative du marché."),
  ("Quelle méthode pour comprendre l'expérience en boutique ?",
   "L'observation accompagnée, puis l'entretien individuel. Un questionnaire de satisfaction ne capte pas la gêne du client d'entrée de catégorie, pour une raison simple&nbsp;: les gens qui la ressentent ne remplissent pas les questionnaires, ils ne reviennent pas."),
 ],
 "aide": {"titre": "Comprendre ceux qui sont partis",
  "chapo": "Nous travaillons les codes du désir et l'expérience client haut de gamme, y compris sur les populations difficiles à recruter — celles qui ne sont plus dans vos fichiers.",
  "points": ["Recrutement sur comportement d'achat passé, pas seulement sur fichier client actif",
             "Observation accompagnée en boutique, puis entretien individuel hors du lieu",
             "Entretiens sur la première marche : ce que le prix d'entrée signifie pour qui hésite",
             "Restitution en atelier avec vos équipes retail et produit, jusqu'à l'arbitrage"]},
 "loin": [("Entretiens individuels ou focus groups", "article-entretiens-ou-groupes.html"),
          ("Notre secteur Mode & Luxe", "secteur-mode-luxe.html"),
          ("Composer votre dispositif", "decision-rapide.html#configurateur")],
},

{
 "slug": "marche-bricolage-peur-de-mal-faire.html",
 "auteur": "TN",
 "illus": "stylos.webp",
 "cat": "Observatoire · Bâtiment",
 "date": "2026-08-25",
 "read": "9 min",
 "title": "Bricolage : 9 Français sur 10 s'y mettent, 7 ont peur",
 "h1": "Neuf Français sur dix<br>bricolent. Sept sur dix<br>ont peur de mal faire.",
 "desc": "Le marché recule pour la troisième année, mais le frein principal n'est pas le pouvoir d'achat : c'est la peur de rater. Ce que ça change.",
 "kw": "marché bricolage France 2026, GSB, DIY consommateur, peur de mal faire bricolage",
 "sources": [
  ("Points de Vente — marché du bricolage", "21,8 Mds € TTC de chiffre d'affaires GSB en 2025, un marché global au-delà de 39 Mds €", "https://pointsdevente.fr/fil-info/2026-06-15-le-marche-du-bricolage-toujours-en-recul-malgre-le-rebond-de-limmobilier/"),
  ("Bricolage en France 2026 — stabilisation", "9 Français sur 10 bricolent, 7 sur 10 sont freinés par la peur de mal faire", "https://www.montrealmirror.com/actu10359/bricolage-france-2026-marche-stabilisation-peur-de-mal-faire.html"),
  ("IntoTheMinds — étude du marché du bricolage en France", "structure du marché et poids des circuits", "https://www.intotheminds.com/blog/etude-marche-bricolage-france/"),
 ],
 "chapo": "Trois années de recul consécutives, et une explication qui tourne en boucle : le pouvoir d'achat et l'immobilier. C'est vrai, et c'est insuffisant. Le frein le plus cité par les Français n'est pas financier — il est psychologique, et il se traite.",
 "body": """
<h2>Où en est le marché du bricolage ?</h2>
<p><strong>En recul pour la troisième année consécutive, avec un début 2026 plus rassurant.</strong> Le chiffre d'affaires des grandes surfaces de bricolage s'établit à 21,8 milliards d'euros TTC en 2025, en baisse de 1,4 % — après −1,4 % en 2023 et −4,3 % en 2024. Le marché global, tous circuits confondus, dépasse toujours 39 milliards d'euros.</p>
""" + stats([
  ("21,8 Mds €", "de chiffre d'affaires en grandes surfaces de bricolage en 2025", "Points de Vente, 2026"),
  ("3 années", "de recul consécutif du circuit GSB", "−1,4 % en 2023, −4,3 % en 2024, −1,4 % en 2025"),
  ("9 / 10", "Français déclarent bricoler en 2026", "Étude sectorielle, 2026"),
  ("7 / 10", "sont freinés par la peur de mal faire", "Étude sectorielle, 2026"),
]) + """
<p>Les professionnels du secteur parlent d'une reprise « graduelle et structurée » plutôt que d'un rebond. Les grandes surfaces tiennent 75 % du marché, tandis que le e-commerce progresse vers 19 % du chiffre d'affaires du secteur.</p>

<h2>Le déplacement que le chiffre d'affaires cache</h2>
<p><strong>Les Français n'ont pas arrêté de bricoler : ils ont changé de projets.</strong> La baisse du pouvoir d'achat et le ralentissement immobilier ont déplacé la demande de la rénovation lourde vers l'entretien courant et la réparation économique.</p>
<p>Pour une enseigne, ce n'est pas un ralentissement — c'est un changement de métier. On ne vend pas de la même façon un chantier de salle de bains et un joint à refaire. Le panier baisse, la fréquence peut monter, et le conseil demandé n'est plus du tout le même.</p>

""""" + fig_matrice(
  "Deux marchés du bricolage dans un seul chiffre d'affaires",
  "Le recul global masque une bascule : moins de projets de transformation, davantage d'entretien et de réparation. Les deux ne se vendent, ne se conseillent et ne s'équipent pas de la même manière.",
  "Type de projet", "Ce que le client attend",
  [(0, 0, "Rénovation lourde", "Panier élevé, décision longue, plusieurs visites. Le client attend un accompagnement de projet."),
   (1, 0, "Entretien et réparation", "Panier faible, décision immédiate, une visite. Le client attend une réponse, pas un projet."),
   (0, 1, "Ce qui recule", "Les chantiers de transformation, freinés par le pouvoir d'achat et le marché immobilier."),
   (1, 1, "Ce qui tient", "Les petits travaux et le dépannage — mais avec une exigence de réassurance beaucoup plus forte.")]) + """

<h2>Le vrai frein : la peur de rater</h2>
<p><strong>Neuf Français sur dix bricolent, mais sept sur dix sont freinés par la peur de mal faire.</strong> C'est, de loin, le chiffre le plus actionnable du secteur — et le moins exploité.</p>
<p>Ce frein n'est pas financier, et c'est ce qui le rend intéressant : il se traite par le conseil, la pédagogie, la garantie de résultat et la conception produit, pas par la promotion. Une remise de 20 % ne réduit pas la crainte de percer au mauvais endroit.</p>
<p>En entretien, cette peur se décompose en trois craintes distinctes, qui n'appellent pas les mêmes réponses :</p>
<ul>
  <li><strong>La peur d'abîmer</strong> — le logement, un support, un élément qu'on ne pourra pas remplacer. Elle bloque avant l'achat, en magasin comme en ligne.</li>
  <li><strong>La peur d'acheter le mauvais produit</strong> — se tromper de dimension, de compatibilité, de quantité. Elle produit du renoncement en rayon, et une part importante des retours.</li>
  <li><strong>La peur du jugement</strong> — devoir demander, montrer qu'on ne sait pas. Elle est très présente chez les publics qui bricolent peu, et elle explique une partie du basculement vers le e-commerce, où l'on peut chercher sans être vu.</li>
</ul>

""""" + fig_barres(
  "Ce qui freine le passage à l'acte, en fréquence de citation",
  "La hiérarchie déclarée place la peur de mal faire au premier rang, devant le budget. C'est un frein qui se traite par le conseil et la conception, pas par la promotion. Proportions issues des études sectorielles 2026.",
  [("Peur de mal faire", 70, "≈ 7 sur 10"),
   ("Contrainte de budget", 55, "élevée"),
   ("Manque de temps", 40, "moyenne"),
   ("Manque d'outillage", 25, "plus faible")]) + """

<h2>Ce que ça implique pour une enseigne ou une marque</h2>
<ul>
  <li><strong>Le conseil devient le produit.</strong> Sur un marché où le frein dominant est la crainte de l'échec, la valeur se déplace vers ce qui rassure : la démonstration, le tutoriel situé, la garantie, la reprise en cas d'erreur.</li>
  <li><strong>Le rayon doit répondre avant qu'on demande.</strong> La peur du jugement rend le client silencieux. S'il faut demander pour comprendre, une partie de la clientèle repartira sans acheter — sans jamais dire pourquoi.</li>
  <li><strong>Le e-commerce n'est pas qu'un canal de prix.</strong> Il est aussi un canal de discrétion : on peut y chercher longuement, comparer, apprendre, sans se dévoiler. Cela change ce qu'on doit y mettre.</li>
  <li><strong>Les professionnels et les particuliers ne se croisent plus au même endroit.</strong> Un artisan cherche une référence, un particulier cherche une réponse. Traiter les deux avec le même dispositif de conseil en déçoit un sur deux.</li>
</ul>

<h2>Pourquoi le quantitatif ne suffit pas ici</h2>
<p>« Sept sur dix ont peur de mal faire » est un excellent chiffre : il alerte. Il ne dit ni de quoi les gens ont peur exactement, ni à quel moment du parcours la peur bloque, ni ce qui la lève. Ces trois réponses déterminent pourtant tout ce qu'on peut faire — la formation des équipes, le contenu du rayon, la notice, la garantie.</p>
<p>C'est le genre d'écart qui se comble en une douzaine d'entretiens à domicile, chez des gens qui ont un projet en cours et un projet abandonné.</p>
""",
 "faq_titre": "Questions fréquentes sur le marché du bricolage",
 "faq": [
  ("Le marché du bricolage est-il en croissance en 2026 ?",
   "Non, il sort de trois années de recul consécutif en grandes surfaces&nbsp;: −1,4 % en 2023, −4,3 % en 2024 et −1,4 % en 2025, pour 21,8 milliards d'euros TTC. Les professionnels évoquent pour 2026 une reprise « graduelle et structurée », pas un rebond."),
  ("Quel est le principal frein au bricolage en France ?",
   "La peur de mal faire, citée par environ sept Français sur dix, devant la contrainte budgétaire. C'est un frein psychologique, ce qui le rend traitable par le conseil, la pédagogie et la conception produit plutôt que par la promotion."),
  ("Pourquoi le panier moyen baisse-t-il ?",
   "Parce que la demande s'est déplacée de la rénovation lourde vers l'entretien courant et la réparation économique. Le panier baisse, mais la fréquence peut monter — et le type de conseil attendu change complètement."),
  ("Quelle part du marché le e-commerce représente-t-il ?",
   "Environ 15 % du chiffre d'affaires du secteur, avec une perspective autour de 19 %. Mais le lire uniquement comme un canal de prix est une erreur&nbsp;: c'est aussi un canal de discrétion, où l'on peut chercher sans être vu."),
  ("Comment étudier les freins au passage à l'acte ?",
   "Chez les gens, pas en salle. Un entretien à domicile, devant le projet en cours et le projet abandonné, produit une matière que ni le questionnaire ni le groupe ne donnent — parce que la peur de mal faire est précisément ce qu'on n'avoue pas devant les autres."),
 ],
 "aide": {"titre": "Aller voir ce qui bloque, là où ça bloque",
  "chapo": "Habitat, distribution de matériaux, DIY et décoration font partie de nos secteurs historiques, auprès des particuliers comme des professionnels.",
  "points": ["Entretiens à domicile, devant le projet en cours et le projet abandonné",
             "Terrain en rayon : ce qui se passe quand personne ne demande rien",
             "Dispositifs séparés particuliers / artisans — ils ne cherchent pas la même chose",
             "Recrutement dans votre fichier client quand vous en avez un : c'est le levier de coût le plus efficace"]},
 "loin": [("Un cas réel : recruter dans le fichier du client", "cas-fichier-client-materiaux.html"),
          ("Notre secteur Bâtiment", "secteur-batiment.html"),
          ("Comment rédiger un brief d'étude qualitative", "article-brief-etude-qualitative.html")],
},
]

# ═══════════════════════════════════════════════════════════════════════
#  PRODUCTION — les plans validés en veille éditoriale
#  Chaque article traite un sujet que les concurrents occupent, avec ce
#  qu'eux n'ont pas : quarante ans de terrain, la clinique produit, et le
#  droit de dire ce qui ne marche pas.
# ═══════════════════════════════════════════════════════════════════════

ARTICLES += [
{
 "slug": "article-declare-observe.html",
 "auteur": "VJ",
 "cat": "Point de vue",
 "date": "2026-08-26",
 "read": "9 min",
 "illus": "objet.webp",
 "title": "Ce que les gens disent, ce qu'ils font : l'écart",
 "h1": 'Personne ne ment.<br>Tout le monde reconstruit.',
 "desc": "Le déclaratif ne ment pas, il reconstruit. Trois écarts qu'on mesure sur le terrain, et ce que ça change sur un arbitrage produit.",
 "kw": "biais déclaratif, écart déclaré observé, comportement consommateur réel, clinique produit",
 "sources": [
  ("Agalma Études — au-delà du déclaratif", "un institut français sur le même constat, côté sciences comportementales", "https://agalma-etudes.com/blog/"),
  ("Square Cocoon — Prix d'un focus group", "repères de budget pour un dispositif en salle, 2026", "https://www.squarecocoon.fr/prix-d-un-focus-group/"),
  ("IntoTheMinds — Combien coûte une étude de marché", "les ordres de grandeur par méthode", "https://www.intotheminds.com/blog/combien-coute-une-etude-de-marche/"),
 ],
 "chapo": "« Est-ce que ce prix vous paraît acceptable ? » — oui. Trois mois plus tard, personne n'achète. Le participant n'a pas menti : on lui a posé une question à laquelle un être humain ne sait pas répondre.",
 "body": """
<h2>Pourquoi le déclaratif ment sans mentir</h2>
<p><strong>Parce qu'une décision se prend avant d'être expliquée, et que l'explication se fabrique après.</strong> Quand vous demandez à quelqu'un pourquoi il a choisi une voiture, il ne vous restitue pas son processus de décision&nbsp;: il en construit un, cohérent, présentable, et sincèrement cru.</p>
<p>Ce n'est pas de la mauvaise foi, c'est le fonctionnement normal de la mémoire. Le participant vous donne une reconstruction rationnelle d'un arbitrage qui ne l'était qu'en partie. Et cette reconstruction a une propriété gênante&nbsp;: elle est <em>plus rationnelle que la décision réelle</em>, parce qu'elle a été fabriquée pour être racontable.</p>
<p>D'où la règle qui organise tout notre travail de terrain&nbsp;: <strong>on ne demande pas aux gens d'expliquer, on leur demande de raconter, et on regarde ce qu'ils font.</strong></p>

<h2>Quels écarts mesure-t-on, et où se logent-ils&nbsp;?</h2>

<h3>1. La hiérarchie déclarée n'est pas la hiérarchie observée</h3>
<p>Interrogés en amont, les participants classent en tête des critères rationnels d'usage&nbsp;: coût, volume, autonomie, praticité. Devant l'objet, leurs premiers gestes et leurs premières réactions portent régulièrement sur d'autres registres — la posture, la matière, ce que l'objet dit d'eux.</p>
<p>Aucun questionnaire ne fait apparaître cet écart, parce qu'un questionnaire n'a accès qu'au déclaratif. C'est précisément la raison d'être d'une clinique produit.</p>

<h3>2. La préférence exprimée n'est pas le geste réel</h3>
<p>Sur trois directions présentées, une majorité peut désigner la même préférée — et se diriger, quelques minutes plus tard et sans consigne, vers une autre. L'écart est instructif à deux titres&nbsp;: il indique laquelle emporte l'adhésion, et il indique laquelle emporte le <em>choix</em>. Ce ne sont pas toujours les mêmes, et ce n'est pas la même décision qu'on prend selon celle qu'on écoute.</p>

<h3>3. L'usage raconté n'est pas l'usage constaté</h3>
<p>C'est l'écart le plus large, et il se voit chez les gens plutôt qu'en salle. Un artisan explique qu'il range ses outils «&nbsp;comme il faut&nbsp;». Un entretien à domicile devant le véhicule montre un rangement adapté à sa journée réelle, avec des contraintes qu'il n'aurait jamais énoncées parce qu'elles lui paraissent évidentes.</p>
""" + fig_matrice(
  "Ce que chaque registre donne, et ce qu'il cache",
  "Le déclaratif et l'observé ne sont pas en concurrence : ils répondent à deux questions différentes. L'erreur n'est pas d'écouter le déclaratif, c'est de croire qu'il décrit le comportement.",
  "Ce qu'on en fait", "Registre",
  [(0, 0, "Le déclaratif", "Ce que la personne pense de son choix, et comment elle le justifierait devant un tiers."),
   (1, 0, "L'observé", "Ce que la personne fait quand personne ne lui demande rien. Trente secondes suffisent."),
   (0, 1, "Utile pour", "Comprendre les représentations, le vocabulaire, ce qui est acceptable de dire."),
   (1, 1, "Utile pour", "Arbitrer un design, une ergonomie, un rayon — tout ce qui se joue avant la parole.")]) + """

<h2>Comment on rend l'écart visible</h2>
<p><strong>En observant avant de questionner, systématiquement.</strong> Sur une clinique produit, les trente premières secondes sont les plus informatives de la journée&nbsp;: par où la personne entre, ce qu'elle touche, ce qu'elle contourne, ce à quoi elle revient. Pendant ce temps, l'animateur ne dit rien.</p>
<p>Ce silence coûte cher à tenir. C'est aussi la différence la plus mesurable entre un animateur expérimenté et un animateur pressé — et l'un des rares points où l'automatisation ne peut rien&nbsp;: un dispositif sans humain dans la pièce n'observe pas, il enregistre des réponses.</p>
<p>Le protocole s'écrit ensuite à la minute, parce que <strong>l'ordre des expositions détermine les résultats</strong>. Faire réagir avant de faire comparer ne donne pas la même chose que l'inverse.</p>

<h2>Ce que ça change sur un arbitrage</h2>
<p>Sur une clinique auprès de possesseurs de véhicules électriques concurrents, la hiérarchie déclarée des critères plaçait en tête des arguments d'usage. Devant l'objet, les premières réactions et les premiers gestes portaient sur d'autres registres — et c'est cet écart, documenté poste par poste, qui a orienté l'arbitrage avant le gel du projet.</p>
<p>L'analyse livrée séparait explicitement les deux lectures. C'est un choix de restitution, pas de méthode&nbsp;: présenter une synthèse unique aurait obligé à trancher entre les deux registres à la place du client.</p>
<p class="art-more">Le dispositif complet, anonymisé&nbsp;: <a href="cas-clinique-electrique.html">arbitrer un design par les conducteurs de la concurrence</a>.</p>

<h2>Les trois questions qui font sortir le fait plutôt que l'opinion</h2>
<ol>
  <li><strong>« Racontez-moi votre mardi. »</strong> Pas votre semaine type — un mardi précis, celui de la semaine dernière. Le récit daté résiste beaucoup mieux à la reconstruction que le récit général.</li>
  <li><strong>« Montrez-moi. »</strong> Dès qu'un objet, un écran ou un lieu est disponible, faire faire plutôt que faire dire. La main sait des choses que la mémoire a oubliées.</li>
  <li><strong>« La dernière fois que ça ne s'est pas passé comme prévu ? »</strong> L'incident est le seul moment dont les gens se souviennent précisément, et il révèle la contrainte réelle mieux que dix questions de satisfaction.</li>
</ol>
<p>Et une question à ne jamais poser en ouverture&nbsp;: <em>«&nbsp;êtes-vous satisfait&nbsp;?&nbsp;»</em>. Sur un public professionnel, elle produit «&nbsp;ça fait le job&nbsp;» — et rien d'autre pendant vingt minutes.</p>

<h2>Pourquoi une IA ne voit pas cet écart</h2>
<p><strong>Parce qu'elle reçoit un texte, et que l'écart n'est pas dans le texte.</strong> Un modèle qui lit une transcription voit deux affirmations&nbsp;: l'explication rationnelle, puis, trente secondes plus tard, la description d'un comportement qui la contredit. Il en produit une version cohérente — c'est exactement ce qu'on lui demande de faire.</p>
<p>Un analyste, lui, entend la contradiction et la garde. C'est cette contradiction qui vaut le prix de l'étude.</p>
<p class="art-more">Le partage précis entre ce que nous automatisons et ce que nous n'automatisons jamais&nbsp;: <a href="article-ia-etudes-qualitatives.html">IA et études qualitatives</a>.</p>
""",
 "faq_titre": "Questions fréquentes",
 "faq": [
  ("Le déclaratif est-il inutile ?",
   "Non, il répond à une autre question. Le déclaratif dit ce que la personne pense de son choix et comment elle le justifierait&nbsp;; l'observé dit ce qu'elle fait. L'erreur n'est pas d'écouter le déclaratif, c'est de croire qu'il décrit le comportement."),
  ("Peut-on mesurer cet écart sans clinique produit ?",
   "En partie, par l'entretien à domicile devant l'objet ou le lieu d'usage. Ce qu'on perd, c'est la comparaison directe entre plusieurs alternatives présentes — et c'est souvent là que la hiérarchie réelle apparaît."),
  ("Combien de participants faut-il pour que l'écart soit lisible ?",
   "Une trentaine sur une clinique, une douzaine en entretiens à domicile. En dessous, un écart observé sur deux personnes ne se distingue pas d'une particularité individuelle."),
  ("Comment restituer deux lectures contradictoires à un comité ?",
   "En les séparant explicitement, poste par poste, avec les verbatims et les observations sources. Présenter une synthèse unique reviendrait à trancher entre les deux registres à la place du client — ce n'est pas notre rôle."),
  ("Un questionnaire quantitatif peut-il corriger ce biais ?",
   "Il l'amplifie, parce qu'il ne recueille que du déclaratif et sur un volume plus grand. Un écart massif et bien mesuré reste un écart. Le quantitatif dit combien&nbsp;; il ne dit pas ce que les gens font."),
 ],
 "aide": {"titre": "Aller voir plutôt que demander",
  "chapo": "Nous conduisons des cliniques produit depuis quarante ans, sur le secteur le plus exigeant que nous connaissions. Le principe vaut bien au-delà de l'automobile.",
  "points": ["Observation avant questionnement, avec un protocole écrit à la minute",
             "Entretiens à domicile ou sur le lieu d'usage, devant l'objet réel",
             "Analyse qui sépare explicitement le déclaré de l'observé, poste par poste",
             "Restitution en atelier, pour que l'écart soit discuté par ceux qui décident"]},
 "loin": [("Qu'est-ce qu'une car clinic ?", "article-car-clinic.html"),
          ("Un cas réel, anonymisé : arbitrer un design", "cas-clinique-electrique.html"),
          ("Entretiens individuels ou focus groups", "article-entretiens-ou-groupes.html")],
},

{
 "slug": "article-verbatims-donnees-personnelles.html",
 "auteur": "VB",
 "cat": "Repères",
 "date": "2026-08-26",
 "read": "8 min",
 "illus": "bulles.webp",
 "title": "Vos verbatims sont des données personnelles",
 "h1": "Une voix suffit<br>à identifier quelqu'un.",
 "desc": "Base légale, consentement, durée de conservation, sous-traitance IA : ce qu'un enregistrement d'entretien vous impose, et les questions à poser à votre prestataire.",
 "kw": "RGPD étude qualitative, verbatim données personnelles, consentement participant étude, IA sous-traitance données",
 "sources": [
  ("Syntec Conseil", "sept engagements pour un usage responsable de l'IA dans les études, mai 2025 : supervision humaine et transparence sur les outils", "https://syntec-conseil.fr/"),
  ("ESOMAR", "cadre déontologique international des études de marché et de l'opinion", "https://esomar.org/"),
  ("CNIL", "l'autorité française de référence sur le traitement des données personnelles", "https://www.cnil.fr/"),
  ("Gladia — tarifs et politique de données", "fournisseur français : désactivation de l'entraînement dès le plan Growth, rétention nulle en Enterprise", "https://www.gladia.io/pricing"),
 ],
 "chapo": "Un enregistrement d'entretien contient une voix, un prénom, un métier, parfois un état de santé ou une situation familiale. Juridiquement, ce n'est pas un « corpus » : c'est un traitement de données personnelles, avec tout ce que ça implique.",
 "body": """
<h2>Un enregistrement d'entretien, c'est quoi juridiquement ?</h2>
<p><strong>Une donnée personnelle, et parfois une donnée sensible.</strong> La voix identifie une personne. Le contenu peut révéler une opinion, un état de santé, une situation économique — trois catégories qui appellent des précautions renforcées.</p>
<p>Ça ne rend pas l'étude qualitative compliquée. Ça la rend <em>cadrée</em>, et le cadre se règle en une heure au moment du cadrage. Ce qui coûte cher, c'est de s'en apercevoir à la restitution.</p>

<h2>Les quatre obligations qui s'appliquent à toute étude</h2>
<ol>
  <li><strong>Une base légale.</strong> Pour une étude de marché, c'est presque toujours l'intérêt légitime ou le consentement. Le choix n'est pas indifférent&nbsp;: sur des données sensibles, le consentement explicite devient nécessaire.</li>
  <li><strong>Une information claire des participants.</strong> Qui traite, pourquoi, combien de temps, quels droits. Elle se donne avant l'entretien, pas au moment de lancer l'enregistrement.</li>
  <li><strong>Un consentement recueilli et conservé.</strong> À l'enregistrement, à la captation vidéo si elle a lieu, et à l'observation par un tiers derrière une glace sans tain — ce dernier point est le plus souvent oublié.</li>
  <li><strong>Une durée de conservation définie.</strong> Pas «&nbsp;jusqu'à nouvel ordre&nbsp;». Une durée écrite, appliquée, et distincte pour l'enregistrement brut et pour le corpus anonymisé.</li>
</ol>

<h2>Ce que change le passage par une IA</h2>
<p><strong>Chaque outil ajouté à la chaîne est un sous-traitant de plus, et parfois un transfert hors d'Europe.</strong> C'est le point où beaucoup de dispositifs se fragilisent sans que personne ne l'ait décidé&nbsp;: un outil de transcription pratique, essayé une fois, devenu habituel.</p>
""" + fig_chaine(
  "Le statut de vos données, maillon par maillon",
  "Les maillons pleins sont ceux où un tiers traite vos données. Chacun doit être identifié, contractualisé, et sa localisation connue — c'est la première question d'un service juridique.",
  [("Captation", "vous et nous"), ("Transcription", "sous-traitant"),
   ("Structuration", "sous-traitant"), ("Analyse", "nous"),
   ("Corpus livré", "vous")],
  pleines=0) + """
<p>Trois questions décident de la solidité de la chaîne&nbsp;:</p>
<ul>
  <li><strong>Où sont traitées les données&nbsp;?</strong> Un fournisseur européen évite la question du transfert. Un fournisseur français la ferme.</li>
  <li><strong>Servent-elles à entraîner un modèle&nbsp;?</strong> C'est une option, souvent activée par défaut, souvent désactivable. Il faut la désactiver et pouvoir le prouver.</li>
  <li><strong>Combien de temps sont-elles conservées chez le sous-traitant&nbsp;?</strong> Une rétention «&nbsp;pour amélioration du service&nbsp;» est une conservation.</li>
</ul>

<h2>Les questions à poser à votre prestataire</h2>
<p>Elles tiennent en cinq lignes, et une réponse évasive sur l'une d'elles est en soi une réponse&nbsp;:</p>
<div class="tw">
<table>
<thead><tr><th>Question</th><th>Ce qu'une bonne réponse contient</th></tr></thead>
<tbody>
<tr><td>Quels outils interviennent dans la chaîne&nbsp;?</td><td>Une liste nommée, pas une catégorie. «&nbsp;Un outil de transcription&nbsp;» n'est pas une réponse.</td></tr>
<tr><td>Où sont hébergées les données&nbsp;?</td><td>Un pays, et le cas échéant le mécanisme de transfert.</td></tr>
<tr><td>Entraînent-elles des modèles&nbsp;?</td><td>Non, avec la mention du plan contractuel qui le garantit.</td></tr>
<tr><td>Combien de temps sont-elles conservées&nbsp;?</td><td>Deux durées&nbsp;: enregistrement brut, corpus anonymisé.</td></tr>
<tr><td>Que contient le corpus livré&nbsp;?</td><td>Anonymisé ou pseudonymisé, et selon quelle règle.</td></tr>
</tbody>
</table>
</div>

<h2>Ce que nous faisons, et pourquoi c'est écrit</h2>
<p>La transcription passe par un <strong>fournisseur français</strong>, avec l'entraînement des modèles désactivé et sans rétention au-delà du traitement. Les corpus livrés sont anonymisés, avec la règle d'anonymisation indiquée. Les enregistrements bruts ont une durée de conservation distincte, arrêtée au cadrage.</p>
<p>Nous remettons cette chaîne par écrit en avant-vente, avant qu'on nous la demande. Ce n'est pas une précaution commerciale&nbsp;: c'est la transparence sur les outils que demande le cadre professionnel français depuis 2025, et c'est la seule façon pour un service juridique de valider un dispositif sans y passer trois semaines.</p>

<h2>Le cadre professionnel, au-delà de la loi</h2>
<p>Deux textes structurent la pratique française et vont plus loin que le strict minimum réglementaire&nbsp;:</p>
<ul>
  <li>Les <strong>engagements Syntec Conseil</strong> publiés en mai 2025&nbsp;: supervision humaine à chaque étape et transparence complète sur les outils employés.</li>
  <li>Le <strong>cadre ESOMAR</strong>, international, sur le consentement, l'indemnisation et la non-réutilisation des données des participants à d'autres fins.</li>
</ul>
<p>Les deux disent la même chose sous deux angles&nbsp;: un participant a accepté de parler pour une étude, pas pour alimenter un système.</p>
""",
 "faq_titre": "Questions fréquentes sur les données d'une étude",
 "faq": [
  ("Faut-il l'accord écrit des participants pour enregistrer ?",
   "Oui, et il doit couvrir séparément l'enregistrement, la captation vidéo si elle a lieu, et l'observation par un tiers. Ce dernier point — les observateurs derrière une glace sans tain — est le plus souvent omis."),
  ("Peut-on réutiliser un corpus pour une autre étude ?",
   "Pas sans base légale nouvelle et sans information des personnes. Un participant a consenti à une finalité précise&nbsp;; la réutilisation en est une autre. En pratique, on repart d'un corpus anonymisé quand c'est possible."),
  ("Combien de temps garder les enregistrements ?",
   "Une durée définie au cadrage et respectée, distincte pour l'enregistrement brut et pour le corpus anonymisé. «&nbsp;Jusqu'à nouvel ordre&nbsp;» n'est pas une durée."),
  ("Un outil de transcription américain pose-t-il problème ?",
   "Il ajoute une question de transfert hors Union européenne, qui se traite mais qui se traite <em>avant</em>. Passer par un fournisseur français supprime la question — c'est le choix que nous faisons."),
  ("Que doit contenir le corpus qu'on me livre ?",
   "Les transcripts intégraux et horodatés, anonymisés selon une règle explicite, avec les consignes de non-diffusion des matériaux nominatifs. Ils vous appartiennent, y compris si vous ne prenez pas l'analyse."),
 ],
 "aide": {"titre": "Un dispositif que votre juridique valide",
  "chapo": "Le cadre se règle au cadrage, en une heure, et il ne se rattrape pas après. Nous le remettons par écrit avant qu'on nous le demande.",
  "points": ["Chaîne de traitement écrite : quels outils, où, combien de temps",
             "Transcription par un fournisseur français, sans entraînement ni rétention",
             "Consentements couvrant enregistrement, vidéo et observation par un tiers",
             "Corpus livré anonymisé, avec la règle d'anonymisation indiquée"]},
 "loin": [("IA et études qualitatives : ce qu'elle rate encore", "article-ia-etudes-qualitatives.html"),
          ("Peut-on remplacer les répondants par de l'IA ?", "article-repondants-synthetiques.html"),
          ("Le livre blanc : la parole client jusqu'à la décision", "livre-blanc.html")],
},
]

ARTICLES += [
{
 "slug": "article-biais-etude.html",
 "auteur": "CC",
 "cat": "Méthode",
 "date": "2026-08-26",
 "read": "9 min",
 "illus": "groupes.webp",
 "title": "Huit biais qui faussent une étude qualitative",
 "h1": 'Huit biais faussent<br>une étude. Trois<br>viennent de vous.',
 "desc": "Désirabilité, dominance, relance orientée : les biais du terrain sont connus. Ceux du commanditaire le sont moins, et ils coûtent plus cher.",
 "kw": "biais étude qualitative, désirabilité sociale, biais confirmation étude marché, biais animateur",
 "sources": [
  ("Agalma Études — biais cognitifs et décisions d'achat", "un traitement complémentaire, côté sciences comportementales", "https://agalma-etudes.com/blog/"),
  ("ESOMAR", "cadre déontologique : indemnisation, consentement, non-réutilisation", "https://esomar.org/"),
  ("Syntec Conseil", "supervision humaine à chaque étape et transparence sur les outils, mai 2025", "https://syntec-conseil.fr/"),
 ],
 "chapo": "Tout le monde connaît la désirabilité sociale. Presque personne n'écrit sur les trois biais qui viennent de celui qui commande l'étude — parce que ça se dit mal quand on veut vendre. Ce sont pourtant les plus coûteux.",
 "body": """
<h2>Côté participant : quatre biais bien documentés</h2>
<p><strong>Ils sont connus, et ils se traitent par la conception du dispositif plutôt que par la vigilance de l'animateur.</strong></p>
<ul>
  <li><strong>La désirabilité sociale.</strong> On répond ce qu'il est acceptable de répondre. Elle s'aggrave en groupe, sur tout ce qui touche à l'argent, à la santé et à la compétence professionnelle. <em>Correctif&nbsp;:</em> l'entretien individuel sur ces sujets, sans exception.</li>
  <li><strong>La rationalisation a posteriori.</strong> Le participant reconstruit une décision plus rationnelle qu'elle ne l'a été. <em>Correctif&nbsp;:</em> faire raconter un épisode daté plutôt que demander d'expliquer.</li>
  <li><strong>L'effet de dominance.</strong> En quelques minutes, un groupe s'aligne sur le plus assuré. <em>Correctif&nbsp;:</em> des groupes homogènes en statut et en expertise, et un tour de table écrit avant la discussion ouverte.</li>
  <li><strong>Le répondant professionnel.</strong> Il connaît les codes, il donne de bonnes réponses. <em>Correctif&nbsp;:</em> deux filtres au recrutement — une question sur les participations récentes, une question ouverte à rédiger.</li>
</ul>

<h2>Côté animateur : deux biais qui ne se voient pas à la relecture</h2>
<ul>
  <li><strong>La relance qui oriente.</strong> «&nbsp;Donc c'est plutôt le prix qui vous a arrêté&nbsp;?&nbsp;» ferme le champ et produit une confirmation. Dans la transcription, la réponse paraîtra spontanée. <em>Correctif&nbsp;:</em> relancer sur le dernier mot du participant, pas sur une hypothèse.</li>
  <li><strong>Le silence non tenu.</strong> Les trois secondes après une réponse convenue sont l'endroit où la personne se reprend. Un animateur pressé les comble et perd la phrase. C'est la différence la plus mesurable entre un consultant senior et un vacataire.</li>
</ul>

<h2>Et les trois biais qui viennent de vous&nbsp;?</h2>
<p class="art-more" style="border-left-color:var(--ink);color:var(--grey-700)">Cette section est la seule raison d'écrire cet article. Les six biais précédents figurent dans tous les manuels&nbsp;; ceux-ci coûtent plus cher et n'apparaissent nulle part, parce qu'un prestataire les évoque rarement avec son client.</p>

<h3>7. Le brief qui contient déjà sa réponse</h3>
<p>«&nbsp;Comprendre pourquoi nos clients apprécient notre nouveau service&nbsp;» n'est pas une question d'étude&nbsp;: c'est une conclusion déguisée. Le dispositif construit dessus la confirmera, et il aura raison de le faire — c'est ce qu'on lui a demandé.</p>
<p><em>Correctif&nbsp;:</em> reformuler en question ouverte, et écrire les hypothèses concurrentes avant le terrain.</p>

<h3>8. L'échantillon choisi pour confirmer</h3>
<p>Recruter dans sa base client est excellent pour le coût et la justesse du profil — et biaise vers les clients actifs. Les partants et les perdus n'y sont pas. Sur une question de fidélité ou d'attrition, l'étude conclura à la satisfaction générale, ce qui sera vrai de l'échantillon et faux du marché.</p>
<p><em>Correctif&nbsp;:</em> annoncer la limite au cadrage, et compléter par un sourcing externe quand la question porte sur ceux qui sont partis.</p>

<h3>9. La restitution écoutée en cherchant l'accord</h3>
<p>Le biais le plus difficile à traiter, parce qu'il arrive quand tout est fini. Une salle qui écoute une restitution retient ce qui confirme la direction déjà prise et range le reste dans «&nbsp;cas particuliers&nbsp;». Le rapport est excellent, la décision est inchangée.</p>
<p><em>Correctif&nbsp;:</em> l'atelier plutôt que la présentation. On ne sort pas de la salle sans arbitrage écrit, ce qui oblige à traiter les constats gênants au lieu de les absorber.</p>
""" + fig_barres(
  "Où se logent les biais, et ce qu'ils coûtent",
  "Les biais du commanditaire arrivent plus tôt dans la chaîne et se corrigent moins tard : un brief mal posé fausse tout ce qui suit, alors qu'une relance orientée ne fausse qu'un passage. Estimation d'impact issue de notre pratique.",
  [("Brief orienté", 100, "fausse tout le dispositif"),
   ("Échantillon confirmant", 80, "fausse la conclusion"),
   ("Restitution filtrée", 70, "annule le bénéfice"),
   ("Dominance en groupe", 45, "fausse un groupe"),
   ("Relance orientée", 30, "fausse un passage")]) + """

<h2>Le seul antidote qui marche vraiment</h2>
<p><strong>Écrire les hypothèses concurrentes avant le terrain, et demander à l'étude de les départager.</strong> Pas «&nbsp;valider&nbsp;» l'une d'elles — les départager.</p>
<p>C'est une rubrique de trois lignes dans un brief, et c'est celle qui manque presque toujours. Son effet est mécanique&nbsp;: une étude qui doit trancher entre deux explications écrites ne peut pas revenir confirmer l'opinion du plus gradé, parce que les deux explications sont sur la table depuis le début et que chacun les a vues.</p>
<p>Deuxième effet, moins attendu&nbsp;: l'exercice fait remonter les désaccords internes <em>avant</em> de dépenser. Il arrive qu'on découvre à ce moment-là que le marketing et le produit n'attendaient pas la même chose de l'étude. C'est une heure très rentable.</p>
<p class="art-more">La rubrique et sa place dans un brief&nbsp;: <a href="article-brief-etude-qualitative.html">comment rédiger un brief d'étude qualitative</a>.</p>

<h2>Ce qu'un dispositif court aggrave — et ce qu'il n'aggrave pas</h2>
<p><strong>Il n'aggrave aucun des biais de terrain, à condition de ne pas toucher au recrutement.</strong> Un dispositif de quatre semaines avec un recrutement sur critères vérifiés et un consultant senior produit exactement la même qualité de matière qu'un dispositif de dix semaines.</p>
<p>Il aggrave en revanche deux choses&nbsp;: la tentation de sauter la semaine de cadrage — donc le biais 7 —, et la restitution expédiée en visioconférence de quarante-cinq minutes — donc le biais 9. Les deux se règlent en refusant de comprimer ces deux postes-là.</p>
<p class="art-more">Ce qui se comprime et ce qui ne se comprime pas&nbsp;: <a href="article-decider-vite.html">décider vite sans décider mal</a>.</p>
""",
 "faq_titre": "Questions fréquentes sur les biais",
 "faq": [
  ("Peut-on supprimer complètement les biais d'une étude qualitative ?",
   "Non, et ce n'est pas l'objectif. On les rend visibles et on les compense par la conception&nbsp;: composition des groupes, ordre des expositions, formulation des relances, hypothèses écrites. Un dispositif sans biais n'existe pas&nbsp;; un dispositif dont on connaît les biais se lit."),
  ("Comment savoir si mon brief est orienté ?",
   "Un test simple&nbsp;: si vous ne pouvez pas écrire l'hypothèse inverse sans qu'elle paraisse absurde, le brief contient déjà sa réponse. «&nbsp;Comprendre pourquoi ils apprécient&nbsp;» ne passe pas ce test&nbsp;; «&nbsp;comprendre ce qui les fait revenir ou partir&nbsp;» le passe."),
  ("Le recrutement en base client est-il à éviter ?",
   "Non, c'est le meilleur levier de coût et il améliore la justesse du profil. Il faut simplement savoir qu'il ne contient que des clients actifs, et compléter par un sourcing externe si la question porte sur l'attrition."),
  ("Une IA d'analyse réduit-elle les biais ?",
   "Elle en supprime un — la fatigue de l'analyste sur un gros corpus — et en ajoute un autre&nbsp;: elle produit la lecture la plus consensuelle et lisse les signaux minoritaires, qui sont souvent l'information neuve."),
  ("Faut-il que le client assiste au terrain ?",
   "Oui, derrière une glace sans tain ou en retour vidéo, jamais dans la salle. Assister réduit fortement le biais 9&nbsp;: on filtre beaucoup moins une restitution quand on a entendu les gens soi-même."),
 ],
 "aide": {"titre": "Un dispositif conçu contre ses propres biais",
  "chapo": "La partie la plus utile de notre travail se joue avant le terrain, au moment où l'on écrit ce que l'étude doit départager.",
  "points": ["Un cadrage qui reformule le brief en question ouverte, et écrit les hypothèses concurrentes",
             "Composition des groupes et ordre des expositions arrêtés contre les biais connus",
             "Animation par un consultant senior — les silences tenus ne s'automatisent pas",
             "Restitution en atelier plutôt qu'en présentation, jusqu'à l'arbitrage écrit"]},
 "loin": [("Comment rédiger un brief d'étude qualitative", "article-brief-etude-qualitative.html"),
          ("Ce que les gens disent, ce qu'ils font", "article-declare-observe.html"),
          ("Entretiens individuels ou focus groups", "article-entretiens-ou-groupes.html")],
},

{
 "slug": "article-packaging-avant-lecture.html",
 "auteur": "CC",
 "cat": "Méthode",
 "date": "2026-08-26",
 "read": "8 min",
 "illus": "terrain.webp",
 "title": "Ce qu'un packaging dit avant qu'on l'ait lu",
 "h1": "Trois secondes en rayon,<br>et rien n'a été lu.",
 "desc": "En rayon, la reconnaissance de catégorie précède la lecture. Pourquoi un test de packaging en salle se trompe souvent, et la consigne qui change tout.",
 "kw": "test packaging, sémiologie packaging, codes de catégorie rayon, test concept emballage",
 "sources": [
  ("Agalma Études — sémiologie appliquée au marketing", "un traitement complémentaire de la méthode", "https://agalma-etudes.com/blog/"),
  ("Square Cocoon — Prix d'un focus group", "repères de budget pour un dispositif en salle, 2026", "https://www.squarecocoon.fr/prix-d-un-focus-group/"),
 ],
 "chapo": "Un consommateur passe moins de trois secondes devant un produit qu'il n'achète pas. Dans ces trois secondes, il n'a rien lu — et il a pourtant décidé si le produit fait partie de son monde.",
 "body": """
<h2>Les trois secondes qui décident en rayon</h2>
<p><strong>La reconnaissance de catégorie précède la lecture, et elle se joue sur la forme, la couleur et la densité — jamais sur le texte.</strong> Avant de savoir ce qu'est un produit, on sait s'il appartient au rayon qu'on cherche. Cette reconnaissance est si rapide qu'elle n'est pas consciente&nbsp;: interrogé, un client vous parlera du prix et des ingrédients, c'est-à-dire de ce qu'il a lu <em>après</em> avoir décidé de regarder.</p>
<p>C'est le premier écart que le terrain rend visible, et c'est celui qui coûte le plus cher à ignorer&nbsp;: un packaging qui rate la reconnaissance de catégorie n'est jamais lu, donc jamais évalué, donc jamais testé par le marché.</p>

<h2>Que lit-on sans le savoir&nbsp;?</h2>
<p>Quatre registres portent l'essentiel du message avant tout mot&nbsp;:</p>
<ul>
  <li><strong>La couleur comme code de catégorie</strong> — elle dit d'abord «&nbsp;je suis un yaourt&nbsp;», ensuite seulement «&nbsp;je suis cette marque&nbsp;». S'en écarter est une décision stratégique, pas graphique.</li>
  <li><strong>La densité d'information</strong> — un packaging chargé signale le fonctionnel et le rapport qualité-prix&nbsp;; un packaging vide signale le premium ou le naturel. Le contenu du texte compte moins que sa quantité.</li>
  <li><strong>La matière et le rendu</strong> — mat contre brillant, papier contre plastique&nbsp;: le registre se lit à distance, avant la main.</li>
  <li><strong>La silhouette</strong> — le contour reconnaissable à un mètre. C'est ce qui survit à la vision périphérique, et c'est ce qu'on teste en dernier.</li>
</ul>
""" + fig_matrice(
  "Les deux tensions d'un packaging, et l'arbitrage qu'elles imposent",
  "Un packaging doit ressembler assez à sa catégorie pour être trouvé, et s'en écarter assez pour être choisi. Les deux exigences se contredisent, et c'est l'arbitrage réel d'une refonte.",
  "Distance de lecture", "Fonction du signe",
  [(0, 0, "Code de catégorie", "Ce qui permet d'être trouvé dans le rayon. Se lit à un mètre, en vision périphérique."),
   (1, 0, "Signature de marque", "Ce qui permet d'être choisi plutôt qu'un autre. Se lit à trente centimètres."),
   (0, 1, "Ce qu'on ne bouge pas", "Trop s'écarter du code de catégorie, c'est sortir du rayon dans la tête du client."),
   (1, 1, "Ce qu'on peut bouger", "La signature, si le code tient. C'est là que se gagne la préférence.")]) + """

<h2>Pourquoi un test de packaging en salle se trompe souvent</h2>
<p><strong>Parce qu'il fait lire ce que personne ne lit.</strong> Posez un packaging sur une table devant six personnes attentives, demandez ce qu'elles en pensent&nbsp;: elles vont le prendre en main, le retourner, lire la composition, commenter la typographie. Aucun de ces gestes n'a lieu en rayon.</p>
<p>Le test produit alors un matériau sincère et inutilisable&nbsp;: des avis sur un objet examiné, alors que la décision réelle se prend sur un objet aperçu.</p>
<p>Deux dispositifs corrigent cela&nbsp;:</p>
<ul>
  <li><strong>Le rayon simulé</strong> — le produit est présenté au milieu de ses concurrents, à distance de rayon, avec un temps d'exposition limité. On mesure d'abord ce qui est vu, ensuite ce qui est compris.</li>
  <li><strong>L'observation en magasin</strong> — plus lourde, mais c'est la seule qui donne accès au parcours réel&nbsp;: par où on entre dans le rayon, ce qu'on prend en main, ce qu'on repose.</li>
</ul>

<h2>La méthode : faire décrire avant de faire juger</h2>
<p><strong>La consigne d'ouverture détermine tout ce qui suit.</strong> «&nbsp;Qu'en pensez-vous&nbsp;?&nbsp;» déclenche l'évaluation, donc le registre de l'opinion, donc la justification. «&nbsp;Décrivez-moi ce que vous voyez&nbsp;» déclenche la description, donc l'accès aux signes.</p>
<p>Concrètement, l'ordre qui fonctionne&nbsp;:</p>
<ol>
  <li><strong>Exposition brève, sans consigne.</strong> Ce qui est vu en trois secondes, et dans quel ordre.</li>
  <li><strong>Description libre.</strong> «&nbsp;Qu'est-ce que c'est&nbsp;?&nbsp;» avant «&nbsp;est-ce que ça vous plaît&nbsp;?&nbsp;»</li>
  <li><strong>Attribution.</strong> «&nbsp;Ça pourrait être quelle marque&nbsp;? Ça coûte combien, à votre avis&nbsp;?&nbsp;» — la réponse au prix estimé est l'un des indicateurs les plus fiables du registre perçu.</li>
  <li><strong>Comparaison.</strong> Seulement à ce moment, et avec les concurrents réels présents.</li>
  <li><strong>Jugement.</strong> En dernier, quand il ne peut plus contaminer le reste.</li>
</ol>

<h2>Ce que ça donne sur une refonte de gamme</h2>
<p>La question opérationnelle d'une refonte n'est jamais «&nbsp;est-ce que le nouveau packaging plaît&nbsp;?&nbsp;» mais «&nbsp;qu'est-ce qu'on garde&nbsp;?&nbsp;». Le terrain répond en séparant deux inventaires&nbsp;:</p>
<ul>
  <li><strong>Ce qui appartient à la catégorie</strong> et qu'on ne peut pas abandonner sans sortir du rayon.</li>
  <li><strong>Ce qui appartient à la marque</strong> et que les clients reconnaissent — souvent des détails que l'entreprise juge secondaires, et parfois pas ceux qu'elle croyait.</li>
</ul>
<p>C'est l'inventaire le plus utile qu'une étude de packaging puisse produire, et il ne s'obtient pas en demandant aux gens ce qu'ils préfèrent.</p>
""",
 "faq_titre": "Questions fréquentes sur les tests de packaging",
 "faq": [
  ("Combien de participants pour un test de packaging ?",
   "Deux groupes par segment à comparer, ou une vingtaine de passages en rayon simulé. Le volume compte moins que les conditions d'exposition&nbsp;: mieux vaut douze personnes en rayon simulé que trente autour d'une table."),
  ("Faut-il montrer les concurrents ?",
   "Toujours, et réels. Une préférence exprimée dans l'absolu vaut peu&nbsp;; une préférence exprimée devant les alternatives que le client rencontrera vraiment vaut une décision."),
  ("Peut-on tester un packaging en ligne ?",
   "Pour la reconnaissance de catégorie et la lisibilité à distance, oui, avec un temps d'exposition contrôlé. Pour la matière, le poids et le geste d'ouverture, non — et ces trois-là portent une part du positionnement."),
  ("Le prix estimé par les participants est-il fiable ?",
   "Pas comme prévision de prix acceptable, mais oui comme <em>indicateur de registre perçu</em>. Un écart important entre le prix estimé et le prix réel signale un problème de positionnement visuel, pas de tarif."),
  ("À quel stade du projet tester ?",
   "Deux fois. Une fois tôt, sur des directions encore ouvertes, en test de concept peu coûteux. Une fois tard, sur les maquettes réelles en rayon simulé. Le test unique en fin de parcours n'arbitre plus rien&nbsp;: il valide ou il inquiète."),
 ],
 "aide": {"titre": "Tester un packaging dans les conditions du rayon",
  "chapo": "Retail, grande consommation, cosmétique et parfumerie font partie de nos secteurs historiques, du test de concept au rayon simulé.",
  "points": ["Rayon simulé avec les concurrents réels et un temps d'exposition contrôlé",
             "Protocole qui fait décrire avant de faire juger — la consigne détermine le matériau",
             "Observation en magasin quand la question porte sur le parcours réel",
             "Restitution qui sépare le code de catégorie de la signature de marque"]},
 "loin": [("Ce que les gens disent, ce qu'ils font", "article-declare-observe.html"),
          ("Notre secteur Retail et FMCG", "secteur-retail-fmcg.html"),
          ("Composer votre dispositif", "decision-rapide.html#configurateur")],
},
]

# ═══════════════════════════════════════════════════════════════════════
#  GABARIT SECTORIEL — « où se joue vraiment la décision »
#  Écrit une fois, décliné six fois. Chaque déclinaison apporte ses
#  chiffres datés et son « moment sous-estimé » — c'est ce moment qui
#  fait l'article ; le reste est une charpente commune.
# ═══════════════════════════════════════════════════════════════════════

SECTEURS_PARCOURS = [
{
 "slug": "parcours-mobilite.html",
 "auteur": "VJ",
 "h1": "Un porche trop bas élimine<br>plus de modèles<br>qu'un argumentaire.",
 "h2_ou": 'À quel moment la liste courte se ferme-t-elle&nbsp;?',
 "faq": [
  ("Combien de temps dure un parcours d'achat automobile ?", "Six à neuf mois entre le déclencheur et la signature, dont l'essentiel se passe hors de votre vue. Ce qui compte n'est pas la durée mais le moment où la liste courte se ferme&nbsp;: après, tout ce que vous direz arrive trop tard."),
  ("Peut-on étudier un véhicule qui n'existe pas encore ?", "Oui, sur maquette à l'échelle ou en clinique statique avec des directions de design. Ce qu'on perd par rapport à un prototype roulant&nbsp;: le comportement routier perçu, le bruit et l'ergonomie en situation. Ce qu'on garde&nbsp;: l'arbitrage sur les proportions et la posture, qui se joue à l'arrêt."),
  ('Faut-il interroger les possesseurs de la marque ou ceux de la concurrence ?', "Ceux de la concurrence, sur le modèle précis qu'ils possèdent. L'avis d'un client fidèle porte sur ce qu'il connaît déjà&nbsp;; celui d'un conducteur d'un modèle rival porte sur ce qui l'a fait choisir autre chose — l'information que vous n'avez pas."),
  ("Le parcours est-il le même sur l'électrique ?", "Non&nbsp;: la phase de repérage s'allonge, la question du coût total et de la valeur de revente arrive beaucoup plus tôt, et l'entourage pèse davantage. Interroger des conducteurs thermiques sur un véhicule électrique recueille des craintes fantasmées plutôt que des contraintes vécues."),
 ],
 "secteur": "l'automobile", "cat": "Parcours · Mobilité",
 "illus": "voiture.webp", "page_secteur": "secteur-mobilite.html",
 "titre_court": "automobile", "read": "8 min",
 "chapo": "Entre le moment où quelqu'un se dit qu'il va changer de voiture et celui où il signe, il se passe six à neuf mois. La concession n'intervient que sur les trois dernières semaines.",
 "chiffres": [("857 177", "immatriculations en France au premier semestre 2026", "Carte Grise, juillet 2026"),
              ("−26,5 %", "de volume par rapport au premier semestre 2019", "Carte Grise, juillet 2026"),
              ("20 000 €", "le seuil qui structure l'entrée de gamme", "Prix d'appel constructeurs, 2026")],
 "etapes": [("Déclencheur", "une panne, un enfant"), ("Repérage", "en ligne, seul"),
            ("Comparaison", "deux ou trois modèles"), ("Décision", "en concession"),
            ("Usage", "les six premiers mois")],
 "plein": 1,
 "ou": "Le repérage, qui dure des mois et se fait entièrement hors de votre vue. Quand le client entre en concession, la liste courte est déjà écrite.",
 "sous_estime": ("Le passage sous le porche", """<p>Sur les utilitaires et les citadines, une contrainte physique décide plus souvent qu'un argument commercial&nbsp;: la hauteur d'un porche, la largeur d'une place de parking résidentielle, l'accès à un parking souterrain d'immeuble.</p>
<p>Personne ne la mentionne spontanément, parce qu'elle paraît trop banale pour être dite. Elle apparaît dès qu'on fait raconter une journée plutôt qu'évaluer un véhicule — et elle élimine des modèles entiers avant tout essai.</p>"""),
 "dispositif": "Clinique produit avec les concurrents réels présents, complétée d'entretiens à domicile devant le véhicule actuel. Le recrutement se fait sur véhicule possédé, vérifié — c'est le critère le plus coûteux à sourcer et celui qui rend les avis opérants.",
 "questions": ["Combien de vos acheteurs avaient déjà arrêté leur modèle avant le premier contact&nbsp;?",
               "Que savez-vous de ceux qui ont configuré en ligne sans jamais venir&nbsp;?",
               "Vos remontées après-vente signalent-elles des contraintes d'usage, ou seulement des défauts&nbsp;?"],
 "sources": [("Marché automobile français S1 2026", "857 177 immatriculations, +1,8 % sur un an", "https://www.cartegrise.com/blog/2026/07/marche-automobile-francais-s1-2026-le-grand-bilan-dun-semestre-de-bascule"),
             ("Atlas Automobiles — marché français", "record historique pour l'électrique en 2026", "https://atlas-automobiles.com/articles/aamarche-automobile-france-mai-2026-3-7-d-immatriculations-et-record-historique-pour-l-electrique")],
 "loin": [("Citadines : la France et le Royaume-Uni divergent", "marche-citadines-france-uk.html"),
          ("Qu'est-ce qu'une car clinic ?", "article-car-clinic.html")],
},
{
 "slug": "parcours-retail-fmcg.html",
 "auteur": "TN",
 "h1": "Le geste qui vous coûte<br>le plus, c'est celui<br>de reposer.",
 "h2_ou": 'Que se passe-t-il dans les trois secondes du rayon&nbsp;?',
 "faq": [
  ('Combien de temps dure un arbitrage en rayon ?', "Moins de trois secondes sur un produit qu'on n'achète pas. Dans ce laps de temps, rien n'a été lu&nbsp;: la reconnaissance de catégorie s'est faite sur la forme, la couleur et la densité d'information."),
  ('Les données de caisse suffisent-elles à comprendre le rayon ?', "Elles décrivent ce qui a été acheté. Elles ne voient ni le produit pris puis reposé, ni le client qui n'est jamais entré dans le rayon — et ces deux populations expliquent l'essentiel de l'écart entre le trafic et le chiffre d'affaires."),
  ('Faut-il tester en rayon simulé ou en magasin réel ?', "Le rayon simulé pour arbitrer entre des directions, parce qu'on contrôle l'exposition et les concurrents présents. Le magasin réel quand la question porte sur le parcours, c'est-à-dire sur ce qui se passe avant d'arriver devant le produit."),
  ('Les acheteurs drive et les acheteurs magasin se comportent-ils pareil ?', "Non, et souvent ce ne sont même pas les mêmes personnes selon les catégories. Le drive supprime l'arbitrage de rayon et le remplace par une liste et un moteur de recherche&nbsp;: ce qui se gagne en linéaire ne se gagne pas de la même façon en ligne."),
 ],
 "secteur": "la grande consommation", "cat": "Parcours · Retail & FMCG",
 "illus": "donnees.webp", "page_secteur": "secteur-retail-fmcg.html",
 "titre_court": "grande consommation", "read": "8 min",
 "chapo": "Un arbitrage de rayon dure moins de trois secondes et se prend sur des signes, pas sur des arguments. Tout ce qui précède — la marque, la publicité, le prix — sert à entrer dans la liste courte, pas à gagner l'arbitrage.",
 "chiffres": [("13,3 %", "des dépenses PGC passent par l'e-commerce alimentaire en France", "Presse spécialisée, 2026"),
              ("~125 €", "de panier moyen, après +22 % d'inflation cumulée depuis 2021", "Presse spécialisée, 2026"),
              ("+2 pts", "de part de marché captés par les cinq premiers distributeurs entre 2023 et 2025", "Presse spécialisée, 2026")],
 "etapes": [("Déclencheur", "la liste, l'habitude"), ("Repérage", "le rayon, le drive"),
            ("Comparaison", "trois secondes"), ("Décision", "la main"),
            ("Usage", "le réachat")],
 "plein": 2,
 "ou": "Dans le rayon, sur des signes lus avant tout texte. La comparaison réelle porte sur trois références, pas sur la catégorie entière.",
 "sous_estime": ("Le produit qu'on repose", """<p>Le geste le plus informatif d'un parcours d'achat n'est pas la prise en main&nbsp;: c'est le fait de reposer. Quelqu'un qui prend un produit puis le repose a hésité, comparé, tranché contre vous — en trois secondes, et sans jamais pouvoir vous dire pourquoi.</p>
<p>Aucune donnée de caisse ne le voit, puisqu'il n'y a pas eu de transaction. C'est l'angle mort le plus large de la connaissance client en grande consommation, et il ne se comble que par l'observation.</p>"""),
 "dispositif": "Rayon simulé avec les concurrents réels et un temps d'exposition contrôlé, complété d'observation en magasin quand la question porte sur le parcours. La consigne d'ouverture fait décrire avant de faire juger — sinon on recueille des opinions sur un objet examiné, pas des réactions à un objet aperçu.",
 "questions": ["Que savez-vous de ceux qui ont pris votre produit puis l'ont reposé&nbsp;?",
               "Vos acheteurs drive et vos acheteurs magasin sont-ils les mêmes personnes&nbsp;?",
               "Votre code de catégorie a-t-il bougé sans que vous l'ayez décidé&nbsp;?"],
 "sources": [("Parts de marché de la grande distribution en France", "bilan 2025 et perspectives 2026", "https://www.catalog-prospectus.fr/articles/parts-de-marche-grande-distribution-france-bilan-2025-et-perspectives-2026-leclerc-resiste-carrefour-et-u-progressent"),
             ("LSA Conso — négociations commerciales 2026", "une quasi-stabilité des prix en magasin", "https://www.lsa-conso.fr/grande-distribution-les-negos-2026-se-concluent-sur-une-quasi-stabilite-des-prix-en-magasins-mais-de-fortes-tensions-avec-les-industriels,464749")],
 "loin": [("Ce qu'un packaging dit avant qu'on l'ait lu", "article-packaging-avant-lecture.html"),
          ("Ce que les gens disent, ce qu'ils font", "article-declare-observe.html")],
},
{
 "slug": "parcours-sante-cosmetiques.html",
 "auteur": "CC",
 "h1": "Un produit qui ne trouve<br>pas sa place sur l'étagère<br>ne revient pas.",
 "h2_ou": "Pourquoi un produit acheté n'est-il pas réacheté&nbsp;?",
 "faq": [
  ('Comment étudier une routine cosmétique ?', "À domicile, devant l'étagère réelle, avec un test en usage sur plusieurs semaines. En salle, un participant décrit une routine idéale&nbsp;; devant son étagère, il montre les trois produits achetés et jamais finis, et il explique pourquoi."),
  ("Peut-on interroger en groupe sur des sujets de peau ou d'âge ?", "Nous l'évitons. Sur tout ce qui touche au corps, à l'âge ou à la santé, le groupe produit une vérité collective très propre et très fausse&nbsp;: chacun se cale sur ce qu'il est acceptable de dire. L'entretien individuel est le seul dispositif honnête."),
  ("Comment savoir pourquoi un produit n'est pas réacheté ?", "En allant voir ce qu'il devait remplacer. Un produit qui ne trouve pas sa place dans un enchaînement de gestes existant n'est jamais réacheté, et le client ne le formulera jamais ainsi&nbsp;: il dira qu'il « n'a pas accroché »."),
  ("Le conseil en pharmacie influence-t-il vraiment l'achat ?", "Le circuit pharmacie et parapharmacie capte environ 45 % des volumes en valeur, ce qui en fait le premier canal du marché français. La question utile n'est pas s'il influence, mais ce qu'il dit réellement de votre produit — et ça, seul le terrain le montre."),
 ],
 "secteur": "la cosmétique", "cat": "Parcours · Santé & Cosmétiques",
 "illus": "conversation.webp", "page_secteur": "secteur-sante-cosmetiques.html",
 "titre_court": "cosmétique", "read": "8 min",
 "chapo": "En cosmétique, la décision d'achat n'est presque jamais isolée : elle s'insère dans une routine existante, qu'il faut déplacer. C'est ce déplacement qui coûte, pas le produit.",
 "chiffres": [("~68 Mds €", "de chiffre d'affaires pour le marché cosmétique français", "Sources sectorielles 2026 — l'année de référence varie selon les publications"),
              ("45 %", "des volumes en valeur captés par pharmacies et parapharmacies", "Sources sectorielles, 2026"),
              ("23 %", "du secteur pour la cosmétique biologique", "Sources sectorielles, 2026")],
 "etapes": [("Déclencheur", "un changement de peau"), ("Repérage", "conseil, avis, réseaux"),
            ("Comparaison", "la composition"), ("Décision", "l'essai"),
            ("Usage", "la routine, ou pas")],
 "plein": 4,
 "ou": "Dans l'usage, pas à l'achat. Un produit acheté qui ne trouve pas sa place dans une routine existante n'est jamais réacheté — et personne ne vous le dira.",
 "sous_estime": ("La place sur l'étagère", """<p>Une routine cosmétique est un enchaînement physique&nbsp;: un ordre de gestes, une place dans la salle de bains, un moment de la journée. Un produit nouveau doit s'y insérer, ce qui veut dire en déplacer un autre.</p>
<p>C'est là que se joue le réachat, et ça ne s'observe qu'à domicile. En salle, un participant vous décrira une routine idéale&nbsp;; devant son étagère, il vous montrera les trois produits achetés et jamais finis, et il vous dira pourquoi.</p>"""),
 "dispositif": "Entretiens à domicile devant l'étagère réelle, avec test produit en usage sur plusieurs semaines. Sur les sujets sensibles — peau, âge, corps — l'entretien individuel est le seul dispositif honnête : le groupe produit une vérité collective très propre et très fausse.",
 "questions": ["Vos acheteurs de premier flacon reviennent-ils, et au bout de combien de temps&nbsp;?",
               "Que remplace votre produit dans la routine de vos clients&nbsp;?",
               "Le conseil en pharmacie dit-il de votre produit ce que vous croyez qu'il en dit&nbsp;?"],
 "sources": [("Marché des cosmétiques — chiffres et tendances", "repères de marché français, 2026", "https://independant.io/tendances-chiffres-marche-cosmetiques/"),
             ("Analyse du marché de la cosmétique en France", "structure du marché et canaux de distribution", "https://modelesdebusinessplan.com/blogs/infos/marche-cosmetique-france")],
 "loin": [("Entretiens individuels ou focus groups", "article-entretiens-ou-groupes.html"),
          ("Vos verbatims sont des données personnelles", "article-verbatims-donnees-personnelles.html")],
},
{
 "slug": "parcours-batiment.html",
 "auteur": "TN",
 "h1": 'Il est entré, il a regardé,<br>il est reparti. Vous ne<br>le saurez jamais.',
 "h2_ou": "Où se perd le client d'une grande surface de bricolage&nbsp;?",
 "faq": [
  ("Comment interroger quelqu'un qui a renoncé à son projet ?", "En le faisant parler du projet en cours d'abord, du projet abandonné ensuite. La comparaison des deux, chez lui, produit une matière que la question directe ne donne jamais&nbsp;: on n'aime pas raconter un renoncement, mais on accepte de le comparer."),
  ('Les particuliers et les artisans demandent-ils la même chose ?', 'Non, et les traiter ensemble en déçoit un sur deux. Un artisan cherche une référence précise et un délai&nbsp;; un particulier cherche une réponse et une réassurance. Deux dispositifs séparés, deux guides différents.'),
  ('Comment mesurer ceux qui repartent sans rien acheter ?', "Par l'observation en rayon, parce qu'ils n'apparaissent dans aucun indicateur — ni vente, ni retour, ni réclamation. C'est l'angle mort le plus large de la distribution de matériaux, et il est entièrement observable."),
  ('La peur de mal faire se traite-t-elle par la promotion ?', "Non, et c'est ce qui rend le sujet intéressant. Une remise de 20 % ne réduit pas la crainte de percer au mauvais endroit. Ce frein se traite par le conseil, la pédagogie, la garantie de résultat et la conception du produit."),
 ],
 "secteur": "le bâtiment", "cat": "Parcours · Bâtiment",
 "illus": "brief.webp", "page_secteur": "secteur-batiment.html",
 "titre_court": "bâtiment et matériaux", "read": "8 min",
 "chapo": "Un particulier qui entre dans une grande surface de bricolage ne cherche pas un produit : il cherche l'assurance de ne pas se tromper. Sept sur dix ne l'obtiennent pas.",
 "chiffres": [("21,8 Mds €", "de chiffre d'affaires en grandes surfaces de bricolage en 2025", "Points de Vente, 2026"),
              ("9 / 10", "Français déclarent bricoler", "Étude sectorielle, 2026"),
              ("7 / 10", "sont freinés par la peur de mal faire", "Étude sectorielle, 2026")],
 "etapes": [("Déclencheur", "une panne, un projet"), ("Repérage", "tutoriels, entourage"),
            ("Comparaison", "en rayon, seul"), ("Décision", "ou renoncement"),
            ("Usage", "et retour éventuel")],
 "plein": 3,
 "ou": "En rayon, au moment où il faudrait demander — et où beaucoup ne demandent pas. Le renoncement silencieux est la moitié de l'histoire.",
 "sous_estime": ("Celui qui repart sans rien", """<p>La peur de mal faire produit un comportement précis&nbsp;: on entre, on regarde longtemps, on ne demande pas, on repart. Ce client-là n'apparaît dans aucun indicateur — ni vente, ni retour, ni réclamation.</p>
<p>Il explique une part importante de l'écart entre le trafic en magasin et le chiffre d'affaires, et il est aussi celui qui bascule le plus facilement vers le e-commerce, où l'on peut chercher longtemps sans être vu.</p>"""),
 "dispositif": "Entretiens à domicile devant le projet en cours et le projet abandonné — c'est la comparaison des deux qui produit la matière. Complétés d'observation en rayon : ce qui se passe quand personne ne demande rien. Les particuliers et les artisans demandent des dispositifs séparés, ils ne cherchent pas la même chose.",
 "questions": ["Que savez-vous de ceux qui sont venus, ont regardé, et sont repartis&nbsp;?",
               "Vos vendeurs sont-ils sollicités par les clients qui en ont le plus besoin&nbsp;?",
               "Vos retours produits signalent-ils une erreur d'achat ou un défaut&nbsp;?"],
 "sources": [("Points de Vente — marché du bricolage", "21,8 Mds € en 2025, troisième année de recul", "https://pointsdevente.fr/fil-info/2026-06-15-le-marche-du-bricolage-toujours-en-recul-malgre-le-rebond-de-limmobilier/"),
             ("Bricolage en France 2026", "9 Français sur 10 bricolent, 7 sur 10 freinés par la peur de mal faire", "https://www.montrealmirror.com/actu10359/bricolage-france-2026-marche-stabilisation-peur-de-mal-faire.html")],
 "loin": [("Bricolage : neuf sur dix bricolent, sept ont peur", "marche-bricolage-peur-de-mal-faire.html"),
          ("Un cas réel : recruter dans le fichier du client", "cas-fichier-client-materiaux.html")],
},
{
 "slug": "parcours-mode-luxe.html",
 "auteur": "CC",
 "h1": 'Huit secondes sur le seuil<br>décident de vingt ans.',
 "h2_ou": "Qu'est-ce qui se joue sur le seuil d'une boutique&nbsp;?",
 "faq": [
  ("Comment interroger des clients qui ont cessé d'acheter ?", "En les recrutant sur comportement d'achat passé plutôt que sur fichier client&nbsp;: ils n'y sont plus. Le sourcing coûte davantage, et c'est la population la plus informative du marché — celle dont la disparition explique vingt millions de clients perdus en un an."),
  ("Peut-on étudier l'expérience en boutique sans y être ?", "Non. La gêne du client d'entrée de catégorie ne figure dans aucun baromètre, pour une raison mécanique&nbsp;: ceux qui la ressentent ne remplissent pas les questionnaires, ils ne reviennent pas. Il faut être là, puis les interroger à la sortie."),
  ('La seconde main change-t-elle le parcours ?', "Profondément, et surtout chez les moins de trente-cinq ans&nbsp;: le neuf cesse d'être la norme et devient une option parmi d'autres. Un dispositif qui ne met pas la seconde main dans le jeu concurrentiel passe à côté de l'arbitrage réel."),
  ("Qu'est-ce qui déclenche un premier achat de luxe aujourd'hui ?", "Ce n'est plus ce que c'était il y a quinze ans, et c'est précisément ce qu'il faut aller chercher. La première marche n'est pas un prix&nbsp;: c'est un franchissement, et ce qui s'y joue décide de vingt ans de relation ou de son absence."),
 ],
 "secteur": "le luxe", "cat": "Parcours · Mode & Luxe",
 "illus": "fuite.webp", "page_secteur": "secteur-mode-luxe.html",
 "titre_court": "mode et luxe", "read": "8 min",
 "chapo": "Le premier achat de luxe n'est pas un achat : c'est un franchissement. Ce qui se joue à ce moment-là décide de vingt ans de relation — ou de son absence.",
 "chiffres": [("330 M", "de clients actifs du luxe dans le monde, contre 400 M trois ans plus tôt", "Bain & Company, 2026"),
              ("−20 M", "de consommateurs perdus sur la seule année 2025", "Bain & Company, 2026"),
              ("~75 %", "du marché porté par les Millennials et la Génération Z", "BCG")],
 "etapes": [("Déclencheur", "une occasion, un statut"), ("Repérage", "seconde main comprise"),
            ("Décision", "franchir la porte"), ("Achat", "ou renoncement"),
            ("Relation", "sur vingt ans")],
 "plein": 2,
 "ou": "Sur le seuil de la boutique, avant tout contact commercial. Les huit premières secondes décident du retour.",
 "sous_estime": ("La gêne de celui qui n'ose pas demander", """<p>Le client d'entrée de catégorie décrit régulièrement une gêne précise&nbsp;: ne pas savoir comment se comporter, être identifié comme non-acheteur, ne pas oser demander un prix.</p>
<p>Cette gêne ne figure dans aucun baromètre de satisfaction, pour une raison mécanique&nbsp;: les gens qui la ressentent ne remplissent pas les questionnaires. Ils ne reviennent pas. C'est exactement la population dont la disparition explique les vingt millions de clients perdus en un an.</p>"""),
 "dispositif": "Observation accompagnée en boutique, puis entretien individuel hors du lieu — la parole se libère à la sortie, pas sur place. Le recrutement se fait sur comportement d'achat passé plutôt que sur fichier client actif : ceux qui sont partis ne sont plus dans vos bases, et ce sont eux qui portent l'information.",
 "questions": ["Que savez-vous de vos clients d'il y a trois ans qui ne sont pas revenus&nbsp;?",
               "Combien de visiteurs entrent en boutique sans qu'un conseiller les aborde&nbsp;?",
               "Votre première marche de prix a-t-elle bougé, et qu'a-t-elle déplacé&nbsp;?"],
 "sources": [("Bain & Company — marché mondial du luxe", "stabilisation en valeur, contraction de la clientèle", "https://www.journalduluxe.fr/fr/business/luxe-bain-stabilisation-marche-mondial-2026"),
             ("Bain — transformation de la clientèle", "330 millions de clients actifs contre 400 millions trois ans plus tôt", "https://www.clubpatrimoine.com/contenus/marche-luxe-mondial")],
 "loin": [("Le luxe a perdu vingt millions de clients", "marche-luxe-clients-perdus.html"),
          ("Ce que les gens disent, ce qu'ils font", "article-declare-observe.html")],
},
{
 "slug": "parcours-territoires.html",
 "auteur": "VB",
 "h1": "Ceux qui décideront de<br>l'acceptabilité ne viennent<br>pas aux réunions.",
 "h2_ou": 'Qui parle vraiment dans une concertation&nbsp;?',
 "faq": [
  ('Comment toucher ceux qui ne viennent pas aux réunions publiques ?', "En allant les chercher là où ils sont&nbsp;: sur leur lieu de travail, à domicile, ou à distance en horaires décalés. C'est un choix de dispositif et de budget, pas une intention — et c'est lui qui rend une concertation opposable."),
  ('Une concertation réussie se mesure-t-elle au nombre de participants ?', "Non, à la présence de ceux qui ne viennent jamais. Une réunion publique recueille l'avis des riverains concernés, des militants organisés et des personnes disponibles en soirée&nbsp;: trois avis légitimes qui ne composent pas un territoire."),
  ('Faut-il interroger les opposants à un projet ?', "Impérativement, et en amont. Une opposition qui n'a pas été entendue avant l'arbitrage réapparaît après, avec plus de force et moins de marge de manœuvre. C'est la question à poser sur le dernier projet contesté&nbsp;: l'opposition était-elle représentée en amont&nbsp;?"),
  ("Quelle différence entre concertation et étude d'opinion ?", "L'étude d'opinion mesure un état à un instant&nbsp;; la concertation construit une décision avec ceux qu'elle concerne. La seconde suppose que quelque chose puisse encore changer — sinon c'est de l'information, et il vaut mieux l'appeler ainsi."),
 ],
 "secteur": "un territoire", "cat": "Parcours · Territoires & RSE",
 "illus": "stylos.webp", "page_secteur": "secteur-territoires.html",
 "titre_court": "concertation territoriale", "read": "8 min",
 "chapo": "Une concertation réussie ne se mesure pas au nombre de participants mais à la présence de ceux qui ne viennent jamais. Ce sont eux qui décideront de l'acceptabilité du projet.",
 "chiffres": None,
 "etapes": [("Annonce", "du projet"), ("Information", "réunion publique"),
            ("Expression", "ceux qui viennent"), ("Arbitrage", "la collectivité"),
            ("Acceptation", "ou contestation")],
 "plein": 2,
 "ou": "Chez ceux qui ne se déplacent pas. Une réunion publique recueille l'avis des disponibles et des mobilisés — deux populations qui ne représentent pas le territoire.",
 "sous_estime": ("L'absent structurel", """<p>Les réunions publiques attirent trois profils&nbsp;: les riverains directement concernés, les militants organisés, et les retraités disponibles en soirée. Ce sont des avis légitimes, et ils ne composent pas le territoire.</p>
<p>Les actifs avec enfants, les travailleurs en horaires décalés et les publics éloignés des institutions n'y sont pas — et ce sont souvent eux qui subiront ou porteront le projet au quotidien. Aller les chercher là où ils sont est un choix de dispositif, pas une intention.</p>"""),
 "dispositif": "Groupes en salle pour la dynamique collective, complétés d'entretiens individuels sur les publics qui ne se déplacent pas — sur leur lieu de travail, à domicile, ou à distance en horaires décalés. La composition de l'échantillon est ici le cœur du dispositif : c'est elle qui rend la concertation opposable.",
 "questions": ["Qui n'est jamais venu à vos réunions publiques, et le savez-vous&nbsp;?",
               "Vos contributions écrites viennent-elles des mêmes personnes que la salle&nbsp;?",
               "Sur le dernier projet contesté, l'opposition était-elle représentée en amont&nbsp;?"],
 "sources": [("ESOMAR", "cadre déontologique international, applicable aux études d'opinion", "https://esomar.org/"),
             ("Syntec Conseil", "engagements professionnels sur la conduite des études, mai 2025", "https://syntec-conseil.fr/")],
 "loin": [("Entretiens individuels ou focus groups", "article-entretiens-ou-groupes.html"),
          ("Huit biais qui faussent une étude", "article-biais-etude.html")],
},
]


def _parcours(d):
    """Le gabarit : cinq moments, un chiffre daté, le moment sous-estimé, le
    dispositif, trois questions aux données existantes. Seul le contenu change."""
    titre_ss, corps_ss = d["sous_estime"]
    blocs = []
    if d["chiffres"]:
        blocs.append(stats(d["chiffres"]))
    blocs.append(fig_chaine(
        f"Les cinq moments du parcours — {d['titre_court']}",
        f"Le maillon plein est celui où la décision se prend réellement. C'est rarement celui où l'on met le plus de moyens.",
        d["etapes"], pleines=d["plein"]))
    questions = "".join(f"<li>{q}</li>" for q in d["questions"])
    body = f"""
<h2>{d['h2_ou']}</h2>
<p><strong>{d['ou']}</strong></p>
{''.join(blocs)}

<h2>Le moment que tout le monde sous-estime&nbsp;: {titre_ss.lower()}</h2>
{corps_ss}

<h2>Ce qu'il faut aller observer, et comment</h2>
<p>{d['dispositif']}</p>
<p class="art-more">Le détail des dispositifs et de leur calendrier&nbsp;: <a href="decision-rapide.html#configurateur">composez le vôtre en deux minutes</a>.</p>

<h2>Trois questions à poser à vos données existantes</h2>
<p>Avant d'engager du terrain, ces trois questions disent ce que vous savez déjà et où commence l'angle mort. Si vous n'avez de réponse à aucune, vous savez où commence le terrain.</p>
<ol>{questions}</ol>
<p>Un CRM sait ce qui s'est passé. Il ne sait jamais ce qui a failli se passer autrement — et c'est précisément ce qui décide.</p>
"""
    return {
        "slug": d["slug"], "cat": d["cat"], "date": "2026-08-26", "read": d["read"],
        "illus": d["illus"],
        "title": f"Parcours {d['titre_court']} : où se joue la décision",
        # Un h1 propre à chaque secteur, pas une formule déclinée six fois :
        # six titres identiques ne donnent envie de lire aucun des six.
        "h1": d["h1"],
        "desc": f"Les cinq moments du parcours {d['titre_court']}, celui que tout le monde sous-estime, et ce qu'il faut aller observer pour le comprendre.",
        "kw": f"parcours client {d['titre_court']}, étude qualitative {d['titre_court']}, décision achat {d['titre_court']}",
        "chapo": d["chapo"], "body": body, "sources": d["sources"],
        "auteur": d.get("auteur"),
        "faq_titre": "Questions fréquentes",
        # Les questions sont propres au secteur : six pages qui répondent aux
        # mêmes quatre questions se disputeraient la même intention.
        "faq": d["faq"],
        "aide": {"titre": f"Cartographier votre parcours sur {d['secteur']}",
                 "chapo": "Nous travaillons ce secteur depuis des années, auprès des acheteurs comme des prescripteurs. Le parcours se reconstitue en écoutant, pas en modélisant.",
                 "points": ["Recrutement sur comportement réel, y compris chez ceux qui ont renoncé",
                            "Terrain là où se prend la décision — domicile, rayon, boutique, chantier",
                            "Analyse qui distingue le moment déclaré du moment observé",
                            "Restitution en atelier, jusqu'à l'arbitrage sur les points de contact à revoir"]},
        "loin": d["loin"] + [("Notre secteur dédié", d["page_secteur"])],
    }


ARTICLES += [_parcours(d) for d in SECTEURS_PARCOURS]

# ═══════════════════════════════════════════════════════════════════════
#  PAGE PILIER
#  Pas pour gagner « étude qualitative définition » — c'est le piège 01 de
#  la veille, la SERP est tenue par les sites pédagogiques. Pour donner au
#  cluster un point d'ancrage qui redistribue vers les vingt articles, et
#  un objet unique que les moteurs génératifs peuvent citer.
#  Sans millésime dans le titre : une date de mise à jour, pas une date de
#  péremption.
# ═══════════════════════════════════════════════════════════════════════

ARTICLES += [
{
 "slug": "etude-qualitative.html",
 "auteur": "VB",
 "cat": "Guide",
 "date": "2026-08-26",
 "read": "14 min",
 "illus": "demontage.webp",
 "title": "L'étude qualitative, du cadrage à la décision",
 "h1": 'Le chiffre dit combien.<br>Il ne dit jamais<br>pourquoi.',
 "desc": "À quoi elle sert, quand elle ne sert à rien, les six dispositifs et lequel choisir, combien de temps, combien ça coûte, et ce que vous recevez.",
 "kw": "étude qualitative, méthode qualitative, focus group entretien, institut études qualitatives",
 "sources": [
  ("Square Cocoon — Prix d'un focus group", "3 000 à 10 000 € par groupe de 6 à 10 participants, 2026", "https://www.squarecocoon.fr/prix-d-un-focus-group/"),
  ("IntoTheMinds — Combien coûte une étude de marché", "environ 600 € l'entretien en B2C, 750 € en B2B", "https://www.intotheminds.com/blog/combien-coute-une-etude-de-marche/"),
  ("Syntec Conseil", "sept engagements pour un usage responsable de l'IA dans les études, mai 2025", "https://syntec-conseil.fr/"),
  ("ESOMAR", "cadre déontologique international des études de marché et de l'opinion", "https://esomar.org/"),
 ],
 "chapo": "Ce guide rassemble ce qu'on nous demande le plus souvent, avec les chiffres publics quand ils existent. Il commence par la question qu'on pose rarement : dans quels cas une étude qualitative ne sert à rien.",
 "body": """
<h2>À quoi sert une étude qualitative&nbsp;?</h2>
<p><strong>À comprendre pourquoi les gens font ce qu'ils font, quand la question n'est pas encore assez claire pour être posée en questionnaire.</strong> Elle repose sur un petit nombre d'entretiens ou de groupes conduits en profondeur, dont on analyse le contenu — les mots employés, les hésitations, les contradictions — plutôt que des scores.</p>
<p>Le quantitatif dit combien. Le qualitatif dit pourquoi, et surtout&nbsp;: <em>ce à quoi vous n'aviez pas pensé</em>. C'est sa vraie valeur, et c'est ce qui explique qu'un échantillon de douze personnes puisse orienter une décision à plusieurs millions.</p>

<h3>Et quand elle ne sert à rien</h3>
<p>Trois cas, que nous disons au cadrage plutôt qu'en fin de mission&nbsp;:</p>
<ul>
  <li><strong>Quand la décision est déjà prise.</strong> Une étude commandée pour confirmer produira une confirmation — c'est le premier biais du commanditaire, et il fausse tout ce qui suit.</li>
  <li><strong>Quand il faut mesurer une proportion.</strong> «&nbsp;Combien de nos clients sont concernés&nbsp;?&nbsp;» est une question quantitative. Y répondre en qualitatif donne un chiffre faux avec de belles citations.</li>
  <li><strong>Quand personne n'écoutera la réponse.</strong> Si les décideurs n'assistent ni au terrain ni à la restitution, l'étude sera reformulée par un tiers avant de leur parvenir, et elle perdra en route ce qui la rendait utile.</li>
</ul>
<p class="art-more">Le détail des biais, y compris ceux qui viennent du commanditaire&nbsp;: <a href="article-biais-etude.html">huit biais qui faussent une étude</a>.</p>

<h2>Les six dispositifs, et lequel pour quelle question</h2>
<p><strong>Le choix se fait sur la question, jamais sur le catalogue.</strong> La ligne de partage la plus utile&nbsp;: le groupe révèle les normes d'un milieu, l'entretien révèle les écarts individuels.</p>
<div class="tw">
<table>
<thead><tr><th>Dispositif</th><th>Ce qu'il donne</th><th>Pour quelle question</th></tr></thead>
<tbody>
<tr><td><strong>Entretien individuel</strong></td><td>Le parcours réel, les hésitations, ce qui a failli se passer autrement</td><td>Prix, parcours d'achat, sujet sensible, décision B2B</td></tr>
<tr><td><strong>Focus group</strong></td><td>La norme d'un milieu, le vocabulaire spontané, la confrontation</td><td>Concept, packaging, discours de marque, positionnement</td></tr>
<tr><td><strong>Clinique produit</strong></td><td>L'écart entre ce qu'on déclare préférer et ce vers quoi on va</td><td>Design, ergonomie, arbitrage entre directions</td></tr>
<tr><td><strong>Observation</strong></td><td>Ce que les gens font quand on ne leur demande rien</td><td>Parcours en magasin, usage à domicile, poste de travail</td></tr>
<tr><td><strong>Rayon simulé</strong></td><td>Ce qui est vu avant d'être lu</td><td>Packaging, planogramme, visibilité en linéaire</td></tr>
<tr><td><strong>Journal d'usage</strong></td><td>L'usage dans la durée, pas la première rencontre</td><td>Adoption, routine, abandon après quelques semaines</td></tr>
</tbody>
</table>
</div>
<p class="art-more">L'arbitrage détaillé entre les deux dispositifs les plus fréquents&nbsp;: <a href="article-entretiens-ou-groupes.html">entretiens individuels ou focus groups</a>. Et pour le test produit&nbsp;: <a href="article-car-clinic.html">qu'est-ce qu'une car clinic</a>.</p>

<h2>Combien de personnes&nbsp;?</h2>
<p><strong>Douze à dix-huit entretiens sur une cible homogène, ou deux groupes de six à huit personnes par segment à comparer.</strong> Le seuil qui compte est la saturation&nbsp;: le moment où un entretien supplémentaire n'apporte plus rien de neuf. Il arrive plus tard dès qu'on croise deux profils ou deux marchés.</p>
<p>Une règle qui ne se négocie pas&nbsp;: <strong>jamais un seul groupe par segment</strong>. Avec un groupe unique, vous ne pouvez pas distinguer ce qui tient au public de ce qui tient à la dynamique de cette salle-là.</p>

<h2>Combien de temps&nbsp;?</h2>
<p><strong>Quatre à sept semaines pour un dispositif resserré, huit à douze pour une étude complète multi-cibles.</strong></p>
""" + fig_chaine(
  "Le calendrier d'une étude qualitative, phase par phase",
  "Le recrutement est le poste le plus long et le seul qui se raccourcisse vraiment — si vous fournissez votre fichier client. Le cadrage, lui, ne se comprime jamais : c'est lui qui détermine la valeur de tout le reste.",
  [("Cadrage", "1 semaine"), ("Recrutement", "1 à 3 semaines"),
   ("Terrain", "1 à 2 semaines"), ("Analyse", "1 à 2 semaines"),
   ("Restitution", "1 semaine")],
  pleines=1) + """
<p class="art-more">Ce qui se comprime et ce qui ne se comprime pas&nbsp;: <a href="article-decider-vite.html">décider vite sans décider mal</a>.</p>

<h2>Combien ça coûte&nbsp;?</h2>
<p><strong>Le recrutement domine — 200 à 300&nbsp;€ par participant sur critères — puis la modalité de terrain, puis le périmètre des livrables.</strong> Les repères publics du marché français situent un focus group entre 3 000 et 10 000&nbsp;€ tout compris, et un entretien individuel autour de 600&nbsp;€ en B2C, 750&nbsp;€ en B2B.</p>
<p>Le levier le plus efficace pour faire baisser un budget&nbsp;: fournir votre propre fichier client. Il supprime le sourcing, raccourcit le calendrier d'une à deux semaines, et améliore la justesse du profil au passage.</p>
<p class="art-more">La structure de coût poste par poste&nbsp;: <a href="article-prix-etude-qualitative.html">combien coûte une étude qualitative</a>.</p>

<h2>Ce que vous recevez</h2>
<p><strong>Au minimum les transcripts intégraux horodatés — ils vous appartiennent, sans exception.</strong> Le reste se choisit&nbsp;:</p>
<ul>
  <li><strong>Un corpus interrogeable</strong>, pour que vos équipes y reviennent sur leurs propres angles.</li>
  <li><strong>Des top lines</strong> de cinq à huit pages, orientées décision.</li>
  <li><strong>Une analyse complète</strong>, structurée et argumentée, avec ses verbatims à l'appui.</li>
  <li><strong>Des typologies</strong> réutilisables en ciblage comme en conception.</li>
  <li><strong>Un atelier de décision animé</strong>, où l'on travaille les constats jusqu'à un arbitrage écrit.</li>
</ul>
<p>C'est le principe de notre offre <a href="decision-rapide.html">Décision rapide</a>&nbsp;: un socle qui ne bouge jamais — cadrage, recrutement, terrain, transcripts — et des livrables à la carte.</p>

<h2>Ce qui a changé en dix ans, et ce qui n'a pas bougé</h2>
<p><strong>Ce qui a changé&nbsp;:</strong> la transcription ne coûte plus rien, la structuration d'un corpus prend des minutes, et un premier balayage thématique sur trente entretiens se fait pendant qu'on prend un café. Ces gains sont réels et nous les prenons — ils libèrent du temps d'analyse.</p>
<p><strong>Ce qui n'a pas bougé&nbsp;:</strong> trouver les bonnes personnes coûte toujours 200 à 300&nbsp;€ pièce, un entretien dure toujours une heure, et arbitrer entre deux lectures d'un même passage reste un jugement. La profession française a d'ailleurs posé un cadre en 2025&nbsp;: supervision humaine à chaque étape et transparence sur les outils employés.</p>
<p>Il y a une chose qu'on entend moins qu'il y a dix ans, et c'est peut-être le vrai changement&nbsp;: personne ne demande plus si le qualitatif «&nbsp;est représentatif&nbsp;». La question est enfin comprise pour ce qu'elle est — un malentendu de catégorie. Une étude qualitative ne mesure pas, elle explique.</p>
<p class="art-more">Notre position complète sur l'automatisation&nbsp;: <a href="article-ia-etudes-qualitatives.html">IA et études qualitatives</a>, et <a href="article-repondants-synthetiques.html">peut-on remplacer les répondants par de l'IA</a>.</p>

<h2>Par où commencer</h2>
<p>Si vous n'avez encore rien écrit&nbsp;: <a href="article-brief-etude-qualitative.html">les huit rubriques d'un brief</a>, dont celle que tout le monde oublie — les hypothèses concurrentes à départager.</p>
<p>Si vous voulez une idée du dispositif et du calendrier avant de nous parler&nbsp;: le <a href="decision-rapide.html#configurateur">configurateur</a> vous les donne en deux minutes.</p>
""",
 "faq_titre": "Les questions qu'on nous pose le plus",
 "faq": [
  ("Une étude qualitative est-elle représentative ?",
   "Non, et elle ne cherche pas à l'être — c'est un malentendu de catégorie. Elle n'estime aucune proportion&nbsp;: elle identifie des mécanismes, des motivations et des freins. Pour savoir <em>combien</em>, il faut un questionnaire&nbsp;; pour savoir <em>quoi mettre dans le questionnaire</em>, il faut du qualitatif."),
  ("Peut-on faire du qualitatif et du quantitatif sur le même projet ?",
   "Oui, et l'ordre compte. Le qualitatif d'abord pour découvrir les hypothèses et le vocabulaire, le quantitatif ensuite pour les mesurer. L'inverse — du qualitatif pour «&nbsp;expliquer&nbsp;» des résultats quantitatifs — fonctionne aussi, mais il enferme dans les catégories déjà posées."),
  ("Quelle est la différence entre un institut et un freelance ?",
   "Le terrain organisé. Un freelance senior conduit d'excellents entretiens&nbsp;; ce qu'il n'a pas, c'est le recrutement sur critères vérifiés, la logistique multi-villes, la continuité sur plusieurs années et l'assurance d'un dispositif qui tient si quelqu'un tombe malade."),
  ("Peut-on assister au terrain ?",
   "Oui, et c'est recommandé — derrière une glace sans tain ou en retour vidéo, jamais dans la salle. Assister change la façon dont on écoute la restitution&nbsp;: on filtre beaucoup moins ce qui dérange quand on a entendu les gens soi-même."),
  ("Combien de temps garde-t-on les enregistrements ?",
   "Une durée définie au cadrage et respectée, distincte pour l'enregistrement brut et pour le corpus anonymisé. Ce sont des données personnelles, avec tout ce que ça implique&nbsp;: base légale, information, consentement."),
  ("Comment comparer deux marchés dans une même étude ?",
   "Par l'équivalence, pas par la traduction&nbsp;: mêmes guides, échantillons comparables, et une analyse qui sépare explicitement l'usage universel des habitudes locales. C'est cette distinction dont dépendent les arbitrages produit — le détail figure dans notre article <a href=\"marche-citadines-france-uk.html\">sur les citadines France et Royaume-Uni</a>."),
 ],
 "aide": {"titre": "Une question à éclairer ?",
  "chapo": "Nous conduisons des études qualitatives depuis quarante ans, du cadrage à l'atelier de décision. Le premier échange sert à savoir si une étude est la bonne réponse — parfois, elle ne l'est pas.",
  "points": ["Une heure de cadrage pour traduire votre décision en question de terrain",
             "Un ordre de grandeur budgétaire donné dès ce premier échange",
             "Un chiffrage sous 48 heures, ligne par ligne, pour que vous puissiez arbitrer",
             "Et un « passez votre tour » assumé si la question ne justifie pas l'étude"]},
 "loin": [("Composer votre dispositif en deux minutes", "decision-rapide.html#configurateur"),
          ("Comment rédiger un brief d'étude qualitative", "article-brief-etude-qualitative.html"),
          ("Tous nos contenus", "contenus.html")],
},
]

# ═══════════════════════════════════════════════════════════════════════
#  VERSION ANGLAISE
#  Sur des URL distinctes, sous en/, avec des alternates hreflang dans les
#  deux sens. Servir deux langues sur une même URL annulerait le travail
#  SEO : un moteur a besoin d'une URL par langue, et un moteur génératif
#  qui cite une page a besoin qu'elle soit dans UNE langue.
#
#  Le périmètre est délibérément restreint. Tout le terrain gagnable en
#  référencement est francophone (« focus group Lyon », « prix étude
#  qualitative ») : traduire les vingt-sept pages produirait un miroir que
#  personne ne cherche. On traduit ce qu'un prospect international lit
#  vraiment — ce que fait le cabinet, et les articles d'observatoire, qui
#  sont les seuls à voyager par nature.
# ═══════════════════════════════════════════════════════════════════════

NAV_EN = """<header class="nav">
  <div class="container nav-inner">
    <a href="../index.html" class="nav-logo"><img src="../assets/logo/logo-noir.png" alt="ACMÉ" /></a>
    <nav class="nav-menu">
      <div class="nav-dd">
      <a href="../index.html#sectors" class="nav-dd-trigger"><span>Sectors</span><span class="nav-dd-caret" aria-hidden="true">&#9662;</span></a>
      <div class="nav-dd-menu">
        <a href="../secteur-mobilite.html">Mobility &amp; Automotive</a>
        <a href="../secteur-retail-fmcg.html">Retail and FMCG</a>
        <a href="../secteur-sante-cosmetiques.html">Health &amp; Cosmetics</a>
        <a href="../secteur-batiment.html">Construction</a>
        <a href="../secteur-territoires.html">Regions, Tourism &amp; CSR</a>
        <a href="../secteur-mode-luxe.html">Fashion &amp; Luxury</a>
      </div>
    </div>
      <a href="../decision-rapide.html">Quick Decision</a>
      <a href="index.html"{cur}>Insights</a>
      <a href="../etudes-et-ia.html">Studies &amp; AI</a>
      <a href="../qui-sommes-nous.html">About us</a>
    </nav>
    <div class="nav-right">
      <div class="lang-toggle" role="group" aria-label="Language">
        <a href="{fr}" class="lang-link">FR</a>
        <span class="lang-sep">/</span>
        <button data-lang="en" type="button" class="active">EN</button>
      </div>
      <a href="../contact.html" class="btn btn-primary-dark" style="padding: 12px 20px;">
        <span>Start a project</span>
        <svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none"><path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg>
      </a>
      <button class="nav-burger" aria-label="Menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>"""

FOOTER_EN = """<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <div style="font-family: var(--font-display); font-weight: 700; letter-spacing: 0.22em; font-size: 18px; margin-bottom: 20px;">ACMÉ</div>
        <p>Four decades of qualitative research. Head office: 24 rue Turbil, 69003 Lyon, France.</p>
      </div>
      <div>
        <h4>Sectors</h4>
        <ul>
          <li><a href="../secteur-mobilite.html">Mobility &amp; Automotive</a></li>
          <li><a href="../secteur-retail-fmcg.html">Retail and FMCG</a></li>
          <li><a href="../secteur-sante-cosmetiques.html">Health &amp; Cosmetics</a></li>
          <li><a href="../secteur-batiment.html">Construction</a></li>
          <li><a href="../secteur-territoires.html">Regions, Tourism &amp; CSR</a></li>
          <li><a href="../secteur-mode-luxe.html">Fashion &amp; Luxury</a></li>
        </ul>
      </div>
      <div>
        <h4>Insights</h4>
        <ul>
          <li><a href="index.html">In English</a></li>
          <li><a href="../contenus.html">Tous les contenus (FR)</a></li>
          <li><a href="../livre-blanc.html">Livre blanc (FR)</a></li>
          <li><a href="../faq.html">FAQ (FR)</a></li>
        </ul>
      </div>
      <div>
        <h4>Contact</h4>
        <ul>
          <li><a href="mailto:contact@acme-consultant.fr">contact@acme-consultant.fr</a></li>
          <li><a href="../contact.html">Contact form</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-esomar">
      <span>Corporate member</span>
      <img src="../assets/logos/esomar.png" alt="ESOMAR" loading="lazy">
    </div>
    <div class="footer-legal">
      <div>&copy; <span data-year></span> ACM&Eacute; Consultants &middot; All rights reserved</div>
      <div>Lyon &middot; Paris &middot; Munich &middot; Milan</div>
    </div>
  </div>
</footer>"""


def page_en(slug, title, desc, body, fr_slug, extra_jsonld=None, current="",
            og_image="assets/illus/courbes.webp", og_type="website"):
    """Gabarit anglais. Les chemins remontent d'un cran (les pages vivent sous
    en/) et les alternates hreflang pointent dans les deux sens."""
    blocs = [dict(org_jsonld(), inLanguage="en")]
    if extra_jsonld:
        blocs.append(extra_jsonld)
    ld = "\n".join(
        '<script type="application/ld+json">%s</script>' %
        json.dumps(b, ensure_ascii=False, separators=(",", ":")) for b in blocs)
    nav = NAV_EN.format(cur=' class="current"' if current == "ct" else "", fr="../" + fr_slug)

    head = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="UTF-8" />\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
        '<meta name="robots" content="noindex, nofollow, noarchive, nosnippet" />\n'
        f'<title>{title}</title>\n'
        f'<meta name="description" content="{html.escape(desc, quote=True)}" />\n'
        f'<link rel="canonical" href="{SITE}/en/{slug}" />\n'
        '<!-- Une URL par langue, et les deux se declarent l\'une l\'autre. Sans\n'
        '     cela, les deux versions se font concurrence au lieu de se completer. -->\n'
        f'<link rel="alternate" hreflang="fr" href="{SITE}/{fr_slug}" />\n'
        f'<link rel="alternate" hreflang="en" href="{SITE}/en/{slug}" />\n'
        f'<link rel="alternate" hreflang="x-default" href="{SITE}/{fr_slug}" />\n'
        f'<meta property="og:type" content="{og_type}" />\n'
        '<meta property="og:site_name" content="ACMÉ Consultants" />\n'
        '<meta property="og:locale" content="en_GB" />\n'
        '<meta property="og:locale:alternate" content="fr_FR" />\n'
        f'<meta property="og:title" content="{html.escape(title, quote=True)}" />\n'
        f'<meta property="og:description" content="{html.escape(desc, quote=True)}" />\n'
        f'<meta property="og:url" content="{SITE}/en/{slug}" />\n'
        f'<meta property="og:image" content="{SITE}/{og_image}" />\n'
        '<meta name="twitter:card" content="summary_large_image" />\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">\n'
        '<link rel="stylesheet" href="../styles.css" />\n'
        '<link rel="stylesheet" href="../styles-v3.css" />\n'
        '<link rel="stylesheet" href="../styles-contenus.css" />\n'
        + ld + '\n</head>\n<body class="v3 v3-1">\n\n')

    tail = (
        '\n\n<script src="../main.js"></script>\n<script>\n'
        "/* La page est servie en anglais : on aligne la preference stockee pour que\n"
        "   la bascule du reste du site suive. Ces pages ne portent aucun data-i18n,\n"
        "   donc i18n.js ne repasse pas sur ce texte. */\n"
        "try { localStorage.setItem('acme-lang', 'en'); } catch (e) {}\n"
        "document.querySelectorAll('[data-year]').forEach(function (el) {\n"
        "  el.textContent = new Date().getFullYear();\n"
        "});\n</script>\n</body>\n</html>\n")

    return head + nav + '\n\n' + body + '\n\n' + FOOTER_EN + tail


def render_article_en(a):
    """Meme anatomie que la version francaise : bandeau, corps, FAQ, bloc
    d'activation, sources, maillage."""
    byline = ""
    if a.get("auteur"):
        au = AUTEURS[a["auteur"]]
        byline = ('<div class="art-by"><span class="art-by-i" aria-hidden="true">%s</span>'
                  '<span class="art-by-t">By <a href="../qui-sommes-nous.html">'
                  '<strong>%s</strong></a><span class="art-by-r">%s</span></span></div>'
                  % (a["auteur"], au["nom"], au["role_en"]))
    illus = ""
    if a.get("illus"):
        illus = ('<div class="art-illus"><img src="../assets/illus/%s" alt="" '
                 'width="1600" height="600" loading="lazy" decoding="async"></div>' % a["illus"])
    faq = ""
    if a.get("faq"):
        items = "".join(
            '<details class="faq-i"><summary><h3>%s</h3></summary>'
            '<div class="faq-a"><p>%s</p></div></details>' % (q, r) for q, r in a["faq"])
        faq = ('<section class="art-faq"><h2>%s</h2>%s</section>'
               % (a.get("faq_titre", "Frequently asked questions"), items))
    src = ""
    if a.get("sources"):
        items = "".join(
            '<li><a href="%s" rel="nofollow noopener" target="_blank">%s</a> — %s</li>'
            % (u, n, q) for n, q, u in a["sources"])
        src = ('<aside class="art-sources"><h2>Sources</h2><ul>' + items + '</ul>'
               '<p class="art-sources-note">Figures gathered in August 2026. Market data '
               'moves — check the date of a source before using it as a reference.</p></aside>')
    loin = ""
    if a.get("loin"):
        liens = "".join(
            '<a href="%s"><span>%s</span>'
            '<svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none">'
            '<path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg></a>'
            % (u, t) for t, u in a["loin"])
        loin = ('<section class="art-loin"><h2>Further reading</h2>'
                '<div class="art-loin-g">%s</div></section>' % liens)
    act = ""
    if a.get("aide"):
        puces = "".join("<li>%s</li>" % x for x in a["aide"]["points"])
        act = (
            '<section class="art-help">\n  <div class="art-help-in">\n'
            '    <div class="eyebrow">&mdash; How ACM&Eacute; can help</div>\n'
            '    <h2>%s</h2>\n    <p class="lead">%s</p>\n'
            '    <ul class="art-help-list">%s</ul>\n'
            '    <div class="ctas">\n'
            '      <a href="../decision-rapide.html#configurateur" class="btn btn-primary-light">'
            '<span>Build a study design</span>'
            '<svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none">'
            '<path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg></a>\n'
            '      <a href="../contact.html" class="btn btn-outline-light">Talk to us</a>\n'
            '    </div>\n  </div>\n</section>'
            % (a["aide"]["titre"], a["aide"]["chapo"], puces))

    body = (
        '<article class="art">\n  <header class="art-head">\n'
        '    <div class="container art-w">\n'
        '      <div class="art-kicker"><a href="index.html">All insights</a>'
        '<span>&middot;</span><span>%s</span></div>\n'
        '      <h1 class="display">%s</h1>\n'
        '      <p class="art-chapo">%s</p>\n'
        '      <div class="art-meta"><time datetime="%s">%s</time>'
        '<span>&middot;</span><span>%s read</span></div>\n      %s\n'
        '    </div>\n  </header>\n  %s\n'
        '  <div class="container art-w art-body" lang="en">\n%s\n%s\n%s\n%s\n  </div>\n'
        '</article>\n%s\n'
        '<article class="art">\n  <div class="container art-w">\n'
        '    <div class="art-foot">\n'
        '      <a href="index.html" class="btn btn-outline-dark">All insights</a>\n'
        '      <a href="../contact.html" class="btn btn-primary-dark"><span>Start a project</span>'
        '<svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none">'
        '<path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg></a>\n'
        '    </div>\n  </div>\n</article>'
        % (a["cat"], a["h1"], a["chapo"], a["date"], a["date_en"], a["read"],
           byline, illus, a["body"], faq, src, loin, act))

    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Article",
         "headline": re.sub(r"<[^>]+>", " ", a["h1"]).replace("&nbsp;", " ").strip(),
         "description": a["desc"], "datePublished": a["date"], "dateModified": a["date"],
         "inLanguage": "en", "keywords": a["kw"],
         "author": ({"@type": "Person", "name": AUTEURS[a["auteur"]]["nom"],
                    "jobTitle": AUTEURS[a["auteur"]]["role"],
                    "worksFor": {"@type": "Organization", "name": ORG["name"]}}
                   if a.get("auteur") else {"@type": "Organization", "name": ORG["name"]}),
         "publisher": {"@type": "Organization", "name": ORG["name"]},
         "mainEntityOfPage": {"@type": "WebPage", "@id": "%s/en/%s" % (SITE, a["slug"])}}]}
    if a.get("faq"):
        ld["@graph"].append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer",
                                "text": re.sub(r"<[^>]+>", "", r).replace("&nbsp;", " ")}}
            for q, r in a["faq"]]})

    return page_en(a["slug"], a["title"], a["desc"], body, a["fr"], extra_jsonld=ld,
                   current="ct", og_type="article",
                   og_image=("assets/illus/%s" % a["illus"]) if a.get("illus")
                            else "assets/illus/courbes.webp")

# ── Les articles anglais ────────────────────────────────────────────────
ARTICLES_EN = [
{
 "slug": "city-cars-france-uk.html", "auteur": "VJ", "fr": "marche-citadines-france-uk.html",
 "cat": "Market watch · Mobility", "date": "2026-08-26", "date_en": "26 August 2026",
 "read": "9 min", "illus": "voiture.webp",
 "title": "City cars: France and the UK diverge",
 "h1": "City cars: France<br>and the UK don't look<br>at the same car.",
 "desc": "Two entry-level markets, two opposite mechanics: the sticker price in France, the discount in the UK. What that changes for anyone launching a small car.",
 "kw": "French city car market, UK supermini, B segment Europe, small car buyers",
 "sources": [
  ("French car market, H1 2026", "857,177 registrations in the first half, up 1.8% year on year", "https://www.cartegrise.com/blog/2026/07/marche-automobile-francais-s1-2026-le-grand-bilan-dun-semestre-de-bascule"),
  ("SMMT via Carwow — used car sales Q1 2026", "superminis account for 648,229 transactions, 32.2% of the UK used market", "https://www.carwow.co.uk/news/10706/used-car-sales-q1-2026"),
  ("GEM — average new car price in the UK", "average discounts approaching £6,000 in early 2026", "https://www.motoringassist.com/news/new-car-prices-whats-the-uk-average"),
 ],
 "chapo": "On paper it is the same segment: a small car, four or five seats, a tight budget. In practice the two markets clear in completely different ways — and a promise that lands in Lyon can fall flat in Manchester.",
 "body": """
<h2>Where does the French market stand?</h2>
<p><strong>It is recovering slowly, and the entry level is pulling it.</strong> The first half of 2026 recorded 857,177 registrations, up 1.8% year on year — but still 26.5% below the first half of 2019. The market has not recovered&nbsp;; it has reorganised.</p>
""" + stats([
  ("857,177", "registrations in France, first half of 2026", "Carte Grise, July 2026"),
  ("+6.5%", "growth for city cars in Q1 2026", "Trade press, 2026"),
  ("−26.5%", "in volume against the first half of 2019", "Carte Grise, July 2026"),
]) + """
<p>Within that constrained market, the city car has taken back first place, carried by electric models entering the segment.</p>

<h2>What really structures the French choice: the sticker price</h2>
<p><strong>The €20,000 threshold has become the real dividing line of the market.</strong> Entry prices cluster just below a round number, and that is no accident.</p>
<p>What we hear in interviews, year after year, is that this threshold does not work as a calculation but as a <em>moral boundary</em>. Above it, the purchase changes nature: it becomes a decision you have to justify — to a partner, and to yourself. Below it, it stays a reasonable purchase.</p>
""" + fig_barres(
  "Entry prices of the main French city cars, 2026",
  "Entry prices cluster just under the €20,000 threshold, which structures the most dynamic category of the French market. Manufacturer entry prices, 2026.",
  [("Dacia Sandero Stepway", 17900, "≈ €17,900"),
   ("Citroën C3", 18900, "≈ €18,900"),
   ("Peugeot 208", 19500, "≈ €19,500"),
   ("Psychological threshold", 20000, "€20,000")]) + """

<h2>And in the United Kingdom?</h2>
<p><strong>The market is roughly twice the size, and it clears through discounting rather than through the sticker price.</strong> The SMMT expects 2.048 million units in 2026, up 1.4%. But the figure that changes everything sits elsewhere: average discounts on a new car approached £6,000 in early 2026, across all fuel types.</p>
""" + stats([
  ("2.048 M", "units expected in the UK in 2026", "SMMT forecast"),
  ("≈ £6,000", "average discount on a new car", "GEM, early 2026"),
  ("32.2%", "of the UK used market held by superminis", "SMMT via Carwow, Q1 2026"),
]) + """
<p>The direct consequence: in the UK, <strong>the advertised price is not the price</strong>. It is an opening position, and the buyer knows it. Work on the list price therefore produces far less effect than in France, where the sticker <em>is</em> the promise.</p>
<p>A second, more structural gap: the British supermini lives largely on the used market. It accounts for 648,229 transactions in the first quarter of 2026 — 32.2% of used sales, by far the most bought category.</p>

<h2>Two opposite mechanics, side by side</h2>
""" + fig_matrice(
  "France and the UK: two ways of making an entry-level car affordable",
  "The same segment, two opposite mechanics. The consequence bears less on the product than on how you talk about it.",
  "How affordability is built", "What the buyer looks at",
  [(0, 0, "France — the sticker price", "The €20,000 threshold draws the line. The advertised price is the promise, and discounting stays marginal in the discourse."),
   (1, 0, "United Kingdom — the discount", "The list price is an opening position. Around £6,000 of average discount: the buyer negotiates and knows it."),
   (0, 1, "France — electrified new", "The entry level is renewing itself through electric city cars, which now enter the top of the rankings."),
   (1, 1, "United Kingdom — recent used", "The supermini plays out first on the used market: 32.2% of Q1 2026 transactions.")]) + """

<h2>What this changes for anyone launching a small car</h2>
<ul>
  <li><strong>The same price argument cannot be tested the same way.</strong> In France you test the sticker price, because that is what triggers or blocks. In the UK you test the <em>price expected after negotiation</em> — otherwise you are measuring a reaction to a number nobody believes.</li>
  <li><strong>The comparison set is not the same.</strong> A French buyer compares new cars with each other. A British buyer regularly weighs a discounted new car against a well-equipped recent used one. A concept test that leaves used cars out of the competitive set misses the real trade-off.</li>
  <li><strong>Electrification is not told the same story.</strong> In France it enters through the top of the city-car rankings and benefits from a narrative of renewal. In the UK, total cost of ownership and residual value come into the conversation far earlier.</li>
</ul>

<h2>What the figures do not say</h2>
<p>This data describes a market&nbsp;; it explains no decision. A registration table tells you neither why someone gave up the model they preferred, nor what happens in the garage when a couple weighs two trim levels, nor what the neighbours make of a car parked outside the house.</p>
<p>That is exactly the gap qualitative research exists to close — and on a multi-market launch, it is the most expensive gap to ignore, because it only becomes visible afterwards.</p>
""",
 "faq_titre": "Frequently asked questions",
 "faq": [
  ("Why does the €20,000 threshold matter so much in France?",
   "Because it works as a boundary rather than a calculation. Below it, the purchase stays reasonable&nbsp;; above it, it becomes a decision you have to justify. That is what we hear in interviews, and it explains why entry prices cluster just underneath."),
  ("Is the British market comparable to the French one?",
   "In volume it is about twice the size — 2.048 million units expected in 2026. In mechanics it differs deeply: average discounts approach £6,000, which makes the advertised price an opening position rather than a promise."),
  ("Should each market be studied separately?",
   "A shared discussion guide, yes&nbsp;; shared fieldwork, no. The two markets share the category but not the comparison sets. A matched design — same guide, equivalent samples — is what lets you separate universal usage from local habit."),
  ("Are these figures enough to arbitrate a launch?",
   "No. They frame a market&nbsp;; they describe no individual decision. To arbitrate a design, a price or a trim level, you have to put real buyers in front of the object and its alternatives — which is what a product clinic is for."),
 ],
 "aide": {"titre": "Testing a small car across two markets",
  "chapo": "We have run matched France–UK and France–Italy fieldwork for years, on the most contested segment of the European market.",
  "points": ["Recruitment on the vehicle actually owned, market by market",
             "Shared guide and equivalent samples, so the comparison holds",
             "Static or dynamic product clinic, with real competitors present",
             "Analysis that separates universal usage from local habit — the distinction your product decisions rest on"]},
 "loin": [("Luxury has lost twenty million customers", "luxury-lost-customers.html"),
          ("All insights", "index.html")],
},

{
 "slug": "luxury-lost-customers.html", "auteur": "CC", "fr": "marche-luxe-clients-perdus.html",
 "cat": "Market watch · Fashion & Luxury", "date": "2026-08-26", "date_en": "26 August 2026",
 "read": "8 min", "illus": "fuite.webp",
 "title": "Luxury has lost twenty million customers",
 "h1": "Luxury has lost<br>twenty million<br>customers.",
 "desc": "The world's luxury customer base fell from 400 to 330 million in three years. What qualitative work says about those who left — and those who stayed.",
 "kw": "luxury market 2026, luxury customer base, Gen Z luxury, personal luxury goods",
 "sources": [
  ("Bain & Company — global luxury market study", "€1,443bn in worldwide luxury spending in 2025; personal goods at €358bn, expected at €365–373bn in 2026", "https://www.journalduluxe.fr/fr/business/luxe-bain-stabilisation-marche-mondial-2026"),
  ("Bain — the changing customer base", "close to 20 million consumers lost in 2025; 330 million active customers against 400 million three years earlier", "https://www.clubpatrimoine.com/contenus/marche-luxe-mondial"),
  ("BCG", "Millennials and Generation Z account for around 75% of the luxury market", "https://www.bcg.com/press/19july2023-dici-2026-les-millennials-et-la-generation-z-representeront-75-du-marche-du-luxe"),
 ],
 "chapo": "Revenue is stabilising, and that is what everyone reports. The figure that matters sits elsewhere: the number of people who buy luxury has fallen by a quarter in three years. That is not a cyclical problem. It is a recruitment problem.",
 "body": """
<h2>What the 2026 figures say</h2>
<p><strong>The market is stabilising in value and contracting in customers.</strong> Both movements are happening at once, which is what makes the reading tricky.</p>
""" + stats([
  ("330 M", "active luxury customers worldwide, against 400 M three years earlier", "Bain & Company, 2026"),
  ("−20 M", "consumers lost in 2025 alone", "Bain & Company, 2026"),
  ("+2 to 4%", "growth expected on personal luxury goods in 2026", "Bain & Company, 2026"),
  ("≈ 75%", "of the market carried by Millennials and Generation Z", "BCG"),
]) + """
<p>Worldwide luxury spending reached €1,443bn in 2025 and is expected to hold between €1,440bn and €1,470bn in 2026. Personal goods — leather, fashion, jewellery, beauty — are expected between €365bn and €373bn, up 2 to 4% after a 2% decline in 2025.</p>
<p>In other words: <strong>value holds because those who remain are spending more.</strong> That is stabilisation through concentration, not through recruitment.</p>

<h2>Who left, exactly?</h2>
<p><strong>The entry-level customer — the one who bought one piece a year, sometimes less.</strong> That is the most price-sensitive population, and it is also the one that fed the generational renewal of the customer base.</p>
<p>Its disappearance creates a problem revenue does not show. A luxury house does not recruit its top-tier clients directly. It recruits them at the bottom, on a first purchase — often an accessory or a fragrance — and moves them up over ten or twenty years. When the entry step gets too high, you do not merely lose this year's revenue: <strong>you lose the 2040 cohort</strong>.</p>
""" + fig_chaine(
  "How a luxury house recruits a lifelong customer",
  "A house does not recruit its top-tier clients directly: it moves them up. When the first step gets too high, what goes missing is the cohort of fifteen years from now, not this year's revenue.",
  [("First purchase", "accessory, fragrance"), ("Repeat", "one purchase a year"),
   ("Attachment", "the house is a choice"), ("Established", "several categories"),
   ("Lifelong client", "a long relationship")],
  pleines=1) + """

<h2>Three things the figures do not say, and fieldwork does</h2>
<h3>1. Giving up is not experienced as a budget trade-off</h3>
<p>In interviews, people who stopped buying luxury rarely explain it by price alone. They describe a shift in meaning: the sense that the relationship between what is paid and what is received has changed, and that the object no longer «&nbsp;is worth&nbsp;» what it costs. That is a judgement about legitimacy, not about an amount — and it does not get corrected with a promotion.</p>

<h3>2. The boutique has become a filter rather than a welcome</h3>
<p>Entry-level customers regularly describe a specific discomfort: not knowing how to behave, being read as a non-buyer, not daring to ask a price. This discomfort appears in no satisfaction survey, for a mechanical reason — the people who feel it do not fill in questionnaires. They do not come back.</p>

<h3>3. Generation Z does not mechanically replace the departing base</h3>
<p>Millennials and Generation Z already account for around three quarters of the market, but their relationship to the category differs: second-hand is legitimate, new is not an imperative, and attachment to a house builds on other signals. Counting on them to rebuild the lost base means understanding what triggers a first purchase today — and it is not what triggered one fifteen years ago.</p>

<h2>The European turning point</h2>
<p>Europe is the weak point of the market, with international tourist spending down around 20% in February, while the Americas return as the main engine of personal luxury. For a European house, that shifts the question: <strong>the local customer base, long treated as a floor, becomes a conquest again.</strong></p>

<h2>What to go and find on the ground</h2>
<ul>
  <li><strong>What tipped the leavers.</strong> Interviewing them is hard — they are no longer in the files — but they are the most informative population in the market.</li>
  <li><strong>What the first step actually represents.</strong> The entry price is a number&nbsp;; what it means to someone hesitating is another matter.</li>
  <li><strong>What happens in the first eight seconds in the boutique.</strong> That is where the return is decided, and it can only be observed by being there.</li>
  <li><strong>What makes a house desirable to a twenty-five-year-old</strong> who grew up with second-hand and never treated new as the norm.</li>
</ul>
""",
 "faq_titre": "Frequently asked questions",
 "faq": [
  ("Is the luxury market in crisis in 2026?",
   "In value, no: personal luxury goods are expected to grow 2 to 4% after a 2% decline in 2025. In customers, yes: the active base fell from around 400 to 330 million in three years. Value holds because those who remain spend more."),
  ("Why does losing entry-level customers matter so much?",
   "Because a house recruits its lifelong clients from the bottom, on a first purchase, then moves them up over ten or twenty years. Losing the entry step is not losing this year's revenue — it is losing the cohort of fifteen years from now."),
  ("How do you interview customers who have stopped buying?",
   "That is the hard part: they are no longer in the active files. They have to be recruited on past purchase behaviour rather than from a client database, which makes sourcing more expensive — and they are the most informative population in the market."),
  ("What method captures the boutique experience?",
   "Accompanied observation, then a one-to-one interview away from the store. A satisfaction survey does not capture the entry-level customer's discomfort, for a simple reason: the people who feel it do not fill in questionnaires."),
 ],
 "aide": {"titre": "Understanding those who left",
  "chapo": "We work on the codes of desire and on premium customer experience, including with populations that are hard to reach — the ones no longer in your files.",
  "points": ["Recruitment on past purchase behaviour, not only from active client files",
             "Accompanied observation in store, then one-to-one interviews away from it",
             "Interviews on the first step: what the entry price means to someone hesitating",
             "Findings worked through in a facilitated session with your retail and product teams"]},
 "loin": [("City cars: France and the UK diverge", "city-cars-france-uk.html"),
          ("All insights", "index.html")],
},

{
 "slug": "diy-fear-of-getting-it-wrong.html", "auteur": "TN", "fr": "marche-bricolage-peur-de-mal-faire.html",
 "cat": "Market watch · Construction", "date": "2026-08-26", "date_en": "26 August 2026",
 "read": "8 min", "illus": "stylos.webp",
 "title": "Nine in ten French people DIY. Seven are afraid",
 "h1": "Nine in ten French<br>people do DIY. Seven<br>are afraid of getting<br>it wrong.",
 "desc": "The French DIY market is down for a third year, but the main brake is not purchasing power — it is the fear of botching the job. What that changes for retailers and brands.",
 "kw": "French DIY market 2026, home improvement France, DIY consumer behaviour, builders merchants France",
 "sources": [
  ("Points de Vente — the DIY market", "€21.8bn in DIY superstore revenue in 2025, in a market above €39bn", "https://pointsdevente.fr/fil-info/2026-06-15-le-marche-du-bricolage-toujours-en-recul-malgre-le-rebond-de-limmobilier/"),
  ("DIY in France 2026", "nine in ten French people do DIY, seven in ten are held back by the fear of getting it wrong", "https://www.montrealmirror.com/actu10359/bricolage-france-2026-marche-stabilisation-peur-de-mal-faire.html"),
 ],
 "chapo": "Three consecutive years of decline, and one explanation on repeat: purchasing power and the housing market. It is true, and it is not enough. The brake French people cite most is not financial — it is psychological, and it can be treated.",
 "body": """
<h2>Where does the DIY market stand?</h2>
<p><strong>Down for a third consecutive year, with a more reassuring start to 2026.</strong> DIY superstore revenue stood at €21.8bn including tax in 2025, down 1.4% — after −1.4% in 2023 and −4.3% in 2024. The total market, all channels, still exceeds €39bn.</p>
""" + stats([
  ("€21.8bn", "in DIY superstore revenue in 2025", "Points de Vente, 2026"),
  ("3 years", "of consecutive decline in the superstore channel", "−1.4% in 2023, −4.3% in 2024, −1.4% in 2025"),
  ("9 in 10", "French people say they do DIY in 2026", "Sector study, 2026"),
  ("7 in 10", "are held back by the fear of getting it wrong", "Sector study, 2026"),
]) + """
<p>Superstores hold 75% of the market, while e-commerce is moving towards 19% of sector revenue.</p>

<h2>The shift the revenue figure hides</h2>
<p><strong>French people have not stopped doing DIY: they have changed projects.</strong> Falling purchasing power and a slower housing market have moved demand from heavy renovation towards routine maintenance and economical repair.</p>
<p>For a retailer this is not a slowdown — it is a change of trade. You do not sell a bathroom project the way you sell a joint that needs redoing. Basket size falls, frequency can rise, and the advice being asked for is not remotely the same.</p>
""" + fig_matrice(
  "Two DIY markets inside a single revenue figure",
  "The overall decline masks a shift: fewer transformation projects, more maintenance and repair. The two are not sold, advised or stocked the same way.",
  "Type of project", "What the customer expects",
  [(0, 0, "Heavy renovation", "High basket, long decision, several visits. The customer expects project support."),
   (1, 0, "Maintenance and repair", "Low basket, immediate decision, one visit. The customer expects an answer, not a project."),
   (0, 1, "What is declining", "Transformation projects, held back by purchasing power and the housing market."),
   (1, 1, "What is holding", "Small jobs and repairs — but with a far stronger demand for reassurance.")]) + """

<h2>The real brake: the fear of botching it</h2>
<p><strong>Nine in ten French people do DIY, but seven in ten are held back by the fear of getting it wrong.</strong> That is by far the most actionable figure in the sector, and the least exploited.</p>
<p>The brake is not financial, and that is what makes it interesting: it is treated through advice, teaching, guarantee of outcome and product design — not through promotion. A 20% discount does not reduce the fear of drilling in the wrong place.</p>
<p>In interviews, this fear breaks down into three distinct anxieties, which call for different answers:</p>
<ul>
  <li><strong>Fear of causing damage</strong> — to the home, to a surface, to something that cannot be replaced. It blocks before purchase, in store as much as online.</li>
  <li><strong>Fear of buying the wrong thing</strong> — wrong size, wrong compatibility, wrong quantity. It produces abandonment at the shelf, and a large share of returns.</li>
  <li><strong>Fear of being judged</strong> — having to ask, showing that you do not know. It is strong among people who rarely do DIY, and it explains part of the shift to e-commerce, where you can search without being seen.</li>
</ul>
""" + fig_barres(
  "What holds people back, by frequency of mention",
  "The declared hierarchy puts the fear of getting it wrong ahead of budget. It is a brake treated by advice and design, not by promotion. Proportions drawn from 2026 sector studies.",
  [("Fear of getting it wrong", 70, "≈ 7 in 10"),
   ("Budget constraint", 55, "high"),
   ("Lack of time", 40, "medium"),
   ("Lack of tools", 25, "lower")]) + """

<h2>What it means for a retailer or a brand</h2>
<ul>
  <li><strong>Advice becomes the product.</strong> In a market where the dominant brake is fear of failure, value shifts towards whatever reassures: demonstration, situated tutorials, guarantees, take-back if it goes wrong.</li>
  <li><strong>The aisle has to answer before being asked.</strong> Fear of judgement makes the customer silent. If understanding requires asking, part of your traffic will leave without buying — and without ever telling you why.</li>
  <li><strong>E-commerce is not only a price channel.</strong> It is also a channel of discretion: you can browse at length, compare and learn without exposing yourself. That changes what belongs there.</li>
  <li><strong>Trade and consumer customers no longer meet in the same place.</strong> A tradesperson wants a reference&nbsp;; a consumer wants an answer. Serving both with the same advice model disappoints one of the two.</li>
</ul>

<h2>Why quantitative data is not enough here</h2>
<p>«&nbsp;Seven in ten fear getting it wrong&nbsp;» is an excellent figure: it raises the alarm. It does not say what exactly people fear, at which point in the journey the fear blocks, or what lifts it. Those three answers determine everything you can do about it — staff training, aisle content, instructions, guarantee.</p>
<p>It is the kind of gap that closes with a dozen interviews at home, with people who have one project underway and one abandoned.</p>
""",
 "faq_titre": "Frequently asked questions",
 "faq": [
  ("Is the French DIY market growing in 2026?",
   "No, it is emerging from three consecutive years of decline in the superstore channel: −1.4% in 2023, −4.3% in 2024 and −1.4% in 2025, for €21.8bn including tax. The trade describes 2026 as a gradual, structured recovery rather than a rebound."),
  ("What is the main brake on DIY in France?",
   "The fear of getting it wrong, cited by around seven in ten people, ahead of budget. Being psychological, it can be treated through advice, teaching and product design rather than through promotion."),
  ("Why is average basket size falling?",
   "Because demand has moved from heavy renovation towards routine maintenance and economical repair. Basket size falls, frequency can rise, and the kind of advice expected changes completely."),
  ("How do you study what blocks the purchase?",
   "At home, not in a facility. An interview in front of the project underway and the project abandoned produces material that neither a questionnaire nor a group gives — because fear of getting it wrong is precisely what people will not admit in front of others."),
 ],
 "aide": {"titre": "Going to see what blocks, where it blocks",
  "chapo": "Housing, builders merchants, DIY and decoration are among our long-standing sectors, with consumers and trade customers alike.",
  "points": ["Interviews at home, in front of the project underway and the one abandoned",
             "Fieldwork in the aisle: what happens when nobody asks for anything",
             "Separate designs for consumers and tradespeople — they are not looking for the same thing",
             "Recruitment from your own customer file when you have one: the most effective cost lever there is"]},
 "loin": [("City cars: France and the UK diverge", "city-cars-france-uk.html"),
          ("Luxury has lost twenty million customers", "luxury-lost-customers.html")],
},
]


def render_index_en():
    cartes = "".join(
        '<a class="ct-card" href="%s">'
        '<div class="ct-card-top"><span class="ct-tag">%s</span><span class="ct-read">%s</span></div>'
        '<h3>%s</h3><p>%s</p>'
        '<div class="ct-card-foot"><time datetime="%s">%s</time>'
        '<span class="ct-go">Read &rarr;</span></div></a>'
        % (a["slug"], a["cat"], a["read"],
           re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", a["h1"]).replace("&nbsp;", " ")).strip(),
           a["desc"], a["date"], a["date_en"])
        for a in ARTICLES_EN)
    body = (
        '<section class="hero-compact">\n  <div class="container hero-compact-inner">\n'
        '    <div class="eyebrow" style="margin-bottom:14px;">&mdash; Insights</div>\n'
        '    <h1 class="display">The state of<br>our markets.</h1>\n'
        '    <p class="lead">Dated, attributed figures on the sectors we work in — and, beneath '
        'the figures, what fieldwork says and no market data shows.</p>\n'
        '    <p class="ct-frnote">Our full editorial archive — method articles, anonymised case '
        'studies, white paper and FAQ — is published in French. '
        '<a href="../contenus.html" style="border-bottom:1px solid currentColor">See it here</a>.</p>\n'
        '  </div>\n</section>\n\n'
        '<section class="section-pad">\n  <div class="container">\n'
        '    <div class="ct-grid">%s</div>\n  </div>\n</section>\n\n'
        '<section class="cta-block dark">\n  <div class="container">\n'
        '    <h2 class="display">A question<br>to illuminate?</h2>\n'
        '    <p class="lead">Build a study design in two minutes, or write us your question in three lines.</p>\n'
        '    <div class="ctas">\n'
        '      <a href="../decision-rapide.html#configurateur" class="btn btn-primary-light">'
        '<span>Build a study design</span>'
        '<svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none">'
        '<path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg></a>\n'
        '      <a href="../contact.html" class="btn btn-outline-light">Write to us</a>\n'
        '    </div>\n  </div>\n</section>' % cartes)
    ld = {"@context": "https://schema.org", "@type": "CollectionPage",
          "name": "Insights — ACMÉ Consultants", "inLanguage": "en",
          "description": "Market watch on the sectors ACMÉ works in, with dated and attributed figures."}
    return page_en("index.html",
                   "Insights — market watch | ACMÉ Consultants",
                   "Dated, attributed figures on mobility, luxury and DIY in France — and what fieldwork says beneath the figures.",
                   body, "contenus.html", extra_jsonld=ld, current="ct")


# Le point d'entrée reste EN DERNIER : tout ce qui est déclaré après ne serait
# pas encore défini au moment où main() s'exécute.
if __name__ == "__main__":
    main()
