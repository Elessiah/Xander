"""Morpion à trois joueurs (``Games/Morpion3.py``), son professeur max^n, et l'éducation
d'un fils à plus de deux joueurs."""

import functools
import random
import unittest
from pathlib import Path

from Games.MaxnMorpion3 import best_move, maxn_morpion3_play
from Games.Morpion3 import PLAYERS, Morpion3, build_lines, next_player
from xander import concepts
from xander.education import BUDGET, issue
from xander.mother import Mother

EMPTY = [str(i) for i in range(16)]
EXAMPLE = Path(__file__).resolve().parent.parent / "res" / "exampleMorpion3.py"


def board_with(**cells) -> list:
    """Un plateau 4 × 4 où ``X=(0, 1)`` pose X sur les cases 0 et 1, etc."""
    board = list(EMPTY)
    for player, indices in cells.items():
        for i in indices:
            board[i] = player
    return board


class Morpion3Test(unittest.TestCase):
    def setUp(self):
        self.game = Morpion3()
        self.game.init("X")

    def play_all(self, moves):
        result = None
        for move in moves:
            result = self.game.play(move)
        return result

    def test_three_players_in_turn(self):
        seen = []
        for move in range(7):
            seen.append(self.game.get_turn())
            self.assertIsInstance(self.game.play(move), list)
        self.assertEqual(seen, ["X", "O", "Z", "X", "O", "Z", "X"])
        self.assertEqual(self.game.board[:7], ["X", "O", "Z", "X", "O", "Z", "X"])

    def test_any_start_player(self):
        self.game.init("Z")
        turns = []
        for move in (0, 5, 10):
            turns.append(self.game.get_turn())
            self.game.play(move)
        self.assertEqual(turns, ["Z", "X", "O"])
        self.assertEqual([next_player(p) for p in PLAYERS], ["O", "Z", "X"])
        for _ in range(20):
            self.game.init("R")
            self.assertIn(self.game.get_turn(), PLAYERS)

    def test_refused_moves_change_nothing(self):
        self.game.play(5)
        before = self.game.get_game_state()
        for move in (5, -1, 16, "4", 4.0, True, None):
            self.assertIs(self.game.play(move), False, move)
        self.assertEqual(self.game.get_game_state(), before)
        self.assertEqual(self.game.get_turn(), "O")
        self.assertEqual(self.game.nb_turn, 1)

    def test_board_and_lines(self):
        self.assertEqual(self.game.get_game_state(), EMPTY)
        self.assertEqual(len(self.game.lines), 24)  # 8 horizontales, 8 verticales, 8 diagonales
        self.assertEqual(len(build_lines(5, 3)), 48)

    def test_every_line_wins_for_every_player(self):
        for line in self.game.lines:
            for player in PLAYERS:
                game = Morpion3()
                self.assertIs(game.set_game_state(board_with(**{player: line[:2]}), player), False)
                self.assertIs(game.play(line[2]), True, (line, player))
                self.assertEqual(game.win, player)

    def test_directions(self):
        # X : ligne 4-5-6 ; O : colonne 1-5-9 ; Z : diagonale 0-5-10 ; X : anti-diagonale 3-6-9.
        cases = {
            "horizontale": ([4, 0, 1, 5, 2, 3, 6], "X"),
            "verticale": ([0, 1, 2, 3, 5, 4, 8, 9], "O"),
            "diagonale": ([1, 2, 0, 3, 4, 5, 7, 8, 10], "Z"),
            "anti-diagonale": ([3, 0, 1, 6, 4, 5, 9], "X"),
        }
        for name, (moves, winner) in cases.items():
            self.game.init("X")
            self.assertIs(self.play_all(moves), True, name)
            self.assertEqual(self.game.win, winner, name)

    def test_draw(self):
        moves = [4, 10, 15, 14, 1, 6, 2, 12, 13, 7, 11, 8, 3, 0, 9, 5]
        for move in moves[:-1]:
            self.assertIsInstance(self.game.play(move), list)
        self.assertIs(self.game.play(moves[-1]), True)
        self.assertEqual(self.game.win, "D")
        self.assertIs(self.game.play(0), False)  # partie terminée
        self.assertEqual(self.game.get_moves(), [])

    def test_back(self):
        self.play_all([0, 5])
        self.assertEqual(self.game.get_turn(), "Z")
        board = self.game.back()
        self.assertEqual(board, board_with(X=[0]))
        self.assertEqual(self.game.get_turn(), "O")  # la main revient à celui qui avait joué
        self.game.back()
        self.assertEqual(self.game.get_turn(), "X")
        self.assertEqual(self.game.back(), EMPTY)  # rien à annuler
        self.assertEqual(self.game.nb_turn, 0)

    def test_back_after_a_win(self):
        self.play_all([4, 0, 1, 5, 2, 3])
        self.assertIs(self.game.play(6), True)
        self.game.back()
        self.assertEqual(self.game.win, "")
        self.assertEqual(self.game.get_turn(), "X")
        self.assertIsInstance(self.game.play(7), list)

    def test_get_game_state_restarts_finished_game(self):
        self.play_all([4, 0, 1, 5, 2, 3, 6])
        self.assertEqual(self.game.get_game_state(), EMPTY)
        self.assertEqual(self.game.get_turn(), "X")

    def test_example_is_a_real_game(self):
        namespace = {}
        exec(compile(EXAMPLE.read_text(encoding="utf-8"), str(EXAMPLE), "exec"), namespace)
        self.assertEqual(namespace["game"].win, "Z")
        self.assertIs(namespace["board"], True)


