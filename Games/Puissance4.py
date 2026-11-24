"""Puissance 4 (7 colonnes x 6 lignes).

Le plateau est une liste de 42 cases (``" "``, ``"X"`` ou ``"O"``) indexée
par :class:`Coords` ; la ligne ``y = 0`` est celle du bas.
"""

import random

from Games.Coords import Coords

DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))  # horizontale, verticale, deux diagonales
EMPTY = " "


class Puissance4:
    def __init__(self):
        self.nb_turn = 0
        self.player = "X"
        self.win = ""
        self.board = []
        self.past = []
        self.start_player = "X"
        self.width = 7
        self.height = 6
        self.init(self.start_player)

    # Initialisation
    def init(self, start_player: str = "R"):  # Pattern Name
        self.start_player = start_player
        self.reset_var()
        return self.board.copy()

    # Fonctions de jeu
    def play(self, column):  # Pattern Name
        """Lâche un jeton dans ``column``.

        Renvoie ``False`` si le coup est invalide, ``True`` si la partie est
        terminée, sinon une copie du plateau.
        """
        if self.win or type(column) is not int or not 0 <= column < self.width:
            return False
        coords = self.set_token(column)
        if coords is None:
            return False  # colonne pleine
        if self.check_win_slot(coords):
            self.win = self.player
            return True
        if all(slot != EMPTY for slot in self.board):
            self.win = "D"
            return True
        self.next_player()
        return self.board.copy()

    def get_game_state(self):  # Pattern Name
        if self.win:
            self.init(self.start_player)
        return self.board.copy()

    def get_moves(self):
        """Colonnes encore jouables."""
        top = (self.height - 1) * self.width
        return [x for x in range(self.width) if self.board[top + x] == EMPTY]

    def get_turn(self):  # Pattern Name
        return self.player

    def print(self):  # Pattern Name
        coords = Coords(width=self.width)
        for y in range(self.height - 1, -1, -1):
            row = []
            for x in range(self.width):
                coords.set(x=x, y=y)
                row.append(self.board[coords.i])
            print("|" + "|".join(row) + "|")
        print(" " + " ".join(str(x) for x in range(self.width)))

    # Fonctions d'administration
    def back(self):  # Pattern Name
        if self.past:
            self.board, self.player, self.nb_turn = self.past.pop()
            self.win = ""
        return self.board.copy()

    # Outils internes
    def set_token(self, column: int):
        """Pose le jeton au plus bas de la colonne ; renvoie sa position ou ``None``."""
        coords = Coords(width=self.width)
        for y in range(self.height):
            coords.set(x=column, y=y)
            if self.board[coords.i] == EMPTY:
                self.past.append((self.board.copy(), self.player, self.nb_turn))
                self.board[coords.i] = self.player
                self.nb_turn += 1
                return coords
        return None

    def count_direction(self, coords: Coords, dx: int, dy: int) -> int:
        """Jetons identiques consécutifs depuis ``coords`` (exclu) dans la direction (dx, dy)."""
        target = self.board[coords.i]
        x, y, count = coords.x + dx, coords.y + dy, 0
        probe = Coords(width=self.width)
        while 0 <= x < self.width and 0 <= y < self.height:
            probe.set(x=x, y=y)
            if self.board[probe.i] != target:
                break
            count += 1
            x, y = x + dx, y + dy
        return count

    def check_win_slot(self, coords: Coords) -> bool:
        if self.board[coords.i] == EMPTY:
            return False
        return any(1 + self.count_direction(coords, dx, dy) + self.count_direction(coords, -dx, -dy) >= 4
                   for dx, dy in DIRECTIONS)

    def check_win(self) -> bool:
        coords = Coords(width=self.width)
        for i in range(self.width * self.height):
            coords.set(i=i)
            if self.check_win_slot(coords):
                return True
        return False

    def next_player(self):
        self.player = "O" if self.player == "X" else "X"

    def reset_player(self):
        self.player = random.choice("XO") if self.start_player == "R" else self.start_player

    def reset_board(self):
        self.board = [EMPTY] * (self.width * self.height)

    def reset_var(self):
        self.nb_turn = 0
        self.reset_player()
        self.win = ""
        self.reset_board()
        self.past.clear()
