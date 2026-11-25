"""Jeu d'essai pour les expériences de la mère : un Morpion dont les pions sont des chiffres.

Une case libre affiche son indice (le nombre ``0`` … ``8``), les joueurs posent
``"1"`` et ``"2"`` et ``play(i)`` joue la case d'indice ``i``. (Si les cases
libres affichaient le texte ``"1"``, le joueur ``"1"`` qui la joue ne
changerait rien de visible, et le labo croirait le coup refusé.) Dans l'exemple,
« la case d'indice i » et « les cases qui valent i » disent la même chose. Mais
dès qu'un pion ``"2"`` est posé, jouer la case libre 2 les départage : une
seule case change, pas toutes celles qui valent 2.
"""

LIGNES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
PIONS = ("1", "2")


class MorpionChiffres:
    def __init__(self):
        self.init("1")

    def init(self, joueur: str = "1"):
        self.cases = [None] * 9
        self.joueur = joueur
        self.passe = []
        self.fini = False
        return self.get_game_state()

    def get_game_state(self):
        return [c if c is not None else i for i, c in enumerate(self.cases)]

    def play(self, i):
        if self.fini or type(i) is not int or not 0 <= i < 9 or self.cases[i] is not None:
            return False
        self.passe.append((list(self.cases), self.joueur))
        self.cases[i] = self.joueur
        if any(all(self.cases[c] == self.joueur for c in ligne) for ligne in LIGNES) or None not in self.cases:
            self.fini = True
            return True
        self.joueur = PIONS[1] if self.joueur == PIONS[0] else PIONS[0]
        return self.get_game_state()

    def back(self):
        if self.passe:
            self.cases, self.joueur = self.passe.pop()
            self.fini = False
        return self.get_game_state()