class MaxnMorpion3Test(unittest.TestCase):
    def test_takes_a_win_rather_than_blocks(self):
        # X menace 2 (0-1-2), O menace 6 (4-5-6) : chacun gagne plutôt que de parer l'autre.
        board = board_with(X=[0, 1], O=[4, 5], Z=[8, 15])
        self.assertEqual(best_move(board, "X"), 2)
        self.assertEqual(best_move(board, "O"), 6)
        # Z gagne en colonne (4-8-12) alors que X et O menacent aussi.
        board = board_with(X=[1, 2], O=[5, 6], Z=[8, 12])
        self.assertEqual(best_move(board, "Z"), 4)

    def test_blocks_the_next_player(self):
        # X a le trait, O (qui joue juste après) menace 6 ; X ne peut pas gagner.
        board = board_with(X=[0, 15], O=[4, 5], Z=[3, 12])
        self.assertEqual(best_move(board, "X"), 6)

    def test_blocks_the_third_player(self):
        # X a le trait, Z (qui joue après O) menace 10 ; O ne menace rien. Le professeur
        # ne compte pas sur O pour parer.
        board = board_with(X=[3, 12], O=[1, 15], Z=[0, 5])
        self.assertEqual(best_move(board, "X"), 10)

    def test_blocks_each_opponent_from_each_seat(self):
        # Le même motif, vu par chaque joueur : la menace vient du suivant puis du troisième.
        for turn in PLAYERS:
            following = next_player(turn)
            third = next_player(following)
            board = board_with(**{following: [8, 9], third: [14], turn: [3]})
            self.assertEqual(best_move(board, turn), 10, (turn, "suivant"))
            board = board_with(**{third: [8, 9], following: [14], turn: [3]})
            self.assertEqual(best_move(board, turn), 10, (turn, "troisième"))

    def test_full_board_has_no_move(self):
        board = ["X", "O", "Z", "X"] * 4
        self.assertIsNone(best_move(board, "O"))

    def test_plays_only_legal_moves(self):
        """Trois professeurs après deux premiers coups au hasard : chaque coup est permis."""
        for seed in range(6):
            rng = random.Random(seed)
            game = Morpion3()
            game.init(PLAYERS[seed % 3])
            game.play(rng.choice(game.get_moves()))
            game.play(rng.choice(game.get_moves()))
            while not game.win:
                move = best_move(game.get_game_state(), game.get_turn())
                self.assertIn(move, game.get_moves())
                self.assertIsNot(game.play(move), False)

    def test_beats_two_random_players(self):
        """Contre deux joueurs au hasard, à chaque place, il gagne au moins 8 parties sur 10."""
        for seat in PLAYERS:
            wins = 0
            for seed in range(10):
                rng = random.Random(seed)
                game = Morpion3()
                game.init("X")
                while not game.win:
                    if game.get_turn() == seat:
                        maxn_morpion3_play(game)
                    else:
                        game.play(rng.choice(game.get_moves()))
                wins += game.win == seat
            self.assertGreaterEqual(wins, 8, f"professeur en {seat}")

    def test_three_teachers_finish(self):
        game = Morpion3()
        game.init("X")
        while not game.win:
            self.assertIsNot(maxn_morpion3_play(game), False)
        self.assertEqual(game.win, "D")  # sans hasard, trois professeurs font nul


@functools.lru_cache(maxsize=None)
def education(nb_games: int = 0):
    """Une éducation au Morpion à trois, partagée par les tests qui ne font que la regarder."""
    return Mother().raise_son(EXAMPLE, maxn_morpion3_play, nb_games)


