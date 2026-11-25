"""Tours de Hanoï : déplacer une pile de disques d'un piquet à un autre (jeu à un joueur).

Trois piquets (``0``, ``1``, ``2``) et ``nb_disques`` disques de tailles
différentes (3 par défaut). Au départ, tous les disques sont sur le piquet 0,
du plus grand en bas au plus petit en haut. Un coup, ``play(depart, arrivee)``,
prend le disque du dessus du piquet ``depart`` et le pose sur le piquet
``arrivee``. On ne pose jamais un disque sur un plus petit.

**Le but** : tous les disques sur le dernier piquet (le piquet 2). Le minimum
est ``2 ** nb_disques - 1`` coups. **La limite** : au plus le double du
minimum (14 coups pour 3 disques). Le coup qui atteint la limite sans avoir
rangé la pile fait perdre.

**L'état observable** : pour chaque disque, du plus petit au plus grand, le
numéro du piquet où il est. ``[0, 0, 0]`` au départ, ``[2, 2, 2]`` au but.
C'est une liste plate de taille fixe, et toute liste de ``0``, ``1`` et ``2``
est une position possible : l'ordre des disques sur un piquet n'a pas à être
écrit, il est imposé par la règle (le plus petit en haut).
"""

JOUEUR = "J"
NB_PIQUETS = 3


def minimum(nb_disques: int) -> int:
    """Le nombre minimal de coups pour déplacer toute la pile."""
    return 2 ** nb_disques - 1


def limite(nb_disques: int) -> int:
    """Le nombre de coups permis dans une partie : le double du minimum."""
    return 2 * minimum(nb_disques)


def dessus(etat, piquet: int):
    """Le disque du dessus de ``piquet`` (son indice, le plus petit), ou ``None`` s'il est vide."""
    return next((disque for disque, ou in enumerate(etat) if ou == piquet), None)


def permis(etat, depart, arrivee) -> bool:
    """Le coup ``(depart, arrivee)`` respecte-t-il les règles dans ``etat`` ?"""
    piquets = range(NB_PIQUETS)
    if any(type(p) is not int or p not in piquets for p in (depart, arrivee)) or depart == arrivee:
        return False  # un booléen n'est pas un piquet
    disque = dessus(etat, depart)
    if disque is None:
        return False  # piquet vide
    autre = dessus(etat, arrivee)
    return autre is None or autre > disque  # jamais sur un plus petit


def coups_permis(etat) -> list[tuple[int, int]]:
    """Tous les coups permis dans ``etat``, dans l'ordre ``(0, 1), (0, 2), (1, 0)…``."""
    return [(d, a) for d in range(NB_PIQUETS) for a in range(NB_PIQUETS) if permis(etat, d, a)]


def apres(etat, depart: int, arrivee: int) -> list[int]:
    """L'état après le coup (supposé permis)."""
    suivant = list(etat)
    suivant[dessus(etat, depart)] = arrivee
    return suivant


def but(nb_disques: int) -> list[int]:
    return [NB_PIQUETS - 1] * nb_disques


class Hanoi:
    def __init__(self, nb_disques: int = 3):
        if type(nb_disques) is not int or nb_disques < 1:
            raise ValueError(f"nombre de disques invalide : {nb_disques!r}")
        self.nb_disques = nb_disques
        self.disques: list[int] = []
        self.coups = 0
        self.passe: list[tuple] = []  # (disques, coups) avant chaque coup, pour back()
        self.finie = False
        self.win = ""
        self.init()

    # Initialisation
    def set_nb_disques(self, nb_disques: int):
        """Change la taille de la pile ; prend effet à la prochaine partie (``init``)."""
        if type(nb_disques) is not int or nb_disques < 1:
            raise ValueError(f"nombre de disques invalide : {nb_disques!r}")
        self.nb_disques = nb_disques

    def init(self):  # Pattern Name
        """Nouvelle partie : toute la pile sur le piquet 0. Renvoie l'état."""
        self.disques = [0] * self.nb_disques
        self.coups = 0
        self.passe.clear()
        self.finie = False
        self.win = ""
        return list(self.disques)

    # Fonctions de jeu
    def play(self, depart, arrivee):  # Pattern Name
        """Déplace le disque du dessus de ``depart`` vers ``arrivee``.

        Renvoie ``False`` si le coup est refusé (rien ne change), ``True`` si la
        partie est finie (gagnée : ``win`` vaut ``"J"`` ; perdue : ``win`` vaut
        ``""``), sinon le nouvel état.
        """
        if self.finie or not permis(self.disques, depart, arrivee):
            return False
        self.passe.append((list(self.disques), self.coups))
        self.disques = apres(self.disques, depart, arrivee)
        self.coups += 1
        if self.disques == but(self.nb_disques):
            self.finie, self.win = True, JOUEUR
        elif self.coups >= limite(self.nb_disques):
            self.finie = True
        return True if self.finie else list(self.disques)

    def get_game_state(self):  # Pattern Name
        """Renvoie l'état. Si la partie précédente est finie, en recommence une."""
        if self.finie:
            self.init()
        return list(self.disques)

    def get_turn(self):  # Pattern Name
        """Le joueur qui doit jouer : toujours le même, il est seul."""
        return JOUEUR

    def get_moves(self) -> list[tuple[int, int]]:
        """Les coups permis (aucun si la partie est finie)."""
        return [] if self.finie else coups_permis(self.disques)

    def back(self):  # Pattern Name
        """Annule le dernier coup (et la fin qu'il a provoquée) et renvoie l'état."""
        if self.passe:
            self.disques, self.coups = self.passe.pop()
            self.finie, self.win = False, ""
        return list(self.disques)

    def print(self):  # Pattern Name
        print(f"Coup {self.coups} / {limite(self.nb_disques)}")
        for piquet in range(NB_PIQUETS):
            pile = [d + 1 for d in reversed(range(self.nb_disques)) if self.disques[d] == piquet]
            print(f"{piquet} | " + " ".join(map(str, pile)))

    # Fonctions d'administration
    def set_game_state(self, disques, coups: int = 0):
        """Impose une position : ``disques[i]`` est le piquet du disque ``i`` (0 = le plus petit)."""
        if len(disques) != self.nb_disques or any(p not in range(NB_PIQUETS) for p in disques):
            raise ValueError(f"position invalide : {disques!r}")
        self.disques = list(disques)
        self.coups = coups
        self.passe.clear()
        self.finie = False
        self.win = ""
