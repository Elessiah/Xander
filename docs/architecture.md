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
   (section 7) vrai après le coup du professeur et faux après celui du fils
   dans **au moins deux** souvenirs. Elle l'essaie comme règle à chaque rang
   de priorité, du plus bas au plus haut. Le refactor est gardé si le fils
   joue encore bien dans **tous** les cas (vérifié dans le labo), si au moins
   deux souvenirs deviennent inutiles (ils sont oubliés) et si le fils reste
   dans son budget de réflexion. Le concept devient une **brique** pour les
   suivants. Enfin, elle retire les règles devenues inutiles (sans elles,
   tous les cas restent bien joués). Puis elle **réécrit le code du fils**.

La mère part **sans aucun concept**. Au Morpion, en 200 parties (une
vingtaine de secondes) : les 8 alignements sont découverts, et elle construit
seule ses règles. Selon les parties rencontrées, le chemin diffère. Avec une
graine, elle retrouve exactement `gagner > parer > fourchette >
contre_fourchette` :

```text
gagne(moi)                                   je gagne
Non(AuMoins(1, lui, gagne(lui)))             aucun de ses coups ne le fait gagner
AuMoins(2, moi, gagne(moi))                  au moins 2 de mes coups me font gagner
Non(AuMoins(1, lui, concept_2(lui)))         aucun de ses coups ne lui donne une fourchette
```

Avec une autre, elle fond « gagner ou parer » en un seul concept, ou trouve
des combinaisons que personne n'a écrites. Un test explore toutes les suites
de coups adverses possibles : le fils ne peut plus perdre. Sur 10 graines, 5 donnent un fils parfait dès 200 parties, 6 à 400 et 8 à 800 ; les 2 autres perdent encore sur une seule suite de coups, qu'elles n'ont pas rencontrée. C'est plus lent qu'avec le vocabulaire écrit à la main (17 sur 20 à 200 parties), mais c'est la mère qui apprend.

## 7. Les briques — `xander/concepts.py`

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
| `AuMoins(k, J, x)` | au moins k actions de J (k = 1 ou 2) mènent à une position où x est vrai |

Une règle se lit « jouer une action après laquelle le concept est vrai » ;
une règle qui accepte toutes les actions ne choisit rien et est ignorée. La
mère énumère les arbres par taille croissante (jusqu'à 6 nœuds, 2 niveaux de
`AuMoins`), et confond deux arbres qui disent la même chose sur un
échantillon de positions imaginées : on garde le plus petit. Chaque concept
adopté devient une brique, d'où des concepts plus grands à taille égale
(composition, comme les configurations de Chase et Simon).

**Fourni à la main** : ces quatre sortes de nœuds, les valeurs 1 et 2 de k,
les bornes de la recherche et le budget du fils. Le vocabulaire écrit à la
main (`xander/vocabulary.py` : `gagner`, `parer`, `fourchette`,
`contre_fourchette`, `attaque`) ne sert plus qu'aux tests, pour comparer.

## 8. Le fils — `xander/son_writer.py`

Le fils est un **fichier Python autonome**, écrit par la mère, réécrit après
chaque correction, qui n'importe rien de Xander :

1. **Perception** : `possibles`, `apres`, `gagne`, `adversaire`, écrites à
   partir de ce qu'elle a compris (pions observés, motifs, action
   `SINGLE_TARGET_INDEX`), plus `VUES`, le compteur des positions regardées.
2. **Règles** : les concepts qu'elle a construits et appris au fils, **et
   seulement ceux-là** (avec les briques dont ils dépendent), traduits en
   Python, `REGLES` dans l'ordre appris et `SOUVENIRS`.
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
- Les concepts sont construits par la mère, mais leur langage (les quatre
  sortes de nœuds, k = 1 ou 2) est fourni. Ses concepts sont parfois
  difficiles à lire : ils sont justes sur tous les cas vus, pas forcément
  élégants. Un concept validé sur peu de cas peut être une coïncidence ; il
  est corrigé quand une erreur le contredit.
- Les symétries (une position tournée de 90°) ne sont pas encore découvertes :
  chaque souvenir ne vaut que pour sa position exacte.
- `gagne(etat, joueur)` ne sait pas encore dire qu'un coup fait **perdre**
  celui qui le joue (Allumettes « misère » : prendre la dernière perd). Il
  faudra que la perception sache qui a le trait.
- Les motifs sont des ensembles de cases précis : la mère ne généralise pas
  encore un alignement par translation ou symétrie (indispensable au
  Puissance 4).
