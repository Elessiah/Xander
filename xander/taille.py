"""La taille de ce que sait un fils : une longueur de description (le rasoir d'Ockham).

Une seule mesure, partagée par la mère (pour choisir entre deux fils qui jouent aussi bien
tous les cas enregistrés : elle garde le plus court) et par le bulletin (pour nous) :

* les **nœuds** des règles et des briques dont elles dépendent, chaque brique comptée une
  fois : la complexité ne se cache pas dans une brique ;
* les **cases fixées** par les souvenirs et les petits motifs : un souvenir entier fixe toutes
  les cases de la position, un petit motif seulement celles qui comptent (les « ? » ne coûtent
  rien) ; une valeur compte pour une case, un tuple pour chacun de ses termes ;
* le **coup** que demande chaque souvenir ou petit motif : un de plus chacun. Un souvenir dit
  « dans cette position » *et* « jouer ce coup » ; sans ce terme, un souvenir d'une seule valeur
  ne coûterait qu'un, autant qu'un nœud de règle, et la mère préférerait retenir des valeurs
  plutôt qu'une règle qui les explique.

Un souvenir coûte ; une règle qui en remplace plusieurs rapporte. Rien ici n'est propre à un
jeu : une connaissance est un dictionnaire comme celui qu'écrit la mère (``memories``,
``motifs``, ``rules``, ``concepts``), les clés sont celles de :mod:`xander.son_writer`.
"""

from __future__ import annotations

import ast

from xander import concepts


def cases_fixees(cle) -> int:
    """Cases qu'un souvenir fixe : toutes celles de la position, sauf les « ? » d'un petit motif."""
    if isinstance(cle, str):
        if " " in cle:  # une valeur et le trait : la valeur entière (un tuple : chacun de ses termes)
            try:
                valeur = ast.literal_eval(cle.rsplit(" ", 1)[0])
            except (ValueError, SyntaxError):
                return 1
            return len(valeur) if isinstance(valeur, (tuple, list)) else 1
        return sum(c != "?" for c in cle)
    if isinstance(cle, (tuple, list)):
        return len(cle)
    return 1


def noeuds(regles: list[str], definitions: dict) -> int:
    """Nœuds des règles et des briques dont elles dépendent (chaque brique une fois)."""
    noms = list(dict.fromkeys(concepts.dependances(regles, definitions) + list(regles)))
    return sum(definitions[nom].size for nom in noms if nom in definitions)


def cases(knowledge: dict) -> int:
    """Cases fixées par les souvenirs et les petits motifs (un joueur seul : ``motifs``)."""
    return (sum(cases_fixees(cle) for cle in knowledge.get("memories", {}))
            + sum(len(motif) for motif, _ in knowledge.get("motifs", [])))


def coups(knowledge: dict) -> int:
    """Coups demandés : un par souvenir et par petit motif."""
    return len(knowledge.get("memories", {})) + len(knowledge.get("motifs", []))


def taille(knowledge: dict) -> int:
    """La taille totale : nœuds des règles et de leurs briques + cases fixées + coups demandés."""
    return (noeuds(list(knowledge.get("rules", [])), knowledge.get("concepts", {}))
            + cases(knowledge) + coups(knowledge))


def plus_court(avant: dict, apres: dict, egalite: bool = False) -> bool:
    """Le critère de la mère : ``apres`` est gardé s'il est **strictement** plus court que
    ``avant`` ; à taille égale seulement si ``egalite`` (le rasoir ne départage pas : une règle
    qui remplace des souvenirs de même taille qu'elle est gardée, car elle explique plusieurs
    cas et dit quelque chose des positions jamais vues, un souvenir rien).
    Qu'il joue encore bien tous les cas enregistrés, c'est à la mère de le vérifier."""
    t_avant, t_apres = taille(avant), taille(apres)
    return t_apres < t_avant or (egalite and t_apres == t_avant)


__all__ = ["cases", "cases_fixees", "coups", "noeuds", "plus_court", "taille"]
