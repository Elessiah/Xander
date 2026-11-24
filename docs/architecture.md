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
      │  mother.py          (à faire) génération et correction des enfants
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
d'un tour**. Les tours sont découpés quand le joueur change, ou quand un appel
qui lit suit un appel qui agit (nécessaire pour les jeux à un joueur comme
Jumper) ; on retient la longueur de tour la plus fréquente.

## 5. Enfants — `xander/mother.py`

`Mother.create_son(nom, exemple)` écrit `output/sons/<nom>.py` avec un
dictionnaire `KNOWLEDGE` (ce que la mère a compris) et une fonction
`play(game)` encore vide. C'est le point de départ de la suite du projet.

## Limites connues

- Les hypothèses sont codées en dur : un jeu dont l'état défile (Jumper)
  n'est compris par aucune d'elles, et c'est attendu à ce stade.
- La mère ne déduit pas encore les **conditions de victoire** (le gagnant de
  l'exemple est seulement lu dans `# end`).
- La première hypothèse compatible l'emporte : au Morpion, où la case *n*
  contient le texte `"n"`, `SINGLE_TARGET_INDEX` et `SINGLE_TARGET_NAME` sont
  toutes deux vraies, seule la première est retenue.
- Le lissage majoritaire peut généraliser une coïncidence : au Puissance 4,
  tant qu'on joue sur la rangée du bas, l'indice de la case vaut le numéro de
  colonne, et `SINGLE_TARGET_INDEX` est retenu à tort. Des exemples variés
  limitent ce risque.
