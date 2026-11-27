"""Comment la mère écrit le code de son fils.

Le fils est un fichier Python autonome (il n'importe rien de Xander) que la
mère écrit, puis réécrit à chaque correction. Il a trois parties :

1. **Perception** : ``possibles``, ``apres``, ``gagne``, ``suivant``, écrites
   à partir de ce que la mère a compris du jeu : ``apres`` recopie le programme
   qu'elle a construit pour décrire l'action (voir :mod:`xander.effets`), les
   pions viennent de ce qu'elle a observé (dans l'ordre où les joueurs jouent :
   ``suivant`` en vient), les motifs de la contre-épreuve.
2. **Règles** : les concepts que la mère a construits et appris au fils, et
   seulement ceux-là (voir :mod:`xander.concepts`), traduits en Python, dans
   l'ordre de priorité appris, plus ses souvenirs.
3. **Squelette** : l'ordre de décision (souvenir, règles, défaut) et la
   fonction ``play(game)``. Écrit à la naissance ; c'est là qu'on pourra plus
   tard transmettre l'expérience de ses frères.

Quand l'état est une valeur (un nombre) et non un tableau, la perception est
écrite autrement (:func:`perception_valeur_source`) : une position est
``[valeur, trait]``, la fin de partie une valeur avec le joueur qu'elle fait
gagner, et il n'y a ni cases, ni motifs, ni symétries.

Le fils compte les positions qu'il regarde (``VUES``, incrémenté par
``apres``) : c'est le budget de réflexion vérifié par les tests. **Il ne calcule
pas deux fois la même chose** : pendant un coup, il retient les positions qu'il a
déjà regardées et ce qu'il a déjà compris d'une position (:data:`DEJA_SOURCE`) ;
une position revue n'est ni recalculée ni recomptée.
"""

from __future__ import annotations

import types
from pprint import pformat

from xander import concepts, effets


def empty_knowledge(model) -> dict:
    """Ce que la mère sait au départ pour écrire un fils : comment lire et jouer."""
    return {
        "getter": model.getter.short_name,
        "effect": None,     # le programme qui décrit l'action, construit par la mère (Hypothese)
        "action": model.action.short_name,
        "end_signal": model.end_signal,
        "actions": [],      # actions que le jeu accepte au départ (essayées dans le labo)
        "largeur": 1,       # arguments d'une action ; à plusieurs, une action est le tuple de ses arguments
        "ecritures": None,  # sans pions : ce qu'écrit chaque partie de l'action (voir effets.ecritures)
        "reach": {},        # action -> cases qu'on l'a vue remplir, dans l'ordre déduit (labo)
        "written": ("joueur",),  # la valeur que l'action écrit (décrite par la mère, voir effets.ecriture)
        "free": ("toujours",),   # quand une case peut être jouée (décrit par la mère, voir effets.liberte)
        "start": [],        # la position du début de la partie
        "marks": [],        # pions posés par chaque joueur, dans l'ordre où ils jouent (« X », « O »)
        "patterns": [],     # motifs qui finissent la partie, compris par contre-épreuve
        "ends": {},         # état valeur : valeur de fin -> qui gagne (« dernier » ou « trait »)
        "concepts": {},     # nom -> arbre de concept construit par la mère (une brique)
        "rules": [],        # concepts appris comme règles, du plus prioritaire au moins prioritaire
        "memories": {},     # cle(etat, moi) -> case à jouer ; « ? » dans la clé : case qui ne compte pas
        "symmetries": [],   # renumérotations des cases qui ne changent rien au jeu (vérifiées)
    }


#: Les lettres d'une position vue d'un côté : M pour moi, puis A pour le suivant, B pour le
#: joueur d'après… (à deux, seulement M et A).
LETTRES = "MABCDEFGHIJKL"

#: L'ordre des joueurs, commun aux deux perceptions : ``suivant`` et la lettre de chacun.
ORDRE_SOURCE = '''def suivant(joueur):
    """Le joueur qui joue après lui (l'ordre vu dans l'exemple ; à deux, l'adversaire)."""
    return JOUEURS[(JOUEURS.index(joueur) + 1) % len(JOUEURS)]


def lettres(moi):
    """Chaque joueur vu de mon côté : M moi, A le suivant, B celui d'après…"""
    vus, joueur = [], moi
    for lettre in LETTRES[:len(JOUEURS)]:
        vus.append((joueur, lettre))
        joueur = suivant(joueur)
    return vus
'''


