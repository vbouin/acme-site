#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère acme-site/index-v4-2.html depuis index-v3-1.html.

On part de v3.1 pour hériter de tout le contenu déjà écrit (piliers, méthodo,
secteurs, expertises, footer) et on ne remplace que ce qui change : le hero,
plus quatre actes scrubbés insérés entre les sections existantes.
"""
from build_common import read, write, sub, splice, scrub_video, meter

out = read("index-v3-1.html")

# ── 1. tête ────────────────────────────────────────────────────────────────
out = sub(out, "<title>ACMÉ v3.1 — Hero auto-cycle</title>",
    "<title>ACMÉ v4.2 — La bande</title>")
out = sub(out, '<meta name="description" content="ACMÉ — grille interactive + hero auto-cycle des deux animations." />',
    '<meta name="description" content="ACMÉ Consultants — la parole client enregistrée, montée, décidée. '
    'Le scroll déroule la bande." />')
out = sub(out, '<link rel="stylesheet" href="styles-v3.css" />',
    '<link rel="stylesheet" href="styles-v4-2.css" />')
out = sub(out, '<body class="v3 v3-1">', '<body class="v4-2">')

# ── 2. HERO ────────────────────────────────────────────────────────────────
HERO = '''<!-- HERO v4.2 — LE PLATEAU
     Le fond de section reprend le dégradé du fond de la vidéo (même axe 135°)
     et les bords du média sont estompés au masque : le magnétophone flotte
     dans la page, sans cadre ni boîte. -->
<section class="v4-hero" id="plateau" data-track="Plateau" data-track-en="Set">
  <div class="v4-bar top" aria-hidden="true"></div>
  <div class="v4-bar bot" aria-hidden="true"></div>

  <div class="container v4-hero-inner">
    <div class="v4-hero-copy">
      <div class="eyebrow v4-rise" style="--d:100ms" data-i18n="hero.eyebrow">ACMÉ · CONSULTANTS · DEPUIS 1987</div>
      <h1 class="display">
        <span class="v4-rise" style="--d:200ms" data-i18n="v4.h1.l1">La parole client,</span>
        <span class="serif v4-rise" style="--d:320ms" data-i18n="v4.h1.l2">enregistrée,</span>
        <span class="v4-rise" style="--d:440ms" data-i18n="v4.h1.l3">puis décidée.</span>
      </h1>
      <p class="lead v4-rise" style="--d:580ms" data-i18n="v4.lead">30 ans d'études qualitatives. Nous captons la parole, nous la montons, et nous vous rendons une décision — pas un rapport.</p>
      <div class="v4-hero-ctas v4-rise" style="--d:690ms">
        <a href="#parole" class="btn btn-primary-dark v4-key"><i class="tri">&#9654;</i> <span data-i18n="v4.cta.brief">Brief</span></a>
        <a href="#sectors" class="btn btn-outline-dark v4-key" data-i18n="v4.cta.sectors">Nos secteurs</a>
      </div>
      <div class="v4-slate v4-rise" style="--d:800ms" data-i18n="v4.slate">Plan 01 · magnétophone Acmé · touche « brief » · 24 i/s</div>
    </div>

    <div class="v4-hero-stage">
      <div class="v4-tape">
        <video src="assets/v4/tape-hero.mp4" poster="assets/v4/tape-hero.jpg"
               muted loop playsinline autoplay preload="auto"
               disablepictureinpicture aria-label="Magnétophone ACMÉ Consultants"
               tabindex="-1"></video>
        <div class="v4-hud rec"><span class="v4-dot"></span>Rec</div>
        <div class="v4-hud tc">TC <span data-tc data-fps="24">00:00:00:00</span></div>
        <button class="v4-pp" type="button" aria-label="Suspendre ou relancer la bande">&#10074;&#10074; Pause</button>
        <div class="v4-vu" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
      </div>
    </div>
  </div>

  <div class="v4-cue down" aria-hidden="true"><i></i><span data-i18n="v4.cue">Dérouler</span></div>
</section>

'''
out = splice(out, "<!-- HERO — split slider", "<!-- MARQUEE -->", HERO)

# ── 3. les quatre actes ────────────────────────────────────────────────────
ACT_PAROLE = '''<!-- ACTE 01 — DE LA PAROLE À LA BANDE
     Séquence scrubbée : la tête de lecture est le scroll. Les trois bulles
     de la vidéo (pain points / expectations / decision) sont doublées par
     trois légendes synchronisées sur la progression de la séquence. -->
<section class="v4-act v4-bubbles" id="parole" data-act data-track="La parole" data-track-en="The voice">
  <div class="v4-act-track" style="--track:280vh;--track-m:210vh">
    <div class="v4-act-stage">
      <div class="v4-act-media">
        ''' + scrub_video('bubbles', 'Des bulles de verre — pain points, expectations, decision — fusionnent dans la cassette') + '''
      </div>
      <div class="v4-act-copy">
          <div>
            <div class="eyebrow" data-i18n="v4.a1.eyebrow">— Acte 01 · de la parole à la bande</div>
            <h2 class="display" data-i18n="v4.a1.h2">Chaque phrase<br><span class="serif">devient</span><br>une donnée.</h2>
            <p class="lead" data-i18n="v4.a1.lead">Nous n'enregistrons pas des avis : nous enregistrons des raisons. Chaque tour de parole reste rattaché à son entretien, jusqu'à la décision qu'il éclaire.</p>
            <div class="v4-beat-list">
              <div class="v4-beat" data-from="0.10" data-to="0.46" data-i18n="v4.a1.b1"><span>01</span><div><b>Pain points</b> — ce qui bloque, dit avec les mots du client</div></div>
              <div class="v4-beat" data-from="0.38" data-to="0.72" data-i18n="v4.a1.b2"><span>02</span><div><b>Expectations</b> — ce qui est attendu, et dans quel ordre</div></div>
              <div class="v4-beat" data-from="0.64" data-to="1" data-i18n="v4.a1.b3"><span>03</span><div><b>Decision</b> — ce qui se joue, arbitré</div></div>
            </div>
          </div>
      </div>
''' + meter(1) + '''    </div>
  </div>
</section>

'''

ACT_MORPH = '''<!-- ACTE 02 — DU CROQUIS À L'OBJET
     Les deux images sont calées au pixel (même cadrage, 1618×1092) : un
     simple clip-path piloté au scroll suffit à faire devenir le croquis
     un objet. Le filet d'encre marque la pointe du crayon. -->
<section class="v4-act v4-morph" id="livrable" data-act data-track="Le livrable" data-track-en="Deliverable">
  <div class="v4-act-track" style="--track:240vh;--track-m:190vh">
    <div class="v4-act-stage">
      <div class="v4-act-media">
        <div class="v4-morph-wrap">
          <img class="sketch" src="assets/v4/tape-sketch.webp" loading="lazy" decoding="async"
               alt="Croquis de la cassette ACMÉ" />
          <img class="final" src="assets/v4/tape-final.webp" loading="lazy" decoding="async"
               alt="La cassette ACMÉ finie" />
          <span class="v4-morph-edge" aria-hidden="true"></span>
          <div class="v4-morph-labels"><span data-i18n="v4.a2.lab1">Croquis · brief</span><span data-i18n="v4.a2.lab2">Objet · livrable</span></div>
        </div>
      </div>
      <div class="v4-act-copy">
        <div>
          <div class="eyebrow" data-i18n="v4.a2.eyebrow">— Acte 02 · du brief au livrable</div>
          <h2 class="display" data-i18n="v4.a2.h2">Le brief est<br>un croquis.<br><span class="serif">Le livrable</span><br>est un objet.</h2>
          <p class="lead" data-i18n="v4.a2.lead">Entre les deux : le cadrage, le terrain, l'analyse. Rien ne se perd — tout se précise.</p>
        </div>
      </div>
''' + meter(2) + '''    </div>
  </div>
</section>

'''

ACT_PERSONA = '''<!-- ACTE 03 — LE PERSONA S'ÉCRIT À LA MAIN
     La vidéo est désaturée (identité strictement monochrome) et masquée en
     dégradé vers le bas : les annotations s'y posent sans cartouche. -->
<section class="v4-act v4-pens media-left" id="personas" data-act data-track="Les personas" data-track-en="Personas">
  <div class="v4-act-track" style="--track:260vh;--track-m:200vh">
    <div class="v4-act-stage">
      <div class="v4-act-media">
        ''' + scrub_video('pens', "Deux mains annotent au stylo le croquis d'une cassette ACMÉ") + '''
      </div>
      <div class="v4-act-copy">
        <div>
          <div class="eyebrow" data-i18n="v4.a3.eyebrow">— Acte 03 · le persona</div>
          <h2 class="display" data-i18n="v4.a3.h2">Le persona<br><span class="serif">s'écrit</span> à la main.</h2>
          <div class="v4-beat-list" style="max-width:660px">
            <div class="v4-note v4-beat" data-from="0.08" data-to="0.42" data-i18n="v4.a3.n1">Persona buyer — for a small city car</div>
            <div class="v4-note v4-beat" data-from="0.34" data-to="0.68" data-i18n="v4.a3.n2">User 01 · User 02 · User 03 — trois voix, un même arbitrage</div>
            <div class="v4-note v4-beat" data-from="0.62" data-to="1" data-i18n="v4.a3.n3">Relu, annoté, validé — puis livré</div>
          </div>
        </div>
      </div>
''' + meter(3) + '''    </div>
  </div>
</section>

'''

ACT_OBJET = '''<!-- ACTE 04 — L'OBJET FINI
     Platine : la cassette tourne au rythme du scroll. Remonter la fait
     tourner à l'envers — la bande rembobine pour de vrai. -->
<section class="v4-act v4-turn" id="objet" data-act data-track="L'objet" data-track-en="The object">
  <div class="v4-act-track" style="--track:200vh;--track-m:165vh">
    <div class="v4-act-stage">
      <div class="v4-act-media">
        ''' + scrub_video('turn', 'La cassette ACMÉ translucide tourne lentement') + '''
      </div>
      <div class="v4-act-copy">
        <div>
          <div class="eyebrow" data-i18n="v4.a4.eyebrow">— Acte 04 · l'objet</div>
          <h2 class="display" data-i18n="v4.a4.h2">Une étude,<br><span class="serif">trois</span> niveaux de lecture.</h2>
          <p class="lead" data-i18n="v4.a4.lead">Extensif pour ceux qui creusent, vidéo pour ceux qui décident, flash pour ceux qui passent. La même bande, trois montages.</p>
          <div class="v4-turn-hint" data-i18n="v4.a4.hint">Remontez : la bande rembobine</div>
        </div>
      </div>
''' + meter(4) + '''    </div>
  </div>
</section>

'''

out = sub(out, "<!-- METHODOLOGY -->", ACT_PAROLE + "<!-- METHODOLOGY -->")
out = sub(out, "<!-- DELIVERABLES TIERS -->", ACT_MORPH + "<!-- DELIVERABLES TIERS -->")
out = sub(out, "<!-- IMPACT DASHBOARD -->", ACT_PERSONA + "<!-- IMPACT DASHBOARD -->")
out = sub(out, "<!-- CTA FINAL -->", ACT_OBJET + "<!-- CTA FINAL -->")

# ── 4. pistes du transport sur les sections existantes ─────────────────────
out = sub(out, '<section class="method section-pad" id="methodologie">',
    '<section class="method section-pad" id="methodologie" data-track="Méthodologie" data-track-en="Method">')
out = sub(out, '<!-- DELIVERABLES TIERS -->\n<section class="section-pad">',
    '<!-- DELIVERABLES TIERS -->\n<section class="section-pad" data-track="Livrables" data-track-en="Deliverables">')
out = sub(out, '<section class="impact section-pad">',
    '<section class="impact section-pad" data-track="Impact" data-track-en="Impact">')
out = sub(out, '<section class="sectors section-pad" id="sectors">',
    '<section class="sectors section-pad" id="sectors" data-track="Secteurs" data-track-en="Sectors">')
out = sub(out, '<section class="expertises section-pad" id="expertises">',
    '<section class="expertises section-pad" id="expertises" data-track="Expertises" data-track-en="Expertise">')
out = sub(out, '<section class="cta-block dark">',
    '<section class="cta-block dark" data-track="Contact" data-track-en="Contact">')

# ── 5. moteur de scroll ────────────────────────────────────────────────────
out = sub(out, '<script src="main.js"></script>',
    '<script src="main.js"></script>\n<script src="acts.js"></script>')

write("index-v4-2.html", out)
print(f"  actes scrubbés : {out.count('data-act')} · pistes : {out.count('data-track=')}")
