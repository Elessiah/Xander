"""Lanceur d'examen blanc : ``python -m xander.examen <dossier>``.

Un examen blanc mesure la mère sur des problèmes **inédits**, écrits à
l'avance et gardés sous scellé hors du dépôt (jalon 6 de la feuille de
route). Le lanceur ne connaît aucun problème en particulier : il ne fait que
de la plomberie (trouver l'exemple, le professeur et l'arbitre, rendre le
dossier du problème importable), puis il fait éduquer un fils par la mère
avec l'API habituelle (:meth:`Mother.raise_son`), mesure ce fils et écrit un
rapport. Il ne change rien à la mère.

**Convention.** Chaque sous-dossier direct de ``<dossier>`` est un problème,
pris dans l'ordre alphabétique et numéroté à partir de 1. Il contient :

* ``exemple.py`` : une vraie partie, au format de ``docs/format-exemple.md`` ;
  sa section ``# include`` importe le jeu par son nom de module (le dossier
  du problème est mis dans le chemin d'import, y compris pour le rejeu) ;
* ``professeur.py`` : une fonction ``professeur(game)`` qui joue un coup ;
* ``arbitre.py`` : ce que sait l'auteur du problème, et pas la mère : comment
  une partie commence et se termine, ce qui compte comme un bon résultat, et
  quels coups sont permis. Obligatoire. Interface (noms au niveau du module) :

  - ``joueurs`` : le nombre de joueurs (1, 2, 3…) ;
  - ``plafond`` : le nombre maximal de coups d'une partie de mesure (au-delà,
    la partie s'arrête et on lit le résultat tel quel : indispensable quand
    on survit plus ou moins longtemps) ;
  - ``nouvelle_partie(graine)`` : une partie neuve et initialisée, commencée
    comme celle de l'exemple ; la graine sert aux jeux qui en ont une ;
  - ``a_qui(game)`` : la place (``0`` à ``joueurs - 1``) du joueur au trait ;
  - ``finie(game)`` : la partie est-elle finie ?
  - ``resultat(game, place)`` : un nombre, plus grand est meilleur (victoire
    1, nul 0, défaite -1 ; ou la durée de survie ; ou moins le nombre
    d'essais). Appelé sur une partie finie, ou arrêtée au plafond ;
  - ``coups_permis(game)`` : la liste de **tous** les coups que le jeu accepte
    maintenant, chacun sous la forme ``(nom_de_methode, argument, …)``, par
    exemple ``[("play", 0), ("play", 3)]``. Le joueur au hasard de la mesure
    tire parmi eux, et un coup du fils qui n'y est pas est un coup impossible.

**Barème : au moins aussi bien que le professeur à sa place.** Une
*situation* de mesure est une graine, une place à la table et des adversaires
(tous les autres joueurs sont le professeur, ou tous jouent au hasard ; seul,
il n'y en a pas). Chaque situation se joue deux fois, avec les mêmes graines
et les mêmes autres joueurs : une fois le fils à cette place, une fois le
professeur. Le fils la *tient* si son ``resultat`` à cette place est au
moins celui du professeur, sans coup impossible. Score relatif d'un
problème : la part des situations tenues. Problème **réussi** : toutes les
situations tenues, et aucun coup impossible après les :attr:`Budget.rodage`
premières parties d'éducation. Si la mère dit qu'elle ne sait pas éduquer ce
problème, si elle plante ou si le temps est dépassé : raté, score relatif 0.

Le fils mesuré est son code tel que la mère l'a écrit, chargé à part et joué
**sans correction** : rien de la mesure ne revient vers la mère. Le lanceur
ne lit jamais la fin d'une partie de mesure dans la mère : c'est l'arbitre
qui décide.

**Budget, fixé avant tout examen** (:data:`BUDGET`). Le nombre de parties
d'éducation, de situations et le plafond de coups bornent le travail ; une
limite de temps par problème reste comme garde-fou. Elle est exprimée en
multiples d'une tâche de référence fixe (:func:`tache_de_reference`), mesurée
au début de l'examen, pour dépendre moins de la machine.

Chaque problème passe dans un sous-processus à part (modules du jeu isolés,
limite de temps tenue en l'arrêtant). Le rapport donne le commit, la date, la
machine et sa mesure de référence, le budget, puis pour chaque problème son
numéro, réussi ou raté, son score relatif, son nombre de joueurs et la
durée : rien d'autre sur leur contenu. Il est écrit sur la sortie et dans un
fichier hors du dépôt (par défaut dans ``<dossier>``).

**Le bulletin, après coup.** Une fois le score d'un problème écrit (le
sous-processus l'envoie avant toute autre chose), le lanceur lit le fils
comme on relit du code : son bulletin (:mod:`xander.bulletin` : taille,
compression, origine des coups, généralisation à des positions jamais vues).
Il ne compte pas dans la limite de l'examen et ne change ni le score ni la
mère, qui a fini ; il a sa propre limite, :attr:`Budget.facteur_bulletin`
fois la tâche de référence. Le rapport le donne en annexe, en nombres
seulement (rien sur le contenu du problème). Comme le score, il se lit comme
une mesure : on ne s'en sert jamais pour corriger la mère sur ces problèmes.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import datetime
import io
import json
import numbers
import os
import platform
import random
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from xander.rebuilder import PROJECT_ROOT

EXEMPLE = "exemple.py"
PROFESSEUR = "professeur.py"
ARBITRE = "arbitre.py"
FONCTION_PROFESSEUR = "professeur"
INTERFACE_ARBITRE = ("joueurs", "plafond", "nouvelle_partie", "a_qui", "finie", "resultat", "coups_permis")
MARQUEUR = "@@examen"
MARQUEUR_BULLETIN = "@@bulletin"


@dataclass(frozen=True)
class Budget:
    parties: int = 200        # parties d'éducation
    graine: int = 0           # graine maîtresse : éducation, graines des parties de mesure, hasard
    graines: int = 10         # graines de mesure (pour chaque place et chaque sorte d'adversaires)
    rodage: int = 5           # coups impossibles tolérés pendant les premières parties d'éducation
    facteur: float = 20_000   # limite de temps par problème, en multiples de la tâche de référence
    facteur_bulletin: float = 10_000  # limite du bulletin, après le score (même unité)

    def describe(self) -> str:
        return (f"{self.parties} parties d'éducation, graine maîtresse {self.graine} ; mesure : "
                f"{self.graines} graines pour chaque place et chaque sorte d'adversaires (professeur, "
                f"hasard ; aucun pour un joueur seul), chaque situation jouée par le fils puis par le "
                f"professeur ; aucun coup impossible après la partie {self.rodage} ; limite de temps : "
                f"{self.facteur:g} fois la tâche de référence par problème ; bulletin après le score, "
                f"hors de cette limite : au plus {self.facteur_bulletin:g} fois la référence")


#: Le budget de l'examen, fixé avant tout examen. Ne pas le changer pour un examen en cours.
BUDGET = Budget()


class BranchementError(Exception):
    """Le lanceur n'arrive pas à brancher un problème (plomberie, pas la mère)."""


