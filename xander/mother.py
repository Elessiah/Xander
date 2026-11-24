"""La logique mère : elle apprend un jeu à partir d'un exemple et crée des enfants.

Chaîne complète ::

    fichier d'exemple --parse--> ParsedExample --rejeu--> observations
        --analyse--> AnalysisReport --synthèse--> GameModel --> enfant

Puis la mère élève un fils (voir :mod:`xander.education`) : il naît sans rien
savoir, joue, et la mère corrige chacune de ses erreurs en comprenant pourquoi
c'en était une. Le code du fils est écrit par la mère (:mod:`xander.son_writer`) :
il ne contient que les règles et les souvenirs qu'elle lui a appris, et ne
revient jamais en arrière.
"""

from __future__ import annotations

from pathlib import Path

from xander.analyzer import analyse
from xander.education import Education
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
        return self.understand(example_path, keep_pool_test)[1]

    def understand(self, example_path: str | Path, keep_pool_test: bool = False):
        """Comme :meth:`learn`, mais renvoie aussi l'exemple lu : ``(parsed, model)``."""
        parsed = parse_example(example_path)
        self.log(parsed.summary())
        script = OUTPUT_DIR / "poolTest.py" if keep_pool_test else None
        observations = replay(parsed, script)
        self.log(f"{len(observations)} valeurs observées pendant le rejeu")
        return parsed, GameModel.from_analysis(parsed, analyse(parsed, observations))

    def raise_son(self, example_path: str | Path, teacher=None, nb_games: int = 200,
                  seed: int = 0, on_game=None) -> Education:
        """Fait naître un fils (il ne sait rien), lui montre l'exemple, puis le corrige.

        Sans ``teacher``, le fils ne reçoit que la leçon de l'exemple.
        """
        parsed, model = self.understand(example_path)
        education = Education(parsed, model, teacher, seed)
        lesson = education.first_lesson()
        if on_game:
            on_game(lesson)
        if teacher is not None and nb_games:
            education.train(nb_games, on_game)
        return education

    def create_son(self, name: str, example_path: str | Path,
                   output_dir: str | Path = OUTPUT_DIR / "sons", teacher=None,
                   nb_games: int = 200, on_game=None) -> Path:
        """Élève un fils (voir :meth:`raise_son`) et l'écrit dans ``output_dir/<name>.py``."""
        education = self.raise_son(example_path, teacher, nb_games, on_game=on_game)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{name}.py"
        path.write_text(render_son(name, education), encoding="utf-8")
        return path


def render_son(name: str, education: Education) -> str:
    """Le code du fils tel que la mère l'a écrit (fichier autonome, sans import de Xander)."""
    return education.source(name)
