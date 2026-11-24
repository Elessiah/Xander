"""Jouer à Jumper dans le terminal : ``python -m Games.mainJumper``.

Espace pour sauter, ``q`` (ou ``²``) pour quitter. Fonctionne sous Windows
(``msvcrt``) et sous Linux / macOS (``termios``).
"""

import os
import queue
import sys
import threading
import time

from Games.Jumper import Jumper

FRAME_DELAY = 0.1
QUIT_KEYS = ("q", "²")

# La console « Run » de PyCharm (et toute entrée redirigée) n'est pas un vrai
# terminal : msvcrt / termios n'y voient aucune touche. On se rabat alors sur
# une lecture ligne par ligne : Entrée pour sauter, « q » + Entrée pour quitter.
INTERACTIVE = sys.stdin.isatty()

if not INTERACTIVE:
    _lines = queue.Queue()

    def _read_lines():
        for line in sys.stdin:
            _lines.put(line.strip() or " ")
        _lines.put("q")  # fin de l'entrée : on quitte proprement

    threading.Thread(target=_read_lines, daemon=True).start()

    def read_key_non_blocking(timeout=FRAME_DELAY):
        try:
            return _lines.get(timeout=timeout)[0]
        except queue.Empty:
            return None

    def clear_screen():
        print("\n" * 3)
elif os.name == "nt":
    import msvcrt

    def read_key_non_blocking(timeout=FRAME_DELAY):
        end = time.monotonic() + timeout
        key = None
        while time.monotonic() < end:
            if msvcrt.kbhit():
                key = msvcrt.getwch()
            time.sleep(0.01)
        return key

    def clear_screen():
        os.system("cls")
else:
    import select
    import termios
    import tty

    def read_key_non_blocking(timeout=FRAME_DELAY):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ready, _, _ = select.select([sys.stdin], [], [], timeout)
            return sys.stdin.read(1) if ready else None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def clear_screen():
        os.system("clear")


def main():
    if INTERACTIVE:
        print("Appuie sur une touche pour commencer (espace : sauter, q : quitter)")
    else:
        print(
            "Console non interactive (ex. : Run de PyCharm) : appuie sur Entrée "
            "pour commencer et pour sauter, « q » + Entrée pour quitter.\n"
            "Pour jouer avec la barre d'espace, lance le jeu depuis un vrai "
            "terminal : python -m Games.mainJumper"
        )
    while read_key_non_blocking() is None:
        pass

    game = Jumper()
    while not game.game_over:
        key = read_key_non_blocking()
        if key in QUIT_KEYS:
            break
        game.play(key == " ")
        clear_screen()
        game.print()
    print(f"Perdu ! Distance parcourue : {game.ticks}")


if __name__ == "__main__":
    main()