class FauteDuFils(Exception):
    """Pendant la mesure, le fils fait un coup impossible ou plante."""


@dataclass
class Resultat:
    numero: int
    reussi: bool
    relatif: float
    joueurs: int
    duree: float
    bulletin: str | None = None  # lu après le score ; None : pas de fils, ou temps dépassé


@dataclass(frozen=True)
class Situation:
    graine: int        # graine de la partie (``nouvelle_partie``)
    place: int         # place mesurée (``0`` à ``joueurs - 1``)
    adversaires: str   # "professeur", "hasard" ou "seul"

    def tirage(self) -> str:
        """Graine du hasard de cette situation (la même pour le fils et pour le professeur)."""
        return f"{self.graine}/{self.place}/{self.adversaires}"


# --------------------------------------------------------------------------- #
# La machine
# --------------------------------------------------------------------------- #

def tache_de_reference() -> int:
    """Une petite tâche fixe en Python pur (tirer, trier, compter), qui ne dépend d'aucun
    problème : sa durée sert d'unité à la limite de temps."""
    rng = random.Random(20261125)
    total = 0
    for _ in range(200):
        valeurs = sorted(rng.randrange(1000) for _ in range(1000))
        comptes: dict = {}
        for v in valeurs:
            comptes[v] = comptes.get(v, 0) + 1
        total += len(comptes) + sum(i * v for i, v in enumerate(valeurs[:50]))
    return total


