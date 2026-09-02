# ACMÉ — site v5.2

Version de travail du nouveau site ACMÉ Consultants, servie par GitHub Pages :

### **[→ Ouvrir l'aperçu](https://vbouin.github.io/acme-site/v5.2/)**

Le bouton **FR / EN** en haut à droite bascule tout le site en anglais
(le contenu éditorial — articles, cas, livre blanc, FAQ — reste en français).

## Ce que v5.2 ajoute

| Nouveauté | Page |
|---|---|
| **Décision rapide** — l'offre courte, avec un configurateur de dispositif | [/v5.2/decision-rapide.html](decision-rapide.html) |
| **Contenus** — hub blog, études de cas, livre blanc, FAQ | [/v5.2/contenus.html](contenus.html) |
| 27 articles | [focus group Lyon](article-focus-group-lyon.html) · [IA et quali](article-ia-etudes-qualitatives.html) · [prix](article-prix-etude-qualitative.html) · [entretiens ou groupes](article-entretiens-ou-groupes.html) · [décider vite](article-decider-vite.html) · [répondants synthétiques](article-repondants-synthetiques.html) · [car clinic](article-car-clinic.html) · [brief d'étude](article-brief-etude-qualitative.html) |
| **5 articles d'intention d'achat (sept. 2026)** | [quali ou quanti, dans quel ordre](article-quali-ou-quanti.html) · [combien d'entretiens](article-combien-entretiens.html) · [test de concept](article-test-de-concept.html) · [étude qualitative B2B](article-etude-qualitative-b2b.html) · [restitution et atelier de décision](article-restitution-atelier-decision.html) |
| 3 études de cas anonymisées | [utilitaire & artisans](cas-utilitaire-artisans.html) · [clinique électrique](cas-clinique-electrique.html) · [fichier client](cas-fichier-client-materiaux.html) |
| **Observatoire de marchés** | [citadines France/UK](marche-citadines-france-uk.html) · [le luxe et ses 20 M de clients perdus](marche-luxe-clients-perdus.html) · [bricolage et peur de mal faire](marche-bricolage-peur-de-mal-faire.html) |
| **Parcours sectoriels** (gabarit ×6) | [mobilité](parcours-mobilite.html) · [retail & FMCG](parcours-retail-fmcg.html) · [cosmétique](parcours-sante-cosmetiques.html) · [bâtiment](parcours-batiment.html) · [mode & luxe](parcours-mode-luxe.html) · [territoires](parcours-territoires.html) |
| **Page pilier** | [L'étude qualitative, du cadrage à la décision](etude-qualitative.html) |
| Livre blanc, 7 chapitres | [/v5.2/livre-blanc.html](livre-blanc.html) |
| FAQ, 22 questions | [/v5.2/faq.html](faq.html) |

### Septembre 2026 — cinq articles d'intention d'achat

Choisis d'après le corpus de prompts et la veille éditoriale : les questions qu'un
acheteur pose en phase de cadrage (quali ou quanti, combien d'entretiens, tester un
concept, interroger des décideurs B2B) et celle que personne ne pose mais qui décide
de tout (à quoi sert le rapport). Aucune requête de définition, aucune requête
« outil ». Chaque article cite ses sources en ligne (Hennink & Kaiser 2022, Guest 2006,
Nielsen, IntoTheMinds, Enov, Greenbook, Quirk's) et porte un fait de terrain.

Le cocon « L'étude qualitative » reçoit une quatrième branche, **« Jusqu'à la
décision »** (décider vite + restitution). La FAQ globale et la page pilier renvoient
désormais vers l'article canonique sur le nombre d'entretiens : une question, une page.

⚠️ Signatures : TN (quali/quanti), CC (entretiens, B2B), VJ (test de concept),
VB (restitution). Chacun relit et valide ce qui porte son nom avant publication.

## Décision rapide

Un **socle** qui ne bouge jamais — cadrage, recrutement, terrain, transcripts
intégraux — et des **livrables en options** : plateforme verbatim, top lines,
analyse complète, typologies, atelier de décision.

Le configurateur qualifie le besoin en quatre questions (décision, secteur, terrain,
livrables) et renvoie le dispositif recommandé, son calendrier par phases et la liste
exacte des livrables. Le secteur pré-règle le terrain tant que le visiteur n'a pas
réglé lui-même le paramètre concerné.

### ⚠️ Les prix ne sont pas publics

Décision prise en réunion : les tarifs varient d'un client à l'autre et s'annoncent
en rendez-vous, pas sur le web. **Le configurateur n'affiche aucun montant à un
visiteur.** Il produit un schéma, un calendrier et des livrables, et renvoie vers un
chiffrage sous 48 h.

Un **mode présentation** existe pour les rendez-vous :
`decision-rapide.html?interne=1`, ou <kbd>Ctrl</kbd>/<kbd>⌘</kbd> + <kbd>Alt</kbd> + <kbd>P</kbd>.
Un bandeau s'affiche en bas à gauche tant qu'il est actif, et le mode ne survit pas
à la fermeture de l'onglet.

**La grille de prix est provisoire** : elle vit dans l'objet `TARIFS` en tête de
`decision-rapide.js`, chaque ligne commentée. C'est un ordre de grandeur à remplacer
par la vraie grille — et, à ce moment-là, à sortir du JavaScript public.

## Contenus

Les pages de contenu ne s'écrivent pas à la main : elles sont **générées** par
`build_contenus.py`, qui tient le texte, le chrome (nav, pied de page), les balises
Open Graph et le JSON-LD. Corriger un article = éditer le script, puis :

```bash
python3 build_contenus.py
```

## Anatomie d'un article

Chaque article porte désormais, en plus du corps de texte :

- **Une à deux figures en SVG inline** par article, soit 14 au total — barres comparées,
  matrices 2×2, chaînes de maillons, jauges. Strictement monochrome, générées par `fig_barres()`, `fig_matrice()`,
  `fig_chaine()` et `fig_jauge()` dans `build_contenus.py`. Chacune porte un `<title>`
  (lu par les lecteurs d'écran, extrait par les moteurs) et une ancre `#fig-N`.

  ⚠️ Ces fonctions sont appelées **à la définition** des articles : elles doivent rester
  déclarées **avant** les listes `ARTICLES`, et le bloc `if __name__` **après**. Un corps
  d'article qui insère une figure doit fermer et rouvrir son triple guillemet
  (`""" + fig_chaine(…) + """`), sinon l'appel devient du texte littéral.

  Pour les vérifier sans navigateur (le pane se bloque au scroll) : extraire le `<svg>`,
  y inliner les valeurs de couleur, puis `qlmanage -t -s 1200 -o . fig.svg`.
- **Des bandeaux de chiffres sourcés** (`stats()`) — valeur, libellé, source datée.
- **Une FAQ de 3 à 5 questions**, balisée `FAQPage` et fusionnée avec l'`Article` dans
  un `@graph` : la page est une entité qui est à la fois un article et une FAQ.
- **Un bloc « Comment ACMÉ peut vous aider »** en pleine largeur, qui transforme la
  lecture en conversation — un article qui explique sans dire ce qu'on peut en faire
  ensemble laisse le lecteur au milieu du gué.
- **Un « Aller plus loin »** de trois liens internes.
- **Un bloc « Sources »** en pied.

Les trois études de cas portent en plus une section **« Ce que ça a changé »** :
décision engagée, ce qui a été évité, ce qui a été gagné, effet de levier. Aucun
chiffre d'affaires ni indicateur commercial n'y figure — ils appartiennent au client.

## Illustrations

`assets/illus/` — 15 bandeaux WebP et 2 boucles vidéo, ~1,7 Mo au total, tirés des
rushes ACMÉ (cassette, magnétophone, terminal, dessins annotés).

- **Le gris est baké à l'encodage** (`hue=s=0`), comme les vidéos du hero d'accueil :
  l'identité est monochrome, et un `filter: grayscale()` en CSS sortirait chaque image
  du chemin rapide du compositeur.
- **Un bandeau 1600×600 par article**, entre l'en-tête et le corps, en `loading="lazy"`
  avec `alt=""` — il est décoratif, une description redondante avec le titre n'apporte
  rien à un lecteur d'écran.
- **L'image Open Graph de chaque page est son propre bandeau** : un article partagé sur
  LinkedIn montre son visuel, pas le même pour tous.
- **Deux boucles vidéo** : le terminal qui écrit (hub Contenus) et les stylos qui
  annotent le corpus (livre blanc). Muettes, sans audio dans le fichier, relancées à
  l'entrée dans le viewport et **mises en pause hors champ** — inutile de décoder une
  image qu'on ne voit pas. Sous `prefers-reduced-motion`, elles s'arrêtent sur leur
  poster.

⚠️ **Ces rushes sont générés : le texte qui apparaît à l'écran est du charabia.** Il
faut choisir les plans où il n'est pas lisible — la première boucle du hub montrait un
gros plan parfaitement déchiffrable, elle a été retaillée sur le plan large de fin, en
aller-retour pour boucler sans raccord.

`ffmpeg` d'ici **n'a pas d'encodeur WebP** : extraire en PNG puis convertir avec `cwebp`.

## Le gabarit sectoriel

Les six articles `parcours-*.html` sont produits par une seule fonction,
`_parcours()`, à partir de la table `SECTEURS_PARCOURS`. Charpente commune,
contenu propre à chaque secteur.

⚠️ **Un gabarit amplifie tout, les faiblesses comprises.** Trois pièges payés
en le construisant :

- Les six pages partageaient **quatre questions de FAQ identiques** — six pages
  qui se disputent la même intention. Chaque secteur a désormais ses propres
  questions, dans la table.
- Le **premier titre de section** était le même partout (« Où se prend
  réellement la décision ? »). Il est maintenant paramétré (`h2_ou`).
- Une tournure faible dans le gabarit est répétée autant de fois qu'il y a de
  déclinaisons : un seul « c'est là que » y est devenu six.

Le contrôle à passer après toute modification du gabarit :

```bash
python3 ~/.claude/skills/redac-fr/scripts/tics.py . --html --strict
```

## La version anglaise

`en/` — quatre pages sur des **URL distinctes**, avec des `hreflang` réciproques
dans les deux sens.

⚠️ **Deux langues sur une même URL annuleraient tout le travail SEO** : un moteur
a besoin d'une URL par langue, et un moteur génératif qui cite une page a besoin
qu'elle soit dans une seule langue. La bascule FR/EN du chrome (i18n.js) reste
valable pour la nav et les pages d'offre ; elle ne convient pas au contenu
éditorial.

**Le périmètre est délibérément restreint.** Tout le terrain gagnable en
référencement est francophone — « focus group Lyon », « prix étude qualitative ».
Traduire les vingt-sept pages produirait un miroir que personne ne cherche. On
traduit ce qu'un prospect international lit vraiment : les trois articles
d'observatoire, qui sont les seuls à voyager par nature, plus leur index.

Les pages `en/` n'utilisent **aucun `data-i18n`** : leur texte est anglais en dur.
Elles alignent simplement `acme-lang` dans le `localStorage` pour que la bascule du
reste du site suive.

Ajouter une page anglaise : une entrée dans `ARTICLES_EN`, plus une ligne dans
`EN_ALTERNATES` pour que la page française la déclare.

## Titres, signatures, cocon

**Le `<title>` et le `<h1>` ne font pas le même travail.** Le premier est formulé
comme la requête et travaille en SERP&nbsp;; le second s'adresse à quelqu'un qui vient
d'arriver. Les deux sont désormais distincts sur les 22 articles — auparavant le h1
répétait le titre, et les six parcours sectoriels portaient six fois la même formule.

**Les articles sont signés.** Quatre consultants, attribués par compétence réelle
d'après les bios de `qui-sommes-nous.html`, avec un `author: Person` dans le JSON-LD.
⚠️ **Chaque consultant doit relire et valider les articles qui portent sa signature
avant publication** — une signature engage une personne.

**Le cocon sémantique est tenu par le code, pas par la discipline.** L'arbre vit dans
`COCONS` : une page cible par silo, des branches, des feuilles. `liens_cocon()`
construit le bloc « aller plus loin » à partir de l'arbre — le parent et les frères de
la même branche, jamais une page d'un autre silo. Huit silos, 32 pages, deux niveaux
sous la cible.

Le contrôle, à passer après tout ajout de page :

```python
# liens structurels franchissant un silo — doit rester à 0
python3 - <<'EOF'
import re, glob, importlib.util
spec = importlib.util.spec_from_file_location('bc', 'build_contenus.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for f in glob.glob('*.html'):
    b = re.search(r'<section class="art-loin">.*?</section>', open(f, encoding='utf-8').read(), re.S)
    if not b: continue
    mine = m.cocon_de(f)
    for u in re.findall(r'<a href="([^"#]+)"', b.group(0)):
        o = m.cocon_de(u)
        if mine and o and mine[0] != o[0]: print('HORS SILO', f, '->', u)
EOF
```

Les liens **en pleine prose restent libres** : ils sont contextuels, un lecteur les
suit, et les contraindre appauvrirait le texte. Ce qui est tenu, c'est le bloc
structurel de fin — celui qui porte le signal.

## SEO / GEO

Balisage en place sur **les 25 pages** : `Organization` + `ProfessionalService` partout
(posé sur les pages préexistantes par `build_head_seo.py`), plus `Article`, `FAQPage`,
`CollectionPage`, `Service` et `BreadcrumbList` selon le type. Open Graph et `canonical`
partout. Le site n'avait aucune donnée structurée.

Les articles **citent leurs sources en ligne et en pied de page**. C'est la tactique la
mieux mesurée en GEO : le travail fondateur sur le sujet (arXiv:2311.09735) situe à
**+30 à 40 %** le gain des trois méthodes « citer des sources », « ajouter des citations »
et « ajouter des statistiques », là où la mise en forme seule a un effet faible.

Deux outils tiennent la qualité, dans les skills `geo-seo` et `redac-fr` :

```bash
python3 ~/.claude/skills/geo-seo/scripts/audit.py .
python3 ~/.claude/skills/redac-fr/scripts/tics.py . --html --strict
```

⚠️ **Toutes les pages sont en `noindex` et `robots.txt` porte `Disallow: /`.** C'est
délibéré tant que c'est une maquette — mais rien ne peut se positionner tant que ce
verrou est en place. C'est une date à fixer, pas une option.

Les études de cas sont **anonymisées** : dispositif réel, client jamais nommé, aucun
résultat chiffré. Les nommer suppose l'accord écrit du client.

## Chiffres

Les nouvelles pages n'emploient **aucun** des chiffres non documentés de la maquette
(« 50 ans », « 3 500 projets », « 400+ études », « 98 % »). L'ancien site
acmeconsultants.fr annonce « +40 ans » et « +4 000 études » — les deux séries ne sont
pas compatibles et la question doit être tranchée avant mise en ligne. Le pied de page
hérité dit encore « 50 ans » : à corriger sur l'ensemble du site.

## Lancer en local

```bash
node server.js
```

Puis <http://localhost:4321>. Le serveur node répond en `206 Partial Content`, ce qui
est **nécessaire** au hero scrollé : sa vidéo est seekée en continu par le scroll, et
`python -m http.server` n'implémente pas les requêtes `Range`.

## Statut

Maquette de travail, `noindex` sur toutes les pages — délibéré. Le site en production
reste [acmeconsultants.fr](https://acmeconsultants.fr/).
