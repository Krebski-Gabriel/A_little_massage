/* =========================================================================
   Autumn — falling leaves tied to the reading (experimental, autumn.html)
   -------------------------------------------------------------------------
   The leaves belong to the page's progress, not to a timer:
     A  opening    nothing until the moon is touched, then only a stray leaf
     B  reading    more leaves as she scrolls through the letter
     C  the end    the ground of leaves builds up (3 layers), falling leaves
                   settle into it
   New leaves come from a "budget" filled by scrolling (px) and, more slowly,
   by time — so if she stops to read, the air calms down but never freezes.

   Cost: at most 22 leaves (12 on phones), drawn from one sprite atlas on
   two canvases; scroll is read once per frame; nothing runs before the
   moon is touched, while the tab is hidden, or with reduced motion.
   Works alongside script.js without changing it.
   ========================================================================= */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var body = document.body;
  var back = document.querySelector(".leaves--back");
  var front = document.querySelector(".leaves--front");
  var ground = document.querySelector(".ground");
  if (!back || !back.getContext || !ground) return;

  var bctx = back.getContext("2d");
  var fctx = front ? front.getContext("2d") : null;

  /* ---------------------------------------------------------- settings */
  var small = Math.min(window.innerWidth, window.innerHeight) < 600;
  var MAX_LEAVES = small ? 12 : 22;
  var DENSITY = small ? 0.8 : 1;          // fewer leaves on phones
  var TILE = 128;                          // atlas tile size
  var KINDS = 12;                          // leaves in the atlas
  // atlas rows: 0 front, 1 back, 2 front blurred, 3 back blurred

  /* ---------------------------------------------------------- state */
  var atlas = null;
  var leaves = [];
  var started = false;
  var running = false;
  var last = 0;
  var budget = 0;
  var W = 0, H = 0, dpr = 1;
  var scrollY = window.pageYOffset, lastScrollY = scrollY, maxScroll = 1;
  var groundTop = 0, groundH = 0;          // page coordinates, cached

  function rnd(a, b) { return a + Math.random() * (b - a); }
  function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
  function smooth(x) { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); }

  /* ---------------------------------------------------------- layout */
  function measure() {
    dpr = Math.min(window.devicePixelRatio || 1, small ? 1.5 : 2);
    W = window.innerWidth;
    H = window.innerHeight;
    [back, front].forEach(function (c) {
      if (!c) return;
      c.width = Math.round(W * dpr);
      c.height = Math.round(H * dpr);
    });
    maxScroll = Math.max(1, document.documentElement.scrollHeight - H);
    var r = ground.getBoundingClientRect();
    groundTop = r.top + window.pageYOffset;
    groundH = r.height;
  }

  /* progress through the letter, 0 → 1 */
  function progress() { return clamp(scrollY / maxScroll, 0, 1); }

  /* leaves per second (time) and per 1000 px scrolled, by progress */
  function timeRate(p) {
    if (p < 0.06) return 0.05;                                  // A: a stray leaf
    if (p < 0.55) return 0.05 + (p - 0.06) / 0.49 * 0.45;       // B: more and more
    if (p < 0.9) return 0.5 + (p - 0.55) / 0.35 * 0.2;          // C: the most
    return 0.55;
  }
  function scrollRate(p) { return 1.5 + 7 * smooth(p / 0.85); }

  /* ---------------------------------------------------------- ground */
  function updateGround() {
    // the pile builds up over the last part of the scroll
    var remaining = maxScroll - scrollY;
    var win = Math.max(groundH, H * 0.6);
    var a = clamp(1 - remaining / win, 0, 1);
    ground.style.setProperty("--g1", smooth(a / 0.4).toFixed(3));
    ground.style.setProperty("--g2", smooth((a - 0.3) / 0.4).toFixed(3));
    ground.style.setProperty("--g3", smooth((a - 0.62) / 0.38).toFixed(3));
  }

  /* ---------------------------------------------------------- leaves */
  function spawn() {
    var p = progress();
    var z = Math.random();                       // 0 far … 1 near
    var inFront = fctx && W >= 700 && Math.random() < 0.12;
    var x;
    if (inFront) {
      z = rnd(0.92, 1);
      x = Math.random() < 0.5 ? rnd(-0.04, 0.12) * W : rnd(0.88, 1.04) * W;
    } else {
      z = Math.min(z, 0.9);
      // prefer the sides, away from the column of text
      x = Math.random() < 0.6
        ? (Math.random() < 0.5 ? rnd(-0.05, 0.3) : rnd(0.7, 1.05)) * W
        : rnd(0, 1) * W;
    }
    var size = (small ? 20 : 30) + z * (small ? 26 : 48) + (inFront ? 50 : 0);
    leaves.push({
      kind: (Math.random() * KINDS) | 0,
      front: inFront,
      z: z,
      x: x,
      y: Math.random() < 0.35 ? rnd(0.02, 0.3) * H : -size - rnd(0, 40),
      size: size * rnd(0.85, 1.15),
      vy: (22 + 38 * z) * rnd(0.8, 1.2) * (inFront ? 1.3 : 1),
      drift: rnd(-8, 14),                         // a light night breeze to the right
      swayA: rnd(14, 34) * (0.6 + z),
      swayW: rnd(0.7, 1.3),
      phase: rnd(0, 6.28),
      rot: rnd(0, 6.28),
      rotV: rnd(-0.9, 0.9),
      flip: rnd(0, 6.28),
      flipV: rnd(0.9, 2.0) * (Math.random() < 0.5 ? -1 : 1),
      alpha: 0,
      peak: (0.5 + 0.45 * z) * (inFront ? 0.7 : 1) * rnd(0.85, 1.05),
      t: 0,
      landY: null,
      landed: 0,
    });
    // far and near leaves are out of focus
    var l = leaves[leaves.length - 1];
    l.blur = l.front || l.z < 0.12;
    void p;
  }

  function step(dt) {
    var p = progress();
    // the top of the pile, in screen coordinates
    var surface = groundTop + groundH * 0.2 - scrollY;
    var dy = scrollY - lastScrollY;
    lastScrollY = scrollY;

    // budget: scrolling brings leaves, time brings a few more
    budget += (timeRate(p) * dt + Math.abs(dy) / 1000 * scrollRate(p)) * DENSITY;
    while (budget >= 1) {
      budget -= 1;
      if (leaves.length < MAX_LEAVES) spawn();
    }

    for (var i = leaves.length - 1; i >= 0; i--) {
      var l = leaves[i];
      l.t += dt;
      // the leaves are in the scene: when she scrolls, nearer ones move more
      l.y -= dy * (0.06 + 0.18 * l.z);
      if (l.landed > 0) {
        l.landed += dt;
        l.alpha = l.peak * (1 - clamp(l.landed / 1.4, 0, 1));
        if (l.landed > 1.4) { leaves.splice(i, 1); }
        continue;
      }
      var s = Math.sin(l.phase + l.t * l.swayW);
      // a leaf glides sideways and drops faster when it turns edge-on
      l.y += l.vy * (0.7 + 0.6 * Math.abs(Math.cos(l.phase + l.t * l.swayW))) * dt;
      l.x += (l.drift + l.swayA * l.swayW * Math.cos(l.phase + l.t * l.swayW)) * dt;
      l.rot += (l.rotV + 0.6 * s) * dt;
      l.flip += l.flipV * dt;
      l.alpha = Math.min(l.peak, l.alpha + dt * 0.45);   // fades in, never pops
      // settle into the ground when it is on screen
      if (!l.front && surface < H) {
        if (l.landY === null) l.landY = surface + rnd(0.05, 0.55) * groundH;
        if (l.y >= l.landY) { l.landed = 0.0001; continue; }
      }
      if (l.y > H + 80 || l.x < -120 || l.x > W + 120 || l.y < -260) leaves.splice(i, 1);
    }
  }

  function draw() {
    bctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    bctx.clearRect(0, 0, W, H);
    if (fctx) {
      fctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      fctx.clearRect(0, 0, W, H);
    }
    for (var i = 0; i < leaves.length; i++) {
      var l = leaves[i];
      if (l.alpha <= 0.005) continue;
      var ctx = l.front ? fctx : bctx;
      var c = Math.cos(l.flip);
      var row = (c < 0 ? 1 : 0) + (l.blur ? 2 : 0);
      var sx = 0.22 + 0.78 * Math.abs(c);          // turning in 3D (never a hairline)
      var sy = 0.82 + 0.18 * Math.abs(Math.sin(l.flip * 0.5 + l.phase));
      ctx.save();
      ctx.globalAlpha = l.alpha * (0.75 + 0.25 * sx);  // edge-on catches less light
      ctx.translate(l.x, l.y);
      ctx.rotate(l.rot);
      ctx.scale(sx, sy);
      ctx.drawImage(atlas, l.kind * TILE, row * TILE, TILE, TILE,
        -l.size / 2, -l.size / 2, l.size, l.size);
      ctx.restore();
    }
  }

  function frame(t) {
    if (!running) return;
    var dt = Math.min(0.05, (t - last) / 1000 || 0.016);
    last = t;
    scrollY = window.pageYOffset;
    step(dt);
    draw();
    requestAnimationFrame(frame);
  }

  function run() {
    if (running || !atlas || document.hidden) return;
    running = true;
    last = performance.now();
    lastScrollY = window.pageYOffset;
    requestAnimationFrame(frame);
  }
  function pause() { running = false; }

  /* ---------------------------------------------------------- ground only */
  var groundQueued = false;
  function onScroll() {
    if (groundQueued) return;
    groundQueued = true;
    requestAnimationFrame(function () {
      groundQueued = false;
      scrollY = window.pageYOffset;
      updateGround();
    });
  }

  /* ---------------------------------------------------------- start */
  function start() {
    if (started) return;
    started = true;
    // wait for the letter to be laid out before measuring
    requestAnimationFrame(function () {
      measure();
      updateGround();
      window.addEventListener("scroll", onScroll, { passive: true });
      var resizeTimer = 0;
      window.addEventListener("resize", function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () { measure(); updateGround(); }, 150);
      });
      // the letter grows as paragraphs appear and fonts settle: re-measure
      if ("ResizeObserver" in window) {
        new ResizeObserver(function () { measure(); updateGround(); }).observe(document.body);
      }
      if (reduceMotion.matches) return;          // the ground only, no motion
      atlas = new Image();
      atlas.decoding = "async";
      atlas.onload = run;
      atlas.src = "assets/autumn/leaves.webp";
      document.addEventListener("visibilitychange", function () {
        if (document.hidden) pause(); else run();
      });
      if (reduceMotion.addEventListener) {
        reduceMotion.addEventListener("change", function () {
          if (reduceMotion.matches) { pause(); leaves = []; draw(); } else run();
        });
      }
    });
  }

  // for testing in the browser console: __autumn.count()
  window.__autumn = { count: function () { return leaves.length; } };

  // Phase A: nothing falls until the moon has been touched and the letter is open.
  if (body.classList.contains("is-open")) {
    start();
  } else if ("MutationObserver" in window) {
    var mo = new MutationObserver(function () {
      if (body.classList.contains("is-open")) { mo.disconnect(); start(); }
    });
    mo.observe(body, { attributes: true, attributeFilter: ["class"] });
  }
})();
