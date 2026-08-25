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


def page(slug, title, desc, body, extra_jsonld=None, current="", css_extra="",
         breadcrumbs=None, og_type="website"):
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

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet" />
<title>{title}</title>
<meta name="description" content="{html.escape(desc, quote=True)}" />
<link rel="canonical" href="{SITE}/{slug}" />
<!-- Open Graph : absent du site aujourd'hui, chaque lien partagé sur LinkedIn
     s'affichait dégradé — or LinkedIn est le premier levier d'acquisition. -->
<meta property="og:type" content="{og_type}" />
<meta property="og:site_name" content="ACMÉ Consultants" />
<meta property="og:locale" content="fr_FR" />
<meta property="og:title" content="{html.escape(title, quote=True)}" />
<meta property="og:description" content="{html.escape(desc, quote=True)}" />
<meta property="og:url" content="{SITE}/{slug}" />
<meta property="og:image" content="{SITE}/assets/v4/decision.jpg" />
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
</body>
</html>
"""


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
 "cat": "Terrain",
 "date": "2026-08-25",
 "read": "7 min",
 "title": "Organiser un focus group à Lyon : ce qu'on a appris en quarante ans — ACMÉ Consultants",
 "h1": "Organiser un focus group à&nbsp;Lyon :<br>ce qu'on a appris en quarante ans.",
 "desc": "Salle, recrutement, taille de groupe, animation : le guide pratique d'un cabinet d'études qualitatives lyonnais, fondé sur les erreurs qu'on a payées.",
 "kw": "focus group Lyon, institut d'études Lyon, étude qualitative Lyon, salle focus group",
 "chapo": "Un focus group raté ne se voit pas le jour même. Il se voit trois semaines plus tard, quand l'analyse ne dit rien qu'on ne savait déjà. Voici où ça se joue — et ce qui, à Lyon, change la donne.",
 "body": """
<h2>Combien de participants dans un focus group ?</h2>
<p><strong>Six à huit personnes, rarement plus.</strong> C'est le point d'équilibre entre deux échecs symétriques : en dessous de cinq, un participant dominant confisque la parole et le groupe devient un entretien à témoins ; au-delà de neuf, la durée de parole individuelle tombe sous les cinq minutes et vous n'obtenez plus que des positions de principe.</p>
<p>Le chiffre qui compte n'est pas le nombre d'inscrits mais le nombre de présents. Sur un recrutement grand public, tablez sur 15 à 20&nbsp;% de défection malgré la confirmation la veille. Nous recrutons donc systématiquement deux personnes de plus que la cible, et nous les indemnisons toutes, y compris celles que nous renvoyons — c'est le coût de la sécurité du dispositif, et il est très inférieur à celui d'un groupe à quatre.</p>

<h2>Faut-il une salle spécialisée ou une salle de réunion suffit-elle ?</h2>
<p><strong>Une salle spécialisée se justifie dès qu'il y a des observateurs.</strong> Si votre équipe marketing veut assister, une salle avec glace sans tain ou retour vidéo change tout : sans elle, vous mettez cinq personnes en costume au fond de la pièce et vous obtenez un groupe qui se surveille.</p>
<p>À Lyon, plusieurs prestataires équipés opèrent en presqu'île, avec streaming et prise de son multipiste. C'est une commodité réelle du bassin lyonnais : sur beaucoup de villes de taille comparable, il faut monter le dispositif de toutes pièces. Si personne n'observe et que le sujet n'exige pas de matériel, une salle neutre bien insonorisée suffit — et vous économisez un poste.</p>
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

