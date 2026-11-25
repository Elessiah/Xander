import random
import unittest

from Games.Allumettes import Allumettes
from Games.Coords import Coords
from Games.Jumper import Jumper
from Games.MinmaxAllumettes import minmax_allumettes_play
from Games.MinmaxMorpion import best_move, minmax_morpion_play
from Games.MinmaxPuissance4 import best_move as p4_best_move, minmax_puissance4_play
from Games.Morpion import Morpion
from Games.Puissance4 import Puissance4
from Games.MinmaxPylos import WIN, minmax_pylos_play, solution
from Games.Pylos import PLAY, TAKE, TAKE_MORE, Pylos, pyramide


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

    def test_booleans_are_not_moves(self):
        self.assertIs(self.game.play(True), False)
        self.assertIs(Allumettes().play(True), False)
        self.assertIs(Puissance4().play(True), False)

    def test_set_game_state_with_player(self):
        self.game.set_game_state(["X", "O", "2", "3", "4", "5", "6", "7", "8"], "O")
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
        self.assertEqual(game.nb_turn, 0)

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


    def test_get_moves(self):
        self.play_all([0] * 6)
        self.assertEqual(self.game.get_moves(), [1, 2, 3, 4, 5, 6])


class MinmaxPuissance4Test(unittest.TestCase):
    def test_takes_win_and_blocks(self):
        board = [" "] * 42
        board[0:3] = ["X", "X", "X"]  # X a trois jetons en bas à gauche
        board[7:9] = ["O", "O"]
        self.assertEqual(p4_best_move(board, "X"), 3)  # gagne
        self.assertEqual(p4_best_move(board, "O"), 3)  # bloque

    def test_full_board_has_no_move(self):
        self.assertIsNone(p4_best_move(["X"] * 42, "O"))

    def test_beats_random(self):
        for seed in range(6):
            rng = random.Random(seed)
            game = Puissance4()
            game.init("XO"[seed % 2])
            while not game.win:
                if game.get_turn() == "X":
                    minmax_puissance4_play(game, verbose=False, depth=4)
                else:
                    game.play(rng.choice(game.get_moves()))
            self.assertEqual(game.win, "X", f"graine {seed}")

    def test_minmax_vs_minmax_ends(self):
        game = Puissance4()
        game.init("X")
        while not game.win:
            self.assertIsNot(minmax_puissance4_play(game, verbose=False, depth=3), False)
        self.assertIn(game.win, ("X", "O", "D"))


class PylosTest(unittest.TestCase):
    def setUp(self):
        self.game = Pylos(3)
        self.game.init("X")

    def play_all(self, moves):
        result = None
        for move in moves:
            result = self.game.play(move)
        return result

    def test_geometry(self):
        geo = pyramide(3)
        self.assertEqual(geo.nb_spots, 14)
        self.assertEqual(geo.per_player, 7)
        self.assertEqual(geo.supports[9], (0, 1, 3, 4))
        self.assertEqual(geo.supports[13], (9, 10, 11, 12))
        self.assertEqual(geo.above[4], (9, 10, 11, 12))
        self.assertEqual(pyramide(4).nb_spots, 30)

    def test_needs_support(self):
        self.assertIs(self.game.play(9), False)
        self.play_all([0, 1, 3])
        self.assertIs(self.game.play(9), False)
        self.assertIsInstance(self.game.play(4), list)
        self.assertIsInstance(self.game.play(9), list)
        self.assertIs(self.game.play(0), False)  # occupé

    def test_move_up(self):
        self.play_all([0, 1, 3, 4, 2])  # X : 0, 3, 2 ; O : 1, 4 ; 9 est soutenu
        self.assertEqual(self.game.get_turn(), "O")
        self.assertIs(self.game.move(1, 9), False)  # 1 soutient 9
        self.assertIs(self.game.move(4, 9), False)
        self.game.play(5)
        self.assertIsInstance(self.game.move(2, 9), list)  # X monte une bille libre qui ne soutient pas 9
        self.assertEqual(self.game.board[2], " ")
        self.assertEqual(self.game.get_reserve("X"), 4)  # monter ne puise pas dans la réserve

    def test_square_then_take(self):
        self.play_all([0, 2, 1, 5, 3, 6, 4])  # X forme le carré 0, 1, 3, 4
        self.assertEqual(self.game.get_turn(), "X")
        self.assertEqual(self.game.get_phase(), TAKE)
        self.assertIs(self.game.stop(), False)  # il faut reprendre au moins une bille
        self.assertIs(self.game.take(2), False)  # pas à lui
        self.assertIsInstance(self.game.take(4), list)
        self.assertEqual(self.game.get_phase(), TAKE_MORE)
        self.assertIsInstance(self.game.stop(), list)
        self.assertEqual(self.game.get_turn(), "O")
        self.assertEqual(self.game.get_reserve("X"), 4)

    def test_top_wins_and_back(self):
        actions = solution(3).perfect_game()
        for i, action in enumerate(actions):
            result = getattr(self.game, action[0])(*action[1:])
            self.assertIs(result is True, i == len(actions) - 1)
        self.assertEqual(self.game.win, "X")
        self.game.back()
        self.assertEqual(self.game.win, "")
        self.assertEqual(self.game.board[13], " ")

    def test_play_text(self):
        self.assertIsInstance(self.game.play_text("4"), list)
        self.assertIs(self.game.play_text("r 4"), False)
        self.assertIs(self.game.play_text("abc"), False)


class MinmaxPylosTest(unittest.TestCase):
    """Le Pylos 3 × 3 n'est pas dégénéré : carrés, reprises et montées comptent."""

    def test_first_player_wins_only_from_center(self):
        sol = solution(3)
        self.assertEqual(sol.value[0], WIN)
        winning = [a for a, cid, same in sol.children[0] if sol.child_outcome(cid, same)[0] == WIN]
        self.assertEqual(winning, [("play", 4)])

    def test_perfect_game_uses_a_square(self):
        kinds = [action[0] for action in solution(3).perfect_game()]
        self.assertIn("take", kinds)

    def test_moving_up_is_sometimes_the_only_win(self):
        sol = solution(3)
        found = False
        for sid, (text, phase) in enumerate(sol.keys):
            if phase != PLAY or sol.value[sid] != WIN:
                continue
            wins = {a[0] for a, cid, same in sol.children[sid] if sol.child_outcome(cid, same)[0] == WIN}
            if wins == {"move"}:
                found = True
                break
        self.assertTrue(found)

    def test_beats_random(self):
        for seed in range(6):
            rng = random.Random(seed)
            game = Pylos(3)
            game.init("X")
            while not game.win:
                if game.get_turn() == "X":
                    minmax_pylos_play(game, verbose=False)
                else:
                    action = rng.choice(game.get_moves())
                    getattr(game, action[0])(*action[1:])
            self.assertEqual(game.win, "X", f"graine {seed}")


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
