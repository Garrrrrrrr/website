/* ============================================================================
   Hero renderer

   A working ray tracer, ported from the C renderer listed in Selected Work.
   Ray-sphere and ray-plane intersection, Lambertian diffuse with a Blinn-Phong
   specular term, and hard shadows from a single point light.

   It renders in four progressive passes (1/8, 1/4, 1/2, then full resolution)
   under a per-frame time budget, so the main thread is never blocked. It runs
   once and stops. The only way to see it again is the Re-render control, which
   is a deliberate user action rather than a loop.
   ========================================================================= */

(function () {
  'use strict';

  var stage = document.querySelector('[data-render]');
  if (!stage) return;

  var canvas = stage.querySelector('.render__canvas');
  var bar = stage.querySelector('.render__bar');
  var replay = stage.querySelector('[data-render-replay]');
  var progress = stage.querySelector('.render__progress');
  if (!canvas || !canvas.getContext) return;

  var ctx = canvas.getContext('2d', { alpha: false });
  if (!ctx) return;

  /* -- vector helpers ----------------------------------------------------- */

  function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function add(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }
  function scale(a, t) { return [a[0] * t, a[1] * t, a[2] * t]; }
  function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function norm(a) {
    var l = Math.sqrt(dot(a, a)) || 1;
    return [a[0] / l, a[1] / l, a[2] / l];
  }

  /* -- scene -------------------------------------------------------------- */

  var CAMERA = [0, 1.05, -3.6];
  var LIGHT = [-2.4, 4.2, -2.0];
  var FOV = Math.tan((46 * Math.PI) / 180 / 2);
  var PLANE_Y = 0;
  var EPS = 0.0012;

  var spheres = [
    { c: [-1.15, 0.55, 0.45], r: 0.55, albedo: [0.05, 0.36, 0.29], spec: 0.35, shine: 48 },
    { c: [0.28, 0.88, 1.35], r: 0.88, albedo: [0.82, 0.82, 0.80], spec: 0.55, shine: 96 },
    { c: [1.62, 0.42, 0.15], r: 0.42, albedo: [0.30, 0.31, 0.34], spec: 0.28, shine: 32 }
  ];

  /* Sky and ground read from the active theme so the render belongs to the
     page it sits on rather than fighting it. These are the light-theme
     fallbacks used if the tokens cannot be read. */
  var palette = { skyTop: [0.90, 0.90, 0.88], skyLow: [0.99, 0.99, 0.98],
                  tileA: [0.86, 0.86, 0.84], tileB: [0.78, 0.78, 0.76] };

  function readPalette() {
    var cs = getComputedStyle(document.documentElement);
    var sunken = parseColor(cs.getPropertyValue('--surface-sunken'));
    var surface = parseColor(cs.getPropertyValue('--surface'));
    var accent = parseColor(cs.getPropertyValue('--accent'));
    var ink = parseColor(cs.getPropertyValue('--ink'));
    if (!sunken || !surface || !accent || !ink) return;

    // The scene is built out of the theme's own surface tokens, so it belongs
    // to the panel it sits in. Light and dark need separate weights rather
    // than one shared formula: on light the tiles have to be pulled down from
    // a near-white ground, on dark they have to be lifted off a near-black
    // one, and the same numbers cannot do both without the scene either
    // washing out or disappearing.
    var BLACK = [0, 0, 0], WHITE = [1, 1, 1];
    spheres[0].albedo = accent;

    if (luminance(surface) < 0.2) {
      palette.skyTop = mix(sunken, ink, 0.012);
      palette.skyLow = mix(surface, ink, 0.004);
      palette.tileA = mix(sunken, ink, 0.018);
      palette.tileB = mix(sunken, ink, 0.075);
      spheres[1].albedo = mix(sunken, ink, 0.55);
      spheres[2].albedo = mix(sunken, ink, 0.10);
    } else {
      palette.skyTop = mix(sunken, BLACK, 0.06);
      palette.skyLow = surface;
      palette.tileA = mix(sunken, surface, 0.5);
      palette.tileB = mix(sunken, BLACK, 0.14);
      spheres[1].albedo = mix(surface, WHITE, 0.2);
      spheres[2].albedo = mix(sunken, BLACK, 0.35);
    }
  }

  /* Theme tokens are sRGB. Lighting has to happen in linear space or the
     result comes out washed out, so colours are linearised on the way in and
     gamma-encoded once on the way out. */
  var GAMMA = 2.2;
  function toLinear(c) { return Math.pow(c, GAMMA); }

  function parseColor(v) {
    v = (v || '').trim();
    if (!v) return null;
    var rgb = null;
    var m = v.match(/^#([0-9a-f]{6})$/i);
    if (m) {
      var n = parseInt(m[1], 16);
      rgb = [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
    } else {
      m = v.match(/rgba?\(([^)]+)\)/);
      if (m) {
        var p = m[1].split(/[\s,\/]+/).filter(Boolean).map(parseFloat);
        if (p.length >= 3) rgb = [p[0] / 255, p[1] / 255, p[2] / 255];
      }
    }
    if (!rgb) return null;
    return [toLinear(rgb[0]), toLinear(rgb[1]), toLinear(rgb[2])];
  }

  /* Relative luminance of an already-linear colour. Used only to decide which
     way the theme leans. */
  function luminance(c) {
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }

  function mix(a, b, t) {
    return [a[0] + (b[0] - a[0]) * t,
            a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t];
  }

  /* The literals above are written in sRGB for readability. Linearise them
     once so the fallback path matches the token path. */
  (function lineariseDefaults() {
    ['skyTop', 'skyLow', 'tileA', 'tileB'].forEach(function (k) {
      palette[k] = palette[k].map(toLinear);
    });
    spheres.forEach(function (s) { s.albedo = s.albedo.map(toLinear); });
  })();

  /* -- intersection ------------------------------------------------------- */

  function hitSphere(o, d, s) {
    var oc = sub(o, s.c);
    var b = dot(oc, d);
    var c = dot(oc, oc) - s.r * s.r;
    var disc = b * b - c;
    if (disc < 0) return Infinity;
    var sq = Math.sqrt(disc);
    var t = -b - sq;
    if (t > EPS) return t;
    t = -b + sq;
    return t > EPS ? t : Infinity;
  }

  function hitPlane(o, d) {
    if (Math.abs(d[1]) < 1e-6) return Infinity;
    var t = (PLANE_Y - o[1]) / d[1];
    return t > EPS ? t : Infinity;
  }

  function trace(o, d) {
    var best = Infinity, obj = null, isPlane = false;

    for (var i = 0; i < spheres.length; i++) {
      var t = hitSphere(o, d, spheres[i]);
      if (t < best) { best = t; obj = spheres[i]; isPlane = false; }
    }
    var tp = hitPlane(o, d);
    if (tp < best && tp < 26) { best = tp; obj = null; isPlane = true; }

    if (best === Infinity) {
      // Sky. A vertical ramp between two theme colours, no hard horizon.
      var t2 = Math.min(1, Math.max(0, d[1] * 1.9 + 0.28));
      return mix(palette.skyLow, palette.skyTop, t2);
    }

    var p = add(o, scale(d, best));
    var n, albedo, spec, shine;

    if (isPlane) {
      n = [0, 1, 0];
      var checker = (Math.floor(p[0] * 1.1) + Math.floor(p[2] * 1.1)) & 1;
      albedo = checker ? palette.tileA : palette.tileB;
      // Fade the floor into the sky so the plane has no visible cut-off edge.
      var fade = Math.min(1, Math.max(0, (best - 7) / 16));
      albedo = mix(albedo, palette.skyLow, fade);
      spec = 0.06; shine = 16;
    } else {
      n = norm(sub(p, obj.c));
      albedo = obj.albedo;
      spec = obj.spec; shine = obj.shine;
    }

    var toLight = sub(LIGHT, p);
    var dist = Math.sqrt(dot(toLight, toLight));
    var l = scale(toLight, 1 / dist);

    // Hard shadow: one ray toward the light, occluded or not.
    var lit = 1;
    for (var j = 0; j < spheres.length; j++) {
      if (hitSphere(p, l, spheres[j]) < dist) { lit = 0; break; }
    }

    var diff = Math.max(0, dot(n, l)) * lit;
    var ambient = 0.34;

    var h = norm(sub(l, d));
    var specular = lit && diff > 0
      ? Math.pow(Math.max(0, dot(n, h)), shine) * spec
      : 0;

    var k = ambient + diff * 0.78;
    return [
      Math.min(1, albedo[0] * k + specular),
      Math.min(1, albedo[1] * k + specular),
      Math.min(1, albedo[2] * k + specular)
    ];
  }

  /* -- progressive driver ------------------------------------------------- */

  var W = 0, H = 0, image = null;
  var PASSES = [8, 4, 2, 1];
  var passIndex = 0, y = 0, running = false, rafId = 0;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');

  function resize() {
    var rect = stage.querySelector('.render__stage').getBoundingClientRect();
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    // Cap the traced resolution. Beyond this the cost stops buying detail.
    var cssW = Math.max(240, Math.min(rect.width, 560));
    W = Math.round(cssW * dpr);
    H = Math.round((W * 3) / 4);
    canvas.width = W;
    canvas.height = H;
    image = ctx.createImageData(W, H);
  }

  function renderRow(row, step) {
    var aspect = W / H;
    for (var x = 0; x < W; x += step) {
      var u = ((x + step / 2) / W * 2 - 1) * FOV * aspect;
      var v = (1 - (row + step / 2) / H * 2) * FOV;
      var col = trace(CAMERA, norm([u, v, 1]));

      var r = Math.round(Math.pow(col[0], 1 / GAMMA) * 255);
      var g = Math.round(Math.pow(col[1], 1 / GAMMA) * 255);
      var b = Math.round(Math.pow(col[2], 1 / GAMMA) * 255);

      // Fill the whole step block so coarse passes read as a real preview.
      for (var by = 0; by < step && row + by < H; by++) {
        var base = ((row + by) * W + x) * 4;
        for (var bx = 0; bx < step && x + bx < W; bx++) {
          var o = base + bx * 4;
          image.data[o] = r;
          image.data[o + 1] = g;
          image.data[o + 2] = b;
          image.data[o + 3] = 255;
        }
      }
    }
  }

  function setProgress(fraction) {
    if (bar) bar.style.width = Math.round(fraction * 100) + '%';
  }

  function finish() {
    running = false;
    stage.classList.add('is-complete');
    setProgress(1);
    if (progress) progress.setAttribute('aria-hidden', 'true');
    canvas.setAttribute('aria-busy', 'false');
    if (replay) replay.hidden = false;
  }

  function frame() {
    var budget = performance.now() + 9;

    while (performance.now() < budget) {
      var step = PASSES[passIndex];
      renderRow(y, step);
      y += step;

      if (y >= H) {
        ctx.putImageData(image, 0, 0);
        passIndex++;
        y = 0;
        if (passIndex >= PASSES.length) {
          finish();
          return;
        }
      }
    }

    ctx.putImageData(image, 0, 0);
    // Weight progress by pass so the bar tracks real work, not row count.
    var done = passIndex / PASSES.length;
    setProgress(done + (y / H) / PASSES.length);
    rafId = requestAnimationFrame(frame);
  }

  function renderAll() {
    for (var p = 0; p < PASSES.length; p++) {
      for (var row = 0; row < H; row += PASSES[p]) renderRow(row, PASSES[p]);
    }
    ctx.putImageData(image, 0, 0);
    finish();
  }

  function start() {
    if (running) cancelAnimationFrame(rafId);
    readPalette();
    resize();
    stage.classList.remove('is-complete');
    canvas.setAttribute('aria-busy', 'true');
    if (replay) replay.hidden = true;
    passIndex = 0;
    y = 0;
    setProgress(0);

    if (reduced.matches) {
      // No animated passes. Compute the finished frame and paint it once.
      renderAll();
      stage.classList.add('is-live');
      return;
    }

    // Paint the coarsest pass synchronously before revealing the canvas, so
    // it never shows an empty frame in place of the static fallback.
    for (var row = 0; row < H; row += PASSES[0]) renderRow(row, PASSES[0]);
    ctx.putImageData(image, 0, 0);
    stage.classList.add('is-live');
    passIndex = 1;
    setProgress(1 / PASSES.length);

    running = true;
    rafId = requestAnimationFrame(frame);
  }

  if (replay) {
    replay.addEventListener('click', function () { start(); });
  }

  // Re-render on theme change so the scene keeps matching the page.
  window.addEventListener('themechange', function () {
    if (stage.classList.contains('is-complete') || running) start();
  });

  // Only start once the panel is actually on screen.
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting) { io.disconnect(); start(); }
    }, { rootMargin: '120px' });
    io.observe(stage);
  } else {
    start();
  }

  // Expose for the OG image build, which needs to await a finished frame.
  window.__renderComplete = function () {
    return stage.classList.contains('is-complete');
  };
})();
