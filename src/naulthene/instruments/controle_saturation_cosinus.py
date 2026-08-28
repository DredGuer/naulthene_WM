# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Contrôle d'instrument — le cosinus sature-t-il dans un espace à activations positives ?

Cinq lignes de données synthétiques dont on connaît la réponse. À lancer AVANT de publier
toute conclusion fondée sur une similarité cosinus.

RÉSULTAT : deux nuages nettement séparés (d' = 2,925) donnent encore **cos = 0,9711**, et
deux nuages identiques donnent **0,9991**. Dans un espace post-`relu` — où tout est ≥ 0 et
où les vecteurs sont confinés au même hyper-octant — le cosinus ne discrimine rien.

C'est ce contrôle qui a invalidé la conclusion « le réseau détruit l'information » publiée
le 28/08 (voir l'addendum de `docs/recherche/COLLAPSE_28082026_*.md`). Le plancher
intra-classe valait 0,9999 dans la sonde d'origine : ce n'était pas une validation, c'était
le signe que l'indicateur était mort.
"""
import numpy as np
rng=np.random.RandomState(0)
def cos(a,b):
    a,b=a.mean(0),b.mean(0); return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)))
def dprime(A,B):
    mu=A.mean(0)-B.mean(0); ec=np.linalg.norm(mu)
    s=(np.sqrt(((A-A.mean(0))**2).sum(1).mean())+np.sqrt(((B-B.mean(0))**2).sum(1).mean()))/2
    return ec/s
print("Deux nuages a activations POSITIVES (relu), avec des moyennes DIFFERENTES :\n")
print(f"{'ecart des moyennes':<22}{'cosinus':>10}{'d-prime':>10}")
print("-"*42)
for ecart in [0.0, 0.1, 0.3, 1.0, 3.0]:
    A=np.abs(rng.randn(150,64))+1.0
    B=np.abs(rng.randn(150,64))+1.0+ecart*rng.rand(64)
    print(f"{ecart:<22.2f}{cos(A,B):>10.4f}{dprime(A,B):>10.3f}")
print("\n→ le cosinus reste >0,97 MEME quand les nuages sont nettement separes (d'=3+).")
print("  Dans un espace a activations positives, il SATURE. Le d' ne sature pas.")
