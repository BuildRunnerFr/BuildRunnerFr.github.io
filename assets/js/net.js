/* Réseau de l'en-tête.
   Un maillage fixe de nœuds ; entre le nœud « Ethan » (près du portrait) et le curseur, le plus court chemin
   est calculé avec l'algorithme de Dijkstra, celui d'OSPF, et recalculé à chaque déplacement. De temps en temps
   un lien du chemin tombe : la route se recalcule, comme sur un vrai réseau.
   Purement décoratif : sans ce script, la page est complète. */
(function () {
  'use strict';
  var canvas = document.getElementById('net');
  var hero = document.getElementById('home');
  if (!canvas || !hero || !canvas.getContext) return;
  var ctx = canvas.getContext('2d');
  var cap = document.getElementById('net-cap');
  var capText = cap ? cap.querySelector('span') : null;
  var hopForms = cap ? cap.dataset.hop.split('|') : ['', ''];
  var portrait = hero.querySelector('.portrait picture');
  var textBlock = hero.querySelector('.hero__text');
  var figsBlock = hero.querySelector('.figs');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var W = 0, H = 0, dpr = 1;
  var nodes = [], edges = [], adj = [];
  var src = 0, dst = -1, path = [], cum = [0], pathLen = 0, cost = 0, mode = 'auto', changedAt = 0;
  var pointer = null, lastMove = 0, lastWander = 0, lastCut = 0, cutMsgUntil = 0, capTimer = 0;
  var col = { accent: '74, 63, 224', ink: '15, 18, 34', paper: '#ffffff' };
  var onScreen = true, raf = 0;

  function readColors() {
    var cs = getComputedStyle(canvas);
    col.accent = cs.getPropertyValue('--accent-rgb').trim() || col.accent;
    col.ink = cs.getPropertyValue('--ink-rgb').trim() || col.ink;
    col.paper = cs.getPropertyValue('--paper').trim() || col.paper;
  }
  function rgba(c, a) { return 'rgba(' + c + ', ' + a.toFixed(3) + ')'; }

  /* Tirage reproductible : le maillage garde la même allure d'une visite à l'autre */
  function seeded(seed) {
    return function () {
      seed = seed + 0x6D2B79F5 | 0;
      var t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  function nearest(x, y) {
    var best = 0, bd = Infinity;
    for (var i = 0; i < nodes.length; i++) {
      var dx = nodes[i].x - x, dy = nodes[i].y - y, d = dx * dx + dy * dy;
      if (d < bd) { bd = d; best = i; }
    }
    return best;
  }

  function build() {
    var r = seeded(11);
    var step = W < 700 ? 56 : 92;
    var cols = Math.ceil(W / step) + 1, rows = Math.ceil(H / step) + 1;
    var ox = (W - (cols - 1) * step) / 2, oy = (H - (rows - 1) * step) / 2;
    var i, j;
    nodes = []; edges = [];
    for (j = 0; j < rows; j++) {
      for (i = 0; i < cols; i++) {
        nodes.push({ x: ox + i * step + (r() - 0.5) * step * 0.56, y: oy + j * step + (r() - 0.5) * step * 0.56, a: 0 });
      }
    }
    /* Le texte et le portrait sont des zones au coût élevé, comme des liens qu'on préfère éviter : les routes les contournent quand elles le peuvent */
    var hr = hero.getBoundingClientRect();
    var pad = W < 700 ? 26 : 14;  /* sur téléphone, les marges de côté comptent comme du texte : pas de route dans la gouttière */
    var zones = [[textBlock, 3, pad], [figsBlock, 3, pad], [portrait, 9, 4], [cap, 3, pad]].filter(function (z) { return z[0]; }).map(function (z) {
      var q = z[0].getBoundingClientRect();
      return [q.left - hr.left - z[2], q.top - hr.top - z[2], q.right - hr.left + z[2], q.bottom - hr.top + z[2], z[1]];
    });
    function zoneCost(x, y) {
      for (var z = 0; z < zones.length; z++) if (x > zones[z][0] && x < zones[z][2] && y > zones[z][1] && y < zones[z][3]) return zones[z][4];
      return 1;
    }
    function inText(x, y) { return zoneCost(x, y) > 1; }
    function link(a, b) {
      var A = nodes[a], B = nodes[b];
      var w = Math.hypot(A.x - B.x, A.y - B.y) * Math.max(zoneCost((A.x + B.x) / 2, (A.y + B.y) / 2), zoneCost(A.x, A.y), zoneCost(B.x, B.y));
      edges.push({ a: a, b: b, w: w, down: 0 });
    }
    for (j = 0; j < rows; j++) {
      for (i = 0; i < cols; i++) {
        var n = j * cols + i;
        if (i < cols - 1 && r() < 0.84) link(n, n + 1);
        if (j < rows - 1 && r() < 0.84) link(n, n + cols);
        if (i < cols - 1 && j < rows - 1 && r() < 0.3) { if (r() < 0.5) link(n, n + cols + 1); else link(n + 1, n + cols); }
      }
    }
    adj = nodes.map(function () { return []; });
    edges.forEach(function (e, k) { adj[e.a].push(k); adj[e.b].push(k); });

    /* La source est le nœud le plus proche du portrait ; le maillage s'estompe en s'en éloignant, pour laisser le texte tranquille */
    var pr = portrait ? portrait.getBoundingClientRect() : null;
    var fx = pr && pr.width ? pr.left - hr.left - 30 : W * 0.72;
    if (pr && pr.width && fx < 28) fx = pr.right - hr.left + 30;  /* téléphone : le portrait est collé à gauche, la source passe à sa droite */
    var fy = pr && pr.width ? pr.top - hr.top + pr.height * 0.4 : H * 0.36;
    var sd = Infinity;
    nodes.forEach(function (nd, idx) {
      nd.quiet = !inText(nd.x, nd.y);
      var d = Math.hypot(nd.x - fx, nd.y - fy);
      if (nd.quiet && d < sd) { sd = d; src = idx; }
    });
    var reach = Math.max(W, H) * (W < 700 ? 0.95 : 0.78);
    nodes.forEach(function (nd) {
      var k = Math.max(0, 1 - Math.hypot(nd.x - fx, nd.y - fy) / reach);
      nd.a = k * k * (W < 700 ? 0.6 : 1);
    });
    dst = -1; path = []; pathLen = 0;
    var first = -1, far = 0;
    nodes.forEach(function (nd, idx) {
      if (!nd.quiet || nd.a < 0.12) return;
      var d = Math.hypot(nd.x - nodes[src].x, nd.y - nodes[src].y);
      if (d > far && d < Math.max(240, W * 0.5) && calm(idx)) { far = d; first = idx; }
    });
    if (first >= 0) go(first, false);
  }

  /* Plus court chemin (Dijkstra). Les liens coupés sont ignorés. */
  function route(from, to) {
    var N = nodes.length, dist = [], prev = [], done = [], k;
    for (k = 0; k < N; k++) { dist.push(Infinity); prev.push(-1); done.push(false); }
    dist[from] = 0;
    for (var it = 0; it < N; it++) {
      var u = -1, best = Infinity;
      for (k = 0; k < N; k++) if (!done[k] && dist[k] < best) { best = dist[k]; u = k; }
      if (u < 0 || u === to) break;
      done[u] = true;
      for (var m = 0; m < adj[u].length; m++) {
        var e = edges[adj[u][m]];
        if (e.down) continue;
        var v = e.a === u ? e.b : e.a, nd = dist[u] + e.w;
        if (nd < dist[v]) { dist[v] = nd; prev[v] = u; }
      }
    }
    if (to !== from && prev[to] < 0) return null;
    var out = [to];
    while (out[0] !== from) out.unshift(prev[out[0]]);
    return { nodes: out, cost: dist[to] };
  }

  /* Une route est « au calme » si aucun de ses nœuds ne tombe sur du texte ou sur le portrait */
  function calm(idx) {
    var r = route(src, idx);
    if (!r || r.nodes.length < 2 || r.nodes.length > 11) return false;
    for (var i = 1; i < r.nodes.length; i++) if (!nodes[r.nodes[i]].quiet) return false;
    return true;
  }

  function go(idx, byUser, force) {
    if (idx === dst && !force) { mode = byUser ? 'you' : mode; return; }
    var r = route(src, idx);
    if (!r || r.nodes.length < 2) return;
    dst = idx; path = r.nodes; cost = r.cost; mode = byUser ? 'you' : 'auto';
    cum = [0];
    for (var i = 1; i < path.length; i++) {
      cum.push(cum[i - 1] + Math.hypot(nodes[path[i]].x - nodes[path[i - 1]].x, nodes[path[i]].y - nodes[path[i - 1]].y));
    }
    pathLen = cum[cum.length - 1];
    changedAt = performance.now();
    caption();
  }

  function caption() {
    if (!capText || !path.length) return;
    var hops = path.length - 1;
    var text = performance.now() < cutMsgUntil
      ? cap.dataset.down
      : (mode === 'you' ? cap.dataset.you : cap.dataset.auto).replace('{hops}', hops + ' ' + hopForms[hops > 1 ? 1 : 0]).replace('{cost}', Math.round(cost / 10));
    if (capText.textContent !== text) capText.textContent = text;
  }

  /* Un lien du milieu du chemin tombe quelques secondes : la route se recalcule */
  function cut(now) {
    if (path.length < 5) return;
    var k = 1 + Math.floor(Math.random() * (path.length - 3));
    var a = path[k], b = path[k + 1];
    for (var m = 0; m < adj[a].length; m++) {
      var e = edges[adj[a][m]];
      if ((e.a === a && e.b === b) || (e.a === b && e.b === a)) {
        e.down = now + 5200;
        if (!route(src, dst) || (mode !== 'you' && !calm(dst))) { e.down = 0; return; }
        cutMsgUntil = now + 1900;
        go(dst, mode === 'you', true);
        clearTimeout(capTimer);
        capTimer = setTimeout(caption, 1950);
        return;
      }
    }
  }

  function pointAt(len) {
    for (var i = 1; i < cum.length; i++) {
      if (len <= cum[i]) {
        var a = nodes[path[i - 1]], b = nodes[path[i]], k = (len - cum[i - 1]) / ((cum[i] - cum[i - 1]) || 1);
        return { x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k };
      }
    }
    var last = nodes[path[path.length - 1]];
    return { x: last.x, y: last.y };
  }

  function draw(now) {
    var i, e, a, b, al;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';

    /* le maillage, très discret */
    ctx.lineWidth = 1;
    for (i = 0; i < edges.length; i++) {
      e = edges[i]; a = nodes[e.a]; b = nodes[e.b]; al = Math.min(a.a, b.a);
      if (al < 0.03) continue;
      if (e.down) {
        ctx.setLineDash([2, 5]);
        ctx.strokeStyle = rgba(col.ink, 0.12 + 0.3 * al);
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        ctx.setLineDash([]);
        var mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
        ctx.strokeStyle = rgba(col.ink, 0.55);
        ctx.beginPath(); ctx.moveTo(mx - 3, my - 3); ctx.lineTo(mx + 3, my + 3); ctx.moveTo(mx + 3, my - 3); ctx.lineTo(mx - 3, my + 3); ctx.stroke();
      } else {
        ctx.strokeStyle = rgba(col.ink, 0.13 * al);
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      }
    }
    for (i = 0; i < nodes.length; i++) {
      a = nodes[i];
      if (a.a < 0.03) continue;
      ctx.fillStyle = rgba(col.ink, 0.34 * a.a);
      ctx.beginPath(); ctx.arc(a.x, a.y, 1.6, 0, 6.2832); ctx.fill();
    }
    if (path.length < 2) return;

    /* la route, qui se trace depuis la source */
    var k = reduce ? 1 : Math.min(1, (now - changedAt) / 460);
    var shown = pathLen * (1 - Math.pow(1 - k, 3));
    ctx.strokeStyle = rgba(col.accent, 0.8);
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    ctx.moveTo(nodes[path[0]].x, nodes[path[0]].y);
    for (i = 1; i < path.length && cum[i] <= shown; i++) ctx.lineTo(nodes[path[i]].x, nodes[path[i]].y);
    var tip = pointAt(shown);
    ctx.lineTo(tip.x, tip.y);
    ctx.stroke();
    ctx.fillStyle = rgba(col.accent, 1);
    for (i = 1; i < path.length - 1 && cum[i] <= shown; i++) {
      ctx.beginPath(); ctx.arc(nodes[path[i]].x, nodes[path[i]].y, 2.3, 0, 6.2832); ctx.fill();
    }

    /* les paquets qui circulent */
    if (!reduce) {
      for (i = 0; i < 3; i++) {
        var pos = (now * 0.15 + i * pathLen / 3) % pathLen;
        if (pos > shown) continue;
        var p = pointAt(pos);
        ctx.fillStyle = rgba(col.accent, 0.22);
        ctx.beginPath(); ctx.arc(p.x, p.y, 6.5, 0, 6.2832); ctx.fill();
        ctx.fillStyle = rgba(col.accent, 1);
        ctx.beginPath(); ctx.arc(p.x, p.y, 2.8, 0, 6.2832); ctx.fill();
      }
    }

    /* la source, près du portrait */
    var s = nodes[src], pulse = reduce ? 0.5 : 0.5 + 0.5 * Math.sin(now / 520);
    ctx.fillStyle = rgba(col.accent, 0.1 + 0.1 * pulse);
    ctx.beginPath(); ctx.arc(s.x, s.y, 9 + 3 * pulse, 0, 6.2832); ctx.fill();
    ctx.fillStyle = rgba(col.accent, 1);
    ctx.beginPath(); ctx.arc(s.x, s.y, 4.2, 0, 6.2832); ctx.fill();

    /* la destination : le nœud le plus proche du curseur */
    if (k >= 1 || shown >= pathLen - 1) {
      var d = nodes[dst];
      ctx.fillStyle = col.paper;
      ctx.strokeStyle = rgba(col.accent, 1);
      ctx.lineWidth = 1.6;
      ctx.beginPath(); ctx.arc(d.x, d.y, 5.5, 0, 6.2832); ctx.fill(); ctx.stroke();
      if (mode === 'you' && pointer) {
        ctx.setLineDash([2, 5]);
        ctx.strokeStyle = rgba(col.accent, 0.55);
        ctx.lineWidth = 1.2;
        ctx.beginPath(); ctx.moveTo(d.x, d.y); ctx.lineTo(pointer.x, pointer.y); ctx.stroke();
        ctx.setLineDash([]);
      }
    }
  }

  function frame(now) {
    raf = 0;
    if (!onScreen || document.hidden || !W) return;
    var rerouted = false;
    for (var i = 0; i < edges.length; i++) {
      if (edges[i].down && edges[i].down < now) { edges[i].down = 0; rerouted = true; }
    }
    if (rerouted) go(dst, mode === 'you', true);
    if (pointer && now - lastMove > 6000) pointer = null;
    if (!pointer && now - lastWander > 3800) {
      lastWander = now;
      for (var t = 0; t < 40; t++) {
        var pick = Math.floor(Math.random() * nodes.length), nd = nodes[pick];
        if (nd.a > 0.1 && nd.quiet && pick !== dst && Math.hypot(nd.x - nodes[src].x, nd.y - nodes[src].y) > (W < 700 ? 70 : Math.min(W, H) * 0.3) && calm(pick)) { go(pick, false); break; }
      }
    }
    if (now - lastCut > 6400) { lastCut = now; cut(now); }
    draw(now);
    raf = requestAnimationFrame(frame);
  }
  function start() {
    if (reduce) { if (W) draw(performance.now()); return; }
    if (!raf) raf = requestAnimationFrame(frame);
  }

  function resize() {
    var w = hero.clientWidth, h = hero.clientHeight;
    if (!w || !h) { W = 0; return; }
    if (w === W && Math.abs(h - H) < 2) return;
    W = w; H = h;
    dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    readColors();
    build();
    lastCut = lastWander = performance.now();
    start();
  }

  function onPointer(e) {
    if (!W) return;
    var r = hero.getBoundingClientRect();
    var x = e.clientX - r.left, y = e.clientY - r.top;
    if (x < 0 || y < 0 || x > r.width || y > r.height) { pointer = null; return; }
    pointer = { x: x, y: y };
    lastMove = performance.now();
    go(nearest(x, y), true);
    if (reduce) draw(lastMove);
  }
  window.addEventListener('pointermove', onPointer, { passive: true });
  window.addEventListener('pointerdown', onPointer, { passive: true });

  if ('ResizeObserver' in window) new ResizeObserver(resize).observe(hero);
  else window.addEventListener('resize', resize);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) { onScreen = entries[0].isIntersecting; if (onScreen) start(); }).observe(hero);
  }
  document.addEventListener('visibilitychange', function () { if (!document.hidden) start(); });
  function recolor() { readColors(); if (W) draw(performance.now()); }
  if ('MutationObserver' in window) new MutationObserver(recolor).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme', 'data-accent'] });
  var scheme = window.matchMedia('(prefers-color-scheme: dark)');
  if (scheme.addEventListener) scheme.addEventListener('change', recolor);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { W = 0; resize(); });
  resize();
})();