def symmetries_literal(knowledge: dict) -> str:
    return pformat([None] + knowledge["symmetries"], compact=True, width=70)


def written_source(written: tuple) -> str:
    """L'expression Python de la valeur écrite, telle que la mère l'a décrite
    (voir :func:`xander.effets.ecriture`)."""
    if written[0] == "constante":
        return repr(written[1])
    if written[0] == "argument":
        return f"(action,)[{written[1]}]"
    return "joueur"  # une valeur propre à chaque joueur : son pion


def free_source(free: tuple, start: list) -> str:
    """``libre(etat, case)`` telle que la mère l'a décrite (voir :func:`xander.effets.liberte`)."""
    if free[0] == "constante":
        test, depart = f"etat[case] == {free[1]!r}", ""
    elif free[0] == "depart":
        test, depart = "etat[case] == DEPART[case]", f"DEPART = {start!r}  # la position du début\n\n\n"
    else:  # le programme suffit : il n'annonce aucune case quand on ne peut pas jouer
        test, depart = "True", ""
    return f"""{depart}def libre(etat, case):
    \"\"\"La case peut-elle recevoir l'action ? {free!r}, vu dans le labo.\"\"\"
    return {test}
"""


def apres_source(effect: effets.Hypothese, written: tuple = ("joueur",)) -> str:
    """``apres`` (et ``case_jouee``) à partir de ce que la mère a compris de l'action.

    Pour un tableau, le programme dit quelles cases changent ; la case jouée est
    la seule qui change, si elle est libre, et elle reçoit la valeur que la mère
    a décrite (``written`` : au Morpion, une valeur propre à chaque joueur, son
    pion). Pour un nombre, le programme donne directement la nouvelle valeur.
    """
    if effect.forme != effets.CHANGEES:
        return f"""{effets.source(effect)}

def apres(etat, action, joueur):
    global VUES
    VUES += 1
    return valeur_apres(etat, action if isinstance(action, tuple) else (action,))
"""
    return f"""{effets.source(effect)}

def case_jouee(etat, action):
    \"\"\"La case que remplit l'action : la seule qui change, si elle peut être jouée.\"\"\"
    cases = changees(etat, arguments(action))
    if len(cases) != 1:
        return None
    (case,) = cases
    return case if libre(etat, case) else None


def apres(etat, action, joueur):
    global VUES
    VUES += 1
    suite = list(etat)
    suite[case_jouee(etat, action)] = {written_source(written)}  # {written!r}, vu dans le labo
    return suite
"""


def est_valeur(knowledge: dict) -> bool:
    """L'état est-il une valeur (un nombre) plutôt qu'un tableau de cases à pions ? (Un tableau sans
    pions, dont l'action écrit des valeurs, se traite comme une valeur : la position porte le trait.)"""
    effect = knowledge["effect"]
    return effect is not None and (effect.forme == effets.APRES or knowledge.get("ecritures") is not None)


def permise_source(free: tuple) -> str:
    """``permise(valeur)`` telle que la mère l'a décrite (voir :func:`xander.effets.bornes`)."""
    if free[0] == "au_moins":
        test = f"valeur >= {free[1]!r}"
    elif free[0] == "au_plus":
        test = f"valeur <= {free[1]!r}"
    elif free[0] == "entre":
        test = f"{free[1]!r} <= valeur <= {free[2]!r}"
    else:
        test = "True"
    return f"""def permise(valeur):
    \"\"\"Une action qui mène à cette valeur est-elle permise ? {free!r}, vu dans le labo.\"\"\"
    return {test}
"""


def arguments_source(knowledge: dict) -> str:
    """``arguments(action)`` : ce que le fils passe au jeu pour jouer une action."""
    largeur = knowledge.get("largeur", 1)
    return f'''LARGEUR = {largeur}  # arguments d'une action (vu dans l'exemple)


def arguments(action):
    """Les arguments d'une action : à plusieurs, l'action est le tuple de ses arguments."""
    return tuple(action) if LARGEUR > 1 else (action,)


def gele(valeur):
    """Un état en liste devient un tuple (une position sert de clé)."""
    return tuple(gele(v) for v in valeur) if isinstance(valeur, list) else valeur
'''


