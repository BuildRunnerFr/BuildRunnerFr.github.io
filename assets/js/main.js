(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Menu mobile */
  var toggle = document.querySelector('.nav__toggle');
  var links = document.getElementById('nav-links');
  function closeMenu() {
    links.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
  }
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
    });
    links.addEventListener('click', function (e) {
      if (e.target.closest('a')) closeMenu();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && links.classList.contains('is-open')) {
        closeMenu();
        toggle.focus();
      }
    });
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.nav')) closeMenu();
    });
  }

  /* Le sélecteur de langue garde la section en cours */
  document.querySelectorAll('[data-lang-link]').forEach(function (a) {
    a.addEventListener('click', function () {
      if (location.hash) a.href = a.getAttribute('href').split('#')[0] + location.hash;
    });
  });

  /* Apparitions au scroll */
  var reveals = document.querySelectorAll('.reveal');
  if (reduce || !('IntersectionObserver' in window)) {
    reveals.forEach(function (el) { el.classList.add('is-in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      var n = 0;
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.style.setProperty('--d', (n++ * 0.08) + 's');
        entry.target.classList.add('is-in');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    reveals.forEach(function (el) { io.observe(el); });
  }

  /* Lien de navigation actif */
  var navLinks = {};
  document.querySelectorAll('[data-nav]').forEach(function (a) { navLinks[a.dataset.nav] = a; });
  var sections = document.querySelectorAll('main > section[id]');
  function setActive() {
    var line = window.innerHeight * 0.4;
    var current = '';
    sections.forEach(function (s) {
      if (s.offsetParent !== null && s.getBoundingClientRect().top <= line) current = s.id;
    });
    Object.keys(navLinks).forEach(function (id) {
      if (id === current) navLinks[id].setAttribute('aria-current', 'true');
      else navLinks[id].removeAttribute('aria-current');
    });
  }

  /* La ligne des expériences se remplit avec le scroll */
  var path = document.querySelector('.path');
  var thread = document.querySelector('.path__line');
  function setThread() {
    if (!path || !thread || reduce) return;
    var r = path.getBoundingClientRect();
    var p = (window.innerHeight * 0.7 - r.top) / r.height;
    thread.style.setProperty('--p', Math.max(0, Math.min(1, p)).toFixed(4));
  }

  /* Filtre des outils par domaine */
  var filters = document.querySelectorAll('.filter');
  var groups = document.querySelectorAll('.group');
  filters.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var key = btn.dataset.filter;
      filters.forEach(function (b) { b.setAttribute('aria-pressed', String(b === btn)); });
      groups.forEach(function (g) {
        g.hidden = key !== 'all' && g.dataset.group !== key;
        g.classList.add('is-in');
      });
    });
  });

  /* Barre de progression (repli quand les animations liées au scroll en CSS manquent) */
  var bar = document.querySelector('.progress span');
  var cssScroll = window.CSS && CSS.supports && CSS.supports('animation-timeline: scroll()');
  function setProgress() {
    if (!bar || cssScroll || reduce) return;
    var max = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.setProperty('--sp', max > 0 ? (window.scrollY / max).toFixed(4) : 0);
  }

  /* Chiffres clés : comptent jusqu'à leur valeur quand ils apparaissent */
  var counters = document.querySelectorAll('[data-count]');
  if (!reduce && 'IntersectionObserver' in window) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var end = parseInt(el.dataset.count, 10);
        var start = null;
        cio.unobserve(el);
        function step(ts) {
          if (start === null) start = ts;
          var k = Math.min(1, (ts - start) / 1100);
          el.textContent = Math.round(end * (1 - Math.pow(1 - k, 3)));
          if (k < 1) requestAnimationFrame(step);
        }
        el.textContent = '0';
        requestAnimationFrame(step);
      });
    }, { threshold: 0.6 });
    counters.forEach(function (el) { cio.observe(el); });
  }

  /* Boutons aimantés : ils suivent légèrement le pointeur */
  if (!reduce && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    document.querySelectorAll('.btn').forEach(function (btn) {
      btn.addEventListener('pointermove', function (e) {
        var r = btn.getBoundingClientRect();
        btn.style.setProperty('--mx', ((e.clientX - r.left - r.width / 2) * 0.22).toFixed(1) + 'px');
        btn.style.setProperty('--my', ((e.clientY - r.top - r.height / 2) * 0.32).toFixed(1) + 'px');
      });
      btn.addEventListener('pointerleave', function () {
        btn.style.removeProperty('--mx');
        btn.style.removeProperty('--my');
      });
    });
  }

  /* Cartes de projets : légère inclinaison sous le pointeur */
  if (!reduce && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    document.querySelectorAll('.project').forEach(function (card) {
      card.addEventListener('pointermove', function (e) {
        var r = card.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width - 0.5;
        var y = (e.clientY - r.top) / r.height - 0.5;
        card.style.setProperty('--ry', (x * 3).toFixed(2) + 'deg');
        card.style.setProperty('--rx', (-y * 3).toFixed(2) + 'deg');
      });
      card.addEventListener('pointerleave', function () {
        card.style.removeProperty('--rx');
        card.style.removeProperty('--ry');
      });
    });
  }

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      setActive();
      setThread();
      setProgress();
      ticking = false;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  setActive();
  setThread();

  /* Copier l'adresse e-mail */
  var copy = document.querySelector('.copy');
  var status = document.querySelector('.copy__status');
  if (copy && navigator.clipboard) {
    copy.addEventListener('click', function () {
      navigator.clipboard.writeText(copy.dataset.copy).then(function () {
        status.textContent = copy.dataset.done;
        setTimeout(function () { status.textContent = ''; }, 2600);
      });
    });
  } else if (copy) {
    copy.hidden = true;
  }

  /* Piano : un petit synthé, joué au clic, au toucher ou au clavier. Aucun son sans geste du visiteur. */
  var piano = document.querySelector('.piano');
  var AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (piano && !AudioCtx) {
    piano.hidden = true;
  } else if (piano) {
    var actx = null;
    var bus = null;
    var pianoKeys = Array.prototype.slice.call(piano.querySelectorAll('[data-note]'));
    pianoKeys.sort(function (a, b) { return a.dataset.note - b.dataset.note; });
    var byNote = {};
    pianoKeys.forEach(function (k) { byNote[k.dataset.note] = k; });

    var audio = function () {
      if (!actx) {
        actx = new AudioCtx();
        bus = actx.createDynamicsCompressor();
        var master = actx.createGain();
        master.gain.value = 0.7;
        bus.connect(master);
        master.connect(actx.destination);
      }
      if (actx.state === 'suspended') actx.resume();
      return actx;
    };

    /* Une note : quelques harmoniques, attaque rapide, longue extinction */
    var sound = function (midi) {
      var c = audio();
      var t = c.currentTime;
      var f = 440 * Math.pow(2, (midi - 69) / 12);
      var env = c.createGain();
      env.gain.setValueAtTime(0.0001, t);
      env.gain.exponentialRampToValueAtTime(0.5, t + 0.012);
      env.gain.exponentialRampToValueAtTime(0.16, t + 0.28);
      env.gain.exponentialRampToValueAtTime(0.0001, t + 1.9);
      var tone = c.createBiquadFilter();
      tone.type = 'lowpass';
      tone.frequency.setValueAtTime(f * 6, t);
      tone.frequency.exponentialRampToValueAtTime(f * 2, t + 1.2);
      [[1, 1, 'triangle'], [2, 0.3, 'sine'], [3, 0.12, 'sine'], [4.01, 0.05, 'sine']].forEach(function (h) {
        var osc = c.createOscillator();
        var level = c.createGain();
        osc.type = h[2];
        osc.frequency.value = f * h[0];
        level.gain.value = h[1];
        osc.connect(level);
        level.connect(tone);
        osc.start(t);
        osc.stop(t + 2);
      });
      tone.connect(env);
      env.connect(bus);
    };

    var press = function (key) {
      if (!key) return;
      sound(+key.dataset.note);
      key.classList.add('is-down');
      setTimeout(function () { key.classList.remove('is-down'); }, 190);
    };

    /* Une seule touche dans l'ordre de tabulation ; les flèches passent de l'une à l'autre */
    var focusKey = function (key) {
      pianoKeys.forEach(function (k) { k.tabIndex = k === key ? 0 : -1; });
      key.focus({ preventScroll: true });
    };

    /* Exemple : le début de l'Ode à la joie (domaine public) */
    var demo = document.querySelector('[data-demo]');
    var tune = [[64, 1], [64, 1], [65, 1], [67, 1], [67, 1], [65, 1], [64, 1], [62, 1], [60, 1], [60, 1], [62, 1], [64, 1], [64, 1.5], [62, 0.5], [62, 2]];
    var timer = null;
    var stopDemo = function () {
      clearTimeout(timer);
      timer = null;
      if (demo) demo.setAttribute('aria-pressed', 'false');
    };
    var playDemo = function (i) {
      if (i >= tune.length) { stopDemo(); return; }
      press(byNote[tune[i][0]]);
      timer = setTimeout(function () { playDemo(i + 1); }, tune[i][1] * 400);
    };
    if (demo) {
      demo.addEventListener('click', function () {
        if (timer) { stopDemo(); return; }
        demo.setAttribute('aria-pressed', 'true');
        playDemo(0);
      });
    }

    var last = null;
    piano.addEventListener('pointerdown', function (e) {
      var key = e.target.closest('[data-note]');
      if (!key) return;
      if (key.hasPointerCapture && key.hasPointerCapture(e.pointerId)) key.releasePointerCapture(e.pointerId);
      stopDemo();
      last = key;
      press(key);
      pianoKeys.forEach(function (k) { k.tabIndex = k === key ? 0 : -1; });
    });
    /* glisser d'une touche à l'autre, bouton ou doigt enfoncé */
    piano.addEventListener('pointerover', function (e) {
      var key = e.target.closest('[data-note]');
      if (!key || key === last) return;
      if (e.pointerType === 'mouse' ? e.buttons !== 1 : e.pressure === 0) return;
      last = key;
      press(key);
    });
    ['pointerup', 'pointercancel', 'pointerleave'].forEach(function (type) {
      piano.addEventListener(type, function () { last = null; });
    });
    /* clavier et lecteurs d'écran : le clic natif du bouton (Entrée, Espace) */
    piano.addEventListener('click', function (e) {
      var key = e.target.closest('[data-note]');
      if (key && e.detail === 0) { stopDemo(); press(key); }
    });
    var codes = { KeyA: 60, KeyW: 61, KeyS: 62, KeyE: 63, KeyD: 64, KeyF: 65, KeyT: 66, KeyG: 67, KeyY: 68, KeyH: 69, KeyU: 70, KeyJ: 71, KeyK: 72, KeyO: 73, KeyL: 74, KeyP: 75, Semicolon: 76 };
    piano.addEventListener('keydown', function (e) {
      var key = e.target.closest('[data-note]');
      if (!key || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        var shown = pianoKeys.filter(function (k) { return k.offsetParent !== null; });
        var next = shown[shown.indexOf(key) + (e.key === 'ArrowRight' ? 1 : -1)];
        if (next) focusKey(next);
        e.preventDefault();
      } else if (codes[e.code] && !e.repeat) {
        var target = byNote[codes[e.code]];
        if (target && target.offsetParent !== null) { stopDemo(); press(target); }
      }
    });
  }
})();
