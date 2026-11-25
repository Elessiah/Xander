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
        "marks": [],        # pions posés par chaque joueur (« X », « O »)
        "patterns": [],     # motifs qui finissent la partie, compris par contre-épreuve
        "concepts": {},     # nom -> arbre de concept construit par la mère (une brique)
        "rules": [],        # concepts appris comme règles, du plus prioritaire au moins prioritaire
        "memories": {},     # cle(etat, moi) -> action
        "symmetries": [],   # renumérotations des cases qui ne changent rien au jeu (vérifiées)
    }


def symmetries_literal(knowledge: dict) -> str:
    return pformat([None] + knowledge["symmetries"], compact=True, width=70)


def apres_source(effect: effets.Hypothese) -> str:
    """``apres`` à partir du programme que la mère a trouvé pour décrire l'action.

    Pour un tableau, le programme dit quelles cases changent ; elles reçoivent
    le pion du joueur (supposé à la main : la mère ne décrit pas encore la
    valeur écrite). Pour un nombre, il donne directement la nouvelle valeur.
    """
    if effect.forme == effets.CHANGEES:
        body = """    suite = list(etat)
    for case in changees(etat, (action,)):
        suite[case] = joueur
    return suite"""
    else:
        body = "    return valeur_apres(etat, (action,))"
    return f"""{effets.source(effect)}

def apres(etat, action, joueur):
    global VUES
    VUES += 1
{body}
"""


def perception_source(knowledge: dict) -> str:
    """Les quatre notions, pour un état en tableau."""
    return f'''# --- Perception (écrite par la mère) -------------------------------------
# L'action est décrite par le programme que la mère a construit (Analyzer) ;
# elle a vu quel pion pose chaque joueur et quels motifs finissent la partie.

PIONS = {knowledge["marks"]!r}
MOTIFS = {pformat(knowledge["patterns"], compact=True, width=70)}
VUES = 0  # positions regardées pendant le coup en cours


def possibles(etat):
    return [i for i, valeur in enumerate(etat) if valeur not in PIONS]


{apres_source(knowledge["effect"])}

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


def rappel(etat, moi, souvenirs):
    """Un souvenir de cette position, ou d'une position équivalente : (sa clé, mon coup ici)."""
    for sigma in SYMETRIES:
        vue = etat if sigma is None else transformer(etat, sigma)
        k = cle(vue, moi)
        if k in souvenirs:
            coup = souvenirs[k]
            return k, (coup if sigma is None else sigma.index(coup))
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
            joue = changees(etat, (action,))  # mon pion : ce qui est apparu là où j'ai joué
            MEMOIRE["moi"] = next((suite[c] for c in joue if suite[c] in PIONS), moi)
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