def prevision_source(knowledge: dict) -> str:
    """``valeur_apres(avant, args)`` pour un tableau dont l'action écrit des valeurs : les briques
    (recopiées de :data:`effets.AIDES_SOURCE`), les portées vues dans le labo, puis ce que la
    mère a compris (où l'action écrit, ce qu'elle écrit, quand elle est permise)."""
    return (effets.AIDES_SOURCE
            + f"\n\nPORTEES = {pformat(knowledge['reach'], compact=True, width=70)}  # vu dans le labo\n\n\n"
            + effets.source_prevision(knowledge["effect"], knowledge["ecritures"], knowledge["free"]))


def valeur_permise_source(knowledge: dict) -> str:
    """``valeur_permise(valeur, action)`` : la valeur d'après si l'action est permise, sinon
    ``None``. (``suivant``, lui, est le joueur qui joue après un autre.)"""
    if knowledge.get("ecritures") is not None:
        return f'''{prevision_source(knowledge)}

def valeur_permise(valeur, action):
    """L'état après l'action, None si elle n'est pas permise (sa description le dit)."""
    return valeur_apres(valeur, arguments(action))
'''
    return f'''{effets.source(knowledge["effect"])}

{permise_source(knowledge["free"])}

def valeur_permise(valeur, action):
    """La valeur après l'action, None si elle n'est pas permise."""
    apres_ = valeur_apres(valeur, arguments(action))
    return apres_ if permise(apres_) else None
'''


def perception_valeur_source(knowledge: dict) -> str:
    """Les quatre notions, pour un état qui est une valeur (un nombre) et non un tableau, ou un
    tableau sans pions (au Nim, les tas : l'action y écrit une valeur qui ne dit pas qui a joué).

    Une valeur ne dit pas qui a joué : la position que voient la mère et le fils
    est ``[valeur, trait]`` (le joueur qui doit jouer ; un tableau y devient un
    tuple). La fin de partie est une valeur, avec le joueur qu'elle fait gagner :
    celui qui vient de jouer (« dernier ») ou celui qui a le trait (« trait »).
    Il n'y a ni cases, ni motifs, ni symétries : un souvenir retient l'action.
    """
    return f'''# --- Perception (écrite par la mère) -------------------------------------
# L'état est une valeur : l'action est décrite par le programme que la mère a
# construit (Analyzer) ; elle a essayé les actions dans son labo, vu lesquelles
# le jeu refuse, et compris à quelle valeur la partie finit et qui la gagne.
# Une position est [valeur, trait] : la valeur ne dit pas qui doit jouer.

JOUEURS = {knowledge["marks"]!r}  # dans l'ordre où ils jouent
LETTRES = {LETTRES!r}
FINS = {knowledge["ends"]!r}  # valeur de fin -> qui gagne (dernier : celui qui vient de jouer)
VUES = 0  # positions regardées pendant le coup en cours

ACTIONS = {knowledge["actions"]!r}  # acceptées par le jeu (essayées dans le labo)

{arguments_source(knowledge)}

{valeur_permise_source(knowledge)}

def possibles(etat):
    valeur, _ = etat
    if valeur in FINS:
        return []  # la partie est finie
    return [action for action in ACTIONS if valeur_permise(valeur, action) is not None]


def apres(etat, action, joueur):
    global VUES
    VUES += 1
    return [gele(valeur_apres(etat[0], arguments(action))), suivant(joueur)]


def gagne(etat, joueur):
    """Une fin « dernier » fait gagner celui qui vient de jouer (celui d'avant le trait)."""
    valeur, trait = etat
    qui = FINS.get(valeur)
    return (qui == "dernier" and suivant(joueur) == trait) or (qui == "trait" and joueur == trait)


{ORDRE_SOURCE}

def cle(etat, moi):
    """La position vue de mon côté : la valeur, et qui doit jouer (M moi, A le suivant…)."""
    valeur, trait = etat
    return f"{{valeur!r}} {{dict(lettres(moi))[trait]}}"


def case_jouee(etat, action):
    """Une valeur n'a pas de cases : ce que vise l'action, c'est l'action elle-même."""
    return action if action in possibles(etat) else None


def action_pour(action):
    return action


SYMETRIES = [None]  # une valeur ne se renumérote pas


def rappel(etat, moi, souvenirs):
    """Un souvenir de cette position : (sa clé, mon coup ici), s'il est permis."""
    k = cle(etat, moi)
    if k in souvenirs and souvenirs[k] in possibles(etat):
        return k, souvenirs[k]
    return None, None
'''


