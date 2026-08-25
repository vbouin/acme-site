/* =========================================================
   ACMÉ — shared behaviors
   Nav · reveal · counters · SVG draw-in · 3D scenes · map
   ========================================================= */

/* -------- Nav -------- */
(function nav() {
  const nav = document.querySelector('.nav');
  if (!nav) return;
  const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 40);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  const burger = document.querySelector('.nav-burger');
  const menu = document.querySelector('.nav-menu');
  burger?.addEventListener('click', () => menu.classList.toggle('open'));
})();

/* -------- Reveal -------- */
(function reveal() {
  const els = document.querySelectorAll('.reveal');
  if (!els.length) return;
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('in');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12 });
  els.forEach(el => io.observe(el));
})();

/* -------- Animated counters -------- */
(function counters() {
  const els = document.querySelectorAll('.counter[data-count-to]');
  if (!els.length) return;
  const animate = (el) => {
    const target = parseFloat(el.dataset.countTo);
    const suffix = el.dataset.suffix || '';
    const duration = 1500;
    const start = performance.now();
    const initial = 0;
    const step = (now) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      const value = Math.round(initial + (target - initial) * eased);
      el.textContent = value + suffix;
      if (p < 1) requestAnimationFrame(step);
      else el.textContent = target + suffix;
    };
    requestAnimationFrame(step);
  };
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) { animate(e.target); io.unobserve(e.target); }
    });
  }, { threshold: 0.4 });
  els.forEach(el => io.observe(el));
})();

/* -------- SVG draw-in + flow-bars viewport triggers -------- */
(function vizTriggers() {
  const els = document.querySelectorAll('.draw-in, .flow-bars');
  if (!els.length) return;
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { threshold: 0.25 });
  els.forEach(el => io.observe(el));
})();

/* -------- Three.js utilities -------- */
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function createScene(canvas, { alpha = true } = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, alpha, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
  camera.position.set(0, 0, 5);

  const resize = () => {
    const rect = canvas.getBoundingClientRect();
    renderer.setSize(rect.width, rect.height, false);
    camera.aspect = rect.width / rect.height;
    camera.updateProjectionMatrix();
  };
  resize();
  const ro = new ResizeObserver(resize);
  ro.observe(canvas);
  window.addEventListener('resize', resize);

  // Perf: only render while the canvas is on-screen and the tab is visible.
  // The animation loops keep spinning (cheap trig), but the costly WebGL draw
  // is skipped when off-screen — so at most 1–2 scenes render at once.
  canvas.__visible = true;
  const vio = new IntersectionObserver(
    (entries) => { canvas.__visible = entries[0].isIntersecting; },
    { threshold: 0 }
  );
  vio.observe(canvas);
  const realRender = renderer.render.bind(renderer);
  renderer.render = (sc, cam) => {
    if (canvas.__visible && !document.hidden) realRender(sc, cam);
  };

  return { renderer, scene, camera, resize };
}

/* Build a more anatomically-real wireframe car */
function buildDetailedCar(scale = 1) {
  const car = new THREE.Group();
  const mat = new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.9 });
  const fill = new THREE.MeshBasicMaterial({ color: 0x000000, wireframe: true, transparent: true, opacity: 0.65 });

  // Chassis profile — sedan silhouette via extruded shape
  const shape = new THREE.Shape();
  shape.moveTo(-1.4, -0.15);
  shape.lineTo(-1.3, 0.05);
  shape.quadraticCurveTo(-1.0, 0.1, -0.7, 0.18);
  shape.quadraticCurveTo(-0.5, 0.22, -0.35, 0.52); // windshield base
  shape.lineTo(0.35, 0.62);                         // roof
  shape.quadraticCurveTo(0.7, 0.55, 0.95, 0.22);   // rear window
  shape.quadraticCurveTo(1.15, 0.18, 1.35, 0.1);
  shape.lineTo(1.42, -0.12);
  shape.quadraticCurveTo(1.4, -0.2, 1.25, -0.22);
  shape.lineTo(-1.25, -0.22);
  shape.quadraticCurveTo(-1.4, -0.2, -1.4, -0.15);
  const extrude = new THREE.ExtrudeGeometry(shape, { depth: 0.78, bevelEnabled: false, steps: 1 });
  extrude.translate(0, 0, -0.39);
  const body = new THREE.LineSegments(new THREE.EdgesGeometry(extrude), mat);
  car.add(body);
  const bodyFill = new THREE.Mesh(extrude, fill);
  car.add(bodyFill);

  // Windows (darker inner rectangles)
  const windowMat = new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.5 });
  const wGeo = new THREE.PlaneGeometry(0.65, 0.32);
  const wLeft = new THREE.LineSegments(new THREE.EdgesGeometry(wGeo), windowMat);
  wLeft.position.set(0, 0.4, 0.41);
  car.add(wLeft);
  const wRight = wLeft.clone();
  wRight.position.z = -0.41;
  car.add(wRight);

  // Wheel arches + wheels (4)
  const wheelPositions = [
    [-0.82, -0.22, 0.41], [0.82, -0.22, 0.41],
    [-0.82, -0.22, -0.41], [0.82, -0.22, -0.41],
  ];
  wheelPositions.forEach(([x, y, z]) => {
    // Tire
    const tire = new THREE.Mesh(
      new THREE.TorusGeometry(0.22, 0.08, 8, 20),
      new THREE.MeshBasicMaterial({ color: 0x000000, wireframe: true })
    );
    tire.rotation.y = Math.PI / 2;
    tire.position.set(x, y, z);
    car.add(tire);
    // Rim spokes
    const rimGeo = new THREE.CircleGeometry(0.14, 8);
    const rim = new THREE.LineSegments(new THREE.EdgesGeometry(rimGeo), mat);
    rim.rotation.y = Math.PI / 2;
    rim.position.set(x + (z > 0 ? 0.02 : -0.02), y, z);
    car.add(rim);
    // Hub
    const hub = new THREE.Mesh(
      new THREE.SphereGeometry(0.04, 8, 8),
      new THREE.MeshBasicMaterial({ color: 0x000000 })
    );
    hub.position.set(x + (z > 0 ? 0.03 : -0.03), y, z);
    car.add(hub);
  });

  // Headlights
  [[1.4, 0, 0.28], [1.4, 0, -0.28]].forEach(([x, y, z]) => {
    const hl = new THREE.Mesh(
      new THREE.SphereGeometry(0.06, 10, 10),
      new THREE.MeshBasicMaterial({ color: 0x000000 })
    );
    hl.position.set(x, y, z);
    car.add(hl);
  });

  // Door line
  const doorLine = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-0.1, -0.2, 0.4), new THREE.Vector3(-0.1, 0.3, 0.4)
    ]),
    mat
  );
  car.add(doorLine);
  const doorLine2 = doorLine.clone();
  doorLine2.position.z = -0.8;
  car.add(doorLine2);

  car.scale.setScalar(scale);
  return car;
}

