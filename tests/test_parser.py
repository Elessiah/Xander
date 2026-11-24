"""Tests du parseur de fichiers d'exemple (xander/parser.py)."""

import tempfile
import textwrap
import unittest
from pathlib import Path

from xander.model import FunctionKind
from xander.parser import (
    ExampleParser,
    ExampleSyntaxError,
    parse_call_line,
    parse_example,
    parse_type_comment,
    split_comment,
)

RES = Path(__file__).resolve().parent.parent / "res"


def parse(text: str):
    return ExampleParser().parse_text(textwrap.dedent(text))


class SplitCommentTest(unittest.TestCase):
    def test_code_and_comment(self):
        self.assertEqual(split_comment("board = game.play(4)  # array 9"), ("board = game.play(4)", "array 9"))

    def test_no_comment(self):
        self.assertEqual(split_comment("game.play(4)   "), ("game.play(4)", ""))

    def test_hash_inside_string_is_not_a_comment(self):
        self.assertEqual(split_comment('game.say("#1")  # string'), ('game.say("#1")', "string"))
        self.assertEqual(split_comment("game.say('a # b')"), ("game.say('a # b')", ""))

    def test_unterminated_code_does_not_crash(self):
        code, comment = split_comment("game.play(")
        self.assertEqual((code, comment), ("game.play(", ""))


class ParseTypeCommentTest(unittest.TestCase):
    def test_kind_and_size(self):
        self.assertEqual(parse_type_comment("array 9"), ("array", 9))
        self.assertEqual(parse_type_comment("  array   200 "), ("array", 200))

    def test_default_size_is_one(self):
        for kind in ("game", "integer", "bool", "string", "back"):
            with self.subTest(kind):
                self.assertEqual(parse_type_comment(kind), (kind, 1))

    def test_kind_is_case_insensitive(self):
        self.assertEqual(parse_type_comment("Array 3"), ("array", 3))

    def test_errors(self):
        cases = {"": "type manquant", "float": "type inconnu", "array neuf": "entier", "array -1": "entier"}
        for comment, message in cases.items():
            with self.subTest(comment), self.assertRaisesRegex(ValueError, message):
                parse_type_comment(comment)


class ParseCallLineTest(unittest.TestCase):
    def test_call_with_assignment(self):
        target, name, parameters, arguments = parse_call_line("board = game.play(4)", "array 9")
        self.assertEqual((target.name, target.kind, target.size), ("board", "array", 9))
        self.assertEqual((name, parameters, arguments), ("game.play", ["4"], [4]))

    def test_call_without_assignment_needs_no_type(self):
        target, name, parameters, _ = parse_call_line("game.reset()", "")
        self.assertTrue(target.is_empty)
        self.assertEqual((name, parameters), ("game.reset", []))

    def test_constructor_and_plain_function(self):
        self.assertEqual(parse_call_line("game = Morpion()", "game")[1], "Morpion")
        self.assertEqual(parse_call_line("x = f(1)", "integer")[1], "f")

    def test_literal_arguments(self):
        _, _, parameters, arguments = parse_call_line(
            "game.f(-1, 2.5, 'a, b', True, None, [1, 2], (3, 4), {'k': 1})", "")
        self.assertEqual(parameters[2], "'a, b'")
        self.assertEqual(arguments, [-1, 2.5, "a, b", True, None, [1, 2], (3, 4), {"k": 1}])

    def test_non_literal_argument_is_kept_as_source(self):
        _, _, parameters, arguments = parse_call_line("game.play(board[0], x + 1)", "")
        self.assertEqual(parameters, ["board[0]", "x + 1"])
        self.assertEqual(arguments, [None, None])

    def test_unhashable_literal_gives_none(self):
        self.assertEqual(parse_call_line("game.play({[1]: 2})", "")[3], [None])

    def test_errors(self):
        cases = [  # (code, commentaire de type, message attendu)
            ("x = game.get()", "", "type manquant"),
            ("game.play(", "", "invalide"),
            ("game.a(); game.b()", "", "une seule instruction"),
            ("a, b = game.get()", "integer", "variable simple"),
            ("a = b = game.get()", "integer", "variable simple"),
            ("game.board[0] = game.get()", "integer", "variable simple"),
            ("import os", "", "seuls les appels"),
            ("x = 3", "integer", "appel de fonction"),
            ("game", "", "appel de fonction"),
            ("game.play(move=4)", "", "arguments nommés"),
            ("game.play(g(1))", "", "imbriqués"),
            ("game.play([g(1)])", "", "imbriqués"),
            ("game.play(g(1) + 1)", "", "imbriqués"),
        ]
        for code, comment, message in cases:
            with self.subTest(code), self.assertRaisesRegex(ValueError, message):
                parse_call_line(code, comment)

    def test_starred_argument_has_no_known_value(self):
        self.assertEqual(parse_call_line("game.play(*moves)", "")[3], [None])


