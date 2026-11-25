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

* les feuilles ``arg(k)`` (le k-ième argument de l'appel) et ``avant`` (la
  valeur d'avant) ;
* ``plus(x, y)`` et ``moins(x, y)`` sur des nombres ;
* ``case(x)`` : la case d'indice ``x`` ; ``valant(x)`` : les cases dont la
  valeur est ``x`` (ou s'écrit comme ``x``) ; ``union(e, f)`` de deux ensembles
  de cases.

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
case(arg1))``.

Ce qui est fourni à la main : les deux formes, les feuilles, les cinq
opérations ci-dessus, la taille maximale des termes (:data:`MAX_TAILLE`) et le
nombre minimal de cas (:data:`MIN_CAS`).
"""

from __future__ import annotations

from dataclasses import dataclass

#: Taille maximale d'un terme (nombre de nœuds).
MAX_TAILLE = 5
#: Nombre minimal de cas distincts pour qu'une hypothèse soit retenue.
MIN_CAS = 2

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
        key = (kind,) + tuple(a.id if isinstance(a, Terme) else a for a in args)
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
        return f"{self.kind}({', '.join(map(repr, self.args))})"


def arg(k: int) -> Terme:
    return Terme("arg", k)


def avant() -> Terme:
    return Terme("avant")


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


def _est_indice(valeur, tableau) -> bool:
    return (isinstance(valeur, int) and not isinstance(valeur, bool)
            and isinstance(tableau, list) and 0 <= valeur < len(tableau))


def evaluer(terme: Terme, cas: Cas, enfants: tuple = None):
    """Valeur de ``terme`` sur ``cas`` (``enfants`` : valeurs déjà calculées des sous-termes)."""
    if enfants is None:
        enfants = tuple(evaluer(a, cas) for a in terme.args if isinstance(a, Terme))
    if any(v is INDEFINI for v in enfants):
        return INDEFINI
    kind, tableau = terme.kind, cas.valeur_avant
    if kind == "arg":
        k = terme.args[0]
        return cas.arguments[k] if k < len(cas.arguments) else INDEFINI
    if kind == "avant":
        return tableau
    if kind in ("plus", "moins"):
        x, y = enfants
        if not (_est_nombre(x) and _est_nombre(y)):
            return INDEFINI
        return x + y if kind == "plus" else x - y
    if kind == "case":
        (x,) = enfants
        return frozenset((x,)) if _est_indice(x, tableau) else INDEFINI
    if kind == "valant":
        (x,) = enfants
        if not isinstance(tableau, list) or isinstance(x, (frozenset, list)):
            return INDEFINI
        return frozenset(i for i, v in enumerate(tableau) if v == x or str(v) == str(x))
    if kind == "union":
        e, f = enfants
        return e | f if isinstance(e, frozenset) and isinstance(f, frozenset) else INDEFINI
    raise ValueError(kind)


# ---------------------------------------------------------------------- #
# Découvrir les hypothèses
# ---------------------------------------------------------------------- #

UNAIRES = (case, valant)
BINAIRES = (plus, moins, union)


def termes(cas: list[Cas], nb_arguments: int, max_taille: int = MAX_TAILLE):
    """Énumère les termes par taille croissante, avec leurs valeurs sur ``cas``.

    Renvoie ``(terme, valeurs)``. Un terme qui donne les mêmes valeurs qu'un
    terme plus petit n'est pas renvoyé ; un terme de même taille l'est (il
    coexiste) mais ne sert pas à en construire d'autres.
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

    def construire(terme: Terme, *enfants):
        valeurs = tuple(evaluer(terme, c, tuple(e[i] for e in enfants)) for i, c in enumerate(cas))
        return proposer(terme, valeurs)

    feuilles = [arg(k) for k in range(nb_arguments)] + [avant()]
    for feuille in feuilles:
        trouve = construire(feuille)
        if trouve:
            yield trouve
    for taille in range(2, max_taille + 1):
        for operation in UNAIRES:
            for terme, valeurs in list(par_taille.get(taille - 1, [])):
                trouve = construire(operation(terme), valeurs)
                if trouve:
                    yield trouve
        for operation in BINAIRES:
            for gauche in range(1, taille - 1):
                droite = taille - 1 - gauche
                for x, vx in list(par_taille.get(gauche, [])):
                    for y, vy in list(par_taille.get(droite, [])):
                        if operation is not moins and x.id > y.id:
                            continue  # commutatif : un seul ordre
                        if x is y and operation is not plus:
                            continue  # x - x et x ∪ x n'apprennent rien
                        terme = operation(x, y)
                        if terme.size != taille:
                            continue
                        enfants = (vx, vy) if terme.args[0] is x else (vy, vx)
                        trouve = construire(terme, *enfants)
                        if trouve:
                            yield trouve


def _cle(valeur):
    """Clé hachable et sans ambiguïté de type (``1`` et ``True`` diffèrent)."""
    if isinstance(valeur, (list, tuple)):
        return (type(valeur).__name__, tuple(_cle(v) for v in valeur))
    return (type(valeur).__name__, valeur) if valeur is not INDEFINI else ("indefini",)


def decouvrir(observations: list[Cas], max_taille: int = MAX_TAILLE,
              min_cas: int = MIN_CAS) -> list[Hypothese]:
    """Les plus petites hypothèses qui expliquent tous les cas (vide si aucune ou trop peu de cas).

    Les cas doivent tous avoir la même forme (voir :attr:`Cas.forme`) ; les
    doublons sont ignorés.
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
    for terme, valeurs in termes(cas, nb_arguments, max_taille):
        if trouvees and terme.size > trouvees[0].terme.size:
            break
        if tuple(_cle(v) for v in valeurs) == cibles:
            trouvees.append(Hypothese(forme, terme))
    return trouvees


def explique(hypothese: Hypothese, cas: Cas) -> bool:
    """L'hypothèse prédit-elle ce qui s'est passé dans ``cas`` ?"""
    if cas.forme != hypothese.forme:
        return False
    return _cle(evaluer(hypothese.terme, cas)) == _cle(cas.cible())