/* Build a minimalist 2D persona vector icon (flat shape, always facing camera) */
function buildPersonaIcon(kind) {
  const g = new THREE.Group();
  const fill = new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.DoubleSide });
  const white = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide });
  const stroke = new THREE.LineBasicMaterial({ color: 0x000000 });

  const addShape = (shape) => g.add(new THREE.Mesh(new THREE.ShapeGeometry(shape), fill));
  const addOutline = (pts) => g.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts), stroke));

  if (kind === 'person') {
    // Head
    const head = new THREE.Mesh(new THREE.CircleGeometry(0.08, 24), fill);
    head.position.set(0, 0.14, 0);
    g.add(head);
    // Shoulders + torso (rounded trapezoid)
    const body = new THREE.Shape();
    body.moveTo(-0.13, 0.04);
    body.quadraticCurveTo(-0.18, -0.05, -0.12, -0.22);
    body.lineTo(0.12, -0.22);
    body.quadraticCurveTo(0.18, -0.05, 0.13, 0.04);
    body.quadraticCurveTo(0, 0.1, -0.13, 0.04);
    addShape(body);
  } else if (kind === 'pin') {
    // Map pin — teardrop
    const pin = new THREE.Shape();
    pin.moveTo(0, -0.22);
    pin.bezierCurveTo(-0.18, -0.05, -0.15, 0.18, 0, 0.18);
    pin.bezierCurveTo(0.15, 0.18, 0.18, -0.05, 0, -0.22);
    addShape(pin);
    const hole = new THREE.Mesh(new THREE.CircleGeometry(0.05, 20), white);
    hole.position.set(0, 0.05, 0.001);
    g.add(hole);
  } else if (kind === 'bag') {
    // Shopping bag
    const bag = new THREE.Shape();
    bag.moveTo(-0.14, -0.16);
    bag.lineTo(0.14, -0.16);
    bag.lineTo(0.12, 0.08);
    bag.lineTo(-0.12, 0.08);
    bag.lineTo(-0.14, -0.16);
    addShape(bag);
    // Handles (outlined arcs)
    const handleL = [];
    for (let i = 0; i <= 14; i++) {
      const t = (i / 14) * Math.PI;
      handleL.push(new THREE.Vector3(-0.06 + Math.cos(Math.PI - t) * 0.05, 0.08 + Math.sin(t) * 0.08, 0.001));
    }
    g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(handleL), stroke));
    const handleR = handleL.map(v => new THREE.Vector3(v.x + 0.12, v.y, v.z));
    g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(handleR), stroke));
  } else if (kind === 'phone') {
    const body = new THREE.Shape();
    const w = 0.11, h = 0.2, r = 0.03;
    body.moveTo(-w + r, -h);
    body.lineTo(w - r, -h);
    body.quadraticCurveTo(w, -h, w, -h + r);
    body.lineTo(w, h - r);
    body.quadraticCurveTo(w, h, w - r, h);
    body.lineTo(-w + r, h);
    body.quadraticCurveTo(-w, h, -w, h - r);
    body.lineTo(-w, -h + r);
    body.quadraticCurveTo(-w, -h, -w + r, -h);
    addShape(body);
    // Screen inner
    const screen = new THREE.Mesh(new THREE.PlaneGeometry(0.16, 0.28), white);
    screen.position.set(0, 0.01, 0.001);
    g.add(screen);
    // Notch
    const notch = new THREE.Mesh(new THREE.PlaneGeometry(0.04, 0.01), fill);
    notch.position.set(0, 0.16, 0.002);
    g.add(notch);
  } else if (kind === 'heart') {
    const s = new THREE.Shape();
    s.moveTo(0, -0.14);
    s.bezierCurveTo(-0.22, 0.02, -0.14, 0.2, 0, 0.08);
    s.bezierCurveTo(0.14, 0.2, 0.22, 0.02, 0, -0.14);
    addShape(s);
  } else if (kind === 'gear') {
    // Center disk
    const disk = new THREE.Mesh(new THREE.CircleGeometry(0.1, 28), fill);
    g.add(disk);
    // 8 teeth
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      const tooth = new THREE.Mesh(new THREE.PlaneGeometry(0.06, 0.05), fill);
      tooth.position.set(Math.cos(a) * 0.13, Math.sin(a) * 0.13, 0);
      tooth.rotation.z = a;
      g.add(tooth);
    }
    // Hole
    const hole = new THREE.Mesh(new THREE.CircleGeometry(0.04, 20), white);
    hole.position.z = 0.001;
    g.add(hole);
  } else if (kind === 'leaf') {
    const leaf = new THREE.Shape();
    leaf.moveTo(0, -0.18);
    leaf.bezierCurveTo(0.18, -0.05, 0.15, 0.15, 0, 0.18);
    leaf.bezierCurveTo(-0.15, 0.15, -0.18, -0.05, 0, -0.18);
    addShape(leaf);
    const stem = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, -0.12, 0.001), new THREE.Vector3(0, 0.12, 0.001)]),
      new THREE.LineBasicMaterial({ color: 0xffffff })
    );
    g.add(stem);
  } else if (kind === 'compass') {
    const ring = new THREE.Mesh(new THREE.RingGeometry(0.11, 0.13, 32), fill);
    g.add(ring);
    const n = new THREE.Shape();
    n.moveTo(-0.04, 0); n.lineTo(0, 0.12); n.lineTo(0.04, 0); n.lineTo(-0.04, 0);
    addShape(n);
    const s = new THREE.Mesh(new THREE.PlaneGeometry(0.06, 0.12), fill);
    s.position.y = -0.06;
    g.add(s);
  }
  return g;
}

