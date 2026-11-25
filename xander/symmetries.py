"""Situations équivalentes : les renumérotations qui ne changent rien au jeu.

Au Morpion, une position tournée de 90° est la même situation. La mère ne le
sait pas d'avance (au Puissance 4, la gravité interdit de retourner le
plateau) : elle cherche les façons de renuméroter les cases qui préservent ce
qu'elle a compris du jeu, puis les vérifie dans son laboratoire.

1. **Candidates** : les permutations ``sigma`` des cases qui envoient chaque
   motif de fin sur un motif de fin. Recherche par retour arrière, case par
   case : une case ne peut aller que sur une case qui appartient au même
   nombre de motifs, et chaque motif dont toutes les cases sont placées doit
   arriver sur un motif. On évite ainsi d'essayer les 9! renumérotations.
2. **Vérification** (dans :mod:`xander.education`) : des parties jouées au
   hasard sont rejouées renumérotées dans le labo. Le jeu doit accepter les
   mêmes coups, passer par les mêmes positions renumérotées et finir au même
   moment. Une permutation qui ne préserve que les motifs déjà compris (et pas
   ceux qui restent à découvrir) est ainsi rejetée.

``sigma[i]`` est la case où va la case ``i``.
"""

from __future__ import annotations


def candidates(size: int, patterns: list[list[int]], limit: int = 5000) -> list[list[int]] | None:
    """Les permutations qui préservent les motifs ; ``None`` s'il y en a trop (motifs trop peu
    nombreux pour dire quelque chose : la mère attend d'en savoir plus)."""
    motifs = {frozenset(p) for p in patterns}
    containing = [[m for m in motifs if i in m] for i in range(size)]
    degree = [len(c) for c in containing]
    sigma: list[int | None] = [None] * size
    used: set[int] = set()
    found: list[list[int]] = []

    def consistent(i: int) -> bool:
        for motif in containing[i]:
            if all(sigma[c] is not None for c in motif) and frozenset(sigma[c] for c in motif) not in motifs:
                return False
        return True

    def place(i: int) -> bool:
        if i == size:
            found.append(list(sigma))
            return len(found) <= limit
        for j in range(size):
            if j in used or degree[j] != degree[i]:
                continue
            sigma[i] = j
            used.add(j)
            if consistent(i) and not place(i + 1):
                return False
            used.discard(j)
            sigma[i] = None
        return True

    if not place(0):
        return None
    return found


def transform(state, sigma: list[int]) -> list:
    """La position renumérotée : ce qui était en case ``i`` passe en case ``sigma[i]``."""
    image = list(state)
    for i, value in enumerate(state):
        image[sigma[i]] = value
    return image
