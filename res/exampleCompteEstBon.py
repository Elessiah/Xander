# include
from Games.CompteEstBon import CompteEstBon

# init
# graine 2 : le même tirage à chaque rejeu (le constructeur tire 1 2 2 6 -> 16,
# puis game.init() tire le suivant : 5 5 10 4 -> 85). Le joueur fait 4 + 5 = 9, puis
# 10 x 9 = 90, puis 90 - 5 = 85 : la cible apparaît, play renvoie True (gagnée)
game = CompteEstBon(2)  # game
etat = game.init()  # array 5

# back
etat = game.back()  # array 5

# player joueur
etat = game.get_game_state()  # array 5
etat = game.play(3, 0, 0)  # array 5

etat = game.get_game_state()  # array 5
etat = game.play(2, 3, 2)  # array 5

etat = game.get_game_state()  # array 5
etat = game.play(2, 1, 1)  # bool

# end player joueur
