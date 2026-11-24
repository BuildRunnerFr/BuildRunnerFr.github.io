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
SECTIONS = ["home", "about", "experience", "projects", "skills", "contact"]


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


ARROW = '<svg class="arrow" viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><path d="M4 10h11M10.5 5l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
SQUIGGLE = '<svg class="eyebrow__mark" viewBox="0 0 44 12" width="44" height="12" aria-hidden="true"><path d="M2 7c5-6 8-6 12 0s8 6 12 0 8-5 16-1" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'


def wave(cls):
    return (
        f'<svg class="wave {cls}" viewBox="0 0 1440 90" preserveAspectRatio="none" aria-hidden="true">'
        '<path d="M0 52c120-34 260-44 420-24s250 52 430 44 250-58 400-56 150 22 190 34v40H0z"/></svg>'
    )


def eyebrow(text):
    return f'<p class="eyebrow">{SQUIGGLE}<span>{text}</span></p>'


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


def render(c):
    lang = c["lang"]
    other = "en" if lang == "fr" else "fr"
    url = SITE + c["path"]
    h, a, x, pr, sk, ct = c["hero"], c["about"], c["experience"], c["projects"], c["skills"], c["contact"]

    nav_links = "".join(
        f'<li><a href="#{s}" data-nav="{s}">{c["nav"][s]}</a></li>' for s in SECTIONS[1:]
    )

    lang_switch = (
        f'<div class="lang" role="group" aria-label="{c["ui"]["lang_label"]}">'
        + "".join(
            f'<a href="{c["path"] if l == lang else c["other_path"]}" lang="{l}" hreflang="{l}" data-lang-link'
            + (' aria-current="true"' if l == lang else "")
            + f'><span aria-hidden="true">{l.upper()}</span><span class="sr-only">{"Français" if l == "fr" else "English"}</span></a>'
            for l in ("fr", "en")
        )
        + "</div>"
    )

    facts = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in a["facts"])

    xp = ""
    for i, it in enumerate(x["items"]):
        logos = logo(it["logo"], it["org"])
        if it.get("logo2"):
            logos += logo(it["logo2"], it["org2"])
        bullets = "".join(f"<li>{b}</li>" for b in it["bullets"])
        xp += f"""
          <li class="step reveal">
            <span class="step__dot" aria-hidden="true"></span>
            <div class="step__logos">{logos}</div>
            <h3 class="step__role">{it["role"]}</h3>
            <p class="step__meta"><span class="step__org">{it["org"]}</span><span class="step__dates">{it["dates"]}</span></p>
            <ul class="step__list">{bullets}</ul>
          </li>"""

    edu = ""
    for it in x["edu"]:
        edu += f"""
          <li class="edu reveal">
            <div class="edu__logo">{logo(it["logo"], it["org"])}</div>
            <div>
              <h4 class="edu__org">{it["org"]}</h4>
              <p class="edu__what">{it["what"]}</p>
              <p class="edu__dates">{it["dates"]}</p>
            </div>
          </li>"""

    f = pr["featured"]
    featured = f"""
        <article class="project project--featured reveal">
          <div class="project__media">
            <img src="{f["image"]}" alt="{escape(f["image_alt"])}" width="{f["image_w"]}" height="{f["image_h"]}" loading="lazy" decoding="async">
          </div>
          <div class="project__body">
            <p class="project__context">{kind_badge(c, f["kind"])}<span>{f["context"]}</span></p>
            {project_logos(c, f["logos"])}
            <h3 class="project__name">{f["name"]}</h3>
            <p class="project__tagline">{f["tagline"]}</p>
            <p>{f["desc"]}</p>
            {part_block(c, f.get("part"))}
            {tags(f["tags"])}
            <p class="project__links">{code_link(c, f)}</p>
          </div>
        </article>"""

    cards = ""
    for p in pr["items"]:
        media = ""
        if p.get("image"):
            media = (
                f'<div class="project__media"><img src="{p["image"]}" alt="{escape(p["image_alt"])}" '
                f'width="{p["image_w"]}" height="{p["image_h"]}" loading="lazy" decoding="async"></div>'
            )
        cards += f"""
        <article class="project reveal">
          {media}
          <div class="project__body">
            <p class="project__context">{kind_badge(c, p["kind"])}<span>{p["context"]}</span></p>
            {project_logos(c, p["logos"])}
            <h3 class="project__name">{p["name"]}</h3>
            <p class="project__tagline">{p["tagline"]}</p>
            <p>{p["desc"]}</p>
            {part_block(c, p.get("part"))}
            {tags(p["tags"])}
            <p class="project__links">{code_link(c, p)}</p>
          </div>
        </article>"""

    more = "".join(
        f'<li class="reveal"><span class="more__name">{n}</span><span class="more__stack">{s}</span></li>'
        for n, s in pr["more"]
    )

    groups = ""
    for g in sk["groups"]:
        chips = "".join(f'<li class="chip">{icon(slug)}<span>{escape(name)}</span></li>' for name, slug in g["items"])
        note = f' <span class="group__note">{g["note"]}</span>' if g.get("note") else ""
        groups += f'<div class="group reveal"><h3 class="group__name">{g["name"]}{note}</h3><ul class="chips">{chips}</ul></div>'
    langs = "".join(
        f'<li class="chip"><span>{n}</span><span class="chip__level">{lv}</span></li>' for n, lv in sk["languages"]
    )
    groups += f'<div class="group reveal"><h3 class="group__name">{sk["languages_title"]}</h3><ul class="chips">{langs}</ul></div>'

    paragraphs = "".join(f"<p>{p}</p>" for p in a["paragraphs"])

    jsonld = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": "Ethan Blombou",
            "url": SITE + "/",
            "image": SITE + "/assets/ethan.jpg",
            "email": "mailto:" + EMAIL,
            "jobTitle": c["experience"]["items"][0]["role"],
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
<meta name="theme-color" content="#f5efe3">
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
<link rel="preload" href="/assets/fonts/fraunces.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/instrument-sans.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/style.css">
<script>document.documentElement.classList.add('js')</script>
<script type="application/ld+json">{jsonld}</script>
</head>
<body>
<a class="skip" href="#main">{c["ui"]["skip"]}</a>