/* Kept for other scenes that may reference it — unchanged body */
function buildMannequin(scale = 1, side = 1) {
  const m = new THREE.Group();
  const wire = new THREE.MeshBasicMaterial({ color: 0x000000, wireframe: true, transparent: true, opacity: 0.85 });
  const line = new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.9 });

  // Head
  const head = new THREE.Mesh(new THREE.IcosahedronGeometry(0.28, 1), wire);
  head.position.y = 1.55;
  m.add(head);
  m.userData.head = head;

  // Neck
  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.08, 0.18, 8), wire);
  neck.position.y = 1.3;
  m.add(neck);

  // Torso via lathe profile (wider shoulders → narrower waist)
  const torsoProfile = [
    new THREE.Vector2(0.0, 0.6),
    new THREE.Vector2(0.38, 0.55),
    new THREE.Vector2(0.42, 0.3),
    new THREE.Vector2(0.36, -0.05),
    new THREE.Vector2(0.28, -0.35),
    new THREE.Vector2(0.3, -0.5),
    new THREE.Vector2(0.0, -0.5),
  ];
  const torso = new THREE.Mesh(new THREE.LatheGeometry(torsoProfile, 14), wire);
  torso.position.y = 0.65;
  m.add(torso);

  // Arm builder — two bent segments pointing forward (gesturing toward partner)
  const makeArm = (s) => {
    const arm = new THREE.Group();
    arm.position.set(0.38 * s, 1.15, 0);
    const upper = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.05, 0.45, 8), wire);
    upper.position.y = -0.22;
    upper.rotation.z = s * 0.2;
    arm.add(upper);
    const elbow = new THREE.Mesh(new THREE.SphereGeometry(0.055, 10, 10), wire);
    elbow.position.set(s * 0.05, -0.44, 0);
    arm.add(elbow);
    const lower = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.04, 0.4, 8), wire);
    lower.position.set(s * -0.12, -0.55, 0.22);
    lower.rotation.set(-Math.PI / 3, 0, s * 0.3);
    arm.add(lower);
    const hand = new THREE.Mesh(new THREE.SphereGeometry(0.07, 10, 10), wire);
    hand.position.set(s * -0.22, -0.65, 0.45);
    arm.add(hand);
    arm.userData.hand = hand;
    return arm;
  };
  const armL = makeArm(-1);
  const armR = makeArm(1);
  m.add(armL);
  m.add(armR);
  m.userData.armL = armL;
  m.userData.armR = armR;

  // Legs
  [-1, 1].forEach((s) => {
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.07, 1.15, 8), wire);
    leg.position.set(s * 0.16, -0.4, 0);
    m.add(leg);
    const foot = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.08, 0.3), wire);
    foot.position.set(s * 0.16, -1.02, 0.06);
    m.add(foot);
  });

  // Ground shadow oval
  const shadow = new THREE.Mesh(
    new THREE.RingGeometry(0.2, 0.45, 16),
    new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.18, side: THREE.DoubleSide })
  );
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.y = -1.05;
  m.add(shadow);

  // Face the center (partner is on the other side)
  m.rotation.y = side > 0 ? -Math.PI / 4 : Math.PI / 4;
  m.scale.setScalar(scale);
  return m;
}

/* -------- HERO scene : morphing data graph + persona constellation solar system -------- */


/* -------- Tier mini-scenes -------- */
function initTierScene(canvas, type) {
  if (typeof THREE === 'undefined') return;
  const { renderer, scene, camera } = createScene(canvas);
  camera.position.set(0, 0, 4);
  const group = new THREE.Group();
  scene.add(group);
  const mat = new THREE.MeshBasicMaterial({ color: 0x000000, wireframe: true, transparent: true, opacity: 0.85 });
  const lineMat = new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.8 });

  if (type === 'docs') {
    // Stack of pages with text lines
    for (let i = 0; i < 5; i++) {
      const plane = new THREE.LineSegments(
        new THREE.EdgesGeometry(new THREE.PlaneGeometry(2, 1.3)),
        lineMat
      );
      plane.position.set(i * 0.15 - 0.3, i * 0.1 - 0.2, -i * 0.1);
      plane.rotation.y = 0.2;
      group.add(plane);
      // text lines
      for (let j = 0; j < 5; j++) {
        const tl = new THREE.Line(
          new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(-0.85, 0.4 - j * 0.2, 0.01),
            new THREE.Vector3(0.8 - Math.random() * 0.3, 0.4 - j * 0.2, 0.01)
          ]),
          new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.5 })
        );
        tl.position.copy(plane.position);
        tl.rotation.copy(plane.rotation);
        group.add(tl);
      }
    }
  } else if (type === 'video') {
    const screen = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(2.4, 1.5, 0.08)),
      lineMat
    );
    group.add(screen);
    // Play triangle
    const playPts = [
      new THREE.Vector3(-0.18, 0.22, 0.06),
      new THREE.Vector3(0.26, 0, 0.06),
      new THREE.Vector3(-0.18, -0.22, 0.06),
      new THREE.Vector3(-0.18, 0.22, 0.06),
    ];
    const play = new THREE.Line(new THREE.BufferGeometry().setFromPoints(playPts), lineMat);
    group.add(play);
    // Timeline
    const tl = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(-1.0, -0.6, 0.06),
        new THREE.Vector3(1.0, -0.6, 0.06)
      ]),
      lineMat
    );
    group.add(tl);
    for (let i = 0; i < 8; i++) {
      const tick = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(-1.0 + i * 0.28, -0.55, 0.06),
          new THREE.Vector3(-1.0 + i * 0.28, -0.65, 0.06)
        ]),
        lineMat
      );
      group.add(tick);
    }
  } else {
    // Flash: concentric squares + rays
    for (let i = 0; i < 6; i++) {
      const s = 0.4 + i * 0.25;
      const sq = new THREE.LineSegments(
        new THREE.EdgesGeometry(new THREE.PlaneGeometry(s, s)),
        new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.9 - i * 0.12 })
      );
      group.add(sq);
    }
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      const ray = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(Math.cos(a) * 1.2, Math.sin(a) * 1.2, 0),
          new THREE.Vector3(Math.cos(a) * 1.5, Math.sin(a) * 1.5, 0)
        ]),
        lineMat
      );
      group.add(ray);
    }
  }

  const start = performance.now();
  function animate() {
    const t = (performance.now() - start) / 1000;
    if (!reducedMotion) {
      group.rotation.y = Math.sin(t * 0.4) * 0.35;
      group.rotation.x = Math.cos(t * 0.3) * 0.2;
    }
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
  }
  animate();
}

