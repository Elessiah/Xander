"""Les briques avec lesquelles la mère construit ses propres concepts.

Un concept est un **arbre** (une structure Python, pas du texte) qui décrit une
position du point de vue d'un joueur (« moi »). Il s'écrit uniquement avec les
quatre notions que la mère apprend pour chaque jeu (``possibles``, ``apres``,
``gagne``, ``adversaire``) et quatre sortes de nœuds :

* ``Brique(nom, J)`` : une brique déjà connue, vue du côté de ``J`` (moi ou
  lui). Au départ, la seule brique est ``gagne`` ; chaque concept que la mère
  trouve devient une nouvelle brique (composition) ;
* ``Non(x)`` ;
* ``Et(x, y)`` ;
* ``AuMoins(k, J, x)`` : au moins ``k`` actions de ``J`` (k vaut 1 ou 2)
  mènent à une position où ``x`` est vrai.

Une **règle** se lit « jouer une action après laquelle le concept est vrai ».
Une règle qui accepte toutes les actions ne choisit rien : elle est ignorée.

Exemples (que la mère doit trouver seule, ils ne sont écrits nulle part) :
« jouer là où je gagne » est ``Brique(gagne, moi)`` ; « jouer là où il n'a plus
de coup gagnant » est ``Non(AuMoins(1, lui, Brique(gagne, lui)))``.

Ce qui est fourni à la main : ces quatre sortes de nœuds, les valeurs 1 et 2
de ``k``, et les bornes de la recherche (taille et profondeur des arbres).

La mère énumère les arbres par taille croissante. Deux arbres qui disent la
même chose sur un échantillon de positions sont confondus (on garde le plus
petit), comme on ne retient qu'un mot pour une idée.
"""

from __future__ import annotations

import random

MOI, LUI = "moi", "lui"
GAGNE = "gagne"


class Concept:
    """Nœud d'un arbre de concept. Les nœuds sont uniques (internés) : ``is`` suffit."""

    __slots__ = ("kind", "args", "id", "size", "depth")
    _table: dict = {}

    def __new__(cls, kind, *args, depth_of=None):
        key = (kind, depth_of) + tuple(a.id if isinstance(a, Concept) else a for a in args)
        node = cls._table.get(key)
        if node is None:
            node = object.__new__(cls)
            node.kind, node.args, node.id = kind, args, len(cls._table)
            children = [a for a in args if isinstance(a, Concept)]
            node.size = 1 + sum(c.size for c in children)
            if kind == "brique":
                node.depth = depth_of or 0
            else:
                node.depth = max((c.depth for c in children), default=0) + (kind == "au_moins")
            cls._table[key] = node
        return node

    def __repr__(self) -> str:
        if self.kind == "brique":
            return f"{self.args[0]}({self.args[1]})"
        if self.kind == "non":
            return f"Non({self.args[0]!r})"
        if self.kind == "et":
            return f"Et({self.args[0]!r}, {self.args[1]!r})"
        k, joueur, x = self.args
        return f"AuMoins({k}, {joueur}, {x!r})"


def brique(nom: str, joueur: str, depth: int = 0) -> Concept:
    return Concept("brique", nom, joueur, depth_of=depth)


def non(x: Concept) -> Concept:
    return Concept("non", x)


def et(x: Concept, y: Concept) -> Concept:
    return Concept("et", *sorted((x, y), key=lambda c: c.id))


def au_moins(k: int, joueur: str, x: Concept) -> Concept:
    return Concept("au_moins", k, joueur, x)


# ---------------------------------------------------------------------- #
# Évaluer un concept avec les quatre notions
# ---------------------------------------------------------------------- #

def _key(etat):
    return tuple(etat) if isinstance(etat, list) else etat


