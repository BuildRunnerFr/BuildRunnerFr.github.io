#!/usr/bin/env python3
"""Génère le site : la page d'accueil (français, anglais) et une page par projet.

Les textes sont dans content/fr.json et content/en.json, les chiffres et les README dans
content/github.json et content/readmes/ (relevés par tools/github_stats.py).
Après une modification :  python3 build.py
Aucune dépendance : bibliothèque standard uniquement.
"""
import json
import re
import struct
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
SITE = "https://buildrunnerfr.github.io"
EMAIL = "ethancte@gmail.com"
LINKEDIN = "https://www.linkedin.com/in/ethan-blombou"
GITHUB = "https://github.com/BuildRunnerFr"
CV = "/assets/cv-ethan-blombou.pdf"
SECTIONS = ["about", "skills", "journey", "projects", "stats", "life", "contact"]
THEME = "#0b0c14"             # couleur de la barre du navigateur sur téléphone (fond du thème sombre)
THEME_CHOICE = False          # False : thème sombre pour tout le monde, sans bouton ; True : le visiteur choisit
ICONS = '<link rel="icon" href="/favicon-v4.svg" type="image/svg+xml">\n<link rel="icon" href="/favicon-v4-32.png" sizes="32x32" type="image/png">\n<link rel="apple-touch-icon" href="/apple-touch-icon-v4.png">'


# ---------- petits outils ----------

def nbsp_fr(text):
    """Espaces insécables de la typographie française."""
    text = re.sub(r" ([:;?!»])", " \\1", text)
    return text.replace("« ", "« ")


def walk(node, fn):
    if isinstance(node, str):
        return fn(node)
    if isinstance(node, list):
        return [walk(n, fn) for n in node]
    if isinstance(node, dict):
        return {k: walk(v, fn) for k, v in node.items()}
    return node


def image_size(path):
    """Dimensions intrinsèques d'un PNG, d'un WebP ou d'un SVG, pour éviter les sauts de mise en page."""
    data = path.read_bytes()
    if path.suffix == ".png":
        return struct.unpack(">II", data[16:24])
    if path.suffix == ".webp":
        kind = data[12:16]
        if kind == b"VP8X":
            return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
        if kind == b"VP8L":
            bits = int.from_bytes(data[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        w, h = struct.unpack("<HH", data[26:30])
        return w & 0x3FFF, h & 0x3FFF
    head = data[:2000].decode("utf-8", "ignore")
    m = re.search(r'viewBox="([^"]+)"', head)
    if m:
        parts = [float(x) for x in m.group(1).replace(",", " ").split()]
        return parts[2], parts[3]
    w = re.search(r'\swidth="([\d.]+)', head)
    h = re.search(r'\sheight="([\d.]+)', head)
    return float(w.group(1)), float(h.group(1))


def logo(stem, alt, cls="logo"):
    """Balise <img> d'un logo d'organisation, ou rien si le fichier manque."""
    for ext in ("svg", "webp", "png"):
        path = ROOT / "assets" / "logos" / f"{stem}.{ext}"
        if path.exists():
            w, h = image_size(path)
            ratio = w / h
            shape = "wide" if ratio > 3.5 else "square" if ratio < 1.25 else "mid"
            return (
                f'<img class="{cls} {cls}--{shape} {cls}--{stem}" src="/assets/logos/{stem}.{ext}" '
                f'alt="{escape(alt)}" width="{round(w)}" height="{round(h)}" loading="lazy" decoding="async">'
            )
    return ""


def icon(slug):
    if slug and (ROOT / "assets" / "icons" / f"{slug}.svg").exists():
        return f'<img class="ic" src="/assets/icons/{slug}.svg" alt="" width="18" height="18" loading="lazy" decoding="async">'
    return ""


def variants(src, own_width=0):
    """Largeurs disponibles d'une image : « nom.webp » et ses réductions « nom-800.webp » rangées dans le même dossier."""
    path = ROOT / src.lstrip("/")
    base = re.sub(r"-\d+$", "", path.stem)
    found = {}
    for f in path.parent.glob(f"{base}*{path.suffix}"):
        m = re.fullmatch(re.escape(base) + r"(?:-(\d+))?", f.stem)
        if m and (m.group(1) or own_width):
            found[int(m.group(1)) if m.group(1) else own_width] = "/" + f.relative_to(ROOT).as_posix()
    return sorted(found.items())


def srcset(files):
    return ", ".join(f"{path} {w}w" for w, path in files)


def photo(stem, w, h, meta, sizes, cls="shot"):
    """Photo en WebP à plusieurs largeurs, avec légende. `sizes` dit au navigateur la largeur d'affichage, pour qu'il choisisse le bon fichier."""
    files = variants(f"/assets/photos/{stem}.webp")
    return (
        f'<figure class="{cls}"><img src="{files[-1][1]}" srcset="{srcset(files)}" sizes="{sizes}" '
        f'alt="{escape(meta["alt"])}" width="{w}" height="{h}" loading="lazy" decoding="async">'
        f'<figcaption>{meta["caption"]}</figcaption></figure>'
    )


def day_label(iso, months, year=True):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {months[m - 1]}" + (f" {y}" if year else "")


def plural(forms, n):
    return forms[0 if n < 2 else 1].format(n=n)


SVG = {
    "arrow": '<svg class="i i--arrow" viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><path d="M4 10h11M10.5 5l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "back": '<svg class="i i--back" viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><path d="M16 10H5M9.5 5l-5 5 5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "down": '<svg class="i i--down" viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><path d="M10 3v10M5.5 9l4.5 4.5L14.5 9M4 16.5h12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "play": '<svg class="i" viewBox="0 0 20 20" width="14" height="14" aria-hidden="true"><path d="M6 4.5v11l9-5.5z" fill="currentColor"/></svg>',
    "check": '<svg class="i" viewBox="0 0 20 20" width="12" height="12" aria-hidden="true"><path d="M4.5 10.5l3.5 3.5 7.5-8" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "moon": '<svg class="i i--moon" viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><path d="M16.5 12.2A7 7 0 0 1 7.8 3.5a7 7 0 1 0 8.7 8.7z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>',
    "sun": '<svg class="i i--sun" viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><circle cx="10" cy="10" r="3.6" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.3 4.3l1.4 1.4M14.3 14.3l1.4 1.4M4.3 15.7l1.4-1.4M14.3 5.7l1.4-1.4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>',
    "github": '<svg class="i" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M12 .5a11.5 11.5 0 0 0-3.64 22.41c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.36-3.88-1.36-.52-1.33-1.28-1.69-1.28-1.69-1.05-.71.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.76 2.7 1.25 3.36.96.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.29 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.17 1.18a11 11 0 0 1 5.78 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.8 1.19 1.83 1.19 3.09 0 4.42-2.69 5.39-5.26 5.68.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 12 .5z"/></svg>',
    "linkedin": '<svg class="i" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.45zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zM7.12 20.45H3.56V9h3.56zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z"/></svg>',
}

MINI = (
    '<ellipse cx="0" cy="0" rx="13" ry="4" fill="rgba(16,20,31,0.22)"/><g>'
    '<rect x="-7.5" y="-11" width="6" height="10" rx="2" fill="#1c1512"/><rect x="1.5" y="-11" width="6" height="10" rx="2" fill="#1c1512"/>'
    '<rect x="-11.5" y="-30" width="23" height="21" rx="7" fill="#efe1c8" stroke="#1c1512" stroke-width="2.5"/>'
    '<circle cx="0" cy="-40" r="10.5" fill="#c08a5f" stroke="#1c1512" stroke-width="2.5"/>'
    '<g fill="#1c1512"><circle cx="-8.5" cy="-46" r="5"/><circle cx="-3.5" cy="-50.5" r="5.5"/><circle cx="3.5" cy="-50.5" r="5.5"/><circle cx="8.5" cy="-46" r="5"/><circle cx="0" cy="-47.5" r="6"/><circle cx="-10.5" cy="-41.5" r="3.2"/><circle cx="10.5" cy="-41.5" r="3.2"/></g>'
    '<circle cx="-3.7" cy="-38.5" r="1.4" fill="#1c1512"/><circle cx="3.7" cy="-38.5" r="1.4" fill="#1c1512"/>'
    '<path d="M-3.2 -34.3q3.2 2.6 6.4 0" fill="none" stroke="#1c1512" stroke-width="1.6" stroke-linecap="round"/></g>'
)


# ---------- Markdown (README des dépôts) ----------

SKIP_SECTIONS = re.compile(r"quickstart|démarrage|repository|organisation du dépôt|prérequis|configuration|variables|lancer|déploiement|install", re.I)
LIST_ITEM = re.compile(r"(\s*)([-*]|\d+\.)\s+(.*)")


MD_TOKEN = re.compile(r"\[((?:`[^`]*`|[^\]`])+)\]\(([^)]+)\)|`([^`]+)`")


def md_emph(text):
    s = escape(text, quote=False)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)


def md_inline(text, base):
    text = re.sub(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)", "", text)  # badges
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)  # images
    text = re.sub(r"</?[a-zA-Z][^>]*>", " ", text)  # balises HTML
    out, pos = [], 0
    for m in MD_TOKEN.finditer(text):
        out.append(md_emph(text[pos:m.start()]))
        pos = m.end()
        if m.group(3) is not None:  # code en ligne
            out.append(f"<code>{escape(m.group(3))}</code>")
            continue
        # lien, dont le libellé peut lui-même contenir du code : [`fichier.py`](chemin/fichier.py)
        label = "".join(
            f"<code>{escape(part[1:-1])}</code>" if len(part) > 2 and part.startswith("`") and part.endswith("`") else md_emph(part)
            for part in re.split(r"(`[^`]+`)", m.group(1))
        )
        url = m.group(2).split(" ")[0]
        if url.startswith("#"):
            out.append(label)
            continue
        if not re.match(r"https?://", url):
            url = f"{base}/{url.lstrip('./')}"
        out.append(f'<a href="{escape(url)}" rel="noopener">{label}</a>')
    out.append(md_emph(text[pos:]))
    return re.sub(r"\s{2,}", " ", "".join(out)).strip()