CONSTRUCTIONS_SOURCE = '''# --- Ce que je vois sans rien imaginer : les constructions en cours -----------
# Une construction : un motif de fin où un seul joueur a des pions. Le tableau des
# constructions est tenu au fil de la partie : un coup ne change que celles qui passent
# par sa case (un pion posé il y a trois coups et celui qui le complète se retrouvent
# dans la même construction) ; il n'est jamais recompté de zéro quand une position voisine
# est déjà connue.

PAR_CASE = {}  # case -> les motifs qui passent par elle
for _i, _motif in enumerate(MOTIFS):
    for _case in _motif:
        PAR_CASE.setdefault(_case, []).append(_i)
TABLEAUX = {}  # position -> l'état de chaque construction
DERNIER = []  # la dernière position dont je connais le tableau
VU = {}  # (position, joueur) -> ce que j'en ai déjà vu (les cases qui finiraient ses constructions)


def construction(etat, i):
    """(joueur, cases qui lui manquent) si un seul joueur a des pions dans le motif i, sinon None."""
    joueurs = {etat[c] for c in MOTIFS[i] if etat[c] in PIONS}
    if len(joueurs) != 1:
        return None
    (joueur,) = joueurs
    return joueur, tuple(c for c in MOTIFS[i] if etat[c] != joueur)


def constructions(etat):
    """Le tableau des constructions : mis à jour depuis la dernière position connue (seules
    les constructions qui passent par une case changée), sinon fait une fois."""
    cle = tuple(etat)
    tableau = TABLEAUX.get(cle)
    if tableau is None:
        if DERNIER:
            avant, connu = DERNIER[0]
            tableau = list(connu)
            for case in [c for c in range(len(cle)) if cle[c] != avant[c]]:
                for i in PAR_CASE.get(case, ()):
                    tableau[i] = construction(cle, i)
        else:
            tableau = [construction(cle, i) for i in range(len(MOTIFS))]
        if len(TABLEAUX) > 20000:
            TABLEAUX.clear()
            VU.clear()
        TABLEAUX[cle] = tableau
    DERNIER[:] = [(cle, tableau)]
    return tableau


def jouables(etat):
    """Les cases où un coup peut tomber (ce que je sais de l'action, sans l'imaginer)."""
    return {case_jouee(etat, action) for action in possibles(etat)} - {None}


def completions(etat, joueur):
    """Les cases jouables qui finiraient une de ses constructions (toutes, si une est finie).
    Une position déjà vue n'est pas regardée deux fois."""
    cle = (tuple(etat), joueur)
    if cle not in VU:
        tableau, ici, fins = constructions(etat), None, set()
        for c in tableau:
            if c is not None and c[0] == joueur and len(c[1]) <= 1:
                ici = jouables(etat) if ici is None else ici
                if not c[1]:
                    fins = ici
                    break
                if c[1][0] in ici:
                    fins.add(c[1][0])
        VU[cle] = fins
    return VU[cle]


def menace(etat, joueur):
    """Une de ses constructions n'attend plus qu'une case, et cette case est jouable."""
    return len(completions(etat, joueur)) >= 1


def double_menace(etat, joueur):
    """Deux cases jouables différentes qui finissent chacune une de ses constructions."""
    return len(completions(etat, joueur)) >= 2
'''


def uses_perceptions(knowledge: dict) -> bool:
    """Une règle du fils (ou une de ses briques) parle-t-elle de ce qu'il voit (menace…) ?"""
    definitions = knowledge.get("concepts", {})

    def parle(c) -> bool:
        if c.kind == "brique" and c.args[0] in concepts.PERCEPTIONS:
            return True
        return any(parle(a) for a in c.args if isinstance(a, concepts.Concept))

    names = concepts.dependances(knowledge.get("rules", []), definitions)
    return any(parle(definitions[n]) for n in names)


