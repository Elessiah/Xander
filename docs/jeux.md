# Les jeux de test

Les jeux de `Games/` servent de terrain d'entraînement à la mère. Les jeux à
deux joueurs (Morpion, Allumettes, Puissance 4, Pylos, Nim) suivent la même interface (les
méthodes marquées `# Pattern Name` dans le code), ce qui permet d'écrire des
exemples de partie semblables. Jumper et Partition, à un joueur, ont leur
propre interface ; Mastermind, à un joueur, garde celle des jeux à deux
(voir plus bas).

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

## Nim à plusieurs tas — `Games/Nim.py`

Plusieurs tas d'objets (`set_tas(3, 4, 5)` avant `init`, c'est le
défaut). À son tour, un joueur prend autant d'objets qu'il veut, au moins
un, dans **un** tas : `play(tas, nombre)`, une action à **deux arguments**.
Celui qui prend le dernier objet gagne. L'état est la liste des tailles :
`[3, 4, 5]`. Un coup refusé (tas inexistant ou vide, nombre nul ou trop
grand, argument qui n'est pas un entier, booléen compris) renvoie `False` et
ne change rien. Interface des jeux à deux : `init`, `get_game_state`,
`get_turn`, `play`, `back`, `win`, plus `get_moves()` (les couples
`(tas, nombre)` permis), `set_game_state(tas, joueur)` et `play_text("1 3")`.

**Variante misère** — `Games/NimMisere.py`, exemple
`res/exampleNimMisere.py` : celui qui prend le dernier objet perd. Comme aux
Allumettes jouées jusqu'au bout, la fin (tous les tas vides) fait gagner le
joueur qui a le trait. Seul l'attribut de classe `MISERE` change.

Professeur : `Games/MinmaxNim.py`, exact. C'est la stratégie de Bouton : la
position est perdue pour celui qui a le trait si le ou exclusif des tailles
(la « somme de Nim ») est nul, sinon il la ramène à zéro. En misère, on joue
pareil tant qu'au moins deux tas ont plus d'un objet, puis on laisse un
nombre impair de tas d'un objet. Depuis une position perdue, il prend un
objet du plus gros tas. Les tests comparent la stratégie à un Minmax
exhaustif mémoïsé (`valeur`) sur toutes les positions de 3 tas jusqu'à 5 et
de 4 tas jusqu'à 3, dans les deux variantes : mêmes valeurs, et le coup
proposé gagne toujours depuis une position gagnante. Contre un joueur
aléatoire, il gagne toutes les parties commencées dans une position gagnante, qu'il
joue en premier ou en second. Depuis `[3, 4, 5]`, le premier joueur gagne en
prenant 2 objets du tas 0.

Ce que le jeu apporte de nouveau : un état fait de **plusieurs nombres**
(ni un plateau de cases à propriétaire, ni un seul nombre), une action à
**deux arguments** (où, et combien), et une stratégie gagnante qui n'est pas
une simple période (aux Allumettes, `n % 4` suffisait ; ici il faut combiner
les tas, et le ou exclusif n'est pas dans l'équipement de la mère).

Exemple de partie : [`res/exampleNim.py`](../res/exampleNim.py) (tas 3, 4,
5 ; 7 coups ; X se trompe au premier coup, O au sixième, X prend le dernier
objet). `python -m Games.GamePlayer nim --x humain --o minmax` pour y jouer.

**Ce que la mère en comprend** (`python -m xander res/exampleNim.py`) :
deux joueurs, un tour `get_game_state -> play`, la variable `tas` (tableau
de 3), et `play : changees = case(arg0)` : le premier argument désigne le
tas qui change. Le dernier coup (qui renvoie `True`) reste « non compris »,
comme dans les autres exemples.

**L'éducation** (`python -m xander res/exampleNim.py --prof
Games.MinmaxNim:minmax_nim_play --parties 30`), sans rien de propre au Nim
dans `xander/` (voir `docs/architecture.md`, § 3 et § 6) :

- les actions : les tas 0 à 2 et les nombres 1 à 5, explorés argument par
  argument à partir de l'exemple ; 12 couples gardés (le jeu les accepte
  quelque part) ;
- ce que l'action écrit : `case(arg0)` reçoit `moins(ici, arg1)` (le tas perd
  ce qu'on y prend), un programme qu'elle construit ;
- quand un coup est permis : `non inf(ici, arg1)` (le tas a au moins ce qu'on
  prend), déduit des coups refusés ;
- la valeur écrite ne dit pas qui a joué : pas de pions, la position porte le
  trait, comme aux Allumettes ; la fin est l'état `(0, 0, 0)`, gagnée par
  celui qui vient de jouer (en misère, par celui qui a le trait), comprise
  par contre-épreuve ;
- deux règles construites (« après mon coup, tout coup laisse un gain »,
  celle des Allumettes, et une autre à deux niveaux) et 30 souvenirs ;
  44 erreurs, presque toutes dans les deux premières parties ; 0 coup
  impossible ; au plus 301 positions regardées pour un coup.

Le fils gagne en premier contre le professeur, perd en second (la position
de départ est perdue pour lui), et bat le hasard 196 à 200 fois sur 200. Il
rate encore le gain dans 16 des 102 positions gagnables à 3, 4 et 5 tas au
plus : la somme de Nim est hors de portée de ses concepts, et le professeur
rejoue les mêmes parties (200 parties n'y changent rien). Variante misère :
même chemin, 48 erreurs, une règle, 35 souvenirs, 17 positions gagnables
ratées sur 101.

## Mastermind — `Games/Mastermind.py`

Jeu à **un joueur** avec une **information cachée**. `Mastermind(graine)`
tire un code secret de 3 chiffres de 1 à 6 (216 codes, répétitions
permises) ; `Mastermind(0)` donne toujours la même suite de secrets (le
premier est `441`). Le joueur propose un code, **un chiffre par argument** :
`play(1, 2, 3)`. Le jeu répond par le nombre de chiffres **bien placés** et
de chiffres **mal placés** (chaque chiffre du secret ne compte qu'une fois).
La partie est gagnée quand les 3 sont bien placés, perdue après 8
propositions.

**L'état observable** (`get_game_state`, et ce que renvoie `play`) est le
plateau du jeu de société : 8 rangées de 5 trous, les 3 chiffres proposés
puis les bien placés et les mal placés, soit une liste de 40 cases, rangée
après rangée ; une case vide vaut `" "`. La proposition `k` remplit la
rangée `k`. Le secret n'y apparaît jamais. Pourquoi ce choix : c'est la
forme des autres jeux (une liste de cases de taille fixe, `" "` pour une
case vide, comme au Puissance 4 ou au Pylos), c'est l'historique complet
sous la forme la plus simple, et la mère peut y chercher ce que change une
action avec les outils qu'elle a déjà (quelles cases, quelle valeur). Une
liste de propositions qui s'allonge aurait demandé un état de taille
variable, que rien d'autre dans le dépôt n'utilise.

**L'action** prend un argument par chiffre plutôt qu'un nombre (`play(123)`)
ou une chaîne : chaque argument est la valeur d'une case, la mère peut
relier directement un argument à une case qui change, sans apprendre
d'abord à découper un nombre en chiffres. Nouveau par rapport aux autres
jeux : les arguments sont des **valeurs écrites**, pas des positions.

Interface : celle des jeux à deux. `init()` (l'argument `start_player` est
accepté et ignoré ; une partie que personne n'a commencée garde son secret),
`get_game_state()` (relance une partie, avec un nouveau secret, si la
précédente est finie), `play(a, b, c)` (`False` si la proposition est
invalide : mauvais nombre de chiffres, chiffre hors de 1 à 6, argument qui
n'est pas un entier, partie finie ; `True` si la partie finit, gagnée ou
perdue ; sinon le plateau), `back()` (retire la dernière proposition, le
secret ne change pas), `get_turn()` (toujours `"X"`, le seul joueur),
`get_moves()`, `play_text("123")`, `set_secret(a, b, c)` (pour les tests).
Après la fin, `win` vaut `"X"` si le code est trouvé, `"O"` sinon : O est le
codeur, qui a choisi le secret et ne joue jamais.
`python -m Games.Mastermind` pour y jouer.

Professeur : `Games/MinmaxMastermind.py`. Il ne lit que le plateau et les
règles, jamais le secret (un test le vérifie : deux secrets différents, même
plateau, même proposition), et il est déterministe. Il propose le code dont
la **pire** réponse laisse le moins de codes compatibles (à la manière de
Knuth), en préférant à égalité un code qui peut être le secret. Mesuré sur
les 216 secrets : **4,05 essais en moyenne, 5 au plus** (1 secret trouvé en
1 essai, 2 en 2, 37 en 3, 122 en 4, 54 en 5), moins d'une seconde pour les
216 parties. Une stratégie plus naïve, « proposer le premier code encore
compatible » (`premier_compatible_play`), demande 5,26 essais en moyenne et
jusqu'à 8, tout juste la limite.

Ce que le jeu apporte de nouveau : un jeu à **un seul joueur** qui se gagne
(pas seulement « durer », comme Jumper ou Partition), une **information
cachée** (deux parties au même plateau peuvent avoir des secrets
différents), **déduire** à partir de quelques indices (éliminer les codes
incompatibles), **compter** (bien placés, mal placés), une action à
**trois arguments** qui sont des valeurs, et des cases écrites qui ne
dépendent pas de l'action seule mais du secret.

Exemple de partie : [`res/exampleMastermind.py`](../res/exampleMastermind.py)
(graine 0, secret `441`, trouvé au sixième essai : `123`, `456`, `415`,
`431`, `451`, `441`). La section de fin est `# end player X` : le format dit
que le seul joueur a gagné (`# end` seul dirait une partie perdue).

**Ce que la mère en comprend aujourd'hui** (`python -m xander
res/exampleMastermind.py`) : un seul joueur, X, un tour `get_game_state ->
play`, la variable `plateau` (tableau de 40) et que l'exemple est gagné.
Elle ne comprend **aucun** appel de `play` (« opération inconnue », la
variable n'est « modifiée par » rien) : les cases qui changent dépendent du
numéro de la proposition (la première rangée vide), pas d'un argument, et
deux d'entre elles (bien et mal placés) dépendent du secret. Avec `--son`,
le mode « un joueur » s'arrête tout de suite : « aucun programme n'explique
ce que change l'action ».

## Lancer une série de parties

```powershell
python -m Games.GamePlayer morpion --x humain --o minmax --score 3 --start R
```

Jeux : `morpion`, `allumettes`, `puissance4`, `pylos`, `nim`, `nim-misere`.
`--x` / `--o` : `humain` ou `minmax`. Au Pylos, on tape `4` (poser), `2 9` (monter de 2 vers 9),
`r 5` (reprendre) ou `s` (s'arrêter). Au Nim, `2 3` (3 objets du tas 2). La série s'arrête quand un joueur atteint
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

**Ce que la mère en comprend** (`python -m xander res/exampleHanoi.py`) :
un joueur seul, un tour `get_game_state -> play`, la fonction d'annulation,
le gagnant et la variable `disques` (tableau de 3). L'Analyzer seul (sur
l'exemple, sans labo) ne décrit pas l'action : il lui faut des portées, que
seul le labo donne.

**L'éducation** (`python -m xander res/exampleHanoi.py --son hanoi
--parties 30`), sans rien de propre à Hanoï dans `xander/` (voir
`docs/architecture.md`, § 3 et § 6) :

- les actions : les 6 couples `(depart, arrivee)` de piquets différents,
  explorés argument par argument à partir de l'exemple ;
- où l'action écrit : avec les portées rangées par argument (`(0, 0)`, partir
  du piquet 0, remplit les cases 0, 1, 2 dans cet ordre),
  `premiere_de(portee(arg0), valant(arg0))`, « le premier disque du piquet de
  départ » ; ce qu'elle écrit : `arg1`, le piquet d'arrivée ;
- quand un coup est permis :
  `non inf(premiere_de(portee(arg0), valant(arg1)), cellule)`, « aucun disque
  du piquet d'arrivée ne vient avant celui qu'on déplace » : jamais sur un
  plus petit. Déduit des coups refusés, puis mis à l'épreuve dans le labo
  (l'exploration seule donnait une coïncidence) ;
- **deux fins au même signal** : `play` renvoie `True` à la victoire et à la
  limite. La mère comprend l'état de fin de l'exemple, `[2, 2, 2]`, par
  contre-épreuve ; une fin ailleurs n'est pas comprise et ne vaut rien
  (jamais une victoire). Elle ne lit pas `win` (l'exemple ne le lit pas) ;
- un casse-tête : elle juge un coup en cherchant une victoire jusqu'à 10 coups
  plus loin (la longueur de l'exemple), plus tôt valant mieux.

Résultat (graines 0 à 2, moins d'une seconde) : les parties 1 à 4 finissent
à la limite, avec 25 erreurs ; dès la partie 5, le fils range la pile en 7
coups (le minimum) à chaque partie, avec 7 souvenirs, aucun petit motif, 0
coup impossible. Le fils joué dans le vrai jeu range la pile en 7 coups. Il
voit 76 des 78 coups permis des 27 positions (aucun interdit) et ne range la
pile que depuis 15 des 27 positions : il ne reconnaît que les positions de
son chemin. Le compte de coups caché (la limite) reste confondu : deux
parties dans le même état visible sont jugées pareil.

## Le compte est bon (version courte) — `Games/CompteEstBon.py`

Jeu à un joueur, sur des nombres. On dispose de **4 nombres** (de 1 à 10,
répétitions permises) et d'une **cible** (de 11 à 100). Un coup combine deux
nombres disponibles avec une opération : les deux nombres sont remplacés par
le résultat. Les résultats sont toujours entiers et positifs (règle
classique) : une soustraction doit donner plus que 0, une division doit
tomber juste.

**État** (`get_game_state()`) : une liste plate de 5 entiers, les 4 places
puis la cible, par exemple `[5, 5, 10, 4, 85]`. Une place vide vaut `0`, qui
n'est jamais un nombre puisque tout résultat est positif. Les places ne
bougent pas : on voit directement quelles cases un coup a changées, et la
liste garde toujours la même taille et le même type de valeurs (aucune
`None`, aucun texte). La cible est une case comme les autres, qui ne change
jamais.

**Action** : `play(i, j, op)`, trois entiers. Le résultat de
`nombres[i] op nombres[j]` va à la place `i`, la place `j` se vide. `op` :
`0` addition, `1` soustraction (`i` moins `j`), `2` multiplication, `3`
division (`i` divisé par `j`). Des entiers plutôt que `"+"` : tous les
arguments sont du même genre, comme les cases des autres jeux.

| Méthode | Rôle |
|---|---|
| `CompteEstBon(graine)` | série de tirages reproductible ; le constructeur tire le premier |
| `init()` | tire le suivant et renvoie l'état |
| `get_game_state()` | l'état ; ne relance **pas** une partie finie (comme Partition) |
| `play(i, j, op)` | l'état, `True` (gagnée), `False` (perdue ou refusé) |
| `back()` | annule le dernier coup, même celui qui a fini la partie |
| `get_moves()` | les coups `(i, j, op)` permis |
| `print()`, `set_game_state(etat)` | affichage ; imposer un état (tests) |

Attributs : `finie`, `gagnee`. Pas de `get_turn` ni de `win` : il n'y a
qu'un joueur, comme à Jumper et Partition.

**Fin.** Règle la plus simple : la partie est **gagnée** dès que la cible
apparaît parmi les nombres (`play` renvoie `True`), **perdue** quand il ne
reste qu'un nombre et que ce n'est pas la cible (`play` renvoie `False`,
comme la fin perdue de Partition et Jumper ; le coup est joué). Avec deux
nombres ou plus, l'addition est toujours possible : la partie ne se bloque
jamais avant. Elle dure donc **au plus 3 coups**. On ne s'arrête pas quand
la cible devient inatteignable : ce serait une règle que le joueur ne voit
pas.

**Coup refusé** : partie finie, indice hors des 4 places ou place vide,
`i == j`, opération inconnue, soustraction qui ne donne pas un résultat
positif, division qui ne tombe pas juste, argument qui n'est pas un entier
(un booléen non plus). Rien ne change et `play` renvoie `False`, comme au
Morpion. Un refus se distingue d'une fin perdue parce que l'état n'a pas
changé : c'est justement ce que regarde le labo de la mère.

**Tirage.** Chaque tirage est **soluble** : la cible est choisie au hasard
parmi les valeurs de 11 à 100 que l'on peut atteindre avec les 4 nombres
(et qui n'en font pas déjà partie). Si aucune ne l'est (`1 1 1 1`), on
retire les nombres. Sur 500 graines, la solution la plus courte demande
1 coup (67 fois), 2 coups (203) ou 3 coups (230).

**Professeur** : `Games/SolveurCompteEstBon.py`,
`solveur_compte_est_bon_play(game)`. Il lit l'état observable et cherche
**en largeur** le chemin le plus court vers un état où la cible apparaît
(tous les coups permis, puis tous ceux d'après, sans revisiter un état déjà
vu), puis joue le premier coup. Il est exact : il trouve toujours la cible
sur un tirage soluble, par le chemin le plus court. Il regarde au plus
quelques centaines d'états (758 au plus sur 500 graines ; environ 4 ms pour
une partie entière). Si un coup maladroit a rendu la cible inatteignable, il
vise le nombre le plus proche (règle du vrai jeu). Il ne fait pas partie de
Xander.

**Exemple** : [`res/exampleCompteEstBon.py`](../res/exampleCompteEstBon.py),
graine 2, tirage `5 5 10 4 → 85`. Le joueur fait 4 + 5 = 9, 10 × 9 = 90,
90 − 5 = 85 : `play` renvoie `True`, l'exemple finit par
`# end player joueur` (une partie gagnée, comme un casse-tête résolu). Les
indices varient (`i` plus grand ou plus petit que `j`) et trois opérations
sur quatre apparaissent.

**Notions nouvelles** : combiner des quantités pour atteindre un but (le but
est une case de l'état, la cible) ; une action à **plusieurs arguments**,
dont un ne désigne pas une case (`op`) ; une partie qui peut finir de deux
façons (gagnée, perdue) ; chercher sans tout énumérer (pour la mère, plus
tard : reconnaître « il manque 5, et j'ai un 5 »).

**Ce que la mère en comprend** (`python -m xander res/exampleCompteEstBon.py`) :
un seul joueur, des tours `get_game_state -> play`, l'annulation, le
gagnant, la variable `etat` (tableau de 5) que lit `get_game_state` et que
modifie `play`. Sur l'exemple seul, elle décrit `play` par **les cases qui
changent** : `changees = union(case(arg0), case(arg1))`, les places des deux
nombres combinés. Une deuxième hypothèse, `union(case(arg2), case(3))`, est
une coïncidence de l'exemple ; les essais du labo la réfutent.

**L'éducation** (`python -m xander res/exampleCompteEstBon.py --son ceb
--parties 30`), sans rien de propre au jeu dans `xander/` (voir
`docs/architecture.md`, § 3 et § 6) :

- les actions : les places 0 à 3 et les opérations 0 à 3, explorées argument
  par argument ; 36 des 64 combinaisons sont acceptées quelque part sur le
  tirage du labo ;
- où l'action écrit : `ecrites = union(case(arg0), case(arg1))`, les cases
  **écrites** (5 × 1 laisse 5 à sa place : la case est écrite sans changer) ;
- ce qu'elle écrit : `case(arg0)` reçoit, **selon `arg2`**, `plus`, `moins`,
  `fois` ou `divise(ici, val(arg1))` ; `case(arg1)` reçoit `0`. Elle sépare
  les coups selon la valeur de l'argument qui choisit l'opération ;
- quand un coup est permis : `inf(ecrit1, ici) et inf(ecrit1, ecrit)` (la
  place n'était pas vide, le résultat est positif) ; une division qui ne
  tombe pas juste n'a pas de sens, ce n'est pas un coup. Avec la graine 0,
  une coïncidence de même taille gagne : `inf(arg0, ici)` (l'indice de la
  place est plus petit que son nombre, vrai sur ce tirage) ;
- les fins : la victoire est l'état final de l'exemple, `[0, 0, 85, 0, 85]`,
  comprise par contre-épreuve ; la défaite (il ne reste qu'un nombre, `play`
  renvoie `False` sur un coup joué) se voit comme une partie **bloquée** :
  aucune action n'est acceptée.

Résultat (graines 0 et 1, 6 à 9 s pour 30 parties) : le labo rejoue toujours
le tirage de l'exemple (`5 5 10 4 → 85`). Les parties 1 à 3 finissent
bloquées (une erreur chacune), puis le fils gagne en 3 coups à chaque
partie, avec 3 souvenirs et 0 coup impossible. **Où elle s'arrête** : sur
100 tirages jamais vus, le fils gagne 3 fois, sans aucun coup refusé (il voit
78 % des coups permis, aucun coup interdit). Il ne reconnaît que les états
exacts de son tirage ; il lui faudrait reconnaître des configurations
(« il manque 5, et j'ai un 5 »), et comprendre la victoire comme « la cible
apparaît parmi les nombres » plutôt qu'un état exact. Les petits motifs
(des cases à des valeurs fixes) et les fins par état n'y suffisent pas.

## Mot mystère — `Games/MotMystere.py`

Jeu à **un joueur**, sur des **mots**, avec une **information cachée**.
`MotMystere(graine)` tire un mot secret de 5 lettres dans le dictionnaire
`Games/mots_mystere.txt` (405 mots français courants, sans accents, en
minuscules, écrit pour le dépôt) ; la même graine tire toujours la même
suite de secrets. Le joueur propose un mot du dictionnaire ; le jeu répond
pour chaque lettre : `=` bien placée, `~` présente ailleurs, `-` absente. La
partie est **gagnée** quand le mot est trouvé, **perdue** après 6 essais.

**Lettres répétées.** Chaque lettre du secret ne sert qu'une fois. On marque
d'abord les lettres bien placées ; puis, de gauche à droite, une lettre mal
placée reçoit `~` seulement s'il reste dans le secret un exemplaire de cette
lettre qui n'a encore servi ni à un `=`, ni à un `~` plus à gauche ; sinon
`-`. Avec le secret `arbre`, `terre` donne `--~==` (le `r` bien placé prend
un des deux `r`, le `r` mal placé l'autre ; le seul `e` sert au `e` bien
placé, l'autre `e` est absent). Avec le secret `lampe`, `pelle` donne
`~-~-=` : le premier `e` est absent, car le seul `e` du secret est pris par
le `e` bien placé plus à droite.

| Méthode | Rôle |
|---|---|
| `init()` | nouvelle partie avec le secret suivant de la graine ; renvoie l'état vide |
| `get_game_state()` | l'état (60 cases) ; **relance une partie** si la précédente est finie |
| `get_turn()` | toujours `"joueur"` |
| `get_moves()` | les mots permis (tout le dictionnaire) |
| `play(mot)` | `False` si le coup est refusé, `True` si la partie est finie, sinon le nouvel état |
| `back()` | annule la dernière proposition (même après la fin) et renvoie l'état |
| `print()` | affiche les essais |
| `set_secret(mot)` | administration (tests) : nouvelle partie avec ce secret |

Après la fin, `game.win` vaut `"joueur"` (trouvé) ou `"personne"` (six
essais sans le trouver). Un coup refusé (pas une chaîne, mauvaise longueur,
majuscules, mot hors du dictionnaire, partie finie) ne change rien et
renvoie `False`, comme aux autres jeux du dépôt.

**L'état observable** ne contient jamais le secret. C'est l'historique, à
plat, en 60 cases : 6 essais de 10 cases, une paire *lettre, réponse* par
lettre (case `10 × essai + 2 × i` : la `i`-ième lettre proposée ; la case
suivante : sa réponse), et `.` pour les essais pas encore joués. Pourquoi
cette forme : une liste de cases, comme les plateaux des autres jeux, sans
structure propre aux mots (pas de chaîne de 5 lettres ni de liste de
listes) ; chaque lettre est **à côté** de sa réponse, ce qui garde ensemble
ce qui va ensemble ; et le nombre d'essais restants se lit aux cases vides,
sans compteur à part. Deux secrets qui donnent les mêmes réponses donnent
exactement le même état (vérifié par les tests).

**Professeur** — `Games/ProfesseurMotMystere.py`,
`professeur_mot_mystere_play(game)`. Il ne lit pas le secret : il ne voit
que l'état et le dictionnaire (les tests le font jouer à travers une
« vitre » qui ne montre que `get_game_state`, `get_moves`, `play` et `win`).
Sa règle, déterministe : garder les mots **compatibles** (ceux qui, s'ils
étaient le secret, auraient donné chaque réponse reçue), puis proposer celui
qui **partage le plus** les mots restants (dont la réponse prendrait le plus
de formes différentes selon le secret ; à égalité, le premier dans l'ordre
alphabétique). Il ne propose que des mots encore possibles. Premier essai :
`tenir`. Sur les 405 secrets du dictionnaire (`python -m
Games.ProfesseurMotMystere`) : **405 trouvés (100 %), 2,99 essais en
moyenne** (1 en 1 essai, 93 en 2, 229 en 3, 75 en 4, 6 en 5, 1 en 6). À
titre de comparaison, la règle simple « le premier mot compatible » en
rate un et en met 3,36.

**Notions nouvelles** : le domaine des mots (des actions qui sont des
chaînes, tirées d'un vocabulaire de plusieurs centaines de valeurs) ; une
information **cachée** qui ne se voit jamais, seulement ses conséquences ;
**déduire** à partir d'indices (chaque réponse élimine des mondes
possibles) ; des **lettres qui reviennent** (une même valeur à plusieurs
endroits, que la réponse ne compte qu'une fois). Les deux fins (gagnée,
perdue) ont le même signal (`play` renvoie `True`) et ne se distinguent que
par `win`.

Exemple : [`res/exampleMotMystere.py`](../res/exampleMotMystere.py), graine
10 : `porte` (`--~-=`), `livre` (`---==`), `barre` (`~~~==`), puis `arbre`,
trouvé au quatrième essai (`# end player joueur` : la partie est gagnée).

**Ce que la mère en comprend déjà** (`python -m xander
res/exampleMotMystere.py`, sans rien changer à `xander/`) : un seul joueur,
deux actions par tour (`get_game_state -> play`), l'annulation (`back`),
l'état (un tableau de 60 cases) et la fin (`play` renvoie `True`, la partie
est gagnée). L'effet de `play` reste **inconnu** : les quatre appels sont
« non compris ». Chaque proposition change les **10 cases** de l'essai
suivant (0 à 9, puis 10 à 19…), et aucune de ses briques ne décrit « le
bloc suivant de cases vides » : `premiere_de(…, valant('.'))` ne donne
qu'une case, `valant('.')` toutes les cases vides, et une portée n'est
observée que pour une action qui change **une seule** case.

**Où l'éducation bloque** (`--son motmystere --parties 30`) : dans
`Solo.__init__` (`xander/un_joueur.py`), avant la première partie, sur
« aucun programme n'explique ce que change l'action, même avec ce que la
mère a vu dans le labo ». Elle a pourtant exploré : ses actions sont les
quatre mots de l'exemple (pour des valeurs qui ne sont ni des entiers ni
des booléens, elle ne connaît que celles de l'exemple), 44 positions, et
chaque coup change le bloc suivant de 10 cases.

**Ce qui lui manquerait**, d'après ce qu'on voit ici : décrire **où** agit
une action qui remplit plusieurs cases d'un coup (le prochain bloc libre) ;
décrire **ce qu'elle écrit** (les lettres de l'argument, une sur deux) ;
connaître le **vocabulaire** des actions au-delà de l'exemple ; distinguer
**deux fins** au même signal (gagnée, perdue) ; et surtout raisonner sur
un **état caché**. Dans son labo, toutes les parties ont le même secret
(l'`init` de l'exemple est rejoué tel quel, et `back` revient en arrière sans
changer de secret) : en mesurant la valeur des coups avec `back`, elle
apprendrait par cœur le secret de la graine 10, pas à déduire. Il lui
faudrait des parties à secrets différents et une façon de juger un coup
sur l'ensemble des secrets encore possibles (le professeur le fait : il
garde les mots compatibles avec les réponses).

