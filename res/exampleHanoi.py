# include
from Games.Hanoi import Hanoi

# init
# 3 disques sur le piquet 0 ; le but : les ranger sur le piquet 2, en 14 coups au plus.
# L'état donne, pour chaque disque (du plus petit au plus grand), son piquet.
# Une vraie partie, pas parfaite : le joueur pose le disque moyen sur le piquet 2
# trop tôt, doit l'en retirer, et range la pile en 10 coups (le minimum est 7).
game = Hanoi(3)  # game
disques = game.init()  # array 3

# back
disques = game.back()  # array 3

# player joueur
disques = game.get_game_state()  # array 3
disques = game.play(0, 1)  # array 3

disques = game.get_game_state()  # array 3
disques = game.play(0, 2)  # array 3

disques = game.get_game_state()  # array 3
disques = game.play(1, 2)  # array 3

disques = game.get_game_state()  # array 3
disques = game.play(2, 0)  # array 3

disques = game.get_game_state()  # array 3
disques = game.play(2, 1)  # array 3

disques = game.get_game_state()  # array 3
disques = game.play(0, 1)  # array 3

disques = game.get_game_state()  # array 3
disques = game.play(0, 2)  # array 3

disques = game.get_game_state()  # array 3
disques = game.play(1, 0)  # array 3

disques = game.get_game_state()  # array 3
disques = game.play(1, 2)  # array 3

disques = game.get_game_state()  # array 3
disques = game.play(0, 2)  # bool

# end player joueur
