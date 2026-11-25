import re
import unittest
from pathlib import Path

from Games.MotMystere import (ABSENTE, AILLEURS, BIEN, ESSAIS, JOUEUR, MOTS, PERSONNE, TAILLE, VIDE,
                              MotMystere, essais, reponse)
from Games.ProfesseurMotMystere import (choisir, compatibles, partie, performances,
                                        professeur_mot_mystere_play)

EXEMPLE = Path(__file__).resolve().parent.parent / "res" / "exampleMotMystere.py"


class DictionnaireTest(unittest.TestCase):
    def test_mots_de_cinq_lettres_sans_accents(self):
        self.assertGreaterEqual(len(MOTS), 300)
        self.assertEqual(len(set(MOTS)), len(MOTS))
        for mot in MOTS:
            self.assertRegex(mot, r"^[a-z]{5}$")

    def test_des_mots_avec_lettres_repetees(self):
        repetees = [m for m in MOTS if len(set(m)) < len(m)]
        self.assertGreaterEqual(len(repetees), 50)


class ReponseTest(unittest.TestCase):
    def test_symboles(self):
        self.assertEqual((BIEN, AILLEURS, ABSENTE, VIDE), ("=", "~", "-", "."))

    def test_lettres_simples(self):
        self.assertEqual(reponse("arbre", "arbre"), "=====")
        self.assertEqual(reponse("porte", "arbre"), "--~-=")
        self.assertEqual(reponse("livre", "arbre"), "---==")
        self.assertEqual(reponse("tigre", "chien"), "-~--~")
        self.assertEqual(reponse("lundi", "pomme"), "-----")

    def test_lettre_repetee_dans_la_proposition(self):
        # un seul r dans le secret : il sert d'abord au r bien placé, l'autre r est absent
        self.assertEqual(reponse("terre", "livre"), "---==")
        # deux r dans le secret : le r bien placé en prend un, le r mal placé l'autre ;
        # un seul e, déjà pris par le e bien placé
        self.assertEqual(reponse("terre", "arbre"), "--~==")
        # deux l proposés, un seul dans le secret : seul le premier reçoit ~
        self.assertEqual(reponse("pelle", "lapin"), "~-~--")

    def test_lettre_repetee_dans_le_secret(self):
        # deux m dans le secret, un seul proposé (mal placé) : ~
        self.assertEqual(reponse("monde", "pomme"), "~=--=")
        # deux m proposés, deux dans le secret : tous deux bien placés
        self.assertEqual(reponse("gomme", "pomme"), "-====")
        self.assertEqual(reponse("somme", "homme"), "-====")

    def test_bien_place_prioritaire_sur_ailleurs(self):
        # le premier e de « pelle » est mal placé, mais le seul e du secret est déjà pris
        # par le e bien placé plus à droite : il est absent
        self.assertEqual(reponse("pelle", "lampe"), "~-~-=")
        self.assertEqual(reponse("bille", "bulle"), "=-===")


