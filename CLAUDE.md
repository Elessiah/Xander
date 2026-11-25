# Xander — consignes pour Claude

## Vision : reproduire la logique humaine

Xander cherche à apprendre comme un humain : **faire une erreur, comprendre
pourquoi, ne plus la refaire**, puis s'appuyer sur l'expérience acquise pour
éviter les erreurs du passé. Pas de réseau de neurones, pas d'apprentissage
statistique à l'aveugle : chaque correction doit venir d'une **explication**.

À terme, on doit pouvoir mettre la mère devant **n'importe quel problème** (pas
seulement des jeux de plateau). À partir d'un exemple, elle crée son fils, le
corrige erreur après erreur et finit avec un fils parfait.

## Première finalité : l'examen ARC

Le but n'est pas pour tout de suite, mais **tout le travail va dans cette
direction** : résoudre des problèmes de logique inédits comme ceux du test
ARC de François Chollet (*Abstraction and Reasoning Corpus*). Chaque tâche
donne quelques paires d'exemples (une grille d'entrée, la grille de sortie
attendue) et une ou plusieurs entrées de test ; il faut produire la grille
de sortie exacte, avec le nombre d'essais que permet la version du test.
Les tâches sont nouvelles : le test mesure la capacité à apprendre une
compétence à partir de très peu, ce que Xander prétend faire.

Cet examen sert à **démontrer la méthode**. Il ne vaut que si personne n'a
aidé : ni nous, ni Claude. On branche ARC comme on brancherait n'importe
quel test du genre, la mère crée un fils pour chaque tâche, et le fils
répond. Règles, à respecter **à la lettre** :

1. **Aucune préparation sur ARC.** Personne ne regarde les tâches ARC
   (entraînement ou évaluation) pour concevoir une brique, un concept, une
   heuristique, un test ou un réglage. Aucune tâche ARC dans le dépôt, aucun
   téléchargement avant l'examen. Ni la mère ni un fils n'en voient une
   avant le jour de l'examen. Claude connaît ARC par sa formation : il ne
   s'en sert pas pour orienter la mère, et ne justifie jamais un changement
   par « ARC en aura besoin ».
   *Pourquoi, même le jeu d'entraînement public :* si nous lisons des tâches
   pour décider quoi construire, l'intelligence vient de nous et le
   résultat devient un « logiciel expert ARC » (le reproche fait aux
   solveurs dont le langage a été écrit en étudiant les tâches) ; on ne
   pourrait plus prouver que la mère a trouvé seule. Et si la mère
   s'entraîne seule dessus, on ne démontre plus qu'une méthode générale
   réussit un examen inédit, seulement qu'un entraînement sur ARC réussit
   ARC. L'ordre est irréversible : une fois ARC vu, on ne peut plus passer
   l'examen à vierge. On passe donc d'abord l'examen propre ; un résultat
   avec entraînement ne viendrait qu'après, présenté comme tel. Le même
   risque existe par la bande : nos problèmes d'entraînement ne doivent pas
   ressembler à ARC (grilles de couleurs, objets à déplacer) ; on varie les
   domaines.
2. **Le branchement ne fait que traduire.** Un adaptateur lit le format
   officiel (JSON) et présente chaque tâche à la mère comme tout autre
   problème : des exemples et une question. Il n'interprète rien (ni objets,
   ni couleurs, ni symétries, ni fond). C'est le seul code propre à ARC ; il
   est écrit à partir de la description du format et testé sur une tâche
   inventée, pas sur une vraie.
3. **Pendant l'examen, personne ne touche à rien.** Le code est figé (on note
   le commit), le budget de calcul est fixé d'avance, aucune réponse
   attendue ne revient vers la mère pour l'aider, aucun humain n'intervient.
4. **Un examen se passe une fois.** On note le score, le commit et la date
   dans la feuille de route. On ne regarde pas les tâches ratées pour
   corriger la mère : dès qu'on le fait, ce jeu de tâches devient de
   l'entraînement et ses scores suivants ne comptent plus. L'examen suivant
   se passe sur un jeu jamais vu.
