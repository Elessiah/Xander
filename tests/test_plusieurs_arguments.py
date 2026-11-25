"""Des actions à plusieurs arguments, et ce qu'elles écrivent.

Trois jeux du dépôt ont une action à plusieurs arguments : le Nim
(``play(tas, nombre)``, deux joueurs), les Tours de Hanoï
(``play(depart, arrivee)``, un joueur) et le Compte est bon
(``play(i, j, op)``, un joueur). Rien dans ``xander/`` n'est propre à l'un d'eux :
la mère découvre les actions argument par argument, décrit **ce que l'action
écrit** par un petit programme, déduit **quand un coup est permis** des coups
joués et refusés, et comprend une fin par l'état où elle arrive (deux fins au
même signal, à Hanoï). Les descriptions attendues sont écrites ici pour
comparer ; elles ne sont jamais données à la mère.
"""

import functools
import itertools
import random
import unittest
from pathlib import Path

from Games.CompteEstBon import CompteEstBon
from Games.Hanoi import Hanoi
from Games.MinmaxNim import minmax_nim_play, valeur
from Games.Nim import Nim
from Games.NimMisere import NimMisere
from xander import effets, son_writer
from xander.mother import Mother, render_son

RES = Path(__file__).resolve().parent.parent / "res"


@functools.lru_cache(maxsize=None)
def eleve(exemple: str, parties: int, professeur: bool = False):
    """Une éducation partagée par les tests qui ne font que la regarder."""
    return Mother().raise_son(RES / exemple, minmax_nim_play if professeur else None, parties)


def cas_joues(fabrique, actions, parties=30, coups=40, graine=0):
    """Des coups joués au hasard dans le vrai jeu : (avant, arguments, après) ; un coup refusé
    laisse l'état tel quel (comme dans le labo)."""
    rng, cas = random.Random(graine), []
    for _ in range(parties):
        jeu = fabrique()
        for _ in range(coups):
            avant = jeu.get_game_state()
            arguments = rng.choice(actions)
            resultat = jeu.play(*arguments)
            if resultat is True:
                break
            apres = jeu.get_game_state()
            cas.append(effets.Cas(avant, arguments, apres))
            if getattr(jeu, "finie", False):
                break
    return cas


def nim():
    jeu = Nim()
    jeu.init("X")
    return jeu


ACTIONS_NIM = [(i, n) for i in range(3) for n in range(1, 6)]
ACTIONS_HANOI = [(a, b) for a in range(3) for b in range(3)]
ACTIONS_CEB = [(i, j, op) for i in range(4) for j in range(4) for op in range(4)]


