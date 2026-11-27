"""Les briques avec lesquelles la mère construit ses propres concepts.

Un concept est un **arbre** (une structure Python, pas du texte) qui décrit une
position du point de vue d'un joueur (« moi »). Il s'écrit uniquement avec les
quatre notions que la mère apprend pour chaque jeu (``possibles``, ``apres``,
``gagne``, ``suivant``) et quatre sortes de nœuds :

* ``Brique(nom, J)`` : une brique déjà connue, vue du côté de ``J``. Au départ,
  la seule brique est ``gagne`` ; chaque concept que la mère trouve devient une
  nouvelle brique (composition) ;
* ``Non(x)`` ;
* ``Et(x, y)`` ;
* ``AuMoins(k, J, x)`` : au moins ``k`` actions de ``J`` mènent à une position
  où ``x`` est vrai. Par défaut k vaut 1 (« il existe ») : avec 1 et 2, la
  mère apprend à peine mieux, avec 1, 2 et 3 elle apprend moins bien (plus de
  coïncidences).

**Les joueurs.** ``J`` désigne un joueur par sa place dans l'ordre du jeu, à
partir de « moi » : ``moi``, ``lui`` (le suivant, ``suivant(moi)``), ``lui2``
(le suivant du suivant), et ainsi de suite jusqu'au nombre de joueurs que la
mère a vus jouer dans l'exemple. À deux, il n'y a que ``moi`` et ``lui`` : le
suivant est l'adversaire. À trois, une parade peut dire **qui** elle pare : le
suivant, qui joue juste après moi, ou ``lui2``, qui joue après lui.

Une **règle** se lit « jouer une action après laquelle le concept est vrai ».
Une règle qui accepte toutes les actions ne choisit rien : elle est ignorée. Une règle propose,
elle ne tranche pas seule : elle écarte des coups, et la suivante choisit parmi ceux qui restent
(:meth:`Pensee.decision`).

Exemples (que la mère doit trouver seule, ils ne sont écrits nulle part) :
« jouer là où je gagne » est ``Brique(gagne, moi)`` ; « jouer là où il n'a plus
de coup gagnant » est ``Non(AuMoins(1, lui, Brique(gagne, lui)))``.

Ce qui est fourni à la main : ces quatre sortes de nœuds, les valeurs de
``k``, la façon de désigner un joueur (par sa place après moi, avec
``suivant``) et les bornes de la recherche (taille et profondeur des arbres).

La mère énumère les arbres par taille croissante. Deux arbres qui disent la
même chose sur un échantillon de positions sont confondus (on garde le plus
petit), comme on ne retient qu'un mot pour une idée.
"""

from __future__ import annotations

import random

MOI, LUI = "moi", "lui"
GAGNE = "gagne"
#: Ce que le joueur **voit** sans rien imaginer, dans un jeu dont la fin est un motif de cases :
#: une menace (une de ses constructions n'attend plus qu'une case, et cette case est jouable) et
#: une double menace (deux cases jouables différentes qui en complètent chacune une). Ce sont des
#: briques de départ, comme ``gagne``, quand la perception du jeu les fournit
#: (:func:`xander.son_writer.constructions_source`) ; la mère ne garde, entre deux concepts qui
#: disent la même chose sur ses positions, que le plus petit : une menace reconnue (un nœud)
#: remplace « un de ses coups donne « il a gagné » » (deux nœuds, un coup imaginé par action).
PERCEPTIONS = ("menace", "double_menace")


def joueurs(n: int = 2) -> list[str]:
    """Les joueurs dont un concept peut parler quand ``n`` joueurs jouent chacun leur tour :
    ``moi``, ``lui`` (le suivant), puis ``lui2``, ``lui3``… (le suivant du suivant, etc.)."""
    return [MOI, LUI][:max(n, 1)] + [f"{LUI}{d}" for d in range(2, n)]


def distance(qui: str) -> int:
    """La place de ``qui`` après moi dans l'ordre du jeu (0 : moi, 1 : le suivant…)."""
    if qui == MOI:
        return 0
    return 1 if qui == LUI else int(qui[len(LUI):])


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


def negation(x: Concept) -> Concept:
    """Le contraire de ``x`` (sans double négation)."""
    return x.args[0] if x.kind == "non" else non(x)


