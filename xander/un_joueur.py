"""Élever un fils qui joue seul : se tromper, revenir en arrière, ne plus le refaire.

Avec un seul joueur, il n'y a ni adversaire, ni professeur, ni « qui a gagné » :
les quatre notions des jeux à deux (``gagne``, ``adversaire``…) n'ont pas de
sens. La mère juge un coup **par ce qui arrive** : la partie finit, ou elle
continue. C'est la notion de résultat d'une partie à un joueur, apprise de
l'exemple et du labo, pas codée pour un jeu :

* **la fin** est le signal que l'exemple montre au dernier coup (l'action
  renvoie autre chose que d'habitude), retrouvé dans le labo ; l'exemple dit
  si elle est **perdue** (personne n'a gagné : ``# end``) ou **gagnée** (le
  joueur a gagné : ``# end player <nom>``, un casse-tête résolu) ;
* **la durée d'effet** d'une action : dans le labo, la mère joue chaque action
  puis la même suite de coups, et regarde quand les deux parties redeviennent
  identiques. Une action n'a plus d'effet visible au-delà : c'est jusque-là
  qu'il faut regarder pour la juger (l'**horizon**, la plus longue durée vue,
  plus un coup) ;
* **la valeur d'un coup** : combien de coups la partie dure au mieux après lui,
  sans dépasser l'horizon (une fin perdue vaut 0, une fin gagnée plus que tout
  ce qui ne finit pas, et plus tôt vaut mieux). La mère la mesure **dans son
  labo, avec back** : elle essaie les suites de coups possibles et revient en
  arrière ; deux actions qui mènent au même état ne sont essayées qu'une fois.

Déroulé : le fils joue une partie dans le labo (au plus :data:`COUPS_MAX`
coups ; au-delà il a survécu). Une décision prise plus d'un horizon avant la
fin ne peut pas être une erreur (la partie a duré assez après elle) ; la mère
revoit donc les dernières. Si un autre coup valait plus que celui du fils,
c'est une **erreur** : elle en fait un **souvenir** (dans cet état exact,
jouer ce coup). Chaque position revue devient un **cas** avec la valeur de
chaque coup : les cas sont les tests de ce qui suit.

**Petits motifs.** Quand au moins deux souvenirs demandent le même coup, la
mère cherche ce qu'ils ont en commun qui suffit : le plus petit ensemble de
cases (avec leur valeur) qu'ils partagent, tel que partout où il apparaît dans
les cas enregistrés, le coup est l'un des meilleurs. Parmi les plus petits,
elle garde celui dont la présence annonce le mieux que le coup est nécessaire
(la plus grande part des cas où il apparaît où le coup était le seul bon).
Le fils le reconnaît ensuite partout. Un motif démenti par une erreur est
oublié. Il ne regarde aucune position à l'avance : il reconnaît.

Le fils joue un seul coup par tour, n'utilise jamais ``back`` et ne simule
rien. Rien ici n'est propre à un jeu : un état est une liste de cases ou une
valeur, les actions sont celles que la mère a trouvées.

Limites : un seul joueur, une action à un argument ; un état « caché » (deux
parties dans le même état visible mais pas dans le même état interne) est
confondu : la mère juge sur ce qu'elle voit.
"""

from __future__ import annotations

import itertools
import random

from xander import effets, son_writer
from xander.education import Education, GameRecord, Lesson
from xander.game_model import GameModel
from xander.lab import Lab, LabError
from xander.parser import ParsedExample

#: Coups d'une partie du labo : au-delà, le fils a survécu.
COUPS_MAX = 300
#: Positions où la mère mesure la durée d'effet des actions ; durée mesurée au plus.
MESURES, DUREE_MAX = 30, 40
#: Petits motifs essayés au plus (toutes tailles confondues) avant d'oublier les cases une à une.
COMBINAISONS = 20000


class SoloLesson(Lesson):
    """Une erreur du fils qui joue seul : un autre coup valait plus (mesuré dans le labo)."""

    def __str__(self) -> str:
        return (f"{self.position} : le fils a joué {self.son_cell!r} ({self.son_reason}), "
                f"{self.teacher_cell!r} valait plus ({self.explanation}) ; {self.change}")


class SoloRecord(GameRecord):
    """Une partie du fils qui joue seul."""

    def __str__(self) -> str:
        text = super().__str__()
        _, _, rest = text.partition("\n")
        head = f"partie {self.number:>3} | seul : {self.result:<20} | {len(self.lessons)} erreur(s)"
        if self.impossibles:
            head += f" | {len(self.impossibles)} coup(s) impossible(s)"
        return head + ("\n" + rest if rest else "")


