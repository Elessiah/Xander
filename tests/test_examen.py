"""Le lanceur d'examen blanc, essayé sur des problèmes inventés et non scellés.

Chaque problème d'essai reprend un jeu de ``Games/`` mais passe par un module
posé dans le dossier du problème (comme un jeu sous scellé, hors de
``sys.path``), avec son ``arbitre.py`` et son ``professeur.py`` :

* le Morpion (deux joueurs, nul en jeu parfait) ;
* Partition (un joueur, pas de vraie défaite : on survit plus ou moins longtemps) ;
* les Allumettes avec 9 allumettes (deux joueurs, le premier perd en jeu parfait) ;
* Jumper (un joueur, obstacles tirés de la graine).

On vérifie la plomberie et le barème, pas la mère.
"""

import contextlib
import importlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from xander import examen
from xander.rebuilder import PROJECT_ROOT
from tests import lent

RES = PROJECT_ROOT / "res"
PETIT = examen.Budget(parties=2, graines=2, facteur=5000)

MORPION = {
    "jeu": "from Games.Morpion import Morpion  # noqa: F401\n",
    "exemple": (RES / "exampleMorpion.py", "from Games.Morpion import Morpion", "from jeu_local import Morpion"),
    "professeur": "from Games.MinmaxMorpion import minmax_morpion_play as professeur  # noqa: F401\n",
    "arbitre": '''from jeu_local import Morpion

joueurs = 2
plafond = 9


def nouvelle_partie(graine):
    game = Morpion()
    game.init("X")
    return game


def a_qui(game):
    return "XO".index(game.get_turn())


def finie(game):
    return bool(game.win)


def resultat(game, place):
    if game.win in ("", "D"):
        return 0
    return 1 if game.win == "XO"[place] else -1


def coups_permis(game):
    return [("play", case) for case in game.get_moves()]
''',
}

PARTITION = {
    "jeu": "from Games.Partition import Partition  # noqa: F401\n",
    "exemple": (RES / "examplePartition.py", "from Games.Partition import Partition",
                "from jeu_local import Partition"),
    "professeur": '''def professeur(game):
    game.play(game.get_partition()[0] == "o")
''',
    "arbitre": '''from jeu_local import Partition

joueurs = 1
plafond = 100


def nouvelle_partie(graine):
    return Partition(graine)


def a_qui(game):
    return 0


def finie(game):
    return game.finie


def resultat(game, place):
    return game.joues   # temps joués : plus longtemps est mieux


def coups_permis(game):
    return [("play", False), ("play", True)]
''',
}

EXEMPLE_ALLUMETTES_9 = '''# include
from jeu_local import Allumettes

# init
game = Allumettes()  # game
game.set_max_nb_allumettes(9)
nb = game.init("X")  # integer

# back
nb = game.back()  # integer

# player X
nb = game.get_game_state()  # integer
nb = game.play(1)  # integer

# player O
nb = game.get_game_state()  # integer
nb = game.play(3)  # integer

# player X
nb = game.get_game_state()  # integer
nb = game.play(2)  # integer

# player O
nb = game.get_game_state()  # integer
nb = game.play(2)  # bool

# end player O
'''

ALLUMETTES_PERDANTES = {
    "jeu": "from Games.Allumettes import Allumettes  # noqa: F401\n",
    "exemple": EXEMPLE_ALLUMETTES_9,
    "professeur": "from Games.MinmaxAllumettes import minmax_allumettes_play as professeur  # noqa: F401\n",
    "arbitre": '''from jeu_local import Allumettes

joueurs = 2
plafond = 20


def nouvelle_partie(graine):
    game = Allumettes()
    game.set_max_nb_allumettes(9)   # 9 : le premier joueur perd en jeu parfait
    game.init("X")
    return game


def a_qui(game):
    return "XO".index(game.get_turn())


def finie(game):
    return bool(game.win)


def resultat(game, place):
    if not game.win:
        return 0
    return 1 if game.win == "XO"[place] else -1


def coups_permis(game):
    return [("play", prise) for prise in (1, 2, 3) if prise <= game.nb_allumettes]
''',
}

JUMPER = {
    "jeu": "from Games.Jumper import Jumper  # noqa: F401\n",
    "exemple": (RES / "exampleJumper.py", "from Games.Jumper import Jumper", "from jeu_local import Jumper"),
    "professeur": '''def professeur(game):
    game.play(game.get_board()[162] == "T")   # sauter quand un obstacle est juste devant
''',
    "arbitre": '''from jeu_local import Jumper

joueurs = 1
plafond = 150


def nouvelle_partie(graine):
    return Jumper(graine)


def a_qui(game):
    return 0


def finie(game):
    return game.game_over


def resultat(game, place):
    return game.ticks   # durée de survie


def coups_permis(game):
    return [("play", False), ("play", True)]
''',
}


