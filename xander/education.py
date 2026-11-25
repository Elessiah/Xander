"""Comment la mère élève son fils : jouer, se tromper, comprendre, corriger.

Déroulé ::

    exemple ──► 1re leçon : rejouer l'exemple et comprendre pourquoi il finit
       │
       ▼
    partie du fils (contre le professeur, le hasard ou un adversaire mixte)
       │  fin de partie : la mère comprend qui a gagné et pourquoi (motifs)
       ▼
    revue de chaque décision du fils, avec back
       │  le professeur aurait-il joué autre chose ? était-ce vraiment mieux ?
       │  et s'il avait joué ailleurs ? (variantes de l'adversaire)
       ▼
    chaque erreur ──► souvenir ; puis refactor : souvenirs ──► règle (concept construit)
       │  puis souvenirs restants ──► petits motifs (ce qui comptait, reconnu partout)
       │
       └──► le fils corrigé joue la partie suivante

**Comprendre une fin de partie.** Quand une partie s'arrête, la mère cherche
le *motif* responsable, par contre-épreuve : pour chaque pion du joueur qui a
fini la partie, elle rejoue la partie (avec ``back``) en posant ce pion
ailleurs. Si la partie ne s'arrête plus, le pion était nécessaire. Les pions
nécessaires et le dernier coup forment le motif (au Morpion : un alignement).
Une fin sans motif est un match nul.

**Comprendre une erreur.** Pour chaque décision du fils, la mère revient à la
position, demande son coup au professeur, puis fait finir la partie au
professeur des deux côtés, après le coup du fils et après celui du professeur.
Si le coup du professeur mène à un meilleur résultat, c'est une erreur.

**Corriger cas par cas, puis refactoriser.** La mère part sans aucun concept.
Chaque erreur devient d'abord un **souvenir** (dans cette position, jouer le
coup du professeur) et un **cas** enregistré. Après chaque partie, elle cherche
le plus petit concept (voir :mod:`xander.concepts`) vrai après le coup du
professeur et faux après celui du fils dans au moins deux souvenirs. Elle
l'essaie comme règle, à chaque rang de priorité en partant du plus bas : si le
fils joue encore bien dans **tous** les cas enregistrés (les cas sont les tests
du refactor) et qu'au moins deux souvenirs deviennent inutiles, elle les
remplace par la règle. Le concept devient une brique pour les suivants.

**Petits motifs.** Chaque souvenir restant est réduit à ce qui comptait (les
autres cases deviennent « ? »), puis essayé décalé ; les deux sont vérifiés
dans les cas enregistrés et dans des positions imaginées dans le labo. Le fils
reconnaît ensuite ce petit motif partout où il apparaît.

**Cases et actions.** La mère raisonne en cases : un motif, un souvenir, une
symétrie parlent des cases du plateau. Une action remplit une case : celle que
prédit le programme qu'elle a construit pour décrire l'action (Morpion :
``changees = case(arg0)``, Puissance 4 :
``changees = premiere_de(portee(arg0), valant(' '))``,
voir :mod:`xander.effets`), après l'avoir mis à l'épreuve dans le labo. Sa
perception (``case_jouee``, ``action_pour``) fait le lien ; elle a rejoué
chaque action dans le labo pour savoir quelles cases elle peut remplir.

**Une valeur au lieu d'un tableau.** Quand l'état est un nombre (le programme
qui décrit l'action a la forme ``apres``), il n'y a ni cases ni pions : la
position vue est ``[valeur, trait]`` (une valeur ne dit pas qui doit jouer),
les actions permises sont des bornes sur la valeur d'après
(:func:`effets.bornes`), et une fin de partie est une valeur, vérifiée par
contre-épreuve dans le labo, avec le joueur qu'elle fait gagner (celui qui
vient de jouer, ou celui qui a le trait), lu dans l'exemple. Motifs décalés,
symétries et petits motifs ne s'appliquent pas ; un souvenir retient l'action.

Limites : jeux à deux joueurs qui jouent chacun leur tour ; état en tableau
dont chaque action remplit une case, ou état qui est un nombre.
"""

from __future__ import annotations

import itertools
import math
import random
from dataclasses import dataclass, field

from xander.game_model import GameModel
from xander.lab import Lab, LabError
from xander.parser import ParsedExample
from xander import concepts, effets, son_writer, symmetries
from xander.concepts import MOI

RESULTS = {1: "victoire", 0: "nul", -1: "défaite"}

#: Le fils pense comme un joueur humain : il reconnaît, il ne calcule pas tout.
#: La mère refuse une règle qui lui ferait regarder plus de positions pour un coup.
BUDGET = 1000

#: Coups que la mère joue dans son labo pour mettre à l'épreuve la description de l'action.
EXPERIENCES = 40
#: Parties d'exploration (par curiosité) : ce qu'elle y voit sert à décrire l'action.
PARTIES_D_ESSAI = 8
#: Nouvelles recherches de programme permises quand le labo a tout réfuté.
REPRISES = 3
#: Refus de suite après lesquels la mère cesse d'essayer des entiers plus loin.
PATIENCE = 2
#: État valeur : depuis combien de valeurs différentes la mère vérifie qu'une fin en est une.
CONTRE_EPREUVES = 3
#: Action à plusieurs arguments : combinaisons essayées pour savoir si une valeur d'un argument
#: est permise (les autres arguments prennent les valeurs vues dans l'exemple) ; actions au plus.
COMBINAISONS_ARGUMENT, ACTIONS_MAX = 50, 1000
#: Coups joués au plus pour chercher, un coup plus loin que l'exploration, des positions d'où une
#: action mène à une fin (contre-épreuve d'une fin).
SOURCES_MAX = 3000
#: Coups joués au plus pour mettre à l'épreuve « quand une action est permise » (tableau sans pions).
EPREUVES_LIBERTE = 600


def gele(valeur):
    """Une valeur hachable : une liste devient un tuple (un état en liste sert de clé)."""
    if isinstance(valeur, list):
        return tuple(gele(v) for v in valeur)
    return valeur


@dataclass
class Lesson:
    """Une erreur du fils, et ce que la mère en a tiré."""

    position: str      # cle(etat, moi) de la position (M : fils, A : adversaire)
    son_cell: int
    son_reason: str
    teacher_cell: int
    explanation: str   # "souvenir" : la mère corrige d'abord le cas
    change: str        # ce qui a changé chez le fils

    def __str__(self) -> str:
        board = self.position
        return (f"{board} : le fils a joué {self.son_cell} ({self.son_reason}), "
                f"le professeur {self.teacher_cell} -> {self.explanation} ; {self.change}")


@dataclass
class Case:
    """Une position revue par la mère, qui sert ensuite de test aux refactors.

    Une erreur du fils y laisse un souvenir ; une position bien jouée reste un
    test de non-régression (un refactor ne doit pas la faire mal jouer).
    """

    moves: list[tuple]   # la partie jusqu'à la position (pour y revenir dans le labo)
    state: list
    me: object
    key: str
    son_cell: int        # l'action du fils (au Morpion, la case ; au Puissance 4, la colonne)
    teacher_cell: int    # l'action du professeur ; le souvenir, lui, retient la case remplie


@dataclass
class GameRecord:
    number: int
    opponent: str
    son_side: str
    result: str
    lessons: list[Lesson] = field(default_factory=list)
    patterns: list[list[int]] = field(default_factory=list)  # motifs découverts pendant la partie
    refactors: list[str] = field(default_factory=list)       # souvenirs remplacés par une règle
    impossibles: list[str] = field(default_factory=list)     # coups du fils refusés par le jeu

    def __str__(self) -> str:
        text = f"partie {self.number:>3} | fils {self.son_side} contre {self.opponent:<10} : {self.result:<8}"
        text += f" | {len(self.lessons)} erreur(s)"
        if self.impossibles:
            text += f" | {len(self.impossibles)} coup(s) impossible(s)"
        for impossible in self.impossibles:
            text += f"\n      {impossible}"
        for pattern in self.patterns:
            text += f"\n      {pattern}" if isinstance(pattern, str) else f"\n      motif compris : {pattern}"
        for lesson in self.lessons:
            text += f"\n      {lesson}"
        for refactor in self.refactors:
            text += f"\n      refactor : {refactor}"
        return text


def random_player(rng: random.Random, actions: list, action: str, getter: str, end_signal):
    """Adversaire faible : essaie au hasard les actions que la mère a trouvées, jusqu'à ce que le
    jeu en accepte une (il les connaît par leurs noms dans l'exemple, comme le fils). ``actions`` :
    les arguments de chaque action (des tuples)."""
    def play(game):
        state = getattr(game, getter)()
        for arguments in rng.sample(actions, len(actions)):
            result = getattr(game, action)(*arguments)
            if type(result) is type(end_signal) and result == end_signal:
                return  # la partie est finie : ne pas relire l'état
            if getattr(game, getter)() != state:
                return
    play.__name__ = "hasard"
    return play


def mixed_player(teacher, rng: random.Random, randomly):
    """Adversaire imprévisible : une fois sur deux le coup du professeur, sinon un coup au hasard.

    Il crée des menaces comme le professeur, mais pas toujours les mêmes : le
    fils rencontre ainsi des positions variées et difficiles.
    """
    def play(game):
        (teacher if rng.random() < 0.5 else randomly)(game)
    play.__name__ = "mixte"
    return play


@dataclass
class Trials:
    """Les expériences de la mère sur l'action : ce qui a résisté, ce qui a été réfuté et par quoi."""

    survivors: list
    played: int = 0
    refutations: dict = field(default_factory=dict)  # hypothèse -> cas qui la contredit
    retries: int = 0                                  # nouvelles recherches après une réfutation

    def describe(self) -> str:
        text = f"{self.survivors[0]!r}" if self.survivors else "rien"
        if len(self.survivors) > 1:
            others = ", ".join(map(repr, self.survivors[1:]))
            text += f" (indiscernable de {others})"
        refuted = f", {len(self.refutations)} réfutée(s)" if self.refutations else ""
        if self.retries:
            refuted += f" ({', '.join(map(repr, self.refutations))}), {self.retries} nouvelle(s) recherche(s)"
        return f"{text} : {self.played} expérience(s) dans le labo{refuted}"