def md(text, base, keep=None):
    """Petit rendu Markdown : titres, paragraphes, listes, tableaux, code, citations. Les images sont laissées de côté."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    lines = text.split("\n")
    html, para, i, skipping, seen_h2 = [], [], 0, False, False

    def flush():
        if para:
            body = md_inline(" ".join(para), base)
            if body:
                html.append(f"<p>{body}</p>")
            para.clear()

    def cells(row):
        return [cell.strip() for cell in row.strip().strip("|").split("|")]

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith("```"):
            flush()
            code, diagram = [], s[3:].strip().lower() == "mermaid"
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            # un schéma Mermaid ne se lit pas en code : il reste à voir sur le dépôt
            if not skipping and not diagram:
                html.append("<pre><code>" + escape("\n".join(code)) + "</code></pre>")
            continue
        m = re.match(r"(#{1,5})\s+(.*)", s)
        if m:
            flush()
            level, title = len(m.group(1)), re.sub(r"\s*#+$", "", m.group(2))
            if level == 2:
                seen_h2 = True
                skipping = (title not in keep) if keep else bool(SKIP_SECTIONS.search(title))
            if level >= 2 and not skipping:
                html.append(f"<h{level + 1}>{md_inline(title, base)}</h{level + 1}>")
            i += 1
            continue
        if skipping or (keep and not seen_h2):
            i += 1
            continue
        if not s or re.fullmatch(r"-{3,}|\*{3,}", s):
            flush()
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1]):
            flush()
            head = cells(s)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            thead = "".join(f"<th>{md_inline(cell, base)}</th>" for cell in head)
            tbody = "".join("<tr>" + "".join(f"<td>{md_inline(cell, base)}</td>" for cell in r) + "</tr>" for r in rows)
            html.append(f'<div class="md__table"><table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table></div>')
            continue
        if s.startswith(">"):
            flush()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            html.append(f"<blockquote><p>{md_inline(' '.join(quote), base)}</p></blockquote>")
            continue
        m = LIST_ITEM.match(line)
        if m:
            flush()
            tag = "ol" if m.group(2)[0].isdigit() else "ul"
            items = []
            while i < len(lines):
                mm = LIST_ITEM.match(lines[i])
                if mm:
                    items.append([len(mm.group(1)), mm.group(3)])
                elif lines[i].strip() and lines[i].startswith(" ") and items:
                    items[-1][1] += " " + lines[i].strip()
                else:
                    break
                i += 1
            out, open_sub = [f"<{tag}>"], False
            for indent, body in items:
                if indent >= 2 and not open_sub and len(out) > 1:
                    out[-1] = out[-1].removesuffix("</li>")
                    out.append("<ul>")
                    open_sub = True
                elif indent < 2 and open_sub:
                    out.append("</ul></li>")
                    open_sub = False
                out.append(f"<li>{md_inline(body, base)}</li>")
            if open_sub:
                out.append("</ul></li>")
            out.append(f"</{tag}>")
            html.append("".join(out))
            continue
        if re.fullmatch(r"(\s*</?[a-zA-Z][^>]*>\s*)+", line):
            flush()
            i += 1
            continue
        para.append(s)
        i += 1
    flush()
    return "\n".join(html)


# ---------- graphiques ----------

def heatmap(days, months):
    """Calendrier d'activité : une colonne par semaine, une case par jour."""
    first = date.fromisoformat(days[0][0])
    pad = first.weekday()  # lundi = 0
    cell, gap = 13, 3
    cols = (pad + len(days) + 6) // 7
    rects, labels, seen = [], [], set()
    for i, (iso, n) in enumerate(days):
        col, row = divmod(pad + i, 7)
        level = 0 if n == 0 else 1 if n < 4 else 2 if n < 10 else 3 if n < 25 else 4
        x, y = col * (cell + gap), 18 + row * (cell + gap)
        rects.append(f'<rect class="l{level}" style="--c:{col}" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3"><title>{day_label(iso, months)} : {n}</title></rect>')
        ym = iso[:7]
        if ym not in seen and int(iso[8:]) <= 7:
            seen.add(ym)
            labels.append(f'<text x="{x}" y="10">{months[int(iso[5:7]) - 1]}</text>')
    w, h = cols * (cell + gap) - gap, 18 + 7 * (cell + gap) - gap
    return f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" aria-hidden="true">{"".join(labels)}{"".join(rects)}</svg>'