<h2>Le calendrier réaliste</h2>
<p><strong>Comptez cinq à sept semaines entre le brief et la restitution</strong> pour un dispositif de quatre groupes&nbsp;: une semaine de cadrage et d'écriture du guide, deux semaines de recrutement, une semaine de terrain, une à deux semaines d'analyse et de restitution. Le recrutement est le seul poste qui se comprime vraiment — et uniquement si vous fournissez le fichier.</p>
<p class="art-more">Vous pouvez composer un dispositif et obtenir son calendrier sur notre <a href="decision-rapide.html#configurateur">configurateur Décision rapide</a>.</p>
""",
},
{
 "slug": "article-ia-etudes-qualitatives.html",
 "cat": "Méthode",
 "date": "2026-08-25",
 "read": "9 min",
 "title": "IA et études qualitatives : ce que la machine fait bien, ce qu'elle rate encore — ACMÉ Consultants",
 "h1": "IA et études qualitatives :<br>ce qu'elle fait bien,<br>ce qu'elle rate encore.",
 "desc": "Transcription, codage, synthèse, entretien modéré par IA : maillon par maillon, ce que l'automatisation apporte vraiment à une étude qualitative — et où elle coûte plus qu'elle ne rapporte.",
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
<p><strong>Non, pas comme substitut de terrain.</strong> La profession française a tranché avant nous&nbsp;: Syntec Conseil a publié en mai 2025 sept engagements d'usage responsable de l'IA dans les études — supervision humaine à chaque étape, transparence totale sur les outils employés. Et la direction générale d'OpinionWay a publiquement qualifié les entretiens synthétiques de « mirage dangereux » en novembre 2025.</p>
<p>La raison est simple&nbsp;: un modèle génère la réponse la plus probable. Une étude qualitative sert à trouver l'improbable — la personne qui n'utilise pas votre produit comme prévu, celle qui a un usage que personne n'avait imaginé. Interroger un modèle revient à interroger la moyenne de ce qui a déjà été écrit, c'est-à-dire exactement ce que vous savez déjà.</p>
<p>Les répondants synthétiques ont un usage honnête et étroit&nbsp;: pré-tester un guide d'entretien, repérer une question mal formulée avant d'engager du terrain réel. Nous les utilisons pour ça, et pour rien d'autre.</p>

<h2>Notre règle : ce que l'IA fait, ce qu'elle ne fait jamais</h2>
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
 "cat": "Repères",
 "date": "2026-08-25",
 "read": "8 min",
 "title": "Combien coûte une étude qualitative ? Les repères d'un marché opaque — ACMÉ Consultants",
 "h1": "Combien coûte<br>une étude qualitative ?",
 "desc": "Recrutement, terrain, analyse, restitution : ce qui fait réellement le prix d'une étude qualitative, avec les repères publics du marché français en 2026.",
 "kw": "prix étude qualitative, tarif focus group, budget étude qualitative, coût entretien qualitatif",
 "chapo": "Presque aucun institut n'affiche ses prix. Le résultat, c'est un acheteur qui ne sait pas s'il regarde un devis à 8 000 ou à 80 000 euros, et qui renonce à demander. Voici la structure de coût, poste par poste, et les repères publics qui existent.",
 "body": """
<h2>Pourquoi personne n'affiche de prix</h2>
<p><strong>Parce qu'une étude qualitative n'est pas un produit, et que les instituts facturent le même dispositif à des niveaux différents selon le client.</strong> C'est une convention de marché, pas une conspiration&nbsp;: le coût réel dépend de la difficulté de recrutement, du nombre de pays, du matériel à manipuler et du livrable attendu, qui varient d'un facteur cinq.</p>
<p>Cette opacité a toutefois un effet pervers documenté&nbsp;: elle fait renoncer les acheteurs qui n'ont aucune idée de l'ordre de grandeur, et elle laisse le champ libre au premier acteur qui affiche un prix — même s'il ne vend pas la même chose.</p>

<h2>Les cinq postes qui font le prix</h2>
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
<thead><tr><th>Repère</th><th>Niveau observé</th><th>Ce que ça dit</th></tr></thead>
<tbody>
<tr><td>Transcription automatique</td><td>0,20 à 0,75&nbsp;$ / heure</td><td>Le poste n'est plus facturable comme un service.</td></tr>
<tr><td>TJM freelance UX / recherche</td><td>125 à 950&nbsp;€ / jour</td><td>Plancher très bas ; la dispersion mesure l'écart de séniorité.</td></tr>
<tr><td>Coût interne équivalent salarié</td><td>~218&nbsp;€ / jour</td><td>L'ancre mentale d'un client qui envisage d'internaliser.</td></tr>
<tr><td>Entrée UX research affichée</td><td>à partir de 10 000&nbsp;€ HT</td><td>Le seul prix public du panel — il devient la référence par défaut.</td></tr>
<tr><td>Instituts d'études</td><td>Aucun prix public</td><td>L'opacité reste la norme.</td></tr>
</tbody>
</table>
</div>
<p class="art-note">Repères relevés en août 2026 sur des sources publiques (grilles tarifaires d'éditeurs, profils de plateformes de freelances, pages tarifaires d'agences). Ce sont des ordres de grandeur de marché, pas des tarifs ACMÉ.</p>

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
 "cat": "Méthode",
 "date": "2026-08-25",
 "read": "6 min",
 "title": "Entretiens individuels ou focus groups : comment choisir — ACMÉ Consultants",
 "h1": "Entretiens individuels<br>ou focus groups ?",
 "desc": "Le groupe révèle les normes, l'entretien révèle les écarts. Une grille de décision concrète pour choisir le bon dispositif selon votre question, votre cible et votre budget.",
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

