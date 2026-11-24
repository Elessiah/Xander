"""Le fils : un joueur entièrement décrit par ce que la mère lui a appris.

Le fils ne cherche pas, ne simule pas et **n'utilise jamais ``back``**. À son
tour, il lit l'état et applique, dans l'ordre :

1. ses **souvenirs** : positions précises où la mère lui a montré le bon coup ;
2. ses **règles**, rangées par priorité par la mère (``gagner``, ``parer``…) ;
3. son choix par défaut : la première case libre.

Tout ce qui fait sa force (les motifs gagnants, les règles, leur ordre, les
souvenirs) se trouve dans ``knowledge`` et vient des corrections de la mère.

Les règles sont écrites avec un **vocabulaire** général, défini sur des motifs
et des cases, et non sur un jeu en particulier : un *motif* est un ensemble de
cases qui, toutes occupées par le même joueur, terminent la partie. Ce
vocabulaire est fourni à la main pour l'instant ; l'objectif est que la mère
finisse par le découvrir seule.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class View:
    """Une position vue par le joueur ``me``."""

    state: list
    me: object
    opp: object
    patterns: list[list[int]]
    free: set[int]

    def with_move(self, cell: int, mark) -> View:
        state = list(self.state)
        state[cell] = mark
        return View(state, self.me, self.opp, self.patterns, self.free - {cell})


def completing_cells(view: View, mark) -> set[int]:
    """Cases libres qui complètent un motif pour ``mark`` (il ne manque qu'elles)."""
    cells = set()
    for pattern in view.patterns:
        missing = [c for c in pattern if view.state[c] != mark]
        if len(missing) == 1 and missing[0] in view.free:
            cells.add(missing[0])
    return cells


def gagner(view: View) -> set[int]:
    """Je complète un de mes motifs : la partie est gagnée."""
    return completing_cells(view, view.me)


def parer(view: View) -> set[int]:
    """L'adversaire complètera un motif au prochain coup : je prends la case."""
    return completing_cells(view, view.opp)


def fourchette(view: View) -> set[int]:
    """Je crée deux menaces à la fois : l'adversaire ne pourra en parer qu'une."""
    return {c for c in view.free if len(completing_cells(view.with_move(c, view.me), view.me)) >= 2}


def contre_fourchette(view: View) -> set[int]:
    """Je prends la case où l'adversaire créerait deux menaces à la fois."""
    return {c for c in view.free if len(completing_cells(view.with_move(c, view.opp), view.opp)) >= 2}


def carrefour(view: View) -> set[int]:
    """Je prends la case libre qui sert au plus grand nombre de motifs encore possibles."""
    open_patterns = [p for p in view.patterns if all(view.state[c] != view.opp for c in p)]
    counts = {c: sum(c in p for p in open_patterns) for c in view.free}
    best = max(counts.values(), default=0)
    return {c for c, n in counts.items() if n == best} if best else set()


#: Le vocabulaire avec lequel la mère explique un coup et écrit une règle.
VOCABULARY = {
    "gagner": gagner,
    "parer": parer,
    "fourchette": fourchette,
    "contre_fourchette": contre_fourchette,
    "carrefour": carrefour,
}


def memory_key(state: list, me, opp) -> str:
    """Position vue de mon côté : ``M`` mes pions, ``A`` ceux de l'adversaire, ``.`` libre."""
    return "".join("M" if v == me else "A" if v == opp else "." for v in state)


def empty_knowledge(model) -> dict:
    """Ce que sait un fils qui vient de naître : comment lire et jouer, rien de plus."""
    return {
        "getter": model.getter.short_name,
        "action": model.action.short_name,
        "end_signal": model.end_signal,
        "marks": [],        # valeurs que posent les joueurs (« X », « O »)
        "patterns": [],     # motifs gagnants, appris par la mère
        "rules": [],        # noms du vocabulaire, du plus prioritaire au moins prioritaire
        "memories": {},     # memory_key -> case
    }


class Son:
    def __init__(self, knowledge: dict):
        self.knowledge = knowledge
        self.me = None
        self.last_occupied = 0

    # ------------------------------------------------------------------ #
    # Décision : uniquement à partir de l'état et des connaissances
    # ------------------------------------------------------------------ #

    def view(self, state: list, me, opp) -> View:
        marks = self.knowledge["marks"]
        free = {i for i, v in enumerate(state) if v not in marks}
        return View(list(state), me, opp, self.knowledge["patterns"], free)

    def choose(self, state: list, me, opp) -> tuple[int, str]:
        """Case choisie et raison du choix (``souvenir``, nom de règle ou ``défaut``)."""
        view = self.view(state, me, opp)
        if not view.free:
            raise ValueError("aucune case libre")
        memory = self.knowledge["memories"].get(memory_key(state, me, opp))
        if memory is not None and memory in view.free:
            return memory, "souvenir"
        for rule in self.knowledge["rules"]:
            cells = VOCABULARY[rule](view)
            if cells:
                return min(cells), rule
        return min(view.free), "défaut"

    # ------------------------------------------------------------------ #
    # Jouer sur une vraie partie (sans back)
    # ------------------------------------------------------------------ #

    def sides(self, state: list):
        """Devine quel pion est le mien : celui que j'ai posé, sinon celui qui manque."""
        marks = self.knowledge["marks"]
        counts = {m: sum(v == m for v in state) for m in marks}
        occupied = sum(counts.values())
        if occupied < self.last_occupied or occupied <= 1:
            self.me = None  # nouvelle partie
        if self.me is None:
            present = [m for m in marks if counts[m]]
            if len(present) == 1:
                self.me = next(m for m in marks if m != present[0])
            elif len(present) == 2 and counts[marks[0]] != counts[marks[1]]:
                self.me = min(marks, key=counts.get)
        me = self.me if self.me is not None else marks[0]
        return me, next(m for m in marks if m != me)

    def play(self, game):
        """Joue un tour sur ``game`` ; renvoie ce que renvoie l'action du jeu."""
        knowledge = self.knowledge
        state = getattr(game, knowledge["getter"])()
        me, opp = self.sides(state)
        cell, _ = self.choose(state, me, opp)
        free = [cell] + sorted(i for i, v in enumerate(state) if v not in knowledge["marks"] and i != cell)
        for cell in free:  # si le jeu refuse, l'état ne change pas : rien à défaire
            result = getattr(game, knowledge["action"])(cell)
            if type(result) is type(knowledge["end_signal"]) and result == knowledge["end_signal"]:
                return result
            after = getattr(game, knowledge["getter"])()
            if after != state:
                self.me = after[cell]
                self.last_occupied = sum(v in knowledge["marks"] for v in after)
                return result
        raise RuntimeError("le jeu a refusé toutes les cases libres")
