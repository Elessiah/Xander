"""Le bulletin du fils : mesurer la qualité de ce qu'il sait, pas seulement ses victoires.

Un fils peut gagner en ayant **retenu** (une position, un coup) ou en ayant **compris** (une
règle qui explique beaucoup de cas). Le bulletin le dit avec des nombres, pour nous : il lit
une éducation finie (:class:`~xander.education.Education` ou :class:`~xander.un_joueur.Solo`)
et ne modifie rien de ce que sait la mère. Rien de ce qu'il mesure ne revient vers elle.

Mesures (voir ``docs/feuille-de-route.md``, « Le bulletin du fils ») :

* **taille** de ce qu'il sait : nœuds des règles et des briques dont elles dépendent (chaque
  brique comptée une fois), cases fixées par les souvenirs et les petits motifs (un souvenir
  entier fixe toutes les cases de la position, un petit motif seulement celles qui comptent ;
  une valeur compte pour une case), plus un coup demandé par souvenir et petit motif. C'est une
  longueur de description, la même que celle de la mère (:mod:`xander.taille`) : plus court
  vaut mieux ;
* **compression** : cas enregistrés bien joués par le fils, divisés par la taille ;
* **origine des coups** : sur des parties jouées sans correction, la part des coups décidés par
  une règle, un petit motif, un souvenir ou le coup par défaut ;
* **généralisation** : depuis des positions **jamais vues** pendant l'éducation (tirées par le
  bulletin en jouant des coups au hasard depuis le début, avec son propre hasard), la part où
  le fils fait au moins aussi bien que la référence : le professeur à deux joueurs et plus, le
  calcul de la mère dans son labo pour un joueur seul ;
* **solidité des règles** : pour chaque règle, les cas où elle choisirait un coup, ceux où le
  coup qu'elle choisit est bon, ceux où c'est elle qui décide chez le fils ; une règle qui ne
  choisit jamais rien est du code mort ;
* **budget** : positions regardées au plus pour un coup (déjà mesuré par l'éducation).

La stabilité (relancer l'éducation avec d'autres graines et comparer les règles) demande de
nouvelles éducations : c'est :func:`stabilite`, à part, car elle coûte autant que l'éducation.

Les seuils d'interprétation ne sont pas fixés : le bulletin donne des nombres, on les compare
d'un fils à l'autre. La généralisation est le juge ; la mère n'y a jamais accès.
"""

from __future__ import annotations

import contextlib
import io
import random
from dataclasses import dataclass, field

from xander import son_writer, taille
from xander.education import Education, par_defaut
from xander.un_joueur import Solo

#: Positions jamais vues tirées pour mesurer la généralisation ; coups au hasard au plus pour y
#: arriver ; marches au hasard.
POSITIONS, COUPS_AU_HASARD, TENTATIVES = 50, 12, 2000
#: Positions énumérées au plus en largeur depuis le début.
ENUMERATION = 2000
#: Parties sans correction pour l'origine des coups (par place, contre le hasard ; une partie de
#: plus par place contre le professeur).
PARTIES = 10
#: Un joueur seul : coups au plus d'une partie de généralisation.
PLAFOND_SOLO = 150


