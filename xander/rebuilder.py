"""Rejoue un exemple pour observer les valeurs renvoyées par chaque appel.

L'exemple est réécrit en un script « pool test » qui exécute tous les appels
dans l'ordre chronologique et imprime, pour chaque valeur de retour, une
ligne ``@@xander <time> <variable> <repr(valeur)>``. Le script est lancé dans
un sous-processus (le jeu peut imprimer ce qu'il veut, seules les lignes
préfixées sont lues).
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

from xander.model import Function
from xander.parser import ParsedExample

MARKER = "@@xander"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class ReplayError(Exception):
    """Le script reconstruit a échoué."""


def build_pool_test(parsed: ParsedExample) -> str:
    """Renvoie le code source du script qui rejoue l'exemple."""
    lines = list(parsed.imports)
    lines.append("")
    for function in parsed.init_functions + parsed.player_functions():
        lines.append(function.call_source())
        if _is_observed(function):
            name = function.return_value.name
            lines.append(f"print({MARKER!r}, {function.time}, {name!r}, repr({name}), flush=True)")
    return "\n".join(lines) + "\n"


def _is_observed(function: Function) -> bool:
    variable = function.return_value
    return not variable.is_empty and variable.kind != "game"


def parse_observations(stdout: str) -> dict[int, object]:
    """Lit la sortie du pool test : ``{time: valeur}``."""
    observations = {}
    for line in stdout.splitlines():
        if not line.startswith(MARKER + " "):
            continue
        _, time, _name, value = line.split(" ", 3)
        try:
            observations[int(time)] = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            observations[int(time)] = value  # objet non littéral : on garde sa repr
    return observations


def replay(parsed: ParsedExample, script_path: str | Path | None = None,
           timeout: float = 30) -> dict[int, object]:
    """Écrit (optionnellement) puis exécute le pool test, renvoie les observations."""
    source = build_pool_test(parsed)
    if script_path is not None:
        script_path = Path(script_path)
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(source, encoding="utf-8")

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(PROJECT_ROOT), env.get("PYTHONPATH")]))
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run([sys.executable, "-c", source], cwd=PROJECT_ROOT, env=env,
                            capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    if result.returncode != 0:
        raise ReplayError(f"le rejeu de l'exemple a échoué :\n{result.stderr}")
    return parse_observations(result.stdout)
