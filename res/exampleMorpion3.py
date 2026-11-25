# include
from Games.Morpion3 import Morpion3

# init
game = Morpion3()  # game
board = game.init("X")  # array 16

# back
board = game.back()  # array 16

# player X
board = game.get_game_state()  # array 16
board = game.play(1)  # array 16

# player O
board = game.get_game_state()  # array 16
board = game.play(13)  # array 16

# player Z
board = game.get_game_state()  # array 16
board = game.play(9)  # array 16

# player X
board = game.get_game_state()  # array 16
board = game.play(5)  # array 16

# player O
board = game.get_game_state()  # array 16
board = game.play(2)  # array 16

# player Z
board = game.get_game_state()  # array 16
board = game.play(10)  # array 16

# player X
board = game.get_game_state()  # array 16
board = game.play(8)  # array 16

# player O
board = game.get_game_state()  # array 16
board = game.play(11)  # array 16

# player Z
board = game.get_game_state()  # array 16
board = game.play(6)  # array 16

# player X
board = game.get_game_state()  # array 16
board = game.play(14)  # array 16

# player O
board = game.get_game_state()  # array 16
board = game.play(3)  # array 16

# player Z
board = game.get_game_state()  # array 16
board = game.play(12)  # bool 1

# end player Z
