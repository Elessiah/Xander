"""Jeu d'essai à un joueur dont l'action ne s'explique pas : ``play(k)`` mélange les cases.

Aucun programme (cases changées, valeur, défilement) ne prévoit un mélange au
hasard : la mère doit dire qu'elle ne comprend pas l'action, pas faire semblant.
"""

import random


class Melange:
    def __init__(self):
        self.random = random.Random(0)
        self.cases, self.passe = [], []
        self.init()

    def init(self):
        self.cases = list("abcdefgh")
        self.passe = []
        return list(self.cases)

    def get_game_state(self):
        return list(self.cases)

    def play(self, k):
        if k not in (1, 2, 3):
            return False  # coup refusé : rien ne change
        self.passe.append((list(self.cases), self.random.getstate()))
        self.random.shuffle(self.cases)
        return list(self.cases)

    def back(self):
        if self.passe:
            self.cases, etat = self.passe.pop()
            self.random.setstate(etat)
        return list(self.cases)
