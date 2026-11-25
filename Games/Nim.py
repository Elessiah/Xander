"""Nim à plusieurs tas (version normale).

Il y a plusieurs tas d'objets (3, 4 et 5 par défaut). À tour de rôle, chaque
joueur choisit **un** tas et y prend autant d'objets qu'il veut, au moins un :
``play(tas, nombre)``. Celui qui prend le dernier objet gagne.

L'état est la liste des tailles des tas : ``[3, 4, 5]``. Un coup refusé (tas
inexistant ou vide, nombre nul ou trop grand, argument qui n'est pas un
entier) ne change rien et ``play`` renvoie ``False``, comme dans les autres
jeux.

Variante misère (celui qui prend le dernier objet perd) :
:mod:`Games.NimMisere`. Professeur : :mod:`Games.MinmaxNim`.
"""

import random

DEFAULT_HEAPS = (3, 4, 5)


def other_player(player: str) -> str:
    return "O" if player == "X" else "X"


def coups(tas) -> list:
    """Toutes les actions permises : ``(tas, nombre)``."""
    return [(i, n) for i, size in enumerate(tas) for n in range(1, size + 1)]


class Nim:
    MISERE = False  # True : celui qui prend le dernier objet perd

    def __init__(self):
        self.start_heaps = list(DEFAULT_HEAPS)
        self.heaps = list(self.start_heaps)
        self.player = "X"
        self.start_player = "X"
        self.nb_turn = 0
        self.win = ""
        self.past = []  # (tas, joueur, nb_turn) avant chaque coup, pour back()

    # Initialisation
    def set_tas(self, *tailles):
        """Tailles des tas au début de chaque partie, par exemple ``set_tas(3, 4, 5)``."""
        if not tailles or any(type(t) is not int or t < 0 for t in tailles):
            raise ValueError("il faut au moins un tas, de taille entière positive ou nulle")
        self.start_heaps = list(tailles)

    def init(self, start_player="R"):  # Pattern Name
        """Nouvelle partie. ``start_player`` : ``"X"``, ``"O"`` ou ``"R"`` (aléatoire)."""
        self.start_player = start_player
        self.heaps = list(self.start_heaps)
        self.past.clear()
        self.nb_turn = 0
        self.win = ""
        self.player = random.choice("XO") if start_player == "R" else start_player
        return self.heaps.copy()

    # Fonctions de jeu
    def play(self, tas, nombre):  # Pattern Name
        """Prend ``nombre`` objets dans le tas ``tas``.

        Renvoie ``False`` si le coup est invalide, ``True`` si la partie est
        terminée, sinon les tas restants.
        """
        if self.win or type(tas) is not int or type(nombre) is not int:
            return False
        if not 0 <= tas < len(self.heaps) or not 1 <= nombre <= self.heaps[tas]:
            return False
        self.past.append((self.heaps.copy(), self.player, self.nb_turn))
        self.heaps[tas] -= nombre
        self.nb_turn += 1
        if not any(self.heaps):
            # Le joueur vient de prendre le dernier objet.
            self.win = other_player(self.player) if self.MISERE else self.player
            return True
        self.player = other_player(self.player)
        return self.heaps.copy()

    def get_turn(self):  # Pattern Name
        return self.player

    def get_game_state(self):  # Pattern Name
        """Renvoie les tas. Si la partie précédente est finie, en recommence une."""
        if self.win:
            self.init(self.start_player)
        return self.heaps.copy()

    def get_moves(self):
        """Actions permises : ``(tas, nombre)``."""
        return [] if self.win else coups(self.heaps)

    def print(self):  # Pattern Name
        for i, size in enumerate(self.heaps):
            print(f"tas {i} : {'| ' * size}({size})")

    def play_text(self, text: str):
        """Joue un coup tapé par un humain : ``"1 3"`` prend 3 objets dans le tas 1."""
        words = text.split()
        if len(words) == 2 and all(w.isdigit() for w in words):
            return self.play(int(words[0]), int(words[1]))
        return False

    # Fonctions d'administration
    def set_game_state(self, tas, player):
        """Impose une position : les tailles ``tas``, ``player`` doit jouer."""
        self.heaps = list(tas)
        self.player = player
        self.past.clear()
        self.nb_turn = 0
        self.win = ""

    def back(self):  # Pattern Name
        """Annule le dernier coup et renvoie les tas."""
        if self.past:
            self.heaps, self.player, self.nb_turn = self.past.pop()
            self.win = ""
        return self.heaps.copy()
