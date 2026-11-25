"""L'éducation d'un fils qui joue seul : Partition, puis Jumper.

Pas d'adversaire ni de professeur : la mère juge un coup par ce qui arrive (la
partie finit ou continue), en revenant en arrière dans son labo. Le fils, lui,
ne joue qu'un coup par tour, ne revient jamais en arrière et ne simule rien.
"""

import functools
import unittest
from pathlib import Path

from Games.Jumper import Jumper
from Games.Partition import Partition
from xander import effets, son_writer
from xander.analyzer import analyse
from xander.game_model import GameModel
from xander.lab import Lab
from xander.mother import Mother, render_son
from xander.parser import parse_example
from xander.rebuilder import replay

RES = Path(__file__).resolve().parent.parent / "res"


@functools.lru_cache(maxsize=None)
def trained(example: str, nb_games: int):
    return Mother().raise_son(RES / example, None, nb_games)


class NoBackJumper(Jumper):
    def back(self):
        raise AssertionError("le fils a utilisé back")


def distance(son, game, cap: int) -> int:
    """Coups joués par le fils avant la fin (au plus ``cap``)."""
    for played in range(cap):
        if son.play(game) is False:
            return played + 1
    return cap


def unseen(cls, son, seeds, cap):
    """Distances sur des graines que la mère n'a jamais vues (le labo n'a que celle de l'exemple)."""
    found = []
    for seed in seeds:
        game = cls(seed)
        game.init()
        found.append(distance(son, game, cap))
    return found


class ScrollingTest(unittest.TestCase):
    """L'Analyzer décrit un état qui défile : l'état d'avant, décalé, sauf ce qu'il ne prévoit pas."""

    def test_queue(self):
        """Une file d'attente : chacun avance d'une place, un nouveau arrive au bout."""
        cases = [effets.Cas(list("abcd"), (), list("bcde")), effets.Cas(list("bcde"), (), list("cdef")),
                 effets.Cas(list("cdef"), (), list("defa"))]
        (found,) = effets.decouvrir(cases)
        self.assertEqual((found.d, found.entree, found.mobile, found.fixes), (1, (3,), None, frozenset()))
        self.assertEqual(found.prevoir(list("wxyz")), ("x", "y", "z", effets.INDEFINI))
        self.assertFalse(effets.explique(found, effets.Cas(list("abcd"), (), list("dcba"))))

    def test_jumper_is_described(self):
        """Jumper : le décor défile d'une case ; ce qui entre par le bord n'est pas prévu, le
        coureur (présent une seule fois partout) ne défile pas, et ce qui décide de sa hauteur
        est caché (le même argument l'a fait monter ou descendre)."""
        parsed = parse_example(RES / "exampleJumper.py")
        report = analyse(parsed, replay(parsed))
        (operation,) = report.operations["game.play"]
        found = operation.programme
        self.assertEqual(found.forme, effets.SUITE)
        self.assertEqual((found.d, found.entree, found.mobile, found.fixes), (1, (198, 199), "*", frozenset({159})))
        moves = dict(found.mouvements)
        self.assertGreater(len(moves[False]), 1)  # caché : elle ne prétend pas le prévoir
        self.assertIn("ce qui les décide est caché", repr(found))
        self.assertEqual([f.time for f in report.unknown_calls], [147])  # le dernier coup renvoie False

    def test_partition_is_described(self):
        parsed = parse_example(RES / "examplePartition.py")
        report = analyse(parsed, replay(parsed))
        (operation,) = report.operations["game.play"]
        self.assertEqual(repr(operation.programme),
                         "suite = decale(avant, 1) sauf : ce qui entre par le bord (cases 7 à 7, imprévisible)")

    def test_unchanged_screen_is_a_move(self):
        """Au début de Jumper rien ne bouge à l'écran : le coup est pourtant joué (l'action a renvoyé
        l'écran, comme d'habitude), pas refusé."""
        parsed = parse_example(RES / "exampleJumper.py")
        model = GameModel.from_analysis(parsed, analyse(parsed, replay(parsed)))
        lab = Lab(parsed, model)
        self.assertEqual(lab.play(False), "moved")
        self.assertEqual(lab.states[0], lab.states[1])


class PartitionTest(unittest.TestCase):
    """Le jeu simple : aucun état caché, une erreur se paie tout de suite."""

    def test_learns_to_play_the_notes(self):
        teaching = trained("examplePartition.py", 20)
        self.assertEqual(teaching.knowledge["fin"], "perdue")
        self.assertEqual(teaching.horizon, 1)
        self.assertEqual(teaching.knowledge["motifs"], [({0: "o"}, True)])
        self.assertEqual(teaching.knowledge["memories"], {})
        games = [r for r in teaching.records if r.number > 0]
        self.assertEqual(sum(len(r.lessons) for r in games), 2)
        self.assertTrue(all(not r.lessons for r in games[2:]))
        birth = son_writer.load(son_writer.solo_source("naissance", dict(teaching.knowledge, motifs=[])))
        self.assertLess(max(unseen(Partition, birth, range(1, 21), 500)), 50)
        self.assertEqual(unseen(Partition, teaching.son, range(1, 21), 500), [500] * 20)


class JumperTest(unittest.TestCase):
    def test_learns_to_jump(self):
        """La mère trouve seule « sauter quand un obstacle est juste devant » : deux souvenirs, puis
        un petit motif d'une case. Le fils survit sur des graines qu'il n'a jamais vues."""
        teaching = trained("exampleJumper.py", 10)
        self.assertEqual(teaching.knowledge["fin"], "perdue")
        self.assertEqual(teaching.horizon, 8)  # un saut dure 7 coups, plus un
        self.assertEqual(teaching.knowledge["motifs"], [({162: "T"}, True)])
        self.assertEqual(teaching.knowledge["memories"], {})
        games = [r for r in teaching.records if r.number > 0]
        self.assertEqual([len(r.lessons) for r in games[:3]], [1, 1, 0])
        birth = son_writer.load(son_writer.solo_source("naissance", dict(teaching.knowledge, motifs=[])))
        self.assertLess(max(unseen(Jumper, birth, range(1, 21), 1000)), 100)
        self.assertEqual(unseen(Jumper, teaching.son, range(1, 21), 1000), [1000] * 20)

    def test_son_does_not_cheat(self):
        """Après 5 parties, aucun coup impossible ; le fils ne regarde aucune position à l'avance
        et n'utilise jamais back ; son fichier n'importe rien de Xander."""
        teaching = trained("exampleJumper.py", 10)
        games = [r for r in teaching.records if r.number > 0]
        self.assertEqual(sum(len(r.impossibles) for r in games[5:]), 0)
        self.assertEqual(teaching.max_views, 0)
        source = render_son("jumper", teaching)
        self.assertNotIn("import", source)
        son = son_writer.load(source)
        game = NoBackJumper(3)
        self.assertEqual(distance(son, game, 300), 300)
        self.assertEqual(son.VUES, 0)


if __name__ == "__main__":
    unittest.main()
