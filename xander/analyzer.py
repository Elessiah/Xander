"""Déduction du rôle de chaque fonction à partir des valeurs observées.

Pour chaque appel « qui agit » (INPUT ou INOUT) on compare une variable juste
avant et juste après l'appel, puis on teste des hypothèses codées en dur
(voir :class:`~xander.model.FunctionOperation`) :

* tableau + 1 paramètre  -> la case d'indice / de valeur <param> a changé ?
* tableau + 2 paramètres -> les cases <p1> et <p2> ont changé ?
* nombre  + 1 paramètre  -> nombre -= / += / = <param> ?

Les variables comparées sont la valeur de retour de l'appel (INOUT) et
celles des getters appelés juste après lui. Une même fonction pouvant être
mal interprétée sur un coup particulier, on ne garde ensuite pour chaque
fonction que les opérations observées sur au moins la moitié de ses appels.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from xander.model import Function, FunctionKind, FunctionOperation, Operation, Variable
from xander.parser import ParsedExample

#: Proportion minimale d'appels où une opération doit être observée pour être retenue.
MAJORITY = 0.5


def _same(element, parameter: str, argument) -> bool:
    """Compare une case du plateau au paramètre (valeur ou texte source)."""
    return element == argument or str(element) == parameter


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _changed_exactly(prev: list, nxt: list, changed: set[int]) -> bool:
    if len(prev) != len(nxt) or not changed:
        return False
    return all((prev[i] != nxt[i]) == (i in changed) for i in range(len(prev)))


# --------------------------------------------------------------------------- #
# Hypothèses testées
# --------------------------------------------------------------------------- #

def test_single_target_index(prev, nxt, function: Function) -> bool:
    index = function.arguments[0]
    if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(prev):
        return False
    return _changed_exactly(prev, nxt, {index})


def test_single_target_name(prev, nxt, function: Function) -> bool:
    targets = {i for i, element in enumerate(prev)
               if _same(element, function.parameters[0], function.arguments[0])}
    return _changed_exactly(prev, nxt, targets)


def test_src_dest_target_index(prev, nxt, function: Function) -> bool:
    indexes = function.arguments[:2]
    if not all(isinstance(i, int) and not isinstance(i, bool) and 0 <= i < len(prev) for i in indexes):
        return False
    return _changed_exactly(prev, nxt, set(indexes))


def test_src_dest_target_name(prev, nxt, function: Function) -> bool:
    targets = {i for i, element in enumerate(prev)
               if any(_same(element, p, a) for p, a in zip(function.parameters[:2], function.arguments[:2]))}
    return _changed_exactly(prev, nxt, targets)


def test_quantity(prev, nxt, function: Function) -> FunctionOperation | None:
    quantity = function.arguments[0]
    if not (_is_number(prev) and _is_number(nxt) and _is_number(quantity)):
        return None
    if prev - quantity == nxt:
        return FunctionOperation.QUANTITY_RM
    if prev + quantity == nxt:
        return FunctionOperation.QUANTITY_ADD
    if nxt == quantity:
        return FunctionOperation.QUANTITY_SET
    return None


def guess_operation(prev, nxt, function: Function) -> FunctionOperation | None:
    """Renvoie la première hypothèse compatible avec le changement ``prev -> nxt``."""
    nb_parameters = len(function.parameters)
    if isinstance(prev, list) and isinstance(nxt, list):
        if nb_parameters == 1:
            if test_single_target_index(prev, nxt, function):
                return FunctionOperation.SINGLE_TARGET_INDEX
            if test_single_target_name(prev, nxt, function):
                return FunctionOperation.SINGLE_TARGET_NAME
        elif nb_parameters == 2:
            if test_src_dest_target_index(prev, nxt, function):
                return FunctionOperation.SRC_DEST_TARGET_INDEX
            if test_src_dest_target_name(prev, nxt, function):
                return FunctionOperation.SRC_DEST_TARGET_NAME
    elif nb_parameters == 1:
        return test_quantity(prev, nxt, function)
    return None


# --------------------------------------------------------------------------- #
# Analyse complète
# --------------------------------------------------------------------------- #

@dataclass
class AnalysisReport:
    """Ce que la logique mère a compris de l'exemple."""

    observations: dict[int, object]
    variables: dict[str, Variable]                    # une entrée par nom de variable
    operations: dict[str, list[Operation]]            # nom de fonction -> opérations retenues
    unknown_calls: list[Function] = field(default_factory=list)  # appels non compris