/* -------- Expertise scenes -------- */
function initExpertiseScene(canvas, kind) {
  if (typeof THREE === 'undefined') return;
  const { renderer, scene, camera } = createScene(canvas);
  camera.position.set(0, 0.3, 5);
  const group = new THREE.Group();
  scene.add(group);
  const mat = new THREE.MeshBasicMaterial({ color: 0x000000, wireframe: true, transparent: true, opacity: 0.85 });
  const lineMat = new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.85 });

  if (kind === 'automotive') {
    // Electric motor + battery composition
    const motor = new THREE.Group();
    group.add(motor);

    // Stator (outer ring + housing)
    const housing = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.CylinderGeometry(1.1, 1.1, 1.4, 24, 1)),
      lineMat
    );
    housing.rotation.z = Math.PI / 2;
    motor.add(housing);
    // Cooling fins (vertical rings)
    for (let i = -2; i <= 2; i++) {
      const fin = new THREE.LineLoop(
        new THREE.BufferGeometry().setFromPoints(
          Array.from({ length: 48 }, (_, k) => {
            const t = (k / 48) * Math.PI * 2;
            return new THREE.Vector3(0, Math.cos(t) * 1.14, Math.sin(t) * 1.14);
          })
        ),
        new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.55 })
      );
      fin.position.x = i * 0.32;
      motor.add(fin);
    }
    // Rotor shaft (rotates)
    const rotor = new THREE.Group();
    const shaft = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.CylinderGeometry(0.18, 0.18, 2.4, 16)),
      new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.95 })
    );
    shaft.rotation.z = Math.PI / 2;
    rotor.add(shaft);
    // Rotor blades (spokes)
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2;
      const spoke = new THREE.Mesh(
        new THREE.BoxGeometry(0.04, 0.9, 0.04),
        new THREE.MeshBasicMaterial({ color: 0x000000 })
      );
      spoke.position.set(0, Math.cos(a) * 0.45, Math.sin(a) * 0.45);
      spoke.rotation.x = a;
      rotor.add(spoke);
    }
    motor.add(rotor);
    motor.userData.rotor = rotor;

    // Battery (left side)
    const battery = new THREE.Group();
    const body = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(1.0, 1.3, 0.7)),
      lineMat
    );
    battery.add(body);
    // Battery cells (internal lines)
    for (let i = 0; i < 4; i++) {
      const cell = new THREE.LineSegments(
        new THREE.EdgesGeometry(new THREE.BoxGeometry(0.18, 1.1, 0.55)),
        new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.45 })
      );
      cell.position.x = -0.36 + i * 0.24;
      battery.add(cell);
    }
    // Terminals (+) and (-)
    const termPlus = new THREE.Mesh(
      new THREE.BoxGeometry(0.18, 0.12, 0.18),
      new THREE.MeshBasicMaterial({ color: 0x000000 })
    );
    termPlus.position.set(-0.25, 0.71, 0);
    const termMinus = termPlus.clone();
    termMinus.position.x = 0.25;
    battery.add(termPlus, termMinus);
    battery.position.set(-2.8, 0, 0);
    motor.add(battery);

    // Power cables (curve from battery to motor)
    const cableMat = new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.8 });
    [-0.25, 0.25].forEach((dx, i) => {
      const pts = [];
      for (let t = 0; t <= 1; t += 0.05) {
        const x = -2.55 + dx + t * (2.55 + dx - 1.1);
        const y = 0.71 - Math.sin(t * Math.PI) * 0.5 + (i ? 0.1 : -0.1);
        pts.push(new THREE.Vector3(x, y, 0));
      }
      const cable = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), cableMat);
      motor.add(cable);
    });

    // Electric pulses traveling along cables
    const pulses = [];
    for (let i = 0; i < 6; i++) {
      const p = new THREE.Mesh(
        new THREE.SphereGeometry(0.07, 12, 10),
        new THREE.MeshBasicMaterial({ color: 0xffaa33 })
      );
      p.userData = { t: i / 6, lane: i % 2 ? 0.25 : -0.25 };
      motor.add(p);
      pulses.push(p);
    }
    motor.userData.pulses = pulses;

    // Lightning bolt above motor (subtle pulse glow)
    const bolt = new THREE.Mesh(
      new THREE.CircleGeometry(0.5, 24),
      new THREE.MeshBasicMaterial({ color: 0xffaa33, transparent: true, opacity: 0 })
    );
    bolt.position.set(0, 1.6, 0);
    motor.add(bolt);
    motor.userData.bolt = bolt;

    // Ground grid (kept for context)
    const grid = new THREE.GridHelper(8, 12, 0xB8B8B8, 0xDDDDDD);
    grid.position.y = -1.4;
    grid.material.transparent = true;
    grid.material.opacity = 0.35;
    group.add(grid);

    // Ambient charge particles around the whole rig
    for (let i = 0; i < 18; i++) {
      const a = (i / 18) * Math.PI * 2;
      const r = 2.8 + Math.sin(i) * 0.4;
      const dot = new THREE.Mesh(
        new THREE.SphereGeometry(0.04, 8, 8),
        new THREE.MeshBasicMaterial({ color: 0x000000 })
      );
      dot.position.set(Math.cos(a) * r, Math.sin(i * 1.5) * 0.7, Math.sin(a) * r);
      dot.userData = { a, r, phase: Math.random() * Math.PI * 2 };
      group.add(dot);
    }
  } else if (kind === 'territories') {
    // Stylized globe with meridians + map pins
    const wire = new THREE.Mesh(
      new THREE.SphereGeometry(1.4, 24, 18),
      new THREE.MeshBasicMaterial({ color: 0x000000, wireframe: true, transparent: true, opacity: 0.3 })
    );
    group.add(wire);
    // Emphasized meridians
    for (let i = 0; i < 6; i++) {
      const ring = new THREE.LineLoop(
        new THREE.BufferGeometry().setFromPoints(
          Array.from({ length: 64 }, (_, k) => {
            const t = (k / 64) * Math.PI * 2;
            return new THREE.Vector3(Math.cos(t) * 1.4, Math.sin(t) * 1.4, 0);
          })
        ),
        new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.55 })
      );
      ring.rotation.y = (i / 6) * Math.PI;
      group.add(ring);
    }
    // Pins on key territories (lat/lon on globe)
    const pins = [
      [0.5, 0.3, 0.9], [-1.1, 0.5, 0.5], [-0.3, 0.7, 1.1],
      [1.2, -0.3, 0.5], [0.9, 0.1, 1.0], [-0.4, -0.8, 1.1],
    ];
    pins.forEach((p) => {
      const pin = new THREE.Mesh(
        new THREE.ConeGeometry(0.08, 0.25, 6),
        new THREE.MeshBasicMaterial({ color: 0x000000 })
      );
      const v = new THREE.Vector3(...p).normalize().multiplyScalar(1.5);
      pin.position.copy(v);
      pin.lookAt(0, 0, 0);
      pin.rotateX(Math.PI / 2);
      group.add(pin);
      const halo = new THREE.Mesh(
        new THREE.RingGeometry(0.12, 0.14, 16),
        new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.4, side: THREE.DoubleSide })
      );
      halo.position.copy(v.clone().multiplyScalar(1.01));
      halo.lookAt(0, 0, 0);
      group.add(halo);
    });
    // Ambient dots
    for (let i = 0; i < 40; i++) {
      const u = Math.random(), v = Math.random();
      const theta = 2 * Math.PI * u, phi = Math.acos(2 * v - 1);
      const dot = new THREE.Mesh(
        new THREE.SphereGeometry(0.03, 8, 8),
        new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.4 })
      );
      dot.position.set(
        1.45 * Math.sin(phi) * Math.cos(theta),
        1.45 * Math.sin(phi) * Math.sin(theta),
        1.45 * Math.cos(phi)
      );
      group.add(dot);
    }
  } else if (kind === 'retail') {
    // Grid of pulsing dots (shopper field)
    for (let i = 0; i < 18; i++) {
      for (let j = 0; j < 11; j++) {
        const dot = new THREE.Mesh(
          new THREE.SphereGeometry(0.04, 8, 8),
          new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.55 + Math.random() * 0.45 })
        );
        dot.position.set((i - 8.5) * 0.26, (j - 5) * 0.26, (Math.random() - 0.5) * 0.4);
        dot.userData = { baseY: dot.position.y, phase: Math.random() * Math.PI * 2 };
        group.add(dot);
      }
    }
    // Frame lines (store perimeter)
    const rectPts = [
      new THREE.Vector3(-2.4, -1.5, 0), new THREE.Vector3(2.4, -1.5, 0),
      new THREE.Vector3(2.4, 1.5, 0), new THREE.Vector3(-2.4, 1.5, 0),
      new THREE.Vector3(-2.4, -1.5, 0)
    ];
    const rect = new THREE.Line(new THREE.BufferGeometry().setFromPoints(rectPts), lineMat);
    group.add(rect);
  } else if (kind === 'beauty') {
    // Stylized perfume bottle + droplets
    const bottleProfile = [
      new THREE.Vector2(0, -1.2),
      new THREE.Vector2(0.55, -1.2),
      new THREE.Vector2(0.6, -1.0),
      new THREE.Vector2(0.6, 0.3),
      new THREE.Vector2(0.45, 0.45),
      new THREE.Vector2(0.2, 0.55),
      new THREE.Vector2(0.22, 0.9),
      new THREE.Vector2(0.35, 0.9),
      new THREE.Vector2(0.35, 1.15),
      new THREE.Vector2(0, 1.15),
    ];
    const latheGeo = new THREE.LatheGeometry(bottleProfile, 20);
    const bottle = new THREE.Mesh(latheGeo, mat);
    group.add(bottle);
    // Label band
    const label = new THREE.LineLoop(
      new THREE.BufferGeometry().setFromPoints(
        Array.from({ length: 32 }, (_, k) => {
          const t = (k / 32) * Math.PI * 2;
          return new THREE.Vector3(Math.cos(t) * 0.62, -0.35, Math.sin(t) * 0.62);
        })
      ),
      lineMat
    );
    group.add(label);
    const label2 = label.clone();
    label2.position.y = 0.05 - (-0.35);
    // floating droplets & particles
    for (let i = 0; i < 30; i++) {
      const d = new THREE.Mesh(
        new THREE.SphereGeometry(0.03 + Math.random() * 0.02, 8, 8),
        new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.5 + Math.random() * 0.5 })
      );
      d.position.set((Math.random() - 0.5) * 3.4, Math.random() * 2.8 - 1.0, (Math.random() - 0.5) * 2);
      d.userData = { baseY: d.position.y, phase: Math.random() * Math.PI * 2, speed: 0.4 + Math.random() * 0.8 };
      group.add(d);
    }
    // Spray fan (lines emitting from top)
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      const start = new THREE.Vector3(0, 1.2, 0);
      const end = new THREE.Vector3(Math.cos(a) * 1.2, 1.8, Math.sin(a) * 1.2);
      const line = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([start, end]),
        new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.3 })
      );
      group.add(line);
    }
  }

  const start = performance.now();
  function animate() {
    const t = (performance.now() - start) / 1000;
    if (!reducedMotion) {
      group.rotation.y = Math.sin(t * 0.3) * 0.4 + t * 0.04;
      group.rotation.x = Math.cos(t * 0.2) * 0.12;
      group.children.forEach((c) => {
        if (c.userData && c.userData.baseY !== undefined) {
          const phase = c.userData.phase || 0;
          const speed = c.userData.speed || 1.5;
          c.position.y = c.userData.baseY + Math.sin(t * speed + phase) * 0.18;
        }
        // Electric-motor sub-animations
        if (c.userData && c.userData.rotor) {
          c.userData.rotor.rotation.x = t * 4.5;
          if (c.userData.pulses) {
            c.userData.pulses.forEach((p) => {
              p.userData.t = (p.userData.t + 0.012) % 1;
              const u = p.userData.t;
              const x = -2.55 + p.userData.lane + u * (2.55 + p.userData.lane - 1.1);
              const y = 0.71 - Math.sin(u * Math.PI) * 0.5 + (p.userData.lane > 0 ? 0.1 : -0.1);
              p.position.set(x, y, 0);
              p.material.opacity = Math.sin(u * Math.PI) * 0.95 + 0.05;
              p.material.transparent = true;
            });
          }
          if (c.userData.bolt) {
            c.userData.bolt.material.opacity = (Math.sin(t * 3) * 0.5 + 0.5) * 0.15;
          }
        }
      });
    }
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
  }
  animate();
}

