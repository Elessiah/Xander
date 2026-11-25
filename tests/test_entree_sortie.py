"""Problèmes « entrée -> sortie » : format, briques, recherche, fils, mesure."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from xander import briques, fils_repondeur, mesure, transformations
from xander.__main__ import main
from xander.problemes import ProblemeMalForme, lire_problemes, lire_texte
from xander.transformations import comprendre

PROBLEMES = Path(__file__).resolve().parent.parent / "res" / "problemes"
ENTRAINEMENT = PROBLEMES / "entrainement"
INEDITS = PROBLEMES / "inedits"


def _lot(dossier: Path) -> list:
    return [p for f in sorted(dossier.glob("*.json")) for p in lire_problemes(f)]


class FormatTest(unittest.TestCase):
    UN = json.dumps({
        "nom": "envers", "domaine": "mots", "enonce": "à l'envers",
        "paires": [{"entree": "ab", "sortie": "ba"}, {"entree": "abc", "sortie": "cba"}],
        "questions": [{"entree": "xyz", "sortie": "zyx"}, {"entree": "uv"}],
    })

    def test_un_probleme(self):
        (p,) = lire_texte(self.UN)
        self.assertEqual(p.nom, "envers")
        self.assertEqual(p.paires, [("ab", "ba"), ("abc", "cba")])
        self.assertEqual(p.questions, ["xyz", "uv"])
        self.assertEqual(p.attendues, ["zyx", None])

    def test_la_mere_ne_recoit_pas_les_reponses(self):
        (p,) = lire_texte(self.UN)
        paires, questions = p.enonce_pour_la_mere()
        self.assertEqual(questions, ["xyz", "uv"])
        self.assertNotIn("zyx", json.dumps([paires, questions]))

    def test_un_lot(self):
        texte = json.dumps({"domaine": "nombres", "problemes": [
            {"nom": "a", "paires": [{"entree": 1, "sortie": 2}]},
            {"nom": "b", "domaine": "autre", "paires": [{"entree": [1, [2, 3]], "sortie": True}]}]})
        a, b = lire_texte(texte)
        self.assertEqual((a.domaine, b.domaine), ("nombres", "autre"))
        self.assertEqual(b.paires, [([1, [2, 3]], True)])
        self.assertIsNone(a.attendues)

    def test_forme_commune(self):
        (p,) = lire_texte(self.UN)
        self.assertEqual(p.en_observations()[0], {"etat": "ab", "action": None, "joueur": None, "suivant": "ba"})

    def test_erreurs(self):
        mauvais = [
            "pas du json",
            json.dumps({"paires": []}),
            json.dumps({"paires": [{"entree": 1}]}),
            json.dumps({"paires": [{"entree": None, "sortie": 1}]}),
            json.dumps({"paires": [{"entree": {"a": 1}, "sortie": 1}]}),
            json.dumps({"paires": [{"entree": 1, "sortie": 1}], "questions": [{"sortie": 1}]}),
            json.dumps({"paires": [{"entree": 1, "sortie": 1}], "indice": "tricher"}),
            json.dumps({"problemes": [{"nom": "a", "paires": [{"entree": 1, "sortie": 1}]},
                                      {"nom": "a", "paires": [{"entree": 1, "sortie": 1}]}]}),
        ]
        for texte in mauvais:
            with self.subTest(texte=texte), self.assertRaises(ProblemeMalForme):
                lire_texte(texte)

    def test_les_fichiers_du_depot_se_lisent(self):
        for f in sorted(PROBLEMES.rglob("*.json")):
            with self.subTest(fichier=f.name):
                for p in lire_problemes(f):
                    self.assertGreaterEqual(len(p.paires), 2)
                    self.assertTrue(p.questions)
                    self.assertIsNotNone(p.attendues)


class BriquesTest(unittest.TestCase):
    def test_un_texte_est_une_suite_de_lettres(self):
        self.assertEqual(briques.inverser("abc"), "cba")
        self.assertEqual(briques.trier("chat"), "acht")
        self.assertEqual(briques.garder(lambda e: e != " ", "a b"), "ab")
        self.assertEqual(briques.couper("le chat", " "), ["le", "chat"])
        self.assertEqual(briques.chaque(briques.longueur, ["ab", "c"]), [2, 1])
        self.assertEqual(briques.positions("banane", "n"), [2, 4])

    def test_listes(self):
        self.assertEqual(briques.couper([1, 0, 2, 3, 0], 0), [[1], [2, 3], []])
        self.assertEqual(briques.compter([[1], [1], 1], [1]), 2)
        self.assertEqual(briques.element([4, 5, 6], 2), 6)
        self.assertEqual(briques.somme([1, 2.5]), 3.5)

    def test_types_distincts(self):
        self.assertFalse(briques.egal(1, True))
        self.assertFalse(briques.egal(1, "1"))
        self.assertEqual(briques.compter([1, True, 1.0], 1), 1)

    def test_indefini(self):
        for appel in (lambda: briques.premier([]), lambda: briques.longueur(3), lambda: briques.somme("ab"),
                      lambda: briques.element([1, 2], 2), lambda: briques.element([1, 2], -1),
                      lambda: briques.plus(1, True), lambda: briques.non(0),
                      lambda: briques.trier([1, "a"]), lambda: briques.garder(lambda e: e, [1, 2])):
            with self.assertRaises(briques.Indefini):
                appel()


class RechercheTest(unittest.TestCase):
    def test_le_plus_petit_programme(self):
        c = comprendre([("chat", "tahc"), ("lune", "enul")], ["rose"])
        self.assertEqual(repr(c.essais[0]), "sortie = inverser(x)")
        self.assertEqual(c.essais[0].reponses, ["esor"])

    def test_fonction_de_l_element(self):
        c = comprendre([([1, 2], [2, 3]), ([5], [6]), ([0, 9, 3], [1, 10, 4])], [[7, 7]])
        self.assertEqual(repr(c.essais[0].programme), "chaque(plus(e, 1), x)")
        self.assertEqual(c.essais[0].reponses, [[8, 8]])

    def test_deuxieme_essai_reellement_different(self):
        # Le dernier, ou le plus grand ? Les paires ne départagent pas, la question si.
        c = comprendre([([1, 2, 3], 3), ([4, 5, 6], 6)], [[9, 8, 7]])
        premier, deuxieme = c.essais
        self.assertLessEqual(premier.taille, deuxieme.taille)
        self.assertNotEqual(premier.reponses, deuxieme.reponses)
        self.assertEqual(sorted([premier.reponses[0], deuxieme.reponses[0]]), [7, 9])

    def test_pas_de_deuxieme_essai_sans_autre_reponse(self):
        c = comprendre([(3, 4), (10, 11), (0, 1)], [41])
        self.assertEqual(len(c.essais), 1)

    def test_une_paire_ne_suffit_pas(self):
        c = comprendre([("chat", "tahc"), ("chat", "tahc")], ["rose"])
        self.assertFalse(c.comprise)
        self.assertIn("au moins 2 paires", c.raison)

    def test_paires_contradictoires(self):
        c = comprendre([(1, 2), (1, 3), (4, 5)], [6])
        self.assertFalse(c.comprise)

    def test_elle_n_invente_pas(self):
        c = comprendre([(2, 5), (3, 1), (4, 8), (7, 3)], [5], max_taille=3)
        self.assertFalse(c.comprise)
        self.assertIn("taille 3 au plus", c.raison)
        self.assertIn("ne trouve pas", c.decrire())

    def test_budget(self):
        c = comprendre([(2, 5), (3, 1), (4, 8), (7, 3)], [5], max_programmes=10)
        self.assertFalse(c.comprise)
        self.assertIn("budget", c.raison)

    def test_constantes_remarquees(self):
        consts = transformations.constantes([("a-b", "a"), ("c-d", "c"), ("e-f", "e")])
        self.assertEqual(consts[:3], (0, 1, "-"))

    def test_evaluer_comme_la_recherche(self):
        c = comprendre([("le chat", ["l", "c"]), ("un deux trois", ["u", "d", "t"])], ["il pleut"])
        programme = c.essais[0].programme
        self.assertEqual(transformations.evaluer(programme, "il pleut"), c.essais[0].reponses[0])


class FilsTest(unittest.TestCase):
    def setUp(self):
        self.paires = [([1, 2, 3], 3), ([4, 5, 6], 6)]
        self.comprehension = comprendre(self.paires, [[9, 8, 7]])
        self.code = fils_repondeur.source("dernier", self.comprehension, [[9, 8, 7]])

    def test_autonome_et_minimal(self):
        self.assertNotIn("xander", self.code)
        self.assertIn("def repondre(x)", self.code)
        self.assertIn("def deuxieme_essai(x)", self.code)
        utilisees = set()
        for essai in self.comprehension.essais:
            utilisees |= essai.programme.briques()
        for brique in transformations.BRIQUES:
            self.assertEqual(f"def {brique.nom}(" in self.code, brique.nom in utilisees, brique.nom)

    def test_il_explique_les_paires(self):
        self.assertEqual(fils_repondeur.verifier(self.code, self.paires), [])
        self.assertTrue(fils_repondeur.verifier(self.code, [([1, 2], 1)]))

    def test_il_repond_seul(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "fils.py"
            chemin.write_text(self.code, encoding="utf-8")
            sortie = subprocess.run([sys.executable, "-I", str(chemin)], capture_output=True, text=True,
                                    encoding="utf-8", check=True).stdout
            self.assertEqual(sortie.strip(), f"[9, 8, 7] -> {self.comprehension.essais[0].reponses[0]}")
            sortie = subprocess.run([sys.executable, "-I", str(chemin), '"abc"'], capture_output=True,
                                    text=True, encoding="utf-8", check=True).stdout
            self.assertIn("->", sortie)

    def test_pas_de_fils_sans_comprehension(self):
        with self.assertRaises(ValueError):
            fils_repondeur.source("rien", comprendre([(1, 2)], [3]), [3])


class LigneDeCommandeTest(unittest.TestCase):
    def test_un_probleme(self):
        sortie = io.StringIO()
        with contextlib.redirect_stdout(sortie):
            code = main([str(ENTRAINEMENT / "mots.json"), "--probleme", "initiales"])
        self.assertEqual(code, 0)
        self.assertIn("chaque(premier(e), couper(x, \" \"))", sortie.getvalue())
        self.assertIn("Le fils répond", sortie.getvalue())
        self.assertIn("Score : 1/1", sortie.getvalue())

    def test_fichier_mal_forme(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "faux.json"
            chemin.write_text('{"paires": []}', encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main([str(chemin)]), 1)


class EntrainementTest(unittest.TestCase):
    """Les problèmes d'entraînement : ce qui a servi à choisir les briques et les réglages."""

    #: Pas encore à sa portée : il faudrait voir des lignes, ou un « si ». Elle doit le dire.
    HORS_DE_PORTEE = {"qui-a-trois-pions-alignes", "a-qui-le-tour"}

    @classmethod
    def setUpClass(cls):
        cls.bilan = mesure.passer(_lot(ENTRAINEMENT))

    def test_score(self):
        rates = {r.probleme.nom for r in self.bilan.notes if not r.premier_essai}
        # Au premier essai, elle prend la coïncidence « compter les a » ; le deuxième essai corrige.
        self.assertEqual(rates, self.HORS_DE_PORTEE | {"combien-de-fois-cette-lettre"})
        self.assertEqual(self.bilan.deux_essais, len(self.bilan.notes) - len(self.HORS_DE_PORTEE))

    def test_elle_n_invente_pas(self):
        for r in self.bilan.resultats:
            if r.probleme.nom in self.HORS_DE_PORTEE:
                self.assertFalse(r.comprehension.comprise, r.probleme.nom)
                self.assertIsNone(r.code)

    def test_rapide(self):
        for r in self.bilan.resultats:
            self.assertLess(r.comprehension.duree, 5.0, r.probleme.nom)

    def test_chaque_brique_est_justifiee_par_deux_domaines(self):
        """Une brique de l'équipement de naissance sert dans au moins deux domaines différents."""
        domaines: dict = {}
        for r in self.bilan.resultats:
            if r.premier_essai:
                for nom in r.comprehension.essais[0].programme.briques():
                    domaines.setdefault(nom, set()).add(r.probleme.domaine)
        for brique in transformations.BRIQUES:
            with self.subTest(brique=brique.nom):
                self.assertGreaterEqual(len(domaines.get(brique.nom, ())), 2, domaines.get(brique.nom))


if __name__ == "__main__":
    unittest.main()
