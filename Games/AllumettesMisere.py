"""Jeu des allumettes, variante « misère » jouée jusqu'au bout.

À tour de rôle, chaque joueur retire 1, 2 ou 3 allumettes (pas plus qu'il n'en
reste). La partie ne s'arrête pas quand il reste une allumette : elle finit
quand il n'en reste plus, et **celui qui prend la dernière perd**. Le dernier
coup fait donc perdre celui qui le joue.

C'est le même jeu que :mod:`Games.Allumettes` (qui s'arrête dès qu'il reste une
allumette, puisque le joueur suivant devra la prendre), mais la fin se lit
autrement : à 0 allumette, c'est le joueur qui a le trait qui a gagné.

Professeur : :func:`Games.MinmaxAllumettes.minmax_allumettes_play`, dont la
stratégie (laisser 1, 5, 9… allumettes) vaut pour les deux variantes.
"""

from Games.Allumettes import Allumettes, other_player


class AllumettesMisere(Allumettes):
    def check_win(self):
        """Met à jour ``win`` après le coup de ``player`` : prendre la dernière fait perdre."""
        if self.nb_allumettes < 1:
            self.win = other_player(self.player)