5. **Pas de béquille déguisée.** Interdit aussi : une brique ajoutée parce
   qu'une tâche ARC ressemble à ça, un problème d'entraînement recopié d'une
   tâche ARC, un seuil réglé sur un score ARC, une branche de la mère
   réservée aux grilles de couleurs.

**Préparer, sans tricher.** On doit tout faire pour que la mère arrive prête :

- développer des capacités **générales** sur d'autres problèmes (jeux,
  énigmes, problèmes que nous inventons), chacune justifiée par un problème
  qui n'est pas ARC ;
- garder ce qui est fourni à la main court, général et **listé** : c'est
  l'équipement de naissance de la mère, l'équivalent de ce qu'un humain
  apporte à l'examen (objets, nombre, géométrie élémentaire, agents),
  fixé avant l'examen, et qu'elle doit à terme découvrir seule ;
- faire passer des **examens blancs** : des problèmes écrits à l'avance et
  mis sous scellé (jamais utilisés pendant le développement), branchés avec
  le même protocole et sans aucune modification du code. C'est la vraie
  mesure du progrès.

À chaque changement, se demander : « est-ce que ça rapproche la mère de
résoudre seule un problème qu'elle n'a jamais vu ? »

## Rôles — à respecter absolument

- **La mère crée le fils.** Toute l'intelligence du fils doit venir de ce que
  la mère a appris et corrigé. Ne jamais coder à la main une stratégie de jeu
  (minimax, heuristique, etc.) dans le fils et la présenter comme son œuvre.
- **Le fils exécute son code, bêtement.** Son code est **écrit par la mère** :
  il ne contient que ce qu'elle lui a appris (un fils qui n'a appris que
  `parer` ne contient que `parer`). Il lit l'état, applique ses règles et joue.
  **Il n'utilise jamais `back`** et ne fait pas de force brute avec essai et
  annulation. C'est la mère qui réfléchit et qui corrige ce code.
- **`back` est l'outil de la mère.** Il lui sert à revenir sur une erreur du
  fils, à comparer avec d'autres coups et à comprendre ce qui s'est passé.
- **Les Minmax de `Games/`** sont des adversaires et des professeurs (la mère
  peut leur demander le coup qu'ils préfèrent). Ils ne font pas partie de Xander.

## Le chemin compte plus que le résultat

Un fils parfait ne prouve rien si c'est nous qui avons écrit ce qu'il sait.
Quand une vérification révèle un trou, on ne le bouche pas en codant un
concept à la main : on cherche ce qui manque à la mère pour le trouver
elle-même. On accepte un apprentissage plus long si c'est elle qui apprend.
Toujours dire clairement ce qui est encore fourni à la main.

## Correction par la compréhension : le détail, puis la logique générale

La mère apprend comme un développeur : elle corrige d'abord **cas par cas**,
puis elle **refactorise** en trouvant la logique commune.

1. **Comprendre l'état de défaite** (au Morpion : trois pions adverses
   alignés), appris à partir des parties jouées et non codé en dur.
2. **Corriger le cas.** Chaque erreur devient un souvenir précis : dans cette
   position, il fallait jouer ce coup (celui du professeur, pas celui du fils).
3. **Refactoriser.** Quand plusieurs cas se ressemblent, la mère cherche la
   plus petite logique qui les explique tous (pourquoi le meilleur coup est
   meilleur : gain, défense, double menace, parade…) et remplace ces souvenirs
   par une règle. Une règle doit expliquer **plusieurs** cas : un seul cas
   peut être une coïncidence.
4. **Les souvenirs sont les tests du refactor.** Après un refactor, le fils
   doit encore jouer le bon coup dans tous les cas enregistrés ; sinon la mère
   l'abandonne. Une règle trouvée devient une brique pour les suivantes.

Un apprentissage un peu plus long est accepté : mieux vaut une règle sûre,
tirée de plusieurs cas, qu'une règle rapide tirée d'une coïncidence.