## Morpion à trois joueurs — `Games/Morpion3.py`

Jeu d'entraînement pour apprendre qu'un adversaire n'est pas forcément
« l'autre ». Trois joueurs, `X`, `O` et `Z`, posent chacun leur pion à tour
de rôle (`X -> O -> Z -> X`, à partir du premier joueur choisi) sur un
plateau 4 × 4. Le premier qui aligne **trois** pions (ligne, colonne ou
diagonale : 24 fenêtres) gagne ; plateau plein sans alignement : nul.

**Interface** : celle du Morpion. L'état est une liste plate de 16 cases ;
une case libre contient son indice (`"0"`…`"15"`), une case jouée `"X"`,
`"O"` ou `"Z"`. `init(start_player)` accepte `"X"`, `"O"`, `"Z"` ou `"R"`
(au hasard parmi les trois). `play(i)` renvoie `False` pour un coup refusé
(case occupée, hors plateau, pas un entier, un booléen, partie finie) sans
rien changer, `True` quand la partie se termine, sinon le plateau. `back()`
annule le dernier coup et rend la main à celui qui l'avait joué.
`get_turn()`, `get_game_state()` (relance une partie finie), `get_moves()`,
`set_game_state(plateau, joueur)` et `win` (`"X"`, `"O"`, `"Z"` ou `"D"`)
suivent les autres jeux. `Morpion3(size, k)` change la taille et
l'alignement.