/* -------- Pillar data-visualization scenes (ACMÉ brand vocabulary) -------- */
function initPillarScene(canvas, kind) {
  if (typeof THREE === 'undefined') return;
  const { renderer, scene, camera } = createScene(canvas);
  camera.position.set(0, 0.4, 6);
  const root = new THREE.Group();
  scene.add(root);

  const ink = 0x000000;
  const greyLine = 0x3a3a3a;
  const accent = 0xaa7744; // beige-orange
  const blueGrey = 0x576270;

  const lineMat = new THREE.LineBasicMaterial({ color: ink, transparent: true, opacity: 0.92 });
  const softMat = new THREE.LineBasicMaterial({ color: greyLine, transparent: true, opacity: 0.45 });

  // ====== AXES (Fichier 41 growth-chart) ======
  if (kind === 'axes') {
    camera.position.set(0.2, 0.4, 5.2);
    // X and Y axes with cone arrow tips
    const axisMat = new THREE.LineBasicMaterial({ color: ink, transparent: true, opacity: 0.95 });
    const xAxis = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(-2.2, -1.3, 0),
        new THREE.Vector3(2.2, -1.3, 0),
      ]),
      axisMat
    );
    const yAxis = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(-2.2, -1.3, 0),
        new THREE.Vector3(-2.2, 1.6, 0),
      ]),
      axisMat
    );
    root.add(xAxis, yAxis);
    const coneMat = new THREE.MeshBasicMaterial({ color: ink });
    const xTip = new THREE.Mesh(new THREE.ConeGeometry(0.08, 0.22, 16), coneMat);
    xTip.position.set(2.3, -1.3, 0); xTip.rotation.z = -Math.PI / 2;
    const yTip = new THREE.Mesh(new THREE.ConeGeometry(0.08, 0.22, 16), coneMat);
    yTip.position.set(-2.2, 1.7, 0);
    root.add(xTip, yTip);

    // Blue-grey rectangular accent panel (the cls-3 block)
    const panel = new THREE.Mesh(
      new THREE.PlaneGeometry(0.55, 1.5),
      new THREE.MeshBasicMaterial({ color: blueGrey, transparent: true, opacity: 0.82 })
    );
    panel.position.set(-0.2, -0.35, -0.05);
    root.add(panel);

    // Hatched density stripes under curve
    const hatchGroup = new THREE.Group();
    const hatchMat = new THREE.LineBasicMaterial({ color: ink, transparent: true, opacity: 0.55 });
    const curveFn = (x) => {
      // arched bezier-ish curve
      const t = (x + 2.2) / 4.4; // 0..1
      return -1.3 + Math.pow(t, 1.4) * 2.4 + Math.sin(t * Math.PI) * 0.35;
    };
    for (let i = 0; i < 42; i++) {
      const x = -2.0 + i * 0.095;
      const topY = curveFn(x);
      const line = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(x, -1.28, 0.01),
          new THREE.Vector3(x, topY, 0.01),
        ]),
        hatchMat.clone()
      );
      line.material.opacity = 0.18 + Math.random() * 0.3;
      hatchGroup.add(line);
    }
    root.add(hatchGroup);

    // Smooth arched growth curve + traveling dot
    const curvePts = [];
    for (let i = 0; i <= 80; i++) {
      const x = -2.0 + (i / 80) * 4.0;
      curvePts.push(new THREE.Vector3(x, curveFn(x), 0.05));
    }
    const curveLine = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(curvePts),
      new THREE.LineBasicMaterial({ color: ink, linewidth: 2, transparent: true, opacity: 1 })
    );
    root.add(curveLine);

    // Anchor dots on curve
    const dotPositions = [0.1, 0.3, 0.55, 0.78];
    const dots = [];
    dotPositions.forEach((t) => {
      const x = -2.0 + t * 4.0;
      const dot = new THREE.Mesh(
        new THREE.CircleGeometry(0.09, 24),
        new THREE.MeshBasicMaterial({ color: ink })
      );
      dot.position.set(x, curveFn(x), 0.08);
      root.add(dot);
      dots.push(dot);
    });

    // Traveling pulse dot
    const traveler = new THREE.Mesh(
      new THREE.CircleGeometry(0.12, 24),
      new THREE.MeshBasicMaterial({ color: accent })
    );
    root.add(traveler);

    const start = performance.now();
    function animate() {
      const t = (performance.now() - start) / 1000;
      if (!reducedMotion) {
        root.rotation.y = Math.sin(t * 0.25) * 0.25;
        root.rotation.x = Math.cos(t * 0.2) * 0.08;
        const u = (t * 0.18) % 1;
        const x = -2.0 + u * 4.0;
        traveler.position.set(x, curveFn(x) + 0.02, 0.12);
        traveler.scale.setScalar(1 + Math.sin(t * 4) * 0.15);
        hatchGroup.children.forEach((l, i) => {
          l.material.opacity = 0.18 + (Math.sin(t * 1.2 + i * 0.2) * 0.5 + 0.5) * 0.35;
        });
      }
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    }
    animate();
    return;
  }

  // ====== STAIRS (Fichier 49 stepped pyramid) ======
  if (kind === 'stairs') {
    camera.position.set(3.2, 2.6, 4.2);
    camera.lookAt(0, 0.2, 0);

    const stepCount = 5;
    const stepW = 2.6;
    const stepD = 0.55;
    const stepH = 0.35;
    const steps = [];
    for (let i = 0; i < stepCount; i++) {
      const w = stepW - i * 0.0;
      const box = new THREE.BoxGeometry(w, stepH, stepD);
      const wire = new THREE.LineSegments(
        new THREE.EdgesGeometry(box),
        new THREE.LineBasicMaterial({ color: ink, transparent: true, opacity: 0.95 })
      );
      const fill = new THREE.Mesh(
        box,
        new THREE.MeshBasicMaterial({ color: 0xffffff })
      );
      const g = new THREE.Group();
      g.add(fill); g.add(wire);
      g.position.set(0, i * stepH - 0.8, -i * stepD);
      root.add(g);
      steps.push(g);
    }

    // Beige accent sphere sitting on one step (Fichier 49's orange circle)
    const accentBall = new THREE.Mesh(
      new THREE.SphereGeometry(0.28, 28, 24),
      new THREE.MeshBasicMaterial({ color: accent })
    );
    accentBall.position.set(-0.6, stepCount * stepH - 0.8 - stepH / 2 + 0.28, -(stepCount - 1) * stepD);
    root.add(accentBall);
    const accentOutline = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.IcosahedronGeometry(0.3, 1)),
      new THREE.LineBasicMaterial({ color: ink, transparent: true, opacity: 0.5 })
    );
    accentOutline.position.copy(accentBall.position);
    root.add(accentOutline);

    // Ambient data dots climbing the steps
    const dotMat = new THREE.MeshBasicMaterial({ color: ink });
    const climbers = [];
    for (let i = 0; i < 14; i++) {
      const m = new THREE.Mesh(new THREE.SphereGeometry(0.06, 12, 10), dotMat);
      m.userData.phase = Math.random() * Math.PI * 2;
      m.userData.lane = (Math.random() - 0.5) * (stepW - 0.4);
      root.add(m);
      climbers.push(m);
    }

    // Side projection ticks (chart axis suggestion)
    const tickMat = new THREE.LineBasicMaterial({ color: ink, transparent: true, opacity: 0.4 });
    for (let i = 0; i < stepCount; i++) {
      const y = i * stepH - 0.8;
      const tick = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(-stepW / 2 - 0.2, y + stepH / 2, 0.3),
          new THREE.Vector3(-stepW / 2 - 0.5, y + stepH / 2, 0.3),
        ]),
        tickMat
      );
      root.add(tick);
    }

    const start = performance.now();
    function animate() {
      const t = (performance.now() - start) / 1000;
      if (!reducedMotion) {
        root.rotation.y = Math.sin(t * 0.3) * 0.4 - 0.2;
        accentBall.position.y += Math.sin(t * 1.4) * 0.0018;
        accentOutline.position.y = accentBall.position.y;
        accentOutline.rotation.y = t * 0.6;
        accentOutline.rotation.x = t * 0.4;
        climbers.forEach((m, i) => {
          const u = ((t * 0.22 + i / climbers.length) % 1);
          const stepIdx = Math.min(stepCount - 1, Math.floor(u * stepCount));
          const stepProgress = (u * stepCount) - stepIdx;
          const y = stepIdx * stepH - 0.8 + stepH / 2 + 0.1;
          const z = -stepIdx * stepD + stepD / 2 - stepProgress * 0.1;
          m.position.set(m.userData.lane, y, z);
          m.material.opacity = 0.9;
        });
      }
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    }
    animate();
    return;
  }

  // ====== CYLINDER (Fichier 45 barrel/database) ======
  if (kind === 'cylinder') {
    camera.position.set(0, 0.2, 5.2);

    // Main wireframe barrel
    const barrelGeo = new THREE.CylinderGeometry(1.2, 1.2, 2.4, 36, 6, false);
    const barrel = new THREE.LineSegments(
      new THREE.EdgesGeometry(barrelGeo),
      new THREE.LineBasicMaterial({ color: ink, transparent: true, opacity: 0.85 })
    );
    root.add(barrel);

    // Top and bottom ellipse rings for database-look
    const topRing = new THREE.Mesh(
      new THREE.TorusGeometry(1.2, 0.02, 8, 48),
      new THREE.MeshBasicMaterial({ color: ink })
    );
    topRing.position.y = 1.2; topRing.rotation.x = Math.PI / 2;
    const botRing = topRing.clone();
    botRing.position.y = -1.2;
    root.add(topRing, botRing);

    // Grey rectangular highlight overlay (Fichier 45's grey square)
    const overlay = new THREE.Mesh(
      new THREE.PlaneGeometry(1.4, 1.4),
      new THREE.MeshBasicMaterial({ color: 0xd6d6d6, transparent: true, opacity: 0.9, side: THREE.DoubleSide })
    );
    overlay.position.set(0.1, 0.1, 0);
    root.add(overlay);
    const overlayEdge = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.PlaneGeometry(1.4, 1.4)),
      new THREE.LineBasicMaterial({ color: ink, transparent: true, opacity: 0.95 })
    );
    overlayEdge.position.copy(overlay.position);
    root.add(overlayEdge);

    // Internal data lines (horizontal slices suggesting records)
    const slicesGroup = new THREE.Group();
    for (let i = 0; i < 7; i++) {
      const y = -1.0 + i * 0.33;
      const pts = [];
      for (let a = 0; a <= 64; a++) {
        const ang = (a / 64) * Math.PI * 2;
        pts.push(new THREE.Vector3(Math.cos(ang) * 1.2, y, Math.sin(ang) * 1.2));
      }
      const ring = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(pts),
        new THREE.LineBasicMaterial({ color: ink, transparent: true, opacity: 0.18 })
      );
      slicesGroup.add(ring);
    }
    root.add(slicesGroup);

    // Streaming data particles flowing through the barrel
    const particleCount = 36;
    const particles = [];
    const partMat = new THREE.MeshBasicMaterial({ color: ink });
    for (let i = 0; i < particleCount; i++) {
      const p = new THREE.Mesh(new THREE.SphereGeometry(0.04, 10, 8), partMat);
      p.userData.angle = Math.random() * Math.PI * 2;
      p.userData.radius = 1.2 + (Math.random() - 0.5) * 0.08;
      p.userData.y = (Math.random() * 2 - 1) * 1.1;
      p.userData.speed = 0.4 + Math.random() * 0.6;
      root.add(p);
      particles.push(p);
    }

    // Vertical streaming beams above + below
    const beamGroup = new THREE.Group();
    for (let i = 0; i < 5; i++) {
      const x = -0.8 + i * 0.4;
      const beam = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(x, 1.2, 0.3),
          new THREE.Vector3(x, 2.0, 0.3),
        ]),
        new THREE.LineBasicMaterial({ color: ink, transparent: true, opacity: 0.5 })
      );
      beamGroup.add(beam);
      const beam2 = beam.clone();
      beam2.geometry = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(x, -1.2, 0.3),
        new THREE.Vector3(x, -2.0, 0.3),
      ]);
      beamGroup.add(beam2);
    }
    root.add(beamGroup);

    const start = performance.now();
    function animate() {
      const t = (performance.now() - start) / 1000;
      if (!reducedMotion) {
        barrel.rotation.y = t * 0.35;
        slicesGroup.rotation.y = t * 0.2;
        topRing.rotation.z = t * 0.6;
        botRing.rotation.z = -t * 0.6;
        particles.forEach((p, i) => {
          p.userData.angle += 0.02 * p.userData.speed;
          p.userData.y += 0.012 * p.userData.speed;
          if (p.userData.y > 1.2) p.userData.y = -1.2;
          p.position.set(
            Math.cos(p.userData.angle) * p.userData.radius,
            p.userData.y,
            Math.sin(p.userData.angle) * p.userData.radius
          );
          p.material.opacity = 0.7 + Math.sin(t * 2 + i) * 0.3;
        });
        beamGroup.children.forEach((b, i) => {
          b.material.opacity = 0.2 + (Math.sin(t * 3 + i * 0.7) * 0.5 + 0.5) * 0.6;
        });
      }
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    }
    animate();
    return;
  }
}

