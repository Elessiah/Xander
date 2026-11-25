"""Comment la mère écrit le code de son fils.

Le fils est un fichier Python autonome (il n'importe rien de Xander) que la
mère écrit, puis réécrit à chaque correction. Il a trois parties :

1. **Perception** : ``possibles``, ``apres``, ``gagne``, ``adversaire``, écrites
   à partir de ce que la mère a compris du jeu : ``apres`` recopie le programme
   qu'elle a construit pour décrire l'action (voir :mod:`xander.effets`), les
   pions viennent de ce qu'elle a observé, les motifs de la contre-épreuve.
2. **Règles** : les concepts que la mère a construits et appris au fils, et
   seulement ceux-là (voir :mod:`xander.concepts`), traduits en Python, dans
   l'ordre de priorité appris, plus ses souvenirs.
3. **Squelette** : l'ordre de décision (souvenir, règles, défaut) et la
   fonction ``play(game)``. Écrit à la naissance ; c'est là qu'on pourra plus
   tard transmettre l'expérience de ses frères.

Le fils compte les positions qu'il regarde (``VUES``, incrémenté par
``apres``) : c'est le budget de réflexion vérifié par les tests.
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
        "reach": {},        # action -> cases qu'on l'a vue remplir, dans l'ordre déduit (labo)
        "written": ("joueur",),  # la valeur que l'action écrit (décrite par la mère, voir effets.ecriture)
        "free": ("toujours",),   # quand une case peut être jouée (décrit par la mère, voir effets.liberte)
        "start": [],        # la position du début de la partie
        "marks": [],        # pions posés par chaque joueur (« X », « O »)
        "patterns": [],     # motifs qui finissent la partie, compris par contre-épreuve
        "concepts": {},     # nom -> arbre de concept construit par la mère (une brique)
        "rules": [],        # concepts appris comme règles, du plus prioritaire au moins prioritaire
        "memories": {},     # cle(etat, moi) -> case à jouer ; « ? » dans la clé : case qui ne compte pas
        "symmetries": [],   # renumérotations des cases qui ne changent rien au jeu (vérifiées)
    }


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
    return valeur_apres(etat, (action,))
"""
    return f"""{effets.source(effect)}

def case_jouee(etat, action):
    \"\"\"La case que remplit l'action : la seule qui change, si elle peut être jouée.\"\"\"
    cases = changees(etat, (action,))
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


def perception_source(knowledge: dict) -> str:
    """Les quatre notions, pour un état en tableau dont chaque action remplit une case."""
    return f'''# --- Perception (écrite par la mère) -------------------------------------
# L'action est décrite par le programme que la mère a construit (Analyzer) ;
# elle a essayé les actions dans son labo, vu quel pion pose chaque joueur et
# quels motifs finissent la partie.

PIONS = {knowledge["marks"]!r}
MOTIFS = {pformat(knowledge["patterns"], compact=True, width=70)}
VUES = 0  # positions regardées pendant le coup en cours

ACTIONS = {knowledge["actions"]!r}  # acceptées par le jeu au départ (essayées dans le labo)
PORTEES = {pformat(knowledge["reach"], compact=True, width=70)}  # cases que chaque action remplit, dans l'ordre
ACTION_DE = {{case: action for action in reversed(ACTIONS) for case in PORTEES.get(action, [])}}


{free_source(knowledge["free"], knowledge["start"])}

{apres_source(knowledge["effect"], knowledge["written"])}

def action_pour(case):
    """L'action qui peut remplir cette case (vu dans le labo)."""
    return ACTION_DE.get(case)


def possibles(etat):
    return [action for action in ACTIONS if case_jouee(etat, action) is not None]


def gagne(etat, joueur):
    return any(all(etat[case] == joueur for case in motif) for motif in MOTIFS)


def adversaire(joueur):
    return PIONS[1] if joueur == PIONS[0] else PIONS[0]