@dataclass
class Bulletin:
    jeu: str
    joueurs: int
    parties: int                       # parties d'éducation
    souvenirs: int = 0                 # souvenirs entiers
    petits_motifs: int = 0
    cases_fixees: int = 0              # cases fixées par les souvenirs et les petits motifs
    regles: list = field(default_factory=list)
    noeuds: int = 0                    # nœuds des règles et de leurs briques
    cas: int = 0                       # cas enregistrés pendant l'éducation
    cas_bien_joues: int = 0
    origine: dict = field(default_factory=dict)       # raison -> coups
    victoires_par_defaut: tuple = (0, 0)  # (victoires par défaut, victoires) des parties sans correction
    generalisation: tuple = (0, 0)     # (tenues, positions jamais vues)
    victoires: tuple | None = None     # un casse-tête : (gagnées par le fils, par la référence)
    solidite: dict = field(default_factory=dict)      # règle -> {"choisit", "bon", "decide"}
    budget: int = 0

    @property
    def taille(self) -> int:
        # la mesure de :func:`xander.taille.taille` : un coup demandé par souvenir et petit motif
        return self.noeuds + self.cases_fixees + self.souvenirs + self.petits_motifs

    @property
    def compression(self) -> float:
        return self.cas_bien_joues / self.taille if self.taille else float(self.cas_bien_joues)

    def part(self, raison: str) -> float:
        total = sum(self.origine.values())
        return self.origine.get(raison, 0) / total if total else 0.0

    def decrire(self) -> str:
        tenues, vues = self.generalisation
        lignes = [
            f"Bulletin du fils ({self.jeu}, {self.joueurs} joueur(s), {self.parties} parties d'éducation)",
            f"  Taille : {self.taille} = {self.noeuds} nœud(s) de règles et briques + {self.cases_fixees} "
            f"case(s) fixée(s) + {self.souvenirs + self.petits_motifs} coup(s) demandé(s) "
            f"({self.souvenirs} souvenir(s), {self.petits_motifs} petit(s) motif(s))",
            f"  Compression : {self.cas_bien_joues} cas bien joués sur {self.cas} enregistrés, "
            f"{self.compression:.2f} cas par unité de taille",
        ]
        total = sum(self.origine.values())
        if total:
            parts = ", ".join(f"{raison} {n * 100 / total:.0f} %" for raison, n in
                              sorted(self.origine.items(), key=lambda x: (-x[1], x[0])))
            lignes.append(f"  Origine des coups ({total} coups sans correction) : {parts}")
        par_defaut, gagnees = self.victoires_par_defaut
        if gagnees:
            lignes.append(f"  Victoires par défaut : {par_defaut} sur {gagnees} victoire(s) sans correction "
                          f"(plus de la moitié des coups du fils joués par défaut : gagnées sans savoir pourquoi)")
        if vues:
            lignes.append(f"  Généralisation : {tenues} position(s) jamais vue(s) tenue(s) sur {vues} "
                          f"({tenues * 100 / vues:.0f} %)")
            if self.victoires is not None:
                fils, reference = self.victoires
                lignes.append(f"    (la mère, par son calcul, gagne depuis {reference} de ces positions, "
                              f"le fils depuis {fils} ; une égalité sans victoire compte comme tenue)")
        else:
            lignes.append("  Généralisation : aucune position jamais vue trouvée")
        for regle, s in self.solidite.items():
            mort = " — ne choisit jamais : code mort" if not s["choisit"] else ""
            lignes.append(f"  Règle {regle} : choisirait dans {s['choisit']} cas (bon coup dans {s['bon']}), "
                          f"décide dans {s['decide']}{mort}")
        lignes.append(f"  Budget : au plus {self.budget} position(s) regardée(s) pour un coup")
        return "\n".join(lignes)


# --------------------------------------------------------------------------- #
# Ne rien changer à l'éducation
# --------------------------------------------------------------------------- #

@contextlib.contextmanager
def intact(education):
    """Ce que le bulletin fait jouer dans le labo ne laisse aucune trace : ni dans ce que sait
    la mère, ni dans ses mémoires de calcul (coups du professeur, issues, valeurs)."""
    sauve = {nom: getattr(education, nom) for nom in ("max_views", "impossibles", "discovered")
             if hasattr(education, nom)}
    caches = {nom: dict(getattr(education, nom)) for nom in ("teacher_moves", "outcomes", "_judged", "_values")
              if isinstance(getattr(education, nom, None), dict)}
    avant = repr(education.knowledge)
    try:
        with contextlib.redirect_stdout(io.StringIO()):  # les professeurs commentent leurs coups
            yield
    finally:
        for nom, valeur in sauve.items():
            setattr(education, nom, valeur)
        for nom, valeur in caches.items():
            setattr(education, nom, valeur)
        education.lab.goto([])
    if repr(education.knowledge) != avant:
        raise RuntimeError("le bulletin a changé ce que sait la mère")


# --------------------------------------------------------------------------- #
# Taille
# --------------------------------------------------------------------------- #

# La mesure est celle de la mère (:mod:`xander.taille`) : une seule définition pour les deux.
cases_fixees, noeuds = taille.cases_fixees, taille.noeuds


# --------------------------------------------------------------------------- #
# Deux joueurs et plus
# --------------------------------------------------------------------------- #

def raison_du_fils(education: Education, etat, moi, raison: str) -> str:
    """« souvenir » ou « petit motif » (un souvenir à « ? »), sinon la raison du fils."""
    if raison != "souvenir":
        return "défaut" if raison == "défaut" else f"règle {raison}"
    cle, _ = education.mind.rappel(list(etat), moi, education.knowledge["memories"])
    return "petit motif" if cle is not None and "?" in cle else "souvenir"