def perception_source(knowledge: dict, constructions: bool = True) -> str:
    """Les quatre notions, pour un état en tableau dont chaque action remplit une case ; et ce
    que le joueur voit sans rien imaginer (les constructions en cours), sauf ``constructions``
    faux : le fils ne le reçoit que s'il s'en sert."""
    if est_valeur(knowledge):
        return perception_valeur_source(knowledge)
    return f'''# --- Perception (écrite par la mère) -------------------------------------
# L'action est décrite par le programme que la mère a construit (Analyzer) ;
# elle a essayé les actions dans son labo, vu quel pion pose chaque joueur et
# quels motifs finissent la partie.

PIONS = JOUEURS = {knowledge["marks"]!r}  # dans l'ordre où ils jouent
LETTRES = {LETTRES!r}
MOTIFS = {pformat(knowledge["patterns"], compact=True, width=70)}
VUES = 0  # positions regardées pendant le coup en cours

ACTIONS = {knowledge["actions"]!r}  # acceptées par le jeu au départ (essayées dans le labo)
PORTEES = {pformat(knowledge["reach"], compact=True, width=70)}  # cases que chaque action remplit, dans l'ordre
ACTION_DE = {{case: action for action in reversed(ACTIONS) for case in PORTEES.get(action, [])}}

{arguments_source(knowledge)}

{free_source(knowledge["free"], knowledge["start"])}

{apres_source(knowledge["effect"], knowledge["written"])}

def action_pour(case):
    """L'action qui peut remplir cette case (vu dans le labo)."""
    return ACTION_DE.get(case)


def possibles(etat):
    return [action for action in ACTIONS if case_jouee(etat, action) is not None]


def gagne(etat, joueur):
    return any(all(etat[case] == joueur for case in motif) for motif in MOTIFS)


{CONSTRUCTIONS_SOURCE if constructions else ""}

{ORDRE_SOURCE}

def cle(etat, moi):
    """La position vue de mon côté : M mes pions, A ceux du suivant (à deux : les siens), B ceux
    du joueur d'après…, . libre, # autre chose."""
    vus = lettres(moi)

    def lettre(i, v):
        for joueur, l in vus:
            if v == joueur:
                return l
        return "." if libre(etat, i) else "#"
    return "".join(lettre(i, v) for i, v in enumerate(etat))


SYMETRIES = {symmetries_literal(knowledge)}  # None : la position telle quelle


def transformer(etat, sigma):
    """La position renumérotée : ce qui était en case i passe en case sigma[i]."""
    image = list(etat)
    for i, valeur in enumerate(etat):
        image[sigma[i]] = valeur
    return image


def contient(motif, k):
    """La position (sa clé) contient-elle ce petit motif ? « ? » : une case qui ne compte pas."""
    return all(m == "?" or m == v for m, v in zip(motif, k))


def jouable(etat, case, sigma):
    """L'action qui remplit ici la case d'un souvenir (vu sous sigma), si elle est jouable."""
    if sigma is not None:
        case = sigma.index(case)
    action = action_pour(case)
    return action if action is not None and case_jouee(etat, action) == case else None


def rappel(etat, moi, souvenirs):
    """Un souvenir de cette position, d'une position équivalente, ou d'un petit motif
    qu'elle contient (où qu'il soit, sous chaque façon de la voir) : (sa clé, mon coup ici).
    Un souvenir dit quelle case occuper ; il ne vaut que si une action la remplit."""
    ici = cle(etat, moi)  # lue sur la position elle-même, puis renumérotée
    for sigma in SYMETRIES:
        k = ici if sigma is None else "".join(transformer(ici, sigma))
        if k in souvenirs:
            action = jouable(etat, souvenirs[k], sigma)
            if action is not None:
                return k, action
        for motif in souvenirs:
            if "?" in motif and contient(motif, k):
                action = jouable(etat, souvenirs[motif], sigma)
                if action is not None:
                    return motif, action
    return None, None


def qui_suis_je(etat, memoire):
    """Mon pion : celui que j'ai posé, sinon celui du joueur à qui c'est le tour, lu sur le
    plateau : chacun joue à son tour, donc c'est le seul qui a posé moins de pions que celui
    qui joue avant lui (s'ils en ont tous autant, le plateau ne le dit pas)."""
    poses = sum(v in PIONS for v in etat)
    if poses < memoire.get("poses", 0) or poses < len(PIONS):
        memoire.pop("moi", None)  # nouvelle partie
    if "moi" not in memoire:
        comptes = [etat.count(p) for p in PIONS]
        en_retard = [p for i, p in enumerate(PIONS) if comptes[i] < comptes[i - 1]]
        if len(en_retard) == 1:
            memoire["moi"] = en_retard[0]
    return memoire.get("moi", PIONS[0])
'''