class Pensee:
    """Évalue des concepts sur des positions, avec les quatre notions d'un jeu.

    Les positions déjà regardées sont mémorisées : c'est la mère qui pense, pas
    le fils (lui exécute son code sans mémoire et compte ce qu'il regarde).
    """

    def __init__(self, notions, definitions: dict[str, Concept] | None = None):
        self.notions = notions
        self.definitions = definitions if definitions is not None else {}
        self._memo: dict = {}
        self._enfants: dict = {}
        self._gagne: dict = {}
        self._choix: dict = {}

    def enfants(self, etat, joueur) -> list:
        cle = (etat, joueur)
        if cle not in self._enfants:
            n = self.notions
            self._enfants[cle] = [(a, _key(n.apres(etat, a, joueur))) for a in n.possibles(etat)]
        return self._enfants[cle]

    def gagne(self, etat, joueur) -> bool:
        cle = (etat, joueur)
        if cle not in self._gagne:
            self._gagne[cle] = bool(self.notions.gagne(etat, joueur))
        return self._gagne[cle]

    def vrai(self, concept: Concept, etat, moi) -> bool:
        etat = _key(etat)
        cle = (concept.id, etat, moi)
        if cle in self._memo:
            return self._memo[cle]
        kind, args = concept.kind, concept.args
        if kind == "brique":
            nom, qui = args
            joueur = moi if qui == MOI else self.notions.adversaire(moi)
            valeur = self.gagne(etat, joueur) if nom == GAGNE else self.vrai(self.definitions[nom], etat, joueur)
        elif kind == "non":
            valeur = not self.vrai(args[0], etat, moi)
        elif kind == "et":
            valeur = self.vrai(args[0], etat, moi) and self.vrai(args[1], etat, moi)
        else:
            k, qui, x = args
            joueur = moi if qui == MOI else self.notions.adversaire(moi)
            compte = 0
            for _, suite in self.enfants(etat, joueur):
                if self.vrai(x, suite, moi):
                    compte += 1
                    if compte >= k:
                        break
            valeur = compte >= k
        self._memo[cle] = valeur
        return valeur

    def coups(self, concept: Concept, etat, moi) -> set:
        """La règle : les actions après lesquelles le concept est vrai."""
        return {a for a, suite in self.enfants(_key(etat), moi) if self.vrai(concept, suite, moi)}

    def choix(self, regle: Concept, etat, moi) -> set:
        """Les coups proposés par la règle ; vide si elle n'en écarte aucun (elle ne choisit rien)."""
        etat = _key(etat)
        cle = (regle.id, etat, moi)
        if cle not in self._choix:
            coups = self.coups(regle, etat, moi)
            self._choix[cle] = coups if len(coups) < len(self.enfants(etat, moi)) else set()
        return self._choix[cle]


# ---------------------------------------------------------------------- #
# Énumérer les concepts par taille
# ---------------------------------------------------------------------- #

def echantillon(notions, depart, joueurs, nombre: int = 120, graine: int = 0) -> list[tuple]:
    """Des positions imaginées par la mère (parties au hasard avec ``apres``), vues des deux côtés."""
    rng = random.Random(graine)
    vues, resultat = set(), []
    for _ in range(nombre * 4):
        etat, trait = _key(depart), 0
        while len(resultat) < nombre:
            for moi in joueurs:
                if (etat, moi) not in vues:
                    vues.add((etat, moi))
                    resultat.append((etat, moi))
            actions = notions.possibles(etat)
            if not actions or any(notions.gagne(etat, j) for j in joueurs):
                break
            etat = _key(notions.apres(etat, rng.choice(actions), joueurs[trait]))
            trait = 1 - trait
        if len(resultat) >= nombre:
            break
    return resultat


