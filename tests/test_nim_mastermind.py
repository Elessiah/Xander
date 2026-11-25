"""Tests du Nim à plusieurs tas et du Mastermind, et de leurs professeurs."""

import itertools
import random
import unittest
from pathlib import Path

from Games.Mastermind import ESSAIS, VIDE, Mastermind, historique, reponse, tous_les_codes
from Games.MinmaxMastermind import meilleur_code, minmax_mastermind_play, premier_compatible_play
from Games.MinmaxNim import gagnante, meilleur_coup, minmax_nim_play, valeur
from Games.Nim import Nim
from Games.NimMisere import NimMisere

RES = Path(__file__).resolve().parent.parent / "res"


def rejouer(nom: str) -> dict:
    """Exécute un exemple de ``res/`` tel quel et renvoie ses variables."""
    variables = {}
    exec((RES / nom).read_text(encoding="utf-8"), variables)
    return variables


class NimTest(unittest.TestCase):
    def setUp(self):
        self.game = Nim()
        self.game.set_tas(3, 4, 5)
        self.assertEqual(self.game.init("X"), [3, 4, 5])

    def test_coup_permis(self):
        self.assertEqual(self.game.play(1, 4), [3, 0, 5])
        self.assertEqual(self.game.get_turn(), "O")
        self.assertEqual(self.game.play(0, 1), [2, 0, 5])

    def test_coups_refuses(self):
        for coup in ((3, 1), (-1, 1), (0, 0), (0, 4), (0, -1), (True, 1), (0, True), ("0", 1), (0, 1.0)):
            self.assertIs(self.game.play(*coup), False, coup)
        self.game.play(1, 4)
        self.assertIs(self.game.play(1, 1), False)  # tas vide
        self.assertEqual(self.game.heaps, [3, 0, 5])
        self.assertEqual(self.game.get_turn(), "O")
        self.assertEqual(len(self.game.past), 1)

    def test_prendre_le_dernier_gagne(self):
        self.game.set_game_state([0, 2, 0], "O")
        self.assertIs(self.game.play(1, 2), True)
        self.assertEqual(self.game.win, "O")
        self.assertIs(self.game.play(1, 1), False)  # partie terminée
        self.assertEqual(self.game.get_moves(), [])

    def test_misere_prendre_le_dernier_perd(self):
        game = NimMisere()
        game.set_game_state([0, 1, 0], "O")
        self.assertIs(game.play(1, 1), True)
        self.assertEqual(game.win, "X")

    def test_back(self):
        self.game.play(2, 5)
        self.game.play(0, 3)
        self.assertEqual(self.game.back(), [3, 4, 0])
        self.assertEqual(self.game.get_turn(), "O")
        self.game.set_game_state([1, 0, 0], "X")
        self.game.play(0, 1)
        self.assertEqual(self.game.win, "X")
        self.assertEqual(self.game.back(), [1, 0, 0])
        self.assertEqual(self.game.win, "")

    def test_get_game_state_relance_une_partie_finie(self):
        self.game.set_game_state([0, 0, 1], "X")
        self.game.play(2, 1)
        self.assertEqual(self.game.get_game_state(), [3, 4, 5])
        self.assertEqual(self.game.get_turn(), "X")

    def test_get_moves(self):
        self.game.set_game_state([1, 0, 2], "X")
        self.assertEqual(self.game.get_moves(), [(0, 1), (2, 1), (2, 2)])

    def test_play_text(self):
        self.assertEqual(self.game.play_text("2 3"), [3, 4, 2])
        self.assertIs(self.game.play_text("abc"), False)