def ecrire_probleme(dossier: Path, nom: str, jeu: dict = MORPION, sans: tuple = ()) -> Path:
    """Écrit un problème d'essai dans ``dossier/nom`` (sans les fichiers de ``sans``)."""
    probleme = dossier / nom
    probleme.mkdir(parents=True)
    (probleme / "jeu_local.py").write_text(jeu["jeu"], encoding="utf-8")
    exemple = jeu["exemple"]
    if isinstance(exemple, tuple):
        chemin, avant, apres = exemple
        exemple = chemin.read_text(encoding="utf-8").replace(avant, apres)
    fichiers = {"exemple.py": exemple, "professeur.py": jeu["professeur"], "arbitre.py": jeu["arbitre"]}
    for nom_fichier, texte in fichiers.items():
        if nom_fichier not in sans:
            (probleme / nom_fichier).write_text(texte, encoding="utf-8")
    return probleme


class DossierTemporaire(unittest.TestCase):
    def setUp(self):
        self.dossier = Path(tempfile.mkdtemp(prefix="examen-essai-"))
        self.addCleanup(shutil.rmtree, self.dossier, ignore_errors=True)

    def importer(self, probleme: Path, *modules):
        """Importe les modules d'un problème dans ce processus (puis les oublie). Le dossier du
        problème passe aussi dans ``PYTHONPATH``, pour le rejeu de l'exemple."""
        sys.path.insert(0, str(probleme))
        ancien = os.environ.get("PYTHONPATH")
        os.environ["PYTHONPATH"] = os.pathsep.join(filter(None, [str(probleme), ancien]))
        noms = ("jeu_local", *modules)

        def oublier():
            sys.path.remove(str(probleme))
            if ancien is None:
                os.environ.pop("PYTHONPATH", None)
            else:
                os.environ["PYTHONPATH"] = ancien
            for nom in noms:
                sys.modules.pop(nom, None)
        self.addCleanup(oublier)
        for nom in noms:
            sys.modules.pop(nom, None)
        return [importlib.import_module(nom) for nom in modules]


class TestPlomberie(DossierTemporaire):
    def test_budget_fixe_avant_l_examen(self):
        self.assertEqual(examen.BUDGET, examen.Budget(parties=200, graine=0, graines=10, rodage=5,
                                                      facteur=20_000, facteur_bulletin=10_000))

    def test_le_dossier_du_probleme_est_importable_jusque_dans_le_rejeu(self):
        probleme = ecrire_probleme(self.dossier, "a")
        env = examen.environnement(probleme, 0)
        self.assertEqual(examen.verifier_branchement(probleme, env), 2)
        code = (f"from xander.mother import Mother\n"
                f"e = Mother().raise_son({str(probleme / 'exemple.py')!r}, None, 0)\n"
                f"print(e.model.action.short_name)\n")
        fini = subprocess.run([sys.executable, "-c", code], cwd=PROJECT_ROOT, env=env,
                              capture_output=True, text=True, encoding="utf-8", timeout=300)
        self.assertEqual(fini.returncode, 0, fini.stderr)
        self.assertEqual(fini.stdout.strip().splitlines()[-1], "play")

    def test_sans_arbitre_c_est_une_erreur_de_branchement(self):
        ecrire_probleme(self.dossier, "a", sans=("arbitre.py",))
        with self.assertRaisesRegex(examen.BranchementError, "arbitre.py manquant"):
            examen.passer_examen(self.dossier, PETIT, self.dossier / "r.txt", lambda _: None)
        self.assertFalse((self.dossier / "r.txt").exists())  # aucun score : la mère n'a rien passé

    def test_arbitre_incomplet_ou_faux(self):
        probleme = ecrire_probleme(self.dossier, "a")
        env = examen.environnement(probleme, 0)
        arbitre = probleme / "arbitre.py"
        texte = arbitre.read_text(encoding="utf-8")
        for faute, attendu in ((texte.replace("def coups_permis", "def autre_chose"), "il manque coups_permis"),
                               (texte.replace("plafond = 9", "plafond = 0"), "plafond"),
                               (texte.replace('return "XO".index', 'return 5 + "XO".index'), "a_qui"),
                               (texte.replace("return bool(game.win)", "return True"), "déjà finie")):
            arbitre.write_text(faute, encoding="utf-8")
            with self.assertRaisesRegex(examen.BranchementError, attendu):
                examen.verifier_branchement(probleme, env)

    def test_autres_erreurs_de_branchement(self):
        ecrire_probleme(self.dossier, "a", sans=("professeur.py",))
        with self.assertRaises(examen.BranchementError):
            examen.passer_examen(self.dossier, PETIT, self.dossier / "r.txt", lambda _: None)
        with self.assertRaises(examen.BranchementError):  # les problèmes restent hors du dépôt
            examen.passer_examen(PROJECT_ROOT / "res", PETIT, self.dossier / "r.txt", lambda _: None)
        shutil.rmtree(self.dossier / "a")
        ecrire_probleme(self.dossier, "b")
        with self.assertRaises(examen.BranchementError):  # le rapport aussi
            examen.passer_examen(self.dossier, PETIT, PROJECT_ROOT / "rapport.txt", lambda _: None)

    def test_situations(self):
        budget = examen.Budget(graines=3)
        seul = examen.situations(1, budget)
        self.assertEqual(len(seul), 3)
        self.assertEqual({s.adversaires for s in seul}, {"seul"})
        trois = examen.situations(3, budget)
        self.assertEqual(len(trois), 3 * 3 * 2)  # graines × places × (professeur, hasard)
        self.assertEqual(examen.situations(3, budget), trois)  # graine maîtresse fixe
        self.assertNotEqual(examen.situations(3, examen.Budget(graine=1, graines=3)), trois)

    def test_reference_de_la_machine(self):
        self.assertEqual(examen.tache_de_reference(), examen.tache_de_reference())
        self.assertGreater(examen.mesure_de_reference(1), 0)


