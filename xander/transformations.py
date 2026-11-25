"""La mère comprend un problème « entrée -> sortie » : le plus petit programme qui explique tout.

C'est ce qu'elle fait déjà quand elle décrit l'effet d'une action
(:mod:`xander.effets`), sur un problème d'un autre genre : quelques paires
(une entrée, la sortie attendue) et des questions. Elle énumère par taille
croissante de petits programmes ``sortie = t(x)`` écrits avec ses briques
(:mod:`xander.briques`, l'équipement de naissance) et garde ceux qui
expliquent **toutes** les paires.

Un programme est un arbre :

* la feuille ``x`` (l'entrée) ;
* des **constantes** : ``0``, ``1``, et celles que la mère remarque dans les
  paires (:func:`constantes`) ;
* une brique appliquée à des programmes : ``inverser(x)``,
  ``element(x, 1)``… ;
* ``chaque(f, s)`` et ``garder(p, s)`` reçoivent une **fonction de
  l'élément** ``e`` : un petit programme où la feuille ``e`` désigne l'élément
  (``chaque(plus(e, 1), x)`` : ajouter 1 à chaque élément). La feuille ``e``
  ne compte pas dans la taille ; une fonction fait au plus
  :data:`MAX_TAILLE_FONCTION` nœuds et ne contient ni ``chaque`` ni ``garder``.

**Taille** : le nombre de nœuds (``e`` exclu). La mère cherche jusqu'à
:data:`MAX_TAILLE` ; au-delà, c'est le jalon 2 (chercher sans tout énumérer).

**Programmes confondus.** Comme dans :mod:`xander.effets`, deux programmes
qui donnent les mêmes valeurs sont confondus et on garde le plus petit (ou, à
taille égale, le premier trouvé). Les valeurs comparées sont celles des
entrées des paires **et des questions** : deux programmes qui s'accordent sur
les paires mais pas sur une question restent distincts, puisqu'ils
proposent deux réponses différentes. La mère ne voit que les entrées des
questions, jamais leurs réponses.

**Conclure à partir de peu (jalon 4).**

* Il faut au moins :data:`MIN_PAIRES` paires distinctes : une seule peut être
  une coïncidence.
* Premier essai : le plus petit programme qui explique toutes les paires et
  sait répondre à toutes les questions ; à taille égale, le premier trouvé
  dans l'ordre d'énumération (les feuilles, puis les briques dans l'ordre de
  :data:`BRIQUES`, de la plus simple à la plus composée).
* Deuxième essai : le plus petit programme suivant qui explique aussi toutes
  les paires mais donne une **autre** réponse à au moins une question.
* Si rien n'explique les paires jusqu'à :data:`MAX_TAILLE` (ou dans le budget
  :data:`MAX_PROGRAMMES`), elle le dit : pas de réponse inventée.

Ce qui est fourni à la main : les briques et leur ordre, la feuille ``x``,
les constantes ``0`` et ``1``, la façon de remarquer les constantes, la taille
maximale des programmes et des fonctions, le nombre minimal de paires, le
budget, et la préférence à taille égale.
"""

from __future__ import annotations

import itertools
import time
from collections import Counter
from dataclasses import dataclass, field

from xander import briques
from xander.effets import INDEFINI, _compositions

#: Taille maximale d'un programme (nombre de nœuds, la feuille ``e`` exclue).
MAX_TAILLE = 6
#: Taille maximale d'une fonction de l'élément (dans ``chaque`` et ``garder``).
MAX_TAILLE_FONCTION = 3
#: Nombre minimal de paires distinctes : une seule peut être une coïncidence.
MIN_PAIRES = 2
#: Nombre maximal de constantes remarquées dans les paires (en plus de 0 et 1).
MAX_CONSTANTES = 4
#: Budget : nombre maximal de programmes distincts examinés pour un problème.
MAX_PROGRAMMES = 400_000
#: Nombre maximal d'éléments sur lesquels on compare deux fonctions de l'élément.
MAX_ECHANTILLON = 48