**Pourquoi 4 × 4 et trois alignés.** À trois, une double menace ne suffit
plus : chacun des deux autres peut boucher une case avant que le menaçant
rejoue. Mesures (le premier joueur est `X`) :

| | 4 × 4, k = 3 | 5 × 5, k = 3 |
|---|---|---|
| 3 joueurs au hasard (20 000 parties) : X / O / Z / nul | 40 % / 25 % / 22 % / 14 % | 40 % / 32 % / 27 % / 1 % |
| 3 professeurs, plateau vide | nul (quel que soit le premier) | X gagne en 10 coups |
| 3 professeurs, premier coup au hasard | 300 parties : X 5 %, O 7 %, nul 87 % | 30 parties : O gagne 29 fois |

Le 5 × 5 est dégénéré : presque jamais de nul, et dès que le premier coup
change, la partie se décide d'elle-même (O gagne). Le 4 × 4 ne l'est pas :
le premier joueur ne gagne pas d'office (nul en jeu du professeur), les
parties ne sont pas toujours nulles (avec deux premiers coups au hasard,
300 parties : X 13 %, Z 6 %, O 1 %, nul 80 % ; au hasard, 86 % de parties
gagnées), et les trois places gagnent.

**Professeur** : `Games/MaxnMorpion3.py`, fonction
`maxn_morpion3_play(game)`. Le minimax ne s'applique pas tel quel à trois :
il utilise **max^n**, où chaque position a une valeur par joueur et chacun
maximise la sienne. Victoire : `1000 + profondeur restante` pour le
gagnant, l'opposé pour les deux autres ; nul : 0 ; feuille : chaque fenêtre
qui ne contient que les pions d'un joueur lui rapporte 1 (un pion) ou 5
(deux), et sa note est `2 × ses points - ceux des deux autres`. Avant de
chercher, à chaque nœud : (1) gagner s'il le peut ; (2) boucher la case
gagnante du **suivant** ; (3) boucher celle du **troisième**, sans compter
sur le suivant pour le faire (max^n pur lui laisserait ce travail ; un
adversaire réel peut l'oublier). Sinon max^n explore un tour complet
(3 demi-coups). **Départage** : à valeur égale pour celui qui a le trait,
la première case dans un ordre fixe, des plus centrales (traversées par le
plus de fenêtres) aux bords, puis par indice. Il est déterministe et garde
ses calculs en mémoire : 0,6 ms par coup en moyenne sur 11 000 coups, 75 ms au
plus (le premier coup sur un plateau vide).

Force mesurée (300 parties par ligne, `X` commence) :

| Professeur en… | contre deux joueurs au hasard : gagne / nul / perd |
|---|---|
| X (premier) | 96 % / 3 % / 1 % |
| O (deuxième) | 90 % / 5 % / 5 % |
| Z (troisième) | 82 % / 10 % / 8 % |

Contre deux copies de lui-même, sans hasard, la partie est nulle quelle que
soit sa place. Il n'est pas imbattable : seul contre deux, il ne peut pas
parer toutes les menaces d'un joueur que le troisième laisse faire (le
hasard ne pare pas), et une recherche plus profonde n'aide pas contre le
hasard (max^n suppose que les autres jouent bien). Comparé pendant la mise
au point : 2 demi-coups, ou une variante « paranoïaque » (les deux autres
jouent ensemble contre moi), donnent à peu près le même résultat contre
des copies ; 4 et 5 demi-coups sont 6 à 20 fois plus lents sans gain.

