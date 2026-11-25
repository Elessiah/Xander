"""Comment la mère écrit le code de son fils.

Le fils est un fichier Python autonome (il n'importe rien de Xander) que la
mère écrit, puis réécrit à chaque correction. Il a trois parties :

1. **Perception** : ``possibles``, ``apres``, ``gagne``, ``adversaire``, écrites
   à partir de ce que la mère a compris du jeu (action décrite par l'Analyzer,
   pions observés, motifs trouvés par contre-épreuve).
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

from xander import concepts
from xander.model import FunctionOperation


def target_knowledge(model) -> dict:
    """Comment l'action désigne la case qu'elle remplit, d'après l'Analyzer."""
    target = model.target
    if target is not None and target.kind is FunctionOperation.SEQUENCE_TARGET_INDEX:
        offset, step = target.parameters
        return {"kind": "file", "offset": offset, "step": step}
    return {"kind": "case"}


def empty_knowledge(model) -> dict:
    """Ce que la mère sait au départ pour écrire un fils : comment lire et jouer."""
    return {
        "getter": model.getter.short_name,
        "action": model.action.short_name,
        "end_signal": model.end_signal,
        "target": target_knowledge(model),  # l'action désigne une case, ou une file de cases
        "size": 0,          # nombre de cases du plateau
        "actions": [],      # actions que le jeu accepte au départ (essayées dans le labo)
        "marks": [],        # pions posés par chaque joueur (« X », « O »)
        "patterns": [],     # motifs qui finissent la partie, compris par contre-épreuve
        "concepts": {},     # nom -> arbre de concept construit par la mère (une brique)
        "rules": [],        # concepts appris comme règles, du plus prioritaire au moins prioritaire
        "memories": {},     # cle(etat, moi) -> case à jouer ; « ? » dans la clé : case qui ne compte pas
        "symmetries": [],   # renumérotations des cases qui ne changent rien au jeu (vérifiées)
    }


def symmetries_literal(knowledge: dict) -> str:
    return pformat([None] + knowledge["symmetries"], compact=True, width=70)


def target_source(knowledge: dict) -> str:
    """Ce que désigne une action : une case (Morpion) ou une file de cases (gravité)."""
    target = knowledge["target"]
    if target["kind"] == "file":
        return f'''# L'Analyzer a compris que l'action désigne une file de cases (SEQUENCE_TARGET_INDEX) :
# action {target["offset"]:+d}, puis {target["step"]:+d} à chaque case ; le pion prend la première case libre.

ACTIONS = {knowledge["actions"]!r}  # acceptées par le jeu au départ (essayées dans le labo)
TAILLE, DECALAGE, PAS = {knowledge["size"]}, {target["offset"]}, {target["step"]}


def _file(action):
    cases, case = [], action + DECALAGE
    while 0 <= case < TAILLE:
        cases.append(case)
        case += PAS
    return cases


FILES = {{action: _file(action) for action in ACTIONS}}
ACTION_DE = {{case: action for action in reversed(ACTIONS) for case in FILES[action]}}


def case_jouee(etat, action):
    """La case que remplit l'action : la première case libre de sa file."""
    return next((case for case in FILES[action] if etat[case] not in PIONS), None)


def action_pour(case):
    """L'action qui vise la file de cette case."""
    return ACTION_DE.get(case)


def possibles(etat):
    return [action for action in ACTIONS if case_jouee(etat, action) is not None]


def apres(etat, action, joueur):
    global VUES
    VUES += 1
    suite = list(etat)
    suite[case_jouee(etat, action)] = joueur
    return suite
'''
    return '''# L'Analyzer a compris que l'action désigne une case (SINGLE_TARGET_INDEX).


def case_jouee(etat, action):
    """La case que remplit l'action : celle qu'elle désigne, si elle est libre."""
    return action if etat[action] not in PIONS else None


def action_pour(case):
    return case


def possibles(etat):
    return [i for i, valeur in enumerate(etat) if valeur not in PIONS]


def apres(etat, action, joueur):
    global VUES
    VUES += 1
    suite = list(etat)
    suite[action] = joueur
    return suite
'''


def perception_source(knowledge: dict) -> str:
    """Les quatre notions, pour un état en tableau dont chaque action remplit une case."""
    return f'''# --- Perception (écrite par la mère) -------------------------------------
# La mère a vu quel pion pose chaque joueur et quels motifs finissent la partie.

PIONS = {knowledge["marks"]!r}
MOTIFS = {pformat(knowledge["patterns"], compact=True, width=70)}
VUES = 0  # positions regardées pendant le coup en cours

{target_source(knowledge)}


def gagne(etat, joueur):
    return any(all(etat[case] == joueur for case in motif) for motif in MOTIFS)


def adversaire(joueur):
    return PIONS[1] if joueur == PIONS[0] else PIONS[0]


def cle(etat, moi):
    """La position vue de mon côté : M mes pions, A les siens, . libre."""
    lui = adversaire(moi)
    return "".join("M" if v == moi else "A" if v == lui else "." for v in etat)


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
    for sigma in SYMETRIES:
        vue = etat if sigma is None else transformer(etat, sigma)
        k = cle(vue, moi)
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
            MEMOIRE["moi"], MEMOIRE["poses"] = suite[action], sum(v in PIONS for v in suite)
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
