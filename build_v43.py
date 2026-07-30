#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère acme-site/index-v4-3.html depuis index-v4-2.html.

v4.3 garde TOUT v4.2 (les quatre actes scrubbés, le HUD de transport, les
plaques calées sur les fonds des vidéos) et ne remplace que le hero : au lieu
d'un plan fixe, une séquence continue de 17,3 s — le montage bout à bout des
deux plans HD (démontage de l'appareil, puis éruption de données) — dont la
tête de lecture est le scroll, avec six paliers de texte qui se relaient.

La chaîne est explicite : ce script régénère d'abord v4.2, dont il dérive.
Sans ça, éditer build_v42.py puis ne lancer que celui-ci produirait une v4.3
bâtie sur une v4.2 périmée — le seul endroit que les assertions ne voient pas.
"""
import runpy
from build_common import DIR, read, write, splice, sub

runpy.run_path(str(DIR / "build_v42.py"), run_name="__chained__")

out = read("index-v4-2.html")

# ── 1. tête ────────────────────────────────────────────────────────────────
out = sub(out, "<title>ACMÉ v4.2 — La bande</title>",
          "<title>ACMÉ v4.3 — Le démontage</title>")
out = sub(out,
          '<meta name="description" content="ACMÉ Consultants — la parole client enregistrée, montée, décidée. '
          'Le scroll déroule la bande." />',
          '<meta name="description" content="ACMÉ Consultants — le scroll démonte l\'appareil, '
          'pièce par pièce, jusqu\'à la donnée." />')
out = sub(out, '<link rel="stylesheet" href="styles-v4-2.css" />',
          '<link rel="stylesheet" href="styles-v4-2.css" />\n'
          '<link rel="stylesheet" href="styles-v4-3.css" />')
out = sub(out, '<body class="v4-2">', '<body class="v4-2 v4-3">')

# ── 2. les six paliers, déclarés UNE fois ──────────────────────────────────
# La borne d'un palier est aussi le repère du chapitre correspondant : les deux
# doivent bouger ensemble, donc elles ne sont écrites qu'ici.
BEATS = [
    ("0",     "0.125", "Objet",      "Object"),
    ("0.125", "0.29",  "Démontage",  "Teardown"),
    ("0.29",  "0.45",  "Grille",     "Grid"),
    ("0.45",  "0.585", "Bande",      "Tape"),
    ("0.585", "0.785", "Donnée",     "Data"),
    ("0.785", "1",     "Décision",   "Decision"),
]

HERO_BEAT = '''        <div class="h2-beat" data-from="0" data-to="0.125">
          <span class="eyebrow" data-i18n="hero.eyebrow">ACMÉ · CONSULTANTS · DEPUIS 1987</span>
          <h1 class="display">
            <span data-i18n="v4.h1.l1">La parole client,</span>
            <span class="serif" data-i18n="v4.h1.l2">enregistrée,</span>
            <span data-i18n="v4.h1.l3">puis décidée.</span>
          </h1>
          <p data-i18n="v4.lead">30 ans d'études qualitatives.</p>
          <div class="v4-hero-ctas">
            <a href="#parole" class="btn btn-primary-dark v4-key"><i class="tri">&#9654;</i> <span data-i18n="v4.cta.brief">Brief</span></a>
            <a href="#sectors" class="btn btn-outline-dark v4-key" data-i18n="v4.cta.sectors">Nos secteurs</a>
          </div>
        </div>
'''

def beat(i, frm, to, extra=""):
    """Un palier : eyebrow + titre + texte, remplacés sur place au scroll.
    Le texte vient de i18n.js (clés v43.bN.*) — ici, seuls la structure et la
    fenêtre de progression."""
    return (f'        <div class="h2-beat" data-from="{frm}" data-to="{to}">\n'
            f'          <span class="eyebrow" data-i18n="v43.b{i}.eyebrow">Plan 0{i}</span>\n'
            f'          <h2 class="display" data-i18n="v43.b{i}.h2">—</h2>\n'
            f'          <p data-i18n="v43.b{i}.p">—</p>\n'
            f'{extra}'
            f'        </div>\n')

CTA = ('          <div class="v4-hero-ctas">\n'
       '            <a href="contact.html" class="btn btn-primary-dark v4-key"><i class="tri">&#9654;</i> '
       '<span data-i18n="v43.cta">Démarrer un projet</span></a>\n'
       '          </div>\n')

beats = HERO_BEAT + "".join(
    beat(i, frm, to, CTA if i == len(BEATS) else "")
    for i, (frm, to, _, _) in enumerate(BEATS[1:], start=2)
)
rail = "".join(
    f'        <span data-at="{frm}" data-i18n="v43.r{i}">{fr}</span>\n'
    for i, (frm, _, fr, _) in enumerate(BEATS, start=1)
)

HERO = '''<!-- HERO v4.3 — LE DÉMONTAGE
     Séquence continue de 17,3 s (deux plans HD montés bout à bout : leur
     raccord est franc, la cassette est au même cadrage de part et d'autre).
     La tête de lecture est le scroll ; six paliers de texte se relaient dans
     le tiers gauche, jamais sur l'objet qui est au centre du cadre.
     Le fond de section reprend le fond réel de la vidéo — le plan n'a donc
     ni cadre ni vignette : le studio continue dans la typo. -->
<section class="v4-hero2" id="plateau" data-act data-track="Le démontage" data-track-en="The teardown">
  <div class="v4-act-track" style="--track:520vh;--track-m:300vh">
    <div class="h2-stage">
      <div class="v4-bar top" aria-hidden="true"></div>
      <div class="v4-bar bot" aria-hidden="true"></div>

      <div class="h2-media">
        <video data-scrub src="assets/v4/story.mp4" poster="assets/v4/story.jpg"
               muted playsinline preload="auto" disablepictureinpicture
               aria-label="Le magnétophone ACMÉ se démonte, puis la bande restitue ses données"
               tabindex="-1"></video>
      </div>

      <div class="container h2-copy">
''' + beats + '''      </div>

      <div class="h2-rail" aria-hidden="true">
''' + rail + '''      </div>

      <div class="v4-hud tc h2-tc" aria-hidden="true">TC <span data-tc data-fps="15">00:00:00:00</span></div>
      <div class="v4-cue h2-cue" aria-hidden="true"><i></i><span data-i18n="v4.cue">Dérouler</span></div>
    </div>
  </div>
</section>

'''

out = splice(out, "<!-- HERO v4.2 — LE PLATEAU", "<!-- MARQUEE -->", HERO)

write("index-v4-3.html", out)
print(f"  paliers : {out.count('h2-beat')} · chapitres : {out.count('data-at=')} · "
      f"actes scrubbés : {out.count('data-act')}")
