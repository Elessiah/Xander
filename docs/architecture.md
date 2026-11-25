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

Ce qui est encore fourni à la main : les deux formes (`apres`, `changees`), les
feuilles et les sortes de constantes, les sept opérations (dont
`premiere_de`, une brique d'ordre générale), la façon de déduire l'ordre
d'une portée (une case remplie alors qu'une autre était dans le même état
vient avant elle), les trois descriptions de la valeur écrite et les trois de
la case libre, la taille maximale des programmes (5 nœuds) et le minimum de
deux cas.

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
   Elle vérifie aussi que, dans l'exemple, deux joueurs jouent chacun leur
   tour : c'est ce qui lui permet ensuite de reconnaître le joueur à la parité
   du coup. Sinon, elle dit qu'elle ne sait pas encore éduquer de fils.

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
   cas (Jumper), elle sait qu'elle n'a pas compris l'action.
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
   professeur), une fois X, une fois O.
4. **Revue des décisions.** Pour chaque coup du fils, la mère demande son
   coup au professeur. S'il diffère, elle fait finir la partie au professeur
   des deux côtés, après chacun des deux coups. Si le coup du professeur mène
   à un meilleur résultat, c'est une **erreur**. Elle revoit aussi les
   **variantes** : avec `back`, elle essaie chaque autre coup de l'adversaire
   (« et s'il avait joué là ? ») et revoit la réponse du fils.
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

Avec les petits motifs, le fils fait environ 16 erreurs avant d'être parfait,
contre 24 à 44 sans eux. L'éducation est aussi deux à trois fois plus rapide,
car il y a moins de cas à revoir.

## 7. Motifs décalés et symétries — `xander/symmetries.py`

**Un motif marcherait-il ailleurs ?** Dès qu'elle comprend un motif, la mère
fait l'hypothèse qu'il vaut aussi décalé (chaque case + d) et la vérifie dans
le labo : le premier joueur pose ses pions sur le motif décalé, l'autre joue
ailleurs, et la contre-épreuve dit quel motif a fini la partie. Elle ne sait
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
adverse : « et si cette case avait été la sienne ? ». Sans cela, un jeton qui
en soutient un autre semblerait faire partie de l'alignement.

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
gauche-droite : renversé, le jeu ne tombe plus au même endroit.

Le fils reçoit la liste `SYMETRIES` : pour retrouver un souvenir, il regarde
sa position sous chacune des 8 façons de la voir, et renumérote le coup
retenu. Un refactor compte deux positions équivalentes comme un seul
souvenir.

### Petits motifs : ce qui comptait, reconnu partout

Un maître d'échecs ne retient pas des positions entières : il reconnaît des
configurations de quelques pièces (Chase et Simon). La mère fait de même avec
ses souvenirs, en deux questions, toutes deux vérifiées dans le labo.

**« Qu'est-ce qui comptait ? »** Un souvenir `MM.AA....` → 2 (`M` : mes pions,
`A` : les siens, `.` : libre au sens qu'elle a appris, `#` : autre chose)
devient un **petit motif** : les cases qui ne
comptent pas deviennent `?`. Un petit motif tient si son coup est le bon
partout où il apparaît. La mère le vérifie de deux façons :

- dans tous les cas enregistrés, sous chaque façon de les voir : le coup doit
  y être aussi bon que celui du professeur ;
- dans 20 positions qu'elle imagine dans le labo. Les `?` y sont remplis au
  hasard (pions de l'un, de l'autre, ou cases libres), le fils jouant en
  premier ou en second. Elle écarte une position où la partie est déjà
  finie, ou qu'aucune suite de coups n'atteint (avec la gravité, un pion ne
  flotte pas). Elle demande son coup au professeur. S'il joue le coup du
  motif, la position le **confirme**. S'il joue ailleurs, elle vérifie que le
  coup du motif est aussi bon que le sien, en lui faisant finir la partie :
  sinon le motif est **démenti**, sinon la position ne dit rien. Il faut
  qu'au moins la moitié des positions le confirment.

Pourquoi ne pas se contenter de « aussi bon » ? Au Morpion, un coup change
souvent l'issue d'une partie. Au Puissance 4, presque jamais : finie par le
professeur des deux côtés, une partie se termine de la même façon quel que
soit le coup joué. « Aussi bon » y laisse donc passer presque tout. Demander
au professeur ce qu'il jouerait est plus exigeant, et bien moins cher (un
coup au lieu de deux fins de partie).

