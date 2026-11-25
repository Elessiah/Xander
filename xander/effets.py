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


def _portee(portees: dict | None, x):
    """La portée observée de l'action ``x`` (une suite de cases), ``INDEFINI`` si elle est inconnue."""
    try:
        suite = (portees or {}).get(x)
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
        return _portee(portees, x)
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
COMMUTATIVES = (plus, union)


def _compositions(total: int, parts: int):
    """Les façons d'écrire ``total`` comme somme ordonnée de ``parts`` entiers positifs."""
    if parts == 1:
        yield (total,)
        return
    for first in range(1, total - parts + 2):
        for rest in _compositions(total - first, parts - 1):
            yield (first,) + rest


def termes(cas: list[Cas], nb_arguments: int, max_taille: int = MAX_TAILLE, constants: tuple = (),
           portees: dict | None = None):
    """Énumère les termes par taille croissante, avec leurs valeurs sur ``cas``.

    Renvoie ``(terme, valeurs)``. Un terme qui donne les mêmes valeurs qu'un
    terme plus petit n'est pas renvoyé ; un terme de même taille l'est (il
    coexiste) mais ne sert pas à en construire d'autres. Sans ``portees``, les
    termes ``portee`` ne sont pas essayés.
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

    operations = [(op, n) for op, n in OPERATIONS if portees or op is not portee]
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
                    if operation in (moins, union) and enfants[0] is enfants[1]:
                        continue  # x - x et x ∪ x n'apprennent rien
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
    """
    vues: dict = {}        # action -> cases, dans l'ordre où elles ont été vues
    remplissages = []      # (action, case remplie, état avant)
    for c in observations:
        if c.forme != CHANGEES or len(c.arguments) != 1:
            continue
        changees = c.cible()
        if len(changees) != 1:
            continue
        (case_,) = changees
        a = c.arguments[0]
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
    return trouvees


def explique(hypothese: Hypothese, cas: Cas, portees: dict | None = None) -> bool:
    """L'hypothèse prédit-elle ce qui s'est passé dans ``cas`` ?"""
    if cas.forme != hypothese.forme:
        return False
    return _cle(evaluer(hypothese.terme, cas, None, portees)) == _cle(cas.cible())


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
    return [_cle(evaluer(h.terme, cas, None, portees)) for h in hypotheses]


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
