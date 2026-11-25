"""Pylos : une pyramide de billes, sur une base de ``size`` × ``size``.

Les emplacements forment des étages : l'étage 0 est la base (``size`` × ``size``),
l'étage 1 compte ``size - 1`` × ``size - 1`` emplacements, et ainsi de suite
jusqu'au sommet. Un emplacement d'un étage supérieur repose sur les quatre
emplacements qui sont sous lui. Le plateau est une liste de tous les
emplacements (``" "``, ``"X"`` ou ``"O"``), étage par étage, ligne par ligne.

Chaque joueur a une réserve de billes (la moitié du nombre d'emplacements).
À son tour, un joueur :

1. **pose** une bille de sa réserve sur un emplacement libre et soutenu
   (``play(dest)``), ou **monte** une de ses billes libres vers un emplacement
   plus haut qu'elle ne soutient pas (``move(src, dest)``). Une bille est libre
   quand aucune bille ne repose sur elle ;
2. si la bille posée ou montée complète un **carré** de 2 × 2 billes de sa
   couleur sur un même étage, il **reprend** une de ses billes libres
   (``take(cell)``), puis il peut en reprendre une deuxième ou s'arrêter
   (``stop()``). Les billes reprises retournent dans sa réserve.

Un joueur qui ne peut plus rien faire à son tour (réserve vide et aucune
bille à monter, ou pyramide complète) a perdu : poser la bille du sommet fait
donc gagner. Variante choisie ici : un joueur dont la réserve est vide continue
tant qu'il peut monter une bille.

La géométrie (:class:`Pyramide`) et les règles (:func:`actions`,
:func:`apply_action`) sont des fonctions pures, partagées avec le Minmax.
"""

import random
from functools import lru_cache

EMPTY = " "

# Phases d'un tour.
PLAY = 0       # poser ou monter une bille
TAKE = 1       # un carré vient d'être formé : reprendre une bille
TAKE_MORE = 2  # une bille reprise : en reprendre une deuxième ou s'arrêter


def other_player(player: str) -> str:
    return "O" if player == "X" else "X"


class Pyramide:
    """Géométrie d'une pyramide de base ``size`` × ``size``."""

    def __init__(self, size: int):
        if size < 2:
            raise ValueError("la base doit faire au moins 2 × 2")
        self.size = size
        self.spots = []  # (étage, x, y) de chaque emplacement
        index = {}
        for level in range(size):
            width = size - level
            for y in range(width):
                for x in range(width):
                    index[(level, x, y)] = len(self.spots)
                    self.spots.append((level, x, y))
        self.nb_spots = len(self.spots)
        self.per_player = (self.nb_spots + 1) // 2
        self.level = [level for level, _, _ in self.spots]
        self.supports = []  # les quatre emplacements sous chaque emplacement
        for level, x, y in self.spots:
            if level == 0:
                self.supports.append(())
            else:
                self.supports.append(tuple(index[(level - 1, x + dx, y + dy)]
                                           for dy in (0, 1) for dx in (0, 1)))
        self.above = [tuple(j for j in range(self.nb_spots) if i in self.supports[j])
                      for i in range(self.nb_spots)]
        squares = []
        for level in range(size - 1):
            width = size - level
            for y in range(width - 1):
                for x in range(width - 1):
                    squares.append(tuple(index[(level, x + dx, y + dy)] for dy in (0, 1) for dx in (0, 1)))
        self.squares_by_spot = [tuple(sq for sq in squares if i in sq) for i in range(self.nb_spots)]


@lru_cache(maxsize=None)
def pyramide(size: int) -> Pyramide:
    return Pyramide(size)


# --------------------------------------------------------------------------- #
# Règles
# --------------------------------------------------------------------------- #

def is_free(geo: Pyramide, board, i: int) -> bool:
    """La bille en ``i`` existe et rien ne repose sur elle."""
    return board[i] != EMPTY and all(board[j] == EMPTY for j in geo.above[i])


def can_receive(geo: Pyramide, board, i: int) -> bool:
    """L'emplacement ``i`` est vide et soutenu."""
    return board[i] == EMPTY and all(board[j] != EMPTY for j in geo.supports[i])


def reserve(geo: Pyramide, board, player: str) -> int:
    """Billes de ``player`` encore dans sa réserve."""
    return geo.per_player - sum(1 for slot in board if slot == player)


def forms_square(geo: Pyramide, board, i: int) -> bool:
    """La bille en ``i`` appartient-elle à un carré de sa couleur ?"""
    player = board[i]
    return any(all(board[j] == player for j in square) for square in geo.squares_by_spot[i])


def actions(geo: Pyramide, board, player: str, phase: int) -> list:
    """Actions permises : ``("play", d)``, ``("move", s, d)``, ``("take", s)``, ``("stop",)``."""
    free_own = [i for i in range(geo.nb_spots) if board[i] == player and is_free(geo, board, i)]
    if phase != PLAY:
        result = [("take", i) for i in free_own]
        if phase == TAKE_MORE:
            result.append(("stop",))
        return result
    dests = [i for i in range(geo.nb_spots) if can_receive(geo, board, i)]
    result = [("play", d) for d in dests] if reserve(geo, board, player) > 0 else []
    for s in free_own:
        for d in dests:
            if geo.level[d] > geo.level[s] and s not in geo.supports[d]:
                result.append(("move", s, d))
    return result


