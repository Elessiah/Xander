"""Le compte est bon (version courte) et son professeur exact."""

import unittest
from pathlib import Path

from Games.CompteEstBon import (ADDITION, DIVISION, MULTIPLICATION, SOUSTRACTION, VIDE, CompteEstBon,
                                atteignables, coups_permis)
from Games.SolveurCompteEstBon import meilleur_chemin, meilleur_coup, solveur_compte_est_bon_play

RES = Path(__file__).resolve().parent.parent / "res"


def partie(etat):
    game = CompteEstBon(0)
    game.set_game_state(etat)
    return game


class ReglesTest(unittest.TestCase):
    def test_coup_permis(self):
        game = partie([3, 7, 5, 2, 50])
        self.assertEqual(game.play(1, 2, MULTIPLICATION), [3, 35, VIDE, 2, 50])
        self.assertEqual(game.play(0, 3, ADDITION), [5, 35, VIDE, VIDE, 50])
        self.assertIs(game.play(1, 0, SOUSTRACTION), False)  # il ne reste que 30 : perdue
        self.assertEqual(game.get_game_state(), [VIDE, 30, VIDE, VIDE, 50])
        self.assertTrue(game.finie)
        self.assertFalse(game.gagnee)

    def test_division_et_soustraction(self):
        game = partie([8, 2, 6, 9, 99])
        self.assertEqual(game.play(0, 1, DIVISION), [4, VIDE, 6, 9, 99])
        self.assertEqual(game.play(3, 2, SOUSTRACTION), [4, VIDE, VIDE, 3, 99])  # 9 - 6, à la place 3

    def test_coups_refuses(self):
        etat = [8, 3, VIDE, 8, 50]
        for coup in ((0, 1, DIVISION),       # 8 / 3 ne tombe pas juste
                     (1, 0, SOUSTRACTION),   # 3 - 8 < 0
                     (0, 3, SOUSTRACTION),   # 8 - 8 = 0
                     (0, 0, ADDITION),       # même nombre
                     (0, 2, ADDITION),       # place vide
                     (0, 4, ADDITION),       # la cible n'est pas un nombre
                     (0, 9, ADDITION),       # hors du plateau
                     (-1, 0, ADDITION),
                     (0, 1, 4),              # opération inconnue
                     (0, 1, True),           # un booléen n'est pas un coup
                     (0, 1, "+"),
                     (0, 1, None)):
            game = partie(etat)
            self.assertIs(game.play(*coup), False, coup)
            self.assertEqual(game.get_game_state(), etat, coup)
            self.assertFalse(game.finie, coup)
        self.assertIs(partie(etat).play(0), False)  # un seul argument

    def test_fin_gagnee(self):
        game = partie([6, 4, 1, 1, 24])
        self.assertIs(game.play(0, 1, MULTIPLICATION), True)
        self.assertTrue(game.finie and game.gagnee)
        self.assertEqual(game.get_game_state(), [24, VIDE, 1, 1, 24])  # pas de nouvelle partie
        self.assertIs(game.play(2, 3, ADDITION), False)              # partie finie : refusé
        self.assertEqual(game.get_moves(), [])

    def test_fin_perdue(self):
        game = partie([2, 3, VIDE, VIDE, 50])
        self.assertIs(game.play(0, 1, ADDITION), False)
        self.assertEqual(game.get_game_state(), [5, VIDE, VIDE, VIDE, 50])  # le coup est joué
        self.assertTrue(game.finie)
        self.assertFalse(game.gagnee)
        self.assertIs(game.play(0, 1, ADDITION), False)

    def test_back(self):
        game = CompteEstBon(5)
        depart = game.get_game_state()
        game.play(*game.get_moves()[0])
        game.play(*game.get_moves()[0])
        self.assertNotEqual(game.get_game_state(), depart)
        game.back()
        self.assertEqual(game.back(), depart)
        self.assertEqual(game.back(), depart)  # rien à annuler

    def test_back_apres_la_fin(self):
        game = partie([6, 4, 1, 1, 24])
        game.play(0, 1, MULTIPLICATION)
        self.assertEqual(game.back(), [6, 4, 1, 1, 24])
        self.assertFalse(game.finie)
        self.assertEqual(game.play(2, 3, ADDITION), [6, 4, 2, VIDE, 24])

    def test_tirages_reproductibles_et_solubles(self):
        for graine in range(200):
            game = CompteEstBon(graine)
            self.assertEqual(game.get_game_state(), CompteEstBon(graine).get_game_state())
            for etat in (game.get_game_state(), game.init()):
                *nombres, cible = etat
                self.assertEqual(len(nombres), 4)
                self.assertTrue(all(1 <= n <= 10 for n in nombres))
                self.assertTrue(11 <= cible <= 100)
                self.assertIn(cible, atteignables(nombres))

    def test_init_tire_le_suivant(self):
        game = CompteEstBon(2)
        self.assertEqual(game.get_game_state(), [1, 2, 2, 6, 16])
        self.assertEqual(game.init(), [5, 5, 10, 4, 85])


class SolveurTest(unittest.TestCase):
    def test_ne_joue_que_des_coups_permis_et_trouve_la_cible(self):
        for graine in range(300):
            game = CompteEstBon(graine)
            chemin, regardees = meilleur_chemin(game.get_game_state())
            self.assertLessEqual(regardees, 1000)  # recherche complète, mais petite
            joues = 0
            while not game.finie:
                coup = meilleur_coup(game.get_game_state())
                self.assertIn(coup, game.get_moves())
                solveur_compte_est_bon_play(game, verbose=False)
                joues += 1
            self.assertTrue(game.gagnee, graine)
            self.assertEqual(joues, len(chemin))  # il suit le chemin le plus court

    def test_chemin_le_plus_court(self):
        self.assertEqual(meilleur_chemin([6, 4, 1, 1, 24])[0], [(0, 1, MULTIPLICATION)])
        self.assertEqual(len(meilleur_chemin([5, 5, 10, 4, 85])[0]), 3)
        self.assertEqual(meilleur_chemin([24, VIDE, 1, 1, 24])[0], [])  # déjà gagnée

    def test_cible_hors_d_atteinte(self):
        """Après une maladresse, il vise le nombre le plus proche."""
        etat = [10, 1, VIDE, VIDE, 50]
        self.assertNotIn(50, atteignables([10, 1]))
        self.assertEqual(meilleur_coup(etat), (0, 1, ADDITION))  # 11 est le plus proche de 50
        game = partie(etat)
        self.assertIs(solveur_compte_est_bon_play(game, verbose=False), False)
        self.assertEqual(game.get_game_state()[0], 11)

    def test_partie_finie(self):
        self.assertIsNone(solveur_compte_est_bon_play(partie([5, VIDE, VIDE, VIDE, 50]), verbose=False))

    def test_coups_permis_coherents(self):
        game = CompteEstBon(7)
        for coup in coups_permis(game.get_game_state()):
            self.assertNotEqual(game.play(*coup), False)
            game.back()


class ExempleTest(unittest.TestCase):
    def test_exemple_se_joue_tel_quel(self):
        namespace = {}
        exec(compile((RES / "exampleCompteEstBon.py").read_text(encoding="utf-8"), "exemple", "exec"),
             namespace)
        self.assertIs(namespace["etat"], True)
        self.assertTrue(namespace["game"].gagnee)


if __name__ == "__main__":
    unittest.main()