def gantt(rows, months, today_label):
    """Chronologie : une ligne par projet, placée en pourcentage entre le premier et le dernier mois."""
    today = date.today()
    start = min(date.fromisoformat(r["start"]) for r in rows).replace(day=1)
    end = date(today.year + (1 if today.month == 12 else 0), today.month % 12 + 1, 1)
    span = (end - start).days

    def pos(iso):
        return max(0.0, min(100.0, (date.fromisoformat(iso) - start).days / span * 100))

    ticks, d = [], start
    while d < end:
        # un mois sur deux est nommé, sauf tout près de la marque « aujourd'hui »
        show = (d.month % 2 == 1 or d == start) and pos(d.isoformat()) < pos(today.isoformat()) - 6
        with_year = d.month == 1 or d == start
        label = months[d.month - 1] + (f" {d.year}" if with_year else "")
        short = months[d.month - 1] + (f" {d.year % 100}" if with_year else "")
        kind = "" if show else " gantt__tick--minor"
        if show and (d.month % 4 == 1 or d == start):
            kind += " gantt__tick--main"
        if pos(d.isoformat()) > pos(today.isoformat()) - 24:
            kind += " gantt__tick--late"
        both = f'<i><span class="wide">{label}</span><span class="narrow">{short}</span></i>' if show else ""
        ticks.append(f'<span class="gantt__tick{kind}" style="left:{pos(d.isoformat()):.2f}%">{both}</span>')
        d = date(d.year + (1 if d.month == 12 else 0), d.month % 12 + 1, 1)
    lines = []
    for n, r in enumerate(sorted(rows, key=lambda r: r["start"])):
        a = pos(r["start"])
        b = pos(r["end"] or today.isoformat())
        name = f'<a href="{r["href"]}">{r["name"]}</a>' if r.get("href") else r["name"]
        lines.append(
            f'<li class="gantt__row gantt__row--{r["cat"]}{" is-live" if not r["end"] else ""}" style="--i:{n}"><span class="gantt__name">{name}</span>'
            f'<span class="gantt__track"><span class="gantt__bar" style="left:{a:.2f}%;width:max(8px, {b - a:.2f}%)" title="{escape(r["title"])}"></span></span></li>'
        )
    now = f'<span class="gantt__now" style="left:{pos(today.isoformat()):.2f}%"><i>{today_label}</i></span>'
    return (
        f'<div class="gantt__in"><div class="gantt__scale" aria-hidden="true"><span class="gantt__name"></span><span class="gantt__track">{"".join(ticks)}{now}</span></div>'
        f'<ul class="gantt__rows">{"".join(lines)}</ul></div>'
    )


def lang_bar(languages, other_label, lang):
    bar = "".join(f'<span class="langs__seg langs__seg--{i}" style="flex-grow:{pct}"></span>' for i, (_, pct) in enumerate(languages[:6]))
    items = "".join(
        f'<li><i class="langs__dot langs__seg--{i}"></i>{other_label if name == "other" else escape(name)}<span>{str(pct).replace(".", "," if lang == "fr" else ".")} %</span></li>'
        for i, (name, pct) in enumerate(languages[:6])
    )
    return f'<div class="langs__bar" aria-hidden="true">{bar}</div><ul class="langs__list">{items}</ul>'


# ---------- gabarit commun ----------

def shell(c, *, title, description, path, alt_path, body, home, page="home", extra_head="", scripts=("main",)):
    lang, ui = c["lang"], c["ui"]
    url = SITE + path
    alt_lang = "en" if lang == "fr" else "fr"
    nav_links = "".join(f'<li><a href="{home}#{s}" data-nav="{s}">{c["nav"][s]}</a></li>' for s in SECTIONS)
    play_btn = ""
    if page == "home":
        play_btn = f'<button class="tool tool--play" type="button" data-mode-switch>{c["play"]["to_classic"]}</button>'
    can_play = "true" if page == "home" else "false"
    theme_js = "t==='light'?'light':'dark'" if THEME_CHOICE else "'dark'"
    theme_btn = f'<button class="tool tool--theme" type="button" data-theme-toggle aria-label="{escape(ui["theme"])}">{SVG["moon"]}{SVG["sun"]}</button>' if THEME_CHOICE else ""
    script_tags = "".join(f'<script src="/assets/js/{s}.js" defer></script>' for s in scripts)
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{escape(description)}">
<meta name="author" content="Ethan Blombou">
<meta name="theme-color" content="{THEME}">
<meta name="color-scheme" content="dark light">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="{lang}" href="{url}">
<link rel="alternate" hreflang="{alt_lang}" href="{SITE}{alt_path}">
<meta property="og:type" content="{'profile' if page == 'home' else 'article'}">
<meta property="og:site_name" content="Ethan Blombou">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="{c["og_locale"]}">
<meta property="og:image" content="{SITE}/assets/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Ethan Blombou">
<meta name="twitter:card" content="summary_large_image">
{ICONS}
<link rel="preload" href="/assets/fonts/space-grotesk.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/poppins-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/style.css">
<script>(function(){{var d=document.documentElement,h=location.hash.slice(1),m=null,t=null;d.classList.add('js');try{{m=localStorage.getItem('mode');t=localStorage.getItem('theme')}}catch(e){{}}d.setAttribute('data-theme',{theme_js});if(h==='jeu'||h==='play')m='play';else if(h)m='classic';d.setAttribute('data-mode',m==='play'&&{can_play}?'play':'classic')}})()</script>
{extra_head}</head>
<body class="page--{page}">
<a class="skip" href="#main">{ui["skip"]}</a>

