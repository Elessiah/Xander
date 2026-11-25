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
   sans changer une ligne.
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
| Problèmes qui ne sont pas des jeux (une entrée, une sortie) | fait, première forme : 18 briques listées ; entraînement 52/55 (53 en deux essais), lot jamais vu 25/34 (jalon 1) |
| Examens blancs sous scellé | premier passé (jalon 6) : `python -m xander.examen` |
| Branchement ARC (adaptateur et lanceur d'examen) | à faire (jalon 7) |
| Examen ARC | **le cap** (jalon 8) |

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
| Pions appris par parité de coup | **vérifiée** : la parité ne sert que si l'exemple montre deux joueurs qui alternent ; reste propre aux jeux à deux joueurs |
| Positions lues en `M` / `A` / `.` | reste, mais `.` est la case libre apprise et `#` le reste : c'est la position vue de son côté, générale pour deux joueurs |

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
| Cas distincts pour garder une explication (effet, refactor, souvenirs libérés) | 2 | `effets.MIN_CAS`, `refactor_once` | principe : un seul cas peut être une coïncidence |
| Positions regardées par le fils pour un coup | 1 000 | `education.BUDGET` | principe (budget mesurable) ; valeur a priori, loin du minimax complet (500 000) |
| Taille d'un programme d'effet | 5 nœuds | `effets.MAX_TAILLE` | a priori ; suffit pour la gravité (5 nœuds) |
| Constantes retenues de chaque sorte | 8 | `effets.MAX_CONSTANTES` | a priori |
| Expériences pour réfuter l'effet / parties d'exploration / nouvelles recherches / refus avant d'arrêter d'explorer | 40 / 8 / 3 / 2 | `EXPERIENCES`, `PARTIES_D_ESSAI`, `REPRISES`, `PATIENCE` | a priori |
| Taille et profondeur d'un concept | 6 nœuds, 2 `AuMoins` | `Education.max_size`, `max_depth` | réglé au Morpion |
| k dans `AuMoins(k, …)` | 1 seulement | `Education.counts` | réglé au Morpion (tableau de `docs/architecture.md`, § 6) |
| Positions imaginées pour départager des concepts | 120 | `concepts.echantillon` | a priori |
| Autres coups adverses revus (variantes) | tous | `Education.variants` | réglé au Morpion (toute autre valeur y est pire) |
| Parties au hasard pour vérifier une symétrie / renumérotations candidates au plus | 20 / 5 000 | `probe_games`, `symmetries.candidates` | a priori |
| Petits motifs essayés avant d'oublier les cases une à une | 100 | `Education.combinations` | réglé (taille du plateau du Morpion contre Puissance 4) |
| Positions imaginées pour vérifier un petit motif / tamis avant la vérification complète | 20 / 5 | `holds`, `Education.sieve` | 20 a priori ; 5 réglé au Puissance 4 (temps) |
| Confirmations pour garder un petit motif | au moins la moitié, et r+ ≥ (1 + r−) / 2 contre le groupe témoin | `holds` | réglé au Puissance 4 (écarter le coup au centre joué par habitude) |
| Désaccords jugés par petit motif | 2 | `holds` | réglé au Puissance 4 (temps) |
| Adversaires de l'éducation | professeur, hasard, mixte (le professeur une fois sur deux) | `train`, `mixed_player` | a priori |
| Durée maximale du rejeu d'un exemple | 30 s | `rebuilder.replay` | a priori (plomberie) |
| Défilement : profondeur de l'entrée par le bord / part de l'état qu'elle peut couvrir | 2 \|d\| cases / la moitié (4 \|d\| ≤ n) | `effets._defilement` | 2 \|d\| réglé à Jumper (un obstacle naît une case avant le bord) ; la moitié réglée au Puissance 4 (sans elle, un faux décalage de −28 y « expliquait » l'exemple) |
| Un joueur : coups d'une partie du labo (au-delà, survie) | 300 | `un_joueur.COUPS_MAX` | a priori |
| Un joueur : positions où mesurer la durée d'effet / durée mesurée au plus | 30 / 40 | `un_joueur.MESURES`, `DUREE_MAX` | a priori |
| Un joueur : horizon pour juger un coup | durée d'effet la plus longue vue + 1 | `Solo.measure_horizon` | principe (voir l'effet d'un coup jusqu'au bout) ; le « + 1 » a priori |
| Un joueur : petits motifs essayés avant d'oublier les cases une à une | 20 000 | `un_joueur.COMBINAISONS` | a priori (vérifier un motif ne coûte ici aucune partie : les cas sont déjà jugés) |
| Un joueur : choix entre motifs de même taille | la plus grande part de cas qui confirment, puis le plus de confirmations | `Solo.smallest` | réglé à Jumper (l'ordre des cases choisissait une coïncidence à égalité) |

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
6. **Autres formes de problèmes.** Plus de deux joueurs, état qui n'est ni
   un tableau ni un nombre (un nombre : fait, les Allumettes).
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
   - **Mot mystère** (`Games/MotMystere.py`) : un joueur, un mot secret de
     5 lettres caché, 6 essais ; le professeur, qui ne lit pas le secret,
     trouve les 405 secrets en 2,99 essais. La mère voit le joueur seul,
     `back` et la fin, mais pas l'effet de `play` (un bloc de 10 cases) :
     l'éducation bloque dans `Solo.__init__`, et l'état caché (un seul
     secret dans le labo) reste à comprendre (voir `docs/jeux.md`).
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
