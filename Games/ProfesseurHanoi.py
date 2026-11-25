"""Professeur des Tours de Hanoï : le plus court chemin vers le but, depuis n'importe quelle position.

Avec ``n`` disques, il y a ``3 ** n`` positions (27 pour 3 disques, 81 pour 4).
Un coup se défait par le coup inverse : la distance d'une position au but est
donc sa distance **depuis** le but. Un parcours en largeur parti du but la
donne pour toutes les positions d'un coup (calculé une fois par taille).

Le meilleur coup est un coup permis qui mène à une position plus proche du
but d'un coup ; entre plusieurs (cela n'arrive pas à Hanoï, mais le code ne le
suppose pas), le premier dans l'ordre de :func:`Games.Hanoi.coups_permis`.
Le professeur ne lit que l'état observable.
"""

from collections import deque
from functools import lru_cache

from Games.Hanoi import NB_PIQUETS, apres, but, coups_permis


@lru_cache(maxsize=None)
def distances(nb_disques: int) -> dict[tuple, int]:
    """Pour chaque position (tuple des piquets des disques), le nombre minimal de coups jusqu'au but."""
    depart = tuple(but(nb_disques))
    vues = {depart: 0}
    file = deque([depart])
    while file:
        etat = file.popleft()
        for coup in coups_permis(etat):
            suivant = tuple(apres(etat, *coup))
            if suivant not in vues:
                vues[suivant] = vues[etat] + 1
                file.append(suivant)
    assert len(vues) == NB_PIQUETS ** nb_disques  # toutes les positions sont atteignables
    return vues


def distance(etat) -> int:
    """Le nombre minimal de coups de ``etat`` au but."""
    return distances(len(etat))[tuple(etat)]


def meilleur_coup(etat):
    """Le coup ``(depart, arrivee)`` qui rapproche le plus vite du but (``None`` au but)."""
    reste = distance(etat)
    if reste == 0:
        return None
    return next(coup for coup in coups_permis(etat) if distance(apres(etat, *coup)) == reste - 1)


def professeur_hanoi_play(game, verbose: bool = True):
    """Fait jouer le professeur sur ``game`` (un coup, lu sur l'état observable).

    Renvoie ``True`` si ce coup finit la partie, sinon ``None``.
    """
    etat = game.get_game_state()
    coup = meilleur_coup(etat)
    if coup is None:
        return None
    resultat = game.play(*coup)
    if verbose:
        print(f"Professeur : du piquet {coup[0]} vers le piquet {coup[1]}")
    return True if resultat is True else None
