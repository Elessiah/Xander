"""Comment la mère écrit un fils qui **répond** (problèmes « entrée -> sortie »).

Le fils est un fichier Python autonome : il n'importe rien de Xander (seulement
``json`` et ``sys``, pour lire une entrée et écrire sa réponse). Il contient :

1. le programme que la mère a trouvé (:mod:`xander.transformations`), traduit
   en Python : ``repondre(x)``, et le deuxième essai s'il y en a un ;
2. les briques dont ce programme se sert, **et seulement celles-là**,
   recopiées de :mod:`xander.briques` (avec les outils qu'elles utilisent) :
   ce que la mère a vérifié est exactement ce que le fils exécute ;
3. les entrées des questions du problème, auxquelles il répond quand on le
   lance sans argument.

Le fils ne cherche rien : il exécute son programme. Avant de le livrer, la
mère l'exécute sur toutes les paires (:func:`verifier`) : elles sont les
tests de ce qu'elle a compris.
"""

from __future__ import annotations

import inspect
from pprint import pformat

from xander import briques
from xander.transformations import Comprehension, Noeud

#: Ordre dans lequel les briques sont recopiées (celui du module).
_ORDRE = [nom for nom, objet in vars(briques).items() if inspect.isfunction(objet) and not nom.startswith("_")]


def _briques_utilisees(comprehension: Comprehension) -> list[str]:
    noms = set()
    for essai in comprehension.essais:
        noms |= essai.programme.briques()
    return [nom for nom in _ORDRE if nom in noms]


def _outils(sources: list[str]) -> list[str]:
    """Les outils dont ces sources se servent (et ceux dont ces outils se servent)."""
    besoin, a_voir = [], list(sources)
    while a_voir:
        texte = a_voir.pop()
        for outil in briques.OUTILS:
            if outil.__name__ + "(" in texte and outil.__name__ not in besoin:
                besoin.append(outil.__name__)
                a_voir.append(inspect.getsource(outil))
    return [o.__name__ for o in briques.OUTILS if o.__name__ in besoin]


def _fonction(nom: str, programme: Noeud, quoi: str) -> str:
    return (f"def {nom}(x):\n"
            f'    """{quoi} : sortie = {programme!r} (trouvé par la mère)."""\n'
            f"    return {programme.python()}\n")


def source(nom: str, comprehension: Comprehension, questions: list) -> str:
    """Le code du fils qui répond, tel que la mère l'écrit."""
    if not comprehension.essais:
        raise ValueError("la mère n'a rien compris : elle n'écrit pas de fils qui inventerait")
    premier = comprehension.essais[0]
    utilisees = _briques_utilisees(comprehension)
    sources_briques = [inspect.getsource(getattr(briques, n)) for n in utilisees]
    outils = [inspect.getsource(getattr(briques, n)) for n in _outils(sources_briques)]
    deuxieme = comprehension.essais[1] if len(comprehension.essais) > 1 else None
    parties = [
        f'"""Fils écrit par la mère pour le problème « {nom} » (une entrée -> une sortie).\n\n'
        f"Ce qu'elle a compris, vérifié sur les {comprehension.nb_paires} paires de l'exemple :\n"
        f"    sortie = {premier.programme!r}    (taille {premier.taille})\n"
        + (f"Deuxième essai, s'il faut une autre réponse :\n"
           f"    sortie = {deuxieme.programme!r}    (taille {deuxieme.taille})\n" if deuxieme else "")
        + "\nIl ne contient que ce programme et les briques dont il se sert.\n"
        "Lancé sans argument, il répond aux questions du problème ; sinon à chaque\n"
        "entrée donnée en JSON sur la ligne de commande.\n"
        '"""\n',
        "import json\nimport sys\n",
        inspect.getsource(briques.Indefini),
        *outils,
        *sources_briques,
        "# Ce que la mère a trouvé\n\n" + _fonction("repondre", premier.programme, "Premier essai"),
    ]
    if deuxieme:
        parties.append(_fonction("deuxieme_essai", deuxieme.programme, "Deuxième essai"))
    parties.append(f"QUESTIONS = {pformat(list(questions), width=70, compact=True)}\n")
    parties.append('''def main(argv):
    entrees = [json.loads(a) for a in argv] if argv else QUESTIONS
    for entree in entrees:
        try:
            reponse = json.dumps(repondre(entree), ensure_ascii=False)
        except Indefini:
            reponse = "je ne sais pas"
        print(json.dumps(entree, ensure_ascii=False), "->", reponse)


if __name__ == "__main__":
    main(sys.argv[1:])
''')
    return "\n\n".join(p.rstrip("\n") + "\n" for p in parties)


def charger(code: str) -> dict:
    """Exécute le code du fils (sans le lancer) et renvoie ses fonctions."""
    espace: dict = {"__name__": "fils"}
    exec(compile(code, "<fils>", "exec"), espace)
    return espace


def verifier(code: str, paires: list[tuple]) -> list[tuple]:
    """Les paires que le fils n'explique pas (vide : il les explique toutes)."""
    fils = charger(code)
    ratees = []
    for entree, sortie in paires:
        try:
            reponse = fils["repondre"](entree)
        except fils["Indefini"]:
            reponse = None
        if briques._cle(reponse) != briques._cle(sortie) or reponse is None:
            ratees.append((entree, sortie, reponse))
    return ratees
