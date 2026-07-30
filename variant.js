/* variant.js — single source of truth for variant styling across the whole site.
 *
 * Every per-variant fact lives in ONE row of VARIANTS: which file selects it,
 * which body classes it wears, which stylesheets it needs, which overlay
 * elements it injects, and how the toggle labels it. Detection, application and
 * the pill are all derived from that table — adding a variant is adding a row,
 * not editing four parallel if-chains. Inheritance (v3.1 keeps v3, v4.3 keeps
 * v4.2) is therefore data you can read, not a prefix match to decode.
 *
 * Idempotent: safe to include on home pages that already hardcode their variant.
 */
(function () {
  const V3_OVERLAYS = ['v3-grid-base', 'v3-reveal', 'v3-dot'];

  const VARIANTS = [
    { k: 'v1',   file: 'index.html',      label: 'v1',   body: [],                  css: [],                                        overlays: [] },
    { k: 'v2',   file: 'index-v2.html',   label: 'v2',   body: ['v2'],              css: ['styles-v2.css'],                         overlays: ['v2-cursor'] },
    { k: 'v3',   file: 'index-v3.html',   label: 'v3',   body: ['v3'],              css: ['styles-v3.css'],                         overlays: V3_OVERLAYS },
    { k: 'v3-1', file: 'index-v3-1.html', label: 'v3.1', body: ['v3', 'v3-1'],      css: ['styles-v3.css'],                         overlays: V3_OVERLAYS },
    { k: 'v4-2', file: 'index-v4-2.html', label: 'v4.2', body: ['v4-2'],            css: ['styles-v4-2.css'],                       overlays: [] },
    { k: 'v4-3', file: 'index-v4-3.html', label: 'v4.3', body: ['v4-2', 'v4-3'],    css: ['styles-v4-2.css', 'styles-v4-3.css'],    overlays: [] },
  ];
  const DEFAULT = VARIANTS[0];

  // 1. Detect from the URL (home pages) or localStorage (secondary pages)
  const file = window.location.pathname.split('/').pop() || 'index.html';
  let active = VARIANTS.find((v) => v.file === file);
  if (!active) {
    let stored = null;
    try { stored = localStorage.getItem('acme-variant'); } catch (_) {}
    active = VARIANTS.find((v) => v.k === stored) || DEFAULT;
  }

  // 2. Persist, so secondary-page nav inherits the variant
  try {
    if (active === DEFAULT) localStorage.removeItem('acme-variant');
    else localStorage.setItem('acme-variant', active.k);
  } catch (_) {}

  // 3. Body classes (classList.add is idempotent)
  if (active.body.length) document.body.classList.add(...active.body);

  // 4. Stylesheets, in declared order
  active.css.forEach((href) => {
    if (document.querySelector(`link[rel="stylesheet"][href*="${href}"]`)) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    document.head.appendChild(link);
  });

  // 5. Overlay elements
  active.overlays.forEach((cls) => {
    if (document.querySelector('.' + cls)) return;
    const el = document.createElement('div');
    el.className = cls;
    el.setAttribute('aria-hidden', 'true');
    document.body.appendChild(el);
  });

  // 6. The variant toggle pill
  if (!document.querySelector('.v2-toggle')) {
    const wrap = document.createElement('div');
    wrap.className = 'v2-toggle';
    wrap.setAttribute('aria-label', 'Variant toggle');
    VARIANTS.forEach((v) => {
      const isActive = v === active;
      const node = document.createElement(isActive ? 'span' : 'a');
      node.className = isActive ? 'v2-current' : 'v2-link';
      if (!isActive) node.href = v.file;
      node.textContent = v.label;
      wrap.appendChild(node);
    });
    document.body.appendChild(wrap);
  }
})();
