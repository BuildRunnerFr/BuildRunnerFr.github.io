(function () {
  'use strict';
  var root = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var each = function (list, fn) { Array.prototype.forEach.call(list, fn); };

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
  each(document.querySelectorAll('[data-lang-link]'), function (a) {
    a.addEventListener('click', function () {
      if (location.hash) a.href = a.getAttribute('href').split('#')[0] + location.hash;
    });
  });

  /* Apparitions au défilement */
  var reveals = document.querySelectorAll('.reveal');
  if (reduce || !('IntersectionObserver' in window)) {
    each(reveals, function (el) { el.classList.add('is-in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    each(reveals, function (el) { io.observe(el); });
  }

  /* Lien de navigation actif */
  var navLinks = {};
  each(document.querySelectorAll('[data-nav]'), function (a) { navLinks[a.dataset.nav] = a; });
  var sections = document.querySelectorAll('main > section[id]');
  function setActive() {
    var line = window.innerHeight * 0.4;
    var current = '';
    each(sections, function (s) {
      if (s.offsetParent !== null && s.getBoundingClientRect().top <= line) current = s.id;
    });
    Object.keys(navLinks).forEach(function (id) {
      if (id === current) navLinks[id].setAttribute('aria-current', 'true');
      else navLinks[id].removeAttribute('aria-current');
    });
  }

  /* Parcours : le fil se colore à mesure qu'on descend */
  var steps = document.querySelectorAll('.step[data-kind]');
  function setSteps() {
    var line = window.innerHeight * 0.62;
    each(steps, function (st) {
      if (st.offsetParent !== null) st.classList.toggle('is-past', st.getBoundingClientRect().top < line);
    });
  }

  /* Barre de progression sous le menu */
  var bar = document.querySelector('.progress');
  function setProgress() {
    var max = root.scrollHeight - window.innerHeight;
    if (bar) bar.style.setProperty('--sp', max > 0 ? Math.min(1, window.scrollY / max).toFixed(4) : 0);
    root.classList.toggle('is-scrolled', window.scrollY > 8);
  }

  /* Chiffres : ils comptent jusqu'à leur valeur quand ils apparaissent */
  var counters = document.querySelectorAll('[data-count]');
  if (!reduce && 'IntersectionObserver' in window) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var end = parseInt(el.dataset.count, 10);
        var start = null;
        cio.unobserve(el);
        if (!(end > 0)) return;
        function step(ts) {
          if (start === null) start = ts;
          var k = Math.min(1, (ts - start) / 1200);
          el.textContent = Math.round(end * (1 - Math.pow(1 - k, 3)));
          if (k < 1) requestAnimationFrame(step);
        }
        el.textContent = '0';
        requestAnimationFrame(step);
      });
    }, { threshold: 0.6 });
    each(counters, function (el) { cio.observe(el); });
  }

  /* Boutons aimantés : ils suivent très légèrement le pointeur */
  if (!reduce && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    each(document.querySelectorAll('.btn'), function (btn) {
      btn.addEventListener('pointermove', function (e) {
        var r = btn.getBoundingClientRect();
        btn.style.setProperty('--mx', ((e.clientX - r.left - r.width / 2) * 0.16).toFixed(1) + 'px');
        btn.style.setProperty('--my', ((e.clientY - r.top - r.height / 2) * 0.24).toFixed(1) + 'px');
      });
      btn.addEventListener('pointerleave', function () {
        btn.style.removeProperty('--mx');
        btn.style.removeProperty('--my');
      });
    });
  }

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      setActive();
      setSteps();
      setProgress();
      ticking = false;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  setActive();
  setSteps();
  setProgress();

  /* Filtres : onglets du parcours, catégories des projets */
  function chipGroup(buttons, apply) {
    each(buttons, function (btn) {
      btn.addEventListener('click', function () {
        each(buttons, function (b) { b.setAttribute('aria-pressed', String(b === btn)); });
        apply(btn);
      });
    });
  }
  chipGroup(document.querySelectorAll('.chipbtn[data-tab]'), function (btn) {
    var kind = btn.dataset.tab, last = null;
    each(steps, function (st) {
      st.hidden = kind !== 'all' && st.dataset.kind !== kind;
      st.classList.add('is-in');
      st.classList.remove('is-last');
      if (!st.hidden) last = st;
    });
    if (last) last.classList.add('is-last');
    setSteps();
  });
  var cards = document.querySelectorAll('.pc[data-cats]');
  chipGroup(document.querySelectorAll('.chipbtn[data-cat]'), function (btn) {
    var cat = btn.dataset.cat;
    each(cards, function (card) {
      card.hidden = cat !== 'all' && card.dataset.cats.split(' ').indexOf(cat) < 0;
      card.classList.add('is-in');
    });
  });

  /* Thème clair ou sombre : celui du système par défaut, puis le choix du visiteur, retenu d'une visite à l'autre */
  var themeBtn = document.querySelector('[data-theme-toggle]');
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var current = root.getAttribute('data-theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      var next = current === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) { /* le choix vaut pour cette visite */ }
    });
  }

  /* Copier l'adresse e-mail */
  var copy = document.querySelector('.copy');
  var status = document.querySelector('.copy__status');
  if (copy && navigator.clipboard) {
    copy.addEventListener('click', function () {
      navigator.clipboard.writeText(copy.dataset.copy).then(function () {
        status.textContent = copy.dataset.done;
        setTimeout(function () { status.textContent = ''; }, 2600);
      }).catch(function () { /* presse-papiers refusé : l'adresse reste affichée et sélectionnable */ });
    });
  } else if (copy) {
    copy.hidden = true;
  }

  /* Compétences : chaque ligne défile en boucle, à vitesse constante, une ligne sur deux dans l'autre sens.
     Sans script ou si le visiteur préfère moins de mouvement, les pastilles restent simplement posées. */
  var marquees = document.querySelectorAll('[data-marquee]');
  if (!reduce && marquees.length) {
    var fillAll = function () {
      each(marquees, function (box, idx) {
        var track = box.querySelector('.marquee__track');
        var list = box.querySelector('ul');
        if (!track) {
          track = document.createElement('div');
          track.className = 'marquee__track';
          box.appendChild(track);
          track.appendChild(list);
          box.classList.add('is-live');
          if (idx % 2) box.classList.add('marquee--rev');
        }
        while (track.children.length > 1) track.removeChild(track.lastChild);
        var w = list.getBoundingClientRect().width;
        if (!w) return;
        var copies = Math.ceil(box.clientWidth / w) + 1;
        for (var i = 0; i < copies; i++) {
          var clone = list.cloneNode(true);
          clone.setAttribute('aria-hidden', 'true');
          track.appendChild(clone);
        }
        track.style.setProperty('--shift', (-w).toFixed(1) + 'px');
        track.style.animationDuration = (w / 34).toFixed(1) + 's';
      });
    };
    fillAll();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(fillAll);
    var refill = 0;
    window.addEventListener('resize', function () { clearTimeout(refill); refill = setTimeout(fillAll, 200); });
  }
})();
