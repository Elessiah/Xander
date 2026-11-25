"""Morpion à trois joueurs (``X``, ``O``, ``Z``) sur un plateau 4 × 4, trois alignés gagnent.

Le plateau est une liste plate de ``size * size`` chaînes, comme au Morpion :
une case libre contient son indice (``"0"`` à ``"15"``), une case jouée
contient ``"X"``, ``"O"`` ou ``"Z"`` ::

     0 |  1 |  2 |  3
     4 |  5 |  6 |  7
     8 |  9 | 10 | 11
    12 | 13 | 14 | 15

Les joueurs jouent à tour de rôle dans l'ordre ``X -> O -> Z -> X``, à partir
du premier joueur choisi. Le premier qui aligne ``k`` pions (horizontalement,
verticalement ou en diagonale) gagne ; plateau plein sans alignement : nul.

La taille et ``k`` se changent (``Morpion3(size=5, k=3)``) ; les valeurs par
défaut, 4 × 4 et ``k = 3``, sont justifiées dans ``docs/jeux.md``.
"""

import random

from Games.Coords import Coords

PLAYERS = ("X", "O", "Z")
DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))  # horizontale, verticale, deux diagonales
DEFAULT_SIZE = 4
DEFAULT_K = 3


def is_free(slot: str) -> bool:
    return slot.isdigit()


def next_player(player: str) -> str:
    """Le joueur qui joue après ``player`` (``X -> O -> Z -> X``)."""
    return PLAYERS[(PLAYERS.index(player) + 1) % len(PLAYERS)]


def build_lines(size: int, k: int) -> tuple:
    """Toutes les fenêtres de ``k`` cases alignées sur un plateau ``size`` × ``size``."""
    lines = []
    for y in range(size):
        for x in range(size):
            for dx, dy in DIRECTIONS:
                end_x, end_y = x + (k - 1) * dx, y + (k - 1) * dy
                if 0 <= end_x < size and 0 <= end_y < size:
                    lines.append(tuple((y + j * dy) * size + x + j * dx for j in range(k)))
    return tuple(lines)


def winner_of(board, lines) -> str:
    """``"X"``/``"O"``/``"Z"`` si un joueur a aligné ``k`` pions, ``"D"`` si le plateau est plein, sinon ``""``."""
    for line in lines:
        first = board[line[0]]
        if not is_free(first) and all(board[i] == first for i in line):
            return first
    if not any(is_free(slot) for slot in board):
        return "D"
    return ""


class Morpion3:
    def __init__(self, size: int = DEFAULT_SIZE, k: int = DEFAULT_K):
        self.size = size
        self.k = k
        self.lines = build_lines(size, k)
        self.nb_turn = 0
        self.player = "X"
        self.win = ""  # "X"/"O"/"Z" : victoire d'un joueur, "D" : match nul
        self.board = []
        self.past = []  # états précédents, pour back()
        self.start_player = "X"
        self.init(self.start_player)

    # Initialisation
    def init(self, start_player="R"):  # Pattern Name
        """Vide le plateau. ``start_player`` : ``"X"``, ``"O"``, ``"Z"`` ou ``"R"`` (aléatoire)."""
        self.start_player = start_player
        self.board = [str(i) for i in range(self.size * self.size)]
        self.past.clear()
        self.nb_turn = 0
        self.win = ""
        self.player = random.choice(PLAYERS) if start_player == "R" else start_player
        return self.board.copy()

    # Fonctions de jeu
    def play(self, move):  # Pattern Name
        """Joue la case ``move``.

        Renvoie ``False`` si le coup est invalide (partie finie, case occupée,
        hors plateau, pas un entier ; un booléen est refusé), ``True`` si la
        partie est terminée (victoire ou nul), sinon une copie du plateau.
        """
        if self.win or type(move) is not int or not 0 <= move < len(self.board):
            return False
        if not is_free(self.board[move]):
            return False
        self.past.append((self.board.copy(), self.player, self.nb_turn))
        self.board[move] = self.player
        self.nb_turn += 1
        self.win = winner_of(self.board, self.lines)
        if self.win:
            return True
        self.player = next_player(self.player)
        return self.board.copy()

    def get_game_state(self):  # Pattern Name
        """Renvoie le plateau. Si la partie précédente est finie, en recommence une."""
        if self.win:
            self.init(self.start_player)
        return self.board.copy()

    def get_turn(self):  # Pattern Name
        return self.player

    def get_moves(self):
        """Cases encore jouables."""
        if self.win:
            return []
        return [i for i, slot in enumerate(self.board) if is_free(slot)]

    def print(self):  # Pattern Name
        print("Plateau :\n")
        coords = Coords(width=self.size)
        for y in range(self.size):
            for x in range(self.size):
                coords.set(x=x, y=y)
                print(f"[{self.board[coords.i]:>2}] ", end="")
            print("\n")

    # Fonctions d'administration
    def back(self):  # Pattern Name
        """Annule le dernier coup, rend la main à celui qui l'avait joué et renvoie le plateau."""
        if self.past:
            self.board, self.player, self.nb_turn = self.past.pop()
            self.win = ""
        return self.board.copy()

    def set_game_state(self, new_board, player=None):
        """Impose un plateau. ``player`` doit jouer ; s'il est omis, on suppose
        que X a commencé et on le déduit du nombre de pions posés.

        Renvoie ``True`` si la partie est finie sur ce plateau (victoire ou nul).
        """
        self.board = list(new_board)
        self.past.clear()
        self.nb_turn = sum(not is_free(slot) for slot in self.board)
        self.player = player or PLAYERS[self.nb_turn % len(PLAYERS)]
        self.win = winner_of(self.board, self.lines)
        return bool(self.win)