class Education:
    def __init__(self, parsed: ParsedExample, model: GameModel, teacher, seed: int = 0):
        state = model.getter.return_value.name if model.getter else None
        observed = (model.report.cases.get(model.action.name, {}).get(state, [])
                    if model.report and model.action else [])
        forms = {case.forme for case in observed}
        if effets.CHANGEES in forms:
            self.forme = effets.CHANGEES             # un tableau : l'action change des cases
        elif effets.APRES in forms:
            self.forme = effets.APRES                # une valeur : l'action donne la valeur d'après
        else:
            raise LabError("l'exemple ne montre ni quelles cases change l'action, ni quelle valeur "
                           "elle donne : la mère ne peut pas encore éduquer de fils")
        self.tableau = self.forme == effets.CHANGEES  # un tableau dont les pions disent qui a joué
        self.liste = False                           # un tableau sans pions (la position porte le trait)
        self.formes = (self.forme,)                 # formes de description acceptées
        self.parsed = parsed
        self.model = model
        self.lab = Lab(parsed, model)
        self.teacher = teacher
        self.seed = seed
        self.rng = random.Random(seed)
        self.knowledge = son_writer.empty_knowledge(model)
        self.width = self.knowledge["largeur"] = self.arity()
        self.knowledge["actions"] = self.discover_actions()
        if not self.alternate():
            raise LabError("dans l'exemple, deux joueurs ne jouent pas chacun leur tour : "
                           "la mère ne sait encore éduquer un fils que pour ces jeux-là")
        self.endings: list[tuple] = []               # coups acceptés qui ont fini la partie (état avant, arguments)
        positions, seen = self.explore()
        self.positions = positions                   # positions vues en explorant (coups, état)
        self.seen = seen                             # coups vus en explorant (cas, joueur)
        lab_cases = [case for case, _ in seen]
        if self.tableau:
            # Ce que chaque action remplit et la valeur qu'elle écrit : déduits de ce qu'elle a vu.
            self.knowledge["reach"] = effets.portees_observees(lab_cases)
            self.knowledge["written"] = effets.ecriture(seen)
            if self.knowledge["written"] != ("joueur",):
                # La valeur écrite ne dit pas qui a joué (au Nim, le tas perd ce qu'on y prend) :
                # pas de pions, la position portera le trait, comme pour une valeur.
                self.tableau, self.liste = False, True
                self.formes = (effets.CHANGEES, effets.ECRITES)
        # Avec ces portées, elle cherche de nouveau le programme qui explique les coups de
        # l'exemple et ceux de son exploration (l'Analyzer seul n'a que l'exemple).
        # (un coup refusé n'a rien changé : il n'y a rien à expliquer, il sert à `free`)
        observed = list(observed) + [c for c in lab_cases if c.valeur_apres != c.valeur_avant]
        effects = [h for h in effets.decouvrir(observed, portees=self.knowledge["reach"])
                   if h.forme in self.formes]
        if not effects:
            raise LabError("aucun programme n'explique ce que change l'action, même avec ce "
                           "que la mère a vu dans le labo : elle ne peut pas encore éduquer de fils")
        self.trials = self.test_effects(effects, observed, positions)
        # Les programmes qui restent ont résisté à toutes les expériences : quand il en reste
        # plusieurs, aucune ne les a départagés, et la mère prend le premier trouvé.
        self.knowledge["effect"] = self.trials.survivors[0]
        # Quand une case peut être jouée (une action est permise) : déduit des coups joués et
        # des coups refusés.
        self.knowledge["start"] = self.copy(self.lab.states[0])
        self.lab_cases = lab_cases                   # coups vus (joués et refusés) : la perception en vient
        if self.liste:
            self.describe_writing()
        self.knowledge["free"] = self.free()
        if self.liste and self.knowledge["free"] is None:
            self.knowledge["free"] = effets.Condition()  # provisoire : les épreuves du labo trancheront
        if self.knowledge["free"] is None:
            raise LabError("la mère ne sait pas dire quand une action peut être jouée : "
                           "elle ne peut pas encore éduquer de fils")
        self._son = self._mind = None               # code du fils et espace de pensée, à réécrire
        self.max_views = 0                           # plus grand nombre de positions regardées par le fils
        self.impossibles: list[str] = []             # coups du fils refusés par le jeu (partie en cours)
        self.marks: dict[int, object] = {}          # parité du coup -> pion posé
        self.outcomes: dict[tuple, int | None] = {}  # position -> parité du gagnant (None : nul)
        self.teacher_moves: dict[tuple, tuple] = {}
        self.discovered: list[list[int]] = []
        self.records: list[GameRecord] = []
        self.cases: dict[str, Case] = {}            # cle de la position -> cas enregistré
        self._pensee = None                          # évalue les concepts (à refaire si le jeu est mieux compris)
        self._bank = None                            # concepts énumérés par taille (à refaire si une brique s'ajoute)
        self._judged: dict = {}                      # (cas, coup) -> aussi bon que le professeur ?
        self._symmetries_known = False               # à chercher de nouveau si un motif s'ajoute
        self._shapes_known = False                   # motifs à essayer décalés (idem)
        self._shifts_tried: set = set()              # motifs décalés déjà essayés dans le labo
        self._generalized: set = set()               # souvenirs déjà réduits à un petit motif
        self.combinations = 100                      # petits motifs essayés d'abord, du plus petit au plus grand
        self.variants = None                         # autres coups adverses revus par coup (None : tous)
        self.sieve = 5                               # positions imaginées pour un oubli, avant la vérification finale
        self.max_size, self.max_depth = 6, 2         # bornes de la recherche de concepts
        self.counts = (1,)                           # valeurs de k dans AuMoins(k, …) : « il existe »
        self.budget = BUDGET                         # positions que le fils peut regarder pour un coup
        self.unknown_ends: list = []                 # état valeur : fins vues dont elle ignore le gagnant
        if not self.tableau:
            # Une valeur ne garde pas trace de qui a joué : les joueurs sont ceux de l'exemple,
            # dans l'ordre où ils y jouent (la position est [valeur, trait]).
            owners = self.owners()
            self.marks = {0: owners[0], 1: owners[1]}
            self.knowledge["marks"] = [owners[0], owners[1]]
        if self.liste:
            self.free_fixes = self.test_free()
            self.check_perception()

    # ------------------------------------------------------------------ #
    # Mettre à l'épreuve la description de l'action
    # ------------------------------------------------------------------ #

    def test_effects(self, effects: list, observed: list, positions: list) -> Trials:
        """Joue dans le labo des coups que l'exemple ne montrait pas, pour réfuter ou départager.

        Les positions viennent de l'exemple et de l'exploration (voir :meth:`explore`) ;
        les arguments essayés sont les actions trouvées et les valeurs de l'exemple.
        La mère joue d'abord les expériences qui départagent les hypothèses
        restantes (elles n'annoncent pas toutes la même chose), puis d'autres,
        au hasard en partant des positions les plus proches du début, pour
        tenter de réfuter ce qui reste.

        Si plus rien ne résiste, elle apprend du contre-exemple : chaque coup
        joué devient un cas de plus, et elle cherche de nouveau le plus petit
        programme qui explique les cas de l'exemple **et** ceux du labo (au plus
        :data:`REPRISES` fois), avec des portées revues à la lumière de ces
        nouveaux coups. Si elle n'en trouve aucun, elle sait qu'elle n'a pas
        compris l'action.
        """
        rng, lab, trials = random.Random(f"effets-{self.seed}"), self.lab, Trials(list(effects))
        reach = self.knowledge["reach"]
        calls = [f for f in self.parsed.player_functions() if f.name == self.model.action.name]
        example = [tuple(f.arguments) for f in calls]
        if self.width > 1:  # les actions trouvées, et celles de l'exemple
            candidates = list(dict.fromkeys([self.args(a) for a in self.knowledge["actions"]] + example))
        else:
            values = list(dict.fromkeys(list(self.knowledge["actions"]) + [a for f in calls for a in f.arguments]))
            width = len(self.model.action.parameters)
            candidates = list(itertools.product(values, repeat=width))[:200]
        seen = {(tuple(example[:k]), example[k]) for k in range(len(example))}

        experiences = [(m, state, a) for m, state in positions for a in candidates
                       if (tuple(m), a) not in seen]
        rng.shuffle(experiences)
        experiences.sort(key=lambda e: len(e[0]))  # d'abord près du début : le contre-exemple le plus simple

        survivors, gathered = trials.survivors, []  # gathered : les cas observés dans le labo
        while trials.played < EXPERIENCES and experiences:
            if not survivors:
                if trials.retries >= REPRISES:
                    break
                trials.retries += 1
                # les nouveaux coups montrent peut-être des cases qu'une action remplit aussi
                reach = self.knowledge["reach"] = effets.portees_observees(list(observed) + gathered)
                survivors = [h for h in effets.decouvrir(list(observed) + gathered, portees=reach)
                             if h.forme in self.formes]
                for hypothesis in survivors:  # réfutée avec des portées incomplètes, pas avec celles-ci
                    trials.refutations.pop(hypothesis, None)
                trials.survivors = survivors
                if not survivors:
                    break
            index = next((i for i, (_, state, a) in enumerate(experiences)
                          if effets.decisive(survivors, state, a, reach)), 0)
            moves, _, arguments = experiences.pop(index)
            if not lab.goto(moves) or lab.ended:
                continue
            before = lab.states[-1]
            trials.played += 1
            try:
                outcome = lab.play(*arguments)
            except Exception:  # le jeu ne supporte pas cette expérience : on repart d'une partie neuve
                lab.new_game()
                continue
            if outcome == "moved":
                case = effets.Cas(before, arguments, lab.states[-1])
                gathered.append(case)
                kept = effets.departager(survivors, case, reach)
                for hypothesis in survivors:
                    if hypothesis not in kept:
                        trials.refutations[hypothesis] = case
                survivors = trials.survivors = kept
            if outcome != "refused":
                lab.undo()
        lab.goto([])
        if not survivors:
            case = next(iter(trials.refutations.values()))
            call = f"{self.model.action.short_name}({', '.join(map(repr, case.arguments))})"
            seen = (f"a changé les cases {sorted(case.cible())}" if case.forme == effets.CHANGEES
                    else f"a donné {case.cible()!r}")
            raise LabError(f"le labo a réfuté {list(trials.refutations)} : sur {case.valeur_avant}, {call} "
                           f"{seen}, et aucun programme n'explique tous les cas ; "
                           "l'Analyzer doit d'abord mieux comprendre l'action")
        return trials

    # ------------------------------------------------------------------ #
    # Perception
    # ------------------------------------------------------------------ #

    def arity(self) -> int:
        """Combien d'arguments prend l'action (vu dans l'exemple) : au Morpion un (la case), au Nim
        deux (le tas, le nombre), au Compte est bon trois (deux places et l'opération)."""
        calls = [f for f in self.parsed.player_functions() if f.name == self.model.action.name]
        return max([len(f.arguments) for f in calls] + [1])

    def action(self, arguments: tuple):
        """Une action telle que la mère et le fils la retiennent : son argument, ou le tuple de ses
        arguments quand elle en a plusieurs (souvenirs, règles, petits motifs la retiennent
        entière)."""
        return tuple(arguments) if self.width > 1 else arguments[0]

    def args(self, action) -> tuple:
        """Les arguments à passer au jeu pour jouer ``action`` (l'inverse de :meth:`action`)."""
        return tuple(action) if self.width > 1 else (action,)

    def copy(self, state):
        """Une copie d'un état lu dans le jeu (un tableau se copie, une valeur non)."""
        return list(state) if isinstance(state, list) else state

    def position(self) -> list:
        """La position que voit la mère dans le labo. Un tableau dit qui a joué (les pions) ;
        une valeur non, ni un tableau sans pions (au Nim, des tas) : la position est alors
        ``[valeur, trait]``, le trait étant le joueur qui doit jouer (la parité du coup : elle a
        vu dans l'exemple que les joueurs alternent). Un tableau y devient un tuple."""
        lab = self.lab
        if self.tableau:
            return list(lab.states[-1])
        return [gele(lab.states[-1]), self.marks[len(lab.moves) % 2]]

    def start_position(self) -> list:
        """La position du début de la partie, telle que la mère la voit."""
        start = self.lab.states[0]
        return list(start) if self.tableau else [gele(start), self.marks[0]]

    def raw(self, position):
        """L'état du jeu dans une position vue par la mère (sans le trait)."""
        if self.tableau:
            return list(position)
        return list(position[0]) if isinstance(position[0], tuple) else position[0]

    def free(self) -> tuple | None:
        """Quand une action peut être jouée, déduit des coups joués, refusés et de ceux qui ont
        fini la partie (voir :func:`effets.liberte` ; pour un tableau sans pions, dont la valeur
        écrite dépend des valeurs, :func:`effets.liberte_valeurs`)."""
        if self.liste:
            return effets.liberte_valeurs(self.knowledge["effect"], self.knowledge["ecritures"], self.lab_cases,
                                          self.knowledge["reach"], acceptes=self.endings)
        return effets.liberte(self.knowledge["effect"], self.lab_cases, self.knowledge["start"],
                              self.knowledge["reach"], acceptes=self.endings)

    def describe_writing(self) -> None:
        """Ce qu'écrit chaque partie de l'action (voir :func:`effets.ecritures`), déduit des coups
        de l'exemple et de l'exploration. Sinon, elle sait qu'elle ne le comprend pas."""
        ecrits = effets.ecritures(self.knowledge["effect"], self.seen, self.knowledge["reach"])
        if ecrits is None:
            raise LabError("la mère ne sait pas décrire la valeur que l'action écrit : "
                           "elle ne peut pas encore éduquer de fils")
        self.knowledge["ecritures"] = ecrits

    def test_free(self) -> int:
        """Met à l'épreuve, dans le labo, ce qu'elle a compris de « quand une action est permise ».

        Depuis les positions vues en explorant (les plus proches du début d'abord, chaque état
        une fois), elle joue chaque action et compare au jeu ce qu'elle prévoyait : un coup
        qu'elle croyait permis et que le jeu refuse (ou l'inverse) devient une observation de
        plus, et elle cherche de nouveau la condition (:meth:`free`). Au plus
        :data:`EPREUVES_LIBERTE` coups. Renvoie le nombre de corrections. C'est ce qu'elle fait
        déjà pour la description de l'action (:meth:`test_effects`) : un contre-exemple joué dans
        le labo vaut mieux qu'un coup impossible du fils."""
        lab, played, fixes, seen = self.lab, 0, 0, set()
        actions = [self.args(a) for a in self.knowledge["actions"]]
        for path, state in sorted(self.positions, key=lambda p: len(p[0])):
            if played >= EPREUVES_LIBERTE:
                break
            if gele(state) in seen:
                continue
            seen.add(gele(state))
            surprises = []
            for arguments in actions:
                if played >= EPREUVES_LIBERTE or not lab.goto(list(path)) or lab.ended:
                    break
                before = self.copy(lab.states[-1])
                predicted = gele(self.mind.valeur_apres(before, arguments))
                outcome = lab.play(*arguments)
                played += 1
                if outcome == "refused":
                    if predicted is None:
                        continue
                    self.lab_cases.append(effets.Cas(before, arguments, self.copy(before)))
                elif outcome == "moved":
                    if predicted == gele(lab.states[-1]):
                        continue
                    case = effets.Cas(before, arguments, self.copy(lab.states[-1]))
                    self.lab_cases.append(case)
                    self.seen.append((case, self.player_of(path)))
                else:
                    if predicted is not None:
                        continue
                    self.endings.append((before, arguments))
                surprises.append(outcome)
            if surprises:  # elle apprend de ces contre-exemples, une fois pour la position
                fixes += len(surprises)
                if "moved" in surprises:
                    # un coup joué qu'elle ne prévoyait pas : une case que l'action remplit aussi
                    # (portées revues), ou une valeur écrite mal décrite (décrite de nouveau)
                    self.knowledge["reach"] = effets.portees_observees(self.lab_cases)
                    self.describe_writing()
                free = self.free()
                self.knowledge["free"] = free if free is not None else effets.Condition()  # provisoire
                self.rethink()
        lab.goto([])
        free = self.free()
        if free is None:
            raise LabError("le labo contredit sa perception et la mère ne sait pas dire quand une action "
                           "peut être jouée : la condition est hors de portée de son langage ; elle ne peut "
                           "pas encore éduquer de fils")
        self.knowledge["free"] = free
        self.rethink()
        return fixes

    def player_of(self, moves: list) -> int | None:
        """Le joueur qui joue après ``moves`` (la parité du coup)."""
        return len(moves) % 2

    def check_perception(self) -> None:
        """Ce qu'elle a écrit (sa perception, celle du fils) prévoit-il tout ce qu'elle a vu ?
        Chaque coup joué donne l'état d'après, chaque coup refusé n'est pas un coup. Les coups vus
        sont les tests de ce qu'elle a compris."""
        mind = self.mind
        for case in self.lab_cases:
            expected = None if case.valeur_apres == case.valeur_avant else gele(case.valeur_apres)
            found = gele(mind.valeur_apres(case.valeur_avant, case.arguments))
            if found != expected:
                raise LabError(f"sa description prévoit {found} pour {self.model.action.short_name}"
                               f"{case.arguments} sur {case.valeur_avant}, le jeu a donné {expected} : "
                               "elle ne peut pas encore éduquer de fils")

    def cell(self, state, arguments: tuple) -> int | None:
        """La case que remplit le coup ``arguments`` dans ``state`` (perception de la mère)."""
        return self.mind.case_jouee(list(state), self.action(arguments))

    def random_player(self, rng: random.Random):
        """Un adversaire qui joue au hasard parmi les actions que la mère a trouvées."""
        return random_player(rng, [self.args(a) for a in self.knowledge["actions"]], self.knowledge["action"],
                             self.knowledge["getter"], self.knowledge["end_signal"])

    def discover_actions(self) -> list:
        """Quelles actions existent ? La mère ne le sait pas d'avance : elle part des valeurs que
        l'exemple a passées à l'action et explore autour, dans son labo.

        * des entiers : tous ceux entre le plus petit et le plus grand vus, puis plus loin dans
          chaque sens, tant que le jeu en accepte (« si 7 marche, et 8 ? ») ; elle s'arrête après
          :data:`PATIENCE` refus de suite ;
        * des booléens : les deux ;
        * d'autres valeurs : celles de l'exemple.

        Une valeur est une action si le jeu l'accepte au départ ou à une position de l'exemple.

        **Plusieurs arguments** (au Nim, ``play(tas, nombre)``) : la mère explore chaque argument
        de la même façon, en partant des valeurs vues **pour cet argument**. Une valeur d'un
        argument est permise si le jeu accepte au moins une action où elle figure, les autres
        arguments prenant les valeurs vues dans l'exemple (au plus
        :data:`COMBINAISONS_ARGUMENT` combinaisons, pour ne pas exploser). Les actions sont
        alors les combinaisons de ces valeurs que le jeu accepte à une position de l'exemple ;
        l'exploration (:meth:`explore`) essaie aussi les autres, et garde celles qu'il accepte
        quelque part. Les coups refusés restent des observations.
        """
        lab = self.lab
        calls = [f for f in self.parsed.player_functions() if f.name == self.model.action.name]
        example = [tuple(f.arguments) for f in calls]
        positions = [example[:k] for k in range(len(example))]
        verdicts: dict = {}

        def accepted(arguments: tuple) -> bool:
            key = effets._cle(arguments)
            if key not in verdicts:
                verdicts[key] = False
                for moves in positions:
                    if not lab.goto(moves) or lab.ended:
                        continue
                    try:
                        outcome = lab.play(*arguments)
                    except Exception:  # le jeu ne supporte pas cette valeur
                        lab.new_game()
                        break
                    if outcome != "refused":
                        lab.undo()
                        verdicts[key] = True
                        break
            return verdicts[key]

        if self.width == 1:
            seen = list(dict.fromkeys(f.arguments[0] for f in calls if f.arguments))
            found = self.around(seen, lambda v: accepted((v,)))
            self.candidates = list(found)
        else:
            seen = [list(dict.fromkeys(f.arguments[k] for f in calls if len(f.arguments) > k))
                    for k in range(self.width)]
            values = []
            for k in range(self.width):
                def allowed(v, k=k) -> bool:
                    others = [[v] if j == k else seen[j] for j in range(self.width)]
                    tries = itertools.islice(itertools.product(*others), COMBINAISONS_ARGUMENT)
                    return any(accepted(t) for t in tries)
                values.append(self.around(seen[k], allowed))
            self.candidates = list(itertools.islice(itertools.product(*values), ACTIONS_MAX))
            found = [a for a in self.candidates if accepted(a)]
        lab.goto([])
        return found

    @staticmethod
    def around(seen: list, accepted) -> list:
        """Les valeurs permises d'un argument, en partant de celles vues (``accepted(v)`` : le jeu
        accepte-t-il une action avec cette valeur ?). Des entiers : tous ceux entre le plus petit
        et le plus grand vus, puis plus loin dans chaque sens jusqu'à :data:`PATIENCE` refus de
        suite ; des booléens : les deux ; d'autres valeurs : celles vues."""
        integers = sorted({v for v in seen if isinstance(v, int) and not isinstance(v, bool)})
        candidates = [v for v in seen if not (isinstance(v, int) and not isinstance(v, bool))]
        if any(isinstance(v, bool) for v in seen):
            candidates += [v for v in (False, True) if v not in candidates]
        found = [v for v in candidates if accepted(v)]
        if integers:
            inside = [v for v in range(integers[0], integers[-1] + 1) if accepted(v)]
            outside = []
            for start, step in ((integers[-1] + 1, 1), (integers[0] - 1, -1)):
                value, refusals = start, 0
                while refusals < PATIENCE:
                    if accepted(value):
                        outside.append(value)
                        refusals = 0
                    else:
                        refusals += 1
                    value += step
            found += sorted(inside + outside)
        return found

    def owners(self) -> list:
        """Les joueurs qui jouent l'action dans l'exemple, coup après coup."""
        name = self.model.action.name
        owners = [owner for owner, player in self.parsed.players.items()
                  for f in player.functions_used if f.name == name]
        times = [f.time for player in self.parsed.players.values()
                 for f in player.functions_used if f.name == name]
        return [owner for _, owner in sorted(zip(times, owners))]

    def alternate(self) -> bool:
        """Dans l'exemple, deux joueurs jouent-ils l'action chacun leur tour ?

        C'est ce qui permet ensuite de reconnaître le joueur à la parité du coup.
        """
        owners = self.owners()
        return len(set(owners)) == 2 and all(a != b for a, b in zip(owners, owners[1:]))

    def explore(self) -> tuple[list, list]:
        """La mère joue dans son labo pour voir ce que font les actions, par curiosité.

        Elle rejoue d'abord l'exemple, puis :data:`PARTIES_D_ESSAI` parties où, à
        chaque coup, elle choisit l'action qu'elle a le moins vue agir (au hasard
        entre égales) ; si le jeu la refuse, la suivante. Elle note chaque coup
        coup : l'état avant, l'action, l'état après et le joueur qui a joué (la
        parité du coup : elle a vu dans l'exemple que les joueurs alternent). Un
        coup refusé est noté aussi, avec un état après égal à l'état avant : il
        montre quand une case ne peut pas être jouée. Rien ne lui dit qu'une
        action remplit une colonne : c'est ce qu'elle en déduira
        (:func:`~xander.effets.portees_observees`, :func:`~xander.effets.liberte`).

        Renvoie les positions atteintes ``(coups, état)`` et les coups notés
        ``(cas, joueur)``.
        """
        rng, lab = random.Random(f"exploration-{self.seed}"), self.lab
        calls = [f for f in self.parsed.player_functions() if f.name == self.model.action.name]
        example = [tuple(f.arguments) for f in calls]
        # plusieurs arguments : elle essaie aussi les combinaisons que l'exemple n'a pas montrées
        tried = self.candidates if self.width > 1 else self.knowledge["actions"]
        actions = [self.args(a) for a in tried]
        positions, seen, counts = [], [], {a: 0 for a in actions}
        filled = {a: set() for a in actions}   # cases qu'on a vu chaque action changer
        surprising = set()                     # actions dont le dernier coup a montré du nouveau

        def note(arguments, before, after, player):
            case = effets.Cas(before, arguments, after)
            seen.append((case, player))
            if arguments in counts:
                counts[arguments] += 1
                if case.forme != effets.CHANGEES:
                    return  # une valeur n'a pas de cases : rien de surprenant à suivre
                new = set(case.cible()) - filled[arguments]
                filled[arguments] |= set(case.cible())
                (surprising.add if new else surprising.discard)(arguments)

        lab.goto([])
        positions.append(([], lab.states[-1]))
        for k, arguments in enumerate(example):
            before = lab.states[-1]
            outcome = lab.play(*arguments)
            if outcome == "end":
                self.endings.append((self.copy(before), arguments))
            if outcome != "moved":
                break
            note(arguments, before, lab.states[-1], k % 2)
            positions.append((example[:k + 1], lab.states[-1]))
        for _ in range(PARTIES_D_ESSAI):
            lab.goto([])
            moves: list[tuple] = []
            surprising.clear()
            while len(moves) < 4 * max(len(example), 1):
                # d'abord l'action qui vient de montrer du nouveau, sinon la moins vue
                order = sorted(rng.sample(actions, len(actions)),
                               key=lambda a: (a not in surprising, counts[a]))
                for arguments in order:
                    before = lab.states[-1]
                    outcome = lab.play(*arguments)
                    if outcome == "moved":
                        note(arguments, before, lab.states[-1], len(moves) % 2)
                        moves.append(arguments)
                        positions.append((list(moves), lab.states[-1]))
                        break
                    surprising.discard(arguments)  # refusée ou finale : plus rien à voir ici
                    if outcome == "end":  # le jeu l'a acceptée, et la partie a fini : noté aussi
                        self.endings.append((self.copy(before), arguments))
                        lab.undo()
                    else:  # refusé : rien n'a changé, c'est aussi une observation
                        seen.append((effets.Cas(before, arguments, self.copy(before)), len(moves) % 2))
                else:
                    break  # aucun coup ne fait avancer la partie sans la finir
        lab.goto([])
        if self.width > 1:  # les actions : celles que le jeu a acceptées quelque part
            played = {effets._cle(c.arguments) for c, _ in seen if c.valeur_apres != c.valeur_avant}
            played |= {effets._cle(tuple(arguments)) for _, arguments in self.endings}
            known = {effets._cle(self.args(a)) for a in self.knowledge["actions"]}
            self.knowledge["actions"] = [a for a in tried
                                         if effets._cle(self.args(a)) in played | known]
        return positions, seen

    def played_cells(self, moves: list[tuple]) -> list[int]:
        """Les cases remplies par chaque coup de ``moves``, relues dans le labo."""
        lab = self.lab
        lab.goto(moves)
        states = lab.states
        cells = [next(i for i, (a, b) in enumerate(zip(states[k], states[k + 1])) if a != b)
                 for k in range(len(states) - 1)]
        if lab.ended:
            cells.append(self.cell(states[-1], lab.moves[-1]))
        return cells

    def learn_marks(self) -> None:
        """Quel pion pose chaque joueur : la valeur qui apparaît dans la case jouée. (Une valeur
        n'a pas de pions : les joueurs sont ceux de l'exemple.)"""
        if not self.tableau:
            return
        states = self.lab.states
        for k in range(len(states) - 1):
            if k % 2 not in self.marks:
                changed = [i for i, (a, b) in enumerate(zip(states[k], states[k + 1])) if a != b]
                if len(changed) == 1:
                    self.marks[k % 2] = states[k + 1][changed[0]]
        if len(self.marks) == 2 and self.knowledge["marks"] != [self.marks[0], self.marks[1]]:
            self.knowledge["marks"] = [self.marks[0], self.marks[1]]
            self.rethink()

    def final_state(self) -> list:
        """La position à la fin de la partie (le jeu ne la montre pas : la mère la calcule)."""
        lab = self.lab
        if not lab.ended:
            return self.position()
        mover = (len(lab.moves) - 1) % 2
        before = list(lab.states[-1]) if self.tableau else [gele(lab.states[-1]), self.marks[mover]]
        return self.mind.apres(before, self.action(lab.moves[-1]), self.marks[mover])

    # ------------------------------------------------------------------ #
    # Comprendre une fin de partie
    # ------------------------------------------------------------------ #

    def winner(self, full_board: bool = True) -> int | None:
        """Parité du gagnant de la partie terminée du labo, ``None`` pour un nul.

        Avec ``full_board=False`` (une partie que le professeur finit pour juger un coup), la
        mère ne cherche pas de nouveau motif quand plus aucune action n'est possible : c'est
        presque toujours un nul, et la contre-épreuve y coûte cher (aucune case libre où
        déplacer un pion). Les motifs se découvrent dans les vraies parties.
        """
        if not self.tableau:
            return self.value_winner()
        lab = self.lab
        self.learn_marks()
        mover = (len(lab.moves) - 1) % 2
        final = self.final_state()
        last = self.cell(lab.states[-1], lab.moves[-1])
        mine = {i for i, v in enumerate(final) if v == self.marks[mover]}
        if any(last in p and set(p) <= mine for p in self.knowledge["patterns"]):
            return mover
        if not full_board and not self.mind.possibles(list(final)):
            return None
        pattern = self.counter_test(final, mover)
        if pattern is None:
            return None
        if pattern in self.knowledge["patterns"]:
            return mover  # la contre-épreuve a retrouvé un motif connu
        self.knowledge["patterns"].append(pattern)
        self.discovered.append(pattern)
        self.rethink()
        return mover

    def value_winner(self) -> int | None:
        """Parité du gagnant quand l'état est une valeur : la fin est une valeur que la mère a
        comprise, avec le joueur qu'elle fait gagner (celui qui vient de jouer, ou l'autre).
        Une fin à une valeur qu'elle n'a pas comprise : elle ne sait pas qui a gagné, elle le
        note et la compte nulle (comme une fin sans motif au Morpion)."""
        mover = (len(self.lab.moves) - 1) % 2
        valeur = self.final_state()[0]
        who = self.knowledge["ends"].get(valeur)
        if who == "dernier":
            return mover
        if who == "trait":
            return 1 - mover
        if who is None and valeur not in self.unknown_ends:
            self.unknown_ends.append(valeur)
            self.discovered.append(f"fin à la valeur {valeur!r} : la mère ne sait pas qui l'a gagnée "
                                   "(comptée nulle)")
        return None

    def understand_end(self, winner: str) -> str | None:
        """Comprendre la fin de l'exemple quand l'état est une valeur : la partie finit à cette
        valeur, et l'exemple dit qui l'a gagnée (celui qui vient de jouer, ou l'autre).

        **Contre-épreuve** : est-ce bien la valeur qui finit la partie, et pas le chemin ? La
        mère cherche, dans les positions vues en explorant, des coups qui y mènent depuis
        d'autres valeurs (son programme le lui dit) et les joue dans le labo : la partie doit
        finir à chaque fois. Il faut qu'elle ait fini depuis au moins deux valeurs différentes
        (:data:`CONTRE_EPREUVES` au plus), et qu'aucun coup n'y ait mené sans la finir. Sinon,
        elle ne comprend pas cette fin."""
        lab = self.lab
        moves, mover = list(lab.moves), (len(lab.moves) - 1) % 2
        valeur = self.final_state()[0]
        sources = self.end_sources(valeur)
        lab.goto(moves)
        if sources is None or len(sources) < 2:
            return None
        if winner == "D":
            who = "nul"
        elif winner == self.marks[mover]:
            who = "dernier"
        elif winner == self.marks[1 - mover]:
            who = "trait"
        else:
            return None
        if self.knowledge["ends"].get(valeur) == who:
            return None
        self.knowledge["ends"][valeur] = who
        self.rethink()
        text = {"nul": "un nul", "dernier": "gagnée par celui qui vient de jouer",
                "trait": "gagnée par celui qui a le trait (le dernier coup fait perdre celui qui le joue)"}
        return (f"fin comprise : la partie finit à la valeur {valeur!r}, {text[who]} ; contre-épreuve "
                f"dans le labo : elle y a fini depuis les valeurs {sorted(sources)}, aucun coup n'y a "
                "mené sans la finir")

    def end_sources(self, valeur) -> set | None:
        """Contre-épreuve d'une fin : est-ce bien cette valeur (cet état) qui finit la partie ?

        La mère cherche des coups qui y mènent (son programme le lui dit), depuis les positions
        vues en explorant, et les joue dans le labo : la partie doit finir à chaque fois. Si elle
        n'en trouve pas deux, elle cherche un coup plus loin que ce qu'elle a exploré (au plus
        :data:`SOURCES_MAX` coups joués). Renvoie les états d'où une action l'a finie (au plus
        :data:`CONTRE_EPREUVES`), ou ``None`` si un coup y a mené sans la finir : ce n'est pas
        l'état qui finit la partie."""
        lab, mind = self.lab, self.mind

        def reached(avant, arguments) -> bool:
            return gele(mind.valeur_apres(avant, tuple(arguments))) == valeur

        sources = {gele(avant) for avant, arguments in self.endings if reached(avant, arguments)}
        if any(c.forme in (effets.APRES, effets.CHANGEES) and c.valeur_apres != c.valeur_avant
               and gele(c.valeur_apres) == valeur for c in self.lab_cases):
            return None
        actions = [self.args(a) for a in self.knowledge["actions"]]
        tried, budget = set(), [SOURCES_MAX]

        def further():
            """Les positions vues en explorant, puis celles qu'un coup de plus atteint."""
            seen = {gele(avant) for _, avant in self.positions}
            for path, _ in self.positions:
                for arguments in actions:
                    if budget[0] <= 0 or not lab.goto(path) or lab.ended:
                        break
                    budget[0] -= 1
                    if lab.play(*arguments) == "moved" and gele(lab.states[-1]) not in seen:
                        seen.add(gele(lab.states[-1]))
                        yield list(path) + [arguments], self.copy(lab.states[-1])

        for phase in (iter(self.positions), further()):
            for path, avant in phase:
                if len(sources) >= CONTRE_EPREUVES:
                    break
                key = gele(avant)
                if key in sources or key in tried:
                    continue
                tried.add(key)
                for arguments in actions:
                    if not reached(avant, arguments) or not lab.goto(list(path)) or lab.ended:
                        continue
                    outcome = lab.play(*arguments)
                    if outcome == "end":
                        self.endings.append((self.copy(avant), arguments))
                        sources.add(key)
                        break
                    if outcome == "moved":  # la valeur atteinte sans finir : ce n'est pas elle
                        self.lab_cases.append(effets.Cas(self.copy(avant), arguments, self.copy(lab.states[-1])))
                        return None
            if len(sources) >= 2:
                break
        return sources

    def counter_test(self, final: list, mover: int) -> list[int] | None:
        """Quels pions étaient nécessaires à la fin ? Rejoue la fin sans chacun d'eux.

        Pour chaque pion du joueur qui a fini la partie, la mère imagine la même
        position avec ce pion **ailleurs**, sur une case libre (pas celle du
        dernier coup), puis rejoue le dernier coup. Si la partie ne finit plus,
        le pion était nécessaire. Elle raisonne sur la position, pas sur la
        suite de coups : elle cherche ensuite une suite de coups qui y mène (avec
        la gravité, un pion ne se pose que sur un autre). Si aucune case libre ne
        convient (plateau plein, pion qui en soutient d'autres), elle échange le
        pion avec un pion adverse : « et si cette case avait été la sienne ? ».

        Un pion jugé inutile reste déplacé pour la suite des tests : si le
        dernier coup complétait deux motifs à la fois, on garde ainsi un motif
        entier au lieu de ce que les deux ont en commun. Un pion déplacé est
        testé de nouveau à sa nouvelle place, au cas où celle-ci aurait complété
        un autre motif.
        """
        lab, mind = self.lab, self.mind
        moves = list(lab.moves)
        last = self.cell(lab.states[-1], moves[-1])
        action = mind.action_pour(last)
        mine = {i for i, v in enumerate(final) if v == self.marks[mover] and i != last}
        his = {i for i, v in enumerate(final) if v == self.marks[1 - mover]}
        free = [i for i in range(len(final)) if i not in mine | his and i != last]
        needed: set[int] = set()
        to_test, moved = sorted(mine), set()
        try:
            while to_test:
                cell = to_test.pop(0)
                kept = None   # un déplacement après lequel la partie finit encore
                tested = necessary = False
                relocations = [(mine - {cell} | {f}, his, f) for f in free]
                swaps = [(mine - {cell} | {h}, his - {h} | {cell}, h) for h in sorted(his)]
                for variants in (relocations, swaps):
                    for new_mine, new_his, place in variants:
                        if (not self.reach(new_mine, new_his, mover)
                                or mind.case_jouee(list(lab.states[-1]), action) != last):
                            continue
                        tested = True
                        if lab.play(*self.args(action)) != "end":
                            necessary = True
                            break
                        if kept is None:
                            kept = (new_mine, new_his, place)
                    if tested:
                        break
                if not tested:
                    return None  # impossible à vérifier : pas d'explication
                if necessary:
                    needed.add(cell)
                elif cell not in moved:
                    mine, his, place = kept
                    now = [i for i in range(len(final)) if i not in mine | his and i != last]
                    free = [i for i in free if i in now] + [i for i in now if i not in free]
                    moved.add(place)
                    to_test.append(place)  # à retester à sa nouvelle place
        finally:
            lab.goto(moves)
        if not needed:
            return None
        return sorted(needed | {last})

    def reach(self, mine: set, his: set, mover: int, attempts: int = 5) -> bool:
        """Amène le labo à une position où ``mover`` a les pions ``mine`` et l'autre ``his``,
        avant le coup de ``mover`` (une suite de coups qui y mène, s'il y en a une)."""
        first, second = (mine, his) if mover == 0 else (his, mine)
        for attempt in range(attempts):
            moves = self.order(sorted(first), sorted(second), random.Random(attempt))
            if moves is not None and self.lab.goto(moves) and not self.lab.ended:
                return True
        return False

    # ------------------------------------------------------------------ #
    # Situations équivalentes
    # ------------------------------------------------------------------ #

    def shift_patterns(self) -> list[str]:
        """« Ce motif marcherait-il ailleurs ? » La mère essaie chaque motif décalé (chaque
        case + d) et le joue dans le labo. Elle ne sait rien de la forme du plateau : un
        décalage qui déborde d'une rangée sur la suivante ne finit pas la partie, et il est
        rejeté.
        """
        size, patterns, done = len(self.lab.states[0]), self.knowledge["patterns"], []
        grown = True
        while grown:
            grown = False
            for pattern in list(patterns):
                for shift in range(1 - size, size):
                    image = [cell + shift for cell in pattern]
                    if (not shift or image[0] < 0 or image[-1] >= size or image in patterns
                            or tuple(image) in self._shifts_tried):
                        continue
                    self._shifts_tried.add(tuple(image))
                    found = self.play_pattern(image)
                    if found is not None and found not in patterns:
                        patterns.append(found)
                        self.discovered.append(found)
                        grown = True
                        done.append(f"motif {found} : le motif {pattern} décalé de {shift:+d}, "
                                    "vérifié dans le labo")
        if done:
            self.rethink()
        self._shapes_known = True
        self.lab.goto([])
        return done

    def play_pattern(self, cells: list[int], attempts: int = 10) -> list[int] | None:
        """Le premier joueur occupe les cases ``cells``, l'autre joue ailleurs : si la partie
        finit au dernier pion, la contre-épreuve dit quel motif l'a finie. Une case pas encore
        atteignable (avec la gravité, la case du dessous est libre) attend : chacun joue alors
        d'abord dessous."""
        lab, mind = self.lab, self.mind
        for attempt in range(attempts):
            rng = random.Random(attempt)
            lab.goto([])
            todo = sorted(cells)
            while todo and not lab.ended:
                state = list(lab.states[-1])
                landing = {mind.case_jouee(state, a): a for a in mind.possibles(state)}
                elsewhere = [c for c in landing if c not in cells]
                below = [c for c in elsewhere if any(mind.action_pour(c) == mind.action_pour(t) for t in todo)]
                ready = [c for c in todo if c in landing] if len(lab.moves) % 2 == 0 else []
                choices = ready or below or elsewhere
                if not choices:
                    break
                cell = choices[0] if attempt == 0 else rng.choice(choices)
                if cell in todo:
                    todo.remove(cell)
                lab.play(*self.args(landing[cell]))
            if not todo and lab.ended:
                return self.counter_test(self.final_state(), 0)
        return None

    def abstract(self, state) -> tuple:
        """Ce qui compte d'une position : tout sauf les cases libres (elles n'ont pas d'identité)."""
        marks, free = self.knowledge["marks"], self.mind.libre
        return tuple(v if v in marks or not free(state, i) else None for i, v in enumerate(state))

    def probe_games(self, number: int = 20) -> list:
        """Des parties jouées au hasard dans le labo, jusqu'au bout."""
        rng, lab, games = random.Random(len(self.knowledge["patterns"])), self.lab, []
        for _ in range(number):
            lab.goto([])
            while not lab.ended:
                lab.play(*self.args(rng.choice(self.mind.possibles(list(lab.states[-1])))))
            moves = list(lab.moves)
            games.append((self.played_cells(moves), [self.abstract(s) for s in lab.states]))
        return games

    def symmetric_in_lab(self, sigma: list[int], games: list) -> bool:
        """Le jeu renuméroté se joue-t-il exactement comme le jeu ? (vérifié avec ``back``)"""
        lab, mind = self.lab, self.mind
        for cells, states in games:
            actions = [mind.action_pour(sigma[c]) for c in cells]
            if None in actions or not lab.goto([self.args(a) for a in actions]) or not lab.ended:
                return False
            if len(lab.states) != len(states) or any(
                    self.abstract(s) != tuple(symmetries.transform(t, sigma))
                    for s, t in zip(lab.states, states)):
                return False
        return True

    def discover_symmetries(self) -> str | None:
        """Cherche les renumérotations qui ne changent rien au jeu et les vérifie dans le labo."""
        self._symmetries_known = True
        size = len(self.lab.states[0])
        found = symmetries.candidates(size, self.knowledge["patterns"])
        if found is None:
            return None  # trop de candidates : les motifs ne disent pas encore assez
        identity = list(range(size))
        games = self.probe_games()
        kept = [s for s in found if s != identity and self.symmetric_in_lab(s, games)]
        self.lab.goto([])
        if kept == self.knowledge["symmetries"]:
            return None
        self.knowledge["symmetries"] = kept
        self._son = self._mind = None
        return (f"symétries : {len(kept) + 1} façons de voir une position ({len(found)} "
                f"renumérotation(s) préservent les motifs, {len(kept) + 1} vérifiée(s) dans le labo)")

    # ------------------------------------------------------------------ #
    # Le professeur
    # ------------------------------------------------------------------ #

    def key(self) -> tuple:
        return repr(self.lab.states[-1]), len(self.lab.moves) % 2

    def teacher_move(self, moves: list[tuple]) -> tuple:
        self.lab.goto(moves)
        key = self.key()
        if key not in self.teacher_moves:
            self.teacher_moves[key] = self.lab.ask(self.teacher)
            self.lab.undo()
        return self.teacher_moves[key]

    def value(self, moves: list[tuple], side: int) -> int:
        """Résultat pour ``side`` si le professeur finit la partie des deux côtés.

        Le professeur joue toujours de la même façon : chaque position par laquelle il passe
        en finissant la partie a la même issue, et la mère retient aussi le coup qu'il y a
        joué. Une autre question sur l'une de ces positions ne coûte plus rien.
        """
        lab = self.lab
        lab.goto(moves)
        if lab.ended:
            winner = self.winner()
        else:
            key = self.key()
            if key not in self.outcomes:
                start, seen = list(lab.moves), []
                while not lab.ended:
                    position = self.key()
                    if position in self.outcomes:  # déjà fini depuis ici
                        break
                    seen.append(position)
                    self.teacher_moves[position] = lab.ask(self.teacher)
                winner = self.outcomes[position] if not lab.ended else self.winner(full_board=False)
                for position in seen:
                    self.outcomes[position] = winner
                lab.goto(start)
            winner = self.outcomes[key]
        return 0 if winner is None else (1 if winner == side else -1)

    def better(self, moves: list[tuple], teacher: tuple, action, side: int) -> bool:
        """Le coup du professeur mène-t-il à un meilleur résultat que ``action`` ? (Inutile de
        finir la partie après le sien si ``action`` gagne déjà.)"""
        mine = self.value(moves + [self.args(action)], side)
        return mine < 1 and self.value(moves + [teacher], side) > mine

    # ------------------------------------------------------------------ #
    # Parties et corrections
    # ------------------------------------------------------------------ #

    def first_lesson(self) -> GameRecord:
        """Rejoue l'exemple et comprend pourquoi il se termine."""
        action = self.model.action.name
        moves = [tuple(f.arguments) for f in self.parsed.player_functions() if f.name == action]
        lab = self.lab
        lab.goto([])
        for arguments in moves:
            if lab.play(*arguments) == "refused":
                raise LabError(f"le coup {arguments} de l'exemple est refusé par le jeu")
        self.learn_marks()
        if not self.tableau:
            return self.first_lesson_value()
        for k in range(len(lab.states) - 1 if len(self.marks) == 2 else 0):
            before, after = lab.states[k], lab.states[k + 1]  # elle vérifie qu'elle a compris l'action
            changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
            expected = self.cell(before, lab.moves[k])
            if changed != [expected]:
                raise LabError(f"{self.model.action.short_name}{lab.moves[k]} a changé les cases {changed}, "
                               f"pas la case {expected} : l'Analyzer doit d'abord mieux comprendre "
                               "l'action, la mère ne peut pas encore éduquer de fils")
        record = GameRecord(0, "exemple", "-", "terminé" if lab.ended else "inachevé")
        if lab.ended:
            winner = self.winner()
            record.result = "nul" if winner is None else f"gagné par {self.marks[winner]}"
        record.patterns, self.discovered = self.discovered, []
        self.records.append(record)
        return record

    def first_lesson_value(self) -> GameRecord:
        """La leçon de l'exemple quand l'état est une valeur : la mère vérifie que son programme
        prédit chaque valeur, puis comprend à quelle valeur la partie finit et qui la gagne."""
        lab, mind = self.lab, self.mind
        for k in range(len(lab.states) - 1):
            expected = mind.valeur_apres(lab.states[k], tuple(lab.moves[k]))
            if gele(expected) != gele(lab.states[k + 1]):
                raise LabError(f"{self.model.action.short_name}{lab.moves[k]} a donné {lab.states[k + 1]!r}, "
                               f"pas {expected!r} : l'Analyzer doit d'abord mieux comprendre l'action")
        record = GameRecord(0, "exemple", "-", "terminé" if lab.ended else "inachevé")
        if lab.ended:
            understood = self.understand_end(self.parsed.winner)
            if understood:
                self.discovered.append(understood)
            winner = self.winner()
            record.result = "nul" if winner is None else f"gagné par {self.marks[winner]}"
        record.patterns, self.discovered = self.discovered, []
        self.records.append(record)
        return record

    # ------------------------------------------------------------------ #
    # Le code du fils, écrit par la mère
    # ------------------------------------------------------------------ #

    def rewrite(self) -> None:
        """Ce que sait la mère a changé : le code du fils sera réécrit."""
        self._son = None

    def rethink(self) -> None:
        """La mère comprend mieux le jeu (pions, motifs) : sa perception est à refaire."""
        self._son = self._mind = self._pensee = self._bank = None
        self._judged = {}
        self._symmetries_known = False
        self._shapes_known = False

    def source(self, name: str = "fils") -> str:
        return son_writer.son_source(name, self.knowledge, len(self.records) - 1)

    @property
    def son(self):
        """Le fils tel que la mère l'a écrit (module exécuté à partir de son code)."""
        if self._son is None:
            self._son = son_writer.load(self.source())
        return self._son

    @property
    def mind(self):
        """La perception du jeu par la mère (les quatre notions)."""
        if self._mind is None:
            self._mind = son_writer.mind(self.knowledge)
        return self._mind

    # ------------------------------------------------------------------ #

    def play_game(self, opponent, son_side: int) -> tuple[int, list]:
        """Une partie du fils contre ``opponent``. Si le jeu refuse son coup (un coup
        impossible), la mère comprend pourquoi (:meth:`impossible`) et le fils rejoue ; les
        coups impossibles de la partie sont dans ``self.impossibles``."""
        lab = self.lab
        lab.goto([])
        decisions, self.impossibles = [], []
        while not lab.ended:
            if len(lab.moves) % 2 == son_side:
                moves, state = list(lab.moves), self.position()
                action, reason = self.son.choisir(list(state), self.marks[son_side])
                self.max_views = max(self.max_views, self.son.VUES)
                if lab.play(*self.args(action)) == "refused":
                    self.impossibles.append(self.impossible(state, action))
                    continue
                decisions.append((moves, state, action, reason))
            else:
                lab.ask(opponent)
        winner = self.winner()
        return (0 if winner is None else 1 if winner == son_side else -1), decisions

    def impossible(self, state: list, action) -> str:
        """Le jeu a refusé le coup du fils. « Pourquoi ? » C'est sa perception qui se trompe :
        la mère note le refus comme une observation du labo (rien n'a changé), réapprend quand
        une case peut être jouée (:func:`effets.liberte`) et réécrit le fils. Si elle ne
        comprend pas, ou si le fils croirait encore ce coup possible, elle s'arrête : un fils
        qui essaie des coups jusqu'à ce que le jeu en accepte un tricherait."""
        raw = self.raw(state)
        self.lab_cases.append(effets.Cas(self.copy(raw), self.args(action), self.copy(raw)))
        free = self.free()
        if free is not None:
            self.knowledge["free"] = free
            self.rethink()
        if free is None or action in self.mind.possibles(list(state)):
            raise LabError(f"le jeu refuse l'action {action}, que le fils croyait possible, "
                           "et la mère ne comprend pas pourquoi")
        return f"coup impossible : {action} refusé ; une action peut être jouée : {free}"

    def variations(self, decisions: list, son_side: int) -> list:
        """« Et s'il avait joué ailleurs ? » La mère revient (``back``) sur chaque coup de
        l'adversaire, essaie les autres, et note ce que le fils aurait répondu.

        Avec ``self.variants``, elle n'essaie qu'autant d'autres coups par coup adverse, en
        commençant par celui que le professeur aurait joué à sa place (le plus dangereux) :
        comme un joueur qui revoit sa partie, elle ne regarde pas toutes les réponses.
        """
        lab, me, imagined = self.lab, self.marks[son_side], []
        for moves, _, _, _ in decisions:
            if not moves:
                continue
            before = moves[:-1]
            lab.goto(before)
            others = [a for a in self.mind.possibles(self.position()) if self.args(a) != tuple(moves[-1])]
            if self.variants is not None and len(others) > self.variants:
                best = self.action(self.teacher_move(before))
                others = ([best] if best in others else []) + [a for a in others if a != best]
                others = others[:self.variants]
            for action in others:
                if not lab.goto(before + [self.args(action)]) or lab.ended:
                    continue
                state = self.position()
                son_cell, reason = self.son.choisir(list(state), me)
                self.max_views = max(self.max_views, self.son.VUES)
                imagined.append((list(lab.moves), state, son_cell, reason))
        return imagined

    def review(self, decisions: list, son_side: int) -> list[Lesson]:
        lessons = []
        me = self.marks[son_side]
        for moves, state, son_cell, reason in decisions:
            teacher = self.teacher_move(moves)
            teacher_cell = self.action(teacher)
            if teacher_cell == son_cell or not self.better(moves, teacher, son_cell, son_side):
                key = self.mind.cle(list(state), me)
                if key not in self.cases:  # bien joué : la position reste un test pour les refactors
                    self.cases[key] = Case(list(moves), list(state), me, key, son_cell, teacher_cell)
                continue
            lessons.append(self.correct(state, me, son_cell, reason, teacher_cell, moves))
        return lessons

    def correct(self, state, me, son_cell, reason, teacher_cell, moves=None) -> Lesson:
        """Corrige le cas : la position devient un souvenir et un cas enregistré."""
        self.rewrite()
        memories = self.knowledge["memories"]
        key = self.mind.cle(list(state), me)
        changes = []
        wrong, recalled = self.mind.rappel(list(state), me, memories) if reason == "souvenir" else (None, None)
        if wrong is not None and recalled == son_cell:  # (déjà oublié si une correction de la
            covered = [c for c in self.cases.values()  # même revue l'a démenti)
                       if self.mind.rappel(list(c.state), c.me, memories)[0] == wrong]
            del memories[wrong]
            if "?" in wrong:  # le labo n'avait pas imaginé cette position : les cas qu'il couvrait
                for case in covered:  # redeviennent des souvenirs entiers, à réduire de nouveau
                    memories.setdefault(case.key, self.mind.case_jouee(list(case.state), case.teacher_cell))
                changes.append(f"petit motif {wrong} faux oublié")
            else:
                changes.append("souvenir faux oublié")
        memories[key] = self.mind.case_jouee(list(state), teacher_cell)  # la case à occuper
        changes.append("nouveau souvenir")
        self.cases[key] = Case(list(moves or []), list(state), me, key, son_cell, teacher_cell)
        return Lesson(key, son_cell, reason, teacher_cell, "souvenir", ", ".join(changes))

    # ------------------------------------------------------------------ #
    # Petits motifs : ce qui comptait dans un souvenir, reconnu partout
    # ------------------------------------------------------------------ #

    def generalize(self) -> list[str]:
        """Chaque nouveau souvenir est réduit aux cases qui comptaient, puis essayé décalé."""
        memories, done = self.knowledge["memories"], []
        for key in [k for k in memories if k not in self._generalized]:
            if key not in memories:
                continue
            self._generalized.add(key)
            move = memories[key]
            chunk = self.reduce(key, move)
            if chunk != key:
                del memories[key]
                memories[chunk] = move
                self._generalized.add(chunk)
                kept = sum(v != "?" for v in chunk)
                done.append(f"souvenir {key} -> petit motif {chunk} ({kept} cases sur {len(key)} "
                            "comptent, vérifié dans le labo)")
            done += self.shift_chunk(chunk, move)
        if done:
            self.rewrite()
        self.lab.goto([])
        return done

    def reduce(self, key: str, move: int) -> str:
        """« Qu'est-ce qui comptait ? » La plus petite partie du souvenir (le reste devient
        « ? ») qui tient (:meth:`holds`) : le coup reste bon partout où elle apparaît, et à
        cause d'elle.

        La mère regarde d'abord la **zone** du coup : les cases qui partagent avec lui un
        motif de fin qu'elle connaît (ce qui se joue sur les lignes passant par le coup).
        Si rien n'y tient, le souvenir reste entier. (Sans motif de fin connu par le coup, elle
        regarde toutes les cases.)
        """
        others = [i for i, v in enumerate(key) if i != move and v != "?"]
        zone = {c for p in self.knowledge["patterns"] if move in p for c in p}
        near = [i for i in others if i in zone]
        chunk = self.smallest(key, move, near if zone else others)
        return key if chunk is None else chunk

    def smallest(self, key: str, move: int, cells: list[int]) -> str | None:
        """Le plus petit motif qui tient, fait du coup et de cases prises dans ``cells``.

        Elle essaie d'abord les configurations de 0, 1, 2… cases, tant qu'il y en a au plus
        ``self.combinations`` à essayer (sur les 9 cases du Morpion, jusqu'à 3 cases ; sur les
        42 du Puissance 4, une seule). Ensuite, partie de toutes les cases de ``cells``, elle
        les oublie une à une et garde chaque oubli qui tient sur quelques positions. Chaque
        essai passe d'abord ce tamis (``self.sieve`` positions) : seul un motif qui le passe
        est vérifié sur toutes. Rien si aucun ne tient.
        """
        tried = 0
        for size in range(len(cells) + 1):
            tried += math.comb(len(cells), size)
            if tried > self.combinations:
                break
            for kept in itertools.combinations(cells, size):
                chunk = "".join(v if i == move or i in kept else "?" for i, v in enumerate(key))
                if self.holds(chunk, move, self.sieve) and self.holds(chunk, move):
                    return chunk
        else:
            return None  # toutes les configurations essayées : aucune ne tient
        chunk = [v if i == move or i in cells else "?" for i, v in enumerate(key)]
        for i in cells:
            trial = chunk[:i] + ["?"] + chunk[i + 1:]
            if self.holds("".join(trial), move, self.sieve):
                chunk = trial
        chunk = "".join(chunk)
        return chunk if self.holds(chunk, move) else None

    def shift_chunk(self, chunk: str, move: int) -> list[str]:
        """« Et ailleurs ? » Le petit motif décalé (chaque case + d), vérifié de la même façon.
        Comme pour les motifs de fin, la mère ne sait rien de la forme du plateau."""
        memories, size, done = self.knowledge["memories"], len(chunk), []
        placed = [i for i, v in enumerate(chunk) if v != "?"]
        for shift in range(1 - size, size):
            if not shift or placed[0] + shift < 0 or placed[-1] + shift >= size:
                continue
            image = ["?"] * size
            for i in placed:
                image[i + shift] = chunk[i]
            image = "".join(image)
            if self.known(image, move + shift) or not self.holds(image, move + shift):
                continue
            memories[image] = move + shift
            self._generalized.add(image)
            done.append(f"petit motif {image} : {chunk} décalé de {shift:+d}, vérifié dans le labo")
        return done

    def known(self, chunk: str, move: int) -> bool:
        """Ce petit motif (ou une façon équivalente de le voir) est-il déjà un souvenir ?"""
        memories = self.knowledge["memories"]
        for sigma in [None] + self.knowledge["symmetries"]:
            image = chunk if sigma is None else "".join(symmetries.transform(chunk, sigma))
            if image in memories and memories[image] == (move if sigma is None else sigma[move]):
                return True
        return False

    def holds(self, chunk: str, move: int, number: int = 20) -> bool:
        """Le coup est-il le bon partout où le petit motif apparaît, **à cause** du motif ?
        D'abord dans des positions imaginées, puis dans les cas enregistrés (vus sous chaque
        façon de les voir).

        Dans une position imaginée, la mère demande son coup au professeur. S'il joue le coup
        du motif, la position le confirme. S'il joue ailleurs, elle vérifie que le coup du
        motif est aussi bon (en lui faisant finir la partie) : sinon le motif est démenti.
        Elle ne le vérifie ainsi que pour les deux premiers désaccords (chacun coûte deux fins
        de partie), et seulement une fois les comptes passés (confirmations et témoin) : un
        motif que les comptes refusent ne coûte aucune fin de partie. Les désaccords suivants
        comptent seulement comme des positions qui ne confirment pas.
        Une position où le motif ne s'applique pas (sa case n'y est pas atteignable) ne dit
        rien.

        **Le témoin.** Pour chaque position, elle imagine aussi la même position *sans* le
        motif (une de ses cases changée, voir :meth:`witness`) et demande de nouveau son coup
        au professeur. Si le professeur joue ce coup aussi souvent sans le motif, le motif
        n'explique rien (au Puissance 4, il joue souvent la colonne du centre, motif ou
        pas). Avec ``r+`` la part des positions qui confirment et ``r-`` la part des témoins
        où il joue quand même ce coup, il faut ``r+ >= (1 + r-) / 2`` : le motif fait au
        moins la moitié du chemin entre le témoin et la certitude. Un motif réduit à la case
        jouée n'a pas de témoin possible : il n'explique rien.
        """
        kept = [i for i, v in enumerate(chunk) if v != "?" and i != move]
        if not kept:
            return False
        mind, rng = self.mind, random.Random(chunk + "témoin")
        action = mind.action_pour(move)
        imagined = applied = confirmed = witnesses = still = 0
        disagreements = []
        for moves in self.imagine(chunk, number):
            imagined += 1
            state = list(self.lab.states[-1])
            if mind.case_jouee(state, action) != move:
                continue  # la case n'y est pas encore atteignable : le motif ne s'applique pas
            applied += 1
            if self.action(self.teacher_move(moves)) == action:
                confirmed += 1
            elif len(disagreements) < 2:  # jugés plus loin, si le motif passe les comptes
                disagreements.append((list(moves), state))
            witness = self.witness(chunk, kept, move, len(moves), rng)
            if witness is not None:
                witnesses += 1
                still += self.action(self.teacher_move(witness)) == action
            if 2 * (imagined - confirmed) > number:
                return False  # la moitié ne peut plus être atteinte
        if not witnesses or 2 * confirmed < imagined:
            return False
        if 2 * confirmed * witnesses < applied * (witnesses + still):  # r+ < (1 + r-) / 2
            return False
        for moves, state in disagreements:  # un jugement coûte deux fins de partie
            if not self.judge(moves, state, action):
                return False
        trial = {chunk: move}
        for case in self.cases.values():
            _, cell = mind.rappel(list(case.state), case.me, trial)
            if cell is not None and not self.good(case, cell):
                return False
        return True

    def witness(self, chunk: str, kept: list[int], move: int, total: int, rng) -> list[tuple] | None:
        """Une position sans le petit motif, aussi chargée (``total`` pions) : une case du motif
        prend une autre valeur (un pion devient l'autre pion ou une case libre ; une case
        libre reçoit un pion), le reste est joué comme dans :meth:`imagine`. Le coup du motif
        doit y rester jouable. Renvoie la suite de coups qui y mène (le labo y est), ou
        ``None``."""
        action, side = self.mind.action_pour(move), total % 2
        for _ in range(5):
            cell = rng.choice(kept)
            broken = list(chunk)
            broken[cell] = rng.choice([v for v in "MA." if v != chunk[cell]])
            mine = total // 2 - broken.count("M")
            his = total - total // 2 - broken.count("A")
            if mine < 0 or his < 0:
                continue
            moves = self.grow("".join(broken), side, mine, his, rng)
            if (moves is not None and self.lab.goto(moves) and not self.lab.ended
                    and self.mind.case_jouee(list(self.lab.states[-1]), action) == move):
                return moves
        return None

    def order(self, first: list[int], second: list[int], rng) -> list[tuple] | None:
        """Une suite de coups qui pose les pions de chacun sur ses cases, chacun son tour (un
        pion ne se pose que sur une case qu'une action remplit à ce moment-là), ou ``None``."""
        mind, todo, state, moves = self.mind, [list(first), list(second)], list(self.lab.states[0]), []
        while todo[0] or todo[1]:
            turn = len(moves) % 2
            ready = [c for c in todo[turn] if mind.case_jouee(state, mind.action_pour(c)) == c]
            if not ready:
                return None
            cell = rng.choice(ready)
            todo[turn].remove(cell)
            action = mind.action_pour(cell)
            state = mind.apres(state, action, self.marks[turn])
            moves.append(self.args(action))
        return moves

    def imagine(self, chunk: str, number: int = 20):
        """Des positions qui contiennent le petit motif, fabriquées dans le labo en jouant
        (:meth:`grow`) : le fils peut être l'un ou l'autre joueur, et un nombre de pions tiré
        au hasard occupe les cases « ? ». Une position où la partie est déjà finie est
        écartée. Chaque suite de coups est donnée quand le labo y est arrivé."""
        rng = random.Random(chunk)
        cells = {v: [i for i, c in enumerate(chunk) if c == v] for v in "MA?"}
        found, seen = 0, set()
        for _ in range(number * 10):
            if found >= number:
                break
            side = rng.randrange(2)  # 0 : le fils joue en premier
            total = len(cells["M"]) + len(cells["A"]) + rng.randint(0, len(cells["?"]))
            mine = total // 2 - len(cells["M"])  # pions du fils à ajouter
            his = total - total // 2 - len(cells["A"])
            if total % 2 != side or mine < 0 or his < 0:
                continue
            moves = self.grow(chunk, side, mine, his, rng)
            if moves is None or not self.lab.goto(moves) or self.lab.ended:
                continue
            signature = tuple(self.lab.states[-1])
            if signature in seen:
                continue
            seen.add(signature)
            found += 1
            yield moves

    def grow(self, chunk: str, side: int, mine: int, his: int, rng) -> list[tuple] | None:
        """Une suite de coups permis qui mène au motif : à son tour, chacun pose un de ses
        pions du motif si une action le pose là, ou un pion de plus (il en a ``mine`` pour le
        fils, ``his`` pour l'autre) sur une case « ? » qu'une action remplit. Comme dans une
        vraie partie, aucun pion n'arrive là où aucune action ne le pose. ``None`` si un
        joueur ne peut plus rien poser."""
        mind = self.mind
        need = [[i for i, c in enumerate(chunk) if c == v] for v in "MA"]  # 0 : le fils
        left = [mine, his]
        state, moves = list(self.lab.states[0]), []
        while need[0] or need[1] or left[0] or left[1]:
            turn = len(moves) % 2
            who = turn if side == 0 else 1 - turn
            actions = {}
            for action in mind.possibles(state):
                actions.setdefault(mind.case_jouee(state, action), action)
            options = [c for c in need[who] if c in actions]
            if left[who]:
                options += [c for c in actions if c is not None and chunk[c] == "?"]
            if not options:
                return None
            cell = rng.choice(options)
            if cell in need[who]:
                need[who].remove(cell)
            else:
                left[who] -= 1
            state = mind.apres(state, actions[cell], self.marks[turn])
            moves.append(self.args(actions[cell]))
        return moves

    # ------------------------------------------------------------------ #
    # Refactor : remplacer des souvenirs par une règle
    # ------------------------------------------------------------------ #

    @property
    def pensee(self) -> concepts.Pensee:
        if self._pensee is None:
            self._pensee = concepts.Pensee(self.mind, self.knowledge["concepts"])
        return self._pensee

    @property
    def bank(self) -> list:
        """Les concepts que la mère sait former, du plus petit au plus grand."""
        if self._bank is None:
            positions = concepts.echantillon(self.mind, self.start_position(), self.knowledge["marks"])
            self._bank = concepts.enumerer(self.pensee, positions, self.max_size, self.max_depth, self.counts)
        return self._bank

    def rule(self, name: str) -> concepts.Concept:
        return self.knowledge["concepts"][name]  # l'arbre lui-même : un nom essayé peut être abandonné

    def decide(self, state, me, rules: list[str]) -> int:
        """Le coup que jouerait le fils avec ces règles, sans souvenir (comme son squelette)."""
        for name in rules:
            cells = self.pensee.choix(self.rule(name), state, me)
            if cells:
                return min(cells)
        return min(self.mind.possibles(list(state)))

    def good(self, case: Case, cell: int) -> bool:
        """Le coup est-il aussi bon que celui du professeur ? (vérifié dans le labo)"""
        return cell == case.teacher_cell or self.judge(case.moves, case.state, cell)

    def judge(self, moves: list[tuple], state, cell: int) -> bool:
        """Dans la position où mènent ``moves``, ``cell`` est-il aussi bon que le coup du
        professeur ? Le professeur finit la partie des deux côtés après chacun des deux."""
        key = (repr(list(state)), cell)
        if key not in self._judged:
            side, teacher = len(moves) % 2, self.teacher_move(moves)
            self._judged[key] = self.action(teacher) == cell or not self.better(moves, teacher, cell, side)
        return self._judged[key]

    def covering(self) -> dict[str, str | None]:
        """Pour chaque cas, la clé du souvenir qui décide (le sien ou celui d'une position
        équivalente), ou ``None`` si ce sont les règles qui décident."""
        memories, mind = self.knowledge["memories"], self.mind
        return {case.key: mind.rappel(list(case.state), case.me, memories)[0]
                for case in self.cases.values()}

    def check(self, rules: list[str], covering: dict) -> list[str] | None:
        """Rejoue tous les cas avec ces règles : ``None`` si un cas sans souvenir est raté,
        sinon les souvenirs dont plus aucun cas n'a besoin."""
        needed, useful = set(), set()
        for case in self.cases.values():
            ok = self.good(case, self.decide(case.state, case.me, rules))
            memory = covering[case.key]
            if memory is None:
                if not ok:
                    return None
            else:
                useful.add(memory)
                if not ok:
                    needed.add(memory)
        return sorted(useful - needed)

    def views(self, rules: list[str], freed: list[str]) -> int:
        """Positions regardées au plus par le fils écrit avec ces règles, sur les cas enregistrés."""
        knowledge = dict(self.knowledge, rules=rules,
                         memories={k: v for k, v in self.knowledge["memories"].items() if k not in freed})
        son = son_writer.load(son_writer.son_source("essai", knowledge))
        most = 0
        for case in self.cases.values():
            son.choisir(list(case.state), case.me)
            most = max(most, son.VUES)
            if most > self.budget:
                break
        return most

    def refactor(self) -> list[str]:
        """Remplace des souvenirs par des règles, tant que c'est possible, puis retire
        les règles devenues inutiles."""
        done = []
        while True:
            message = self.refactor_once()
            if message is None:
                break
            done.append(message)
        if done:
            done += self.prune()
        return done

    def prune(self) -> list[str]:
        """Retire chaque règle sans laquelle tous les cas restent bien joués (du code mort)."""
        done = []
        for name in list(reversed(self.knowledge["rules"])):
            rules = [r for r in self.knowledge["rules"] if r != name]
            if self.check(rules, self.covering()) is not None:
                self.knowledge["rules"] = rules
                self.rewrite()
                done.append(f"{name} retirée (inutile) ; règles : {' > '.join(rules) or 'aucune'}")
        return done

    def refactor_once(self) -> str | None:
        memories, definitions = self.knowledge["memories"], self.knowledge["concepts"]
        covering = self.covering()
        pending = [case for case in self.cases.values() if covering[case.key] is not None]
        if len({covering[case.key] for case in pending}) < 2:
            return None
        pensee = self.pensee
        candidates = []
        for rank, concept in enumerate(self.bank):
            explained = set()  # souvenirs expliqués (deux positions équivalentes comptent pour un)
            for case in pending:
                cells = pensee.choix(concept, case.state, case.me)
                if case.teacher_cell in cells and case.son_cell not in cells:
                    explained.add(covering[case.key])
            if len(explained) >= 2:
                candidates.append((concept.size, -len(explained), rank, concept))
        names = {c.id: name for name, c in definitions.items()}
        for _, _, _, concept in sorted(candidates):
            if concept.kind == "brique" and concept.args[1] == MOI and concept.args[0] in definitions:
                concept = definitions[concept.args[0]]  # une brique connue : la règle existe déjà
            known = concept.id in names
            name = names[concept.id] if known else f"concept_{len(definitions) + 1}"
            if not known:
                definitions[name] = concept
            others = [r for r in self.knowledge["rules"] if r != name]
            for rank in range(len(others), -1, -1):  # du moins prioritaire au plus prioritaire
                rules = others[:rank] + [name] + others[rank:]
                freed = self.check(rules, covering)
                if freed is not None and len(freed) >= 2 and self.views(rules, freed) <= self.budget:
                    return self.adopt(name, concept, rules, freed, known)
            if not known:
                del definitions[name]
        return None

    def adopt(self, name, concept, rules, freed, known) -> str:
        self.knowledge["rules"] = rules
        for key in freed:
            del self.knowledge["memories"][key]
        if not known:
            self._bank = None  # une nouvelle brique : la mère sait former de nouveaux concepts
        self.rewrite()
        what = "règle remontée" if known else f"nouvelle règle « {concepts.decrire_regle(concept)} »"
        return (f"{len(freed)} souvenirs -> {name} ({what}) ; "
                f"règles : {' > '.join(rules)} ; souvenirs : {len(self.knowledge['memories'])}")

    def train(self, nb_games: int, on_game=None) -> list[GameRecord]:
        """Fait jouer et corrige le fils ``nb_games`` fois (professeur, hasard et mixte, des deux côtés).

        Après chaque partie, la mère revoit les coups du fils et ses réponses aux
        variantes, corrige chaque erreur par un souvenir, puis refactorise.
        """
        if not self.records:
            record = self.first_lesson()
            if on_game:
                on_game(record)
        if len(self.marks) < 2:
            raise LabError("la mère n'a pas compris quel pion pose chaque joueur")
        opponents = [("professeur", self.teacher), ("hasard", self.random_player(self.rng)),
                     ("mixte", mixed_player(self.teacher, self.rng, self.random_player(self.rng)))]
        for number in range(1, nb_games + 1):
            name, opponent = opponents[(number - 1) // 2 % len(opponents)]
            side = (number - 1) % 2
            # Motifs décalés, symétries, petits motifs : des cases. Une valeur n'en a pas.
            shifted = [] if self._shapes_known or not self.tableau else self.shift_patterns()
            symmetry = None if self._symmetries_known or not self.tableau else self.discover_symmetries()
            result, decisions = self.play_game(opponent, side)
            record = GameRecord(len(self.records), name, str(self.marks[side]), RESULTS[result])
            record.impossibles = self.impossibles
            record.refactors += shifted
            if symmetry:
                record.refactors.append(symmetry)
            record.lessons = self.review(decisions + self.variations(decisions, side), side)
            if record.lessons:
                record.refactors += self.refactor()
                if self.tableau:
                    record.refactors += self.generalize()
            record.patterns, self.discovered = self.discovered, []
            self.records.append(record)
            if on_game:
                on_game(record)
        return self.records

    def evaluate(self, nb_random: int = 100) -> dict[str, dict[str, int]]:
        """Fait jouer le fils sans le corriger : bilan par adversaire."""
        scores = {}
        for name, opponent, games in (("professeur", self.teacher, 2),
                                      ("hasard", self.random_player(random.Random(1)), nb_random)):
            score = {"victoire": 0, "nul": 0, "défaite": 0}
            for number in range(games):
                result, _ = self.play_game(opponent, number % 2)
                score[RESULTS[result]] += 1
            scores[name] = score
        self.discovered = []
        return scores
