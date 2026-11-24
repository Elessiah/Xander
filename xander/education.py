"""Comment la mère élève son fils : jouer, se tromper, comprendre, corriger.

Déroulé ::

    exemple ──► 1re leçon : rejouer l'exemple et comprendre pourquoi il finit
       │
       ▼
    partie du fils (contre le professeur ou un joueur au hasard)
       │  fin de partie : la mère comprend qui a gagné et pourquoi (motifs)
       ▼
    revue de chaque décision du fils, avec back
       │  le professeur aurait-il joué autre chose ? était-ce vraiment mieux ?
       ▼
    explication : gagner ? parer ? fourchette ? …  ──► règle (ou souvenir)
       │
       └──► le fils corrigé joue la partie suivante

**Comprendre une fin de partie.** Quand une partie s'arrête, la mère cherche
le *motif* responsable, par contre-épreuve : pour chaque pion du joueur qui a
fini la partie, elle rejoue la partie (avec ``back``) en posant ce pion
ailleurs. Si la partie ne s'arrête plus, le pion était nécessaire. Les pions
nécessaires et le dernier coup forment le motif (au Morpion : un alignement).
Une fin sans motif est un match nul.

**Comprendre une erreur.** Pour chaque décision du fils, la mère revient à la
position, demande son coup au professeur, puis fait finir la partie au
professeur des deux côtés, après le coup du fils et après celui du professeur.
Si le coup du professeur mène à un meilleur résultat, c'est une erreur. Elle
cherche alors dans son vocabulaire (voir :mod:`xander.son`) un concept vrai pour
le coup du professeur et faux pour celui du fils :

* le concept devient une **règle** du fils, placée juste avant la règle qui
  l'a trompé : une seule erreur corrige toutes les positions semblables ;
* sans explication, la mère garde la position comme **souvenir**.

Limites : jeux à deux joueurs qui jouent chacun leur tour, état en tableau, et
action qui désigne directement une case (``SINGLE_TARGET_INDEX``).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from xander.game_model import GameModel
from xander.lab import Lab, LabError
from xander.model import FunctionOperation
from xander.parser import ParsedExample
from xander.son import VOCABULARY, Son, empty_knowledge, memory_key

RESULTS = {1: "victoire", 0: "nul", -1: "défaite"}


@dataclass
class Lesson:
    """Une erreur du fils, et ce que la mère en a tiré."""

    position: str      # memory_key de la position (M : fils, A : adversaire)
    son_cell: int
    son_reason: str
    teacher_cell: int
    explanation: str   # nom du concept, ou "souvenir"
    change: str        # ce qui a changé chez le fils

    def __str__(self) -> str:
        board = self.position
        return (f"{board} : le fils a joué {self.son_cell} ({self.son_reason}), "
                f"le professeur {self.teacher_cell} -> {self.explanation} ; {self.change}")


@dataclass
class GameRecord:
    number: int
    opponent: str
    son_side: str
    result: str
    lessons: list[Lesson] = field(default_factory=list)
    patterns: list[list[int]] = field(default_factory=list)  # motifs découverts pendant la partie

    def __str__(self) -> str:
        text = f"partie {self.number:>3} | fils {self.son_side} contre {self.opponent:<10} : {self.result:<8}"
        text += f" | {len(self.lessons)} erreur(s)"
        for pattern in self.patterns:
            text += f"\n      motif compris : {pattern}"
        for lesson in self.lessons:
            text += f"\n      {lesson}"
        return text


def random_player(rng: random.Random):
    """Adversaire faible : essaie des arguments au hasard jusqu'à ce que le jeu en accepte un."""
    def play(game):
        state = game.get_game_state()
        for argument in rng.sample(range(len(state)), len(state)):
            if game.play(argument) is not False:
                return
    play.__name__ = "hasard"
    return play


