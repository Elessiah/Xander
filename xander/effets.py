"""Les briques avec lesquelles la mère décrit l'effet d'une action.

L'Analyzer ne connaît plus d'hypothèses nommées (« modifie la case
d'indice p », « retire p »…) : la mère **construit** la description de ce que
fait une action, comme elle construit ses concepts (voir
:mod:`xander.concepts`).

Un **cas** est une transition observée : la valeur d'une variable avant
l'appel, les arguments de l'appel, et la valeur après. Une **hypothèse** est un
petit programme qui prédit, à partir de la valeur d'avant et des arguments,
ce qui a changé. Elle prend l'une de deux formes :

* ``apres = t`` : la nouvelle valeur entière (pour un nombre) ;
* ``changees = t`` : l'ensemble des cases qui ont changé (pour un tableau).

Le terme ``t`` est un arbre construit avec :

* les feuilles ``arg(k)`` (le k-ième argument de l'appel), ``avant`` (la
  valeur d'avant) et des **constantes mesurées** sur les cas (voir
  :func:`constantes`) : écarts entre la case changée et un argument, valeurs
  qu'avaient les cases changées ;
* ``plus(x, y)`` et ``moins(x, y)`` sur des nombres ;
* ``case(x)`` : la case d'indice ``x`` ; ``valant(x)`` : les cases dont la
  valeur est ``x`` (ou s'écrit comme ``x``) ; ``union(e, f)`` de deux ensembles
  de cases ;
* ``portee(x)`` : les cases que la mère a vu l'action ``x`` remplir, dans
  l'ordre qu'elle en déduit (voir :func:`portees_observees`). C'est une
  **observation** faite dans le labo, pas un calcul : au Morpion une seule case, au Puissance 4 la colonne de bas
  en haut ;
* ``premiere_de(s, e)`` : la première case de la suite ``s`` qui appartient à
  l'ensemble ``e`` (aucune s'il n'y en a pas).

La gravité du Puissance 4 n'est donc pas fournie : c'est une composition que la
mère construit, ``premiere_de(portee(arg0), valant(' '))`` (la première case
vide de ce que remplit l'action). Le même programme décrit une gravité vers le
haut, un tube ou une pile : l'ordre vient de ce qu'elle a vu.

La mère énumère les termes par taille croissante et garde, pour chaque
variable, les plus petites hypothèses qui expliquent **tous** les cas
observés, et au moins deux cas distincts (un seul cas peut être une
coïncidence). Deux termes qui donnent les mêmes valeurs sur tous les cas sont
confondus, on garde le plus petit ; à taille égale, ils coexistent : la mère
ne sait pas encore les départager (au Morpion, « la case d'indice p » et « la
case qui vaut p » disent toujours la même chose).

Exemples (que la mère doit trouver seule, ils ne sont écrits nulle part sauf
dans les tests) : au Morpion ``changees = case(arg0)`` ; aux Allumettes
``apres = moins(avant, arg0)`` ; un déplacement ``changees = union(case(arg0),
case(arg1))`` ; au Puissance 4 ``changees = premiere_de(portee(arg0), valant(' '))``.

Ce qui est fourni à la main : les deux formes, les feuilles, les sortes de
constantes mesurées, les sept opérations ci-dessus (dont ``premiere_de``, une
brique d'ordre générale), la façon d'observer une portée (rejouer la même
action depuis le début), la taille maximale des termes (:data:`MAX_TAILLE`) et
le nombre minimal de cas (:data:`MIN_CAS`).

**Un état qui défile.** Quand aucun ensemble de cases changées ne s'explique,
la mère essaie une troisième forme, ``suite = decale(avant, d)`` (voir
:class:`Defilement`) : l'état d'avant, décalé, sauf ce qu'elle sait nommer et
ne prévoit pas (ce qui entre par le bord, un mobile qui ne défile pas, des
cases fixes). Fournis à la main : ces trois sortes d'exceptions, la profondeur
de l'entrée (2 |d|) et la part de l'état qu'elle peut couvrir (la moitié).
"""

from __future__ import annotations

import itertools
from collections import Counter
from dataclasses import dataclass

#: Taille maximale d'un terme (nombre de nœuds).
MAX_TAILLE = 5
#: Nombre minimal de cas distincts pour qu'une hypothèse soit retenue.
MIN_CAS = 2
#: Nombre maximal de constantes de chaque sorte retenues (les plus fréquentes).
MAX_CONSTANTES = 8

APRES, CHANGEES = "apres", "changees"


class _Indefini:
    """Valeur d'un terme qui n'a pas de sens sur un cas (``case`` d'un texte…)."""

    def __repr__(self) -> str:
        return "INDEFINI"


INDEFINI = _Indefini()


class Terme:
    """Nœud d'un terme. Les nœuds sont uniques (internés) : ``is`` et ``==`` suffisent."""

    __slots__ = ("kind", "args", "size", "id")
    _table: dict = {}

    def __new__(cls, kind, *args):
        key = (kind,) + tuple(a.id if isinstance(a, Terme) else (type(a).__name__, a) for a in args)
        node = cls._table.get(key)
        if node is None:
            node = object.__new__(cls)
            node.kind, node.args, node.id = kind, args, len(cls._table)
            node.size = 1 + sum(a.size for a in args if isinstance(a, Terme))
            cls._table[key] = node
        return node

    def __repr__(self) -> str:
        if self.kind == "arg":
            return f"arg{self.args[0]}"
        if self.kind == "avant":
            return "avant"
        if self.kind == "const":
            return repr(self.args[0])
        if self.kind in ("ici", "ecrit", "cellule"):
            return self.kind + (str(self.args[0]) if self.args[0] else "")
        return f"{self.kind}({', '.join(map(repr, self.args))})"


def arg(k: int) -> Terme:
    return Terme("arg", k)


def avant() -> Terme:
    return Terme("avant")


def const(valeur) -> Terme:
    return Terme("const", valeur)


def _ordonnes(x: Terme, y: Terme) -> tuple[Terme, Terme]:
    return (x, y) if x.id <= y.id else (y, x)


def plus(x: Terme, y: Terme) -> Terme:
    return Terme("plus", *_ordonnes(x, y))


def moins(x: Terme, y: Terme) -> Terme:
    return Terme("moins", x, y)


def case(x: Terme) -> Terme:
    return Terme("case", x)


def valant(x: Terme) -> Terme:
    return Terme("valant", x)


def union(e: Terme, f: Terme) -> Terme:
    return Terme("union", *_ordonnes(e, f))


def portee(x: Terme) -> Terme:
    return Terme("portee", x)


def premiere_de(s: Terme, e: Terme) -> Terme:
    return Terme("premiere_de", s, e)


# Ce que l'action écrit, et quand elle est permise : feuilles et opérations de plus
# (voir :func:`ecritures` et :func:`liberte_valeurs`).

def ici(p: int = 0) -> Terme:
    """La valeur qu'avait, avant le coup, la case que change la partie ``p`` de l'action."""
    return Terme("ici", p)


def ecrit(p: int = 0) -> Terme:
    """La valeur que la partie ``p`` de l'action écrit dans sa case."""
    return Terme("ecrit", p)


def cellule(p: int = 0) -> Terme:
    """L'indice de la case que change la partie ``p`` de l'action."""
    return Terme("cellule", p)


def val(x: Terme) -> Terme:
    """La valeur qu'avait, avant le coup, la case d'indice ``x``."""
    return Terme("val", x)


def fois(x: Terme, y: Terme) -> Terme:
    return Terme("fois", *_ordonnes(x, y))


def divise(x: Terme, y: Terme) -> Terme:
    """La division de deux entiers, seulement quand elle tombe juste (sinon elle n'a pas de sens)."""
    return Terme("divise", x, y)


@dataclass(frozen=True)
class Hypothese:
    """« ``forme`` = ``terme`` » : ce que la mère pense qu'une action fait à une variable."""

    forme: str
    terme: Terme

    def __repr__(self) -> str:
        return f"{self.forme} = {self.terme!r}"


# ---------------------------------------------------------------------- #
# Évaluer un terme sur un cas
# ---------------------------------------------------------------------- #

@dataclass(frozen=True)
class Cas:
    """Une transition observée : ``valeur_avant --action(arguments)--> valeur_apres``."""

    valeur_avant: object
    arguments: tuple
    valeur_apres: object

    @property
    def forme(self) -> str | None:
        """La forme d'hypothèse qui peut l'expliquer, ``None`` s'il n'y a rien à expliquer."""
        a, b = self.valeur_avant, self.valeur_apres
        if _est_nombre(a) and _est_nombre(b):
            return APRES
        if isinstance(a, list) and isinstance(b, list) and len(a) == len(b) and a != b:
            return CHANGEES
        return None

    def cible(self):
        """Ce que l'hypothèse doit prédire : la valeur d'après, ou les cases changées."""
        if self.forme == APRES:
            return self.valeur_apres
        return frozenset(i for i, (x, y) in enumerate(zip(self.valeur_avant, self.valeur_apres)) if x != y)