class HeaderTest(unittest.TestCase):
    def test_sections(self):
        parsed = parse("""
            # include
            from Games.Morpion import Morpion
            # init
            game = Morpion()  # game
            # back
            board = game.back()  # array 9
            # player X
            board = game.play(4)  # array 9
            # end player X
        """)
        self.assertEqual(parsed.imports, ["from Games.Morpion import Morpion"])
        self.assertEqual([f.name for f in parsed.init_functions], ["Morpion"])
        self.assertEqual(parsed.back_function.name, "game.back")
        self.assertEqual(parsed.players_name, ["X"])
        self.assertEqual(parsed.winner, "X")

    def test_header_spelling_variants(self):
        for header in ("# player X", "#player X", "#   player   X  ", "# PLAYER X", "# Player X"):
            with self.subTest(header):
                parsed = ExampleParser().parse_text(f"{header}\ngame.play(1)\n")
                self.assertEqual(parsed.players_name, ["X"])

    def test_player_name_keeps_its_case(self):
        self.assertEqual(parse("# player Alice\ngame.play(1)\n").players_name, ["Alice"])

    def test_winner_forms(self):
        cases = {"# end player O": "O", "# END PLAYER O": "O", "# end  player   O": "O",
                 "# end draw": "D", "# end nul": "D", "# end d": "D", "# end": ""}
        for header, winner in cases.items():
            with self.subTest(header):
                text = f"# player X\ngame.play(1)\n# player O\ngame.play(2)\n{header}\n"
                self.assertEqual(ExampleParser().parse_text(text).winner, winner)

    def test_free_comments_are_ignored(self):
        parsed = parse("""
            # player X
            # le joueur X ouvre au centre
            #
            #    commentaire indenté
            # ending, backup, initial : ne sont pas des mots-clés
            # backup du plateau
            # -*- coding: utf-8 -*-
            x = game.get()  # integer
            # end player X
        """)
        self.assertEqual(parsed.players_name, ["X"])
        self.assertEqual(len(parsed.players["X"].functions_used), 1)
        self.assertEqual(parsed.winner, "X")

    def test_malformed_headers_are_errors(self):
        for header in ("# player O  (2e tour)", "# player", "# end player X gagne", "# end of setup",
                       "# back to the board", "# init ialisation", "# include os",
                       "# player: O", "# player:O", "# PLAYERS O", "# end-player X", "# init:"):
            with self.subTest(header), self.assertRaisesRegex(ExampleSyntaxError, "ligne 3 : en-tête mal formé"):
                ExampleParser().parse_text(f"# player X\ngame.play(1)\n{header}\ngame.play(2)\n")

    def test_players_in_order_of_first_appearance(self):
        parsed = parse("""
            # player O
            game.play(1)
            # player X
            game.play(2)
            # player O
            game.play(3)
        """)
        self.assertEqual(parsed.players_name, ["O", "X"])
        self.assertEqual([f.arguments for f in parsed.players["O"].functions_used], [[1], [3]])

    def test_code_before_any_header_is_an_import(self):
        parsed = ExampleParser().parse_text("import random\n# player A\ngame.play(1)\n")
        self.assertEqual(parsed.imports, ["import random"])

    def test_code_after_end_is_an_error(self):
        with self.assertRaisesRegex(ExampleSyntaxError, "après '# end'"):
            ExampleParser().parse_text("# player A\ngame.play(1)\n# end\ngame.play(2)\n")


