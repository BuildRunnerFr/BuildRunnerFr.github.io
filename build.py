#!/usr/bin/env python3
"""Génère index.html (français) et en/index.html (anglais).

Les textes sont dans content/fr.json et content/en.json.
Après une modification :  python3 build.py
Aucune dépendance : bibliothèque standard uniquement.
"""
import json
import re
import struct
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
SITE = "https://buildrunnerfr.github.io"
EMAIL = "ethancte@gmail.com"
LINKEDIN = "https://www.linkedin.com/in/ethan-blombou"
GITHUB = "https://github.com/BuildRunnerFr"
SECTIONS = ["home", "about", "experience", "projects", "skills", "life", "contact"]


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
    """Dimensions intrinsèques d'un PNG ou d'un SVG, pour éviter les sauts de mise en page."""
    data = path.read_bytes()
    if path.suffix == ".png":
        return struct.unpack(">II", data[16:24])
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
    for ext in ("svg", "png", "webp"):
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
        return f'<img class="chip__icon" src="/assets/icons/{slug}.svg" alt="" width="18" height="18" loading="lazy" decoding="async">'
    return ""


DOWN = '<svg class="dl" viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><path d="M10 3v10M5.500 9l4.500 4.500L14.500 9M4 16.500h12" fill="none" stroke="currentColor" stroke-width="1.800" stroke-linecap="round" stroke-linejoin="round"/></svg>'
CV = "/assets/cv-ethan-blombou.pdf"


def photo(stem, sizes_w, w, h, meta, sizes, cls="shot"):
    """Photo en WebP à deux largeurs, avec légende."""
    srcset = ", ".join(f"/assets/photos/{stem}-{x}.webp {x}w" for x in sizes_w)
    return (
        f'<figure class="{cls}"><img src="/assets/photos/{stem}-{sizes_w[-1]}.webp" srcset="{srcset}" sizes="{sizes}" '
        f'alt="{escape(meta["alt"])}" width="{w}" height="{h}" loading="lazy" decoding="async">'
        f'<figcaption>{meta["caption"]}</figcaption></figure>'
    )


PLAY = '<svg viewBox="0 0 20 20" width="14" height="14" aria-hidden="true"><path d="M6 4.500v11l9-5.500z" fill="currentColor"/></svg>'

# dessins au trait des cases « À côté » (formes simples, aucune œuvre existante)
ART = {
    "manga": '<svg viewBox="0 0 120 90"><path d="M14 40c0-17 20-30 46-30s46 13 46 30-20 30-46 30c-6 0-12-.700-17-2L24 80l5-18C19.500 56.500 14 48.700 14 40z" fill="var(--card)" stroke="currentColor" stroke-width="3.500" stroke-linejoin="round"/><circle cx="44" cy="40" r="4"/><circle cx="60" cy="40" r="4"/><circle cx="76" cy="40" r="4"/></svg>',
    "chess": '<span class="board"></span>',
    "foot": '<svg viewBox="0 0 160 120" preserveAspectRatio="xMaxYMid slice" fill="none" stroke="currentColor" stroke-width="2.200"><path d="M92 -40v200M160 28h-30v64h30M160 44h-12v32h12"/><circle cx="92" cy="60" r="30"/><circle cx="92" cy="60" r="2.600" fill="currentColor" stroke="none"/></svg>',
    "abroad": '<svg viewBox="0 0 240 70" preserveAspectRatio="xMinYMid meet" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="M12 60C62 -6 178 -6 228 60" stroke-dasharray="0.100 9"/><circle cx="12" cy="60" r="6" fill="currentColor" stroke="none"/><circle cx="228" cy="60" r="6" fill="currentColor" stroke="none"/><path d="M108 3l24 7.500-24 7.500 5.500-7.500z" fill="currentColor" stroke-linejoin="round" stroke-width="2"/></svg>',
    "ctf": '<svg viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path d="M18 74V8"/><path d="M18 12h44l-10 15 10 15H18z" fill="var(--accent)"/></svg>',
    "quant": '<svg viewBox="0 0 200 80" preserveAspectRatio="none" fill="none" stroke="currentColor" stroke-width="3.500" stroke-linecap="round" stroke-linejoin="round"><path d="M4 66l28-14 22 8 30-30 24 14 30-26 26 10 32-22" vector-effect="non-scaling-stroke"/></svg>',
}