Toute connaissance fournie à la main (briques d'explication, hypothèses)
doit rester exprimée en termes généraux, jamais en termes propres à un jeu, et
l'objectif est que la mère finisse par la découvrir seule. Les règles
s'écrivent uniquement avec quatre notions que la mère apprend pour chaque jeu :
`apres(etat, action, joueur)` (vient de l'Analyzer), `gagne(etat, joueur)` (fin
de partie comprise par la mère), `possibles(etat)` (actions permises) et
`adversaire(joueur)`. Ainsi la même règle vaut pour tous les jeux.

## Situations équivalentes : les symétries

Au Morpion, une position tournée de 90° (ou vue dans un miroir) est la même
situation : un souvenir ou une règle appris sur l'une vaut pour l'autre. Ces
symétries ne sont **pas codées à la main** (elles dépendent du jeu : au
Puissance 4, la gravité interdit de retourner le plateau, seul le miroir
gauche-droite reste). La mère les **découvre** : ce sont les façons de
renuméroter les cases qui ne changent rien à ce qu'elle a compris du jeu
(les motifs de fin restent des motifs de fin, les actions permises restent
permises), et elle les vérifie dans son laboratoire avant de s'en servir.

## Penser comme un joueur humain, pas comme un minimax

Les maîtres d'échecs ne calculent pas plus que les amateurs (de Groot) : ils
**reconnaissent** des configurations apprises (Chase et Simon), n'examinent que
quelques coups candidats, et ne calculent loin que les suites **forcées**. Le
fils doit penser ainsi. Trois règles, que la mère respecte quand elle écrit son
code :

1. **Les règles proposent, le calcul vérifie.** Les coups candidats viennent
   toujours d'une règle apprise (gagner, parer, fourchette, souvenir…), jamais
   de « tous les coups possibles » explorés en arbre.
2. **Un coup d'avance sur tout, plus loin seulement si c'est forcé.** Regarder
   toutes les réponses adverses au coup suivant, c'est de la perception (voir
   un échec). Au-delà, le fils ne suit que des suites forcées (« je menace, il
   doit parer ici, alors… ») ; il n'énumère jamais toutes les réponses.
3. **Un budget mesurable.** On compte les positions que le fils regarde par
   coup et un test vérifie que ça reste petit. Si une correction demande de
   dépasser ce budget, il faut apprendre à **reconnaître** une nouvelle
   configuration, pas calculer davantage.

## L'Analyzer doit être le plus général possible

`xander/analyzer.py` doit couvrir **un maximum de cas, idéalement tous**. Il
donne à la mère le vocabulaire pour comprendre un problème (qui a changé quoi,
à qui appartient une case, quelle quantité varie…). Quand on l'étend, on
généralise : pas de cas taillé pour un seul jeu. Garder cet objectif en tête à
chaque modification.

## Pour l'instant : chaque fils part de zéro

Chaque fils naît sans rien savoir : il ne sait que lire l'état et jouer, et
tout le reste vient des corrections de la mère. On garde ce départ à zéro
simple tant qu'il n'est pas solide.

Plus tard seulement : réutiliser l'expérience des apprentissages réussis
(motifs, règles, explications d'un fils devenu parfait) comme base pour un
nouveau fils, sur un autre jeu ou un autre problème. Le squelette du fils
(ordre de décision, choix par défaut), écrit par la mère à la naissance, est
l'endroit où l'on pourra lui transmettre l'expérience de ses frères sous forme
de logiques pré-induites.

## Pratique

- Le code, les commentaires, la doc et les messages de commit sont en **français**.
- Claude répond **toujours en français** dans ce projet, même si on lui écrit
  dans une autre langue.
- Python 3.10+, aucune dépendance.
- Tests : `python -m unittest discover -s tests -t .`
- Apprendre un exemple : `python -m xander res/exampleMorpion.py`
- Doc : `docs/architecture.md` (fonctionnement), `docs/feuille-de-route.md`
  (état et prochaines étapes), `docs/format-exemple.md` (format des exemples).