DEJA_SOURCE = '''# --- Ne pas calculer deux fois la même chose (écrit par la mère) ----------

DEJA = {}  # pendant le coup en cours : positions déjà regardées, concepts déjà compris


def _cle(etat):
    return repr(etat)


_apres_calcule = apres


def apres(etat, action, joueur=None):
    """Une position déjà regardée pendant ce coup n'est ni recalculée ni recomptée."""
    cle = ("apres", _cle(etat), repr(action), repr(joueur))
    if cle not in DEJA:
        DEJA[cle] = _apres_calcule(etat, action, joueur)
    return DEJA[cle]


def retenu(concept):
    """Ce qu'il a déjà compris d'une position pendant ce coup, il ne le recalcule pas."""
    def deja_compris(etat, moi):
        cle = (concept.__name__, _cle(etat), repr(moi))
        if cle not in DEJA:
            DEJA[cle] = concept(etat, moi)
        return DEJA[cle]
    deja_compris.__name__, deja_compris.__doc__ = concept.__name__, concept.__doc__
    return deja_compris
'''


def concepts_source(rules: list[str], definitions: dict) -> list[str]:
    """Les concepts du fils (ses règles et leurs briques), chacun retenu pendant le coup."""
    return ["@retenu\n" + concepts.source(name, definitions[name])
            for name in concepts.dependances(rules, definitions)]


def rules_source(knowledge: dict) -> str:
    rules, definitions = knowledge["rules"], knowledge["concepts"]
    parts = ["# --- Règles apprises (concepts construits par la mère) --------------------\n"
             "# Une règle : jouer une action après laquelle le concept est vrai.", DEJA_SOURCE]
    if rules:
        parts.append(concepts.AU_MOINS_SOURCE)
        parts += concepts_source(rules, definitions)
    parts.append(f"REGLES = [{', '.join(rules)}]  # ordre de priorité appris")
    parts.append(f"SOUVENIRS = {pformat(knowledge['memories'], width=70)}")
    return "\n\n".join(parts) + "\n"


PLAY_VALEUR = '''

def play(game):
    """Joue un tour : lit la valeur, choisit, joue. C'est mon tour : j'ai le trait. Jamais de
    retour en arrière, et un seul essai : essayer d'autres actions jusqu'à ce que le jeu en
    accepte une, ce serait tricher."""
    valeur = gele(getattr(game, GETTER)())
    moi = JOUEURS[0]  # seul compte qui joue : moi, qui ai le trait
    coup, _ = choisir([valeur, moi], moi)
    resultat = getattr(game, ACTION)(*arguments(coup))
    if type(resultat) is type(FIN) and resultat == FIN:
        return resultat
    if gele(getattr(game, GETTER)()) == valeur:  # un coup refusé ne change rien
        raise RuntimeError(f"coup impossible : le jeu a refusé {coup!r}")
    return resultat
'''


def skeleton_source(knowledge: dict) -> str:
    source = f'''# --- Squelette (écrit par la mère à la naissance) -----------------------

GETTER, ACTION, FIN = {knowledge["getter"]!r}, {knowledge["action"]!r}, {knowledge["end_signal"]!r}
MEMOIRE = {{}}


def choisir(etat, moi):
    """Mon coup et sa raison : souvenir, sinon mes règles l'une après l'autre (chacune écarte des
    coups parmi ceux que laissent les précédentes ; la raison : la dernière qui en a écarté),
    sinon défaut."""
    global VUES
    VUES = 0
    DEJA.clear()  # un nouveau coup : rien n'est encore regardé
    _, coup = rappel(etat, moi, SOUVENIRS)
    if coup is not None and coup in possibles(etat):
        return coup, "souvenir"
    candidats, raison = list(possibles(etat)), "défaut"
    for regle in REGLES:
        if len(candidats) <= 1:
            break  # un seul coup reste : plus rien à regarder
        coups = [a for a in candidats if regle(apres(etat, a, moi), moi)]
        if coups and len(coups) < len(candidats):  # une règle qui garde tout (ou rien) se tait
            candidats, raison = coups, regle.__name__
    return min(candidats), raison
'''
    if est_valeur(knowledge):
        return source + PLAY_VALEUR
    return source + '''

def play(game):
    """Joue un tour : lit l'état, choisit, joue. Jamais de retour en arrière, et un seul
    essai : essayer d'autres actions jusqu'à ce que le jeu en accepte une, ce serait tricher."""
    etat = getattr(game, GETTER)()
    moi = qui_suis_je(etat, MEMOIRE)
    coup, _ = choisir(etat, moi)
    resultat = getattr(game, ACTION)(*arguments(coup))
    if type(resultat) is type(FIN) and resultat == FIN:
        return resultat
    suite = getattr(game, GETTER)()
    if suite == etat:  # un coup refusé ne change rien
        raise RuntimeError(f"coup impossible : le jeu a refusé {coup!r}")
    case = case_jouee(etat, coup)  # mon pion : ce qui est apparu là où j'ai joué
    MEMOIRE["moi"] = suite[case] if case is not None and suite[case] in PIONS else moi
    MEMOIRE["poses"] = sum(v in PIONS for v in suite)
    return resultat
'''


