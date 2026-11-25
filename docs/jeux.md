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

## Tours de Hanoï — `Games/Hanoi.py`

Jeu à **un joueur**, avec des **déplacements**. Trois piquets (`0`, `1`, `2`)
et `n` disques de tailles différentes (`Hanoi(3)` par défaut, `Hanoi(4)` ou
`set_nb_disques(4)` avant `init()` pour une pile plus haute). Au départ, toute
la pile est sur le piquet 0, le plus grand en bas. Un coup prend le disque du
dessus d'un piquet et le pose sur un autre ; on ne pose jamais un disque sur un
plus petit. **Le but** : toute la pile sur le piquet 2, ce qui demande au
moins `2ⁿ − 1` coups (7 pour 3 disques, 15 pour 4). **La limite** : au plus le
double du minimum (14 coups pour 3 disques, 30 pour 4) ; le coup qui l'atteint
sans avoir rangé la pile fait perdre. Si ce coup range la pile, la partie est
gagnée. La limite donne au jeu une fin perdue sans le rendre cruel : depuis le
départ, on peut gaspiller autant de coups que le minimum.

**L'état observable** : pour chaque disque, du plus petit au plus grand, le
numéro du piquet où il est. `[0, 0, 0]` au départ, `[2, 2, 2]` au but ;
`[1, 2, 0]` : le petit sur le piquet 1, le moyen sur le 2, le grand sur le 0.
Pourquoi ce choix plutôt qu'une liste par piquet :

- c'est une **liste plate de taille fixe** (une case par disque), comme les
  plateaux des autres jeux, et c'est la plus courte (`n` cases) ;
- **toute** liste de `0`, `1` et `2` est une position permise : l'ordre des
  disques sur un piquet n'a pas à être écrit, la règle l'impose (le plus petit
  en haut). Une liste par piquet aurait une taille variable, et une case par
  emplacement (3 piquets × `n` étages) beaucoup de positions impossibles et
  l'allure d'une grille ;
- un coup change **une seule case** : celle du disque déplacé, qui prend la
  valeur du piquet d'arrivée.

Le nombre de coups joués (la limite) n'est **pas** dans l'état : comme une
pendule, il ne compte que pour la fin. `game.coups` le donne.

| Méthode | Rôle |
|---|---|
| `init()` | nouvelle partie, renvoie l'état |
| `get_game_state()` | renvoie l'état ; **relance une partie** si la précédente est finie |
| `play(depart, arrivee)` | `False` si le coup est refusé (rien ne change), `True` si la partie est finie (gagnée ou perdue), sinon le nouvel état |
| `back()` | annule le dernier coup (et la fin qu'il a provoquée) et renvoie l'état |
| `get_moves()` | les coups permis, des couples `(depart, arrivee)` |
| `get_turn()` | toujours `"J"` : le joueur est seul |
| `print()` | affiche les piquets |
| `set_game_state(disques, coups=0)` | impose une position (tests, professeur) |

Un coup est **refusé** (`play` renvoie `False`, l'état et le compte de coups
ne changent pas, `back` ne le voit pas) quand le piquet de départ est vide,
quand le disque irait sur un plus petit, quand un piquet n'existe pas, quand
départ et arrivée sont le même piquet, quand un argument n'est pas un entier
(un booléen est refusé) et quand la partie est finie. Après la fin,
`game.finie` est vrai et `game.win` vaut `"J"` si la pile est rangée, `""`
si la limite est atteinte (personne n'a gagné). `play` renvoie `True` dans
les deux cas, comme aux jeux à deux : il faut lire `win` pour savoir laquelle.

**Le professeur** — `Games/ProfesseurHanoi.py`. Il y a `3ⁿ` positions (27
pour 3 disques, 81 pour 4) et un coup se défait par le coup inverse : un
parcours en largeur **parti du but** donne en une fois la distance au but de
toutes les positions (0,5 ms pour 3 disques, 1,3 ms pour 4, 0,1 s pour 8).
`meilleur_coup(etat)` joue le premier coup permis qui rapproche le but d'un
coup ; `professeur_hanoi_play(game)` lit l'état observable et joue ce coup.
Il est exact : les tests vérifient, depuis **chacune** des 27 et 81
positions, qu'il ne joue que des coups permis et range la pile en le nombre
minimal de coups (au plus `2ⁿ − 1`, la distance la plus longue), et que les
distances vérifient `d = 1 + min(d des voisins)` (contrôle indépendant du
parcours).

**Exemple de partie** : [`res/exampleHanoi.py`](../res/exampleHanoi.py),
3 disques. Une vraie partie, pas parfaite : le joueur pose le disque moyen
sur le piquet 2 trop tôt, doit l'en retirer, et range la pile en 10 coups
(les six sortes de déplacements y apparaissent). Elle finit gagnée :
`# end player joueur`, et le dernier `play` renvoie `True` (`# bool`).

**Les notions nouvelles** : déplacer quelque chose d'un endroit à un autre
sous une contrainte (jamais sur un plus petit), une action à **deux
arguments** (départ, arrivée) dont aucun n'est l'indice de la case qui
change, et un **but à atteindre** plutôt qu'un adversaire, avec deux fins
possibles (gagnée, perdue). C'est un pas vers les montées de billes du Pylos
et vers les dames.

**Ce que la mère en comprend déjà** (sans rien changer à `xander/`) :

- `python -m xander res/exampleHanoi.py` : elle voit un joueur seul, un tour
  `get_game_state -> play`, la fonction d'annulation, le gagnant et la
  variable `disques` (tableau de 3). Elle **ne décrit pas** l'action :
  `game.play : inconnue`, les 10 coups sont « non compris ». Aucun terme de
  `xander/effets.py` ne donne la case qui change : c'est **la première case
  qui vaut `arg0`** (le plus petit disque du piquet de départ), et
  `premiere_de` demande une suite ordonnée, que seule `portee(x)` fournit ;
  or `portees_observees` ne regarde que les cas **à un argument**.
  Vérifié à part, sans toucher au dépôt : en calculant les portées sur
  `arg0`, la mère obtient `portee(0) = [0, 1, 2]` et le terme
  `premiere_de(portee(arg0), valant(arg0))` (taille 4) explique les 10 coups.
  La forme `changees` ne dit pas non plus la **nouvelle valeur** de la case
  (`arg1`) : pour prévoir l'état d'après, il faudra une forme « la case
  changée prend la valeur … ».
- `python -m xander res/exampleHanoi.py --son hanoi --parties 30` s'arrête
  aussitôt, avant la première partie, dans `Solo.__init__`
  (`xander/un_joueur.py`) : « aucun programme n'explique ce que change
  l'action, même avec ce que la mère a vu dans le labo ». En amont,
  `Education.discover_actions` (`xander/education.py`) ne regarde que le
  premier argument (`f.arguments[0]`) et essaie `play(0)` avec **un seul**
  argument : le jeu lève une erreur, aucune action n'est trouvée, et
  `explore` ne joue que l'exemple.

Ce qui manquerait, dans l'ordre où la mère le rencontrera : des actions à
plusieurs arguments (les découvrir, les explorer, les écrire dans le fils
comme des couples) ; des portées et une description pour ces actions ; une
forme qui dit ce que devient la case changée ; une fin à **deux issues** —
`play` renvoie `True` aux deux, et `Solo` lit dans l'exemple une seule
valeur de fin (« gagnée ») : sans lire `win` ou reconnaître la position but,
elle prendrait la limite atteinte pour une victoire ; enfin une partie dont
le compte de coups est caché (deux parties dans le même état visible n'ont
pas le même nombre de coups restants), limite déjà notée de `Solo`.
