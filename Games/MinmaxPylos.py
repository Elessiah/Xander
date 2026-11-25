"""Joueur Minmax exact pour le Pylos (adversaire de référence, codé à la main).

Sur une base 3 × 3, toutes les positions atteignables tiennent en mémoire :
on les énumère, puis on les résout **à rebours** depuis les fins de partie
(analyse rétrograde). Contrairement à un minimax en profondeur, cette méthode
reste juste quand une partie peut revenir sur une position déjà vue (reprendre
des billes vide la pyramide) : les positions qu'aucun camp ne peut forcer
restent nulles.

Chaque position est notée pour le joueur qui doit agir : gagnée, perdue ou
nulle, avec la distance (en actions) jusqu'à la fin. Le meilleur coup gagne le
plus vite possible, ou perd le plus tard possible.

Pour la base 4 × 4, l'énumération est trop grande : il faudra un Minmax à
profondeur limitée (professeur faillible).

Les positions sont rangées du point de vue du joueur qui agit : ses billes
sont notées ``"X"``, celles de l'adversaire ``"O"``. Une position et sa copie
aux couleurs échangées ne sont donc calculées qu'une fois.
"""

from collections import deque
from functools import lru_cache

from Games.Pylos import EMPTY, PLAY, Pylos, actions, apply_action, pyramide

WIN, LOSS, DRAW = 1, -1, 0
_SWAP = str.maketrans("XO", "OX")


def _key(board, player: str, phase: int) -> tuple:
    text = "".join(board)
    return (text if player == "X" else text.translate(_SWAP)), phase


class Solution:
    """Toutes les positions atteignables d'une pyramide, résolues."""

    def __init__(self, size: int):
        self.geo = geo = pyramide(size)
        self.ids = {}
        self.keys = []
        self.children = []  # par position : [(action, enfant, même joueur ?)]
        start = _key([EMPTY] * geo.nb_spots, "X", PLAY)
        self._add(start)
        queue = deque([0])
        while queue:
            sid = queue.popleft()
            text, phase = self.keys[sid]
            links = []
            for action in actions(geo, text, "X", phase):
                board, player, new_phase = apply_action(geo, text, "X", phase, action)
                key = _key(board, player, new_phase)
                cid = self.ids.get(key)
                if cid is None:
                    cid = self._add(key)
                    queue.append(cid)
                links.append((action, cid, player == "X"))
            self.children[sid] = links
        self._solve()

    def _add(self, key) -> int:
        self.ids[key] = len(self.keys)
        self.keys.append(key)
        self.children.append(None)
        return len(self.keys) - 1

    def _solve(self):
        n = len(self.keys)
        parents = [[] for _ in range(n)]
        for sid, links in enumerate(self.children):
            for _, cid, same in links:
                parents[cid].append((sid, same))
        self.value = [DRAW] * n
        self.dist = [0] * n
        remaining = [len(links) for links in self.children]
        queue = deque()
        for sid in range(n):
            if remaining[sid] == 0:  # plus aucune action : perdu
                self.value[sid] = LOSS
                queue.append(sid)
        solved = [False] * n
        for sid in queue:
            solved[sid] = True
        while queue:
            cid = queue.popleft()
            for sid, same in parents[cid]:
                if solved[sid]:
                    continue
                good = self.value[cid] == (WIN if same else LOSS)
                if good:
                    self.value[sid], self.dist[sid] = WIN, self.dist[cid] + 1
                else:
                    remaining[sid] -= 1
                    if remaining[sid] > 0:
                        continue
                    self.value[sid], self.dist[sid] = LOSS, self.dist[cid] + 1
                solved[sid] = True
                queue.append(sid)

    def outcome(self, board, player: str, phase: int):
        """``(valeur, distance)`` de la position pour ``player``, qui doit agir."""
        sid = self.ids[_key(board, player, phase)]
        return self.value[sid], self.dist[sid]

    def child_outcome(self, cid: int, same: bool):
        """Valeur d'un enfant vue par le joueur qui vient d'agir."""
        value = self.value[cid]
        return (value if same else -value), self.dist[cid]

    def best_action(self, board, player: str, phase: int):
        """Meilleure action ; ``None`` s'il n'y en a aucune."""
        sid = self.ids[_key(board, player, phase)]
        best, best_rank = None, None
        for action, cid, same in self.children[sid]:
            value, dist = self.child_outcome(cid, same)
            # Gagner vite, perdre tard ; une nulle vaut mieux qu'une perte.
            rank = (value, -dist if value == WIN else dist)
            if best_rank is None or rank > best_rank:
                best, best_rank = action, rank
        return best  # les cases sont les mêmes quelle que soit la couleur vue

    def perfect_game(self) -> list:
        """Actions d'une partie où les deux camps jouent parfaitement, depuis le départ."""
        sid, game = 0, []
        board, player, phase = [EMPTY] * self.geo.nb_spots, "X", PLAY
        while self.children[sid]:
            action = self.best_action(board, player, phase)
            game.append(action)
            board, player, phase = apply_action(self.geo, board, player, phase, action)
            sid = self.ids[_key(board, player, phase)]
        return game


@lru_cache(maxsize=None)
def solution(size: int = 3) -> Solution:
    return Solution(size)


def best_action(board, player: str, phase: int, size: int = 3):
    return solution(size).best_action(board, player, phase)


def minmax_pylos_play(game: Pylos, verbose: bool = True):
    """Fait jouer une action à Minmax. Renvoie le gagnant si elle termine la partie."""
    turn = game.get_turn()
    board = game.get_game_state()
    action = best_action(board, turn, game.get_phase(), game.size)
    result = getattr(game, action[0])(*action[1:])
    if verbose:
        print(f"Minmax {turn} : {action}")
    return game.win if result is True else None