def cle(etat, moi):
    """La position vue de mon côté : M mes pions, A les siens, . libre, # autre chose."""
    lui = adversaire(moi)
    return "".join("M" if v == moi else "A" if v == lui else "." if libre(etat, i) else "#"
                   for i, v in enumerate(etat))


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
    """Mon pion : celui que j'ai posé, sinon celui qui manque sur le plateau."""
    poses = sum(v in PIONS for v in etat)
    if poses < memoire.get("poses", 0) or poses <= 1:
        memoire.pop("moi", None)  # nouvelle partie
    if "moi" not in memoire:
        presents = [p for p in PIONS if p in etat]
        if len(presents) == 1:
            memoire["moi"] = adversaire(presents[0])
        elif len(presents) == 2 and etat.count(PIONS[0]) != etat.count(PIONS[1]):
            memoire["moi"] = min(PIONS, key=etat.count)
    return memoire.get("moi", PIONS[0])
'''


def rules_source(knowledge: dict) -> str:
    rules, definitions = knowledge["rules"], knowledge["concepts"]
    parts = ["# --- Règles apprises (concepts construits par la mère) --------------------\n"
             "# Une règle : jouer une action après laquelle le concept est vrai."]
    if rules:
        parts.append(concepts.AU_MOINS_SOURCE)
        parts += [concepts.source(name, definitions[name])
                  for name in concepts.dependances(rules, definitions)]
    parts.append(f"REGLES = [{', '.join(rules)}]  # ordre de priorité appris")
    parts.append(f"SOUVENIRS = {pformat(knowledge['memories'], width=70)}")
    return "\n\n".join(parts) + "\n"


def skeleton_source(knowledge: dict) -> str:
    return f'''# --- Squelette (écrit par la mère à la naissance) -----------------------

GETTER, ACTION, FIN = {knowledge["getter"]!r}, {knowledge["action"]!r}, {knowledge["end_signal"]!r}
MEMOIRE = {{}}


def choisir(etat, moi):
    """Mon coup et sa raison : souvenir, sinon première règle qui s'applique, sinon défaut."""
    global VUES
    VUES = 0
    _, coup = rappel(etat, moi, SOUVENIRS)
    if coup is not None and coup in possibles(etat):
        return coup, "souvenir"
    for regle in REGLES:
        coups = [a for a in possibles(etat) if regle(apres(etat, a, moi), moi)]
        if coups and len(coups) < len(possibles(etat)):  # une règle qui accepte tout ne choisit rien
            return min(coups), regle.__name__
    return min(possibles(etat)), "défaut"


def play(game):
    """Joue un tour : lit l'état, choisit, joue. Jamais de retour en arrière."""
    etat = getattr(game, GETTER)()
    moi = qui_suis_je(etat, MEMOIRE)
    coup, _ = choisir(etat, moi)
    for action in [coup] + [a for a in possibles(etat) if a != coup]:
        resultat = getattr(game, ACTION)(action)
        if type(resultat) is type(FIN) and resultat == FIN:
            return resultat
        suite = getattr(game, GETTER)()
        if suite != etat:  # coup accepté (un coup refusé ne change rien)
            case = case_jouee(etat, action)  # mon pion : ce qui est apparu là où j'ai joué
            MEMOIRE["moi"] = suite[case] if case is not None and suite[case] in PIONS else moi
            MEMOIRE["poses"] = sum(v in PIONS for v in suite)
            return resultat
    raise RuntimeError("le jeu a refusé toutes mes actions")
'''


def son_source(name: str, knowledge: dict, nb_games: int = 0) -> str:
    header = (
        f'"""Fils « {name} », écrit par la logique mère de Xander.\n\n'
        f"Leçon de l'exemple, puis {nb_games} partie(s) corrigée(s). Ce fichier ne contient\n"
        "que ce que la mère lui a appris ; il l'exécute sans jamais revenir en arrière.\n"
        '"""\n'
    )
    return "\n\n".join([header, perception_source(knowledge), rules_source(knowledge),
                        skeleton_source(knowledge)])


def load(source: str, name: str = "fils") -> types.ModuleType:
    """Exécute le code d'un fils et renvoie le module obtenu."""
    module = types.ModuleType(name)
    exec(compile(source, f"<{name}>", "exec"), module.__dict__)
    return module


def mind(knowledge: dict) -> types.ModuleType:
    """L'espace où la mère pense : sa perception du jeu (les quatre notions)."""
    return load(perception_source(knowledge), "mere")