class TimeTest(unittest.TestCase):
    def test_chronology(self):
        parsed = parse("""
            # init
            game = Game()  # game
            game.init()
            # back
            game.back()
            # player A
            x = game.get()  # integer
            game.play(1)
            # player B
            game.play(2)
        """)
        self.assertEqual([f.time for f in parsed.init_functions], [0, 1])
        self.assertEqual(parsed.back_function.time, 0)  # back ne consomme pas de temps
        self.assertEqual([f.time for f in parsed.player_functions()], [2, 3, 4])

    def test_back_in_the_middle_does_not_shift_time(self):
        parsed = parse("""
            # player A
            game.play(1)
            # back
            game.back()
            # player A
            game.play(2)
        """)
        self.assertEqual([f.time for f in parsed.player_functions()], [0, 1])


class FunctionKindTest(unittest.TestCase):
    def test_kinds(self):
        parsed = parse("""
            # player A
            game.reset()
            game.play(1)
            x = game.get()  # integer
            x = game.play(2)  # integer
        """)
        kinds = [f.kind for f in parsed.players["A"].functions_used]
        self.assertEqual(kinds, [FunctionKind.NONE, FunctionKind.INPUT, FunctionKind.OUTPUT, FunctionKind.INOUT])

    def test_variables_are_recorded_for_each_assignment(self):
        parsed = parse("""
            # init
            game = Game()  # game
            # player A
            x = game.get()  # integer
            game.play(1)
            x = game.get()  # integer
        """)
        self.assertEqual([(v.name, v.kind) for v in parsed.variables],
                         [("game", "game"), ("x", "integer"), ("x", "integer")])


class FileTest(unittest.TestCase):
    def test_morpion_example(self):
        parsed = parse_example(RES / "exampleMorpion.py")
        self.assertEqual(parsed.source, RES / "exampleMorpion.py")
        self.assertEqual(parsed.players_name, ["X", "O"])
        self.assertEqual(parsed.winner, "X")
        self.assertEqual([f.time for f in parsed.init_functions], [0, 1])
        self.assertEqual([f.time for f in parsed.player_functions()], list(range(2, 12)))
        self.assertEqual(parsed.back_function.name, "game.back")
        play = parsed.players["X"].functions_used[1]
        self.assertEqual((play.name, play.parameters, play.arguments), ("game.play", ["4"], [4]))
        self.assertIs(play.kind, FunctionKind.INOUT)
        self.assertEqual((play.return_value.kind, play.return_value.size), ("array", 9))

    def test_every_example_parses(self):
        for path in sorted(RES.glob("example*.py")):
            with self.subTest(path.name):
                parsed = parse_example(path)
                self.assertTrue(parsed.players)
                self.assertTrue(parsed.player_functions())

    def test_last_line_without_newline(self):
        parsed = ExampleParser().parse_text("# player A\nx = game.get()  # integer")
        self.assertEqual(len(parsed.players["A"].functions_used), 1)

    def test_windows_line_endings(self):
        parsed = ExampleParser().parse_text("# player A\r\nx = game.get()  # integer\r\n# end player A\r\n")
        self.assertEqual(parsed.winner, "A")
        self.assertEqual(parsed.players["A"].functions_used[0].return_value.kind, "integer")

    def test_utf8_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bom.py"
            path.write_bytes(b"\xef\xbb\xbf" + (RES / "exampleMorpion.py").read_bytes())
            parsed = parse_example(path)
        self.assertEqual(parsed.imports, ["from Games.Morpion import Morpion"])

    def test_missing_file(self):
        with self.assertRaises(OSError):
            parse_example(RES / "n_existe_pas.py")

    def test_no_player(self):
        with self.assertRaisesRegex(ExampleSyntaxError, "aucun joueur"):
            ExampleParser().parse_text("# init\ngame = Game()  # game\n")

    def test_error_reports_line_number(self):
        with self.assertRaises(ExampleSyntaxError) as context:
            ExampleParser().parse_text("# player A\n\ngame.play(1)\nx = game.get()  # float\n")
        self.assertIn("ligne 4", str(context.exception))
        self.assertIn("x = game.get()  # float", str(context.exception))

    def test_summary(self):
        summary = parse_example(RES / "exampleMorpion.py").summary()
        self.assertIn("Joueur X", summary)
        self.assertIn("Gagnant : X", summary)


if __name__ == "__main__":
    unittest.main()