def contre_son_but(c: Concept, definitions: dict, n: int = 2) -> bool:
    """Le concept dit-il qu'un coup vaut mieux parce qu'il **me laisse moins près de gagner** (une
    de mes perceptions de progrès, :data:`PERCEPTIONS`, niée : « je n'ai pas de menace ») ou **le
    laisse, lui, plus près** (la sienne, affirmée : « il a une menace ») ? Un joueur ne se fait
    pas de tort : un tel concept n'explique pas pourquoi le coup du professeur valait mieux, c'est
    une coïncidence. Sous « au moins k de ses coups » (un autre que moi choisit), on ne conclut
    rien : il choisira ce qui l'arrange. ``n`` : le nombre de joueurs (« lui pour le suivant »,
    c'est moi à deux). Principe fourni à la main, général : on joue pour gagner.

    Seulement pour les perceptions : une construction est faite des pions d'un joueur, elle est à
    lui. ``gagne`` et les coups imaginés, non : au Nim, où les deux joueurs ont les mêmes coups,
    « aucun de mes coups ne donne « aucun de mes coups ne donne « je n'ai pas gagné » » » est
    une bonne règle (mes coups y imaginent les siens)."""
    def tort(x: Concept, signe: int, qui: int, libre: bool) -> bool:
        kind, args = x.kind, x.args
        if kind == "brique":
            nom, joueur = args
            joueur = (qui + distance(joueur)) % n
            if nom in definitions:
                return tort(definitions[nom], signe, joueur, libre)
            if nom not in PERCEPTIONS or libre:
                return False
            return signe < 0 if joueur == 0 else signe > 0
        if kind == "non":
            return tort(args[0], -signe, qui, libre)
        if kind == "et":
            return tort(args[0], signe, qui, libre) or tort(args[1], signe, qui, libre)
        _, joueur, y = args
        return tort(y, signe, qui, libre or (qui + distance(joueur)) % n != 0)
    return tort(c, 1, 0, False)


def parties_ou(c: Concept) -> list[Concept]:
    """Les parties d'un « ou » : ``non(et(non a, non b))`` se lit « a ou b ». Un concept qui n'en
    est pas un est sa seule partie. Les parties sont rangées **du plus immédiat au plus lointain**
    (profondeur croissante : combien de fois on regarde un coup plus loin), puis du plus petit au
    plus grand : on règle d'abord ce qui arrive le plus tôt."""
    def parties(x: Concept) -> list[Concept]:
        if x.kind == "non" and x.args[0].kind == "et":
            a, b = x.args[0].args
            return parties(negation(a)) + parties(negation(b))
        return [x]
    trouvees = list(dict.fromkeys(parties(c)))
    return sorted(trouvees, key=lambda x: (x.depth, x.size)) if len(trouvees) > 1 else trouvees


# ---------------------------------------------------------------------- #
# Évaluer un concept avec les quatre notions
# ---------------------------------------------------------------------- #

#: Ce que la mère retient au plus de ses calculs (par sorte : valeurs des concepts, positions
#: imaginées…). Ce n'est qu'une mémoire de travail : pleine, elle est vidée et la mère recalcule
#: ce dont elle a encore besoin (les résultats n'en dépendent pas). Sans ce plafond, une recherche
#: de concepts à trois joueurs, élargie, a rempli 31 Go.
MEMOIRE_MAX = 3_000_000


def _retenir(memoire: dict, cle, valeur):
    """Retient ``valeur`` sous ``cle`` ; une mémoire pleine est d'abord vidée."""
    if len(memoire) >= MEMOIRE_MAX:
        memoire.clear()
    memoire[cle] = valeur
    return valeur


def _key(etat):
    return tuple(etat) if isinstance(etat, list) else etat