ARROW = '<svg class="arrow" viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><path d="M4 10h11M10.5 5l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def tags(items):
    return '<ul class="tags">' + "".join(f"<li>{escape(t)}</li>" for t in items) + "</ul>"


def kind_badge(c, kind):
    return f'<span class="kind kind--{kind}">{c["ui"][kind]}</span>'


def project_logos(c, items):
    out = "".join(logo(stem, name, "plogo") for stem, name in items)
    return f'<div class="project__logos">{out}</div>' if out else ""


def part_block(c, text):
    if not text:
        return ""
    return f'<div class="part"><p class="part__label">{c["ui"]["my_part"]}</p><p>{text}</p></div>'


def code_link(c, p):
    return (
        f'<a class="link" href="{p["url"]}" rel="noopener">'
        f'{c["ui"]["code"]}<span class="sr-only"> : {escape(p["name"])}</span>{ARROW}</a>'
    )


def words(text):
    """Chaque mot dans un masque, pour l'apparition mot à mot des titres."""
    return " ".join(
        f'<span class="w"><span style="--i:{i}">{w}</span></span>' for i, w in enumerate(text.split(" "))
    )


def shead(c, n, kicker, title, id_):
    return (
        f'<header class="shead"><p class="shead__k"><span class="shead__n">{c["ui"]["chapter"]} {n}</span>{kicker}</p>'
        f'<h2 class="shead__t reveal" id="{id_}" aria-label="{escape(title)}">{words(title)}</h2></header>'
    )