Exemple de partie : [`res/exampleMorpion3.py`](../res/exampleMorpion3.py),
12 coups, quatre tours complets ; Z gagne sur la diagonale 6-9-12.

**Notions nouvelles** : plus de deux joueurs ; deux adversaires différents
(le suivant, qu'il faut parer tout de suite, et le troisième, que le
suivant peut parer ou non) ; un tour qui revient tous les trois coups ; un
plateau plus grand que les fenêtres gagnantes (un même motif apparaît à
plusieurs endroits).

**Ce que la mère en comprend** (`python -m xander res/exampleMorpion3.py`) :
`Joueurs (3) : X, O, Z`, un tour de deux appels (`get_game_state -> play`),
l'annulation, le gagnant (`Z`), et l'action : `changees = case(arg0)` (la
case jouée), `valant(arg0)`. À l'éducation, elle lit dans l'exemple
**l'ordre des joueurs** (le cycle X, O, Z) : le joueur d'un coup est sa place
dans le cycle (voir `docs/architecture.md`, § 6 et § 8). Rien n'est propre à
ce jeu dans `xander/`.

**Éducation** (`--prof Games.MaxnMorpion3:maxn_morpion3_play --son morpion3
--parties 200`, graine 0, mesurée avant la fusion des actions à plusieurs
arguments ; après la fusion, les 80 premières parties suivent le même
rythme, la mesure complète n'a pas été refaite) :

- Leçon de l'exemple : pions `X`, `O`, `Z` et le motif `[6, 9, 12]` par
  contre-épreuve. Dans les toutes premières parties (moins de 10), motifs
  décalés puis symétries : les
  **24 alignements** et les **8 symétries du carré**.
- Règles qu'elle construit seule (dès les 30 premières parties, inchangées
  ensuite), dans l'ordre de priorité :
  `gagne(moi)` (gagner) >
  `Non(AuMoins(1, lui, gagne(lui)))` (parer le suivant) >
  `concept_1(lui)` (la même brique vue du côté du suivant : parer **le 2e
  après moi**) >
  `AuMoins(1, moi, gagne(moi))` (se créer une menace). La parade du
  troisième vient d'une composition : personne ne lui a dit qu'il existait.