class Pensee:
    """Évalue des concepts sur des positions, avec les quatre notions d'un jeu
    (``possibles``, ``apres``, ``gagne``, ``suivant``).

    Les positions déjà regardées sont mémorisées : c'est la mère qui pense, pas
    le fils (lui exécute son code, ne retient que pendant un coup ce qu'il a déjà
    regardé, et compte les positions distinctes qu'il regarde).
    """

    def __init__(self, notions, definitions: dict[str, Concept] | None = None):
        self.notions = notions
        self.definitions = definitions if definitions is not None else {}
        self._memo: dict = {}
        self._enfants: dict = {}
        self._gagne: dict = {}
        self._choix: dict = {}
        self._coups: dict = {}
        self._regards: dict = {}

    @property
    def perceptions(self) -> list[str]:
        """Les briques de perception que fournit la perception de ce jeu (voir :data:`PERCEPTIONS`)."""
        return [nom for nom in PERCEPTIONS if callable(getattr(self.notions, nom, None))]

    def enfants(self, etat, joueur) -> list:
        cle = (etat, joueur)
        enfants = self._enfants.get(cle)
        if enfants is None:
            n = self.notions
            enfants = _retenir(self._enfants, cle, [(a, _key(n.apres(etat, a, joueur))) for a in n.possibles(etat)])
        return enfants

    def joueur(self, moi, qui: str):
        """Le joueur ``qui`` vu de ``moi`` : moi, ou le suivant autant de fois que sa place."""
        joueur = moi
        for _ in range(distance(qui)):
            joueur = self.notions.suivant(joueur)
        return joueur

    def gagne(self, etat, joueur) -> bool:
        cle = (etat, joueur)
        valeur = self._gagne.get(cle)
        if valeur is None:
            valeur = _retenir(self._gagne, cle, bool(self.notions.gagne(etat, joueur)))
        return valeur

    def vrai(self, concept: Concept, etat, moi) -> bool:
        return self._vrai(concept, _key(etat), moi)

    def _vrai(self, concept: Concept, etat, moi) -> bool:
        """:meth:`vrai`, pour une position déjà sous sa forme de clé."""
        cle = (concept.id, etat, moi)
        if cle in self._memo:
            return self._memo[cle]
        kind, args = concept.kind, concept.args
        if kind == "brique":
            nom, qui = args
            joueur = self.joueur(moi, qui)
            if nom == GAGNE:
                valeur = self.gagne(etat, joueur)
            elif nom in PERCEPTIONS:
                valeur = bool(getattr(self.notions, nom)(etat, joueur))  # vu, pas imaginé
            else:
                valeur = self._vrai(self.definitions[nom], etat, joueur)
        elif kind == "non":
            valeur = not self._vrai(args[0], etat, moi)
        elif kind == "et":
            valeur = self._vrai(args[0], etat, moi) and self._vrai(args[1], etat, moi)
        else:
            k, qui, x = args
            joueur = self.joueur(moi, qui)
            compte = 0
            for _, suite in self.enfants(etat, joueur):
                if self._vrai(x, suite, moi):
                    compte += 1
                    if compte >= k:
                        break
            valeur = compte >= k
        return _retenir(self._memo, cle, valeur)

    def regard(self, concept: Concept, etat, moi) -> int:
        """Combien de positions le fils regarde ici pour savoir si le concept est vrai, en
        exécutant son code (``and`` s'arrête au premier faux, ``au_moins`` dès ses ``k`` coups),
        sans compter ce qu'il retient d'une sous-partie à l'autre (au plus :meth:`regardees`)."""
        etat = _key(etat)
        cle = (concept.id, etat, moi)
        valeur = self._regards.get(cle)
        if valeur is not None:
            return valeur
        kind, args = concept.kind, concept.args
        if kind == "brique":
            nom, qui = args
            valeur = 0 if nom == GAGNE or nom in PERCEPTIONS else self.regard(
                self.definitions[nom], etat, self.joueur(moi, qui))
        elif kind == "non":
            valeur = self.regard(args[0], etat, moi)
        elif kind == "et":
            valeur = self.regard(args[0], etat, moi)
            if self._vrai(args[0], etat, moi):
                valeur += self.regard(args[1], etat, moi)
        else:
            k, qui, x = args
            valeur, compte = 0, 0
            for _, suite in self.enfants(etat, self.joueur(moi, qui)):
                valeur += 1 + self.regard(x, suite, moi)
                if self._vrai(x, suite, moi):
                    compte += 1
                    if compte >= k:
                        break
        return _retenir(self._regards, cle, valeur)

    def regardees(self, concept: Concept, etat, moi, vues: set, faits: set) -> None:
        """Ajoute à ``vues`` les positions que regarde le fils (ses appels à ``apres`` :
        ``(état, action, joueur)``) pour savoir si le concept est vrai ici, en exécutant son code
        tel que la mère l'écrit (:func:`expression`) : ``and`` s'arrête au premier faux,
        ``au_moins`` dès qu'il a ses ``k`` coups. **Il ne calcule pas deux fois la même chose**
        pendant un coup : une position déjà regardée ne compte qu'une fois, et ce qu'il a déjà
        compris d'une position (``faits`` : (concept, état, joueur)) n'est pas recalculé. La mère
        le compte sans écrire ni compiler ce code."""
        etat = _key(etat)
        cle = (concept.id, etat, moi)
        if cle in faits:
            return
        faits.add(cle)
        kind, args = concept.kind, concept.args
        if kind == "brique":
            nom, qui = args
            if nom != GAGNE and nom not in PERCEPTIONS:  # ce qu'il voit ne coûte aucune position
                self.regardees(self.definitions[nom], etat, self.joueur(moi, qui), vues, faits)
        elif kind == "non":
            self.regardees(args[0], etat, moi, vues, faits)
        elif kind == "et":
            self.regardees(args[0], etat, moi, vues, faits)
            if self.vrai(args[0], etat, moi):
                self.regardees(args[1], etat, moi, vues, faits)
        else:
            k, qui, x = args
            joueur, compte = self.joueur(moi, qui), 0
            for action, suite in self.enfants(etat, joueur):
                vues.add((etat, action, joueur))
                self.regardees(x, suite, moi, vues, faits)
                if self.vrai(x, suite, moi):
                    compte += 1
                    if compte >= k:
                        break

    def regle_regardees(self, regle: Concept, etat, moi, vues: set, faits: set,
                        candidats: set | None = None) -> None:
        """Les positions que regarde le fils pour appliquer la règle ici : chaque coup encore
        candidat (tous, sans ``candidats``), puis le concept après lui (voir :meth:`regardees`)."""
        etat = _key(etat)
        for action, suite in self.enfants(etat, moi):
            if candidats is not None and action not in candidats:
                continue
            vues.add((etat, action, moi))
            self.regardees(regle, suite, moi, vues, faits)

    def vues(self, regle: Concept, etat, moi) -> int:
        """Combien de positions distinctes le fils regarde pour appliquer cette seule règle ici."""
        vues: set = set()
        self.regle_regardees(regle, etat, moi, vues, set())
        return len(vues)

    def coups(self, concept: Concept, etat, moi) -> set:
        """La règle : les actions après lesquelles le concept est vrai."""
        return {a for a, suite in self.enfants(_key(etat), moi) if self.vrai(concept, suite, moi)}

    def filtre(self, regle: Concept, etat, moi, candidats: set) -> set:
        """Les candidats que garde la règle : ceux après lesquels le concept est vrai, si elle en
        écarte (sinon elle se tait, et tous restent). **Une règle propose, elle ne tranche pas
        seule** : elle écarte des coups, et la suivante choisit parmi ceux qui restent."""
        etat = _key(etat)
        cle = (regle.id, etat, moi)
        acceptes = self._coups.get(cle)
        if acceptes is None:
            acceptes = _retenir(self._coups, cle, frozenset(self.coups(regle, etat, moi)))
        gardes = candidats & acceptes
        return gardes if gardes and len(gardes) < len(candidats) else candidats

    def decision(self, regles: list[Concept], etat, moi) -> tuple[set, int | None]:
        """Les coups qui restent après les règles, dans l'ordre (chacune filtre ce que laissent les
        précédentes ; un seul coup restant, il n'y a plus rien à regarder), et le rang de la
        dernière règle qui a écarté des coups (``None`` : aucune, le coup est par défaut)."""
        etat = _key(etat)
        candidats, rang = {a for a, _ in self.enfants(etat, moi)}, None
        for i, regle in enumerate(regles):
            if len(candidats) <= 1:
                break
            gardes = self.filtre(regle, etat, moi, candidats)
            if gardes is not candidats:
                candidats, rang = gardes, i
        return candidats, rang

    def choix(self, regle: Concept, etat, moi) -> set:
        """Les coups proposés par la règle ; vide si elle n'en écarte aucun (elle ne choisit rien)."""
        etat = _key(etat)
        cle = (regle.id, etat, moi)
        choisis = self._choix.get(cle)
        if choisis is None:
            coups = self.coups(regle, etat, moi)
            choisis = _retenir(self._choix, cle, coups if len(coups) < len(self.enfants(etat, moi)) else set())
        return choisis


