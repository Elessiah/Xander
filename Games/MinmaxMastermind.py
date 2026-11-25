"""Professeur pour le Mastermind (joueur de référence, codé à la main).

Il ne fait pas partie de Xander et ne triche pas : il ne lit jamais le
secret, seulement le plateau (``get_game_state``) et les règles (longueur du
code, chiffres permis). Il est déterministe.

Les **codes compatibles** sont ceux qui, s'ils étaient le secret, auraient
donné exactement les réponses déjà reçues. Deux stratégies :

- :func:`premier_compatible` : proposer le premier code compatible dans
  l'ordre (``111``, ``112``…). Simple, et jamais absurde : chaque
  proposition peut être le secret ;
- :func:`meilleur_code` (le professeur, à la manière de Knuth, 1977) :
  proposer le code dont la **pire** réponse laisse le moins de codes
  compatibles. À égalité, on préfère un code compatible (il peut gagner
  tout de suite), puis le premier dans l'ordre.

Mesures sur les 216 secrets possibles (3 chiffres de 1 à 6), vérifiées par
les tests : le professeur trouve en 4,05 essais en moyenne (874 essais pour
216 secrets) et 5 au plus ; « premier compatible » en 5,26 en moyenne et 8 au
plus, tout juste la limite du jeu (8 essais). Commencer par ``111`` coûte
cher : une proposition qui peut gagner n'est pas toujours celle qui apprend
le plus.
"""

from functools import lru_cache

from Games.Mastermind import Mastermind, historique, reponse, tous_les_codes


def compatibles(coups, codes) -> list:
    """Les codes de ``codes`` qui donnent les réponses de ``coups`` (``[(code, réponse), …]``)."""
    return [c for c in codes if all(reponse(c, code) == rep for code, rep in coups)]


def premier_compatible(coups, longueur: int, chiffres: int) -> tuple:
    return compatibles(coups, tous_les_codes(longueur, chiffres))[0]


@lru_cache(maxsize=None)
def _meilleur(coups: tuple, longueur: int, chiffres: int) -> tuple:
    codes = tous_les_codes(longueur, chiffres)
    restants = compatibles(coups, codes)
    if len(restants) <= 2:
        return restants[0]
    candidats = set(restants)
    meilleur, note = None, None
    for code in codes:
        tailles = {}
        for secret in restants:
            rep = reponse(secret, code)
            tailles[rep] = tailles.get(rep, 0) + 1
        n = (max(tailles.values()), code not in candidats)
        if note is None or n < note:
            meilleur, note = code, n
    return meilleur


def meilleur_code(coups, longueur: int, chiffres: int) -> tuple:
    """La proposition du professeur, d'après les coups déjà joués."""
    return _meilleur(tuple(coups), longueur, chiffres)


def minmax_mastermind_play(game: Mastermind, verbose: bool = True):
    """Fait jouer une proposition au professeur. Renvoie le gagnant si elle termine la partie."""
    coups = historique(game.get_game_state(), game.longueur)
    code = meilleur_code(coups, game.longueur, game.chiffres)
    result = game.play(*code)
    if verbose:
        print(f"Professeur : {''.join(map(str, code))}")
    return game.win if result is True else None


def premier_compatible_play(game: Mastermind, verbose: bool = True):
    """Joue le premier code compatible. Renvoie le gagnant si le coup termine la partie."""
    coups = historique(game.get_game_state(), game.longueur)
    code = premier_compatible(coups, game.longueur, game.chiffres)
    result = game.play(*code)
    if verbose:
        print(f"Premier compatible : {''.join(map(str, code))}")
    return game.win if result is True else None
