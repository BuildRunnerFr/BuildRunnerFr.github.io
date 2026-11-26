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

## Ajouter une photo à une expérience

1. Déposer la photo en deux largeurs dans `assets/photos/` : `nom-640.webp` et `nom-1200.webp`.
2. Dans `content/fr.json` et `content/en.json`, ajouter à l'expérience concernée :
   `"photos": [{"stem": "nom", "w": 1200, "h": 900, "alt": "ce que montre la photo", "caption": "légende courte"}]`
3. Relancer `python3 build.py`.

## Organisation

- `build.py` : gabarit HTML et génération des deux pages
- `content/` : textes français et anglais
- `assets/css/style.css`, `assets/js/main.js` : styles et interactions (dont le clavier de piano de la section « À côté », synthétisé dans le navigateur, sans fichier son)
- `assets/photos/` : photos en WebP, deux largeurs par image (`nom-640.webp`, `nom-1200.webp`)
- `assets/logos/` : logos des organisations, fichiers d'origine non modifiés (seuls les PNG ont été réduits en taille)
- `assets/icons/` : icônes des technologies, issues de Simple Icons
- `assets/fonts/` : Bricolage Grotesque et Instrument Sans (licence OFL)

Les logos et marques appartiennent à leurs détenteurs respectifs.
