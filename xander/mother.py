"""La logique mère : elle apprend un jeu à partir d'un exemple et crée des enfants.

Chaîne complète ::

    fichier d'exemple --parse--> ParsedExample --rejeu--> observations
        --analyse--> AnalysisReport --synthèse--> GameModel --> enfant

La création d'un enfant (un joueur autonome qui réutilise les fonctions du jeu)
et sa correction par la mère ne sont pas encore implémentées : ``create_son``
génère pour l'instant un squelette qui contient ce que la mère a compris.
"""

from __future__ import annotations

from pathlib import Path
from pprint import pformat

from xander.analyzer import analyse
from xander.game_model import GameModel
from xander.parser import parse_example
from xander.rebuilder import PROJECT_ROOT, replay

OUTPUT_DIR = PROJECT_ROOT / "output"


class Mother:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def log(self, message: str) -> None:
        if self.verbose:
            print(message)

    def learn(self, example_path: str | Path, keep_pool_test: bool = False) -> GameModel:
        """Analyse l'exemple ``example_path`` et renvoie le modèle du jeu."""
        parsed = parse_example(example_path)
        self.log(parsed.summary())
        script = OUTPUT_DIR / "poolTest.py" if keep_pool_test else None
        observations = replay(parsed, script)
        self.log(f"{len(observations)} valeurs observées pendant le rejeu")
        report = analyse(parsed, observations)
        return GameModel.from_analysis(parsed, report)

    def create_son(self, name: str, example_path: str | Path,
                   output_dir: str | Path = OUTPUT_DIR / "sons") -> Path:
        """Apprend le jeu puis écrit le squelette de l'enfant ``name``.

        TODO : générer une stratégie de jeu à partir des getters / setters,
        faire jouer l'enfant, puis le corriger à l'aide de ``back_function``.
        """
        model = self.learn(example_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{name}.py"
        path.write_text(render_son(name, model), encoding="utf-8")
        return path


def render_son(name: str, model: GameModel) -> str:
    knowledge = {
        "players": model.players_names,
        "actions_per_turn": model.turn_pattern,
        "back": model.back_function.call_source() if model.back_function else None,
        "variables": {
            v.name: {
                "kind": v.kind,
                "size": v.size,
                "getters": sorted({f.short_name for f in v.getters}),
                "setters": sorted({f.short_name for f in v.setters}),
            }
            for v in model.env
        },
        "operations": {
            function: [(op.kind.name, op.variable.name) for op in operations]
            for function, operations in (model.report.operations.items() if model.report else [])
        },
    }
    return (
        f'"""Enfant « {name} » généré par la logique mère de Xander.\n\n'
        "Squelette : la stratégie n'est pas encore générée.\n"
        '"""\n\n'
        f"KNOWLEDGE = {pformat(knowledge, sort_dicts=False)}\n\n\n"
        "def play(game):\n"
        '    """Joue un tour sur ``game``. À générer par la mère."""\n'
        "    raise NotImplementedError\n"
    )