- 337 erreurs en 200 parties (par tranche de 10 : 53, 36, 9, 7, 24, 11, 16,
  24, 19, 11, 12, 15, 26, 14, 10, 20, 5, 17, 6, 2). Contre le professeur, 29
  en tout (7 en X, 11 en O, 11 en Z) ; les autres contre le hasard et
  l'adversaire mixte, qui montrent sans cesse des positions nouvelles.
- **304 souvenirs** restants, dont 2 petits motifs seulement : surtout des
  ouvertures (« X a joué là, jouer ici ») et des positions tactiques que les
  quatre règles n'expliquent pas. La courbe ne descend plus vraiment après 30
  parties : il lui manque une règle plus fine (une fourchette à trois, où
  chacun des deux autres peut boucher).
- 0 coup impossible (ni avant, ni après la 5e partie).
- Au plus **784 positions** regardées pour un coup (budget : 1 000).
- Durée : **1 717 s** (environ 29 minutes) pour 200 parties, dont deux tiers
  dans les refactors (`refactor_once` : `views` et `check` rejouent tous les
  cas, qui grossissent avec les souvenirs). C'est à la limite de temps d'un
  examen blanc (environ 30 minutes, mesure comprise).

**Mesure** (protocole de `xander/examen.py` : 10 graines par place et par
sorte d'adversaires, chaque situation jouée par le fils puis par le
professeur ; V victoire, N nul, D défaite) :

| Place | Contre 2 professeurs : fils / professeur | Contre 2 joueurs au hasard : fils / professeur |
|---|---|---|
| X (premier) | N10 / N10 | V10 / V9 N1 |
| O (deuxième) | N10 / N10 | V10 / V9 D1 |
| Z (troisième) | N10 / N10 | V9 N1 / V9 N1 |

Le fils tient les **60 situations sur 60** (score relatif 1,00), au plus 784
positions regardées par coup pendant la mesure. Après 30 parties seulement,
59 sur 60 (en Z contre le hasard, une défaite là où le professeur fait nul).
Ce n'est pas un examen blanc : la partie, le professeur et l'exemple ont
servi au développement.

**Ce qui manque encore** : des règles qui remplacent les souvenirs
d'ouverture (petits motifs qui tiennent rarement sur 16 cases) et une
tactique propre à trois (fourchette qui résiste aux deux autres) ; des
variantes qui revoient aussi le coup de l'avant-dernier joueur ; et le temps
(les refactors coûtent cher quand les souvenirs s'accumulent).