class MinmaxNimTest(unittest.TestCase):
    def test_strategie_exacte(self):
        """La stratégie connue donne la même valeur que le Minmax exhaustif, et un coup gagnant."""
        positions = [p for p in itertools.product(range(6), repeat=3) if any(p)]
        positions += [p for p in itertools.product(range(4), repeat=4) if any(p)]
        for misere in (False, True):
            for tas in positions:
                gagne = valeur(tas, misere)
                self.assertEqual(gagnante(tas, misere), gagne, (tas, misere))
                i, n = meilleur_coup(tas, misere)
                self.assertTrue(1 <= n <= tas[i])
                if gagne:
                    suite = list(tas)
                    suite[i] -= n
                    self.assertFalse(valeur(suite, misere), (tas, misere, (i, n)))

    def test_somme_de_nim(self):
        self.assertTrue(gagnante([3, 4, 5]))
        self.assertEqual(meilleur_coup([3, 4, 5]), (0, 2))  # laisse 1, 4, 5 : somme nulle
        self.assertFalse(gagnante([1, 2, 3]))

    def test_gagne_depuis_une_position_gagnante_des_deux_cotes(self):
        for cls in (Nim, NimMisere):
            for tas in ([3, 4, 5], [1, 2, 4], [2, 2, 3], [5, 6], [1, 1, 1], [4, 4, 1, 1]):
                if not gagnante(tas, cls.MISERE):
                    continue
                for prof in "XO":
                    for seed in range(3):
                        rng = random.Random(seed)
                        game = cls()
                        game.set_tas(*tas)
                        game.init(prof)
                        while not game.win:
                            if game.get_turn() == prof:
                                avant = len(game.past)
                                minmax_nim_play(game, verbose=False)
                                self.assertEqual(len(game.past), avant + 1)  # un coup permis
                            else:
                                game.play(*rng.choice(game.get_moves()))
                        self.assertEqual(game.win, prof, (cls.__name__, tas, prof, seed))

    def test_ne_joue_que_des_coups_permis(self):
        for cls in (Nim, NimMisere):
            for tas in itertools.product(range(4), repeat=3):
                if not any(tas):
                    continue
                game = cls()
                game.set_game_state(list(tas), "X")
                coup = meilleur_coup(game.get_game_state(), cls.MISERE)
                self.assertIn(coup, game.get_moves())
                self.assertIsNot(game.play(*coup), False)


class MastermindTest(unittest.TestCase):
    def setUp(self):
        self.game = Mastermind(0)
        self.game.set_secret(4, 4, 1)

    def test_reponse(self):
        self.assertEqual(reponse((4, 4, 1), (1, 2, 3)), (0, 1))
        self.assertEqual(reponse((4, 4, 1), (4, 1, 4)), (1, 2))
        self.assertEqual(reponse((4, 4, 1), (4, 4, 4)), (2, 0))  # chaque chiffre du secret compte une fois
        self.assertEqual(reponse((1, 2, 3), (3, 1, 2)), (0, 3))

    def test_graine_reproductible(self):
        secrets = []
        for _ in range(2):
            game = Mastermind(0)
            game.init()
            secrets.append(game.secret)
        self.assertEqual(secrets, [(4, 4, 1), (4, 4, 1)])
        self.assertNotEqual(Mastermind(1).secret, (4, 4, 1))

    def test_le_plateau_ne_montre_pas_le_secret(self):
        plateau = self.game.get_game_state()
        self.assertEqual(plateau, [VIDE] * (ESSAIS * 5))
        plateau = self.game.play(1, 2, 3)
        self.assertEqual(plateau[:5], [1, 2, 3, 0, 1])
        self.assertEqual(plateau[5:], [VIDE] * ((ESSAIS - 1) * 5))
        self.assertEqual(historique(plateau), [((1, 2, 3), (0, 1))])

    def test_propositions_refusees(self):
        for proposition in ((1, 2), (1, 2, 3, 4), (0, 1, 2), (1, 2, 7), (True, 1, 1), ("1", 2, 3), (1.0, 2, 3)):
            self.assertIs(self.game.play(*proposition), False, proposition)
        self.assertEqual(self.game.nb_turn, 0)
        self.assertEqual(self.game.get_game_state(), [VIDE] * (ESSAIS * 5))

    def test_gagnee(self):
        self.game.play(1, 2, 3)
        self.assertIs(self.game.play(4, 4, 1), True)
        self.assertEqual(self.game.win, "X")
        self.assertEqual(self.game.get_turn(), "X")
        self.assertIs(self.game.play(4, 4, 1), False)  # partie terminée

    def test_perdue_apres_le_dernier_essai(self):
        for _ in range(ESSAIS - 1):
            self.assertIsInstance(self.game.play(1, 1, 1), list)
        self.assertIs(self.game.play(1, 1, 1), True)
        self.assertEqual(self.game.win, "O")

    def test_back(self):
        self.game.play(1, 2, 3)
        avant = self.game.get_game_state()
        self.game.play(4, 4, 1)
        self.assertEqual(self.game.back(), avant)
        self.assertEqual(self.game.win, "")
        self.assertEqual(self.game.nb_turn, 1)
        self.assertEqual(self.game.secret, (4, 4, 1))  # back ne change pas le secret
        self.assertEqual(self.game.back(), [VIDE] * (ESSAIS * 5))
        self.assertEqual(self.game.back(), [VIDE] * (ESSAIS * 5))  # rien à annuler

    def test_get_game_state_relance_une_partie_finie(self):
        self.game.play(4, 4, 1)
        self.assertEqual(self.game.get_game_state(), [VIDE] * (ESSAIS * 5))
        self.assertEqual(self.game.win, "")

    def test_play_text(self):
        self.assertIsInstance(self.game.play_text("123"), list)
        self.assertIs(self.game.play_text("12a"), False)


