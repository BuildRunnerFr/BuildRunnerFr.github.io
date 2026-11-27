/* Version jeu : une discussion à choix avec Ethan, et une carte de son parcours à explorer.
   La version classique reste dans la page ; on passe de l'une à l'autre sans rechargement. */
(function () {
  'use strict';
  var root = document.documentElement;
  var stage = document.getElementById('play');
  var raw = document.getElementById('play-data');
  if (!stage || !raw) return;
  var data = JSON.parse(raw.textContent);
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (id) { return document.getElementById(id); };
  var each = function (list, fn) { Array.prototype.forEach.call(list, fn); };

  /* ---------- jeu ou classique ---------- */
  var talkStarted = false;
  function closeMenu() {
    var links = $('nav-links');
    var toggle = document.querySelector('.nav__toggle');
    if (links) links.classList.remove('is-open');
    if (toggle) toggle.setAttribute('aria-expanded', 'false');
  }
  function setMode(mode, keepScroll) {
    root.setAttribute('data-mode', mode);
    try { localStorage.setItem('mode', mode); } catch (e) { /* stockage indisponible : le choix vaut pour cette visite */ }
    closeMenu();
    if (mode === 'play') {
      if (!talkStarted) say('start');
      if (scene === 'map') layoutMap();
    }
    if (!keepScroll) window.scrollTo(0, 0);
    window.dispatchEvent(new Event('scroll'));
  }
  function mode() { return root.getAttribute('data-mode'); }
  /* vers une section de la version classique */
  function toClassic(id) {
    setMode('classic', !!id);
    if (!id) return;
    var target = document.getElementById(id);
    if (!target) return;
    try { history.replaceState(null, '', '#' + id); } catch (e) { /* sans importance */ }
    requestAnimationFrame(function () { target.scrollIntoView(); });
  }
  each(document.querySelectorAll('[data-mode-switch]'), function (b) {
    b.addEventListener('click', function () {
      if (mode() === 'play') setMode('classic');
      else { try { history.replaceState(null, '', location.pathname); } catch (e) { /* idem */ } setMode('play'); }
    });
  });
  each(document.querySelectorAll('[data-mode-set]'), function (b) {
    b.addEventListener('click', function () {
      if (b.getAttribute('data-mode-set') === 'play') { try { history.replaceState(null, '', location.pathname); } catch (e) { /* idem */ } }
      setMode(b.getAttribute('data-mode-set'));
    });
  });
  /* depuis le jeu, un lien du menu ouvre la section voulue en version classique */
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href^="#"]');
    if (!a || mode() !== 'play') return;
    var id = a.getAttribute('href').slice(1);
    if (id === 'home' || id === '') { e.preventDefault(); showScene('talk'); window.scrollTo(0, 0); closeMenu(); return; }
    if (id === 'main' || !document.getElementById(id)) return;
    setMode('classic', true);
  });
  window.addEventListener('hashchange', function () {
    var id = location.hash.slice(1);
    if (id === 'jeu' || id === 'play') setMode('play');
    else if (id && document.getElementById(id) && mode() === 'play') setMode('classic', true);
  });

  /* ---------- les deux scènes ---------- */
  var scene = 'talk';
  function showScene(name, focus) {
    scene = name;
    each(stage.querySelectorAll('.scene'), function (s) { s.hidden = s.getAttribute('data-scene') !== name; });
    if (name === 'map') { layoutMap(); if (focus) $('map-title').focus({ preventScroll: true }); }
    if (name === 'talk' && focus) $('talk-say').focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }
  each(stage.querySelectorAll('[data-scene-go]'), function (b) {
    b.addEventListener('click', function () { showScene(b.getAttribute('data-scene-go'), true); });
  });

  /* une cible de bouton : une réplique, la carte, la version classique ou un lien */
  function follow(target) {
    if (target === '@map') showScene('map', true);
    else if (target === '@classic') toClassic('');
    else if (target.indexOf('@classic#') === 0) toClassic(target.slice(9));
    else say(target);
  }
  function control(label, target, cls) {
    var href = data.links[target];
    var el = document.createElement(href ? 'a' : 'button');
    el.className = cls;
    el.textContent = label;
    if (href) {
      el.href = href;
      if (target === '@cv') el.setAttribute('download', '');
      else if (href.indexOf('http') === 0) el.rel = 'noopener';
    } else {
      el.type = 'button';
      el.addEventListener('click', function () { if (cls.indexOf('choice') >= 0) lastChoice = label; follow(target); });
    }
    return el;
  }

  /* ---------- la discussion ---------- */
  var typing = null, full = '', visited = {}, lastChoice = '';
  function finish() { clearTimeout(typing); typing = null; $('talk-say').textContent = full; }
  function type(text) {
    full = text;
    $('talk-live').textContent = text;
    clearTimeout(typing);
    if (reduce) { finish(); return; }
    var i = 0, box = $('talk-say');
    (function tick() {
      box.textContent = text.slice(0, i);
      if (i < text.length) {
        var caret = document.createElement('span');
        caret.className = 'caret';
        box.appendChild(caret);
        i++;
        typing = setTimeout(tick, /[.,:!?]/.test(text[i - 1]) ? 120 : 18);
      } else typing = null;
    })();
  }
  function say(id) {
    var node = data.nodes[id];
    if (!node) return;
    talkStarted = true;
    visited[id] = true;
    if (node.topic) { var chip = stage.querySelector('.topic[data-topic="' + node.topic + '"]'); if (chip) chip.classList.add('is-done'); }
    var you = $('talk-you');
    you.hidden = !lastChoice || id === 'start';
    you.textContent = lastChoice;
    lastChoice = '';
    type(node.say);
    var box = $('talk-choices');
    box.textContent = '';
    (node.opts === '@menu' ? data.menu : node.opts).forEach(function (o) {
      var seen = visited[o[1]] && o[1] !== 'again';
      box.appendChild(control(o[0], o[1], 'choice' + (seen ? ' is-done' : '') + (o[1].charAt(0) === '@' ? ' choice--go' : '')));
    });
  }
  $('talk-say').addEventListener('click', function () { if (typing) finish(); });
  $('talk-say').addEventListener('keydown', function (e) {
    if ((e.key === 'Enter' || e.key === ' ') && typing) { e.preventDefault(); finish(); }
  });

  /* ---------- la carte ---------- */
  var ICON = {
    school: '<path d="M3 10l9-5 9 5-9 5z"/><path d="M7 12.5v4c0 1.3 2.2 2.5 5 2.5s5-1.2 5-2.5v-4"/>',
    plane: '<path d="M3 12.5L21 4l-6 17-3.5-7z"/><path d="M11.5 14L21 4"/>',
    antenna: '<path d="M12 10v11M8 21h8"/><path d="M8.3 5.8a5.2 5.2 0 0 0 0 7.4M15.7 5.8a5.2 5.2 0 0 1 0 7.4"/><path d="M12 9.2v.6"/>',
    light: '<path d="M9.5 21l1.2-11h2.600l1.200 11z"/><path d="M10 10V7h4v3M9 10h6"/><path d="M3.500 5.500L7 7.500M20.500 5.500L17 7.500"/>',
    bank: '<path d="M3 10l9-6 9 6z"/><path d="M6 10v8M10 10v8M14 10v8M18 10v8M4 21h16M5 18h14"/>',
    turtle: '<ellipse cx="11" cy="13" rx="7" ry="5"/><path d="M18 11.500c1.500-1.500 4-1 4 .5s-2 2.300-3.800 1.600M6.500 17.500l-1.500 2.500M15.500 17.500l1.500 2.500M4 13l-2 .5M8 9.500l1.500 3.500h3L14 9.500M9.500 13L8 16M12.500 13l1.500 3"/>',
    laptop: '<path d="M5 6h14v9H5zM2.500 18.500h19"/><path d="M12.500 8l-2 3h3l-2 3"/>',
    mail: '<path d="M3 6h18v12H3z"/><path d="M3 7l9 6.500L21 7"/>'
  };
  var STOPS = data.stops, N = STOPS.length, L = data.map;
  var WIDE = 'M75 130 C 195 20, 305 235, 445 130 S 695 40, 718 215 S 600 440, 455 395 S 215 320, 90 425';
  var TALL = 'M70 90 C 190 30, 330 60, 330 150 S 80 190, 80 290 S 330 300, 330 400 S 190 520, 75 500';
  var svg = $('map'), road = $('road'), done = $('road-done'), mini = $('mini'), stopsG = $('stops');
  var pos = 0, len = 0, total = 0, busy = false, seen = [true], narrow = null;
  function mk(tag, attrs) {
    var el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (var k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  }
  function at(i) { return total * i / (N - 1); }
  function fill(text, vars) { return text.replace(/\{(\w+)\}/g, function (m, k) { return vars[k]; }); }

  function layoutMap() {
    var width = svg.getBoundingClientRect().width;
    if (!width) return;
    var isNarrow = width < 520;
    if (isNarrow === narrow) return;
    narrow = isNarrow;
    svg.setAttribute('viewBox', narrow ? '0 -34 410 614' : '0 -44 800 534');
    road.setAttribute('d', narrow ? TALL : WIDE);
    done.setAttribute('d', narrow ? TALL : WIDE);
    total = road.getTotalLength();
    done.style.strokeDasharray = total;
    stopsG.textContent = '';
    STOPS.forEach(function (s, i) {
      var p = road.getPointAtLength(at(i));
      var g = mk('g', { 'class': 'stop', tabindex: '0', role: 'button', 'aria-label': fill(L.stop, { n: i + 1, label: s.label }), transform: 'translate(' + p.x.toFixed(1) + ',' + p.y.toFixed(1) + ')' });
      g.appendChild(mk('circle', { r: 21 }));
      var ic = mk('g', { transform: 'translate(-12,-12)' });
      ic.innerHTML = ICON[s.icon] || '';
      g.appendChild(ic);
      var t = mk('text', { y: 40 });
      t.textContent = s.label;
      g.appendChild(t);
      g.addEventListener('click', function () { walk(i); });
      g.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); walk(i); } });
      stopsG.appendChild(g);
    });
    len = at(pos);
    place(len, 1);
    paint(false);
  }
  function place(l, dir, hop) {
    var p = road.getPointAtLength(l), k = narrow ? 1.2 : 1.5;
    mini.setAttribute('transform', 'translate(' + p.x.toFixed(1) + ',' + (p.y - 24 - (hop || 0)).toFixed(1) + ') scale(' + (dir < 0 ? -k : k) + ',' + k + ')');
    done.style.strokeDashoffset = total - l;
  }
  function paint(pop) {
    each(stopsG.children, function (g, i) {
      g.classList.toggle('is-seen', !!seen[i] && i !== pos);
      g.classList.toggle('is-here', i === pos);
    });
    var s = STOPS[pos];
    $('p-tag').textContent = s.tag;
    $('p-title').textContent = s.title;
    $('p-what').textContent = s.what;
    $('p-say').textContent = s.say;
    var shots = $('p-shots');
    shots.textContent = '';
    shots.hidden = !s.photos.length;
    s.photos.forEach(function (ph) {
      var img = document.createElement('img');
      img.src = ph.src; img.alt = ph.alt; img.width = 480; img.height = 600; img.decoding = 'async';
      shots.appendChild(img);
    });
    var more = $('p-more');
    more.textContent = '';
    more.hidden = !(s.more && s.more.length);
    (s.more || []).forEach(function (m) { more.appendChild(control(m[0], m[1], 'link')); });
    $('map-hud').textContent = fill(L.step, { n: pos + 1, total: N });
    $('map-prev').disabled = pos === 0;
    $('map-next').disabled = pos === N - 1;
    $('map-next').textContent = pos === N - 1 ? L.end : L.next + ' →';
    each($('bag').children, function (b, i) { b.classList.toggle('is-got', !!seen[i]); });
    if (pop !== false) { var panel = $('map-panel'); panel.classList.remove('pop'); void panel.offsetWidth; panel.classList.add('pop'); }
  }
  function walk(to) {
    if (busy || to === pos || to < 0 || to >= N) return;
    var a = len, b = at(to), dir = b > a ? 1 : -1, dur = Math.min(1700, 560 * Math.abs(to - pos)), t0 = null;
    function arrive() {
      for (var i = Math.min(pos, to); i <= Math.max(pos, to); i++) seen[i] = true;
      pos = to; len = b; busy = false;
      place(len, dir);
      paint();
    }
    if (reduce) { arrive(); return; }
    busy = true;
    requestAnimationFrame(function step(ts) {
      if (t0 === null) t0 = ts;
      var k = Math.min(1, (ts - t0) / dur), e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      place(a + (b - a) * e, dir, Math.abs(Math.sin((ts - t0) / 95)) * 5);
      if (k < 1) requestAnimationFrame(step); else arrive();
    });
  }
  STOPS.forEach(function (s) {
    var b = document.createElement('span');
    b.className = 'bag__i';
    b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true">' + (ICON[s.icon] || '') + '</svg>';
    $('bag').appendChild(b);
  });
  $('map-prev').addEventListener('click', function () { walk(pos - 1); });
  $('map-next').addEventListener('click', function () { walk(pos + 1); });
  document.addEventListener('keydown', function (e) {
    if (mode() !== 'play' || scene !== 'map' || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === 'ArrowRight') { walk(pos + 1); e.preventDefault(); }
    if (e.key === 'ArrowLeft') { walk(pos - 1); e.preventDefault(); }
  });
  window.addEventListener('resize', function () { if (mode() === 'play' && scene === 'map' && !busy) layoutMap(); });

  /* ---------- départ ---------- */
  if (mode() === 'play') say('start');
})();