class EffetsTest(unittest.TestCase):
    """Ce que la mère sait décrire, sur des coups joués dans le vrai jeu."""

    def comprendre(self, fabrique, actions):
        cas = cas_joues(fabrique, actions)
        joues = [c for c in cas if c.valeur_apres != c.valeur_avant]
        portees = effets.portees_observees(cas)
        effet = effets.decouvrir(joues, portees=portees)[0]
        ecrits = effets.ecritures(effet, [(c, None) for c in joues], portees)
        condition = effets.liberte_valeurs(effet, ecrits, cas, portees)
        return cas, portees, effet, ecrits, condition

    def verifier(self, cas, portees, effet, ecrits, condition):
        """La mère prévoit chaque coup vu (l'état d'après, ou « pas un coup ») et le fils, écrit
        par elle, prévoit exactement la même chose."""
        espace = {"PORTEES": portees}
        exec(effets.AIDES_SOURCE + "\n" + effets.source_prevision(effet, ecrits, condition), espace)
        for c in cas:
            attendu = None if c.valeur_apres == c.valeur_avant else tuple(c.valeur_apres)
            prevu = effets.prevoir(effet, ecrits, c.valeur_avant, c.arguments, portees, condition)
            self.assertEqual(prevu, attendu, c)
            self.assertEqual(espace["valeur_apres"](c.valeur_avant, c.arguments), prevu)

    def test_nim(self):
        cas, portees, effet, ecrits, condition = self.comprendre(nim, ACTIONS_NIM)
        self.assertEqual(effet, effets.Hypothese(effets.CHANGEES, effets.case(effets.arg(0))))
        # le tas perd ce qu'on y prend
        self.assertEqual(ecrits, [(effets.case(effets.arg(0)),
                                   ("programme", effets.moins(effets.ici(), effets.arg(1))))])
        self.assertEqual(repr(condition), "non inf(ici, arg1)")  # on ne prend pas plus qu'il n'y a
        self.verifier(cas, portees, effet, ecrits, condition)

    def test_hanoi(self):
        cas, portees, effet, ecrits, condition = self.comprendre(lambda: Hanoi(3), ACTIONS_HANOI)
        # la portée se range par argument : partir du piquet 0 déplace le petit disque, puis le moyen…
        self.assertEqual(portees[(0, 0)], [0, 1, 2])
        dessus = effets.premiere_de(effets.portee(effets.arg(0)), effets.valant(effets.arg(0)))
        self.assertEqual(effet, effets.Hypothese(effets.CHANGEES, dessus))
        self.assertEqual(ecrits, [(dessus, ("argument", 1))])  # le disque va sur le piquet d'arrivée
        # jamais sur un plus petit : le premier disque du piquet d'arrivée ne vient pas avant lui
        self.assertEqual(repr(condition), "non inf(premiere_de(portee(arg0), valant(arg1)), cellule)")
        self.verifier(cas, portees, effet, ecrits, condition)

    def test_compte_est_bon(self):
        cas, portees, effet, ecrits, condition = self.comprendre(lambda: CompteEstBon(2), ACTIONS_CEB)
        # 5 × 1 laisse 5 à sa place : les cases écrites, pas seulement celles qui changent
        self.assertEqual(effet.forme, effets.ECRITES)
        self.assertEqual(effet.terme, effets.union(effets.case(effets.arg(0)), effets.case(effets.arg(1))))
        (place, resultat), (vide, zero) = ecrits
        self.assertEqual(zero, ("constante", 0))
        self.assertEqual(resultat[:2], ("selon", 2))  # l'opération est choisie par arg2
        operations = {v: d[1].kind for v, d in resultat[2]}
        self.assertEqual(operations, {0: "plus", 1: "moins", 2: "fois", 3: "divise"})
        self.assertIsNotNone(condition)
        self.verifier(cas, portees, effet, ecrits, condition)

    def test_selon_ne_garde_pas_un_groupe_vu_une_fois(self):
        def ecrit(a, b, op, valeur):
            return effets.Ecrit([a, b], (0, 1, op), 0, valeur), None
        ecrits = [ecrit(2, 3, 0, 5), ecrit(4, 1, 0, 5), ecrit(2, 3, 1, -1), ecrit(5, 1, 1, 4), ecrit(3, 3, 2, 9)]
        sorte, k, table = effets.decrire_ecriture(ecrits)
        self.assertEqual((sorte, k), ("selon", 2))
        self.assertEqual([v for v, _ in table], [0, 1])  # « 2 » n'a été vu qu'une fois : pas décrit
        moins = effets.moins(effets.ici(), effets.val(effets.arg(1)))
        self.assertEqual(table[1][1], ("programme", moins))
        self.assertIs(effets.valeur_ecrite(("selon", k, table), [3, 3], (0, 1, 2), 0), effets.INDEFINI)

    def test_une_condition_hors_de_portee_est_dite(self):
        """Un coup refusé que rien dans son langage ne distingue des coups joués : la mère ne
        l'invente pas, elle dit qu'elle ne sait pas."""
        effet = effets.Hypothese(effets.CHANGEES, effets.case(effets.arg(0)))
        ecrits = [(effets.case(effets.arg(0)), ("constante", "x"))]
        joue = effets.Cas([".", "."], (0,), ["x", "."])
        joue_aussi = effets.Cas([".", "."], (1,), [".", "x"])
        refuse = effets.Cas([".", "."], (0,), [".", "."])  # le même coup, refusé cette fois
        self.assertIsNone(effets.liberte_valeurs(effet, ecrits, [joue, joue_aussi, refuse]))


class DecouverteTest(unittest.TestCase):
    def test_actions_du_nim(self):
        education = eleve("exampleNim.py", 0, True)
        actions = education.knowledge["actions"]
        self.assertTrue(all(isinstance(a, tuple) and len(a) == 2 for a in actions))
        # tas 0 à 2, de 1 au plus gros tas ; jamais (0, 4) : le tas 0 n'a jamais plus de 3 objets
        self.assertEqual(set(actions), {(t, n) for t, taille in enumerate((3, 4, 5)) for n in range(1, taille + 1)})

    def test_actions_de_hanoi(self):
        self.assertEqual(eleve("exampleHanoi.py", 0).knowledge["actions"],
                         [(a, b) for a in range(3) for b in range(3) if a != b])


