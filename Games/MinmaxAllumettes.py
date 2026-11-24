"""Joueur Minmax pour le jeu des allumettes (adversaire de référence).

Stratégie gagnante de la variante misère avec des prises de 1 à 3 : laisser
à l'adversaire un nombre d'allumettes ``n`` tel que ``(n - 1) % 4 == 0``
(1, 5, 9, 13...). Depuis ``n`` allumettes, il faut donc en retirer
``(n - 1) % 4``. Si ce reste vaut 0, la position est perdante : on retire 1
en espérant une erreur de l'adversaire.

L'ancienne version raisonnait en « tiers » (``% 3`` puis ``% 2``, voir
``docs/jeux.md``) et se trompait sur une partie des positions.
"""

from Games.Allumettes import MAX_TAKE, Allumettes


def define_choice_score(nb_allumettes: int) -> dict:
    """Note de chaque prise possible (1 pour le bon coup, 0 sinon)."""
    scored_choice = {take: 0 for take in range(1, MAX_TAKE + 1)}
    winning_take = (nb_allumettes - 1) % (MAX_TAKE + 1)
    scored_choice[winning_take or 1] = 1
    return scored_choice


def get_best_choice(scored_choice: dict) -> int:
    return max(scored_choice, key=scored_choice.get)


def minmax_allumettes_play(game: Allumettes, verbose: bool = True):
    """Fait jouer Minmax sur ``game``. Renvoie le gagnant si le coup termine la partie."""
    turn = game.get_turn()
    nb_allumettes = game.get_game_state()
    choice = min(get_best_choice(define_choice_score(nb_allumettes)), nb_allumettes)
    result = game.play(choice)
    if verbose:
        print(f"Minmax {turn} a retiré {choice} allumette(s)")
    return game.win if result is True else None