def _est_nombre(valeur) -> bool:
    return isinstance(valeur, (int, float)) and not isinstance(valeur, bool)


def _est_entier(valeur) -> bool:
    return isinstance(valeur, int) and not isinstance(valeur, bool)


def _est_indice(valeur, tableau) -> bool:
    return _est_entier(valeur) and isinstance(tableau, list) and 0 <= valeur < len(tableau)


def _portee(portees: dict | None, x, k: int | None = None):
    """La portée observée de l'action ``x`` (une suite de cases), ``INDEFINI`` si elle est inconnue.

    Pour une action à plusieurs arguments, les portées sont rangées par argument :
    la clé ``(k, x)`` donne les cases que l'action remplit quand son argument ``k``
    vaut ``x`` (voir :func:`portees_observees`)."""
    try:
        portees = portees or {}
        suite = portees.get((k, x)) if k is not None else None
        if suite is None:
            suite = portees.get(x)
    except TypeError:  # argument non hachable
        return INDEFINI
    return tuple(suite) if suite is not None else INDEFINI


def evaluer(terme: Terme, cas: Cas, enfants: tuple = None, portees: dict | None = None):
    """Valeur de ``terme`` sur ``cas`` (``enfants`` : valeurs déjà calculées des sous-termes ;
    ``portees`` : action -> cases qu'elle remplit, observées dans le labo)."""
    if enfants is None:
        enfants = tuple(evaluer(a, cas, None, portees) for a in terme.args if isinstance(a, Terme))
    if any(v is INDEFINI for v in enfants):
        return INDEFINI
    kind, tableau = terme.kind, cas.valeur_avant
    if kind == "arg":
        k = terme.args[0]
        return cas.arguments[k] if k < len(cas.arguments) else INDEFINI
    if kind == "avant":
        return tableau
    if kind == "const":
        return terme.args[0]
    if kind in ("plus", "moins", "fois"):
        x, y = enfants
        if not (_est_nombre(x) and _est_nombre(y)):
            return INDEFINI
        return x + y if kind == "plus" else x - y if kind == "moins" else x * y
    if kind == "divise":
        x, y = enfants
        if not (_est_entier(x) and _est_entier(y)) or y == 0 or x % y:
            return INDEFINI
        return x // y
    if kind in ("ici", "ecrit", "cellule"):
        parties = getattr(cas, "parties", None)
        p = terme.args[0]
        if not parties or p >= len(parties):
            return INDEFINI
        return parties[p][("cellule", "ici", "ecrit").index(kind)]
    if kind == "val":
        (x,) = enfants
        return tableau[x] if _est_indice(x, tableau) else INDEFINI
    if kind == "case":
        (x,) = enfants
        return frozenset((x,)) if _est_indice(x, tableau) else INDEFINI
    if kind == "valant":
        (x,) = enfants
        if not isinstance(tableau, list) or isinstance(x, (frozenset, list, tuple)):
            return INDEFINI
        return frozenset(i for i, v in enumerate(tableau) if v == x or str(v) == str(x))
    if kind == "union":
        e, f = enfants
        return e | f if isinstance(e, frozenset) and isinstance(f, frozenset) else INDEFINI
    if kind == "portee":
        (x,) = enfants
        if isinstance(x, (frozenset, list, tuple)):
            return INDEFINI
        feuille = terme.args[0]
        return _portee(portees, x, feuille.args[0] if feuille.kind == "arg" else None)
    if kind == "premiere_de":
        s, e = enfants
        if not (isinstance(s, tuple) and isinstance(e, frozenset)):
            return INDEFINI
        return next((frozenset((c,)) for c in s if c in e), frozenset())
    raise ValueError(kind)


# ---------------------------------------------------------------------- #
# Découvrir les hypothèses
# ---------------------------------------------------------------------- #

#: Les opérations et leur nombre d'arguments.
OPERATIONS = ((case, 1), (valant, 1), (portee, 1), (plus, 2), (moins, 2), (union, 2), (premiere_de, 2))
#: Opérations commutatives : un seul ordre d'arguments est essayé.
COMMUTATIVES = (plus, union, fois)
#: Pour dire la valeur qu'une action écrit : la valeur d'avant d'une case et les quatre opérations
#: (l'équipement « nombre » ; voir :func:`ecritures`).
OPERATIONS_ECRITURE = ((val, 1), (plus, 2), (moins, 2), (fois, 2), (divise, 2))
#: Pour dire quand une action est permise : ce qui désigne des cases et des valeurs (voir
#: :func:`liberte_valeurs`).
OPERATIONS_CONDITION = ((val, 1), (valant, 1), (portee, 1), (plus, 2), (moins, 2), (premiere_de, 2))


def _compositions(total: int, parts: int):
    """Les façons d'écrire ``total`` comme somme ordonnée de ``parts`` entiers positifs."""
    if parts == 1:
        yield (total,)
        return
    for first in range(1, total - parts + 2):
        for rest in _compositions(total - first, parts - 1):
            yield (first,) + rest


def termes(cas: list[Cas], nb_arguments: int, max_taille: int = MAX_TAILLE, constants: tuple = (),
           portees: dict | None = None, operations: tuple | None = None, feuilles: list | None = None):
    """Énumère les termes par taille croissante, avec leurs valeurs sur ``cas``.

    Renvoie ``(terme, valeurs)``. Un terme qui donne les mêmes valeurs qu'un
    terme plus petit n'est pas renvoyé ; un terme de même taille l'est (il
    coexiste) mais ne sert pas à en construire d'autres. Sans ``portees``, les
    termes ``portee`` ne sont pas essayés. ``operations`` et ``feuilles``
    remplacent celles qui décrivent les cases changées (pour la valeur écrite et
    les conditions, voir :data:`OPERATIONS_ECRITURE`).
    """
    vus: dict[tuple, int] = {}                     # valeurs -> taille du plus petit terme
    par_taille: dict[int, list] = {}               # taille -> [(terme, valeurs)] servant de briques

    def proposer(terme: Terme, valeurs: tuple):
        if all(v is INDEFINI for v in valeurs):
            return None
        cle = tuple(_cle(v) for v in valeurs)
        taille = vus.get(cle)
        if taille is not None and taille < terme.size:
            return None
        if taille is None:
            vus[cle] = terme.size
            par_taille.setdefault(terme.size, []).append((terme, valeurs))
        return terme, valeurs

    def construire(terme: Terme, enfants: dict | None = None):
        ordre = [enfants[a] for a in terme.args if isinstance(a, Terme)] if enfants else []
        valeurs = tuple(evaluer(terme, c, tuple(v[i] for v in ordre), portees) for i, c in enumerate(cas))
        return proposer(terme, valeurs)

    operations = [(op, n) for op, n in (operations or OPERATIONS) if portees or op is not portee]
    if feuilles is None:
        feuilles = [arg(k) for k in range(nb_arguments)] + [avant()] + [const(v) for v in constants]
    for feuille in feuilles:
        trouve = construire(feuille)
        if trouve:
            yield trouve
    for taille in range(2, max_taille + 1):
        for operation, arite in operations:
            if taille - 1 < arite:
                continue
            for tailles in _compositions(taille - 1, arite):
                groupes = [list(par_taille.get(t, [])) for t in tailles]
                for choix in itertools.product(*groupes):
                    enfants = [t for t, _ in choix]
                    if operation in COMMUTATIVES and enfants[0].id > enfants[1].id:
                        continue  # commutatif : un seul ordre
                    if operation in (moins, union, divise) and enfants[0] is enfants[1]:
                        continue  # x - x, x ∪ x et x / x n'apprennent rien
                    terme = operation(*enfants)
                    trouve = construire(terme, dict(choix))
                    if trouve:
                        yield trouve


def constantes(cas: list[Cas]) -> tuple:
    """Les constantes que la mère remarque dans les cas (les plus fréquentes de chaque sorte).

    * écarts entre une case changée et un argument entier (un décalage) ;
    * valeurs qu'avaient les cases changées (au Puissance 4, la case vide).

    Pour un nombre (forme ``apres``), aucune constante n'est mesurée.
    """
    nombres, valeurs = Counter(), Counter()
    for c in cas:
        if c.forme != CHANGEES:
            continue
        for i in sorted(c.cible()):
            valeurs[_cle(c.valeur_avant[i])] += 1
            for a in c.arguments:
                if _est_entier(a):
                    nombres[i - a] += 1
    retenus = [n for n, _ in nombres.most_common(MAX_CONSTANTES)]
    vues = [cle[1] for cle, _ in valeurs.most_common(MAX_CONSTANTES)]
    return tuple(sorted(retenus, key=lambda n: (abs(n), n))) + tuple(vues)


