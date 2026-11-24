"""Description d'un jeu telle que la logique mère la comprend."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from xander.analyzer import AnalysisReport
from xander.model import Function, FunctionKind, Variable
from xander.parser import ParsedExample


@dataclass
class GameModel:
    """Synthèse d'un exemple analysé, destinée à la construction des enfants."""

    game: Variable | None = None                     # la variable qui contient le jeu
    back_function: Function | None = None            # annule le dernier coup
    env: list[Variable] = field(default_factory=list)  # variables observables (hors jeu)
    players_names: list[str] = field(default_factory=list)
    nb_actions_per_turn: int = 0                     # nombre d'appels d'un joueur par tour
    turn_pattern: list[str] = field(default_factory=list)  # ex. ["get_game_state", "play"]
    winner: str = ""
    report: AnalysisReport | None = None
    # Ce qu'il faut pour jouer (voir xander/lab.py et xander/son_writer.py)
    getter: Function | None = None                   # lit l'état pendant un tour
    action: Function | None = None                   # joue le coup du tour
    end_signal: object = None                        # valeur renvoyée par le coup qui finit la partie

    @property
    def nb_players(self) -> int:
        return len(self.players_names)

    @classmethod
    def from_analysis(cls, parsed: ParsedExample, report: AnalysisReport) -> GameModel:
        turns = split_turns(parsed)
        nb_actions = most_common_turn_length(turns)
        pattern = next((turn for turn in turns if len(turn) == nb_actions), [])
        getter = next((f for f in pattern if f.kind is FunctionKind.OUTPUT), None)
        action = next((f for f in pattern if f.kind in ACTING), None)
        return cls(
            getter=getter,
            action=action,
            end_signal=end_signal(parsed, report, action),
            game=next((v for v in report.variables.values() if v.kind == "game"), None),
            back_function=parsed.back_function,
            env=[v for v in report.variables.values() if v.kind != "game"],
            players_names=parsed.players_name,
            nb_actions_per_turn=nb_actions,
            turn_pattern=[function.short_name for function in pattern],
            winner=parsed.winner,
            report=report,
        )

    def describe(self) -> str:
        lines = [
            f"Jeu : {self.game.name if self.game else '?'}",
            f"Joueurs ({self.nb_players}) : {', '.join(self.players_names)}",
            f"Actions par tour : {self.nb_actions_per_turn} ({' -> '.join(self.turn_pattern)})",
            f"Annulation : {self.back_function.call_source() if self.back_function else 'aucune'}",
            f"Gagnant de l'exemple : {self.winner or 'inconnu'}",
            "Variables :",
        ]
        for variable in self.env:
            getters = ", ".join(sorted({f.short_name for f in variable.getters})) or "-"
            setters = ", ".join(sorted({f.short_name for f in variable.setters})) or "-"
            lines.append(f"  {variable} | lue par : {getters} | modifiée par : {setters}")
        if self.report:
            lines.append("Opérations déduites :")
            for name, operations in self.report.operations.items():
                text = ", ".join(f"{op.kind.name} sur {op.variable.name}" for op in operations)
                lines.append(f"  {name} : {text or 'inconnue'}")
            if self.report.unknown_calls:
                lines.append("Appels non compris :")
                lines += [f"  {function}" for function in self.report.unknown_calls]
        return "\n".join(lines)


ACTING = (FunctionKind.INPUT, FunctionKind.INOUT)


def split_turns(parsed: ParsedExample) -> list[list[Function]]:
    """Découpe la chronologie en tours.

    Un nouveau tour commence quand le joueur change, ou quand le tour en cours
    a déjà agi (INPUT/INOUT) et qu'arrive un getter (OUTPUT) ou la fonction qui
    a ouvert le tour. Pour un jeu à un joueur, ``print, get, play`` répété
    donne des tours ``print -> get -> play``, et ``get, play, print`` répété
    des tours ``get -> play -> print`` : un appel NONE reste à sa place.

    Limite : un getter de confirmation après le coup (``get, play, get``) est
    rattaché au tour suivant.
    """
    owner = {f.time: name for name, player in parsed.players.items() for f in player.functions_used}
    turns: list[list[Function]] = []
    previous_owner = None
    has_acted = False
    for function in parsed.player_functions():
        if (owner[function.time] != previous_owner
                or (has_acted and (function.kind is FunctionKind.OUTPUT
                                   or function.name == turns[-1][0].name))):
            turns.append([])
            previous_owner = owner[function.time]
            has_acted = False
        turns[-1].append(function)
        has_acted = has_acted or function.kind in ACTING
    return turns


def end_signal(parsed: ParsedExample, report: AnalysisReport, action: Function | None):
    """Valeur renvoyée par le coup qui finit l'exemple, si elle change de type.

    Au Morpion, ``play`` renvoie le plateau, sauf au dernier coup : ``True``.
    """
    if action is None:
        return None
    calls = [f for f in parsed.player_functions() if f.name == action.name]
    usual = Counter(f.return_value.kind for f in calls).most_common(1)[0][0]
    last = calls[-1]
    return report.observations.get(last.time) if last.return_value.kind != usual else None


def most_common_turn_length(turns: list[list[Function]]) -> int:
    """Longueur de tour la plus fréquente (le dernier tour peut être incomplet)."""
    if not turns:
        return 0
    return Counter(len(turn) for turn in turns).most_common(1)[0][0]
