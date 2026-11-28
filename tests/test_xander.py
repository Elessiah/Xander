import contextlib
import functools
import io
import textwrap
import unittest
from pathlib import Path

from Games.MinmaxMorpion import minmax_morpion_play
from Games.MinmaxNim import minmax_nim_play
from Games.MinmaxPuissance4 import WINDOWS, minmax_puissance4_play
from Games.Morpion import LINES, Morpion, is_free, winner_of
from xander.analyzer import analyse
from xander.education import REPRISES, Case, Education
from xander.game_model import GameModel
from xander.lab import Lab, LabError
from xander.model import Function, Variable
from xander.mother import Mother, render_son
from xander.parser import ExampleParser, parse_example
from xander.rebuilder import ReplayError, build_pool_test, parse_observations, replay
from xander import concepts, effets, son_writer, symmetries, vocabulary
from xander.concepts import LUI, MOI

RES = Path(__file__).resolve().parent.parent / "res"


def parse(text: str):
    return ExampleParser().parse_text(textwrap.dedent(text))


def call(*arguments):
    return Function("game.f", Variable("array", 3, "board"), [repr(a) for a in arguments], 0, list(arguments))


#: Les anciennes hypothèses écrites à la main, que la mère doit retrouver seule
#: (écrites ici pour comparer, jamais données à la mère).
A0, A1, AVANT = effets.arg(0), effets.arg(1), effets.avant()
CASE_INDICE = effets.Hypothese(effets.CHANGEES, effets.case(A0))
CASE_VALANT = effets.Hypothese(effets.CHANGEES, effets.valant(A0))
DEPLACER_INDICE = effets.Hypothese(effets.CHANGEES, effets.union(effets.case(A0), effets.case(A1)))
DEPLACER_VALANT = effets.Hypothese(effets.CHANGEES, effets.union(effets.valant(A0), effets.valant(A1)))
RETIRER = effets.Hypothese(effets.APRES, effets.moins(AVANT, A0))
AJOUTER = effets.Hypothese(effets.APRES, effets.plus(AVANT, A0))
FIXER = effets.Hypothese(effets.APRES, A0)
GRAVITE = effets.Hypothese(effets.CHANGEES, effets.premiere_de(effets.portee(A0), effets.valant(effets.const(" "))))


def discover(*transitions, portees=None):
    """``(avant, arguments, après)`` -> hypothèses trouvées par la mère."""
    return effets.decouvrir([effets.Cas(a, tuple(args), b) for a, args, b in transitions], portees=portees)


class RebuilderTest(unittest.TestCase):
    def test_pool_test_and_observations(self):
        parsed = parse_example(RES / "exampleMorpion.py")
        source = build_pool_test(parsed)
        self.assertIn("board = game.play(4)", source)
        self.assertNotIn("'game'", source)  # la variable de jeu n'est pas observée
        observations = parse_observations("bruit\n@@xander 3 board ['0', 'X']\nprompt> @@xander 4 b True\n"
                                          "le jeu dit @@xander salut\n@@xander abc d 1\n@@xander ² a 1\n")
        self.assertEqual(observations, {3: ["0", "X"], 4: True})

    def test_unhashable_literal_is_not_a_crash(self):
        parsed = parse("# player A\ngame.play({[1]: 2})\n")
        self.assertEqual(parsed.players["A"].functions_used[0].arguments, [None])

    def test_long_example_replays(self):
        turn = "# player {}\nnb = game.get_game_state()  # integer\nnb = game.play(1)  # integer\n"
        text = ("# include\nfrom Games.Allumettes import Allumettes\n# init\ngame = Allumettes()  # game\n"
                "game.set_max_nb_allumettes(1000)\nnb = game.init('X')  # integer\n"
                + "".join(turn.format(p) for p in "XO" * 250))
        parsed = ExampleParser().parse_text(text)
        self.assertGreater(len(build_pool_test(parsed)), 40_000)  # au-delà de la limite Windows de -c
        self.assertEqual(len(replay(parsed)), 1001)

    def test_replay_timeout(self):
        parsed = ExampleParser().parse_text("# include\nimport time\n# player A\ntime.sleep(5)\n")
        with self.assertRaisesRegex(ReplayError, "dépassé"):
            replay(parsed, timeout=1)


class EffectDiscoveryTest(unittest.TestCase):
    """La mère retrouve les anciennes hypothèses sans qu'elles soient nommées nulle part."""

    def test_single_target_index(self):
        self.assertEqual(discover((["a", "b", "c"], [1], ["a", "X", "c"]),
                                  (["a", "b", "c"], [2], ["a", "b", "X"])), [CASE_INDICE])

    def test_single_target_name(self):
        self.assertEqual(discover((["a", "b", "c"], ["b"], ["a", "X", "c"]),
                                  (["a", "b", "c"], ["c"], ["a", "b", "X"])), [CASE_VALANT])

    def test_index_and_name_coexist(self):
        """Au Morpion, la case d'indice p vaut « p » : rien ne les départage encore."""
        self.assertEqual(discover((["0", "1", "2"], [1], ["0", "X", "2"]),
                                  (["0", "X", "2"], [2], ["0", "X", "O"])), [CASE_INDICE, CASE_VALANT])

    def test_src_dest(self):
        self.assertEqual(discover((["P", " ", "c"], [0, 1], [" ", "P", "c"]),
                                  (["c", "P", " "], [1, 2], ["c", " ", "P"])), [DEPLACER_INDICE])
        self.assertEqual(discover((["P", "e", "c"], ["P", "e"], ["e", "P", "c"]),
                                  (["c", "P", "e"], ["P", "e"], ["c", "e", "P"])), [DEPLACER_VALANT])

    def test_quantity(self):
        self.assertEqual(discover((10, [3], 7), (7, [2], 5)), [RETIRER])
        self.assertEqual(discover((10, [3], 13), (7, [2], 9)), [AJOUTER])
        self.assertEqual(discover((10, [3], 3), (7, [2], 2)), [FIXER])

    def test_sequence(self):
        """Gravité, pile, tube : la première case vide de ce que l'action remplit, vu dans le labo.
        L'ordre vient de l'observation : une gravité vers le haut s'écrit de la même façon."""
        vide = [" "] * 6  # 2 colonnes de 3 cases : case = ligne * 2 + colonne
        cases = ((vide, [0], ["O", " ", " ", " ", " ", " "]),
                 (["O", " ", " ", " ", " ", " "], [0], ["O", " ", "X", " ", " ", " "]),
                 (vide, [1], [" ", "X", " ", " ", " ", " "]))
        self.assertEqual(discover(*cases), [])  # sans le labo, rien ne l'explique
        for portees in ({0: [0, 2, 4], 1: [1, 3, 5]}, {0: [0, 2, 4, 9], 1: [1, 3]}):
            self.assertEqual(discover(*cases, portees=portees), [GRAVITE])
        haut = ((vide, [0], [" ", " ", " ", " ", "O", " "]),
                (vide[:4] + ["O", " "], [0], [" ", " ", "X", " ", "O", " "]),
                (vide, [1], [" ", " ", " ", " ", " ", "X"]))
        self.assertEqual(discover(*haut, portees={0: [4, 2, 0], 1: [5, 3, 1]}), [GRAVITE])

    def test_measured_constants(self):
        """Décalages (case changée - argument) et valeurs des cases changées."""
        cas = [effets.Cas([" "] * 4, (1,), [" ", "O", " ", " "]),
               effets.Cas([" ", "O", " ", " "], (1,), [" ", "O", " ", "X"])]
        self.assertEqual(effets.constantes(cas), (0, 2, " "))  # 1 - 1 et 3 - 1 ; la case vide

    def test_nothing_matches(self):
        self.assertEqual(discover((["a", "b", "c"], [1], ["X", "X", "c"]),
                                  (["a", "b", "c"], [0], ["a", "Y", "Y"])), [])
        self.assertEqual(discover((10, [3], 9), (7, [2], 1)), [])

    def test_not_a_case(self):
        """La fin de partie renvoie un booléen, un coup refusé ne change rien : rien à expliquer."""
        self.assertIsNone(effets.Cas(["a", "b"], (1,), True).forme)
        self.assertIsNone(effets.Cas(["a", "b"], (1,), ["a", "b"]).forme)

    def test_one_case_is_a_coincidence(self):
        self.assertEqual(discover((10, [3], 7)), [])
        self.assertEqual(discover((10, [3], 7), (10, [3], 7)), [])  # le même cas deux fois

    def test_every_case_must_be_explained(self):
        self.assertEqual(discover((10, [3], 7), (7, [2], 5), (5, [1], 5)), [])

    def test_composition_beyond_old_hypotheses(self):
        """Un effet qu'aucune ancienne hypothèse ne décrivait : retirer la somme de deux arguments.

        Les trois écritures de même taille disent la même chose : elles coexistent."""
        found = discover((10, [1, 2], 7), (7, [2, 2], 3), (3, [0, 1], 2))
        self.assertIn(effets.Hypothese(effets.APRES, effets.moins(AVANT, effets.plus(A0, A1))), found)
        self.assertEqual(len(found), 3)


