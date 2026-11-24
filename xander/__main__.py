"""Point d'entrée : ``python -m xander res/exampleMorpion.py``."""

import argparse
import sys

from xander.mother import Mother
from xander.parser import ExampleSyntaxError
from xander.rebuilder import ReplayError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xander", description="Apprend un jeu à partir d'un exemple de partie.")
    parser.add_argument("example", help="fichier d'exemple (voir res/)")
    parser.add_argument("-v", "--verbose", action="store_true", help="affiche le détail de l'analyse")
    parser.add_argument("--keep", action="store_true", help="conserve le script de rejeu dans output/poolTest.py")
    parser.add_argument("--son", metavar="NOM", help="génère aussi le squelette d'un enfant dans output/sons/")
    args = parser.parse_args(argv)

    mother = Mother(verbose=args.verbose)
    try:
        model = mother.learn(args.example, keep_pool_test=args.keep)
        print(model.describe())
        if args.son:
            print(f"\nEnfant écrit dans {mother.create_son(args.son, args.example)}")
    except (ExampleSyntaxError, ReplayError, OSError) as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
