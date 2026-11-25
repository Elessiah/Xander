# Feuille de route

## Où en est le projet

| Étape | État |
|---|---|
| Lire un exemple de partie | fait |
| Rejouer l'exemple et observer chaque valeur | fait |
| Déduire l'effet des fonctions (opérations) | fait : programmes construits par la mère, langage fourni |
| Associer getters et setters aux variables | fait |
| Comprendre le déroulé d'un tour | fait |
| Déduire les conditions de victoire | fait : motifs trouvés par contre-épreuve |
| Créer un fils qui part de zéro | fait |
| Corriger le fils cas par cas (souvenirs) | fait |
| Refactoriser : des souvenirs aux règles, concepts construits par la mère | fait, Morpion : fils imbattable |
| Découvrir les symétries (positions équivalentes) | fait, vérifiées dans le labo |
| Petits motifs : un souvenir réduit à ce qui comptait, reconnu partout | fait, vérifiés dans le labo |
| Réutiliser l'expérience d'un fils pour un autre | **plus tard** |

## Prochaines étapes proposées

**Retirer les aides orientées.** Objectif : que la mère n'ait plus que des
briques générales. État des aides qu'on lui donne encore, de la plus taillée
pour un jeu à la plus structurelle :

| Aide | État |
|---|---|
| Les actions sont les indices du plateau (`range(len(state))`) | **retirée** : elle explore autour des valeurs de l'exemple |
| L'adversaire au hasard appelle `get_game_state` et `play` | **retirée** : il utilise les noms appris dans l'exemple |
| `premiere(x, pas, v)`, la gravité toute faite | **retirée** (étape 4) : elle compose `premiere_de(portee(arg0), valant(' '))` |
| Une seule expérience pour voir une portée : rejouer la même action depuis le début | reste ; à remplacer par des expériences qu'elle choisit (curiosité) ou par un ordre déduit de tout ce qu'elle a vu |
| `valant` compare aussi le texte (`"4"` et `4`), une conversion cachée pensée pour le Morpion | reste ; à rendre explicite (une brique `texte(x)`). Coût : au Morpion, `case(arg0)` et `valant(arg0)` ne seraient plus départageables du tout, et le jeu d'essai qui les départage est à refaire |
| Une case changée reçoit le pion du joueur | reste ; la mère devrait décrire la valeur écrite comme elle décrit la case |
| Une case libre est une case sans pion ; pions appris par parité de coup ; positions lues en `M` / `A` / `.` | reste ; c'est le cadre « plateau à pions » de toute l'éducation, qui touche aussi l'entraînement (à coordonner) |

