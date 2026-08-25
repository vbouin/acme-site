/* ================================================================
   ACMÉ — moteur de séquences scrollées (v4.x)
   ----------------------------------------------------------------
   Toute section portant [data-act] devient une séquence : sa vidéo est
   scrubbée par le scroll, ses légendes s'allument sur des fenêtres de
   progression, et sa progression est publiée en CSS via --p.

   Trois règles tenues par ce fichier :

   1. UNE SEULE boucle rAF, et elle sort tôt. Rien n'est calculé dans un
      écouteur de scroll, et une frame où rien n'a bougé ne fait rien.
   2. AUCUNE lecture de layout dans la boucle. Les géométries (hauteur du
      document, position des pistes, hauteur du hero) sont mesurées une fois
      et réinvalidées au resize — la progression est ensuite de l'arithmétique
      sur scrollY.
   3. AUCUNE écriture DOM redondante. Tout passe par setVar/setText/setAttr,
      qui comparent à la dernière valeur écrite. Une propriété custom réécrite
      à l'identique invalide quand même le style du sous-arbre.

   Le rendu, lui, est décrit en CSS à partir de --p (parallaxe, poussée
   d'objectif, césure demi-écran) : ce fichier ne fabrique pas de transform.
   --p est quantifié au centième, ce qui suffit au sous-pixel et divise par
   ~10 le nombre de recalculs de la grille demi-écran.

   Les vidéos scrubbées sont encodées toutes-images-clés (-g 1) et déjà en
   gris : sans keyframes le seek saccade, et un filter:grayscale() sortirait
   chaque image du chemin rapide vidéo du compositeur.
   ================================================================ */
