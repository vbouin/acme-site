#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Briques communes aux générateurs de variantes v4.x.

Les pages v4 ne sont pas écrites à la main : elles dérivent d'une variante
précédente par substitutions ancrées. Tout ancrage est vérifié — un ancrage qui
bouge doit casser le build, pas produire silencieusement une page incomplète.
"""
from pathlib import Path

DIR = Path(__file__).resolve().parent


def read(name):
    return (DIR / name).read_text(encoding="utf-8")


def write(name, html):
    (DIR / name).write_text(html, encoding="utf-8")
    print(f"[écrit] {name} — {len(html.encode())/1024:.1f} Ko")


def sub(html, old, new):
    """Remplace un fragment unique. Lève si absent ou ambigu."""
    n = html.count(old)
    assert n == 1, f"ancrage {n}× (attendu 1) : {old[:70]!r}"
    return html.replace(old, new)


def splice(html, start, end, new):
    """Remplace tout ce qui va de `start` (inclus) à `end` (exclu).

    Les deux bornes sont vérifiées comme des ancrages uniques : c'est le même
    contrat que sub(), sur une découpe.
    """
    for anchor in (start, end):
        n = html.count(anchor)
        assert n == 1, f"ancrage {n}× (attendu 1) : {anchor[:70]!r}"
    i, j = html.index(start), html.index(end)
    assert i < j, f"ancrages inversés : {start[:40]!r} après {end[:40]!r}"
    return html[:i] + new + html[j:]


def scrub_video(stem, alt, preload="metadata"):
    """Une <video> scrubbée au scroll.

    preload par défaut à "metadata" : les séquences sous la ligne de flottaison
    ne doivent pas se télécharger au chargement (plusieurs Mo). acts.js promeut
    en "auto" à l'approche, avec ~30vh d'avance.
    """
    return (f'<video data-scrub src="assets/v4/{stem}.mp4" poster="assets/v4/{stem}.jpg"\n'
            f'               muted playsinline preload="{preload}" disablepictureinpicture\n'
            f'               aria-label="{alt}" tabindex="-1"></video>')


def meter(n):
    """Compteur d'acte : le numéro gouverne le libellé ET la clé i18n."""
    return ('      <div class="v4-act-meter" aria-hidden="true">\n'
            f'        <span data-i18n="v4.a{n}.meter">Acte 0{n}</span>'
            '<span class="rail"><b></b></span>'
            '<span><span data-pct>000</span> %</span>\n'
            '      </div>\n')