def portees_observees(observations: list[Cas]) -> dict:
    """Ce que chaque action remplit, et dans quel ordre, déduit de tout ce que la mère a vu.

    Seuls comptent les cas à un argument où une seule case a changé. La portée
    de l'action ``a`` est l'ensemble des cases qu'on l'a vue remplir. L'ordre se
    déduit des positions : si ``a`` a rempli la case ``c`` alors que la case
    ``d`` (de sa portée) était encore dans le même état que ``c``, c'est que
    ``c`` vient avant ``d``. À égalité, l'ordre dans lequel la mère les a vues.
    Si aucun ordre ne convient (un cycle), l'action n'a pas de portée : ce
    qu'elle remplit ne suit pas une suite.

    Au Morpion, chaque action n'a qu'une case ; au Puissance 4, la colonne, de
    bas en haut, sans que la mère sache ce qu'est une colonne.

    **Une action à plusieurs arguments** (à Hanoï, ``play(depart, arrivee)`` ; au
    Nim, ``play(tas, nombre)``) : la mère range ce qu'elle a vu **par argument**.
    La clé ``(k, x)`` donne les cases que l'action a remplies quand son argument
    ``k`` valait ``x``, dans l'ordre déduit de la même façon ; le terme
    ``portee(argk)`` la lit. À Hanoï, ``(0, 0)`` (partir du piquet 0) remplit les
    cases 0, 1, 2 dans cet ordre (le petit disque part avant le moyen) ; au Nim,
    ``(0, 2)`` remplit la case 2. Les cas à un argument restent rangés par
    valeur, comme avant.
    """
    vues: dict = {}        # action -> cases, dans l'ordre où elles ont été vues
    remplissages = []      # (action, case remplie, état avant)
    for c in observations:
        if c.forme != CHANGEES or not c.arguments:
            continue
        changees = c.cible()
        if len(changees) != 1:
            continue
        (case_,) = changees
        cles = [c.arguments[0]] if len(c.arguments) == 1 else list(enumerate(c.arguments))
        for a in cles:
            try:
                hash(a)
            except TypeError:
                continue
            cases = vues.setdefault(a, [])
            if case_ not in cases:
                cases.append(case_)
            remplissages.append((a, case_, c.valeur_avant))
    avant_que: dict = {a: {c: set() for c in cases} for a, cases in vues.items()}  # c -> cases après c
    for a, case_, etat in remplissages:
        for autre in vues[a]:
            if autre != case_ and etat[autre] == etat[case_]:
                avant_que[a][case_].add(autre)
    portees = {}
    for a, cases in vues.items():
        apres = avant_que[a]
        restantes, ordre = list(cases), []
        while restantes:
            libre = next((c for c in restantes
                          if not any(c in apres[d] for d in restantes if d != c)), None)
            if libre is None:
                break  # un cycle : pas d'ordre
            ordre.append(libre)
            restantes.remove(libre)
        if not restantes:
            portees[a] = ordre
    return portees


def ecriture(observations: list[tuple[Cas, object]]) -> tuple | None:
    """Quelle valeur l'action écrit-elle dans la case qu'elle change ?

    ``observations`` : des couples (cas, joueur qui a joué). La mère essaie, de
    la plus simple à la moins simple, les descriptions qu'elle connaît et garde
    la première qui convient à tous les cas où une seule case a changé :

    * ``("constante", v)`` : toujours la même valeur ;
    * ``("argument", k)`` : la valeur du k-ième argument ;
    * ``("joueur",)`` : une valeur propre à chaque joueur, la même à chaque fois
      qu'il joue et différente de celle des autres (au Morpion, le pion).

    ``None`` si aucune ne convient (ou s'il n'y a aucun cas).
    """
    ecrits = []  # (valeur écrite, arguments, joueur)
    for c, joueur in observations:
        if c.forme != CHANGEES or len(c.cible()) != 1:
            continue
        (case_,) = c.cible()
        ecrits.append((c.valeur_apres[case_], c.arguments, joueur))
    if not ecrits:
        return None
    valeurs = {_cle(v) for v, _, _ in ecrits}
    if len(valeurs) == 1:
        return ("constante", ecrits[0][0])
    for k in range(min(len(args) for _, args, _ in ecrits)):
        if all(_cle(v) == _cle(args[k]) for v, args, _ in ecrits):
            return ("argument", k)
    par_joueur: dict = {}
    for v, _, joueur in ecrits:
        par_joueur.setdefault(_cle(joueur), set()).add(_cle(v))
    if all(len(vs) == 1 for vs in par_joueur.values()) and \
            len({next(iter(vs)) for vs in par_joueur.values()}) == len(par_joueur):
        return ("joueur",)
    return None


# ---------------------------------------------------------------------- #
# Ce que l'action écrit, partie par partie : un petit programme
# ---------------------------------------------------------------------- #

#: Valeurs distinctes d'un argument au plus pour que la mère sépare les cas selon sa valeur.
MAX_VALEURS_SELON = 8


@dataclass(frozen=True)
class Ecrit:
    """Une case qu'une action a écrite : l'état d'avant, les arguments, la case et ce qu'elle reçoit.

    ``parties`` donne au terme ``ici`` la valeur qu'avait la case (voir :func:`evaluer`)."""

    valeur_avant: object
    arguments: tuple
    case: int
    valeur: object

    @property
    def parties(self) -> tuple:
        return ((self.case, self.valeur_avant[self.case], INDEFINI),)


@dataclass(frozen=True)
class Coup:
    """Un coup prévu, pour décider s'il est permis : l'état d'avant, les arguments et, pour
    chaque partie de l'action, ``(case, valeur d'avant, valeur écrite)`` (``INDEFINI`` partout
    si la partie ne change pas exactement une case)."""

    valeur_avant: object
    arguments: tuple
    parties: tuple


def parties(hypothese: Hypothese) -> list[Terme]:
    """Les parties d'une description ``changees = …`` : les termes réunis par ``union``.

    Au Compte est bon, ``union(case(arg0), case(arg1))`` a deux parties : la place du
    résultat et celle qui se vide. Chacune écrit sa propre valeur."""
    def morceaux(t: Terme) -> list[Terme]:
        return morceaux(t.args[0]) + morceaux(t.args[1]) if t.kind == "union" else [t]
    return morceaux(hypothese.terme)


def _sans_selon(ecrits: list) -> tuple | None:
    """Une description de la valeur écrite qui ne sépare pas les cas (voir :func:`decrire_ecriture`)."""
    valeurs = {_cle(e.valeur) for e, _ in ecrits}
    if len(valeurs) == 1:
        return ("constante", ecrits[0][0].valeur)
    for k in range(min(len(e.arguments) for e, _ in ecrits)):
        if all(_cle(e.valeur) == _cle(e.arguments[k]) for e, _ in ecrits):
            return ("argument", k)
    joueurs = {_cle(j) for _, j in ecrits}
    if len(joueurs) > 1 and None not in {j for _, j in ecrits}:
        par_joueur: dict = {}
        for e, j in ecrits:
            par_joueur.setdefault(_cle(j), set()).add(_cle(e.valeur))
        if all(len(vs) == 1 for vs in par_joueur.values()) and \
                len({next(iter(vs)) for vs in par_joueur.values()}) == len(par_joueur):
            return ("joueur",)
    terme = programme_ecrit([e for e, _ in ecrits])
    return ("programme", terme) if terme is not None else None


def programme_ecrit(ecrits: list[Ecrit], max_taille: int = MAX_TAILLE, min_cas: int = MIN_CAS) -> Terme | None:
    """Le plus petit programme qui donne la valeur écrite dans **tous** les cas (au moins
    ``min_cas`` cas distincts), construit avec les arguments, ``ici`` (la valeur d'avant de la
    case), ``val(x)`` (la valeur d'avant de la case *x*) et les quatre opérations. Au Nim :
    ``moins(ici, arg1)``, le tas perd ce qu'on y prend."""
    uniques = {_cle((e.valeur_avant, e.arguments, e.case, e.valeur)): e for e in ecrits}
    cas = list(uniques.values())
    if len(cas) < min_cas:
        return None
    nb_arguments = min(len(e.arguments) for e in cas)
    cibles = tuple(_cle(e.valeur) for e in cas)
    feuilles = [arg(k) for k in range(nb_arguments)] + [ici()]
    for terme, valeurs in termes(cas, nb_arguments, max_taille, (), None, OPERATIONS_ECRITURE, feuilles):
        if tuple(_cle(v) for v in valeurs) == cibles:
            return terme
    return None


