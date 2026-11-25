"""Professeur pour le Morpion à trois joueurs (adversaire de référence, codé à la main).

À trois, le minimax ne s'applique pas tel quel : il n'y a plus « moi contre
l'autre ». On utilise **max^n** (Luckhardt et Irani, 1986) : chaque position
reçoit un vecteur de valeurs, une par joueur, et à chaque nœud le joueur qui a
le trait choisit le coup qui maximise **sa propre** valeur. Les autres joueurs
sont supposés raisonner de la même façon.

Valeurs :

- victoire : ``WIN_SCORE + profondeur restante`` pour le gagnant (gagner vite
  vaut plus), ``-(WIN_SCORE + profondeur restante)`` pour les deux autres
  (perdre tard coûte moins) ;
- nul : 0 pour tout le monde ;
- feuille (profondeur épuisée) : une heuristique. Chaque fenêtre de ``k``
  cases alignées qui ne contient que des pions d'un joueur lui rapporte des
  points selon leur nombre (``WINDOW_POINTS``) ; la note d'un joueur est
  ``2 × ses points - les points des deux autres``.

Trois règles, appliquées à chaque nœud avant la recherche (elles valent aussi
pour les joueurs imaginés dans l'arbre) :

1. **gagner** : s'il existe un coup gagnant, le jouer ;
2. **parer le suivant** : si le joueur suivant peut gagner au prochain coup, se
   mettre sur la case qui le fait gagner (s'il en a deux, la partie est perdue ;
   on en bouche une) ;
3. **parer le troisième, sans compter sur le suivant** : si le joueur d'après
   peut gagner sur une case, la boucher aussi. Max^n pur laisserait ce travail
   au joueur suivant (il a intérêt à parer) ; le professeur ne fait pas ce
   pari, car un adversaire réel (un fils, le hasard) peut ne pas le faire.

Sinon, max^n explore ``depth`` demi-coups. **Départage** : à valeur égale
pour le joueur qui a le trait, on garde le premier coup dans l'ordre fixe des
cases, des plus centrales (celles que traversent le plus de fenêtres) aux
bords, puis par indice croissant. Le professeur est donc déterministe. Les
positions déjà calculées sont gardées en mémoire (le jeu est le même pour tous
les appels), ce qui le rend rapide quand la mère lui fait finir beaucoup de
parties.
"""

from functools import lru_cache

from Games.Morpion3 import DEFAULT_K, DEFAULT_SIZE, PLAYERS, Morpion3, build_lines, next_player

DEFAULT_DEPTH = 3  # un tour complet : moi, le suivant, le troisième
WIN_SCORE = 1000
WINDOW_POINTS = {1: 1, 2: 5}  # pions d'un seul joueur dans une fenêtre (k = 3)


class Geometry:
    """Les fenêtres d'un plateau ``size`` × ``size`` et l'ordre dans lequel on essaie les cases."""

    def __init__(self, size: int, k: int):
        self.size, self.k = size, k
        self.cells = size * size
        self.lines = build_lines(size, k)
        self.lines_by_cell = tuple(tuple(line for line in self.lines if i in line) for i in range(self.cells))
        self.order = tuple(sorted(range(self.cells), key=lambda i: (-len(self.lines_by_cell[i]), i)))
        self.rank = tuple(self.order.index(i) for i in range(self.cells))
        self.points = {count: WINDOW_POINTS.get(count, 5 ** (count - 1)) for count in range(1, k)}


@lru_cache(maxsize=None)
def geometry(size: int = DEFAULT_SIZE, k: int = DEFAULT_K) -> Geometry:
    return Geometry(size, k)


def scan(board, geo: Geometry) -> tuple:
    """Un passage sur toutes les fenêtres : ``(menaces, potentiels)``.

    ``menaces[joueur]`` : la première case (dans l'ordre des cases) où ``joueur``
    complète un alignement ; absent s'il n'en a pas. ``potentiels[joueur]`` :
    les points des fenêtres qui ne contiennent que ses pions.
    """
    threats = {}
    potential = dict.fromkeys(PLAYERS, 0)
    rank, points, last = geo.rank, geo.points, geo.k - 1
    for line in geo.lines:
        owner, count, hole = None, 0, -1
        for i in line:
            slot = board[i]
            if slot.isdigit():
                hole = i
                continue
            if owner is None:
                owner = slot
            elif slot != owner:
                owner = ""
                break
            count += 1
        if owner:
            potential[owner] += points.get(count, 0)
            if count == last:
                best = threats.get(owner)
                if best is None or rank[hole] < rank[best]:
                    threats[owner] = hole
    return threats, potential