(function () {
  'use strict';

  var ACTS = [].slice.call(document.querySelectorAll('[data-act]'));
  var hero = document.querySelector('.v4-hero');
  if (!ACTS.length && !hero) return;

  var CALM = matchMedia('(prefers-reduced-motion: reduce)');
  var clamp = function (v, a, b) { return v < a ? a : v > b ? b : v; };
  var lerp = function (a, b, t) { return a + (b - a) * t; };
  var pad2 = function (n) { return String(n).padStart(2, '0'); };
  /* timecode SMPTE — la cadence vient du média, pas d'une constante ici */
  var timecode = function (t, fps) {
    return '00:' + pad2(Math.floor(t / 60) % 60) + ':' + pad2(Math.floor(t) % 60) +
           ':' + pad2(Math.floor((t % 1) * fps));
  };

  /* ── écritures DOM idempotentes ─────────────────────────────────── */
  var last = new WeakMap();
  function memo(el, key, val) {
    var m = last.get(el);
    if (!m) { m = {}; last.set(el, m); }
    if (m[key] === val) return false;
    m[key] = val;
    return true;
  }
  function setVar(el, prop, val) { if (el && memo(el, prop, val)) el.style.setProperty(prop, val); }
  function setText(el, val) { if (el && memo(el, 'text', val)) el.textContent = val; }
  function setAttr(el, name, val) { if (el && memo(el, '@' + name, val)) el.setAttribute(name, val); }
  function setOn(el, on) { if (el && memo(el, 'on', on)) el.classList.toggle('on', on); }

  /* ════════════════════════════════════════════════════════════════
     1. HERO EN PLAN FIXE (v4.2) — lecture en boucle + timecode
     ════════════════════════════════════════════════════════════════ */
  var heroVid = hero && hero.querySelector('video');
  var heroTc = hero && hero.querySelector('[data-tc]');
  var heroFps = heroTc ? +heroTc.getAttribute('data-fps') || 24 : 24;
  var heroPP = hero && hero.querySelector('.v4-pp');

  if (heroVid) {
    heroVid.muted = true;
    var wantPlay = !CALM.matches;
    var setKey = function () { if (heroPP) setText(heroPP, heroVid.paused ? '▶ Play' : '❙❙ Pause'); };
    var tryPlay = function () {
      if (!wantPlay) return;
      var pr = heroVid.play();
      if (pr && pr.catch) pr.catch(function () {});
    };
    heroVid.addEventListener('timeupdate', function () {
      setText(heroTc, timecode(heroVid.currentTime, heroFps));
    });
    if (heroPP) heroPP.addEventListener('click', function () {
      if (heroVid.paused) { wantPlay = true; tryPlay(); } else { wantPlay = false; heroVid.pause(); }
      setKey();
    });
    if (CALM.addEventListener) CALM.addEventListener('change', function () {
      wantPlay = !CALM.matches;
      wantPlay ? tryPlay() : heroVid.pause();
      setKey();
    });
    tryPlay();
    setKey();
  }

  /* ════════════════════════════════════════════════════════════════
     2. SÉQUENCES SCRUBBÉES
     ════════════════════════════════════════════════════════════════ */
  var acts = ACTS.map(function (el) {
    var video = el.querySelector('video[data-scrub]');
    var tcEl = el.querySelector('[data-tc]');
    var o = {
      el: el,
      track: el.querySelector('.v4-act-track') || el,
      video: video,
      fps: tcEl ? +tcEl.getAttribute('data-fps') || 24 : 24,
      tc: tcEl,
      beats: [].slice.call(el.querySelectorAll('[data-from]')).map(function (b) {
        return { el: b, from: +b.getAttribute('data-from'), to: +(b.getAttribute('data-to') || 1) };
      }),
      chapters: [].slice.call(el.querySelectorAll('[data-at]')).map(function (c) {
        return { el: c, at: +c.getAttribute('data-at') };
      }),
      fill: el.querySelector('.v4-act-meter .rail b'),
      pct: el.querySelector('[data-pct]'),
      morph: el.querySelector('.v4-morph-wrap'),
      edge: el.querySelector('.v4-morph-edge'),
      near: false, primed: false, chapter: -1, cur: 0, top: 0, span: 1
    };
    if (video) { video.muted = true; video.setAttribute('playsinline', ''); video.pause(); }
    return o;
  });

  /* Un seul observateur pour toutes les pistes. À l'approche on promeut le
     préchargement : le média hors écran ne se télécharge pas au chargement
     de la page (5 Mo de séquences sous la ligne de flottaison), et il a ~30vh
     d'avance pour arriver prêt. */
  if ('IntersectionObserver' in window) {
    var byTrack = new WeakMap();
    acts.forEach(function (o) { byTrack.set(o.track, o); });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var o = byTrack.get(e.target);
        if (!o) return;
        o.near = e.isIntersecting;
        if (e.isIntersecting && o.video && o.video.preload !== 'auto') {
          o.video.preload = 'auto';
          o.video.load();
        }
      });
    }, { rootMargin: '30% 0px 30% 0px' });
    acts.forEach(function (o) { io.observe(o.track); });
  } else {
    acts.forEach(function (o) { o.near = true; });
  }

  /* iOS/Safari : une vidéo jamais lue ne peint pas toujours sur un seek.
     Un play() muet suivi d'un pause() amorce le décodeur. */
  function prime(o) {
    if (o.primed || !o.video) return;
    o.primed = true;
    var pr = o.video.play();
    if (pr && pr.then) pr.then(function () { o.video.pause(); }).catch(function () {});
    else o.video.pause();
  }

  function drawAct(o, y, vh) {
    var p = o.span > 0 ? clamp((y - o.top) / o.span, 0, 1) : (y >= o.top ? 1 : 0);

    // --p : le contrat JS → CSS. Quantifié au centième : la parallaxe et la
    // poussée d'objectif restent sous le pixel, et la grille demi-écran ne se
    // recalcule qu'une centaine de fois par acte au lieu d'une par frame.
    setVar(o.el, '--p', p.toFixed(2));

    if (o.fill) setVar(o.fill, '--fill', p.toFixed(3));
    if (o.pct) setText(o.pct, ('00' + Math.round(p * 100)).slice(-3));

    // essuyage croquis → objet : fenêtre resserrée pour que l'image finale
    // tienne à l'écran avant que la section ne sorte
    if (o.morph) {
      var w = clamp((p - 0.14) / 0.62, 0, 1);
      setVar(o.morph, '--wipe', (w * 100).toFixed(1) + '%');
      setOn(o.edge, w > 0.004 && w < 0.996);
    }

    for (var i = 0; i < o.beats.length; i++) {
      var b = o.beats[i];
      setOn(b.el, p >= b.from && p <= b.to);
    }

    if (o.chapters.length) {
      var cur = 0;
      for (var c = 0; c < o.chapters.length; c++) if (p >= o.chapters[c].at) cur = c;
      if (cur !== o.chapter) {
        if (o.chapter >= 0) o.chapters[o.chapter].el.classList.remove('on');
        o.chapters[cur].el.classList.add('on');
        o.chapter = cur;
      }
    }

    // tête de lecture — lissée pour absorber les à-coups de la molette
    if (o.video && o.video.readyState >= 1) {
      var dur = o.video.duration;
      if (dur && isFinite(dur)) {
        var target = p * (dur - 0.04);
        o.cur = Math.abs(target - o.cur) < 0.004 ? target : lerp(o.cur, target, 0.2);
        try { o.video.currentTime = o.cur; } catch (e) { /* seek pas encore possible */ }
        setText(o.tc, timecode(o.cur, o.fps));
        return Math.abs(target - o.cur) > 0.004;   // encore en train de rattraper
      }
    }
    return false;
  }

  /* ════════════════════════════════════════════════════════════════
     3. TRANSPORT — bobines, piste courante, progression de page
     ════════════════════════════════════════════════════════════════ */
  var TRACKS = [].slice.call(document.querySelectorAll('[data-track]'));
  var transport = null, drawTransport = null;

  if (!CALM.matches && TRACKS.length) {
    transport = document.createElement('div');
    transport.className = 'v4-transport';
    transport.setAttribute('aria-hidden', 'true');
    /* une seule bobine décrite, la seconde est un <use> : la géométrie et les
       rayons vivent en un seul endroit (REEL_FULL/REEL_EMPTY/RUN ci-dessous) */
    transport.innerHTML =
      '<svg viewBox="0 0 74 34" role="presentation">' +
        '<defs><g id="v4reel" stroke="#F5F5F3" stroke-width="1.1" fill="none">' +
          '<circle cx="17" cy="15" r="4.6"/>' +
          '<path d="M17 10.4V19.6M12.4 15h9.2M13.7 11.7l6.6 6.6M20.3 11.7l-6.6 6.6"/>' +
        '</g></defs>' +
        '<circle class="tape-l" cx="17" cy="15" r="13" fill="#1A1A1A" opacity=".82"/>' +
        '<circle class="tape-r" cx="57" cy="15" r="5.2" fill="#1A1A1A" opacity=".82"/>' +
        '<use class="v4-reel-spin spin-l" href="#v4reel"/>' +
        '<use class="v4-reel-spin spin-r" href="#v4reel" x="40"/>' +
        '<path d="M6 31H68" stroke="#DDD" stroke-width="1.5"/>' +
        '<path class="tape-run" d="M6 31H68" stroke="#0A0A0A" stroke-width="1.5" ' +
              'stroke-dasharray="62" stroke-dashoffset="62"/>' +
      '</svg>' +
      '<div class="meta"><b data-tname></b><span data-tnum></span></div>' +
      '<div class="mode" data-mode>▶▶ FF</div>';
    document.body.appendChild(transport);

    var pageLine = document.createElement('div');
    pageLine.className = 'v4-tape-line';
    pageLine.setAttribute('aria-hidden', 'true');
    document.body.appendChild(pageLine);

    var spinL = transport.querySelector('.spin-l');
    var spinR = transport.querySelector('.spin-r');
    var tapeL = transport.querySelector('.tape-l');
    var tapeR = transport.querySelector('.tape-r');
    var tapeRun = transport.querySelector('.tape-run');
    var tName = transport.querySelector('[data-tname]');
    var tNum = transport.querySelector('[data-tnum]');
    var modeChip = transport.querySelector('[data-mode]');

    var REEL_FULL = 13, REEL_EMPTY = 5.2, RUN = 62;
    var angle = 0, modeUntil = 0, curTrack = -1;

    /* le libellé de piste suit la langue : le HUD ne doit pas rester en
       français quand le reste de la page passe en anglais */
    var trackLabel = function (el) {
      var en = document.documentElement.lang === 'en' && el.getAttribute('data-track-en');
      return en || el.getAttribute('data-track');
    };
    addEventListener('languagechange', function () {
      if (curTrack >= 0) setText(tName, trackLabel(TRACKS[curTrack]));
    });

    drawTransport = function (now, y, dy, vh, docSpan, tops) {
      var page = docSpan > 0 ? clamp(y / docSpan, 0, 1) : 0;

      // les bobines tournent AVEC le scroll : remonter les fait tourner à l'envers
      if (dy) {
        angle += dy * 0.42;
        setVar(spinL, '--a', angle.toFixed(1) + 'deg');
        setVar(spinR, '--a', (angle * 1.35).toFixed(1) + 'deg');
      }
      // la bande passe d'une bobine à l'autre
      setAttr(tapeL, 'r', lerp(REEL_FULL, REEL_EMPTY, page).toFixed(2));
      setAttr(tapeR, 'r', lerp(REEL_EMPTY, REEL_FULL, page).toFixed(2));
      setAttr(tapeRun, 'stroke-dashoffset', (RUN * (1 - page)).toFixed(1));
      setVar(pageLine, '--page', page.toFixed(4));
      setOn(transport, y > vh * 0.55);

      // FF / REW quand on défile vite
      if (Math.abs(dy) > 26) {
        setText(modeChip, dy > 0 ? '▶▶ FF' : '◀◀ REW');
        modeUntil = now + 620;
      }
      if (memo(modeChip, 'live', now < modeUntil)) modeChip.classList.toggle('on', now < modeUntil);

      // piste courante : dernière dont le haut a passé le tiers haut de l'écran
      var mark = y + vh * 0.34, idx = 0;
      for (var i = 0; i < tops.length; i++) if (tops[i] <= mark) idx = i;
      if (idx !== curTrack) {
        curTrack = idx;
        setText(tName, trackLabel(TRACKS[idx]));
        setText(tNum, pad2(idx + 1) + ' / ' + pad2(TRACKS.length));
      }

      // l'étiquette (marquee) suit le sens et la vitesse du scroll
      if (Math.abs(dy) > 2) {
        setVar(document.body, '--mq-dir', dy > 0 ? 'normal' : 'reverse');
        setVar(document.body, '--mq-dur', clamp(40 - Math.abs(dy) * 0.7, 12, 40).toFixed(0) + 's');
      }
      return now < modeUntil;   // la puce FF/REW doit encore s'éteindre
    };
  }

  /* ════════════════════════════════════════════════════════════════
     4. GÉOMÉTRIES — mesurées hors boucle, réinvalidées au resize
     ════════════════════════════════════════════════════════════════ */
  var vh = 0, docSpan = 0, heroH = 1, tops = [];

  function measure() {
    vh = innerHeight;
    docSpan = document.documentElement.scrollHeight - vh;
    heroH = hero ? hero.offsetHeight || 1 : 1;
    tops = TRACKS.map(function (el) { return el.getBoundingClientRect().top + scrollY; });
    acts.forEach(function (o) {
      var r = o.track.getBoundingClientRect();
      o.top = r.top + scrollY;
      o.span = r.height - vh;
    });
  }

  var remeasure = null;
  function scheduleMeasure() {
    if (remeasure) cancelAnimationFrame(remeasure);
    remeasure = requestAnimationFrame(function () { remeasure = null; measure(); dirty = true; });
  }
  addEventListener('resize', scheduleMeasure, { passive: true });
  addEventListener('load', scheduleMeasure);
  if ('ResizeObserver' in window) new ResizeObserver(scheduleMeasure).observe(document.body);
  measure();

  /* ════════════════════════════════════════════════════════════════
     5. LA BOUCLE — une seule, et elle sort tôt
     ════════════════════════════════════════════════════════════════ */
  requestAnimationFrame(function () {
    requestAnimationFrame(function () { document.body.classList.add('v4-open'); });
  });

  if (CALM.matches) {
    // mouvement réduit : état final posé une fois, pas de boucle
    acts.forEach(function (o) {
      o.beats.forEach(function (b) { b.el.classList.add('on'); });
      o.chapters.forEach(function (c) { c.el.classList.add('on'); });
      if (o.morph) o.morph.style.setProperty('--wipe', '100%');
    });
    return;
  }

  var lastY = -1, dirty = true;
  function tick(now) {
    var y = scrollY;
    var dy = y - (lastY < 0 ? y : lastY);
    // une frame où rien n'a bougé ne fait rien : sur une page lue à l'arrêt,
    // c'est ~90 % du travail qui disparaît
    if (dy !== 0 || dirty) {
      dirty = false;
      lastY = y;
      if (drawTransport && drawTransport(now, y, dy, vh, docSpan, tops)) dirty = true;
      if (hero) setVar(hero, '--p', clamp(y / heroH, 0, 1).toFixed(2));
      for (var i = 0; i < acts.length; i++) {
        if (!acts[i].near) continue;
        prime(acts[i]);
        if (drawAct(acts[i], y, vh)) dirty = true;   // la tête de lecture rattrape encore
      }
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
})();
