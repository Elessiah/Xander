"""Partition : un musicien lit une partition qui défile (jeu à un joueur).

La partition montre les 8 prochains temps : ``o`` une note, ``.`` un silence.
À chaque ``play`` le premier temps est joué, puis la partition avance d'un
temps et un nouveau temps apparaît au bout. ``play(True)`` frappe, ``play(False)``
se tait. Frapper sur un silence ou se taire sur une note termine la partie
(``play`` renvoie ``False``).

Plus simple que Jumper : aucun état caché (tout ce qui compte est visible) et
une erreur se paie tout de suite. La suite des temps est fixée par le numéro
du morceau (``Partition(3)`` joue toujours le même morceau).
"""

import random

LONGUEUR = 8
NOTE, SILENCE = "o", "."


class Partition:
    def __init__(self, morceau=None):
        self.random = random.Random(morceau)
        self.temps = []
        self.joues = 0
        self.passe = []
        self.finie = False
        self.init()

    def _suivant(self):
        return NOTE if self.random.random() < 0.4 else SILENCE

    def init(self):  # Pattern Name
        self.temps = [self._suivant() for _ in range(LONGUEUR)]
        self.joues = 0
        self.passe = []
        self.finie = False
        return list(self.temps)

    def get_partition(self):  # Pattern Name
        return list(self.temps)

    def play(self, frappe=False):  # Pattern Name
        """Joue le premier temps. Renvoie la partition, ou ``False`` si c'était faux."""
        if self.finie:
            return False
        self.passe.append((list(self.temps), self.joues, self.random.getstate()))
        juste = (self.temps[0] == NOTE) == bool(frappe)
        self.joues += 1
        self.temps = self.temps[1:] + [self._suivant()]
        if not juste:
            self.finie = True
            return False
        return list(self.temps)

    def back(self):  # Pattern Name
        """Revient au temps précédent et renvoie la partition."""
        if self.passe:
            temps, self.joues, etat = self.passe.pop()
            self.temps = temps
            self.random.setstate(etat)
            self.finie = False
        return list(self.temps)