/* -------- Hero auto-cycle: each animation runs its full natural loop + 1s pause -------- */
function initSliderHero() {
  const hero = document.getElementById('sliderHero');
  if (!hero) return;
  const frames = Array.from(hero.querySelectorAll('.hsplit-frame'));
  if (frames.length < 2) return;

  // Natural loop durations of the embedded animations
  //   chess.html  → CONFIG.duration (4000) + holdAtEnd (600) = 4600 ms
  //   highlight.svg → CSS keyframes @ 8s
  const NATURAL = { strategise: 4600, highlight: 8000 };
  const PAUSE = 1000;

  let idx = 0;
  const advance = () => {
    frames.forEach((f, n) => f.classList.toggle('is-active', n === idx));
    const key = frames[idx].dataset.hsKey;
    const dwell = (NATURAL[key] || 5000) + PAUSE;
    setTimeout(() => { idx = (idx + 1) % frames.length; advance(); }, dwell);
  };
  advance();
}

/* -------- Legacy slider mechanics retained as no-op stub -------- */
function _initSliderHeroLegacy() {
  const hero = document.getElementById('sliderHero');
  if (!hero) return;
  const frames  = Array.from(hero.querySelectorAll('.hsplit-frame'));
  const labels  = Array.from(hero.querySelectorAll('.hsplit-label'));
  const num     = hero.querySelector('[data-hs-num]');
  const fill    = hero.querySelector('[data-hs-fill]');
  const prev    = hero.querySelector('.hsplit-prev');
  const next    = hero.querySelector('.hsplit-next');
  if (frames.length < 2) return;

  const total = frames.length;
  let idx = 0;
  let timer = null;
  const INTERVAL = 5000;

  const setIndex = (i) => {
    idx = (i + total) % total;
    frames.forEach((f, n) => f.classList.toggle('is-active', n === idx));
    labels.forEach((l, n) => l.classList.toggle('is-active', n === idx));
    if (num) num.textContent = String(idx + 1).padStart(2, '0');
    if (fill) {
      const pct = 100 / total;
      fill.style.width = pct + '%';
      fill.style.transform = `translateX(${idx * 100}%)`;
    }
  };
  const advance = () => setIndex(idx + 1);
  const start = () => {
    if (reducedMotion) return;
    stop();
    timer = setInterval(advance, INTERVAL);
  };
  const stop = () => { if (timer) { clearInterval(timer); timer = null; } };

  prev?.addEventListener('click', (e) => { e.stopPropagation(); setIndex(idx - 1); start(); });
  next?.addEventListener('click', (e) => { e.stopPropagation(); setIndex(idx + 1); start(); });

  // Click on visual stage → advance
  hero.querySelector('.hsplit-stage')?.addEventListener('click', () => { advance(); start(); });

  // Touch swipe support
  const stage = hero.querySelector('.hsplit-stage');
  if (stage) {
    let sx = 0;
    stage.addEventListener('touchstart', (e) => { sx = e.touches[0].clientX; }, { passive: true });
    stage.addEventListener('touchend', (e) => {
      const dx = (e.changedTouches[0].clientX) - sx;
      if (Math.abs(dx) > 40) { setIndex(idx + (dx < 0 ? 1 : -1)); start(); }
    });
  }

  // Pause when offscreen
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => { if (en.isIntersecting) start(); else stop(); });
  }, { threshold: 0.2 });
  io.observe(hero);

  setIndex(0);
}