<svg width="0" height="0" class="defs" aria-hidden="true" focusable="false">
  <defs>
    <clipPath id="galet" clipPathUnits="objectBoundingBox">
      <path d="M.5.012C.72-.01.93.09.972.31c.04.2-.005.43-.1.57C.76 1.01.53 1.005.34.975.16.945.045.83.02.63-.01.43.03.21.16.1.26.03.38.022.5.012Z"/>
    </clipPath>
  </defs>
</svg>

<header class="top">
  <nav class="nav" aria-label="{c["ui"]["nav_label"]}">
    <a class="nav__brand" href="#home">Ethan Blombou</a>
    <button class="nav__toggle" type="button" aria-expanded="false" aria-controls="nav-links">
      <span class="nav__toggle-bars" aria-hidden="true"></span><span>{c["ui"]["menu"]}</span>
    </button>
    <ul class="nav__links" id="nav-links">{nav_links}</ul>
    {lang_switch}
  </nav>
</header>

<main id="main">

  <section class="hero" id="home">
    <div class="wrap hero__grid">
      <div class="hero__text">
        <p class="badge"><span class="badge__dot" aria-hidden="true"></span>{h["badge"]}</p>
        <h1 class="hero__name">Ethan <span>Blombou</span></h1>
        <p class="hero__statement">{h["statement"]}</p>
        <p class="hero__lead">{h["lead"]}</p>
        <p class="hero__cta">
          <a class="btn btn--solid" href="#projects">{h["cta_projects"]}{ARROW}</a>
          <a class="btn btn--line" href="#contact">{h["cta_contact"]}</a>
        </p>
        <p class="hero__place"><svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><path d="M10 18s5.5-5 5.5-9.3A5.5 5.5 0 0 0 4.500 8.700C4.500 13 10 18 10 18Z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><circle cx="10" cy="8.600" r="1.900" fill="currentColor"/></svg>{h["place"]}</p>
      </div>
      <figure class="portrait">
        <svg class="blob blob--sage" viewBox="0 0 200 200" aria-hidden="true"><path d="M100 8c34-4 70 12 82 46s6 78-18 104-66 38-100 26S10 140 8 104 30 36 58 20c14-8 28-10 42-12Z"/></svg>
        <svg class="blob blob--clay" viewBox="0 0 200 200" aria-hidden="true"><path d="M96 14c36-8 72 16 84 50s-2 76-30 98-70 30-102 12S6 118 14 82s46-60 82-68Z"/></svg>
        <picture class="portrait__photo">
          <source type="image/webp" srcset="/assets/ethan-400.webp 400w, /assets/ethan-640.webp 640w, /assets/ethan-890.webp 890w" sizes="(min-width: 900px) 340px, min(300px, 78vw)">
          <img src="/assets/ethan.jpg" alt="{escape(h["photo_alt"])}" width="890" height="1205" fetchpriority="high" decoding="async">
        </picture>
        <svg class="portrait__thread" viewBox="0 0 240 120" aria-hidden="true"><path pathLength="1" d="M6 92c30-50 62-66 84-44s-8 58-26 40 6-62 52-68 84 14 118 44" fill="none" stroke="currentColor" stroke-width="2.600" stroke-linecap="round"/></svg>
      </figure>
    </div>
    {wave("wave--sand")}
  </section>

  <section class="section section--sand" id="about" aria-labelledby="about-title">
    <div class="wrap about">
      <div class="about__main">
        {eyebrow(a["eyebrow"])}
        <h2 class="title reveal" id="about-title">{a["title"]}</h2>
        <div class="prose reveal">{paragraphs}</div>
      </div>
      <aside class="facts reveal" aria-label="{a["facts_title"]}">
        <h3 class="facts__title">{a["facts_title"]}</h3>
        <dl>{facts}</dl>
      </aside>
    </div>
    {wave("wave--paper")}
  </section>

  <section class="section" id="experience" aria-labelledby="experience-title">
    <div class="wrap">
      {eyebrow(x["eyebrow"])}
      <h2 class="title reveal" id="experience-title">{x["title"]}</h2>
      <div class="path">
        <div class="thread" aria-hidden="true">
          <svg viewBox="0 0 40 1000" preserveAspectRatio="none"><path d="M20 0c14 60-12 110 0 170s14 110 0 170-14 110 0 170 12 110 0 170-12 110 0 170 10 100 0 150" fill="none" stroke="currentColor" stroke-width="2.500" stroke-linecap="round" vector-effect="non-scaling-stroke"/></svg>
        </div>
        <ol class="steps">{xp}
        </ol>
      </div>
      <h3 class="subtitle reveal">{x["edu_title"]}</h3>
      <ul class="edus">{edu}
      </ul>
    </div>
    {wave("wave--sand")}
  </section>

  <section class="section section--sand" id="projects" aria-labelledby="projects-title">
    <div class="wrap">
      {eyebrow(pr["eyebrow"])}
      <h2 class="title reveal" id="projects-title">{pr["title"]}</h2>
      <p class="intro reveal">{pr["intro"]}</p>
      {featured}
      <div class="projects">{cards}
      </div>
      <h3 class="subtitle reveal">{pr["more_title"]}</h3>
      <ul class="more">{more}</ul>
    </div>
    {wave("wave--paper")}
  </section>

  <section class="section" id="skills" aria-labelledby="skills-title">
    <div class="wrap">
      {eyebrow(sk["eyebrow"])}
      <h2 class="title reveal" id="skills-title">{sk["title"]}</h2>
      <div class="groups">{groups}</div>
    </div>
    {wave("wave--forest")}
  </section>

  <section class="section section--forest" id="contact" aria-labelledby="contact-title">
    <svg class="contact__blob" viewBox="0 0 200 200" aria-hidden="true"><path d="M100 8c34-4 70 12 82 46s6 78-18 104-66 38-100 26S10 140 8 104 30 36 58 20c14-8 28-10 42-12Z"/></svg>
    <svg class="contact__pebble" viewBox="0 0 200 200" aria-hidden="true"><path d="M96 14c36-8 72 16 84 50s-2 76-30 98-70 30-102 12S6 118 14 82s46-60 82-68Z"/></svg>
    <div class="wrap contact">
      {eyebrow(ct["eyebrow"])}
      <h2 class="title title--xl reveal" id="contact-title">{ct["title"]}</h2>
      <p class="contact__text reveal">{ct["text"]}</p>
      <div class="contact__mail reveal">
        <a class="mail" href="mailto:{EMAIL}"><span class="sr-only">{ct["email_label"]} : </span>{EMAIL}</a>
        <button class="copy" type="button" data-copy="{EMAIL}" data-done="{c["ui"]["copied"]}">{c["ui"]["copy"]}</button>
        <span class="copy__status" role="status" aria-live="polite"></span>
      </div>
      <ul class="contact__links reveal">
        <li><a class="link link--light" href="{LINKEDIN}" rel="noopener me">{ct["linkedin"]}<span class="link__handle">in/ethan-blombou</span>{ARROW}</a></li>
        <li><a class="link link--light" href="{GITHUB}" rel="noopener me">{ct["github"]}<span class="link__handle">BuildRunnerFr</span>{ARROW}</a></li>
      </ul>
    </div>
  </section>

</main>

<footer class="footer">
  <div class="wrap footer__in">
    <p>© 2026 Ethan Blombou · {c["footer"]["made"]}</p>
    <p>{c["footer"]["note"]}</p>
    <p><a href="#home">{c["ui"]["top"]} ↑</a></p>
  </div>
</footer>

<script src="/assets/js/main.js" defer></script>
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


if __name__ == "__main__":
    main()