def decrire_ecriture(ecrits: list) -> tuple | None:
    """Quelle valeur une partie de l'action écrit-elle ? ``ecrits`` : des couples
    (:class:`Ecrit`, joueur qui a joué). De la plus simple à la moins simple :

    * ``("constante", v)``, ``("argument", k)``, ``("joueur",)`` (comme :func:`ecriture`) ;
    * ``("programme", t)`` : un petit programme (:func:`programme_ecrit`) ;
    * ``("selon", k, ((v, description), …))`` : la valeur dépend de **ce que choisit un
      argument** ; la mère sépare les cas selon la valeur de l'argument ``k`` (au plus
      :data:`MAX_VALEURS_SELON` valeurs) et décrit chaque groupe seul. Un groupe vu une seule
      fois n'est pas décrit (un seul cas peut être une coïncidence) : pour cette valeur, elle
      ne prévoit rien. Au Compte est bon, ``arg2`` choisit l'opération.

    ``None`` si rien ne convient."""
    if not ecrits:
        return None
    simple = _sans_selon(ecrits)
    if simple is not None:
        return simple
    for k in range(min(len(e.arguments) for e, _ in ecrits)):
        groupes: dict = {}
        try:
            for e, j in ecrits:
                groupes.setdefault(_cle(e.arguments[k]), (e.arguments[k], []))[1].append((e, j))
        except TypeError:
            continue
        if not 2 <= len(groupes) <= MAX_VALEURS_SELON:
            continue
        table, compris = [], True
        for valeur, groupe in groupes.values():
            distincts = {_cle((e.valeur_avant, e.arguments, e.case)) for e, _ in groupe}
            if len(distincts) < MIN_CAS:
                continue  # vu une seule fois : peut-être une coïncidence, elle ne le décrit pas
            description = _sans_selon(groupe)
            if description is None:
                compris = False
                break
            table.append((valeur, description))
        if compris and len(table) >= MIN_CAS:
            return ("selon", k, tuple(sorted(table, key=lambda t: repr(t[0]))))
    return None


def ecritures(hypothese: Hypothese, observations: list, portees: dict | None = None) -> list | None:
    """Ce que chaque partie de l'action écrit : ``[(partie, description), …]``.

    ``observations`` : des couples (cas, joueur qui a joué). Pour chaque partie de la
    description (voir :func:`parties`), la mère regarde ce que sont devenues les cases
    qu'elle désignait, et décrit cette valeur (:func:`decrire_ecriture`). Au Nim,
    ``case(arg0)`` reçoit ``moins(ici, arg1)`` ; à Hanoï, la case du disque déplacé reçoit
    ``arg1`` (le piquet d'arrivée) ; au Compte est bon, ``case(arg0)`` reçoit le résultat
    (l'opération choisie par ``arg2``) et ``case(arg1)`` reçoit 0. ``None`` si une partie ne
    se décrit pas."""
    if not isinstance(hypothese, Hypothese) or hypothese.forme not in (CHANGEES, ECRITES):
        return None
    resultat = []
    for partie in parties(hypothese):
        ecrits = []
        for c, joueur in observations:
            if c.forme != CHANGEES:
                continue
            cases = evaluer(partie, c, None, portees)
            if not isinstance(cases, frozenset):
                continue
            ecrits += [(Ecrit(c.valeur_avant, c.arguments, case_, c.valeur_apres[case_]), joueur)
                       for case_ in sorted(cases)]
        description = decrire_ecriture(ecrits)
        if description is None:
            return None
        resultat.append((partie, description))
    return resultat


def valeur_ecrite(description: tuple, avant: list, arguments: tuple, case_: int):
    """La valeur qu'écrit une partie décrite par ``description`` (``INDEFINI`` si elle ne la
    prévoit pas)."""
    sorte = description[0]
    if sorte == "constante":
        return description[1]
    if sorte == "argument":
        k = description[1]
        return arguments[k] if k < len(arguments) else INDEFINI
    if sorte == "programme":
        return evaluer(description[1], Ecrit(avant, tuple(arguments), case_, INDEFINI))
    if sorte == "selon":
        k, table = description[1], description[2]
        if k >= len(arguments):
            return INDEFINI
        choix = next((d for v, d in table if _cle(v) == _cle(arguments[k])), None)
        return INDEFINI if choix is None else valeur_ecrite(choix, avant, arguments, case_)
    return INDEFINI  # (« joueur » : la valeur dépend de qui joue, pas de l'état)


@dataclass(frozen=True)
class Condition:
    """Quand un coup est permis : tous les ``atomes`` sont vrais. Un atome est
    ``(comparaison, nie, terme, feuille)`` : ``inf`` (plus petit) ou ``egal``, éventuellement
    nié. Une comparaison qui n'a pas de sens (une case qui n'existe pas) est fausse. Sans
    atome : toujours permis (le programme suffit)."""

    atomes: tuple = ()

    def __repr__(self) -> str:
        if not self.atomes:
            return "toujours"
        return " et ".join(f"{'non ' if nie else ''}{cmp}({t!r}, {f!r})" for cmp, nie, t, f in self.atomes)

    def vraie(self, coup: Coup, portees: dict | None = None) -> bool:
        return all(_atome(a, coup, portees) for a in self.atomes)


def _comparable(v):
    """Une case seule se compare par son indice ; un ensemble vide ou plus grand n'a pas de rang."""
    if isinstance(v, frozenset):
        return next(iter(v)) if len(v) == 1 else INDEFINI
    return v


def _comparer(cmp: str, a, b) -> bool:
    a, b = _comparable(a), _comparable(b)
    if a is INDEFINI or b is INDEFINI:
        return False
    if cmp == "egal":
        return _cle(a) == _cle(b)
    return _est_nombre(a) and _est_nombre(b) and a < b


def _atome(atome: tuple, coup: Coup, portees: dict | None) -> bool:
    cmp, nie, terme, feuille = atome
    vrai = _comparer(cmp, evaluer(terme, coup, None, portees), evaluer(feuille, coup, None, portees))
    return vrai != nie


def _prevoir(hypothese: Hypothese, ecrits: list, avant, arguments: tuple, portees: dict | None):
    """``(suite, parties)`` : l'état prévu après le coup et ce qu'écrit chaque partie ; ``None``
    si ce n'est pas un coup (une partie n'a pas de sens, deux parties visent la même case, ou
    rien ne change)."""
    if not isinstance(avant, list):
        avant = list(avant)
    cas, suite, vues, faites = Cas(avant, tuple(arguments), None), list(avant), set(), []
    for partie, description in ecrits:
        cases = evaluer(partie, cas, None, portees)
        if not isinstance(cases, frozenset):
            return None
        for case_ in sorted(cases):
            valeur = valeur_ecrite(description, avant, arguments, case_)
            if case_ in vues or valeur is INDEFINI:
                return None
            vues.add(case_)
            suite[case_] = valeur
        faites.append((next(iter(cases)), avant[next(iter(cases))], suite[next(iter(cases))])
                      if len(cases) == 1 else (INDEFINI, INDEFINI, INDEFINI))
    if suite == avant:
        return None  # un coup change quelque chose
    return suite, tuple(faites)


def prevoir(hypothese: Hypothese, ecrits: list, avant, arguments: tuple, portees: dict | None = None,
            condition: Condition | None = None) -> tuple | None:
    """L'état prévu après le coup ``arguments`` (un tuple), ou ``None`` si ce n'est pas un coup
    permis."""
    prevu = _prevoir(hypothese, ecrits, avant, tuple(arguments), portees)
    if prevu is None:
        return None
    suite, faites = prevu
    if condition is not None and not condition.vraie(Coup(list(avant), tuple(arguments), faites), portees):
        return None
    return tuple(suite)


#: Une condition : chaque côté d'une comparaison a au plus cette taille ; l'un d'eux est une feuille.
MAX_TAILLE_CONDITION = MAX_TAILLE
#: Atomes essayés au plus, du plus petit au plus grand, pour former une condition à deux atomes.
MAX_ATOMES_PAIRES = 400


