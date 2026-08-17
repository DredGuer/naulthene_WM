#!/usr/bin/env python3
"""Compare deux `.brain` par leur CONTENU, jamais par leur md5 (17/08/2026).

⚠️ POURQUOI CE SCRIPT EXISTE — un piège qui a failli invalider un chantier.

Le protocole du projet utilisait `md5` pour vérifier qu'un correctif est « bit-identique ».
Mesuré le 17/08 : **deux runs rigoureusement identiques produisent des md5 DIFFÉRENTS**,
alors que leurs cerveaux sont égaux élément par élément (0 différence sur l'intégralité de
l'arbre : poids, buffers, dicts, scalaires).

La cause est la sérialisation `torch.save` (ordre interne du zip, horodatages), pas la
cognition. Conséquence : un md5 différent ne prouve **rien**, et un test « md5 identique »
qui passe est une chance, pas une garantie.

C'est un faux négatif dangereux : il fait croire qu'une télémétrie pure a modifié le run,
et pousse à « corriger » du code sain.

Usage :
    PYTHONPATH=src python docs/recherche/scripts/comparer_brains.py a.brain b.brain
"""
from __future__ import annotations
import sys

import torch


def comparer(x, y, prefixe=""):
    """Parcours récursif. Retourne la liste des chemins qui diffèrent."""
    diffs = []
    if isinstance(x, dict):
        if not isinstance(y, dict):
            return [f"{prefixe[:-1]} [type: dict vs {type(y).__name__}]"]
        for cle in x:
            if cle not in y:
                diffs.append(f"{prefixe}{cle} [absent à droite]")
                continue
            diffs += comparer(x[cle], y[cle], f"{prefixe}{cle}.")
        for cle in y:
            if cle not in x:
                diffs.append(f"{prefixe}{cle} [absent à gauche]")
    elif isinstance(x, (list, tuple)):
        if len(x) != len(y):
            return [f"{prefixe[:-1]} [longueurs {len(x)} vs {len(y)}]"]
        for i, (a, b) in enumerate(zip(x, y)):
            diffs += comparer(a, b, f"{prefixe}{i}.")
    elif torch.is_tensor(x):
        if x.shape != y.shape:
            diffs.append(f"{prefixe[:-1]} [formes {tuple(x.shape)} vs {tuple(y.shape)}]")
        elif not torch.equal(x.float(), y.float()):
            ecart = (x.float() - y.float()).abs().max().item()
            diffs.append(f"{prefixe[:-1]} [écart max {ecart:.3e}]")
    else:
        if x != y:
            diffs.append(f"{prefixe[:-1]} ({x!r} != {y!r})")
    return diffs


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    a = torch.load(sys.argv[1], map_location="cpu", weights_only=False)
    b = torch.load(sys.argv[2], map_location="cpu", weights_only=False)
    diffs = comparer(a, b)
    if not diffs:
        print(f"✅ IDENTIQUES — 0 différence de contenu")
        print(f"   ({sys.argv[1].split('/')[-1]} vs {sys.argv[2].split('/')[-1]})")
        return 0
    print(f"❌ {len(diffs)} différence(s) :")
    for d in diffs[:40]:
        print(f"   {d}")
    if len(diffs) > 40:
        print(f"   … et {len(diffs) - 40} autre(s)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
