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
      if (s.getBoundingClientRect().top <= line) current = s.id;
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
})();
