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
[`res/examplePuissance4.py`](../res/examplePuissance4.py),
[`res/examplePylos.py`](../res/examplePylos.py),
[`res/exampleJumper.py`](../res/exampleJumper.py),
[`res/exampleNim.py`](../res/exampleNim.py),
[`res/exampleNimMisere.py`](../res/exampleNimMisere.py),
[`res/exampleMastermind.py`](../res/exampleMastermind.py).

## Problèmes « entrée → sortie »

Un genre de problème qui n'est pas un jeu : ni partie, ni adversaire, ni
action. Quelques **paires** montrent une entrée et la sortie attendue ; une ou
plusieurs **questions** donnent une entrée dont il faut trouver la sortie. La
mère cherche le plus petit programme qui transforme chaque entrée en sa sortie
(voir `docs/architecture.md`, § 10) et écrit un fils qui **répond**.

Le fichier est du **JSON** (extension `.json`, c'est ainsi que
`python -m xander` reconnaît le genre) :

```json
{
  "nom": "initiales",
  "domaine": "mots",
  "enonce": "La première lettre de chaque mot.",
  "paires": [
    {"entree": "jean pierre", "sortie": ["j", "p"]},
    {"entree": "le petit chat", "sortie": ["l", "p", "c"]}
  ],
  "questions": [
    {"entree": "un deux trois", "sortie": ["u", "d", "t"]}
  ]
}
```

| Clé | Rôle |
|---|---|
| `paires` | obligatoire, non vide : des objets `{"entree": …, "sortie": …}` |
| `questions` | des objets `{"entree": …}` ; `"sortie"` est permise mais **réservée à l'examinateur** : elle sert à noter le fils et n'est jamais donnée à la mère |
| `nom` | le nom du problème (unique dans un lot) |
| `domaine`, `enonce` | pour les humains (ranger, comprendre, mesurer) ; la mère ne les lit pas |

Les **valeurs** sont des nombres, des textes, des booléens (`true`,
`false`) et des listes de ces valeurs, imbriquées autant qu'on veut. Rien
n'est propre à un domaine : une liste de nombres, une phrase, un plateau de
Morpion (une liste de 9 cases, ou 3 rangées de 3) s'écrivent avec les mêmes
valeurs. `null` et les objets ne sont pas permis : une erreur le dit, avec la
paire fautive.

Un fichier peut aussi contenir un **lot** : `{"domaine": …, "problemes":
[…]}`. Le `domaine` du lot vaut pour chaque problème qui n'en donne pas.

Il faut au moins deux paires distinctes : une seule peut être une
coïncidence (la mère refuse alors de conclure).

**Lien avec la forme commune visée** (jalon 1 de la feuille de route : un
exemple est une suite d'observations, *un état, ce qui s'est passé, l'état
suivant*). Une paire est une suite d'**une seule** observation où il ne s'est
rien passé de visible : l'état est l'entrée, l'état suivant la sortie, sans
action ni joueur (`Probleme.en_observations()` la donne sous cette forme). Une
partie, elle, est une suite de plusieurs observations reliées par des actions.
Le programme cherché, `sortie = t(x)`, est l'analogue de `apres = t(avant,
args)` que la mère construit pour une action (`xander/effets.py`), sans
arguments. Le jour où les deux formats se rejoindront, un problème « entrée →
sortie » sera un exemple d'une observation par paire ; rien n'est réécrit
pour l'instant.

Problèmes fournis : `res/problemes/entrainement/` (listes, mots, nombres,
plateaux de nos jeux), qui ont servi à choisir les briques, et
`res/problemes/inedits/`, écrits une fois les briques figées et passés une
seule fois (voir la feuille de route). Aucun ne ressemble à ARC : ni grilles
de couleurs, ni objets à déplacer.
