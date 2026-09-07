#!/usr/bin/env python3
"""Lecteur unique des journaux de cursus (registre MES-01).

Chaque campagne recopiait sa propre fonction `lire()` et ses propres expressions
régulières. Une expression régulière copiée six fois est six occasions de dériver
sans que personne ne s'en aperçoive : c'est la même maladie que MES-02
(l'instrument qui réimplémente le noyau). Ce module est la seule lecture autorisée
d'un `*.log` de run de cursus.

Il ne juge rien : il transcrit. Toute la sévérité est dans
`naulthene.instruments.depouillement`.
"""
from __future__ import annotations

import re
import statistics as st
from typing import Any

__all__ = ["lire_journal", "resumer_journal", "FENETRE_FINALE"]

#: Nombre de nuits finales sur lesquelles les médianes de fin de run sont prises.
FENETRE_FINALE = 100

_JOUR = re.compile(r"^🌙 Jour (\d+) ")
_CURSUS = re.compile(r"Niveau (\d+)/15 — maîtrise (\d+)%")
_ARBITRAGE = re.compile(r"C1=([\d.]+) C2=([\d.]+).*?gain C1 ×([\d.]+)")
_ACCORD = re.compile(r"accord ([\d.]+)%")
_VICTOIRES = re.compile(r"🏆 (\d+) victoire\(s\)")
_ENTROPIE_C1 = re.compile(r"entropie des votes — C1 ([\d.]+)")


def lire_journal(chemin: str) -> list[dict[str, Any]]:
    """Transcrit un journal de run en une ligne par nuit **complète**.

    Une nuit sans ligne de cursus est écartée : c'est une journée tronquée par un
    arrêt brutal, pas une observation.
    """
    nuits: list[dict[str, Any]] = []
    courante: dict[str, Any] | None = None
    with open(chemin, errors="ignore", encoding="utf-8") as fh:
        for ligne in fh:
            debut = _JOUR.match(ligne)
            if debut:
                if courante:
                    nuits.append(courante)
                courante = {"j": int(debut.group(1))}
                continue
            if courante is None:
                continue
            m = _ARBITRAGE.search(ligne)
            if m:
                courante.update(c1=float(m.group(1)), c2=float(m.group(2)),
                                gain=float(m.group(3)))
            m = _ACCORD.search(ligne)
            if m:
                courante["accord"] = float(m.group(1))
            m = _VICTOIRES.search(ligne)
            if m:
                courante["vict"] = int(m.group(1))
            m = _ENTROPIE_C1.search(ligne)
            if m:
                courante["hc1"] = float(m.group(1))
            m = _CURSUS.search(ligne)
            if m:
                courante.update(niv=int(m.group(1)), mait=int(m.group(2)))
    if courante:
        nuits.append(courante)
    return [n for n in nuits if "niv" in n]


def _mediane_finale(nuits: list[dict[str, Any]], cle: str, fenetre: int):
    valeurs = [n[cle] for n in nuits[-fenetre:] if cle in n]
    return st.median(valeurs) if valeurs else None


def resumer_journal(nuits: list[dict[str, Any]],
                    fenetre: int = FENETRE_FINALE) -> dict[str, Any] | None:
    """État de fin de run : dernier jour, dernier palier, médianes de la fenêtre finale.

    Le **niveau** est celui du dernier jour, jamais une médiane : c'est un palier
    atteint, pas une tendance. La **maîtrise** est une médiane de fenêtre parce
    qu'elle est quantifiée par pas de 5 % et fortement bruitée (voir EVA-01).
    """
    if not nuits:
        return None
    dernier = nuits[-1]
    return {
        "jours_final": dernier["j"],
        "niv": dernier["niv"],
        "vict": dernier.get("vict", 0),
        "nuits": len(nuits),
        "mait": _mediane_finale(nuits, "mait", fenetre),
        "gain": _mediane_finale(nuits, "gain", fenetre),
        "c1": _mediane_finale(nuits, "c1", fenetre),
        "c2": _mediane_finale(nuits, "c2", fenetre),
        "hc1": _mediane_finale(nuits, "hc1", fenetre),
        "accord": _mediane_finale(nuits, "accord", fenetre),
    }