def mesure_de_reference(essais: int = 5) -> float:
    """Durée de la tâche de référence sur cette machine (la plus courte de ``essais``)."""
    durees = []
    for _ in range(essais):
        debut = time.perf_counter()
        tache_de_reference()
        durees.append(time.perf_counter() - debut)
    return min(durees)


def machine() -> str:
    processeur = platform.processor() or platform.machine() or "processeur inconnu"
    return (f"{platform.platform()}, {processeur}, {os.cpu_count()} cœurs, "
            f"Python {platform.python_version()}")


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


def controler_arbitre(arbitre) -> int:
    """Vérifie l'interface d'un arbitre sur une partie neuve ; renvoie son nombre de joueurs.
    Lève :class:`BranchementError` si quelque chose manque ou ne va pas."""
    manque = [nom for nom in INTERFACE_ARBITRE if not hasattr(arbitre, nom)]
    if manque:
        raise BranchementError(f"{ARBITRE} : il manque {', '.join(manque)}")
    joueurs, plafond = arbitre.joueurs, arbitre.plafond
    for nom, valeur in (("joueurs", joueurs), ("plafond", plafond)):
        if type(valeur) is not int or valeur < 1:
            raise BranchementError(f"{ARBITRE} : {nom} doit être un entier positif")
    for nom in INTERFACE_ARBITRE[2:]:
        if not callable(getattr(arbitre, nom)):
            raise BranchementError(f"{ARBITRE} : {nom} doit être une fonction")
    with contextlib.redirect_stdout(io.StringIO()):
        game = arbitre.nouvelle_partie(0)
        if arbitre.finie(game):
            raise BranchementError(f"{ARBITRE} : une partie neuve est déjà finie")
        if arbitre.a_qui(game) not in range(joueurs):
            raise BranchementError(f"{ARBITRE} : a_qui doit donner une place entre 0 et {joueurs - 1}")
        coups = arbitre.coups_permis(game)
        if not isinstance(coups, list) or not coups or not all(
                isinstance(c, tuple) and c and isinstance(c[0], str) for c in coups):
            raise BranchementError(f"{ARBITRE} : coups_permis doit donner une liste non vide de "
                                   "tuples (nom_de_methode, argument, …)")
        valeur = arbitre.resultat(game, 0)
        if isinstance(valeur, bool) or not isinstance(valeur, numbers.Real):
            raise BranchementError(f"{ARBITRE} : resultat doit être un nombre")
    return joueurs


def _controle_arbitre() -> None:
    """Contrôle lancé dans un sous-processus (le dossier du problème est dans le chemin)."""
    import arbitre  # noqa: PLC0415 — le module du problème, trouvé par PYTHONPATH
    try:
        joueurs = controler_arbitre(arbitre)
    except BranchementError as erreur:
        print(erreur, file=sys.stderr)
        sys.exit(1)
    print(MARQUEUR, json.dumps({"joueurs": joueurs}), flush=True)


def _sous_processus(commande: list, env: dict, timeout: float | None):
    return subprocess.run(commande, cwd=PROJECT_ROOT, env=env, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout)


def _reponse(sortie: str, marqueur: str = MARQUEUR) -> dict | None:
    """La dernière ligne ``@@examen {…}`` (ou d'un autre marqueur) d'une sortie."""
    lignes = [l for l in sortie.splitlines() if l.startswith(marqueur + " ")]
    return json.loads(lignes[-1][len(marqueur) + 1:]) if lignes else None


def verifier_branchement(probleme: Path, env: dict) -> int:
    """Avant que la mère voie quoi que ce soit : les fichiers existent, l'exemple s'exécute
    tel quel depuis la racine du dépôt (comme le rejeu, qui part d'un dossier temporaire : les
    imports ne passent que par ``PYTHONPATH``), le professeur s'importe et l'arbitre a son
    interface. Renvoie le nombre de joueurs donné par l'arbitre."""
    for nom in (EXEMPLE, PROFESSEUR, ARBITRE):
        if not (probleme / nom).is_file():
            raise BranchementError(f"{probleme.name} : {nom} manquant")
    controles = (
        [sys.executable, "-c", f"import runpy; runpy.run_path({str(probleme / EXEMPLE)!r})"],
        [sys.executable, "-c", f"import {Path(PROFESSEUR).stem} as p; assert callable(p.{FONCTION_PROFESSEUR})"],
        [sys.executable, "-c", "from xander.examen import _controle_arbitre; _controle_arbitre()"],
    )
    for commande in controles:
        try:
            fini = _sous_processus(commande, env, 120)
        except subprocess.TimeoutExpired:
            raise BranchementError(f"{probleme.name} : le contrôle {commande[1:]} ne se termine pas") from None
        if fini.returncode != 0:
            raise BranchementError(f"{probleme.name} : le contrôle {commande[1:]} échoue :\n{fini.stderr}")
    return _reponse(fini.stdout)["joueurs"]


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
# La mesure (dans le sous-processus d'un problème)
# --------------------------------------------------------------------------- #