# ---------------------------------------------------------------------- #
# Énumérer les concepts par taille
# ---------------------------------------------------------------------- #

def echantillon(notions, depart, joueurs, nombre: int = 120, graine: int = 0) -> list[tuple]:
    """Des positions imaginées par la mère (parties au hasard avec ``apres``), vues du côté de
    chaque joueur. ``joueurs`` : les joueurs, dans l'ordre où ils jouent."""
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
            trait = (trait + 1) % len(joueurs)
        if len(resultat) >= nombre:
            break
    return resultat


def cout(c: Concept, coups: float, definitions: dict, memo: dict | None = None,
         connus: dict | None = None) -> float:
    """Au plus combien de positions le fils regarde pour savoir si ``c`` est vrai, quand chaque
    position offre ``coups`` coups. Rien pour ce qu'il voit (``gagne``, une perception) ;
    « au moins k de ses coups » : chacun de ses coups et ce qui suit ; « a et b » : les deux.
    ``connus`` : pour les concepts déjà formés, ce qu'il regarde **au pire, mesuré** sur les
    positions de la mère (:meth:`Pensee.regard`) : elle ne suppose le pire que de ce qu'elle
    n'a pas encore pensé. Se lit sur l'arbre du concept, sans rien imaginer."""
    memo = {} if memo is None else memo
    connus = {} if connus is None else connus
    if c.id in connus:
        return connus[c.id]
    if c.id not in memo:
        kind, args = c.kind, c.args
        if kind == "brique":
            nom = args[0]
            valeur = cout(definitions[nom], coups, definitions, memo, connus) if nom in definitions else 0.0
        elif kind == "non":
            valeur = cout(args[0], coups, definitions, memo, connus)
        elif kind == "et":
            valeur = cout(args[0], coups, definitions, memo, connus) + cout(args[1], coups, definitions, memo, connus)
        else:
            valeur = coups * (1 + cout(args[2], coups, definitions, memo, connus))
        memo[c.id] = valeur
    return memo[c.id]


