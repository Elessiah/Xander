"""Jeu des allumettes (variante « misère » du jeu de Nim).

À tour de rôle, chaque joueur retire 1, 2 ou 3 allumettes. Celui qui doit
prendre la dernière allumette perd : laisser exactement 1 allumette à
l'adversaire fait gagner.
"""

import random

MIN_TAKE, MAX_TAKE = 1, 3


def other_player(player: str) -> str:
    return "O" if player == "X" else "X"


class Allumettes:
    def __init__(self):
        self.nb_turn = 0
        self.win = ""
        self.player = "X"
        self.start_nb_allumettes = 50
        self.nb_allumettes = self.start_nb_allumettes
        self.past = []  # (allumettes, joueur, nb_turn) avant chaque coup, pour back()
        self.start_player = "X"

    # Initialisation
    def set_max_nb_allumettes(self, allumettes):
        """Nombre d'allumettes au début de chaque partie."""
        self.start_nb_allumettes = allumettes

    def init(self, start_player="R"):  # Pattern Name
        """Nouvelle partie. ``start_player`` : ``"X"``, ``"O"`` ou ``"R"`` (aléatoire)."""
        self.start_player = start_player
        self.nb_allumettes = self.start_nb_allumettes
        self.past.clear()
        self.nb_turn = 0
        self.win = ""
        self.player = random.choice("XO") if start_player == "R" else start_player
        return self.nb_allumettes

    # Fonctions de jeu
    def play(self, quantity):  # Pattern Name
        """Retire ``quantity`` allumettes.

        Renvoie ``False`` si le coup est invalide, ``True`` si la partie est
        terminée, sinon le nombre d'allumettes restantes.
        """
        if self.win or type(quantity) is not int or not MIN_TAKE <= quantity <= MAX_TAKE:
            return False
        if quantity > self.nb_allumettes:
            return False
        self.past.append((self.nb_allumettes, self.player, self.nb_turn))
        self.nb_allumettes -= quantity
        self.nb_turn += 1
        self.check_win()
        if self.win:
            return True
        self.player = other_player(self.player)
        return self.nb_allumettes

    def get_turn(self):  # Pattern Name
        return self.player

    def get_game_state(self):  # Pattern Name
        """Renvoie le nombre d'allumettes. Si la partie précédente est finie, en recommence une."""
        if self.win:
            self.init(self.start_player)
        return self.nb_allumettes

    def print(self):  # Pattern Name
        print(f"{self.nb_allumettes} allumette(s)")
        print(". " * self.nb_allumettes)
        print("| " * self.nb_allumettes)

    # Fonctions d'administration
    def set_game_state(self, allumettes, player):
        """Impose une position : ``allumettes`` restantes, ``player`` doit jouer."""
        self.nb_allumettes = allumettes
        self.player = player
        self.past.clear()
        self.nb_turn = 0
        self.win = ""

    def back(self):  # Pattern Name
        """Annule le dernier coup et renvoie le nombre d'allumettes."""
        if self.past:
            self.nb_allumettes, self.player, self.nb_turn = self.past.pop()
            self.win = ""
        return self.nb_allumettes

    # Outils internes
    def next_player(self):
        self.player = other_player(self.player)

    def check_win(self):
        """Met à jour ``win`` après le coup de ``player``."""
        if self.nb_allumettes == 1:
            self.win = self.player                # l'adversaire doit prendre la dernière
        elif self.nb_allumettes < 1:
            self.win = other_player(self.player)  # le joueur a pris la dernière
