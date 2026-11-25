"""Déduction du rôle de chaque fonction à partir des valeurs observées.

Pour chaque appel « qui agit » (INPUT ou INOUT) on compare une variable juste
avant et juste après l'appel, puis on teste des hypothèses codées en dur
(voir :class:`~xander.model.FunctionOperation`) :

* tableau + 1 paramètre  -> la case d'indice / de valeur <param> a changé ?
* tableau + 2 paramètres -> les cases <p1> et <p2> ont changé ?
* nombre  + 1 paramètre  -> nombre -= / += / = <param> ?
* tableau + 1 paramètre, sinon -> le paramètre désigne une *file* de cases
  (``<param> + décalage``, puis ``+ pas`` à chaque fois) et c'est la première
  case libre de la file qui change ? (gravité du Puissance 4, une pile, un tube…)
  Le décalage et le pas ne sont pas donnés : l'Analyzer les mesure sur tous les
  appels de la fonction (les cases changées par deux appels de même argument).

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


def test_sequence_target_index(prev, nxt, argument, offset: int, step: int) -> bool:
    """Une seule case a changé, et c'est la première case libre de la file ``argument +
    offset``, ``+ step``… Une case libre est une case qui valait ce que valait la case changée
    (au Puissance 4, une case vide) : le jeton n'a pas pu s'arrêter avant elle."""
    if (not isinstance(argument, int) or isinstance(argument, bool) or not step
            or len(prev) != len(nxt)):
        return False
    changed = [i for i in range(len(prev)) if prev[i] != nxt[i]]
    if len(changed) != 1:
        return False
    target, free = changed[0], prev[changed[0]]
    cell = argument + offset
    while 0 <= cell < len(prev):
        if cell == target:
            return True
        if prev[cell] == free:
            return False
        cell += step
    return False


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
        for function in acting:
            function.operations = self.raw_operations(function)
        self.fit_sequences(acting)
        unknown = [function for function in acting if not function.operations]

        operations = self.uniform_operations(acting)
        variables = self.define_getters_setters(operations)
        return AnalysisReport(self.observations, variables, operations, unknown)

    def fit_sequences(self, acting: list[Function]) -> None:
        """Pour une fonction à un paramètre dont l'argument ne désigne pas directement la case
        changée : cherche le décalage et le pas d'une file qui expliquent la majorité de ses
        appels (``SEQUENCE_TARGET_INDEX``).

        Décalages essayés : case changée - argument. Pas essayés : l'écart entre les cases
        changées par deux appels successifs de même argument. On garde la file qui explique
        le plus d'appels, puis le plus petit décalage et le plus petit pas.
        """
        calls = Counter(function.name for function in acting)
        for name in calls:
            functions = [f for f in acting if f.name == name and len(f.parameters) == 1]
            direct = sum(any(op.kind is FunctionOperation.SINGLE_TARGET_INDEX for op in f.operations)
                         for f in functions)
            if not functions or direct >= calls[name] * MAJORITY:
                continue
            seen: dict[str, list] = {}   # variable -> (appel, variable, avant, après, case changée)
            for function in functions:
                for variable, prev, nxt in self.compared_values(function):
                    if not (isinstance(prev, list) and isinstance(nxt, list) and len(prev) == len(nxt)):
                        continue
                    changed = [i for i in range(len(prev)) if prev[i] != nxt[i]]
                    observations = seen.setdefault(variable.name, [])
                    if len(changed) == 1 and all(o[0] is not function for o in observations):
                        observations.append((function, variable, prev, nxt, changed[0]))
            for observations in seen.values():
                self.fit_sequence(observations, calls[name])

    @staticmethod
    def fit_sequence(observations: list, nb_calls: int) -> None:
        offsets = {cell - f.arguments[0] for f, _, _, _, cell in observations
                   if isinstance(f.arguments[0], int) and not isinstance(f.arguments[0], bool)}
        steps, last = set(), {}
        for f, _, _, _, cell in observations:
            argument = f.arguments[0]
            if argument in last and last[argument] != cell:
                steps.add(cell - last[argument])
            last[argument] = cell
        best = None
        for offset in sorted(offsets):
            for step in sorted(steps):
                explained = [o for o in observations
                             if test_sequence_target_index(o[2], o[3], o[0].arguments[0], offset, step)]
                score = (-len(explained), abs(offset), abs(step))
                if explained and (best is None or score < best[0]):
                    best = (score, offset, step, explained)
        if best is None or len(best[3]) < nb_calls * MAJORITY:
            return
        _, offset, step, explained = best
        for function, variable, _, _, _ in explained:
            operation = Operation(FunctionOperation.SEQUENCE_TARGET_INDEX, variable, (offset, step))
            if operation not in function.operations:
                function.operations.append(operation)

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