class Analyzer:
    def __init__(self, parsed: ParsedExample, observations: dict[int, object]):
        self.parsed = parsed
        self.observations = observations
        self.timeline = sorted(parsed.init_functions + parsed.player_functions(),
                               key=lambda function: function.time)
        self.by_time = {function.time: function for function in self.timeline}

    def value_before(self, variable_name: str, time: int):
        """Dernière valeur observée de ``variable_name`` strictement avant ``time``."""
        for t in range(time - 1, -1, -1):
            function = self.by_time.get(t)
            if function and function.return_value.name == variable_name and t in self.observations:
                return True, self.observations[t]
        return False, None

    def compared_values(self, function: Function):
        """Couples (variable, avant, après) à comparer pour un appel."""
        candidates = []
        if function.kind is FunctionKind.INOUT:
            candidates.append(function)
        t = function.time + 1
        while (getter := self.by_time.get(t)) and getter.kind is FunctionKind.OUTPUT:
            candidates.append(getter)
            t += 1
        for observed in candidates:
            if observed.time not in self.observations:
                continue
            found, prev = self.value_before(observed.return_value.name, function.time)
            if found:
                yield observed.return_value, prev, self.observations[observed.time]

    def raw_operations(self, function: Function) -> list[Operation]:
        operations = []
        for variable, prev, nxt in self.compared_values(function):
            kind = guess_operation(prev, nxt, function)
            if kind is not None:
                operation = Operation(kind, variable)
                if operation not in operations:
                    operations.append(operation)
        return operations

    def run(self) -> AnalysisReport:
        acting = [f for f in self.parsed.player_functions()
                  if f.kind in (FunctionKind.INPUT, FunctionKind.INOUT)]
        unknown = []
        for function in acting:
            function.operations = self.raw_operations(function)
            if not function.operations:
                unknown.append(function)

        operations = self.uniform_operations(acting)
        variables = self.define_getters_setters(operations)
        return AnalysisReport(self.observations, variables, operations, unknown)

    @staticmethod
    def uniform_operations(acting: list[Function]) -> dict[str, list[Operation]]:
        """Garde, pour chaque fonction, les opérations majoritaires et les applique à tous ses appels."""
        calls = Counter(function.name for function in acting)
        counts: dict[str, Counter] = {name: Counter() for name in calls}
        for function in acting:
            counts[function.name].update(function.operations)
        retained = {name: [op for op, n in counter.items() if n >= calls[name] * MAJORITY]
                    for name, counter in counts.items()}
        for function in acting:
            function.operations = list(retained[function.name])
        return retained

    def define_getters_setters(self, operations: dict[str, list[Operation]]) -> dict[str, Variable]:
        """Associe à chaque variable les fonctions qui la lisent et celles qui la modifient."""
        variables: dict[str, Variable] = {}
        for variable in self.parsed.variables:
            canonical = variables.setdefault(variable.name, variable)
            variable.getters, variable.setters = canonical.getters, canonical.setters

        seen_getters = set()
        for function in self.timeline:
            name = function.return_value.name
            if name in variables and (function.name, name) not in seen_getters:
                seen_getters.add((function.name, name))
                variables[name].getters.append(function)

        for function_name, function_operations in operations.items():
            function = next(f for f in self.timeline if f.name == function_name)
            for operation in function_operations:
                setters = variables[operation.variable.name].setters
                if function not in setters:
                    setters.append(function)
        return variables


def analyse(parsed: ParsedExample, observations: dict[int, object]) -> AnalysisReport:
    return Analyzer(parsed, observations).run()