<h2>La grille de décision</h2>
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
 "cat": "Point de vue",
 "date": "2026-08-25",
 "read": "8 min",
 "title": "Décider vite sans décider mal : ce que peut vraiment un dispositif court — ACMÉ Consultants",
 "h1": "Décider vite<br>sans décider mal.",
 "desc": "« Huit fois plus vite, 80 % moins cher » : ce que ces promesses compressent réellement, ce qu'elles sacrifient, et comment cadrer un dispositif court qui tienne devant un comité.",
 "kw": "étude qualitative rapide, quick study, dispositif court étude, décision rapide étude marché",
 "chapo": "Le marché des études s'est mis à vendre de la vitesse. La question n'est pas de savoir si c'est possible — c'est de savoir ce qu'on enlève pour y arriver, et si ce qu'on enlève est ce dont on avait besoin.",
 "body": """
<h2>Ce que la vitesse compresse réellement</h2>
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

<h2>À quoi ressemble un dispositif court qui tient</h2>
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

<h2>Quand un dispositif court n'est pas la bonne réponse</h2>
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
 "cat": "Mobilité & Automobile",
 "date": "2026-08-25",
 "read": "5 min",
 "title": "Cas — Concevoir un utilitaire léger pour des artisans qui ne se plaignent jamais",
 "h1": "Concevoir un utilitaire<br>pour des artisans qui<br>ne se plaignent jamais.",
 "desc": "Étude de cas anonymisée : trois focus groups et une série d'entretiens dans deux pays pour cadrer la prochaine génération d'un véhicule utilitaire léger.",
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

<h2>Ce qu'on en retient pour d'autres missions</h2>
<p>Sur un public professionnel, la question « êtes-vous satisfait » ne produit rien. La question « racontez-moi votre mardi » produit tout. Et le réinvitation d'un groupe est le meilleur rapport qualité-prix d'un dispositif qualitatif&nbsp;: pas de nouveau recrutement, un matériau nettement plus profond.</p>
""",
},
{
 "slug": "cas-clinique-electrique.html",
 "cat": "Mobilité & Automobile",
 "date": "2026-08-25",
 "read": "5 min",
 "title": "Cas — Faire arbitrer un design de véhicule électrique par ceux qui en conduisent déjà un",
 "h1": "Faire arbitrer un design<br>par ceux qui conduisent<br>déjà la concurrence.",
 "desc": "Étude de cas anonymisée : une clinique produit auprès de possesseurs de véhicules électriques concurrents pour arbitrer concept, design et interface avant design freeze.",
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

<h2>Ce qu'on en retient pour d'autres missions</h2>
<p>Quand il y a un objet, il faut être devant l'objet&nbsp;: aucun dispositif à distance ne restitue ce qui se joue dans les trente secondes où quelqu'un tourne autour d'une voiture. Et le critère de recrutement le plus rentable est souvent le plus contraignant à sourcer.</p>
""",
},
{
 "slug": "cas-fichier-client-materiaux.html",
 "cat": "Bâtiment",
 "date": "2026-08-25",
 "read": "4 min",
 "title": "Cas — Diviser le coût d'un terrain en recrutant dans le fichier du client",
 "h1": "Diviser le coût d'un terrain<br>en recrutant dans<br>le fichier du client.",
 "desc": "Étude de cas anonymisée : comment un réseau de distribution de matériaux a fourni sa propre base client, et ce que ça change au budget comme à la qualité du terrain.",
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

<h2>Ce qu'on en retient pour d'autres missions</h2>
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
 ("Qu'est-ce qu'une car clinic ?",
  "Une clinique produit est un dispositif où des participants recrutés sur critères évaluent un véhicule, un prototype ou des directions de design en présence physique de l'objet. Elle peut être statique — l'objet est observé et manipulé — ou dynamique, avec essai. C'est le seul dispositif qui rend visible l'écart entre ce que les gens déclarent préférer et ce vers quoi ils vont réellement."),
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
 ("Où sont hébergées les données de mon étude ?",
  "La transcription passe par un fournisseur français, sans entraînement des modèles sur les corpus clients et sans rétention au-delà du traitement. Les corpus restent votre propriété et vous sont remis intégralement, y compris si vous ne prenez pas l'analyse."),
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
 "title": "Livre blanc — La parole client, structurée jusqu'à la décision | ACMÉ Consultants",
 "h1": "La parole client,<br>structurée jusqu'à<br>la décision.",
 "desc": "Livre blanc : un protocole d'analyse de verbatim traçable, où l'IA fait le travail mécanique et où chaque conclusion reste remontable jusqu'à sa source.",
 "kw": "analyse de verbatim, protocole étude qualitative, traçabilité verbatim, méthode qualitative IA",
 "chapo": "Comment passer de quarante heures d'enregistrement à une décision que l'on peut défendre — sans perdre en route ce qui rendait le corpus intéressant.",
 "sommaire": [
   ("01", "Le problème que ce protocole résout", "pb"),
   ("02", "Quatre principes", "principes"),
   ("03", "Le protocole, phase par phase", "phases"),
   ("04", "Ce que l'IA fait, ce qu'elle ne fait jamais", "ia"),
   ("05", "La traçabilité, concrètement", "trace"),
   ("06", "Le cadre déontologique", "cadre"),
   ("07", "Ce que ça change pour vous", "vous"),
 ],
 "body": """
<section id="pb">
<h2><span class="wb-n">01</span> Le problème que ce protocole résout</h2>
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
<h2><span class="wb-n">04</span> Ce que l'IA fait, ce qu'elle ne fait jamais</h2>
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
        "author": {"@type": "Organization", "name": ORG["name"]},
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
    body = f"""<article class="art">
  <header class="art-head">
    <div class="container art-w">
      <div class="art-kicker"><a href="{back[0]}">{back[1]}</a><span>·</span><span>{a['cat']}</span></div>
      <h1 class="display">{a['h1']}</h1>
      <p class="art-chapo">{a['chapo']}</p>
      <div class="art-meta"><time datetime="{a['date']}">{date_fr(a['date'])}</time><span>·</span><span>{a['read']} de lecture</span></div>
      {meta}
      {anon}
    </div>
  </header>
  <div class="container art-w art-body" lang="fr">
{a['body']}
  </div>
  <div class="container art-w">
    <div class="art-foot">
      <a href="{back[0]}" class="btn btn-outline-dark">{back[1]}</a>
      <a href="contact.html" class="btn btn-primary-dark"><span data-i18n="nav.cta">Démarrer un projet</span><svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none"><path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg></a>
    </div>
  </div>
</article>"""
    return page(a["slug"], a["title"], a["desc"], body,
                extra_jsonld=article_jsonld(a, kind), current="ct", og_type="article",
                breadcrumbs=[("Accueil", ""), ("Contenus", "contenus.html"),
                             (re.sub(r"<[^>]+>", " ", a["h1"]).replace("&nbsp;", " ").strip(), a["slug"])])


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
    <div class="faq-cta">
      <h2 class="display">Votre question<br>n'y est pas ?</h2>
      <p class="lead">Écrivez-nous en trois lignes. Nous répondons sous 48 heures.</p>
      <div class="ctas"><a href="contact.html" class="btn btn-primary-dark"><span data-i18n="nav.cta">Démarrer un projet</span><svg class="arrow" width="14" height="10" viewBox="0 0 14 10" fill="none"><path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5"/></svg></a></div>
    </div>
  </div>
</section>"""
    return page("faq.html", "FAQ — études qualitatives, délais, budget et données | ACMÉ Consultants",
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
    arts = "".join(card(a, "article") for a in ARTICLES)
    cass = "".join(card(c, "cas") for c in CAS)
    body = f"""<section class="hero-compact">
  <div class="container hero-compact-inner">
    <div class="eyebrow" style="margin-bottom:14px;" data-i18n="content.eyebrow">— Contenus</div>
    <h1 class="display" data-i18n="content.h1">Ce qu'on a appris,<br>et qu'on peut écrire.</h1>
    <p class="lead" data-i18n="content.lead">Des articles de praticiens plutôt que des définitions, des études de cas anonymisées plutôt que des logos, et les réponses aux questions qu'on nous pose vraiment.</p>
    <p class="ct-frnote" data-i18n="content.frnote"></p>
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
      <div class="ct-feature-mark" aria-hidden="true"><span>01</span><span>02</span><span>03</span><span>04</span><span>05</span></div>
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
    }
    return page("contenus.html",
                "Contenus — articles, études de cas et livre blanc | ACMÉ Consultants",
                "Articles de praticiens sur les études qualitatives, études de cas anonymisées, livre blanc sur l'analyse de verbatim traçable et FAQ complète.",
                body, extra_jsonld=ld, current="ct",
                breadcrumbs=[("Accueil", ""), ("Contenus", "contenus.html")])


def main():
    out = []
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


if __name__ == "__main__":
    main()
