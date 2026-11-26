"""L'éducation d'un fils quand l'état n'est pas un tableau : les Allumettes.

L'état est un nombre (les allumettes qui restent) : pas de cases, pas de pions,
pas de motifs. La mère doit pourtant y apprendre comme au Morpion : comprendre
pourquoi la partie finit, quelles actions sont permises, faire jouer son fils,
garder des souvenirs, puis des règles qu'elle construit elle-même.
"""

import copy
import functools
import unittest
from pathlib import Path

from Games.Allumettes import Allumettes
from Games.AllumettesMisere import AllumettesMisere
from Games.MinmaxAllumettes import minmax_allumettes_play
from xander import concepts, effets, son_writer
from xander.mother import Mother, render_son

RES = Path(__file__).resolve().parent.parent / "res"

#: Ce que la mère doit trouver seule (écrit ici pour comparer, jamais donné à la mère).
RETIRER = effets.Hypothese(effets.APRES, effets.moins(effets.avant(), effets.arg(0)))
#: Budget de réflexion du fils (comme au Morpion).
BUDGET = 1000


@functools.lru_cache(maxsize=None)
def trained(example: str, nb_games: int):
    """Une éducation partagée par les tests qui ne font que la regarder."""
    return Mother().raise_son(RES / example, minmax_allumettes_play, nb_games)


def new_game(cls, start="X"):
    game = cls()
    game.set_max_nb_allumettes(10)
    game.init(start)
    return game


def legal(game) -> list[int]:
    return [a for a in (1, 2, 3) if copy.deepcopy(game).play(a) is not False]


def to_move_wins(game, memo) -> bool:
    """Le joueur qui a le trait peut-il gagner ? (calcul exact sur le vrai jeu, pour vérifier)"""
    key = game.nb_allumettes
    if key not in memo:
        me, memo[key] = game.player, False
        for action in legal(game):
            child = copy.deepcopy(game)
            child.play(action)
            if (child.win == me) if child.win else not to_move_wins(child, memo):
                memo[key] = True
    return memo[key]


def audit(son, cls) -> tuple[list[int], dict]:
    """Toutes les suites de coups adverses, le fils jouant X puis O : les positions gagnables
    où il joue un coup perdant, et le nombre de parties qu'il perd."""
    faults, defeats, memo = set(), {"X": 0, "O": 0}, {}

    def explore(game, side):
        if game.win:
            defeats[side] += game.win != side
            return
        if game.player == side:
            child = copy.deepcopy(game)
            son.play(child)
            if to_move_wins(game, memo) and not (child.win == side or (not child.win and not to_move_wins(child, memo))):
                faults.add(game.nb_allumettes)
            explore(child, side)
        else:
            for action in legal(game):
                child = copy.deepcopy(game)
                child.play(action)
                explore(child, side)

    for side in "XO":
        explore(new_game(cls), side)
    return sorted(faults), defeats


class RefusingAllumettes(Allumettes):
    """Des Allumettes qui refusent tous les coups, et comptent combien on en essaie."""

    calls = 0

    def play(self, *arguments):
        self.calls += 1
        return False


class NoBackAllumettes(Allumettes):
    """Des Allumettes qui interdisent ``back`` : le fils ne doit jamais s'en servir."""

    def back(self):
        raise AssertionError("le fils a utilisé back")


