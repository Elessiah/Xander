# include
from Games.Partition import Partition

# init
# morceau 0 : la même partition à chaque rejeu ; le musicien joue juste, puis
# se tait sur une note (play renvoie False) : la partie finit
game = Partition(0)  # game
partition = game.init()  # array 8

# back
partition = game.back()  # array 8

# player musicien
partition = game.get_partition()  # array 8
partition = game.play(False)  # array 8

partition = game.get_partition()  # array 8
partition = game.play(False)  # array 8

partition = game.get_partition()  # array 8
partition = game.play(False)  # array 8

partition = game.get_partition()  # array 8
partition = game.play(False)  # array 8

partition = game.get_partition()  # array 8
partition = game.play(True)  # array 8

partition = game.get_partition()  # array 8
partition = game.play(False)  # array 8

partition = game.get_partition()  # array 8
partition = game.play(False)  # array 8

partition = game.get_partition()  # array 8
partition = game.play(True)  # array 8

partition = game.get_partition()  # array 8
partition = game.play(False)  # array 8

partition = game.get_partition()  # array 8
partition = game.play(False)  # array 8

partition = game.get_partition()  # array 8
partition = game.play(False)  # array 8

partition = game.get_partition()  # array 8
partition = game.play(False)  # array 8

partition = game.get_partition()  # array 8
partition = game.play(False)  # bool

# end
