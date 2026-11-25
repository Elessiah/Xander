"""Lanceur d'examen blanc : ``python -m xander.examen <dossier>``.

Un examen blanc mesure la mère sur des problèmes **inédits**, écrits à
l'avance et gardés sous scellé hors du dépôt (jalon 6 de la feuille de
route). Le lanceur ne connaît aucun problème en particulier : il ne fait que
de la plomberie (trouver l'exemple et le professeur, rendre le dossier du
problème importable), puis il fait éduquer un fils par la mère avec l'API
habituelle (:meth:`Mother.raise_son`), mesure ce fils et écrit un rapport.
Il ne change rien à la mère.

**Convention.** Chaque sous-dossier direct de ``<dossier>`` est un problème,
pris dans l'ordre alphabétique et numéroté à partir de 1. Il contient :

* ``exemple.py`` : une vraie partie, au format de ``docs/format-exemple.md`` ;
  sa section ``# include`` importe le jeu par son nom de module (le dossier
  du problème est mis dans le chemin d'import, y compris pour le rejeu) ;
* ``professeur.py`` : une fonction ``professeur(game)`` qui joue un coup.

Le jeu suit l'interface des jeux à deux joueurs de ``docs/jeux.md`` : le
verdict de chaque partie de mesure est lu dans le jeu lui-même (``win`` :
``"X"``, ``"O"`` ou ``"D"`` ; ``get_turn()`` pour savoir qui est qui), pas
dans ce que la mère en comprend. Sans ``win``, on garde le verdict de la mère.

**Budget et barème, fixés avant tout examen** (:data:`BUDGET`) :

* la mère éduque le fils pendant :attr:`Budget.parties` parties, graine
  :attr:`Budget.graine` ;
* chaque problème a :attr:`Budget.limite` secondes en tout (compréhension,
  éducation et mesure) ; au-delà, il est raté ;
* mesure, sans correction : :attr:`Budget.professeur` parties contre le
  professeur et :attr:`Budget.hasard` contre un joueur au hasard, le fils
  jouant chaque côté une fois sur deux ; on compte aussi les coups
  impossibles du fils après ses :attr:`Budget.rodage` premières parties ;
* un problème est **réussi** si le fils ne perd aucune partie de mesure et
  ne fait aucun coup impossible après son rodage. Si la mère dit qu'elle ne
  sait pas éduquer ce problème, ou si elle plante, il est raté ;
* score = problèmes réussis / total.

Chaque problème passe dans un sous-processus à part (modules du jeu isolés,
limite de temps tenue en l'arrêtant). Le rapport donne le commit, la date, le
budget, puis pour chaque problème son numéro, réussi ou raté, et la durée :
rien d'autre sur leur contenu. Il est écrit sur la sortie et dans un fichier
hors du dépôt (par défaut dans ``<dossier>``).
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import random
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from xander.rebuilder import PROJECT_ROOT

EXEMPLE = "exemple.py"
PROFESSEUR = "professeur.py"
FONCTION_PROFESSEUR = "professeur"
MARQUEUR = "@@examen"


@dataclass(frozen=True)
class Budget:
    parties: int = 200        # parties d'éducation
    limite: float = 30 * 60   # secondes par problème, tout compris
    graine: int = 0
    professeur: int = 2       # parties de mesure contre le professeur (fils et professeur déterministes)
    hasard: int = 100         # parties de mesure contre le hasard
    rodage: int = 5           # coups impossibles tolérés pendant les premières parties d'éducation

    def describe(self) -> str:
        return (f"{self.parties} parties d'éducation, {self.limite:g} s par problème, graine {self.graine} ; "
                f"mesure : {self.professeur} parties contre le professeur et {self.hasard} contre le hasard "
                f"(chaque côté une fois sur deux), aucun coup impossible après la partie {self.rodage}")


#: Le budget de l'examen, fixé avant tout examen. Ne pas le changer pour un examen en cours.
BUDGET = Budget()


class BranchementError(Exception):
    """Le lanceur n'arrive pas à brancher un problème (plomberie, pas la mère)."""


@dataclass
class Resultat:
    numero: int
    reussi: bool
    duree: float


# --------------------------------------------------------------------------- #
# Plomberie
# --------------------------------------------------------------------------- #

def problemes(dossier: Path) -> list[Path]:
    """Les dossiers de problèmes, dans l'ordre (numéros 1, 2…)."""
    return sorted((p for p in dossier.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))),
                  key=lambda p: p.name)


