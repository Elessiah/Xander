"""Comment la mère écrit le code de son fils.

Le fils est un fichier Python autonome (il n'importe rien de Xander) que la
mère écrit, puis réécrit à chaque correction. Il a trois parties :

1. **Perception** : ``possibles``, ``apres``, ``gagne``, ``adversaire``, écrites
   à partir de ce que la mère a compris du jeu (action décrite par l'Analyzer,
   pions observés, motifs trouvés par contre-épreuve).
2. **Règles** : le texte des concepts que la mère lui a appris, et seulement
   ceux-là (voir :mod:`xander.vocabulary`), dans l'ordre de priorité appris,
   plus ses souvenirs.
3. **Squelette** : l'ordre de décision (souvenir, règles, défaut) et la
   fonction ``play(game)``. Écrit à la naissance ; c'est là qu'on pourra plus
   tard transmettre l'expérience de ses frères.

Le fils compte les positions qu'il regarde (``VUES``, incrémenté par
``apres``) : c'est le budget de réflexion vérifié par les tests.
"""

from __future__ import annotations

import types
from pprint import pformat

from xander import vocabulary


def empty_knowledge(model) -> dict:
    """Ce que la mère sait au départ pour écrire un fils : comment lire et jouer."""
    return {
        "getter": model.getter.short_name,
        "action": model.action.short_name,
        "end_signal": model.end_signal,
        "marks": [],        # pions posés par chaque joueur (« X », « O »)
        "patterns": [],     # motifs qui finissent la partie, compris par contre-épreuve
        "rules": [],        # concepts appris, du plus prioritaire au moins prioritaire
        "memories": {},     # cle(etat, moi) -> action
    }


def perception_source(knowledge: dict) -> str:
    """Les quatre notions, pour un état en tableau dont l'action désigne une case."""
    return f'''# --- Perception (écrite par la mère) -------------------------------------
# L'Analyzer a compris que l'action désigne une case (SINGLE_TARGET_INDEX) ;
# la mère a vu quel pion pose chaque joueur et quels motifs finissent la partie.

PIONS = {knowledge["marks"]!r}
MOTIFS = {pformat(knowledge["patterns"], compact=True, width=70)}
VUES = 0  # positions regardées pendant le coup en cours


def possibles(etat):
    return [i for i, valeur in enumerate(etat) if valeur not in PIONS]


def apres(etat, action, joueur):
    global VUES
    VUES += 1
    suite = list(etat)
    suite[action] = joueur
    return suite


def gagne(etat, joueur):
    return any(all(etat[case] == joueur for case in motif) for motif in MOTIFS)


def adversaire(joueur):
    return PIONS[1] if joueur == PIONS[0] else PIONS[0]


def cle(etat, moi):
    """La position vue de mon côté : M mes pions, A les siens, . libre."""
    lui = adversaire(moi)
    return "".join("M" if v == moi else "A" if v == lui else "." for v in etat)


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
    rules = knowledge["rules"]
    parts = ["# --- Règles apprises (recopiées du vocabulaire de la mère) ---------------"]
    if rules:
        parts.append(vocabulary.tools_source())
        parts += [vocabulary.concept_source(name) for name in rules]
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
    coup = SOUVENIRS.get(cle(etat, moi))
    if coup is not None and coup in possibles(etat):
        return coup, "souvenir"
    for regle in REGLES:
        coups = regle(etat, moi)
        if coups:
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
    """L'espace où la mère pense : sa perception du jeu et tout son vocabulaire."""
    source = "\n\n".join([perception_source(knowledge), vocabulary.tools_source()]
                         + [vocabulary.source(concept) for concept in vocabulary.CONCEPTS])
    return load(source, "mere")