class Solo(Education):
    """L'éducation d'un fils qui joue seul (voir le module)."""

    def __init__(self, parsed: ParsedExample, model: GameModel, seed: int = 0):
        state = model.getter.return_value.name if model.getter else None
        observed = (model.report.cases.get(model.action.name, {}).get(state, [])
                    if model.report and model.action else [])
        forms = {case.forme for case in observed}
        if not forms:
            raise LabError("l'exemple ne montre pas ce que change l'action : la mère ne peut pas "
                           "encore éduquer de fils")
        self.forme = effets.APRES if forms == {effets.APRES} else effets.CHANGEES
        self.tableau = self.forme != effets.APRES
        self.formes = (self.forme, effets.SUITE)     # un état qui défile se décrit aussi
        self.parsed, self.model = parsed, model
        self.lab = Lab(parsed, model)
        self.teacher, self.seed, self.rng = None, seed, random.Random(seed)
        self.knowledge = son_writer.empty_knowledge(model)
        self.knowledge["motifs"] = []                 # petits motifs : ({case: valeur}, action)
        self.knowledge["usual"] = self.lab.usual.__name__ if self.lab.usual else None
        self.knowledge["actions"] = self.discover_actions()
        if len(set(self.owners())) != 1:
            raise LabError("l'exemple ne montre pas un joueur seul")
        self.endings: list[tuple] = []
        self.lab.refusals = 0
        positions, seen = self.explore()
        self.positions = positions
        self.lab_cases = [case for case, _ in seen]
        observed = list(observed) + [c for c in self.lab_cases if c.valeur_apres != c.valeur_avant]
        effects = [h for h in effets.decouvrir(observed) if h.forme in self.formes]
        if not effects:
            raise LabError("aucun programme n'explique ce que change l'action, même avec ce "
                           "que la mère a vu dans le labo : elle ne peut pas encore éduquer de fils")
        self.trials = self.test_effects(effects, observed, positions)
        self.knowledge["effect"] = self.trials.survivors[0]
        self.knowledge["start"] = self.copy(self.lab.states[0])
        refused = self.lab.refusals
        if self.forme == effets.APRES:
            self.knowledge["free"] = self.free()
        else:  # un coup refusé laisse l'état tel quel ; sans refus vu, toute action est permise
            self.knowledge["free"] = ("toujours",) if not refused else None
        if self.knowledge["free"] is None:
            raise LabError("la mère ne sait pas dire quand une action peut être jouée : "
                           "elle ne peut pas encore éduquer de fils")
        self.knowledge["fin"] = self.result_of_end()
        self.horizon, self.durations = self.measure_horizon()
        self.knowledge["horizon"] = self.horizon
        self._son = None
        self.max_views = 0
        self.impossibles: list[str] = []
        self.records: list[GameRecord] = []
        self.cases: dict[tuple, dict] = {}   # coups -> {"state", "values", "moves"}
        self._values: dict = {}               # (coups, profondeur) -> valeur au mieux
        self.discovered: list = []

    # ------------------------------------------------------------------ #
    # Le résultat d'une partie à un joueur
    # ------------------------------------------------------------------ #

    def result_of_end(self) -> str:
        """Ce que vaut la fin, lu dans l'exemple : gagnée si le joueur y est le gagnant, nulle
        pour un nul, perdue sinon (la partie s'arrête et personne n'a gagné)."""
        winner = self.parsed.winner
        if winner == "D":
            return "nulle"
        return "gagnée" if winner and winner in self.parsed.players else "perdue"

    def measure_horizon(self) -> tuple[int, list[int]]:
        """Combien de temps l'effet d'une action reste-t-il visible ? Depuis des positions vues
        en explorant, la mère joue chaque action, puis toujours la plus petite, et compte les coups
        jusqu'à ce que les deux parties soient de nouveau dans le même état. Une mesure où l'une des
        deux finit ne dit rien. L'horizon est la plus longue durée vue, plus un coup (au moins 1)."""
        lab, actions = self.lab, self.knowledge["actions"]
        if len(actions) < 2:
            return 1, []
        rng = random.Random(f"durée-{self.seed}")
        sample = rng.sample(self.positions, min(MESURES, len(self.positions)))
        durations = []
        for moves, _ in sample:
            runs = []
            for first in actions:
                states = []
                if not lab.goto(list(moves)) or lab.ended:
                    break
                for k in range(DUREE_MAX):
                    if lab.play(first if k == 0 else actions[0]) != "moved":
                        break
                    states.append(lab.states[-1])
                runs.append(states)
            if len(runs) != len(actions):
                continue
            reference = runs[0]
            for other in runs[1:]:
                same = next((k for k, (a, b) in enumerate(zip(reference, other)) if a == b), None)
                if same is not None:
                    durations.append(same)
                elif len(reference) == len(other) == DUREE_MAX:
                    durations.append(DUREE_MAX)  # jamais réunies : l'effet dure
        lab.goto([])
        return (max(durations) + 1 if durations else 1), sorted(set(durations))

    def value(self, moves: list[tuple], depth: int | None = None) -> int:
        """Ce que vaut au mieux la suite de la partie après ``moves`` (au plus ``depth`` coups),
        mesuré dans le labo avec back. Une fin perdue ou nulle vaut 0 ; une fin gagnée vaut plus
        que tout ce qui ne finit pas, et plus tôt vaut mieux."""
        depth = self.horizon if depth is None else depth
        key = (tuple(moves), depth)
        if key in self._values:
            return self._values[key]
        lab = self.lab
        if not lab.goto(list(moves)):
            raise LabError(f"le labo ne peut pas rejouer {moves}")
        if lab.ended:
            result = self.end_value(depth)
        elif depth == 0:
            result = 0
        else:
            result, seen = 0, set()
            for action in self.knowledge["actions"]:
                if not lab.goto(list(moves)):
                    break
                outcome = lab.play(action)
                if outcome == "refused":
                    continue
                if outcome == "moved":
                    state = repr(lab.states[-1])
                    if state in seen:
                        continue  # même état : même avenir (elle juge sur ce qu'elle voit)
                    seen.add(state)
                    worth = 1 + self.value(list(moves) + [(action,)], depth - 1)
                else:
                    worth = self.end_value(depth)
                result = max(result, worth)
                if result >= depth and self.knowledge["fin"] != "gagnée":
                    break  # survivre jusqu'à l'horizon : on ne peut pas faire mieux
        self._values[key] = result
        return result

    def end_value(self, depth: int) -> int:
        """Ce que vaut une fin atteinte quand il restait ``depth`` coups à regarder."""
        return 2 * self.horizon + depth if self.knowledge["fin"] == "gagnée" else 0

    def values(self, moves: list[tuple], known: dict | None = None) -> dict:
        """La valeur de chaque action possible après ``moves`` (``known`` : celles que la partie
        a déjà montrées)."""
        found = dict(known or {})
        for action in self.knowledge["actions"]:
            if action in found:
                continue
            if not self.lab.goto(list(moves)) or self.lab.ended:
                break
            outcome = self.lab.play(action)
            if outcome == "refused":
                continue
            if outcome == "end":
                found[action] = self.end_value(self.horizon)
            else:
                found[action] = 1 + self.value(list(moves) + [(action,)], self.horizon - 1)
        return found

    # ------------------------------------------------------------------ #
    # Le fils
    # ------------------------------------------------------------------ #

    def source(self, name: str = "fils") -> str:
        return son_writer.solo_source(name, self.knowledge, len(self.records) - 1)

    @property
    def son(self):
        if self._son is None:
            self._son = son_writer.load(self.source())
        return self._son

    def rewrite(self) -> None:
        self._son = None

    def position(self):
        state = self.lab.states[-1]
        return list(state) if isinstance(state, list) else state

    # ------------------------------------------------------------------ #
    # Leçon de l'exemple, parties, revue
    # ------------------------------------------------------------------ #

    def first_lesson(self) -> GameRecord:
        """Rejoue l'exemple : la description de l'action prédit-elle chaque coup ? La partie
        finit-elle comme dans l'exemple ?"""
        action = self.model.action.name
        moves = [tuple(f.arguments) for f in self.parsed.player_functions() if f.name == action]
        lab, effect = self.lab, self.knowledge["effect"]
        lab.goto([])
        for arguments in moves:
            before = lab.states[-1]
            outcome = lab.play(*arguments)
            if outcome == "refused":
                raise LabError(f"le coup {arguments} de l'exemple est refusé par le jeu")
            if outcome == "moved":
                case = effets.Cas(self.copy(before), arguments, lab.states[-1])
                if case.forme is not None and not effets.explique(effect, case):
                    raise LabError(f"{self.model.action.short_name}{arguments} : {effect!r} ne prévoit pas "
                                   "ce qui s'est passé ; l'Analyzer doit d'abord mieux comprendre l'action")
        record = SoloRecord(0, "exemple", "-", "exemple, terminé" if lab.ended else "exemple, inachevé")
        record.patterns.append(f"fin : la partie s'arrête au coup {len(lab.moves)} ({self.knowledge['fin']}, "
                               "lu dans l'exemple)" if lab.ended else "l'exemple ne finit pas")
        shown = ", ".join(map(str, self.durations)) or "aucune"
        record.patterns.append(f"durée d'effet d'une action : {shown} coup(s) ; la mère juge un coup "
                               f"sur {self.horizon} coup(s)")
        self.records.append(record)
        return record

    def play_game(self) -> list:
        """Une partie du fils dans le labo. Il ne joue qu'un coup par tour ; un coup refusé est un
        coup impossible, que la mère doit comprendre (sinon elle s'arrête)."""
        lab = self.lab
        lab.goto([])
        decisions, self.impossibles = [], []
        while not lab.ended and len(lab.moves) < COUPS_MAX:
            moves, state = list(lab.moves), self.position()
            action, reason = self.son.choisir(state)
            self.max_views = max(self.max_views, self.son.VUES)
            if lab.play(action) == "refused":
                self.impossibles.append(self.impossible(state, action))
                continue
            decisions.append((moves, state, action, reason))
        return decisions

    def impossible(self, state, action) -> str:
        raw = self.copy(state)
        self.lab_cases.append(effets.Cas(raw, (action,), self.copy(raw)))
        free = self.free() if self.forme == effets.APRES else None
        if free is None or action in self.son_after(free).possibles(state):
            raise LabError(f"le jeu refuse l'action {action!r}, que le fils croyait possible, "
                           "et la mère ne comprend pas pourquoi")
        self.knowledge["free"] = free
        self.rewrite()
        return f"coup impossible : {action!r} refusé ; une action peut être jouée : {free}"

    def son_after(self, free):
        return son_writer.load(son_writer.solo_source("essai", dict(self.knowledge, free=free)))

    def review(self, decisions: list) -> list[Lesson]:
        """Revoit chaque décision du fils : la valeur de chaque coup, mesurée dans le labo. Celle
        du coup du fils se lit souvent sur la partie elle-même (elle a duré au moins un horizon
        après lui). Un coup qui vaut moins qu'un autre est une erreur ; chaque position revue
        devient un cas, le test des petits motifs."""
        lessons, lab = [], self.lab
        played, ended = len(lab.moves), lab.ended
        for moves, state, action, reason in decisions:
            key = tuple(moves)
            if key not in self.cases:
                lasted = played - len(moves) - (1 if ended else 0)  # coups survécus, le sien compris
                known = ({action: self.horizon}
                         if lasted >= self.horizon and self.knowledge["fin"] != "gagnée" else {})
                self.cases[key] = {"moves": moves, "state": state, "values": self.values(moves, known)}
            worth = self.cases[key]["values"]
            if worth and worth.get(action, -1) < max(worth.values()):
                lessons.append(self.correct(moves, state, action, reason, worth))
        lab.goto([])
        return lessons

    def best(self, worth: dict):
        top = max(worth.values())
        return min(a for a, v in worth.items() if v == top)

    def correct(self, moves, state, action, reason, worth) -> Lesson:
        """Corrige le cas : dans cet état, jouer le meilleur coup. Un petit motif qui a décidé
        ce coup est démenti : la mère l'oublie."""
        self.rewrite()
        changes = []
        if reason == "petit motif":
            motif = self.son.motif_de(state)
            self.knowledge["motifs"] = [(m, a) for m, a in self.knowledge["motifs"] if m != motif]
            changes.append(f"petit motif {son_writer.motif_text(motif)} démenti, oublié")
        good = self.best(worth)
        self.knowledge["memories"][son_writer.state_key(state)] = good
        changes.append("nouveau souvenir")
        return SoloLesson(f"coup {len(moves) + 1}", action, reason, good,
                          f"valeurs {dict(sorted(worth.items(), key=repr))}", ", ".join(changes))

    # ------------------------------------------------------------------ #
    # Petits motifs : ce que plusieurs souvenirs ont en commun
    # ------------------------------------------------------------------ #

    def plays_well(self, knowledge: dict) -> bool:
        """Le fils écrit avec ``knowledge`` joue-t-il un des meilleurs coups dans chaque cas ?"""
        son = son_writer.load(son_writer.solo_source("essai", knowledge))
        for case in self.cases.values():
            worth = case["values"]
            if worth and worth.get(son.choisir(case["state"])[0], -1) < max(worth.values()):
                return False
        return True

    def matching(self, motif: dict) -> list[dict]:
        return [case for case in self.cases.values()
                if isinstance(case["state"], list) and son_writer.contains(case["state"], motif)]

    def holds(self, motif: dict, action) -> tuple[bool, int]:
        """Le coup est-il l'un des meilleurs partout où le motif apparaît (dans les cas) ?
        Renvoie aussi le nombre de cas qui le **confirment** (le coup y était le seul bon)."""
        confirmed = 0
        for case in self.matching(motif):
            worth = case["values"]
            if not worth or action not in worth:
                continue
            top = max(worth.values())
            if worth[action] < top:
                return False, 0
            confirmed += all(v < top for a, v in worth.items() if a != action)
        return True, confirmed

    def generalize(self) -> list[str]:
        """Remplace des souvenirs par un petit motif, pour chaque coup que demandent au moins deux
        souvenirs (un seul cas peut être une coïncidence)."""
        if not self.tableau:
            return []
        done = []
        memories = self.knowledge["memories"]
        for action in sorted(set(memories.values()), key=repr):
            keys = [k for k, a in memories.items() if a == action]
            if len(keys) < effets.MIN_CAS:
                continue
            motif = self.smallest(keys, action)
            if motif is None:
                continue
            freed = [k for k in keys if son_writer.contains(list(k), motif)]
            trial = dict(self.knowledge, memories={k: a for k, a in memories.items() if k not in freed},
                         motifs=self.knowledge["motifs"] + [(motif, action)])
            if len(freed) < effets.MIN_CAS or not self.plays_well(trial):
                continue
            self.knowledge["memories"], self.knowledge["motifs"] = trial["memories"], trial["motifs"]
            self.rewrite()
            done.append(f"{len(freed)} souvenirs -> petit motif {son_writer.motif_text(motif)} : "
                        f"{action!r} ({len(motif)} case(s) sur {len(keys[0])}, confirmé par "
                        f"{self.holds(motif, action)[1]} cas)")
        return done

    def smallest(self, keys: list[tuple], action) -> dict | None:
        """Le plus petit motif commun aux souvenirs qui tient (:meth:`holds`) et en couvre au moins
        deux : d'abord 1 case, puis 2… (au plus :data:`COMBINAISONS` essais). À taille égale,
        celui dont la présence annonce le mieux que le coup est nécessaire : la plus grande part
        des cas où il apparaît qui le confirment (comme le groupe témoin des jeux à deux), puis le
        plus de confirmations. Sinon, partie de toutes les cases communes, elle les
        oublie une à une tant que le motif tient."""
        common = [i for i in range(len(keys[0])) if len({repr(k[i]) for k in keys}) == 1]
        values = {i: keys[0][i] for i in common}
        tried = 0
        for size in range(1, len(common) + 1):
            best = None
            for cells in itertools.combinations(common, size):
                tried += 1
                if tried > COMBINAISONS:
                    break
                motif = {i: values[i] for i in cells}
                if sum(son_writer.contains(list(k), motif) for k in keys) < effets.MIN_CAS:
                    continue
                ok, confirmed = self.holds(motif, action)
                if not ok:
                    continue
                # « à cause du motif » : la part des cas où il apparaît qui le confirment (un motif
                # présent partout où le coup est indifférent n'explique pas qu'il soit nécessaire)
                score = (confirmed / len(self.matching(motif)), confirmed)
                if best is None or score > best[0]:
                    best = (score, motif)
            if best is not None:
                return best[1]
            if tried > COMBINAISONS:
                break
        motif = dict(values)
        if not self.holds(motif, action)[0]:
            return None
        for i in common:
            trial = {c: v for c, v in motif.items() if c != i}
            if trial and self.holds(trial, action)[0]:
                motif = trial
        return motif

    # ------------------------------------------------------------------ #

    def train(self, nb_games: int, on_game=None) -> list[GameRecord]:
        """Fait jouer le fils ``nb_games`` fois dans le labo et le corrige après chaque partie."""
        if not self.records:
            record = self.first_lesson()
            if on_game:
                on_game(record)
        for number in range(1, nb_games + 1):
            decisions = self.play_game()
            played = len(self.lab.moves)
            result = f"perdue au coup {played}" if self.lab.ended else f"survie ({played} coups)"
            if self.lab.ended and self.knowledge["fin"] == "gagnée":
                result = f"gagnée au coup {played}"
            record = SoloRecord(len(self.records), "seul", "-", result)
            record.impossibles = self.impossibles
            record.lessons = self.review(decisions)
            if record.lessons:
                record.refactors += self.generalize()
            self.records.append(record)
            if on_game:
                on_game(record)
        return self.records

    def evaluate(self, nb_random: int = 0) -> dict[str, dict[str, int]]:
        """Une partie du fils sans correction, dans le labo."""
        self.play_game()
        played = len(self.lab.moves)
        return {"labo": {"coups joués": played, "fin": int(self.lab.ended)}}
