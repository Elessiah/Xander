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

**Ce que la mère en comprend aujourd'hui** (`python -m xander
res/exampleNim.py`) : deux joueurs, un tour `get_game_state -> play`, la
variable `tas` (tableau de 3), et `play : changees = case(arg0)` : le
premier argument désigne le tas qui change. Elle ne décrit pas **la valeur
écrite** (l'ancienne taille moins `arg1`) : avec `--prof`, l'éducation
s'arrête sur « la mère ne sait pas décrire la valeur que l'action écrit ».
Le dernier coup (qui renvoie `True`) reste « non compris », comme dans les
autres exemples. Même chose pour la variante misère.

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

**Ce que la mère en comprend déjà** (`python -m xander
res/exampleCompteEstBon.py`, sans rien changer à `xander/`) : un seul
joueur, des tours `get_game_state -> play`, l'annulation, le gagnant, la
variable `etat` (tableau de 5) que lit `get_game_state` et que modifie
`play`. Elle décrit `play` par **les cases qui changent** :
`changees = union(case(arg0), case(arg1))`, les places des deux nombres
combinés. Elle ne dit pas **ce qu'elles deviennent** (aucun programme
n'explique la valeur nouvelle : un calcul entre deux cases, choisi par un
argument), ni le rôle de `arg2`. Une deuxième hypothèse,
`union(case(arg2), case(3))`, est une coïncidence de l'exemple (seulement
deux coups qui continuent) ; les essais du labo la réfutent.

**Où l'éducation bloque** (`--son`, `--parties 30`) : dans
`Solo.__init__` (`xander/un_joueur.py`), avec « la mère ne sait pas dire
quand une action peut être jouée ». Avant cela, `discover_actions`
(`xander/education.py`) ne cherche que des actions **à un argument** : elle
joue `play(3)`, `play(4)`… que le jeu refuse tous, et ne trouve **aucune**
action. Son exploration ne joue donc rien, les essais de `test_effects`
(avec trois arguments pris dans l'exemple) se font refuser, et pour une
action décrite par ses cases changées, elle ne sait dire que « toujours
permise » quand elle n'a vu aucun refus. Il lui manquerait, dans l'ordre :
des actions à plusieurs arguments (les découvrir, les rejouer, les écrire
dans le fils) ; décrire une **valeur calculée** à partir de deux cases
(`case(arg0) + case(arg1)`, l'opération choisie par un argument) ; une
liberté qui dépend des valeurs (une case vide, une division qui tombe
juste) ; deux fins distinctes (le `True` de la victoire et la position sans
coup possible de la défaite) ; enfin, pour être bonne, reconnaître des
configurations au lieu d'essayer les 48 coups de chaque position.

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
