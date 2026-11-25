"""Comment la mère élève son fils : jouer, se tromper, comprendre, corriger.

Déroulé ::

    exemple ──► 1re leçon : rejouer l'exemple et comprendre pourquoi il finit
       │
       ▼
    partie du fils (contre le professeur, le hasard ou un adversaire mixte)
       │  fin de partie : la mère comprend qui a gagné et pourquoi (motifs)
       ▼
    revue de chaque décision du fils, avec back
       │  le professeur aurait-il joué autre chose ? était-ce vraiment mieux ?
       │  et s'il avait joué ailleurs ? (variantes de l'adversaire)
       ▼
    chaque erreur ──► souvenir ; puis refactor : souvenirs ──► règle (concept construit)
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
Si le coup du professeur mène à un meilleur résultat, c'est une erreur.

**Corriger cas par cas, puis refactoriser.** La mère part sans aucun concept.
Chaque erreur devient d'abord un **souvenir** (dans cette position, jouer le
coup du professeur) et un **cas** enregistré. Après chaque partie, elle cherche
le plus petit concept (voir :mod:`xander.concepts`) vrai après le coup du
professeur et faux après celui du fils dans au moins deux souvenirs. Elle
l'essaie comme règle, à chaque rang de priorité en partant du plus bas : si le
fils joue encore bien dans **tous** les cas enregistrés (les cas sont les tests
du refactor) et qu'au moins deux souvenirs deviennent inutiles, elle les
remplace par la règle. Le concept devient une brique pour les suivants.

Limites : jeux à deux joueurs qui jouent chacun leur tour, état en tableau, et
action qui désigne directement une case (la mère a trouvé
``changees = case(arg0)``, voir :data:`CASE_DESIGNEE`). Le ``apres`` du fils
est le programme trouvé ; les cases changées reçoivent le pion du joueur.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field

from xander.game_model import GameModel
from xander.lab import Lab, LabError
from xander.parser import ParsedExample
from xander import concepts, effets, son_writer, symmetries
from xander.concepts import MOI

RESULTS = {1: "victoire", 0: "nul", -1: "défaite"}

#: Pont provisoire : le ``apres`` du fils et de la mère vient du programme
#: qu'elle a trouvé, mais son raisonnement (contre-épreuve, symétries, coup du
#: professeur) relie encore l'argument d'un coup à la case jouée. Elle vérifie
#: donc que « la case d'indice ``arg0`` » fait partie de ses hypothèses.
CASE_DESIGNEE = effets.Hypothese(effets.CHANGEES, effets.case(effets.arg(0)))

#: Le fils pense comme un joueur humain : il reconnaît, il ne calcule pas tout.
#: La mère refuse une règle qui lui ferait regarder plus de positions pour un coup.
BUDGET = 1000

#: Coups que la mère joue dans son labo pour mettre à l'épreuve la description de l'action.
EXPERIENCES = 40
#: Parties au hasard qui fournissent des positions où faire ces expériences.
PARTIES_D_ESSAI = 8


@dataclass
class Lesson:
    """Une erreur du fils, et ce que la mère en a tiré."""

    position: str      # cle(etat, moi) de la position (M : fils, A : adversaire)
    son_cell: int
    son_reason: str
    teacher_cell: int
    explanation: str   # "souvenir" : la mère corrige d'abord le cas
    change: str        # ce qui a changé chez le fils

    def __str__(self) -> str:
        board = self.position
        return (f"{board} : le fils a joué {self.son_cell} ({self.son_reason}), "
                f"le professeur {self.teacher_cell} -> {self.explanation} ; {self.change}")


@dataclass
class Case:
    """Une position revue par la mère, qui sert ensuite de test aux refactors.

    Une erreur du fils y laisse un souvenir ; une position bien jouée reste un
    test de non-régression (un refactor ne doit pas la faire mal jouer).
    """

    moves: list[tuple]   # la partie jusqu'à la position (pour y revenir dans le labo)
    state: list
    me: object
    key: str
    son_cell: int
    teacher_cell: int


@dataclass
class GameRecord:
    number: int
    opponent: str
    son_side: str
    result: str
    lessons: list[Lesson] = field(default_factory=list)
    patterns: list[list[int]] = field(default_factory=list)  # motifs découverts pendant la partie
    refactors: list[str] = field(default_factory=list)       # souvenirs remplacés par une règle

    def __str__(self) -> str:
        text = f"partie {self.number:>3} | fils {self.son_side} contre {self.opponent:<10} : {self.result:<8}"
        text += f" | {len(self.lessons)} erreur(s)"
        for pattern in self.patterns:
            text += f"\n      motif compris : {pattern}"
        for lesson in self.lessons:
            text += f"\n      {lesson}"
        for refactor in self.refactors:
            text += f"\n      refactor : {refactor}"
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


def mixed_player(teacher, rng: random.Random):
    """Adversaire imprévisible : une fois sur deux le coup du professeur, sinon un coup au hasard.

    Il crée des menaces comme le professeur, mais pas toujours les mêmes : le
    fils rencontre ainsi des positions variées et difficiles.
    """
    randomly = random_player(rng)

    def play(game):
        (teacher if rng.random() < 0.5 else randomly)(game)
    play.__name__ = "mixte"
    return play


@dataclass
class Trials:
    """Les expériences de la mère sur l'action : ce qui a résisté, ce qui a été réfuté et par quoi."""

    survivors: list
    played: int = 0
    refutations: dict = field(default_factory=dict)  # hypothèse -> cas qui la contredit

    def describe(self) -> str:
        text = f"{self.survivors[0]!r}" if self.survivors else "rien"
        if len(self.survivors) > 1:
            others = ", ".join(map(repr, self.survivors[1:]))
            text += f" (indiscernable de {others})"
        refuted = f", {len(self.refutations)} réfutée(s)" if self.refutations else ""
        return f"{text} : {self.played} expérience(s) dans le labo{refuted}"


