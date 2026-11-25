# include
from Games.Mastermind import Mastermind

# init
# graine 0 : le secret est le même à chaque rejeu. Le plateau a 8 rangées de
# 5 cases : les 3 chiffres proposés, les bien placés, les mal placés.
# Une vraie partie, trouvée au sixième essai.
game = Mastermind(0)  # game
plateau = game.init()  # array 40

# back
plateau = game.back()  # array 40

# player X
plateau = game.get_game_state()  # array 40
plateau = game.play(1, 2, 3)  # array 40

plateau = game.get_game_state()  # array 40
plateau = game.play(4, 5, 6)  # array 40

plateau = game.get_game_state()  # array 40
plateau = game.play(4, 1, 5)  # array 40

plateau = game.get_game_state()  # array 40
plateau = game.play(4, 3, 1)  # array 40

plateau = game.get_game_state()  # array 40
plateau = game.play(4, 5, 1)  # array 40

plateau = game.get_game_state()  # array 40
plateau = game.play(4, 4, 1)  # bool

# end player X