class TestMesure(DossierTemporaire):
    """La mesure dans ce processus : le barème, et rien ne revient vers la mère."""

    def setUp(self):
        super().setUp()
        silence = contextlib.redirect_stdout(io.StringIO())  # les Minmax commentent leurs coups
        silence.__enter__()
        self.addCleanup(silence.__exit__, None, None, None)

    def eduquer(self, nom: str, jeu: dict, parties: int):
        from xander.mother import Mother

        probleme = ecrire_probleme(self.dossier, nom, jeu)
        professeur, arbitre = self.importer(probleme, "professeur", "arbitre")
        education = Mother().raise_son(probleme / "exemple.py", professeur.professeur, parties)
        return education, arbitre, professeur.professeur

    def test_la_mesure_ne_change_rien_a_la_mere(self):
        education, arbitre, professeur = self.eduquer("a", MORPION, 4)
        avant = (repr(education.knowledge), education.source(), len(education.records),
                 list(education.lab.moves), education.max_views)
        examen.mesurer(education, arbitre, professeur, examen.Budget(graines=2))
        apres = (repr(education.knowledge), education.source(), len(education.records),
                 list(education.lab.moves), education.max_views)
        self.assertEqual(avant, apres)

    def test_une_situation_se_rejoue_a_l_identique(self):
        """Les graines ne dépendent que de la situation : la même partie, rejouée, donne le même
        résultat (c'est ce qui rend juste la comparaison avec le professeur)."""
        for nom, jeu in (("m", MORPION), ("a", ALLUMETTES_PERDANTES), ("p", PARTITION)):
            probleme = ecrire_probleme(self.dossier, nom, jeu)
            professeur, arbitre = self.importer(probleme, "professeur", "arbitre")
            for situation in examen.situations(arbitre.joueurs, examen.Budget(graines=3)):
                place = examen.joueur_professeur(professeur.professeur)
                self.assertEqual(examen.jouer(arbitre, situation, place, professeur.professeur),
                                 examen.jouer(arbitre, situation, place, professeur.professeur))

    def test_perdre_comme_le_professeur_n_est_pas_un_echec(self):
        """Allumettes à 9 : le premier joueur perd en jeu parfait. Le fils, premier contre le
        professeur, perd ; le professeur à sa place aussi : la situation est tenue."""
        education, arbitre, professeur = self.eduquer("a", ALLUMETTES_PERDANTES, 30)
        from xander import son_writer

        situation = examen.Situation(0, 0, "professeur")
        fils = examen.joueur_fils(son_writer.load(education.source()))
        self.assertEqual(examen.jouer(arbitre, situation, fils, professeur), -1)
        self.assertEqual(examen.jouer(arbitre, situation, examen.joueur_professeur(professeur), professeur), -1)
        self.assertEqual(examen.mesurer(education, arbitre, professeur, examen.Budget(graines=3)), 1.0)

    def test_un_coup_impossible_est_une_faute_du_fils(self):
        _, arbitre, professeur = self.eduquer("m", MORPION, 0)

        class Tricheur:
            @staticmethod
            def play(game):
                game.play(4)
                game.play(4)   # un deuxième essai

        class Hors:
            @staticmethod
            def play(game):
                game.play(42)  # un coup que le jeu ne permet pas

        for fils in (Tricheur, Hors):
            with self.assertRaises(examen.FauteDuFils):
                examen.jouer(arbitre, examen.Situation(0, 0, "professeur"), examen.joueur_fils(fils), professeur)


