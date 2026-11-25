"""Mastermind avec des chiffres (jeu à un joueur, information cachée).

Le jeu tire un code secret de ``LONGUEUR`` chiffres (3), chacun de 1 à
``CHIFFRES`` (6), répétitions permises : 6³ = 216 codes possibles. Le joueur
propose un code, un chiffre par argument : ``play(1, 2, 3)``. Le jeu répond
par deux nombres :

- **bien placés** : les chiffres justes à la bonne place ;
- **mal placés** : les chiffres justes à la mauvaise place (chaque chiffre du
  secret ne compte qu'une fois).

La partie est gagnée quand les trois chiffres sont bien placés, perdue après
``ESSAIS`` (8) propositions sans trouver.

**L'état observable** ne contient jamais le secret. C'est le plateau du
Mastermind : ``ESSAIS`` rangées de ``LONGUEUR + 2`` trous (les chiffres
proposés, puis les bien placés, puis les mal placés), soit une liste de
8 × 5 = 40 cases, rangée après rangée. Une case encore vide vaut ``" "`` ;
la proposition ``k`` (à partir de 0) remplit la rangée ``k``.

Le seul joueur est ``"X"`` (``get_turn`` le renvoie toujours). Après une
partie gagnée, ``win`` vaut ``"X"`` ; après une partie perdue, ``"O"`` : le
codeur, qui a choisi le secret et ne joue jamais.

``Mastermind(graine)`` rend les secrets reproductibles (``Mastermind(0)``
tire toujours la même suite de secrets, et sa première partie a toujours le
secret ``441``), ce qui est nécessaire pour qu'un exemple de partie se
rejoue à l'identique.

Professeur : :mod:`Games.MinmaxMastermind`. Pour jouer :
``python -m Games.Mastermind``.
"""

import itertools
import random
from collections import Counter

LONGUEUR = 3   # chiffres dans un code
CHIFFRES = 6   # chiffres de 1 à 6
ESSAIS = 8     # propositions permises
VIDE = " "
LARGEUR = LONGUEUR + 2  # une rangée : les chiffres, bien placés, mal placés


def reponse(secret, proposition) -> tuple:
    """``(bien placés, mal placés)`` de ``proposition`` face à ``secret``."""
    bien = sum(s == p for s, p in zip(secret, proposition))
    communs = sum((Counter(secret) & Counter(proposition)).values())
    return bien, communs - bien


def tous_les_codes(longueur: int = LONGUEUR, chiffres: int = CHIFFRES) -> list:
    """Tous les codes, dans l'ordre : ``(1, 1, 1)``, ``(1, 1, 2)``…"""
    return list(itertools.product(range(1, chiffres + 1), repeat=longueur))


def historique(plateau, longueur: int = LONGUEUR) -> list:
    """Les propositions déjà jouées sur ``plateau`` : ``[(code, (bien, mal)), …]``."""
    largeur = longueur + 2
    coups = []
    for debut in range(0, len(plateau), largeur):
        rangee = plateau[debut:debut + largeur]
        if rangee[0] == VIDE:
            break
        coups.append((tuple(rangee[:longueur]), (rangee[longueur], rangee[longueur + 1])))
    return coups