def apply_action(geo: Pyramide, board, player: str, phase: int, action: tuple):
    """Nouvel état ``(plateau, joueur, phase)`` après ``action`` (supposée permise)."""
    board = list(board)
    kind = action[0]
    if kind in ("play", "move"):
        if kind == "move":
            board[action[1]] = EMPTY
        dest = action[-1]
        board[dest] = player
        if forms_square(geo, board, dest):
            return board, player, TAKE
    elif kind == "take":
        board[action[1]] = EMPTY
        if phase == TAKE:
            return board, player, TAKE_MORE
    return board, other_player(player), PLAY


# --------------------------------------------------------------------------- #
# Le jeu
# --------------------------------------------------------------------------- #

class Pylos:
    def __init__(self, size: int = 3):
        self.geo = pyramide(size)
        self.size = size
        self.nb_turn = 0
        self.player = "X"
        self.phase = PLAY
        self.win = ""
        self.board = []
        self.past = []
        self.start_player = "X"
        self.init(self.start_player)

    # Initialisation
    def init(self, start_player: str = "R"):  # Pattern Name
        self.start_player = start_player
        self.nb_turn = 0
        self.player = random.choice("XO") if start_player == "R" else start_player
        self.phase = PLAY
        self.win = ""
        self.board = [EMPTY] * self.geo.nb_spots
        self.past.clear()
        return self.board.copy()

    # Fonctions de jeu
    def play(self, dest):  # Pattern Name
        """Pose une bille de la réserve en ``dest``."""
        return self._act(("play", dest))

    def move(self, src, dest):  # Pattern Name
        """Monte la bille ``src`` en ``dest``."""
        return self._act(("move", src, dest))

    def take(self, cell):  # Pattern Name
        """Reprend la bille ``cell`` (après un carré)."""
        return self._act(("take", cell))

    def stop(self):  # Pattern Name
        """Ne reprend pas de deuxième bille."""
        return self._act(("stop",))

    def get_game_state(self):  # Pattern Name
        if self.win:
            self.init(self.start_player)
        return self.board.copy()

    def get_turn(self):  # Pattern Name
        return self.player

    def get_phase(self):  # Pattern Name
        return self.phase

    def get_reserve(self, player):  # Pattern Name
        return reserve(self.geo, self.board, player)

    def get_moves(self):
        return actions(self.geo, self.board, self.player, self.phase)

    def print(self):  # Pattern Name
        start = 0
        for level in range(self.size):
            width = self.size - level
            print(f"Étage {level} (réserve X : {self.get_reserve('X')}, O : {self.get_reserve('O')})"
                  if level == 0 else f"Étage {level}")
            for y in range(width):
                cells = []
                for x in range(width):
                    i = start + y * width + x
                    cells.append(self.board[i] if self.board[i] != EMPTY else str(i))
                print("  " * level + " ".join(f"{c:>3}" for c in cells))
            start += width * width
        if self.phase == PLAY:
            print("Poser : « 4 ». Monter : « 2 9 » (de 2 vers 9).")
        else:
            print("Reprendre une bille : « r 5 »." + (" S'arrêter : « s »." if self.phase == TAKE_MORE else ""))

    def play_text(self, text: str):
        """Joue une action tapée par un humain : ``4``, ``2 9`` (monter), ``r 5`` (reprendre), ``s``."""
        words = text.lower().split()
        if words == ["s"]:
            return self.stop()
        if len(words) == 2 and words[0] == "r" and words[1].isdigit():
            return self.take(int(words[1]))
        if all(w.isdigit() for w in words):
            if len(words) == 1:
                return self.take(int(words[0])) if self.phase != PLAY else self.play(int(words[0]))
            if len(words) == 2:
                return self.move(int(words[0]), int(words[1]))
        return False

    # Fonctions d'administration
    def back(self):  # Pattern Name
        if self.past:
            self.board, self.player, self.phase, self.nb_turn = self.past.pop()
            self.win = ""
        return self.board.copy()

    # Outils internes
    def _act(self, action: tuple):
        """Renvoie ``False`` si l'action est invalide, ``True`` si la partie est
        terminée, sinon une copie du plateau."""
        if self.win or any(type(arg) is not int for arg in action[1:]):
            return False
        if action not in actions(self.geo, self.board, self.player, self.phase):
            return False
        self.past.append((self.board.copy(), self.player, self.phase, self.nb_turn))
        player = self.player
        self.board, self.player, self.phase = apply_action(self.geo, self.board, self.player, self.phase, action)
        if self.player != player:
            self.nb_turn += 1
            if not actions(self.geo, self.board, self.player, self.phase):
                self.win = player
                return True
        return self.board.copy()
