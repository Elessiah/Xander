"""Lire un problème « entrée -> sortie » (voir ``docs/format-exemple.md``).

Un problème donne quelques **paires** (une entrée, la sortie attendue) et une
ou plusieurs **questions** (une entrée dont il faut trouver la sortie). Ni
partie, ni adversaire, ni action. Les valeurs sont des nombres, des textes,
des booléens et des listes, éventuellement imbriquées : rien n'est propre à
un domaine.

Le fichier est du JSON : un problème, ou un lot de problèmes. Les réponses
attendues aux questions, quand le fichier les donne, sont rangées à part
(:attr:`Probleme.attendues`) : elles servent à l'examinateur pour noter le
fils, **jamais** à la mère (:meth:`Probleme.enonce_pour_la_mere`).

Lien avec la forme commune visée par le jalon 1 (un exemple est une suite
d'observations : un état, ce qui s'est passé, l'état suivant) : une paire est
une suite d'**une seule** observation, où il ne s'est rien passé de visible
(aucune action, aucun joueur) : l'état est l'entrée, l'état suivant la
sortie. Une question est un état dont on ne connaît pas encore le suivant.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class ProblemeMalForme(ValueError):
    """Le fichier ne suit pas le format des problèmes « entrée -> sortie »."""


@dataclass
class Probleme:
    nom: str
    paires: list[tuple]                 # (entrée, sortie)
    questions: list                     # entrées dont il faut trouver la sortie
    attendues: list | None = None       # réponses attendues : pour l'examinateur seulement
    domaine: str = ""                   # pour les humains (ranger, mesurer) ; la mère ne le lit pas
    enonce: str = ""                    # pour les humains ; la mère ne le lit pas
    source: str = ""                    # fichier d'origine

    def enonce_pour_la_mere(self) -> tuple[list[tuple], list]:
        """Ce que la mère reçoit : les paires et les entrées des questions, rien d'autre."""
        return [tuple(p) for p in self.paires], list(self.questions)

    def en_observations(self) -> list[dict]:
        """Les paires dans la forme commune du jalon 1 : (état, ce qui s'est passé, état suivant)."""
        return [{"etat": entree, "action": None, "joueur": None, "suivant": sortie}
                for entree, sortie in self.paires]


def _valeur(v, ou: str):
    """Vérifie qu'une valeur est permise : nombre, texte, booléen, liste de valeurs permises."""
    if isinstance(v, list):
        for i, w in enumerate(v):
            _valeur(w, f"{ou}[{i}]")
        return v
    if isinstance(v, (bool, int, float, str)):
        return v
    genre = "null" if v is None else type(v).__name__
    raise ProblemeMalForme(f"{ou} : valeur non permise ({genre}) ; seuls nombres, textes, "
                           "booléens et listes sont permis")


def _probleme(donnees, ou: str, source: str) -> Probleme:
    if not isinstance(donnees, dict):
        raise ProblemeMalForme(f"{ou} : un problème est un objet JSON")
    inconnues = set(donnees) - {"nom", "domaine", "enonce", "paires", "questions"}
    if inconnues:
        raise ProblemeMalForme(f"{ou} : clé(s) inconnue(s) {sorted(inconnues)}")
    nom = donnees.get("nom") or ou
    paires_brutes = donnees.get("paires")
    if not isinstance(paires_brutes, list) or not paires_brutes:
        raise ProblemeMalForme(f"{ou} ({nom}) : « paires » doit être une liste non vide")
    paires = []
    for i, p in enumerate(paires_brutes):
        if not isinstance(p, dict) or set(p) != {"entree", "sortie"}:
            raise ProblemeMalForme(f"{nom}, paire {i} : il faut exactement « entree » et « sortie »")
        paires.append((_valeur(p["entree"], f"{nom}, paire {i}, entree"),
                       _valeur(p["sortie"], f"{nom}, paire {i}, sortie")))
    questions_brutes = donnees.get("questions", [])
    if not isinstance(questions_brutes, list):
        raise ProblemeMalForme(f"{nom} : « questions » doit être une liste")
    questions, attendues = [], []
    for i, q in enumerate(questions_brutes):
        if not isinstance(q, dict) or "entree" not in q or not set(q) <= {"entree", "sortie"}:
            raise ProblemeMalForme(f"{nom}, question {i} : il faut « entree » (et, au choix, « sortie »)")
        questions.append(_valeur(q["entree"], f"{nom}, question {i}, entree"))
        attendues.append(_valeur(q["sortie"], f"{nom}, question {i}, sortie") if "sortie" in q else None)
    return Probleme(nom=str(nom), paires=paires, questions=questions,
                    attendues=attendues if any("sortie" in q for q in questions_brutes) else None,
                    domaine=str(donnees.get("domaine", "")), enonce=str(donnees.get("enonce", "")),
                    source=source)


def lire_texte(texte: str, source: str = "") -> list[Probleme]:
    """Les problèmes décrits par un texte JSON (un problème, ou ``{"problemes": [...]}``)."""
    try:
        donnees = json.loads(texte)
    except json.JSONDecodeError as erreur:
        raise ProblemeMalForme(f"{source or 'texte'} : JSON invalide ({erreur})") from None
    if isinstance(donnees, dict) and "problemes" in donnees:
        lot = donnees["problemes"]
        if not isinstance(lot, list) or not lot:
            raise ProblemeMalForme(f"{source} : « problemes » doit être une liste non vide")
        domaine = donnees.get("domaine", "")
        problemes = []
        for i, d in enumerate(lot):
            if isinstance(d, dict) and domaine and "domaine" not in d:
                d = {**d, "domaine": domaine}
            problemes.append(_probleme(d, f"problème {i}", source))
        noms = [p.nom for p in problemes]
        doublons = sorted({n for n in noms if noms.count(n) > 1})
        if doublons:
            raise ProblemeMalForme(f"{source} : noms en double {doublons}")
        return problemes
    return [_probleme(donnees, "problème", source)]


def lire_problemes(chemin: str | Path) -> list[Probleme]:
    """Les problèmes du fichier ``chemin``."""
    chemin = Path(chemin)
    return lire_texte(chemin.read_text(encoding="utf-8"), str(chemin))


def est_un_probleme(chemin: str | Path) -> bool:
    """Le fichier est-il un problème « entrée -> sortie » (et non un exemple de partie) ?"""
    return Path(chemin).suffix.lower() == ".json"
