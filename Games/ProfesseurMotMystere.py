"""Professeur du Mot mystère : il déduit le secret des réponses, sans jamais le lire.

Il ne voit que ce que voit le joueur : l'état (l'historique des propositions et
des réponses) et le dictionnaire du jeu. Sa règle, déterministe :

1. garder les mots **compatibles** : ceux qui, s'ils étaient le secret,
   auraient donné exactement chacune des réponses déjà reçues ;
2. parmi eux, proposer celui qui **partage le plus** les mots restants : celui
   dont la réponse prendrait le plus de formes différentes selon le secret
   (chaque forme est un groupe de mots que la réponse laisserait possibles) ;
   à égalité, le premier dans l'ordre alphabétique.

Il ne propose donc que des mots encore possibles : chaque essai peut gagner.
Sur les 405 secrets du dictionnaire, il trouve toujours le mot, en 2,99 essais
en moyenne (premier essai : ``tenir``) (voir ``performances`` et ``docs/jeux.md``).
"""

from __future__ import annotations

from functools import lru_cache

from Games.MotMystere import MotMystere, essais, reponse


def compatibles(etat: list, mots) -> list[str]:
    """Les mots qui auraient donné chacune des réponses déjà reçues."""
    joues = essais(etat)
    return [m for m in mots if all(reponse(propose, m) == recu for propose, recu in joues)]


def groupes(candidat: str, restants) -> int:
    """En combien de groupes la réponse à ``candidat`` partage-t-elle les mots ``restants`` ?"""
    return len({reponse(candidat, secret) for secret in restants})


def meilleur(restants: tuple[str, ...]) -> str:
    """Le mot restant qui partage le plus les restants (à égalité, le premier)."""
    if len(restants) <= 2:
        return restants[0]
    return max(restants, key=lambda candidat: (groupes(candidat, restants), [-ord(c) for c in candidat]))


@lru_cache(maxsize=8)
def _premier(mots: tuple[str, ...]) -> str:
    """Le premier essai ne dépend que du dictionnaire : calculé une fois."""
    return meilleur(mots)


def choisir(etat: list, mots) -> str:
    """Le mot que propose le professeur dans l'état ``etat``."""
    mots = tuple(mots)
    if not essais(etat):
        return _premier(mots)
    restants = tuple(compatibles(etat, mots))
    if not restants:
        raise ValueError("aucun mot du dictionnaire ne donne ces réponses")
    return meilleur(restants)


def professeur_mot_mystere_play(game, verbose: bool = True):
    """Fait jouer le professeur sur ``game``. Renvoie ``game.win`` si le coup finit la partie."""
    etat = game.get_game_state()
    mot = choisir(etat, game.get_moves())
    result = game.play(mot)
    if verbose:
        print(f"Le professeur propose {mot!r}")
    return game.win if result is True else None


def partie(secret: str) -> tuple[bool, int, list[str]]:
    """Le professeur joue une partie contre ``secret`` : (trouvé, essais, propositions)."""
    game = MotMystere(0)
    game.set_secret(secret)
    while not game.win:
        professeur_mot_mystere_play(game, verbose=False)
    return game.win == "joueur", len(game.propositions), list(game.propositions)


def performances(mots=None) -> dict:
    """Le professeur contre chaque secret du dictionnaire : taux de réussite, essais moyens
    (parties gagnées) et répartition du nombre d'essais."""
    mots = MotMystere(0).mots if mots is None else mots
    trouves, total, repartition, rates = 0, 0, {}, []
    for secret in mots:
        gagne, nb, _ = partie(secret)
        if gagne:
            trouves += 1
            total += nb
            repartition[nb] = repartition.get(nb, 0) + 1
        else:
            rates.append(secret)
    return {"secrets": len(mots), "trouves": trouves, "taux": trouves / len(mots),
            "essais_moyens": total / trouves if trouves else None,
            "repartition": dict(sorted(repartition.items())), "rates": rates}


if __name__ == "__main__":
    resultat = performances()
    print(f"premier essai : {_premier(MotMystere(0).mots)!r}")
    print(f"{resultat['trouves']}/{resultat['secrets']} secrets trouvés "
          f"({resultat['taux']:.1%}), {resultat['essais_moyens']:.2f} essais en moyenne")
    print(f"répartition : {resultat['repartition']} ; ratés : {resultat['rates']}")
