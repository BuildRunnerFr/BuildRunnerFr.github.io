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

  /* Lignes qui défilent (compétences, étagère de mangas) : en boucle, à vitesse constante, une ligne sur deux dans l'autre sens.
     On peut les faire défiler à la main : glisser à la souris ou au doigt (avec un peu d'élan), molette horizontale,
     flèches de l'étagère. Au survol, la ligne ralentit jusqu'à s'arrêter.
     Les copies qui font la boucle ne sont créées que lorsque la ligne approche de l'écran : une image copiée se
     télécharge tout de suite, et il ne faut pas charger toute l'étagère dès l'ouverture de la page.
     Sans script, ou si le visiteur préfère moins de mouvement, les éléments restent simplement posés. */
  var marquees = document.querySelectorAll('[data-marquee]');
  if (!reduce && marquees.length) {
    var rows = [];
    var wrap = function (row) { if (row.w) row.x = ((row.x % row.w) - row.w) % row.w; };
    var fill = function (row) {
      var track = row.track, list = row.list;
      while (track.children.length > 1) track.removeChild(track.lastChild);
      var w = list.getBoundingClientRect().width;
      if (!w) return;
      var copies = Math.ceil(row.box.clientWidth / w) + 1;
      for (var i = 0; i < copies; i++) {
        var clone = list.cloneNode(true);
        clone.setAttribute('aria-hidden', 'true');
        track.appendChild(clone);
      }
      each(track.querySelectorAll('img[loading="lazy"]'), function (img) { img.loading = 'eager'; });
      row.w = w;
      wrap(row);
    };
    each(marquees, function (box, idx) {
      var list = box.querySelector('ul');
      var track = document.createElement('div');
      track.className = 'marquee__track';
      track.appendChild(list);
      box.appendChild(track);
      box.classList.add('is-live');
      var dir = idx % 2 ? 1 : -1;
      var row = { box: box, track: track, list: list, w: 0, x: 0, dir: dir, speed: parseFloat(box.dataset.speed) || 34,
                  vel: dir * (parseFloat(box.dataset.speed) || 34), hover: false, drag: null, glide: 0, near: false, seen: false };
      rows.push(row);

      box.addEventListener('pointerenter', function (e) { if (e.pointerType === 'mouse') row.hover = true; });
      box.addEventListener('pointerleave', function () { row.hover = false; });
      box.addEventListener('pointerdown', function (e) {
        if (e.pointerType === 'mouse' && e.button !== 0) return;
        row.drag = { x0: e.clientX, off: row.x, last: e.clientX, t: performance.now(), v: 0, id: e.pointerId, moved: false };
        row.glide = 0;
      });
      box.addEventListener('pointermove', function (e) {
        var d = row.drag;
        if (!d || d.id !== e.pointerId) return;
        var dx = e.clientX - d.x0;
        if (!d.moved && Math.abs(dx) > 4) {
          d.moved = true;
          box.classList.add('is-dragging');
          try { box.setPointerCapture(e.pointerId); } catch (err) { /* sans capture, le glisser marche tant que le pointeur reste sur la ligne */ }
        }
        if (!d.moved) return;
        var now = performance.now(), dt = Math.max(1, now - d.t);
        d.v = 0.8 * ((e.clientX - d.last) / dt * 1000) + 0.2 * d.v;
        d.last = e.clientX; d.t = now;
        row.x = d.off + dx;
        wrap(row);
      });
      var release = function (e) {
        var d = row.drag;
        if (!d || (e && d.id !== e.pointerId)) return;
        if (d.moved) row.vel = Math.max(-2600, Math.min(2600, d.v));
        row.drag = null;
        box.classList.remove('is-dragging');
      };
      box.addEventListener('pointerup', release);
      box.addEventListener('pointercancel', release);
      box.addEventListener('lostpointercapture', release);
      box.addEventListener('dragstart', function (e) { e.preventDefault(); });
      box.addEventListener('wheel', function (e) {
        if (Math.abs(e.deltaX) <= Math.abs(e.deltaY)) return;     // la molette verticale fait défiler la page, comme d'habitude
        e.preventDefault();
        row.x -= e.deltaX;
        row.vel = 0;
        wrap(row);
      }, { passive: false });
    });

    // flèches de l'étagère : un grand pas, en douceur
    each(document.querySelectorAll('[data-nudge]'), function (btn) {
      var box = btn.closest('.shelf').querySelector('[data-marquee]');
      btn.addEventListener('click', function () {
        var row = rows.filter(function (r) { return r.box === box; })[0];
        if (row) { row.glide -= parseFloat(btn.dataset.nudge) * box.clientWidth * 0.6; row.vel = 0; }
      });
    });

    var last = 0, running = false;
    var tick = function (t) {
      var dt = Math.min(0.05, (t - (last || t)) / 1000);
      last = t;
      var any = false;
      rows.forEach(function (row) {
        if (!row.seen || !row.w) return;
        any = true;
        if (row.drag) {
          row.track.style.transform = 'translate3d(' + row.x.toFixed(2) + 'px,0,0)';
          return;
        }
        if (Math.abs(row.glide) > 0.5) {
          var step = row.glide * Math.min(1, dt * 7);
          row.x += step; row.glide -= step;
        } else {
          row.glide = 0;
          var aim = row.hover ? 0 : row.dir * row.speed;
          row.vel += (aim - row.vel) * Math.min(1, dt * (Math.abs(row.vel) > row.speed * 1.5 ? 2.2 : 3.5));
          row.x += row.vel * dt;
        }
        wrap(row);
        row.track.style.transform = 'translate3d(' + row.x.toFixed(2) + 'px,0,0)';
      });
      if (any) requestAnimationFrame(tick);
      else { running = false; last = 0; }
    };
    var run = function () { if (!running) { running = true; requestAnimationFrame(tick); } };

    if ('IntersectionObserver' in window) {
      var near = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          near.unobserve(entry.target);
          var row = rows.filter(function (r) { return r.box === entry.target; })[0];
          row.near = true;
          fill(row);
        });
      }, { rootMargin: '600px 0px' });
      var seen = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var row = rows.filter(function (r) { return r.box === entry.target; })[0];
          row.seen = entry.isIntersecting;
        });
        run();
      });
      rows.forEach(function (row) { near.observe(row.box); seen.observe(row.box); });
    } else {
      rows.forEach(function (row) { row.near = row.seen = true; fill(row); });
      run();
    }
    var refillNear = function () { rows.forEach(function (row) { if (row.near) fill(row); }); run(); };
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(refillNear);
    var refill = 0;
    window.addEventListener('resize', function () { clearTimeout(refill); refill = setTimeout(refillNear, 200); });
  }
})();
