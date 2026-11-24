"""Joueur Minmax pour le Morpion (adversaire de référence, codé à la main).

Deux étages :

1. une **heuristique** qui note chaque case libre selon les lignes qui la
   traversent (préparer un alignement, bloquer l'adversaire...) ;
2. un **minimax** avec élagage alpha-bêta qui explore l'arbre de jeu complet
   (le morpion est assez petit) ; l'heuristique sert à départager les coups
   de même valeur et à ordonner l'exploration.

Le joueur ne perd donc jamais ; deux Minmax font toujours match nul.
"""

from functools import lru_cache

from Games.Morpion import LINES, Morpion, is_free, other_player, winner_of

COEFS = {"close": 2, "block": 4, "end": 3}
WIN_SCORE = 10


# --------------------------------------------------------------------------- #
# Heuristique
# --------------------------------------------------------------------------- #

def line_score(board: list, line: tuple, turn: str) -> int:
    """Intérêt d'une ligne pour ``turn`` selon les symboles déjà posés."""
    ally = sum(board[i] == turn for i in line)
    enemy = sum(not is_free(board[i]) and board[i] != turn for i in line)
    score = 0
    if ally == 0 and enemy == 0:
        score += COEFS["close"]          # ligne encore vierge
    if enemy == 0:
        score += ally * COEFS["end"]     # on prépare / termine un alignement
    if ally == 0:
        score += enemy * COEFS["block"]  # on gêne l'adversaire
    return score


def define_board_score(turn: str, board: list) -> list:
    """Note de chaque case (``-1`` pour une case occupée)."""
    scored_board = []
    for index, slot in enumerate(board):
        if not is_free(slot):
            scored_board.append(-1)
            continue
        scored_board.append(sum(line_score(board, line, turn) for line in LINES if index in line))
    return scored_board


# --------------------------------------------------------------------------- #
# Minimax
# --------------------------------------------------------------------------- #

def ordered_moves(board: list, turn: str) -> list:
    scores = define_board_score(turn, board)
    moves = [i for i, slot in enumerate(board) if is_free(slot)]
    return sorted(moves, key=lambda move: -scores[move])


@lru_cache(maxsize=None)
def negamax(board: tuple, turn: str, alpha: int = -WIN_SCORE - 10, beta: int = WIN_SCORE + 10) -> int:
    """Valeur du plateau pour le joueur ``turn`` qui doit jouer (gagner vite vaut plus)."""
    result = winner_of(board)
    if result == "D":
        return 0
    if result:  # le joueur précédent vient de gagner (plus tôt = pire pour nous)
        return -WIN_SCORE - _free_count(board)
    best = -WIN_SCORE - 10
    for move in ordered_moves(list(board), turn):
        child = list(board)
        child[move] = turn
        value = -negamax(tuple(child), other_player(turn), -beta, -alpha)
        best = max(best, value)
        alpha = max(alpha, value)
        if alpha >= beta:
            break
    return best


def _free_count(board) -> int:
    return sum(is_free(slot) for slot in board)


def best_move(board: list, turn: str) -> int:
    """Coup optimal ; à valeur égale, celui que l'heuristique préfère."""
    best, best_value = None, None
    for move in ordered_moves(board, turn):
        child = list(board)
        child[move] = turn
        value = -negamax(tuple(child), other_player(turn))
        if best_value is None or value > best_value:
            best, best_value = move, value
    return best


def minmax_morpion_play(game: Morpion, verbose: bool = False):
    """Fait jouer Minmax sur ``game``. Renvoie le gagnant si le coup termine la partie."""
    turn = game.get_turn()
    board = game.get_game_state()
    move = best_move(board, turn)
    if verbose:
        print(f"Minmax {turn} joue {move} (notes : {define_board_score(turn, board)})")
    if game.play(move) is True:
        return game.win
    return None
