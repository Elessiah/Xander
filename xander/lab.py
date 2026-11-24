"""Le laboratoire de la mère : une vraie partie qu'elle peut rejouer et défaire.

C'est **ici, et seulement ici,** que ``back`` est utilisé. La mère s'en sert
pour revenir sur une erreur de son fils, rejouer une partie autrement (« et si
ce pion n'avait pas été là ? ») ou demander au professeur ce qu'il aurait joué.
Le fils, lui, ne voit jamais ce laboratoire.

Le labo tient la liste des coups joués depuis le début (``moves``) et l'état
lu avant chaque coup (``states``). :meth:`Lab.goto` amène la partie à
n'importe quelle suite de coups en annulant puis en rejouant.

Un coup est *refusé* quand l'état lu après lui n'a pas changé ; il *termine*
la partie quand l'action renvoie le signal de fin appris dans l'exemple. Après
la fin, l'état n'est plus relu (certains jeux recommencent une partie quand on
lit un état terminé).
"""

from __future__ import annotations

import contextlib
import io
import sys

from xander.game_model import GameModel
from xander.parser import ParsedExample
from xander.rebuilder import PROJECT_ROOT


class LabError(Exception):
    pass


def build_game(parsed: ParsedExample):
    """Crée une partie neuve en exécutant les sections ``# include`` et ``# init``."""
    game_calls = [f for f in parsed.init_functions if f.return_value.kind == "game"]
    if not game_calls:
        raise LabError("l'exemple ne dit pas quelle variable contient le jeu (# game)")
    source = "\n".join(parsed.imports + [f.call_source() for f in parsed.init_functions])
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    namespace: dict = {}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(source, "<init de l'exemple>", "exec"), namespace)
    return namespace[game_calls[0].return_value.name]


class Spy:
    """Le jeu tel que le voit le professeur : la mère note chaque coup qu'il joue."""

    def __init__(self, lab: Lab):
        object.__setattr__(self, "_lab", lab)

    def __getattr__(self, name):
        lab = self._lab
        if name == lab.action:
            return lab.play_raw
        if name == lab.back:
            return lambda: (lab.undo(), lab.read())[1]
        return getattr(lab.game, name)

    def __setattr__(self, name, value):
        setattr(self._lab.game, name, value)


class Lab:
    def __init__(self, parsed: ParsedExample, model: GameModel):
        if model.getter is None or model.action is None or model.back_function is None:
            raise LabError("l'exemple doit montrer un getter, une action et un # back")
        self.parsed = parsed
        self.getter = model.getter.short_name
        self.action = model.action.short_name
        self.back = model.back_function.short_name
        self.end_signal = model.end_signal
        self.new_game()

    def new_game(self) -> None:
        self.game = build_game(self.parsed)
        self.moves: list[tuple] = []
        self.states: list = [self.read()]
        self.ended = False

    # ------------------------------------------------------------------ #

    def read(self):
        return getattr(self.game, self.getter)()

    def is_end(self, result) -> bool:
        return type(result) is type(self.end_signal) and result == self.end_signal

    @property
    def state(self):
        """État courant (``None`` si la partie est finie)."""
        return None if self.ended else self.states[-1]

    def play_raw(self, *arguments):
        """Joue sur le vrai jeu, tient les registres, renvoie ce que renvoie l'action."""
        if self.ended:
            return None
        result = getattr(self.game, self.action)(*arguments)
        if self.is_end(result):
            self.moves.append(arguments)
            self.ended = True
            return result
        after = self.read()
        if after != self.states[-1]:
            self.moves.append(arguments)
            self.states.append(after)
        return result

    def play(self, *arguments) -> str:
        """Joue et résume : ``"moved"``, ``"end"`` ou ``"refused"``."""
        before = len(self.moves)
        self.play_raw(*arguments)
        if len(self.moves) == before:
            return "refused"
        return "end" if self.ended else "moved"

    def undo(self) -> None:
        if not self.moves:
            return
        getattr(self.game, self.back)()
        self.moves.pop()
        if self.ended:
            self.ended = False
        else:
            self.states.pop()

    def goto(self, moves: list[tuple]) -> bool:
        """Amène la partie à ``moves``. Faux si un coup est refusé ou finit trop tôt."""
        common = 0
        while common < min(len(moves), len(self.moves)) and moves[common] == self.moves[common]:
            common += 1
        while len(self.moves) > common:
            self.undo()
        for i, arguments in enumerate(moves[common:], start=common):
            outcome = self.play(*arguments)
            if outcome == "refused" or (outcome == "end" and i < len(moves) - 1):
                return False
        return True

    def ask(self, player) -> tuple:
        """Laisse ``player`` (une fonction ``player(game)``) jouer un coup et le renvoie."""
        before = len(self.moves)
        with contextlib.redirect_stdout(io.StringIO()):  # les Minmax commentent leurs coups
            player(Spy(self))
        if len(self.moves) != before + 1:
            raise LabError(f"{getattr(player, '__name__', player)} devait jouer exactement un coup")
        return self.moves[-1]
