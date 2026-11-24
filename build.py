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


def shead(n, kicker, title, id_):
    return (
        f'<header class="shead"><p class="shead__k"><span class="shead__n">{n}</span>{kicker}</p>'
        f'<h2 class="shead__t reveal" id="{id_}">{title}</h2></header>'
    )


def render(c):
    lang = c["lang"]
    url = SITE + c["path"]
    ui = c["ui"]
    h, a, x, pr, sk, ct = c["hero"], c["about"], c["experience"], c["projects"], c["skills"], c["contact"]

    nav_links = "".join(
        f'<li><a href="#{s}" data-nav="{s}">{c["nav"][s]}</a></li>' for s in SECTIONS[1:]
    )
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

    fiche = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in h["fiche"])
    route = "".join(
        f'<li class="route__node{" is-target" if i >= 2 else ""}"><span class="route__dot" aria-hidden="true"></span>{name}</li>'
        for i, name in enumerate(ui["route"])
    )

    facts = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in a["facts"][3:])

    xp = ""
    for i, it in enumerate(x["items"], 1):
        logos = logo(it["logo"], it["org"])
        if it.get("logo2"):
            logos += logo(it["logo2"], it["org2"])
        bullets = "".join(f"<li>{b}</li>" for b in it["bullets"])
        xp += f"""
          <li class="hop reveal">
            <p class="hop__n" aria-hidden="true">{i:02d}</p>
            <p class="hop__dates">{it["dates"]}</p>
            <div class="hop__body">
              <div class="hop__logos">{logos}</div>
              <h3 class="hop__role">{it["role"]}</h3>
              <p class="hop__org">{it["org"]}</p>
              <ul class="hop__list">{bullets}</ul>
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
        if p.get("image"):
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
<meta name="theme-color" content="#f3f2ed">
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
<script>document.documentElement.classList.add('js')</script>
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
</header>

<main id="main">

  <section class="hero" id="home">
    <div class="wrap">
      <div class="hero__top">
        <p class="badge"><span class="badge__dot" aria-hidden="true"></span>{h["badge"]}</p>
        <p class="hero__coords" aria-hidden="true">48.86°N 2.35°E <span>⇄</span> 48.39°N 4.49°W</p>
      </div>
      <h1 class="hero__name"><span class="line"><span>Ethan</span></span> <span class="line"><span>Blombou</span></span></h1>
      <div class="hero__grid">
        <figure class="portrait">
          <picture>
            <source type="image/webp" srcset="/assets/ethan-400.webp 400w, /assets/ethan-640.webp 640w" sizes="200px">
            <img src="/assets/ethan.jpg" alt="{escape(h["photo_alt"])}" width="890" height="1205" fetchpriority="high" decoding="async">
          </picture>
        </figure>
        <div class="hero__pitch">
          <p class="hero__statement">{h["statement"]}</p>
          <p class="hero__lead">{h["lead"]}</p>
          <p class="hero__cta">
            <a class="btn btn--solid" href="#projects">{h["cta_projects"]}{ARROW}</a>
            <a class="btn btn--line" href="#contact">{h["cta_contact"]}</a>
          </p>
        </div>
        <dl class="fiche">{fiche}</dl>
      </div>
      <div class="route" role="img" aria-label="{escape(ui["route_label"])}">
        <div class="route__track" aria-hidden="true"><span class="route__packet"></span></div>
        <ol class="route__nodes" aria-hidden="true">{route}</ol>
      </div>
    </div>
  </section>

  <section class="section" id="about" aria-labelledby="about-title">
    <div class="wrap">
      {shead("01", a["eyebrow"], a["title"], "about-title")}
      <div class="about">
        <div class="prose reveal">{paragraphs}</div>
        <dl class="facts reveal">{facts}</dl>
      </div>
    </div>
  </section>

  <section class="section" id="experience" aria-labelledby="experience-title">
    <div class="wrap">
      {shead("02", x["eyebrow"], x["title"], "experience-title")}
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
      {shead("03", pr["eyebrow"], pr["title"], "projects-title")}
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
      {shead("04", sk["eyebrow"], sk["title"], "skills-title")}
      <div class="filters reveal" role="group" aria-label="{escape(ui["filter"])}">{filters}</div>
      <div class="groups">{groups}</div>
    </div>
  </section>

  <section class="section section--dark" id="contact" aria-labelledby="contact-title">
    <div class="wrap contact">
      {shead("05", ct["eyebrow"], ct["title"], "contact-title")}
      <p class="contact__text reveal">{ct["text"]}</p>
      <div class="contact__mail reveal">
        <a class="mail" href="mailto:{EMAIL}"><span class="sr-only">{ct["email_label"]} : </span>{EMAIL}</a>
        <button class="copy" type="button" data-copy="{EMAIL}" data-done="{ui["copied"]}">{ui["copy"]}</button>
        <span class="copy__status" role="status" aria-live="polite"></span>
      </div>
      <ul class="contact__links reveal">
        <li><a class="link" href="{LINKEDIN}" rel="noopener me">{ct["linkedin"]}<span class="link__handle">in/ethan-blombou</span>{ARROW}</a></li>
        <li><a class="link" href="{GITHUB}" rel="noopener me">{ct["github"]}<span class="link__handle">BuildRunnerFr</span>{ARROW}</a></li>
      </ul>
    </div>
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
