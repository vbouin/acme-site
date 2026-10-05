# Husky Descent

Jeu isométrique en une seule page (`index.html`, aucune dépendance) : le héros descend un canal, l'élève touche
le côté gauche ou droit de l'écran pour choisir la bonne réponse (noms d'animaux et adjectifs, français ou anglais).
La descente est infinie, de fontaine en fontaine ; le bouton Menu met en pause, permet de reprendre ou de terminer avec un bilan.
La qualité d'affichage s'adapte toute seule si l'écran peine (textures, reflets, brume retirés en premier).

## Extraits Wikipédia réels

Les fiches utilisent par défaut un texte court écrit pour le jeu (à vérifier). Pour les remplacer par de vrais
extraits de Wikipédia (API REST officielle, licence CC BY-SA 4.0, source et licence affichées dans le jeu) :

    python3 husky-descent/fetch_fiches.py husky-descent/index.html

Il faut que `fr.wikipedia.org` et `en.wikipedia.org` soient joignables. Le script garde 2 ou 3 phrases entières,
ignore les pages d'homonymie et ne modifie rien si le réseau est bloqué. Test hors réseau : `--mock fichier.json`.

## Mode zoo

Les étoiles gagnées pendant la descente (bonne réponse du premier coup) servent de monnaie dans « Mon zoo » :
adopter un animal, débloquer un enclos, soigner, améliorer l'abri. Chaque animal a un tempérament parmi huit
(gourmand, joueur, timide, paresseux, curieux, fier, câlin, énergique) qui change ses besoins, ses déplacements
et ses répliques. Actions : nourrir (remplit la gamelle, l'animal vient manger), soigner, nettoyer, jouer, caresser, loger.
La progression est enregistrée dans le navigateur ; absent, l'animal vieillit très doucement et ne risque rien.
Les régimes, tempéraments et habitats sont des choix de jeu simplifiés, pas des données scientifiques.