#: Les sortes de valeurs : nombre, booléen, texte, liste.
NOMBRE, BOOLEEN, TEXTE, LISTE = "N", "B", "T", "L"
SUITE = TEXTE + LISTE
TOUT = None


@dataclass(frozen=True)
class Brique:
    nom: str
    fonction: object
    sortes: tuple          # pour chaque argument : sortes acceptées (TOUT : n'importe laquelle)
    fonctionnelle: bool = False   # le premier argument est une fonction de l'élément
    commutative: bool = False


#: L'équipement de naissance, dans l'ordre où la mère essaie les briques.
BRIQUES = (
    Brique("longueur", briques.longueur, (SUITE,)),
    Brique("premier", briques.premier, (SUITE,)),
    Brique("dernier", briques.dernier, (SUITE,)),
    Brique("inverser", briques.inverser, (SUITE,)),
    Brique("trier", briques.trier, (SUITE,)),
    Brique("somme", briques.somme, (LISTE,)),
    Brique("non", briques.non, (BOOLEEN,)),
    Brique("element", briques.element, (SUITE, NOMBRE)),
    Brique("compter", briques.compter, (SUITE, TOUT)),
    Brique("positions", briques.positions, (SUITE, TOUT)),
    Brique("couper", briques.couper, (SUITE, TOUT)),
    Brique("plus", briques.plus, (NOMBRE, NOMBRE), commutative=True),
    Brique("moins", briques.moins, (NOMBRE, NOMBRE)),
    Brique("fois", briques.fois, (NOMBRE, NOMBRE), commutative=True),
    Brique("egal", briques.egal, (TOUT, TOUT), commutative=True),
    Brique("inferieur", briques.inferieur, (NOMBRE, NOMBRE)),
    Brique("chaque", briques.chaque, (None, SUITE), fonctionnelle=True),
    Brique("garder", briques.garder, (None, SUITE), fonctionnelle=True),
)
PAR_NOM = {b.nom: b for b in BRIQUES}
#: Briques permises dans une fonction de l'élément.
BRIQUES_FONCTION = tuple(b for b in BRIQUES if not b.fonctionnelle)


# ---------------------------------------------------------------------- #
# Les programmes
# ---------------------------------------------------------------------- #

class Noeud:
    """Un programme : ``x``, ``e``, une constante, ou une brique appliquée à des programmes."""

    __slots__ = ("kind", "args", "size")

    def __init__(self, kind: str, *args):
        self.kind, self.args = kind, args
        if kind == "e":
            self.size = 0
        elif kind in ("x", "const"):
            self.size = 1
        else:
            self.size = 1 + sum(a.size for a in args)

    def __repr__(self) -> str:
        if self.kind in ("x", "e"):
            return self.kind
        if self.kind == "const":
            return _litteral(self.args[0])
        return f"{self.kind}({', '.join(map(repr, self.args))})"

    def briques(self) -> set[str]:
        """Les noms des briques dont le programme se sert."""
        noms = set() if self.kind in ("x", "e", "const") else {self.kind}
        for a in self.args:
            if isinstance(a, Noeud):
                noms |= a.briques()
        return noms

    def python(self) -> str:
        """Le programme en expression Python (avec les briques de :mod:`xander.briques`)."""
        if self.kind in ("x", "e"):
            return self.kind
        if self.kind == "const":
            return repr(self.args[0])
        args = [a.python() for a in self.args]
        if PAR_NOM[self.kind].fonctionnelle:
            args[0] = f"lambda e: {args[0]}"
        return f"{self.kind}({', '.join(args)})"


def _litteral(v) -> str:
    return '"' + v + '"' if isinstance(v, str) else repr(v)


X = Noeud("x")
E = Noeud("e")


def _cle(v):
    """Clé hachable sans ambiguïté de type (comme ``effets._cle``, en plus rapide)."""
    t = type(v)
    if t is list:
        return (t, tuple(map(_cle, v)))
    return (t, v)


def _sorte(v) -> str:
    if isinstance(v, bool):
        return BOOLEEN
    if isinstance(v, (int, float)):
        return NOMBRE
    if isinstance(v, str):
        return TEXTE
    return LISTE


