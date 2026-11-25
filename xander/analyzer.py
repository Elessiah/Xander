"""Déduction du rôle de chaque fonction à partir des valeurs observées.

Pour chaque appel « qui agit » (INPUT ou INOUT) on compare une variable juste
avant et juste après l'appel : chaque comparaison est un **cas** (voir
:class:`~xander.effets.Cas`). Les variables comparées sont la valeur de retour
de l'appel (INOUT) et celles des getters appelés juste après lui.

L'Analyzer ne teste plus d'hypothèses écrites à la main : pour chaque fonction
et chaque variable, la mère construit les plus petits programmes qui
expliquent tous les cas observés (voir :mod:`xander.effets`). Un cas où il n'y
a rien à comparer (la fin de partie renvoie un booléen, ou rien n'a changé)
n'est pas un cas.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from xander import effets
from xander.effets import Cas
from xander.model import Function, FunctionKind, Operation, Variable
from xander.parser import ParsedExample


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
    cases: dict[str, dict[str, list[Cas]]] = field(default_factory=dict)  # fonction -> variable -> cas


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

    def cases(self, function: Function) -> dict[str, tuple[Variable, list[Cas]]]:
        """Les cas d'un appel, par nom de variable."""
        found: dict[str, tuple[Variable, list[Cas]]] = {}
        for variable, prev, nxt in self.compared_values(function):
            case = Cas(prev, tuple(function.arguments), nxt)
            if case.forme is not None:
                found.setdefault(variable.name, (variable, []))[1].append(case)
        return found

    def run(self) -> AnalysisReport:
        acting = [f for f in self.parsed.player_functions()
                  if f.kind in (FunctionKind.INPUT, FunctionKind.INOUT)]
        by_call = {function.time: self.cases(function) for function in acting}

        operations: dict[str, list[Operation]] = {}
        all_cases: dict[str, dict[str, list[Cas]]] = {}
        for name in dict.fromkeys(f.name for f in acting):
            pooled: dict[str, tuple[Variable, list[Cas]]] = {}
            for function in acting:
                if function.name == name:
                    for variable_name, (variable, cases) in by_call[function.time].items():
                        pooled.setdefault(variable_name, (variable, []))[1].extend(cases)
            all_cases[name] = {variable.name: cases for variable, cases in pooled.values()}
            operations[name] = [Operation(hypothesis, variable)
                                for variable, cases in pooled.values()
                                for hypothesis in effets.decouvrir(cases)]

        unknown = []
        for function in acting:
            function.operations = list(operations[function.name])
            calls = by_call[function.time]
            explained = any(effets.explique(op.programme, case)
                            for op in function.operations
                            for case in calls.get(op.variable.name, (None, []))[1])
            if not explained:
                unknown.append(function)

        variables = self.define_getters_setters(operations)
        return AnalysisReport(self.observations, variables, operations, unknown, all_cases)

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
