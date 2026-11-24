# Xander

[![Tests](https://github.com/Elessiah/Xander/actions/workflows/tests.yml/badge.svg)](https://github.com/Elessiah/Xander/actions/workflows/tests.yml)

Xander est une tentative d'IA de jeu **sans réseau de neurones**. Une
*logique mère* lit un exemple de partie écrit en Python, en déduit à quoi sert
chaque fonction du jeu (lire l'état, jouer un coup, annuler…), puis, à terme,
crée des *enfants* qui jouent seuls et qu'elle corrige.

> **État : prototype inachevé.** La mère sait lire un exemple, le rejouer et
> déduire le rôle des fonctions. La génération d'enfants qui jouent vraiment, et
> leur correction, restent à écrire (voir [la feuille de route](docs/feuille-de-route.md)).

## Démarrage rapide

Python 3.10 ou plus récent, aucune dépendance. Toutes les commandes se lancent
depuis la racine du dépôt.

```powershell
python -m xander res/exampleMorpion.py
```

```text
Jeu : game
Joueurs (2) : X, O
Actions par tour : 2 (get_game_state -> play)
Annulation : board = game.back()
Gagnant de l'exemple : X
Variables :
  board (array, taille 9) | lue par : get_game_state, init, play | modifiée par : play
Opérations déduites :
  game.play : SINGLE_TARGET_INDEX sur board
Appels non compris :
  t=11  board = game.play(7)                [INOUT]
```

La mère a compris que `play(n)` modifie la case `n` du plateau. Le dernier coup
n'est « pas compris » parce qu'il renvoie `True` (fin de partie) au lieu du
plateau : il n'y a pas d'état « après » à comparer.

Options : `-v` (détail de l'analyse), `--keep` (garde le script de rejeu dans
`output/poolTest.py`), `--son NOM` (écrit le squelette d'un enfant dans
`output/sons/NOM.py`).

### Jouer aux jeux de test

```powershell
python -m Games.GamePlayer morpion --x humain --o minmax
```

```powershell
python -m Games.GamePlayer allumettes --x minmax --o minmax
```

```powershell
python -m Games.GamePlayer puissance4 --x humain --o minmax
```

```powershell
python -m Games.mainJumper
```

### Lancer les tests

```powershell
python -m unittest discover -s tests -t .
```

La CI GitHub Actions ([`.github/workflows/tests.yml`](.github/workflows/tests.yml)) lance ces
tests et l'apprentissage des trois exemples de `res/` sous Linux et Windows,
avec Python 3.10, 3.12 et 3.13, à chaque push sur `main` et sur chaque PR.

## Organisation

| Dossier | Contenu |
|---|---|
| `xander/` | la logique mère : lecture de l'exemple, rejeu, analyse, création d'enfants |
| `Games/` | jeux servant de terrain d'essai (Morpion, Allumettes, Puissance 4, Jumper) et adversaires Minmax codés à la main (un par jeu à deux joueurs) |
| `res/` | exemples de parties que la mère apprend |
| `tests/` | tests unitaires (`unittest`) |
| `docs/` | documentation détaillée |
| `output/` | fichiers générés (ignoré par git) |

## Documentation

- [Format des fichiers d'exemple](docs/format-exemple.md) : comment écrire une partie que la mère peut apprendre.
- [Architecture](docs/architecture.md) : la chaîne d'apprentissage étape par étape et les heuristiques d'analyse.
- [Les jeux](docs/jeux.md) : règles, interface commune et adversaires Minmax.
- [Feuille de route](docs/feuille-de-route.md) : ce qui reste à faire et ce qui a été corrigé.