def environnement(probleme: Path, graine: int) -> dict:
    """Variables d'environnement du sous-processus : le dossier du problème est importable,
    et ce chemin passe aussi au rejeu de l'exemple (:mod:`xander.rebuilder` garde ``PYTHONPATH``)."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(probleme), str(PROJECT_ROOT),
                                                      env.get("PYTHONPATH")]))
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONHASHSEED"] = str(graine)
    return env


def verifier_branchement(probleme: Path, env: dict) -> None:
    """Avant que la mère voie quoi que ce soit : les fichiers existent, l'exemple s'exécute
    tel quel depuis la racine du dépôt (comme le rejeu, qui part d'un dossier temporaire : les
    imports ne passent que par ``PYTHONPATH``) et le professeur s'importe."""
    for nom in (EXEMPLE, PROFESSEUR):
        if not (probleme / nom).is_file():
            raise BranchementError(f"{probleme.name} : {nom} manquant")
    controles = (
        [sys.executable, "-c", f"import runpy; runpy.run_path({str(probleme / EXEMPLE)!r})"],
        [sys.executable, "-c", f"import {Path(PROFESSEUR).stem} as p; assert callable(p.{FONCTION_PROFESSEUR})"],
    )
    for commande in controles:
        try:
            fini = subprocess.run(commande, cwd=PROJECT_ROOT, env=env, stdin=subprocess.DEVNULL,
                                  capture_output=True, text=True, encoding="utf-8", errors="replace",
                                  timeout=120)
        except subprocess.TimeoutExpired:
            raise BranchementError(f"{probleme.name} : le contrôle {commande[1:]} ne se termine pas") from None
        if fini.returncode != 0:
            raise BranchementError(f"{probleme.name} : le contrôle {commande[1:]} échoue :\n{fini.stderr}")


def commit() -> str:
    def git(*args):
        return subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.strip()
    sha = git("rev-parse", "HEAD") or "inconnu"
    return sha + (" (avec des modifications non commitées)" if git("status", "--porcelain")
                  else "")


def dans_le_depot(chemin: Path) -> bool:
    try:
        chemin.resolve().relative_to(PROJECT_ROOT)
        return True
    except ValueError:
        return False


# --------------------------------------------------------------------------- #
# Un problème (dans son sous-processus)
# --------------------------------------------------------------------------- #

def mesurer(education, budget: Budget) -> bool:
    """Le fils joue sans correction ; ``True`` s'il ne perd aucune partie et ne fait aucun
    coup impossible. Le verdict est celui du jeu (``win``) quand il le donne."""
    adversaires = [(education.teacher, budget.professeur),
                   (education.random_player(random.Random(budget.graine + 1)), budget.hasard)]
    for adversaire, nombre in adversaires:
        for numero in range(nombre):
            symboles = set()

            def joue(game, adversaire=adversaire, symboles=symboles):
                if hasattr(game, "get_turn"):
                    symboles.add(game.get_turn())
                adversaire(game)

            resultat, _ = education.play_game(joue, numero % 2)
            if education.impossibles:
                return False
            if verdict(education.lab.game, symboles, resultat) < 0:
                return False
    return True


def verdict(game, symboles_adversaire: set, resultat_mere: int) -> int:
    """1 : le fils gagne, 0 : nul, -1 : il perd. Lu dans le jeu s'il dit qui a gagné."""
    gagnant = getattr(game, "win", None)
    if not isinstance(gagnant, str) or not gagnant or len(symboles_adversaire) != 1:
        return resultat_mere
    if gagnant == "D":
        return 0
    return -1 if gagnant in symboles_adversaire else 1


def passer_probleme(probleme: Path, budget: Budget) -> bool:
    """Fait éduquer un fils par la mère sur ``probleme``, puis le mesure. Toute erreur de la
    mère (elle ne sait pas éduquer ce problème, ou elle plante) rend le problème raté."""
    import importlib

    from xander.mother import Mother

    teacher = getattr(importlib.import_module(Path(PROFESSEUR).stem), FONCTION_PROFESSEUR)
    random.seed(budget.graine)
    try:
        education = Mother().raise_son(probleme / EXEMPLE, teacher, budget.parties, seed=budget.graine)
        if any(record.impossibles for record in education.records if record.number > budget.rodage):
            return False
        return mesurer(education, budget)
    except Exception:  # noqa: BLE001 — la mère ne sait pas, ou plante : raté, sans regarder pourquoi
        return False


