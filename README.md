# buildrunnerfr.github.io

Site personnel d'Ethan Blombou : <https://buildrunnerfr.github.io> (français) et <https://buildrunnerfr.github.io/en/> (anglais).

Site statique sans framework, publié par GitHub Pages depuis la branche `main`.

## Modifier le contenu

Les textes sont dans `content/fr.json` et `content/en.json`. Les pages `index.html` et `en/index.html` sont générées :

```bash
python3 build.py
```

Aucune dépendance : Python 3 standard. Pour prévisualiser :

```bash
python3 -m http.server 4173
```

## Organisation

- `build.py` : gabarit HTML et génération des deux pages
- `content/` : textes français et anglais
- `assets/css/style.css`, `assets/js/main.js` : styles et interactions
- `assets/logos/` : logos des organisations, fichiers d'origine non modifiés (seuls les PNG ont été réduits en taille)
- `assets/icons/` : icônes des technologies, issues de Simple Icons
- `assets/fonts/` : Fraunces, Bricolage Grotesque, Instrument Sans et JetBrains Mono (licence OFL)

Les logos et marques appartiennent à leurs détenteurs respectifs.
