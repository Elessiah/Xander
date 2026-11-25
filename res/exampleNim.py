# include
from Games.Nim import Nim

# init
# trois tas de 3, 4 et 5 objets ; X commence. Une vraie partie, pas parfaite :
# X se trompe au premier coup, O au sixième, et X prend le dernier objet.
game = Nim()  # game
game.set_tas(3, 4, 5)
tas = game.init("X")  # array 3

# back
tas = game.back()  # array 3

# player X
tas = game.get_game_state()  # array 3
tas = game.play(2, 2)  # array 3

# player O
tas = game.get_game_state()  # array 3
tas = game.play(1, 4)  # array 3

# player X
tas = game.get_game_state()  # array 3
tas = game.play(0, 1)  # array 3

# player O
tas = game.get_game_state()  # array 3
tas = game.play(2, 1)  # array 3

# player X
tas = game.get_game_state()  # array 3
tas = game.play(0, 2)  # array 3

# player O
tas = game.get_game_state()  # array 3
tas = game.play(2, 1)  # array 3

# player X
tas = game.get_game_state()  # array 3
tas = game.play(2, 1)  # bool

# end player X
