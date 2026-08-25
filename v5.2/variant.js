/* variant.js — site consolidé sur la variante v3.1 (grille révélée + hero auto-cycle).
 * Idempotent : sûr à inclure sur des pages qui appliquent déjà la classe/feuille en dur. */
(function () {
  // 1. Appliquer la classe de variante (si absente)
  document.body.classList.add('v3', 'v3-1');

  // 2. Charger la feuille de style v3 (si un <link> n'existe pas déjà)
  if (!document.querySelector('link[rel="stylesheet"][href*="styles-v3.css"]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'styles-v3.css';
    document.head.appendChild(link);
  }

})();
