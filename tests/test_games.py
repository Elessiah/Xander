import random
import unittest

from Games.Allumettes import Allumettes
from Games.Coords import Coords
from Games.Jumper import Jumper
from Games.MinmaxAllumettes import minmax_allumettes_play
from Games.MinmaxMorpion import best_move, minmax_morpion_play
from Games.Morpion import Morpion
from Games.Puissance4 import Puissance4


class CoordsTest(unittest.TestCase):
    def test_round_trip(self):
        coords = Coords(width=7)
        for i in range(42):
            coords.set(i=i)
            self.assertEqual(Coords(coords.x, coords.y, width=7).i, i)
        self.assertEqual(Coords(x=2, y=1, width=3).i, 5)


class MorpionTest(unittest.TestCase):
    def setUp(self):
        self.game = Morpion()
        self.game.init("X")

    def test_win(self):
        for move in (0, 3, 1, 4):
            self.assertIsInstance(self.game.play(move), list)
        self.assertIs(self.game.play(2), True)
        self.assertEqual(self.game.win, "X")
        self.assertIs(self.game.play(8), False)  # partie terminée

    def test_draw(self):
        for move in (0, 1, 2, 4, 3, 5, 7, 6):
            self.game.play(move)
        self.assertIs(self.game.play(8), True)
        self.assertEqual(self.game.win, "D")

    def test_invalid_moves(self):
        self.game.play(4)
        for move in (4, -1, 9, "4"):
            self.assertIs(self.game.play(move), False)
        self.assertEqual(self.game.get_turn(), "O")

    def test_back_restores_player(self):
        self.game.play(4)
        self.assertEqual(self.game.back(), [str(i) for i in range(9)])
        self.assertEqual(self.game.get_turn(), "X")

    def test_get_game_state_restarts_finished_game(self):
        for move in (0, 3, 1, 4, 2):
            self.game.play(move)
        self.assertEqual(self.game.get_game_state(), [str(i) for i in range(9)])


class MinmaxMorpionTest(unittest.TestCase):
    def test_takes_win_and_blocks(self):
        self.assertEqual(best_move(["X", "X", "2", "O", "O", "5", "6", "7", "8"], "X"), 2)
        self.assertEqual(best_move(["X", "X", "2", "3", "O", "5", "6", "7", "8"], "O"), 2)

    def test_never_loses_against_random(self):
        rng = random.Random(0)
        for start in "XO" * 10:
            game = Morpion()
            game.init(start)
            while not game.win:
                if game.get_turn() == "X":
                    minmax_morpion_play(game)
                else:
                    game.play(rng.choice(game.get_moves()))
            self.assertIn(game.win, ("X", "D"))

    def test_minmax_vs_minmax_is_draw(self):
        game = Morpion()
        game.init("X")
        while not game.win:
            minmax_morpion_play(game)
        self.assertEqual(game.win, "D")


class AllumettesTest(unittest.TestCase):
    def test_rules(self):
        game = Allumettes()
        game.set_max_nb_allumettes(5)
        game.init("X")
        self.assertIs(game.play(4), False)
        self.assertEqual(game.play(3), 2)
        self.assertIs(game.play(1), True)  # O laisse 1 allumette à X
        self.assertEqual(game.win, "O")

    def test_taking_last_loses(self):
        game = Allumettes()
        game.set_game_state(2, "X")
        self.assertIs(game.play(2), True)
        self.assertEqual(game.win, "O")

    def test_back(self):
        game = Allumettes()
        game.init("X")
        game.play(3)
        self.assertEqual(game.back(), 50)
        self.assertEqual(game.get_turn(), "X")

    def test_minmax_wins_from_winning_positions(self):
        rng = random.Random(0)
        for start in range(2, 40):
            if (start - 1) % 4 == 0:
                continue  # position perdante pour celui qui commence
            game = Allumettes()
            game.set_max_nb_allumettes(start)
            game.init("X")
            while not game.win:
                if game.get_turn() == "X":
                    minmax_allumettes_play(game, verbose=False)
                else:
                    game.play(rng.randint(1, min(3, game.nb_allumettes)))
            self.assertEqual(game.win, "X", f"départ à {start}")


class Puissance4Test(unittest.TestCase):
    def setUp(self):
        self.game = Puissance4()
        self.game.init("X")

    def play_all(self, columns):
        result = None
        for column in columns:
            result = self.game.play(column)
        return result

    def test_vertical(self):
        self.assertIs(self.play_all([0, 1, 0, 1, 0, 1, 0]), True)
        self.assertEqual(self.game.win, "X")

    def test_horizontal(self):
        self.assertIs(self.play_all([0, 0, 1, 1, 2, 2, 3]), True)

    def test_diagonal(self):
        self.assertIs(self.play_all([0, 1, 1, 2, 2, 3, 2, 3, 3, 6, 3]), True)
        self.assertEqual(self.game.win, "X")

    def test_full_column_and_back(self):
        self.play_all([0] * 6)
        self.assertIs(self.game.play(0), False)
        self.game.back()
        self.assertEqual(self.game.board.count(" "), 42 - 5)
        self.assertEqual(self.game.get_turn(), "O")


class JumperTest(unittest.TestCase):
    def test_deterministic_with_seed(self):
        frames = []
        for _ in range(2):
            game = Jumper(seed=1)
            frames.append([game.play(False) for _ in range(30)])
        self.assertEqual(frames[0], frames[1])

    def test_jump_and_back(self):
        game = Jumper(seed=0)
        before = game.get_board()
        game.play(True)
        self.assertEqual(game.player_pos.y, 3)
        self.assertEqual(game.back(), before)

    def test_collision(self):
        game = Jumper(seed=0)
        while game.play(False) is not False:
            self.assertLess(game.ticks, 500)
        self.assertTrue(game.game_over)


if __name__ == "__main__":
    unittest.main()