class AllumettesTest(unittest.TestCase):
    def test_perception_of_a_quantity(self):
        """La mère décrit l'action, trouve les actions, les coups permis et la fin de partie ;
        une position est [valeur, trait] : la valeur ne dit pas qui doit jouer."""
        teaching = trained("exampleAllumettes.py", 0)
        knowledge = teaching.knowledge
        self.assertFalse(teaching.tableau)
        self.assertEqual(knowledge["effect"], RETIRER)
        self.assertEqual(knowledge["actions"], [1, 2, 3])  # l'exemple joue 1, 2, 3 ; 4 et 0 refusés
        self.assertEqual(knowledge["free"], ("au_moins", 0))  # déduit d'un coup refusé
        self.assertEqual(knowledge["ends"], {1: "dernier"})
        self.assertIn("fin comprise : la partie finit à la valeur 1", teaching.records[0].patterns[0])
        mind = teaching.mind
        self.assertEqual(mind.possibles([2, "X"]), [1, 2])  # on ne prend pas plus qu'il n'en reste
        self.assertEqual(mind.possibles([1, "O"]), [])     # la partie est finie
        self.assertEqual(mind.apres([7, "X"], 2, "X"), [5, "O"])
        self.assertTrue(mind.gagne([1, "O"], "X"))         # X vient de jouer : il a gagné
        self.assertFalse(mind.gagne([1, "O"], "O"))
        self.assertEqual(mind.cle([7, "X"], "X"), "7 M")

    def test_free_actions_come_from_refusals(self):
        """Ce qui est permis vient de ce qu'elle a vu : sans coup refusé, tout est permis ; un
        coup refusé (rien n'a changé) donne la borne, mesurée sur les coups acceptés."""
        cases = [effets.Cas(5, (1,), 4), effets.Cas(4, (3,), 1)]
        self.assertEqual(effets.bornes(RETIRER, cases), ("toujours",))
        refused = effets.Cas(2, (3,), 2)
        self.assertEqual(effets.bornes(RETIRER, cases + [refused]), ("au_moins", 1))
        self.assertEqual(effets.bornes(RETIRER, cases + [refused], [(2, (2,))]), ("au_moins", 0))
        adding = effets.Hypothese(effets.APRES, effets.plus(effets.avant(), effets.arg(0)))
        self.assertEqual(effets.bornes(adding, [effets.Cas(5, (2,), 7), effets.Cas(7, (2,), 7)]),
                         ("au_plus", 7))

    def test_impossible_move_is_understood(self):
        """Un coup refusé est une observation : la mère réapprend ce qui est permis."""
        teaching = Mother().raise_son(RES / "exampleAllumettes.py", minmax_allumettes_play, 0)
        teaching.knowledge["free"] = ("toujours",)  # perception fausse : tout est permis
        teaching.lab_cases = [c for c in teaching.lab_cases if c.valeur_apres != c.valeur_avant]
        teaching.rethink()
        self.assertIn(3, teaching.mind.possibles([2, "X"]))
        message = teaching.impossible([2, "X"], 3)
        self.assertIn("coup impossible", message)
        self.assertEqual(teaching.knowledge["free"], ("au_moins", 0))
        self.assertNotIn(3, teaching.mind.possibles([2, "X"]))

    def test_mother_builds_her_rules(self):
        """Partie de zéro, elle corrige des souvenirs puis les remplace par une règle qu'elle
        construit : « quoi qu'il joue ensuite, je peux finir à 1 » (laisser 5, ou 1)."""
        teaching = trained("exampleAllumettes.py", 30)
        records = teaching.records[1:]
        self.assertGreater(sum(len(r.lessons) for r in records), 0)  # il a fait des erreurs
        self.assertTrue(any(r.refactors for r in records))
        self.assertTrue(teaching.knowledge["rules"])
        mind = teaching.mind
        for name in teaching.knowledge["rules"]:  # rien que les quatre notions
            self.assertIsInstance(teaching.knowledge["concepts"][name], concepts.Concept)
        self.assertEqual(teaching.decide([7, "X"], "X", teaching.knowledge["rules"]), 2)  # laisser 5
        self.assertEqual(teaching.decide([3, "X"], "X", teaching.knowledge["rules"]), 2)  # laisser 1
        self.assertEqual(mind.possibles([3, "X"]), [1, 2, 3])

    def test_son_never_loses_a_winnable_game(self):
        """Toutes les suites de coups adverses : le fils ne rate aucune position gagnable. En
        premier, il gagne toujours ; en second, il ne perd que si l'adversaire joue
        parfaitement (10 allumettes : le premier joueur gagne)."""
        teaching = trained("exampleAllumettes.py", 30)
        faults, defeats = audit(teaching.son, Allumettes)
        self.assertEqual(faults, [])
        self.assertEqual(defeats, {"X": 0, "O": 1})
        score = teaching.evaluate(20)
        self.assertEqual(score["professeur"], {"victoire": 1, "victoire par défaut": 0, "nul": 0, "défaite": 1})
        self.assertLessEqual(teaching.max_views, BUDGET)

    def test_no_impossible_move_after_five_games(self):
        teaching = trained("exampleAllumettes.py", 30)
        self.assertEqual([r.number for r in teaching.records if r.number > 5 and r.impossibles], [])

    def test_son_never_tries_another_action(self):
        son = son_writer.load(render_son("fils", trained("exampleAllumettes.py", 0)))
        game = RefusingAllumettes()
        game.init("X")
        with self.assertRaisesRegex(RuntimeError, "coup impossible"):
            son.play(game)
        self.assertEqual(game.calls, 1)

    def test_saved_son_plays_against_minmax_without_back(self):
        source = render_son("fils", trained("exampleAllumettes.py", 30))
        self.assertNotIn("xander", source.split('"""', 2)[2])  # fichier autonome
        self.assertNotIn("llumette", source)
        son = son_writer.load(source)
        game = NoBackAllumettes()
        game.set_max_nb_allumettes(10)
        game.init("X")
        while not game.win:
            game.get_game_state()
            if game.get_turn() == "X":
                son.play(game)
            else:
                minmax_allumettes_play(game, verbose=False)
        self.assertEqual(game.win, "X")  # le premier joueur gagne avec 10 allumettes

    def test_misere_a_move_can_lose(self):
        """Misère : celui qui prend la dernière perd. L'exemple le dit (O prend la dernière, X
        gagne) ; la mère comprend que la fin à 0 fait gagner celui qui a le trait, et son fils
        ne rate aucune position gagnable."""
        teaching = trained("exampleAllumettesMisere.py", 30)
        self.assertEqual(teaching.knowledge["ends"], {0: "trait"})
        mind = teaching.mind
        self.assertTrue(mind.gagne([0, "X"], "X"))   # O a pris la dernière : X gagne
        self.assertFalse(mind.gagne([0, "X"], "O"))
        faults, defeats = audit(teaching.son, AllumettesMisere)
        self.assertEqual(faults, [])
        self.assertEqual(defeats, {"X": 0, "O": 1})
        self.assertEqual([r.number for r in teaching.records if r.number > 5 and r.impossibles], [])


if __name__ == "__main__":
    unittest.main()