class Education:
    def __init__(self, parsed: ParsedExample, model: GameModel, teacher, seed: int = 0):
        operations = model.report.operations.get(model.action.name, []) if model.report and model.action else []
        if not any(op.kind is FunctionOperation.SINGLE_TARGET_INDEX for op in operations):
            raise LabError("l'Analyzer ne sait pas encore relier un argument de l'action à une case "
                           "(il faut SINGLE_TARGET_INDEX) : la mère ne peut pas encore éduquer de fils")
        self.parsed = parsed
        self.model = model
        self.lab = Lab(parsed, model)
        self.teacher = teacher
        self.rng = random.Random(seed)
        self.knowledge = empty_knowledge(model)
        self.son = Son(self.knowledge)
        self.marks: dict[int, object] = {}          # parité du coup -> pion posé
        self.outcomes: dict[tuple, int | None] = {}  # position -> parité du gagnant (None : nul)
        self.teacher_moves: dict[tuple, tuple] = {}
        self.discovered: list[list[int]] = []
        self.records: list[GameRecord] = []

    # ------------------------------------------------------------------ #
    # Perception
    # ------------------------------------------------------------------ #

    @staticmethod
    def cell(arguments: tuple) -> int:
        return arguments[0]  # SINGLE_TARGET_INDEX : l'argument est l'indice de la case

    def learn_marks(self) -> None:
        """Quel pion pose chaque joueur : la valeur qui apparaît dans la case jouée."""
        states = self.lab.states
        for k in range(len(states) - 1):
            if k % 2 not in self.marks:
                changed = [i for i, (a, b) in enumerate(zip(states[k], states[k + 1])) if a != b]
                if len(changed) == 1:
                    self.marks[k % 2] = states[k + 1][changed[0]]
        if len(self.marks) == 2:
            self.knowledge["marks"] = [self.marks[0], self.marks[1]]

    def final_state(self) -> list:
        lab = self.lab
        if not lab.ended:
            return list(lab.states[-1])
        state = list(lab.states[-1])
        state[self.cell(lab.moves[-1])] = self.marks[(len(lab.moves) - 1) % 2]
        return state

    # ------------------------------------------------------------------ #
    # Comprendre une fin de partie
    # ------------------------------------------------------------------ #

    def winner(self) -> int | None:
        """Parité du gagnant de la partie terminée du labo, ``None`` pour un nul."""
        lab = self.lab
        self.learn_marks()
        mover = (len(lab.moves) - 1) % 2
        final = self.final_state()
        last = self.cell(lab.moves[-1])
        mine = {i for i, v in enumerate(final) if v == self.marks[mover]}
        if any(last in p and set(p) <= mine for p in self.knowledge["patterns"]):
            return mover
        pattern = self.counter_test(final, mover)
        if pattern is None:
            return None
        self.knowledge["patterns"].append(pattern)
        self.discovered.append(pattern)
        return mover

    def counter_test(self, final: list, mover: int) -> list[int] | None:
        """Quels pions étaient nécessaires à la fin ? Rejoue la partie sans chacun d'eux."""
        lab = self.lab
        moves = list(lab.moves)
        last = self.cell(moves[-1])
        free = [i for i, v in enumerate(final) if v not in self.marks.values() and i != last]
        needed = [last]
        try:
            for index in range(mover, len(moves) - 1, 2):
                tested = necessary = False
                for replacement in free:
                    variant = moves[:index] + [(replacement,)] + moves[index + 1:-1]
                    if not lab.goto(variant) or lab.ended:
                        continue
                    tested = True
                    if lab.play(*moves[-1]) != "end":
                        necessary = True
                        break
                if not tested:
                    return None  # impossible à vérifier (plateau plein) : pas d'explication
                if necessary:
                    needed.append(self.cell(moves[index]))
        finally:
            lab.goto(moves)
        return sorted(needed) if len(needed) > 1 else None

    # ------------------------------------------------------------------ #
    # Le professeur
    # ------------------------------------------------------------------ #

    def key(self) -> tuple:
        return repr(self.lab.states[-1]), len(self.lab.moves) % 2

    def teacher_move(self, moves: list[tuple]) -> tuple:
        self.lab.goto(moves)
        key = self.key()
        if key not in self.teacher_moves:
            self.teacher_moves[key] = self.lab.ask(self.teacher)
            self.lab.undo()
        return self.teacher_moves[key]

    def value(self, moves: list[tuple], side: int) -> int:
        """Résultat pour ``side`` si le professeur finit la partie des deux côtés."""
        lab = self.lab
        lab.goto(moves)
        if lab.ended:
            winner = self.winner()
        else:
            key = self.key()
            if key not in self.outcomes:
                start = list(lab.moves)
                while not lab.ended:
                    lab.ask(self.teacher)
                self.outcomes[key] = self.winner()
                lab.goto(start)
            winner = self.outcomes[key]
        return 0 if winner is None else (1 if winner == side else -1)

    # ------------------------------------------------------------------ #
    # Parties et corrections
    # ------------------------------------------------------------------ #

    def first_lesson(self) -> GameRecord:
        """Rejoue l'exemple et comprend pourquoi il se termine."""
        action = self.model.action.name
        moves = [tuple(f.arguments) for f in self.parsed.player_functions() if f.name == action]
        lab = self.lab
        lab.goto([])
        for arguments in moves:
            outcome = lab.play(*arguments)
            if outcome == "refused":
                raise LabError(f"le coup {arguments} de l'exemple est refusé par le jeu")
            if outcome == "moved":  # la mère vérifie qu'elle a bien compris l'action
                before, after = lab.states[-2], lab.states[-1]
                changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
                if changed != [self.cell(arguments)]:
                    raise LabError(f"{self.model.action.short_name}{arguments} a changé les cases {changed}, "
                                   f"pas la case {self.cell(arguments)} : l'Analyzer doit d'abord mieux "
                                   "comprendre l'action, la mère ne peut pas encore éduquer de fils")
        self.learn_marks()
        record = GameRecord(0, "exemple", "-", "terminé" if lab.ended else "inachevé")
        if lab.ended:
            winner = self.winner()
            record.result = "nul" if winner is None else f"gagné par {self.marks[winner]}"
        record.patterns, self.discovered = self.discovered, []
        self.records.append(record)
        return record

    def play_game(self, opponent, son_side: int) -> tuple[int, list]:
        lab = self.lab
        lab.goto([])
        decisions = []
        while not lab.ended:
            if len(lab.moves) % 2 == son_side:
                state = lab.states[-1]
                me, opp = self.marks[son_side], self.marks[1 - son_side]
                cell, reason = self.son.choose(state, me, opp)
                decisions.append((list(lab.moves), list(state), cell, reason))
                if lab.play(cell) == "refused":
                    raise LabError(f"le jeu refuse la case {cell}, que le fils croyait libre")
            else:
                lab.ask(opponent)
        winner = self.winner()
        return (0 if winner is None else 1 if winner == son_side else -1), decisions

    def review(self, decisions: list, son_side: int) -> list[Lesson]:
        lessons = []
        me, opp = self.marks[son_side], self.marks[1 - son_side]
        for moves, state, son_cell, reason in decisions:
            teacher = self.teacher_move(moves)
            teacher_cell = self.cell(teacher)
            if teacher_cell == son_cell:
                continue
            if self.value(moves + [teacher], son_side) <= self.value(moves + [(son_cell,)], son_side):
                continue  # autre coup, mais pas meilleur
            lessons.append(self.correct(state, me, opp, son_cell, reason, teacher_cell))
        return lessons

    def explain(self, state: list, me, opp, son_cell: int, teacher_cell: int) -> str | None:
        view = self.son.view(state, me, opp)
        for name, concept in VOCABULARY.items():
            cells = concept(view)
            if teacher_cell in cells and son_cell not in cells:
                return name
        return None

    def correct(self, state, me, opp, son_cell, reason, teacher_cell) -> Lesson:
        rules, memories = self.knowledge["rules"], self.knowledge["memories"]
        key = memory_key(state, me, opp)
        changes = []
        if reason == "souvenir":
            del memories[key]
            changes.append("souvenir faux oublié")
        explanation = self.explain(state, me, opp, son_cell, teacher_cell)
        if explanation is None:
            memories[key] = teacher_cell
            changes.append("nouveau souvenir")
            return Lesson(key, son_cell, reason, teacher_cell, "souvenir", ", ".join(changes))
        if explanation in rules and reason in rules and rules.index(explanation) > rules.index(reason):
            rules.remove(explanation)
        if explanation not in rules:
            position = rules.index(reason) if reason in rules else len(rules)
            rules.insert(position, explanation)
            changes.append(f"règles : {' > '.join(rules)}")
        return Lesson(key, son_cell, reason, teacher_cell, explanation, ", ".join(changes) or "déjà su")

    def train(self, nb_games: int, on_game=None) -> list[GameRecord]:
        """Fait jouer et corrige le fils ``nb_games`` fois (professeur et hasard, des deux côtés)."""
        if not self.records:
            record = self.first_lesson()
            if on_game:
                on_game(record)
        if len(self.marks) < 2:
            raise LabError("la mère n'a pas compris quel pion pose chaque joueur")
        opponents = [("professeur", self.teacher), ("hasard", random_player(self.rng))]
        for number in range(1, nb_games + 1):
            name, opponent = opponents[(number - 1) // 2 % 2]
            side = (number - 1) % 2
            result, decisions = self.play_game(opponent, side)
            record = GameRecord(len(self.records), name, str(self.marks[side]), RESULTS[result])
            record.lessons = self.review(decisions, side)
            record.patterns, self.discovered = self.discovered, []
            self.records.append(record)
            if on_game:
                on_game(record)
        return self.records

    def evaluate(self, nb_random: int = 100) -> dict[str, dict[str, int]]:
        """Fait jouer le fils sans le corriger : bilan par adversaire."""
        scores = {}
        for name, opponent, games in (("professeur", self.teacher, 2),
                                      ("hasard", random_player(random.Random(1)), nb_random)):
            score = {"victoire": 0, "nul": 0, "défaite": 0}
            for number in range(games):
                result, _ = self.play_game(opponent, number % 2)
                score[RESULTS[result]] += 1
            scores[name] = score
        self.discovered = []
        return scores
