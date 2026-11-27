# buildrunnerfr.github.io

Site personnel d'Ethan Blombou : <https://buildrunnerfr.github.io> (français) et <https://buildrunnerfr.github.io/en/> (anglais).

Site statique sans framework, publié par GitHub Pages depuis la branche `main`.

## Ce que contient le site

- **L'accueil** (`index.html`, `en/index.html`) : à propos, compétences, parcours, projets, chiffres, à côté, contact.
- **Une page par projet** (`projets/<nom>/`, `en/projects/<name>/`) : résumé, ma partie, technologies, langages du dépôt, et le README du dépôt quand il est public.
- **Une version jeu** de l'accueil, discrète : une discussion à choix avec Ethan, puis une carte de son parcours. Elle se lance par « Jouer mon parcours », en bas de la section « À côté », ou par `/#jeu` ; le choix est gardé dans le navigateur. Code dans `assets/js/play.js`, répliques dans la clé `play` des contenus.

## Modifier le contenu

Les textes sont dans `content/fr.json` et `content/en.json` (les projets dans `projects.list`). Tout le reste est généré :

```bash
python3 build.py
```

Aucune dépendance : Python 3 standard. Pour prévisualiser : `python3 -m http.server 4173`.

## Mettre à jour les données GitHub

Les chiffres, les dates et langages des dépôts (`content/github.json`) et les README affichés sur les pages de projet (`content/readmes/`) sont un relevé daté. Pour le refaire (il faut l'outil `gh`, connecté au compte) :

```bash
python3 tools/github_stats.py && python3 build.py
```

## Ajouter une photo à une expérience

1. Déposer la photo en trois largeurs dans `assets/photos/`, recadrée en portrait 4:5 : `nom-320.webp`, `nom-480.webp` et `nom-960.webp` (par exemple `cwebp -q 76 -resize 320 0 photo.jpg -o nom-320.webp`). Le site propose toutes les largeurs trouvées, et chaque écran télécharge la plus petite qui suffit.
2. Dans `content/fr.json` et `content/en.json`, ajouter à l'expérience concernée :
   `"photos": [{"stem": "nom", "w": 960, "h": 1200, "alt": "ce que montre la photo", "caption": "légende courte"}]`
   Les photos d'une expérience apparaissent aussi à son étape sur la carte de la version jeu.
3. Relancer `python3 build.py`.

## Organisation

- `build.py` : gabarits HTML, petit rendu Markdown pour les README, génération de toutes les pages
- `content/` : textes français et anglais
- `assets/css/style.css`, `assets/js/main.js` : styles et interactions (dont le clavier de piano de la section « À côté », synthétisé dans le navigateur, sans fichier son)
- `assets/js/net.js` : le réseau animé de l'en-tête. Un maillage fixe, et le plus court chemin (Dijkstra, l'algorithme d'OSPF) entre le portrait et le curseur, recalculé en direct ; de temps en temps un lien tombe et la route se recalcule. Décoratif : sans lui la page est complète
- `assets/photos/` : photos en WebP, plusieurs largeurs par image (`nom-320.webp`, `nom-480.webp`…). Même principe pour les couvertures de projets : `triad-cockpit.webp` et ses réductions `triad-cockpit-800.webp`, `triad-cockpit-1200.webp`
- `assets/logos/` : logos des organisations, non modifiés. Pour les logos en image, le site sert une copie réduite en WebP sans perte (`.webp`) ; le fichier d'origine reste à côté (`.png`)
- `assets/icons/` : icônes des technologies, issues de Simple Icons
- `assets/fonts/` : Bricolage Grotesque, Instrument Sans et IBM Plex Mono (licence OFL). Bricolage est allégée : seule la largeur normale est gardée, les graisses vont de 400 à 800

Les logos et marques appartiennent à leurs détenteurs respectifs.