class MinmaxMastermindTest(unittest.TestCase):
    def jouer_tous_les_secrets(self, prof) -> list:
        game = Mastermind(0)
        essais = []
        for secret in tous_les_codes():
            game.set_secret(*secret)
            while not game.win:
                avant = game.nb_turn
                prof(game, verbose=False)
                self.assertEqual(game.nb_turn, avant + 1)  # une proposition permise
            self.assertEqual(game.win, "X", secret)
            essais.append(game.nb_turn)
        return essais

    def test_le_professeur_trouve_tout_en_5_essais_au_plus(self):
        essais = self.jouer_tous_les_secrets(minmax_mastermind_play)
        self.assertEqual(len(essais), 216)
        self.assertLessEqual(max(essais), 5)
        self.assertEqual(sum(essais), 874)  # 4,05 essais en moyenne

    def test_premier_compatible_tient_dans_la_limite(self):
        essais = self.jouer_tous_les_secrets(premier_compatible_play)
        self.assertLessEqual(max(essais), ESSAIS)

    def test_ne_lit_pas_le_secret(self):
        """Deux secrets différents, même plateau : même proposition."""
        coups = []
        for secret in ((4, 4, 1), (4, 1, 1)):
            game = Mastermind(0)
            game.set_secret(*secret)
            game.play(1, 2, 3)  # (0, 1) pour les deux
            game.play(4, 5, 6)  # (1, 0) pour les deux
            coups.append(meilleur_code(historique(game.get_game_state()), 3, 6))
            self.assertEqual(historique(game.get_game_state()), [((1, 2, 3), (0, 1)), ((4, 5, 6), (1, 0))])
        self.assertEqual(coups[0], coups[1])


class ExemplesTest(unittest.TestCase):
    def test_exemple_nim(self):
        game = rejouer("exampleNim.py")["game"]
        self.assertEqual(game.win, "X")

    def test_exemple_nim_misere(self):
        game = rejouer("exampleNimMisere.py")["game"]
        self.assertEqual(game.win, "O")

    def test_exemple_mastermind(self):
        game = rejouer("exampleMastermind.py")["game"]
        self.assertEqual(game.win, "X")
        self.assertEqual(game.nb_turn, 6)


if __name__ == "__main__":
    unittest.main()
