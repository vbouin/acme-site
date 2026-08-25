/* =========================================================
   ACMÉ — Configurateur « Décision rapide »
   Vanilla, sans dépendance, bilingue via window.getLanguage().

   ⚠️  LES PRIX NE SONT JAMAIS AFFICHÉS PUBLIQUEMENT.
   Le panneau budget est masqué par CSS et ne s'ouvre qu'en
   « mode présentation » : ?interne=1 dans l'URL, ou Ctrl/Cmd + Alt + P.
   C'est la règle posée en réunion : le schéma se montre, le prix se
   discute en rendez-vous. Ne pas retirer ce garde-fou.
   ========================================================= */
(function () {
  'use strict';

  var form = document.querySelector('.dr-sim');
  if (!form) return;

  /* -------------------------------------------------------
     1. GRILLE TARIFAIRE — INTERNE, INDICATIVE, À CALER
     Ordres de grandeur de départ, à remplacer par la grille
     réelle. Tout est en euros HT.
     ------------------------------------------------------- */
  var TARIFS = {
    cadrage:            1200,   // cadrage de la question + guide d'entretien
    cadrageStimuli:      900,   // préparation des stimuli (concepts, visuels)
    cadrageProduit:     2400,   // logistique produit / mise en place clinique

    recrutParPersonne:   260,   // recrutement complet sur critères (repère marché : 200–300 €)
    recrutSurFichier:     90,   // qualification + prise de rendez-vous dans le fichier client

    indemniteEntretien:   60,   // indemnisation participant — entretien
    indemniteGroupe:      80,   // indemnisation participant — groupe

    entretienOnline:     320,   // conduite + captation, par entretien
    entretienPresentiel: 520,   // idem, avec déplacement et salle
    groupeOnline:       1400,   // par groupe de 2 h (6 participants)
    groupePresentiel:   2200,   // idem, avec salle et intendance

    transcriptParHeure:   12,   // transcription assistée + relecture humaine

    plateforme:         2500,
    toplines:           1800,
    rapport:            4800,
    typologies:         2200,
    atelier:            2800
  };

  /* -------------------------------------------------------
     2. PARAMÈTRES DE VOLUME PAR DISPOSITIF
     ------------------------------------------------------- */
  var VOLUMES = {
    entretiens: { min: 6, max: 30, def: 12 },
    groupes:    { min: 2, max: 8,  def: 4  },
    mixte:      { min: 6, max: 20, def: 10 }   // + 2 groupes systématiques
  };
  var GROUPES_EN_MIXTE = 2;
  var PAR_GROUPE = 6;                          // participants par groupe

  /* Capacité de terrain par semaine, en unités de charge
     (1 entretien = 1 unité, 1 groupe = 2,5 unités) */
  var CAPACITE = { online: 16, presentiel: 10, hybride: 12 };

  /* -------------------------------------------------------
     3. SECTEURS — pré-réglages et justification
     Le secteur pré-règle le terrain, tant que l'utilisateur
     n'a pas lui-même touché le réglage concerné.
     ------------------------------------------------------- */
  var SECTEURS = {
    mobilite:    { dispositif: 'entretiens', modalite: 'presentiel', materiel: 'produit' },
    fmcg:        { dispositif: 'groupes',    modalite: 'hybride',    materiel: 'stimuli' },
    sante:       { dispositif: 'entretiens', modalite: 'presentiel', materiel: 'aucun'   },
    batiment:    { dispositif: 'entretiens', modalite: 'online',     materiel: 'stimuli' },
    territoires: { dispositif: 'groupes',    modalite: 'hybride',    materiel: 'aucun'   },
    mode:        { dispositif: 'groupes',    modalite: 'presentiel', materiel: 'produit' }
  };

  /* -------------------------------------------------------
     4. TEXTES DYNAMIQUES (FR / EN)
     Les textes statiques passent par data-i18n ; ceux-ci sont
     assemblés en JS, donc ils vivent ici.
     ------------------------------------------------------- */
  var T = {
    fr: {
      unit: { entretiens: 'entretiens', groupes: 'groupes', mixte: 'entretiens + 2 groupes' },
      hint: { entretiens: 'Nombre d’entretiens', groupes: 'Nombre de groupes', mixte: 'Entretiens (deux groupes s’y ajoutent)' },
      phase: { cadrage: 'Cadrage', recrutement: 'Recrutement', terrain: 'Terrain', livrables: 'Livrables' },
      name: {
        terrain:    'Terrain seul',
        plateforme: 'Terrain & plateforme',
        toplines:   'Terrain & top lines',
        atelier:    'Terrain & atelier de décision',
        rapport:    'Étude resserrée',
        complet:    'Étude resserrée, jusqu’à la décision'
      },
      deliv: {
        guide:      'Guide d’entretien et grille d’analyse',
        terrain:    'Terrain conduit par un consultant senior',
        transcript: 'Transcripts intégraux, horodatés',
        plateforme: 'Plateforme verbatim interrogeable',
        toplines:   'Top lines — 5 à 8 pages',
        rapport:    'Analyse complète et argumentée',
        typologies: 'Typologies et figures du corpus',
        atelier:    'Atelier de décision animé (demi-journée)'
      },
      sub: {
        lancement:      'Objectif : savoir ce qui accroche et ce qui bloque avant d’engager la production.',
        pricing:        'Objectif : comprendre ce qui justifie le prix et où passe le seuil d’acceptation.',
        cible:          'Objectif : entendre les attentes réelles de la cible, dans ses propres mots.',
        positionnement: 'Objectif : vérifier ce que votre discours dit vraiment à ceux qui le reçoivent.',
        parcours:       'Objectif : repérer où le parcours casse, et ce que ça coûte à l’usage.',
        arbitrage:      'Objectif : faire trancher le terrain là où le comité ne tranche pas.'
      },
      sector: {
        mobilite:    'Sur ce secteur, les arbitrages se jouent devant l’objet : nous partons en clinique, en présentiel, produit ou maquette sous les yeux.',
        fmcg:        'Sur ce secteur, le rayon et le packaging demandent la confrontation : le groupe fait émerger ce que l’entretien seul n’attrape pas.',
        sante:       'Sur ce secteur, la parole est sensible : l’entretien individuel la protège, et le recrutement demande plus de temps.',
        batiment:    'Sur ce secteur, artisans et prescripteurs sont sur les chantiers : l’entretien à distance passe mieux qu’un déplacement en salle.',
        territoires: 'Sur ce secteur, la concertation vit du collectif : des groupes, en salle comme à distance, selon les publics.',
        mode:        'Sur ce secteur, la matière se touche : présentiel, avec les pièces sous la main.'
      },
      recrutNote: 'Recrutement dans votre fichier : nous qualifions et prenons les rendez-vous. C’est le poste le plus lourd d’un dispositif court — le retirer change l’équation, et raccourcit le calendrier d’une à deux semaines.',
      copyOk: 'Récapitulatif copié',
      copyFail: 'Copie impossible — sélectionnez le texte',
      recapTitle: 'DISPOSITIF — ACMÉ Décision rapide',
      lblDecision: 'Décision', lblSecteur: 'Secteur', lblTerrain: 'Terrain',
      lblModalite: 'Modalité', lblRecrut: 'Recrutement', lblMateriel: 'Matériel',
      lblVoix: 'Voix client', lblDuree: 'Durée estimée', lblLivrables: 'Livrables',
      semaines: 'semaines', heures: 'h de parole client',
      recrutBy: { acme: 'par ACMÉ', fichier: 'sur fichier client' },
      matLabel: { aucun: 'aucun', stimuli: 'concepts / visuels', produit: 'produit ou prototype' },
      modLabel: { online: 'à distance', presentiel: 'en présentiel', hybride: 'mixte' },
      decLabel: {
        lancement: 'Lancement produit', pricing: 'Prix & offre', cible: 'Attentes de la cible',
        positionnement: 'Positionnement', parcours: 'Parcours & expérience', arbitrage: 'Arbitrage entre options'
      },
      secLabel: {
        mobilite: 'Mobilité & Automobile', fmcg: 'Retail et FMCG', sante: 'Santé & Cosmétiques',
        batiment: 'Bâtiment', territoires: 'Territoires, Tourisme & RSE', mode: 'Mode & Luxe'
      }
    },
    en: {
      unit: { entretiens: 'interviews', groupes: 'groups', mixte: 'interviews + 2 groups' },
      hint: { entretiens: 'Number of interviews', groupes: 'Number of groups', mixte: 'Interviews (two groups are added)' },
      phase: { cadrage: 'Framing', recrutement: 'Recruitment', terrain: 'Fieldwork', livrables: 'Deliverables' },
      name: {
        terrain:    'Fieldwork only',
        plateforme: 'Fieldwork & platform',
        toplines:   'Fieldwork & top lines',
        atelier:    'Fieldwork & decision workshop',
        rapport:    'Focused study',
        complet:    'Focused study, through to the decision'
      },
      deliv: {
        guide:      'Discussion guide and analysis grid',
        terrain:    'Fieldwork run by a senior consultant',
        transcript: 'Full time-stamped transcripts',
        plateforme: 'Searchable verbatim platform',
        toplines:   'Top lines — 5 to 8 pages',
        rapport:    'Full, argued analysis',
        typologies: 'Typologies and corpus figures',
        atelier:    'Facilitated decision workshop (half-day)'
      },
      sub: {
        lancement:      'Goal: know what lands and what blocks before committing to production.',
        pricing:        'Goal: understand what justifies the price and where the acceptance threshold sits.',
        cible:          'Goal: hear what the target really expects, in their own words.',
        positionnement: 'Goal: check what your message actually says to the people receiving it.',
        parcours:       'Goal: find where the journey breaks, and what that costs in use.',
        arbitrage:      'Goal: let the field decide where the steering committee cannot.'
      },
      sector: {
        mobilite:    'In this sector the trade-offs happen in front of the object: we run a clinic, in person, with the product or model in view.',
        fmcg:        'In this sector shelf and packaging call for confrontation: groups surface what one-to-one interviews miss.',
        sante:       'In this sector speech is sensitive: one-to-one interviews protect it, and recruitment takes longer.',
        batiment:    'In this sector trades and prescribers are on site: remote interviews work better than a trip to a facility.',
        territoires: 'In this sector consultation lives on the collective: groups, in the room or remote, depending on the audience.',
        mode:        'In this sector the material has to be touched: in person, with the pieces at hand.'
      },
      recrutNote: 'Recruiting from your own file: we qualify and book the sessions. It is the heaviest line of a short study — removing it changes the equation, and cuts one to two weeks off the schedule.',
      copyOk: 'Summary copied',
      copyFail: 'Copy failed — select the text',
      recapTitle: 'STUDY DESIGN — ACMÉ Quick Decision',
      lblDecision: 'Decision', lblSecteur: 'Sector', lblTerrain: 'Fieldwork',
      lblModalite: 'Mode', lblRecrut: 'Recruitment', lblMateriel: 'Material',
      lblVoix: 'Customer voices', lblDuree: 'Estimated duration', lblLivrables: 'Deliverables',
      semaines: 'weeks', heures: 'h of customer speech',
      recrutBy: { acme: 'by ACMÉ', fichier: 'from client file' },
      matLabel: { aucun: 'none', stimuli: 'concepts / visuals', produit: 'product or prototype' },
      modLabel: { online: 'remote', presentiel: 'in person', hybride: 'mixed' },
      decLabel: {
        lancement: 'Product launch', pricing: 'Price & offer', cible: 'Target expectations',
        positionnement: 'Positioning', parcours: 'Journey & experience', arbitrage: 'Choosing between options'
      },
      secLabel: {
        mobilite: 'Mobility & Automotive', fmcg: 'Retail and FMCG', sante: 'Health & Cosmetics',
        batiment: 'Construction', territoires: 'Regions, Tourism & CSR', mode: 'Fashion & Luxury'
      }
    }
  };

  function t() { return T[(window.getLanguage && window.getLanguage()) === 'en' ? 'en' : 'fr']; }

  /* -------------------------------------------------------
     5. LECTURE DU FORMULAIRE
     ------------------------------------------------------- */
  var vol      = document.getElementById('dr-vol');
  var volVal   = document.getElementById('dr-vol-val');
  var volUnit  = document.getElementById('dr-vol-unit');
  var volHint  = document.getElementById('dr-vol-hint');
  var touched  = {};   // réglages que l'utilisateur a modifiés lui-même

  function pick(name) {
    var el = form.querySelector('input[name="' + name + '"]:checked');
    return el ? el.value : null;
  }
  function livrables() {
    return Array.prototype.map.call(
      form.querySelectorAll('input[name="liv"]:checked'), function (i) { return i.value; }
    );
  }

  function state() {
    var d = pick('dispositif');
    var n = parseInt(vol.value, 10);
    var groupes = d === 'groupes' ? n : (d === 'mixte' ? GROUPES_EN_MIXTE : 0);
    var entretiens = d === 'groupes' ? 0 : n;
    return {
      decision: pick('decision'),
      secteur: pick('secteur'),
      dispositif: d,
      n: n,
      entretiens: entretiens,
      groupes: groupes,
      modalite: pick('modalite'),
      recrutement: pick('recrutement'),
      materiel: pick('materiel'),
      liv: livrables(),
      participants: entretiens + groupes * PAR_GROUPE,
      heures: entretiens * 1 + groupes * 2
    };
  }

  /* -------------------------------------------------------
     6. CALCULS
     ------------------------------------------------------- */
  function calendrier(s) {
    var cadrage = 1 + (s.materiel === 'produit' ? 1 : 0);

    var recrutement = s.recrutement === 'fichier' ? 1 : 2;
    if (s.recrutement === 'acme' && (s.secteur === 'sante' || s.secteur === 'batiment')) recrutement += 1;

    var charge = s.entretiens * 1 + s.groupes * 2.5;
    if (s.materiel === 'produit') charge *= 1.3;
    var terrain = Math.max(1, Math.ceil(charge / CAPACITE[s.modalite]));

    var l = 0.5;
    if (s.liv.indexOf('plateforme') > -1) l += 0.5;
    if (s.liv.indexOf('toplines')   > -1) l += 0.5;
    if (s.liv.indexOf('rapport')    > -1) l += 1.5;
    if (s.liv.indexOf('typologies') > -1) l += 0.5;
    if (s.liv.indexOf('atelier')    > -1) l += 0.5;
    var livrablesW = Math.ceil(l);

    return {
      cadrage: cadrage, recrutement: recrutement, terrain: terrain, livrables: livrablesW,
      total: cadrage + recrutement + terrain + livrablesW
    };
  }

  function budget(s) {
    var p = TARIFS.cadrage;
    if (s.materiel === 'stimuli') p += TARIFS.cadrageStimuli;
    if (s.materiel === 'produit') p += TARIFS.cadrageProduit;

    p += s.participants * (s.recrutement === 'fichier' ? TARIFS.recrutSurFichier : TARIFS.recrutParPersonne);
    p += s.entretiens * TARIFS.indemniteEntretien + s.groupes * PAR_GROUPE * TARIFS.indemniteGroupe;

    var dist = s.modalite === 'online' ? 1 : (s.modalite === 'presentiel' ? 0 : 0.5);
    p += s.entretiens * (TARIFS.entretienPresentiel + dist * (TARIFS.entretienOnline - TARIFS.entretienPresentiel));
    p += s.groupes    * (TARIFS.groupePresentiel    + dist * (TARIFS.groupeOnline    - TARIFS.groupePresentiel));

    p += s.heures * TARIFS.transcriptParHeure;

    s.liv.forEach(function (k) { p += TARIFS[k] || 0; });
    return p;
  }

  function nomDispositif(s) {
    var L = s.liv, n = t().name;
    if (L.indexOf('rapport') > -1 && L.indexOf('atelier') > -1) return n.complet;
    if (L.indexOf('rapport') > -1) return n.rapport;
    if (L.indexOf('atelier') > -1) return n.atelier;
    if (L.indexOf('toplines') > -1) return n.toplines;
    if (L.indexOf('plateforme') > -1) return n.plateforme;
    return n.terrain;
  }

  function listeLivrables(s) {
    var d = t().deliv;
    var out = [
      { txt: d.guide, core: true },
      { txt: d.terrain, core: true },
      { txt: d.transcript, core: true }
    ];
    ['plateforme', 'toplines', 'rapport', 'typologies', 'atelier'].forEach(function (k) {
      if (s.liv.indexOf(k) > -1) out.push({ txt: d[k], core: false });
    });
    return out;
  }

  /* -------------------------------------------------------
     7. RENDU
     ------------------------------------------------------- */
  var nbsp = ' ';
  function eur(v) {
    return String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, nbsp) + nbsp + '€';
  }
  function round500(v) { return Math.round(v / 500) * 500; }

  function render() {
    var s = state(), L = t();
    var cal = calendrier(s);

    document.getElementById('dr-name').textContent = nomDispositif(s);
    document.getElementById('dr-sub').textContent = L.sub[s.decision];
    document.getElementById('dr-voices').textContent = s.participants;
    document.getElementById('dr-weeks').textContent = cal.total;
    document.getElementById('dr-hours').textContent = s.heures + nbsp + 'h';

    /* Calendrier — segments proportionnels */
    var phases = [
      { k: 'cadrage', w: cal.cadrage },
      { k: 'recrutement', w: cal.recrutement },
      { k: 'terrain', w: cal.terrain },
      { k: 'livrables', w: cal.livrables }
    ];
    var tl = document.getElementById('dr-tl');
    var lg = document.getElementById('dr-tl-legend');
    tl.innerHTML = '';
    lg.innerHTML = '';
    phases.forEach(function (p) {
      var seg = document.createElement('div');
      seg.className = 'dr-tl-seg' + (p.k === 'terrain' ? ' is-field' : '');
      seg.style.flexGrow = p.w;
      seg.setAttribute('title', L.phase[p.k] + ' — ' + p.w + ' ' + L.semaines);
      tl.appendChild(seg);

      var item = document.createElement('span');
      item.className = 'dr-tl-item' + (p.k === 'terrain' ? ' is-field' : '');
      item.innerHTML = '<span class="dr-tl-dot"></span>' + L.phase[p.k] + nbsp + p.w + nbsp + (L === T.fr ? 'sem.' : 'w');
      lg.appendChild(item);
    });

    /* Livrables */
    var ul = document.getElementById('dr-deliv');
    ul.innerHTML = '';
    listeLivrables(s).forEach(function (d) {
      var li = document.createElement('li');
      if (d.core) li.className = 'is-core';
      li.innerHTML = '<span class="mk">' + (d.core ? '■' : '□') + '</span><span>' + d.txt + '</span>';
      ul.appendChild(li);
    });

    /* Budget — mode présentation uniquement */
    var b = budget(s);
    document.getElementById('dr-budget').textContent =
      eur(round500(b * 0.9)) + ' – ' + eur(round500(b * 1.15));

    /* Notes */
    document.getElementById('dr-sector-note').textContent = L.sector[s.secteur];
    var rn = document.getElementById('dr-recrut-note');
    if (s.recrutement === 'fichier') { rn.hidden = false; rn.textContent = L.recrutNote; }
    else { rn.hidden = true; }

    /* Lien contact pré-rempli */
    document.getElementById('dr-cta').setAttribute('href', 'contact.html?brief=' + encodeURIComponent(recap(s, cal)));

    /* Curseur */
    volVal.textContent = s.n;
    volUnit.textContent = L.unit[s.dispositif];
    volHint.textContent = L.hint[s.dispositif];
    vol.setAttribute('aria-valuetext', s.n + ' ' + L.unit[s.dispositif]);
    vol.setAttribute('aria-label', L.hint[s.dispositif]);

    /* Annonce : l'essentiel seulement, sinon chaque cran du curseur
       ferait relire le calendrier et les livrables en entier. */
    document.getElementById('dr-status').textContent =
      nomDispositif(s) + ' — ' + s.participants + ' ' + L.lblVoix.toLowerCase() +
      ', ' + cal.total + ' ' + L.semaines + '.';
  }

  function recap(s, cal) {
    var L = t();
    var lines = [
      L.recapTitle,
      '',
      L.lblDecision + ' : ' + L.decLabel[s.decision],
      L.lblSecteur + ' : ' + L.secLabel[s.secteur],
      L.lblTerrain + ' : ' + s.entretiens + ' ' + L.unit.entretiens +
        (s.groupes ? ' + ' + s.groupes + ' ' + L.unit.groupes : ''),
      L.lblModalite + ' : ' + L.modLabel[s.modalite],
      L.lblRecrut + ' : ' + L.recrutBy[s.recrutement],
      L.lblMateriel + ' : ' + L.matLabel[s.materiel],
      L.lblVoix + ' : ' + s.participants + ' (' + s.heures + ' ' + L.heures + ')',
      L.lblDuree + ' : ' + cal.total + ' ' + L.semaines,
      '',
      L.lblLivrables + ' :'
    ];
    listeLivrables(s).forEach(function (d) { lines.push('  - ' + d.txt); });
    return lines.join('\n');
  }

  /* -------------------------------------------------------
     8. ÉVÉNEMENTS
     ------------------------------------------------------- */
  function applyVolumeRange(dispositif, force) {
    var v = VOLUMES[dispositif];
    vol.min = v.min; vol.max = v.max;
    if (force || vol.value < v.min || vol.value > v.max) vol.value = v.def;
  }

  /* Le secteur pré-règle le terrain, sans jamais écraser un réglage
     que l'utilisateur a posé lui-même. `init` sert au premier rendu :
     rien n'est encore « touché », donc tout s'applique. */
  function appliquerSecteur(secteur, init) {
    var d = SECTEURS[secteur];
    if (!d) { applyVolumeRange(pick('dispositif'), false); return; }
    ['dispositif', 'modalite', 'materiel'].forEach(function (k) {
      if (!init && touched[k]) return;
      var input = form.querySelector('input[name="' + k + '"][value="' + d[k] + '"]');
      if (input) input.checked = true;
    });
    if (init || !touched.dispositif) applyVolumeRange(d.dispositif, true);
  }

  form.addEventListener('change', function (e) {
    var name = e.target.name;
    if (!name) return;

    if (name === 'secteur') {
      appliquerSecteur(e.target.value, false);
    } else if (name === 'dispositif') {
      touched.dispositif = true;
      applyVolumeRange(e.target.value, true);
    } else if (name !== 'liv') {
      touched[name] = true;
    }
    render();
  });

  vol.addEventListener('input', function () {
    volVal.textContent = vol.value;
    render();
  });

  document.getElementById('dr-copy').addEventListener('click', function (e) {
    var btn = e.currentTarget, L = t();
    var s = state();
    var txt = recap(s, calendrier(s));
    var done = function (ok) {
      var prev = btn.textContent;
      btn.textContent = ok ? L.copyOk : L.copyFail;
      setTimeout(function () { btn.textContent = prev; }, 2000);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).then(function () { done(true); }, function () { done(false); });
    } else {
      done(false);
    }
  });

  window.addEventListener('languagechange', render);

  /* -------------------------------------------------------
     9. MODE PRÉSENTATION
     ?interne=1 dans l'URL, ou Ctrl/Cmd + Alt + P.
     Persiste le temps de l'onglet, jamais au-delà.
     ------------------------------------------------------- */
  var KEY = 'acme-dr-interne';
  function setInterne(on) {
    document.body.classList.toggle('dr-interne', on);
    try { on ? sessionStorage.setItem(KEY, '1') : sessionStorage.removeItem(KEY); } catch (_) {}
  }
  var params = new URLSearchParams(location.search);
  var stored = false;
  try { stored = sessionStorage.getItem(KEY) === '1'; } catch (_) {}
  setInterne(params.get('interne') === '1' || stored);

  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.altKey && (e.key === 'p' || e.key === 'P')) {
      e.preventDefault();
      setInterne(!document.body.classList.contains('dr-interne'));
    }
  });

  /* -------------------------------------------------------
     10. DÉMARRAGE
     ------------------------------------------------------- */
  appliquerSecteur(pick('secteur'), true);
  render();
  /* i18n s'applique au DOMContentLoaded : on repasse après, pour que
     les textes assemblés en JS suivent la langue choisie. */
  document.addEventListener('DOMContentLoaded', render);
})();