def son_source(name: str, knowledge: dict, nb_games: int = 0) -> str:
    header = (
        f'"""Fils « {name} », écrit par la logique mère de Xander.\n\n'
        f"Leçon de l'exemple, puis {nb_games} partie(s) corrigée(s). Ce fichier ne contient\n"
        "que ce que la mère lui a appris ; il l'exécute sans jamais revenir en arrière.\n"
        '"""\n'
    )
    return "\n\n".join([header, perception_source(knowledge, uses_perceptions(knowledge)),
                        rules_source(knowledge), skeleton_source(knowledge)])


def load(source: str, name: str = "fils") -> types.ModuleType:
    """Exécute le code d'un fils et renvoie le module obtenu."""
    module = types.ModuleType(name)
    exec(compile(source, f"<{name}>", "exec"), module.__dict__)
    return module


def mind(knowledge: dict) -> types.ModuleType:
    """L'espace où la mère pense : sa perception du jeu (les quatre notions)."""
    return load(perception_source(knowledge), "mere")


# --------------------------------------------------------------------------- #
# Un fils qui joue seul (voir xander/un_joueur.py)
# --------------------------------------------------------------------------- #

def state_key(state):
    """La clé d'un souvenir : l'état exact (une liste devient un tuple)."""
    return tuple(state) if isinstance(state, list) else state


def contains(state: list, motif: dict) -> bool:
    """L'état contient-il ce petit motif ({case: valeur}) ?"""
    return all(0 <= i < len(state) and state[i] == v for i, v in motif.items())


def motif_text(motif: dict) -> str:
    return "{" + ", ".join(f"{i}: {v!r}" for i, v in sorted(motif.items())) + "}"


SOLO_NOTIONS_SOURCE = '''# --- Règles apprises (concepts construits par la mère) --------------------
# Une règle : jouer une action après laquelle le concept est vrai.

def apres(etat, action, joueur=None):
    """L'état après l'action, tel que je le prévois (une position regardée à l'avance)."""
    global VUES
    VUES += 1
    suite = valeur_apres(list(etat), arguments(action))
    return list(suite) if isinstance(suite, (list, tuple)) else suite


def gagne(etat, joueur=None):
    """Ai-je gagné ? L'état est une fin gagnée que la mère a comprise."""
    cle = tuple(etat) if isinstance(etat, list) else etat
    return FINS.get(cle) == "gagnée"


def suivant(joueur):
    """Seul, c'est encore moi qui joue après moi."""
    return joueur
'''


def solo_rules_source(knowledge: dict) -> str:
    """Les règles d'un fils qui joue seul, avec les quatre notions qu'elles demandent : ``apres``
    (l'état prévu, le seul endroit où il regarde à l'avance : ``VUES`` les compte), ``gagne``
    (l'état est une fin gagnée comprise), ``possibles`` et ``suivant`` (seul, je joue après
    moi). Sans règle, rien : le fils reconnaît, il ne prévoit pas."""
    rules, definitions = knowledge.get("rules", []), knowledge.get("concepts", {})
    if not rules:
        return "REGLES = []  # aucune règle apprise\nDEJA = {}"
    parts = [SOLO_NOTIONS_SOURCE, DEJA_SOURCE, concepts.AU_MOINS_SOURCE]
    parts += concepts_source(rules, definitions)
    parts.append(f"REGLES = [{', '.join(rules)}]  # ordre de priorité appris")
    return "\n\n".join(parts) + "\n"


