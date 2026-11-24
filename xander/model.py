"""Structures de données manipulées par la logique mère.

Un fichier d'exemple (voir ``res/``) est découpé en :

* :class:`Variable`  – une valeur nommée et typée (``board # array 9``) ;
* :class:`Function`  – un appel de fonction observé dans l'exemple, horodaté
  par sa position chronologique (``time``) dans la partie ;
* :class:`Player`    – la liste des appels faits par un joueur ;
* :class:`Operation` – l'effet déduit d'une fonction sur une variable
  (« ``play(4)`` modifie la case d'indice 4 de ``board`` »).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class FunctionKind(Enum):
    """Forme d'une fonction selon ses entrées / sorties."""

    NONE = 0    # ni paramètre ni valeur de retour : game.init()
    OUTPUT = 1  # « getter » : board = game.get_game_state()
    INPUT = 2   # « setter » : game.play(4)
    INOUT = 3   # les deux : board = game.play(4)


class FunctionOperation(Enum):
    """Effet qu'une fonction INPUT/INOUT a sur une variable observée."""

    UNKNOWN = 0
    SINGLE_TARGET_INDEX = 1    # modifie la case d'indice <param> d'un tableau
    SINGLE_TARGET_NAME = 2     # modifie la case dont la valeur vaut <param>
    SRC_DEST_TARGET_INDEX = 3  # déplace de l'indice <p1> vers l'indice <p2>
    SRC_DEST_TARGET_NAME = 4   # déplace de la case <p1> vers la case <p2>
    QUANTITY_SET = 5           # variable = <param>
    QUANTITY_RM = 6            # variable -= <param>
    QUANTITY_ADD = 7           # variable += <param>
    CHECK_VICTORY = 8          # (réservé) la fonction signale une victoire


VARIABLE_KINDS = ("array", "string", "integer", "bool", "game", "back")


@dataclass(eq=False)
class Variable:
    """Une variable de l'exemple, décrite par son commentaire ``# <type> [taille]``."""

    kind: str = ""
    size: int = 1
    name: str = ""
    getters: list[Function] = field(default_factory=list)
    setters: list[Function] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        """Vrai pour la « variable vide » d'une fonction sans valeur de retour."""
        return not self.kind or not self.name

    def __str__(self) -> str:
        text = f"{self.name} ({self.kind}"
        if self.kind == "array":
            text += f", taille {self.size}"
        return text + ")"


@dataclass(eq=False)
class Operation:
    """Effet observé d'une fonction sur une variable."""

    kind: FunctionOperation = FunctionOperation.UNKNOWN
    variable: Variable | None = None

    @property
    def key(self) -> tuple[FunctionOperation, str]:
        return self.kind, self.variable.name if self.variable else ""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Operation) and self.key == other.key

    def __hash__(self) -> int:
        return hash(self.key)

    def __repr__(self) -> str:
        return f"Operation({self.kind.name}, {self.key[1]!r})"


@dataclass(eq=False)
class Function:
    """Un appel de fonction relevé dans l'exemple.

    ``parameters`` contient le texte source des arguments (``["4"]``),
    ``arguments`` leur valeur Python quand c'est un littéral (``[4]``).
    Deux appels de la même fonction à des moments différents sont deux
    objets distincts mais sont considérés égaux (comparaison par nom).
    """

    name: str = ""
    return_value: Variable = field(default_factory=Variable)
    parameters: list[str] = field(default_factory=list)
    time: int = 0
    arguments: list = field(default_factory=list)
    operations: list[Operation] = field(default_factory=list)

    @property
    def kind(self) -> FunctionKind:
        has_output = not self.return_value.is_empty
        if self.parameters and has_output:
            return FunctionKind.INOUT
        if self.parameters:
            return FunctionKind.INPUT
        if has_output:
            return FunctionKind.OUTPUT
        return FunctionKind.NONE

    @property
    def short_name(self) -> str:
        """Nom sans l'objet : ``game.play`` -> ``play``."""
        return self.name.rsplit(".", 1)[-1]

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Function) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def call_source(self) -> str:
        """Reconstitue l'appel Python : ``board = game.play(4)``."""
        call = f"{self.name}({', '.join(self.parameters)})"
        if self.return_value.is_empty:
            return call
        return f"{self.return_value.name} = {call}"

    def __str__(self) -> str:
        return f"t={self.time:<3} {self.call_source():<35} [{self.kind.name}]"


@dataclass
class Player:
    """Un joueur de l'exemple et les appels qu'il a faits, dans l'ordre."""

    name: str
    functions_used: list[Function] = field(default_factory=list)

    def get_function_at(self, time: int) -> Function | None:
        for function in self.functions_used:
            if function.time == time:
                return function
        return None

    def __str__(self) -> str:
        lines = [f"Joueur {self.name} :"]
        lines += [f"  {function}" for function in self.functions_used]
        return "\n".join(lines)