def cles_equivalentes(education: Education, etat, moi) -> set:
    mind = education.mind
    ici = mind.cle(list(etat), moi)
    cles = {ici}
    for sigma in getattr(mind, "SYMETRIES", [None]):
        if sigma is not None and hasattr(mind, "transformer"):
            cles.add("".join(mind.transformer(ici, sigma)))
    return cles


def atteignables(education, rng: random.Random, permis) -> list[list[tuple]]:
    """Des suites de coups qui mènent à des positions atteignables, non finies, différentes :
    d'abord en largeur depuis le début (au plus :data:`ENUMERATION` positions : tout un petit
    jeu), puis par des coups au hasard (plus loin dans un grand jeu). ``permis()`` : les actions
    à essayer dans la position où est le labo."""
    lab, suites, deja = education.lab, [], set()

    def noter() -> bool:
        cle = (repr(lab.states[-1]), len(lab.moves) % getattr(education, "n", 1))
        if lab.ended or cle in deja:
            return False
        deja.add(cle)
        suites.append(list(lab.moves))
        return True

    lab.goto([])
    noter()
    file = [[]]
    while file and len(suites) < ENUMERATION:
        coups = file.pop(0)
        lab.goto(coups)
        for action in [education.args(a) for a in permis()]:
            lab.goto(coups)
            if lab.play(*action) != "refused" and noter():
                file.append(list(lab.moves))
    for _ in range(TENTATIVES):
        lab.goto([])
        for _ in range(rng.randint(1, COUPS_AU_HASARD)):
            actions = permis()
            if not actions or lab.play(*education.args(rng.choice(actions))) == "end":
                break
        noter()
    rng.shuffle(suites)
    return suites


def positions_jamais_vues(education: Education, graine: int, nombre: int) -> list[list[tuple]]:
    """Des positions atteignables (voir :func:`atteignables`), jamais enregistrées pendant
    l'éducation (à symétrie près), où le joueur au trait a le choix, tirées avec le hasard du
    bulletin. Renvoie les suites de coups qui y mènent."""
    rng, lab, vues = random.Random(f"bulletin-{graine}"), education.lab, set(education.cases)
    trouvees, deja = [], set()
    for coups in atteignables(education, rng, lambda: education.mind.possibles(education.position())):
        if len(trouvees) >= nombre:
            break
        lab.goto(coups)
        etat = education.position()
        moi = education.marks[education.seat(len(coups))]
        if len(education.mind.possibles(etat)) < 2:
            continue
        cles = cles_equivalentes(education, etat, moi)
        if cles & vues or cles & deja:
            continue
        deja |= cles
        trouvees.append(coups)
    return trouvees


def bulletin_plusieurs(education: Education, nom: str, graine: int, positions: int, parties: int) -> Bulletin:
    k = education.knowledge
    b = Bulletin(nom, education.n, len(education.records) - 1)
    memoires = k["memories"]
    b.petits_motifs = sum("?" in cle for cle in memoires)
    b.souvenirs = len(memoires) - b.petits_motifs
    b.cases_fixees = taille.cases(k)
    b.regles = list(k["rules"])
    b.noeuds = noeuds(b.regles, k["concepts"])
    b.budget = education.max_views
    fils = education.son
    with intact(education):
        # Compression et solidité : les cas enregistrés
        pensee = education.pensee
        b.solidite = {r: {"choisit": 0, "bon": 0, "decide": 0} for r in b.regles}
        for cas in education.cases.values():
            coup, raison = fils.choisir(list(cas.state), cas.me)
            b.cas += 1
            b.cas_bien_joues += education.good(cas, coup)
            if raison in b.solidite:
                b.solidite[raison]["decide"] += 1
            permis = education.mind.possibles(list(cas.state))
            for regle in b.regles:
                choix = pensee.choix(education.rule(regle), list(cas.state), cas.me)
                if choix and len(choix) < len(permis):
                    b.solidite[regle]["choisit"] += 1
                    b.solidite[regle]["bon"] += education.good(cas, min(choix))
        # Origine des coups : parties sans correction, à chaque place
        adversaires = [("professeur", education.teacher, 1),
                       ("hasard", education.random_player(random.Random(f"bulletin-{graine}")), parties)]
        for _, adversaire, nombre in adversaires:
            for place in range(education.n):
                for _ in range(nombre):
                    issue_, decisions = education.play_game(adversaire, place)
                    if issue_ == 1:
                        n, g = b.victoires_par_defaut
                        b.victoires_par_defaut = (n + par_defaut(decisions), g + 1)
                    moi = education.marks[place]
                    for _, etat, _, raison in decisions:
                        r = raison_du_fils(education, etat, moi, raison)
                        b.origine[r] = b.origine.get(r, 0) + 1
        # Généralisation : des positions jamais vues, le fils contre le professeur à sa place
        suites = positions_jamais_vues(education, graine, positions)
        tenues = 0
        for coups in suites:
            education.lab.goto(coups)
            etat = education.position()
            moi = education.marks[education.seat(len(coups))]
            coup, _ = fils.choisir(list(etat), moi)
            tenues += education.judge(coups, etat, coup)
        b.generalisation = (tenues, len(suites))
    return b


