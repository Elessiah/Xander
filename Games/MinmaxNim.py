"""Professeur exact pour le Nim à plusieurs tas (adversaire de référence).

Il ne fait pas partie de Xander : c'est la stratégie connue du Nim (Bouton,
1901), écrite à la main.

**Version normale** (prendre le dernier objet fait gagner). La « somme de
Nim » d'une position est le ou exclusif (``^``) des tailles des tas. Le joueur
qui a le trait perd si elle est nulle (quoi qu'il fasse, il la rend non
nulle, et l'adversaire peut toujours la ramener à zéro). Sinon, il gagne en
la ramenant à zéro : il existe un tas ``h`` avec ``h ^ s < h`` ; on le réduit
à ``h ^ s``.

**Version misère** (prendre le dernier objet fait perdre). On joue comme en
version normale tant qu'au moins deux tas ont plus d'un objet. Quand il n'en
reste qu'un, on le réduit à 0 ou 1 objet de façon à laisser un nombre
**impair** de tas d'un objet. Quand tous les tas ont au plus un objet, la
position est gagnante si leur nombre est pair.

Depuis une position perdante, le professeur prend un objet dans le plus gros
tas (la partie dure le plus longtemps possible, en espérant une erreur).

:func:`valeur` résout une position par un Minmax exhaustif avec mémoïsation ;
les tests s'en servent pour vérifier la stratégie.
"""

from functools import lru_cache, reduce
from operator import xor

from Games.Nim import Nim, coups


def somme_de_nim(tas) -> int:
    return reduce(xor, tas, 0)


def gagnante(tas, misere: bool = False) -> bool:
    """La position est-elle gagnante pour le joueur qui a le trait ?"""
    if not any(tas):
        # Partie finie : l'adversaire a pris le dernier objet.
        return misere
    if misere and all(size <= 1 for size in tas):
        return sum(tas) % 2 == 0
    return somme_de_nim(tas) != 0


def meilleur_coup(tas, misere: bool = False) -> tuple:
    """Le coup du professeur : ``(tas, nombre)``. ``tas`` ne doit pas être vide de partout."""
    tas = list(tas)
    if not any(tas):
        raise ValueError("plus aucun objet : la partie est finie")
    gros = [i for i, size in enumerate(tas) if size > 1]
    if misere and len(gros) <= 1:
        uns = sum(1 for size in tas if size == 1)
        if not gros:
            # Que des tas d'un objet : on en prend un (le seul coup possible, à l'ordre près).
            return tas.index(1), 1
        # Un seul gros tas : laisser un nombre impair de tas d'un objet.
        i = gros[0]
        reste = 1 if uns % 2 == 0 else 0
        return i, tas[i] - reste
    s = somme_de_nim(tas)
    if s:
        for i, size in enumerate(tas):
            if size ^ s < size:
                return i, size - (size ^ s)
    # Position perdante : un objet du plus gros tas.
    return tas.index(max(tas)), 1


@lru_cache(maxsize=None)
def _valeur(tas: tuple, misere: bool) -> bool:
    if not any(tas):
        return misere
    for i, n in coups(tas):
        suite = list(tas)
        suite[i] -= n
        if not _valeur(tuple(sorted(suite)), misere):
            return True
    return False


def valeur(tas, misere: bool = False) -> bool:
    """Minmax exhaustif mémoïsé : la position est-elle gagnante pour le joueur qui a le trait ?"""
    return _valeur(tuple(sorted(tas)), misere)


def minmax_nim_play(game: Nim, verbose: bool = True):
    """Fait jouer le professeur sur ``game``. Renvoie le gagnant si le coup termine la partie."""
    turn = game.get_turn()
    tas, nombre = meilleur_coup(game.get_game_state(), game.MISERE)
    result = game.play(tas, nombre)
    if verbose:
        print(f"Minmax {turn} a pris {nombre} objet(s) dans le tas {tas}")
    return game.win if result is True else None
