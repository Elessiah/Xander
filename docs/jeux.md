# Les jeux de test

Les jeux de `Games/` servent de terrain d'entraînement à la mère. Les jeux à
deux joueurs (Morpion, Allumettes, Puissance 4, Pylos) suivent la même interface (les
méthodes marquées `# Pattern Name` dans le code), ce qui permet d'écrire des
exemples de partie semblables. Jumper et Partition, à un joueur, ont leur
propre interface (voir plus bas).

| Méthode | Rôle |
|---|---|
| `init(start_player="R")` | nouvelle partie ; `"X"`, `"O"` ou `"R"` (aléatoire) |
| `get_game_state()` | renvoie l'état ; **relance une partie** si la précédente est finie |
| `get_turn()` | joueur qui doit jouer |
| `play(coup)` | `False` si coup invalide (un booléen est refusé), `True` si la partie est finie, sinon le nouvel état |
| `back()` | annule le dernier coup (état et joueur) et renvoie l'état |
| `print()` | affiche le jeu |

Après la fin d'une partie, `game.win` vaut `"X"`, `"O"` ou `"D"` (nul).

## Morpion — `Games/Morpion.py`

Plateau de 9 cases ; une case libre contient son indice (`"0"`…`"8"`).
Adversaire : `Games/MinmaxMorpion.py`. Une heuristique note chaque case
(ligne vierge, alignement à compléter, adversaire à bloquer) et un minimax avec
élagage alpha-bêta explore l'arbre complet ; l'heuristique départage les coups
de même valeur. Il ne perd jamais.

## Allumettes — `Games/Allumettes.py`

On retire 1 à 3 allumettes ; celui qui doit prendre la dernière perd (il gagne
donc s'il en laisse exactement une). Adversaire : `Games/MinmaxAllumettes.py`.

Stratégie : les positions perdantes pour celui qui doit jouer sont
1, 5, 9, 13… allumettes (`(n - 1) % 4 == 0`). Depuis `n` allumettes, il faut en
retirer `(n - 1) % 4` ; si ce reste est nul, la position est perdue et on en
retire une.

L'ancienne note « Schématisation Allumettes » cherchait ce motif à l'aide de
`% 3` et `% 2` (« tiers gagnant / perdant ») ; la bonne période est 4
(= prise maximale + 1).

Pour la mère, la partie finit à 1 allumette et la gagne **celui qui vient de
jouer**. Une prise qui mène à 0 (prendre les 2 ou 3 dernières) finit aussi la
partie, mais la fait perdre à celui qui la joue : l'exemple ne le montre pas.

**Variante jouée jusqu'au bout** — `Games/AllumettesMisere.py`, exemple
`res/exampleAllumettesMisere.py`. La partie ne s'arrête plus à 1 : elle finit
à 0, et celui qui prend la dernière perd. Le dernier coup fait donc perdre
celui qui le joue : la fin à 0 fait gagner le joueur qui a le trait. La
stratégie est la même (laisser 1, 5, 9…) : le professeur est le même Minmax.

## Puissance 4 — `Games/Puissance4.py`

7 colonnes × 6 lignes, `play(colonne)`. Victoire par 4 alignés dans les quatre
directions, nul quand le plateau est plein. `get_moves()` donne les colonnes
encore jouables.

Adversaire : `Games/MinmaxPuissance4.py`. L'arbre complet est trop grand : un
negamax avec élagage alpha-bêta explore 6 demi-coups (moins d'une seconde par
coup), puis note les feuilles. Chaque fenêtre de 4 cases alignées ne contenant
que les jetons d'un joueur lui rapporte des points (2 pour deux jetons, 5 pour
trois), et chaque jeton de la colonne centrale rapporte un bonus. Les colonnes
sont explorées du centre vers les bords. Il ne rate jamais une victoire ou un
blocage immédiat et bat toujours un joueur aléatoire, mais il n'est pas
imbattable : au-delà de son horizon, un humain attentif peut le piéger.