# --------------------------------------------------------------------------- #
# Un joueur seul
# --------------------------------------------------------------------------- #

def score_solo(education, coups_depart: list[tuple], choisir) -> int:
    """Joue depuis la position où mènent ``coups_depart`` avec ``choisir(coups, etat)`` jusqu'à
    la fin ou au plafond. Une fin gagnée vaut plus que toute survie, plus tôt vaut mieux ; sinon
    le nombre de coups joués (une fin perdue arrête le compte)."""
    lab = education.lab
    lab.goto(list(coups_depart))
    joues = 0
    while not lab.ended and joues < PLAFOND_SOLO:
        coups = list(lab.moves)
        action = choisir(coups, education.position())
        lab.goto(coups)  # le calcul de la mère promène le labo : revenir à la position
        if action is None or lab.play(*education.args(action)) == "refused":
            break
        joues += 1
    if lab.ended and education.end_kind() == "gagnée":
        return 10 * PLAFOND_SOLO - joues
    return joues


def bulletin_solo(education, nom: str, graine: int, positions: int, parties: int) -> Bulletin:
    k = education.knowledge
    b = Bulletin(nom, 1, len(education.records) - 1)
    b.souvenirs = len(k["memories"])
    b.petits_motifs = len(k.get("motifs", []))
    b.cases_fixees = taille.cases(k)
    b.budget = education.max_views
    fils = education.son
    with intact(education):
        for cas in education.cases.values():
            valeurs = cas["values"]
            if not valeurs:
                continue
            b.cas += 1
            coup, _ = fils.choisir(cas["state"])
            b.cas_bien_joues += valeurs.get(coup, -1) >= max(valeurs.values())
        for _ in range(parties):
            for _, _, _, raison in education.play_game():
                b.origine[raison] = b.origine.get(raison, 0) + 1
        # Généralisation : depuis des positions jamais vues, le fils contre le calcul de la mère
        rng, lab = random.Random(f"bulletin-{graine}"), education.lab
        vues = {son_writer.state_key(c["state"]) for c in education.cases.values()}
        suites, deja = [], set()
        for coups in atteignables(education, rng, lambda: education.knowledge["actions"]):
            if len(suites) >= positions:
                break
            lab.goto(coups)
            cle = son_writer.state_key(education.position())
            if cle in vues or cle in deja:
                continue
            deja.add(cle)
            suites.append(coups)

        def du_fils(coups, etat):
            return fils.choisir(etat)[0]

        def de_la_mere(coups, etat):
            valeurs = education.values(coups)
            return education.best(valeurs) if valeurs else None

        tenues, gagnees = 0, [0, 0]
        for coups in suites:
            fils_, mere = score_solo(education, coups, du_fils), score_solo(education, coups, de_la_mere)
            tenues += fils_ >= mere
            gagnees[0] += fils_ > PLAFOND_SOLO
            gagnees[1] += mere > PLAFOND_SOLO
        b.generalisation = (tenues, len(suites))
        if k["fin"] == "gagnée":
            b.victoires = tuple(gagnees)
    return b


def bulletin(education, nom: str = "fils", graine: int = 0, positions: int = POSITIONS,
             parties: int = PARTIES) -> Bulletin:
    """Le bulletin d'une éducation finie (voir le module). Ne modifie rien."""
    if isinstance(education, Solo):
        return bulletin_solo(education, nom, graine, positions, parties)
    return bulletin_plusieurs(education, nom, graine, positions, parties)


def stabilite(eleve, graines: list[int]) -> dict:
    """Les règles trouvées par la mère selon la graine de l'éducation. ``eleve(graine)`` rend une
    éducation finie. Des règles qui changent à chaque graine sont des coïncidences."""
    trouvees = {}
    for graine in graines:
        e = eleve(graine)
        k = e.knowledge
        trouvees[graine] = sorted(repr(k["concepts"][r]) for r in k.get("rules", []))
    return trouvees


__all__ = ["Bulletin", "bulletin", "stabilite"]
