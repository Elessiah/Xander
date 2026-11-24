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
cherche alors dans son vocabulaire (voir :mod:`xander.vocabulary`) un concept vrai pour
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
from xander import son_writer, vocabulary

RESULTS = {1: "victoire", 0: "nul", -1: "défaite"}


@dataclass
class Lesson:
    """Une erreur du fils, et ce que la mère en a tiré."""

    position: str      # cle(etat, moi) de la position (M : fils, A : adversaire)
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
        self.knowledge = son_writer.empty_knowledge(model)
        self._son = self._mind = None                # code du fils et espace de pensée, à réécrire
        self.max_views = 0                           # plus grand nombre de positions regardées par le fils
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
        if len(self.marks) == 2 and self.knowledge["marks"] != [self.marks[0], self.marks[1]]:
            self.knowledge["marks"] = [self.marks[0], self.marks[1]]
            self.rewrite()

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
        if pattern in self.knowledge["patterns"]:
            return mover  # la contre-épreuve a retrouvé un motif connu
        self.knowledge["patterns"].append(pattern)
        self.discovered.append(pattern)
        self.rewrite()
        return mover

    def counter_test(self, final: list, mover: int) -> list[int] | None:
        """Quels pions étaient nécessaires à la fin ? Rejoue la partie sans chacun d'eux.

        Un pion jugé inutile reste déplacé pour la suite des tests : si le
        dernier coup complétait deux motifs à la fois, on garde ainsi un motif
        entier au lieu de ce que les deux ont en commun. Un pion déplacé est
        testé de nouveau à sa nouvelle place, au cas où celle-ci aurait complété
        un autre motif.
        """
        lab = self.lab
        moves = list(lab.moves)
        last = self.cell(moves[-1])
        free = [i for i, v in enumerate(final) if v not in self.marks.values() and i != last]
        current = moves[:-1]
        needed: set[int] = set()   # indices des coups nécessaires
        to_test = list(range(mover, len(moves) - 1, 2))
        moved: set[int] = set()
        try:
            while to_test:
                index = to_test.pop(0)
                kept = None   # un déplacement après lequel la partie finit encore
                tested = necessary = False
                for replacement in free:
                    variant = current[:index] + [(replacement,)] + current[index + 1:]
                    if not lab.goto(variant) or lab.ended:
                        continue
                    tested = True
                    if lab.play(*moves[-1]) != "end":
                        necessary = True
                        break
                    if kept is None:
                        kept = replacement
                if not tested:
                    return None  # impossible à vérifier (plateau plein) : pas d'explication
                if necessary:
                    needed.add(index)
                elif index not in moved:
                    free.remove(kept)
                    free.append(self.cell(current[index]))
                    current[index] = (kept,)
                    moved.add(index)
                    to_test.append(index)  # à retester à sa nouvelle place
        finally:
            lab.goto(moves)
        if not needed:
            return None
        return sorted([last] + [self.cell(current[index]) for index in needed])

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

    # ------------------------------------------------------------------ #
    # Le code du fils, écrit par la mère
    # ------------------------------------------------------------------ #

    def rewrite(self) -> None:
        """Ce que sait la mère a changé : le code du fils sera réécrit."""
        self._son = self._mind = None

    def source(self, name: str = "fils") -> str:
        return son_writer.son_source(name, self.knowledge, len(self.records) - 1)

    @property
    def son(self):
        """Le fils tel que la mère l'a écrit (module exécuté à partir de son code)."""
        if self._son is None:
            self._son = son_writer.load(self.source())
        return self._son

    @property
    def mind(self):
        """La perception du jeu par la mère, avec tout son vocabulaire."""
        if self._mind is None:
            self._mind = son_writer.mind(self.knowledge)
        return self._mind

    # ------------------------------------------------------------------ #

    def play_game(self, opponent, son_side: int) -> tuple[int, list]:
        lab = self.lab
        lab.goto([])
        decisions = []
        while not lab.ended:
            if len(lab.moves) % 2 == son_side:
                state = lab.states[-1]
                cell, reason = self.son.choisir(list(state), self.marks[son_side])
                self.max_views = max(self.max_views, self.son.VUES)
                decisions.append((list(lab.moves), list(state), cell, reason))
                if lab.play(cell) == "refused":
                    raise LabError(f"le jeu refuse la case {cell}, que le fils croyait libre")
            else:
                lab.ask(opponent)
        winner = self.winner()
        return (0 if winner is None else 1 if winner == son_side else -1), decisions

    def review(self, decisions: list, son_side: int) -> list[Lesson]:
        lessons = []
        me = self.marks[son_side]
        for moves, state, son_cell, reason in decisions:
            teacher = self.teacher_move(moves)
            teacher_cell = self.cell(teacher)
            if teacher_cell == son_cell:
                continue
            if self.value(moves + [teacher], son_side) <= self.value(moves + [(son_cell,)], son_side):
                continue  # autre coup, mais pas meilleur
            lessons.append(self.correct(state, me, son_cell, reason, teacher_cell))
        return lessons

    def explain(self, state: list, me, son_cell, teacher_cell) -> str | None:
        """Le premier concept vrai pour le coup du professeur et faux pour celui du fils."""
        for name in vocabulary.concept_names():
            actions = getattr(self.mind, name)(list(state), me)
            if teacher_cell in actions and son_cell not in actions:
                return name
        return None

    def correct(self, state, me, son_cell, reason, teacher_cell) -> Lesson:
        """Explique l'erreur et réécrit le code du fils en conséquence."""
        self.rewrite()
        rules, memories = self.knowledge["rules"], self.knowledge["memories"]
        key = self.mind.cle(list(state), me)
        changes = []
        if reason == "souvenir":
            del memories[key]
            changes.append("souvenir faux oublié")
        explanation = self.explain(state, me, son_cell, teacher_cell)
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