def winning_cell(board, player: str, size: int = DEFAULT_SIZE, k: int = DEFAULT_K):
    """La case où ``player`` gagne tout de suite (la première dans l'ordre), ``None`` sinon."""
    return scan(board, geometry(size, k))[0].get(player)


def evaluate(potential: dict) -> tuple:
    """Note heuristique de chaque joueur (dans l'ordre de ``PLAYERS``) : 2 × ses points - ceux des deux autres."""
    total = sum(potential.values())
    return tuple(3 * potential[p] - total for p in PLAYERS)


def win_vector(winner: str, depth: int) -> tuple:
    value = WIN_SCORE + depth
    return tuple(value if p == winner else -value for p in PLAYERS)


def forced_move(threats: dict, turn: str):
    """Règles 2 et 3 : la case à boucher (menace du suivant, sinon du troisième), ``None`` sinon.

    (La règle 1, gagner, se lit directement dans ``threats[turn]``.) Si le suivant
    menace deux cases, la partie est perdue : on bouche la première.
    """
    following = next_player(turn)
    cell = threats.get(following)
    if cell is None:
        cell = threats.get(next_player(following))
    return cell


def maxn(board, turn: str, depth: int = DEFAULT_DEPTH, size: int = DEFAULT_SIZE, k: int = DEFAULT_K) -> tuple:
    """Vecteur des valeurs (une par joueur, dans l'ordre de ``PLAYERS``) de ``board``, ``turn``
    ayant le trait. Le coup précédent n'a pas fini la partie."""
    return _maxn(tuple(board), turn, depth, size, k)


@lru_cache(maxsize=1_000_000)
def _maxn(board: tuple, turn: str, depth: int, size: int, k: int) -> tuple:
    geo = geometry(size, k)
    threats, potential = scan(board, geo)
    if turn in threats:
        return win_vector(turn, depth)          # règle 1 : il gagne au coup suivant
    if depth == 0:
        return evaluate(potential)
    forced = forced_move(threats, turn)
    moves = [forced] if forced is not None else [i for i in geo.order if board[i].isdigit()]
    if not moves:
        return (0, 0, 0)  # plateau plein : nul
    return _choose(board, turn, depth, moves, size, k)[1]


def _choose(board: tuple, turn: str, depth: int, moves: list, size: int, k: int) -> tuple:
    """Le coup de ``moves`` qui maximise la valeur de ``turn`` (le premier à égalité) et son vecteur."""
    me = PLAYERS.index(turn)
    following = next_player(turn)
    best, best_value = None, None
    for move in moves:
        child = board[:move] + (turn,) + board[move + 1:]
        if not any(slot.isdigit() for slot in child):
            value = (0, 0, 0)  # le dernier coup remplit le plateau sans aligner : nul
        else:
            value = _maxn(child, following, depth - 1, size, k)
        if best_value is None or value[me] > best_value[me]:
            best, best_value = move, value
    return best, best_value


def best_move(board, turn: str, depth: int = DEFAULT_DEPTH, size: int = DEFAULT_SIZE, k: int = DEFAULT_K):
    """Le coup du professeur pour ``turn`` ; ``None`` si le plateau est plein."""
    geo = geometry(size, k)
    board = tuple(board)
    threats, _ = scan(board, geo)
    if turn in threats:
        return threats[turn]                    # règle 1 : gagner
    forced = forced_move(threats, turn)
    if forced is not None:
        return forced                           # règles 2 et 3 : parer
    moves = [i for i in geo.order if board[i].isdigit()]
    if not moves:
        return None
    return _choose(board, turn, depth, moves, size, k)[0]


def maxn_morpion3_play(game: Morpion3, verbose: bool = False, depth: int = DEFAULT_DEPTH):
    """Fait jouer le professeur sur ``game``. Renvoie le gagnant si le coup termine la partie."""
    turn = game.get_turn()
    board = game.get_game_state()
    size, k = getattr(game, "size", DEFAULT_SIZE), getattr(game, "k", DEFAULT_K)
    move = best_move(board, turn, depth, size, k)
    if verbose:
        print(f"Max^n {turn} joue {move}")
    if game.play(move) is True:
        return game.win
    return None
