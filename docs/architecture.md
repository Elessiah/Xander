# Architecture de la logique mère

```text
 res/exampleX.py
      │  parser.py          lecture des sections, des appels et des types
      ▼
 ParsedExample  ── variables, fonctions horodatées, joueurs, gagnant
      │  rebuilder.py       réécriture en script + exécution dans un sous-processus
      ▼
 observations   ── {time: valeur renvoyée}
      │  analyzer.py        comparaison avant / après chaque coup
      ▼
 AnalysisReport ── opérations par fonction, getters / setters par variable
      │  game_model.py      synthèse : joueurs, déroulé d'un tour, annulation
      ▼
 GameModel
      │  education.py       la mère élève le fils : parties, erreurs, explications
      │  lab.py             (une vraie partie qu'elle rejoue et défait avec back)
      ▼
 Son (son.py)   ── motifs, règles ordonnées, souvenirs ; joue sans back
      ▼
 output/sons/<nom>.py
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

On teste ensuite des hypothèses codées en dur, dans l'ordre, et on garde la
première qui colle (`FunctionOperation`) :

| Avant / après | Paramètres | Hypothèses |
|---|---|---|
| tableaux | 1 | `SINGLE_TARGET_INDEX` (seule la case d'indice *p* change), puis `SINGLE_TARGET_NAME` (seules les cases valant *p* changent) |
| tableaux | 2 | `SRC_DEST_TARGET_INDEX`, puis `SRC_DEST_TARGET_NAME` (deux cases changent : un déplacement) |
| nombres | 1 | `QUANTITY_RM` (−*p*), `QUANTITY_ADD` (+*p*), `QUANTITY_SET` (= *p*) |

**Lissage.** Un coup particulier peut tromper une hypothèse (la fin de partie,
une coïncidence de valeurs…). Pour chaque fonction, on ne garde que les
opérations observées sur au moins la moitié de ses appels (`MAJORITY`), et on
les applique à tous ses appels. Les appels pour lesquels rien n'a été trouvé
sont listés dans `AnalysisReport.unknown_calls`.

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

1. **Leçon de l'exemple.** La mère rejoue l'exemple, vérifie que l'action
   modifie bien la case annoncée par l'Analyzer, apprend quel pion pose
   chaque joueur, puis comprend pourquoi la partie finit (ci-dessous).
2. **Comprendre une fin de partie (contre-épreuve).** Pour chaque pion du
   joueur qui a fini la partie, la mère rejoue la partie en posant ce pion
   ailleurs. Si la partie ne s'arrête plus, le pion était nécessaire. Le
   dernier coup et les pions nécessaires forment un **motif** (au Morpion, un
   alignement). Une fin sans motif est un nul.
3. **Parties.** Le fils joue contre le professeur et contre un joueur au
   hasard, une fois X, une fois O.
4. **Revue des décisions.** Pour chaque coup du fils, la mère demande son
   coup au professeur. S'il diffère, elle fait finir la partie au professeur
   des deux côtés, après chacun des deux coups. Si le coup du professeur mène
   à un meilleur résultat, c'est une **erreur**.
5. **Explication.** La mère cherche dans son vocabulaire un concept vrai pour
   le coup du professeur et faux pour celui du fils : `gagner`, `parer`,
   `fourchette`, `contre_fourchette`, `carrefour` (définis sur les motifs,
   pas sur un jeu). Le concept devient une **règle**, insérée juste avant la
   règle qui a trompé le fils : la mère apprend ainsi l'ordre des priorités.
   Sans explication, la position devient un **souvenir**.

Au Morpion, en partant de zéro (200 parties, moins d'une seconde) : les 8
alignements sont découverts, les règles finissent dans l'ordre
`gagner > parer > fourchette > contre_fourchette > carrefour`, avec 8
souvenirs (surtout des ouvertures). Un test explore toutes les suites de
coups adverses possibles : le fils ne peut plus perdre.

## 7. Le fils — `xander/son.py`

Le fils ne contient que des connaissances (`KNOWLEDGE`) : comment lire l'état
et jouer, les pions, les motifs, les règles dans l'ordre, les souvenirs. À
son tour : souvenir de la position, sinon première règle qui s'applique,
sinon première case libre. Il ne simule rien et n'appelle jamais `back` ; si
le jeu refuse un coup, l'état n'a pas changé et il en essaie un autre.

`Mother.raise_son(exemple, professeur)` renvoie l'éducation (fils, parties,
leçons) ; `Mother.create_son(nom, exemple, professeur=…)` écrit le fils dans
`output/sons/<nom>.py`.

## Limites connues

- Les hypothèses sont codées en dur : un jeu dont l'état défile (Jumper)
  n'est compris par aucune d'elles, et c'est attendu à ce stade.
- La première hypothèse compatible l'emporte : au Morpion, où la case *n*
  contient le texte `"n"`, `SINGLE_TARGET_INDEX` et `SINGLE_TARGET_NAME` sont
  toutes deux vraies, seule la première est retenue.
- Le lissage majoritaire peut généraliser une coïncidence : au Puissance 4,
  tant qu'on joue sur la rangée du bas, l'indice de la case vaut le numéro de
  colonne, et `SINGLE_TARGET_INDEX` est retenu à tort. Des exemples variés
  limitent ce risque.
- Découpage des tours : un getter de confirmation appelé juste après le coup
  (`get, play, get`) est rattaché au tour suivant.
- Éducation : seulement pour deux joueurs qui alternent, un état en tableau et
  une action qui désigne directement une case (`SINGLE_TARGET_INDEX`). Le
  Puissance 4 (gravité) et les Allumettes (quantité) attendent que l'Analyzer
  sache décrire leur action.
- Le vocabulaire d'explications est fourni à la main. Il est général (motifs,
  cases), mais la mère devra un jour le découvrir seule.
- Les motifs sont des ensembles de cases précis : la mère ne généralise pas
  encore un alignement par translation ou symétrie (indispensable au
  Puissance 4).