class EffectSourceTest(unittest.TestCase):
    """Ce que la mère a vérifié est exactement ce que le fils exécute."""

    def test_translation_matches_evaluation(self):
        cas = [effets.Cas(["0", "X", "2", "O"], (2, 1), ["0", "X", "X", "O"]),
               effets.Cas(["a", "b", "c", "d"], ("b", 3), ["a", "Y", "c", "d"]),
               effets.Cas(10, (3, 2), 7)]
        nb = 0
        portees = {2: [2, 0], 3: [3], "b": [1, 2]}
        for terme, _ in effets.termes(cas, 2, constants=(1, " ", "X"), portees=portees):
            expression = effets.traduire(terme)
            for c in cas:
                attendu = effets.evaluer(terme, c, None, portees)
                if attendu is effets.INDEFINI:
                    continue
                obtenu = eval(expression, {"avant": c.valeur_avant, "args": c.arguments, "PORTEES": portees})
                self.assertEqual(obtenu, attendu, f"{terme!r} sur {c}")
                nb += 1
        self.assertGreater(nb, 50)

    def test_apres_from_a_quantity(self):
        """Aux Allumettes, le apres écrit par la mère retire ce que dit l'argument."""
        module = son_writer.load(son_writer.apres_source(RETIRER) + "\nVUES = 0\n")
        self.assertEqual(module.apres(10, 3, "X"), 7)

    def test_son_apres_is_the_discovered_program(self):
        source = render_son("fils", education())
        self.assertIn("def changees(avant, args):", source)
        self.assertIn("return {args[0]}", source)
        self.assertNotIn("suite[action] = joueur", source)  # plus de gabarit
        son = son_writer.load(source)
        self.assertEqual(son.apres(["0", "1", "2"], 1, "X"), ["0", "X", "2"])


def example(module: str, game: str, size: int, players: str, moves: list[int]) -> str:
    """Un exemple de partie : chaque joueur lit le plateau puis joue ; le dernier coup finit la
    partie (le jeu renvoie alors un booléen, comme dans les exemples de ``res/``)."""
    turns = "".join(f"# player {p}\nboard = game.get_game_state()  # array {size}\n"
                    f"board = game.play({n})  # {'bool' if i == len(moves) - 1 else f'array {size}'}\n\n"
                    for i, (p, n) in enumerate(zip(players, moves)))
    return (f"# include\nfrom {module} import {game}\n\n# init\ngame = {game}()  # game\n"
            f"board = game.init({players[0]!r})  # array {size}\n\n# back\nboard = game.back()  # array {size}\n\n"
            + turns + f"# end player {players[0]}\n")


def example_cases(model) -> list:
    """Les coups de l'exemple, tels que l'Analyzer les a vus (sans rien du labo)."""
    return model.report.cases[model.action.name][model.getter.return_value.name]


def understood(text: str):
    parsed = ExampleParser().parse_text(text)
    return parsed, GameModel.from_analysis(parsed, analyse(parsed, replay(parsed)))