<header class="top">
  <nav class="nav wrap" aria-label="{ui["nav_label"]}">
    <a class="nav__brand" href="{home}#home"><span class="nav__seal" aria-hidden="true"></span>Ethan Blombou</a>
    <ul class="nav__links" id="nav-links">{nav_links}</ul>
    <div class="nav__tools">
      {play_btn}
      <a class="tool tool--cv" href="{CV}" download>{ui["cv_short"]}{SVG["down"]}</a>
      <a class="tool tool--lang" href="{alt_path}" lang="{alt_lang}" hreflang="{alt_lang}" data-lang-link><span aria-hidden="true">{alt_lang.upper()}</span><span class="sr-only">{"English" if alt_lang == "en" else "Français"}</span></a>
      {theme_btn}
      <button class="nav__toggle" type="button" aria-expanded="false" aria-controls="nav-links"><span class="nav__toggle-bars" aria-hidden="true"></span><span class="sr-only">{ui["menu"]}</span></button>
    </div>
  </nav>
  <div class="progress" aria-hidden="true"><span class="progress__bar"></span></div>
</header>

{body}

<footer class="footer">
  <div class="wrap footer__in">
    <p>© 2026 Ethan Blombou</p>
    <p>{c["footer"]["note"]}</p>
    <p><a href="#top-of-page">{ui["top"]} ↑</a></p>
  </div>
</footer>

{script_tags}
</body>
</html>
"""


def shead(kicker, title, id_, lead=""):
    lead_html = f'<p class="shead__lead reveal">{lead}</p>' if lead else ""
    return f'<header class="shead"><p class="shead__k reveal">{kicker}</p><h2 class="shead__t reveal" id="{id_}">{title}</h2>{lead_html}</header>'


def live_tag(c, p):
    return f'<span class="live"><i></i>{c["ui"]["status"]["live"]}</span>' if p["status"] == "live" else ""


def project_cover(p, cls, sizes, eager=False):
    cv = p.get("cover")
    if cv:
        load = 'fetchpriority="high"' if eager else 'loading="lazy"'
        files = variants(cv["src"], cv["w"])
        many = f' srcset="{srcset(files)}" sizes="{sizes}"' if len(files) > 1 else ""
        focus = f' style="object-position:{cv["focus"]}"' if cv.get("focus") else ""
        return f'<img class="{cls}" src="{cv["src"]}"{many} alt="{escape(cv["alt"])}" width="{cv["w"]}" height="{cv["h"]}"{focus} {load} decoding="async">'
    first = p["logos"][0] if p["logos"] else None
    words = " · ".join(p["tags"][:3])
    return f'<span class="{cls} {cls}--blank">{logo(first[0], first[1], "plogo") if first else ""}<small>{escape(words)}</small></span>'


def project_url(c, p):
    return ("/projets/" if c["lang"] == "fr" else "/en/projects/") + p["slug"] + "/"


def project_dates(p, gh):
    """Début et fin d'un projet : ceux donnés dans le contenu, sinon ceux du dépôt GitHub (premier commit, dernier push)."""
    if p.get("start"):
        return p["start"], p.get("end", "")
    repo = gh["public"].get(p.get("repo", ""))
    return (repo["created"], repo["pushed"]) if repo else ("", "")


# ---------- page d'accueil ----------

