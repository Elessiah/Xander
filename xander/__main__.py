"""Point d'entrée.

``python -m xander res/exampleMorpion.py`` : ce que la mère comprend de l'exemple.

``python -m xander res/exampleMorpion.py --prof Games.MinmaxMorpion:minmax_morpion_play --son morpion`` :
la mère élève un fils en le corrigeant à chaque erreur, affiche sa courbe
d'apprentissage et l'écrit dans ``output/sons/morpion.py``.

``python -m xander res/exampleJumper.py --son jumper --parties 30`` : un jeu à un
joueur n'a pas de professeur ; la mère juge chaque coup par ce qui arrive, dans
son labo.

``python -m xander res/problemes/entrainement/mots.json [--probleme initiales] [--son NOM]`` :
un problème « entrée -> sortie » (ou un lot) : le programme que la mère a
trouvé, ce que répond le fils qu'elle écrit, et le score si le fichier donne
les réponses attendues.
"""

import argparse
import importlib
import sys

from xander import concepts
from xander.lab import LabError
from xander.mother import OUTPUT_DIR, Mother
from xander.parser import ExampleSyntaxError
from xander.problemes import ProblemeMalForme, est_un_probleme as is_problem
from xander.rebuilder import ReplayError
from xander.un_joueur import Solo


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


def print_solo(education: Solo, args) -> None:
    """Le bilan d'une éducation à un joueur : fin, horizon, souvenirs et petits motifs."""
    from xander.mother import render_son
    from xander import son_writer
    knowledge = education.knowledge
    print(f"Actions : {knowledge['actions']} ({knowledge['free']}, vu dans le labo)")
    print(f"Fin : {knowledge['fin']} (lu dans l'exemple) ; un coup est jugé sur {education.horizon} coup(s) "
          f"(durées d'effet vues : {education.durations or 'aucune'})")
    memories, motifs = knowledge["memories"], knowledge["motifs"]
    print(f"Souvenirs (états exacts) : {len(memories)} ; petits motifs : {len(motifs)}")
    for motif, move in motifs:
        print(f"  {son_writer.motif_text(motif)} -> {move!r}")
    print(f"Réflexion : au plus {education.max_views} position(s) regardée(s) à l'avance pour un coup")
    print(f"Bilan sans correction : {education.evaluate()}")
    if args.son:
        path = OUTPUT_DIR / "sons" / f"{args.son}.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_son(args.son, education), encoding="utf-8")
        print(f"\nFils écrit dans {path}")


def print_bulletin(education, args) -> None:
    """Le bulletin du fils (voir :mod:`xander.bulletin`), si on l'a demandé."""
    if not args.bulletin:
        return
    from pathlib import Path

    from xander.bulletin import bulletin
    print("\n" + bulletin(education, Path(args.example).stem).decrire())