class EffectExperimentTest(unittest.TestCase):
    """La mère met à l'épreuve, dans son labo, ce qu'elle a compris de l'action."""

    def test_decisive_experiment(self):
        both = [CASE_INDICE, CASE_VALANT]
        self.assertFalse(effets.decisive(both, ["0", "1", "X"], (1,)))
        self.assertTrue(effets.decisive(both, ["0", "1", "X"], (2,)))  # la case 2 ne vaut plus 2
        self.assertEqual(effets.departager(both, effets.Cas(["0", "1", "2"], (1,), ["0", "1", "2"])), both)

    def test_morpion_hypotheses_are_indistinguishable(self):
        """Au Morpion, aucune expérience ne sépare « la case d'indice n » et « la case qui vaut n »."""
        trials = education().trials
        self.assertEqual(trials.survivors, [CASE_INDICE, CASE_VALANT])
        self.assertEqual(trials.refutations, {})
        self.assertGreater(trials.played, 10)

    def test_experiment_separates_hypotheses(self):
        """Pions « 1 » et « 2 » : jouer la case 2 quand un « 2 » est posé ne change qu'une case.
        L'exploration le montre déjà ; une expérience du labo le montre aussi, à partir des seuls
        coups de l'exemple."""
        parsed, model = understood(example("tests.jeu_chiffres", "MorpionChiffres", 9, "12121", [2, 0, 4, 3, 6]))
        self.assertEqual([op.programme for op in model.report.operations["game.play"]], [CASE_INDICE, CASE_VALANT])
        teaching = Education(parsed, model, None)
        self.assertEqual(teaching.trials.survivors, [CASE_INDICE])
        positions, _ = teaching.explore()
        trials = teaching.test_effects([CASE_INDICE, CASE_VALANT], example_cases(model), positions)
        self.assertEqual(trials.survivors, [CASE_INDICE])
        self.assertEqual(list(trials.refutations), [CASE_VALANT])

    def test_experiment_refutes_a_coincidence(self):
        """Puissance 4 joué sur la rangée du bas : l'indice de la case vaut la colonne. L'exemple
        seul fait croire à case(arg0) ; ce que la mère voit en explorant l'écarte d'emblée. Et si
        elle n'avait que l'exemple, le labo le réfuterait et elle apprendrait du contre-exemple."""
        parsed, model = understood(example("Games.Puissance4", "Puissance4", 42, "XOXOXOX", [0, 4, 1, 5, 2, 6, 3]))
        self.assertEqual([op.programme for op in model.report.operations["game.play"]], [CASE_INDICE])
        teaching = Education(parsed, model, None)
        self.assertEqual(teaching.trials.survivors, [GRAVITE])
        positions, _ = teaching.explore()
        trials = teaching.test_effects([CASE_INDICE], example_cases(model), positions)
        self.assertEqual(list(trials.refutations), [CASE_INDICE])
        self.assertEqual(trials.survivors, [GRAVITE])
        self.assertTrue(1 <= trials.retries <= REPRISES)  # elle a dû revoir ses portées en chemin

    def test_reach_is_deduced_from_what_she_saw(self):
        """L'ordre d'une portée vient des positions : une action n'a rempli la case du haut que
        lorsque celle du bas n'était plus vide. Aucune expérience « rejouer depuis le début »."""
        vide = [" "] * 6
        vus = [effets.Cas(vide, (0,), ["X"] + vide[1:]),
               effets.Cas(["X", " ", "O", " ", " ", " "], (0,), ["X", " ", "O", " ", "X", " "]),
               effets.Cas(["X"] + vide[1:], (0,), ["X", " ", "O", " ", " ", " "]),
               effets.Cas(vide, (1,), [" ", "O", " ", " ", " ", " "])]
        self.assertEqual(effets.portees_observees(vus), {0: [0, 2, 4], 1: [1]})
        boucle = [effets.Cas([" ", " "], (0,), ["X", " "]), effets.Cas([" ", " "], (0,), [" ", "X"])]
        self.assertEqual(effets.portees_observees(boucle), {})  # aucun ordre : pas une suite

    def test_written_value(self):
        """La valeur écrite : propre à chaque joueur (le pion), un argument, ou une constante."""
        def vu(apres, args=(0,)):
            return effets.Cas([" ", " "], args, apres)
        self.assertEqual(effets.ecriture([(vu(["X", " "]), 0), (vu([" ", "O"], (1,)), 1),
                                          (vu(["X", " "]), 0)]), ("joueur",))
        self.assertEqual(effets.ecriture([(vu([7, " "], (0, 7)), 0), (vu([" ", 3], (1, 3)), 1)]), ("argument", 1))
        self.assertEqual(effets.ecriture([(vu(["#", " "]), 0), (vu([" ", "#"], (1,)), 1)]), ("constante", "#"))
        self.assertIsNone(effets.ecriture([(vu(["X", " "]), 0), (vu([" ", "O"], (1,)), 0)]))
        self.assertEqual(education().knowledge["written"], ("joueur",))

    def test_free_cell_is_deduced_from_refusals(self):
        """Quand une case peut être jouée : déduit des coups joués et des coups refusés,
        pas de « une case sans pion »."""
        depart = ["0", "1", "2"]
        joue = effets.Cas(["0", "1", "2"], (1,), ["0", "X", "2"])
        joue_aussi = effets.Cas(["0", "X", "2"], (0,), ["O", "X", "2"])
        refuse = effets.Cas(["0", "X", "2"], (1,), ["0", "X", "2"])  # la case 1 est prise
        self.assertEqual(effets.liberte(CASE_INDICE, [joue, joue_aussi, refuse], depart), ("depart",))
        self.assertEqual(effets.liberte(CASE_INDICE, [joue], depart), ("toujours",))  # rien de refusé
        vide = effets.Cas([" ", " "], (0,), ["X", " "])
        pris = effets.Cas(["X", " "], (0,), ["X", " "])
        self.assertEqual(effets.liberte(CASE_INDICE, [vide, pris], [" ", " "]), ("constante", " "))
        tricheur = effets.Cas(["0", "1", "2"], (1,), ["0", "1", "2"])  # refusé alors que tout est libre
        self.assertIsNone(effets.liberte(CASE_INDICE, [joue, tricheur], depart))
        self.assertEqual(education().knowledge["free"], ("depart",))
        parsed, model = understood(example("tests.jeu_chiffres", "MorpionChiffres", 9, "12121", [2, 0, 4, 3, 6]))
        self.assertEqual(Education(parsed, model, None).knowledge["free"], ("depart",))

    def test_players_must_alternate(self):
        """La parité du coup dit qui joue parce que l'exemple montre deux joueurs qui alternent."""
        parsed, model = understood(example("Games.Puissance4", "Puissance4", 42, "XXOXO", [0, 0, 1, 1, 2]))
        with self.assertRaisesRegex(LabError, "chacun leur tour"):
            Education(parsed, model, None)

    def test_gravity_upwards(self):
        """Les jetons montent : la file part de c + 35 et descend de 7. La mère n'a rien à
        calculer : elle voit l'ordre en rejouant l'action, et le même programme convient."""
        parsed, model = understood(example("tests.jeu_inverse", "Puissance4Inverse", 42, "XOXOXOX",
                                           [3, 3, 2, 2, 4, 4, 1]))
        teaching = Education(parsed, model, None)
        self.assertEqual(teaching.trials.survivors, [GRAVITE])
        self.assertEqual(teaching.knowledge["reach"][3], [38, 31, 24, 17, 10, 3])
        self.assertEqual(teaching.mind.case_jouee([" "] * 38 + ["X"] + [" "] * 3, 3), 31)

    def test_actions_are_explored(self):
        """La mère ne suppose pas que les actions sont des indices : à partir des valeurs de
        l'exemple, elle essaie autour (« si 7 marche, et 8 ? ») et s'arrête après deux refus."""
        morpion = Mother().raise_son(RES / "exampleMorpion.py", None, 0)  # l'exemple joue 4, 5, 1, 2, 7
        self.assertEqual(morpion.knowledge["actions"], list(range(9)))
        puissance4 = Mother().raise_son(RES / "examplePuissance4.py", None, 0)  # 3, 2, 4, 1
        self.assertEqual(puissance4.knowledge["actions"], list(range(7)))

    def test_unknown_action_is_an_error(self):
        """Une action qui mélange l'état : rien ne l'explique, même avec le labo ; la mère le dit.
        (Jumper est maintenant décrit par un défilement : voir tests/test_un_joueur.py.)"""
        turns = "".join("# player seul\nboard = game.get_game_state()  # array 8\n"
                        f"board = game.play({k})  # array 8\n\n" for k in (1, 2, 1, 2, 1))
        text = ("# include\nfrom tests.jeu_melange import Melange\n\n# init\ngame = Melange()  # game\n"
                "board = game.init()  # array 8\n\n# back\nboard = game.back()  # array 8\n\n" + turns)
        parsed, model = understood(text)
        self.assertEqual(model.report.operations["game.play"], [])
        from xander.un_joueur import Solo
        with self.assertRaises(LabError):
            Solo(parsed, model)


