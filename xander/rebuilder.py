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
import tempfile
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
        start = line.find(MARKER + " ")  # le jeu a pu écrire sans retour à la ligne
        if start == -1:
            continue
        parts = line[start:].split(" ", 3)
        if len(parts) != 4 or not (parts[1].isascii() and parts[1].isdecimal()):
            continue  # texte du jeu qui contient le marqueur par hasard
        time, value = int(parts[1]), parts[3]
        try:
            observations[time] = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            observations[time] = value  # objet non littéral : on garde sa repr
    return observations


def replay(parsed: ParsedExample, script_path: str | Path | None = None,
           timeout: float = 30) -> dict[int, object]:
    """Écrit (optionnellement) puis exécute le pool test, renvoie les observations."""
    source = build_pool_test(parsed)
    if script_path is None:
        with tempfile.TemporaryDirectory() as directory:
            return replay(parsed, Path(directory) / "poolTest.py", timeout)
    script_path = Path(script_path)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(source, encoding="utf-8")

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(PROJECT_ROOT), env.get("PYTHONPATH")]))
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        result = subprocess.run([sys.executable, str(script_path)], cwd=PROJECT_ROOT, env=env,
                                stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                encoding="utf-8", timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ReplayError(f"le rejeu a dépassé {timeout} s (boucle infinie ou appel à input() ?)") from None
    if result.returncode != 0:
        raise ReplayError(f"le rejeu de l'exemple a échoué :\n{result.stderr}")
    return parse_observations(result.stdout)
