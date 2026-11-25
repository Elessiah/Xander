# include
from Games.MotMystere import MotMystere

# init
# graine 10 : le secret est le même à chaque rejeu ; le joueur le trouve au
# quatrième essai (play renvoie True : la partie est gagnée)
# l'état : 6 essais de 5 paires (lettre, réponse) ; '=' bien placée,
# '~' présente ailleurs, '-' absente, '.' essai pas encore joué
game = MotMystere(10)  # game
etat = game.init()  # array 60

# back
etat = game.back()  # array 60

# player joueur
etat = game.get_game_state()  # array 60
etat = game.play("porte")  # array 60

# player joueur
etat = game.get_game_state()  # array 60
etat = game.play("livre")  # array 60

# player joueur
etat = game.get_game_state()  # array 60
etat = game.play("barre")  # array 60

# player joueur
etat = game.get_game_state()  # array 60
fin = game.play("arbre")  # bool

# end player joueur
