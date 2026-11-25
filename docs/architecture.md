# Architecture de la logique mère

```text
 res/exampleX.py
      │  parser.py          lecture des sections, des appels et des types
      ▼
 ParsedExample  ── variables, fonctions horodatées, joueurs, gagnant
      │  rebuilder.py       réécriture en script + exécution dans un sous-processus
      ▼
 observations   ── {time: valeur renvoyée}
      │  analyzer.py        comparaison avant / après chaque coup (des cas)
      │  effets.py          la mère construit le programme qui explique les cas
      ▼
 AnalysisReport ── opérations par fonction, getters / setters par variable
      │  game_model.py      synthèse : joueurs, déroulé d'un tour, annulation
      ▼
 GameModel
      │  education.py       la mère élève le fils : parties, souvenirs, refactors
      │  lab.py             (une vraie partie qu'elle rejoue et défait avec back)
      ▼
      │  concepts.py        les briques : arbres de concepts que la mère construit
      │  son_writer.py      la mère écrit (et réécrit) le code du fils
      ▼
 output/sons/<nom>.py ── fichier autonome : perception, règles apprises, squelette
```

Point d'entrée : `Mother().learn(chemin)` renvoie un `GameModel` ;
`python -m xander chemin` l'affiche.

## 1. Lecture de l'exemple — `xander/parser.py`

`ExampleParser` lit le fichier ligne par ligne. Les en-têtes `# …` changent de
section ; chaque ligne de code est analysée avec le module `ast` de Python
(robuste aux chaînes, virgules et `#` dans les arguments), et le commentaire de
fin de ligne avec `tokenize`.

Chaque appel devient une `Function` (voir `xander/model.py`) :

| Champ | Exemple pour `board = game.play(4)  # array 9` |
|---|---|
| `name` | `"game.play"` |
| `parameters` | `["4"]` (texte source) |
| `arguments` | `[4]` (valeur, si c'est un littéral) |
| `return_value` | `Variable(kind="array", size=9, name="board")` |
| `time` | position chronologique |
| `kind` | `INOUT` — déduit : paramètres ? valeur de retour ? |

| `FunctionKind` | Paramètres | Retour | Exemple |
|---|---|---|---|
| `NONE` | non | non | `game.reset()` |
| `OUTPUT` (getter) | non | oui | `board = game.get_game_state()` |
| `INPUT` (setter) | oui | non | `game.play(4)` |
| `INOUT` | oui | oui | `board = game.play(4)` |

## 2. Rejeu — `xander/rebuilder.py`

`build_pool_test` réécrit l'exemple en un script qui exécute tous les appels
dans l'ordre chronologique et imprime chaque valeur renvoyée sous la forme
`@@xander <time> <variable> <repr(valeur)>`. Le script est lancé avec
l'interpréteur courant, depuis la racine du dépôt ; seules les lignes marquées
sont lues (le jeu peut afficher ce qu'il veut ; l'entrée standard est fermée,
un `input()` échoue). Le rejeu est interrompu après 30 s. `--keep` conserve le script
dans `output/poolTest.py` pour le déboguer.

## 3. Analyse — `xander/analyzer.py`

Pour chaque appel qui agit (`INPUT` / `INOUT`) on cherche des couples
*(valeur avant, valeur après)* :

- **après** : la valeur renvoyée par l'appel lui-même (s'il est `INOUT`),
  puis celles des getters appelés juste après lui ;
- **avant** : la dernière valeur observée de la même variable avant l'appel.

Chaque couple est un **cas** (`xander/effets.py`). Un couple où il n'y a rien
à comparer n'est pas un cas : le dernier coup renvoie un booléen au lieu du
plateau, ou rien n'a changé.

**La mère construit la description de l'action.** Il n'y a plus d'hypothèses
nommées à la main. Comme pour les concepts (§ 7), elle énumère par taille
croissante de petits programmes qui prédisent, à partir de la valeur d'avant
et des arguments :

- pour un nombre, la nouvelle valeur : `apres = …` ;
- pour un tableau, l'ensemble des cases qui ont changé : `changees = …`.