def situations(joueurs: int, budget: Budget) -> list[Situation]:
    """Toutes les situations de mesure : graines (tirées de la graine maîtresse) × places ×
    adversaires."""
    rng = random.Random(budget.graine)
    graines = [rng.randrange(2 ** 31) for _ in range(budget.graines)]
    adversaires = ("seul",) if joueurs == 1 else ("professeur", "hasard")
    return [Situation(g, place, a) for g in graines for place in range(joueurs) for a in adversaires]


class VueDuFils:
    """Le jeu tel que le fils le voit pendant un de ses tours de mesure.

    Les appels passent au vrai jeu, sauf les coups : un appel dont le nom est celui d'un coup
    permis (``coups_permis`` de l'arbitre) est un coup. Le premier, s'il est permis, est joué ;
    tout autre (un coup que l'arbitre ne permet pas, un deuxième essai) n'est pas transmis et
    sera compté impossible. Une fois la partie finie (selon l'arbitre), le fils ne lit plus
    qu'une copie du jeu : certains jeux recommencent une partie quand on lit un état terminé."""

    def __init__(self, game, arbitre):
        permis = arbitre.coups_permis(game)
        object.__setattr__(self, "_etat", {"jeu": game, "arbitre": arbitre, "permis": permis,
                                           "noms": {c[0] for c in permis}, "coups": [],
                                           "copie": None})

    def coup_joue(self) -> bool:
        """Le fils a-t-il joué exactement un coup, et un coup permis ?"""
        etat = self._etat
        return len(etat["coups"]) == 1 and etat["coups"][0] in etat["permis"]

    def __getattr__(self, nom):
        etat = self._etat
        jeu = etat["jeu"]
        valeur = getattr(jeu, nom)
        if not callable(valeur):
            return valeur

        def appel(*args, **kwargs):
            if nom in etat["noms"]:
                coup = (nom, *args)
                etat["coups"].append(coup)
                if len(etat["coups"]) > 1 or kwargs or coup not in etat["permis"]:
                    return None   # pas transmis : un coup impossible
                return valeur(*args)
            if etat["copie"] is None and etat["coups"] and etat["arbitre"].finie(jeu):
                etat["copie"] = copy.deepcopy(jeu)
            if etat["copie"] is not None:
                return getattr(etat["copie"], nom)(*args, **kwargs)
            return valeur(*args, **kwargs)
        return appel

    def __setattr__(self, nom, valeur):
        raise FauteDuFils("le fils modifie le jeu")


def joueur_fils(fils):
    """Le fils à sa place : il joue son tour avec son propre code (``play``), sur une vue du jeu.
    Un coup impossible ou un plantage est une :class:`FauteDuFils`."""
    def joue(game, arbitre):
        vue = VueDuFils(game, arbitre)
        try:
            fils.play(vue)
        except Exception as erreur:  # noqa: BLE001 — le fils plante : c'est sa faute, sans regarder pourquoi
            raise FauteDuFils(type(erreur).__name__) from None
        if not vue.coup_joue():
            raise FauteDuFils("coup impossible")
    return joue


def joueur_professeur(professeur):
    def joue(game, arbitre):
        professeur(game)
    joue.__name__ = "professeur"
    return joue


def coup_au_hasard(game, arbitre, rng: random.Random) -> None:
    """Un vrai coup au hasard parmi les coups que le jeu permet (selon l'arbitre, pas la mère)."""
    nom, *arguments = rng.choice(arbitre.coups_permis(game))
    getattr(game, nom)(*arguments)


