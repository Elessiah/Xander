import textwrap
import unittest
from pathlib import Path

from xander.analyzer import guess_operation
from xander.model import Function, FunctionKind, FunctionOperation, Variable
from xander.mother import Mother
from xander.parser import ExampleParser, ExampleSyntaxError, parse_example
from xander.rebuilder import build_pool_test, parse_observations

RES = Path(__file__).resolve().parent.parent / "res"


def parse(text: str):
    return ExampleParser().parse_text(textwrap.dedent(text))


def call(*arguments):
    return Function("game.f", Variable("array", 3, "board"), [repr(a) for a in arguments], 0, list(arguments))


class ParserTest(unittest.TestCase):
    def test_morpion_example(self):
        parsed = parse_example(RES / "exampleMorpion.py")
        self.assertEqual(parsed.players_name, ["X", "O"])
        self.assertEqual(parsed.winner, "X")
        self.assertEqual([f.time for f in parsed.init_functions], [0, 1])
        self.assertEqual([f.time for f in parsed.player_functions()], list(range(2, 12)))
        self.assertEqual(parsed.back_function.name, "game.back")
        play = parsed.players["X"].functions_used[1]
        self.assertEqual((play.name, play.parameters, play.arguments), ("game.play", ["4"], [4]))
        self.assertIs(play.kind, FunctionKind.INOUT)
        self.assertEqual(play.return_value.kind, "array")
        self.assertEqual(play.return_value.size, 9)

    def test_function_kinds(self):
        parsed = parse("""
            # player A
            game.reset()
            game.play(1)
            x = game.get()  # integer
            x = game.play(2)  # integer
        """)
        kinds = [f.kind for f in parsed.players["A"].functions_used]
        self.assertEqual(kinds, [FunctionKind.NONE, FunctionKind.INPUT, FunctionKind.OUTPUT, FunctionKind.INOUT])

    def test_last_line_without_newline(self):
        parsed = ExampleParser().parse_text("# player A\nx = game.get()  # integer")
        self.assertEqual(len(parsed.players["A"].functions_used), 1)

    def test_strings_with_hash_and_commas(self):
        parsed = parse("""
            # player A
            game.say("a, #b", 3)
        """)
        self.assertEqual(parsed.players["A"].functions_used[0].arguments, ["a, #b", 3])

    def test_draw(self):
        self.assertEqual(parse("# player A\ngame.play(1)\n# end draw\n").winner, "D")

    def test_errors(self):
        cases = {
            "type manquant": "# player A\nx = game.get()\n",
            "type inconnu": "# player A\nx = game.get()  # float\n",
            "taille": "# player A\nx = game.get()  # array neuf\n",
            "aucun joueur": "# init\ngame = Game()  # game\n",
        }
        for message, text in cases.items():
            with self.subTest(message), self.assertRaisesRegex(ExampleSyntaxError, message):
                ExampleParser().parse_text(text)


class RebuilderTest(unittest.TestCase):
    def test_pool_test_and_observations(self):
        parsed = parse_example(RES / "exampleMorpion.py")
        source = build_pool_test(parsed)
        self.assertIn("board = game.play(4)", source)
        self.assertNotIn("'game'", source)  # la variable de jeu n'est pas observée
        observations = parse_observations("bruit\n@@xander 3 board ['0', 'X']\n@@xander 4 b True\n")
        self.assertEqual(observations, {3: ["0", "X"], 4: True})


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

    def test_learn_jumper_single_player(self):
        model = Mother().learn(RES / "exampleJumper.py")
        self.assertEqual(model.nb_players, 1)
        self.assertEqual(model.nb_actions_per_turn, 2)

    def test_create_son(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Mother().create_son("fils", RES / "exampleMorpion.py", directory)
            namespace = {}
            exec(path.read_text(encoding="utf-8"), namespace)
            self.assertEqual(namespace["KNOWLEDGE"]["players"], ["X", "O"])


if __name__ == "__main__":
    unittest.main()
