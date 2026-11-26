# Feuille de route

## Le cap : l'examen ARC

Première finalité (règles complètes dans `CLAUDE.md`, « Première finalité :
l'examen ARC ») : brancher le test ARC de François Chollet comme n'importe
quel test, sans avoir rien préparé sur ses tâches, et qu'un fils créé par la
mère le réussisse. Ce n'est pas pour tout de suite ; chaque étape doit nous
en rapprocher, et aucune ne doit être justifiée par ARC lui-même.

**Une tâche ARC, vue par Xander.** C'est un problème d'un genre que la mère
ne connaît pas encore : ni partie, ni adversaire, ni actions, mais quelques
paires « avant / après » et une entrée dont il faut deviner l'après. Elle
fait pourtant déjà la même chose en petit quand elle décrit `apres` : elle
cherche avec son langage le plus petit programme qui explique tous les cas
observés, puis le met à l'épreuve. Les paires d'exemples jouent le rôle des
souvenirs (les tests du refactor), et le programme trouvé devient le fils.
Ce qui manque, c'est surtout de la **généralité**.

Les jalons, dans l'ordre. Chacun se vérifie sur des problèmes qui ne sont
pas ARC.

1. **Des jeux aux problèmes.** La mère accepte n'importe quel problème sous
   une forme commune : un exemple est une suite d'observations (un état,
   ce qui s'est passé, l'état suivant), avec ou sans actions, avec deux
   joueurs, un seul ou aucun. D'abord l'étape 6 (Jumper, état qui n'est pas
   un tableau), puis un genre nouveau : **transformer une entrée en sortie**
   à partir de paires, sur des problèmes que nous inventons dans des
   domaines variés (listes, mots, nombres, plateaux de nos jeux), sans
   recopier ARC. Le fils est alors un programme qui répond, pas un joueur.
   *Un joueur seul : fait* (étape 6). Sans adversaire ni professeur, la mère
   juge un coup par ce qui arrive (la partie finit ou dure), avec `back` dans
   son labo ; elle décrit un état qui défile comme « l'état d'avant, décalé »,
   en disant ce qu'elle ne prévoit pas. Jumper et Partition (inventé pour
   cette étape) sont appris : un petit motif d'une case, trouvé par elle,
   tient sur des graines jamais vues.

   *Fait, première forme* (`docs/architecture.md`, § 10) : format JSON commun
   (des paires, des questions ; une paire est une observation sans action),
   recherche du plus petit programme avec 18 briques générales listées, chacune
   justifiée par deux domaines d'entraînement, deuxième essai réellement
   différent, « je ne trouve pas » plutôt qu'une invention, fils autonome qui
   répond. Entraînement (55 problèmes, a servi à régler) : 52 au premier essai,
   53 en deux. **Lot jamais vu** (34 problèmes écrits après le gel, commit
   e7e14f3, passés une fois) : **25/34 au premier essai, 25/34 en deux**, moins
   de 0,5 s par problème. Échecs : 3 programmes trop grands pour la taille 6
   (écart, allumettes en deux coups, mots de plus de trois lettres : jalon 2),
   5 notions absentes (moitié, pair, mettre à plat, voyelle, tout sauf le
   premier), 1 coïncidence (« le mot le plus long » pris pour « le deuxième
   mot ») ; et 1 bonne réponse pour une mauvaise raison (« les pions du
   joueur » compris comme « les pions de X »). Ce lot, lu pour ce
   bilan, compte désormais comme entraînement. À faire : un moteur commun avec
   `effets.py`, et des briques gardées ou découvertes plutôt que données.
2. **Un langage qui grandit.** Les concepts que la mère trouve deviennent des
   briques qu'elle garde d'un problème à l'autre (étapes 3 et 5). Ce qui
   reste fourni à la main se réduit à une liste courte et documentée,
   l'équipement de naissance (tableau « Retirer les aides orientées »). Et
   elle doit chercher des programmes plus grands sans tout énumérer, guidée
   par ce qu'elle observe (comme les portées vues dans le labo, étape 1).
3. **Percevoir.** L'Analyzer (étape 1) doit voir ce qu'un humain voit sans y
   penser : des **objets** (des cases voisines qui vont ensemble), leurs
   propriétés (taille, forme, valeur, position), leurs relations (contact,
   inclusion, alignement, même forme), des **quantités** (compter, comparer)
   et des **équivalences** qui ne sont pas des renumérotations (étape 4).
   Chaque notion arrive parce qu'un problème qui n'est pas ARC la demande, et
   la mère doit la retrouver seule sur un autre.
4. **Conclure à partir de peu.** Avec quelques paires seulement, plusieurs
   explications tiennent : il faut choisir (la plus courte, celle qui
   réutilise des briques connues), vérifier qu'elle explique **toutes** les
   paires, et savoir proposer un deuxième essai réellement différent quand le
   test en permet plusieurs. Lien avec l'étape 5 (coïncidences validées sur
   peu de cas).
5. **L'expérience.** Chaque fils part de zéro, mais la mère arrive à
   l'examen avec ce qu'elle a appris ailleurs. L'étape 8, prévue « plus
   tard », devient nécessaire.
6. **Examens blancs.** Écrire des jeux de problèmes inédits, les mettre sous
   scellé hors du dépôt (pour qu'aucun agent ne les lise pendant le
   développement), puis les passer avec le protocole de l'examen : code figé,
   un fils par problème, aucune retouche, score noté. Un premier examen blanc
   est possible tôt : une variante de jeu jamais montrée à la mère, branchée
   sans changer une ligne. Depuis le premier, chaque problème fournit son
   arbitre, et le fils doit faire au moins aussi bien que le professeur à sa
   place, pour un, deux ou trois joueurs (`docs/architecture.md`, § 11).
7. **Le branchement ARC.** L'adaptateur (format JSON officiel vers « des
   exemples et une question ») et le lanceur d'examen (commit noté, budget
   de calcul, nombre d'essais, score), écrits d'après la description du
   format et testés sur une tâche inventée. Possible dès le jalon 1, sans
   danger tant qu'on ne le lance pas sur de vraies tâches.
8. **L'examen.** Sur le jeu d'évaluation public, jamais vu, puis, si le
   résultat le justifie, par la voie officielle (tâches cachées). Le score
   va dans le journal ci-dessous, et les tâches ratées ne sont pas regardées.

### Journal des examens

| Date | Examen | Jeu de problèmes | Commit | Score |
|---|---|---|---|---|
| 2026-11-25 | Examen blanc n° 1 | 5 problèmes inédits, sous scellé hors du dépôt | `e757e7e` | 1/5 |