#: Ce qu'une brique peut lever quand elle n'a pas de sens sur ses valeurs.
_ERREURS = (briques.Indefini, TypeError, ValueError, OverflowError, RecursionError)


def _valeurs(fonction, colonnes: list) -> tuple:
    """``fonction`` appliquée ligne à ligne aux colonnes de valeurs (``INDEFINI`` si elle n'a pas de sens)."""
    resultat = []
    if len(colonnes) == 1:
        for a in colonnes[0]:
            if a is INDEFINI:
                resultat.append(INDEFINI)
                continue
            try:
                resultat.append(fonction(a))
            except _ERREURS:
                resultat.append(INDEFINI)
    else:
        for a, b in zip(*colonnes):
            if a is INDEFINI or b is INDEFINI:
                resultat.append(INDEFINI)
                continue
            try:
                resultat.append(fonction(a, b))
            except _ERREURS:
                resultat.append(INDEFINI)
    return tuple(resultat)


def _memoire(f):
    """``f`` qui se souvient de ses réponses sur les valeurs simples (même résultat, plus vite)."""
    vues = {}

    def g(e):
        if type(e) is list:
            return f(e)
        cle = (type(e), e)
        r = vues.get(cle, g)
        if r is g:
            try:
                r = f(e)
            except _ERREURS:
                r = INDEFINI
            vues[cle] = r
        if r is INDEFINI:
            raise briques.Indefini
        return r
    return g


def _fonction_de(corps: Noeud):
    """La fonction Python ``e -> valeur`` d'un corps (lève ``Indefini`` si elle n'a pas de sens)."""
    if corps.kind == "e":
        return lambda e: e
    if corps.kind == "const":
        v = corps.args[0]
        return lambda e: v
    f = PAR_NOM[corps.kind].fonction
    enfants = [_fonction_de(a) for a in corps.args]
    if len(enfants) == 1:
        (a,) = enfants
        return lambda e: f(a(e))
    a, b = enfants
    return lambda e: f(a(e), b(e))


def evaluer(programme: Noeud, x, e=INDEFINI):
    """Valeur du programme sur l'entrée ``x`` (``INDEFINI`` s'il n'a pas de sens)."""
    try:
        return _evaluer(programme, x, e)
    except _ERREURS:
        return INDEFINI


def _evaluer(p: Noeud, x, e):
    if p.kind == "x":
        return x
    if p.kind == "e":
        return e
    if p.kind == "const":
        return p.args[0]
    brique = PAR_NOM[p.kind]
    if brique.fonctionnelle:
        corps, suite = p.args
        return brique.fonction(_fonction_de(corps), _evaluer(suite, x, e))
    valeurs = [_evaluer(a, x, e) for a in p.args]
    if any(v is INDEFINI for v in valeurs):
        raise briques.Indefini
    return brique.fonction(*valeurs)


# ---------------------------------------------------------------------- #
# Les constantes remarquées
# ---------------------------------------------------------------------- #

def _atomes(v):
    """Les valeurs simples contenues dans ``v`` : éléments des listes, lettres des textes."""
    if isinstance(v, list):
        for w in v:
            yield from _atomes(w)
    elif isinstance(v, str):
        yield v
        if len(v) > 1:
            yield from v
    else:
        yield v


def constantes(paires: list[tuple]) -> tuple:
    """Les constantes que la mère essaie : 0, 1, puis ce qui revient dans les paires.

    Une valeur simple (un nombre, un texte, une lettre d'un texte, un booléen)
    est remarquée si elle apparaît dans au moins deux paires (entrée ou sortie).
    On garde les :data:`MAX_CONSTANTES` qui reviennent dans le plus de paires,
    puis le plus souvent.
    """
    dans_paires, total = Counter(), Counter()
    for entree, sortie in paires:
        vues = list(_atomes(entree)) + list(_atomes(sortie))
        total.update(_cle(v) for v in vues)
        dans_paires.update({_cle(v) for v in vues})
    base = [0, 1]
    deja = {_cle(v) for v in base}
    candidates = [cle for cle, n in dans_paires.items() if n >= 2 and cle not in deja]
    candidates.sort(key=lambda cle: (-dans_paires[cle], -total[cle]))
    return tuple(base) + tuple(cle[1] for cle in candidates[:MAX_CONSTANTES])