class MotherTest(unittest.TestCase):
    def test_learn_morpion(self):
        model = Mother().learn(RES / "exampleMorpion.py")
        self.assertEqual(model.nb_players, 2)
        self.assertEqual(model.turn_pattern, ["get_game_state", "play"])
        operations = model.report.operations["game.play"]
        self.assertEqual([(op.programme, op.variable.name) for op in operations],
                         [(CASE_INDICE, "board"), (CASE_VALANT, "board")])
        self.assertEqual([f.time for f in model.report.unknown_calls], [11])  # le coup final renvoie True
        board = next(v for v in model.env if v.name == "board")
        self.assertEqual({f.short_name for f in board.setters}, {"play"})

    def test_learn_allumettes(self):
        model = Mother().learn(RES / "exampleAllumettes.py")
        operations = model.report.operations["game.play"]
        self.assertEqual([op.programme for op in operations], [RETIRER])

    def test_learn_puissance4(self):
        """La gravité : play(3) remplit 3, puis 10, 17… L'Analyzer seul ne l'explique pas : il
        faut rejouer les actions. La mère voit alors ce que chacune remplit (la colonne, de bas en
        haut) et construit « la première case vide de ce que l'action remplit »."""
        model = Mother().learn(RES / "examplePuissance4.py")
        self.assertEqual(model.report.operations["game.play"], [])
        teaching = Mother().raise_son(RES / "examplePuissance4.py", None, 0)
        self.assertEqual(teaching.trials.survivors, [GRAVITE])
        self.assertEqual(teaching.knowledge["reach"][3], [3, 10, 17, 24, 31, 38])
        self.assertEqual(model.nb_players, 2)
        self.assertEqual(model.turn_pattern, ["get_game_state", "play"])
        self.assertEqual(model.winner, "X")

    def test_learn_pylos_actions(self):
        """Pylos : trois sortes d'actions, que la mère décrit seule. Poser et
        reprendre changent une case, monter en change deux. Le tour, lui, n'est
        pas encore compris (il compte une, deux ou trois actions)."""
        model = Mother().learn(RES / "examplePylos.py")
        programmes = {name: [op.programme for op in ops] for name, ops in model.report.operations.items()}
        une_case = effets.Hypothese(effets.CHANGEES, effets.case(A0))
        self.assertEqual(programmes["game.play"], [une_case])
        self.assertEqual(programmes["game.take"], [une_case])
        self.assertEqual(programmes["game.move"],
                         [effets.Hypothese(effets.CHANGEES, effets.union(effets.case(A0), effets.case(A1)))])
        self.assertEqual(model.winner, "X")

    def test_learn_jumper_single_player(self):
        model = Mother().learn(RES / "exampleJumper.py")
        self.assertEqual(model.nb_players, 1)
        self.assertEqual(model.nb_actions_per_turn, 2)

    def test_none_call_stays_in_turn(self):
        from xander.game_model import split_turns
        get, play, show = "b = game.get()  # array 3", "b = game.play(1)  # array 3", "game.print()"
        for order in ([get, play, show], [show, get, play], [get, show, play]):
            with self.subTest([line.split("(")[0] for line in order]):
                parsed = ExampleParser().parse_text("# player A\n" + "\n".join(order * 3) + "\n")
                expected = [[line.split("(")[0].split(".")[-1] for line in order]] * 3
                self.assertEqual([[f.short_name for f in turn] for turn in split_turns(parsed)], expected)

    def test_first_turn_can_differ(self):
        from xander.game_model import split_turns
        lines = ["s = game.score()  # integer", "b = game.play(1)  # array 3"]
        lines += ["b = game.get()  # array 3", "b = game.play(1)  # array 3"] * 3
        parsed = ExampleParser().parse_text("# player A\n" + "\n".join(lines) + "\n")
        self.assertEqual([[f.short_name for f in turn] for turn in split_turns(parsed)],
                         [["score", "play"]] + [["get", "play"]] * 3)

    def test_turns_on_examples(self):
        for name, nb_turns in (("exampleMorpion.py", 5), ("exampleAllumettes.py", 5), ("examplePuissance4.py", 11),
                                ("exampleJumper.py", 73)):
            with self.subTest(name):
                from xander.game_model import split_turns
                turns = split_turns(parse_example(RES / name))
                self.assertEqual(len(turns), nb_turns)
                self.assertTrue(all(len(turn) == 2 for turn in turns))

    def test_create_son(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Mother().create_son("fils", RES / "exampleMorpion.py", directory)  # sans professeur
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("xander", source.split('"""', 2)[2])  # fichier autonome
            self.assertNotIn("def concept_", source)  # né sans règle : rien d'autre que la perception
            son = son_writer.load(source)
            self.assertEqual(son.MOTIFS, [[1, 4, 7]])  # leçon de l'exemple
            self.assertEqual(son.REGLES, [])
            game = NoBackMorpion()
            game.init("X")
            self.assertIsInstance(son.play(game), list)
            self.assertEqual(game.board[0], "X")  # sans règle : première case libre


class RefusingMorpion(Morpion):
    """Un Morpion qui refuse tous les coups, et compte combien on en essaie."""

    calls = 0

    def play(self, *arguments):
        self.calls += 1
        return False


class NoBackMorpion(Morpion):
    """Un Morpion qui interdit ``back`` : le fils ne doit jamais s'en servir."""

    def back(self):
        raise AssertionError("le fils a utilisé back")


def education(nb_games: int = 0) -> Education:
    if nb_games:
        return trained(nb_games)
    return Mother().raise_son(RES / "exampleMorpion.py", minmax_morpion_play, nb_games)


def puissance4() -> Education:
    """Une éducation au Puissance 4 qui n'a vu que l'exemple."""
    return Mother().raise_son(RES / "examplePuissance4.py", minmax_puissance4_play, 0)


@functools.lru_cache(maxsize=None)
def trained(nb_games: int) -> Education:
    """Une éducation complète, partagée par les tests qui ne font que la regarder."""
    return Mother().raise_son(RES / "exampleMorpion.py", minmax_morpion_play, nb_games)


#: Ce que la mère doit retrouver seule (écrit ici pour comparer, jamais donné à la mère).
GAGNER = concepts.brique(concepts.GAGNE, MOI)
PARER = concepts.non(concepts.au_moins(1, LUI, concepts.brique(concepts.GAGNE, LUI)))
# « il n'a pas de menace » : le même concept, reconnu au lieu d'imaginer chacun de ses coups
PARER_VU = concepts.non(concepts.brique("menace", LUI))


def possible_defeats(son) -> tuple[list[list[int]], int]:
    """Toutes les suites de coups adverses qui battent le fils (il joue X puis O),
    et le plus grand nombre de positions qu'il a regardées pour un coup."""
    defeats, views = [], [0]

    def explore(board, turn, me, path):
        result = winner_of(board)
        if result:
            if result not in ("D", me):
                defeats.append(path)
            return
        if turn == me:
            cells = [son.choisir(list(board), me)[0]]
            views[0] = max(views[0], son.VUES)
        else:
            cells = [c for c in range(9) if is_free(board[c])]
        for cell in cells:
            child = list(board)
            child[cell] = turn
            explore(child, "O" if turn == "X" else "X", me, path + [cell])

    empty = [str(i) for i in range(9)]
    explore(empty, "X", "X", [])
    explore(empty, "X", "O", [])
    return defeats, views[0]


#: Budget de réflexion : positions regardées au plus par le fils pour un coup.
#: Un minimax complet du Morpion en regarde plus de 500 000 au premier coup.
BUDGET = 1000


class LabTest(unittest.TestCase):
    def setUp(self):
        parsed, model = Mother().understand(RES / "exampleMorpion.py")
        self.lab = Lab(parsed, model)

    def test_goto_and_undo(self):
        self.assertTrue(self.lab.goto([(4,), (0,), (8,)]))
        self.assertEqual(self.lab.state[8], "X")
        self.assertTrue(self.lab.goto([(4,), (2,)]))  # revient en arrière puis rejoue
        self.assertEqual(self.lab.state[:5], ["0", "1", "O", "3", "X"])
        self.assertEqual(self.lab.play(2), "refused")  # case prise : rien n'est noté
        self.assertEqual(len(self.lab.moves), 2)

    def test_end_and_teacher(self):
        self.assertTrue(self.lab.goto([(0,), (3,), (1,), (4,), (2,)]))
        self.assertTrue(self.lab.ended)
        self.lab.goto([(0,), (3,), (1,), (4,)])
        self.assertEqual(self.lab.ask(minmax_morpion_play), (2,))  # le professeur gagne
        self.assertTrue(self.lab.ended)


class EducationTest(unittest.TestCase):
    def test_first_lesson_understands_the_example(self):
        teaching = education()
        self.assertEqual(teaching.knowledge["marks"], ["X", "O"])
        self.assertEqual(teaching.knowledge["patterns"], [[1, 4, 7]])  # par contre-épreuve
        self.assertEqual(teaching.records[0].patterns, [[1, 4, 7]])

    def test_draw_is_not_a_win(self):
        teaching = education()
        draw = [(0,), (1,), (2,), (4,), (3,), (5,), (7,), (6,), (8,)]
        teaching.lab.goto(draw)
        self.assertIsNone(teaching.winner())

    def test_error_becomes_a_memory(self):
        teaching = education()
        teaching.knowledge["patterns"].append([0, 1, 2])
        state = ["X", "X", "2", "3", "O", "5", "6", "7", "8"]  # O doit parer en 2
        lesson = teaching.correct(state, "O", 3, "défaut", 2)
        self.assertEqual(lesson.explanation, "souvenir")  # d'abord le cas, sans généraliser
        self.assertEqual(teaching.knowledge["memories"], {"AA..M....": 2})
        self.assertEqual(teaching.knowledge["rules"], [])
        self.assertIn("AA..M....", teaching.cases)

    def blocking_lessons(self, teaching, positions):
        teaching.knowledge["patterns"] = [list(line) for line in LINES]
        teaching.rethink()
        for moves, block in positions:
            teaching.lab.goto(moves)
            teaching.correct(list(teaching.lab.states[-1]), "O", 0, "défaut", block, moves)

    def test_refactor_finds_parer(self):
        """Deux souvenirs où il fallait parer deviennent une règle que la mère a construite."""
        teaching = education()
        self.blocking_lessons(teaching, [([(7,), (4,), (8,)], 6), ([(2,), (4,), (5,)], 8)])
        self.assertEqual(len(teaching.knowledge["memories"]), 2)
        done = teaching.refactor()
        self.assertEqual(len(done), 1, done)
        self.assertEqual(teaching.knowledge["memories"], {})  # les deux cas sont couverts
        rule = teaching.knowledge["concepts"][teaching.knowledge["rules"][0]]
        self.assertIn(rule, (PARER, PARER_VU))  # « aucun de ses coups ne le fait gagner »

    def test_one_case_is_not_enough(self):
        """Un seul cas peut être une coïncidence : pas de refactor."""
        teaching = education()
        self.blocking_lessons(teaching, [([(7,), (4,), (8,)], 6)])
        self.assertEqual(teaching.refactor(), [])
        self.assertEqual(teaching.knowledge["rules"], [])

    def test_unexplained_move_becomes_a_memory(self):
        teaching = education()
        teaching.knowledge["patterns"] = []  # aucun motif connu : rien n'explique le coup
        lesson = teaching.correct(list(teaching.lab.states[0]), "X", 0, "défaut", 4)  # plateau vide
        self.assertEqual(lesson.explanation, "souvenir")
        self.assertEqual(teaching.knowledge["memories"], {".........": 4})

    def test_mother_rediscovers_gagner_and_parer(self):
        """Partie de zéro, la mère retrouve seule « gagner », et ses règles savent parer.

        La forme de ses concepts lui appartient (elle a pu fondre « gagner ou
        parer » en un seul) : on compare leurs coups avec le vocabulaire écrit à
        la main, qui ne sert ici que de référence.
        """
        teaching = education(200)
        definitions, rules = teaching.knowledge["concepts"], teaching.knowledge["rules"]
        self.assertIn(GAGNER, [definitions[name] for name in rules])
        mind = think(teaching.mind.possibles, teaching.mind.apres, teaching.mind.gagne,
                          teaching.mind.suivant)
        parried, covering = 0, teaching.covering()
        for case in teaching.cases.values():
            if covering[case.key] is not None:
                continue  # ici c'est un souvenir qui décide (exact, symétrique ou petit motif), pas une règle
            threat = mind["parer"](case.state, case.me)
            if threat and not mind["gagner"](case.state, case.me):
                self.assertIn(teaching.decide(case.state, case.me, rules), threat, case.key)
                parried += 1
        self.assertGreater(parried, 10)

    def test_shifted_patterns(self):
        """Un motif décalé est essayé dans le labo : la mère ne sait pas que le plateau est
        un carré, c'est le jeu qui dit si le décalage est encore un alignement."""
        teaching = education()
        teaching.knowledge["patterns"] = [[0, 1, 2], [0, 3, 6]]
        done = teaching.shift_patterns()
        rows_and_columns = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8]]
        self.assertEqual(sorted(teaching.knowledge["patterns"]), sorted(rows_and_columns))
        self.assertIn((1, 2, 3), teaching._shifts_tried)  # essayé, mais déborde sur la rangée suivante
        self.assertEqual(len(done), 4)

    def test_symmetry_candidates(self):
        """Les renumérotations qui préservent les 8 alignements : 4 rotations et 4 miroirs."""
        found = symmetries.candidates(9, [list(line) for line in LINES])
        self.assertEqual(len(found), 8)
        self.assertIn([6, 3, 0, 7, 4, 1, 8, 5, 2], found)  # un quart de tour
        self.assertEqual(len(symmetries.candidates(9, [[1, 4, 7]])), 4320)  # un seul motif : trop peu

    def test_lab_rejects_false_symmetries(self):
        """Avec un seul motif compris, des milliers de renumérotations le préservent ; le labo
        ne garde que celles qui ne changent vraiment rien au jeu."""
        teaching = education()  # la mère ne connaît que [1, 4, 7]
        teaching.discover_symmetries()
        true = [s for s in symmetries.candidates(9, [list(line) for line in LINES]) if s != list(range(9))]
        self.assertEqual(sorted(teaching.knowledge["symmetries"]),
                         sorted(s for s in true if sorted(s[c] for c in (1, 4, 7)) == [1, 4, 7]))
        self.assertEqual(len(teaching.knowledge["symmetries"]), 3)  # deux miroirs et le demi-tour

    def test_explanation_of_a_case(self):
        """« Pourquoi le coup du professeur valait-il mieux ? » L'explication d'un cas : des
        concepts vrais après son coup et faux après celui du fils (les deux positions suffisent :
        ce sont ceux qui feraient choisir son coup et écarter celui du fils), les plus petits d'abord. Avec
        une marge de 0, seulement ceux de la plus petite taille ; une marge plus grande les
        allonge sans rien perdre (la mère reprend où elle s'était arrêtée). Un coup bien joué n'a
        rien à expliquer."""
        teaching = trained(200)
        errors = [c for c in teaching.cases.values() if c.son_cell != c.teacher_cell]
        pensee = teaching.pensee
        teaching._explanations = {}
        try:
            explained = 0
            for case in errors[:20]:
                short = teaching.explanation(case, 0)
                self.assertLessEqual(len({c.size for c in short}), 1)  # une seule taille
                longer = teaching.explanation(case, 1)
                self.assertEqual(longer[:len(short)], short)          # rien de perdu
                everything = teaching.explanation(case)
                self.assertEqual(everything[:len(longer)], longer)
                for concept in everything:
                    cells = pensee.choix(concept, case.state, case.me)
                    self.assertIn(case.teacher_cell, cells)
                    self.assertNotIn(case.son_cell, cells)
                # comparer les deux positions revient à regarder ce que la règle choisirait
                expected = [c for c in teaching.bank
                            if case.teacher_cell in pensee.choix(c, case.state, case.me)
                            and case.son_cell not in pensee.choix(c, case.state, case.me)
                            and not concepts.contre_son_but(c, teaching.knowledge["concepts"], teaching.n)]
                if expected:
                    self.assertEqual(everything, expected)
                explained += bool(short)
            self.assertGreater(explained, 0)
            good = next(c for c in teaching.cases.values() if c.son_cell == c.teacher_cell)
            self.assertEqual(teaching.explanation(good), [])
        finally:
            teaching._explanations = {}

    def test_hypothesis_checked_at_every_rank_at_once(self):
        """Pour vérifier une hypothèse, la mère juge tous ses rangs en un seul tour des cas, et ne
        rejoue les règles que là où elle écarte des coups (:meth:`Education.check_ranks`) : pendant
        tout un apprentissage, les mêmes rangs adoptables (assez de souvenirs libérés) que rejouer
        tous les cas avec toutes les règles, rang par rang (:meth:`Education.check`)."""
        original, seen = Education.check_ranks, []

        def compared(self, rules, block, covering):
            got = original(self, rules, block, covering)
            names = {c.id: name for name, c in self.knowledge["concepts"].items()}
            others, chosen = [names[c.id] for c in rules], [names[c.id] for c in block]
            expected = {}
            for rank in range(len(others) + 1):
                freed = self.check(others[:rank] + chosen + others[rank:], covering)
                if freed is not None and len(freed) >= effets.MIN_CAS:  # sinon trop peu pour une règle
                    expected[rank] = freed
            seen.append(bool(expected))
            assert got == expected, (block, got, expected)
            return got

        Education.check_ranks = compared
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                Mother().raise_son(RES / "exampleNim.py", minmax_nim_play, 60)
        finally:
            Education.check_ranks = original
        self.assertTrue(any(seen))  # des hypothèses adoptables à certains rangs
        self.assertGreater(len(seen), 20)

    def test_or_rule_is_split_most_immediate_first(self):
        """« gagner ou parer » se lit non(et(non gagne(moi), il a un coup gagnant)) : ses parties,
        la plus immédiate d'abord (gagner : aucun coup plus loin ; parer : un coup plus loin)."""
        gagner = concepts.brique(concepts.GAGNE, MOI)
        menace = concepts.au_moins(1, LUI, concepts.brique(concepts.GAGNE, LUI))
        ou = concepts.non(concepts.et(concepts.non(gagner), menace))
        self.assertEqual(concepts.parties_ou(ou), [gagner, concepts.non(menace)])
        self.assertEqual(concepts.parties_ou(menace), [menace])  # pas un « ou » : une seule partie

    def test_redundant_memory_is_forgotten(self):
        """Un souvenir qui joue ce que les règles joueraient de toute façon est oublié ; celui sans
        lequel un cas serait mal joué est gardé."""
        teaching = trained(200)
        memories, rules = teaching.knowledge["memories"], teaching.knowledge["rules"]
        avant = dict(memories)
        covering = teaching.covering()
        case = next(c for c in teaching.cases.values() if covering[c.key] is None
                    and teaching.good(c, teaching.decide(c.state, c.me, rules)))
        memories[case.key] = teaching.decide(case.state, case.me, rules)  # redondant
        teaching.rewrite()
        try:
            done = teaching.forget()
            self.assertNotIn(case.key, memories)
            self.assertTrue(any(case.key in d for d in done), done)
            son = teaching.son  # …et chaque cas reste bien joué sans ce qui a été oublié
            self.assertTrue(all(teaching.good(c, son.choisir(list(c.state), c.me)[0])
                                for c in teaching.cases.values()))
        finally:
            memories.clear()
            memories.update(avant)
            teaching.rewrite()

    def test_victoire_par_defaut_mise_a_part(self):
        """Une victoire où plus de la moitié des coups du fils sont des coups par défaut est
        comptée à part, et ces coups par défaut ne deviennent pas des cas « bien joués »."""
        from xander import education as module
        defaut = [([], [], 0, "défaut")] * 3 + [([], [], 0, "concept_1")] * 2
        moitie = [([], [], 0, "défaut")] * 2 + [([], [], 0, "concept_1")] * 2
        self.assertEqual(module.resultat(1, defaut), module.PAR_DEFAUT)
        self.assertEqual(module.resultat(1, moitie), "victoire")  # la moitié : pas plus
        self.assertEqual(module.resultat(-1, defaut), "défaite")
        teaching = trained(0)
        teaching.lab.goto([])
        state, me = teaching.position(), teaching.marks[0]
        cell = min(teaching.mind.possibles(list(state)))
        decisions = [([], list(state), cell, "défaut")]
        avant = dict(teaching.cases)
        try:
            teaching.cases.clear()
            self.assertEqual(teaching.review(decisions, 0, untrusted={()}), [])  # pas une erreur…
            self.assertEqual(teaching.cases, {})  # …mais pas un cas bien joué non plus
            teaching.cases.clear()
            self.assertEqual(teaching.review(decisions, 0), [])
            self.assertEqual(len(teaching.cases), 1)  # sans la garde, c'est un cas bien joué
        finally:
            teaching.cases.clear()
            teaching.cases.update(avant)
        score = teaching.evaluate(nb_random=2)
        self.assertEqual(set(score["hasard"]), {"victoire", module.PAR_DEFAUT, "nul", "défaite"})

    def test_views_counted_without_compiling(self):
        """La mère compte les positions que regarderait le fils avec sa pensée, sans écrire ni
        compiler un fils d'essai : le même nombre que le fils compilé, pour tous les ordres d'au
        plus deux règles et pour quelques ordres de toutes ses règles (tous les ordres de six règles,
        ce seraient près de deux mille fils à compiler)."""
        import itertools
        import random
        teaching = trained(200)
        rules = teaching.knowledge["rules"]
        orders = [list(order) for size in range(min(len(rules), 2) + 1)
                  for order in itertools.permutations(rules, size)]
        hasard = random.Random(3)
        orders += [list(rules), list(reversed(rules))] + [hasard.sample(rules, len(rules)) for _ in range(4)]
        for order in orders:
            self.assertEqual(teaching.views(order, []), teaching.views_compiled(order, []), order)
        some = list(teaching.knowledge["memories"])[:2]
        self.assertEqual(teaching.views(rules, some), teaching.views_compiled(rules, some))

    def test_working_memory_is_only_a_cache(self):
        """La mémoire de travail de la mère, même minuscule (vidée sans cesse), ne change aucun
        concept trouvé : elle recalcule ce qu'elle a oublié."""
        teaching = trained(200)
        positions = teaching._bank_positions
        def bank():
            pensee = concepts.Pensee(teaching.mind, teaching.knowledge["concepts"])
            return [c.id for c in concepts.enumerer(pensee, positions[:40], 4, 2)]
        normal = bank()
        old, concepts.MEMOIRE_MAX = concepts.MEMOIRE_MAX, 50
        try:
            self.assertEqual(bank(), normal)
        finally:
            concepts.MEMOIRE_MAX = old

    def test_bank_kept_from_one_search_to_the_next(self):
        """Ce que la mère sait d'un concept, gardé d'une recherche à l'autre, ne change aucun
        concept trouvé : avec une brique de plus, ou un nom qui change de sens, elle trouve les
        mêmes concepts qu'en repartant de rien."""
        teaching = trained(200)
        positions = teaching._bank_positions[:40]
        definitions = dict(teaching.knowledge["concepts"])
        def bank(memoire=None):
            pensee = concepts.Pensee(teaching.mind, definitions)
            return [c.id for c in concepts.enumerer(pensee, positions, 4, 2, budget=200, memoire=memoire)]
        memoire: dict = {}
        self.assertEqual(bank(memoire), bank())
        self.assertEqual(bank(memoire), bank())  # tout vient de la mémoire
        premier = concepts.enumerer(concepts.Pensee(teaching.mind, definitions), positions, 3, 1)
        definitions["nouveau"] = premier[-1]
        self.assertEqual(bank(memoire), bank())
        definitions["nouveau"] = premier[-2]  # le même nom pour autre chose
        self.assertEqual(bank(memoire), bank())

    def test_bank_within_budget_at_worst(self):
        """« Au pire, pas en moyenne » : sur les positions de la mère, aucune règle de sa banque ne
        ferait regarder au fils plus que son budget (ses coups, puis le concept après chacun) ;
        et ce qu'elle compte par concept majore ce qu'il regarde vraiment."""
        teaching = trained(200)
        positions = teaching._bank_positions[:40]
        pensee = concepts.Pensee(teaching.mind, teaching.knowledge["concepts"])
        budget = 60
        banque = concepts.enumerer(pensee, positions, 5, 2, budget=budget)
        coups = sum(len(pensee.enfants(e, m)) for e, m in positions) / len(positions)
        self.assertLess(len(banque), len(concepts.enumerer(pensee, positions, 5, 2)))
        for c in banque:
            pire = max(pensee.regard(c, e, m) for e, m in positions)
            self.assertLessEqual(coups * (1 + pire), budget, c)
            for e, m in positions[:5]:
                vues: set = set()
                pensee.regardees(c, e, m, vues, set())
                self.assertLessEqual(len(vues), pensee.regard(c, e, m), c)

    def test_memory_holds_for_rotated_position(self):
        """Un souvenir vaut pour la position tournée d'un quart de tour."""
        teaching = education()
        teaching.knowledge["symmetries"] = [[6, 3, 0, 7, 4, 1, 8, 5, 2]]
        teaching.knowledge["memories"] = {"M........": 4}  # coin en haut à gauche -> centre
        teaching.rewrite()
        rotated = ["0", "1", "X", "3", "4", "5", "6", "7", "8"]  # le même coin, tourné
        self.assertEqual(teaching.son.choisir(rotated, "X"), (4, "souvenir"))
        corner = ["0", "1", "2", "3", "4", "5", "6", "7", "X"]  # le coin opposé : pas cette symétrie
        self.assertNotEqual(teaching.son.choisir(corner, "X")[1], "souvenir")

    def test_recheck_case_against_symmetric_memory(self):
        """« Les souvenirs sont les tests » : un souvenir d'une position équivalente qui fait mal
        jouer un cas enregistré est démenti pour ce cas, qui devient son propre souvenir."""
        teaching = education()
        quarter = [6, 3, 0, 7, 4, 1, 8, 5, 2]
        teaching.knowledge["symmetries"] = [quarter]
        moves = [(0,), (3,), (1,), (4,)]  # X gagne en 2 ; en 8, il laisse O gagner en 5
        teaching.lab.goto(moves)
        state = list(teaching.lab.states[-1])
        key = teaching.mind.cle(state, "X")
        image = "".join(teaching.mind.transformer(key, quarter))
        teaching.knowledge["memories"] = {image: quarter[8]}  # vu tourné : « jouer en 8 »
        teaching.rewrite()
        self.assertEqual(teaching.son.choisir(list(state), "X"), (8, "souvenir"))
        teaching.cases[key] = Case(moves, state, "X", key, 8, 2)
        done = teaching.recheck()
        self.assertEqual(len(done), 1)
        self.assertEqual(teaching.knowledge["memories"][key], 2)
        self.assertEqual(teaching.son.choisir(list(state), "X"), (2, "souvenir"))
        self.assertEqual(teaching.recheck(), [])  # rien d'autre à démentir

    def lesson_at(self, teaching, moves, son_cell, reason, teacher_cell):
        teaching.lab.goto(moves)
        state = list(teaching.lab.states[-1])
        return teaching.correct(state, teaching.marks[len(moves) % 2], son_cell, reason, teacher_cell, moves)

    def test_memory_becomes_small_pattern_anywhere(self):
        """« Qu'est-ce qui comptait ? » puis « et ailleurs ? » : seuls mes deux pions et la case
        libre comptaient ; le motif décalé d'une rangée marche encore, pas d'une case."""
        teaching = education()
        teaching.knowledge["patterns"] = [list(line) for line in LINES]
        teaching.rethink()
        self.lesson_at(teaching, [(0,), (3,), (1,), (4,)], 5, "défaut", 2)  # X gagne en 2
        self.assertEqual(teaching.knowledge["memories"], {"MM.AA....": 2})
        done = teaching.generalize()
        self.assertEqual(teaching.knowledge["memories"], {"MM.??????": 2, "???MM.???": 5, "??????MM.": 8})
        self.assertEqual(len(done), 3, done)  # réduit, puis décalé de +3 et +6 (+1 : rejeté)
        board = ["0", "O", "2", "X", "X", "5", "O", "7", "8"]  # mes deux pions au milieu
        self.assertEqual(teaching.son.choisir(board, "X"), (5, "souvenir"))

    def test_small_pattern_needs_control_group(self):
        """Un professeur qui joue la case 2 dans deux positions sur trois, motif ou pas,
        « confirme » MM.?????? -> 2 dans plus de la moitié des positions. Le groupe témoin (le
        motif cassé, autant de pions) montre qu'il la joue aussi souvent sans lui."""
        teaching = education()
        teaching.knowledge["patterns"] = [list(line) for line in LINES]
        teaching.rethink()
        self.assertTrue(teaching.holds("MM.??????", 2))
        self.assertFalse(teaching.holds("?????????", 2))  # aucune case en plus du coup

        def biased(moves):  # ne regarde que le nombre de pions
            teaching.lab.goto(moves)
            others = [a for a in teaching.mind.possibles(list(teaching.lab.states[-1])) if a != 2]
            return (2,) if len(moves) % 3 or not others else (others[0],)

        teaching.teacher_move = biased
        teaching.judge = lambda moves, state, action: True  # ses autres coups ne sont pas pires
        self.assertFalse(teaching.holds("MM.??????", 2))

    def test_false_small_pattern_is_forgotten(self):
        """Un petit motif démenti est oublié ; les cas qu'il couvrait redeviennent des souvenirs."""
        teaching = education()
        teaching.knowledge["patterns"] = [list(line) for line in LINES]
        teaching.rethink()
        self.lesson_at(teaching, [(4,), (0,), (8,), (1,)], 3, "défaut", 2)  # X doit parer en 2
        teaching.knowledge["memories"] = {"AA.??????": 2}  # trop général : X peut gagner ailleurs
        teaching.rewrite()
        lesson = self.lesson_at(teaching, [(7,), (0,), (8,), (1,)], 2, "souvenir", 6)  # X gagne en 6
        self.assertEqual(teaching.knowledge["memories"], {"AA..M...M": 2, "AA.....MM": 6})
        self.assertIn("petit motif AA.?????? faux oublié", lesson.change)
        # Une autre décision de la même partie venait du même petit motif : déjà oublié.
        lesson = self.lesson_at(teaching, [(7,), (0,), (6,), (1,)], 2, "souvenir", 8)
        self.assertEqual(lesson.change, "nouveau souvenir")
        self.assertEqual(teaching.knowledge["memories"]["AA....MM."], 8)

    def test_mother_discovers_symmetries(self):
        teaching = education(200)
        self.assertEqual(len(teaching.knowledge["symmetries"]), 7)  # + l'identité : 8 façons de voir

    def test_son_becomes_unbeatable(self):
        teaching = education(200)
        self.assertEqual(sorted(map(sorted, teaching.knowledge["patterns"])),
                         sorted(map(list, LINES)))  # les 8 alignements, découverts seuls
        defeats, views = possible_defeats(teaching.son)
        self.assertEqual(defeats, [])
        self.assertEqual(teaching.evaluate(20)["professeur"]["défaite"], 0)
        self.assertLessEqual(views, BUDGET)  # il reconnaît, il ne calcule pas tout
        self.assertLessEqual(teaching.max_views, BUDGET)

    def test_son_contains_only_what_he_learned(self):
        teaching = education(200)
        source = teaching.source()
        definitions, rules = teaching.knowledge["concepts"], teaching.knowledge["rules"]
        needed = concepts.dependances(rules, definitions)
        for name in definitions:
            self.assertEqual(f"def {name}(" in source, name in needed, name)
        for name in vocabulary.concept_names():  # rien du vocabulaire écrit à la main
            self.assertNotIn(f"def {name}(", source)
        self.assertNotIn("import", source.split("# --- Perception")[1])

    def test_son_code_agrees_with_mother(self):
        """Le code écrit pour le fils dit la même chose que les arbres de la mère."""
        teaching = education(200)
        son = teaching.son
        for name in teaching.knowledge["rules"]:
            rule = teaching.knowledge["concepts"][name]
            for case in list(teaching.cases.values())[:40]:
                expected = teaching.pensee.coups(rule, case.state, case.me)
                actual = {a for a in son.possibles(case.state)
                          if getattr(son, name)(son.apres(case.state, a, case.me), case.me)}
                self.assertEqual(actual, expected, (name, case.key))

    def test_learning_curve_drops(self):
        records = education(200).records[1:]
        first, last = records[:20], records[-20:]
        self.assertGreater(sum(len(r.lessons) for r in first), sum(len(r.lessons) for r in last))

    def test_impossible_move_is_understood(self):
        """Un coup refusé par le jeu est une erreur : la mère comprend pourquoi (sa perception
        se trompait), réécrit le fils, et il ne recommence pas."""
        teaching = education()
        teaching.knowledge["free"] = ("toujours",)  # perception fausse : toute case se joue
        teaching.rethink()
        teaching.play_game(minmax_morpion_play, 0)
        self.assertEqual(len(teaching.impossibles), 1)  # une case déjà prise
        self.assertEqual(teaching.knowledge["free"], ("depart",))  # compris grâce au refus
        teaching.play_game(minmax_morpion_play, 1)
        self.assertEqual(teaching.impossibles, [])

    def test_no_impossible_move_after_five_games(self):
        """Après ses 5 premières parties, un fils ne fait plus aucun coup impossible."""
        teaching = education(200)
        self.assertEqual([r.number for r in teaching.records if r.number > 5 and r.impossibles], [])

    def test_son_never_tries_another_action(self):
        """Si le jeu refuse son coup, le fils le dit : essayer d'autres actions jusqu'à ce
        que le jeu en accepte une, ce serait tricher."""
        son = son_writer.load(render_son("fils", education()))
        game = RefusingMorpion()
        game.init("X")
        with self.assertRaisesRegex(RuntimeError, "coup impossible"):
            son.play(game)
        self.assertEqual(game.calls, 1)

    def test_saved_son_plays_against_minmax_without_back(self):
        son = son_writer.load(render_son("fils", education(200)))  # le fichier écrit par la mère
        for start in "XO":
            game = NoBackMorpion()
            game.init(start)
            while not game.win:
                game.get_game_state()
                (son.play if game.get_turn() == "X" else minmax_morpion_play)(game)
            self.assertEqual(game.win, "D")


