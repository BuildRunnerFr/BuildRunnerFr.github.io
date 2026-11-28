#!/usr/bin/env python3
"""Fabrique les versions « fond sombre » des logos : assets/logos/<nom>-dark.<ext>.

Seuls les textes noirs ou gris foncé passent en clair ; les couleurs de marque ne bougent pas.
Exceptions : le bordeaux des lignes de campus de l'IUT et le violet de l'UMT, trop sombres, sont éclaircis.
Les logos déjà lisibles sur fond sombre (Free, SEATRU) n'ont pas de version « -dark ».
Il faut Pillow pour les logos en image : python3 tools/dark_logos.py
"""
import colorsys
import re
from pathlib import Path

from PIL import Image

LOGOS = Path(__file__).resolve().parent.parent / "assets" / "logos"
LIGHT = (238, 240, 247)  # la couleur --ink du thème sombre

# logos vectoriels : (motif, remplacement), une seule fois chacun
SVG = {
    "societe-generale": [(r"<g>", '<g fill="#fff">')],
    "imt-atlantique": [(r'<svg version="1.1"', '<svg version="1.1" fill="#fff"')],
    "deloitte": [(r"fill:#0f0b0b", "fill:#ffffff")],
    "google-cloud": [(r'fill="#212226"', 'fill="#ffffff"')],
    "meta": [(r"fill:#192830", "fill:#ffffff")],
}


def svg(stem, rules):
    text = (LOGOS / f"{stem}.svg").read_text(encoding="utf-8")
    for pattern, new in rules:
        many = stem == "deloitte"
        text, n = re.subn(pattern, new, text, count=0 if many else 1)
        assert n, f"{stem} : « {pattern} » introuvable"
    (LOGOS / f"{stem}-dark.svg").write_text(text, encoding="utf-8")


def raster(stem, recolor):
    src = Image.open(LOGOS / f"{stem}.png").convert("RGBA")
    w, h = src.size
    px = src.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (*recolor(r, g, b, x / w), a)
    src.save(LOGOS / f"{stem}-dark.png", optimize=True)
    small = Image.open(LOGOS / f"{stem}.webp").size
    src.resize(small, Image.LANCZOS).save(LOGOS / f"{stem}-dark.webp", lossless=True, method=6)


def all_light(r, g, b, x):
    return LIGHT


def iut(r, g, b, x):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if s < 0.2 and v < 0.8:      # « UVSQ » et « IUT de Vélizy-Rambouillet », en gris
        return LIGHT
    if x > 0.42 and s >= 0.2 and (h > 0.85 or h < 0.05):   # les deux lignes de campus, en bordeaux
        return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, 0.5, 0.95))
    return (r, g, b)


def umt(r, g, b, x):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if 0.66 < h < 0.82 and s >= 0.3 and v < 0.7:   # le violet du sigle et du toit
        return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, 0.42, 0.92))
    return (r, g, b)


if __name__ == "__main__":
    for stem, rules in SVG.items():
        svg(stem, rules)
    raster("tu-sofia", all_light)
    raster("iut-velizy", iut)
    raster("umt", umt)
    print("versions sombres :", ", ".join(sorted(p.name for p in LOGOS.glob("*-dark.*"))))
