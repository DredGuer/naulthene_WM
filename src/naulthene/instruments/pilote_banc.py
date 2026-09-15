# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Le pilote EVA-01 — la dérivation MESURÉE de `n` (règle de domination du bruit).

Pourquoi ce module existe
-------------------------
Le banc final ne POSE pas son nombre d'épisodes : il le **dérive**. `n` est un RÉSULTAT,
pas une constante de confort (spec §8bis). La règle, déclarée d'avance :

    retenir le plus petit `n >= 1` tel que l'erreur-type binomiale du taux d'UN cerveau
    reste <= (1 / facteur) × l'écart-type INTER-CERVEAUX de ce même taux, mesuré sur
    cartes figées.

    SE_binomiale(n) = sqrt( p_barre (1 − p_barre) / n )   <=   sd_inter / facteur

Le seul paramètre **posé** de la règle est `facteur = 3,0` : il est isolé dans une
constante nommée, précisément pour pouvoir être contesté ou mesuré plus tard. Tout le
reste — `p_barre`, la dispersion, et les **intervalles de confiance** — est MESURÉ par
`mesurer_pilote`, puis publié dans `pilote.json` à côté de la ligne de calcul.

⚠️ LE `20` DU PILOTE N'EST PAS LE `n` DU PROTOCOLE. `EPISODES_PILOTE` est un **budget de
MESURE**. Le `n` qui entre au protocole est celui que la règle produit, et lui seul.

⚠️🔴 LA DISPERSION OBSERVÉE EST GONFLÉE PAR LE PILOTE LUI-MÊME — C'EST LA CORRECTION DU
TOUR 1, ET ELLE CHANGE LA VALEUR PUBLIÉE. Un taux mesuré sur `n` épisodes est une MOYENNE,
donc bruité. La dispersion observée entre cerveaux contient donc ce bruit en plus de la
dispersion réelle :

    E[s²] = σ² + v        σ = dispersion RÉELLE entre cerveaux
                          v = variance d'échantillonnage du taux de chaque cerveau

Mesuré sur le premier pilote (20 épisodes par carte) : `s² = 0,00515625`, dont **92 %**
étaient de la variance d'échantillonnage. Le `333` dérivé de `s` était donc une **borne
basse**, pas une estimation — et le bruit de mesure ne dominait PAS la dispersion réelle,
contrairement à l'intention écrite du §8bis.

⚠️ CE BIAIS NE SE CORRIGE PAS EN AJOUTANT DES CERVEAUX. `E[s²] = σ² + v` quel que soit leur
nombre : c'est `v` qu'il faut faire baisser, donc jouer PLUS D'ÉPISODES PAR CERVEAU
(`v ≈ p(1−p)/n`, divisé par 10 quand `n` passe de 20 à 200). D'où `EPISODES_PILOTE = 200`.

La règle n'est pas changée pour autant : le §8bis nomme « l'écart-type inter-cerveaux de ce
même taux », c'est-à-dire σ. `s` en est un estimateur biaisé, σ̂ = `sqrt(max(0, s² − v))` en
est l'estimateur correct — voir `variance_echantillonnage`. Les deux sont PUBLIÉS côte à
côte (`sd_inter`, `sd_inter_deconvoluee`). Le `n` POOLÉ (`n_derive_poole`, dérivé de σ̂, et
`n_derive_poole_sd_observee`, dérivé de `s` — borne basse) est publié POUR MÉMOIRE, jamais
comme gel ; le gel est `n_final = max(n PAR CARTE)`.

⚠️ UNE SD DE PILOTE EST INSTABLE. À 4 cerveaux, l'intervalle de confiance de la SD
estimée est large (mesuré : pour `s = 0,15`, `IC95 = [0,085 ; 0,559]`). Publier la seule
valeur ponctuelle ferait passer une dispersion mal connue pour un chiffre ferme — d'où
`intervalle_confiance_sd`, et son équivalent dé-convolué, qui entrent dans `pilote.json`
sous les clés `ic_sd` et `ic_sd_deconvoluee`. La dé-convolution corrige le BIAIS, pas
l'instabilité : à 4 cerveaux `s²` reste estimé sur 3 degrés de liberté.

⚠️ CE MODULE EST PUR AU CHARGEMENT : `banc_final` (donc `noyau` et `torch`) n'est importé
qu'à l'intérieur des fonctions qui mesurent réellement. C'est ce qui permet de tester la
règle — et de la contester — sans charger un cerveau ni lancer une évaluation.

Ce que ce module ne fait PAS : il ne juge pas la justesse du banc. Il dimensionne
l'instrument ; il ne certifie pas qu'il mesure la bonne chose.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import statistics
import sys
from datetime import datetime, timezone
from typing import Sequence

__all__ = [
    "ALPHA_IC_SD",
    "CARTES_PILOTE",
    "CORRECTION_MAX_DERIVER_N",
    "EPISODES_PILOTE",
    "FACTEUR_DOMINATION",
    "PiloteMalDimensionne",
    "PiloteNonDerive",
    "TOLERANCE_RELATIVE_CONTRAINTE",
    "deriver_depuis_rapport",
    "deriver_n",
    "dispersion_inter_cerveaux",
    "intervalle_confiance_sd",
    "mesurer_pilote",
    "variance_echantillonnage",
]

# Les 2 cartes figées du protocole (spec §8, constantes gelées v1) :
# 3 = MiniGrid-SimpleCrossingS9N1-v0 (le mur), 4 = MiniGrid-LavaGapS5-v0 (le palier suivant).
CARTES_PILOTE: tuple[int, int] = (3, 4)
# BUDGET DE MESURE du pilote — jamais le `n` du protocole (voir l'en-tête).
#
# ⚠️ 20 -> 200 (tour de correction 1). À 20, `v` valait 0,00454 pour une variance observée
# de 0,00516, soit 92 % de bruit d'échantillonnage : la dispersion publiée était celle du
# PILOTE, pas celle des cerveaux. À 200, `v` est divisé par 10.
EPISODES_PILOTE: int = 200
# Le SEUL paramètre posé de la règle (spec §8bis) : bruit de mesure <= 1/3 de la dispersion.
FACTEUR_DOMINATION: float = 3.0
ALPHA_IC_SD: float = 0.05
NB_CERVEAUX_PILOTE_MIN: int = 2     # une dispersion ne se mesure pas sur un seul cerveau
NB_CERVEAUX_PILOTE_MAX: int = 4     # borne de la spec §8bis (« 2 à 4 cerveaux »)

