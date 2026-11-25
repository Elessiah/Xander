# include
from Games.Pylos import Pylos

# init
game = Pylos(3)  # game
board = game.init("X")  # array 14

# back
board = game.back()  # array 14

# player X
board = game.get_game_state()  # array 14
board = game.play(8)  # array 14

# player O
board = game.get_game_state()  # array 14
board = game.play(0)  # array 14

# player X
board = game.get_game_state()  # array 14
board = game.play(4)  # array 14

# player O
board = game.get_game_state()  # array 14
board = game.play(1)  # array 14

# player X
board = game.get_game_state()  # array 14
board = game.play(2)  # array 14

# player O
board = game.get_game_state()  # array 14
board = game.play(5)  # array 14

# player X
board = game.get_game_state()  # array 14
board = game.move(8, 10)  # array 14

# player O
board = game.get_game_state()  # array 14
board = game.play(8)  # array 14

# player X
board = game.get_game_state()  # array 14
board = game.play(7)  # array 14

# player O
board = game.get_game_state()  # array 14
board = game.move(0, 12)  # array 14

# player X
board = game.get_game_state()  # array 14
board = game.play(0)  # array 14

# player O
board = game.get_game_state()  # array 14
board = game.play(6)  # array 14

# player X
board = game.get_game_state()  # array 14
board = game.play(3)  # array 14

# player O
board = game.get_game_state()  # array 14
board = game.move(6, 9)  # array 14

# player X
board = game.get_game_state()  # array 14
board = game.play(6)  # array 14
board = game.take(6)  # array 14
board = game.take(10)  # array 14

# player O
board = game.get_game_state()  # array 14
board = game.play(10)  # array 14

# player X
board = game.get_game_state()  # array 14
board = game.play(6)  # array 14
board = game.take(6)  # array 14
board = game.stop()  # array 14

# player O
board = game.get_game_state()  # array 14
board = game.play(6)  # array 14

# player X
board = game.get_game_state()  # array 14
board = game.play(11)  # array 14

# end player X