def enumerer(pensee: Pensee, positions: list[tuple], taille_max: int = 5,
             profondeur_max: int = 2, comptes: tuple = (1, 2),
             qui: tuple = (MOI, LUI), budget: int | None = None) -> list[Concept]:
    """Les concepts distincts, du plus petit au plus grand. ``qui`` : les joueurs dont ils
    peuvent parler (voir :func:`joueurs`).

    Un concept qui dit la même chose qu'un plus petit sur ``positions``, ou qui
    y est toujours vrai (ou toujours faux), n'est pas gardé ; sauf si le plus petit est contraire
    au but et lui non (:func:`contre_son_but` : dans un jeu où « je pourrais gagner » et « il
    pourrait gagner » vont ensemble, la version qui peut expliquer un coup est gardée aussi).

    **Ne pas penser à ce que le fils ne pourrait pas se permettre.** Avec un ``budget`` (les
    positions que le fils peut regarder par coup), la mère n'imagine même pas une règle qui
    pourrait lui coûter davantage : chacun de ses coups, puis le concept (:func:`cout`, avec le
    nombre moyen de coups des ``positions``). **Au pire, pas en moyenne** : le budget est un
    plafond par coup, et un concept bon marché en moyenne (il s'arrête vite) peut énumérer
    toutes les réponses sur plusieurs coups là où il ne s'arrête pas. Ce pire, elle le mesure sur
    ses positions pour ce qu'elle a déjà formé, et ne le suppose que pour le reste. C'est le
    budget qui dit jusqu'où penser, pas une
    profondeur : loin dans un jeu à trois coups par position, à peine au-delà d'un coup quand
    il y en a seize.
    """
    par_taille: dict[int, list[Concept]] = {t: [] for t in range(1, taille_max + 1)}
    signatures: dict = {}  # signature -> le concept qui la représente
    tort: dict = {}

    def contre(c: Concept) -> bool:
        if c.id not in tort:
            tort[c.id] = contre_son_but(c, pensee.definitions, len(qui))
        return tort[c.id]

    couts: dict = {}
    pires: dict = {}  # concept formé -> ce que le fils regarde au pire, mesuré sur les positions
    coups = sum(len(pensee.enfants(etat, moi)) for etat, moi in positions) / max(len(positions), 1)

    def essayer(c: Concept) -> None:
        if c.size > taille_max or c.depth > profondeur_max:
            return
        if budget is not None and coups * (1 + cout(c, coups, pensee.definitions, couts, pires)) > budget:
            return  # trop cher pour le fils : elle n'y pense pas
        signature = tuple(pensee.vrai(c, etat, moi) for etat, moi in positions)
        if all(signature) or not any(signature):
            return
        premier = signatures.get(signature)
        if premier is not None and not (contre(premier) and not contre(c)):
            return
        signatures[signature] = c
        if budget is not None:
            pires[c.id] = max(pensee.regard(c, etat, moi) for etat, moi in positions)
        par_taille[c.size].append(c)

    for nom in [GAGNE] + pensee.perceptions + list(pensee.definitions):
        profondeur = pensee.definitions[nom].depth if nom in pensee.definitions else 0
        for j in qui:
            essayer(brique(nom, j, profondeur))
    for taille in range(2, taille_max + 1):
        for x in par_taille[taille - 1]:
            essayer(non(x))
            for k in comptes:
                for j in qui:
                    essayer(au_moins(k, j, x))
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