def _enfant(probleme: str, budget_json: str) -> int:
    """Point d'entrée du sous-processus : une ligne ``@@examen {"reussi": …}`` sur la sortie."""
    budget = Budget(**json.loads(budget_json))
    reussi = passer_probleme(Path(probleme), budget)
    print(MARQUEUR, json.dumps({"reussi": reussi}), flush=True)
    return 0


# --------------------------------------------------------------------------- #
# L'examen
# --------------------------------------------------------------------------- #

def lancer(probleme: Path, numero: int, budget: Budget) -> Resultat:
    env = environnement(probleme, budget.graine)
    verifier_branchement(probleme, env)
    commande = [sys.executable, "-m", "xander.examen", "--un-probleme", str(probleme),
                "--budget", json.dumps(asdict(budget))]
    debut = time.monotonic()
    try:
        fini = subprocess.run(commande, cwd=PROJECT_ROOT, env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=budget.limite)
    except subprocess.TimeoutExpired:
        return Resultat(numero, False, time.monotonic() - debut)
    duree = time.monotonic() - debut
    lignes = [l for l in fini.stdout.splitlines() if l.startswith(MARQUEUR + " ")]
    if not lignes:  # le sous-processus est mort sans répondre (mémoire, plantage de Python…)
        return Resultat(numero, False, duree)
    return Resultat(numero, bool(json.loads(lignes[-1][len(MARQUEUR) + 1:])["reussi"]), duree)


def passer_examen(dossier: str | Path, budget: Budget = BUDGET, rapport: str | Path | None = None,
                  sortie=print) -> tuple[list[Resultat], Path]:
    """Passe l'examen du dossier ``dossier`` ; renvoie les résultats et le chemin du rapport."""
    dossier = Path(dossier).resolve()
    if not dossier.is_dir():
        raise BranchementError(f"{dossier} n'est pas un dossier")
    if dans_le_depot(dossier):
        raise BranchementError("les problèmes d'un examen restent hors du dépôt")
    liste = problemes(dossier)
    if not liste:
        raise BranchementError(f"aucun problème dans {dossier}")
    debut = datetime.datetime.now()
    rapport = Path(rapport) if rapport else dossier / f"rapport-{debut:%Y-%m-%d-%H%M%S}.txt"
    if dans_le_depot(rapport):
        raise BranchementError("le rapport s'écrit hors du dépôt")
    lignes = [f"Examen blanc : {dossier.name}",
              f"Commit : {commit()}",
              f"Date : {debut:%Y-%m-%d %H:%M}",
              f"Budget : {budget.describe()}"
              + ("" if budget == BUDGET else " (budget réduit, ce n'est pas un examen)"),
              f"Problèmes : {len(liste)}", ""]
    for ligne in lignes:
        sortie(ligne)
    resultats = []
    for numero, probleme in enumerate(liste, 1):
        resultat = lancer(probleme, numero, budget)
        resultats.append(resultat)
        ligne = f"Problème {numero} : {'réussi' if resultat.reussi else 'raté'} ({resultat.duree:.0f} s)"
        lignes.append(ligne)
        sortie(ligne)
    score = sum(r.reussi for r in resultats)
    lignes += ["", f"Score : {score}/{len(resultats)}"]
    sortie(lignes[-2])
    sortie(lignes[-1])
    rapport.parent.mkdir(parents=True, exist_ok=True)
    rapport.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    sortie(f"Rapport écrit dans {rapport}")
    return resultats, rapport


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(prog="xander.examen",
                                     description="Passe un examen blanc : un fils par problème, sans retouche.")
    parser.add_argument("dossier", nargs="?", help="dossier de l'examen (un sous-dossier par problème)")
    parser.add_argument("--rapport", help="fichier du rapport (hors du dépôt ; défaut : dans le dossier)")
    parser.add_argument("--un-probleme", help=argparse.SUPPRESS)
    parser.add_argument("--budget", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.un_probleme:
        return _enfant(args.un_probleme, args.budget or json.dumps(asdict(BUDGET)))
    if not args.dossier:
        parser.error("indiquer le dossier de l'examen")
    try:
        passer_examen(args.dossier, rapport=args.rapport)
    except BranchementError as erreur:
        print(f"Erreur de branchement : {erreur}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