class Education:
    def __init__(self, parsed: ParsedExample, model: GameModel, teacher, seed: int = 0):
        operations = model.report.operations.get(model.action.name, []) if model.report and model.action else []
        state = model.getter.return_value.name if model.getter else None
        effects = [op.programme for op in operations
                   if op.variable.name == state and op.programme.forme == effets.CHANGEES]
        if not effects:
            raise LabError("l'Analyzer n'a pas trouvé quelles cases change l'action : "
                           "la mère ne peut pas encore éduquer de fils")
        self.parsed = parsed
        self.model = model
        self.lab = Lab(parsed, model)
        self.teacher = teacher
        self.seed = seed
        self.rng = random.Random(seed)
        self.knowledge = son_writer.empty_knowledge(model)
        self.trials = self.test_effects(effects)
        survivors = self.trials.survivors
        if CASE_DESIGNEE not in survivors:
            raise LabError(f"la mère raisonne encore sur la case jouée et il lui faut {CASE_DESIGNEE!r}, "
                           f"elle a gardé {survivors} : elle ne peut pas encore éduquer de fils")
        # Les programmes qui restent ont résisté à toutes les expériences : quand il en reste
        # plusieurs, aucune ne les a départagés, et la mère prend le premier trouvé.
        self.knowledge["effect"] = survivors[0]
        self._son = self._mind = None                # code du fils et espace de pensée, à réécrire
        self.max_views = 0                           # plus grand nombre de positions regardées par le fils
        self.marks: dict[int, object] = {}          # parité du coup -> pion posé
        self.outcomes: dict[tuple, int | None] = {}  # position -> parité du gagnant (None : nul)
        self.teacher_moves: dict[tuple, tuple] = {}
        self.discovered: list[list[int]] = []
        self.records: list[GameRecord] = []
        self.cases: dict[str, Case] = {}            # cle de la position -> cas enregistré
        self._pensee = None                          # évalue les concepts (à refaire si le jeu est mieux compris)
        self._bank = None                            # concepts énumérés par taille (à refaire si une brique s'ajoute)
        self._judged: dict = {}                      # (cas, coup) -> aussi bon que le professeur ?
        self._symmetries_known = False               # à chercher de nouveau si un motif s'ajoute
        self._shapes_known = False                   # motifs à essayer décalés (idem)
        self._shifts_tried: set = set()              # motifs décalés déjà essayés dans le labo
        self.max_size, self.max_depth = 6, 2         # bornes de la recherche de concepts
        self.counts = (1,)                           # valeurs de k dans AuMoins(k, …) : « il existe »
        self.budget = BUDGET                         # positions que le fils peut regarder pour un coup

    # ------------------------------------------------------------------ #
    # Mettre à l'épreuve la description de l'action
    # ------------------------------------------------------------------ #

    def test_effects(self, effects: list) -> Trials:
        """Joue dans le labo des coups que l'exemple ne montrait pas, pour réfuter ou départager.

        Les positions viennent de l'exemple et de parties jouées au hasard ; les
        arguments essayés sont les valeurs vues dans les arguments de l'exemple.
        La mère joue d'abord les expériences qui départagent les hypothèses
        restantes (elles n'annoncent pas toutes la même chose), puis d'autres,
        au hasard en partant des positions les plus proches du début, pour
        tenter de réfuter ce qui reste. Si plus rien ne
        résiste, elle sait qu'elle n'a pas compris l'action.
        """
        rng, lab, trials = random.Random(f"effets-{self.seed}"), self.lab, Trials(list(effects))
        calls = [f for f in self.parsed.player_functions() if f.name == self.model.action.name]
        values = list(dict.fromkeys(a for f in calls for a in f.arguments))
        width = len(self.model.action.parameters)
        candidates = list(itertools.product(values, repeat=width))[:200]
        example = [tuple(f.arguments) for f in calls]
        seen = {(tuple(example[:k]), example[k]) for k in range(len(example))}

        positions = []  # (coups, état)
        if lab.goto([]):
            positions.append(([], lab.states[-1]))
        for k in range(1, len(example)):
            if lab.goto(example[:k]) and not lab.ended:
                positions.append((example[:k], lab.states[-1]))
        for _ in range(PARTIES_D_ESSAI):
            moves: list[tuple] = []
            lab.goto([])
            while len(moves) < 4 * max(len(example), 1):
                for arguments in rng.sample(candidates, len(candidates)):
                    outcome = lab.play(*arguments)
                    if outcome == "moved":
                        moves.append(arguments)
                        positions.append((list(moves), lab.states[-1]))
                        break
                    if outcome == "end":
                        lab.undo()
                else:
                    break  # aucun coup ne fait avancer la partie sans la finir
        experiences = [(m, state, a) for m, state in positions for a in candidates
                       if (tuple(m), a) not in seen]
        rng.shuffle(experiences)
        experiences.sort(key=lambda e: len(e[0]))  # d'abord près du début : le contre-exemple le plus simple

        survivors = trials.survivors
        while trials.played < EXPERIENCES and survivors and experiences:
            index = next((i for i, (_, state, a) in enumerate(experiences)
                          if effets.decisive(survivors, state, a)), 0)
            moves, _, arguments = experiences.pop(index)
            if not lab.goto(moves) or lab.ended:
                continue
            before = lab.states[-1]
            trials.played += 1
            try:
                outcome = lab.play(*arguments)
            except Exception:  # le jeu ne supporte pas cette expérience : on repart d'une partie neuve
                lab.new_game()
                continue
            if outcome == "moved":
                case = effets.Cas(before, arguments, lab.states[-1])
                kept = effets.departager(survivors, case)
                for hypothesis in survivors:
                    if hypothesis not in kept:
                        trials.refutations[hypothesis] = case
                survivors = trials.survivors = kept
            if outcome != "refused":
                lab.undo()
        lab.goto([])
        if not survivors:
            case = next(iter(trials.refutations.values()))
            call = f"{self.model.action.short_name}({', '.join(map(repr, case.arguments))})"
            raise LabError(f"le labo a réfuté {effects} : sur {case.valeur_avant}, {call} a changé "
                           f"les cases {sorted(case.cible())} ; l'Analyzer doit d'abord mieux comprendre l'action")
        return trials

    # ------------------------------------------------------------------ #
    # Perception
    # ------------------------------------------------------------------ #

    @staticmethod
    def cell(arguments: tuple) -> int:
        return arguments[0]  # CASE_DESIGNEE : l'argument est l'indice de la case

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
            self.rethink()

    def final_state(self) -> list:
        lab = self.lab
        if not lab.ended:
            return list(lab.states[-1])
        return self.mind.apres(list(lab.states[-1]), *lab.moves[-1], self.marks[(len(lab.moves) - 1) % 2])

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
        self.rethink()
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
    # Situations équivalentes
    # ------------------------------------------------------------------ #

    def shift_patterns(self) -> list[str]:
        """« Ce motif marcherait-il ailleurs ? » La mère essaie chaque motif décalé (chaque
        case + d) et le joue dans le labo. Elle ne sait rien de la forme du plateau : un
        décalage qui déborde d'une rangée sur la suivante ne finit pas la partie, et il est
        rejeté.
        """
        size, patterns, done = len(self.lab.states[0]), self.knowledge["patterns"], []
        grown = True
        while grown:
            grown = False
            for pattern in list(patterns):
                for shift in range(1 - size, size):
                    image = [cell + shift for cell in pattern]
                    if (not shift or image[0] < 0 or image[-1] >= size or image in patterns
                            or tuple(image) in self._shifts_tried):
                        continue
                    self._shifts_tried.add(tuple(image))
                    found = self.play_pattern(image)
                    if found is not None and found not in patterns:
                        patterns.append(found)
                        self.discovered.append(found)
                        grown = True
                        done.append(f"motif {found} : le motif {pattern} décalé de {shift:+d}, "
                                    "vérifié dans le labo")
        if done:
            self.rethink()
        self._shapes_known = True
        self.lab.goto([])
        return done

    def play_pattern(self, cells: list[int]) -> list[int] | None:
        """Le premier joueur pose ses pions sur ``cells`` (l'autre joue ailleurs) : si la partie
        finit au dernier pion, la contre-épreuve dit quel motif l'a finie."""
        others = [c for c in range(len(self.lab.states[0])) if c not in cells]
        for start in range(len(others)):
            replies = (others[start:] + others[:start])[:len(cells) - 1]
            if len(replies) < len(cells) - 1:
                return None
            moves = []
            for mine, his in zip(cells, replies + [None]):
                moves.append((mine,))
                if his is not None:
                    moves.append((his,))
            if self.lab.goto(moves) and self.lab.ended:
                return self.counter_test(self.final_state(), 0)
        return None

    def abstract(self, state) -> tuple:
        """Ce qui compte d'une position : les pions (une case libre n'a pas d'identité)."""
        marks = self.knowledge["marks"]
        return tuple(v if v in marks else None for v in state)

    def probe_games(self, number: int = 20) -> list:
        """Des parties jouées au hasard dans le labo, jusqu'au bout."""
        rng, lab, games = random.Random(len(self.knowledge["patterns"])), self.lab, []
        for _ in range(number):
            lab.goto([])
            while not lab.ended:
                lab.play(rng.choice(self.mind.possibles(list(lab.states[-1]))))
            games.append((list(lab.moves), [self.abstract(s) for s in lab.states]))
        return games

    def symmetric_in_lab(self, sigma: list[int], games: list) -> bool:
        """Le jeu renuméroté se joue-t-il exactement comme le jeu ? (vérifié avec ``back``)"""
        lab = self.lab
        for moves, states in games:
            if not lab.goto([(sigma[self.cell(m)],) for m in moves]) or not lab.ended:
                return False
            if len(lab.states) != len(states) or any(
                    self.abstract(s) != tuple(symmetries.transform(t, sigma))
                    for s, t in zip(lab.states, states)):
                return False
        return True

    def discover_symmetries(self) -> str | None:
        """Cherche les renumérotations qui ne changent rien au jeu et les vérifie dans le labo."""
        self._symmetries_known = True
        size = len(self.lab.states[0])
        found = symmetries.candidates(size, self.knowledge["patterns"])
        if found is None:
            return None  # trop de candidates : les motifs ne disent pas encore assez
        identity = list(range(size))
        games = self.probe_games()
        kept = [s for s in found if s != identity and self.symmetric_in_lab(s, games)]
        self.lab.goto([])
        if kept == self.knowledge["symmetries"]:
            return None
        self.knowledge["symmetries"] = kept
        self._son = self._mind = None
        return (f"symétries : {len(kept) + 1} façons de voir une position ({len(found)} "
                f"renumérotation(s) préservent les motifs, {len(kept) + 1} vérifiée(s) dans le labo)")

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
                changed = {i for i, (a, b) in enumerate(zip(before, after)) if a != b}
                expected = self.mind.changees(list(before), arguments)
                if changed != expected:
                    raise LabError(f"{self.model.action.short_name}{arguments} a changé les cases {sorted(changed)}, "
                                   f"pas {sorted(expected)} : l'Analyzer doit d'abord mieux "
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
        self._son = None

    def rethink(self) -> None:
        """La mère comprend mieux le jeu (pions, motifs) : sa perception est à refaire."""
        self._son = self._mind = self._pensee = self._bank = None
        self._judged = {}
        self._symmetries_known = False
        self._shapes_known = False

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
        """La perception du jeu par la mère (les quatre notions)."""
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

    def variations(self, decisions: list, son_side: int) -> list:
        """« Et s'il avait joué ailleurs ? » La mère revient (``back``) sur chaque coup de
        l'adversaire, essaie les autres, et note ce que le fils aurait répondu."""
        lab, me, imagined = self.lab, self.marks[son_side], []
        for moves, _, _, _ in decisions:
            if not moves:
                continue
            before = moves[:-1]
            lab.goto(before)
            for cell in self.mind.possibles(list(lab.states[-1])):
                if (cell,) == moves[-1] or not lab.goto(before + [(cell,)]) or lab.ended:
                    continue
                state = list(lab.states[-1])
                son_cell, reason = self.son.choisir(list(state), me)
                self.max_views = max(self.max_views, self.son.VUES)
                imagined.append((list(lab.moves), state, son_cell, reason))
        return imagined

    def review(self, decisions: list, son_side: int) -> list[Lesson]:
        lessons = []
        me = self.marks[son_side]
        for moves, state, son_cell, reason in decisions:
            teacher = self.teacher_move(moves)
            teacher_cell = self.cell(teacher)
            if (teacher_cell == son_cell
                    or self.value(moves + [teacher], son_side) <= self.value(moves + [(son_cell,)], son_side)):
                key = self.mind.cle(list(state), me)
                if key not in self.cases:  # bien joué : la position reste un test pour les refactors
                    self.cases[key] = Case(list(moves), list(state), me, key, son_cell, teacher_cell)
                continue
            lessons.append(self.correct(state, me, son_cell, reason, teacher_cell, moves))
        return lessons

    def correct(self, state, me, son_cell, reason, teacher_cell, moves=None) -> Lesson:
        """Corrige le cas : la position devient un souvenir et un cas enregistré."""
        self.rewrite()
        memories = self.knowledge["memories"]
        key = self.mind.cle(list(state), me)
        changes = []
        if reason == "souvenir":
            del memories[self.mind.rappel(list(state), me, memories)[0]]
            changes.append("souvenir faux oublié")
        memories[key] = teacher_cell
        changes.append("nouveau souvenir")
        self.cases[key] = Case(list(moves or []), list(state), me, key, son_cell, teacher_cell)
        return Lesson(key, son_cell, reason, teacher_cell, "souvenir", ", ".join(changes))

    # ------------------------------------------------------------------ #
    # Refactor : remplacer des souvenirs par une règle
    # ------------------------------------------------------------------ #

    @property
    def pensee(self) -> concepts.Pensee:
        if self._pensee is None:
            self._pensee = concepts.Pensee(self.mind, self.knowledge["concepts"])
        return self._pensee

    @property
    def bank(self) -> list:
        """Les concepts que la mère sait former, du plus petit au plus grand."""
        if self._bank is None:
            positions = concepts.echantillon(self.mind, self.lab.states[0], self.knowledge["marks"])
            self._bank = concepts.enumerer(self.pensee, positions, self.max_size, self.max_depth, self.counts)
        return self._bank

    def rule(self, name: str) -> concepts.Concept:
        return self.knowledge["concepts"][name]  # l'arbre lui-même : un nom essayé peut être abandonné

    def decide(self, state, me, rules: list[str]) -> int:
        """Le coup que jouerait le fils avec ces règles, sans souvenir (comme son squelette)."""
        for name in rules:
            cells = self.pensee.choix(self.rule(name), state, me)
            if cells:
                return min(cells)
        return min(self.mind.possibles(list(state)))

    def good(self, case: Case, cell: int) -> bool:
        """Le coup est-il aussi bon que celui du professeur ? (vérifié dans le labo)"""
        if cell == case.teacher_cell:
            return True
        key = (case.key, cell)
        if key not in self._judged:
            side = len(case.moves) % 2
            self._judged[key] = (self.value(case.moves + [(cell,)], side)
                                 >= self.value(case.moves + [(case.teacher_cell,)], side))
        return self._judged[key]

    def covering(self) -> dict[str, str | None]:
        """Pour chaque cas, la clé du souvenir qui décide (le sien ou celui d'une position
        équivalente), ou ``None`` si ce sont les règles qui décident."""
        memories, mind = self.knowledge["memories"], self.mind
        return {case.key: mind.rappel(list(case.state), case.me, memories)[0]
                for case in self.cases.values()}

    def check(self, rules: list[str], covering: dict) -> list[str] | None:
        """Rejoue tous les cas avec ces règles : ``None`` si un cas sans souvenir est raté,
        sinon les souvenirs dont plus aucun cas n'a besoin."""
        needed, useful = set(), set()
        for case in self.cases.values():
            ok = self.good(case, self.decide(case.state, case.me, rules))
            memory = covering[case.key]
            if memory is None:
                if not ok:
                    return None
            else:
                useful.add(memory)
                if not ok:
                    needed.add(memory)
        return sorted(useful - needed)

    def views(self, rules: list[str], freed: list[str]) -> int:
        """Positions regardées au plus par le fils écrit avec ces règles, sur les cas enregistrés."""
        knowledge = dict(self.knowledge, rules=rules,
                         memories={k: v for k, v in self.knowledge["memories"].items() if k not in freed})
        son = son_writer.load(son_writer.son_source("essai", knowledge))
        most = 0
        for case in self.cases.values():
            son.choisir(list(case.state), case.me)
            most = max(most, son.VUES)
            if most > self.budget:
                break
        return most

    def refactor(self) -> list[str]:
        """Remplace des souvenirs par des règles, tant que c'est possible, puis retire
        les règles devenues inutiles."""
        done = []
        while True:
            message = self.refactor_once()
            if message is None:
                break
            done.append(message)
        if done:
            done += self.prune()
        return done

    def prune(self) -> list[str]:
        """Retire chaque règle sans laquelle tous les cas restent bien joués (du code mort)."""
        done = []
        for name in list(reversed(self.knowledge["rules"])):
            rules = [r for r in self.knowledge["rules"] if r != name]
            if self.check(rules, self.covering()) is not None:
                self.knowledge["rules"] = rules
                self.rewrite()
                done.append(f"{name} retirée (inutile) ; règles : {' > '.join(rules) or 'aucune'}")
        return done

    def refactor_once(self) -> str | None:
        memories, definitions = self.knowledge["memories"], self.knowledge["concepts"]
        covering = self.covering()
        pending = [case for case in self.cases.values() if covering[case.key] is not None]
        if len({covering[case.key] for case in pending}) < 2:
            return None
        pensee = self.pensee
        candidates = []
        for rank, concept in enumerate(self.bank):
            explained = set()  # souvenirs expliqués (deux positions équivalentes comptent pour un)
            for case in pending:
                cells = pensee.choix(concept, case.state, case.me)
                if case.teacher_cell in cells and case.son_cell not in cells:
                    explained.add(covering[case.key])
            if len(explained) >= 2:
                candidates.append((concept.size, -len(explained), rank, concept))
        names = {c.id: name for name, c in definitions.items()}
        for _, _, _, concept in sorted(candidates):
            if concept.kind == "brique" and concept.args[1] == MOI and concept.args[0] in definitions:
                concept = definitions[concept.args[0]]  # une brique connue : la règle existe déjà
            known = concept.id in names
            name = names[concept.id] if known else f"concept_{len(definitions) + 1}"
            if not known:
                definitions[name] = concept
            others = [r for r in self.knowledge["rules"] if r != name]
            for rank in range(len(others), -1, -1):  # du moins prioritaire au plus prioritaire
                rules = others[:rank] + [name] + others[rank:]
                freed = self.check(rules, covering)
                if freed is not None and len(freed) >= 2 and self.views(rules, freed) <= self.budget:
                    return self.adopt(name, concept, rules, freed, known)
            if not known:
                del definitions[name]
        return None

    def adopt(self, name, concept, rules, freed, known) -> str:
        self.knowledge["rules"] = rules
        for key in freed:
            del self.knowledge["memories"][key]
        if not known:
            self._bank = None  # une nouvelle brique : la mère sait former de nouveaux concepts
        self.rewrite()
        what = "règle remontée" if known else f"nouvelle règle « {concepts.decrire_regle(concept)} »"
        return (f"{len(freed)} souvenirs -> {name} ({what}) ; "
                f"règles : {' > '.join(rules)} ; souvenirs : {len(self.knowledge['memories'])}")

    def train(self, nb_games: int, on_game=None) -> list[GameRecord]:
        """Fait jouer et corrige le fils ``nb_games`` fois (professeur, hasard et mixte, des deux côtés).

        Après chaque partie, la mère revoit les coups du fils et ses réponses aux
        variantes, corrige chaque erreur par un souvenir, puis refactorise.
        """
        if not self.records:
            record = self.first_lesson()
            if on_game:
                on_game(record)
        if len(self.marks) < 2:
            raise LabError("la mère n'a pas compris quel pion pose chaque joueur")
        opponents = [("professeur", self.teacher), ("hasard", random_player(self.rng)),
                     ("mixte", mixed_player(self.teacher, self.rng))]
        for number in range(1, nb_games + 1):
            name, opponent = opponents[(number - 1) // 2 % len(opponents)]
            side = (number - 1) % 2
            shifted = [] if self._shapes_known else self.shift_patterns()
            symmetry = None if self._symmetries_known else self.discover_symmetries()
            result, decisions = self.play_game(opponent, side)
            record = GameRecord(len(self.records), name, str(self.marks[side]), RESULTS[result])
            record.refactors += shifted
            if symmetry:
                record.refactors.append(symmetry)
            record.lessons = self.review(decisions + self.variations(decisions, side), side)
            if record.lessons:
                record.refactors += self.refactor()
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
