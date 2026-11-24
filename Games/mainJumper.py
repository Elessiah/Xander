"""Jouer à Jumper dans le terminal : ``python -m Games.mainJumper``.

Espace pour sauter, ``q`` (ou ``²``) pour quitter. Fonctionne sous Windows
(``msvcrt``) et sous Linux / macOS (``termios``).
"""

import os
import sys
import time

from Games.Jumper import Jumper

FRAME_DELAY = 0.1
QUIT_KEYS = ("q", "²")

if os.name == "nt":
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
    print("Appuie sur une touche pour commencer (espace : sauter, q : quitter)")
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