Les programmes s'écrivent avec des feuilles (`arg0`, `arg1`…, `avant` et des
**constantes mesurées** sur les cas) et sept opérations : `plus`, `moins`,
`case(x)` (la case d'indice *x*), `valant(x)` (les cases dont la valeur est
*x*), `union`, `portee(x)` (les cases que la mère a vu l'action *x* remplir,
dans l'ordre déduit : une **observation** du labo) et
`premiere_de(s, e)` (la première case de la suite *s* qui est dans
l'ensemble *e*). Pour chaque
fonction et chaque variable, elle garde les plus petits programmes qui
expliquent **tous** les cas, avec au moins deux cas distincts (un seul cas peut
être une coïncidence). Deux programmes qui donnent les mêmes valeurs sur tous
les cas sont confondus et on garde le plus petit ; à taille égale, ils
coexistent.

Elle retrouve ainsi seule les anciennes hypothèses :

| Ce qu'elle trouve | Ancienne étiquette |
|---|---|
| `changees = case(arg0)` | `SINGLE_TARGET_INDEX` |
| `changees = valant(arg0)` | `SINGLE_TARGET_NAME` |
| `changees = union(case(arg0), case(arg1))` | `SRC_DEST_TARGET_INDEX` |
| `changees = union(valant(arg0), valant(arg1))` | `SRC_DEST_TARGET_NAME` |
| `apres = moins(avant, arg0)` / `plus(arg0, avant)` / `arg0` | `QUANTITY_RM` / `_ADD` / `_SET` |

Elle trouve aussi des combinaisons qu'aucune étiquette ne décrivait
(`apres = moins(avant, plus(arg0, arg1))`).

**La gravité, une composition.** Au Puissance 4, `play(3)` remplit la case 3,
puis 10, puis 17 : la case changée n'est l'argument que sur la rangée du bas.
La mère ne connaît ni la gravité ni la forme du plateau, et l'Analyzer seul
n'explique pas cette action. Dans son labo (§ 6), la mère joue des parties
et note, pour chaque action, les cases qu'elle l'a vue remplir : la
**portée** de `play(3)`. L'ordre se déduit des positions
(`portees_observees`) : la case *c* vient avant *d* si l'action a rempli *c*
alors que *d* était encore dans le même état que *c*. Au Puissance 4, `play(3)`
n'a rempli la case 10 qu'une fois la case 3 occupée : la portée est
3, 10, 17, 24, 31, 38. Si les observations se contredisent (un cycle), il n'y a
pas de suite, donc pas de portée. Elle remarque aussi les **constantes**
des cas (`constantes`) : les décalages « case changée − argument » et les
valeurs qu'avaient les cases changées (ici `' '`, la case vide). Avec elles,
le plus petit programme qui explique tous les coups de l'exemple est

    changees = premiere_de(portee(arg0), valant(' '))

« la première case vide de ce que remplit l'action ». Rien n'y parle de
colonnes ni de pas : l'ordre vient de ce qu'elle a vu. Le même programme
décrit une gravité vers le haut (la portée va de 38 à 3), un tube ou une
pile.

Un exemple qui ne joue que sur la rangée du bas se laisse expliquer par
`case(arg0)`, plus petit. Les coups vus en explorant l'écartent d'emblée ;
et si la mère n'avait que l'exemple, le labo le réfuterait dès qu'elle joue
deux fois dans la même colonne, et elle apprendrait du contre-exemple
jusqu'à la gravité (§ 6).

**La valeur écrite.** La case jouée reçoit une valeur que la mère décrit
aussi à partir de ce qu'elle a vu (`ecriture`) : une constante (toujours la
même), sinon un argument de l'action, sinon une valeur propre à chaque joueur,
différente d'un joueur à l'autre (au Morpion et au Puissance 4, le pion). Si
aucune ne convient, elle sait qu'elle n'a pas compris ce que l'action écrit.

**La case libre.** Quand une case peut-elle être jouée ? La mère ne suppose
pas « une case sans pion » : elle le déduit des coups joués et des coups
**refusés** qu'elle a notés en explorant (`liberte`). Elle essaie, de la plus
simple à la moins simple : *toujours* (le programme suffit, il n'annonce
aucune case pour un coup refusé : au Puissance 4, une colonne pleine), *la
case valait v* (toujours la même valeur avant d'être remplie), *la case a
encore sa valeur du début* (au Morpion, la case *n* contient « n » tant que
personne n'y a joué). Elle garde la première que vérifient toutes les cases
remplies et aucune des cases annoncées pour un coup refusé.

Au Morpion, `case(arg0)` et
`valant(arg0)` coexistent (la case *n* contient le texte `"n"`) : l'exemple
ne les départage pas, le labo s'en charge (§ 6). Les appels dont aucun cas
n'est expliqué sont listés dans `AnalysisReport.unknown_calls`.

**Une action à plusieurs arguments.** Au Nim, `play(tas, nombre)` ; à
Hanoï, `play(depart, arrivee)` ; au Compte est bon, `play(i, j, op)`. Les
programmes ont déjà `arg0`, `arg1`… ; ce qui change :

- **les portées se rangent par argument** (`portees_observees`). La clé
  `(k, x)` donne les cases que l'action a remplies quand son argument `k`
  valait `x`, dans l'ordre déduit comme au Puissance 4, et `portee(argk)` la
  lit. À Hanoï, `(0, 0)` (partir du piquet 0) vaut `[0, 1, 2]` : le petit
  disque part avant le moyen, le moyen avant le grand. La case changée est
  alors `premiere_de(portee(arg0), valant(arg0))`, « le premier disque du
  piquet de départ » (taille 5), sans que la mère sache ce qu'est un disque ;
- **les cases écrites** (`effets.ecrites`, forme `ecrites`). Au Compte est
  bon, 5 × 1 laisse 5 à sa place pendant que l'autre place se vide : la case
  est écrite mais ne change pas. Quand aucun programme ne donne exactement
  les cases changées, la mère cherche le plus petit qui les **contient** dans
  tous les cas et les donne exactement dans au moins la moitié (sinon
  « toutes les cases » expliquerait tout). C'est une hypothèse plus faible,
  que la description de la valeur écrite doit confirmer : avec elle, l'état
  d'après est prévu en entier.

**Ce que l'action écrit : un petit programme** (`effets.ecritures`). La
description `changees = …` dit **où**. Pour dire **quoi**, la mère découpe la
description en **parties** (les termes réunis par `union` : au Compte est
bon, la place du résultat et celle qui se vide) et décrit la valeur que
reçoit la case de chaque partie, de la plus simple à la moins simple :
une constante, un argument, une valeur propre au joueur (comme avant), puis
un **petit programme** construit comme les autres, par taille croissante et
vérifié sur tous les cas (au moins deux), avec les arguments, `ici` (la
valeur qu'avait la case), `val(x)` (la valeur qu'avait la case *x*) et les
quatre opérations `plus`, `moins`, `fois`, `divise` (une division d'entiers
n'a de sens que si elle tombe juste). Enfin, **selon un argument** : si un
argument prend peu de valeurs (au plus 8), elle sépare les cas selon sa
valeur et décrit chaque groupe seul ; un groupe vu une seule fois n'est pas
décrit (elle ne prévoit rien pour cette valeur). Elle trouve :

| Jeu | Où | Ce qu'elle écrit |
|---|---|---|
| Nim | `case(arg0)` | `moins(ici, arg1)` : le tas perd ce qu'on y prend |
| Hanoï | `premiere_de(portee(arg0), valant(arg0))` | `arg1` : le piquet d'arrivée |
| Compte est bon | `case(arg0)` | selon `arg2` : `plus`, `moins`, `fois`, `divise(ici, val(arg1))` |
| | `case(arg1)` | `0` : la place se vide |

Avec où et quoi, elle **prévoit l'état d'après en entier** (`effets.prevoir`).
Un coup dont elle ne prévoit rien (une partie sans case, une division qui ne
tombe pas juste, deux parties sur la même case) ou qui ne changerait rien
n'est pas un coup.

**Quand un coup est permis, selon les valeurs** (`effets.liberte_valeurs`).
Le Nim refuse de prendre plus qu'il n'y a ; Hanoï, de poser sur un plus
petit ; le Compte est bon, de combiner une place vide ou de donner un
résultat qui n'est pas positif. La méthode est celle de la case libre :
déduire des coups joués et refusés, de la description la plus simple à la
moins simple. Un coup refusé dont elle ne prévoit rien est déjà expliqué ;
les autres doivent être écartés par une **condition**, qui reste vraie pour
tous les coups joués. Une condition se construit comme les programmes : des
**comparaisons** (`inf` : plus petit, `egal`, éventuellement niées) entre
un terme (au plus 5 nœuds, avec `valant`, `portee`, `premiere_de`, `val`,
`plus`, `moins`) et une **feuille** (un argument, `ici`, `ecrit` et
`cellule` de chaque partie, une borne mesurée sur les coups joués) ; une
seule si elle suffit, sinon deux à la fois. Une case seule se compare par
son indice ; une comparaison qui n'a pas de sens est fausse.

| Jeu | Condition trouvée | Lecture |
|---|---|---|
| Nim | `non inf(ici, arg1)` | le tas a au moins ce qu'on prend |
| Hanoï | `non inf(premiere_de(portee(arg0), valant(arg1)), cellule)` | aucun disque du piquet d'arrivée ne vient avant celui qu'on déplace : jamais sur un plus petit |
| Compte est bon | `inf(ecrit1, ici) et inf(ecrit1, ecrit)` | la place n'était pas vide (0 < ce qu'elle valait) et le résultat est positif |

Avec peu de coups refusés, une coïncidence de même taille peut gagner (au
Compte est bon, graine 0 : `inf(arg0, ici)`, « l'indice de la place est plus
petit que son nombre », vrai sur le seul tirage du labo). Si aucune
condition ne convient, la mère dit que la condition est hors de portée de
son langage. Ce qu'elle a vérifié est ce que le fils exécute : les briques
sont recopiées dans le fils en Python (`effets.AIDES_SOURCE`,
`source_prevision`) et un test compare les deux prévisions sur tous les
coups vus.

Ce qui est encore fourni à la main : les quatre formes (`apres`, `changees`,
`ecrites`, `suite` pour un état qui défile, ci-dessous), les
feuilles et les sortes de constantes, les sept opérations (dont
`premiere_de`, une brique d'ordre générale), la façon de déduire l'ordre
d'une portée (une case remplie alors qu'une autre était dans le même état
vient avant elle) et son rangement par argument, les descriptions de la
valeur écrite (constante, argument, joueur, programme, selon un argument) et
leurs briques (`ici`, `val`, les quatre opérations), les trois descriptions
de la case libre (pour un nombre, les quatre bornes d'une action permise,
§ 6) et le langage des conditions (`inf`, `egal`, la négation, un terme
contre une feuille, au plus deux comparaisons), la taille maximale des
programmes (5 nœuds) et le minimum de deux cas ; pour un défilement, les
trois sortes d'exceptions (bord, mobile, cases fixes) et la profondeur de
l'entrée par le bord (2 |*d*|).

Pourquoi ces briques : `ici`, `val` et `moins` servent au Nim et au Compte
est bon ; `plus` et `moins` décrivaient déjà les Allumettes ; `fois` est
aussi une brique des problèmes « entrée → sortie » (§ 10, `les-carres`,
`le-carre`) ; `divise`, l'inverse de `fois`, n'est justifiée que par le
Compte est bon (l'équipement « nombre » de naissance, dit tel quel).
« Selon un argument » n'est justifié, pour la valeur écrite, que par le
Compte est bon (`op` choisit l'opération) ; c'est la même idée qu'une table
apprise par valeur d'argument, que la mère a déjà : la portée de chaque
action (Puissance 4) et les déplacements du mobile par argument (Jumper).
Les comparaisons servent au Nim, à Hanoï et au Compte est bon.

**Un état qui défile : l'état d'avant, décalé.** À Jumper, chaque coup fait
avancer tout le décor d'une case : beaucoup de cases changent, et aucun
ensemble de cases changées ne s'explique. Quand rien d'autre n'explique les
cas, la mère essaie une troisième forme, `suite = decale(avant, d)` (la case
*i* reçoit ce qui était en *i* + *d*). Le décalage *d* est une **constante
mesurée** sur les cas (celui qui explique la majorité des cases changées),
comme le décalage « chaque case + d » qu'elle essaie déjà sur ses motifs
(§ 7). La description est **partielle et le dit** : elle prévoit chaque
case, sauf celles qu'elle sait nommer (`effets.Defilement`) :

- **ce qui entre par le bord** : les |*d*| cases dont la source sort de
  l'état, et les |*d*| suivantes, où un objet qui entre a pu apparaître d'un
  coup (à Jumper, un obstacle naît en 39 et se montre en 38). Imprévisible :
  elle ne voit pas au-delà du bord ;
- **le mobile** : une valeur présente exactement une fois dans chaque état et
  qui ne suit pas le décalage (un curseur, un pion, un personnage : à Jumper,
  `*`). Ni sa place suivante ni ce qu'il cache ne sont prévus. Elle note ses
  déplacements par argument : `False -> [-40, 0, 40] ; True -> [-40]`. Le même
  argument l'a fait monter, rester ou descendre : **ce qui décide est caché**
  (l'élan du saut), et elle l'écrit au lieu de faire semblant ;
- **les cases fixes** : jamais changées, et que le décalage contredirait (à
  Jumper, la case 159, en fin de rangée : la mère ne connaît pas les rangées).

Partout ailleurs, la prédiction doit être exacte dans tous les cas, et un cas
où rien n'a changé (l'écran défile sur du vide) s'explique aussi. Garde-fous :
le décalage doit expliquer au moins une case changée dans deux cas, plus de la
moitié des cases changées qu'il prévoit, et l'entrée par le bord ne doit pas
couvrir plus de la moitié de l'état (4 |*d*| ≤ *n*). Une exception qu'elle ne
sait pas nommer fait tomber la description. Pour Jumper :

    suite = decale(avant, 1) sauf : ce qui entre par le bord (cases 198 à 199),
    le mobile '*' (déplacements False -> [-40, 0, 40] ; True -> [-40] : ce qui
    les décide est caché), 1 case fixe [159]

Ce n'est pas taillé pour Jumper : un texte qui défile sur un panneau, une file
d'attente au guichet (chacun avance d'une place, un nouveau arrive au bout,
test `test_queue`), un registre à décalage, une partition qui défile sous les
yeux d'un musicien (`Games/Partition.py` : `decale(avant, 1)` sauf la case 7).
Une action qui mélange l'état n'est expliquée par rien, et la mère le dit
(`tests/jeu_melange.py`).

**Getters / setters.** Enfin, chaque variable (identifiée par son nom) reçoit
la liste des fonctions qui la renvoient (getters) et de celles dont une
opération la modifie (setters).

## 4. Synthèse — `xander/game_model.py`

`GameModel` regroupe ce qu'un enfant devra savoir : la variable de jeu, la
fonction d'annulation, les variables observables, les joueurs et le **déroulé
d'un tour**. Les tours sont découpés quand le joueur change, ou, une fois que
le tour a agi, quand arrive un getter ou la fonction qui a ouvert le tour
(nécessaire pour les jeux à un joueur comme Jumper) ; on retient la longueur
de tour la plus fréquente.

## 5. Le laboratoire de la mère — `xander/lab.py`

Une vraie partie, créée en exécutant les sections `# include` et `# init` de
l'exemple. La mère y tient la liste des coups joués et l'état avant chaque
coup ; `goto(coups)` amène la partie à n'importe quelle suite de coups en
annulant (`back`) puis en rejouant. **C'est le seul endroit où `back` sert.**

Le professeur (un Minmax de `Games/`) joue à travers un espion (`Spy`) : la
mère voit quel coup il a choisi sans rien savoir de son fonctionnement.

**Coup joué, coup refusé.** Un coup est refusé quand rien n'a changé **et**
que l'action n'a pas renvoyé ce qu'elle renvoie d'habitude dans l'exemple
(au Morpion, `False` au lieu du plateau). Au début de Jumper, l'écran ne bouge
pas (aucun obstacle) : `play` renvoie l'écran, inchangé, et le coup a bien été
joué. Avant, le labo le prenait pour un refus et se désynchronisait du jeu.

## 6. L'éducation du fils — `xander/education.py`

0. **Mettre à l'épreuve la description de l'action.** Avant tout, la mère
   joue dans son labo des coups que l'exemple ne montrait pas : depuis les
   positions de l'exemple et de 8 parties au hasard, avec les valeurs vues
   dans les arguments de l'exemple. Elle joue d'abord les expériences
   **décisives** (les programmes restants n'annoncent pas tous la même
   chose), puis d'autres en partant des positions les plus proches du début,
   pour tenter de réfuter ce qui reste (40 coups en tout). Chaque coup accepté
   est un nouveau cas ; un programme qu'il contredit est abandonné.
   - Morpion : `case(arg0)` et `valant(arg0)` résistent à tout, ils sont
     **indiscernables** et la mère prend le premier.
   - Morpion à pions chiffrés (jeu d'essai des tests) : dès qu'un pion `"2"`
     est posé, jouer la case libre 2 ne change qu'une case, ce qui réfute
     `valant(arg0)`.
   - Puissance 4 joué sur la rangée du bas : l'indice de la case vaut la
     colonne, et l'Analyzer trouve `case(arg0)`. En jouant deux fois dans la
     même colonne, la mère le réfute.

   Avant les expériences, elle cherche **quelles actions existent** : elle ne
   suppose pas que ce sont des indices. Elle part des valeurs que l'exemple a
   passées à l'action et explore autour dans le labo : pour des entiers, tous
   ceux entre le plus petit et le plus grand vus, puis plus loin dans chaque
   sens tant que le jeu en accepte (« si 7 marche, et 8 ? »), jusqu'à deux refus
   de suite ; pour des booléens, les deux. Au Morpion, l'exemple joue 4, 5, 1, 2
   et 7 : elle trouve 0 à 8. L'adversaire « au hasard » joue parmi ces actions.
   **Une action à plusieurs arguments** s'explore argument par argument, en
   partant des valeurs vues **pour cet argument** : une valeur est permise si
   le jeu accepte au moins une action où elle figure, les autres arguments
   prenant les valeurs de l'exemple (au plus 50 combinaisons, pour ne pas
   exploser). Au Nim, l'exemple joue les tas 2, 1, 0 et les nombres 2, 4, 1 :
   elle trouve les tas 0 à 2 et les nombres 1 à 5 (6 est refusé, 7 aussi).
   Les actions sont alors les combinaisons que le jeu accepte à une position
   de l'exemple ; en explorant, elle essaie aussi les autres et garde celles
   qu'il accepte quelque part (au Nim, 12 sur 15 : le tas 0 n'a jamais 4
   objets ; à Hanoï, 6 sur 9 ; au Compte est bon, 36 sur 64). Une action est
   alors le **tuple** de ses arguments : le labo le joue tel quel, et
   souvenirs, petits motifs et règles retiennent l'action entière.
   Elle lit aussi dans l'exemple **l'ordre des joueurs** : ils jouent chacun
   leur tour, toujours dans le même ordre, un cycle (X, O, X, O… à deux ; X,
   O, Z, X, O, Z… à trois). C'est ce qui lui permet ensuite de reconnaître qui
   joue un coup : sa **place** dans le cycle, le numéro du coup modulo le
   nombre de joueurs (`Education.seat` ; à deux, la parité). Sinon (un joueur
   qui joue deux fois de suite, un ordre qui change), elle dit qu'elle ne sait
   pas encore éduquer de fils.

   Ensuite, elle **explore** : elle rejoue l'exemple, puis 8 parties où elle
   choisit d'abord les actions **surprenantes** (celles qui viennent de
   remplir une case qu'on ne leur avait jamais vu remplir), puis les moins
   jouées. Elle note aussi les coups refusés. Elle déduit de ce qu'elle a vu
   les **portées**, la valeur écrite et la case libre (§ 3), et cherche le programme sur les coups de l'exemple et ceux de
   l'exploration : c'est ainsi qu'elle comprend la gravité, sans les
   coïncidences de l'exemple seul. Quand le labo a
   tout réfuté, elle **apprend du contre-exemple** : les coups joués dans le
   labo deviennent des cas de plus, et elle cherche le plus petit programme
   qui les explique avec ceux de l'exemple (au plus 3 fois). Sur la rangée du
   bas, elle passe ainsi de `case(arg0)` à la gravité. Si rien n'explique les
   cas (une action qui mélange l'état), elle sait qu'elle n'a pas compris
   l'action.

   Quand elle prévoit l'état d'après en entier (une valeur écrite décrite par
   un programme, § 3), elle **met aussi à l'épreuve** ce qu'elle a compris de
   « quand un coup est permis » (`test_free`) : depuis les positions vues en
   explorant (les plus proches du début d'abord, chaque état une fois), elle
   joue chaque action et compare au jeu ce qu'elle prévoyait (au plus 600
   coups). Un coup qu'elle croyait permis et que le jeu refuse, ou l'inverse,
   devient une observation ; un coup joué qu'elle ne prévoyait pas lui fait
   revoir ses portées et sa description de la valeur écrite (au Compte est
   bon, les divisions vues donnaient toutes 1 : « écrire 1 » tombe dès que
   10 / 5 donne 2). Puis elle cherche de nouveau la condition. À Hanoï, sans
   cette épreuve, l'exploration seule donnait `non egal(val(0), arg1)` (« le
   petit disque n'est pas sur le piquet d'arrivée »), une coïncidence.
1. **Leçon de l'exemple.** La mère rejoue l'exemple, vérifie que l'action
   change bien les cases que prédit son programme, apprend quel pion pose
   chaque joueur, puis comprend pourquoi la partie finit (ci-dessous).
2. **Comprendre une fin de partie (contre-épreuve).** Pour chaque pion du
   joueur qui a fini la partie, la mère rejoue la partie en posant ce pion
   ailleurs. Si la partie ne s'arrête plus, le pion était nécessaire. Le
   dernier coup et les pions nécessaires forment un **motif** (au Morpion, un
   alignement). Une fin sans motif est un nul. Un pion inutile reste déplacé
   pour les tests suivants, et un pion déplacé est retesté à sa nouvelle
   place : si le dernier coup complétait deux alignements, la mère en garde
   un entier.
3. **Parties.** Le fils joue contre le professeur, contre un joueur au
   hasard et contre un adversaire « mixte » (une fois sur deux le coup du
   professeur), à chaque place tour à tour (une fois X, une fois O ; à trois,
   X, O puis Z) ; les autres places sont toutes tenues par cet adversaire.
   Si le jeu refuse un coup du fils, c'est
   un **coup impossible** : sa perception se trompe. La mère note le refus
   comme une observation du labo (rien n'a changé), réapprend quand une case
   peut être jouée, réécrit le fils, et la partie continue. Si elle ne
   comprend pas, elle s'arrête. **Règle de toute éducation** : après ses 5
   premières parties, un fils ne fait plus aucun coup impossible (un test le
   vérifie). Mieux vaut un fils qui apprend plus lentement qu'un fils qui
   gagne vite en trichant.
4. **Revue des décisions.** Pour chaque coup du fils, la mère demande son
   coup au professeur. S'il diffère, elle fait finir la partie au professeur
   de tous les côtés, après chacun des deux coups, et compare les deux issues
   **pour le fils** : la victoire de l'un est une défaite pour tous les
   autres, un nul vaut nul pour tous (`education.issue`). Si le coup du
   professeur mène à un meilleur résultat, c'est une **erreur**. Elle revoit
   aussi les **variantes** : avec `back`, elle essaie chaque autre coup du
   joueur qui a joué juste avant le fils (« et s'il avait joué là ? ») et
   revoit la réponse du fils.
5. **Corriger le cas.** Chaque erreur devient un **souvenir** (dans cette
   position, jouer le coup du professeur). Chaque position revue devient un
   **cas** : les cas sont les tests des refactors (une position bien jouée est
   un test de non-régression).
6. **Refactoriser.** Après chaque partie, la mère cherche le plus petit concept
   (section 8) vrai après le coup du professeur et faux après celui du fils
   dans **au moins deux** souvenirs. Elle l'essaie comme règle à chaque rang
   de priorité, du plus bas au plus haut. Le refactor est gardé si le fils
   joue encore bien dans **tous** les cas (vérifié dans le labo), si au moins
   deux souvenirs deviennent inutiles (ils sont oubliés) et si le fils reste
   dans son budget de réflexion. Le concept devient une **brique** pour les
   suivants. Enfin, elle retire les règles devenues inutiles (sans elles,
   tous les cas restent bien joués). Puis elle **réécrit le code du fils**.
7. **Motifs décalés, situations équivalentes** (section 7). Dès qu'elle
   comprend un nouveau motif, la mère l'essaie décalé partout, puis cherche
   les renumérotations des cases qui ne changent rien au jeu. Un souvenir
   vaut alors pour toutes les positions équivalentes.
8. **Petits motifs** (section 7). Après le refactor, chaque nouveau souvenir
   est réduit aux cases qui comptaient, puis essayé décalé. Le fils le
   reconnaît partout où cette petite configuration apparaît.

La mère part **sans aucun concept**. Au Morpion, en 200 parties (quelques
secondes) : les 8 alignements et les 8 symétries sont découverts, et elle
construit seule ses règles. Le chemin dépend des parties rencontrées. Par
exemple :

```text
gagne(moi)                                    j'ai gagné
concept_1 = AuMoins(1, moi, gagne(moi))       (brique) j'ai un coup gagnant : une menace
Non(Et(Non(gagne(moi)), concept_1(lui)))      j'ai gagné ou il n'a pas de menace : gagner ou parer
Non(AuMoins(1, lui, Et(concept_1(lui),        aucun de ses coups ne lui donne une menace
                       concept_2(lui))))      sans danger pour lui : contre-fourchette
```

Avec une autre graine (et `AuMoins(2, …)` permis), elle retrouve exactement
`gagner > parer > fourchette > contre_fourchette`, ou des combinaisons que
personne n'a écrites. Un test explore toutes les suites de coups adverses
possibles : le fils ne peut plus perdre.

| Ce qui est donné à la mère | Fils parfaits à 200 parties (10 graines) | Souvenirs restants |
| --- | --- | --- |
| `AuMoins` avec k = 1 ou 2, sans symétries | 5 (8 à 800) | 10 à 46 |
| k = 1 ou 2, symétries découvertes | 10 | 4 à 16 |
| k = 1 seulement (« il existe »), symétries | 9 (la 10e perd encore 2 suites à 800) | 9 à 30 |
| k = 1, 2 ou 3 | 1 sur 5 | 20 à 24 |
| **k = 1, symétries, petits motifs (par défaut)** | 10 (8 dès 100 parties) | 5 à 7 |

Lui donner moins (k = 1) marche presque aussi bien, deux fois plus vite : elle
exprime la fourchette autrement (« il ne peut pas me menacer sans danger »).
Lui donner plus (k jusqu'à 3) est pire : plus de concepts possibles, donc plus
de coïncidences validées sur peu de cas.

Avec les petits motifs, le fils fait environ 16 à 30 erreurs avant d'être
parfait, contre 24 à 44 sans eux. L'écart vient de l'ordre dans lequel la mère
apprend : en faisant finir des parties au professeur pour juger un motif, elle
découvre parfois un motif de fin, et ses règles changent plus tôt ou plus tard. L'éducation est aussi deux à trois fois plus rapide,
car il y a moins de cas à revoir.

### Un état qui n'est pas un tableau : une valeur (les Allumettes)

Aux Allumettes, l'état est un nombre (les allumettes qui restent) et la mère
décrit l'action par `apres = moins(avant, arg0)`. Rien de ce qui suit n'est
propre aux Allumettes : cela vaut pour tout état qui est un nombre (le
programme trouvé a la forme `apres` ; `Education.tableau` est faux).

- **La position porte le trait.** Un tableau garde la trace de qui a joué
  (les pions) ; une valeur, non. La position que voient la mère et le fils
  est `[valeur, trait]`, le trait étant le joueur qui doit jouer (sa place
  dans l'ordre des joueurs ; les joueurs sont ceux des sections de l'exemple,
  dans l'ordre où ils y jouent). `apres(etat, action, joueur)` donne
  `[valeur_apres(valeur, action), suivant(joueur)]`.
- **Les actions permises** se déduisent comme la case libre (§ 3), de ce
  qu'elle a vu (`effets.bornes`). Elle regarde les valeurs d'après des coups
  acceptés, y compris ceux qui ont fini la partie (le jeu ne montre pas leur
  valeur : elle la calcule avec son programme), et celles que son programme
  annonçait pour les coups refusés. Elle essaie, dans l'ordre, *toujours*,
  *pas sous m* (la plus petite valeur vue), *pas au-dessus de M* (la plus
  grande), *entre les deux*. Elle garde la première qui ne permet aucun coup
  refusé. En explorant, elle voit `play(3)` refusé à 2 allumettes : elle en
  tire `("au_moins", 0)`, on ne prend pas plus qu'il n'en reste.
- **Comprendre une fin (contre-épreuve).** Ici, la question est : « est-ce
  bien la valeur qui finit la partie ? ». La mère calcule la valeur finale
  de l'exemple (1). Dans les positions vues en explorant, elle cherche des
  coups qui y mènent depuis d'autres valeurs (son programme le lui dit) et
  les joue dans le labo. La partie doit finir à chaque fois, depuis au moins
  deux valeurs différentes (`CONTRE_EPREUVES` = 3 au plus), et aucun coup ne
  doit y avoir mené sans la finir. L'exemple dit qui a gagné : celui qui
  vient de jouer (`dernier`), l'autre (`trait`), ou personne (`nul`). Ce
  sont les `FINS`, d'où `gagne(etat, joueur)`. Une position de fin n'a plus
  d'action possible.
- **Une fin incomprise.** Prendre les 2 dernières allumettes mène à 0 : la
  partie finit, et celui qui a joué perd. L'exemple ne le montre pas. Si une
  partie finit à une valeur qu'elle n'a pas comprise, la mère ne sait pas qui
  l'a gagnée : elle le note et la compte nulle, comme une fin sans motif au
  Morpion. En pratique, ni le fils ni le professeur n'y vont.
- **Ce qui ne s'applique pas** : pions, motifs décalés, symétries et petits
  motifs parlent de cases. Un souvenir retient l'action ; sa clé est la
  valeur et qui a le trait (`7 M` : 7 allumettes, à moi de jouer).
- **Les concepts** (§ 8) n'ont pas changé : avec ces quatre notions, ils
  valent tels quels.

Résultats, avec 10 allumettes au départ, 30 parties et 10 graines (le chemin
est le même pour toutes : la 1re partie est contre le professeur) :

- Dans la 1re partie, le fils fait 3 erreurs (à 8, 7 et 4 allumettes, il
  prend 1 au lieu d'en laisser 5 ou 1). La mère en fait 3 souvenirs,
  remplacés aussitôt par une règle qu'elle construit :
  `Non(AuMoins(1, moi, Non(AuMoins(1, moi, gagne(moi)))))`, « jouer un coup
  après lequel, quoi que l'on joue ensuite, on peut encore finir à 1 ». Elle
  laisse 5, ou 1. Elle enchaîne deux fois *mes* coups là où l'on attendrait
  *ses* coups puis les miens. Aux Allumettes, les coups ne dépendent pas du
  joueur : c'est la même chose.
- Ensuite, plus aucune erreur : 0 souvenir, 0 coup impossible, au plus 22
  positions regardées pour un coup.
- Vérifié sur toutes les suites de coups adverses : le fils ne rate aucune
  position gagnable. En premier, il gagne toujours, contre le professeur
  aussi. En second, la partie est perdue d'avance (il reçoit 9 allumettes) :
  il ne perd que si l'adversaire joue parfaitement. Contre le professeur, il
  perd donc toujours ; contre le hasard, il perd 2 à 9 parties sur 100.
- À 10 allumettes, le bon premier coup (en prendre 1) est aussi le coup par
  défaut du squelette (la plus petite action) : la mère n'a pas eu à le
  corriger. Avec un exemple à 14 allumettes, elle garde en plus deux souvenirs
  par quantité (`12 M` → 3, `11 M` → 2).
- La période 4 n'est pas trouvée : « laisser 9 » demande de regarder trois
  coups plus loin, au-delà des deux niveaux de `AuMoins`. Élevé sur 10
  allumettes, le fils gagne toutes les parties gagnables de 5 à 10
  allumettes, et perd au-delà : il n'en a rien vu.

**Variante jouée jusqu'au bout** (`res/exampleAllumettesMisere.py` : la partie
finit à 0, celui qui prend la dernière perd). L'exemple finit sur le coup de O
et dit que X a gagné. La mère comprend `FINS = {0: "trait"}` : le dernier coup
fait perdre celui qui le joue, ce que le trait dans la position permet de
dire. Elle trouve `Non(AuMoins(1, lui, Non(gagne(moi))))`, « jouer un coup
après lequel aucun de ses coups ne me laisse sans victoire » (laisser 1), et
garde deux souvenirs pour laisser 5 (`8 M` → 3, `7 M` → 2). Elle fait 4
erreurs, toutes dans la 1re partie, et son fils ne rate aucune position
gagnable. La règle a une faiblesse : elle est vraie aussi après avoir pris la
dernière allumette (à 0, il n'a plus de coup, et « aucun de ses coups… » est
vrai sans rien dire). Le fils ne s'y trompe pas parce qu'il joue la plus
petite des actions que la règle propose (à 3 allumettes, prendre 2 plutôt que
3) ; les cas enregistrés le vérifient, la règle seule ne le garantit pas.

### Un tableau sans pions : le Nim

Au Morpion, la case jouée reçoit le pion du joueur : l'état dit qui a joué.
Au Nim, le tas reçoit `moins(ici, arg1)` : rien n'y dit qui a joué. Quand la
valeur écrite n'est pas « une valeur propre au joueur », la mère traite le
tableau **comme une valeur** (`Education.liste`, `tableau` est faux) : la
position est `[état, trait]` (l'état en tuple), elle prévoit l'état d'après
en entier (§ 3), les actions permises sont celles qu'elle prévoit, et la fin
est un **état** compris par contre-épreuve, avec qui il fait gagner. Rien
n'y est propre au Nim : c'est le même chemin que les Allumettes, avec un
état plus grand. Pour la contre-épreuve, si les positions de l'exploration
ne donnent pas deux états d'où un coup finit la partie, elle cherche un coup
plus loin (au plus 3 000 coups joués). Au Nim, elle trouve
`FINS = {(0, 0, 0): "dernier"}` (en misère, `"trait"`), vérifiée depuis
`(0, 0, 1)`, `(0, 0, 2)`, `(0, 1, 0)`…

Résultats (tas 3, 4, 5 ; 30 parties contre le professeur, le hasard et
l'adversaire mixte ; graines 0 à 2, moins de 2 s chacune) :

- 44 ou 45 erreurs, presque toutes dans les deux premières parties (avec
  les variantes de l'adversaire), la dernière à la partie 7, 16 ou 22 ;
  0 coup impossible après la partie 5. Avec 200 parties : 43 erreurs dans
  les 20 premières, 2 ensuite, plus rien après la 100e.
- La mère construit deux règles :
  `Non(AuMoins(1, moi, Non(AuMoins(1, moi, gagne(moi)))))` (« après mon
  coup, tout coup laisse un gain » : la règle des Allumettes) et
  `Non(AuMoins(1, moi, Non(AuMoins(1, moi, Non(gagne(moi))))))`, et garde
  30 ou 31 souvenirs. Au plus 301 positions regardées pour un coup.
- Le fils gagne en premier contre le professeur (la position de départ est
  gagnante), perd en second (elle est perdue pour lui), et bat le hasard
  196 à 200 fois sur 200.
- Sur les 102 positions gagnables à 3, 4 et 5 tas au plus, il rate le gain
  dans 16 ou 17 : la somme de Nim (le ou exclusif) est hors de portée de ses
  concepts, il ne sait que ce qu'il a vu et ce que deux coups d'avance lui
  montrent. Avec 200 parties, toujours 16 : le professeur rejoue les mêmes
  parties, le fils ne voit rien de neuf.
- Variante misère : `FINS = {(0, 0, 0): "trait"}`, 48 ou 49 erreurs, une
  règle (`Non(AuMoins(1, lui, Et(Non(gagne(moi)), concept_1(moi))))`, avec
  `concept_1 = Non(AuMoins(1, lui, Non(gagne(moi))))`), 35 ou 36 souvenirs,
  199 ou 200 victoires sur 200 contre le hasard, 17 ou 18 positions
  gagnables ratées sur 101.

### Plus de deux joueurs : le Morpion à trois

Rien n'y est propre au jeu : la mère lit dans l'exemple l'**ordre des
joueurs** (un cycle ; la parité était le cas à deux), et tout ce qui comptait
les coups `% 2` dépend de la place du joueur dans ce cycle
(`Education.seat`) : le pion posé, qui a joué, la place du fils, les
positions imaginées (`extra`, `grow`), la contre-épreuve (pions rangés par
place, échange avec le pion d'un autre joueur), les motifs décalés, la revue
et les variantes. Une position se lit de son côté : `M` moi, `A` le suivant,
`B` celui d'après (à deux, les mêmes clés, les mêmes souvenirs). Une fin vaut
pour chacun (`issue`) : victoire pour le gagnant, défaite pour tous les
autres, nul pour tous ; quand le professeur finit une partie pour juger un
coup, la mère compare les issues **pour le fils**. Les concepts disent
`suivant(joueur)` au lieu d'`adversaire(joueur)` et désignent un joueur par
sa place après moi (§ 8).

Au Morpion à trois (4 × 4, trois alignés), en 200 parties : les 24
alignements et les 8 symétries, quatre règles qu'elle construit (gagner,
parer le suivant, `concept_1(lui)` : la parade vue du côté du suivant, donc
parer le 2e après moi, et se créer une menace), 0 coup impossible, au plus
784 positions regardées par coup, et le fils fait au moins aussi bien que le
professeur à sa place dans les 60 situations de mesure. Restent 304
souvenirs (surtout des ouvertures) et environ 29 minutes d'éducation.
Détail et chiffres : `docs/jeux.md`.

### Un seul joueur : juger un coup par ce qui arrive — `xander/un_joueur.py`

Quand l'exemple ne montre qu'un joueur (Jumper, Partition), il n'y a ni
adversaire, ni professeur, ni « qui a gagné » : `gagne` et `suivant` n'ont
pas de sens. Les quatre notions restent celles des jeux à deux ; pour un
joueur seul, la mère apprend une autre notion, **le résultat d'une partie à
un joueur**, de l'exemple et du labo. Rien n'y est propre à un jeu.

- **La fin.** C'est le signal que l'exemple montre au dernier coup (l'action
  renvoie autre chose que d'habitude : `False` au lieu de l'écran). L'exemple
  dit ce qu'elle vaut : `# end` (personne n'a gagné) = **perdue** ;
  `# end player <nom>` = **gagnée** (un casse-tête résolu) ; `# end draw` =
  nulle. L'exemple de Jumper montre maintenant une partie complète : un saut à
  vide, un saut par-dessus le premier obstacle, puis le coureur touche le
  deuxième (73 coups).
- **La durée d'effet d'une action.** Depuis 30 positions vues en explorant,
  la mère joue chaque action puis toujours la plus petite, et compte les coups
  jusqu'à ce que les deux parties soient de nouveau dans le même état. Une
  mesure où l'une des deux finit ne dit rien. L'**horizon** est la plus longue
  durée vue, plus un coup. À Jumper, sauter ou non : les deux parties se
  rejoignent 7 coups plus tard (le coureur retombe) ; horizon 8. À Partition,
  une erreur finit la partie tout de suite : aucune mesure, horizon 1.
- **La valeur d'un coup** : combien de coups la partie dure au mieux après
  lui, sans dépasser l'horizon (une fin perdue vaut 0 ; une fin gagnée vaut
  plus que tout ce qui ne finit pas, et plus tôt vaut mieux). Elle la mesure
  **dans son labo, avec back** : elle essaie les suites de coups et revient en
  arrière ; deux actions qui mènent au même état ne sont essayées qu'une fois
  (à Jumper, en l'air, sauter ne fait rien : l'arbre reste petit). C'est son
  calcul à elle, pas celui du fils.

Déroulé, après la leçon de l'exemple (l'effet décrit prévoit chaque coup, la
partie finit au même coup) :

1. Le fils joue une partie dans le labo, un coup par tour, au plus 300 coups
   (au-delà, il a survécu).
2. **Revue.** Pour chaque décision, la valeur de chaque coup. Celle du coup du
   fils se lit souvent sur la partie : elle a duré au moins un horizon après
   lui. Un coup qui vaut moins qu'un autre est une **erreur** : faire une
   erreur, revenir en arrière, voir que l'autre action survit. Chaque position
   revue devient un **cas** (avec la valeur de chaque coup).
3. **Souvenir.** Dans cet état exact, jouer le meilleur coup (le plus petit à
   égalité). Un petit motif qui avait décidé un mauvais coup est oublié.
4. **Petit motif.** Quand deux souvenirs (au moins) demandent le même coup, la
   mère cherche les cases (avec leur valeur) qu'ils ont en commun et qui
   suffisent : 1 case, puis 2 (au plus 20 000 essais), sinon elle oublie les
   cases une à une. Un motif tient si, partout où il apparaît dans les cas, le
   coup est l'un des meilleurs, et s'il couvre au moins deux souvenirs. À
   taille égale, elle garde celui dont la présence annonce le mieux que le
   coup est nécessaire (la plus grande part des cas où il apparaît qui le
   confirment, comme le groupe témoin des jeux à deux). Puis elle vérifie que
   le fils, avec ce motif à la place des souvenirs, joue encore un des
   meilleurs coups dans **tous** les cas.

Le fils reconnaît : souvenir, sinon petit motif, sinon le coup par défaut (la
plus petite action). Il ne regarde aucune position à l'avance (`VUES` = 0),
n'utilise jamais `back`, et ne joue qu'un coup par tour.

**Partition** (`Games/Partition.py`, inventé pour cette étape : aucun état
caché, une erreur se paie tout de suite). 30 parties, 0,4 s : deux erreurs
(parties 1 et 2 : se taire sur une note), deux souvenirs remplacés par
`{0: 'o'} -> True` (« frapper quand une note arrive »), 0 souvenir restant.
Sur 50 morceaux jamais vus, plafonnés à 2 000 temps : 2,3 temps en moyenne à
la naissance, 2 000 sur 50 après l'éducation.

**Jumper.** 30 parties, 3 s. Deux erreurs : partie 1, coup 50 (premier
obstacle, valeurs `{False: 0, True: 8}`) ; partie 2, coup 73 (deuxième
obstacle). Deux souvenirs, remplacés après la 2e partie par
`{162: 'T'} -> True` : « sauter quand un obstacle est juste devant moi » (la
case 162 est celle qui suit le coureur au sol ; la mère ne sait pas ce qu'est
un obstacle ni un sol). Ensuite, plus aucune erreur : 300 coups par partie,
0 souvenir, 0 coup impossible, 0 position regardée à l'avance. Sur 50 graines
jamais vues (le labo n'a que la graine 0 de l'exemple), plafonnées à 2 000
coups : 51,7 coups en moyenne à la naissance (le fils ne saute jamais, il
meurt au premier obstacle), 2 000 sur 50 après l'éducation. Le chemin est le
même pour 5 graines d'exploration.

Ce qu'il faut savoir pour lire ce résultat :

- au moment de choisir, trois motifs d'une case tenaient sur les cas vus :
  `{162: 'T'}`, `{163: 'T'}` (sauter deux cases avant : juste aussi) et
  `{169: '-'}` (une coïncidence : dans les cas où sauter tue, un obstacle
  était justement en 169). C'est la règle de choix (la part des cas qui
  confirment : 2 sur 3, 2 sur 4, 2 sur 68) qui écarte la coïncidence ;
- sauter au dernier moment suffit à Jumper parce qu'un obstacle (3 cases au
  plus) est plus court qu'un saut (7 coups en l'air) : la mère n'a pas eu à
  apprendre une distance ;
- le coup par défaut (la plus petite action, `False`) est ici « ne rien
  faire ». Un jeu où l'action par défaut serait la mauvaise demanderait plus
  de souvenirs (non essayé) ;
- l'élan caché ne gêne pas la mère parce qu'elle juge dans le vrai jeu ; elle
  confond seulement deux positions identiques à l'écran (aucun cas vu).

**Des casse-têtes à plusieurs arguments : Hanoï et le Compte est bon.** Ce
qui change quand la mère prévoit l'état d'après en entier (§ 3) :

- **le fils ne propose que des coups permis** : `possibles` est écrit par la
  mère à partir de sa prévision (sinon, sans refus vu, toute action était
  permise ; avec des refus, elle s'arrêtait) ;
- **deux fins au même signal** (`Solo.understand_solo_end`). À Hanoï,
  `play` renvoie `True` quand la pile est rangée (gagnée) et quand la limite
  de 14 coups est atteinte (perdue) ; l'exemple ne lit pas `win`. La mère ne
  prend donc pas le signal pour la fin de l'exemple : elle calcule l'**état
  de fin** de l'exemple (`[2, 2, 2]`) et le vérifie par contre-épreuve (des
  coups qui y mènent depuis d'autres positions finissent la partie, aucun n'y
  mène sans la finir). Une fin ailleurs n'est **pas comprise** : elle ne vaut
  rien, jamais une victoire ;
- **un casse-tête** : quand la fin comprise est gagnée, ce qui compte n'est
  pas de durer. L'exemple a atteint le but en *n* coups (10 à Hanoï, 3 au
  Compte est bon) : la mère juge un coup en cherchant une victoire jusqu'à
  *n* coups plus loin, et un état déjà jugé ne coûte plus rien (elle juge
  sur ce qu'elle voit). **Plus tôt vaut mieux** : une victoire vaut
  `2 h + 2 d` (*d* : les coups qui restaient à regarder). Avant, elle valait
  `2 h + d`, et le coup de plus qu'elle avait duré annulait le coup de moins
  qu'il restait : gagner en 7 coups ou en 9 valait autant (sans effet à
  Jumper et Partition, dont la fin est perdue) ;
- **une partie bloquée** : au Compte est bon, la défaite (il ne reste qu'un
  nombre) renvoie `False` sur un coup pourtant joué. Le fils ne voit alors
  aucun coup ; la mère essaie chaque action dans le labo : toutes refusées,
  la partie est **bloquée** (perdue). Si le jeu en acceptait une, sa
  perception se trompait : elle en apprendrait, ou s'arrêterait.

**Hanoï** (3 disques, 30 parties, graines 0 à 2, moins d'une seconde
chacune). La mère comprend `play` (§ 3), la fin `[2, 2, 2]` (contre-épreuve
depuis 2 états), et l'épreuve du labo corrige 3 fois sa condition avant
la première partie. Les parties 1 à 4 finissent à la limite (« fin non
comprise »), avec 25 erreurs (le fils joue la plus petite action et tourne
en rond) ; dès la partie 5, il range la pile en **7 coups, le minimum**, à
chaque partie. 7 souvenirs (les 7 positions du chemin), aucun petit motif,
0 coup impossible. Le fils voit 76 des 78 coups permis des 27 positions, et
aucun coup interdit ; il ne range la pile que depuis 15 des 27 positions
(ailleurs, il n'a rien appris : il ne reconnaît que ce qu'il a vu).

**Le compte est bon** (10 ou 30 parties, graines 0 et 1, 6 à 9 s). La
mère comprend `play` (`ecrites = union(case(arg0), case(arg1))`, le
résultat selon `arg2`, la place qui se vide), la fin (l'état
`[0, 0, 85, 0, 85]` du tirage de l'exemple) et quand un coup est permis.
L'épreuve du labo corrige 7 fois sa perception (les divisions vues
donnaient toutes 1 : « écrire 1 » tombe dès que 10 / 5 donne 2). Le labo
rejoue toujours le même tirage
(`5 5 10 4 → 85`) : les parties 1 à 3 finissent bloquées (une erreur
chacune), puis le fils gagne en 3 coups à chaque partie, avec **3
souvenirs**. Sur 100 tirages jamais vus, il gagne 3 fois (il ne joue que le
coup par défaut hors de ses souvenirs) sans un seul coup refusé ; sur les
premiers coups de 200 tirages, il voit 78 % des coups permis et aucun coup
interdit (la coïncidence `inf(arg0, ici)` de la graine 0, et les actions
jamais acceptées sur ce tirage, lui en cachent). Pour être bon, il lui
faudrait reconnaître des configurations (« il manque 5, et j'ai un 5 ») au
lieu de souvenirs d'états exacts : les petits motifs, qui comparent des
cases à des valeurs fixes, n'y suffisent pas.

## 7. Motifs décalés et symétries — `xander/symmetries.py`

**Un motif marcherait-il ailleurs ?** Dès qu'elle comprend un motif, la mère
fait l'hypothèse qu'il vaut aussi décalé (chaque case + d) et la vérifie dans
le labo : le premier joueur pose ses pions sur le motif décalé, les autres
jouent ailleurs, et la contre-épreuve dit quel motif a fini la partie. Elle ne sait
rien de la forme du plateau (l'état n'est qu'une liste de cases) : c'est le
jeu qui dit qu'au Morpion la rangée du haut décalée de 3 est une rangée, et
que décalée de 1 elle déborde sur la rangée suivante (la partie ne finit pas).
Au Morpion, la colonne de l'exemple donne les deux autres avant la première
partie. Au Puissance 4, un alignement de la 2e rangée ne s'atteint qu'en
posant d'abord des jetons dessous : chacun y joue alors, puis le premier
joueur occupe le motif.

**Cases et actions.** La mère raisonne en cases (motifs, souvenirs, symétries)
et joue des actions. Sa perception fait le lien : `case_jouee(etat, action)`
donne la case que l'action remplit, et `action_pour(case)` l'action qui vise
la file de cette case. Pour mettre le labo dans une position donnée, elle
cherche une suite de coups qui y mène : avec la gravité, un pion ne se pose
que sur une case qu'une action remplit à ce moment-là. La contre-épreuve
raisonne aussi sur les positions. Elle imagine la même position avec le pion
ailleurs, sans qu'aucun autre ne bouge. Si aucune case libre ne convient (un
pion qui en soutient d'autres, un plateau plein), elle l'échange avec un pion
d'un autre joueur : « et si cette case avait été la sienne ? ». Sans cela, un
jeton qui en soutient un autre semblerait faire partie de l'alignement. Les
pions de chaque joueur sont rangés par sa place dans l'ordre du jeu, et
chacun garde autant de pions : la position reste atteignable en jouant chacun
son tour, à deux comme à trois.

Au Morpion, une position tournée de 90° est la même situation ; au Puissance
4, la gravité interdit de retourner le plateau. La mère ne le sait pas
d'avance. Elle cherche les **renumérotations des cases** qui envoient chaque
motif de fin sur un motif de fin, par retour arrière (une case ne peut aller
que sur une case qui appartient au même nombre de motifs) : on évite les
9! = 362 880 essais. Puis elle les **vérifie dans le labo** : 20 parties
jouées au hasard sont rejouées renumérotées ; le jeu doit accepter les mêmes
coups, passer par les mêmes positions et finir au même moment. Quand elle ne
connaît qu'un motif, 4 320 renumérotations le préservent ; le labo n'en garde
que 4 (identité, deux miroirs, demi-tour), les seules qui ne changent vraiment
rien au jeu. Avec les 8 motifs, elle en garde 8 (4 rotations, 4 miroirs).
Au Puissance 4, les 69 alignements sont préservés par 4 renumérotations
(miroirs gauche-droite et haut-bas, demi-tour). Le labo ne garde que le miroir
gauche-droite : renversé, le jeu ne tombe plus au même endroit. Au Morpion à
trois (4 × 4, trois alignés), elle retrouve les 24 alignements et les 8
symétries du carré, de la même façon (§ 6, *Plus de deux joueurs*).

Le fils reçoit la liste `SYMETRIES` : pour retrouver un souvenir, il regarde
sa position sous chacune des 8 façons de la voir, et renumérote le coup
retenu. Un refactor compte deux positions équivalentes comme un seul
souvenir.

### Petits motifs : ce qui comptait, reconnu partout

Un maître d'échecs ne retient pas des positions entières : il reconnaît des
configurations de quelques pièces (Chase et Simon). La mère fait de même avec
ses souvenirs, en deux questions, toutes deux vérifiées dans le labo.

**« Qu'est-ce qui comptait ? »** Un souvenir `MM.AA....` → 2 (`M` : mes pions,
`A` : les siens, `.` : libre au sens qu'elle a appris, `#` : autre chose ; à
plus de deux joueurs, `A` est le suivant, `B` celui d'après, etc.)
devient un **petit motif** : les cases qui ne
comptent pas deviennent `?`. Un petit motif tient si son coup est le bon
partout où il apparaît. La mère le vérifie de deux façons :

- dans tous les cas enregistrés, sous chaque façon de les voir : le coup doit
  y être aussi bon que celui du professeur ;
- dans 20 positions qu'elle imagine dans le labo, **en jouant** : à son
  tour, chaque joueur pose un de ses pions du motif si une action le pose
  là, ou un pion de plus sur une case `?` qu'une action remplit (le nombre
  de pions est tiré au hasard, le fils étant à n'importe quelle place). Avec
  la gravité, aucun pion ne flotte : la mère n'a pas à le savoir, les
  actions permises s'en chargent. Elle écarte une position où la partie est
  déjà finie. Elle demande son coup au professeur. S'il joue le coup du
  motif, la position le **confirme**. S'il joue ailleurs, elle vérifie que le
  coup du motif est aussi bon que le sien, en lui faisant finir la partie :
  sinon le motif est **démenti**. Il faut qu'au moins la moitié des positions
  le confirment.

  Remplir les `?` au hasard, puis chercher une suite de coups qui y mène,
  marchait au Morpion. Au Puissance 4, presque aucune de ces positions
  n'était atteignable : un motif était « vérifié » sur une ou deux positions.

**Le groupe témoin.** Confirmer ne suffit pas : au Puissance 4, le
professeur joue la colonne du centre dans la plupart des positions imaginées
au hasard. Elles « confirmaient » donc un motif comme « la case 3 est libre :
y jouer », qui ne dit rien de la position (après 3 parties, 391 souvenirs,
presque tous de tels motifs). La mère fait comme un expérimentateur : pour
chaque position imaginée, elle en joue une **témoin**, avec autant de pions,
où le motif est cassé (une de ses cases prend une autre valeur : un pion
devient l'autre pion ou une case libre, une case libre reçoit un pion) et où
le coup reste jouable. Elle compte :

- *r+* : la part des positions avec le motif où le professeur joue son coup ;
- *r−* : la part des positions témoins où il le joue quand même.

Le motif tient si *r+* ≥ (1 + *r−*) / 2 : il fait au moins la moitié du
chemin entre le témoin et la certitude. Si le professeur joue le centre dans
80 % des positions, motif ou pas, il faudrait *r+* ≥ 90 % : le motif est
refusé. Un motif toujours confirmé (*r+* = 1) passe, même si une de ses
cases ne compte pas : il est juste, simplement pas le plus petit.
Il faut au moins une position témoin, et au moins une case en plus du coup
(« jouer ici » tout court n'est pas un motif).

**Ce que cela coûte.** Demander son coup au professeur coûte une recherche ;
juger qu'un coup est aussi bon que le sien coûte deux fins de partie. La mère
économise de trois façons :

- elle retient l'issue et le coup du professeur pour **chaque position** par
  laquelle passe une fin de partie, pas seulement la première : une autre
  question sur l'une d'elles ne coûte plus rien ;
- elle ne juge à fond que deux désaccords par motif, et seulement une fois
  les comptes passés (confirmations et témoin) : un motif que les comptes
  refusent ne coûte aucune fin de partie. Les désaccords suivants comptent
  seulement comme des positions qui ne confirment pas ;
- dans une fin de partie imaginée, elle ne fait pas la contre-épreuve d'un
  plateau qui n'est pas plein (elle ne la fait que pour comprendre une vraie
  fin de partie).

Elle cherche le **plus petit** motif qui tient, en regardant d'abord la
**zone** du coup : les cases qui partagent avec lui un motif de fin qu'elle
connaît (ce qui se joue sur les lignes passant par le coup). Comme le joueur
qui regarde les lignes de sa case, elle ne cherche pas plus loin : si rien ne
tient dans la zone, le souvenir reste entier. (Un coup qu'aucun motif de fin
ne contient a pour zone tout le plateau.) Dans la zone, elle essaie le coup
avec 0 case, puis 1, 2, 3… cases, tant qu'il y a au plus 100 combinaisons à
essayer en tout (`combinations` : au Morpion, toutes les combinaisons pour
une case du bord ou un coin, jusqu'à 3 cases pour le centre ; au
Puissance 4, une seule case). Ensuite, elle part de toute la zone et oublie
les cases une à une. Elle garde chaque oubli qui tient sur 5 positions
seulement (`sieve`, un tamis). Le motif obtenu est vérifié à la fin sur 20
positions ; s'il ne tient pas, le souvenir reste entier. Ici, elle trouve
`MM.??????` → 2 : mes deux pions et la case libre suffisent.

**« Et ailleurs ? »** Comme un motif de fin, le petit motif est essayé décalé
(chaque case + d) et vérifié de la même façon. `MM.??????` décalé de +3
(`???MM.???` → 5) tient, comme décalé de +6. Décalé de +1 (`?MM.?????` → 3),
il déborde sur la rangée suivante, et le labo le rejette. Un décalage
équivalent par symétrie à un souvenir connu n'est pas ajouté.

Le fils reconnaît un petit motif sous chacune des façons de voir sa position.
S'il se trompe sur un petit motif, c'est que le labo n'avait pas imaginé
cette position. La mère oublie alors ce petit motif. Les cas qu'il couvrait
redeviennent des souvenirs entiers, qu'elle réduira de nouveau, avec ce
nouveau cas comme test.

Au Morpion, les petits motifs restent grands : environ 8 cases sur 9. Sur un
plateau aussi petit, presque toutes les cases comptent pour la tactique. Un
motif est parfois vrai d'une façon inattendue, par exemple parce que toutes
les positions qui le contiennent sont perdues de toute façon. Aucun petit
motif n'a été démenti sur 10 graines et 400 parties.

## 8. Les briques — `xander/concepts.py`

Un concept est un **arbre** (une structure Python, pas du texte, pas de
modèle de langage) qui décrit une position du point de vue de « moi ». Il
s'écrit uniquement avec les quatre notions que la mère apprend pour chaque
jeu : `possibles(etat)`, `apres(etat, action, joueur)` (vient de l'Analyzer),
`gagne(etat, joueur)` (la fin de partie comprise par contre-épreuve) et
`suivant(joueur)`, le joueur qui joue après lui (l'ordre des joueurs lu dans
l'exemple ; à deux, c'est l'adversaire, l'ancienne notion
`adversaire(joueur)`).

| Nœud | Sens |
| --- | --- |
| `Brique(nom, J)` | une brique connue, vue du côté de J ; au départ, seulement `gagne` |
| `Non(x)`, `Et(x, y)` | négation, conjonction |
| `AuMoins(k, J, x)` | au moins k actions de J mènent à une position où x est vrai ; par défaut k = 1 : « il existe une action de J après laquelle x » |

**Les joueurs J.** Un joueur est désigné par sa place après moi dans l'ordre
du jeu : `moi`, `lui` (le suivant, `suivant(moi)`), `lui2` (le suivant du
suivant), etc., jusqu'au nombre de joueurs vus dans l'exemple
(`concepts.joueurs(n)`). À deux, il n'y a que `moi` et `lui`, exactement
comme avant : mêmes concepts, mêmes règles. À trois, un concept peut dire
**qui** il pare : `Non(AuMoins(1, lui, gagne(lui)))` pare le suivant,
`Non(AuMoins(1, lui2, gagne(lui2)))` pare celui d'après (« aucun des coups du
2e après moi ne donne « le 2e après moi a gagné » »). Une brique vue du côté
d'un autre se compose : `concept_1(lui)`, c'est `concept_1` du point de vue
du suivant, donc, pour lui, « son suivant » est mon `lui2`. Comme pour
`AuMoins(1, moi, …)` à deux joueurs, un concept peut enchaîner les coups d'un
joueur sans attendre son tour : « celui d'après a un coup gagnant » se lit
juste après mon coup, sans supposer ce que jouera le suivant. C'est ce que
fait aussi le professeur à trois : il ne compte pas sur le suivant pour parer
le troisième.

Une règle se lit « jouer une action après laquelle le concept est vrai » ;
une règle qui accepte toutes les actions ne choisit rien et est ignorée. La
mère énumère les arbres par taille croissante (jusqu'à 6 nœuds, 2 niveaux de
`AuMoins`), et confond deux arbres qui disent la même chose sur un
échantillon de positions imaginées : on garde le plus petit. Chaque concept
adopté devient une brique, d'où des concepts plus grands à taille égale
(composition, comme les configurations de Chase et Simon).

**Fourni à la main** : ces quatre sortes de nœuds (avec k = 1, c'est la
logique minimale : non, et, il existe), la façon de désigner un joueur (sa
place après moi, avec `suivant`), les bornes de la recherche, le budget
du fils, et la forme d'une règle (« jouer une action après laquelle… »). Le vocabulaire écrit à la
main (`xander/vocabulary.py` : `gagner`, `parer`, `fourchette`,
`contre_fourchette`, `attaque`) ne sert plus qu'aux tests, pour comparer.

## 9. Le fils — `xander/son_writer.py`

Le fils est un **fichier Python autonome**, écrit par la mère, réécrit après
chaque correction, qui n'importe rien de Xander :

1. **Perception** : `possibles`, `apres`, `gagne`, `suivant`, écrites à
   partir de ce qu'elle a compris (`JOUEURS` : les pions dans l'ordre où les
   joueurs jouent ; `suivant` en vient), plus `case_jouee`, `action_pour` et
   `VUES`, le compteur des positions regardées. `apres` recopie le programme
   qu'elle a construit pour décrire l'action (§ 3), traduit en Python
   (`changees(avant, args)`, ou `valeur_apres` pour un nombre) : ce qu'elle a
   vérifié sur les cas est exactement ce que le fils exécute. La case jouée est
   la seule case que le programme annonce, si elle est libre (`libre`, telle
   que la mère l'a décrite, § 3) ; elle reçoit la valeur écrite qu'elle a
   décrite (au Morpion, `joueur`). La clé d'une position (`cle`) se lit sur la
   position elle-même, du côté de « moi » (`M` moi, `A` le suivant, `B` celui
   d'après…, `lettres(moi)`), puis se renumérote pour chaque symétrie. Le
   fils lit son pion sur le plateau (`qui_suis_je`) : celui qu'il a posé, sinon
   celui du joueur qui a le trait, le seul qui a posé moins de pions que celui
   qui joue avant lui (chacun joue à son tour) ; si tous en ont autant, celui
   du premier joueur de l'exemple.
   `possibles` garde les actions que le jeu accepte au départ et qui
   remplissent une case ; `action_pour` vient des portées déduites de
   l'exploration. La mère pense avec la même perception. Si plusieurs programmes de
   même taille coexistent, elle prend le premier trouvé.
   Quand l'état est une valeur (§ 6), la perception s'écrit autrement : une
   position est `[valeur, trait]`, `valeur_apres` recopie le programme,
   `permise` dit quelles valeurs d'après sont permises, `FINS` à quelle valeur
   la partie finit et qui la gagne ; ni cases, ni pions, ni symétries. Le fils
   sait seulement que c'est son tour : il a le trait.
2. **Règles** : les concepts qu'elle a construits et appris au fils, **et
   seulement ceux-là** (avec les briques dont ils dépendent), traduits en
   Python, `REGLES` dans l'ordre appris, `SOUVENIRS` et `SYMETRIES`.
3. **Squelette** : `choisir` (souvenir, sinon première règle qui choisit,
   sinon première action possible) et `play(game)`. C'est ici qu'on pourra
   plus tard transmettre l'expérience de ses frères.

Le fils exécute son code bêtement : il ne simule que ce que ses règles
demandent, sans mémoire, et n'appelle jamais `back`. Il ne joue qu'un coup
par tour : si le jeu le refuse, il le dit (« coup impossible ») au lieu
d'essayer d'autres actions jusqu'à ce que le jeu en accepte une, ce qui
serait tricher. **Budget** : la mère
refuse un refactor qui ferait regarder au fils plus de 1 000 positions pour
un coup (un minimax complet en regarde plus de 500 000 au premier coup du
Morpion) ; un test le vérifie sur toutes les positions.

Pour un joueur seul (`son_writer.solo_source`), le fils n'a ni `apres` ni
`gagne` : `possibles`, `SOUVENIRS` (état exact → coup), `MOTIFS` (petits
motifs `{case: valeur}` → coup, dans l'ordre appris) et le squelette
(souvenir, petit motif, défaut). La description de l'action n'y est qu'en
commentaire : il ne prévoit rien, il reconnaît. Un coup est refusé si
l'action ne renvoie pas ce qu'elle renvoie d'habitude **et** que rien n'a
changé.

`Mother.raise_son(exemple, professeur)` renvoie l'éducation (fils, parties,
leçons, refactors) ; `Mother.create_son(nom, exemple, professeur=…)` écrit le
fils dans `output/sons/<nom>.py`. Un exemple à un seul joueur est éduqué
sans professeur (`python -m xander res/exampleJumper.py --son jumper --parties 30`).

## 10. Problèmes « entrée → sortie » — `xander/transformations.py`

Un genre de problème qui n'est pas un jeu (jalon 1) : quelques **paires**
(une entrée, la sortie attendue) et des **questions** (une entrée seule). Le
format et son lecteur : `docs/format-exemple.md` et `xander/problemes.py`.

```text
 res/problemes/*.json
      │  problemes.py       lecture ; les réponses attendues restent à l'examinateur
      ▼
 paires + entrées des questions
      │  transformations.py la mère cherche le plus petit programme sortie = t(x)
      │  briques.py         l'équipement de naissance (18 briques)
      ▼
 Comprehension ── premier essai, deuxième essai, ou « je ne trouve pas »
      │  fils_repondeur.py  la mère écrit le fils et le vérifie sur les paires
      ▼
 output/sons/<nom>.py ── fichier autonome : le programme trouvé et ses briques
      │  mesure.py          l'examinateur lance le fils sur les questions et note
```

**Le même geste que pour une action.** Quand elle décrit l'effet d'une
action (§ 3), la mère cherche par taille croissante le plus petit programme
`apres = t(avant, args)` qui explique tous les cas. Ici, elle cherche
`sortie = t(x)` qui explique toutes les paires : les paires jouent le rôle
des cas (et des souvenirs, les tests du refactor), le programme trouvé
devient le fils.

**Le langage.** Un programme est un arbre : la feuille `x` (l'entrée), des
constantes, et des briques. `chaque(f, s)` et `garder(p, s)` reçoivent une
**fonction de l'élément**, un petit programme où la feuille `e` désigne
l'élément : `chaque(plus(e, 1), x)` ajoute 1 à chaque nombre. La taille d'un
programme est son nombre de nœuds (la feuille `e` ne compte pas) ; la mère
cherche jusqu'à 6 nœuds, et une fonction de l'élément en a au plus 3 (sans
`chaque` ni `garder` dedans).

**Les constantes** : `0`, `1`, et au plus quatre valeurs simples qu'elle
remarque dans les paires (un nombre, un texte, une lettre d'un texte, un
booléen présents dans au moins deux paires ; celles qui reviennent dans le
plus de paires, puis le plus souvent). Elle remarque ainsi l'espace d'une
phrase, le tiret d'une date, le « . » d'un plateau, sans qu'on les lui
donne.

**L'équipement de naissance** (`xander/briques.py`). C'est tout ce qui est
fourni à la main, avec une convention de perception : *un texte est une
suite de lettres* (`inverser("chat")` vaut `"tahc"`). Chaque brique est
justifiée par au moins deux problèmes d'entraînement de domaines différents,
et un test le vérifie sur ce que la mère trouve réellement :

| Brique | Ce qu'elle fait | Problèmes d'entraînement qui s'en servent (domaine) |
|---|---|---|
| `longueur(s)` | nombre d'éléments | combien-de-nombres (listes), nombre-de-lettres, nombre-de-mots (mots) |
| `premier(s)`, `dernier(s)` | premier, dernier élément | initiale, derniere-lettre (mots), soustraction (nombres), colonne-de-gauche (plateaux), le-plus-grand (listes) |
| `inverser(s)` | la suite à l'envers | liste-a-l-envers (listes), mot-a-l-envers (mots), plateau-haut-en-bas, plateau-dans-le-miroir (plateaux) |
| `trier(s)` | ordre croissant | liste-dans-l-ordre (listes), lettres-dans-l-ordre (mots), le-plus-grand-des-deux (nombres) |
| `somme(s)` | somme des nombres | la-somme (listes), addition (nombres) |
| `non(b)` | contraire | sans-les-zeros (listes), sans-espaces (mots), pions-dans-l-ordre (plateaux) |
| `element(s, i)` | l'élément d'indice *i* | l-element-designe (listes), rangee-du-milieu, case-du-centre (plateaux) |
| `compter(s, v)` | combien d'éléments valent *v* | combien-de-zeros (listes), pions-de-x, x-par-rangee (plateaux) |
| `positions(s, v)` | indices des éléments qui valent *v* | ou-sont-les-zeros (listes), ou-est-cette-lettre (mots), cases-libres (plateaux) |
| `couper(s, v)` | morceaux séparés par *v* | groupes-separes-par-zero (listes), les-mots, l-annee (mots) |
| `plus`, `fois` | addition, multiplication | un-de-plus, les-carres (listes), le-suivant, le-carre (nombres) |
| `moins` | soustraction | le-precedent (nombres), allumettes-restantes (plateaux : l'état des Allumettes est un nombre) |
| `egal(a, b)` | identiques ? | liste-symetrique (listes), palindrome (mots), sont-ils-egaux (nombres) |
| `inferieur(a, b)` | *a* < *b* | les-positifs (listes), est-il-plus-petit (nombres) |
| `chaque(f, s)` | *f* sur chaque élément | doubler (listes), initiales (mots), plateau-dans-le-miroir (plateaux) |
| `garder(p, s)` | les éléments qui vérifient *p* | les-positifs (listes), sans-espaces (mots), pions-dans-l-ordre (plateaux) |

Deux valeurs ne sont égales que si elles ont le même type (`1`, `1.0`,
`True` et `"1"` diffèrent) : aucune conversion cachée. Une brique qui n'a pas
de sens sur ses valeurs (la longueur d'un nombre, le premier d'une liste
vide) rend le programme **indéfini** sur cette entrée.

**La recherche.** Comme dans `effets.py` : énumération par taille croissante,
et deux programmes qui donnent les mêmes valeurs sont confondus (on garde le
plus petit, ou le premier trouvé). Les valeurs comparées sont celles des
entrées des paires **et des questions** : deux programmes d'accord sur les
paires mais pas sur une question restent distincts, puisqu'ils proposent deux
réponses. La mère ne voit jamais les réponses attendues. Deux fonctions de
l'élément sont confondues si elles donnent les mêmes valeurs sur un
échantillon d'éléments (ceux des suites déjà construites, 48 au plus) ; à
taille égale, la moins composée d'abord (`0 < e` plutôt que `e < e + e`). Les
sortes de valeurs (nombre, booléen, texte, liste) écartent d'avance les
compositions absurdes (`plus` d'un texte). Un budget borne le nombre de
programmes distincts examinés (400 000).

**Conclure à partir de peu (jalon 4).**

- Il faut au moins deux paires distinctes ; deux paires contradictoires (la
  même entrée, deux sorties) arrêtent tout.
- **Premier essai** : le plus petit programme qui explique toutes les paires
  et sait répondre à toutes les questions. À taille égale : le premier trouvé
  dans l'ordre d'énumération (la feuille `x`, les constantes, puis les
  briques dans l'ordre de `BRIQUES`). C'est la préférence documentée,
  simple et arbitraire ; elle dit aussi combien de programmes de cette taille
  donnaient d'autres réponses.
- **Deuxième essai** : le plus petit programme suivant qui explique aussi
  toutes les paires mais donne une **autre** réponse à au moins une question
  (sinon ce ne serait pas un autre essai).
- **Rien dans la taille permise** : elle le dit (« aucun programme de taille
  6 au plus n'explique toutes les paires ») et n'écrit pas de fils.

Exemple d'entraînement : « combien de fois cette lettre est dans le mot ».
Sur les paires `banane/a → 2`, `chat/c → 1`, `lune/z → 0`, `kayak/k → 2`,
le plus petit programme est la coïncidence `compter(premier(x), "a")` (compter
les « a » !), taille 4 ; le deuxième essai, `compter(premier(x),
dernier(x))`, taille 5, est le bon. Une règle tirée de peu de cas peut être
une coïncidence : le deuxième essai est là pour ça.

**Le fils** (`xander/fils_repondeur.py`) est un fichier Python autonome qui
n'importe rien de Xander : `repondre(x)` (le programme trouvé, traduit en
Python), `deuxieme_essai(x)` s'il y en a un, les briques dont ils se servent
**et seulement celles-là** (recopiées de `briques.py` avec leurs outils), et
les entrées des questions. Lancé seul, il y répond ; on peut aussi lui donner
une entrée en JSON. Avant de le livrer, la mère l'exécute sur toutes les
paires : ce qu'elle a vérifié est exactement ce qu'il exécute.

**La mesure** (`xander/mesure.py`) sépare les rôles : la mère reçoit les
paires et les entrées des questions ; l'examinateur lance le fils et compare
ses réponses aux réponses attendues, qui ne reviennent jamais vers la mère.
`python -m xander res/problemes/entrainement/mots.json` affiche, pour chaque
problème, le programme trouvé, le deuxième essai, ce que répond le fils et le
score ; `--probleme NOM` en choisit un, `--son NOM` écrit le fils dans
`output/sons/`.

**Ce qui est fourni à la main** : les 18 briques et leur ordre, la
convention « un texte est une suite de lettres », la feuille `x`, les
constantes 0 et 1, la façon de remarquer les autres, la taille maximale des
programmes (6) et des fonctions (3), l'échantillon qui confond deux
fonctions, le minimum de deux paires, le budget et la préférence à taille
égale.

**Limites et suites.**

- La taille 6 suffit à l'entraînement (le plus grand programme trouvé en a 5)
  et la recherche prend 0,4 s au plus par problème (8 s pour les 55). Une
  taille 7 multiplie le temps total par 4 environ, une taille 8 par 8 : au-delà,
  c'est le jalon 2 (chercher sans tout énumérer, guidée par ce qu'elle
  observe), pas une raison d'ajouter une brique.
- Pas de « si », pas de façon de voir des lignes sur un plateau : « qui a
  trois pions alignés » et « à qui le tour » restent hors de portée, et elle
  le dit. Pas de constante qu'elle n'a pas vue (« ajouter 10 » quand 10
  n'apparaît dans aucune paire).
- L'échantillon qui confond deux fonctions de l'élément ne contient que les
  éléments des suites de taille 3 au plus : deux fonctions d'accord sur lui
  mais pas ailleurs sont confondues, et l'une peut manquer.
- Les briques sont fournies. Elles devraient devenir, au jalon 2, des
  concepts que la mère garde d'un problème à l'autre (« le plus grand » =
  `dernier(trier(x))`, trouvé ici, pourrait devenir une brique) ; et
  certaines devraient être découvertes plutôt que données.
- **Refactor à faire : un moteur commun avec `effets.py`.** Les deux
  énumèrent des arbres par taille croissante, confondent ceux qui donnent les
  mêmes valeurs et gardent le plus petit qui explique tous les cas ;
  `transformations.py` réutilise déjà `_compositions` et `INDEFINI`. Il
  faudrait un moteur partagé (nœuds, énumération, confusion par les valeurs,
  sortes) où `effets.py` ajoute ses feuilles (`arg`, `avant`) et ses briques
  de cases, et `transformations.py` les siennes et les fonctions de
  l'élément. Une paire « entrée → sortie » deviendrait alors un cas
  `apres = t(avant)` sans arguments.

## 11. Les examens blancs — `xander/examen.py`

Un examen blanc mesure la mère sur des problèmes **inédits**, écrits à
l'avance et gardés sous scellé hors du dépôt (jalon 6 de la feuille de
route). Le lanceur ne connaît aucun problème : il ne fait que de la
plomberie, puis appelle `Mother.raise_son` comme pour n'importe quel jeu. Il
ne change rien à la mère.

```powershell
python -m xander.examen C:\chemin\hors\du\depot\examen-blanc-N
```

**Convention.** Chaque sous-dossier du dossier d'examen est un problème
(ordre alphabétique, numérotés à partir de 1). Il contient trois fichiers,
tous obligatoires :

- `exemple.py` : une vraie partie, au format de `docs/format-exemple.md`, dont
  le `# include` importe le jeu par son nom de module ;
- `professeur.py` : une fonction `professeur(game)` qui joue un coup (pour un
  jeu à un joueur aussi : c'est la référence de la mesure) ;
- `arbitre.py` : ce que sait l'auteur du problème, et pas la mère (voir
  ci-dessous).

Seuls l'exemple et le professeur vont à la mère, comme pour tout jeu.
L'arbitre ne sert qu'à la mesure.

**L'arbitre.** C'est l'auteur du problème qui sait comment son jeu se
termine et ce qui compte comme un bon résultat. Le lanceur ne lit jamais la
fin d'une partie de mesure dans la mère, ni dans une interface supposée du
jeu (`win`, `get_turn`) : c'est l'arbitre qui décide. Interface, au niveau
du module :

| Nom | Rôle |
|---|---|
| `joueurs` | le nombre de joueurs (1, 2, 3…) |
| `plafond` | le nombre maximal de coups d'une partie de mesure ; au-delà, la partie s'arrête et on lit le résultat tel quel (indispensable quand on survit plus ou moins longtemps) |
| `nouvelle_partie(graine)` | une partie neuve et initialisée, **commencée comme celle de l'exemple** (même premier joueur, mêmes réglages) ; la graine sert aux jeux qui en ont une |
| `a_qui(game)` | la place du joueur au trait, de `0` à `joueurs - 1` (toujours `0` pour un joueur seul) |
| `finie(game)` | la partie est-elle finie ? |
| `resultat(game, place)` | un nombre, plus grand est meilleur : victoire 1, nul 0, défaite −1 ; ou la durée de survie ; ou moins le nombre d'essais. Appelé sur une partie finie, ou arrêtée au plafond |
| `coups_permis(game)` | la liste de **tous** les coups que le jeu accepte maintenant, chacun sous la forme `(nom_de_methode, argument, …)`, par exemple `[("play", 0), ("play", 3)]` |

`coups_permis` sert deux fois, sans passer par la mère : le joueur au hasard
de la mesure tire parmi ces coups (un vrai hasard, même si la mère n'a pas
trouvé toutes les actions), et un coup du fils qui n'y est pas est un coup
impossible.

Un exemple d'arbitre (le Morpion de `Games/`, deux joueurs) :

```python
from jeu import Morpion

joueurs = 2
plafond = 9


def nouvelle_partie(graine):
    game = Morpion()
    game.init("X")          # comme l'exemple : X commence
    return game


def a_qui(game):
    return "XO".index(game.get_turn())


def finie(game):
    return bool(game.win)


def resultat(game, place):
    if game.win in ("", "D"):
        return 0
    return 1 if game.win == "XO"[place] else -1


def coups_permis(game):
    return [("play", case) for case in game.get_moves()]
```

Pour un jeu où l'on survit (Partition) : `joueurs = 1`, `a_qui` renvoie 0,
`resultat` renvoie le nombre de temps joués et `plafond` borne la partie.
Pour un casse-tête réussi en plus ou moins de coups : `resultat` renvoie
moins le nombre de coups, et une valeur plus basse que tout si le plafond
est atteint sans réussir. Les tests (`tests/test_examen.py`) en donnent
quatre : Morpion, Partition, Allumettes et Jumper.

**Plomberie.** Le dossier du problème est ajouté à `PYTHONPATH`, que le rejeu
(`xander/rebuilder.py`) conserve : l'exemple s'importe aussi dans le
sous-processus du rejeu et dans le labo. Avant que la mère voie quoi que ce
soit, le lanceur vérifie que les trois fichiers existent, que l'exemple
s'exécute tel quel depuis la racine du dépôt, que le professeur s'importe et
que l'arbitre a son interface (une partie neuve n'est pas finie, `a_qui`
donne une place, `coups_permis` une liste non vide, `resultat` un nombre).
Sinon l'examen s'arrête sur une « erreur de branchement » : ce n'est pas un
échec de la mère, et aucun score n'est écrit. Un professeur ou un arbitre qui
plante pendant la mesure est aussi une erreur de branchement. Chaque problème
passe dans son propre sous-processus (modules isolés, limite de temps tenue
en l'arrêtant, `PYTHONHASHSEED` fixé). Les problèmes et le rapport doivent
être hors du dépôt.

**Barème : au moins aussi bien que le professeur à sa place.** Une
*situation* de mesure est une graine de partie, une place à la table et des
adversaires : tous les autres joueurs sont le professeur, ou tous jouent au
hasard (un joueur seul n'a pas d'adversaire). Chaque situation se joue deux
fois : une fois le fils à cette place, une fois le professeur, avec les mêmes
graines et les mêmes autres joueurs. Le hasard global (`random`, pour un
professeur ou un jeu non déterministe) est réinitialisé par la situation
avant chaque partie, et chaque coup au hasard a sa graine (situation et
numéro du coup) : tant que les deux parties restent les mêmes, le hasard y
fait les mêmes choix. Le fils *tient* la situation si son `resultat` à cette
place est au moins celui du professeur, sans coup impossible.

Ce barème vaut pour un, deux ou trois joueurs, avec ou sans nul, avec ou sans
vraie défaite : perdre une partie que le professeur perd aussi (aux
Allumettes, partir en premier d'une position perdante) n'est pas un échec,
et survivre aussi longtemps que lui suffit.

| | |
|---|---|
| Score relatif d'un problème | la part des situations tenues (de 0 à 1) |
| Réussi | toutes les situations tenues, et aucun coup impossible après les 5 premières parties d'éducation ni pendant la mesure (« le fils ne triche jamais ») |
| Raté | sinon ; aussi, avec un score relatif 0, si la mère dit qu'elle ne sait pas éduquer ce problème, si elle plante ou si le temps est dépassé |
| Score de l'examen | problèmes réussis / total, et la moyenne des scores relatifs |

**La mesure ne nourrit jamais la mère.** Le fils mesuré est son code tel que
la mère l'a écrit (`education.source()`), chargé à part, neuf pour chaque
partie. Il joue avec sa propre fonction `play`, sur une vue du jeu : les
appels passent au vrai jeu, sauf les coups. Le premier coup, s'il est permis,
est joué ; un coup que l'arbitre ne permet pas, ou un deuxième essai, n'est
pas transmis et compte comme un coup impossible (la situation est perdue).
Une fois la partie finie, le fils ne lit plus qu'une copie du jeu (certains
jeux recommencent une partie quand on lit un état terminé). Rien de ce qui
se passe pendant la mesure ne revient vers la mère : elle ne corrige pas, ne
réécrit pas, et son labo n'est pas utilisé (un test le vérifie).

**Budget, fixé avant tout examen** (`BUDGET`, vérifié par un test) :

| | |
|---|---|
| Éducation | 200 parties (le défaut de `raise_son`) |
| Graine maîtresse | 0 : éducation, graines des parties de mesure, hasard |
| Mesure | 10 graines pour chaque place et chaque sorte d'adversaires : 10 situations pour un joueur seul, 40 à deux joueurs, 60 à trois ; deux parties par situation, chacune d'au plus `plafond` coups |
| Rodage | aucun coup impossible après la partie 5 de l'éducation |
| Limite de temps | 20 000 fois la tâche de référence par problème (environ 30 minutes sur la machine de développement), tout compris |

Le travail est borné par les nombres de parties et le plafond de coups. La
limite de temps n'est qu'un garde-fou ; pour qu'elle dépende moins de la
machine, le lanceur mesure au début une **tâche de référence** fixe en Python
pur (`tache_de_reference` : tirer, trier et compter 200 000 nombres, la plus
courte de 5 mesures, environ 0,09 s sur la machine de développement) et la
limite est un multiple de cette mesure. Le rapport donne la machine, la
mesure et la limite qui en découle.

**Rapport.** Sur la sortie et dans un fichier hors du dépôt (par défaut
`<dossier>/rapport-<date>.txt`) : le commit (signalé s'il y a des
modifications non commitées), la date, la machine et sa mesure de référence,
le budget, puis pour chaque problème son numéro, réussi ou raté, son score
relatif, son nombre de joueurs et la durée ; enfin les deux scores. Rien
d'autre sur le contenu des problèmes, ni sur la raison d'un échec.

**Écrire un problème.**

1. Écrire le jeu (un module dans le dossier du problème), une vraie partie
   en exemple, un professeur qui joue bien et l'arbitre. `nouvelle_partie`
   commence comme l'exemple : la mère n'a vu que ce début-là.
2. `coups_permis` liste tous les coups que le jeu accepte, sous la forme
   exacte où on les passe au jeu ; un coup accepté par le jeu mais absent de
   la liste serait compté impossible pour le fils.
3. `resultat` dit ce qui compte, pour chaque place, sur une partie finie ou
   arrêtée au plafond ; le `plafond` laisse au professeur le temps de faire
   ce qu'il sait faire.
4. Vérifier que tout est bien formé sans lancer la mère, par exemple avec
   `controler_arbitre` et une partie professeur contre professeur.

**Passer un examen.**

1. Écrire les problèmes avant de regarder ce que la mère sait faire, les
   mettre sous scellé hors du dépôt (voir le `PROTOCOLE.txt` du dossier des
   scellés) et vérifier qu'ils sont bien formés sans lancer la mère.
2. Commiter : le commit de l'examen est celui qu'affiche le rapport.
3. Lancer `python -m xander.examen <dossier>` une seule fois, sans rien
   toucher pendant l'examen. Si le lanceur s'arrête sur une erreur de
   branchement, on ne corrige que le lanceur ou la plomberie du problème
   (jamais la mère) et on relance tout.
4. Noter la date, l'examen, le jeu de problèmes, le commit et les deux scores
   dans le « Journal des examens » de `docs/feuille-de-route.md`. Ne pas
   regarder pourquoi un problème a raté : ce jeu de problèmes ne sert plus.

**Ce qui reste fragile.** Contre le hasard, dès que le fils et le professeur
jouent autrement, leurs parties divergent et le hasard n'y fait plus les
mêmes choix : la comparaison mêle alors habileté et chance. Le score binaire
demande de tenir toutes les situations ; une seule partie malchanceuse le
fait tomber (le score relatif, lui, le montre à peine). L'arbitre est écrit à
la main par l'auteur du problème : une erreur de sa part (un coup permis
oublié, un résultat mal lu) fausse la mesure sans erreur de branchement. La
tâche de référence ne mesure que la vitesse du Python pur sur un cœur : la
limite reste approximative d'une machine à l'autre.

**Historique.** L'examen blanc n° 1 a été passé avec l'ancien barème (pas
d'arbitre ; verdict lu dans `win` et `get_turn` du jeu, sinon dans la mère ;
réussi si le fils ne perd aucune des 2 parties contre le professeur ni des 100
contre le joueur au hasard de la mère ; 30 minutes par problème). Ce barème a
été changé à cause des fragilités du protocole qu'il a montrées (hasard
emprunté à la mère, fin lue dans la mère, « ne jamais perdre » sans sens pour
un jeu sans nul ou à un joueur, deux parties seulement contre le professeur,
limite dépendant de la machine), pas à cause du score.

## 12. Le bulletin du fils — `xander/bulletin.py`

Une mesure pour nous, qui ne modifie rien : le bulletin lit une éducation finie
et dit si le fils a **compris** ou **retenu**. Tout ce qu'il fait jouer dans le
labo est effacé ensuite (mémoires de calcul de la mère comprises), et il
vérifie que ce que sait la mère n'a pas changé. Rien ne revient vers elle.
`python -m xander res/exampleX.py [--prof …] --parties N --bulletin`.

| Mesure | Calcul |
|---|---|
| Taille | nœuds des règles et des briques dont elles dépendent (chaque brique une fois) + cases fixées par les souvenirs (une position entière : toutes ses cases ; un petit motif : celles qui comptent ; une valeur : 1, un tuple : ses termes) |
| Compression | cas enregistrés que le fils joue bien ÷ taille |
| Origine des coups | sur des parties sans correction (à chaque place : une contre le professeur, dix contre le hasard ; seul : dix parties du labo), la part décidée par chaque règle, un petit motif, un souvenir, le coup par défaut |
| Généralisation | jusqu'à 50 positions atteignables **jamais enregistrées** (à symétrie près), où le joueur au trait a le choix, tirées par le bulletin (en largeur depuis le début, au plus 2 000 positions, puis par des coups au hasard) ; à plusieurs, le coup du fils est-il aussi bon que celui du professeur (le professeur finit la partie de tous les côtés) ; seul, le fils joue jusqu'à la fin depuis la position et fait-il au moins aussi bien que le calcul de la mère (une victoire vaut plus que tout, plus tôt vaut mieux ; sinon la durée) |
| Solidité des règles | pour chaque règle, les cas où elle choisirait (pas tous les coups), ceux où son coup est bon, ceux où elle décide chez le fils |
| Budget | positions regardées au plus pour un coup (mesuré par l'éducation) |
| Stabilité | `stabilite(eleve, graines)` : les règles trouvées selon la graine de l'éducation (à part : coûte une éducation par graine) |

Les seuils d'interprétation ne sont pas fixés : on compare les nombres d'un
fils à l'autre (voir `docs/feuille-de-route.md`, « Le bulletin du fils »).
Limites : un jeu dont le labo rejoue toujours le même tirage (Le compte est
bon, Mastermind) n'offre que des positions de ce tirage ; un tirage nouveau
demande que le labo sache varier l'état de départ (priorité suivante). Pour un
casse-tête, le bulletin dit aussi depuis combien de ces positions la mère et le
fils gagnent : une égalité sans victoire compte comme tenue.

## Limites connues

- Le langage des effets (quatre formes, feuilles, constantes mesurées, sept
  opérations dont `premiere_de` et l'observation `portee` ; pour la valeur
  écrite et les conditions, `ici`, `val`, les quatre opérations, `inf` et
  `egal`) est fourni. La
  gravité n'y est plus : la mère la compose. Une portée suppose que l'action
  remplisse une case à la fois, et elle n'est complète que si l'exploration a
  vu l'action remplir chacune de ses cases. Un état qui défile est décrit
  (§ 3), mais partiellement : ce qui entre par le bord et la place suivante du
  mobile ne sont pas prévus, et l'état caché (l'élan de Jumper) est seulement
  signalé. Un défilement à deux dimensions (la mère ne connaît pas les
  rangées) laisse des cases « fixes » en bout de rangée.
- Les expériences n'essaient que les valeurs vues dans les arguments de
  l'exemple ; un coup qui ne change rien de visible et qui ne renvoie rien
  (ou pas ce qu'il renvoie d'habitude) est pris pour un coup refusé. Deux programmes qui résistent aux 40 expériences
  sont déclarés indiscernables, pas prouvés équivalents.
- Découpage des tours : un getter de confirmation appelé juste après le coup
  (`get, play, get`) est rattaché au tour suivant.
- Un joueur seul (§ 6) : le fils ne fait que reconnaître (souvenirs, petits
  motifs d'un coup), sans règle construite : les concepts parlent de `gagne`
  et de `suivant`. Un petit motif est vérifié sur les cas vus dans le labo
  (une seule graine pour Jumper), pas sur des positions imaginées : la mère ne
  sait pas fabriquer une position de Jumper (elle ne place pas d'obstacle).
  L'horizon suppose que les deux suites se rejoignent ; sinon il vaut 40. La
  mère juge sur ce qu'elle voit : deux positions identiques à l'écran mais pas
  dans le jeu (un élan caché) sont confondues. Un état en liste dont le jeu
  refuse parfois une action n'est éduqué que si la mère prévoit l'état
  d'après en entier (où l'action écrit, et quoi : Hanoï, le Compte est bon) ;
  sinon (un défilement), seule la borne « toujours » existe.
- Plus de deux joueurs : une fin ne vaut que victoire (le gagnant) ou défaite
  (tous les autres), ou nul pour tous ; pas de classement, pas de victoire
  partagée. Un concept parle des coups d'un joueur à la fois (aucune alliance
  ni « les deux autres ensemble »), et les variantes ne revoient que le coup
  du joueur qui joue juste avant le fils. Le fils qui trouve autant de pions
  à chacun ne sait pas qui commence : il suppose le premier joueur de
  l'exemple.
- Éducation à deux joueurs ou plus : seulement pour des joueurs qui jouent
  chacun leur tour, dans un ordre fixe (un cycle lu dans l'exemple : pas de
  joueur qui passe ou rejoue, pas d'ordre qui s'inverse), et un état
  qui est soit un tableau dont chaque action remplit une case du pion du
  joueur (Morpion, Puissance 4), soit un tableau dont l'action écrit des
  valeurs décrites par un programme (le Nim), soit un nombre (les
  Allumettes). Un état d'une autre sorte (texte, liste de longueur variable,
  plusieurs variables à la fois) n'est pas éduqué, ni une action qui pose un
  pion **et** vide une autre case (un déplacement de pion, aux dames :
  plusieurs parties dont l'une écrit le pion du joueur). Les actions sont
  explorées autour des valeurs de l'exemple : une action qu'aucune valeur
  voisine ne laisse deviner (un entier isolé loin des autres, un texte
  jamais vu) reste inconnue.
- Actions à plusieurs arguments : chaque argument est exploré à partir des
  valeurs vues pour lui, les autres prenant les valeurs de l'exemple ; une
  combinaison que ni l'exemple ni l'exploration n'a vue acceptée n'est pas
  une action (au Compte est bon, 36 des 64 combinaisons sur le tirage du
  labo). Une portée rangée par argument n'est complète que si le labo a vu
  l'action remplir chacune de ses cases (à Hanoï, le fils ignore 2 des 78
  coups permis). Une condition est une ou deux comparaisons entre un terme
  et une feuille : une règle qui demande plus (« la somme des tas… ») est
  hors de portée, et la mère le dit ; avec peu de coups refusés, une
  coïncidence de même taille peut gagner (au Compte est bon, `inf(arg0, ici)`
  sur la graine 0). « Selon un argument » ne vaut que pour la valeur écrite
  et un argument à 8 valeurs au plus.
- Une fin comprise par son état exact (Nim, Hanoï, Compte est bon) ne vaut
  que pour cet état : au Compte est bon, la mère ne reconnaît comme victoire
  que l'état final de l'exemple (la cible à la place 2), pas « la cible
  apparaît quelque part ». Une fin ailleurs n'est pas comprise : comptée
  nulle à deux, sans valeur seul (jamais une victoire).
- Pour un nombre, les actions permises sont décrites par des bornes sur la
  valeur d'après (fournies à la main : toujours, au moins, au plus, entre),
  mesurées sur ce qu'elle a vu. Une fin de partie est une valeur exacte, pas
  une condition (« moins de 2 ») : elle ne vaut que pour les valeurs vues, et
  qui la gagne vient de l'exemple. Une fin que l'exemple ne montre pas (aux
  Allumettes, prendre les deux dernières) reste incomprise et comptée nulle :
  la mère n'a aucun moyen de lire le gagnant d'une partie du labo.
- Les concepts sont construits par la mère, mais leur langage (les quatre
  sortes de nœuds) est fourni. Ses concepts sont parfois
  difficiles à lire : ils sont justes sur tous les cas vus, pas forcément
  élégants. Un concept validé sur peu de cas peut être une coïncidence ; il
  est corrigé quand une erreur le contredit.
- Les symétries sont des renumérotations de cases : elles supposent qu'une
  action remplit une case. Leur vérification par 20 parties au hasard est
  une épreuve, pas une preuve.
- Les concepts regardent au plus deux coups plus loin que la règle (deux
  niveaux de `AuMoins`) : assez pour le Morpion, pas pour un jeu dont les
  pièges sont plus profonds (Puissance 4). Il faudra alors des briques
  composées plus loin, ou des suites forcées.
- `gagne(etat, joueur)` sait dire qu'un coup fait **perdre** celui qui le joue
  quand la position porte le trait : une valeur (variante des Allumettes
  jouée jusqu'au bout, § 6) ou un tableau sans pions (Nim misère). Pas
  encore pour un tableau à pions : la contre-épreuve suppose que le joueur
  qui finit la partie avec un motif la gagne.
- Les concepts regardent au plus deux coups plus loin : aux Allumettes, la
  mère trouve « laisser 5 » mais pas la période 4 (« laisser 9, 13… ») ; au
  delà de ce qu'il a vu, le fils garde des souvenirs par quantité, ou perd.
  Une équivalence « la même situation, 4 allumettes plus haut » serait une
  symétrie qui n'est pas une renumérotation.
- Le squelette joue la plus petite des actions qu'une règle propose : une
  règle peut accepter un mauvais coup que ce choix écarte (variante jouée
  jusqu'au bout : prendre la dernière allumette, § 6).
- Les motifs de fin et les souvenirs (petits motifs) sont généralisés par
  décalage d'indice. Les règles, elles, ne parlent pas encore de petits
  motifs : un concept ne peut pas dire « je crée cette configuration ».
- La vérification d'un petit motif par 20 positions imaginées est une
  épreuve, pas une preuve : il faut que le professeur joue le coup du motif
  dans au moins la moitié d'entre elles, et que ce coup ne soit pire dans aucune.
- La qualité d'un fils n'est mesurée que par ses résultats (victoires,
  durée, au moins aussi bien que le professeur). Rien ne dit encore s'il a
  compris ou retenu : à Hanoï, il range la pile en 7 coups mais seulement
  depuis 15 positions sur 27. Le bulletin du fils (taille, compression,
  origine des coups, généralisation à des positions jamais vues, solidité,
  stabilité) est conçu dans `docs/feuille-de-route.md`, « Le bulletin du
  fils », et reste à écrire.
