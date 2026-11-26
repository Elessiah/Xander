"""Le bulletin du fils (``xander/bulletin.py``) : une mesure qui ne change rien."""

import contextlib
import functools
import io
import unittest
from pathlib import Path

from Games.MinmaxAllumettes import minmax_allumettes_play
from Games.MinmaxMorpion import minmax_morpion_play
from xander import bulletin as B
from xander.__main__ import main
from xander.mother import Mother

RES = Path(__file__).resolve().parent.parent / "res"


@functools.lru_cache(maxsize=None)
def eduquer(exemple: str, professeur=None, parties: int = 30, graine: int = 0):
    with contextlib.redirect_stdout(io.StringIO()):
        return Mother().raise_son(RES / exemple, professeur, parties, seed=graine)


class TailleTest(unittest.TestCase):
    def test_cases_fixees(self):
        self.assertEqual(B.cases_fixees("M.A.M.A.."), 9)       # un souvenir entier
        self.assertEqual(B.cases_fixees("M?A??????"), 2)       # un petit motif : les cases qui comptent
        self.assertEqual(B.cases_fixees("7 M"), 1)             # une valeur et le trait
        self.assertEqual(B.cases_fixees("(3, 4, 5) A"), 3)     # un tuple : chacun de ses termes
        self.assertEqual(B.cases_fixees((0, 1, 2)), 3)         # un état à un joueur


class BulletinMorpionTest(unittest.TestCase):
    """Au Morpion, le fils a compris : des règles qui décident, peu de souvenirs, et il tient
    presque toutes les positions qu'il n'a jamais vues."""

    @classmethod
    def setUpClass(cls):
        cls.education = eduquer("exampleMorpion.py", minmax_morpion_play, 200)
        cls.avant = (repr(cls.education.knowledge), cls.education.source(), cls.education.max_views)
        cls.bulletin = B.bulletin(cls.education, "Morpion")

    def test_ne_change_rien(self):
        e = self.education
        self.assertEqual((repr(e.knowledge), e.source(), e.max_views), self.avant)

    def test_meme_bulletin_deux_fois(self):
        self.assertEqual(B.bulletin(self.education, "Morpion"), self.bulletin)

    def test_compris(self):
        b = self.bulletin
        self.assertEqual(b.cas_bien_joues, b.cas)  # les souvenirs sont les tests : tous tenus
        regles = sum(n for raison, n in b.origine.items() if raison.startswith("règle"))
        self.assertGreater(regles, sum(b.origine.values()) / 2)  # surtout des règles
        tenues, vues = b.generalisation
        self.assertEqual(vues, B.POSITIONS)
        self.assertGreaterEqual(tenues / vues, 0.9)
        self.assertEqual(b.taille, b.noeuds + b.cases_fixees + b.souvenirs + b.petits_motifs)
        self.assertEqual(b.taille, B.taille.taille(self.education.knowledge))  # la mesure de la mère
        self.assertLessEqual(b.budget, 1000)
        for regle, s in b.solidite.items():
            self.assertGreater(s["decide"], 0, regle)  # aucune règle morte (la mère les élague)

    def test_texte(self):
        texte = self.bulletin.decrire()
        for mot in ("Taille", "Compression", "Origine des coups", "Généralisation", "Budget"):
            self.assertIn(mot, texte)


class BulletinHanoiTest(unittest.TestCase):
    """À Hanoï, le fils a retenu un chemin : le bulletin doit le dire (surtout des souvenirs et le
    coup par défaut, des règles qui ne voient le but qu'à deux coups, et une mauvaise
    généralisation)."""

    @classmethod
    def setUpClass(cls):
        cls.education = eduquer("exampleHanoi.py", None, 30)
        cls.bulletin = B.bulletin(cls.education, "Hanoi")

    def test_retenu(self):
        b = self.bulletin
        self.assertLessEqual(b.noeuds, 4)  # « gagner maintenant », « gagner au coup d'après »
        self.assertEqual(b.cas_bien_joues, b.cas)
        regles = {r for r in b.origine if r.startswith("règle ")}
        self.assertEqual({r for r in b.origine if r not in regles}, {"souvenir", "défaut"})
        self.assertGreater(sum(b.origine[r] for r in regles), 0)
        for regle, s in b.solidite.items():
            self.assertGreater(s["decide"], 0, regle)
        tenues, vues = b.generalisation
        self.assertGreater(vues, 10)          # Hanoï à 3 disques : 27 positions, toutes énumérées
        self.assertLess(tenues / vues, 0.5)
        fils, reference = b.victoires          # la mère, elle, sait gagner depuis ces positions
        self.assertGreater(reference, fils)


class StabiliteTest(unittest.TestCase):
    def test_regles_selon_la_graine(self):
        trouvees = B.stabilite(lambda g: eduquer("exampleAllumettes.py", minmax_allumettes_play, 30, g), [0, 1])
        self.assertEqual(set(trouvees), {0, 1})
        for regles in trouvees.values():
            self.assertTrue(all(isinstance(r, str) for r in regles))


class LigneDeCommandeTest(unittest.TestCase):
    def test_option_bulletin(self):
        sortie = io.StringIO()
        with contextlib.redirect_stdout(sortie):
            code = main([str(RES / "exampleHanoi.py"), "--parties", "10", "--bulletin", "-q"])
        self.assertEqual(code, 0)
        self.assertIn("Bulletin du fils (exampleHanoi", sortie.getvalue())


if __name__ == "__main__":
    unittest.main()
