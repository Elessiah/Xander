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
| Réutiliser l'expérience d'un fils pour un autre | **plus tard** |

## Prochaines étapes proposées

1. **Analyzer plus général.** C'est lui qui donne à la mère le vocabulaire
   pour percevoir un jeu. La mère construit déjà la description de l'action
   avec un petit langage (étape 1, faite : elle retrouve seule les anciennes
   hypothèses, et celles de même taille coexistent). Suite :
   - fait (étape 2) : le programme trouvé est le `apres` que la mère écrit
     dans le fils et avec lequel elle pense. Reste à décrire la valeur écrite
     (aujourd'hui le pion du joueur, supposé) et à ne plus supposer ailleurs
     que l'argument d'un coup est la case jouée (`possibles`, contre-épreuve,
     symétries) ;
   - quand plusieurs programmes survivent, chercher dans le labo une
     expérience qui les départage ;
   - décrire l'action du Puissance 4 (« le jeton tombe dans la colonne *p* »)
     sans brique de gravité : les cases liées à un argument, puis la première
     libre dans un ordre.
2. **Configurations n'importe où.** Les motifs de fin se décalent déjà
   (vérifiés dans le labo). Il reste à faire de même pour ce qu'elle apprend :
   un souvenir ou une règle qui porte sur quelques cases, reconnu partout où
   cette configuration apparaît (indispensable au Puissance 4, dont le plateau
   n'a qu'une symétrie).
3. **Symétries plus générales.** Aujourd'hui des renumérotations de cases.
   Il faudra des équivalences qui ne sont pas des permutations (échanger les
   deux joueurs, une quantité décalée), et des motifs généraux (translation)
   pour le Puissance 4.
4. **Concepts plus lisibles.** La mère construit ses concepts, mais certains
   sont des combinaisons difficiles à lire, ou des coïncidences validées sur
   peu de cas. Pistes : préférer le concept qui explique le plus de cas,
   relire les concepts quand une nouvelle brique apparaît, et dire ce que le
   langage fournit encore à la main (les nœuds `Non`, `Et`, `AuMoins` avec
   k = 1, la forme « jouer une action après laquelle… »). `gagne` doit aussi apprendre qu'un coup peut faire perdre celui qui
   le joue (Allumettes « misère »), ce qui demande de percevoir le trait.
5. **Autres formes de problèmes.** Jeux à un joueur (Jumper), plus de deux
   joueurs, état qui n'est pas un tableau.
6. **Plus tard : l'expérience.** Partir des apprentissages réussis (motifs,
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
