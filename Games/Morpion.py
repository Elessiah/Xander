"""Morpion (tic-tac-toe) 3x3.

Le plateau est une liste de 9 chaînes : une case libre contient son indice
(``"0"`` à ``"8"``), une case jouée contient ``"X"`` ou ``"O"`` ::

    0 | 1 | 2
    3 | 4 | 5
    6 | 7 | 8
"""

import random

from Games.Coords import Coords

LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # lignes
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # colonnes
    (0, 4, 8), (2, 4, 6),             # diagonales
)


def is_free(slot: str) -> bool:
    return slot.isdigit()


def other_player(player: str) -> str:
    return "O" if player == "X" else "X"


def winner_of(board: list) -> str:
    """Renvoie ``"X"``/``"O"`` si un joueur a aligné trois symboles, ``"D"`` si nul, sinon ``""``."""
    for a, b, c in LINES:
        if not is_free(board[a]) and board[a] == board[b] == board[c]:
            return board[a]
    if not any(is_free(slot) for slot in board):
        return "D"
    return ""


class Morpion:
    def __init__(self):
        self.nb_turn = 0
        self.player = "X"
        self.win = ""  # "X"/"O" : victoire d'un joueur, "D" : match nul
        self.board = []
        self.past = []  # états précédents, pour back()
        self.start_player = "X"
        self.init(self.start_player)

    # Initialisation
    def init(self, start_player="R"):  # Pattern Name
        """Vide le plateau. ``start_player`` : ``"X"``, ``"O"`` ou ``"R"`` (aléatoire)."""
        self.start_player = start_player
        self.board = [str(i) for i in range(9)]
        self.past.clear()
        self.nb_turn = 0
        self.win = ""
        self.player = random.choice("XO") if start_player == "R" else start_player
        return self.board.copy()

    # Fonctions de jeu
    def play(self, move):  # Pattern Name
        """Joue la case ``move``.

        Renvoie ``False`` si le coup est invalide, ``True`` si la partie est
        terminée (victoire ou nul), sinon une copie du plateau.
        """
        if self.win or not isinstance(move, int) or not 0 <= move < len(self.board):
            return False
        if not is_free(self.board[move]):
            return False
        self.past.append((self.board.copy(), self.player, self.nb_turn))
        self.board[move] = self.player
        self.nb_turn += 1
        self.win = winner_of(self.board)
        if self.win:
            return True
        self.player = other_player(self.player)
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
        return [i for i, slot in enumerate(self.board) if is_free(slot)]

    def print(self):  # Pattern Name
        print("Plateau :\n")
        coords = Coords(width=3)
        for y in range(3):
            for x in range(3):
                coords.set(x=x, y=y)
                print(f"[{self.board[coords.i]}] ", end="")
            print("\n")

    # Fonctions d'administration
    def back(self):  # Pattern Name
        """Annule le dernier coup et renvoie le plateau."""
        if self.past:
            self.board, self.player, self.nb_turn = self.past.pop()
            self.win = ""
        return self.board.copy()

    def set_game_state(self, new_board):
        """Impose un plateau ; le joueur courant est déduit du nombre de symboles.

        Renvoie ``True`` si ce plateau est gagnant pour l'un des joueurs.
        """
        self.board = list(new_board)
        self.past.clear()
        nb_x, nb_o = self.board.count("X"), self.board.count("O")
        self.player = "O" if nb_o < nb_x else "X"
        self.nb_turn = nb_x + nb_o
        self.win = winner_of(self.board)
        return self.check_win()

    def check_win(self):
        return self.win in ("X", "O")

    def check_draw(self):
        return self.win == "D"