# ---------------------------------------------------------------------- #
# L'énumération
# ---------------------------------------------------------------------- #

@dataclass
class _Entree:
    noeud: Noeud
    valeurs: tuple
    sortes: frozenset


def _accepte(sortes_permises, entree: _Entree) -> bool:
    return sortes_permises is TOUT or any(s in sortes_permises for s in entree.sortes)


class _Recherche:
    """L'énumération des programmes par taille croissante, sur des entrées données."""

    def __init__(self, contextes: list, consts: tuple, max_taille: int, max_programmes: int):
        self.contextes, self.consts = contextes, consts
        self.max_taille, self.max_programmes = max_taille, max_programmes
        self.vus: dict = {}                       # valeurs -> taille du plus petit programme
        self.par_taille: dict[int, list] = {}     # taille -> programmes servant de briques
        self.fonctions: dict[int, list] = {}      # taille -> fonctions de l'élément
        self.echantillon: list | None = None
        self.examines = 0
        self.budget_epuise = False

    # -- programmes -------------------------------------------------------
    def _proposer(self, noeud: Noeud, valeurs: tuple):
        if all(v is INDEFINI for v in valeurs):
            return None
        cle = tuple(_cle(v) for v in valeurs)
        if cle in self.vus:
            return None  # confondu avec un programme plus petit ou trouvé avant
        self.vus[cle] = noeud.size
        self.examines += 1
        entree = _Entree(noeud, valeurs, frozenset(_sorte(v) for v in valeurs if v is not INDEFINI))
        self.par_taille.setdefault(noeud.size, []).append(entree)
        return entree

    def programmes(self):
        """Les programmes distincts par taille croissante : des :class:`_Entree`."""
        n = len(self.contextes)
        for feuille in [X] + [Noeud("const", c) for c in self.consts]:
            valeurs = tuple(self.contextes) if feuille is X else (feuille.args[0],) * n
            trouve = self._proposer(feuille, valeurs)
            if trouve:
                yield trouve
        for taille in range(2, self.max_taille + 1):
            for brique in BRIQUES:
                for trouve in self._construire(brique, taille):
                    yield trouve
                    if self.examines >= self.max_programmes:
                        self.budget_epuise = True
                        return

    def _construire(self, brique: Brique, taille: int):
        if brique.fonctionnelle:
            yield from self._construire_fonctionnelle(brique, taille)
            return
        arite = len(brique.sortes)
        if taille - 1 < arite:
            return
        for tailles in _compositions(taille - 1, arite):
            if brique.commutative and tailles[0] > tailles[1]:
                continue  # commutatif : le plus petit argument d'abord
            groupes = [[e for e in self.par_taille.get(t, []) if _accepte(s, e)]
                       for t, s in zip(tailles, brique.sortes)]
            for choix in itertools.product(*groupes):
                if arite == 2:
                    a, b = choix
                    if brique.commutative and tailles[0] == tailles[1] and id(a) > id(b):
                        continue
                    if a is b and brique.nom not in ("plus", "fois"):
                        continue
                noeud = Noeud(brique.nom, *(e.noeud for e in choix))
                valeurs = _valeurs(brique.fonction, [e.valeurs for e in choix])
                trouve = self._proposer(noeud, valeurs)
                if trouve:
                    yield trouve

    def _construire_fonctionnelle(self, brique: Brique, taille: int):
        for taille_f in range(1, min(MAX_TAILLE_FONCTION, taille - 2) + 1):
            suites = [e for e in self.par_taille.get(taille - 1 - taille_f, []) if _accepte(SUITE, e)]
            if not suites:
                continue
            for corps, f in self._fonctions(taille_f):
                for suite in suites:
                    noeud = Noeud(brique.nom, corps, suite.noeud)
                    valeurs = _valeurs(brique.fonction, [(f,) * len(suite.valeurs), suite.valeurs])
                    trouve = self._proposer(noeud, valeurs)
                    if trouve:
                        yield trouve

    # -- fonctions de l'élément -------------------------------------------
    def _fonctions(self, taille: int) -> list:
        """Les fonctions de l'élément de cette taille : ``(corps, fonction Python)``.

        Deux fonctions qui donnent les mêmes valeurs sur un échantillon
        d'éléments (ceux des suites déjà construites) sont confondues.
        """
        if taille not in self.fonctions:
            if self.echantillon is None:
                self.echantillon = self._echantillon()
            self.fonctions[taille] = self._fonctions_de_taille(taille)
        return [(c, f) for c, f, _ in self.fonctions[taille]]

    def _echantillon(self) -> list:
        vus, echantillon = set(), []
        for taille in sorted(self.par_taille):
            for entree in self.par_taille[taille]:
                for v in entree.valeurs:
                    if isinstance(v, (str, list)):
                        for w in v:
                            cle = _cle(w)
                            if cle not in vus:
                                vus.add(cle)
                                echantillon.append(w)
        return echantillon[:MAX_ECHANTILLON]

    def _fonctions_de_taille(self, taille: int) -> list:
        if not hasattr(self, "_vues_fonctions"):
            self._vues_fonctions = set()
        # Les morceaux d'un corps : e (taille 0), constantes (taille 1), corps plus petits.
        def morceaux(t):
            if t == 0:
                return [(E, tuple(self.echantillon))]
            if t == 1:
                consts = [(Noeud("const", c), (c,) * len(self.echantillon)) for c in self.consts]
                return consts + [(c, v) for c, _, v in self.fonctions.get(1, [])]
            return [(c, v) for c, _, v in self.fonctions.get(t, [])]

        candidats = []
        for brique in BRIQUES_FONCTION:
            arite = len(brique.sortes)
            for tailles in itertools.product(range(taille), repeat=arite):
                if sum(tailles) != taille - 1:
                    continue
                for choix in itertools.product(*(morceaux(t) for t in tailles)):
                    noeuds = [c for c, _ in choix]
                    if not any(_contient_e(c) for c in noeuds):
                        continue  # une fonction qui ne regarde pas l'élément
                    if arite == 2:
                        a, b = noeuds
                        if a is b and brique.nom not in ("plus", "fois"):
                            continue
                        if brique.commutative and tailles[0] == tailles[1] and repr(a) > repr(b):
                            continue
                    candidats.append((brique, choix))
        # À taille égale, les fonctions les moins composées d'abord : « 0 < e » plutôt que « e < e + e ».
        candidats.sort(key=lambda bc: sum(c.kind not in ("e", "const") for c, _ in bc[1]))
        resultat = []
        for brique, choix in candidats:
            valeurs = _valeurs(brique.fonction, [v for _, v in choix])
            if all(v is INDEFINI for v in valeurs):
                continue
            cle = tuple(_cle(v) for v in valeurs)
            if cle in self._vues_fonctions:
                continue
            self._vues_fonctions.add(cle)
            corps = Noeud(brique.nom, *(c for c, _ in choix))
            resultat.append((corps, _memoire(_fonction_de(corps)), valeurs))
        return resultat


