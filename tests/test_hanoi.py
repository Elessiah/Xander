import itertools
import unittest
from pathlib import Path

from Games.Hanoi import JOUEUR, Hanoi, apres, coups_permis, limite, minimum
from Games.ProfesseurHanoi import distance, distances, meilleur_coup, professeur_hanoi_play

#: La solution parfaite à 3 disques (7 coups).
PARFAITE_3 = [(0, 2), (0, 1), (2, 1), (0, 2), (1, 0), (1, 2), (0, 2)]


class HanoiTest(unittest.TestCase):
    def setUp(self):
        self.game = Hanoi()

    def test_depart(self):
        self.assertEqual(self.game.init(), [0, 0, 0])
        self.assertEqual(self.game.get_game_state(), [0, 0, 0])
        self.assertEqual(self.game.get_turn(), JOUEUR)
        self.assertEqual((minimum(3), limite(3)), (7, 14))
        self.assertEqual(self.game.get_moves(), [(0, 1), (0, 2)])

    def test_taille_reglable(self):
        self.assertEqual(Hanoi(4).get_game_state(), [0, 0, 0, 0])
        self.game.set_nb_disques(4)
        self.assertEqual(self.game.init(), [0, 0, 0, 0])
        self.assertEqual((minimum(4), limite(4)), (15, 30))
        with self.assertRaises(ValueError):
            Hanoi(0)

    def test_coups_permis(self):
        self.assertEqual(self.game.play(0, 1), [1, 0, 0])   # le petit sur le piquet 1
        self.assertEqual(self.game.play(0, 2), [1, 2, 0])   # le moyen sur le piquet 2
        self.assertEqual(self.game.play(1, 2), [2, 2, 0])   # le petit sur le moyen
        self.assertEqual(self.game.coups, 3)

    def test_coups_refuses(self):
        self.game.play(0, 2)                                # [2, 0, 0]
        refuses = [
            (1, 0),                     # piquet vide
            (0, 2),                     # le moyen sur le petit
            (0, 3), (3, 0), (-1, 2),    # piquets inexistants
            (0, 0),                     # même piquet
            (True, 2), (0, False),      # un booléen n'est pas un piquet
            ("0", "1"), (0.0, 1),
        ]
        for coup in refuses:
            with self.subTest(coup=coup):
                self.assertIs(self.game.play(*coup), False)
                self.assertEqual(self.game.get_game_state(), [2, 0, 0])
                self.assertEqual(self.game.coups, 1)
        self.assertEqual(sorted(self.game.get_moves()), [(0, 1), (2, 0), (2, 1)])

    def test_fin_gagnee(self):
        for coup in PARFAITE_3[:-1]:
            self.assertIsInstance(self.game.play(*coup), list)
            self.assertEqual(self.game.win, "")
        self.assertIs(self.game.play(*PARFAITE_3[-1]), True)
        self.assertTrue(self.game.finie)
        self.assertEqual(self.game.win, JOUEUR)
        self.assertEqual(self.game.get_moves(), [])
        self.assertIs(self.game.play(2, 0), False)          # partie terminée
        self.assertEqual(self.game.get_game_state(), [0, 0, 0])  # relit : nouvelle partie
        self.assertEqual(self.game.win, "")

    def test_fin_perdue(self):
        for k in range(limite(3) - 1):                       # le petit fait des allers-retours
            self.assertIsInstance(self.game.play(*((0, 1) if k % 2 == 0 else (1, 0))), list)
        self.assertIs(self.game.play(1, 0), True)            # 14e coup : la limite
        self.assertTrue(self.game.finie)
        self.assertEqual(self.game.win, "")
        self.assertIs(self.game.play(1, 2), False)

    def test_gagner_au_dernier_coup_permis(self):
        self.game.set_game_state([0, 2, 2], coups=limite(3) - 1)
        self.assertIs(self.game.play(0, 2), True)
        self.assertEqual(self.game.win, JOUEUR)

    def test_back(self):
        self.assertEqual(self.game.back(), [0, 0, 0])        # rien à annuler
        self.game.play(0, 1)
        self.game.play(0, 2)
        self.assertEqual(self.game.back(), [1, 0, 0])
        self.assertEqual(self.game.coups, 1)
        self.assertEqual(self.game.back(), [0, 0, 0])
        self.assertEqual(self.game.coups, 0)
        for coup in PARFAITE_3:
            self.game.play(*coup)
        self.assertEqual(self.game.win, JOUEUR)
        self.assertEqual(self.game.back(), [0, 2, 2])        # annule aussi la fin
        self.assertFalse(self.game.finie)
        self.assertEqual(self.game.win, "")
        self.assertIs(self.game.play(0, 2), True)

    def test_refus_sans_trace(self):
        self.game.play(0, 1)
        self.game.play(1, 1)                                 # refusé : rien à annuler
        self.assertEqual(self.game.back(), [0, 0, 0])

    def test_position_imposee(self):
        self.game.set_game_state([1, 0, 2])
        self.assertEqual(self.game.get_game_state(), [1, 0, 2])
        with self.assertRaises(ValueError):
            self.game.set_game_state([0, 3, 0])

    def test_exemple(self):
        """L'exemple de ``res/`` est une vraie partie, gagnée en 10 coups."""
        source = (Path(__file__).resolve().parent.parent / "res" / "exampleHanoi.py").read_text("utf-8")
        espace: dict = {}
        exec(compile(source, "exampleHanoi.py", "exec"), espace)
        self.assertEqual(espace["game"].win, JOUEUR)
        self.assertEqual(espace["game"].coups, 10)


