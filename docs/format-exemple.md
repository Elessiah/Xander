# Format des fichiers d'exemple

Un fichier d'exemple décrit **une partie réelle**, appel par appel. C'est un
script Python valide (on peut le lancer tel quel) découpé en sections par des
commentaires placés en début de ligne.

```python
# include
from Games.Morpion import Morpion

# init
game = Morpion()  # game
board = game.init("X")  # array 9

# back
board = game.back()  # array 9

# player X
board = game.get_game_state()  # array 9
board = game.play(4)  # array 9

# player O
board = game.get_game_state()  # array 9
board = game.play(5)  # array 9

# end player X
```

## Sections

| En-tête | Rôle |
|---|---|
| `# include` | imports nécessaires ; recopiés tels quels dans le script de rejeu |
| `# init` | création et initialisation de la partie |
| `# back` | la fonction qui annule le dernier coup. Elle n'est **pas** jouée pendant le rejeu : la mère la garde pour corriger ses enfants plus tard |
| `# player <nom>` | les appels faits par le joueur `<nom>` pendant **un** tour. On répète l'en-tête à chaque tour |
| `# end player <nom>` | fin de partie, `<nom>` a gagné. `# end draw` pour un match nul |

Les en-têtes doivent avoir exactement ces formes ; la casse et les espaces en
trop ne comptent pas (`#Player   X` est accepté). `# end d` et `# end nul`
valent aussi `# end draw`.

Toute autre ligne qui commence par `#` est un commentaire libre, ignoré, **à
condition de ne pas commencer par un mot-clé de section**. `# player O (2e
tour)` ou `# end of setup` provoquent une erreur « en-tête mal formé » avec
le numéro de ligne : les ignorer attribuerait les coups au mauvais joueur sans
prévenir. Écrivez plutôt `# 2e tour de O` ou `# fin de la mise en place`.

## Lignes de code

Chaque ligne hors `# include` est **un seul appel de fonction**, avec ou sans
variable qui reçoit le résultat :

```python
game.set_max_nb_allumettes(10)   # pas de valeur de retour : pas de type
nb = game.play(3)  # integer     # valeur de retour : type obligatoire
board = game.get_board()  # array 200
```

Le commentaire de fin de ligne donne le **type** de la valeur renvoyée et,
pour un tableau, sa **taille** : `# <type> [taille]`.

| Type | Pour |
|---|---|
| `game` | l'objet du jeu lui-même (jamais observé pendant le rejeu) |
| `array` | une liste, typiquement le plateau |
| `integer` | un nombre |
| `bool` | un booléen (`True` à la fin de partie, par exemple) |
| `string` | une chaîne |
| `back` | réservé |

Pas encore géré : les arguments nommés (`Jumper(seed=0)` → écrire
`Jumper(0)`), les appels imbriqués (`f(g(x))`, `f([g(x)])`) et les affectations multiples.
Une erreur indique alors le numéro de ligne fautif.

## Le temps

Chaque appel reçoit un horodatage `time` qui donne l'ordre chronologique de la
partie : `0, 1, …` pour les appels de `# init`, puis les appels des joueurs
dans l'ordre du fichier. C'est cet ordre qui est rejoué, et c'est lui qui
permet de comparer une variable « avant » et « après » un coup.

## Conseils

- Rendez l'exemple **déterministe** : premier joueur imposé (`init("X")`
  plutôt que tirage au sort), graine fixée pour les jeux aléatoires
  (`Jumper(0)`). Sinon le rejeu ne correspond plus à ce qui est écrit.
- Faites relire l'état (`get_game_state`) au début de chaque tour : c'est ce
  qui permet à la mère de voir l'effet du coup précédent.
- Plusieurs parties ou des coups variés donnent une analyse plus fiable : une
  fonction n'est retenue que si son effet est observé sur au moins la moitié
  de ses appels.

Exemples fournis : [`res/exampleMorpion.py`](../res/exampleMorpion.py),
[`res/exampleAllumettes.py`](../res/exampleAllumettes.py),
[`res/exampleJumper.py`](../res/exampleJumper.py).
