# One Piece – posters tvdb4

Télécharge les couvertures **officielles VF** des tomes de One Piece depuis le
[wiki One Piece FR](https://onepiece.fandom.com/fr) (`static.wikia.nocookie.net`)
en **taille originale**, et les enregistre en JPG dans le dossier `posters/` à côté
du script, nommées au format **tvdb4** d'[Absolute Series Scanner](https://github.com/ZeroQI/Absolute-Series-Scanner) :

```
Season1a.jpg   = Tome 1
Season1h.jpg   = Tome 8
Season25a.jpg  = Tome 91
```

## Installation

Python 3.8 ou plus, plus Pillow pour la conversion en JPG :

```bash
pip install pillow
```

Sans Pillow, le script fonctionne quand même mais enregistre les images en PNG.

## Utilisation

Mode interactif (tome de départ, tome d'arrivée, puis « Ajouter une autre plage ? ») :

```bash
python onepiece_posters.py
```

Plusieurs plages directement en argument :

```bash
python onepiece_posters.py 1-10 25-30 91 100-
```

| Syntaxe   | Signification                        |
|-----------|--------------------------------------|
| `1-10`    | tomes 1 à 10                         |
| `91`      | tome 91 seul                         |
| `100-`    | du tome 100 au dernier paru          |
| `tout`    | tous les tomes                       |

Options :

| Option             | Effet                                                          |
|--------------------|----------------------------------------------------------------|
| `-l`, `--lister`   | affiche le découpage tome -> fichier sans rien télécharger     |
| `--vo`             | prend la couverture japonaise si la VF n'est pas encore sortie |
| `-f`, `--ecraser`  | retélécharge les images déjà présentes                         |
| `-d`, `--dossier`  | autre dossier de destination (défaut : `posters/`)             |
| `-q`, `--qualite`  | qualité JPEG, 1 à 100 (défaut : 95)                            |

## Découpage tome -> saison

Les saisons sont celles de One Piece (tvdbid 81797) dans
[`tvdb4.mapping.xml`](https://github.com/ZeroQI/Absolute-Series-Scanner/blob/master/tvdb4.mapping.xml).
Pour chaque arc, le script connaît le premier chapitre du manga qu'il couvre
(table `SAISONS` en haut du script) et lit sur le wiki les chapitres de chaque tome :

- **saison** : l'arc qui contient la majorité des chapitres du tome ;
- **lettre** : le rang du tome dans cette saison (`a`, `b`, `c`, … `z`, `aa`…).

La saison 9 (G8) est un arc hors-série de l'anime : elle n'a aucun tome.
Pour déplacer un tome à la main, utilisez `FORCER_SAISON`, par exemple
`FORCER_SAISON = {90: 25}`. `python onepiece_posters.py tout --lister`
affiche le découpage complet.
