"""Nim à plusieurs tas, variante misère : celui qui prend le dernier objet perd.

Mêmes règles et même interface que :mod:`Games.Nim` ; seule la fin change.
Le dernier coup fait perdre celui qui le joue : quand tous les tas sont
vides, c'est le joueur qui a le trait qui a gagné.

Professeur : :func:`Games.MinmaxNim.minmax_nim_play`, qui lit ``MISERE``.
"""

from Games.Nim import Nim


class NimMisere(Nim):
    MISERE = True