@lent
class TestExamen(DossierTemporaire):
    """L'examen complet, dans des sous-processus, sur des problèmes d'essai."""

    def test_examen_complet_et_rapport(self):
        ecrire_probleme(self.dossier, "a-morpion", MORPION)
        ecrire_probleme(self.dossier, "b-partition", PARTITION)
        ecrire_probleme(self.dossier, "c-allumettes", ALLUMETTES_PERDANTES)
        rapport = self.dossier / "rapport.txt"
        sortie = []
        budget = examen.Budget(parties=30, graines=2, facteur=5000)
        resultats, chemin = examen.passer_examen(self.dossier, budget, rapport, sortie.append)
        self.assertEqual(chemin, rapport)
        self.assertEqual([r.numero for r in resultats], [1, 2, 3])
        self.assertEqual([r.joueurs for r in resultats], [2, 1, 2])
        self.assertTrue(all(r.duree > 0 and 0 <= r.relatif <= 1 for r in resultats))
        # Partition : survivre aussi longtemps que le professeur ; Allumettes à 9 : perdre en
        # premier contre le professeur, comme lui, n'est pas un échec.
        self.assertTrue(resultats[1].reussi)
        self.assertTrue(resultats[2].reussi)
        texte = rapport.read_text(encoding="utf-8")
        for attendu in ("Commit : ", "Date : ", "Machine : ", "Tâche de référence : ", "Budget : 30 parties",
                        "budget réduit", "Problème 1 : ", "score relatif", "(2 joueurs", "(1 joueur,",
                        "Score : ", "score relatif moyen"):
            self.assertIn(attendu, texte)
        # le bulletin de chaque fils, lu après le score, en annexe
        self.assertTrue(all(r.bulletin and "Taille" in r.bulletin for r in resultats))
        annexe = texte[texte.index("Bulletins des fils"):]
        for attendu in ("Problème 1 : Bulletin du fils", "Problème 3 : ", "Compression", "Généralisation"):
            self.assertIn(attendu, annexe)
        self.assertLess(texte.index("Score : "), texte.index("Bulletins des fils"))
        for nom in ("morpion", "partition", "allumette"):  # rien sur le contenu des problèmes
            self.assertNotIn(nom, texte.lower())
        self.assertEqual(sortie[-1], f"Rapport écrit dans {rapport}")

    def test_temps_depasse_rate(self):
        ecrire_probleme(self.dossier, "a")
        resultats, _ = examen.passer_examen(self.dossier, examen.Budget(parties=2, facteur=1),
                                            self.dossier / "r.txt", lambda _: None)
        self.assertFalse(resultats[0].reussi)
        self.assertEqual(resultats[0].relatif, 0)

    def test_la_mere_ne_sait_pas_eduquer_rate(self):
        probleme = ecrire_probleme(self.dossier, "a")
        # un exemple que la mère comprend mais où l'action ne change aucune case
        (probleme / "exemple.py").write_text(
            "# include\nfrom jeu_local import Morpion\n\n# init\ngame = Morpion()  # game\n"
            "board = game.init(\"X\")  # array 9\n\n# back\nboard = game.back()  # array 9\n\n"
            "# player X\nboard = game.get_game_state()  # array 9\n\n"
            "# player O\nboard = game.get_game_state()  # array 9\n\n# end draw\n", encoding="utf-8")
        resultats, _ = examen.passer_examen(self.dossier, PETIT, self.dossier / "r.txt", lambda _: None)
        self.assertFalse(resultats[0].reussi)
        self.assertEqual(resultats[0].relatif, 0)


if __name__ == "__main__":
    unittest.main()
