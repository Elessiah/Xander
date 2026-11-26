# Xander

Xander est une tentative d'IA de jeu **sans réseau de neurones**. Une
*logique mère* lit un exemple de partie écrit en Python, en déduit à quoi sert
chaque fonction du jeu (lire l'état, jouer un coup, annuler…), puis, à terme,
crée des *enfants* qui jouent seuls et qu'elle corrige.

> **État : prototype.** La mère sait lire un exemple, le rejouer, déduire le
> rôle des fonctions, puis élever un fils qui part de zéro en corrigeant chacune
> de ses erreurs. Au Morpion, le fils devient imbattable. Les autres jeux
> attendent un Analyzer plus général (voir [la feuille de route](docs/feuille-de-route.md)).

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
  game.play : board : changees = case(arg0), board : changees = valant(arg0)
Appels non compris :
  t=11  board = game.play(7)                [INOUT]
```

La mère a construit elle-même la description de `play(n)` : seule la case
d'indice `n` change (ou, ce qui revient au même ici, la case qui contient `"n"`). Le dernier coup
n'est « pas compris » parce qu'il renvoie `True` (fin de partie) au lieu du
plateau : il n'y a pas d'état « après » à comparer.

Options : `-v` (détail de l'analyse), `--keep` (garde le script de rejeu dans
`output/poolTest.py`).

### Élever un fils

```powershell
python -m xander res/exampleMorpion.py --prof Games.MinmaxMorpion:minmax_morpion_play --son morpion
```

Le fils naît sans rien savoir, et la mère sans aucun concept. Elle lui montre
l'exemple, le fait jouer contre le professeur (le Minmax), contre un joueur au
hasard et contre un adversaire mixte, puis revient sur chacune de ses erreurs.
Elle corrige d'abord **cas par cas** (un souvenir par erreur), puis
**refactorise** : le plus petit concept qui explique au moins deux souvenirs,
construit avec ses briques, devient une règle si tous les cas déjà vus restent
bien joués. Les souvenirs restants sont réduits à ce qui comptait, puis
reconnus partout : ce sont des **petits motifs** (`MM.??????` → 2), vérifiés
dans le labo. Chaque partie est affichée avec ses leçons et ses refactors (`-q`
pour ne voir que le bilan), suivie de la courbe d'apprentissage et des
concepts construits :

```text
partie   3 | fils X contre hasard     : victoire | 1 erreur(s)
      ...A.MM.A : le fils a joué 0 (défaut), le professeur 3 -> souvenir ; nouveau souvenir
      refactor : 2 souvenirs -> concept_2 (nouvelle règle « jouer un coup après lequel
                 j'ai gagné ou aucun de ses coups ne donne « il a gagné » ») ; ...
      refactor : concept_1 retirée (inutile) ; règles : concept_3 > concept_4
...
Concepts construits par la mère (une règle : jouer un coup après lequel…) :
  concept_6   [règle] j'ai gagné
                      gagne(moi)
  ...
```

`--parties N` (200 par défaut), `--son NOM` écrit le fils dans
`output/sons/NOM.py` : un fichier Python autonome, écrit par la mère, qui ne
contient que les règles qu'elle lui a apprises. Pour jouer contre lui :

```powershell
python -m Games.GamePlayer morpion --x humain --o xander
```

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

La CI est locale ([`ci.py`](ci.py)) : chaque classe de tests et l'apprentissage
de chaque exemple de `res/` tournent en parallèle, dans des processus séparés
(environ 40 s).

```powershell
python ci.py
```

Les tests lents (marqués `@lent` : l'éducation complète du Morpion à trois,
l'examen blanc de bout en bout en sous-processus) ne tournent qu'avec
`--complet` (environ 5 min). Un filtre ne lance que les tâches dont le nom le
contient (`python ci.py morpion3`).

```powershell
python ci.py --complet
```

## Organisation

| Dossier | Contenu |
|---|---|
| `xander/` | la logique mère : lecture de l'exemple, rejeu, analyse, laboratoire, éducation du fils, le fils |
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

## Licence

Xander est un projet de recherche publié sous la
[PolyForm Noncommercial License 1.0.0](LICENSE.md) :

- le code est libre d'accès, d'étude, de modification et de redistribution ;
- l'usage est réservé aux fins **non commerciales** (recherche, étude,
  enseignement, loisir, organismes à but non lucratif…) ;
- toute copie ou œuvre dérivée doit conserver la licence et la mention
  `Required Notice:` qui crédite l'auteur.

Copyright (c) 2024-2026 Elessiah et les contributeurs de Xander. Pour un usage
commercial, contacter l'auteur.
