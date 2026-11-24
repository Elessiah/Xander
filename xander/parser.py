"""Lecture d'un fichier d'exemple de partie.

Un fichier d'exemple est un script Python valide, découpé en sections par
des commentaires en début de ligne (voir ``docs/format-exemple.md``) ::

    # include               imports nécessaires au jeu
    # init                  création et initialisation de la partie
    # back                  fonction qui annule le dernier coup
    # player <nom>          appels faits par le joueur <nom> pendant son tour
    # end player <nom>      fin de la partie, <nom> a gagné (# end draw : nul)

Chaque appel qui affecte une variable doit être suivi d'un commentaire qui
décrit son type, et éventuellement sa taille : ``board = game.play(4)  # array 9``.
"""

from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass, field
from pathlib import Path

from xander.model import VARIABLE_KINDS, Function, Player, Variable


class ExampleSyntaxError(Exception):
    """Le fichier d'exemple ne respecte pas le format attendu."""

    def __init__(self, message: str, line_number: int | None = None, line: str = ""):
        if line_number is not None:
            message = f"ligne {line_number} : {message}\n    {line.rstrip()}"
        super().__init__(message)


@dataclass
class ParsedExample:
    """Résultat de l'analyse d'un fichier d'exemple."""

    source: Path | None = None
    imports: list[str] = field(default_factory=list)
    variables: list[Variable] = field(default_factory=list)
    init_functions: list[Function] = field(default_factory=list)
    back_function: Function | None = None
    players: dict[str, Player] = field(default_factory=dict)
    winner: str = ""  # nom du gagnant, "D" pour un match nul, "" si inconnu

    @property
    def players_name(self) -> list[str]:
        """Noms des joueurs dans l'ordre de leur première apparition."""
        return list(self.players)

    def player_functions(self) -> list[Function]:
        """Tous les appels des joueurs, triés chronologiquement."""
        functions = [f for player in self.players.values() for f in player.functions_used]
        return sorted(functions, key=lambda function: function.time)

    def summary(self) -> str:
        lines = [f"Exemple : {self.source}", "Init :"]
        lines += [f"  {function}" for function in self.init_functions]
        if self.back_function:
            lines.append(f"Back : {self.back_function.call_source()}")
        lines += [str(player) for player in self.players.values()]
        lines.append(f"Gagnant : {self.winner or 'inconnu'}")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Analyse d'une ligne
# --------------------------------------------------------------------------- #

def split_comment(line: str) -> tuple[str, str]:
    """Sépare le code du commentaire final (en ignorant les ``#`` dans les chaînes)."""
    try:
        for token in tokenize.generate_tokens(io.StringIO(line).readline):
            if token.type == tokenize.COMMENT:
                column = token.start[1]
                return line[:column].rstrip(), token.string[1:].strip()
    except tokenize.TokenError:
        pass
    return line.rstrip(), ""


def parse_type_comment(comment: str) -> tuple[str, int]:
    """``"array 9"`` -> ``("array", 9)`` ; ``"game"`` -> ``("game", 1)``."""
    words = comment.split()
    if not words:
        raise ValueError("type manquant (ex. : '# array 9')")
    kind = words[0].lower()
    if kind not in VARIABLE_KINDS:
        raise ValueError(f"type inconnu {kind!r}, attendu : {', '.join(VARIABLE_KINDS)}")
    if len(words) == 1:
        return kind, 1
    if not words[1].isdigit():
        raise ValueError(f"la taille doit être un entier, pas {words[1]!r}")
    return kind, int(words[1])


def literal_or_none(node: ast.expr):
    try:
        return ast.literal_eval(node)
    except ValueError:
        return None


