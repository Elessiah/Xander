"""Le compte est bon, version courte (jeu à un joueur, sur des nombres).

On dispose de 4 nombres (de 1 à 10) et d'une cible (de 11 à 100). Un coup
combine deux nombres disponibles avec une opération : ``play(i, j, op)``
calcule ``nombres[i] op nombres[j]``, met le résultat à la place ``i`` et vide
la place ``j``. Les opérations sont codées par un petit entier :

    0 : addition       1 : soustraction (résultat > 0)
    2 : multiplication 3 : division (seulement si elle tombe juste)

Les résultats sont donc toujours entiers et positifs : une place vide vaut
``0``, qui n'est jamais un nombre.

**État observable** (``get_game_state``) : une liste plate de 5 entiers, les
4 places (``0`` si vide) puis la cible. Les places ne bougent pas : un nombre
reste à sa place tant qu'il n'est pas combiné.

**Fin.** Gagnée dès que la cible apparaît parmi les nombres (``play`` renvoie
``True``). Perdue quand il ne reste qu'un nombre et que ce n'est pas la cible
(``play`` renvoie ``False``, comme Partition et Jumper ; le coup est joué).
Avec deux nombres ou plus, un coup est toujours possible (l'addition) : la
partie ne peut pas se bloquer avant. Elle dure donc au plus 3 coups.

**Coup refusé** (partie finie, indice hors du plateau ou vide, ``i == j``,
opération inconnue, soustraction qui ne donne pas un résultat positif,
division qui ne tombe pas juste, argument qui n'est pas un entier) : rien ne
change et ``play`` renvoie ``False``, comme au Morpion. Un refus se distingue
d'une fin perdue parce que l'état n'a pas changé.

**Tirage.** ``CompteEstBon(graine)`` rend la suite des tirages
reproductible ; chaque ``init`` tire le suivant (le constructeur tire le
premier, comme Partition). La cible est choisie parmi les valeurs que l'on
peut atteindre avec les nombres tirés : **tout tirage est soluble**. Si
aucune valeur de 11 à 100 n'est atteignable (``1, 1, 1, 1``), on retire les
nombres.
"""

import random

NB_NOMBRES = 4
PLUS_PETIT, PLUS_GRAND = 1, 10              # nombres tirés
CIBLE_MIN, CIBLE_MAX = 11, 100              # cible tirée
VIDE = 0
ADDITION, SOUSTRACTION, MULTIPLICATION, DIVISION = range(4)
OPERATIONS = (ADDITION, SOUSTRACTION, MULTIPLICATION, DIVISION)
SYMBOLES = {ADDITION: "+", SOUSTRACTION: "-", MULTIPLICATION: "x", DIVISION: "/"}


def _entier(valeur) -> bool:
    return type(valeur) is int  # un booléen n'est pas un coup


def calculer(a: int, b: int, op: int):
    """``a op b``, ou ``None`` si le résultat n'est pas un entier positif."""
    if op == ADDITION:
        return a + b
    if op == SOUSTRACTION:
        return a - b if a > b else None
    if op == MULTIPLICATION:
        return a * b
    if op == DIVISION:
        return a // b if b and a % b == 0 else None
    return None


def coups_permis(etat: list) -> list:
    """Les coups ``(i, j, op)`` permis dans ``etat`` (places, puis cible), dans l'ordre."""
    nombres = etat[:NB_NOMBRES]
    if etat[NB_NOMBRES] in nombres or sum(n != VIDE for n in nombres) < 2:
        return []
    coups = []
    for i, a in enumerate(nombres):
        for j, b in enumerate(nombres):
            if i == j or a == VIDE or b == VIDE:
                continue
            coups += [(i, j, op) for op in OPERATIONS if calculer(a, b, op) is not None]
    return coups


def jouer(etat: list, i: int, j: int, op: int) -> list:
    """L'état après le coup ``(i, j, op)``, supposé permis."""
    apres = list(etat)
    apres[i] = calculer(etat[i], etat[j], op)
    apres[j] = VIDE
    return apres


def atteignables(nombres) -> set:
    """Toutes les valeurs que l'on peut faire apparaître avec ``nombres`` (eux compris)."""
    vues, valeurs = set(), set()

    def explorer(multiensemble):
        if multiensemble in vues:
            return
        vues.add(multiensemble)
        valeurs.update(multiensemble)
        for i in range(len(multiensemble)):
            for j in range(len(multiensemble)):
                if i == j:
                    continue
                for op in OPERATIONS:
                    r = calculer(multiensemble[i], multiensemble[j], op)
                    if r is not None:
                        reste = [n for k, n in enumerate(multiensemble) if k not in (i, j)]
                        explorer(tuple(sorted(reste + [r])))

    explorer(tuple(sorted(nombres)))
    return valeurs


class CompteEstBon:
    def __init__(self, graine=None):
        self.random = random.Random(graine)
        self.etat = []
        self.passe = []
        self.finie = False
        self.gagnee = False
        self.init()

    def _tirer(self) -> list:
        while True:
            nombres = [self.random.randint(PLUS_PETIT, PLUS_GRAND) for _ in range(NB_NOMBRES)]
            cibles = sorted(v for v in atteignables(nombres)
                            if CIBLE_MIN <= v <= CIBLE_MAX and v not in nombres)
            if cibles:
                return nombres + [self.random.choice(cibles)]

    def init(self):  # Pattern Name
        """Nouvelle partie : tire les nombres et la cible suivants. Renvoie l'état."""
        self.etat = self._tirer()
        self.passe = []
        self.finie = False
        self.gagnee = False
        return list(self.etat)

    def get_game_state(self):  # Pattern Name
        """Les 4 places (``0`` si vide) puis la cible. Ne relance pas une partie finie."""
        return list(self.etat)

    def get_moves(self):
        return coups_permis(self.etat)

    def play(self, i=None, j=None, op=None):  # Pattern Name
        """Combine ``nombres[i]`` et ``nombres[j]`` par ``op`` (voir le module).

        Renvoie l'état, ``True`` si la cible est atteinte, ``False`` si la
        partie est perdue (il ne reste qu'un nombre) ou si le coup est refusé
        (alors rien ne change).
        """
        if self.finie or not all(_entier(x) for x in (i, j, op)):
            return False
        if (i, j, op) not in coups_permis(self.etat):
            return False
        self.passe.append(list(self.etat))
        self.etat = jouer(self.etat, i, j, op)
        nombres = self.etat[:NB_NOMBRES]
        if self.etat[NB_NOMBRES] in nombres:
            self.finie = self.gagnee = True
            return True
        if sum(n != VIDE for n in nombres) == 1:
            self.finie = True
            return False
        return list(self.etat)

    def back(self):  # Pattern Name
        """Annule le dernier coup et renvoie l'état."""
        if self.passe:
            self.etat = self.passe.pop()
            self.finie = self.gagnee = False
        return list(self.etat)

    def print(self):  # Pattern Name
        nombres = "  ".join(str(n) if n != VIDE else "." for n in self.etat[:NB_NOMBRES])
        print(f"Nombres : {nombres}    Cible : {self.etat[NB_NOMBRES]}")
        if self.finie:
            print("Le compte est bon !" if self.gagnee else "Perdu.")

    # Fonctions d'administration
    def set_game_state(self, etat):
        """Impose un état (4 places puis la cible)."""
        self.etat = list(etat)
        self.passe = []
        self.gagnee = self.etat[NB_NOMBRES] in self.etat[:NB_NOMBRES]
        self.finie = self.gagnee or sum(n != VIDE for n in self.etat[:NB_NOMBRES]) <= 1
