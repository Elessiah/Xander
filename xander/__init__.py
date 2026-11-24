"""Xander : une IA sans réseau de neurones.

Une logique mère lit un exemple de partie, en déduit le rôle de chaque fonction
du jeu, puis (à terme) crée des enfants qui jouent et qu'elle corrige.
"""

from xander.mother import Mother

__all__ = ["Mother"]
