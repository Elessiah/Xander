"""Faire jouer humains et Minmax sur les jeux à deux joueurs.

Exemples ::

    python -m Games.GamePlayer morpion --x humain --o minmax
    python -m Games.GamePlayer allumettes --x minmax --o minmax --score 3
    python -m Games.GamePlayer puissance4
"""

import argparse

from Games.Allumettes import Allumettes
from Games.MinmaxAllumettes import minmax_allumettes_play
from Games.MinmaxMorpion import minmax_morpion_play
from Games.Morpion import Morpion
from Games.Puissance4 import Puissance4

GAMES = {
    "morpion": (Morpion, minmax_morpion_play),
    "allumettes": (Allumettes, minmax_allumettes_play),
    "puissance4": (Puissance4, None),
}


def format_score(score: dict) -> str:
    return f"X: {score['X']}, O: {score['O']}, égalité: {score['D']}"


def player_turn(game, score: dict, score_for_win: int):
    """Demande un coup au joueur humain jusqu'à ce qu'il soit valide."""
    turn = game.get_turn()
    print(f"\nTour de {turn}. Score actuel : {format_score(score)}. Objectif : {score_for_win}\n")
    game.print()
    while True:
        answer = input(f"Quelle est ta prochaine action, {turn} ? (q pour quitter)\n --> ").strip()
        if answer.lower() == "q":
            raise KeyboardInterrupt
        try:
            move = int(answer)
        except ValueError:
            move = None
        if move is not None and game.play(move) is not False:
            return
        print("Coup invalide.")


def duo_game_player(game, score_for_win: int, players: dict, minmax=None, xander=None,
                    start_player: str = "R"):
    """Enchaîne les parties jusqu'à ce qu'un joueur atteigne ``score_for_win``.

    ``players`` associe ``"X"``/``"O"`` à ``"Humain"``, ``"Minmax"`` ou ``"Xander"``.
    Les matchs nuls comptent aussi : la série s'arrête après ``3 * score_for_win`` nuls.
    """
    game.init(start_player)
    score = {"X": 0, "O": 0, "D": 0}
    while score["X"] < score_for_win and score["O"] < score_for_win and score["D"] < score_for_win * 3:
        game.get_game_state()  # relance une partie si la précédente est finie
        kind = players[game.get_turn()]
        if kind == "Minmax" and minmax is not None:
            minmax(game)
        elif kind == "Xander" and xander is not None:
            xander(game)
        else:
            player_turn(game, score, score_for_win)
        if game.win:
            game.print()
            print("Match nul !\n" if game.win == "D" else f"{game.win} marque un point !\n")
            score[game.win] += 1
            print(f"Score actuel : {format_score(score)}. Objectif : {score_for_win}")
    return score


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lance une série de parties.")
    parser.add_argument("game", choices=GAMES)
    parser.add_argument("--x", default="humain", choices=["humain", "minmax"])
    parser.add_argument("--o", choices=["humain", "minmax"], help="défaut : minmax s'il existe, sinon humain")
    parser.add_argument("--score", type=int, default=3, help="points nécessaires pour gagner la série")
    parser.add_argument("--start", default="R", choices=["X", "O", "R"], help="premier joueur (R : aléatoire)")
    args = parser.parse_args(argv)

    game_class, minmax = GAMES[args.game]
    if args.o is None:
        args.o = "minmax" if minmax else "humain"
    players = {"X": args.x.capitalize(), "O": args.o.capitalize()}
    if minmax is None and "Minmax" in players.values():
        parser.error(f"pas encore de Minmax pour {args.game}")
    try:
        duo_game_player(game_class(), args.score, players, minmax, start_player=args.start)
    except (KeyboardInterrupt, EOFError):
        print("\nPartie interrompue.")


if __name__ == "__main__":
    main()
