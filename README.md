# ACMÉ — prototype de refonte

Plusieurs variantes du même site vivent dans ce dossier, commutables par la pilule
en bas à droite de chaque page (`variant.js`) :

| variante | fichier | parti pris |
|---|---|---|
| **v5.2** | **[`v5.2/`](v5.2/)** | **site complet — Décision rapide (configurateur) + Contenus (blog, cas, livre blanc, FAQ)** |
| v1 | `index.html` | base mono editorial |
| v2 | `index-v2.html` | curseur personnalisé |
| v3 | `index-v3.html` | grille révélée au curseur |
| v3.1 | `index-v3-1.html` | v3 + hero auto-cycle des deux animations |
| **v4.2** | `index-v4-2.html` | **« La bande »** — hero magnétophone + 4 actes scrubbés au scroll |
| **v4.3** | `index-v4-3.html` | **« Le démontage »** — le hero devient une séquence continue de 17,3 s |

## v5.2 — le site complet

`v5.2/` n'est pas une variante de hero&nbsp;: c'est le **site entier**, repris de la
maquette consolidée et augmenté de deux onglets.

### **[→ Ouvrir v5.2](https://vbouin.github.io/acme-site/v5.2/)**

- **Décision rapide** — l'offre courte (socle terrain + livrables en options) avec un
  configurateur de dispositif. **Aucun prix n'est affiché à un visiteur** ; un mode
  présentation (`?interne=1`) montre une fourchette indicative en rendez-vous.
- **Contenus** — 5 articles, 3 études de cas anonymisées, un livre blanc et une FAQ de
  22 questions, avec Open Graph et JSON-LD (`Article`, `FAQPage`, `Organization`,
  `BreadcrumbList`) sur toutes les pages.

Les pages de contenu sont générées par `v5.2/build_contenus.py` — le texte vit dans le
script, jamais dans le HTML. Détails dans [`v5.2/README.md`](v5.2/README.md).

## Lancer

```bash
node server.js 4325     # puis http://localhost:4325/index-v4-3.html
```

**Le serveur node est nécessaire pour v4.x** : les vidéos sont scrubbées au scroll,
donc seekées en continu, et `python -m http.server` n'implémente pas les requêtes
`Range` — sans elles le scrub dépend du buffer complet et saccade. `server.js`
répond en 206 et met `assets/` en cache.

## Les variantes v4 en deux idées

**1. Le fond de chaque section reprend le fond réel de sa vidéo.** Les valeurs des
`--plate-*` sont relevées aux quatre coins des rushes. Du coup le média n'a besoin
d'être estompé que sur le bord qui rencontre la typo : plus de « vignette vidéo »,
le studio continue dans la page. Les recettes d'estompage sont nommées
(`--fade-l`, `--fade-r`, `--fade-tb`, `--fade-b`, `--fade-off`) et chaque contexte
choisit la sienne.

> ⚠️ Ne pas paramétrer ces recettes par un angle : la valeur calculée d'une
> propriété custom substitue ses `var()` **là où elle est déclarée**. Un
> `--fade-in: linear-gradient(var(--angle), …)` posé sur `body` reste figé à
> l'angle du body, quoi qu'on redéfinisse plus bas.

**2. Le scroll est la tête de lecture.** `acts.js` pilote toute section portant
`data-act` : il scrubbe sa vidéo, allume ses légendes sur des fenêtres de
progression (`data-from` / `data-to`), et publie la progression en CSS via `--p`.
Parallaxe, poussée d'objectif, césure demi-écran et letterbox sont des `calc()`
sur `--p` — une seule valeur traverse la frontière JS/CSS.

Le moteur tient trois règles : une seule boucle rAF **qui sort tôt** si rien n'a
bougé ; **aucune lecture de layout dans la boucle** (les géométries sont mesurées
au resize) ; **aucune écriture DOM redondante**.

Les vidéos scrubbées sont encodées **toutes-images-clés** (`-g 1`) et **déjà en
gris** — sans keyframes chaque seek repart du GOP précédent, et un
`filter: grayscale()` sortirait chaque image du chemin rapide du compositeur.

## Régénérer

Les pages v4 ne s'écrivent pas à la main : elles dérivent par substitutions
ancrées, chaque ancrage sous `assert` (un ancrage qui bouge casse le build au lieu
de produire une page incomplète).

```bash
python3 build_v42.py            # index-v3-1.html  → index-v4-2.html
python3 build_v43.py            # régénère v4.2, puis en dérive v4.3
python3 export_standalone.py all  # → ACME-v4.2/4.3-autoportant.html
```

`export_standalone.py` produit **un seul fichier HTML par variante, sans aucune
requête réseau** (CSS, JS, médias et polices inlinés) : à double-cliquer, y compris
hors ligne. Il retire au passage three.js et ses dix boucles WebGL toujours
actives, la pilule de variantes et les liens vers les pages sœurs.

## Textes

Tout passe par `data-i18n` et `i18n.js` (FR / EN, 363 clés de chaque côté).
