"""CI locale de Xander : rapide, sans dépendance, à lancer avant chaque fusion.

    python ci.py              # les tests rapides et l'apprentissage des exemples
    python ci.py --complet    # en plus, les tests lents (marqués ``@lent``)
    python ci.py morpion3     # seulement les tâches dont le nom contient « morpion3 »

Chaque classe de tests et chaque exemple de ``res/`` tourne dans son propre
processus, tous en parallèle : la durée totale est celle de la tâche la plus
longue, pas la somme. Le code de sortie vaut 0 si tout passe.
"""

import argparse
import ast
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

RACINE = Path(__file__).resolve().parent


def classes_de_tests(chemin: Path) -> list:
    """Les classes du fichier qui définissent au moins une méthode ``test_`` (lu sans importer)."""
    arbre = ast.parse(chemin.read_text(encoding="utf-8"))
    return [noeud.name for noeud in arbre.body if isinstance(noeud, ast.ClassDef)
            and any(isinstance(f, ast.FunctionDef) and f.name.startswith("test_") for f in noeud.body)]


def taches() -> list:
    """(nom, commande) : une classe de tests, ou l'apprentissage d'un exemple."""
    liste = [(f"tests/{p.name}::{classe}", [sys.executable, "-m", "unittest", f"tests.{p.stem}.{classe}"])
             for p in sorted((RACINE / "tests").glob("test_*.py")) for classe in classes_de_tests(p)]
    liste += [(f"res/{p.name}", [sys.executable, "-m", "xander", str(p.relative_to(RACINE))])
              for p in sorted((RACINE / "res").glob("example*.py"))]
    return liste


def lancer(commande: list, env: dict) -> tuple:
    debut = time.perf_counter()
    fini = subprocess.run(commande, cwd=RACINE, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return fini.returncode, fini.stdout + fini.stderr, time.perf_counter() - debut


def main() -> int:
    parser = argparse.ArgumentParser(description="CI locale de Xander")
    parser.add_argument("--complet", action="store_true", help="lancer aussi les tests lents")
    parser.add_argument("filtres", nargs="*", help="ne garder que les tâches dont le nom contient l'un de ces mots")
    args = parser.parse_args()

    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    if args.complet:
        env["XANDER_LENT"] = "1"
    liste = [(nom, cmd) for nom, cmd in taches()
             if not args.filtres or any(f in nom for f in args.filtres)]
    if not liste:
        print("Aucune tâche ne correspond.")
        return 1

    debut = time.perf_counter()
    echecs = []
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        futurs = {pool.submit(lancer, cmd, env): nom for nom, cmd in liste}
        for futur in as_completed(futurs):
            nom = futurs[futur]
            code, sortie, duree = futur.result()
            print(f"{'ok   ' if code == 0 else 'ÉCHEC'} {duree:6.1f} s  {nom}", flush=True)
            if code != 0:
                echecs.append((nom, sortie))

    for nom, sortie in echecs:
        print(f"\n===== {nom} =====\n{sortie.rstrip()}")
    mode = "complète" if args.complet else "rapide"
    bilan = f"{len(liste) - len(echecs)}/{len(liste)} tâches réussies"
    print(f"\nCI {mode} : {bilan} en {time.perf_counter() - debut:.1f} s")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
