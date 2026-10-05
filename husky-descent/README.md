# Husky Descent

Jeu isométrique en une seule page (`index.html`, aucune dépendance) : le héros descend un canal, l'élève touche
le côté gauche ou droit de l'écran pour choisir la bonne réponse (noms d'animaux et adjectifs, français ou anglais).

## Extraits Wikipédia réels

Les fiches utilisent par défaut un texte court écrit pour le jeu (à vérifier). Pour les remplacer par de vrais
extraits de Wikipédia (API REST officielle, licence CC BY-SA 4.0, source et licence affichées dans le jeu) :

    python3 husky-descent/fetch_fiches.py husky-descent/index.html

Il faut que `fr.wikipedia.org` et `en.wikipedia.org` soient joignables. Le script garde 2 ou 3 phrases entières,
ignore les pages d'homonymie et ne modifie rien si le réseau est bloqué. Test hors réseau : `--mock fichier.json`.