**Au Puissance 4, cela ne suffit pas encore.** Après 3 parties, la mère garde
391 souvenirs, dont environ 400 petits motifs décalés, et des motifs absurdes
passent encore (« la case 3 est libre : y jouer »). Le professeur joue la
colonne du centre dans la plupart des positions imaginées au hasard : elles
« confirment » un motif qui ne dit rien de la position. Il faudra des
positions imaginées plus proches de vraies parties, ou une autre épreuve.

Elle cherche le **plus petit** motif qui tient : d'abord avec 0 case en plus
de la case jouée, puis 1, 2 et 3 cases (`chunk_size`). Si aucun ne tient, elle
oublie les cases une à une et garde chaque oubli qui tient (sur un grand
plateau, les combinaisons seraient trop nombreuses). Ici, elle trouve
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

Au Morpion, les petits motifs restent assez grands : 6 à 7 cases sur 9. Sur
un plateau aussi petit, presque toutes les cases comptent pour la tactique.
Un motif est parfois vrai d'une façon inattendue, par exemple parce que
toutes les positions qui le contiennent sont perdues de toute façon. Aucun
petit motif n'a été démenti sur 10 graines et 400 parties.

## 8. Les briques — `xander/concepts.py`

Un concept est un **arbre** (une structure Python, pas du texte, pas de
modèle de langage) qui décrit une position du point de vue de « moi ». Il
s'écrit uniquement avec les quatre notions que la mère apprend pour chaque
jeu : `possibles(etat)`, `apres(etat, action, joueur)` (vient de l'Analyzer),
`gagne(etat, joueur)` (la fin de partie comprise par contre-épreuve) et
`adversaire(joueur)`.

| Nœud | Sens |
| --- | --- |
| `Brique(nom, J)` | une brique connue, vue du côté de J (moi ou lui) ; au départ, seulement `gagne` |
| `Non(x)`, `Et(x, y)` | négation, conjonction |
| `AuMoins(k, J, x)` | au moins k actions de J mènent à une position où x est vrai ; par défaut k = 1 : « il existe une action de J après laquelle x » |

Une règle se lit « jouer une action après laquelle le concept est vrai » ;
une règle qui accepte toutes les actions ne choisit rien et est ignorée. La
mère énumère les arbres par taille croissante (jusqu'à 6 nœuds, 2 niveaux de
`AuMoins`), et confond deux arbres qui disent la même chose sur un
échantillon de positions imaginées : on garde le plus petit. Chaque concept
adopté devient une brique, d'où des concepts plus grands à taille égale
(composition, comme les configurations de Chase et Simon).

**Fourni à la main** : ces quatre sortes de nœuds (avec k = 1, c'est la
logique minimale : non, et, il existe), les bornes de la recherche, le budget
du fils, et la forme d'une règle (« jouer une action après laquelle… »). Le vocabulaire écrit à la
main (`xander/vocabulary.py` : `gagner`, `parer`, `fourchette`,
`contre_fourchette`, `attaque`) ne sert plus qu'aux tests, pour comparer.

## 9. Le fils — `xander/son_writer.py`

Le fils est un **fichier Python autonome**, écrit par la mère, réécrit après
chaque correction, qui n'importe rien de Xander :

1. **Perception** : `possibles`, `apres`, `gagne`, `adversaire`, écrites à
   partir de ce qu'elle a compris, plus `case_jouee`, `action_pour` et
   `VUES`, le compteur des positions regardées. `apres` recopie le programme
   qu'elle a construit pour décrire l'action (§ 3), traduit en Python
   (`changees(avant, args)`, ou `valeur_apres` pour un nombre) : ce qu'elle a
   vérifié sur les cas est exactement ce que le fils exécute. La case jouée est
   la seule case que le programme annonce, si elle est libre (`libre`, telle
   que la mère l'a décrite, § 3) ; elle reçoit la valeur écrite qu'elle a
   décrite (au Morpion, `joueur`). La clé d'une position (`cle`) se lit sur la
   position elle-même, puis se renumérote pour chaque symétrie.
   `possibles` garde les actions que le jeu accepte au départ et qui
   remplissent une case ; `action_pour` vient des portées déduites de
   l'exploration. La mère pense avec la même perception. Si plusieurs programmes de
   même taille coexistent, elle prend le premier trouvé.
2. **Règles** : les concepts qu'elle a construits et appris au fils, **et
   seulement ceux-là** (avec les briques dont ils dépendent), traduits en
   Python, `REGLES` dans l'ordre appris, `SOUVENIRS` et `SYMETRIES`.
3. **Squelette** : `choisir` (souvenir, sinon première règle qui choisit,
   sinon première action possible) et `play(game)`. C'est ici qu'on pourra
   plus tard transmettre l'expérience de ses frères.

Le fils exécute son code bêtement : il ne simule que ce que ses règles
demandent, sans mémoire, et n'appelle jamais `back` ; si le jeu refuse un
coup, l'état n'a pas changé et il en essaie un autre. **Budget** : la mère
refuse un refactor qui ferait regarder au fils plus de 1 000 positions pour
un coup (un minimax complet en regarde plus de 500 000 au premier coup du
Morpion) ; un test le vérifie sur toutes les positions.

`Mother.raise_son(exemple, professeur)` renvoie l'éducation (fils, parties,
leçons, refactors) ; `Mother.create_son(nom, exemple, professeur=…)` écrit le
fils dans `output/sons/<nom>.py`.

## Limites connues

- Le langage des effets (deux formes, feuilles, constantes mesurées, sept
  opérations dont `premiere_de` et l'observation `portee`) est fourni. La
  gravité n'y est plus : la mère la compose. Une portée suppose que l'action
  remplisse une case à la fois, et elle n'est complète que si l'exploration a
  vu l'action remplir chacune de ses cases. Un jeu dont l'état défile (Jumper) n'est pas encore décrit.
- Les expériences n'essaient que les valeurs vues dans les arguments de
  l'exemple ; un coup qui ne change rien de visible est pris pour un coup
  refusé et n'apprend rien. Deux programmes qui résistent aux 40 expériences
  sont déclarés indiscernables, pas prouvés équivalents.
- Découpage des tours : un getter de confirmation appelé juste après le coup
  (`get, play, get`) est rattaché au tour suivant.
- Éducation : seulement pour deux joueurs qui alternent, un état en tableau et
  une action qui remplit une case (le programme trouvé annonce une seule case
  changée), à un seul argument. Les actions sont explorées autour des valeurs
  de l'exemple : une action qu'aucune valeur voisine ne laisse deviner (un
  entier isolé loin des autres, un texte jamais vu) reste inconnue. Les
  Allumettes (quantité) attendent que la
  perception sache décrire une quantité.
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
- `gagne(etat, joueur)` ne sait pas encore dire qu'un coup fait **perdre**
  celui qui le joue (Allumettes « misère » : prendre la dernière perd). Il
  faudra que la perception sache qui a le trait.
- Les motifs de fin et les souvenirs (petits motifs) sont généralisés par
  décalage d'indice. Les règles, elles, ne parlent pas encore de petits
  motifs : un concept ne peut pas dire « je crée cette configuration ».
- La vérification d'un petit motif par 20 positions imaginées est une
  épreuve, pas une preuve : il faut que le professeur joue le coup du motif
  dans au moins la moitié d'entre elles, et que ce coup ne soit pire dans aucune.
