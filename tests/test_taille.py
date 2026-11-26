"""Le rasoir d'Ockham (``xander/taille.py``) : la mère garde le fils le plus court."""

import contextlib
import io
import unittest
from pathlib import Path

from Games.MinmaxAllumettes import minmax_allumettes_play
from xander import bulletin as B
from xander import taille as T
from xander.concepts import MOI, Concept
from xander.mother import Mother

RES = Path(__file__).resolve().parent.parent / "res"


def regle(n: int) -> Concept:
    """Un arbre de ``n`` nœuds (une chaîne de négations sur une feuille)."""
    c = Concept("feuille_de_test", n)
    for _ in range(n - 1):
        c = Concept("non", c)
    return c


class TailleTest(unittest.TestCase):
    def test_un_coup_par_souvenir(self):
        k = {"memories": {"M.A.M.A..": 4, "M?A??????": 1, "7 M": 2}, "rules": [], "concepts": {}}
        self.assertEqual(T.cases(k), 9 + 2 + 1)
        self.assertEqual(T.coups(k), 3)
        self.assertEqual(T.taille(k), 15)
        solo = {"memories": {(0, 1, 2): 0}, "motifs": [({0: 1, 3: 2}, 1)]}
        self.assertEqual(T.taille(solo), (3 + 1) + (2 + 1))

    def test_briques_comptees_une_fois(self):
        base = regle(3)
        k = {"memories": {}, "concepts": {"a": base, "b": Concept("non", Concept("brique", "a", MOI))},
             "rules": ["b"]}
        # « b » (2 nœuds) dépend de la brique « a » (3 nœuds) : la complexité ne s'y cache pas
        self.assertEqual(T.noeuds(["b"], k["concepts"]), 5)
        self.assertEqual(T.noeuds(["a", "b"], k["concepts"]), 5)
        self.assertEqual(T.taille(k), 5)

    def test_le_critere(self):
        souvenirs = {"7 M": 2, "3 M": 2}                       # deux souvenirs : 2 × (1 case + 1 coup)
        avant = {"memories": souvenirs, "rules": [], "concepts": {"r": regle(3), "s": regle(4), "t": regle(5)}}
        sans = {"memories": {}}
        self.assertTrue(T.plus_court(avant, dict(avant, rules=["r"], **sans)))    # 3 < 4 : gardée
        self.assertFalse(T.plus_court(avant, dict(avant, rules=["s"], **sans)))   # 4 = 4 : pas plus court
        self.assertTrue(T.plus_court(avant, dict(avant, rules=["s"], **sans), egalite=True))
        self.assertFalse(T.plus_court(avant, dict(avant, rules=["t"], **sans), egalite=True))  # 5 > 4

    def test_meme_mesure_que_le_bulletin(self):
        with contextlib.redirect_stdout(io.StringIO()):
            e = Mother().raise_son(RES / "exampleAllumettesMisere.py", minmax_allumettes_play, 30)
        self.assertEqual(B.bulletin(e, "misère").taille, T.taille(e.knowledge))
        # Rien de plus court que ce qu'elle sait, à cas égaux : rien à libérer, pas de nouvelle règle
        self.assertFalse(e.shorter(list(e.knowledge["rules"]), []))  # un refactor libère des souvenirs
        # Libérer un souvenir sans rien ajouter raccourcit toujours le fils
        if e.knowledge["memories"]:
            self.assertTrue(e.shorter(list(e.knowledge["rules"]), list(e.knowledge["memories"])[:1]))


if __name__ == "__main__":
    unittest.main()