Exemple de partie : [`res/examplePuissance4.py`](../res/examplePuissance4.py).
À cause de la gravité, la case modifiée n'est la case `colonne` que pour la
ligne du bas. La mère le décrit elle-même : en jouant des parties dans son
labo, elle voit les cases que remplit chaque colonne, et dans quel ordre, puis
compose
`changees = premiere_de(portee(arg0), valant(' '))` (la première case vide de
ce que remplit l'action). Elle peut ensuite y éduquer un fils.

## Pylos — `Games/Pylos.py`

Une pyramide de billes sur une base de `size` × `size` (3 par défaut :
9 + 4 + 1 = 14 emplacements, 7 billes par joueur ; 4 pour le jeu du
commerce : 30 emplacements). Le plateau liste les emplacements étage par
étage ; un emplacement d'étage supérieur repose sur les quatre du dessous.

Un tour peut compter plusieurs actions, d'où plusieurs fonctions de jeu :

| Action | Rôle |
|---|---|
| `play(dest)` | poser une bille de la réserve sur un emplacement libre et soutenu |
| `move(src, dest)` | monter une de ses billes libres vers un emplacement plus haut qu'elle ne soutient pas |
| `take(cell)` | après un carré 2 × 2 de sa couleur : reprendre une de ses billes libres |
| `stop()` | ne pas reprendre de deuxième bille |

`get_phase()` dit où en est le tour (`0` : poser ou monter, `1` : reprendre,
`2` : reprendre encore ou s'arrêter), `get_reserve(joueur)` le nombre de
billes en réserve, `get_moves()` les actions permises. Un joueur qui ne peut
plus rien faire à son tour perd : poser la bille du sommet fait gagner. Il
n'y a pas de nul. Variante choisie : un joueur à la réserve vide continue tant
qu'il peut monter une bille.

Adversaire : `Games/MinmaxPylos.py`. Sur la base 3 × 3, les 79 453 positions
atteignables sont énumérées puis résolues à rebours depuis les fins de partie
(environ 2 secondes au premier appel). Il est donc exact, et l'analyse reste
juste même si une partie revient sur une position déjà vue. Il gagne le plus
vite possible ou perd le plus tard possible. La base 4 × 4 demandera un
Minmax à profondeur limitée.

Ce que dit la résolution de la base 3 × 3 (vérifié par les tests) :

- le premier joueur gagne, mais **seulement en commençant au centre** ;
- en jeu parfait, il gagne grâce à un **carré** au deuxième étage : il
  reprend une bille, ce qui lui laisse la bille du sommet ;
- dans 3 801 positions gagnantes, **monter** une bille est la seule façon de
  gagner ; un joueur qui pose toujours au plus bas sans jamais monter perd.

Le jeu n'est donc pas dégénéré : carrés, reprises et montées comptent.

Exemple de partie : [`res/examplePylos.py`](../res/examplePylos.py) (19 tours,
avec 3 montées, 3 reprises et un arrêt ; X gagne car O ne peut plus jouer).
La mère y décrit seule les trois actions : `play` et `take` changent
`case(arg0)`, `move` change `union(case(arg0), case(arg1))`. Il faut au moins
deux reprises dans l'exemple : une description tirée d'un seul cas n'est pas
retenue. L'éducation ne marche pas encore : la mère ne connaît qu'une action
par tour (`get_game_state -> play`) et ne rejoue que `play` dans son labo.

## Jumper — `Games/Jumper.py`

Jeu à un joueur : un coureur saute (`play(True)`) par-dessus des obstacles qui
défilent. Interface : `init()`, `play(saut)`, `get_board()`, `back()`,
`print()` et l'attribut `game_over`. `play` renvoie l'écran, ou `False` quand
le joueur est touché (jamais `True`). `get_board()` renvoie l'écran complet (200 caractères : décor,
obstacles, joueur). Les obstacles sont aléatoires ; `Jumper(graine)` les rend
reproductibles, ce qui est nécessaire pour un exemple de partie.
`python -m Games.mainJumper` pour y jouer (Windows, Linux et macOS).
Exemple de partie (`res/exampleJumper.py`) : une partie complète, graine 0,
un saut à vide, un saut par-dessus le premier obstacle, puis le coureur
touche le deuxième au coup 73.

## Partition — `Games/Partition.py`

Jeu à un joueur inventé pour apprendre à éduquer un fils seul, plus simple
que Jumper : aucun état caché, une erreur se paie tout de suite. La partition
montre les 8 prochains temps (`o` une note, `.` un silence) et avance d'un
temps à chaque `play`. `play(True)` frappe, `play(False)` se tait ; frapper sur
un silence ou se taire sur une note finit la partie (`play` renvoie `False`).
Interface : `init()`, `get_partition()`, `play(frappe)`, `back()`.
`Partition(n)` joue toujours le même morceau. Exemple : `res/examplePartition.py`.

## Lancer une série de parties

```powershell
python -m Games.GamePlayer morpion --x humain --o minmax --score 3 --start R
```

`--x` / `--o` : `humain` ou `minmax`. Au Pylos, on tape `4` (poser), `2 9` (monter de 2 vers 9),
`r 5` (reprendre) ou `s` (s'arrêter). La série s'arrête quand un joueur atteint
`--score` points, ou après `3 × score` matchs nuls. Tapez `q` pour quitter.
