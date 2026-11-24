import textwrap
import unittest
from pathlib import Path

from xander.analyzer import guess_operation
from xander.model import Function, FunctionOperation, Variable
from xander.mother import Mother
from xander.parser import ExampleParser, parse_example
from xander.rebuilder import ReplayError, build_pool_test, parse_observations, replay

RES = Path(__file__).resolve().parent.parent / "res"


def parse(text: str):
    return ExampleParser().parse_text(textwrap.dedent(text))


def call(*arguments):
    return Function("game.f", Variable("array", 3, "board"), [repr(a) for a in arguments], 0, list(arguments))


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


class GuessOperationTest(unittest.TestCase):
    def test_single_target_index(self):
        self.assertIs(guess_operation(["a", "b", "c"], ["a", "X", "c"], call(1)),
                      FunctionOperation.SINGLE_TARGET_INDEX)

    def test_single_target_name(self):
        self.assertIs(guess_operation(["a", "b", "c"], ["a", "X", "c"], call("b")),
                      FunctionOperation.SINGLE_TARGET_NAME)

    def test_src_dest(self):
        self.assertIs(guess_operation(["P", " ", "c"], [" ", "P", "c"], call(0, 1)),
                      FunctionOperation.SRC_DEST_TARGET_INDEX)
        self.assertIs(guess_operation(["P", "e", "c"], ["e", "P", "c"], call("P", "e")),
                      FunctionOperation.SRC_DEST_TARGET_NAME)

    def test_quantity(self):
        self.assertIs(guess_operation(10, 7, call(3)), FunctionOperation.QUANTITY_RM)
        self.assertIs(guess_operation(10, 13, call(3)), FunctionOperation.QUANTITY_ADD)
        self.assertIs(guess_operation(10, 3, call(3)), FunctionOperation.QUANTITY_SET)

    def test_nothing_matches(self):
        self.assertIsNone(guess_operation(["a", "b"], ["X", "X"], call(1)))
        self.assertIsNone(guess_operation(["a", "b"], True, call(1)))
        self.assertIsNone(guess_operation(10, 9, call(3)))


class MotherTest(unittest.TestCase):
    def test_learn_morpion(self):
        model = Mother().learn(RES / "exampleMorpion.py")
        self.assertEqual(model.nb_players, 2)
        self.assertEqual(model.turn_pattern, ["get_game_state", "play"])
        operations = model.report.operations["game.play"]
        self.assertEqual([(op.kind, op.variable.name) for op in operations],
                         [(FunctionOperation.SINGLE_TARGET_INDEX, "board")])
        board = next(v for v in model.env if v.name == "board")
        self.assertEqual({f.short_name for f in board.setters}, {"play"})

    def test_learn_allumettes(self):
        model = Mother().learn(RES / "exampleAllumettes.py")
        operations = model.report.operations["game.play"]
        self.assertEqual([op.kind for op in operations], [FunctionOperation.QUANTITY_RM])

    def test_learn_puissance4(self):
        model = Mother().learn(RES / "examplePuissance4.py")
        self.assertEqual(model.nb_players, 2)
        self.assertEqual(model.turn_pattern, ["get_game_state", "play"])
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
                                ("exampleJumper.py", 17)):
            with self.subTest(name):
                from xander.game_model import split_turns
                turns = split_turns(parse_example(RES / name))
                self.assertEqual(len(turns), nb_turns)
                self.assertTrue(all(len(turn) == 2 for turn in turns))

    def test_create_son(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Mother().create_son("fils", RES / "exampleMorpion.py", directory)
            namespace = {}
            exec(path.read_text(encoding="utf-8"), namespace)
            self.assertEqual(namespace["KNOWLEDGE"]["players"], ["X", "O"])


if __name__ == "__main__":
    unittest.main()