def _sujet(qui: str) -> str:
    """Qui est ``qui``, dit en français (« il » : le suivant ; plus loin, sa place après moi)."""
    d = distance(qui)
    return "je" if d == 0 else "il" if d == 1 else f"le {d}e après moi"


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
            return f"{_sujet(qui)} a gagné" if vrai else f"{_sujet(qui)} n'a pas gagné"
        if nom in PERCEPTIONS:
            sujet = "j'ai" if qui == MOI else f"{_sujet(qui)} a"
            negatif = "je n'ai" if qui == MOI else f"{_sujet(qui)} n'a"
            nom = nom.replace("_", " ")
            return f"{sujet} une {nom}" if vrai else f"{negatif} pas de {nom}"
        if qui != MOI:  # une brique vue du côté d'un autre joueur
            d = distance(qui)
            nom = f"{nom} pour {'le suivant' if d == 1 else f'le {d}e après moi'}"
        return nom if vrai else f"pas {nom}"
    if kind == "et":
        parts = []
        for x in args:
            texte = decrire(x, vrai)
            nested = x.kind == "et" or (x.kind == "non" and x.args[0].kind == "et")
            parts.append(f"({texte})" if nested else texte)
        return f" {'et' if vrai else 'ou'} ".join(parts)
    k, qui, x = args
    d = distance(qui)
    coups = "de mes coups" if d == 0 else "de ses coups" if d == 1 else f"des coups du {d}e après moi"
    if k == 1:
        if vrai:
            return f"un {coups} donne « {decrire(x)} »"
        return f"aucun {coups} ne donne « {decrire(x)} »"
    if vrai:
        return f"au moins {k} {coups} donnent « {decrire(x)} »"
    return f"au plus {k - 1} {coups} donne{'nt' if k > 2 else ''} « {decrire(x)} »"


def decrire_regle(c: Concept) -> str:
    return f"jouer un coup après lequel {decrire(c)}"


def expression(c: Concept, etat: str = "etat", niveau: int = 0) -> str:
    """Le concept en Python, avec les quatre notions (``moi``, ``lui``, ``lui2``… sont des
    variables)."""
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


def _plus_loin(c: Concept) -> int:
    """La place après moi du joueur le plus éloigné dont parle le concept."""
    ici = distance(c.args[1]) if c.kind in ("brique", "au_moins") else 0
    return max([ici] + [_plus_loin(a) for a in c.args if isinstance(a, Concept)])


def source(nom: str, c: Concept) -> str:
    """Le texte d'un concept tel que la mère l'écrit dans le code du fils."""
    noms = [MOI] + joueurs(max(_plus_loin(c), 1) + 1)[1:]
    suivants = "".join(f"    {qui} = suivant({avant})\n" for avant, qui in zip(noms, noms[1:]))
    return (f"def {nom}(etat, moi):\n"
            f'    """{decrire(c)}."""\n'
            f"{suivants}"
            f"    return {expression(c)}\n")


def dependances(noms: list[str], definitions: dict[str, Concept]) -> list[str]:
    """Les briques nécessaires à ces concepts, chaque brique avant ceux qui l'utilisent."""
    ordre: list[str] = []

    def visiter(c: Concept) -> None:
        if c.kind == "brique":
            nom = c.args[0]
            if nom != GAGNE and nom not in PERCEPTIONS and nom not in ordre:
                visiter(definitions[nom])
                ordre.append(nom)
        else:
            for a in c.args:
                if isinstance(a, Concept):
                    visiter(a)

    for nom in noms:
        visiter(brique(nom, MOI, definitions[nom].depth))
    return ordre