class ProfesseurHanoiTest(unittest.TestCase):
    def test_distances(self):
        for n in (1, 2, 3, 4):
            with self.subTest(n=n):
                table = distances(n)
                self.assertEqual(len(table), 3 ** n)          # toutes les positions
                self.assertEqual(distance([0] * n), minimum(n))
                self.assertEqual(max(table.values()), minimum(n))
                self.assertEqual(distance([2] * n), 0)

    def test_distances_coherentes(self):
        """Vérification indépendante du parcours : ``d(s) = 1 + min d(voisins)`` hors du but."""
        for n in (3, 4):
            for etat in itertools.product(range(3), repeat=n):
                d = distance(etat)
                if d:
                    voisins = [distance(apres(etat, *c)) for c in coups_permis(etat)]
                    self.assertEqual(d, 1 + min(voisins), etat)

    def test_resout_depuis_toute_position(self):
        """Depuis chaque position, le professeur ne joue que des coups permis et range la pile en
        le nombre minimal de coups."""
        for n in (3, 4):
            game = Hanoi(n)
            for etat in itertools.product(range(3), repeat=n):
                with self.subTest(etat=etat):
                    game.set_game_state(list(etat))
                    attendu, joues = distance(etat), 0
                    if attendu == 0:
                        self.assertIsNone(meilleur_coup(etat))   # déjà rangée : rien à jouer
                        continue
                    while not game.finie:
                        self.assertLess(joues, attendu)
                        coup = meilleur_coup(game.get_game_state())
                        self.assertIn(coup, game.get_moves())
                        professeur_hanoi_play(game, verbose=False)
                        joues += 1
                    self.assertEqual(joues, attendu)
                    self.assertEqual(game.win, JOUEUR)

    def test_partie_parfaite(self):
        game = Hanoi()
        joues = []
        while not game.finie:
            joues.append(meilleur_coup(game.get_game_state()))
            resultat = professeur_hanoi_play(game, verbose=False)
        self.assertIs(resultat, True)
        self.assertEqual(joues, PARFAITE_3)
        self.assertEqual(game.win, JOUEUR)
        self.assertIsNone(meilleur_coup([2, 2, 2]))


if __name__ == "__main__":
    unittest.main()