class Mastermind:
    def __init__(self, seed=None):
        self.random = random.Random(seed)
        self.longueur = LONGUEUR
        self.chiffres = CHIFFRES
        self.essais = ESSAIS
        self.secret = ()
        self.entamee = False  # une proposition a été faite face à ce secret
        self.board = []
        self.nb_turn = 0
        self.win = ""
        self.init()

    # Initialisation
    def init(self, start_player="X"):  # Pattern Name
        """Nouvelle partie. ``start_player`` est ignoré (un seul joueur).

        Un nouveau secret est tiré si le précédent a déjà servi : une partie
        que personne n'a commencée garde le sien. Ainsi ``Mastermind(0)`` suivi
        de ``init()`` joue toujours le même premier secret.
        """
        if self.entamee or not self.secret:
            self.secret = tuple(self.random.randint(1, self.chiffres) for _ in range(self.longueur))
            self.entamee = False
        self.board = [VIDE] * (self.essais * (self.longueur + 2))
        self.nb_turn = 0
        self.win = ""
        return self.board.copy()

    # Fonctions de jeu
    def play(self, *chiffres):  # Pattern Name
        """Propose un code, un chiffre par argument : ``play(1, 2, 3)``.

        Renvoie ``False`` si la proposition est invalide (partie finie, mauvais
        nombre de chiffres, chiffre hors de 1 à 6, argument qui n'est pas un
        entier), ``True`` si la partie est terminée (gagnée ou perdue), sinon
        le plateau.
        """
        if self.win or len(chiffres) != self.longueur:
            return False
        if any(type(c) is not int or not 1 <= c <= self.chiffres for c in chiffres):
            return False
        bien, mal = reponse(self.secret, chiffres)
        self.entamee = True
        debut = self.nb_turn * (self.longueur + 2)
        self.board[debut:debut + self.longueur + 2] = [*chiffres, bien, mal]
        self.nb_turn += 1
        if bien == self.longueur:
            self.win = "X"
        elif self.nb_turn == self.essais:
            self.win = "O"
        return True if self.win else self.board.copy()

    def get_turn(self):  # Pattern Name
        return "X"

    def get_game_state(self):  # Pattern Name
        """Renvoie le plateau. Si la partie précédente est finie, en recommence une."""
        if self.win:
            self.init()
        return self.board.copy()

    def get_moves(self):
        """Propositions permises (toutes, tant que la partie n'est pas finie)."""
        return [] if self.win else tous_les_codes(self.longueur, self.chiffres)

    def print(self):  # Pattern Name
        largeur = self.longueur + 2
        print(f"Code de {self.longueur} chiffres de 1 à {self.chiffres}, {self.essais} essais.")
        for k in range(self.essais):
            rangee = self.board[k * largeur:(k + 1) * largeur]
            if rangee[0] == VIDE:
                print(f"{k + 1:>2}. " + " ".join("." * self.longueur))
            else:
                code = " ".join(str(c) for c in rangee[:self.longueur])
                print(f"{k + 1:>2}. {code}   bien placés : {rangee[-2]}, mal placés : {rangee[-1]}")

    def play_text(self, text: str):
        """Joue une proposition tapée par un humain : ``"123"`` ou ``"1 2 3"``."""
        chiffres = text.replace(" ", "")
        if not chiffres.isdigit():
            return False
        return self.play(*(int(c) for c in chiffres))

    # Fonctions d'administration
    def set_secret(self, *secret):
        """Nouvelle partie avec le secret imposé (pour les tests et le professeur)."""
        self.init()
        self.secret = tuple(secret)
        self.entamee = False

    def back(self):  # Pattern Name
        """Annule la dernière proposition (le secret ne change pas) et renvoie le plateau."""
        if self.nb_turn:
            self.nb_turn -= 1
            debut = self.nb_turn * (self.longueur + 2)
            self.board[debut:debut + self.longueur + 2] = [VIDE] * (self.longueur + 2)
            self.win = ""
        return self.board.copy()


def main():
    game = Mastermind()
    print("Trouvez le code secret. Tapez par exemple « 123 », ou « q » pour quitter.")
    while True:
        game.print()
        answer = input("Proposition ? ").strip().lower()
        if answer == "q":
            return
        result = game.play_text(answer)
        if result is False:
            print("Proposition invalide.")
        elif result is True:
            game.print()
            if game.win == "X":
                print(f"Gagné en {game.nb_turn} essai(s) !")
            else:
                print(f"Perdu : le code était {''.join(map(str, game.secret))}.")
            game.get_game_state()
            print("\nNouvelle partie.")


if __name__ == "__main__":
    main()