1. **Analyzer plus général.** C'est lui qui donne à la mère le vocabulaire
   pour percevoir un jeu. La mère construit la description de l'action avec
   un petit langage (étape 1 : elle retrouve seule les anciennes hypothèses,
   et celles de même taille coexistent). Le programme trouvé est le `apres`
   qu'elle écrit dans le fils et avec lequel elle pense (étape 2). Elle le
   met à l'épreuve dans le labo, d'abord par des expériences qui départagent,
   puis pour réfuter ce qui reste (étape 3). Elle compose elle-même la
   gravité du Puissance 4 (étape 4, ci-dessous).
   Reste à décrire la valeur écrite (aujourd'hui le pion du joueur, supposé)
   et celle des Allumettes (quantité). Piste : un coup refusé est aussi une
   observation (`valant(arg0)` annonce qu'une case occupée ne change rien),
   qui pourrait apprendre `possibles`.

   **Étape 4 (faite) : découvrir la gravité au lieu de la fournir.** La
   brique `premiere(x, pas, v)`, écrite à la main, est remplacée par des
   briques plus petites que la mère compose elle-même :
   - **les cases liées à une action**, observées et non calculées : en
     rejouant une action dans le labo, la mère voit déjà quelles cases elle
     remplit, dans quel ordre (`PORTEES` : au Puissance 4, la colonne de bas
     en haut). C'est l'opération `portee(x)`, à la place de la file
     « *x*, *x* + *pas*… » calculée avec des constantes ;
   - **un ordre et un choix** : « la première case d'une suite qui vérifie
     une condition », où la condition est un terme déjà connu (`valant(v)`,
     la valeur qu'avaient les cases changées). La gravité devient alors une
     composition, `premiere_de(portee(arg0), valant(' '))`, que la mère
     construit et vérifie sur les cas ;
   - **vérifié par les tests** : au Puissance 4, elle trouve cette
     composition ; au Morpion elle garde `case(arg0)` ; une gravité vers le
     haut (la file part de *c* + 35 et descend de 7, jeu d'essai) s'écrit de
     la même façon. Sur un exemple joué seulement sur la rangée du bas, elle
     croit d'abord `case(arg0)`, le labo le réfute, et elle apprend du
     contre-exemple jusqu'à la gravité.

   Ce qui reste fourni à la main : « la première d'une suite qui
   vérifie… » (une brique d'ordre, générale) et la façon d'observer une
   portée (rejouer la même action depuis le début). L'Analyzer seul, sans
   labo, ne comprend plus le Puissance 4 : il faut rejouer les actions.
2. **Puissance 4 : une éducation praticable.** Tout fonctionne de bout en
   bout : l'Analyzer comprend la gravité, la mère retrouve des alignements
   horizontaux, verticaux et diagonaux et le miroir gauche-droite, corrige et
   réduit les souvenirs. Deux problèmes. Les petits motifs y sont mal
   vérifiés : après 3 parties, 391 souvenirs, presque tous des motifs décalés
   que les positions imaginées au hasard « confirment » parce que le
   professeur y joue souvent le centre. Et une partie prend 2 à 8 minutes : chaque
   jugement fait finir la partie deux fois au professeur (environ 0,7 s), et
   la réduction d'un souvenir en petit motif demande des centaines de
   jugements. Pistes : juger moins de positions (variantes, positions
   imaginées), réutiliser les jugements entre positions équivalentes, et des
   concepts qui regardent plus loin (les pièges du Puissance 4 sont plus
   profonds que deux coups).
3. **Petits motifs dans les règles.** Les motifs de fin et les souvenirs se
   décalent déjà : un souvenir est réduit aux cases qui comptaient, puis
   reconnu partout (vérifié dans le labo). Il reste à en faire des briques
   (« jouer un coup qui crée cette configuration »), et à les essayer sur un
   grand plateau. Au Morpion, presque toutes les cases comptent, et les
   petits motifs gardent 6 à 7 cases sur 9.
4. **Symétries plus générales.** Aujourd'hui des renumérotations de cases.
   Il faudra des équivalences qui ne sont pas des permutations (échanger les
   deux joueurs, une quantité décalée).
5. **Concepts plus lisibles.** La mère construit ses concepts, mais certains
   sont des combinaisons difficiles à lire, ou des coïncidences validées sur
   peu de cas. Pistes : préférer le concept qui explique le plus de cas,
   relire les concepts quand une nouvelle brique apparaît, et dire ce que le
   langage fournit encore à la main (les nœuds `Non`, `Et`, `AuMoins` avec
   k = 1, la forme « jouer une action après laquelle… »). `gagne` doit aussi apprendre qu'un coup peut faire perdre celui qui
   le joue (Allumettes « misère »), ce qui demande de percevoir le trait.
6. **Autres formes de problèmes.** Jeux à un joueur (Jumper), plus de deux
   joueurs, état qui n'est pas un tableau.
7. **Plus tard : l'expérience.** Partir des apprentissages réussis (motifs,
   règles) d'un fils pour en élever un autre plus vite.

## Nettoyage et corrections de cette révision

Structure :

- Le cœur, éparpillé entre `Class/`, `old/Class/` et `old/src/` (en partie
  cassé au dernier commit « Save »), est regroupé dans le paquet `xander/`.
  La logique d'analyse reprend la version la plus complète
  (`src/Proceed_parsed_result.py` de l'avant-dernier commit), corrigée.
- `test/` (essais de subprocess, de pointeurs de fonction…) est remplacé par de
  vrais tests dans `tests/`.
- Fichiers générés et `__pycache__` retirés du dépôt, `.gitignore` ajouté.
- `mainMorpion.py` et `mainAllumettes.py` sont remplacés par
  `python -m Games.GamePlayer`, qui ne lance plus de parties à l'import.

Bugs corrigés dans la logique mère :

- `ParseExample.__init__` appelait l'analyse d'une ligne sur le nom du fichier
  au lieu de lire le fichier ; `learn()` utilisait une variable inexistante.
- Une ligne de code en fin de fichier sans retour à la ligne était ignorée ou
  faisait planter le parseur (`IndexError`).
- `# end player X` donnait `"p"` comme gagnant (un seul caractère lu).
- Une fonction sans valeur de retour était classée `OUTPUT`/`INOUT` (test sur
  `is not None` d'une variable vide).
- `Function(operations=[])` : liste par défaut partagée entre toutes les
  fonctions.
- `__cmp__` n'existe plus en Python 3 : les comparaisons de fonctions et
  d'opérations ne marchaient pas (et `Operation` n'était pas hachable).
- Le lissage supprimait des clés d'un dictionnaire pendant son parcours et
  comparait au nombre total d'appels au lieu du nombre d'appels de la fonction.
- Les paramètres restaient des chaînes : `prev - "3"` plantait.
- `SRC_DEST_TARGET_NAME` lisait deux fois le premier paramètre ; les tests
  « src/dest » utilisaient `or` au lieu de `and`.
- Le rejeu utilisait `python3` (absent sous Windows) et des chemins relatifs
  au dossier courant ; il passe maintenant par `sys.executable` et la sortie
  standard.
- `get_env_from_parsed_file` comparait une `Variable` à `"game"` ;
  `get_nb_actions_per_turn` comptait les intervalles à l'envers.
- L'exemple Morpion tirait le premier joueur au sort : le rejeu ne
  correspondait pas à l'exemple.

Bugs corrigés dans les jeux :

- `curses.ascii` n'existe pas sous Windows : Morpion et MinmaxMorpion ne
  s'importaient pas.
- Morpion : `play(9)` plantait (`>` au lieu de `>=`) ; `back()` ne rendait pas
  la main au bon joueur.
- MinmaxMorpion : `best_score = best_score`, simulation qui jouait sur le
  mauvais tableau, conditions de fin jamais vraies, et choix possible d'une case
  occupée qui bloquait la partie en boucle. Remplacé par un vrai minimax qui
  garde l'heuristique d'origine pour départager les coups.
- Allumettes : stratégie Minmax fausse (période 3 au lieu de 4),
  `start_player` jamais mémorisé, `set_game_state` qui changeait de joueur,
  prise de plus d'allumettes qu'il n'en reste.
- Puissance 4 : vérification de victoire en boucle infinie, `Coords` avec une
  largeur de 3, pas de changement de joueur ni de détection de fin. Terminé.
- Coords : le constructeur ne calculait pas l'indice `i`.
- Jumper : `get_board()` renvoyait le décor sans joueur ni obstacles,
  collisions décalées d'une case, `back()` sans effet ; `mainJumper` ne
  fonctionnait que sous Linux.