L'examen n° 1 a été passé avec l'ancien barème : pas d'arbitre, réussi si le
fils ne perd aucune des 2 parties contre le professeur ni des 100 contre le
joueur au hasard de la mère, 30 minutes par problème ; pas de score relatif.
Le barème a changé ensuite à cause des fragilités du protocole, pas de ce
score (un réglage ne se change jamais d'après le score d'un examen blanc) :
le score n° 1 n'est pas comparable à ceux des examens suivants.

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
| Réutiliser l'expérience d'un fils pour un autre | **plus tard**, nécessaire pour ARC (jalon 5) |
| Un état qui est un nombre (Allumettes, misère) | fait : fin comprise par contre-épreuve, position qui porte le trait |
| Un joueur seul (Jumper, Partition) | fait : juger un coup par ce qui arrive, état qui défile |
| Actions à plusieurs arguments et valeur écrite (Nim, Hanoï, Compte est bon) | fait : action en tuple, valeur écrite par un petit programme, coup permis par des comparaisons |
| Plus de deux joueurs (Morpion à trois) | fait : ordre des joueurs lu dans l'exemple, `suivant(joueur)` au lieu d'`adversaire`, positions `M` / `A` / `B` |
| Information cachée (Mastermind, Mot mystère) | à faire : bloc de cases écrites, hypothèses sur le secret |
| Bulletin du fils (qualité, pas seulement victoire) | à faire : conçu ci-dessous, « Le bulletin du fils » |
| Problèmes qui ne sont pas des jeux (une entrée, une sortie) | fait, première forme : 18 briques listées ; entraînement 52/55 (53 en deux essais), lot jamais vu 25/34 (jalon 1) |
| Examens blancs sous scellé | premier passé (jalon 6) : `python -m xander.examen` ; arbitre fourni avec chaque problème, barème « au moins aussi bien que le professeur à sa place » (score binaire et score relatif) |
| Branchement ARC (adaptateur et lanceur d'examen) | à faire (jalon 7) |
| Examen ARC | **le cap** (jalon 8) |

## Reprendre le travail

Pour l'agent qui prend la relève. État au soir du 2026-11-25 (`main`
après la PR #20), mis à jour le 2026-11-26.

### Méthode de travail

- **Une branche, une PR, puis fusion.** Jamais de push direct sur `main`.
  Claude fusionne lui-même ses PR et celles de ses sous-agents, sans demander,
  **après relecture et CI verte** (`gh pr merge N --merge`) : c'est une
  décision de l'utilisateur. Avant de pousser, fusionner `origin/main` dans
  la branche (merge, jamais rebase ni force-push).
- **Des agents en parallèle, sur des fichiers disjoints.** Écrire un jeu
  (`Games/`, `res/`, ses propres tests, sa section à la fin de
  `docs/jeux.md`) se fait en parallèle sans risque. Deux agents qui
  modifient `xander/education.py`, `effets.py`, `un_joueur.py` ou
  `son_writer.py` en même temps doivent chacun intégrer `main` avant de
  finir : préférer les faire l'un après l'autre. Les conflits de doc se
  résolvent en gardant les deux côtés.
- **Relire une PR** : aucun nom ni cas de jeu dans le code de `xander/` (les
  commentaires d'exemple sont permis), ce qui reste fourni à la main est
  listé, tout nouveau réglage est dans le tableau « Réglages fixés à la
  main » avec son origine, toute la suite passe (environ 90 s, « Morpion
  parfait à 200 parties » compris), et les chiffres annoncés sont mesurés.
- **Le fils ne triche jamais** (`CLAUDE.md`) : après ses 5 premières
  parties, aucun coup impossible, dans toute éducation et tout banc.
- **Les examens blancs** se passent sur un dossier sous scellé **hors du
  dépôt** (convention et arbitre : `docs/architecture.md`, § 11). Le jeu
  n° 1 est sur la machine où il a été écrit, et il est **brûlé** : on ne le
  réutilise pas. Le prochain examen demande un nouvel auteur (un agent qui
  ne développe pas la mère), qui écrit les problèmes avant de lire
  `xander/`, avec un `arbitre.py` par problème. Aucun agent qui développe
  la mère ne lit ce dossier.

### Ce que la mère sait faire de chaque jeu

| Jeu | Joueurs | Ce que fait la mère aujourd'hui | Ce qui manque |
|---|---|---|---|
| Morpion | 2 | fils parfait à 200 parties, règles construites, symétries, petits motifs | — |
| Puissance 4 | 2 | éducation praticable (gravité composée, petits motifs vérifiés) | une vraie éducation de 50 à 100 parties et son bilan ; des concepts qui regardent plus loin |
| Allumettes, misère | 2 | aucune position gagnable ratée à 10 allumettes, une règle construite | la période 4 (plus loin que deux `AuMoins`) |
| Nim, misère | 2 | bat le hasard 196 à 200 fois sur 200, une trentaine de souvenirs | la somme de Nim (16 positions gagnables sur 102 encore ratées) |
| Jumper, Partition | 1 | jusqu'au plafond sur 50 graines jamais vues, un petit motif | des règles pour un joueur seul |
| Tours de Hanoï | 1 | range la pile en 7 coups dès la 5e partie | il a retenu un chemin : 15 positions de départ sur 27 seulement |
| Le compte est bon | 1 | gagne le tirage du labo | 3 tirages jamais vus sur 100 : le labo rejoue un seul tirage, pas de « configuration » |
| Morpion à trois | 3 | 24 alignements, 8 symétries, 4 règles construites (gagner, parer chacun des deux autres, menacer) ; 60 situations de mesure tenues sur 60 face au professeur à sa place | 304 souvenirs (surtout des ouvertures), 340 s pour 200 parties ; pas de fourchette propre à trois |
| Mastermind, Mot mystère | 1 | trouve les actions, pas leur effet | un bloc de cases écrites, une information cachée |
| Pylos 3×3 | 2 | décrit les trois actions | tour de longueur variable, plusieurs sortes d'actions, défaite « plus de coup » |
| Problèmes entrée → sortie | 0 | lot jamais vu 25/34 | programmes plus grands (jalon 2), notions absentes |

Le détail de chaque jeu (règles, professeur, ce que la mère comprend, où
l'éducation bloque) est dans `docs/jeux.md`. Commandes :
`python -m xander res/exampleX.py` (ce qu'elle comprend),
`python -m xander res/exampleX.py --prof module:fonction --son nom --parties N`
(une éducation), `python -m xander.examen <dossier>` (un examen).

### Priorités pour la suite, dans l'ordre

**Fait (2026-11-26) : l'hypothèse vient de l'explication** (architecture,
§ 6, « L'hypothèse vient de l'explication ») : explication par cas à marge
croissante, élargissement des bornes, séparation des « ou », contre-exemples,
oubli du redondant, budget tenu en partie. Reste : le souvenir qui passe
avant « gagner », les défaites contre le professeur du Puissance 4, le coût
de l'élargissement au Morpion à trois.

1. ~~Vérifier le Morpion à trois après la fusion~~ : **fait** (2026-11-26).
   Morpion à trois et Puissance 4 identiques leçon pour leçon avant et après
   les PR #20 et #22 ; 200 parties de Morpion à trois en 340 s (voir
   l'étape 6).
2. ~~Le bulletin du fils, comme mesure seule~~ : **fait** (2026-11-26, section
   suivante). Il confirme que Hanoï a retenu et que le Morpion a compris.
3. **Généraliser au lieu de retenir** : Hanoï depuis toute position, Le
   compte est bon sur des tirages jamais vus. Il faut que le labo varie
   l'état de départ (d'autres tirages, d'autres positions) et que la mère
   reconnaisse des configurations plutôt que des positions entières. Le
   bulletin le mesure.
4. **L'information cachée** (Mastermind, Mot mystère) : décrire un bloc de
   cases écrites à une position calculée (« la première rangée vide »), et
   raisonner sur les secrets encore possibles au lieu d'apprendre par cœur
   celui du labo (qui rejoue toujours la même graine).
5. **Pylos 3×3** : tours de longueur variable, plusieurs sortes d'actions
   par tour, défaite quand on ne peut plus jouer.
6. **Des règles pour un joueur seul** : « atteindre le but » **fait**
   (2026-11-26) : quand la mère prévoit l'état et a compris une fin gagnée,
   les quatre notions existent seul (`suivant(moi)` = moi) et elle trouve
   « jouer un coup après lequel j'ai gagné » à Hanoï (taille 28 → 21 ;
   architecture, § 6). Le compte est bon n'en garde aucune : un seul tirage,
   donc un seul cas par règle. La généralisation ne bouge pas (Hanoï 3/15) :
   ces règles ne voient le but que de près. Reste « durer » (fin perdue : Jumper) et
   des sous-buts à reconnaître, ce qui rejoint la priorité 3.
7. **Un moteur commun** pour `effets.py` et `transformations.py` (énumérer
   par taille, confondre par les valeurs) : premier pas vers le jalon 2.
8. **Examen blanc n° 2**, quand plusieurs de ces points sont faits : un
   nouveau jeu de problèmes sous scellé, avec arbitres, passé une fois au
   nouveau barème (score binaire et score relatif).

## Le bulletin du fils : mesurer la qualité, pas seulement la victoire

**Pourquoi.** La seule récompense d'une partie est aujourd'hui son issue, et
pour un joueur seul « plus tôt vaut mieux » (`Solo.end_value`). Cela pousse
à retenir plutôt qu'à comprendre : à Hanoï, le fils range la pile en 7
coups avec 7 souvenirs, mais seulement depuis 15 positions sur 27. Il gagne
vite sans avoir compris. Le projet cherche l'inverse : la plus petite
logique qui explique tous les cas (le refactor), des configurations
reconnues plutôt que des positions entières (Chase et Simon). Un bulletin
automatique dit, pour chaque fils, s'il a compris ou s'il a retenu.

### 1. Le bulletin, une mesure pour nous : **fait** (2026-11-26)

`xander/bulletin.py`, `--bulletin` en ligne de commande, tests dans
`tests/test_bulletin.py` ; fonctionnement dans `docs/architecture.md`, § 12.
Premiers bulletins (graine 0 ; « général. » : positions jamais vues tenues) :

| Jeu (parties) | Taille (nœuds + cases) | Compression | Coups décidés par une règle / un motif ou souvenir / le défaut | Général. |
|---|---|---|---|---|
| Morpion (200) | 81 (10 + 71) | 3,84 | 64 % / 23 % / 13 % | 49/50 |
| Morpion à trois (200) | 4 865 (7 + 4 858) | 0,65 | 61 % / 21 % / 17 % | 41/50 |
| Allumettes (200) | 5 (5 + 0) | 1,80 | 48 % / 0 % / 52 % | toutes vues |
| Allumettes misère (200) | 6 (4 + 2) | 1,67 | 15 % / 25 % / 61 % | toutes vues |
| Nim (200) | 104 (11 + 93) | 0,81 | 38 % / 32 % / 29 % | 19/35 |
| Nim misère (200) | 118 (10 + 108) | 0,72 | 30 % / 51 % / 19 % | 17/34 |
| Jumper (30) | 1 (0 + 1) | 322 | 0 % / 12 % / 88 % | 4/4 |
| Partition (30) | 1 (0 + 1) | 300 | 0 % / 38 % / 62 % | toutes vues |
| Hanoï (30) | 21 (0 + 21) | 2,19 | 0 % / 57 % / 43 % | 3/15 (la mère gagne depuis les 15) |
| Hanoï (30), avec les règles à un joueur | 21 (1 + 20) | 2,19 | 14 % / 43 % / 43 % | 3/15 |
| Le compte est bon (30) | 15 (0 + 15) | 0,40 | 0 % / 100 % / 0 % | 50/50, mais personne ne gagne depuis ces positions |

(Tailles à la première mesure, sans le coup demandé par chaque souvenir ;
la mesure actuelle et les chiffres après le rasoir d'Ockham sont en section 2.)

Ce qu'il dit : le Morpion a **compris** (règles qui décident, 98 % de
positions jamais vues tenues) ; Hanoï a **retenu** un chemin (rien que des
souvenirs et le coup par défaut, 3 positions jamais vues sur 15 alors que la
mère sait gagner depuis les 15) ; au Nim, la moitié des positions nouvelles
sont ratées (la somme de Nim manque) ; le Morpion à trois tient 82 % des
positions nouvelles mais sa taille est faite de 302 souvenirs entiers. Deux
découvertes : au Morpion à trois, 4 des 3 143 cas enregistrés ne sont plus
bien joués par le fils final. Cause trouvée : chacun est décidé par le
souvenir d'une position **symétrique**, enregistré plus tard, et à trois les
positions symétriques n'ont pas la même valeur quand le professeur finit la
partie (max^n départage dans un ordre fixe de cases, qui n'est pas
symétrique : dans l'une, un coup gagne ; dans l'autre, aucun). **Réglé** (2026-11-26) : après les
corrections de chaque partie, la mère revérifie chaque cas que décide un
souvenir (`Education.recheck`) ; un souvenir démenti par un cas laisse à ce
cas son propre souvenir (architecture, § 7). L'autre piste (ne garder une
symétrie que si le professeur la respecte) a été mesurée et écartée : sur 37
positions de sonde, max^n dément chacune des 7 symétries de 1 à 7 fois, la
mère les perdrait toutes. Après le changement : Morpion à trois 3 143 cas
bien joués sur 3 143 (333 leçons au lieu de 337, 306 souvenirs au lieu de
302, généralisation inchangée 41/50, 442 s) ; Morpion et Puissance 4
identiques (la revérification n'y trouve rien). Et au Compte est bon, la
généralisation ne veut rien dire tant que le labo rejoue un seul tirage.

**Reste à faire** : l'écrire dans le rapport du lanceur d'examen ; la
stabilité en ligne de commande ; au Puissance 4 (10 parties), 1 cas sur 499
est mal joué par le fils final, décidé par une règle ou le coup par défaut
et non par un souvenir (déjà avant la revérification) : à comprendre.

Conception d'origine :

Un module `xander/bulletin.py`, qui ne modifie rien. Il lit une éducation
finie (`Education` ou `Solo` : `knowledge["memories"]`, `["patterns"]`,
`["rules"]`, `["concepts"]`, `cases`, `records`, `max_views`) et le code du
fils, et rend un bulletin chiffré :

| Mesure | Calcul | Ce qu'elle dit |
|---|---|---|
| **Taille de ce qu'il sait** | nombre de souvenirs ; nœuds des règles (et des briques dont elles dépendent) ; cases fixées des petits motifs | un fils court qui gagne vaut mieux qu'un fils long qui gagne (longueur de description minimale) |
| **Compression** | cas enregistrés bien joués ÷ taille | une règle qui couvre 40 cas en 6 nœuds est propre ; un souvenir qui couvre un cas ne compresse rien |
| **Origine des coups** | sur les coups des dernières parties : part décidée par une règle, un petit motif, un souvenir, le coup par défaut | un fils qui gagne avec le coup par défaut a eu de la chance (Allumettes, Jumper) |
| **Généralisation** | réussite depuis des positions ou des tirages **jamais vus** pendant l'éducation : autres graines, positions de départ tirées au hasard et atteignables, comparée à celle du professeur depuis les mêmes positions | la vraie mesure de la compréhension (Hanoï 15/27, Compte est bon 3/100) |
| **Solidité des règles** | pour chaque règle : cas qui la soutiennent, cas où elle a décidé, règles jamais utilisées ou toujours vraies (« vraie sans rien dire ») | repère les coïncidences et le code mort |
| **Stabilité** | relancer l'éducation avec d'autres graines et comparer les règles trouvées (mêmes arbres, à symétrie près) | des règles qui changent à chaque graine sont des coïncidences |
| **Budget** | positions regardées par coup (existe déjà) | penser comme un joueur, pas comme un minimax |

Sortie : `python -m xander res/exampleX.py --prof … --son … --bulletin`
l'affiche après l'éducation, et le lanceur d'examen l'écrit dans son
rapport à côté du score (sans rien dire du contenu des problèmes). Un test
par mesure, sur des fils connus : au Morpion, peu de souvenirs et des
règles qui décident ; à Hanoï, la généralisation doit être mauvaise
aujourd'hui (15/27), et le bulletin doit le dire. Les positions « jamais
vues » sont tirées par le bulletin, jamais montrées à la mère.

La lisibilité au sens humain ne s'automatise pas ; la taille, la
compression et l'absence de nœuds inutiles s'en approchent. Les seuils
d'interprétation (bonne ou mauvaise généralisation) ne sont pas fixés :
le bulletin donne des nombres, on les compare d'un fils à l'autre.

### 2. Le bulletin dans la mère : le rasoir d'Ockham : **fait** (2026-11-26)

Entre deux fils qui jouent aussi bien tous les cas enregistrés, la mère
garde **le plus court**. Un souvenir coûte ; une règle qui en remplace
plusieurs rapporte. C'est le rasoir d'Ockham (longueur de description
minimale), général et déjà dans l'esprit du projet ; il sert le jalon 4
(conclure à partir de peu).

**La mesure**, une seule pour la mère et le bulletin : `xander/taille.py`.
Taille = nœuds des règles **et des briques dont elles dépendent** (chaque
brique une fois : la complexité ne se cache pas dans une brique) + cases
fixées par les souvenirs et les petits motifs + **un coup par souvenir ou
petit motif**. Ce dernier terme est nouveau : un souvenir dit « ici » *et*
« jouer ce coup ». Sans lui, un souvenir d'une seule valeur (`7 M`) ne
coûtait qu'un, autant qu'un nœud de règle. Au premier essai, la mère
préférait alors retenir quatre valeurs plutôt que la règle des Allumettes
misère.

**Ce qui est accepté** :

- un **refactor** (`Education.shorter`) : il libère au moins deux souvenirs
  (un seul pendant un temps, voir « Le rasoir mis de côté » ci-dessous),
  ne fait rater aucun cas (`check`) et ne rallonge pas le fils. Les règles
  qu'il rend inutiles comptent comme déjà retirées (`pruned`), puisque
  l'élagage suit. À taille égale, la règle est gardée : le rasoir ne
  départage pas, et une règle qui explique plusieurs cas dit quelque chose
  des positions jamais vues, alors qu'un souvenir n'en dit rien. Avant :
  « au moins deux souvenirs libérés ». Le concept doit toujours expliquer
  au moins deux souvenirs (`MIN_CAS`, coïncidence) ;
- une **réduction en petit motif** (`generalize`) : elle est toujours plus
  courte (seules les cases qui comptent restent), et `holds` rejoue déjà les
  cas enregistrés ; le critère est maintenant écrit ;
- un **oubli** de règle (`prune`) ne rallonge jamais le fils : il le
  raccourcit, ou laisse sa taille quand la règle reste une brique d'une
  autre ;
- **un joueur seul** : un petit motif est gardé s'il raccourcit le fils et
  joue encore bien tous les cas (`Solo.motif_for`). À issue égale, la mère
  retient le coup qui donne la description la plus courte (`Solo.shortest`,
  celui qui rejoint d'autres souvenirs dans un petit motif), puis le plus
  petit. Cela ne change rien aujourd'hui. À Hanoï, l'état est une valeur
  entière : il n'y a pas de petit motif possible, donc rien à raccourcir (il
  faudra reconnaître des configurations, priorité 3). À Jumper, le fils
  était déjà au plus court (un motif). En passant, `generalize` repart
  maintenant de ce que sait la mère après chaque motif adopté. Avant, un
  second motif dans le même appel repartait d'une copie périmée, qui
  remettait les souvenirs libérés par le premier.

**Garde-fou.** La mère n'a jamais accès à la généralisation du bulletin, ni
pendant l'éducation ni pour choisir un refactor. Le changement n'est gardé
que s'il ne la fait baisser sur aucun jeu d'entraînement. Mesures du
2026-11-26 (`xander/bulletin.py`, graine 0 ; taille à la nouvelle mesure, y
compris avant ; « gén. » : positions jamais vues tenues) :

| Jeu (parties) | Taille avant → après | Souvenirs / motifs / règles avant → après | Gén. avant → après |
|---|---|---|---|
| Morpion (200) | 90 → **84** | 4 / 5 / 3 → 3 / 5 / 4 | 49/50 → 49/50, toujours parfait (0 défaite contre le professeur et 200 parties au hasard) |
| Allumettes (200) | 5 → 5 | 0 / 0 / 1 → identique | toutes vues |
| Allumettes misère (200) | 8 → 8 | 2 / 0 / 1 → identique | toutes vues |
| Nim (200) | 135 → **129** | 31 / 0 / 2 → 28 / 0 / 2 | 19/35 (54 %) → **22/36 (61 %)** |
| Nim misère (200) | 154 → **153** | 36 / 0 / 1 → 33 / 0 / 3 | 17/34 (50 %) → **19/34 (56 %)** |
| Hanoï (30) | 28 → 28 | 7 / 0 / 0 → identique | 3/15 → 3/15 |
| Jumper (30) | 2 → 2 | 0 / 1 / 0 → identique | 4/4 → 4/4 |

La généralisation ne baisse nulle part. Elle monte au Nim et au Nim misère,
où la mère garde maintenant des règles plus grandes (Nim : 11 → 17 nœuds ;
Nim misère : 10 → 21) qui remplacent des souvenirs. Avant, elles étaient
écartées faute de libérer deux souvenirs. Les cas enregistrés sont tous bien
joués partout. Le Morpion à trois n'a pas été remesuré : il n'est pas dans
la liste du garde-fou, et sa gestion des symétries change dans une autre
branche.

Ce qui a été essayé :

1. Taille sans le coup demandé (celle du premier bulletin). Le Morpion
   passe de 81 à 76, mais les Allumettes misère perdent leur règle
   (4 nœuds contre 2 souvenirs d'une case), et la généralisation du Nim
   passe de 19/35 à 18/34. Écarté.
2. Avec le coup demandé, en ne gardant que ce qui est strictement plus
   court : les Allumettes misère perdent encore leur règle (8 = 8). D'où la
   règle d'égalité.
3. Avec l'élagage simulé, le refactor qui ne libère aucun souvenir mais
   rend une autre règle inutile bouclait sans fin au Nim (il était
   « plus court » à chaque tour, et l'élagage n'avait lieu qu'à la fin).
   D'où l'exigence d'au moins un souvenir libéré.

**Le rasoir mis de côté** (2026-11-26). Avec un seul souvenir libéré, le
Puissance 4 s'effondrait (10 parties : 1 règle au lieu de 3, 149 souvenirs
au lieu de 139, 2 défaites au lieu de 2 nuls contre le professeur, 40
défaites au lieu de 12 sur 100 contre le hasard) alors que le Nim gagnait
quelques positions. Le seuil revient à **deux souvenirs libérés** (le
concept, lui, expliquait déjà deux souvenirs) :

| | un souvenir libéré | deux |
|---|---|---|
| Morpion | taille 84, 49/50 | taille 90, 49/50 |
| Nim | 22/36 | 19/35 |
| Nim misère | 20/35 | 17/34 |
| Morpion à trois | 3 143 cas bien joués, 89 / 4 / 7 contre le hasard | identique |
| Puissance 4 (10) | 54 / 6 / 40 contre le hasard, 2 défaites contre le professeur | 79 / 9 / 12, 2 nuls |

L'effet du critère change d'un jeu à l'autre sans qu'on sache pourquoi :
le rasoir reste écrit (la taille sert encore à départager et aux petits
motifs), mais on n'y touche plus avant d'avoir compris, au Puissance 4, ce
que la règle tirée d'un seul souvenir libéré y faisait mal. La suite passe
par l'hypothèse tirée de l'explication (priorité suivante).

Les poids du critère (un coup par souvenir ; l'égalité en faveur de la
règle ; au moins un souvenir libéré) sont dans le tableau « Réglages fixés à
la main ». Ils ne se règlent jamais sur un examen blanc.

## Prochaines étapes proposées

Chacune sert un jalon du cap ARC : 1 → jalons 2 et 3 ; 2 → jalons 2 et 4
(vérifier honnêtement, chercher sans tout essayer) ; 3 et 5 → jalons 2 et
4 ; 4 → jalon 3 ; 6 → jalon 1 ; 7 → jalons 1 et 3 (de nouvelles
notions à chaque jeu : tour de longueur variable, défaite qui n'est pas un
motif, déplacements) ; 8 → jalon 5.

**Retirer les aides orientées.** Objectif : que la mère n'ait plus que des
briques générales. État des aides qu'on lui donne encore, de la plus taillée
pour un jeu à la plus structurelle :

| Aide | État |
|---|---|
| Les actions sont les indices du plateau (`range(len(state))`) | **retirée** : elle explore autour des valeurs de l'exemple |
| L'adversaire au hasard appelle `get_game_state` et `play` | **retirée** : il utilise les noms appris dans l'exemple |
| `premiere(x, pas, v)`, la gravité toute faite | **retirée** (étape 4) : elle compose `premiere_de(portee(arg0), valant(' '))` |
| Une seule expérience pour voir une portée : rejouer la même action depuis le début | **retirée** : elle explore (curiosité pour les actions surprenantes) et déduit l'ordre de ce qu'elle a vu |
| `valant` compare aussi le texte (`"4"` et `4`), une conversion cachée pensée pour le Morpion | reste ; à rendre explicite (une brique `texte(x)`). Coût : au Morpion, `case(arg0)` et `valant(arg0)` ne seraient plus départageables du tout, et le jeu d'essai qui les départage est à refaire |
| Une case changée reçoit le pion du joueur | **retirée** : elle décrit la valeur écrite (constante, argument ou propre à chaque joueur) |
| Une case libre est une case sans pion | **retirée** : elle le déduit des coups joués et refusés (toujours, une valeur, ou la valeur du début) |
| Pions appris par parité de coup | **généralisée** : la mère lit dans l'exemple l'ordre des joueurs, un cycle de n joueurs (la parité en est le cas n = 2) ; le joueur d'un coup est sa place dans le cycle. Reste supposé : un ordre fixe (personne ne passe ni ne rejoue) |
| Positions lues en `M` / `A` / `.` | reste, mais `.` est la case libre apprise et `#` le reste : c'est la position vue de son côté ; à plus de deux joueurs, `A` est le suivant, `B` celui d'après, etc. (à deux, les mêmes clés) |

**Réglages fixés à la main.** Les nombres qu'on donne à la mère font aussi
partie de son équipement de naissance. Ils sont listés ici avec leur origine,
pour savoir lesquels ont été choisis en regardant des résultats. Règle : un
réglage n'est **jamais** changé d'après le score d'un examen blanc, et un
réglage changé d'après les résultats d'un jeu d'entraînement le dit ici.
« Principe » : la valeur découle d'une règle de `CLAUDE.md`. « A priori » :
choisie sans mesure, jamais remise en question. « Réglé » : choisi en
comparant des résultats.

| Réglage | Valeur | Où | Origine |
|---|---|---|---|
| Cas distincts pour garder une explication (effet, souvenirs expliqués par un concept de refactor, souvenirs d'un petit motif) | 2 | `effets.MIN_CAS`, `refactor_once` | principe : un seul cas peut être une coïncidence |
| Rasoir d'Ockham : taille d'un fils | nœuds des règles et de leurs briques + cases fixées + 1 coup par souvenir ou petit motif | `xander/taille.py` | principe (longueur de description minimale) ; le « + 1 coup » réglé aux Allumettes misère (sans lui, quatre valeurs retenues battaient la règle) |
| Rasoir d'Ockham : quand un refactor est gardé | au moins 1 souvenir libéré, pas plus long (règles rendues inutiles retirées) ; à taille égale, la règle | `Education.shorter` | principe (Ockham) ; avant : « au moins 2 souvenirs libérés ». L'égalité réglée aux Allumettes misère ; « au moins 1 » imposé par une boucle sans fin au Nim |
| Un joueur : coup retenu à issue égale | le plus court après petit motif, puis le plus petit | `Solo.shortest` | principe (Ockham) ; ne change rien aujourd'hui (Hanoï, Jumper) |
| Positions regardées par le fils pour un coup | 1 000 | `education.BUDGET` | principe (budget mesurable) ; valeur a priori, loin du minimax complet (500 000) |
| Taille d'un programme d'effet | 5 nœuds | `effets.MAX_TAILLE` | a priori ; suffit pour la gravité (5 nœuds) |
| Constantes retenues de chaque sorte | 8 | `effets.MAX_CONSTANTES` | a priori |
| Expériences pour réfuter l'effet / parties d'exploration / nouvelles recherches / refus avant d'arrêter d'explorer | 40 / 8 / 3 / 2 | `EXPERIENCES`, `PARTIES_D_ESSAI`, `REPRISES`, `PATIENCE` | a priori |
| Taille et profondeur d'un concept | 6 nœuds, 2 `AuMoins` | `Education.max_size`, `max_depth` | réglé au Morpion |
| Élargissement des bornes quand un cas reste sans explication | 2 crans (chaque cran : un nœud et un niveau de plus) | `ELARGISSEMENTS`, `Education.wider` | a priori (un nœud et un niveau ensemble, pour ne pas choisir l'un d'après nos jeux) |
| Contre-exemples rejoués d'abord | 20 | `CONTRE_EXEMPLES`, `Education.check` | sans effet sur ce qu'elle apprend (l'ordre de la vérification seulement) |
| Parties d'un « ou » : la plus immédiate d'abord | profondeur croissante, puis taille | `concepts.parties_ou` | principe fourni à la main (régler d'abord ce qui arrive le plus tôt) |
| k dans `AuMoins(k, …)` | 1 seulement | `Education.counts` | réglé au Morpion (tableau de `docs/architecture.md`, § 6) |
| Positions imaginées pour départager des concepts | 120 | `concepts.echantillon` | a priori |
| Autres coups adverses revus (variantes) | tous | `Education.variants` | réglé au Morpion (toute autre valeur y est pire) |
| Parties au hasard pour vérifier une symétrie / renumérotations candidates au plus | 20 / 5 000 | `probe_games`, `symmetries.candidates` | a priori |
| Petits motifs essayés avant d'oublier les cases une à une | 100 | `Education.combinations` | réglé (taille du plateau du Morpion contre Puissance 4) |
| Positions imaginées pour vérifier un petit motif / tamis avant la vérification complète | 20 / 5 | `holds`, `Education.sieve` | 20 a priori ; 5 réglé au Puissance 4 (temps) |
| Confirmations pour garder un petit motif | au moins la moitié, et r+ ≥ (1 + r−) / 2 contre le groupe témoin | `holds` | réglé au Puissance 4 (écarter le coup au centre joué par habitude) |
| Désaccords jugés par petit motif | 2 | `holds` | réglé au Puissance 4 (temps) |
| Adversaires de l'éducation | professeur, hasard, mixte (le professeur une fois sur deux) | `train`, `mixed_player` | a priori |
| Plus de deux joueurs : rotation de l'éducation | chaque sorte d'adversaire une partie à chaque place (n parties), toutes les autres places tenues par lui | `train`, `evaluate` | a priori (à deux : inchangé) |
| Plus de deux joueurs : coups adverses revus en variantes | ceux du joueur qui joue juste avant le fils | `variations` | a priori (à deux : inchangé) |
| Plus de deux joueurs : joueurs dont parle un concept | tous ceux du cycle vu dans l'exemple (`moi`, `lui`, `lui2`…) | `concepts.joueurs` | principe (le jeu dit combien ils sont) |
| Plus de deux joueurs : pion du fils quand tous ont autant de pions | celui du premier joueur de l'exemple | `son_writer.qui_suis_je` | a priori (à deux : inchangé) |
| Durée maximale du rejeu d'un exemple | 30 s | `rebuilder.replay` | a priori (plomberie) |
| Défilement : profondeur de l'entrée par le bord / part de l'état qu'elle peut couvrir | 2 \|d\| cases / la moitié (4 \|d\| ≤ n) | `effets._defilement` | 2 \|d\| réglé à Jumper (un obstacle naît une case avant le bord) ; la moitié réglée au Puissance 4 (sans elle, un faux décalage de −28 y « expliquait » l'exemple) |
| Un joueur : coups d'une partie du labo (au-delà, survie) | 300 | `un_joueur.COUPS_MAX` | a priori |
| Un joueur : positions où mesurer la durée d'effet / durée mesurée au plus | 30 / 40 | `un_joueur.MESURES`, `DUREE_MAX` | a priori |
| Un joueur : horizon pour juger un coup | durée d'effet la plus longue vue + 1 | `Solo.measure_horizon` | principe (voir l'effet d'un coup jusqu'au bout) ; le « + 1 » a priori |
| Un joueur : petits motifs essayés avant d'oublier les cases une à une | 20 000 | `un_joueur.COMBINAISONS` | a priori (vérifier un motif ne coûte ici aucune partie : les cas sont déjà jugés) |
| Un joueur : choix entre motifs de même taille | la plus grande part de cas qui confirment, puis le plus de confirmations | `Solo.smallest` | réglé à Jumper (l'ordre des cases choisissait une coïncidence à égalité) |
| Actions à plusieurs arguments : combinaisons essayées par argument / actions explorées au plus | 50 / 1 000 | `education.COMBINAISONS_ARGUMENT`, `ACTIONS_MAX` | a priori |
| Contre-épreuve d'une fin sans pions : états essayés au plus | 3 000 | `education.SOURCES_MAX` | a priori |
| Épreuves du labo pour vérifier quand un coup est permis | 600 | `education.EPREUVES_LIBERTE` | a priori |
| Valeurs d'un argument pour décrire la valeur écrite « selon » lui | 8 au plus | `effets.MAX_VALEURS_SELON` | a priori |
| Cases écrites : exactes au moins sur | la moitié des cas (et 2 cas) | `effets.ecrites` | a priori ; la borne de 2 est `MIN_CAS` (principe) |
| Quand un coup est permis : terme comparé / comparaisons au plus / paires essayées | 5 nœuds contre une feuille / 2 / 400 | `effets.MAX_TAILLE_CONDITION`, `liberte_valeurs`, `MAX_ATOMES_PAIRES` | 5 nœuds repris de `MAX_TAILLE` ; 2 et 400 a priori (400 pour le temps) |
| Un joueur : horizon d'un casse-tête dont la victoire est comprise | longueur de l'exemple | `Solo.measure_horizon` | a priori (l'exemple montre qu'on y arrive en autant de coups) |
| Un joueur : valeur d'une victoire | 2 h + 2 × profondeur restante | `Solo.end_value` | principe (« plus tôt vaut mieux ») ; changé à Hanoï (avec « 2 h + profondeur », chaque coup de survie annulait l'avance : gagner en 7 coups ou en 9 valait autant) |
| Examen : parties d'éducation / graine maîtresse | 200 / 0 | `examen.BUDGET` | a priori (le défaut de `raise_son`) |
| Examen : graines de mesure par place et par sorte d'adversaires | 10 | `examen.BUDGET` | a priori ; changé (2 parties contre le professeur, 100 contre le hasard) à cause des fragilités du protocole, pas du score |
| Examen : barème | au moins aussi bien que le professeur à sa place, dans toutes les situations ; aucun coup impossible après la partie 5 | `examen.mesurer`, `BUDGET.rodage` | principe (« le fils ne triche jamais ») ; changé (« ne perdre aucune partie ») à cause des fragilités du protocole, pas du score |
| Examen : limite de temps par problème | 20 000 fois la tâche de référence (environ 30 minutes sur la machine de développement) | `BUDGET.facteur`, `tache_de_reference` | a priori (les 30 minutes de l'examen n° 1, rapportées à la machine) |

Les réglages « réglés » sont les premiers à remettre en cause quand un
nouveau problème échoue. L'objectif, à terme, est que la mère choisisse
elle-même ces bornes (par exemple chercher plus grand seulement quand rien
de plus petit n'explique les cas), ce qui rejoint le jalon 2.

1. **Analyzer plus général.** C'est lui qui donne à la mère le vocabulaire
   pour percevoir un jeu. La mère construit la description de l'action avec
   un petit langage (étape 1 : elle retrouve seule les anciennes hypothèses,
   et celles de même taille coexistent). Le programme trouvé est le `apres`
   qu'elle écrit dans le fils et avec lequel elle pense (étape 2). Elle le
   met à l'épreuve dans le labo, d'abord par des expériences qui départagent,
   puis pour réfuter ce qui reste (étape 3). Elle compose elle-même la
   gravité du Puissance 4 (étape 4, ci-dessous).
   La portée et la valeur écrite sont déduites de ce qu'elle voit en
   explorant. **La valeur des Allumettes (quantité) : faite.** La mère
   éduque un fils quand l'état est un nombre (voir `docs/architecture.md`,
   § 6). La position porte le trait (`[valeur, trait]`) : une valeur ne dit
   pas qui a joué. Les actions permises viennent des coups refusés, qui sont
   des observations : « la valeur d'après ne descend pas sous 0 », mesuré sur
   ce qu'elle a vu. La fin est une valeur qu'elle vérifie par contre-épreuve
   dans le labo, et l'exemple dit qui la gagne. Le fils ne rate aucune
   position gagnable à 10 allumettes, avec une règle qu'elle construit
   (laisser 5 ou 1) et sans souvenir ; avec 14, deux souvenirs par quantité
   en plus. Restent la période 4 (au-delà de deux coups, étape 5), une fin
   que l'exemple ne montre pas (prendre les deux dernières : elle ne sait pas
   qui gagne et la compte nulle), et des bornes fournies à la main (toujours,
   au moins, au plus, entre).

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
   vérifie… » (une brique d'ordre, générale) et la façon de déduire l'ordre
   d'une portée. L'Analyzer seul, sans labo, ne comprend plus le
   Puissance 4 : il faut explorer.
2. **Puissance 4 : une éducation praticable.** Tout fonctionne de bout en
   bout. Les petits motifs y sont maintenant vérifiés honnêtement :
   - les positions imaginées sont **jouées** (coups permis), donc
     atteignables avec la gravité ; avant, presque aucune ne l'était et un
     motif était « vérifié » sur une ou deux positions ;
   - un **groupe témoin** (le motif cassé) écarte les motifs que le
     professeur « confirme » par habitude (la colonne du centre) ;
   - la réduction regarde la **zone** du coup (les cases qui partagent un
     motif de fin avec lui), avec un tamis de 5 positions avant chaque
     vérification complète.
   Au Morpion, chaque fils est parfait à 200 parties, après 16 à 30 erreurs,
   sans aucun petit motif démenti sur 10 graines. Au Puissance 4, des motifs
   de 5 à 15 cases sur 42 apparaissent, aucun démenti sur 3 parties.
   Le coût a d'abord augmenté : maintenant que les positions sont réalistes,
   chaque vérification les examine vraiment (35 minutes pour 3 parties). En
   ne jugeant les désaccords qu'une fois les comptes passés, 3 parties
   prennent environ 15 minutes, dont 10 pour réduire les souvenirs (425 fins
   de partie jouées par le professeur au lieu de 2 200). Il reste à faire une
   vraie éducation (50 à 100 parties) et son bilan contre le hasard et contre
   le professeur. Pistes : arrêter plus tôt une vérification perdue d'avance,
   et des concepts qui regardent plus loin (les pièges du Puissance 4 sont
   plus profonds que deux coups). La mère n'y trouve pas encore le miroir
   gauche-droite en 3 parties.
3. **Petits motifs dans les règles.** Les motifs de fin et les souvenirs se
   décalent déjà : un souvenir est réduit aux cases qui comptaient, puis
   reconnu partout (vérifié dans le labo). Il reste à en faire des briques
   (« jouer un coup qui crée cette configuration »), et à les essayer sur un
   grand plateau. Au Morpion, presque toutes les cases comptent, et les
   petits motifs gardent environ 8 cases sur 9.
4. **Symétries plus générales.** Aujourd'hui des renumérotations de cases.
   Il faudra des équivalences qui ne sont pas des permutations (échanger les
   deux joueurs, une quantité décalée).
5. **Concepts plus lisibles.** La mère construit ses concepts, mais certains
   sont des combinaisons difficiles à lire, ou des coïncidences validées sur
   peu de cas. Pistes : préférer le concept qui explique le plus de cas,
   relire les concepts quand une nouvelle brique apparaît, et dire ce que le
   langage fournit encore à la main (les nœuds `Non`, `Et`, `AuMoins` avec
   k = 1, la forme « jouer une action après laquelle… »). `gagne` sait
   maintenant qu'un coup peut faire perdre celui qui le joue, quand l'état
   est une valeur : la position porte le trait, et la variante des Allumettes
   jouée jusqu'au bout (`res/exampleAllumettesMisere.py`, prendre la dernière
   perd) donne `FINS = {0: "trait"}`. Pas encore pour un tableau. Deux
   faiblesses vues aux Allumettes : une règle « aucun de ses coups… » est
   vraie sans rien dire quand la partie est finie (il n'a plus de coup), et
   la période 4 demande de regarder plus loin que deux `AuMoins`.
6. **Autres formes de problèmes.** Plus de deux joueurs (fait : le Morpion
   à trois, ci-dessous), état qui n'est ni un tableau ni un nombre (un
   nombre : fait, les Allumettes).
   **Un joueur seul : fait** (`xander/un_joueur.py`, `docs/architecture.md`
   § 3 et § 6). Trois généralisations, chacune justifiée par un autre problème :
   - *l'état qui défile* : `suite = decale(avant, d)` sauf ce qui entre par
     le bord, un mobile qui ne défile pas et des cases fixes ; la description
     est partielle et dit ce qu'elle ne prévoit pas (à Jumper : l'élan est
     caché). Vaut pour une file d'attente, un bandeau, Partition ;
   - *le résultat d'une partie à un joueur* : la fin (perdue, gagnée, nulle,
     lue dans l'exemple), la durée d'effet d'une action (mesurée dans le labo :
     quand deux suites se rejoignent) et la valeur d'un coup (combien la
     partie dure au mieux, mesuré avec `back`). Les quatre notions restent
     celles des jeux à deux ;
   - *un coup joué sans rien changer de visible* n'est plus pris pour un
     refus si l'action renvoie ce qu'elle renvoie d'habitude.
   Partition (jeu inventé, sans état caché) : 2 erreurs, puis
   `{0: 'o'} -> True`. Jumper : 2 erreurs (les deux premiers obstacles), puis
   `{162: 'T'} -> True`, « sauter quand un obstacle est juste devant » ; 0
   souvenir, 0 coup impossible, 0 position regardée à l'avance ; sur 50
   graines jamais vues, de 51,7 coups en moyenne à la naissance à 2 000 sur
   2 000 (plafond). Restent : des règles construites pour un joueur seul (les
   concepts parlent de `gagne` et d'`adversaire`), vérifier un motif sur des
   positions imaginées (la mère ne sait pas placer un obstacle), un jeu où le
   coup par défaut est le mauvais, et un score qui ne soit pas la durée.
7. **Jeux suivants, une fois Morpion, Allumettes et Puissance 4 appris.**
   Chaque jeu doit apporter de nouvelles notions sans tout changer à la
   fois, et avoir un professeur fiable.
   - **Pylos à base 3×3** (9 + 4 + 1 = 14 billes, 7 par joueur). Il réunit
     ce que les trois premiers jeux ont appris : des carrés (motifs), une
     réserve de billes (quantité) et des billes qui reposent sur quatre
     autres (gravité). Il apporte aussi du nouveau : des `possibles` qui
     dépendent du support, deux sortes d'actions (poser, ou monter une
     bille d'une case à une autre), un tour dont le nombre d'actions varie
     (reprendre 1 ou 2 billes après un carré), une défaite qui n'est pas un
     motif (ne plus pouvoir jouer) et des symétries sur plusieurs étages.
     La base 3×3 contient déjà toutes les règles, garde des parties courtes
     et permet un Minmax exact comme professeur. **Fait :** le jeu
     (`Games/Pylos.py`) et son Minmax exact (`Games/MinmaxPylos.py`). La
     résolution montre que la base 3×3 n'est pas dégénérée : seul le coup
     au centre gagne, la partie parfaite passe par un carré, et monter une
     bille est parfois la seule façon de gagner (voir `docs/jeux.md`).
     Exemple de partie : `res/examplePylos.py`. La mère y décrit seule
     les trois actions (poser, monter, reprendre). Reste l'éducation, qui
     suppose qu'un tour est une seule action d'une seule sorte :
     comprendre un tour dont la longueur varie (il continue tant que le
     même joueur a la main), rejouer et proposer toutes les sortes
     d'actions dans le labo et dans le fils, et comprendre une défaite qui
     n'est pas un motif (ne plus avoir d'action possible).
   - **Pylos à base 4×4** (30 billes) ensuite. Le Minmax devra y limiter
     sa profondeur : il faudra apprendre avec un professeur faillible.
     C'est un bon test de « configurations n'importe où », et plus tard de
     la réutilisation de l'expérience du fils 3×3.
   - **Les échecs, par problèmes bornés.** D'abord des mats en 1 puis en 2
     (uniquement des suites forcées, budget mesurable), puis des finales
     Roi + Dame ou Roi + Tour contre Roi (une table de finales à trois
     pièces se calcule en Python pur : professeur parfait), puis des
     mini-échecs (5×5 ou 6×6), et seulement ensuite la partie complète.
     Si les déplacements d'une case à une autre posent problème, les dames
     sur petit plateau peuvent servir d'étape intermédiaire.
   - **Nim à plusieurs tas** (`Games/Nim.py`, variante misère
     `Games/NimMisere.py`, professeur exact `Games/MinmaxNim.py`, exemples
     `res/exampleNim.py` et `res/exampleNimMisere.py`) : un état fait de
     plusieurs nombres, une action à deux arguments (quel tas, combien), une
     stratégie qui n'est pas une période (la somme de Nim). **Fait :**
     l'éducation (actions à plusieurs arguments, ci-dessous). La mère écrit
     `moins(ici, arg1)`, trouve « on ne prend pas plus qu'il n'y a » et la
     fin `(0, 0, 0)`, construit deux règles et garde une trentaine de
     souvenirs ; le fils gagne en premier contre le professeur, bat le hasard
     196 à 200 fois sur 200, et rate encore 16 des 102 positions gagnables
     (la somme de Nim est hors de portée : on accepte des souvenirs).
   - **Mastermind** (`Games/Mastermind.py`, 3 chiffres de 1 à 6, 8 essais ;
     professeur `Games/MinmaxMastermind.py`, 5 essais au plus ; exemple
     `res/exampleMastermind.py`) : un jeu à un joueur qui se gagne, une
     information cachée, déduire à partir d'indices, compter, une action à
     trois arguments qui sont des valeurs. La mère n'y comprend encore
     aucun coup. Détails dans `docs/jeux.md`.
   - **Tours de Hanoï** (`Games/Hanoi.py`, professeur exact par parcours
     en largeur, exemple `res/exampleHanoi.py`) : un joueur, une action à
     deux arguments (départ, arrivée), un déplacement sous contrainte, un
     but avec une limite de coups. **Fait :** l'éducation seule. La mère
     décrit l'action avec des portées rangées par argument, trouve « jamais
     sur un plus petit », distingue la victoire de la limite atteinte (même
     signal) par l'état de fin ; dès la 5e partie, le fils range la pile en
     7 coups (le minimum), avec 7 souvenirs. Reste : reconnaître des
     positions qu'il n'a pas vues (il ne range la pile que depuis 15 des 27
     positions), et plus de disques.
   - **Le compte est bon, version courte** (un joueur, 4 nombres et une
     cible) : combiner des quantités pour atteindre un but, une action à
     trois arguments `play(i, j, op)`. **Fait :** le jeu
     (`Games/CompteEstBon.py`), son professeur exact
     (`Games/SolveurCompteEstBon.py`) et `res/exampleCompteEstBon.py`.
     **Fait :** la mère décrit le coup (les cases écrites, l'opération
     choisie par `arg2`, la place qui se vide), quand il est permis, la
     victoire (l'état final de l'exemple) et la défaite (une partie
     bloquée). Sur le tirage du labo, le fils gagne dès la 4e partie avec 3
     souvenirs. **Où elle s'arrête :** 3 tirages jamais vus gagnés sur 100.
     Il faudrait reconnaître des configurations (« il manque 5, et j'ai un
     5 ») et comprendre la victoire comme « la cible apparaît », pas un état
     exact (voir `docs/jeux.md`).
   - **Actions à plusieurs arguments, et ce qu'elles écrivent** (fait, pour
     le Nim, Hanoï et le Compte est bon ; rien de propre à un jeu dans
     `xander/`, voir `docs/architecture.md`, § 3 et § 6) : découvrir chaque
     argument à partir de ses valeurs vues ; une action est un tuple (labo,
     fils, souvenirs, règles) ; portées rangées par argument ; la valeur
     écrite décrite partie par partie par un petit programme (`ici`, `val`,
     les quatre opérations, « selon » un argument) ; les cases écrites ;
     quand un coup est permis, par une ou deux comparaisons déduites des
     coups joués et refusés, puis mises à l'épreuve dans le labo ; un
     tableau sans pions traité comme une valeur (la position porte le
     trait) ; deux fins au même signal distinguées par l'état de fin ; un
     casse-tête jugé jusqu'à la longueur de l'exemple. Restent, pour les
     jeux qui les attendent : **Mastermind** et **Mot mystère** (l'action y
     est découverte, 216 propositions au Mastermind, mais les cases écrites
     dépendent d'un compteur que l'état ne montre que par les rangées déjà
     remplies — « la première rangée vide » — et d'un secret caché : il
     faudrait décrire un **bloc** de cases écrites à partir d'une position
     calculée, et une valeur écrite qui dépend d'une information cachée,
     donc des hypothèses sur le secret) ; **Pylos** (plusieurs fonctions
     d'action par tour, un tour de longueur variable, et une action
     `move(src, dest)` qui écrit le pion du joueur **et** vide une case :
     des parties dont l'une écrit un pion, que le mode à pions ne sait pas
     encore prévoir).
   - **Mot mystère** (`Games/MotMystere.py`) : un joueur, un mot secret de
     5 lettres caché, 6 essais ; le professeur, qui ne lit pas le secret,
     trouve les 405 secrets en 2,99 essais. La mère voit le joueur seul,
     `back` et la fin, mais pas l'effet de `play` (un bloc de 10 cases) :
     l'éducation bloque dans `Solo.__init__`, et l'état caché (un seul
     secret dans le labo) reste à comprendre (voir `docs/jeux.md`).
   - **Morpion à trois joueurs** (`Games/Morpion3.py`, 4 × 4, trois alignés ;
     professeur max^n `Games/MaxnMorpion3.py` ; exemple
     `res/exampleMorpion3.py`). **Plus de deux joueurs : fait** (sans rien
     de propre au jeu dans `xander/`). La mère lit dans l'exemple l'ordre
     des joueurs (un cycle, la parité en est le cas à deux), voit chaque
     position de son côté (`M` moi, `A` le suivant, `B` celui d'après), et
     ses concepts parlent de `suivant(joueur)` au lieu d'`adversaire` (à
     deux, la même chose : Morpion, Allumettes et Nim identiques coup pour
     coup). Une fin vaut victoire pour le gagnant, défaite pour les autres,
     nul pour tous. En 200 parties : 24 alignements, 8 symétries, quatre
     règles construites (gagner, parer le suivant, parer le 2e après moi par
     composition, se créer une menace), 0 coup impossible, au plus 784
     positions par coup, et 60 situations sur 60 tenues face au professeur à
     sa place (détail dans `docs/jeux.md`).
     **Vérifié après la fusion des PR #20 et #22** (`main` 90859b1) : les 200
     parties du Morpion à trois sont identiques leçon pour leçon à la mesure
     d'avant (337 erreurs, 304 souvenirs, 60 situations sur 60), en 340 s
     seulement (les 29 minutes d'avant venaient d'une machine plus lente et
     chargée) ; le Puissance 4 (graine 0, 10 parties) donne les mêmes leçons,
     les mêmes règles et le même bilan avant la PR #20 (65147a4) et après
     (139 souvenirs, 3 règles, 518 positions au plus, 0 coup impossible,
     environ 87 s par partie).
     **Reste à faire** :
     - le temps des refactors (`views`, `check` rejouent tous les cas), qui
       croît avec les souvenirs (304 ici, surtout des ouvertures) ;
     - des règles pour ces souvenirs (une fourchette à trois, des petits
       motifs d'ouverture) ; des variantes sur le coup de l'avant-dernier
       joueur ; une fin à classement ou une victoire partagée.
8. **Plus tard : l'expérience.** Partir des apprentissages réussis (motifs,
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
