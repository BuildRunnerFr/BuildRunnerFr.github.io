# buildrunnerfr.github.io

Site personnel d'Ethan Blombou : <https://buildrunnerfr.github.io> (français) et <https://buildrunnerfr.github.io/en/> (anglais).

Site statique sans framework, publié par GitHub Pages depuis la branche `main`.

## Deux versions dans la même page

- **Version jeu** (par défaut) : une discussion à choix avec Ethan, puis une carte de son parcours à explorer. Répliques et étapes sont dans la clé `play` de `content/fr.json` et `content/en.json` ; le code est dans `assets/js/play.js`.
- **Version classique** : le site à faire défiler. On y passe par le bouton du menu, par les liens du menu, ou en arrivant sur une section (`/#projects`). Sans JavaScript, c'est elle qui s'affiche.

Le choix du visiteur est gardé dans son navigateur. `/#jeu` force la version jeu.

## Modifier le contenu

Les textes sont dans `content/fr.json` et `content/en.json`. Les pages `index.html` et `en/index.html` sont générées :

```bash
python3 build.py
```

Aucune dépendance : Python 3 standard. Pour prévisualiser :

```bash
python3 -m http.server 4173
```

## Mettre à jour les chiffres GitHub

La section « En chiffres » lit `content/github.json`, un relevé daté. Pour le refaire (il faut l'outil `gh`, connecté au compte) :

```bash
python3 tools/github_stats.py && python3 build.py
```

## Ajouter une photo à une expérience

1. Déposer la photo en deux largeurs dans `assets/photos/`, recadrée en portrait 4:5 : `nom-480.webp` et `nom-960.webp`.
2. Dans `content/fr.json` et `content/en.json`, ajouter à l'expérience concernée :
   `"photos": [{"stem": "nom", "sizes": [480, 960], "w": 960, "h": 1200, "alt": "ce que montre la photo", "caption": "légende courte"}]`
   Les photos d'une expérience apparaissent aussi à son étape sur la carte de la version jeu.
3. Relancer `python3 build.py`.

## Organisation

- `build.py` : gabarit HTML et génération des deux pages
- `content/` : textes français et anglais
- `assets/css/style.css`, `assets/js/main.js` : styles et interactions (dont le clavier de piano de la section « À côté », synthétisé dans le navigateur, sans fichier son)
- `assets/photos/` : photos en WebP, deux largeurs par image
- `assets/logos/` : logos des organisations, fichiers d'origine non modifiés (seuls les PNG ont été réduits en taille)
- `assets/icons/` : icônes des technologies, issues de Simple Icons
- `assets/fonts/` : Bricolage Grotesque et Instrument Sans (licence OFL)

Les logos et marques appartiennent à leurs détenteurs respectifs.
