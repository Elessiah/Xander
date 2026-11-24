"""Coordonnées sur une grille stockée à plat dans une liste (``i = y * width + x``)."""


class Coords:
    def __init__(self, x=0, y=0, i=None, width=3):
        self.width = width
        self.x = x
        self.y = y
        self.i = 0
        if i is not None:
            self.set(i=i)
        else:
            self.set(x=x, y=y)

    def set(self, x=None, y=None, i=None):
        """Met à jour la position par indice ``i``, ou par ``x`` et/ou ``y``."""
        if i is not None:
            self.i = i
            self.x, self.y = i % self.width, i // self.width
        else:
            if x is not None:
                self.x = x
            if y is not None:
                self.y = y
            self.i = self.y * self.width + self.x

    def __str__(self):
        return f"x: {self.x}, y: {self.y}, index: {self.i}, width: {self.width}"

    def copy(self):
        return Coords(self.x, self.y, width=self.width)