/* -------- v2: discreet blue cursor + cursor-positioned section gradient -------- */
function initV2ColourLayer() {
  if (!document.body.classList.contains('v2')) return;
  const cursor = document.querySelector('.v2-cursor');

  window.addEventListener('pointermove', (e) => {
    if (cursor) {
      cursor.style.transform = `translate(${e.clientX}px, ${e.clientY}px) translate(-50%, -50%)`;
      cursor.classList.add('is-on');
    }
    const sec = e.target.closest('section');
    if (sec) {
      const r = sec.getBoundingClientRect();
      sec.style.setProperty('--mx', ((e.clientX - r.left) / r.width * 100) + '%');
      sec.style.setProperty('--my', ((e.clientY - r.top) / r.height * 100) + '%');
    }
  });
  window.addEventListener('pointerleave', () => cursor?.classList.remove('is-on'));
  document.addEventListener('mouseleave', () => cursor?.classList.remove('is-on'));
}

/* -------- v3: cursor-revealed grid (no halo) -------- */
function initV3GridLayer() {
  if (!document.body.classList.contains('v3')) return;
  const reveal = document.querySelector('.v3-reveal');
  const dot = document.querySelector('.v3-dot');
  const root = document.documentElement;
  let lastX = window.innerWidth / 2, lastY = window.innerHeight / 2;

  // Coalesce pointermove to one style update per frame (a full-screen gradient
  // layer repaints on every --gx/--gy change; unthrottled this janks on move).
  let movePending = false;
  window.addEventListener('pointermove', (e) => {
    lastX = e.clientX; lastY = e.clientY;
    if (movePending) return;
    movePending = true;
    requestAnimationFrame(() => {
      movePending = false;
      root.style.setProperty('--gx', lastX + 'px');
      root.style.setProperty('--gy', lastY + 'px');
      if (dot) dot.style.transform = `translate(${lastX}px, ${lastY}px) translate(-50%, -50%)`;
      if (reveal) reveal.classList.add('is-on');
    });
  }, { passive: true });
  document.addEventListener('mouseleave', () => reveal?.classList.remove('is-on'));

  // Pulse pings every ~2.5s near the cursor — creates "footstep" feel on the grid
  setInterval(() => {
    if (reducedMotion) return;
    const ping = document.createElement('span');
    ping.className = 'v3-ping';
    const jx = lastX + (Math.random() - 0.5) * 80;
    const jy = lastY + (Math.random() - 0.5) * 80;
    ping.style.left = jx + 'px';
    ping.style.top = jy + 'px';
    document.body.appendChild(ping);
    setTimeout(() => ping.remove(), 1400);
  }, 2500);
}