def solve_problems(path: str, only: str | None = None, son: str | None = None) -> int:
    """Un problème « entrée -> sortie » (fichier ``.json``) : ce que la mère comprend, ce que répond le fils."""
    import json
    import textwrap

    from xander.fils_repondeur import source
    from xander.mesure import Bilan, resoudre
    from xander.problemes import lire_problemes

    problems = lire_problemes(path)
    if only:
        problems = [p for p in problems if p.nom == only]
        if not problems:
            raise ValueError(f"aucun problème nommé {only!r} dans {path}")

    def show(value) -> str:
        return value if not isinstance(value, (list, str, int, float, bool)) else json.dumps(value, ensure_ascii=False)

    results = []
    for problem in problems:
        result = resoudre(problem)
        results.append(result)
        print(f"\nProblème « {problem.nom} » : {len(problem.paires)} paire(s), {len(problem.questions)} question(s)")
        print(textwrap.indent(result.comprehension.decrire(), "  "))
        if result.code is None:
            continue
        for i, question in enumerate(problem.questions):
            line = f"  Le fils répond : {show(question)} -> {show(result.reponses[i])}"
            if result.deuxiemes is not None:
                line += f" (deuxième essai : {show(result.deuxiemes[i])})"
            if problem.attendues is not None:
                line += f" ; attendu {show(problem.attendues[i])}"
            print(line)
        if problem.attendues is not None:
            verdict = ("réussi au premier essai" if result.premier_essai else
                       "réussi au deuxième essai" if result.deux_essais else "raté")
            print(f"  Verdict de l'examinateur : {verdict}")
        if son:
            name = son if len(problems) == 1 else f"{son}_{problem.nom}"
            target = OUTPUT_DIR / "sons" / f"{name.replace('-', '_')}.py"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source(problem.nom, result.comprehension, problem.questions), encoding="utf-8")
            print(f"  Fils écrit dans {target}")
    print("\n" + Bilan(results).decrire())
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(prog="xander", description="Apprend un jeu à partir d'un exemple de partie, "
                                     "ou un problème « entrée -> sortie » (fichier .json).")
    parser.add_argument("example", help="fichier d'exemple (voir res/) ou problème .json (voir res/problemes/)")
    parser.add_argument("--probleme", metavar="NOM", help="(problèmes .json) ne traiter que ce problème du lot")
    parser.add_argument("-v", "--verbose", action="store_true", help="affiche le détail de l'analyse")
    parser.add_argument("--keep", action="store_true", help="conserve le script de rejeu dans output/poolTest.py")
    parser.add_argument("--prof", metavar="MODULE:FONCTION",
                        help="professeur qui joue un coup, ex. Games.MinmaxMorpion:minmax_morpion_play")
    parser.add_argument("--parties", type=int, default=200, help="parties d'entraînement du fils (défaut : 200)")
    parser.add_argument("--son", metavar="NOM", help="écrit le fils dans output/sons/NOM.py")
    parser.add_argument("--bulletin", action="store_true",
                        help="après l'éducation, affiche le bulletin du fils (taille, compression, origine "
                        "des coups, généralisation à des positions jamais vues)")
    parser.add_argument("-q", "--quiet", action="store_true", help="n'affiche pas le détail de chaque partie")
    args = parser.parse_args(argv)

    if is_problem(args.example):
        try:
            return solve_problems(args.example, args.probleme, args.son)
        except (ProblemeMalForme, OSError, UnicodeDecodeError, ValueError) as error:
            print(f"Erreur : {error}", file=sys.stderr)
            return 1
    mother = Mother(verbose=args.verbose)
    try:
        print(mother.learn(args.example, keep_pool_test=args.keep).describe())
        if not (args.prof or args.son or args.bulletin):
            return 0
        teacher = load_teacher(args.prof) if args.prof else None
        print("\nÉducation du fils :")
        education = mother.raise_son(args.example, teacher, args.parties,
                                     on_game=None if args.quiet else print)
        print_curve(education.records)
        knowledge = education.knowledge
        print(f"\nAction : {education.trials.describe()}")
        if isinstance(education, Solo):
            print_solo(education, args)
            print_bulletin(education, args)
            return 0
        if education.tableau:
            print(f"Motifs compris : {knowledge['patterns']}")
            print(f"Symétries : {len(knowledge['symmetries']) + 1} façon(s) de voir une position "
                  "(renumérotations vérifiées dans le labo)")
        else:
            print(f"Actions permises : {knowledge['actions']}, si {knowledge['free']} (vu dans le labo)")
            print(f"Fins comprises (valeur -> qui gagne) : {knowledge['ends']}")
            if education.unknown_ends:
                print(f"Fins vues sans savoir qui gagne : {education.unknown_ends}")
        memories = knowledge["memories"]
        small = sum("?" in key for key in memories)
        print(f"Règles : {' > '.join(knowledge['rules']) or 'aucune'} ; souvenirs : {len(memories)}"
              f" (dont {small} petit(s) motif(s), « ? » : une case qui ne compte pas)")
        for key, move in memories.items():
            print(f"  {key} -> {move}")
        print("Concepts construits par la mère (une règle : jouer un coup après lequel…) :")
        needed = concepts.dependances(knowledge["rules"], knowledge["concepts"])
        for name in needed:
            mark = "règle" if name in knowledge["rules"] else "brique"
            print(f"  {name:<11} [{mark}] {concepts.decrire(knowledge['concepts'][name])}")
            print(f"  {'':<11}         {knowledge['concepts'][name]!r}")
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
        print_bulletin(education, args)
    except (ExampleSyntaxError, ReplayError, LabError, OSError, UnicodeDecodeError, ValueError,
            ImportError, AttributeError) as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
