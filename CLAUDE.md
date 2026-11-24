# Xander — consignes pour Claude

## Vision : reproduire la logique humaine

Xander cherche à apprendre comme un humain : **faire une erreur, comprendre
pourquoi, ne plus la refaire**, puis s'appuyer sur l'expérience acquise pour
éviter les erreurs du passé. Pas de réseau de neurones, pas d'apprentissage
statistique à l'aveugle : chaque correction doit venir d'une **explication**.

À terme, on doit pouvoir mettre la mère devant **n'importe quel problème** (pas
seulement des jeux de plateau). À partir d'un exemple, elle crée son fils, le
corrige erreur après erreur et finit avec un fils parfait.

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

## Correction par la compréhension

À chaque erreur du fils, la mère doit :

1. **comprendre l'état de défaite** (au Morpion : trois pions adverses
   alignés), appris à partir des parties jouées et non codé en dur ;
2. **comprendre pourquoi un meilleur coup est meilleur** : gain, défense,
   double menace, parade… ;
3. **généraliser** cette explication en une règle qui s'applique à toutes les
   positions semblables. C'est ce qui donne une courbe d'apprentissage
   fulgurante : une seule défaite doit corriger toute une famille d'erreurs.

Toute connaissance fournie à la main (vocabulaire d'explications, hypothèses)
doit rester exprimée en termes généraux, jamais en termes propres à un jeu, et
l'objectif est que la mère finisse par la découvrir seule. Les concepts
(`gagner`, `parer`, `fourchette`…) s'écrivent uniquement avec trois notions que
la mère apprend pour chaque jeu : `apres(etat, action, joueur)` (vient de
l'Analyzer), `gagne(etat, joueur)` (fin de partie comprise par la mère) et
`possibles(etat)` (actions permises). Ainsi le même `parer` vaut pour tous les
jeux.

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
- Python 3.10+, aucune dépendance.
- Tests : `python -m unittest discover -s tests -t .`
- Apprendre un exemple : `python -m xander res/exampleMorpion.py`
- Doc : `docs/architecture.md` (fonctionnement), `docs/feuille-de-route.md`
  (état et prochaines étapes), `docs/format-exemple.md` (format des exemples).
