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
- **Le fils joue, c'est tout.** Il lit l'état, applique ce que la mère lui a
  donné (par exemple des règles par priorité) et joue. **Il n'utilise jamais
  `back`** et ne fait pas de force brute avec essai et annulation.
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
doit rester exprimée en termes généraux (motifs, cases, quantités), jamais en
termes propres à un jeu, et l'objectif est que la mère finisse par la découvrir
seule.

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
nouveau fils, sur un autre jeu ou un autre problème.

## Pratique

- Le code, les commentaires, la doc et les messages de commit sont en **français**.
- Python 3.10+, aucune dépendance.
- Tests : `python -m unittest discover -s tests -t .`
- Apprendre un exemple : `python -m xander res/exampleMorpion.py`
- Doc : `docs/architecture.md` (fonctionnement), `docs/feuille-de-route.md`
  (état et prochaines étapes), `docs/format-exemple.md` (format des exemples).
