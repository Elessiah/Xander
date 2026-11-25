"""Les briques des problèmes « entrée -> sortie » : l'équipement de naissance.

Pour transformer une entrée en sortie, la mère compose de petits programmes
(voir :mod:`xander.transformations`). Les briques ci-dessous sont **tout** ce
qu'on lui donne à la main : une liste courte de notions générales, celles
qu'un humain apporte avec lui (une suite, compter, comparer, ajouter). Aucune
n'est propre à un domaine : chacune est justifiée par au moins deux problèmes
d'entraînement de domaines différents (``res/problemes/entrainement/``), et
un test vérifie que les programmes trouvés par la mère s'en servent bien
ainsi.

Une seule convention de perception, fournie elle aussi : **un texte est une
suite de lettres**. ``longueur``, ``premier``, ``inverser``, ``garder``…
valent pour un texte comme pour une liste ; une brique qui rend une suite
rend un texte quand on lui a donné un texte (sauf ``chaque`` et ``couper``, qui
rendent toujours une liste).

Chaque brique est une fonction Python autonome : quand la mère écrit son fils,
elle **recopie** les briques dont le programme trouvé se sert (et seulement
celles-là). Ce qu'elle a vérifié est donc exactement ce que le fils exécute.
Une brique qui n'a pas de sens sur ses valeurs (la longueur d'un nombre, le
premier élément d'une liste vide) lève :class:`Indefini`.

Ne pas importer de Xander ici : ce module est recopié dans le code du fils.
"""


class Indefini(Exception):
    """La brique n'a pas de sens sur ces valeurs (la longueur d'un nombre…)."""


# ---------------------------------------------------------------------- #
# Outils des briques (recopiés dans le fils quand une brique s'en sert)
# ---------------------------------------------------------------------- #

def _cle(v):
    """Clé sans ambiguïté de type : ``1``, ``1.0``, ``True`` et ``"1"`` diffèrent."""
    if isinstance(v, list):
        return ("list", tuple(_cle(w) for w in v))
    return (type(v).__name__, v)


def _meme(a, b):
    """Deux valeurs sont-elles identiques (même type, même valeur) ?"""
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(_meme(v, w) for v, w in zip(a, b))
    return a == b


def _suite(s):
    """``s`` si c'est une suite (une liste, ou un texte : une suite de lettres)."""
    if not isinstance(s, (str, list)):
        raise Indefini
    return s


def _nombre(v):
    """``v`` si c'est un nombre (un booléen n'en est pas un)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise Indefini
    return v


def _comme(s, elements):
    """Les ``elements`` rangés dans une suite du même genre que ``s``."""
    return "".join(elements) if isinstance(s, str) else list(elements)


# ---------------------------------------------------------------------- #
# Les briques, dans l'ordre où la mère les essaie
# ---------------------------------------------------------------------- #

def longueur(s):
    """Le nombre d'éléments d'une suite (de lettres d'un texte)."""
    return len(_suite(s))


def premier(s):
    """Le premier élément d'une suite."""
    s = _suite(s)
    if not s:
        raise Indefini
    return s[0]


def dernier(s):
    """Le dernier élément d'une suite."""
    s = _suite(s)
    if not s:
        raise Indefini
    return s[-1]


def element(s, i):
    """L'élément d'indice ``i`` (le premier a l'indice 0)."""
    s, i = _suite(s), _nombre(i)
    if not isinstance(i, int) or not 0 <= i < len(s):
        raise Indefini
    return s[i]


def inverser(s):
    """La suite lue à l'envers."""
    return _suite(s)[::-1]


def trier(s):
    """La suite rangée dans l'ordre croissant (des éléments d'une même sorte)."""
    s = _suite(s)
    if len({type(v) for v in s}) > 1:
        raise Indefini
    try:
        return _comme(s, sorted(s))
    except TypeError:
        raise Indefini from None


def somme(s):
    """La somme des nombres d'une liste."""
    if not isinstance(s, list):
        raise Indefini
    return sum(_nombre(v) for v in s)


def compter(s, v):
    """Combien d'éléments de la suite valent ``v``."""
    return sum(1 for w in _suite(s) if _meme(w, v))


def positions(s, v):
    """Les indices des éléments de la suite qui valent ``v``."""
    return [i for i, w in enumerate(_suite(s)) if _meme(w, v)]


def couper(s, v):
    """Les morceaux de la suite séparés par les éléments qui valent ``v``."""
    s = _suite(s)
    morceaux, morceau = [], []
    for w in s:
        if _meme(w, v):
            morceaux.append(_comme(s, morceau))
            morceau = []
        else:
            morceau.append(w)
    morceaux.append(_comme(s, morceau))
    return morceaux


def chaque(f, s):
    """La liste de ``f(e)`` pour chaque élément ``e`` de la suite."""
    return [f(e) for e in _suite(s)]


def garder(p, s):
    """Les éléments ``e`` de la suite pour lesquels ``p(e)`` est vrai, dans l'ordre."""
    s = _suite(s)
    gardes = []
    for e in s:
        vrai = p(e)
        if not isinstance(vrai, bool):
            raise Indefini
        if vrai:
            gardes.append(e)
    return _comme(s, gardes)


def plus(a, b):
    """``a + b`` (des nombres)."""
    return _nombre(a) + _nombre(b)


def moins(a, b):
    """``a - b`` (des nombres)."""
    return _nombre(a) - _nombre(b)


def fois(a, b):
    """``a × b`` (des nombres)."""
    return _nombre(a) * _nombre(b)


def egal(a, b):
    """``a`` et ``b`` sont-ils identiques ?"""
    return _meme(a, b)


def inferieur(a, b):
    """``a < b`` (des nombres)."""
    return _nombre(a) < _nombre(b)


def non(b):
    """Le contraire d'un booléen."""
    if not isinstance(b, bool):
        raise Indefini
    return not b


#: Les outils dont les briques peuvent se servir (recopiés dans le fils au besoin).
OUTILS = (_cle, _meme, _suite, _nombre, _comme)
