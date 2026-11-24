"""Jumper : un coureur qui saute par-dessus des obstacles (jeu à un joueur).

L'écran fait 40 x 5 caractères (200 cases, ``y = 0`` en haut, sol en
``y = 4``). À chaque ``play`` le décor avance d'une case ; ``play(True)``
fait sauter le joueur s'il est au sol. Toucher un obstacle termine la partie.

Symboles : ``*`` joueur, ``T`` obstacle, ``-`` sol, espace vide.
"""

import copy
import random

from Games.Coords import Coords

WIDTH, HEIGHT = 40, 5
FLOOR = HEIGHT - 1
PLAYER_X = 1


class Obstacle:
    def __init__(self, creation_date, board_length, length):
        self.creation_date = creation_date
        self.length = length
        self.position = board_length - 1

    def __hash__(self):
        return hash(self.creation_date)

    def __eq__(self, other):
        return isinstance(other, Obstacle) and self.creation_date == other.creation_date

    def covers(self, x):
        return self.position <= x < self.position + self.length

    def draw(self, board, width, floor=FLOOR):
        coords = Coords(width=width)
        for i in range(self.length):
            x = self.position + i
            if 0 <= x < width:
                coords.set(x=x, y=floor)
                board[coords.i] = "T"

    def shift_left_board(self):
        """Décale l'obstacle ; renvoie ``False`` quand il est sorti de l'écran."""
        self.position -= 1
        return self.position + self.length > 0


class Jumper:
    def __init__(self, seed=None):
        self.random = random.Random(seed)
        self.ticks = 0
        self.board = []  # décor fixe (vide + sol)
        self.past = []
        self.obstacles = []
        self.last_obstacle = 0
        self.player_pos = Coords(width=WIDTH)
        self.player_ascending = False
        self.game_over = False
        self.init()

    def init(self):  # Pattern Name
        self.ticks = 0
        self.board = [" "] * (WIDTH * FLOOR) + ["-"] * WIDTH
        self.past.clear()
        self.obstacles = []
        self.last_obstacle = 0
        self.player_pos.set(x=PLAYER_X, y=FLOOR)
        self.player_ascending = False
        self.game_over = False
        return self.get_board()

    def play(self, do_jump=False):  # Pattern Name
        """Avance d'une image. Renvoie l'écran, ou ``False`` si le joueur est touché."""
        if self.game_over:
            return False
        self.past.append(self._snapshot())
        self.ticks += 1

        if do_jump and self.player_pos.y == FLOOR:
            self.player_ascending = True
        if self.player_ascending:
            self.player_pos.set(y=self.player_pos.y - 1)
            if self.player_pos.y == 0:
                self.player_ascending = False
        elif self.player_pos.y != FLOOR:
            self.player_pos.set(y=self.player_pos.y + 1)

        self.shift_left_board()

        if self.player_pos.y == FLOOR and any(o.covers(self.player_pos.x) for o in self.obstacles):
            self.game_over = True
            return False
        return self.get_board()

    def shift_left_board(self):
        if self.ticks - self.last_obstacle > 10 and self.random.randint(1, 5) == 1:
            self.last_obstacle = self.ticks
            self.obstacles.append(Obstacle(self.ticks, WIDTH, self.random.randint(1, 3)))
        self.obstacles = [o for o in self.obstacles if o.shift_left_board()]

    def get_board(self):  # Pattern Name
        """Écran courant : décor + obstacles + joueur (liste de 200 caractères)."""
        frame = self.board.copy()
        for obstacle in self.obstacles:
            obstacle.draw(frame, WIDTH)
        frame[self.player_pos.i] = "*"
        return frame

    def print(self):  # Pattern Name
        frame = self.get_board()
        print(f"Distance: {self.ticks}")
        for y in range(HEIGHT):
            print("".join(frame[y * WIDTH:(y + 1) * WIDTH]))

    def back(self):  # Pattern Name
        """Revient à l'image précédente et renvoie l'écran."""
        if self.past:
            state = self.past.pop()
            self.ticks, self.last_obstacle, self.player_ascending, self.obstacles = state[:4]
            self.player_pos.set(x=state[4], y=state[5])
            self.random.setstate(state[6])
            self.game_over = False
        return self.get_board()

    def _snapshot(self):
        return (self.ticks, self.last_obstacle, self.player_ascending,
                copy.deepcopy(self.obstacles), self.player_pos.x, self.player_pos.y,
                self.random.getstate())