def liberte_valeurs(hypothese: Hypothese, ecrits: list, observations: list[Cas], portees: dict | None = None,
                    acceptes: list = ()) -> Condition | None:
    """Quand un coup est-il permis, quand ce que l'action écrit dépend des valeurs ? Déduit des
    coups joués et des coups refusés, comme :func:`liberte`.

    ``observations`` : les coups vus dans le labo (un coup refusé n'a rien changé) ;
    ``acceptes`` : des couples (état avant, arguments) de coups que le jeu a acceptés en
    finissant la partie. Pour chaque coup, la mère prévoit ce qu'il écrit (:func:`_prevoir`).
    Un coup refusé dont elle ne prévoit rien (rien ne changerait, une case qui n'existe pas,
    une division qui ne tombe pas juste) est déjà expliqué. Les autres doivent être écartés par
    la condition, qui doit rester vraie pour tous les coups acceptés.

    La condition se construit comme les programmes : des **comparaisons** (``inf`` : plus
    petit, ``egal``, éventuellement niées) entre un terme et une feuille (un argument, ``ici``,
    ``ecrit`` et ``cellule`` de chaque partie, une borne mesurée sur les coups acceptés),
    essayées de la plus petite à la plus grande ; une seule si elle suffit, sinon deux à la fois.
    Au Nim : ``non inf(ecrit, 0)`` (on ne prend pas plus qu'il n'y a). ``None`` si aucune ne
    convient : la condition est hors de portée de son langage, elle le dit.

    Ce qui est fourni à la main : les deux comparaisons et la négation, la forme « un terme
    contre une feuille », les sortes de bornes (la plus petite et la plus grande valeur vue),
    au plus deux comparaisons (:data:`MAX_TAILLE_CONDITION`, :data:`MAX_ATOMES_PAIRES`).
    """
    nb_parties = len(ecrits)
    acceptes_vus, refuses = {}, {}
    for c in observations:
        refuse = isinstance(c.valeur_avant, list) and c.valeur_apres == c.valeur_avant
        if not refuse and c.forme != CHANGEES:
            continue
        prevu = _prevoir(hypothese, ecrits, c.valeur_avant, c.arguments, portees)
        if refuse:
            if prevu is not None:
                refuses[_cle((c.valeur_avant, c.arguments))] = Coup(list(c.valeur_avant), c.arguments, prevu[1])
            continue
        if prevu is None or _cle(prevu[0]) != _cle(list(c.valeur_apres)):
            return None  # la description ne prévoit pas un coup que le jeu a joué
        acceptes_vus[_cle((c.valeur_avant, c.arguments))] = Coup(list(c.valeur_avant), c.arguments, prevu[1])
    for avant_, arguments in acceptes:
        prevu = _prevoir(hypothese, ecrits, avant_, tuple(arguments), portees)
        if prevu is None:
            return None
        acceptes_vus[_cle((avant_, tuple(arguments)))] = Coup(list(avant_), tuple(arguments), prevu[1])
    if not acceptes_vus:
        return None
    if not refuses:
        return Condition()
    oui, non_ = list(acceptes_vus.values()), list(refuses.values())
    coups = oui + non_
    nb_arguments = min(len(c.arguments) for c in coups)
    bornes = set()
    for p in range(nb_parties):
        for feuille in (ici(p), ecrit(p)):
            vues = [evaluer(feuille, c) for c in oui]
            vues = [v for v in vues if _est_nombre(v)]
            if vues:
                bornes |= {min(vues), max(vues)}
    feuilles = ([arg(k) for k in range(nb_arguments)]
                + [f(p) for p in range(nb_parties) for f in (ici, ecrit, cellule)]
                + [const(v) for v in sorted(bornes)])
    n_oui, tous = len(oui), (1 << len(non_)) - 1
    simples, atomes = [], []  # feuilles ; (taille, atome, écartés)
    seul, taille_vue = None, 0

    def preparer(valeurs) -> tuple:
        """Les valeurs prêtes à comparer (comme :func:`_comparer`) : nombres (``None`` sinon) et clés."""
        comparables = [_comparable(v) for v in valeurs]
        nombres = [v if type(v) in (int, float) else None for v in comparables]
        cles = [None if v is INDEFINI else _cle(v) for v in comparables]
        return nombres, cles

    def vrai(cmp, x, y) -> bool:
        if cmp == "inf":
            return x is not None and y is not None and x < y
        return x is not None and x == y

    def comparer(terme, prets, feuille, prets_f):
        for cmp, ordre in (("inf", 0), ("inf", 1), ("egal", 0)):
            if cmp == "egal" and terme.size == 1 and terme.id > feuille.id:
                continue  # egal est symétrique
            sorte = 0 if cmp == "inf" else 1
            a, b = (prets[sorte], prets_f[sorte]) if ordre == 0 else (prets_f[sorte], prets[sorte])
            premier = vrai(cmp, a[0], b[0])
            if not all(vrai(cmp, x, y) == premier for x, y in zip(a[1:n_oui], b[1:n_oui])):
                continue  # ni vrai ni faux sur tous les coups acceptés
            ecartes = sum(1 << i for i, (x, y) in enumerate(zip(a[n_oui:], b[n_oui:]))
                          if vrai(cmp, x, y) != premier)
            if ecartes:
                t1, t2 = (terme, feuille) if ordre == 0 else (feuille, terme)
                atomes.append((terme.size + 2 + (not premier), (cmp, not premier, t1, t2), ecartes))

    for terme, valeurs in termes(coups, nb_arguments, MAX_TAILLE_CONDITION, (), portees,
                                 OPERATIONS_CONDITION, feuilles):
        valeurs = preparer(valeurs)
        if terme.size > taille_vue:
            # une taille de plus : s'arrêter si une seule comparaison suffit déjà, ou si
            # assez d'atomes sont connus pour en chercher deux
            atomes.sort(key=lambda a: a[0])
            seul = next((a for a in atomes if a[2] == tous), None)
            if (seul is not None and seul[0] <= terme.size + 2) or len(atomes) >= MAX_ATOMES_PAIRES:
                break
            taille_vue = terme.size
        if terme.size == 1:
            simples.append((terme, valeurs))
        for feuille, valeurs_f in simples:
            if feuille is not terme:
                comparer(terme, valeurs, feuille, valeurs_f)
    atomes.sort(key=lambda a: a[0])
    seul = next((a for a in atomes if a[2] == tous), None)
    if seul is not None:
        return Condition((seul[1],))
    meilleure = None
    debut = atomes[:MAX_ATOMES_PAIRES]
    for i, (t1, a1, e1) in enumerate(debut):
        for t2, a2, e2 in debut[i + 1:]:
            if e1 | e2 == tous and (meilleure is None or t1 + t2 < meilleure[0]):
                meilleure = (t1 + t2, (a1, a2))
    return Condition(meilleure[1]) if meilleure else None


def liberte(hypothese: Hypothese, observations: list[Cas], depart: list,
            portees: dict | None = None, acceptes: list = ()) -> tuple | None:
    """Quand une case peut-elle recevoir l'action ? Déduit des coups joués et des coups refusés.

    ``observations`` : les coups vus dans le labo ; un coup refusé est un cas où
    rien n'a changé (``valeur_apres == valeur_avant``). ``depart`` : la position
    du début de la partie. La mère essaie, de la plus simple à la moins simple,
    les descriptions qu'elle connaît et garde la première qui convient : chaque
    case remplie la vérifiait juste avant, et aucune case que le programme
    annonçait pour un coup refusé ne la vérifiait.

    * ``("toujours",)`` : le programme suffit, il n'annonce aucune case pour un
      coup refusé (au Puissance 4, une colonne pleine) ;
    * ``("constante", v)`` : la case valait ``v``, toujours la même valeur ;
    * ``("depart",)`` : la case avait encore sa valeur du début de la partie (au
      Morpion, la case *n* contient « n » tant que personne n'y a joué).

    ``None`` si aucune ne convient (ou si aucune case n'a été remplie).

    Pour un nombre (forme ``apres``), voir :func:`bornes`.
    """
    if hypothese.forme == APRES:
        return bornes(hypothese, observations, acceptes)
    remplies, annoncees = [], []  # (état avant, case)
    for c in observations:
        if c.forme == CHANGEES and len(c.cible()) == 1:
            remplies.append((c.valeur_avant, next(iter(c.cible()))))
        elif c.forme is None and isinstance(c.valeur_avant, list) and c.valeur_apres == c.valeur_avant:
            cases = evaluer(hypothese.terme, Cas(c.valeur_avant, tuple(c.arguments), None), None, portees)
            if cases is not INDEFINI and len(cases) == 1:
                annoncees.append((c.valeur_avant, next(iter(cases))))
    if not remplies:
        return None
    etat, case_ = remplies[0]
    conditions = [(("toujours",), lambda e, c: True),
                  (("constante", etat[case_]), lambda e, c: _cle(e[c]) == _cle(etat[case_])),
                  (("depart",), lambda e, c: c < len(depart) and _cle(e[c]) == _cle(depart[c]))]
    for description, vraie in conditions:
        if all(vraie(e, c) for e, c in remplies) and not any(vraie(e, c) for e, c in annoncees):
            return description
    return None


