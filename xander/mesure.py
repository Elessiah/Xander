"""Faire passer des problèmes « entrée -> sortie » et noter les fils.

Deux rôles bien séparés :

* **la mère** reçoit les paires et les entrées des questions
  (:meth:`Probleme.enonce_pour_la_mere`), comprend
  (:func:`xander.transformations.comprendre`), écrit le fils
  (:func:`xander.fils_repondeur.source`) et vérifie qu'il explique toutes les
  paires ;
* **l'examinateur** lance le fils sur les questions et compare ses réponses
  aux réponses attendues. Rien de ce qu'il voit ne revient vers la mère.

Un problème est réussi au premier essai si ``repondre`` donne la réponse
attendue à **toutes** ses questions ; au deuxième si ``deuxieme_essai`` la
donne quand le premier a échoué.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from xander import fils_repondeur
from xander.briques import _cle
from xander.problemes import Probleme
from xander.transformations import Comprehension, comprendre

class _PasDeReponse:
    def __repr__(self) -> str:
        return "je ne sais pas"


#: Ce que le fils répond quand son programme n'a pas de sens sur l'entrée.
PAS_DE_REPONSE = _PasDeReponse()


@dataclass
class Resultat:
    probleme: Probleme
    comprehension: Comprehension
    code: str | None                   # le code du fils (None : la mère n'a rien compris)
    reponses: list = field(default_factory=list)            # premier essai du fils, par question
    deuxiemes: list | None = None                           # deuxième essai, s'il en a un

    @property
    def premier_essai(self) -> bool | None:
        """Réussi au premier essai ? (``None`` si le problème ne donne pas les réponses attendues)."""
        if self.probleme.attendues is None:
            return None
        return self.code is not None and _memes(self.reponses, self.probleme.attendues)

    @property
    def deux_essais(self) -> bool | None:
        """Réussi au premier ou au deuxième essai ?"""
        if self.probleme.attendues is None:
            return None
        return bool(self.premier_essai) or (self.deuxiemes is not None
                                            and _memes(self.deuxiemes, self.probleme.attendues))


def _memes(reponses: list, attendues: list) -> bool:
    return len(reponses) == len(attendues) and all(
        r is not PAS_DE_REPONSE and _cle(r) == _cle(a) for r, a in zip(reponses, attendues))


def _lancer(fils: dict, nom: str, entree):
    try:
        return fils[nom](entree)
    except fils["Indefini"]:
        return PAS_DE_REPONSE


def resoudre(probleme: Probleme) -> Resultat:
    """La mère comprend le problème et écrit le fils ; l'examinateur le lance sur les questions."""
    paires, questions = probleme.enonce_pour_la_mere()
    comprehension = comprendre(paires, questions)
    if not comprehension.comprise:
        return Resultat(probleme, comprehension, None)
    code = fils_repondeur.source(probleme.nom, comprehension, questions)
    ratees = fils_repondeur.verifier(code, paires)
    if ratees:  # ce que la mère a vérifié doit être exactement ce que le fils exécute
        raise AssertionError(f"{probleme.nom} : le fils n'explique pas les paires {ratees}")
    fils = fils_repondeur.charger(code)
    reponses = [_lancer(fils, "repondre", q) for q in questions]
    deuxiemes = [_lancer(fils, "deuxieme_essai", q) for q in questions] if "deuxieme_essai" in fils else None
    return Resultat(probleme, comprehension, code, reponses, deuxiemes)


@dataclass
class Bilan:
    resultats: list[Resultat]

    @property
    def notes(self) -> list[Resultat]:
        return [r for r in self.resultats if r.probleme.attendues is not None]

    @property
    def premier_essai(self) -> int:
        return sum(bool(r.premier_essai) for r in self.notes)

    @property
    def deux_essais(self) -> int:
        return sum(bool(r.deux_essais) for r in self.notes)

    @property
    def duree(self) -> float:
        return sum(r.comprehension.duree for r in self.resultats)

    def decrire(self) -> str:
        n = len(self.notes)
        if not n:
            return f"{len(self.resultats)} problème(s), aucune réponse attendue fournie : pas de score"
        pire = max(self.resultats, key=lambda r: r.comprehension.duree)
        return (f"Score : {self.premier_essai}/{n} au premier essai, {self.deux_essais}/{n} en deux essais ; "
                f"recherche {self.duree:.1f} s en tout, au plus {pire.comprehension.duree:.2f} s "
                f"({pire.probleme.nom})")


def passer(problemes: list[Probleme]) -> Bilan:
    """Fait passer chaque problème (un fils par problème) et rend le bilan."""
    return Bilan([resoudre(p) for p in problemes])
