"""Point d'entrée.

``python -m xander res/exampleMorpion.py`` : ce que la mère comprend de l'exemple.

``python -m xander res/exampleMorpion.py --prof Games.MinmaxMorpion:minmax_morpion_play --son morpion`` :
la mère élève un fils en le corrigeant à chaque erreur, affiche sa courbe
d'apprentissage et l'écrit dans ``output/sons/morpion.py``.
"""

import argparse
import importlib
import sys

from xander.lab import LabError
from xander.mother import OUTPUT_DIR, Mother
from xander.parser import ExampleSyntaxError
from xander.rebuilder import ReplayError


def load_teacher(path: str):
    """``module:fonction`` -> la fonction ``fonction(game)`` qui joue un coup."""
    module, _, function = path.partition(":")
    if not function:
        raise ValueError(f"--prof attend module:fonction, pas {path!r}")
    return getattr(importlib.import_module(module), function)


def print_curve(records) -> None:
    games = [r for r in records if r.number > 0]
    if not games:
        return
    print("\nCourbe d'apprentissage (erreurs par tranche de 10 parties) :")
    for start in range(0, len(games), 10):
        block = games[start:start + 10]
        errors = sum(len(r.lessons) for r in block)
        print(f"  parties {block[0].number:>3}-{block[-1].number:<3} {'#' * errors:<20} {errors}")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(prog="xander", description="Apprend un jeu à partir d'un exemple de partie.")
    parser.add_argument("example", help="fichier d'exemple (voir res/)")
    parser.add_argument("-v", "--verbose", action="store_true", help="affiche le détail de l'analyse")
    parser.add_argument("--keep", action="store_true", help="conserve le script de rejeu dans output/poolTest.py")
    parser.add_argument("--prof", metavar="MODULE:FONCTION",
                        help="professeur qui joue un coup, ex. Games.MinmaxMorpion:minmax_morpion_play")
    parser.add_argument("--parties", type=int, default=200, help="parties d'entraînement du fils (défaut : 200)")
    parser.add_argument("--son", metavar="NOM", help="écrit le fils dans output/sons/NOM.py")
    parser.add_argument("-q", "--quiet", action="store_true", help="n'affiche pas le détail de chaque partie")
    args = parser.parse_args(argv)

    mother = Mother(verbose=args.verbose)
    try:
        print(mother.learn(args.example, keep_pool_test=args.keep).describe())
        if not (args.prof or args.son):
            return 0
        teacher = load_teacher(args.prof) if args.prof else None
        print("\nÉducation du fils :")
        education = mother.raise_son(args.example, teacher, args.parties,
                                     on_game=None if args.quiet else print)
        print_curve(education.records)
        knowledge = education.knowledge
        print(f"\nMotifs compris : {knowledge['patterns']}")
        print(f"Règles : {' > '.join(knowledge['rules']) or 'aucune'} ; souvenirs : {len(knowledge['memories'])}")
        print(f"Réflexion : au plus {education.max_views} position(s) regardée(s) pour un coup")
        if teacher is not None:
            print("Bilan sans correction :")
            for opponent, score in education.evaluate().items():
                print(f"  contre {opponent:<10} : " + ", ".join(f"{n} {k}" for k, n in score.items()))
        if args.son:
            path = OUTPUT_DIR / "sons" / f"{args.son}.py"
            path.parent.mkdir(parents=True, exist_ok=True)
            from xander.mother import render_son
            path.write_text(render_son(args.son, education), encoding="utf-8")
            print(f"\nFils écrit dans {path}")
    except (ExampleSyntaxError, ReplayError, LabError, OSError, UnicodeDecodeError, ValueError,
            ImportError, AttributeError) as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