def think(possibles, apres, gagne, adversaire) -> dict:
    """Le vocabulaire de la mère, exécuté avec les quatre notions d'un autre jeu."""
    notions = {"possibles": possibles, "apres": apres, "gagne": gagne, "adversaire": adversaire}
    source = "\n\n".join([vocabulary.tools_source()] + [vocabulary.concept_source(name)
                                                         for name in vocabulary.concept_names()])
    exec(source, notions)
    return notions


class ConceptsGenerauxTest(unittest.TestCase):
    """Le vocabulaire de la mère vaut pour d'autres jeux (gravité, quantité, Puissance 4)."""

    def test_one_plays_to_win(self):
        """On joue pour gagner : une explication qui dit « je n'ai pas de menace » ou « il a une
        menace » est une coïncidence ; sous ses coups à lui (il choisit), on ne conclut rien ; une
        victoire ou des coups imaginés (Nim : mes coups y imaginent les siens) ne comptent pas."""
        b, non, au_moins, et = concepts.brique, concepts.non, concepts.au_moins, concepts.et
        moi, lui = concepts.MOI, concepts.LUI
        contre = lambda c, d={}: concepts.contre_son_but(c, d, 2)
        self.assertFalse(contre(non(b("menace", lui))))                      # parer
        self.assertFalse(contre(au_moins(1, moi, b("menace", moi))))         # je peux me créer une menace
        self.assertFalse(contre(au_moins(1, lui, b("menace", moi))))         # il choisit : rien à conclure
        self.assertFalse(contre(non(au_moins(1, moi, non(au_moins(1, moi, non(b("gagne", moi))))))))  # Nim
        self.assertTrue(contre(non(b("menace", moi))))                       # je n'ai pas de menace
        self.assertTrue(contre(b("double_menace", lui)))                     # il a une double menace
        self.assertTrue(contre(et(non(b("menace", lui)), non(au_moins(1, moi, b("menace", moi))))))
        d = {"concept_1": non(b("menace", lui))}
        self.assertTrue(contre(b("concept_1", lui), d))                      # pour le suivant : je n'en ai pas

    def test_rules_filter_one_after_another(self):
        """Une règle propose, elle ne tranche pas seule : la suivante choisit parmi les coups
        qu'elle laisse (ici A garde 0 et 1, B garde 1 et 2 : il reste 1, pas le plus petit de A)."""
        from types import SimpleNamespace
        notions = SimpleNamespace(
            possibles=lambda etat: [i for i in range(4) if etat[i] == "."],
            apres=lambda etat, a, joueur: tuple("X" if i == a else v for i, v in enumerate(etat)),
            gagne=lambda etat, joueur: any(etat[i] == "X" for i in ((0, 1) if joueur == "X" else (1, 2))),
            suivant=lambda joueur: "O" if joueur == "X" else "X")
        pensee = concepts.Pensee(notions)
        a, b = concepts.brique("gagne", concepts.MOI), concepts.brique("gagne", concepts.LUI)
        self.assertEqual(pensee.decision([a, b], tuple("...."), "X"), ({1}, 1))
        self.assertEqual(pensee.decision([a], tuple("...."), "X"), ({0, 1}, 0))
        self.assertEqual(pensee.decision([], tuple("...."), "X"), ({0, 1, 2, 3}, None))

    def test_concepts_are_general_gravity(self):
        """Le même texte vaut avec la gravité : un mini Puissance 4 (4 x 4, aligner 3)."""
        size = 4
        lines = [[(r + k * dr) * size + c + k * dc for k in range(3)]
                 for r in range(size) for c in range(size)
                 for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1))
                 if 0 <= r + 2 * dr < size and 0 <= c + 2 * dc < size]

        def apres(etat, colonne, joueur):
            ligne = next(r for r in range(size) if etat[r * size + colonne] == ".")  # le jeton tombe
            suite = list(etat)
            suite[ligne * size + colonne] = joueur
            return suite

        mind = think(
            possibles=lambda etat: [c for c in range(size) if etat[(size - 1) * size + c] == "."],
            apres=apres,
            gagne=lambda etat, joueur: any(all(etat[i] == joueur for i in line) for line in lines),
            adversaire=lambda joueur: "O" if joueur == "X" else "X")
        board = list("XX.." + "O..." + "...." + "....")  # ligne du bas d'abord
        self.assertEqual(mind["gagner"](board, "X"), {2})
        self.assertEqual(mind["parer"](board, "O"), {2})  # le même parer qu'au Morpion
        board = list(".X.." + ".O.." + "...." + "....")
        self.assertEqual(mind["fourchette"](board, "X"), {2})  # X X au milieu : deux bouts libres

    def test_concepts_are_general_quantity(self):
        """Et avec une quantité : le Nim (prendre 1 à 3 allumettes, la dernière gagne)."""
        mind = think(
            possibles=lambda n: list(range(1, min(3, n) + 1)),
            apres=lambda n, prises, joueur: n - prises,
            gagne=lambda n, joueur: n == 0,
            adversaire=lambda joueur: 1 - joueur)
        self.assertEqual(mind["gagner"](3, 0), {3})
        self.assertEqual(mind["gagner"](6, 0), set())
        self.assertEqual(mind["parer"](6, 0), set())  # aucune menace à parer

    def test_concept_trees_are_general(self):
        """Les arbres de la mère s'évaluent avec les quatre notions de n'importe quel jeu (Nim)."""
        notions = type("Nim", (), {
            "possibles": staticmethod(lambda n: list(range(1, min(3, n) + 1))),
            "apres": staticmethod(lambda n, prises, joueur: n - prises),
            "gagne": staticmethod(lambda n, joueur: n == 0),
            "suivant": staticmethod(lambda joueur: 1 - joueur)})
        pensee = concepts.Pensee(notions)
        self.assertEqual(pensee.choix(GAGNER, 3, 0), {3})
        # « aucun de ses coups ne le fait gagner » : à 5, seule la prise de 1 lui laisse
        # plus de 3 allumettes.
        self.assertEqual(pensee.choix(PARER, 5, 0), {1})

    def test_puissance4_perception(self):
        """La mère écrit pour le fils la gravité que l'Analyzer a comprise."""
        teaching = puissance4()
        self.assertEqual(teaching.knowledge["actions"], list(range(7)))  # essayées dans le labo
        self.assertEqual(teaching.knowledge["patterns"], [[1, 2, 3, 4]])  # leçon de l'exemple
        mind = teaching.mind
        board = [" "] * 42
        board[3], board[10] = "X", "O"
        self.assertEqual(mind.case_jouee(board, 3), 17)  # au-dessus des deux jetons
        self.assertEqual(mind.apres(board, 3, "X")[17], "X")
        self.assertEqual(mind.action_pour(38), 3)
        for row in range(6):
            board[row * 7] = "X"
        self.assertNotIn(0, mind.possibles(board))  # colonne pleine

    def test_puissance4_pattern_needs_support(self):
        """Un alignement de la 2e rangée ne s'atteint qu'en posant d'abord des jetons dessous ;
        décalé d'une case de trop, il déborde sur la rangée suivante et ne finit rien."""
        teaching = puissance4()
        self.assertEqual(teaching.play_pattern([8, 9, 10, 11]), [8, 9, 10, 11])
        self.assertIsNone(teaching.play_pattern([4, 5, 6, 7]))

    def test_puissance4_symmetry(self):
        """Avec les 69 alignements, 4 renumérotations les préservent ; la gravité n'en laisse
        qu'une au labo : le miroir gauche-droite."""
        teaching = puissance4()
        teaching.knowledge["patterns"] = [list(w) for w in WINDOWS]
        teaching.rethink()
        teaching.discover_symmetries()
        mirror = [row * 7 + 6 - column for row in range(6) for column in range(7)]
        self.assertEqual(teaching.knowledge["symmetries"], [mirror])


if __name__ == "__main__":
    unittest.main()