def bornes(hypothese: Hypothese, observations: list[Cas], acceptes: list = ()) -> tuple | None:
    """Quand une action est-elle permise, pour un nombre ? Déduit des coups joués et refusés.

    Il n'y a pas de case à remplir : le programme annonce la valeur d'après. La
    mère regarde les valeurs d'après des coups que le jeu a acceptés (``observations``
    où la valeur a changé, et ``acceptes`` : des couples (valeur avant, arguments)
    de coups acceptés dont elle n'a pas relu la valeur, comme ceux qui finissent la
    partie : elle la calcule avec le programme), et celles que le programme annonçait
    pour les coups refusés (rien n'a changé). Elle essaie, de la plus simple à la
    moins simple, les descriptions qu'elle connaît et garde la première qui convient
    (toutes les valeurs acceptées la vérifient, aucune valeur refusée) :

    * ``("toujours",)`` : toute action est permise ;
    * ``("au_moins", m)`` : la valeur d'après ne descend pas sous ``m``, la plus
      petite qu'elle a vue (aux Allumettes : 0, on ne prend pas plus qu'il n'en
      reste) ;
    * ``("au_plus", m)`` : elle ne dépasse pas ``m``, la plus grande vue ;
    * ``("entre", m, n)`` : les deux.

    ``None`` si aucune ne convient (ou si aucun coup accepté n'a été vu).
    """
    def annoncee(avant, arguments):
        valeur = evaluer(hypothese.terme, Cas(avant, tuple(arguments), None))
        return valeur if _est_nombre(valeur) else None

    vues, refusees = [], []
    for c in observations:
        if c.forme == APRES and c.valeur_apres != c.valeur_avant:
            vues.append(c.valeur_apres)
        elif _est_nombre(c.valeur_avant) and c.valeur_apres == c.valeur_avant:
            refusees.append(annoncee(c.valeur_avant, c.arguments))
    vues += [annoncee(avant, arguments) for avant, arguments in acceptes]
    vues = [v for v in vues if v is not None]
    refusees = [v for v in refusees if v is not None]
    if not vues:
        return None
    bas, haut = min(vues), max(vues)
    conditions = [(("toujours",), lambda v: True),
                  (("au_moins", bas), lambda v: v >= bas),
                  (("au_plus", haut), lambda v: v <= haut),
                  (("entre", bas, haut), lambda v: bas <= v <= haut)]
    for description, vraie in conditions:
        if not any(vraie(v) for v in refusees):
            return description
    return None


def _cle(valeur):
    """Clé hachable et sans ambiguïté de type (``1`` et ``True`` diffèrent)."""
    if isinstance(valeur, (list, tuple)):
        return (type(valeur).__name__, tuple(_cle(v) for v in valeur))
    return (type(valeur).__name__, valeur) if valeur is not INDEFINI else ("indefini",)


def decouvrir(observations: list[Cas], max_taille: int = MAX_TAILLE, min_cas: int = MIN_CAS,
              portees: dict | None = None) -> list[Hypothese]:
    """Les plus petites hypothèses qui expliquent tous les cas (vide si aucune ou trop peu de cas).

    Les cas doivent tous avoir la même forme (voir :attr:`Cas.forme`) ; les
    doublons sont ignorés. ``portees`` : ce que la mère a vu chaque action
    remplir dans son labo (sans elles, ``portee`` n'est pas essayé).
    """
    uniques = {_cle((c.valeur_avant, c.arguments, c.valeur_apres)): c
               for c in observations if c.forme is not None}
    cas = list(uniques.values())
    formes = {c.forme for c in cas}
    if len(cas) < min_cas or len(formes) != 1:
        return []
    forme = formes.pop()
    cibles = tuple(_cle(c.cible()) for c in cas)
    nb_arguments = min(len(c.arguments) for c in cas)
    trouvees: list[Hypothese] = []
    for terme, valeurs in termes(cas, nb_arguments, max_taille, constantes(cas), portees):
        if trouvees and terme.size > trouvees[0].terme.size:
            break
        if tuple(_cle(v) for v in valeurs) == cibles:
            trouvees.append(Hypothese(forme, terme))
    if not trouvees and forme == CHANGEES:
        trouvees = ecrites(cas, max_taille, min_cas, portees)
    if not trouvees and forme == CHANGEES:
        # Aucun ensemble de cases changées ne s'explique : l'état a peut-être défilé.
        return defilements(cas, min_cas)
    return trouvees


#: Quatrième forme : les cases que l'action **écrit** (une case écrite peut garder sa valeur).
ECRITES = "ecrites"


def ecrites(cas: list[Cas], max_taille: int = MAX_TAILLE, min_cas: int = MIN_CAS,
            portees: dict | None = None) -> list[Hypothese]:
    """Quand aucun programme ne donne exactement les cases changées : les cases **écrites**.

    Une action peut écrire dans une case la valeur qu'elle avait déjà (au Compte est bon,
    5 × 1 laisse 5 à sa place, alors que l'autre place se vide). Les cases changées sont
    alors un sous-ensemble des cases écrites. La mère cherche le plus petit programme qui
    contient les cases changées de **tous** les cas et les donne exactement dans au moins la
    moitié d'entre eux (et dans ``min_cas`` cas au moins) : sinon « toutes les cases »
    expliquerait tout. C'est une hypothèse plus faible, que la description de la valeur écrite
    doit confirmer (:func:`ecritures`, :func:`prevoir` : l'état d'après prévu en entier)."""
    nb_arguments = min(len(c.arguments) for c in cas)
    cibles = [c.cible() for c in cas]
    trouvees: list[Hypothese] = []
    for terme, valeurs in termes(cas, nb_arguments, max_taille, constantes(cas), portees):
        if trouvees and terme.size > trouvees[0].terme.size:
            break
        if not all(isinstance(v, frozenset) and cible <= v for v, cible in zip(valeurs, cibles)):
            continue
        exacts = sum(v == cible for v, cible in zip(valeurs, cibles))
        if exacts >= min_cas and 2 * exacts >= len(cas):
            trouvees.append(Hypothese(ECRITES, terme))
    return trouvees


def explique(hypothese: Hypothese, cas: Cas, portees: dict | None = None) -> bool:
    """L'hypothèse prédit-elle ce qui s'est passé dans ``cas`` ?"""
    if isinstance(hypothese, Defilement):
        return hypothese.explique(cas)
    if hypothese.forme == ECRITES:
        valeur = evaluer(hypothese.terme, cas, None, portees)
        return cas.forme == CHANGEES and isinstance(valeur, frozenset) and cas.cible() <= valeur
    if cas.forme != hypothese.forme:
        return False
    return _cle(evaluer(hypothese.terme, cas, None, portees)) == _cle(cas.cible())


# ---------------------------------------------------------------------- #
# Un état qui défile : « l'état d'avant, décalé », sauf ce qu'elle ne prévoit pas
# ---------------------------------------------------------------------- #

#: Troisième forme : l'état d'après en entier, prévu case par case (``INDEFINI`` : pas prévu).
SUITE = "suite"


@dataclass(frozen=True)
class Defilement:
    """« ``suite = decale(avant, d)`` » : la case *i* reçoit ce qui était en *i* + *d*.

    Quand une action change beaucoup de cases à la fois (un bandeau qui défile,
    une file d'attente qui avance d'une place, un tapis roulant), le décrire par
    l'ensemble des cases changées n'explique rien. La mère le décrit comme l'état
    d'avant, décalé (c'est le décalage « chaque case + d » qu'elle essaie déjà sur
    ses motifs), **avec les exceptions qu'elle sait nommer**. La description est
    partielle et le dit :

    * ``entree`` : ce qui entre par le bord (les cases dont la source sort de
      l'état, et les ``|d|`` suivantes, où un objet qui entre a pu apparaître
      d'un coup) : imprévisible, elle ne voit pas au-delà du bord ;
    * ``mobile`` : une valeur présente exactement une fois dans chaque état vu
      (un curseur, un pion, un personnage) qui ne défile pas avec le reste ; sa
      place suivante n'est pas prévue, et ce qu'il cache non plus ;
    * ``fixes`` : les cases qui n'ont jamais changé et que le décalage
      contredirait (un décor immobile, un cadre) ;
    * ``mouvements`` : les déplacements du mobile qu'elle a vus, par argument de
      l'action ; si un même argument en a donné plusieurs, ce qui décide est
      caché (elle ne le prévoit pas).

    Sur ces cases, rien n'est prévu ; partout ailleurs, la prédiction doit être
    exacte dans **tous** les cas. Jumper n'est pas le seul problème : un texte
    qui défile sur un panneau, une file d'attente au guichet (chacun avance
    d'une place, un nouveau arrive au bout), un registre à décalage, une
    partition qui défile sous les yeux d'un musicien (``Games/Partition.py``).
    """

    d: int
    entree: tuple = ()
    mobile: object = None
    fixes: frozenset = frozenset()
    mouvements: tuple = ()     # (argument, déplacements vus du mobile)

    forme = SUITE

    def __repr__(self) -> str:
        sauf = []
        if self.entree:
            sauf.append(f"ce qui entre par le bord (cases {self.entree[0]} à {self.entree[-1]}, imprévisible)")
        if self.mobile is not None:
            vus = "; ".join(f"{a!r} -> {list(m)}" for a, m in self.mouvements)
            cache = any(len(m) > 1 for _, m in self.mouvements)
            sauf.append(f"le mobile {self.mobile!r}, qui ne défile pas (déplacements vus par argument : {vus}"
                        + (" ; ce qui les décide est caché" if cache else "") + ")")
        if self.fixes:
            sauf.append(f"{len(self.fixes)} case(s) fixe(s) {sorted(self.fixes)}")
        return f"suite = decale(avant, {self.d})" + (" sauf : " + ", ".join(sauf) if sauf else "")

    def prevoir(self, avant: list) -> tuple:
        """L'état d'après prévu case par case (``INDEFINI`` là où elle ne prévoit rien)."""
        n, prevu = len(avant), []
        for i in range(n):
            j = i + self.d
            if i in self.fixes:
                prevu.append(avant[i])
            elif i in self.entree or not 0 <= j < n or _egal(avant[j], self.mobile):
                prevu.append(INDEFINI)
            else:
                prevu.append(avant[j])
        return tuple(prevu)

    def ecarts(self, cas: Cas) -> list[int]:
        """Les cases prévues que le cas contredit (celles où se trouve le mobile ne comptent pas)."""
        avant, apres = cas.valeur_avant, cas.valeur_apres
        if not (isinstance(avant, list) and isinstance(apres, list) and len(avant) == len(apres)):
            return [-1]
        return [i for i, v in enumerate(self.prevoir(avant))
                if v is not INDEFINI and not _egal(apres[i], self.mobile) and _cle(v) != _cle(apres[i])]

    def explique(self, cas: Cas) -> bool:
        """Un cas où rien n'a changé (un écran qui défile sur du vide) s'explique aussi."""
        inchange = isinstance(cas.valeur_avant, list) and cas.valeur_avant == cas.valeur_apres
        return (cas.forme is not None or inchange) and not self.ecarts(cas)


