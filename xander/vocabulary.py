"""Un vocabulaire écrit à la main, qui ne sert plus que de **référence** aux tests.

La mère ne s'en sert pas : elle construit ses propres concepts avec les briques
de :mod:`xander.concepts`. Les tests comparent ce qu'elle a trouvé à ces
concepts (``gagner``, ``parer``, ``fourchette``…).

Chaque concept s'écrit **uniquement** avec quatre notions que la mère apprend
pour chaque jeu, et qu'elle écrit elle-même dans le code du fils :

* ``possibles(etat)`` : les actions permises ;
* ``apres(etat, action, joueur)`` : l'état après une action (vient de l'Analyzer) ;
* ``gagne(etat, joueur)`` : l'état, atteint par un coup de ``joueur``, le fait-il gagner ?
* ``adversaire(joueur)``.

Rien ici ne parle de cases, de lignes ou d'allumettes : le même ``parer`` vaut
pour le Morpion, le Puissance 4 ou les Allumettes, dès que la mère sait écrire
ces quatre notions pour le jeu.

Ces fonctions ne s'exécutent pas dans ce module (les quatre notions n'y
existent pas) : les tests exécutent leur **texte** avec les quatre notions d'un
jeu.

Penser comme un joueur humain (voir CLAUDE.md) : un concept regarde au plus un
coup d'avance sur toutes les réponses ; plus loin, seulement ce qui est forcé.
"""

from __future__ import annotations

import inspect

# Les quatre notions sont fournies par la mère au moment d'exécuter ces textes.
possibles = apres = gagne = adversaire = None  # noqa: E305  (repères pour le lecteur)


def victoires(etat, joueur):
    """Actions qui font gagner ``joueur`` tout de suite."""
    return {a for a in possibles(etat) if gagne(apres(etat, a, joueur), joueur)}


def gagner(etat, moi):
    """Je peux gagner tout de suite : je le fais."""
    return victoires(etat, moi)


def parer(etat, moi):
    """L'adversaire gagnerait au prochain coup : je joue de façon à l'en empêcher."""
    lui = adversaire(moi)
    if not victoires(etat, lui):
        return set()
    return {a for a in possibles(etat) if not victoires(apres(etat, a, moi), lui)}


def fourchette(etat, moi):
    """Je crée deux façons de gagner à la fois : il ne pourra en empêcher qu'une.

    Suite forcée : après mon coup, l'adversaire n'a pas de victoire immédiate,
    il doit parer, et il ne peut pas parer deux menaces.
    """
    lui = adversaire(moi)
    choix = set()
    for a in possibles(etat):
        suite = apres(etat, a, moi)
        if len(victoires(suite, moi)) >= 2 and not victoires(suite, lui):
            choix.add(a)
    return choix


def contre_fourchette(etat, moi):
    """L'adversaire pourrait créer deux menaces à la fois : je l'en empêche.

    Soit j'occupe le terrain, soit je menace : s'il doit parer, il n'a plus le
    temps de faire sa fourchette. Seule la suite forcée est calculée (sa
    parade, puis la mienne s'il menace en parant).
    """
    lui = adversaire(moi)

    def ses_fourchettes(e):
        """C'est à lui : ses coups qui créent deux menaces, une fois les coups forcés joués."""
        if not victoires(e, moi):
            return {b for b in possibles(e) if len(victoires(apres(e, b, lui), lui)) >= 2}
        les_siennes = parades(e, lui)
        if len(les_siennes) != 1:
            return {b for b in les_siennes if len(victoires(apres(e, b, lui), lui)) >= 2}
        e = apres(e, les_siennes[0], lui)  # sa parade, forcée
        ses_menaces = victoires(e, lui)
        if len(ses_menaces) >= 2:
            return set(les_siennes)
        if not ses_menaces:
            return set()
        les_miennes = parades(e, moi)
        if len(les_miennes) != 1:
            return set() if les_miennes else set(les_siennes)
        return ses_fourchettes(apres(e, les_miennes[0], moi))  # ma parade, forcée

    if not ses_fourchettes(etat):
        return set()
    return {a for a in possibles(etat) if not ses_fourchettes(apres(etat, a, moi))}


def attaque(etat, moi):
    """Je menace, ses réponses sont forcées, et au bout j'ai deux menaces à la fois.

    Seule la suite forcée est calculée : à chaque coup, on ne suit que l'unique
    parade (la sienne, puis la mienne s'il menace à son tour). Dès qu'un coup
    n'est plus forcé, la suite s'arrête : ce n'est pas une attaque.
    """
    choix = set()
    for a in possibles(etat):
        suite = apres(etat, a, moi)
        if victoires(suite, moi) and suite_forcee(suite, moi):
            choix.add(a)
    return choix


def parades(etat, joueur):
    """Les actions de ``joueur`` après lesquelles son adversaire ne gagne pas tout de suite."""
    lui = adversaire(joueur)
    return [a for a in possibles(etat) if not victoires(apres(etat, a, joueur), lui)]


def suite_forcee(etat, moi):
    """C'est à lui de jouer : en ne suivant que des coups forcés, j'obtiens deux menaces."""
    lui = adversaire(moi)
    for _ in range(len(possibles(etat))):
        if victoires(etat, lui):
            return False  # il gagne avant moi
        if len(victoires(etat, moi)) >= 2:
            return True   # il ne peut pas tout parer
        if not victoires(etat, moi):
            return False  # rien ne le force
        ses_parades = parades(etat, lui)
        if len(ses_parades) != 1:
            return not ses_parades  # aucune parade : je gagne ; plusieurs : rien de forcé
        etat = apres(etat, ses_parades[0], lui)
        ses_menaces = victoires(etat, lui)
        if len(ses_menaces) >= 2 or not ses_menaces:
            return False  # il gagne, ou je ne suis plus forcé : la suite s'arrête
        mes_parades = parades(etat, moi)
        if len(mes_parades) != 1:
            return False
        etat = apres(etat, mes_parades[0], moi)
    return False


#: Concepts que la mère peut enseigner, dans l'ordre où elle les essaie pour expliquer.
CONCEPTS = [gagner, parer, fourchette, contre_fourchette, attaque]

#: Outils dont dépendent les concepts (recopiés avec eux).
TOOLS = [victoires, parades, suite_forcee]


def source(function) -> str:
    """Le texte d'un concept, tel que la mère le recopie dans le code du fils."""
    return inspect.getsource(function)


def concept_names() -> list[str]:
    return [concept.__name__ for concept in CONCEPTS]


def concept_source(name: str) -> str:
    return source(next(concept for concept in CONCEPTS if concept.__name__ == name))


def tools_source() -> str:
    return "\n\n".join(source(tool) for tool in TOOLS)