def solo_source(name: str, knowledge: dict, nb_games: int = 0) -> str:
    """Le fils d'un jeu à un joueur : il lit l'état, reconnaît un souvenir ou un petit motif,
    sinon joue le coup par défaut. Il ne regarde aucune position à l'avance (``VUES`` reste 0)."""
    effect = knowledge["effect"]
    valeur = effect is not None and effect.forme == effets.APRES
    if knowledge.get("ecritures") is not None:
        permises = f"""{prevision_source(knowledge)}

def possibles(etat):
    \"\"\"Les actions permises : celles dont je prévois l'état d'après (sinon ce n'est pas un coup).\"\"\"
    return [action for action in ACTIONS if valeur_apres(etat, arguments(action)) is not None]
"""
    elif valeur and knowledge["free"][0] != "toujours":
        permises = f"""{effets.source(effect)}

{permise_source(knowledge["free"])}

def possibles(etat):
    return [action for action in ACTIONS if permise(valeur_apres(etat, arguments(action)))]
"""
    else:
        permises = f'''def possibles(etat):
    """Les actions permises : {knowledge["free"]!r}, vu dans le labo."""
    return list(ACTIONS)
'''
    motifs = "".join(f"    ({motif_text(m)}, {a!r}),\n" for m, a in knowledge.get("motifs", []))
    regles = solo_rules_source(knowledge)
    return f'''"""Fils « {name} », écrit par la logique mère de Xander (jeu à un joueur).

Leçon de l'exemple, puis {nb_games} partie(s) corrigée(s). Ce fichier ne contient
que ce que la mère lui a appris ; il l'exécute sans jamais revenir en arrière.
"""


# --- Perception (écrite par la mère) -------------------------------------
# L'action : {effect!r}
# (décrite par la mère ; le fils ne s'en sert pas : il reconnaît, il ne prévoit pas).
# Fin de partie : {knowledge.get("fin")} ; un coup est jugé sur {knowledge.get("horizon")} coup(s).

ACTIONS = {knowledge["actions"]!r}  # acceptées par le jeu (essayées dans le labo)
VUES = 0  # positions regardées à l'avance pendant le coup en cours (aucune)
FINS = {knowledge.get("fins", {})!r}  # état de fin compris (contre-épreuve) -> ce qu'il vaut

{arguments_source(knowledge)}

{permises}

def contient(etat, motif):
    """L'état contient-il ce petit motif ({{case: valeur}}) ?"""
    return all(0 <= i < len(etat) and etat[i] == v for i, v in motif.items())


# --- Ce que la mère lui a appris -------------------------------------------

SOUVENIRS = {pformat(knowledge["memories"], width=100)}  # état exact -> coup

MOTIFS = [
{motifs}]  # petits motifs ({{case: valeur}}, coup), dans l'ordre appris

{regles}


def motif_de(etat):
    """Le premier petit motif que contient l'état (None s'il n'y en a pas)."""
    if not isinstance(etat, list):
        return None
    return next((motif for motif, _ in MOTIFS if contient(etat, motif)), None)


# --- Squelette (écrit par la mère à la naissance) -----------------------

GETTER, ACTION, FIN = {knowledge["getter"]!r}, {knowledge["action"]!r}, {knowledge["end_signal"]!r}
HABITUEL = {knowledge.get("usual")!r}  # ce que l'action renvoie quand le coup est joué (vu dans l'exemple)


def choisir(etat, moi=None):
    """Mon coup et sa raison : souvenir, sinon petit motif, sinon la première règle qui choisit,
    sinon défaut (la plus petite action). Aucun coup possible : (None, "aucun coup")."""
    global VUES
    VUES = 0
    DEJA.clear()  # un nouveau coup : rien n'est encore regardé
    permis = possibles(etat)
    if not permis:
        return None, "aucun coup"
    cle = tuple(etat) if isinstance(etat, list) else etat
    if cle in SOUVENIRS and SOUVENIRS[cle] in permis:
        return SOUVENIRS[cle], "souvenir"
    if isinstance(etat, list):
        for motif, coup in MOTIFS:
            if contient(etat, motif) and coup in permis:
                return coup, "petit motif"
    for regle in REGLES:
        coups = [a for a in permis if regle(apres(etat, a, moi), moi)]
        if coups and len(coups) < len(permis):  # une règle qui accepte tout ne choisit rien
            return min(coups), regle.__name__
    return min(permis), "défaut"


def play(game):
    """Joue un tour : lit l'état, choisit, joue. Jamais de retour en arrière, et un seul
    essai : essayer d'autres actions jusqu'à ce que le jeu en accepte une, ce serait tricher."""
    etat = getattr(game, GETTER)()
    coup, _ = choisir(etat)
    if coup is None:
        return None  # aucun coup possible : la partie est bloquée
    resultat = getattr(game, ACTION)(*arguments(coup))
    if type(resultat) is type(FIN) and resultat == FIN:
        return resultat
    if type(resultat).__name__ != HABITUEL and getattr(game, GETTER)() == etat:
        raise RuntimeError(f"coup impossible : le jeu a refusé {{coup!r}}")  # rien n'a changé
    return resultat
'''