# ⚠️ TOLÉRANCE DE BORD, MESURÉE — PAS UN CONFORT. La contrainte de la règle tombe
# EXACTEMENT sur une borne pour les valeurs décimales rondes du brief (0,5 / 0,15 / 3) :
# mathématiquement `sqrt(0,25/100) = 0,05 <= 0,15/3 = 0,05`. En virgule flottante IEEE,
# `(0.25/100)**0.5` vaut 0,050000000000000003 et `0.15/3` vaut 0,049999999999999996 :
# la comparaison EXACTE est donc FAUSSE (mesuré) et rendrait `n = 101` au lieu de `100`
# — un épisode de plus pour un écart de représentation de 6,9e-18. La tolérance relative
# ci-dessous vaut 1e-12, soit 5e-14 en absolu sur cette borne : très au-dessus de l'écart
# de représentation, très en dessous de tout effet qui aurait un sens pour la mesure.
TOLERANCE_RELATIVE_CONTRAINTE: float = 1e-12

# Borne de la boucle de correction de `deriver_n` (voir la fonction) : l'estimation
# analytique est le minimum de la contrainte, donc une correction de plus de quelques
# unités signale une contrainte ALTÉRÉE, jamais un besoin réel. Au-delà, on lève.
CORRECTION_MAX_DERIVER_N: int = 8


class PiloteMalDimensionne(RuntimeError):
    """Le pilote exige 2 à 4 cerveaux : hors de là, la dispersion inter-cerveaux est
    soit indéfinie (1 cerveau), soit hors de la spec §8bis (au-delà de 4)."""


class PiloteNonDerive(RuntimeError):
    """Aucune dérivation n'est publiée sur une cohorte invalide (MES-01).

    Un banc qui sort en violation n'a RIEN mesuré d'exploitable : écrire un `pilote.json`
    à partir de ses chiffres partiels serait publier un agrégat sur une campagne
    incomplète — exactement ce que `Depouillement.publier` interdit.
    """


# --- 1. LA RÈGLE : LE PLUS PETIT `n` QUI DOMINE LE BRUIT DE MESURE ----------------


def deriver_n(p_barre: float, sd_inter: float, facteur: float = FACTEUR_DOMINATION) -> int:
    """Le plus petit `n >= 1` tel que `sqrt(p̄(1−p̄)/n) <= sd_inter / facteur`.

    Fonction **pure** : elle ne lit aucun fichier, ne charge aucun cerveau, ne lance
    aucune évaluation. C'est ce qui la rend testable et contestable sans mesurer.

    Refus (plutôt qu'un `n` arbitraire) :
      - `sd_inter <= 0` : le pilote n'a mesuré AUCUNE dispersion. Une SD nulle signifie
        que les cerveaux sont indiscernables sur la métrique, pas que le bruit de mesure
        est dominé : rendre `n = 1` (la contrainte `0 <= 0` est satisfaite) ou `n = 10000`
        serait dans les deux cas un chiffre INVENTÉ ;
      - `p_barre` hors de `]0, 1[` : taux saturé, la variance binomiale est nulle et la
        règle n'a plus d'objet ;
      - `facteur <= 0` : le levier de la règle ne serait plus un levier.

    La contrainte est évaluée avec `TOLERANCE_RELATIVE_CONTRAINTE` (voir la constante) :
    elle tranche les cas de BORD, elle ne relâche pas la règle.
    """
    p_barre = float(p_barre)
    sd_inter = float(sd_inter)
    facteur = float(facteur)
    if not 0.0 < p_barre < 1.0:
        raise ValueError(
            f"p_barre={p_barre!r} hors de ]0, 1[ : un taux saturé n'a pas de variance "
            f"binomiale — la règle de domination du bruit n'a plus d'objet")
    if sd_inter <= 0.0:
        raise ValueError(
            f"sd_inter={sd_inter!r} <= 0 : le pilote n'a mesuré aucune dispersion "
            f"inter-cerveaux — un `n` dérivé d'une SD nulle serait un chiffre inventé")
    if facteur <= 0.0:
        raise ValueError(f"facteur={facteur!r} <= 0 : le seul paramètre posé de la règle "
                         f"doit être strictement positif")

    variance = p_barre * (1.0 - p_barre)
    cible = (sd_inter / facteur) * (1.0 + TOLERANCE_RELATIVE_CONTRAINTE)
    # Estimation directe : n >= variance / cible². Le plancher à 1 est le « n >= 1 » de
    # la spec : une dispersion énorme ne doit pas rendre 0 épisode.
    n = max(1, int(math.floor(variance / (cible * cible))))
    # La boucle corrige les arrondis de l'estimation dans les DEUX sens : elle ne rend un
    # `n` que lorsque la contrainte est réellement tenue, et elle part du bas pour que le
    # résultat soit bien le PLUS PETIT qui la tienne.
    #
    # ⚠️ ELLE EST BORNÉE, ET PAS SEULEMENT PAR PRUDENCE. L'estimation ci-dessus est le
    # minimum ANALYTIQUE (n >= variance/cible²) : la correction ne peut donc valoir que
    # quelques unités, et seulement si l'arrondi flottant a fait descendre le plancher.
    # Si elle en demandait davantage, c'est que la contrainte ou la cible a été altérée
    # (garde neutralisé, tolérance portée à une valeur absurde) : boucler sans borne
    # transformerait ce défaut en boucle infinie, c'est-à-dire en gel silencieux. On
    # préfère crier.
    for _ in range(CORRECTION_MAX_DERIVER_N):
        if math.sqrt(variance / n) <= cible:
            return n
        n += 1
    raise RuntimeError(
        f"deriver_n : la contrainte n'est toujours pas tenue après "
        f"{CORRECTION_MAX_DERIVER_N} corrections depuis n={n} — l'estimation analytique "
        f"et la vérification divergent, ce qui signale une contrainte altérée "
        f"(p_barre={p_barre!r}, sd_inter={sd_inter!r}, facteur={facteur!r})")