class NimTest(unittest.TestCase):
    """Deux joueurs, un tableau sans pions : la position porte le trait, la fin est un état."""

    def test_comprend_la_fin(self):
        self.assertEqual(eleve("exampleNim.py", 0, True).knowledge["ends"], {(0, 0, 0): "dernier"})
        self.assertEqual(eleve("exampleNimMisere.py", 0, True).knowledge["ends"], {(0, 0, 0): "trait"})

    def test_education(self):
        education = eleve("exampleNim.py", 30, True)
        self.assertFalse(education.tableau)
        self.assertTrue(education.liste)
        parties = [r for r in education.records if r.number > 0]
        self.assertFalse([r for r in parties if r.number > 5 and r.impossibles])  # le fils ne triche pas
        self.assertTrue(education.knowledge["rules"])                               # des règles construites
        self.assertLessEqual(education.max_views, 1000)                             # budget de réflexion
        # les souvenirs retiennent une action complète
        self.assertTrue(all(isinstance(a, tuple) for a in education.knowledge["memories"].values()))

    def test_le_fils_joue_le_vrai_jeu(self):
        """Le fils écrit par la mère joue un coup par tour, sans essai, et bat le hasard."""
        fils = son_writer.load(render_son("nim", eleve("exampleNim.py", 30, True)))
        rng, gagnees = random.Random(0), 0
        for partie in range(40):
            jeu = Nim()
            jeu.init("X")
            cote = "XO"[partie % 2]
            while not jeu.win:
                if jeu.get_turn() == cote:
                    fils.play(jeu)  # lève une erreur si le jeu refuse son coup
                else:
                    jeu.play(*rng.choice(jeu.get_moves()))
            gagnees += jeu.win == cote
        self.assertGreaterEqual(gagnees, 36)

    def test_gagne_en_premier_contre_le_professeur(self):
        fils = son_writer.load(render_son("nim", eleve("exampleNim.py", 30, True)))
        jeu = Nim()
        jeu.init("X")
        while not jeu.win:
            fils.play(jeu) if jeu.get_turn() == "X" else minmax_nim_play(jeu, verbose=False)
        self.assertEqual(jeu.win, "X")

    def test_misere(self):
        education = eleve("exampleNimMisere.py", 30, True)
        self.assertFalse([r for r in education.records if r.number > 5 and r.impossibles])
        fils = son_writer.load(render_son("nim", education))
        jeu = NimMisere()
        jeu.init("X")
        while not jeu.win:  # en premier, contre le professeur : la position de départ est gagnable
            fils.play(jeu) if jeu.get_turn() == "X" else minmax_nim_play(jeu, verbose=False)
        self.assertTrue(valeur([3, 4, 5], misere=True))
        self.assertEqual(jeu.win, "X")


class HanoiTest(unittest.TestCase):
    """Un joueur seul, deux fins au même signal (``True`` : gagnée ou limite atteinte)."""

    def test_fin_comprise_par_son_etat(self):
        education = eleve("exampleHanoi.py", 0)
        self.assertEqual(education.knowledge["fins"], {(2, 2, 2): "gagnée"})
        # la limite atteinte ailleurs n'est pas une victoire
        lab = education.lab
        lab.goto([])
        for k in range(14):  # le petit disque va et vient : la limite de 14 coups est atteinte
            lab.play(*((0, 1) if k % 2 == 0 else (1, 0)))
        self.assertTrue(lab.ended)
        self.assertEqual(education.end_kind(), "inconnue")
        lab.goto([])

    def test_le_fils_range_la_pile(self):
        education = eleve("exampleHanoi.py", 30)
        parties = [r for r in education.records if r.number > 0]
        self.assertFalse([r for r in parties if r.number > 5 and r.impossibles])
        self.assertTrue(all(r.result.startswith("gagnée") for r in parties[-10:]))
        fils = son_writer.load(render_son("hanoi", education))
        jeu, coups = Hanoi(3), 0
        while not jeu.finie:
            fils.play(jeu)
            coups += 1
        self.assertEqual((jeu.win, coups), ("J", 7))  # le minimum

    def test_jamais_sur_un_plus_petit(self):
        """Le fils ne propose que des coups permis, depuis chacune des 27 positions. (Il peut en
        ignorer : la portée d'une action vient de ce que la mère a vu, et le labo n'a pas montré
        partout le grand disque partir de chaque piquet.)"""
        fils = son_writer.load(render_son("hanoi", eleve("exampleHanoi.py", 30)))
        vus = permis = 0
        for etat in itertools.product(range(3), repeat=3):
            jeu = Hanoi(3)
            jeu.set_game_state(list(etat))
            proposes = set(fils.possibles(list(etat)))
            self.assertLessEqual(proposes, set(jeu.get_moves()), etat)
            vus, permis = vus + len(proposes), permis + len(jeu.get_moves())
        self.assertGreaterEqual(vus, permis * 3 // 4)


class CompteEstBonTest(unittest.TestCase):
    def test_education(self):
        education = eleve("exampleCompteEstBon.py", 10)
        self.assertEqual(education.knowledge["fins"], {(0, 0, 85, 0, 85): "gagnée"})
        parties = [r for r in education.records if r.number > 0]
        self.assertFalse([r for r in parties if r.number > 5 and r.impossibles])
        self.assertTrue(parties[-1].result.startswith("gagnée"))
        # une partie perdue (il ne reste qu'un nombre) se voit : la position est bloquée
        self.assertTrue(any(r.result.startswith("bloquée") for r in parties))

    def test_coups_permis(self):
        """Sur le tirage du labo, le fils propose exactement les coups permis."""
        fils = son_writer.load(render_son("ceb", eleve("exampleCompteEstBon.py", 10)))
        jeu = CompteEstBon(2)
        jeu.init()
        etat = jeu.get_game_state()
        self.assertEqual(sorted(fils.possibles(etat)), sorted(jeu.get_moves()))


if __name__ == "__main__":
    unittest.main()