class EducationMorpion3Test(unittest.TestCase):
    """Rien n'est propre au Morpion à trois dans la mère : elle lit l'ordre des joueurs dans
    l'exemple, et le Morpion à deux en est le cas particulier."""

    def test_mother_reads_the_order_of_players(self):
        teaching = education()
        self.assertEqual(teaching.cycle(), ["X", "O", "Z"])  # un cycle de trois, pas une parité
        self.assertEqual(teaching.n, 3)
        self.assertEqual([teaching.seat(k) for k in range(7)], [0, 1, 2, 0, 1, 2, 0])
        self.assertEqual(teaching.knowledge["marks"], ["X", "O", "Z"])  # le pion de chacun
        self.assertEqual(teaching.knowledge["patterns"], [[6, 9, 12]])  # par contre-épreuve
        self.assertEqual(teaching.records[0].result, "gagné par Z")

    def test_position_seen_from_each_side(self):
        """M : moi, A : le suivant, B : celui d'après ; chacun voit les deux autres autrement."""
        mind = education().mind
        board = board_with(X=[0], O=[1], Z=[2])
        self.assertEqual(mind.cle(board, "X"), "MAB" + "." * 13)
        self.assertEqual(mind.cle(board, "O"), "BMA" + "." * 13)
        self.assertEqual(mind.cle(board, "Z"), "ABM" + "." * 13)
        self.assertEqual([mind.suivant(p) for p in "XOZ"], ["O", "Z", "X"])

    def test_son_finds_his_mark_on_the_board(self):
        """Chacun joue à son tour : celui qui a le trait est le seul qui a posé moins de pions
        que celui qui joue avant lui."""
        son = education().son
        self.assertEqual(son.qui_suis_je(list(EMPTY), {}), "X")  # comme dans l'exemple
        self.assertEqual(son.qui_suis_je(board_with(X=[0]), {}), "O")
        self.assertEqual(son.qui_suis_je(board_with(X=[0], O=[5]), {}), "Z")
        self.assertEqual(son.qui_suis_je(board_with(X=[0, 3], O=[5], Z=[7]), {}), "O")

    def test_parade_says_whom_it_parries(self):
        """Le langage des concepts nomme chaque joueur par sa place après moi : parer le
        suivant n'est pas parer celui d'après."""
        teaching = education()
        teaching.knowledge["patterns"] = [list(line) for line in build_lines(4, 3)]
        teaching.rethink()
        pensee = concepts.Pensee(teaching.mind)
        lui, lui2 = concepts.joueurs(3)[1:]
        parer = {qui: concepts.non(concepts.au_moins(1, qui, concepts.brique(concepts.GAGNE, qui)))
                 for qui in (lui, lui2)}
        board = board_with(X=[3, 15], O=[8, 9], Z=[12, 13])  # X a le trait ; O menace 10, Z 14
        self.assertEqual(pensee.choix(parer[lui], board, "X"), {10})
        self.assertEqual(pensee.choix(parer[lui2], board, "X"), {14})
        self.assertIn("le 2e après moi", concepts.decrire_regle(parer[lui2]))
        self.assertIn("lui2 = suivant(lui)", concepts.source("parer_loin", parer[lui2]))

    def test_end_is_worth_something_for_each(self):
        """Une victoire de l'un est une défaite pour les deux autres ; un nul vaut nul pour tous."""
        self.assertEqual([issue(2, side) for side in range(3)], [-1, -1, 1])
        self.assertEqual([issue(None, side) for side in range(3)], [0, 0, 0])

    def test_education_at_every_seat(self):
        """Le fils joue à chaque place, contre le professeur, le hasard et un adversaire mixte ;
        la mère retrouve les 24 alignements et les 8 symétries du carré, sans coup impossible
        après la 5e partie, dans le budget."""
        teaching = education(9)
        records = teaching.records[1:]
        self.assertEqual({r.son_side for r in records}, {"X", "O", "Z"})
        self.assertEqual({r.opponent for r in records}, {"professeur", "hasard", "mixte"})
        self.assertEqual(sorted(map(sorted, teaching.knowledge["patterns"])),
                         sorted(map(sorted, build_lines(4, 3))))
        self.assertEqual(len(teaching.knowledge["symmetries"]) + 1, 8)
        self.assertEqual([r.number for r in records if r.number > 5 and r.impossibles], [])
        self.assertLessEqual(teaching.max_views, BUDGET)
        self.assertTrue(teaching.knowledge["rules"])  # des règles qu'elle a construites


if __name__ == "__main__":
    unittest.main()