def _quantile_chi2(p: float, df: int) -> float:
    """Quantile de la loi du chi-deux à `df` degrés de liberté, en pur `math`.

    Sert à l'intervalle de confiance de la SD ; aucune dépendance nouvelle n'est
    introduite pour une fonction de table. Résolution par bissection sur la fonction
    gamma incomplète régularisée, comme `depouillement.seuil_t` le fait sur la bêta.
    """
    if not 0.0 < p < 1.0:
        raise ValueError(f"probabilité {p!r} hors de ]0, 1[")
    if df < 1:
        raise ValueError(f"df={df} invalide (>= 1)")
    a = df / 2.0
    bas, haut = 0.0, 1.0
    while _gamma_incomplete_regularisee(a, haut / 2.0) < p:
        haut *= 2.0
        if haut > 1e12:
            return haut
    for _ in range(200):
        milieu = 0.5 * (bas + haut)
        if _gamma_incomplete_regularisee(a, milieu / 2.0) < p:
            bas = milieu
        else:
            haut = milieu
    return 0.5 * (bas + haut)


def _gamma_incomplete_regularisee(a: float, x: float) -> float:
    """`P(a, x)`, fonction gamma incomplète régularisée inférieure (série + Lentz).

    Écrite ici parce que le dépôt n'a que `math` : c'est la primitive dont dépend le
    quantile du chi-deux, elle-même primitive de l'IC de la SD. Aucune dépendance
    nouvelle (contrainte de la tâche).
    """
    if x <= 0.0:
        return 0.0
    if x < a + 1.0:  # série : converge vite pour x < a + 1
        ap, somme, delta = a, 1.0 / a, 1.0 / a
        for _ in range(1000):
            ap += 1.0
            delta *= x / ap
            somme += delta
            if abs(delta) < abs(somme) * 1e-16:
                break
        return somme * math.exp(-x + a * math.log(x) - math.lgamma(a))
    # fraction continue de Lentz pour Q(a, x) (Numerical Recipes §6.2)
    minuscule = 1e-300
    b = x + 1.0 - a
    c = 1.0 / minuscule
    d = 1.0 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < minuscule:
            d = minuscule
        c = b + an / c
        if abs(c) < minuscule:
            c = minuscule
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-16:
            break
    return 1.0 - math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def intervalle_confiance_sd(sd: float, n: int, alpha: float = ALPHA_IC_SD
                            ) -> tuple[float, float]:
    """IC de la SD estimée sur `n` observations indépendantes (`n − 1` degrés de liberté).

    Loi du chi-deux sur la VARIANCE, puis racine :

        IC(sigma²) = [ df·s² / χ²(1−α/2 ; df) , df·s² / χ²(α/2 ; df) ]

    ⚠️ POURQUOI CETTE PIÈCE EST OBLIGATOIRE DANS LE CARNET. Un pilote à petit `n` donne
    une SD très mal connue : à 4 cerveaux, `s = 0,15` a pour IC95 `[0,085 ; 0,559]`, et
    `n` en hérite. Publier la valeur ponctuelle seule ferait passer cette instabilité
    pour une mesure ferme. L'intervalle est ASYMÉTRIQUE (plus large au-dessus) : le
    chi-deux n'est pas symétrique, et un intervalle symétrique mentirait sur ce point.

    Hypothèse assumée et écrite : les taux par cerveau sont traités comme approximativement
    normaux. À 4 cerveaux c'est une approximation, pas une garantie — c'est une LIMITE,
    publiée comme telle dans le carnet, pas un détail tu.

    Une SD nulle rend `(0,0)` : mesurer zéro dispersion n'est pas une erreur de calcul,
    c'est un résultat (que `deriver_n` refuse ensuite, lui, de convertir en `n`).
    """
    if n < 2:
        raise ValueError(f"n={n} : une dispersion ne se mesure pas sur moins de 2 "
                         f"observations")
    if sd < 0.0:
        raise ValueError(f"sd={sd!r} négative")
    if sd == 0.0:
        return (0.0, 0.0)
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha={alpha!r} hors de ]0, 1[")
    df = n - 1
    variance = sd * sd
    bas = math.sqrt(df * variance / _quantile_chi2(1.0 - alpha / 2.0, df))
    haut = math.sqrt(df * variance / _quantile_chi2(alpha / 2.0, df))
    return (bas, haut)


def variance_echantillonnage(taux_par_carte: Sequence[float],
                             episodes_par_carte: Sequence[int]) -> float:
    """`v` — la variance d'ÉCHANTILLONNAGE du taux poolé d'un cerveau, en pur calcul.

    ⚠️ POURQUOI CETTE FONCTION EXISTE, ET C'EST LE CŒUR DU PILOTE. Le taux d'un cerveau
    n'est pas une constante : c'est une MOYENNE de `n` tirages. La dispersion observée
    entre cerveaux mélange donc deux choses :

        E[s²] = σ² + v        σ = la dispersion RÉELLE entre cerveaux,
                              v = la variance d'échantillonnage du taux de chacun.

    `s` est donc un estimateur **biaisé vers le haut** de σ — et d'autant plus que le
    pilote joue peu d'épisodes. Mesuré sur le premier pilote (20 épisodes par carte) :
    `s² = 0,00515625`, dont **92 %** de variance d'échantillonnage. Le `n` dérivé de `s`
    était donc une **borne basse**, pas une estimation. ⚠️ Ce biais ne se corrige PAS en
    ajoutant des cerveaux (`E[s²] = σ² + v` quel que soit leur nombre) : il se corrige en
    jouant PLUS D'ÉPISODES PAR CERVEAU, ce qui réduit `v`.

    La formule n'est PAS `p̄(1−p̄)/N` : les deux cartes n'ont pas le même taux, et les
    traiter comme un seul binôme serait faux. Le taux par cerveau est
    `r = Σ_c (n_c/N) · k_c/n_c`, donc, les cartes étant indépendantes :

        v = Σ_c (n_c/N)² · p_c(1−p_c)/n_c = Σ_c n_c·p_c(1−p_c) / N²      N = Σ_c n_c
    """
    taux = [float(p) for p in taux_par_carte]
    effectifs = [int(n) for n in episodes_par_carte]
    if len(taux) != len(effectifs):
        raise ValueError(f"{len(taux)} taux pour {len(effectifs)} effectifs")
    if not taux:
        raise ValueError("aucune carte : la variance d'échantillonnage n'est pas définie")
    if any(n <= 0 for n in effectifs):
        raise ValueError(f"effectif nul ou négatif dans {effectifs}")
    if any(not 0.0 <= p <= 1.0 for p in taux):
        raise ValueError(f"taux hors de [0, 1] dans {taux}")
    total = sum(effectifs)
    return sum(n * p * (1.0 - p) for p, n in zip(taux, effectifs)) / (total * total)


def dispersion_inter_cerveaux(taux_par_cerveau: Sequence[float],
                              alpha: float = ALPHA_IC_SD,
                              variance_echantillonnage_par_cerveau: float = 0.0) -> dict:
    """La dispersion qui entre dans la règle : celle des CERVEAUX, jamais des épisodes.

    Sur `taux_par_cerveau = [0,10 ; 0,30]`, l'écart-type vaut 0,1414 — c'est la
    variabilité réelle entre cerveaux, celle que le bruit d'échantillonnage doit
    dominer. Utiliser la dispersion des épisodes d'un même cerveau mesurerait autre
    chose : la variabilité intra-cerveau, qui n'est pas le signal recherché.

    Au moins 2 cerveaux sont exigés : `stdev` d'une seule valeur n'existe pas, et rendre
    0,0 ferait croire à une dispersion nulle mesurée au lieu d'une dispersion non mesurée.

    ⚠️ DÉ-CONVOLUTION QUAND `variance_echantillonnage_par_cerveau > 0`. La dispersion
    OBSERVÉE `s` majore σ (voir `variance_echantillonnage`) : on publie donc les deux,

        σ̂² = max(0, s² − v)          σ̂ = sqrt(σ̂²)

    et l'IC de σ̂ s'obtient en appliquant à `τ² = σ² + v` l'IC du chi-deux déjà utilisé
    pour `s`, puis en retranchant `v` (transformation monotone, même hypothèse de
    normalité). Quand `τ²_bas <= v`, l'IC de σ̂ **touche 0** : la dispersion réelle n'est
    alors PAS distinguable du bruit d'échantillonnage, et aucun `n` fini ne peut dominer
    une dispersion qui pourrait être nulle. C'est un résultat, publié comme tel.

    `sd_inter` reste la valeur OBSERVÉE (celle des carnets antérieurs) : la sortie porte
    les deux, jamais l'une à la place de l'autre.
    """
    taux = [float(t) for t in taux_par_cerveau]
    if len(taux) < 2:
        raise ValueError(
            f"{len(taux)} valeur(s) : une dispersion inter-cerveaux exige au moins 2 "
            f"cerveaux (une dispersion non mesurée n'est pas une dispersion nulle)")
    v = float(variance_echantillonnage_par_cerveau)
    if v < 0.0:
        raise ValueError(f"variance d'échantillonnage négative ({v!r})")
    sd = statistics.stdev(taux)  # ddof = 1 : échantillon, pas population
    bas, haut = intervalle_confiance_sd(sd, len(taux), alpha)
    sortie = {
        "n_cerveaux": len(taux),
        "taux_par_cerveau": taux,
        "taux_moyen_cerveaux": statistics.fmean(taux),
        "sd_inter": sd,
        "sd_inter_ddof": 1,
        "ic_sd": [bas, haut],
        "ic_sd_alpha": alpha,
        "variance_echantillonnage_par_cerveau": v,
        "variance_observee": sd * sd,
        "part_variance_echantillonnage": (v / (sd * sd)) if sd > 0.0 else None,
    }
    if v > 0.0:
        variance_deconvoluee = max(0.0, sd * sd - v)
        sigma = math.sqrt(variance_deconvoluee)
        # IC de τ² par le chi-deux, puis décalage de v et plancher à 0 : σ̂² ne peut pas
        # être négatif, et « pourrait être 0 » est une information, pas une erreur.
        df = len(taux) - 1
        tau2_bas = df * sd * sd / _quantile_chi2(1.0 - alpha / 2.0, df)
        tau2_haut = df * sd * sd / _quantile_chi2(alpha / 2.0, df)
        sortie.update({
            "sd_inter_deconvoluee": sigma,
            "variance_deconvoluee": variance_deconvoluee,
            "ic_sd_deconvoluee": [math.sqrt(max(0.0, tau2_bas - v)),
                                  math.sqrt(max(0.0, tau2_haut - v))],
            "ic_sd_deconvoluee_touche_zero": bool(tau2_bas <= v),
            "formule_deconvolution": "sigma^2 = max(0, s^2 - v) ; IC(sigma) = "
                                     "sqrt(max(0, IC(tau^2) - v)), tau^2 = sigma^2 + v",
        })
    return sortie


# --- 2. LA DÉRIVATION DEPUIS UN RAPPORT DE BANC (rejouable sans remesurer) --------


def deriver_depuis_rapport(rapport: dict, facteur: float = FACTEUR_DOMINATION,
                           alpha: float = ALPHA_IC_SD) -> dict:
    """Dérive `p_barre`, `sd_inter`, l'IC de la SD et `n` depuis un rapport du banc.

    Séparée de la mesure, cette fonction rend la dérivation **rejouable sans remesurer** :
    `--depuis-rapport <banc_final_*.json>` reproduit `pilote.json` à partir des chiffres
    bruts publiés. C'est ce qui rend la ligne de calcul AUDITABLE.

    `p_barre` est le taux POOLÉ (Σ gagnés / Σ épisodes) sur tous les cerveaux et les deux
    cartes — la définition de la spec §8bis (« taux de franchissement poolé du pilote »).
    La dispersion, elle, est celle des taux PAR CERVEAU : c'est une grandeur différente,
    et les confondre dimensionnerait l'instrument avec son propre bruit d'échantillonnage.

    Les dispersions PAR CARTE sont publiées à côté (`par_carte`) : elles montrent si la
    dispersion mesurée est portée par une carte ou par les deux — sans elles, un `n`
    unique reposerait sur un agrégat dont on ne saurait rien.

    Une dispersion nulle ou un taux saturé n'est PAS masqué : `deriver_n` refuse, et
    `n_derive_poole` (ainsi que chaque `par_carte[*].n_derive`) vaut `None` avec son motif
    écrit. Publier un `n` de secours serait exactement le chiffre inventé que la tâche
    interdit.

    ⚠️ LE `n` QUI FAIT FOI EST DÉRIVÉ PAR CARTE, JAMAIS POOLÉ. La corrélation inter-cartes
    est fortement négative (ρ ≈ −0,88) : le taux poolé est presque indépendant du cerveau,
    donc sa dispersion n'est pas identifiable. Chaque carte porte son propre `n` dérivé de
    sa dispersion **dé-convoluée** σ̂ (`σ̂² = max(0, s² − v)`), et le gel est
    `n_final = max(n PAR CARTE)` — la carte qui contraint est celle de plus petit σ̂ (la
    variance est au dénominateur). Le `n` POOLÉ (`n_derive_poole`, dérivé de σ̂, et
    `n_derive_poole_sd_observee`, dérivé de `s` — borne basse, c'est le `333` du premier
    pilote) est publié POUR MÉMOIRE, jamais comme gel.
    """
    cerveaux = rapport.get("cerveaux") or {}
    if len(cerveaux) < 2:
        raise PiloteMalDimensionne(
            f"le rapport ne porte que {len(cerveaux)} cerveau(x) : aucune dispersion "
            f"inter-cerveaux n'est mesurable, donc aucun `n` n'est dérivable")

    par_cerveau: dict[str, dict] = {}
    for cle, bloc in sorted(cerveaux.items()):
        cartes = bloc.get("cartes") or {}
        k = sum(int(resultat["gagnes"]) for resultat in cartes.values())
        n = sum(int(resultat["taux"]["n"]) for resultat in cartes.values())
        par_cerveau[cle] = {
            "k": k,
            "n": n,
            "taux": (k / n) if n else 0.0,
            "taux_par_carte": {nom: resultat["taux"]["taux"]
                               for nom, resultat in sorted(cartes.items())},
        }

    k_total = sum(v["k"] for v in par_cerveau.values())
    n_total = sum(v["n"] for v in par_cerveau.values())
    p_barre = (k_total / n_total) if n_total else 0.0

    # --- `v` : la variance d'échantillonnage que la dispersion observée contient -------
    # Calculée sur les taux et effectifs PAR CARTE (les deux cartes n'ont pas le même
    # taux : un seul binôme sur 400 épisodes serait faux), et supposée la même pour tous
    # les cerveaux — hypothèse écrite ici et dans le carnet.
    noms_cartes = sorted({nom for bloc in cerveaux.values()
                          for nom in (bloc.get("cartes") or {})})
    taux_par_carte_pooles, effectifs_par_carte = [], []
    for nom in noms_cartes:
        resultats = [bloc["cartes"][nom] for bloc in cerveaux.values()
                     if nom in (bloc.get("cartes") or {})]
        k_carte = sum(int(r["gagnes"]) for r in resultats)
        n_carte = sum(int(r["taux"]["n"]) for r in resultats)
        taux_par_carte_pooles.append((k_carte / n_carte) if n_carte else 0.0)
        effectifs_par_carte.append(n_carte // max(1, len(resultats)))
    v = variance_echantillonnage(taux_par_carte_pooles, effectifs_par_carte)

    dispersion = dispersion_inter_cerveaux([val["taux"] for val in par_cerveau.values()],
                                           alpha, v)
    sd_inter = dispersion["sd_inter"]
    sd_deconvoluee = dispersion.get("sd_inter_deconvoluee")

    # Sensibilité par carte : la dispersion est-elle portée par une carte ou par les deux ?
    # (même dé-convolution, avec le `v` de la carte seule : p(1-p)/n)
    par_carte: dict[str, dict] = {}
    for nom, taux_poolé, effectif in zip(noms_cartes, taux_par_carte_pooles,
                                         effectifs_par_carte):
        taux = [bloc["cartes"][nom]["taux"]["taux"] for bloc in cerveaux.values()
                if nom in (bloc.get("cartes") or {})]
        v_carte = variance_echantillonnage([taux_poolé], [effectif])
        carte_disp = dispersion_inter_cerveaux(taux, alpha, v_carte)
        k_carte = sum(int(bloc["cartes"][nom]["gagnes"]) for bloc in cerveaux.values()
                      if nom in (bloc.get("cartes") or {}))
        n_carte = sum(int(bloc["cartes"][nom]["taux"]["n"]) for bloc in cerveaux.values()
                      if nom in (bloc.get("cartes") or {}))
        p_carte = (k_carte / n_carte) if n_carte else 0.0
        sigma_carte = carte_disp.get("sd_inter_deconvoluee")
        n_carte_derive, motif_carte = None, None
        if sigma_carte is None:
            motif_carte = ("dispersion dé-convoluée indisponible sur cette carte "
                           "(variance d'échantillonnage nulle ou absente)")
        else:
            try:
                n_carte_derive = deriver_n(p_carte, sigma_carte, facteur)
            except ValueError as erreur:
                motif_carte = str(erreur)
        par_carte[nom] = {
            "taux_poolé": p_carte,
            "k": k_carte,
            "n": n_carte,
            **{cle: val for cle, val in carte_disp.items() if cle != "taux_par_cerveau"},
            "n_derive": n_carte_derive,
            "n_derive_motif": motif_carte,
            "ligne_de_calcul": _ligne_de_calcul(p_carte, sigma_carte, facteur,
                                                n_carte_derive),
        }

    # `n_final` : le maximum des `n` PAR CARTE — la carte qui contraint est celle de plus
    # petit σ̂ (la variance est au dénominateur de la règle). C'est CETTE valeur que le
    # protocole gèle. Le `n` POOLÉ publié plus bas (n_derive_poole) est la grandeur que le
    # §1 du protocole interdit pour dimensionner (ρ inter-cartes ≈ −0,88).
    n_par_carte_valides = [c["n_derive"] for c in par_carte.values()
                           if c.get("n_derive") is not None]
    n_final = max(n_par_carte_valides) if n_par_carte_valides else None

    # Le `n` POOLÉ vient de σ̂ ; celui de `s` est publié comme BORNE BASSE. ⚠️ AUCUN des
    # deux n'est le gel : ce sont des grandeurs POOLÉES, interdites pour dimensionner.
    n_derive, motif = None, None
    try:
        n_derive = deriver_n(p_barre, sd_deconvoluee, facteur)
    except ValueError as erreur:
        motif = str(erreur)
    n_borne_basse, motif_borne_basse = None, None
    try:
        n_borne_basse = deriver_n(p_barre, sd_inter, facteur)
    except ValueError as erreur:
        motif_borne_basse = str(erreur)

    resultat = {
        "regle": ("plus petit n >= 1 tel que sqrt(p_barre (1 - p_barre) / n) "
                  "<= sigma / facteur, sigma = dispersion inter-cerveaux DECONVOLUEE"),
        "n_derive_poole_regle": "sd_inter_deconvoluee",
        "facteur": float(facteur),
        "episodes_par_carte_budget_pilote": rapport.get("episodes_par_carte"),
        "tolerance_relative_contrainte": TOLERANCE_RELATIVE_CONTRAINTE,
        "cartes": rapport.get("cartes"),
        "graine_eval_base": rapport.get("graine_eval_base"),
        "graines_entrainement": rapport.get("graines_entrainement"),
        "bras": rapport.get("bras"),
        "campagne": rapport.get("campagne"),
        "p_barre": p_barre,
        "p_barre_definition": ("taux poolé : somme des gagnés / somme des épisodes, sur "
                               "tous les cerveaux et toutes les cartes"),
        "k_total": k_total,
        "episodes_total": n_total,
        "n_cerveaux": dispersion["n_cerveaux"],
        "taux_moyen_cerveaux": dispersion["taux_moyen_cerveaux"],
        "taux_moyen_cerveaux_definition": ("moyenne NON pondérée des taux par cerveau "
                                           "(égale au poolé si les effectifs sont égaux)"),
        "sd_inter": sd_inter,
        "sd_inter_definition": ("écart-type inter-cerveaux des taux par cerveau, OBSERVÉ "
                                "(contient la variance d'échantillonnage du pilote)"),
        "sd_inter_ddof": 1,
        "ic_sd": list(dispersion["ic_sd"]),
        "ic_sd_alpha": alpha,
        "ic_sd_methode": ("loi du chi-deux sur la variance, df = n_cerveaux - 1 : "
                          "IC(sigma) = sqrt(df * s^2 / chi2)"),
        "variance_echantillonnage_par_cerveau": v,
        "variance_echantillonnage_formule": ("v = somme_cartes(n_c * p_c * (1 - p_c)) / N^2, "
                                             "N = nombre total d'episodes par cerveau"),
        "part_variance_echantillonnage": dispersion["part_variance_echantillonnage"],
        "sd_inter_deconvoluee": sd_deconvoluee,
        "sd_inter_deconvoluee_definition": ("estimateur non biaise de la dispersion REELLE "
                                            "entre cerveaux : sigma^2 = s^2 - v"),
        "variance_deconvoluee": dispersion.get("variance_deconvoluee"),
        "ic_sd_deconvoluee": dispersion.get("ic_sd_deconvoluee"),
        "ic_sd_deconvoluee_touche_zero": dispersion.get("ic_sd_deconvoluee_touche_zero"),
        "formule_deconvolution": dispersion.get("formule_deconvolution"),
        "seuil_domination": ((sd_deconvoluee / float(facteur))
                             if sd_deconvoluee is not None else None),
        "seuil_domination_sd_observee": sd_inter / float(facteur),
        "n_derive_poole": n_derive,
        "n_derive_poole_motif": motif,
        "n_derive_poole_sd_observee": n_borne_basse,
        "n_derive_poole_sd_observee_motif": motif_borne_basse,
        "ligne_de_calcul_poole": _ligne_de_calcul(p_barre, sd_deconvoluee, facteur, n_derive),
        "ligne_de_calcul_poole_sd_observee": _ligne_de_calcul(p_barre, sd_inter, facteur,
                                                              n_borne_basse),
        "n_final": n_final,
        "n_final_regle": ("maximum des n derives PAR CARTE (par_carte[*].n_derive) — la "
                          "carte qui contraint est celle de plus petit sigma-chapeau ; "
                          "jamais le n poole"),
        "protocole_gel": "docs/fonctionnement/PROTOCOLE_BANC_FINAL.md",
        "cerveaux": par_cerveau,
        "par_carte": par_carte,
    }
    return resultat


def _ligne_de_calcul(p_barre: float, sd_inter: float, facteur: float,
                     n_derive: int | None) -> str:
    """La ligne de calcul VISIBLE : un `n` dérivé qui ne montre pas son calcul n'est pas
    vérifiable, et un chiffre non vérifiable n'est pas une mesure."""
    cible = sd_inter / facteur
    variance = p_barre * (1.0 - p_barre)
    if n_derive is None:
        return (f"INDÉFINI : p_barre = {p_barre:.6f}, sd_inter = {sd_inter:.6f} — "
                f"la règle n'a pas de solution (voir n_derive_motif)")
    quotient = variance / (cible * cible) if cible > 0.0 else float("inf")
    return (f"n = plus petit entier >= {quotient:.6f} tel que "
            f"sqrt({p_barre:.6f} × (1 − {p_barre:.6f}) / n) <= {sd_inter:.6f} / {facteur} "
            f"= {cible:.6f}  ⇒  n = {n_derive}")


# --- 3. LA MESURE : LE PILOTE RÉEL ------------------------------------------------


def mesurer_pilote(cohorte: str, bras: Sequence[str], cartes: Sequence[int],
                   graines_pilote: Sequence[int], episodes: int, graine_eval_base: int,
                   dossier_sortie: str, cohorte_explicite: str | None = None,
                   max_ticks: int = 0, facteur: float = FACTEUR_DOMINATION,
                   alpha: float = ALPHA_IC_SD) -> dict:
    """Évalue 2 à 4 cerveaux × `episodes` sur les cartes figées, puis dérive `n`.

    La mesure passe par `banc_final.executer_banc` : reproductibilité (trois générateurs
    seedés par épisode), état FRAIS par (bras, carte), carte re-forcée à chaque épisode et
    rapport JSON sont ceux de l'instrument déjà vérifié — le pilote n'en réimplémente rien.

    `cohorte_explicite` suit la voie JSON `{bras: {graine: chemin}}` de `banc_final`.
    ⚠️ CORRECTION MESURÉE : elle n'était **PAS obligatoire** pour les 4 graines de ce
    pilote — `lister_cerveaux('K8_NU', [11, 22, 33, 44])` rend les 4 sans lever (le
    surnuméraire est `K8_NU_g122`, une graine non demandée), et `resoudre_cohorte` non
    plus. Le glob ne refuse `K8_NU` que si l'on demande les **20 graines du manifeste**
    (mesuré : `NomAmbigue`). La voie explicite est ici un CHOIX — elle énumère les
    cerveaux un par un, donc elle reste préférable dès qu'un bras est ambigu — jamais une
    obligation pour ces quatre graines. Elle **deviendra** obligatoire pour les 20.

    Écrit dans `dossier_sortie` : le rapport du banc (par `executer_banc`) et `pilote.json`
    (ici). Ne modifie aucun `.brain` : le banc ouvre en lecture seule et ne sauvegarde
    jamais.

    ⚠️ Sur une cohorte en VIOLATION, rien n'est dérivé : `PiloteNonDerive` est levée plutôt
    que de publier un `n` calculé sur une couverture incomplète (MES-01).
    """
    # Import LOCAL : `banc_final` tire `noyau` et `torch`. La règle (`deriver_n`) et l'IC
    # de la SD doivent rester testables — et contestables — sans charger un cerveau.
    from naulthene.instruments.banc_final import (
        exiger_episodes,
        executer_banc,
        lire_cohorte_explicite,
        refuser_bras_vides,
        resoudre_cohorte,
        verifier_graine_eval_base,
    )

    episodes = exiger_episodes(episodes)
    verifier_graine_eval_base(graine_eval_base)
    graines_pilote = [int(g) for g in graines_pilote]
    if cohorte_explicite:
        cohorte_resolue = lire_cohorte_explicite(cohorte_explicite)
    else:
        cohorte_resolue = resoudre_cohorte(cohorte, bras, graines_pilote)
    # La voie explicite ne passe pas par `resoudre_cohorte` : le refus des bras vides est
    # donc rappelé ici, comme dans `banc_final.main()`.
    cohorte_resolue = refuser_bras_vides(cohorte_resolue)

    nb_cerveaux = sum(len(cerveaux) for cerveaux in cohorte_resolue.values())
    if not NB_CERVEAUX_PILOTE_MIN <= nb_cerveaux <= NB_CERVEAUX_PILOTE_MAX:
        raise PiloteMalDimensionne(
            f"{nb_cerveaux} cerveau(x) résolu(s) pour {list(bras)} : le pilote en exige "
            f"{NB_CERVEAUX_PILOTE_MIN} à {NB_CERVEAUX_PILOTE_MAX} (spec §8bis). Avec un "
            f"seul cerveau la dispersion inter-cerveaux n'existe pas ; au-delà de 4, on "
            f"quitte le budget de mesure du pilote.")

    print(f"🧭 PILOTE EVA-01 — {nb_cerveaux} cerveaux × {len(list(cartes))} cartes figées "
          f"× {episodes} épisodes (BUDGET DE MESURE, pas le `n` du protocole)")
    print(f"   cohorte   : {cohorte}"
          + (f" (explicite : {cohorte_explicite})" if cohorte_explicite else ""))
    print(f"   graines d'évaluation : {graine_eval_base}…"
          f"{graine_eval_base + episodes - 1} (pool dédié, disjoint de l'entraînement)")

    rapport = executer_banc(
        cohorte=cohorte, bras=list(bras), cartes=list(cartes), graines=graines_pilote,
        episodes=episodes, graine_eval_base=graine_eval_base, dossier_sortie=dossier_sortie,
        max_ticks=max_ticks, cohorte_resolue=cohorte_resolue)
    if rapport.get("violations"):
        raise PiloteNonDerive(
            f"{len(rapport['violations'])} violation(s) de couverture : aucun `n` n'est "
            f"dérivé d'une campagne incomplète (MES-01). Voir le rapport ci-dessus.")

    resultat = deriver_depuis_rapport(rapport, facteur=facteur, alpha=alpha)
    resultat["date_mesure"] = datetime.now(timezone.utc).isoformat()
    resultat["protocole"] = "PILOTE_EVA-01 v1"
    resultat["cohorte_explicite"] = cohorte_explicite
    # Le rapport du banc est nommé, pas recopié : c'est lui qui porte les chiffres par
    # épisode (monde, trajectoire, budget), donc la pièce brute que `pilote.json` résume.
    fichiers = sorted(glob.glob(os.path.join(dossier_sortie, "banc_final_*.json")))
    resultat["rapport_banc"] = fichiers[-1] if fichiers else None

    os.makedirs(dossier_sortie, exist_ok=True)
    chemin = os.path.join(dossier_sortie, "pilote.json")
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(resultat, f, ensure_ascii=False, indent=2)

    _afficher_derivation(resultat)
    print(f"\n💾 {chemin} écrit (aucun .brain n'a été modifié).")
    return resultat


def _afficher_derivation(resultat: dict) -> None:
    """Le verdict du pilote, à l'écran, avec l'incertitude À CÔTÉ de la valeur.

    ⚠️ LES DEUX DISPERSIONS SONT AFFICHÉES ET L'ÉCART EST NOMMÉ. `s` (observée) majore σ :
    n'afficher que `s` donnerait un `n` trop PETIT ; n'afficher que σ̂ cacherait d'où vient
    la correction. La ligne de calcul publiée est celle de σ̂, parce que c'est elle qui fait
    foi ; celle de `s` est affichée comme borne basse.
    """
    print("\n=== DÉRIVATION DE n (règle de domination du bruit, spec §8bis) ===")
    print(f"  p̄ poolé                     : {resultat['p_barre']:.6f} "
          f"({resultat['k_total']}/{resultat['episodes_total']})")
    v = resultat.get("variance_echantillonnage_par_cerveau")
    print(f"  SD inter-cerveaux OBSERVÉE   : {resultat['sd_inter']:.6f}   "
          f"(IC{int((1 - resultat['ic_sd_alpha']) * 100)} "
          f"[{resultat['ic_sd'][0]:.6f} ; {resultat['ic_sd'][1]:.6f}])")
    if v:
        part = resultat.get("part_variance_echantillonnage")
        print(f"  dont bruit d'échantillonnage : {v:.8f} de variance"
              + (f" — {100 * part:.1f} % de la variance observée" if part is not None else ""))
    if resultat.get("sd_inter_deconvoluee") is not None:
        ic = resultat.get("ic_sd_deconvoluee") or [float("nan"), float("nan")]
        touche = ", touche 0" if resultat.get("ic_sd_deconvoluee_touche_zero") else ""
        print(f"  SD inter-cerveaux RÉELLE σ̂   : {resultat['sd_inter_deconvoluee']:.6f}   "
              f"(IC{int((1 - resultat['ic_sd_alpha']) * 100)} "
              f"[{ic[0]:.6f} ; {ic[1]:.6f}]{touche})")
    print(f"  seuil de domination (σ̂/{resultat['facteur']:.4g}) : "
          f"{resultat['seuil_domination']}")
    print(f"  ⚠️ n POOLÉ (jamais gelé)     : {resultat['ligne_de_calcul_poole']}")
    if resultat.get("n_derive_poole_sd_observee") is not None:
        print(f"  ⚠️ borne basse POOLÉE (SD OBSERVÉE, gonflée) : "
              f"n = {resultat['n_derive_poole_sd_observee']}")
    if resultat["n_derive_poole"] is None:
        print(f"\n⛔ AUCUN `n` POOLÉ — {resultat['n_derive_poole_motif']}")

    print("\n=== n_final = max(n PAR CARTE) — c'est CE QUI EST GELÉ ===")
    for nom, carte in resultat.get("par_carte", {}).items():
        sigma = carte.get("sd_inter_deconvoluee")
        sigma_txt = f"{sigma:.6f}" if sigma is not None else "indisponible"
        print(f"  {nom:32s} σ̂ = {sigma_txt:12s} {carte.get('ligne_de_calcul', '')}")
    print(f"  n_final = {resultat['n_final']}   ({resultat['n_final_regle']})")
    if resultat["n_final"] is None:
        print(f"\n⛔ AUCUN `n_final` DÉRIVÉ — aucune carte n'a de dispersion identifiable "
              f"(le pilote publie la mesure ; il n'invente pas de `n` de secours)")


# --- 4. POINT D'ENTRÉE ------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pilote EVA-01 — mesure la dispersion inter-cerveaux du taux de "
                    "franchissement sur cartes figées, puis en DÉRIVE `n` (spec §8bis)")
    parser.add_argument("--cohorte", type=str, default=None,
                        help="Dossier de campagne (contient manifeste.json et un dossier "
                             "par bras)")
    parser.add_argument("--bras", type=str, nargs="+", default=None)
    parser.add_argument("--cartes", type=int, nargs="+", default=list(CARTES_PILOTE),
                        help=f"Indices PROGRAMME (défaut gelé : {list(CARTES_PILOTE)})")
    parser.add_argument("--graines-pilote", type=int, nargs="+", default=None,
                        help="Graines d'ENTRAÎNEMENT identifiant les cerveaux du pilote "
                             "(2 à 4). En voie explicite, ce sont les clés du JSON.")
    parser.add_argument("--episodes", type=int, default=EPISODES_PILOTE,
                        help=f"BUDGET DE MESURE du pilote (défaut {EPISODES_PILOTE}) — ce "
                             f"n'est PAS le `n` du protocole, qui est DÉRIVÉ de ce run")
    parser.add_argument("--graine-eval-base", type=int, default=10000,
                        help="Première graine d'évaluation (défaut gelé : 10000)")
    parser.add_argument("--cohorte-explicite", type=str, default=None,
                        help="JSON {bras: {graine: chemin}} — voie OBLIGATOIRE si un bras "
                             "porte des surnuméraires (le glob refuse alors le bras entier)")
    parser.add_argument("--dossier-sortie", type=str, required=True,
                        help="Dossier de campagne où écrire pilote.json ET le rapport du banc")
    parser.add_argument("--max-ticks", type=int, default=0,
                        help="0 = budget natif du monde (jamais un plafond posé)")
    parser.add_argument("--facteur", type=float, default=FACTEUR_DOMINATION,
                        help=f"Le seul paramètre POSÉ de la règle (défaut {FACTEUR_DOMINATION})")
    parser.add_argument("--depuis-rapport", type=str, default=None,
                        help="Reproduit la dérivation depuis un banc_final_*.json déjà "
                             "mesuré, sans relancer aucune évaluation")
    args = parser.parse_args(argv)

    if args.depuis_rapport:
        with open(args.depuis_rapport, "r", encoding="utf-8") as f:
            rapport = json.load(f)
        resultat = deriver_depuis_rapport(rapport, facteur=args.facteur)
        resultat["date_mesure"] = datetime.now(timezone.utc).isoformat()
        resultat["protocole"] = "PILOTE_EVA-01 v1"
        resultat["rapport_banc"] = args.depuis_rapport
        os.makedirs(args.dossier_sortie, exist_ok=True)
        chemin = os.path.join(args.dossier_sortie, "pilote.json")
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(resultat, f, ensure_ascii=False, indent=2)
        print(f"♻️  Dérivation REPRODUITE depuis {args.depuis_rapport} (aucune mesure "
              f"relancée).")
        _afficher_derivation(resultat)
        print(f"\n💾 {chemin} écrit.")
        return 0 if resultat["n_final"] is not None else 1

    if not args.cohorte or not args.bras or not args.graines_pilote:
        parser.error("--cohorte, --bras et --graines-pilote sont requis (ou utilise "
                     "--depuis-rapport)")
    resultat = mesurer_pilote(
        cohorte=args.cohorte, bras=args.bras, cartes=args.cartes,
        graines_pilote=args.graines_pilote, episodes=args.episodes,
        graine_eval_base=args.graine_eval_base, dossier_sortie=args.dossier_sortie,
        cohorte_explicite=args.cohorte_explicite, max_ticks=args.max_ticks,
        facteur=args.facteur)
    return 0 if resultat["n_final"] is not None else 1


if __name__ == "__main__":
    sys.exit(main())