def jouer(arbitre, situation: Situation, a_sa_place, professeur):
    """Une partie de mesure : ``a_sa_place`` tient la place mesurée, les autres places sont
    tenues par le professeur ou par le hasard. Les graines ne dépendent que de la situation :
    le hasard global (un professeur ou un jeu non déterministe) et chaque coup au hasard sont
    les mêmes pour le fils et pour le professeur tant que leurs parties le permettent. Renvoie
    ``resultat`` pour la place mesurée."""
    tirage = situation.tirage()
    random.seed(tirage)

    def arbitrer(fonction, *args):
        try:
            return fonction(*args)
        except FauteDuFils:
            raise
        except Exception as erreur:  # noqa: BLE001
            raise BranchementError(f"pendant la mesure, {getattr(fonction, '__name__', fonction)} "
                                   f"échoue : {type(erreur).__name__}: {erreur}") from None

    game = arbitrer(arbitre.nouvelle_partie, situation.graine)
    coups = 0
    while coups < arbitre.plafond and not arbitrer(arbitre.finie, game):
        place = arbitrer(arbitre.a_qui, game)
        if place == situation.place:
            arbitrer(a_sa_place, game, arbitre)   # une faute du fils passe telle quelle
        elif situation.adversaires == "professeur":
            arbitrer(professeur, game)
        else:
            arbitrer(coup_au_hasard, game, arbitre, random.Random(f"{tirage}/{coups}"))
        coups += 1
    return arbitrer(arbitre.resultat, game, situation.place)


def mesurer(education, arbitre, professeur, budget: Budget) -> float:
    """Le score relatif : la part des situations où le fils, à sa place, fait au moins aussi
    bien que le professeur à la même place. Le fils est son code tel que la mère l'a écrit,
    chargé à part : il joue sans correction, et rien ne revient vers la mère."""
    from xander import son_writer

    source = education.source()
    liste = situations(arbitre.joueurs, budget)
    tenues = 0
    with contextlib.redirect_stdout(io.StringIO()):  # les professeurs commentent leurs coups
        for situation in liste:
            fils = son_writer.load(source)  # un fils neuf pour chaque partie : aucune mémoire d'une autre
            try:
                du_fils = jouer(arbitre, situation, joueur_fils(fils), professeur)
            except FauteDuFils:
                continue
            du_professeur = jouer(arbitre, situation, joueur_professeur(professeur), professeur)
            tenues += du_fils >= du_professeur
    return tenues / len(liste)


def passer_probleme(probleme: Path, budget: Budget) -> tuple[dict, object]:
    """Fait éduquer un fils par la mère sur ``probleme``, puis le mesure. Toute erreur de la
    mère (elle ne sait pas éduquer ce problème, ou elle plante) rend le problème raté. Rend
    aussi l'éducation, pour le bulletin (``None`` si elle a échoué)."""
    import importlib

    from xander.mother import Mother

    teacher = getattr(importlib.import_module(Path(PROFESSEUR).stem), FONCTION_PROFESSEUR)
    arbitre = importlib.import_module(Path(ARBITRE).stem)
    rate = {"reussi": False, "relatif": 0.0}
    random.seed(budget.graine)
    try:
        education = Mother().raise_son(probleme / EXEMPLE, teacher, budget.parties, seed=budget.graine)
        triche = any(record.impossibles for record in education.records if record.number > budget.rodage)
        relatif = mesurer(education, arbitre, teacher, budget)
    except BranchementError:
        raise
    except Exception:  # noqa: BLE001 — la mère ne sait pas, ou plante : raté, sans regarder pourquoi
        return rate, None
    return {"reussi": relatif == 1 and not triche, "relatif": relatif}, education


def lire_le_fils(education) -> str:
    """Le bulletin du fils, une fois le score envoyé : une mesure, qui ne change rien."""
    from xander.bulletin import bulletin
    try:
        return bulletin(education, "problème").decrire()
    except Exception as erreur:  # noqa: BLE001 — le score est déjà donné ; on dit seulement pourquoi
        return f"bulletin impossible ({type(erreur).__name__})"