def _contient_e(n: Noeud) -> bool:
    return n.kind == "e" or any(isinstance(a, Noeud) and _contient_e(a) for a in n.args)


# ---------------------------------------------------------------------- #
# Comprendre un problème
# ---------------------------------------------------------------------- #

@dataclass
class Essai:
    """Un programme qui explique toutes les paires, et ses réponses aux questions."""

    programme: Noeud
    reponses: list

    @property
    def taille(self) -> int:
        return self.programme.size

    def __repr__(self) -> str:
        return f"sortie = {self.programme!r}"


@dataclass
class Comprehension:
    """Ce que la mère a compris d'un problème « entrée -> sortie »."""

    essais: list[Essai] = field(default_factory=list)   # premier essai, puis deuxième s'il existe
    meme_taille: int = 0          # programmes de la taille du premier qui expliquent les paires
    constantes: tuple = ()
    examines: int = 0             # programmes distincts examinés
    duree: float = 0.0            # secondes
    raison: str = ""              # pourquoi elle ne répond pas (si aucun essai)
    nb_paires: int = 0

    @property
    def comprise(self) -> bool:
        return bool(self.essais)

    def decrire(self) -> str:
        lignes = []
        if not self.essais:
            lignes.append(f"La mère ne trouve pas : {self.raison}")
        else:
            premier = self.essais[0]
            lignes.append(f"Ce que la mère a compris : {premier!r}  (taille {premier.taille}, "
                          f"explique les {self.nb_paires} paires)")
            if self.meme_taille > 1:
                lignes.append(f"  {self.meme_taille} programmes de cette taille expliquent les paires, avec des "
                              "réponses différentes ; elle garde le premier trouvé")
            if len(self.essais) > 1:
                deuxieme = self.essais[1]
                lignes.append(f"Deuxième essai, réellement différent : {deuxieme!r}  (taille {deuxieme.taille})")
            else:
                lignes.append("Pas de deuxième essai : aucun autre programme dans la taille permise "
                              "ne donne une autre réponse")
        lignes.append(f"Constantes remarquées : {', '.join(map(_litteral, self.constantes))} ; "
                      f"{self.examines} programmes distincts examinés en {self.duree:.2f} s")
        return "\n".join(lignes)