class JeuTest(unittest.TestCase):
    def setUp(self):
        self.game = MotMystere(0)
        self.game.set_secret("arbre")

    def test_etat_initial_vide(self):
        etat = self.game.get_game_state()
        self.assertEqual(len(etat), TAILLE)
        self.assertEqual(TAILLE, 60)
        self.assertEqual(set(etat), {VIDE})
        self.assertEqual(self.game.get_turn(), JOUEUR)
        self.assertEqual(self.game.win, "")

    def test_etat_a_plat(self):
        etat = self.game.play("porte")
        self.assertEqual(etat[:10], ["p", "-", "o", "-", "r", "~", "t", "-", "e", "="])
        self.assertEqual(set(etat[10:]), {VIDE})
        etat = self.game.play("livre")
        self.assertEqual(etat[10:20], ["l", "-", "i", "-", "v", "-", "r", "=", "e", "="])
        self.assertEqual(essais(etat), [("porte", "--~-="), ("livre", "---==")])

    def test_etat_ne_contient_pas_le_secret(self):
        # deux secrets qui donnent les mêmes réponses donnent le même état
        autre = next(s for s in MOTS if s != "arbre" and reponse("tenir", s) == reponse("tenir", "arbre"))
        game = MotMystere(0)
        game.set_secret(autre)
        self.assertEqual(game.play("tenir"), self.game.play("tenir"))

    def test_coups_refuses(self):
        self.game.play("porte")
        avant = self.game.get_game_state()
        for coup in ("zzzzz", "arbres", "arb", "ARBRE", "", 12345, True, None, ["arbre"]):
            self.assertIs(self.game.play(coup), False, coup)
            self.assertEqual(self.game.get_game_state(), avant)
        self.assertEqual(self.game.propositions, ["porte"])

    def test_gagnee(self):
        for mot in ("porte", "livre", "barre"):
            self.assertIsInstance(self.game.play(mot), list)
        self.assertIs(self.game.play("arbre"), True)
        self.assertEqual(self.game.win, JOUEUR)
        self.assertIs(self.game.play("table"), False)  # partie terminée

    def test_gagnee_au_premier_essai(self):
        self.assertIs(self.game.play("arbre"), True)
        self.assertEqual(self.game.win, JOUEUR)

    def test_perdue_apres_six_essais(self):
        mots = ["porte", "livre", "barre", "table", "monde", "pomme"]
        for mot in mots[:-1]:
            self.assertIsInstance(self.game.play(mot), list)
        self.assertIs(self.game.play(mots[-1]), True)
        self.assertEqual(self.game.win, PERSONNE)
        self.assertEqual(len(self.game.propositions), ESSAIS)

    def test_gagnee_au_sixieme_essai(self):
        for mot in ["porte", "livre", "barre", "table", "monde"]:
            self.game.play(mot)
        self.assertIs(self.game.play("arbre"), True)
        self.assertEqual(self.game.win, JOUEUR)

    def test_back(self):
        vide = self.game.get_game_state()
        un = self.game.play("porte")
        self.game.play("livre")
        self.assertEqual(self.game.back(), un)
        self.assertEqual(self.game.back(), vide)
        self.assertEqual(self.game.back(), vide)  # rien à annuler

    def test_back_apres_la_fin(self):
        self.game.play("porte")
        avant = self.game.get_game_state()
        self.assertIs(self.game.play("arbre"), True)
        self.assertEqual(self.game.back(), avant)
        self.assertEqual(self.game.win, "")
        self.assertIs(self.game.play("arbre"), True)  # même secret

    def test_get_game_state_relance_apres_la_fin(self):
        self.game.play("arbre")
        etat = self.game.get_game_state()
        self.assertEqual(set(etat), {VIDE})
        self.assertEqual(self.game.win, "")

    def test_graine(self):
        suites = []
        for _ in range(2):
            game = MotMystere(7)
            suites.append([game.secret] + [(game.init(), game.secret)[1] for _ in range(5)])
        self.assertEqual(suites[0], suites[1])
        self.assertGreater(len(set(suites[0])), 1)

    def test_set_secret_refuse_un_mot_inconnu(self):
        with self.assertRaises(ValueError):
            self.game.set_secret("xyzzy")


class Vitre:
    """Le jeu vu à travers une vitre : le professeur n'atteint pas le secret."""

    def __init__(self, game):
        self._game = game

    def get_game_state(self):
        return self._game.get_game_state()

    def get_moves(self):
        return self._game.get_moves()

    def play(self, mot):
        return self._game.play(mot)

    @property
    def win(self):
        return self._game.win


class ProfesseurTest(unittest.TestCase):
    def test_ne_lit_pas_le_secret(self):
        game = MotMystere(3)
        vitre = Vitre(game)
        while not game.win:
            professeur_mot_mystere_play(vitre, verbose=False)
        self.assertEqual(game.win, JOUEUR)

    def test_ne_depend_que_de_l_etat(self):
        a, b = MotMystere(0), MotMystere(0)
        a.set_secret("arbre")
        b.set_secret(next(s for s in MOTS if s != "arbre" and reponse("tenir", s) == reponse("tenir", "arbre")))
        a.play("tenir")
        b.play("tenir")
        self.assertEqual(choisir(a.get_game_state(), MOTS), choisir(b.get_game_state(), MOTS))

    def test_mots_permis_et_compatibles(self):
        for secret in MOTS[::20]:
            game = MotMystere(0)
            game.set_secret(secret)
            while not game.win:
                etat = game.get_game_state()
                mot = choisir(etat, MOTS)
                self.assertIn(mot, MOTS)
                self.assertIn(mot, compatibles(etat, MOTS))
                self.assertIsNot(game.play(mot), False)

    def test_deterministe(self):
        self.assertEqual(partie("pomme"), partie("pomme"))

    def test_trouve_presque_toujours(self):
        resultat = performances()
        self.assertEqual(resultat["secrets"], len(MOTS))
        self.assertGreaterEqual(resultat["taux"], 0.99)
        self.assertLess(resultat["essais_moyens"], 3.5)


class ExempleTest(unittest.TestCase):
    def test_exemple_s_execute(self):
        namespace: dict = {}
        exec(compile(EXEMPLE.read_text(encoding="utf-8"), str(EXEMPLE), "exec"), namespace)
        game = namespace["game"]
        self.assertIs(namespace["fin"], True)
        self.assertEqual(game.win, JOUEUR)
        self.assertEqual(game.propositions, ["porte", "livre", "barre", "arbre"])

    def test_exemple_annonce_la_victoire(self):
        texte = EXEMPLE.read_text(encoding="utf-8")
        self.assertRegex(texte, re.compile(r"^# end player joueur$", re.M))


if __name__ == "__main__":
    unittest.main()
