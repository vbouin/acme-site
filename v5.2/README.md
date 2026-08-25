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
| 5 articles | [focus group Lyon](article-focus-group-lyon.html) · [IA et quali](article-ia-etudes-qualitatives.html) · [prix](article-prix-etude-qualitative.html) · [entretiens ou groupes](article-entretiens-ou-groupes.html) · [décider vite](article-decider-vite.html) |
| 3 études de cas anonymisées | [utilitaire & artisans](cas-utilitaire-artisans.html) · [clinique électrique](cas-clinique-electrique.html) · [fichier client](cas-fichier-client-materiaux.html) |
| Livre blanc, 7 chapitres | [/v5.2/livre-blanc.html](livre-blanc.html) |
| FAQ, 22 questions | [/v5.2/faq.html](faq.html) |

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

Balisage en place sur les 11 nouvelles pages : `Organization` + `ProfessionalService`
partout, plus `Article`, `FAQPage`, `CollectionPage` et `BreadcrumbList` selon le type
— le site n'avait aucune donnée structurée, ce qui pénalisait le SEO local comme la
citation par les moteurs génératifs.

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
