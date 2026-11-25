"""Le lanceur d'examen blanc, essayé sur un problème inventé et non scellé.

Le problème d'essai reprend le Morpion de ``Games/`` mais passe par un module
posé dans le dossier du problème (comme un jeu sous scellé, hors de
``sys.path``) : on vérifie la plomberie, pas la mère.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from xander import examen
from xander.rebuilder import PROJECT_ROOT

PETIT = examen.Budget(parties=2, limite=300, professeur=2, hasard=4)


def ecrire_probleme(dossier: Path, nom: str = "a-morpion", professeur: bool = True) -> Path:
    probleme = dossier / nom
    probleme.mkdir(parents=True)
    (probleme / "jeu_local.py").write_text("from Games.Morpion import Morpion  # noqa: F401\n", encoding="utf-8")
    exemple = (PROJECT_ROOT / "res" / "exampleMorpion.py").read_text(encoding="utf-8")
    exemple = exemple.replace("from Games.Morpion import Morpion", "from jeu_local import Morpion")
    (probleme / "exemple.py").write_text(exemple, encoding="utf-8")
    if professeur:
        (probleme / "professeur.py").write_text(
            "from Games.MinmaxMorpion import minmax_morpion_play as professeur  # noqa: F401\n", encoding="utf-8")
    return probleme


class TestExamen(unittest.TestCase):
    def setUp(self):
        self.dossier = Path(tempfile.mkdtemp(prefix="examen-essai-"))
        self.addCleanup(shutil.rmtree, self.dossier, ignore_errors=True)

    def test_budget_fixe_avant_l_examen(self):
        self.assertEqual(examen.BUDGET, examen.Budget(parties=200, limite=1800, graine=0, professeur=2,
                                                      hasard=100, rodage=5))

    def test_le_dossier_du_probleme_est_importable_jusque_dans_le_rejeu(self):
        probleme = ecrire_probleme(self.dossier)
        env = examen.environnement(probleme, 0)
        examen.verifier_branchement(probleme, env)
        code = (f"from xander.mother import Mother\n"
                f"e = Mother().raise_son({str(probleme / 'exemple.py')!r}, None, 0)\n"
                f"print(e.model.action.short_name)\n")
        fini = subprocess.run([sys.executable, "-c", code], cwd=PROJECT_ROOT, env=env,
                              capture_output=True, text=True, encoding="utf-8", timeout=300)
        self.assertEqual(fini.returncode, 0, fini.stderr)
        self.assertEqual(fini.stdout.strip().splitlines()[-1], "play")

    def test_examen_complet_et_rapport(self):
        ecrire_probleme(self.dossier, "a-morpion")
        ecrire_probleme(self.dossier, "b-morpion")
        rapport = self.dossier / "rapport.txt"
        sortie = []
        resultats, chemin = examen.passer_examen(self.dossier, PETIT, rapport, sortie.append)
        self.assertEqual(chemin, rapport)
        self.assertEqual([r.numero for r in resultats], [1, 2])
        self.assertTrue(all(r.duree > 0 for r in resultats))
        texte = rapport.read_text(encoding="utf-8")
        for attendu in ("Commit : ", "Date : ", "Budget : 2 parties", "budget réduit",
                        "Problème 1 : ", "Problème 2 : ", "Score : "):
            self.assertIn(attendu, texte)
        self.assertNotIn("morpion", texte.lower())  # rien sur le contenu des problèmes
        self.assertEqual(sortie[-1], f"Rapport écrit dans {rapport}")

    def test_temps_depasse_rate(self):
        ecrire_probleme(self.dossier)
        resultats, _ = examen.passer_examen(self.dossier, examen.Budget(parties=2, limite=0.5),
                                            self.dossier / "r.txt", lambda _: None)
        self.assertFalse(resultats[0].reussi)

    def test_la_mere_ne_sait_pas_eduquer_rate(self):
        probleme = ecrire_probleme(self.dossier)
        # un exemple que la mère comprend mais où l'action ne change aucune case
        (probleme / "exemple.py").write_text(
            "# include\nfrom jeu_local import Morpion\n\n# init\ngame = Morpion()  # game\n"
            "board = game.init(\"X\")  # array 9\n\n# back\nboard = game.back()  # array 9\n\n"
            "# player X\nboard = game.get_game_state()  # array 9\n\n"
            "# player O\nboard = game.get_game_state()  # array 9\n\n# end draw\n", encoding="utf-8")
        resultats, _ = examen.passer_examen(self.dossier, PETIT, self.dossier / "r.txt", lambda _: None)
        self.assertFalse(resultats[0].reussi)

    def test_erreurs_de_branchement(self):
        ecrire_probleme(self.dossier, professeur=False)
        with self.assertRaises(examen.BranchementError):
            examen.passer_examen(self.dossier, PETIT, self.dossier / "r.txt", lambda _: None)
        with self.assertRaises(examen.BranchementError):  # les problèmes restent hors du dépôt
            examen.passer_examen(PROJECT_ROOT / "res", PETIT, self.dossier / "r.txt", lambda _: None)
        ecrire_probleme(self.dossier, "autre")
        with self.assertRaises(examen.BranchementError):  # le rapport aussi
            examen.passer_examen(self.dossier, PETIT, PROJECT_ROOT / "rapport.txt", lambda _: None)

    def test_verdict_lu_dans_le_jeu(self):
        class Jeu:
            win = "O"
        self.assertEqual(examen.verdict(Jeu(), {"O"}, 1), -1)   # le jeu dit que l'adversaire a gagné
        self.assertEqual(examen.verdict(Jeu(), {"X"}, -1), 1)
        Jeu.win = "D"
        self.assertEqual(examen.verdict(Jeu(), {"X"}, 1), 0)
        Jeu.win = ""
        self.assertEqual(examen.verdict(Jeu(), {"X"}, -1), -1)  # sans verdict du jeu : celui de la mère


if __name__ == "__main__":
    unittest.main()