def _egal(valeur, mobile) -> bool:
    return mobile is not None and _cle(valeur) == _cle(mobile)


def _mobile(etats: list[list]):
    """Une valeur présente exactement une fois dans chaque état (``None`` s'il n'y en a pas une seule)."""
    candidats = None
    for etat in etats:
        uniques = {_cle(v) for v in etat if sum(_cle(w) == _cle(v) for w in etat) == 1} \
            if len(etat) <= 64 else _uniques(etat)
        candidats = uniques if candidats is None else candidats & uniques
        if not candidats:
            return None
    if candidats is None or len(candidats) != 1:
        return None
    return next(iter(candidats))[1]


def _place(etat: list, valeur) -> int | None:
    return next((i for i, v in enumerate(etat) if _cle(v) == _cle(valeur)), None)


def _uniques(etat: list) -> set:
    compte = Counter(_cle(v) for v in etat)
    return {cle for cle, n in compte.items() if n == 1}


def defilements(observations: list[Cas], min_cas: int = MIN_CAS) -> list[Defilement]:
    """Les décalages qui expliquent tous les cas, à des exceptions nommées près (voir :class:`Defilement`).

    Le décalage *d* est mesuré sur les cas (le plus fréquent parmi ceux qui
    expliquent les cases changées : une **constante mesurée**, comme les écarts
    case − argument). Il doit expliquer au moins une case changée dans au moins
    ``min_cas`` cas, et plus de la moitié des cases changées qu'il prévoit ; tout
    ce qu'il ne prévoit pas doit être nommé (entrée par le bord, mobile, cases
    fixes), sinon il n'y a pas de description.
    """
    cas = [c for c in observations if c.forme == CHANGEES]
    if len(cas) < min_cas:
        return []
    n = len(cas[0].valeur_avant)
    if any(len(c.valeur_avant) != n for c in cas):
        return []
    etats = [c.valeur_avant for c in cas] + [c.valeur_apres for c in cas]
    mobile = _mobile(etats)
    votes = Counter()
    for c in cas:
        changees = [i for i in c.cible() if not _egal(c.valeur_apres[i], mobile)]
        for d in range(1 - n, n):
            if d and sum(0 <= i + d < n and _cle(c.valeur_apres[i]) == _cle(c.valeur_avant[i + d])
                         and not _egal(c.valeur_apres[i], mobile) for i in changees) * 2 > len(changees):
                votes[d] += 1
    trouves = []
    for d, _ in votes.most_common(3):
        # un mobile ne défile pas : une valeur unique qui suit toujours le décalage n'en est pas un
        suit = mobile is not None and all(
            _place(c.valeur_apres, mobile) == _place(c.valeur_avant, mobile) - d for c in cas)
        description = _defilement(cas, d, None if suit else mobile, etats, min_cas)
        if description is not None:
            trouves.append(description)
            break
    return trouves


def _defilement(cas: list[Cas], d: int, mobile, etats: list, min_cas: int) -> Defilement | None:
    n = len(cas[0].valeur_avant)
    if 4 * abs(d) > n:
        return None  # l'entrée par le bord en couvrirait plus de la moitié : ce n'est plus un défilement
    bord = list(range(n - d, n)) if d > 0 else list(range(0, -d))
    voisins = list(range(n - 2 * d, n - d)) if d > 0 else list(range(-d, -2 * d))
    brut = Defilement(d, tuple(sorted(bord)), mobile)
    constantes = {i for i in range(n) if len({_cle(e[i]) for e in etats}) == 1}
    fixes, entree, expliques, prevues, soutiens = set(), set(), 0, 0, 0
    for c in cas:
        for i in brut.ecarts(c):
            if i in voisins:
                entree.add(i)          # un objet qui entre a pu apparaître juste après le bord
            elif i in constantes:
                fixes.add(i)           # un décor immobile que le décalage contredirait
            else:
                return None            # une exception qu'elle ne sait pas nommer
        changees = [i for i in c.cible() if i not in bord and not _egal(c.valeur_apres[i], mobile)]
        bons = [i for i in changees if 0 <= i + d < n and not _egal(c.valeur_avant[i + d], mobile)
                and _cle(c.valeur_apres[i]) == _cle(c.valeur_avant[i + d])]
        expliques, prevues = expliques + len(bons), prevues + len(changees)
        soutiens += bool(bons)
    if soutiens < min_cas or expliques * 2 <= prevues:
        return None
    entree = sorted(set(bord) | (set(voisins) if entree else set()))
    mouvements = {}
    if mobile is not None:
        for c in cas:
            avant = [i for i, v in enumerate(c.valeur_avant) if _egal(v, mobile)]
            apres = [i for i, v in enumerate(c.valeur_apres) if _egal(v, mobile)]
            if len(avant) == 1 and len(apres) == 1:
                argument = c.arguments[0] if c.arguments else None
                mouvements.setdefault(argument, set()).add(apres[0] - avant[0])
    vus = tuple(sorted(((a, tuple(sorted(m))) for a, m in mouvements.items()), key=repr))
    return Defilement(d, tuple(entree), mobile, frozenset(fixes), vus)


# ---------------------------------------------------------------------- #
# Écrire une hypothèse en Python (pour le code du fils)
# ---------------------------------------------------------------------- #

def traduire(terme: Terme) -> str:
    """Le terme en expression Python, avec les variables ``avant``, ``args`` et ``PORTEES``.

    ``evaluer`` et l'expression donnent la même chose sur un cas où le terme
    est défini : ce que la mère a vérifié est exactement ce que le fils exécute.
    """
    kind, a = terme.kind, terme.args
    if kind == "arg":
        return f"args[{a[0]}]"
    if kind == "avant":
        return "avant"
    if kind == "const":
        return repr(a[0])
    if kind == "plus":
        return f"({traduire(a[0])} + {traduire(a[1])})"
    if kind == "moins":
        return f"({traduire(a[0])} - {traduire(a[1])})"
    if kind == "case":
        return f"{{{traduire(a[0])}}}"
    if kind == "valant":
        x = traduire(a[0])
        return f"{{i for i, v in enumerate(avant) if v == {x} or str(v) == str({x})}}"
    if kind == "union":
        return f"({traduire(a[0])} | {traduire(a[1])})"
    if kind == "portee":
        return f"tuple(PORTEES[{traduire(a[0])}])"
    if kind == "premiere_de":
        return f"next(({{c}} for c in {traduire(a[0])} if c in {traduire(a[1])}), set())"
    raise ValueError(kind)


