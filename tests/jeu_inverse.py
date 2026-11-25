"""Jeu d'essai : un Puissance 4 dont les jetons « tombent » vers le haut.

``play(c)`` remplit la colonne ``c`` de haut en bas : la case 35 + c, puis
28 + c… La file part de *c* + 35 et descend de 7 : la mère ne peut pas la
calculer avec un décalage et un pas en 5 nœuds, mais elle la voit en rejouant
l'action dans son labo.
"""

from Games.Coords import Coords
from Games.Puissance4 import EMPTY, Puissance4


class Puissance4Inverse(Puissance4):
    def set_token(self, column: int):
        coords = Coords(width=self.width)
        for y in reversed(range(self.height)):
            coords.set(x=column, y=y)
            if self.board[coords.i] == EMPTY:
                self.past.append((self.board.copy(), self.player, self.nb_turn))
                self.board[coords.i] = self.player
                self.nb_turn += 1
                return coords
        return None
