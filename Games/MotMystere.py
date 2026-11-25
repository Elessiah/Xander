"""Mot mystère : trouver un mot secret de 5 lettres en 6 essais (jeu à un joueur).

Le jeu tire un mot secret dans son dictionnaire (``Games/mots_mystere.txt`` :
405 mots français courants de 5 lettres, sans accents, en minuscules). Le
joueur propose un mot du dictionnaire (``play("arbre")``) ; le jeu répond,
pour chaque lettre de la proposition :

* ``=`` la lettre est **bien placée** (le secret a la même lettre au même endroit) ;
* ``~`` la lettre est **présente ailleurs** dans le secret ;
* ``-`` la lettre est **absente** (ou déjà toute comptée, voir plus bas).

**Lettres répétées.** Le secret ne « prête » chacune de ses lettres qu'une
fois. On marque d'abord les lettres bien placées ; puis, de gauche à droite,
une lettre mal placée reçoit ``~`` seulement s'il reste dans le secret un
exemplaire de cette lettre qui n'a pas encore servi (ni à un ``=``, ni à un
``~`` plus à gauche) ; sinon elle reçoit ``-``. Exemples avec le secret
``arbre`` : ``terre`` donne ``--~==`` (le ``r`` bien placé consomme un des
deux ``r`` du secret, le ``r`` mal placé prend l'autre ; le ``e`` du secret
sert au ``e`` bien placé, l'autre ``e`` est absent) ; avec le
secret ``livre``, ``terre`` donne ``---==`` : le seul ``r`` du secret sert
déjà au ``r`` bien placé, l'autre ``r`` de ``terre`` est donc absent.

La partie est **gagnée** quand le mot est trouvé, **perdue** après 6 essais
sans le trouver. ``MotMystere(graine)`` tire toujours la même suite de secrets.

**L'état observable** (``get_game_state``) ne contient jamais le secret : c'est
l'historique des propositions, à plat, en 60 cases. Chaque essai occupe 10
cases (une paire *lettre, réponse* par lettre) : la case ``10 * essai + 2 * i``
est la ``i``-ième lettre proposée, la case suivante sa réponse. Les essais pas
encore joués sont des cases vides (``.``).
"""

from __future__ import annotations

import random
from pathlib import Path

LONGUEUR = 5                  # lettres d'un mot
ESSAIS = 6                    # essais avant de perdre
BIEN, AILLEURS, ABSENTE = "=", "~", "-"
VIDE = "."                    # case d'un essai pas encore joué
TAILLE = ESSAIS * LONGUEUR * 2  # cases de l'état
JOUEUR = "joueur"             # le seul joueur
PERSONNE = "personne"         # valeur de ``win`` quand la partie est perdue

FICHIER_MOTS = Path(__file__).with_name("mots_mystere.txt")


def charger_mots(fichier: Path = FICHIER_MOTS) -> tuple[str, ...]:
    """Le dictionnaire : un mot par ligne, dans l'ordre alphabétique."""
    return tuple(sorted(set(fichier.read_text(encoding="utf-8").split())))


MOTS = charger_mots()


def reponse(proposition: str, secret: str) -> str:
    """La réponse du jeu à ``proposition`` quand le mot secret est ``secret`` (voir le module
    pour les lettres répétées) : une chaîne de 5 symboles parmi ``=``, ``~`` et ``-``."""
    marques = [ABSENTE] * len(proposition)
    restantes: dict[str, int] = {}  # lettres du secret qui n'ont pas encore servi
    for i, (lettre, cachee) in enumerate(zip(proposition, secret)):
        if lettre == cachee:
            marques[i] = BIEN
        else:
            restantes[cachee] = restantes.get(cachee, 0) + 1
    for i, lettre in enumerate(proposition):
        if marques[i] != BIEN and restantes.get(lettre, 0) > 0:
            marques[i] = AILLEURS
            restantes[lettre] -= 1
    return "".join(marques)


def essais(etat: list) -> list[tuple[str, str]]:
    """Relit un état : la liste des essais joués, ``(mot proposé, réponse)``."""
    joues = []
    pas = LONGUEUR * 2
    for debut in range(0, len(etat), pas):
        ligne = etat[debut:debut + pas]
        if ligne[0] == VIDE:
            break
        joues.append(("".join(ligne[0::2]), "".join(ligne[1::2])))
    return joues


class MotMystere:
    def __init__(self, graine=None):
        self.random = random.Random(graine)
        self.mots = MOTS
        self._permis = frozenset(MOTS)
        self.secret = ""
        self.propositions: list[str] = []
        self.reponses: list[str] = []
        self.win = ""
        self.init()

    def init(self):  # Pattern Name
        """Nouvelle partie avec le secret suivant de la graine ; renvoie l'état (vide)."""
        self._nouvelle(self.random.choice(self.mots))
        return self._etat()

    def get_game_state(self):  # Pattern Name
        """L'historique à plat (60 cases, voir le module). Si la partie est finie, en recommence
        une avec un nouveau secret, comme les autres jeux du dépôt."""
        if self.win:
            self.init()
        return self._etat()

    def get_turn(self):  # Pattern Name
        """Toujours le même joueur."""
        return JOUEUR

    def get_moves(self):  # Pattern Name
        """Les mots permis (tout le dictionnaire, à chaque essai)."""
        return list(self.mots)

    def play(self, mot):  # Pattern Name
        """Propose ``mot``.

        Renvoie ``False`` si le coup est refusé (partie finie, pas une chaîne, mauvaise longueur
        ou mot hors du dictionnaire : rien ne change), ``True`` si la partie est finie (``win``
        dit si elle est gagnée), sinon le nouvel état.
        """
        if self.win or type(mot) is not str or len(mot) != LONGUEUR or mot not in self._permis:
            return False
        self.propositions.append(mot)
        self.reponses.append(reponse(mot, self.secret))
        if mot == self.secret:
            self.win = JOUEUR
            return True
        if len(self.propositions) == ESSAIS:
            self.win = PERSONNE
            return True
        return self._etat()

    def back(self):  # Pattern Name
        """Annule la dernière proposition et renvoie l'état."""
        if self.propositions:
            self.propositions.pop()
            self.reponses.pop()
            self.win = ""
        return self._etat()

    def print(self):  # Pattern Name
        for mot, marques in zip(self.propositions, self.reponses):
            print(f"{' '.join(mot.upper())}   {' '.join(marques)}")
        for _ in range(ESSAIS - len(self.propositions)):
            print(" ".join(VIDE * LONGUEUR))
        if self.win == JOUEUR:
            print(f"Trouvé en {len(self.propositions)} essai(s).")
        elif self.win == PERSONNE:
            print(f"Perdu : le mot était {self.secret!r}.")

    # Fonctions d'administration
    def set_secret(self, mot):
        """Nouvelle partie avec ce secret (pour les tests) ; ``mot`` doit être un mot permis."""
        if mot not in self._permis:
            raise ValueError(f"{mot!r} n'est pas dans le dictionnaire")
        self._nouvelle(mot)
        return self._etat()

    # Outils internes
    def _nouvelle(self, secret):
        self.secret = secret
        self.propositions, self.reponses = [], []
        self.win = ""

    def _etat(self):
        """L'état, sans relancer de partie (``back`` peut revenir d'une fin)."""
        etat = []
        for mot, marques in zip(self.propositions, self.reponses):
            for lettre, marque in zip(mot, marques):
                etat += [lettre, marque]
        return etat + [VIDE] * (TAILLE - len(etat))