def render(c):
    lang = c["lang"]
    url = SITE + c["path"]
    ui = c["ui"]
    h, a, x, pr, sk, ct = c["hero"], c["about"], c["experience"], c["projects"], c["skills"], c["contact"]
    lf = c["life"]
    pn = lf["piano"]

    pl = c["play"]
    nav_links = (
        '<li class="nav__mode"><button type="button" class="mode" data-mode-switch>'
        f'<span class="mode__classic">{pl["to_classic"]}</span><span class="mode__play">{PLAY}{pl["to_play"]}</span></button></li>'
    ) + "".join(f'<li><a href="#{s}" data-nav="{s}">{c["nav"][s]}</a></li>' for s in SECTIONS[1:])
    lang_switch = (
        f'<div class="lang" role="group" aria-label="{ui["lang_label"]}">'
        + "".join(
            f'<a href="{c["path"] if l == lang else c["other_path"]}" lang="{l}" hreflang="{l}" data-lang-link'
            + (' aria-current="true"' if l == lang else "")
            + f'><span aria-hidden="true">{l.upper()}</span><span class="sr-only">{"Français" if l == "fr" else "English"}</span></a>'
            for l in ("fr", "en")
        )
        + "</div>"
    )

    route = "".join(
        f'<li{" class=is-target" if i >= 2 else ""}>{name}</li>' for i, name in enumerate(ui["route"])
    )

    name_lines = " ".join(
        '<span class="line" aria-hidden="true"><span>'
        + "".join(f'<span class="l">{ch}</span>' for ch in word)
        + "</span></span>"
        for word in ("Ethan", "Blombou")
    )
    stats = "".join(
        f'<li class="stat reveal"><p class="stat__n">{st[3] if len(st) > 3 else ""}<span data-count="{st[0]}">{st[0]}</span></p>'
        f'<p class="stat__k">{st[1]}</p><p class="stat__d">{st[2]}</p></li>'
        for st in a["stats"]
    )
    facts = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in a["facts"])

    xp = ""
    for i, it in enumerate(x["items"], 1):
        logos = logo(it["logo"], it["org"])
        if it.get("logo2"):
            logos += logo(it["logo2"], it["org2"])
        bullets = "".join(f"<li>{b}</li>" for b in it["bullets"])
        shots = "".join(
            photo(ph["stem"], tuple(ph.get("sizes", (480, 960))), ph["w"], ph["h"], ph, "(min-width: 800px) 230px, 46vw", "shot shot--hop")
            for ph in it.get("photos", [])
        )
        shots = f'<div class="hop__photos">{shots}</div>' if shots else ""
        note = it.get("note")
        note = (
            f'<p class="bubble bubble--note"><span class="bubble__label">{note["label"]}</span>{note["text"]}</p>'
            if note
            else ""
        )
        xp += f"""
          <li class="hop reveal">
            <p class="hop__n" aria-hidden="true">{i:02d}</p>
            <p class="hop__dates">{it["dates"]}</p>
            <div class="hop__body">
              <div class="hop__logos">{logos}</div>
              <h3 class="hop__role">{it["role"]}</h3>
              <p class="hop__org">{it["org"]}</p>
              <ul class="hop__list">{bullets}</ul>
              {shots}
              {note}
            </div>
          </li>"""

    edu = ""
    for it in x["edu"]:
        edu += f"""
            <li class="row reveal">
              <div class="row__logo">{logo(it["logo"], it["org"])}</div>
              <div class="row__main"><h4>{it["org"]}</h4><p>{it["what"]}</p></div>
              <p class="row__dates">{it["dates"]}</p>
            </li>"""
    certs = ""
    for it in x["certs"]:
        certs += f"""
            <li class="row row--cert reveal">
              <div class="row__main"><h4>{it["name"]}</h4><p>{it["issuer"]}</p></div>
            </li>"""

    def project(p, featured=False):
        media = ""
        if featured and p.get("photo"):
            media = (
                '<div class="project__media project__media--duo">'
                + photo("ecoute", (800, 1400), 1400, 934, p["photo"], "(min-width: 940px) 620px, 100vw")
                + f'<img class="project__screen" src="{p["image"]}" alt="{escape(p["image_alt"])}" '
                f'width="{p["image_w"]}" height="{p["image_h"]}" loading="lazy" decoding="async"></div>'
            )
        elif p.get("photo"):
            media = (
                '<div class="project__media project__media--photo">'
                + photo("eaic-salle", (640, 1200), 1200, 800, p["photo"], "(min-width: 760px) 560px, 100vw")
                + "</div>"
            )
        elif p.get("image"):
            media = (
                f'<div class="project__media"><img src="{p["image"]}" alt="{escape(p["image_alt"])}" '
                f'width="{p["image_w"]}" height="{p["image_h"]}" loading="lazy" decoding="async"></div>'
            )
        return f"""
        <article class="project{" project--featured" if featured else ""} reveal">
          {media}
          <div class="project__body">
            <p class="project__context">{kind_badge(c, p["kind"])}<span>{p["context"]}</span></p>
            <h3 class="project__name">{p["name"]}</h3>
            <p class="project__tagline">{p["tagline"]}</p>
            <p class="project__desc">{p["desc"]}</p>
            {part_block(c, p.get("part"))}
            {tags(p["tags"])}
            <div class="project__foot">{code_link(c, p)}{project_logos(c, p["logos"])}</div>
          </div>
        </article>"""

    featured = project(pr["featured"], True)
    cards = "".join(project(p) for p in pr["items"])
    more = "".join(
        f'<li class="reveal"><span class="more__name">{n}</span><span class="more__stack">{s}</span></li>'
        for n, s in pr["more"]
    )

    total = sum(len(g["items"]) for g in sk["groups"])
    filters = f'<button type="button" class="filter" data-filter="all" aria-pressed="true">{ui["all"]}<span>{total}</span></button>'
    groups = ""
    for g in sk["groups"]:
        filters += f'<button type="button" class="filter" data-filter="{g["key"]}" aria-pressed="false">{g["name"]}<span>{len(g["items"])}</span></button>'
        chips = "".join(f'<li class="chip">{icon(slug)}<span>{escape(name)}</span></li>' for name, slug in g["items"])
        groups += (
            f'<div class="group reveal" data-group="{g["key"]}"><h3 class="group__name">{g["name"]}'
            f'<span class="group__count">{len(g["items"])}</span></h3><ul class="chips">{chips}</ul></div>'
        )
    langs = "".join(
        f'<li class="chip"><span>{n}</span><span class="chip__level">{lv}</span></li>' for n, lv in sk["languages"]
    )
    groups += (
        f'<div class="group reveal" data-group="lang"><h3 class="group__name">{sk["languages_title"]}'
        f'<span class="group__count">{len(sk["languages"])}</span></h3><ul class="chips">{langs}</ul></div>'
    )

    paragraphs = "".join(f"<p>{p}</p>" for p in a["paragraphs"])
    quote = f"«\u00a0{a['quote']}\u00a0»" if lang == "fr" else f"“{a['quote']}”"

    # clavier : deux octaves, do à do ; les touches noires sont rattachées à la blanche qui les précède
    keys = ""
    for i in range(15):
        step = i % 7
        midi = 60 + (0, 2, 4, 5, 7, 9, 11)[step] + 12 * (i // 7)
        name = pn["notes"][step]
        octave = i // 7 + 1
        black = ""
        if step in (0, 1, 3, 4, 5) and i < 14:
            black = (
                f'<button type="button" class="pk__b" data-note="{midi + 1}" tabindex="-1" '
                f'aria-label="{name} {pn["sharp"]} {octave}"></button>'
            )
        keys += (
            f'<span class="pk"><button type="button" class="pk__w" data-note="{midi}" tabindex="{0 if i == 0 else -1}" '
            f'aria-label="{name} {octave}"><span aria-hidden="true">{name}</span></button>{black}</span>'
        )
    cases = "".join(
        f"""
        <article class="case case--{p["key"]} reveal">
          <div class="case__art" aria-hidden="true">{ART.get(p["key"], "")}</div>
          <h3 class="case__name">{p["name"]}</h3>
          {f'<p class="case__text">{p["text"]}</p>' if p["text"] else ""}
        </article>"""
        for p in lf["panels"]
    )

    def portrait(key):
        return f"""<figure class="portrait portrait--{key}">
        <span class="burst" aria-hidden="true"></span>
        <div class="stamp" aria-hidden="true">
          <svg class="stamp__ring" viewBox="0 0 120 120">
            <defs><path id="stamp-path-{key}" d="M60 60m-46 0a46 46 0 1 1 92 0a46 46 0 1 1-92 0"/></defs>
            <text><textPath href="#stamp-path-{key}" textLength="286">{ui["stamp"].upper()}</textPath></text>
          </svg>
          <svg class="stamp__arrow" viewBox="-3 -3 30 30"><path d="M0 24 24 0M6 0h18v18" fill="none" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <picture>
          <source type="image/webp" srcset="/assets/ethan-400.webp 400w, /assets/ethan-640.webp 640w" sizes="(min-width: 900px) 250px, 190px">
          <img src="/assets/ethan.jpg" alt="{escape(h["photo_alt"])}" width="890" height="1205" fetchpriority="high" decoding="async">
        </picture>
      </figure>"""

    # données de la version jeu : répliques, étapes de la carte, liens et photos résolus ici
    shots_by_org = {
        it["logo"]: [{"src": f'/assets/photos/{ph["stem"]}-480.webp', "alt": ph["alt"]} for ph in it.get("photos", [])]
        for it in x["items"]
    }
    play_data = json.dumps(
        {
            "menu": pl["menu"],
            "nodes": pl["nodes"],
            "stops": [dict(st, photos=shots_by_org.get(st.get("photos"), [])) for st in pl["stops"]],
            "map": pl["map"],
            "links": {"@cv": CV, "@mail": "mailto:" + EMAIL, "@linkedin": LINKEDIN, "@github": GITHUB},
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")
    topics = "".join(f'<span class="topic" data-topic="{k}">{v}</span>' for k, v in pl["topics"].items())

    jsonld = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": "Ethan Blombou",
            "url": SITE + "/",
            "image": SITE + "/assets/ethan.jpg",
            "email": "mailto:" + EMAIL,
            "jobTitle": x["items"][0]["role"],
            "worksFor": {"@type": "Organization", "name": "Société Générale"},
            "alumniOf": [
                {"@type": "CollegeOrUniversity", "name": "IMT Atlantique"},
                {"@type": "CollegeOrUniversity", "name": "IUT de Vélizy"},
            ],
            "knowsLanguage": ["fr", "en", "es"],
            "sameAs": [LINKEDIN, GITHUB],
        },
        ensure_ascii=False,
    )

    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{c["meta"]["title"]}</title>
<meta name="description" content="{escape(c["meta"]["description"])}">
<meta name="author" content="Ethan Blombou">
<meta name="theme-color" content="#b8401f">
<meta name="color-scheme" content="light">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="fr" href="{SITE}/">
<link rel="alternate" hreflang="en" href="{SITE}/en/">
<link rel="alternate" hreflang="x-default" href="{SITE}/">
<meta property="og:type" content="profile">
<meta property="og:site_name" content="Ethan Blombou">
<meta property="og:title" content="{escape(c["meta"]["title"])}">
<meta property="og:description" content="{escape(c["meta"]["description"])}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="{c["og_locale"]}">
<meta property="og:image" content="{SITE}/assets/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Ethan Blombou">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/assets/fonts/bricolage.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/instrument-sans.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/style.css">
<script>(function(){{var d=document.documentElement,h=location.hash.slice(1),m=null;d.classList.add('js');try{{m=localStorage.getItem('mode')}}catch(e){{}}if(h==='jeu'||h==='play')m='play';else if(h)m='classic';d.setAttribute('data-mode',m==='classic'?'classic':'play')}})()</script>
<script type="application/ld+json">{jsonld}</script>
</head>
<body>
<a class="skip" href="#main">{ui["skip"]}</a>

<header class="top">
  <nav class="nav" aria-label="{ui["nav_label"]}">
    <a class="nav__brand" href="#home"><span class="nav__mark" aria-hidden="true">EB</span>Ethan Blombou</a>
    <button class="nav__toggle" type="button" aria-expanded="false" aria-controls="nav-links">
      <span class="nav__toggle-bars" aria-hidden="true"></span><span>{ui["menu"]}</span>
    </button>
    <ul class="nav__links" id="nav-links">{nav_links}</ul>
    {lang_switch}
  </nav>
  <div class="progress" aria-hidden="true"><span></span></div>
</header>

<main id="main">

  <section class="play" id="play" aria-label="{escape(pl["label"])}">
    <div class="wrap">

      <div class="scene scene--talk" data-scene="talk">
        <div class="talk">
          <div class="talk__text">
            <p class="talk__top">
              <span class="badge"><span class="badge__dot" aria-hidden="true"></span>{h["badge"]}</span>
              <button class="talk__classic" type="button" data-mode-set="classic"><span>{pl["skip"]}</span> {pl["to_classic"]}{ARROW}</button>
            </p>
            <div class="talk__id">
              <img class="talk__face" src="/assets/ethan-400.webp" alt="" width="400" height="542" decoding="async">
              <h2 class="hero__name talk__name" aria-label="Ethan Blombou">{name_lines}</h2>
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
          <button class="btn btn--line" type="button" data-scene-go="talk">← {pl["map"]["back"]}</button>
          <h2 class="mapbar__t" id="map-title" tabindex="-1">{pl["map"]["title"]}</h2>
          <p class="mapbar__hint">{pl["map"]["hint"]}</p>
          <button class="talk__classic" type="button" data-mode-set="classic">{pl["to_classic"]}{ARROW}</button>
        </div>
        <div class="map">
          <div class="map__board pcard">
            <svg id="map" viewBox="0 -44 800 534" role="group" aria-label="{escape(pl["map"]["label"])}">
              <path class="road" id="road" d=""/>
              <path class="road road--done" id="road-done" d=""/>
              <g id="stops"></g>
              <g id="mini" aria-hidden="true">
                <ellipse cx="0" cy="0" rx="13" ry="4" fill="rgba(28,21,18,0.25)"/>
                <g>
                  <rect x="-7.500" y="-11" width="6" height="10" rx="2" fill="#1c1512"/>
                  <rect x="1.500" y="-11" width="6" height="10" rx="2" fill="#1c1512"/>
                  <rect x="-11.500" y="-30" width="23" height="21" rx="7" fill="#efe1c8" stroke="#1c1512" stroke-width="2.500"/>
                  <circle cx="0" cy="-40" r="10.500" fill="#c08a5f" stroke="#1c1512" stroke-width="2.500"/>
                  <g fill="#1c1512"><circle cx="-8.500" cy="-46" r="5"/><circle cx="-3.500" cy="-50.500" r="5.500"/><circle cx="3.500" cy="-50.500" r="5.500"/><circle cx="8.500" cy="-46" r="5"/><circle cx="0" cy="-47.500" r="6"/><circle cx="-10.500" cy="-41.500" r="3.200"/><circle cx="10.500" cy="-41.500" r="3.200"/></g>
                  <circle cx="-3.700" cy="-38.500" r="1.400" fill="#1c1512"/><circle cx="3.700" cy="-38.500" r="1.400" fill="#1c1512"/>
                  <path d="M-3.200 -34.300q3.200 2.600 6.400 0" fill="none" stroke="#1c1512" stroke-width="1.600" stroke-linecap="round"/>
                </g>
              </g>
            </svg>
            <p class="map__hud" id="map-hud" aria-live="polite"></p>
          </div>
          <div class="map__side">
            <div class="bag pcard"><span class="bag__t">{pl["map"]["bag"]}</span><span class="bag__items" id="bag"></span></div>
            <article class="map__panel pcard" id="map-panel" aria-live="polite">
              <p class="map__tag" id="p-tag"></p>
              <h3 id="p-title"></h3>
              <p class="map__what" id="p-what"></p>
              <div class="map__shots" id="p-shots"></div>
              <p class="bubble" id="p-say"></p>
              <p class="map__more" id="p-more"></p>
            </article>
            <div class="map__ctrl">
              <button class="btn btn--line" id="map-prev" type="button" aria-label="{escape(pl["map"]["prev"])}">←</button>
              <button class="btn btn--dark" id="map-next" type="button">{pl["map"]["next"]} →</button>
            </div>
          </div>
        </div>
      </div>

    </div>
    <script type="application/json" id="play-data">{play_data}</script>
  </section>

  <section class="hero" id="home">
    <div class="wrap hero__grid">
      <div class="hero__text">
        <div class="hello">
          <p class="badge"><span class="badge__dot" aria-hidden="true"></span>{h["badge"]}</p>
          <p class="bubble bubble--hello">{ui["hello"]}</p>
        </div>
        <h1 class="hero__name" aria-label="Ethan Blombou">{name_lines}</h1>
        <p class="hero__statement">{h["statement"]}</p>
        <p class="hero__lead">{h["lead"]}</p>
        <p class="hero__cta">
          <button class="btn btn--play" type="button" data-mode-set="play">{PLAY}{pl["hero_play"]}</button>
          <a class="btn btn--dark" href="#projects">{h["cta_projects"]}{ARROW}</a>
          <a class="btn btn--line" href="#contact">{h["cta_contact"]}</a>
          <a class="cv" href="{CV}" download>{DOWN}<span>{ui["cv"]}</span><small>{ui["cv_note"]}</small></a>
        </p>
      </div>
      {portrait("hero")}
    </div>
  </section>

  <div class="band" role="img" aria-label="{escape(ui["route_label"])}">
    <div class="band__track" aria-hidden="true"><ol>{route}</ol><ol>{route}</ol><ol>{route}</ol><ol>{route}</ol></div>
  </div>

  <section class="section" id="about" aria-labelledby="about-title">
    <div class="wrap">
      {shead(c, "01", a["eyebrow"], a["title"], "about-title")}
      <div class="about">
        <div class="about__main">
          <div class="prose reveal">{paragraphs}</div>
          <blockquote class="bubble bubble--quote reveal"><p>{quote}</p></blockquote>
        </div>
        <div class="about__side">
          <div class="reveal">{photo("presentation", (560, 1000), 1000, 918, a["photo"], "(min-width: 900px) 520px, 100vw", "shot shot--about")}</div>
        </div>
      </div>
      <dl class="facts reveal">{facts}</dl>
      <ul class="stats" aria-label="{escape(ui["stats_label"])}">{stats}</ul>
    </div>
  </section>

  <section class="section" id="experience" aria-labelledby="experience-title">
    <div class="wrap">
      {shead(c, "02", x["eyebrow"], x["title"], "experience-title")}
      <p class="intro intro--lead reveal">{x["intro"]}</p>
      <div class="path">
        <div class="path__line" aria-hidden="true"><span></span></div>
        <ol class="hops">{xp}
        </ol>
      </div>
      <div class="creds">
        <div>
          <h3 class="subtitle reveal">{x["edu_title"]}</h3>
          <ul class="rows">{edu}
          </ul>
        </div>
        <div>
          <h3 class="subtitle reveal">{ui["certs"]}</h3>
          <ul class="rows">{certs}
          </ul>
        </div>
      </div>
    </div>
  </section>

  <section class="section" id="projects" aria-labelledby="projects-title">
    <div class="wrap">
      {shead(c, "03", pr["eyebrow"], pr["title"], "projects-title")}
      <p class="intro reveal">{pr["intro"]}</p>
      {featured}
      <div class="projects">{cards}
      </div>
      <h3 class="subtitle reveal">{pr["more_title"]}</h3>
      <ul class="more">{more}</ul>
    </div>
  </section>

  <section class="section" id="skills" aria-labelledby="skills-title">
    <div class="wrap">
      {shead(c, "04", sk["eyebrow"], sk["title"], "skills-title")}
      <div class="filters reveal" role="group" aria-label="{escape(ui["filter"])}">{filters}</div>
      <div class="groups">{groups}</div>
    </div>
  </section>

  <section class="section" id="life" aria-labelledby="life-title">
    <div class="wrap">
      {shead(c, "05", lf["eyebrow"], lf["title"], "life-title")}
      <div class="planche">
        <article class="case case--piano reveal">
          <div class="case__head">
            <h3 class="case__name">{pn["name"]}</h3>
            <p class="case__text">{pn["text"]}</p>
          </div>
          <div class="piano" role="group" aria-label="{escape(pn["label"])}">{keys}</div>
          <p class="piano__more"><button type="button" class="demo" data-demo aria-pressed="false">{PLAY}<span>{pn["demo"]}</span><small>{pn["demo_note"]}</small></button></p>
        </article>{cases}
      </div>
    </div>
  </section>

  <section class="section section--dark" id="contact" aria-labelledby="contact-title">
    <div class="wrap contact">
      {shead(c, "06", ct["eyebrow"], ct["title"], "contact-title")}
      <p class="contact__text reveal">{ct["text"]}</p>
      <div class="contact__mail reveal">
        <a class="mail" href="mailto:{EMAIL}"><span class="sr-only">{ct["email_label"]} : </span>{EMAIL}</a>
        <button class="copy" type="button" data-copy="{EMAIL}" data-done="{ui["copied"]}">{ui["copy"]}</button>
        <span class="copy__status" role="status" aria-live="polite"></span>
      </div>
      <ul class="contact__links reveal">
        <li><a class="link link--cv" href="{CV}" download>{ui["cv"]}<span class="link__handle">{ui["cv_note"]}</span>{DOWN}</a></li>
        <li><a class="link" href="{LINKEDIN}" rel="noopener me">{ct["linkedin"]}<span class="link__handle">in/ethan-blombou</span>{ARROW}</a></li>
        <li><a class="link" href="{GITHUB}" rel="noopener me">{ct["github"]}<span class="link__handle">BuildRunnerFr</span>{ARROW}</a></li>
      </ul>
    </div>
    <div class="wrap"><p class="next reveal"><span>{ui["next"]}</span></p></div>
    <p class="signoff" aria-hidden="true">Ethan Blombou</p>
  </section>

</main>

<footer class="footer">
  <div class="wrap footer__in">
    <p>© 2026 Ethan Blombou</p>
    <p>{c["footer"]["note"]}</p>
    <p><a href="#home">{ui["top"]} ↑</a></p>
  </div>
</footer>

<script src="/assets/js/main.js" defer></script>
<script src="/assets/js/play.js" defer></script>
</body>
</html>
"""


def render_404(c):
    ui = c["ui"]
    return f"""<!doctype html>
<html lang="{c["lang"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>404 · Ethan Blombou</title>
<meta name="robots" content="noindex">
<meta name="theme-color" content="#b8401f">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/css/style.css">
</head>
<body class="nf">
<main class="nf__in">
  <p class="nf__code" aria-hidden="true">404</p>
  <h1 class="nf__title">{ui["nf_title"]}</h1>
  <p class="nf__text">{ui["nf_text"]}</p>
  <p><a class="btn btn--dark" href="/">{ui["nf_back"]}{ARROW}</a></p>
</main>
</body>
</html>
"""


def main():
    for lang, out in (("fr", "index.html"), ("en", "en/index.html")):
        content = json.loads((ROOT / "content" / f"{lang}.json").read_text(encoding="utf-8"))
        if lang == "fr":
            content = walk(content, nbsp_fr)
        target = ROOT / out
        target.parent.mkdir(exist_ok=True)
        target.write_text(render(content), encoding="utf-8")
        print("écrit", out)
        if lang == "fr":
            (ROOT / "404.html").write_text(render_404(content), encoding="utf-8")
            print("écrit 404.html")


if __name__ == "__main__":
    main()
