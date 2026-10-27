/* =========================================================================
   A Little Universe, Just for You — behaviour
   -------------------------------------------------------------------------
   1. Intro entrance (waits for fonts so the title never "jumps")
   2. Moon image loading states (slow network / missing file)
   3. Starfield (sparse, almost still)
   4. Touching the moon → light → glide to the letter
   5. Paragraphs are observed while reading; CSS reveals each as she scrolls to it
   No dependencies. Everything degrades gracefully: without JavaScript the
   letter is simply shown below the moon.
   ========================================================================= */
(function () {
  "use strict";

  if ("scrollRestoration" in history) history.scrollRestoration = "manual";

  var root = document.documentElement;
  var body = document.body;
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* Timing of the main interaction, in ms. Tweak here. */
  var TIMING = {
    lightUp: 900,      // moon brightens before the page starts to move
    glide: 2200,       // duration of the scroll down to the letter
  };

  var moon = document.querySelector(".moon");
  var moonImg = document.querySelector(".moon__img");
  var letter = document.getElementById("letter");
  var letterTitle = document.getElementById("letter-title");

  /* ---------------------------------------------------------------------
     1. Intro entrance
     --------------------------------------------------------------------- */
  function startIntro() {
    if (root.classList.contains("is-ready")) return;
    root.classList.add("is-ready");
  }

  if (document.fonts && document.fonts.ready) {
    // Never wait more than 1.2 s: on a slow connection we prefer
    // fallback fonts to a blank screen.
    Promise.race([
      document.fonts.ready,
      new Promise(function (resolve) { setTimeout(resolve, 1200); }),
    ]).then(startIntro);
  } else {
    startIntro();
  }

  /* ---------------------------------------------------------------------
     2. Moon image states
     --------------------------------------------------------------------- */
  function markLoaded() {
    moon.classList.add("is-loaded");
  }
  function markMissing() {
    moon.classList.add("is-missing");
  }

  if (moonImg.complete && moonImg.naturalWidth > 0) {
    markLoaded();
  } else {
    moonImg.addEventListener("load", function () {
      // decode() avoids a half-painted image popping in on slow phones
      if (moonImg.decode) {
        moonImg.decode().then(markLoaded, markLoaded);
      } else {
        markLoaded();
      }
    });
    moonImg.addEventListener("error", markMissing);
    // Already failed before this script ran?
    if (moonImg.complete && moonImg.naturalWidth === 0) markMissing();
  }

  /* ---------------------------------------------------------------------
     3. Starfield
     A few dozen points, most perfectly still; a handful breathe very slowly
     and the whole field drifts about 1px every few seconds.
     --------------------------------------------------------------------- */
  var sky = document.querySelector(".sky");
  var ctx = sky.getContext ? sky.getContext("2d") : null;
  var stars = [];
  var skyW = 0;
  var skyH = 0;
  var dpr = 1;
  var rafId = 0;

  function seededRandom(seed) {
    // deterministic, so the sky is the same every visit
    return function () {
      seed = (seed * 16807) % 2147483647;
      return (seed - 1) / 2147483646;
    };
  }

  function buildStars() {
    var rand = seededRandom(20261026);
    var area = skyW * skyH;
    // ~1 star per 9 000 px², capped: "very discreet"
    var count = Math.min(140, Math.max(40, Math.round(area / 9000)));
    stars = [];
    for (var i = 0; i < count; i++) {
      var bright = rand();
      stars.push({
        x: rand(),
        y: rand(),
        r: bright > 0.96 ? 1.05 : bright > 0.8 ? 0.75 : 0.5,
        a: bright > 0.96 ? 0.75 : 0.18 + rand() * 0.32,
        twinkle: rand() < 0.18,
        phase: rand() * Math.PI * 2,
        speed: 0.00025 + rand() * 0.0004,
      });
    }
  }

  function resizeSky() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    skyW = window.innerWidth;
    skyH = window.innerHeight;
    sky.width = Math.round(skyW * dpr);
    sky.height = Math.round(skyH * dpr);
    buildStars();
    drawSky(performance.now());
  }

  function drawSky(t) {
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, skyW, skyH);
    var still = reduceMotion.matches;
    var drift = still ? 0 : t * 0.0012; // px — imperceptible from moment to moment
    for (var i = 0; i < stars.length; i++) {
      var s = stars[i];
      var alpha = s.a;
      if (s.twinkle && !still) {
        alpha *= 0.55 + 0.45 * Math.sin(s.phase + t * s.speed);
      }
      var x = (s.x * skyW + drift * (0.4 + s.r)) % skyW;
      var y = s.y * skyH;
      ctx.beginPath();
      ctx.arc(x, y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(226, 231, 238," + alpha.toFixed(3) + ")";
      ctx.fill();
    }
  }

  function loop(t) {
    drawSky(t);
    rafId = requestAnimationFrame(loop);
  }

  function startSky() {
    cancelAnimationFrame(rafId);
    if (reduceMotion.matches) {
      drawSky(0);
    } else {
      rafId = requestAnimationFrame(loop);
    }
  }

  if (ctx) {
    resizeSky();
    startSky();
    var resizeTimer = 0;
    window.addEventListener("resize", function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(resizeSky, 150);
    });
    // Save battery: stop drawing while the tab is hidden.
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) cancelAnimationFrame(rafId);
      else startSky();
    });
    if (reduceMotion.addEventListener) {
      reduceMotion.addEventListener("change", startSky);
    }
  }

  /* ---------------------------------------------------------------------
     4. Touching the moon
     --------------------------------------------------------------------- */
  var opened = false;
  var glideId = 0;

  function easeInOutCubic(x) {
    return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
  }

  // Our own scroll so the pace is slow and even on every browser.
  // Any touch, wheel or key from the reader interrupts it immediately.
  function glideTo(targetY, duration, done) {
    cancelAnimationFrame(glideId);
    var startY = window.pageYOffset;
    var distance = targetY - startY;

    if (reduceMotion.matches || Math.abs(distance) < 2) {
      window.scrollTo(0, targetY);
      if (done) done();
      return;
    }

    var startT = null;
    var cancelled = false;
    function cancel() { cancelled = true; }
    var opts = { passive: true, once: true };
    window.addEventListener("wheel", cancel, opts);
    window.addEventListener("touchstart", cancel, opts);
    window.addEventListener("keydown", cancel, opts);

    function step(t) {
      if (cancelled) { finish(); return; }
      if (startT === null) startT = t;
      var p = Math.min(1, (t - startT) / duration);
      window.scrollTo(0, startY + distance * easeInOutCubic(p));
      if (p < 1) glideId = requestAnimationFrame(step);
      else finish();
    }
    function finish() {
      window.removeEventListener("wheel", cancel);
      window.removeEventListener("touchstart", cancel);
      window.removeEventListener("keydown", cancel);
      if (done) done();
    }
    glideId = requestAnimationFrame(step);
  }

  function letterTop() {
    // Stop with the lower edge of the moon still glowing at the top of the
    // screen, so the thread of light visibly falls from it to the first verse.
    var moonBottom = moon.getBoundingClientRect().bottom + window.pageYOffset;
    var target = moonBottom - window.innerHeight * 0.13;
    var max = document.documentElement.scrollHeight - window.innerHeight;
    return Math.max(0, Math.min(target, max));
  }

  function goToLetter() {
    glideTo(letterTop(), TIMING.glide, function () {
      // Move focus for keyboard and screen-reader users without jumping.
      try { letterTitle.focus({ preventScroll: true }); }
      catch (e) { /* very old browsers: focus is optional */ }
    });
  }

  function openLetter() {
    if (opened) {
      // Second touch: just glide back to the letter, no repeated effect.
      goToLetter();
      return;
    }
    opened = true;

    moon.classList.add("is-lit");
    body.classList.add("is-lit-page");
    moon.setAttribute("aria-expanded", "true");
    var label = moon.querySelector(".moon__label");
    if (label) label.textContent = "Go to the letter";

    var wait = reduceMotion.matches ? 0 : TIMING.lightUp;
    setTimeout(function () {
      body.classList.add("is-open");
      // Let the browser lay the letter out once before animating it.
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          body.classList.add("is-unveiled");
          observeReveals();
          goToLetter();
        });
      });
    }, wait);
  }

  // <button> already turns Enter / Space / tap / click into "click".
  moon.addEventListener("click", openLetter);

  /* ---------------------------------------------------------------------
     5. Reveal while reading
     --------------------------------------------------------------------- */
  function observeReveals() {
    var targets = document.querySelectorAll(".reveal, .finale, .signature");

    if (!("IntersectionObserver" in window)) {
      for (var i = 0; i < targets.length; i++) targets[i].classList.add("is-visible");
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    }, {
      // a stanza appears once it is comfortably inside the screen
      rootMargin: "0px 0px -12% 0px",
      threshold: 0.2,
    });

    for (var j = 0; j < targets.length; j++) io.observe(targets[j]);
  }

  // If the page is restored already scrolled (back/forward cache, reload),
  // make sure nothing stays invisible.
  window.addEventListener("pageshow", function (e) {
    if (e.persisted && opened) observeReveals();
  });
})();