def parse_call_line(code: str, comment: str) -> tuple[Variable, str, list[str], list]:
    """Analyse ``[var =] objet.fonction(args)`` et renvoie ses éléments."""
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        raise ValueError(f"code Python invalide ({error.msg})") from None
    if len(tree.body) != 1:
        raise ValueError("une seule instruction par ligne")
    statement = tree.body[0]

    target = Variable()
    if isinstance(statement, ast.Assign):
        if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
            raise ValueError("une seule variable simple peut recevoir le résultat")
        kind, size = parse_type_comment(comment)
        target = Variable(kind=kind, size=size, name=statement.targets[0].id)
        call = statement.value
    elif isinstance(statement, ast.Expr):
        call = statement.value
    else:
        raise ValueError("seuls les appels de fonction sont acceptés")

    if not isinstance(call, ast.Call):
        raise ValueError("un appel de fonction est attendu")
    if call.keywords:
        raise ValueError("les arguments nommés ne sont pas encore gérés")
    if any(isinstance(arg, ast.Call) for arg in call.args):
        raise ValueError("les appels imbriqués ne sont pas encore gérés")

    name = ast.get_source_segment(code, call.func)
    parameters = [ast.get_source_segment(code, arg) for arg in call.args]
    arguments = [literal_or_none(arg) for arg in call.args]
    return target, name, parameters, arguments


# --------------------------------------------------------------------------- #
# Analyse du fichier
# --------------------------------------------------------------------------- #

class ExampleParser:
    """Transforme un fichier d'exemple en :class:`ParsedExample`.

    Le compteur ``time`` donne l'ordre chronologique des appels : les appels
    de ``# init`` puis ceux des joueurs, dans l'ordre du fichier. La fonction
    ``# back`` n'est pas jouée pendant la partie et garde ``time = 0``.
    """

    INCLUDE, INIT, BACK, PLAYER, END = "include", "init", "back", "player", "end"

    def __init__(self):
        self.result = ParsedExample()
        self.time = 0
        self.section = self.INCLUDE
        self.current_player: str | None = None

    def parse_file(self, path: str | Path) -> ParsedExample:
        path = Path(path)
        result = self.parse_text(path.read_text(encoding="utf-8"))
        result.source = path
        return result

    def parse_text(self, text: str) -> ParsedExample:
        for number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            if line.startswith("#"):
                self._parse_header(line, number)
            else:
                self._parse_code(line, number)
        if not self.result.players:
            raise ExampleSyntaxError("aucun joueur trouvé (section '# player <nom>' manquante)")
        return self.result

    def _parse_header(self, line: str, number: int) -> None:
        words = line[1:].split()
        if not words:
            return
        keyword = words[0].lower()
        if keyword == self.INCLUDE:
            self.section = self.INCLUDE
        elif keyword == self.INIT:
            self.section = self.INIT
        elif keyword == self.BACK:
            self.section = self.BACK
        elif keyword == self.PLAYER:
            if len(words) < 2:
                raise ExampleSyntaxError("nom du joueur manquant", number, line)
            self.section = self.PLAYER
            self.current_player = words[1]
            self.result.players.setdefault(self.current_player, Player(self.current_player))
        elif keyword == self.END:
            self.section = self.END
            if len(words) >= 3 and words[1].lower() == self.PLAYER:
                self.result.winner = words[2]
            elif len(words) >= 2 and words[1].lower() in ("draw", "nul", "d"):
                self.result.winner = "D"
        # Les autres commentaires en début de ligne sont ignorés.

    def _parse_code(self, line: str, number: int) -> None:
        if self.section == self.INCLUDE:
            self.result.imports.append(line.strip())
            return
        if self.section == self.END:
            raise ExampleSyntaxError("du code après '# end'", number, line)

        code, comment = split_comment(line.strip())
        try:
            target, name, parameters, arguments = parse_call_line(code, comment)
        except ValueError as error:
            raise ExampleSyntaxError(str(error), number, line) from None

        function = Function(name, target, parameters, self.time, arguments)
        if not target.is_empty:
            self.result.variables.append(target)

        if self.section == self.BACK:
            function.time = 0
            self.result.back_function = function
            return
        self.time += 1
        if self.section == self.INIT:
            self.result.init_functions.append(function)
        else:
            self.result.players[self.current_player].functions_used.append(function)


def parse_example(path: str | Path) -> ParsedExample:
    """Raccourci : analyse le fichier ``path``."""
    return ExampleParser().parse_file(path)