def enumerer(pensee: Pensee, positions: list[tuple], taille_max: int = 5,
             profondeur_max: int = 2) -> list[Concept]:
    """Les concepts distincts, du plus petit au plus grand.

    Un concept qui dit la même chose qu'un plus petit sur ``positions``, ou qui
    y est toujours vrai (ou toujours faux), n'est pas gardé.
    """
    par_taille: dict[int, list[Concept]] = {t: [] for t in range(1, taille_max + 1)}
    signatures = set()

    def essayer(c: Concept) -> None:
        if c.size > taille_max or c.depth > profondeur_max:
            return
        signature = tuple(pensee.vrai(c, etat, moi) for etat, moi in positions)
        if signature in signatures or all(signature) or not any(signature):
            return
        signatures.add(signature)
        par_taille[c.size].append(c)

    for nom in [GAGNE] + list(pensee.definitions):
        profondeur = 0 if nom == GAGNE else pensee.definitions[nom].depth
        for qui in (MOI, LUI):
            essayer(brique(nom, qui, profondeur))
    for taille in range(2, taille_max + 1):
        for x in par_taille[taille - 1]:
            essayer(non(x))
            for k in (1, 2):
                for qui in (MOI, LUI):
                    essayer(au_moins(k, qui, x))
        for gauche in range(1, (taille - 1) // 2 + 1):
            droite = taille - 1 - gauche
            for i, x in enumerate(par_taille[gauche]):
                autres = par_taille[droite][i + 1:] if gauche == droite else par_taille[droite]
                for y in autres:
                    essayer(et(x, y))
    return [c for t in range(1, taille_max + 1) for c in par_taille[t]]


# ---------------------------------------------------------------------- #
# Dire et écrire un concept
# ---------------------------------------------------------------------- #

def decrire(c: Concept, vrai: bool = True) -> str:
    """Le concept en français, du point de vue de « moi » (``vrai=False`` : sa négation).

    Les négations sont poussées vers les feuilles (« pas (a et b) » se dit
    « pas a ou pas b ») : la description change, pas le concept.
    """
    kind, args = c.kind, c.args
    if kind == "non":
        return decrire(args[0], not vrai)
    if kind == "brique":
        nom, qui = args
        if nom == GAGNE:
            if qui == MOI:
                return "j'ai gagné" if vrai else "je n'ai pas gagné"
            return "il a gagné" if vrai else "il n'a pas gagné"
        return f"{nom}({qui})" if vrai else f"pas {nom}({qui})"
    if kind == "et":
        parts = []
        for x in args:
            texte = decrire(x, vrai)
            nested = x.kind == "et" or (x.kind == "non" and x.args[0].kind == "et")
            parts.append(f"({texte})" if nested else texte)
        return f" {'et' if vrai else 'ou'} ".join(parts)
    k, qui, x = args
    mes = "mes" if qui == MOI else "ses"
    if k == 1:
        if vrai:
            return f"un de {mes} coups donne « {decrire(x)} »"
        return f"aucun de {mes} coups ne donne « {decrire(x)} »"
    if vrai:
        return f"au moins {k} de {mes} coups donnent « {decrire(x)} »"
    return f"au plus {k - 1} de {mes} coups donne{'nt' if k > 2 else ''} « {decrire(x)} »"


def decrire_regle(c: Concept) -> str:
    return f"jouer un coup après lequel {decrire(c)}"


def expression(c: Concept, etat: str = "etat", niveau: int = 0) -> str:
    """Le concept en Python, avec les quatre notions (``moi`` et ``lui`` sont des variables)."""
    kind, args = c.kind, c.args
    if kind == "brique":
        nom, qui = args
        return f"{nom}({etat}, {qui})"
    if kind == "non":
        return f"not ({expression(args[0], etat, niveau)})"
    if kind == "et":
        return f"({expression(args[0], etat, niveau)}) and ({expression(args[1], etat, niveau)})"
    k, qui, x = args
    suite = f"e{niveau + 1}"
    return f"au_moins({k}, {etat}, {qui}, lambda {suite}: {expression(x, suite, niveau + 1)})"


AU_MOINS_SOURCE = '''def au_moins(k, etat, joueur, propriete):
    """Au moins k actions de joueur mènent à une position qui a la propriété."""
    compte = 0
    for action in possibles(etat):
        if propriete(apres(etat, action, joueur)):
            compte += 1
            if compte >= k:
                return True
    return False
'''


def source(nom: str, c: Concept) -> str:
    """Le texte d'un concept tel que la mère l'écrit dans le code du fils."""
    return (f"def {nom}(etat, moi):\n"
            f'    """{decrire(c)}."""\n'
            f"    lui = adversaire(moi)\n"
            f"    return {expression(c)}\n")


def dependances(noms: list[str], definitions: dict[str, Concept]) -> list[str]:
    """Les briques nécessaires à ces concepts, chaque brique avant ceux qui l'utilisent."""
    ordre: list[str] = []

    def visiter(c: Concept) -> None:
        if c.kind == "brique":
            nom = c.args[0]
            if nom != GAGNE and nom not in ordre:
                visiter(definitions[nom])
                ordre.append(nom)
        else:
            for a in c.args:
                if isinstance(a, Concept):
                    visiter(a)

    for nom in noms:
        visiter(brique(nom, MOI, definitions[nom].depth))
    return ordre
