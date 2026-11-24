# include
from Games.Allumettes import Allumettes

# init
game = Allumettes()  # game
game.set_max_nb_allumettes(10)
nb = game.init("X")  # integer

# back
nb = game.back()  # integer

# player X
nb = game.get_game_state()  # integer
nb = game.play(1)  # integer

# player O
nb = game.get_game_state()  # integer
nb = game.play(2)  # integer

# player X
nb = game.get_game_state()  # integer
nb = game.play(2)  # integer

# player O
nb = game.get_game_state()  # integer
nb = game.play(3)  # integer

# player X
nb = game.get_game_state()  # integer
nb = game.play(1)  # bool

# end player X
