"""Tests de Xander. Lancer la CI locale : ``python ci.py`` (``--complet`` pour les tests lents)."""

import os
import unittest

#: Un test lent (une longue éducation, un examen complet en sous-processus) : il ne tourne
#: qu'avec ``python ci.py --complet`` (ou ``XANDER_LENT=1``), pour garder la CI rapide.
lent = unittest.skipUnless(os.environ.get("XANDER_LENT"), "test lent : python ci.py --complet")