def _enfant(probleme: str, budget_json: str) -> int:
    """Point d'entrée du sous-processus : une ligne ``@@examen {…}`` sur la sortie."""
    debut = time.monotonic()
    budget = Budget(**json.loads(budget_json))
    education = None
    try:
        reponse, education = passer_probleme(Path(probleme), budget)
        reponse["duree"] = time.monotonic() - debut
    except BranchementError as erreur:
        reponse = {"branchement": str(erreur)}
    print(MARQUEUR, json.dumps(reponse), flush=True)  # le score d'abord : le bulletin n'y touche plus
    if education is not None:
        print(MARQUEUR_BULLETIN, json.dumps({"texte": lire_le_fils(education)}), flush=True)
    return 0


# --------------------------------------------------------------------------- #
# L'examen
# --------------------------------------------------------------------------- #

def lancer(probleme: Path, numero: int, budget: Budget, limite: float,
           limite_bulletin: float = 0.0) -> Resultat:
    """Le sous-processus a ``limite`` pour envoyer son score, puis ``limite_bulletin`` de plus
    pour le bulletin. Un score envoyé après ``limite`` (mesuré par le sous-processus) est un
    temps dépassé ; un bulletin qui manque ne change pas le score."""
    env = environnement(probleme, budget.graine)
    joueurs = verifier_branchement(probleme, env)
    commande = [sys.executable, "-m", "xander.examen", "--un-probleme", str(probleme),
                "--budget", json.dumps(asdict(budget))]
    debut = time.monotonic()
    try:
        sortie = _sous_processus(commande, env, limite + limite_bulletin).stdout
    except subprocess.TimeoutExpired as arret:  # arrêté : ce qu'il a écrit avant compte encore
        sortie = arret.stdout or ""
        if isinstance(sortie, bytes):
            sortie = sortie.decode("utf-8", errors="replace")
    duree = time.monotonic() - debut
    reponse = _reponse(sortie)
    if reponse is None:  # mort ou arrêté sans répondre (temps, mémoire, plantage de Python…)
        return Resultat(numero, False, 0.0, joueurs, duree)
    if "branchement" in reponse:
        raise BranchementError(f"{probleme.name} : {reponse['branchement']}")
    duree = float(reponse.get("duree", duree))
    if duree > limite:  # le score est arrivé, mais trop tard
        return Resultat(numero, False, 0.0, joueurs, duree)
    bulletin = _reponse(sortie, MARQUEUR_BULLETIN)
    return Resultat(numero, bool(reponse["reussi"]), float(reponse["relatif"]), joueurs, duree,
                    bulletin["texte"] if bulletin else None)


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
    reference = mesure_de_reference()
    limite = budget.facteur * reference
    limite_bulletin = budget.facteur_bulletin * reference
    lignes = [f"Examen blanc : {dossier.name}",
              f"Commit : {commit()}",
              f"Date : {debut:%Y-%m-%d %H:%M}",
              f"Machine : {machine()}",
              f"Tâche de référence : {reference:.3f} s ; limite par problème : {limite:.0f} s "
              f"({budget.facteur:g} fois la référence)",
              f"Budget : {budget.describe()}"
              + ("" if budget == BUDGET else " (budget réduit, ce n'est pas un examen)"),
              f"Problèmes : {len(liste)}", ""]
    for ligne in lignes:
        sortie(ligne)
    resultats = []
    for numero, probleme in enumerate(liste, 1):
        resultat = lancer(probleme, numero, budget, limite, limite_bulletin)
        resultats.append(resultat)
        ligne = (f"Problème {numero} : {'réussi' if resultat.reussi else 'raté'}, score relatif "
                 f"{resultat.relatif:.2f} ({resultat.joueurs} joueur{'s' if resultat.joueurs > 1 else ''}, "
                 f"{resultat.duree:.0f} s)")
        lignes.append(ligne)
        sortie(ligne)
    score = sum(r.reussi for r in resultats)
    relatif = sum(r.relatif for r in resultats) / len(resultats)
    lignes += ["", f"Score : {score}/{len(resultats)} ; score relatif moyen : {relatif:.2f}"]
    sortie(lignes[-2])
    sortie(lignes[-1])
    annexe = ["", "Bulletins des fils (lus après le score, hors de la limite de l'examen) :"]
    for r in resultats:
        texte = r.bulletin or "pas de bulletin (pas de fils, ou temps du bulletin dépassé)"
        annexe.append(f"Problème {r.numero} : " + texte.replace("\n", "\n  "))
    lignes += annexe
    for ligne in annexe:
        sortie(ligne)
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