def comprendre(paires: list[tuple], questions: list, max_taille: int = MAX_TAILLE,
               max_programmes: int = MAX_PROGRAMMES) -> Comprehension:
    """Le plus petit programme qui transforme chaque entrée en sa sortie, et un deuxième essai.

    ``paires`` : des couples (entrée, sortie) ; ``questions`` : des entrées
    seules. Les réponses attendues aux questions ne sont jamais données ici.
    """
    debut = time.perf_counter()
    uniques = {}
    for entree, sortie in paires:
        uniques.setdefault(_cle(entree), (entree, sortie))
    if any(_cle(s) != _cle(uniques[_cle(e)][1]) for e, s in paires):
        return Comprehension(raison="deux paires donnent deux sorties différentes pour la même entrée",
                             nb_paires=len(paires), duree=time.perf_counter() - debut)
    paires = list(uniques.values())
    if len(paires) < MIN_PAIRES:
        return Comprehension(raison=f"il faut au moins {MIN_PAIRES} paires distinctes "
                                    "(une seule peut être une coïncidence)",
                             nb_paires=len(paires), duree=time.perf_counter() - debut)
    consts = constantes(paires)
    contextes = [e for e, _ in paires] + list(questions)
    cibles = tuple(_cle(s) for _, s in paires)
    n = len(paires)
    recherche = _Recherche(contextes, consts, max_taille, max_programmes)
    essais: list[Essai] = []
    meme_taille = 0
    for entree in recherche.programmes():
        if essais and entree.noeud.size > essais[0].taille and len(essais) > 1:
            break
        cles = tuple(_cle(v) for v in entree.valeurs[:n])
        if cles != cibles or any(v is INDEFINI for v in entree.valeurs[n:]):
            continue
        reponses = list(entree.valeurs[n:])
        if not essais:
            essais.append(Essai(entree.noeud, reponses))
        elif len(essais) == 1 and [_cle(r) for r in reponses] != [_cle(r) for r in essais[0].reponses]:
            essais.append(Essai(entree.noeud, reponses))
        if entree.noeud.size == essais[0].taille:
            meme_taille += 1
    raison = ""
    if not essais:
        raison = (f"le budget de {max_programmes} programmes est épuisé" if recherche.budget_epuise else
                  f"aucun programme de taille {max_taille} au plus n'explique toutes les paires")
    return Comprehension(essais=essais, meme_taille=meme_taille, constantes=consts,
                         examines=recherche.examines, duree=time.perf_counter() - debut,
                         raison=raison, nb_paires=n)