#: Les briques en Python, recopiées dans le fils qui prévoit un coup (:func:`source_prevision`).
#: Chacune fait exactement ce que fait :func:`evaluer` ; un terme sans sens lève ``Indefini``.
AIDES_SOURCE = '''class Indefini(Exception):
    """Un terme qui n'a pas de sens sur ce coup (une case qui n'existe pas…)."""


INDEF = Indefini  # une valeur qui n'a pas de sens


def _cle(v):
    if isinstance(v, (list, tuple)):
        return (type(v).__name__, tuple(_cle(w) for w in v))
    return (type(v).__name__, v)


def _nombre(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise Indefini
    return x


def _entier(x):
    if isinstance(x, bool) or not isinstance(x, int):
        raise Indefini
    return x


def _indice(avant, x):
    if isinstance(x, bool) or not isinstance(x, int) or not 0 <= x < len(avant):
        raise Indefini
    return x


def _arg(args, k):
    if k >= len(args):
        raise Indefini
    return args[k]


def _plus(x, y):
    return _nombre(x) + _nombre(y)


def _moins(x, y):
    return _nombre(x) - _nombre(y)


def _fois(x, y):
    return _nombre(x) * _nombre(y)


def _divise(x, y):
    x, y = _entier(x), _entier(y)
    if y == 0 or x % y:
        raise Indefini
    return x // y


def _case(avant, x):
    return frozenset((_indice(avant, x),))


def _val(avant, x):
    return avant[_indice(avant, x)]


def _valant(avant, x):
    if isinstance(x, (frozenset, list, tuple)):
        raise Indefini
    return frozenset(i for i, v in enumerate(avant) if v == x or str(v) == str(x))


def _union(e, f):
    if not (isinstance(e, frozenset) and isinstance(f, frozenset)):
        raise Indefini
    return e | f


def _portee(portees, x, k=None):
    if isinstance(x, (frozenset, list, tuple)):
        raise Indefini
    try:
        suite = portees.get((k, x)) if k is not None else None
        if suite is None:
            suite = portees.get(x)
    except TypeError:
        raise Indefini
    if suite is None:
        raise Indefini
    return tuple(suite)


def _premiere(s, e):
    if not (isinstance(s, tuple) and isinstance(e, frozenset)):
        raise Indefini
    return next((frozenset((c,)) for c in s if c in e), frozenset())


def _partie(parties, p, i):
    if p >= len(parties) or parties[p][i] is INDEF:
        raise Indefini
    return parties[p][i]


def _rang(v):
    if isinstance(v, frozenset):
        if len(v) != 1:
            raise Indefini
        return next(iter(v))
    return v


def _inf(x, y):
    x, y = _rang(x), _rang(y)
    nombres = all(not isinstance(v, bool) and isinstance(v, (int, float)) for v in (x, y))
    return nombres and x < y


def _egal(x, y):
    return _cle(_rang(x)) == _cle(_rang(y))
'''


def python(terme: Terme) -> str:
    """Le terme en Python, avec les briques de :data:`AIDES_SOURCE` (variables ``avant``,
    ``args``, ``parties`` et ``PORTEES``)."""
    kind, a = terme.kind, terme.args
    if kind == "arg":
        return f"_arg(args, {a[0]})"
    if kind == "avant":
        return "avant"
    if kind == "const":
        return repr(a[0])
    if kind in ("plus", "moins", "fois", "divise"):
        return f"_{kind}({python(a[0])}, {python(a[1])})"
    if kind in ("case", "valant", "val"):
        return f"_{kind}(avant, {python(a[0])})"
    if kind == "union":
        return f"_union({python(a[0])}, {python(a[1])})"
    if kind == "portee":
        k = a[0].args[0] if a[0].kind == "arg" else None
        return f"_portee(PORTEES, {python(a[0])}, {k!r})"
    if kind == "premiere_de":
        return f"_premiere({python(a[0])}, {python(a[1])})"
    if kind in ("ici", "ecrit", "cellule"):
        return f"_partie(parties, {a[0]}, {('cellule', 'ici', 'ecrit').index(kind)})"
    raise ValueError(kind)


def _ecriture_python(description: tuple, retrait: str = "    ") -> str:
    sorte = description[0]
    if sorte == "constante":
        return f"{retrait}return {description[1]!r}\n"
    if sorte == "argument":
        return f"{retrait}return _arg(args, {description[1]})\n"
    if sorte == "programme":
        return f"{retrait}return {python(description[1])}\n"
    if sorte == "selon":
        texte = f"{retrait}choix = _cle(_arg(args, {description[1]}))\n"
        for valeur, sous in description[2]:
            texte += f"{retrait}if choix == _cle({valeur!r}):\n" + _ecriture_python(sous, retrait + "    ")
        return texte + f"{retrait}raise Indefini  # une valeur que la mère n'a pas assez vue\n"
    return f"{retrait}raise Indefini  # {description!r} : pas une valeur de l'état\n"


def decrire_ecritures(ecrits: list) -> str:
    """Ce qu'écrit chaque partie, en une ligne."""
    def dire(d: tuple) -> str:
        if d[0] == "selon":
            return f"selon arg{d[1]} : " + ", ".join(f"{v!r} -> {dire(s)}" for v, s in d[2])
        return repr(d[1]) if d[0] in ("constante", "programme") else f"arg{d[1]}" if d[0] == "argument" else d[0]
    return " ; ".join(f"{partie!r} reçoit {dire(d)}" for partie, d in ecrits)


def source_prevision(hypothese: Hypothese, ecrits: list, condition: Condition) -> str:
    """``valeur_apres(avant, args)`` en Python : l'état prévu après le coup, ``None`` si ce n'est
    pas un coup permis. Ce que la mère a vérifié (:func:`prevoir`) est ce que le fils exécute."""
    morceaux = []
    for p, (partie, description) in enumerate(ecrits):
        morceaux.append(f"def _partie_{p}(avant, args):\n    return {python(partie)}\n")
        morceaux.append(f"def _ecrit_{p}(avant, args, parties):\n" + _ecriture_python(description))
    for i, (cmp, nie, t1, t2) in enumerate(condition.atomes):
        morceaux.append(f"def _atome_{i}(avant, args, parties):\n"
                        f"    try:\n        vrai = _{cmp}({python(t1)}, {python(t2)})\n"
                        f"    except Indefini:\n        vrai = False\n"
                        f"    return {'not vrai' if nie else 'vrai'}\n")
    atomes = " and ".join(f"_atome_{i}(avant, args, parties)" for i in range(len(condition.atomes))) or "True"
    liste = ", ".join(f"(_partie_{p}, _ecrit_{p})" for p in range(len(ecrits)))
    morceaux.append(f'''PARTIES = [{liste}]


def permis(avant, args, parties):
    """Quand un coup est permis : {condition!r} (déduit des coups joués et refusés)."""
    return {atomes}


def valeur_apres(avant, args):
    """L'état prévu après le coup ({hypothese!r} ; {decrire_ecritures(ecrits)}).
    None si ce n'est pas un coup permis (rien ne change, ou il n'a pas de sens)."""
    avant = list(avant)
    suite, vues, faites = list(avant), set(), []
    try:
        for partie, ecrire in PARTIES:
            cases = partie(avant, args)
            if not isinstance(cases, frozenset):
                raise Indefini
            for case in sorted(cases):
                if case in vues:
                    raise Indefini
                vues.add(case)
                suite[case] = ecrire(avant, args, ((case, avant[case], INDEF),))
            un = next(iter(cases)) if len(cases) == 1 else None
            faites.append((un, avant[un], suite[un]) if un is not None else (INDEF, INDEF, INDEF))
    except Indefini:
        return None
    if suite == avant or not permis(avant, tuple(args), tuple(faites)):
        return None
    return tuple(suite)
''')
    return "\n\n".join(morceaux)


def source(hypothese: Hypothese) -> str:
    """La fonction Python ``changees(avant, args)`` ou ``valeur_apres(avant, args)``."""
    nom = "changees" if hypothese.forme == CHANGEES else "valeur_apres"
    quoi = "les cases qui changent" if hypothese.forme == CHANGEES else "la nouvelle valeur"
    return (f"def {nom}(avant, args):\n"
            f'    """{quoi.capitalize()} : {hypothese!r} (trouvé par la mère)."""\n'
            f"    return {traduire(hypothese.terme)}\n")


# ---------------------------------------------------------------------- #
# Mettre les hypothèses à l'épreuve (expériences dans le labo)
# ---------------------------------------------------------------------- #

def predictions(hypotheses: list[Hypothese], valeur_avant, arguments: tuple,
                portees: dict | None = None) -> list:
    """Ce que chaque hypothèse annonce si l'on joue ``arguments`` sur ``valeur_avant``."""
    cas = Cas(valeur_avant, tuple(arguments), None)
    return [_cle(h.prevoir(valeur_avant)) if isinstance(h, Defilement)
            else _cle(evaluer(h.terme, cas, None, portees)) for h in hypotheses]


def decisive(hypotheses: list[Hypothese], valeur_avant, arguments: tuple,
             portees: dict | None = None) -> bool:
    """L'expérience départage-t-elle des hypothèses (elles n'annoncent pas toutes la même chose) ?"""
    if len(hypotheses) < 2:
        return False  # une hypothèse seule ne se départage de rien
    return len(set(predictions(hypotheses, valeur_avant, arguments, portees))) > 1


def departager(hypotheses: list[Hypothese], cas: Cas, portees: dict | None = None) -> list[Hypothese]:
    """Les hypothèses que le résultat de l'expérience ne contredit pas.

    Un cas où il n'y a rien à expliquer (coup refusé, fin de partie) ne
    contredit personne.
    """
    if cas.forme is None:
        return list(hypotheses)
    return [h for h in hypotheses if explique(h, cas, portees)]
