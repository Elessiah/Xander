"""Joueur Minmax pour le Puissance 4 (adversaire de référence, codé à la main).

L'arbre complet est bien trop grand : on explore ``depth`` demi-coups avec un
negamax à élagage alpha-bêta, puis on note les feuilles avec une heuristique :

- chaque **fenêtre** de 4 cases alignées (69 au total) qui ne contient que des
  jetons d'un seul joueur rapporte à ce joueur selon leur nombre ;
- les jetons de la **colonne centrale**, qui appartient au plus de fenêtres,
  valent un petit bonus.

Une victoire vaut ``WIN_SCORE`` plus la profondeur restante : gagner vite vaut
plus, perdre tard coûte moins. Les colonnes sont explorées du centre vers les
bords, ce qui accélère l'élagage et départage les coups de même valeur.
"""

from Games.Puissance4 import EMPTY, Puissance4

WIDTH, HEIGHT = 7, 6
CENTER = WIDTH // 2
COLUMN_ORDER = tuple(sorted(range(WIDTH), key=lambda x: abs(x - CENTER)))  # 3, 2, 4, 1, 5, 0, 6
DEFAULT_DEPTH = 6
WIN_SCORE = 1_000_000
INFINITY = 10 * WIN_SCORE

# Points d'une fenêtre selon le nombre de jetons d'un même joueur (sans adversaire).
WINDOW_POINTS = {0: 0, 1: 0, 2: 2, 3: 5, 4: 0}
CENTER_POINTS = 3


def _index(x: int, y: int) -> int:
    return y * WIDTH + x


def _build_windows() -> list:
    windows = []
    for x in range(WIDTH):
        for y in range(HEIGHT):
            for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
                end_x, end_y = x + 3 * dx, y + 3 * dy
                if 0 <= end_x < WIDTH and 0 <= end_y < HEIGHT:
                    windows.append(tuple(_index(x + k * dx, y + k * dy) for k in range(4)))
    return windows


WINDOWS = _build_windows()
WINDOWS_BY_CELL = [[w for w in WINDOWS if i in w] for i in range(WIDTH * HEIGHT)]


def other_player(turn: str) -> str:
    return "O" if turn == "X" else "X"


def column_heights(board: list) -> list:
    """Nombre de jetons dans chaque colonne (= ligne où tombera le prochain)."""
    heights = []
    for x in range(WIDTH):
        y = 0
        while y < HEIGHT and board[_index(x, y)] != EMPTY:
            y += 1
        heights.append(y)
    return heights


def is_winning_move(board: list, index: int) -> bool:
    """Le jeton posé en ``index`` complète-t-il un alignement de 4 ?"""
    player = board[index]
    return any(all(board[i] == player for i in window) for window in WINDOWS_BY_CELL[index])


# --------------------------------------------------------------------------- #
# Heuristique
# --------------------------------------------------------------------------- #

def evaluate(board: list, turn: str) -> int:
    """Note du plateau pour ``turn`` (positive : ``turn`` est mieux placé)."""
    enemy = other_player(turn)
    score = 0
    for window in WINDOWS:
        ally_count = enemy_count = 0
        for i in window:
            slot = board[i]
            if slot == turn:
                ally_count += 1
            elif slot == enemy:
                enemy_count += 1
        if enemy_count == 0:
            score += WINDOW_POINTS[ally_count]
        elif ally_count == 0:
            score -= WINDOW_POINTS[enemy_count]
    for y in range(HEIGHT):
        slot = board[_index(CENTER, y)]
        if slot == turn:
            score += CENTER_POINTS
        elif slot == enemy:
            score -= CENTER_POINTS
    return score


# --------------------------------------------------------------------------- #
# Negamax
# --------------------------------------------------------------------------- #

def negamax(board: list, heights: list, turn: str, depth: int, alpha: int, beta: int) -> int:
    """Valeur du plateau pour ``turn``, qui doit jouer (le coup précédent n'a pas gagné).

    ``board`` et ``heights`` sont modifiés pendant la recherche puis restaurés.
    """
    if depth == 0:
        return evaluate(board, turn)
    best = None
    for x in COLUMN_ORDER:
        y = heights[x]
        if y == HEIGHT:
            continue
        i = _index(x, y)
        board[i] = turn
        heights[x] += 1
        if is_winning_move(board, i):
            value = WIN_SCORE + depth
        else:
            value = -negamax(board, heights, other_player(turn), depth - 1, -beta, -alpha)
        board[i] = EMPTY
        heights[x] -= 1
        if best is None or value > best:
            best = value
        alpha = max(alpha, value)
        if alpha >= beta:
            break
    return 0 if best is None else best  # plateau plein : match nul


def best_move(board: list, turn: str, depth: int = DEFAULT_DEPTH):
    """Meilleure colonne ; à valeur égale, la plus proche du centre. ``None`` si le plateau est plein."""
    board = list(board)
    heights = column_heights(board)
    best, best_value = None, None
    alpha = -INFINITY
    for x in COLUMN_ORDER:
        y = heights[x]
        if y == HEIGHT:
            continue
        i = _index(x, y)
        board[i] = turn
        heights[x] += 1
        if is_winning_move(board, i):
            value = WIN_SCORE + depth
        else:
            value = -negamax(board, heights, other_player(turn), depth - 1, -INFINITY, -alpha)
        board[i] = EMPTY
        heights[x] -= 1
        if best_value is None or value > best_value:
            best, best_value = x, value
            alpha = max(alpha, value)
    return best


def minmax_puissance4_play(game: Puissance4, verbose: bool = True, depth: int = DEFAULT_DEPTH):
    """Fait jouer Minmax sur ``game``. Renvoie le gagnant si le coup termine la partie."""
    turn = game.get_turn()
    board = game.get_game_state()
    move = best_move(board, turn, depth)
    result = game.play(move)
    if verbose:
        print(f"Minmax {turn} joue la colonne {move}")
    return game.win if result is True else None