/* -------- Init scenes on load -------- */
window.addEventListener('DOMContentLoaded', () => {
  initV2ColourLayer();
  // initV3GridLayer(); // grille d'arrière-plan retirée
  initSliderHero(); // now auto-cycles on every variant

  document.querySelectorAll('[data-three="tier"]').forEach((c) => initTierScene(c, c.dataset.kind));
  document.querySelectorAll('[data-three="expertise"]').forEach((c) => initExpertiseScene(c, c.dataset.kind));
  document.querySelectorAll('[data-three="pillar"]').forEach((c) => initPillarScene(c, c.dataset.kind));

  document.querySelectorAll('[data-year]').forEach((el) => { el.textContent = new Date().getFullYear(); });
});

/* -------- Interactive map (territoires page) -------- */
window.initInteractiveMap = function initInteractiveMap() {
  const svg = document.querySelector('#world-map-svg');
  const panel = document.querySelector('#map-panel');
  if (!svg || !panel) return;

  const getLang = () => (window.getLanguage && window.getLanguage()) || 'fr';
  const pickLocalized = (v) => (v && typeof v === 'object' && !Array.isArray(v)) ? (v[getLang()] || v.fr || v.en) : v;

  let activePoint = null;

  const renderPanel = (pt) => {
    if (!pt) return;
    const data = JSON.parse(pt.dataset.region);
    const lang = getLang();
    const dict = (window.I18N && window.I18N[lang]) || {};
    panel.querySelector('.eyebrow-slot').textContent = data.continent;
    panel.querySelector('.name-slot').textContent = pickLocalized(data.name);
    const statusEl = panel.querySelector('.status');
    const directLabel = dict['territ.status.direct'] || 'Présence directe';
    const partnerLabel = dict['territ.status.partner'] || 'Réseau partenaires';
    statusEl.textContent = data.status === 'direct' ? directLabel : partnerLabel;
    statusEl.classList.toggle('partner', data.status !== 'direct');
    const ul = panel.querySelector('.caps-slot');
    ul.innerHTML = '';
    const caps = pickLocalized(data.capabilities) || [];
    caps.forEach((c) => {
      const li = document.createElement('li');
      li.textContent = c;
      ul.appendChild(li);
    });
    panel.classList.add('active');
  };

  const points = svg.querySelectorAll('.map-point');
  points.forEach((pt) => {
    pt.addEventListener('click', () => {
      activePoint = pt;
      renderPanel(pt);
      points.forEach(p => p.classList.remove('active'));
      pt.classList.add('active');
    });
  });

  // Re-render on language change
  window.addEventListener('languagechange', () => {
    if (activePoint) renderPanel(activePoint);
  });

  // Open France by default
  const first = svg.querySelector('.map-point-group[data-open="true"] .map-point') || svg.querySelector('.map-point');
  if (first) {
    activePoint = first;
    renderPanel(first);
    first.classList.add('active');
  }
};

/* -------- Logo wall: filtres par secteur -------- */
(function logoFilters() {
  const bar = document.querySelector('.logo-filters');
  if (!bar) return;
  const slots = [...document.querySelectorAll('.logo-slot')];
  const buttons = [...bar.querySelectorAll('.logo-filter')];
  function apply(cat) {
    slots.forEach((s) => s.classList.toggle('is-hidden', cat !== 'all' && s.dataset.cat !== cat));
    buttons.forEach((b) => b.classList.toggle('is-active', b.dataset.filter === cat));
  }
  bar.addEventListener('click', (e) => {
    const b = e.target.closest('.logo-filter');
    if (b) apply(b.dataset.filter);
  });
  const init = bar.querySelector('.logo-filter.is-active') || buttons[0];
  if (init) apply(init.dataset.filter);
})();

/* -------- Pages secteur : carrousel logos 4 par 4 -------- */
(function logoQuad() {
  document.querySelectorAll('.logo-quad').forEach(function (q) {
    var pool = Array.prototype.slice.call(q.querySelectorAll('.logo-quad-pool img'));
    var row = q.querySelector('.logo-quad-row');
    if (!pool.length || !row) return;
    var N = 4, idx = 0, slots = [];
    for (var i = 0; i < N; i++) {
      var im = document.createElement('img');
      im.className = 'logo-quad-slot';
      im.loading = 'lazy';
      row.appendChild(im);
      slots.push(im);
    }
    function apply(start) {
      for (var i = 0; i < N; i++) {
        var ref = pool[(start + i) % pool.length];
        slots[i].src = ref.getAttribute('src');
        slots[i].alt = ref.getAttribute('alt') || '';
        slots[i].style.setProperty('--b', ref.style.getPropertyValue('--b') || '');
      }
    }
    apply(0);
    if (pool.length <= N) return; // pas de rotation si 4 logos ou moins
    var interval = parseInt(q.getAttribute('data-interval') || '3200', 10);
    setInterval(function () {
      if (document.hidden) return;
      row.classList.add('is-out');
      setTimeout(function () {
        idx = (idx + N) % pool.length;
        apply(idx);
        row.classList.remove('is-out');
      }, 400);
    }, interval);
  });
})();