def home(c, gh):
    lang, ui = c["lang"], c["ui"]
    h, a, x, pr, sk, ct, lf, pl, stt, jn = c["hero"], c["about"], c["experience"], c["projects"], c["skills"], c["contact"], c["life"], c["play"], c["stats"], c["journey"]
    months, nt = ui["months"], ui["net"]
    projects = pr["list"]
    opened_m = int(gh["account_opened"][5:7])
    facts_gh = {
        "repos": gh["repos"], "public": gh["public_repos"], "contributions": gh["contributions"], "langs": gh["languages_count"],
        "best": gh["best_day"]["count"], "best_date": day_label(gh["best_day"]["date"], months), "active": gh["active_days"],
        "opened": f'{("juin" if lang == "fr" else "June") if opened_m == 6 else months[opened_m - 1]} {gh["account_opened"][:4]}',
        "synced": day_label(gh["synced"], months),
    }

    def portrait(key, caption=""):
        return f"""<figure class="portrait portrait--{key}">
        <picture>
          <source type="image/webp" srcset="/assets/ethan-400.webp 400w, /assets/ethan-640.webp 640w" sizes="(min-width: 900px) 340px, 110px">
          <img src="/assets/ethan.jpg" alt="{escape(h["photo_alt"])}" width="890" height="1205" fetchpriority="high" decoding="async">
        </picture>{caption}
      </figure>"""

    # légende du réseau de l'en-tête : le script y écrit la route calculée en direct
    net_cap = (
        f'<figcaption class="netcap" id="net-cap" data-you="{escape(nt["you"])}" data-auto="{escape(nt["auto"])}" '
        f'data-down="{escape(nt["down"])}" data-hop="{escape(nt["hop"])}"><b>ospf</b><span>{nt["idle"]}</span></figcaption>'
    )

    def figures(items):
        return "".join(
            f'<li class="fig reveal" style="--i:{i}"><p class="fig__n">{pre}<span data-count="{n}">{n}</span></p>'
            f'<p class="fig__k">{k}</p><p class="fig__d">{d}</p></li>'
            for i, (n, k, d, pre) in enumerate(items)
        )

    keyfigs = figures([(st[0], st[1], st[2], st[3] if len(st) > 3 else "") for st in a["stats"]])

    # à propos
    paragraphs = "".join(f"<p>{p}</p>" for p in a["paragraphs"])
    quote = f"« {a['quote']} »" if lang == "fr" else f"“{a['quote']}”"
    facts = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in a["facts"])

    # compétences : une ligne par domaine ; l'usage (dépôts, projets) reste en info-bulle
    aliases = {"Bash": "Shell"}
    haystack = [" ".join(p.get("tags", [])).lower() for p in projects] + [(n + " " + s).lower() for n, s in pr["more"]]

    def usage(name):
        repos = gh["language_repos"].get(aliases.get(name, name), 0)
        if repos:
            return plural(ui["in_repos"], repos)
        key = name.split(" · ")[0].lower()
        n = sum(1 for hay in haystack if re.search(r"(?<![\w.])" + re.escape(key) + r"(?![\w.])", hay))
        return plural(ui["in_projects"], n) if n else ""

    def skill(name, slug):
        use = usage(name)
        title = f' title="{escape(use)}"' if use else ""
        return f"<li{title}>{icon(slug)}<span>{escape(name)}</span></li>"

    skillrows = ""
    for g in sk["groups"]:
        items = "".join(skill(name, slug) for name, slug in g["items"])
        skillrows += (
            f'<div class="skillrow"><h3>{g["name"]}<span>{len(g["items"])}</span></h3>'
            f'<div class="marquee" data-marquee><ul class="skilllist">{items}</ul></div></div>'
        )
    spoken = "".join(f"<li><span>{n}</span><small>{lv}</small></li>" for n, lv in sk["languages"])
    skillrows += f'<div class="skillrow"><h3>{sk["languages_title"]}<span>{len(sk["languages"])}</span></h3><ul class="skilllist">{spoken}</ul></div>'
    def badge(it):
        f = ROOT / "assets" / "badges" / f'{it.get("badge", "")}.webp'
        alt = escape(f'{it["name"]}, {it["issuer"]}')
        return f'<img class="badge-img" src="/assets/badges/{f.name}" alt="{alt}" width="160" height="160" loading="lazy" decoding="async">' if f.exists() else ""

    certs = "".join(f'<li class="cert">{badge(it)}<span><b>{it["name"]}</b><small>{it["issuer"]}</small></span></li>' for it in x["certs"])
    skillrows += f'<div class="skillrow"><h3>{sk["certs_title"]}<span>{len(x["certs"])}</span></h3><ul class="skilllist">{certs}</ul></div>'

    # parcours : expériences, formation, certifications sur un même fil
    def step(kind, dates, title, org, logos="", extra=""):
        tiles = f'<div class="step__logos">{logos}</div>' if logos else ""
        return (
            f'<li class="step reveal" data-kind="{kind}"><p class="step__dates">{dates}</p><span class="step__dot" aria-hidden="true"></span>'
            f'<div class="step__body">{tiles}<h3>{title}</h3><p class="step__org">{org}</p>{extra}</div></li>'
        )

    def xp_entry(it):
        logos = tile(it["logo"], it["org"]) + (tile(it["logo2"], it["org2"]) if it.get("logo2") else "")
        bullets = "".join(f"<li>{b}</li>" for b in it.get("bullets", []))
        note = it.get("note")
        extra = (
            (f'<ul class="step__list">{bullets}</ul>' if bullets else "")
            + shots_of(it)
            + (f'<p class="step__note"><span class="label">{note["label"]}</span>{note["text"]}</p>' if note else "")
        )
        return step("xp", it["dates"], it["role"], it["org"], logos, extra)

    def shots_of(it):
        shots = "".join(
            photo(ph["stem"], ph["w"], ph["h"], ph, "(min-width: 800px) 180px, 24vw", "shot shot--step") for ph in it.get("photos", [])
        )
        return f'<div class="step__shots">{shots}</div>' if shots else ""

    def edu_entry(it):
        return step("edu", it["dates"], it["what"], it["org"], tile(it["logo"], it["org"]), shots_of(it))

    def tile(stem, name):
        img = logo(stem, name)
        return f'<span class="logotile">{img}</span>' if img else ""

    steps = (
        xp_entry(x["items"][0]) + xp_entry(x["items"][1]) + edu_entry(x["edu"][0]) + xp_entry(x["items"][2])
        + edu_entry(x["edu"][2]) + edu_entry(x["edu"][1])
    )
    counts = {"all": len(x["items"]) + len(x["edu"]), "xp": len(x["items"]), "edu": len(x["edu"])}
    jtabs = "".join(
        f'<button type="button" class="chipbtn" data-tab="{k}" aria-pressed="{"true" if k == "all" else "false"}">{label}<span>{counts[k]}</span></button>'
        for k, label in jn["tabs"].items()
    )

    # projets : une carte par projet, qui ouvre sa page
    def card(p, i):
        tags_html = "".join(f"<li>{escape(t)}</li>" for t in p["tags"][:4])
        cat = pr["cats"][p["cats"][0]]
        return f"""
        <li class="pc reveal" data-cats="{" ".join(p["cats"])}" style="--i:{i % 2}">
          <a class="pc__link" href="{project_url(c, p)}">
            <div class="pc__cover" style="view-transition-name:cover-{p["key"]}">{project_cover(p, "pc__img", "(min-width: 760px) 520px, 62vw")}</div>
            <p class="pc__meta"><i class="dot dot--{p["cats"][0]}"></i>{cat}<span>{ui["kinds"][p["kind"]]}</span>{live_tag(c, p)}<span class="pc__period">{p["period"]}</span></p>
            <h3 class="pc__name">{p["name"]}</h3>
            <p class="pc__tagline">{p["tagline"]}</p>
            <ul class="tags">{tags_html}</ul>
            <span class="pc__go">{ui["see_project"]}{SVG["arrow"]}</span>
          </a>
        </li>"""

    cards = "".join(card(p, i) for i, p in enumerate(projects))
    cat_counts = {k: (len(projects) if k == "all" else sum(1 for p in projects if k in p["cats"])) for k in pr["cats"]}
    pfilters = ""
    for k, label in pr["cats"].items():
        if not cat_counts[k]:
            continue
        dot = "" if k == "all" else f'<i class="dot dot--{k}"></i>'
        pfilters += f'<button type="button" class="chipbtn" data-cat="{k}" aria-pressed="{"true" if k == "all" else "false"}">{dot}{label}<span>{cat_counts[k]}</span></button>'
    more = "".join(f'<li class="reveal"><span class="more__name">{n}</span><span class="more__stack">{s}</span></li>' for n, s in pr["more"])

    # chiffres
    tiles = figures([(n.format(**facts_gh), k, d.format(**facts_gh), "") for n, k, d in stt["tiles"]])
    rows = []
    for p in projects:
        start, end = project_dates(p, gh)
        if start:
            rows.append({"name": p["name"], "start": start, "end": end, "cat": p["cats"][0], "href": project_url(c, p), "title": f'{p["name"]} · {p["period"]}'})
    rows += [dict(r, title=r["name"]) for r in stt.get("gantt_extra", [])]
    site_repo = gh["public"].get("BuildRunnerFr.github.io")
    if site_repo:
        rows.append({"name": "Ce site" if lang == "fr" else "This site", "start": site_repo["created"], "end": "", "cat": "web", "title": "buildrunnerfr.github.io"})
    for s, e in gh["private"]:
        rows.append({"name": ui["private_repo"], "start": s, "end": e, "cat": "private", "title": ui["private_repo"]})
    g_first, g_last = min(r["start"] for r in rows), date.today().isoformat()
    legend = "".join(f'<li><i class="dot dot--{k}"></i>{label}</li>' for k, label in pr["cats"].items() if k != "all" and any(r["cat"] == k for r in rows))
    legend += f'<li><i class="dot dot--private"></i>{ui["private_repo"]}</li><li><i class="dot dot--live"></i>{ui["status"]["live"]}</li>'

    # à côté : une étagère de mangas en volume, puis les autres centres d'intérêt
    def book(i, it):
        # la couverture : une image rangée dans assets/mangas/ (plusieurs largeurs), sinon le titre et l'auteur en toutes lettres
        files = [(w, f"/assets/mangas/{it['slug']}-{w}.webp") for w in (160, 320) if (ROOT / "assets" / "mangas" / f"{it['slug']}-{w}.webp").exists()]
        if files:
            front = (
                f'<span class="book__front book__front--art"><img src="{files[-1][1]}" srcset="{srcset(files)}" sizes="(min-width: 900px) 148px, 12vw" '
                f'alt="{escape(it["title"])}, {escape(it["author"])}" width="320" height="480" loading="lazy" decoding="async"></span>'
            )
        else:
            front = f'<span class="book__front"><b>{it["title"]}</b><small>{it["author"]}</small></span>'
        return (
            f'<li class="book book--{i % 4}" style="--i:{min(i, 9)}"><div class="book__box">'
            f'<span class="book__spine" aria-hidden="true">{it["title"]}</span>{front}</div></li>'
        )

    sh = lf["shelf"]
    books = "".join(book(i, it) for i, it in enumerate(sh["items"]))
    hobbies = "".join(
        f'<li class="hobby reveal" style="--i:{i % 3}"><h3>{p["name"]}</h3>{"<p>" + p["text"] + "</p>" if p["text"] else ""}</li>'
        for i, p in enumerate(lf["panels"])
    )

    # version jeu : répliques, étapes de la carte, liens et photos résolus ici
    shots_by_org = {
        it["logo"]: [{"src": f'/assets/photos/{ph["stem"]}-480.webp', "alt": ph["alt"]} for ph in it.get("photos", [])]
        for it in x["items"]
    }
    play_data = json.dumps(
        {
            "menu": pl["menu"], "nodes": pl["nodes"],
            "stops": [dict(st, photos=shots_by_org.get(st.get("photos"), [])) for st in pl["stops"]],
            "map": pl["map"],
            "links": {"@cv": CV, "@mail": "mailto:" + EMAIL, "@linkedin": LINKEDIN, "@github": GITHUB},
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")
    topics = "".join(f'<span class="topic" data-topic="{k}">{v}</span>' for k, v in pl["topics"].items())

    jsonld = json.dumps(
        {
            "@context": "https://schema.org", "@type": "Person", "name": "Ethan Blombou", "url": SITE + "/",
            "image": SITE + "/assets/ethan.jpg", "email": "mailto:" + EMAIL, "jobTitle": x["items"][0]["role"],
            "worksFor": {"@type": "Organization", "name": "Société Générale"},
            "alumniOf": [{"@type": "CollegeOrUniversity", "name": "IMT Atlantique"}, {"@type": "CollegeOrUniversity", "name": "IUT de Vélizy"}],
            "knowsLanguage": ["fr", "en", "es"], "sameAs": [LINKEDIN, GITHUB],
        },
        ensure_ascii=False,
    )
    gantt_label = stt["gantt_label"].format(start=day_label(g_first, months), end=day_label(g_last, months))

    body = f"""<main id="main">
  <span id="top-of-page"></span>

  <section class="play" id="play" aria-label="{escape(pl["label"])}">
    <div class="wrap">
      <div class="scene scene--talk" data-scene="talk">
        <div class="talk">
          <div class="talk__text">
            <p class="talk__top">
              <span class="badge"><span class="badge__dot" aria-hidden="true"></span>{h["badge"]}</span>
              <button class="talk__classic" type="button" data-mode-set="classic"><span>{pl["skip"]}</span> {pl["to_classic"]}{SVG["arrow"]}</button>
            </p>
            <div class="talk__id">
              <img class="talk__face" src="/assets/ethan-400.webp" alt="" width="400" height="542" decoding="async">
              <h2 class="talk__name">Ethan Blombou</h2>
            </div>
            <p class="talk__you" id="talk-you" hidden></p>
            <p class="bubble talk__say" id="talk-say" tabindex="0" role="button" aria-label="{escape(pl["say_label"])}"></p>
            <p class="sr-only" id="talk-live" aria-live="polite"></p>
            <div class="choices" id="talk-choices"></div>
            <p class="talk__foot"><span>{pl["topics_label"]} :</span>{topics}</p>
          </div>
          {portrait("talk")}
        </div>
      </div>
      <div class="scene scene--map" data-scene="map" hidden>
        <div class="mapbar">
          <button class="btn btn--ghost" type="button" data-scene-go="talk">{SVG["back"]}{pl["map"]["back"]}</button>
          <h2 class="mapbar__t" id="map-title" tabindex="-1">{pl["map"]["title"]}</h2>
          <p class="mapbar__hint">{pl["map"]["hint"]}</p>
          <button class="talk__classic" type="button" data-mode-set="classic">{pl["to_classic"]}{SVG["arrow"]}</button>
        </div>
        <div class="map">
          <div class="map__board pcard">
            <svg id="map" viewBox="0 -44 800 534" role="group" aria-label="{escape(pl["map"]["label"])}">
              <path class="road" id="road" d=""/><path class="road road--done" id="road-done" d=""/>
              <g id="stops"></g><g id="mini" aria-hidden="true">{MINI}</g>
            </svg>
            <p class="map__hud" id="map-hud" aria-live="polite"></p>
          </div>
          <div class="map__side">
            <div class="bag pcard"><span class="bag__t">{pl["map"]["bag"]}</span><span class="bag__items" id="bag"></span></div>
            <article class="map__panel pcard" id="map-panel" aria-live="polite">
              <p class="map__tag" id="p-tag"></p><h3 id="p-title"></h3><p class="map__what" id="p-what"></p>
              <div class="map__shots" id="p-shots"></div><p class="bubble" id="p-say"></p><p class="map__more" id="p-more"></p>
            </article>
            <div class="map__ctrl">
              <button class="btn btn--ghost" id="map-prev" type="button" aria-label="{escape(pl["map"]["prev"])}">←</button>
              <button class="btn btn--accent" id="map-next" type="button">{pl["map"]["next"]} →</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <script type="application/json" id="play-data">{play_data}</script>
  </section>

  <section class="hero" id="home">
    <canvas class="net" id="net" aria-hidden="true"></canvas>
    <div class="wrap hero__grid">
      <div class="hero__text">
        <p class="badge"><span class="badge__dot" aria-hidden="true"></span>{h["badge"]}</p>
        <h1 class="hero__name">Ethan Blombou</h1>
        <p class="hero__statement">{h["statement"]}</p>
        <p class="hero__lead">{h["lead"]}</p>
        <div class="hero__cta">
          <a class="btn btn--accent" href="#projects">{h["cta_projects"]}{SVG["arrow"]}</a>
          <a class="btn btn--ghost" href="{CV}" download title="{escape(ui["cv_note"])}">{ui["cv"]}{SVG["down"]}</a>
          <span class="socials" role="group" aria-label="{escape(ui["socials"])}">
            <a href="{GITHUB}" rel="noopener me" aria-label="GitHub">{SVG["github"]}</a>
            <a href="{LINKEDIN}" rel="noopener me" aria-label="LinkedIn">{SVG["linkedin"]}</a>
          </span>
        </div>
      </div>
      {portrait("hero", net_cap)}
    </div>
    <div class="wrap"><ul class="figs figs--hero" aria-label="{escape(ui["stats_label"])}">{keyfigs}</ul></div>
  </section>

  <section class="section" id="about" aria-labelledby="about-title">
    <div class="wrap">
      {shead(a["eyebrow"], a["title"], "about-title")}
      <div class="about">
        <div class="about__main">
          <div class="prose reveal">{paragraphs}</div>
          <blockquote class="quote reveal"><p>{quote}</p></blockquote>
        </div>
        <aside class="about__side">
          <div class="reveal">{photo("presentation", 1000, 918, a["photo"], "(min-width: 900px) 440px, 64vw", "shot shot--about")}</div>
          <dl class="facts reveal" aria-label="{escape(a["facts_title"])}">{facts}</dl>
        </aside>
      </div>
    </div>
  </section>

  <section class="section" id="skills" aria-labelledby="skills-title">
    <div class="wrap">
      {shead(sk["eyebrow"], sk["title"], "skills-title")}
      <div class="skillframe reveal">{skillrows}</div>
    </div>
  </section>

  <section class="section" id="journey" aria-labelledby="journey-title">
    <div class="wrap">
      {shead(jn["eyebrow"], jn["title"], "journey-title", x["intro"])}
      <div class="chips reveal" role="group" aria-label="{escape(jn["eyebrow"])}">{jtabs}</div>
      <ol class="steps">{steps}</ol>
    </div>
  </section>

  <section class="section" id="projects" aria-labelledby="projects-title">
    <div class="wrap">
      {shead(pr["eyebrow"], pr["title"], "projects-title", pr["intro"])}
      <div class="chips reveal" role="group" aria-label="{escape(pr["eyebrow"])}">{pfilters}</div>
      <ul class="pcs">{cards}
      </ul>
      <h3 class="subtitle reveal">{pr["more_title"]}</h3>
      <ul class="more">{more}</ul>
    </div>
  </section>

  <section class="section" id="stats" aria-labelledby="stats-title">
    <div class="wrap">
      {shead(stt["eyebrow"], stt["title"], "stats-title")}
      <ul class="figs">{tiles}</ul>
      <div class="plots">
        <figure class="plot plot--heat reveal">
          <figcaption class="label">{stt["activity"].format(**facts_gh)}</figcaption>
          <div class="heat" role="img" aria-label="{escape(stt["activity_label"].format(**facts_gh))}">{heatmap(gh["days"], months)}</div>
          <p class="plot__note">{stt["activity_note"]}<span class="heat__key" aria-hidden="true">{stt["less"]}<i class="l0"></i><i class="l1"></i><i class="l2"></i><i class="l3"></i><i class="l4"></i>{stt["more"]}</span></p>
        </figure>
        <figure class="plot plot--langs reveal" style="--i:1">
          <figcaption class="label">{stt["languages"]}</figcaption>
          {lang_bar(gh["languages"], stt["other"], lang)}
          <p class="plot__note">{stt["languages_note"]}</p>
        </figure>
      </div>
      <figure class="plot plot--gantt reveal">
        <figcaption class="label">{stt["gantt"]}</figcaption>
        <ul class="legend">{legend}</ul>
        <div class="gantt" role="group" aria-label="{escape(gantt_label)}">{gantt(rows, months, ui["today"])}</div>
        <p class="plot__note">{stt["gantt_note"]}</p>
      </figure>
    </div>
  </section>

  <section class="section" id="life" aria-labelledby="life-title">
    <div class="wrap">
      {shead(lf["eyebrow"], lf["title"], "life-title")}
      <article class="shelf reveal">
        <div class="shelf__head"><div><h3>{sh["name"]}</h3><p>{sh["text"]}</p></div>
          <div class="shelf__nav"><span class="shelf__hint">{sh["hint"]}</span>
            <button class="round" type="button" data-nudge="-1" aria-label="{escape(sh["prev"])}">{SVG["back"]}</button>
            <button class="round" type="button" data-nudge="1" aria-label="{escape(sh["next"])}">{SVG["arrow"]}</button></div></div>
        <div class="shelf__row marquee" data-marquee data-speed="26"><ul class="books" aria-label="{escape(sh["label"])}">{books}</ul></div>
      </article>
      <ul class="hobbies">{hobbies}</ul>
      <p class="playline reveal"><span><b>{lf["play"]["name"]}.</b> {lf["play"]["text"]}</span><button class="btn btn--ghost btn--small" type="button" data-mode-set="play">{SVG["play"]}{ui["play"]}</button></p>
    </div>
  </section>

  <section class="section section--last" id="contact" aria-labelledby="contact-title">
    <div class="wrap">
      <div class="contact">
        {shead(ct["eyebrow"], ct["title"], "contact-title", ct["text"])}
        <div class="contact__mail reveal">
          <a class="mail" href="mailto:{EMAIL}"><span class="sr-only">{ct["email_label"]} : </span>{EMAIL}</a>
          <button class="copy" type="button" data-copy="{EMAIL}" data-done="{ui["copied"]}">{ui["copy"]}</button>
          <span class="copy__status" role="status" aria-live="polite"></span>
        </div>
        <ul class="contact__links reveal">
          <li><a class="link link--cv" href="{CV}" download>{ui["cv"]}<span class="link__handle">{ui["cv_note"]}</span>{SVG["down"]}</a></li>
          <li><a class="link" href="{LINKEDIN}" rel="noopener me">{ct["linkedin"]}<span class="link__handle">in/ethan-blombou</span>{SVG["arrow"]}</a></li>
          <li><a class="link" href="{GITHUB}" rel="noopener me">{ct["github"]}<span class="link__handle">BuildRunnerFr</span>{SVG["arrow"]}</a></li>
        </ul>
      </div>
    </div>
  </section>

</main>"""
    return shell(
        c, title=c["meta"]["title"], description=c["meta"]["description"], path=c["path"], alt_path=c["other_path"], body=body, home="",
        extra_head=f'<link rel="preload" href="/assets/fonts/poppins-500.woff2" as="font" type="font/woff2" crossorigin>\n<script type="application/ld+json">{jsonld}</script>\n',
        scripts=("main", "net", "play"),
    )


# ---------- page d'un projet ----------

def project_page(c, gh, p, prev, nxt, alt_path):
    lang, ui, pr = c["lang"], c["ui"], c["projects"]
    months = ui["months"]
    home_url = c["path"]
    repo = gh["public"].get(p.get("repo", ""))
    repo_url = f'{GITHUB}/{p["repo"]}' if repo else ""
    readme_html, minutes = "", 1
    if repo:
        src = ROOT / "content" / "readmes" / f'{p["repo"]}.md'
        if src.exists():
            readme_html = md(src.read_text(encoding="utf-8"), f'{repo_url}/blob/{repo["branch"]}', p.get("readme_keep"))
            minutes = max(1, round(len(re.sub(r"<[^>]+>", " ", readme_html).split()) / 220))
    readme_lang = p.get("readme_lang", "fr")
    other = ui["readme_en"] if readme_lang == "en" else ui["readme_fr"]
    hl = "".join(f"<li>{t}</li>" for t in p["highlights"])
    tags_html = "".join(f"<li>{escape(t)}</li>" for t in p["tags"])
    logos = "".join(logo(stem, name, "plogo") for stem, name in p["logos"])
    part = f'<div class="callout reveal"><p class="label">{ui["my_part"]}</p><p>{p["part"]}</p></div>' if p.get("part") else ""
    note = f'<p class="pp__note reveal">{p["note"]}</p>' if p.get("note") else ""
    gallery = ""
    if p.get("photo"):
        ph = p["photo"]
        gallery = '<div class="pp__gallery reveal">' + photo(ph["stem"], ph["w"], ph["h"], ph, "(min-width: 960px) 700px, 66vw", "shot") + "</div>"
    if p.get("gallery"):
        org = next(it for it in c["experience"]["items"] if it["logo"] == p["gallery"])
        gallery = '<div class="pp__gallery pp__gallery--3 reveal">' + "".join(
            photo(ph["stem"], ph["w"], ph["h"], ph, "(min-width: 900px) 200px, 26vw", "shot shot--step") for ph in org.get("photos", [])
        ) + "</div>"
    readme = ""
    if readme_html:
        readme = (
            f'<section class="pp__readme reveal"><h2>{ui["readme"]}</h2><p class="monoline">{ui["readme_note"].format(date=day_label(gh["synced"], months))}'
            f'{" " + other if other else ""}</p><div class="md"{" lang=en" if readme_lang == "en" else " lang=fr"}>{readme_html}</div></section>'
        )
    langs = f'<div class="side__block"><p class="label">{ui["languages"]}</p>{lang_bar(repo["languages"], c["stats"]["other"], lang)}</div>' if repo and repo["languages"] else ""
    repo_btn = f'<a class="btn btn--dark btn--wide" href="{repo_url}" rel="noopener">{SVG["github"]}{ui["repo"]}</a>' if repo else f'<p class="pp__norepo">{ui["no_repo"]}</p>'
    if p.get("site"):
        repo_btn = f'<a class="btn btn--accent btn--wide" href="{p["site"]}" rel="noopener">{ui["site"]}{SVG["arrow"]}</a>' + repo_btn
    logos_block = f'<div class="side__logos">{logos}</div>' if logos else ""
    side = f"""
      <aside class="pp__side">
        {repo_btn}
        <div class="side">
          <div class="side__row"><span class="label">{ui["period"]}</span><span>{p["period"]}</span></div>
          <div class="side__block"><p class="label">{ui["context"]}</p><p>{p["context"]}</p>{logos_block}</div>
          <div class="side__block"><p class="label">{ui["stack"]}</p><ul class="tags">{tags_html}</ul></div>
          {langs}
        </div>
      </aside>"""

    def neighbour(q, label, cls):
        return f'<a class="pp__neigh pp__neigh--{cls}" href="{project_url(c, q)}"><span class="label">{label}</span><strong>{q["name"]}</strong></a>'

    cat = pr["cats"][p["cats"][0]]
    body = f"""<main id="main" class="pp">
  <span id="top-of-page"></span>
  <div class="wrap">
    <a class="back" href="{home_url}#projects">{SVG["back"]}{ui["all_projects"]}</a>
    <div class="pp__cover" style="view-transition-name:cover-{p["key"]}">{project_cover(p, "pp__img", "(min-width: 1180px) 1080px, (min-width: 700px) 94vw, 66vw", True)}</div>
    <p class="pp__meta"><i class="dot dot--{p["cats"][0]}"></i>{cat}<span>{ui["kinds"][p["kind"]]}</span>{live_tag(c, p)}<span>{ui["min_read"].format(n=minutes)}</span></p>
    <h1 class="pp__title">{p["name"]}</h1>
    <p class="pp__tagline">{p["tagline"]}</p>
    <div class="pp__grid">
      <div class="pp__main">
        <p class="pp__sum">{p["desc"]}</p>
        <ul class="hl hl--big">{hl}</ul>
        {part}
        {gallery}
        {note}
        {readme}
      </div>{side}
    </div>
    <nav class="pp__nav" aria-label="{escape(ui["all_projects"])}">{neighbour(prev, ui["prev_project"], "prev")}{neighbour(nxt, ui["next_project"], "next")}</nav>
    <p class="pp__cta"><a class="btn btn--accent" href="{home_url}#contact">{ui["contact_cta"]}{SVG["arrow"]}</a></p>
  </div>
</main>"""
    return shell(
        c, title=f'{p["name"]} · Ethan Blombou', description=p["desc"], path=project_url(c, p), alt_path=alt_path, body=body, home=home_url, page="project",
    )


def render_404(c):
    ui = c["ui"]
    return f"""<!doctype html>
<html lang="{c["lang"]}" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>404 · Ethan Blombou</title>
<meta name="robots" content="noindex">
<meta name="theme-color" content="{THEME}">
{ICONS}
<link rel="stylesheet" href="/assets/css/style.css">
</head>
<body class="nf">
<main class="nf__in">
  <p class="nf__code" aria-hidden="true">404</p>
  <h1 class="nf__title">{ui["nf_title"]}</h1>
  <p class="nf__text">{ui["nf_text"]}</p>
  <p><a class="btn btn--accent" href="/">{ui["nf_back"]}{SVG["arrow"]}</a></p>
</main>
</body>
</html>
"""


def main():
    gh = json.loads((ROOT / "content" / "github.json").read_text(encoding="utf-8"))
    contents = {}
    for lang in ("fr", "en"):
        c = json.loads((ROOT / "content" / f"{lang}.json").read_text(encoding="utf-8"))
        contents[lang] = walk(c, nbsp_fr) if lang == "fr" else c
    urls = []
    for lang, out in (("fr", "index.html"), ("en", "en/index.html")):
        c = contents[lang]
        other = contents["en" if lang == "fr" else "fr"]
        target = ROOT / out
        target.parent.mkdir(exist_ok=True)
        target.write_text(home(c, gh), encoding="utf-8")
        urls.append(c["path"])
        projects = c["projects"]["list"]
        for i, p in enumerate(projects):
            twin = next(q for q in other["projects"]["list"] if q["key"] == p["key"])
            page = project_page(c, gh, p, projects[i - 1], projects[(i + 1) % len(projects)], project_url(other, twin))
            dest = ROOT / project_url(c, p).strip("/") / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(page, encoding="utf-8")
            urls.append(project_url(c, p))
        print("écrit", out, "et", len(projects), "pages de projet")
    (ROOT / "404.html").write_text(render_404(contents["fr"]), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{SITE}{u}</loc></url>\n" for u in urls)
        + "</urlset>\n",
        encoding="utf-8",
    )
    print("écrit 404.html et sitemap.xml")


if __name__ == "__main__":
    main()
