"""Professeur exact du Compte est bon (il ne fait pas partie de Xander).

Depuis l'état observable (4 places puis la cible), il cherche **en largeur**
le chemin le plus court vers un état où la cible apparaît : tous les coups
permis, puis tous les coups permis après chacun, etc. Les états déjà vus
(les mêmes nombres aux mêmes places) ne sont pas réexplorés. À 4 nombres, la
partie dure au plus 3 coups : la recherche complète regarde au plus quelques
milliers d'états.

Si la cible n'est pas atteignable depuis l'état (un coup maladroit a pu la
rendre impossible), il vise le nombre le plus proche de la cible (règle
classique du jeu), le plus tôt possible. À égalité, le premier coup dans
l'ordre de :func:`Games.CompteEstBon.coups_permis` (``i``, puis ``j``, puis
``op``).
"""

from collections import deque

from Games.CompteEstBon import NB_NOMBRES, VIDE, CompteEstBon, coups_permis, jouer


def meilleur_chemin(etat: list) -> tuple[list, int]:
    """Le chemin le plus court vers la cible depuis ``etat`` : ``(coups, positions regardées)``.

    Sans chemin, celui qui fait apparaître le nombre le plus proche de la cible
    (le plus court à écart égal). ``[]`` si la partie est finie.
    """
    cible = etat[NB_NOMBRES]
    depart = tuple(etat)
    precedent = {depart: None}
    file = deque([depart])
    meilleur, ecart_meilleur = None, None
    while file:
        courant = file.popleft()
        nombres = [n for n in courant[:NB_NOMBRES] if n != VIDE]
        ecart = min(abs(n - cible) for n in nombres)
        if courant != depart and (ecart_meilleur is None or ecart < ecart_meilleur):
            meilleur, ecart_meilleur = courant, ecart
        if ecart == 0:
            break  # en largeur : le premier trouvé est le plus court
        for coup in coups_permis(list(courant)):
            suivant = tuple(jouer(list(courant), *coup))
            if suivant not in precedent:
                precedent[suivant] = (courant, coup)
                file.append(suivant)
    chemin = []
    while meilleur is not None and precedent[meilleur] is not None:
        meilleur, coup = precedent[meilleur]
        chemin.append(coup)
    return chemin[::-1], len(precedent)


def meilleur_coup(etat: list):
    """Le premier coup du meilleur chemin, ou ``None`` si aucun coup n'est permis."""
    chemin, _ = meilleur_chemin(etat)
    return chemin[0] if chemin else None


def solveur_compte_est_bon_play(game: CompteEstBon, verbose: bool = True):
    """Joue un coup sur ``game`` à partir de l'état observable. Renvoie ce que renvoie ``play``."""
    coup = meilleur_coup(game.get_game_state())
    if coup is None:
        return None
    result = game.play(*coup)
    if verbose:
        print(f"Solveur : play{coup}")
    return result
