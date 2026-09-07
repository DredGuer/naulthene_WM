#!/usr/bin/env python3
"""Dépouillement strict — primitive partagée par toutes les campagnes (registre MES-01).

Pourquoi ce module existe
-------------------------
Six scripts `depouiller*.py` ont été écrits par copier-coller successifs. Tous
partageaient le même défaut : une graine absente, un run inachevé ou un garde-fou
échoué **n'empêchaient pas** la publication d'un `agregat.json`, et le motif
`for g in GRAINES if f'{bras}_g{g}' in E` faisait disparaître les exclusions **en
silence**. C'est la panne d'`INSTRUMENT_01092026_la_memoire_du_banc.md` à
l'identique : *un garde-fou de forme doit CRIER quand il rejette*.

Ce module est la seule implémentation autorisée de ces garde-fous. Les scripts de
campagne ne gardent que ce qui leur est propre : la lecture de leurs logs et le
choix de leurs juges.

Deux modes, jamais mélangés
---------------------------
- **confirmatoire** : couverture exacte exigée (toutes les graines de toutes les
  branches, tous les runs terminés), garde-fous bloquants. À la moindre violation :
  aucun agrégat écrit et code de sortie non nul.
- **exploratoire** : tout est calculable, mais chaque verdict est estampillé
  `EXPLORATOIRE`, aucun seuil de significativité n'est prononcé, et le fichier
  produit ne peut jamais s'appeler `agregat.json`.

Le seuil de significativité est **dérivé** de `n` et de la famille de tests
(Bonferroni sur `comparaisons_prevues`), jamais posé en dur. Le fameux `2.86` des
scripts précédents valait `t(df = 19, α = 0,01 bilatéral)` : correct pour `n = 20`,
faux dès qu'une observation manque ou qu'on retire les extrêmes.
"""
from __future__ import annotations

import json
import math
import os
import statistics as st
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

__all__ = [
    "CampagneInvalide",
    "Depouillement",
    "Manifeste",
    "Resultat",
    "seuil_t",
]

MODE_CONFIRMATOIRE = "confirmatoire"
MODE_EXPLORATOIRE = "exploratoire"


class CampagneInvalide(RuntimeError):
    """Levée dès qu'un calcul confirmatoire est tenté sur une campagne invalide."""


# --- 1. LE SEUIL, DÉRIVÉ ET NON POSÉ ---------------------------------------


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    """Fraction continue de Lentz pour la bêta incomplète (Numerical Recipes §6.4)."""
    minuscule = 1e-300
    c = 1.0
    d = 1.0 - (a + b) * x / (a + 1.0)
    if abs(d) < minuscule:
        d = minuscule
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((a + m2 - 1.0) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < minuscule:
            d = minuscule
        c = 1.0 + aa / c
        if abs(c) < minuscule:
            c = minuscule
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (a + b + m) * x / ((a + m2) * (a + m2 + 1.0))
        d = 1.0 + aa * d
        if abs(d) < minuscule:
            d = minuscule
        c = 1.0 + aa / c
        if abs(c) < minuscule:
            c = minuscule
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-16:
            break
    return h


def _beta_incomplete_regularisee(a: float, b: float, x: float) -> float:
    """`I_x(a, b)`, en pur `math` — aucune dépendance à scipy au runtime."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    facteur = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return facteur * _beta_continued_fraction(a, b, x) / a
    return 1.0 - facteur * _beta_continued_fraction(b, a, 1.0 - x) / b


def seuil_t(n: int, comparaisons: int = 1, alpha: float = 0.05) -> float:
    """Seuil bilatéral de Student pour `n` observations appariées.

    `comparaisons` est la taille de la famille de tests pré-enregistrée : la
    correction de Bonferroni s'y applique (`alpha / comparaisons`). Le résultat est
    recalculé à chaque changement de `n` — c'est tout l'objet de MES-01.
    """
    if n < 2:
        raise ValueError(f"seuil_t exige n >= 2 (reçu {n})")
    if comparaisons < 1:
        raise ValueError(f"famille de tests vide (reçu {comparaisons})")
    df = float(n - 1)
    a = alpha / comparaisons  # probabilité bilatérale corrigée
    # P(|T| > t) = I_{df/(df+t²)}(df/2, 1/2) = a  →  t = sqrt(df * (1/x - 1))
    bas, haut = 1e-15, 1.0
    for _ in range(200):
        milieu = 0.5 * (bas + haut)
        if _beta_incomplete_regularisee(df / 2.0, 0.5, milieu) < a:
            bas = milieu
        else:
            haut = milieu
    x = 0.5 * (bas + haut)
    return math.sqrt(df * (1.0 / x - 1.0))


# --- 2. LE MANIFESTE : LE PROTOCOLE ÉCRIT AVANT LE DÉPOUILLEMENT ------------


@dataclass
class Manifeste:
    """Contrat d'une campagne, écrit AVANT le premier run (règle de Trace)."""

    campagne: str
    graines: list[int] = field(default_factory=list)
    bras: dict[str, dict[str, str]] = field(default_factory=dict)
    runs: list[dict[str, str]] = field(default_factory=list)
    jours_requis: int = 0
    mode: str = MODE_CONFIRMATOIRE
    alpha: float = 0.05
    comparaisons_prevues: int = 1
    gardes: list[dict[str, Any]] = field(default_factory=list)
    exclusions_autorisees: list[dict[str, str]] = field(default_factory=list)
    extension_log: str = ".log"

    def __post_init__(self):
        if self.mode not in (MODE_CONFIRMATOIRE, MODE_EXPLORATOIRE):
            raise ValueError(f"mode inconnu : {self.mode!r}")
        if self.runs:
            if self.bras or self.graines:
                raise ValueError(
                    "manifeste ambigu : déclarer SOIT `runs`, SOIT `bras` × `graines`")
        elif not (self.bras and self.graines):
            raise ValueError("manifeste sans cohorte : ni `runs`, ni `bras` × `graines`")

    @property
    def confirmatoire(self) -> bool:
        return self.mode == MODE_CONFIRMATOIRE

    @property
    def cohorte(self) -> list[tuple[str, str]]:
        """Liste ordonnée `(nom du run, chemin relatif)` — la cohorte attendue.

        Une campagne se déclare soit comme une liste explicite de runs, soit comme
        un produit `bras × graines`. Dans les deux cas, `collecter` parcourt cette
        liste **entière** : c'est ce qui interdit l'exclusion silencieuse.
        """
        if self.runs:
            return [(r["nom"], r["fichier"]) for r in self.runs]
        return [
            (f"{bras}_g{graine}",
             os.path.join(spec["dossier"],
                          f"{spec['prefixe']}_g{graine}{self.extension_log}"))
            for bras, spec in self.bras.items()
            for graine in self.graines
        ]

    @property
    def runs_attendus(self) -> int:
        return len(self.cohorte)

    @classmethod
    def depuis_dict(cls, brut: dict[str, Any]) -> "Manifeste":
        connus = {f for f in cls.__dataclass_fields__}
        inconnus = set(brut) - connus - {"commentaire", "date", "source"}
        if inconnus:
            raise ValueError(f"clés inconnues dans le manifeste : {sorted(inconnus)}")
        return cls(**{k: v for k, v in brut.items() if k in connus})

    @classmethod
    def depuis_fichier(cls, chemin: str) -> "Manifeste":
        with open(chemin, encoding="utf-8") as fh:
            return cls.depuis_dict(json.load(fh))


# --- 3. LE RÉSULTAT D'UN TEST APPARIÉ ---------------------------------------


@dataclass
class Resultat:
    label: str
    delta: float
    t: float
    n: int
    favorables: int
    seuil: float
    confirmatoire: bool
    reduit: "Resultat | None" = None

    @property
    def significatif(self) -> bool:
        return self.confirmatoire and abs(self.t) > self.seuil

    def ligne(self) -> str:
        if not self.confirmatoire:
            return (f"  {self.label:32} d = {self.delta:+8.3f}  t = {self.t:+6.2f}  "
                    f"[EXPLORATOIRE — aucun verdict]  ({self.favorables}/{self.n})")
        verdict = "SIG" if self.significatif else "NS "
        return (f"  {self.label:32} d = {self.delta:+8.3f}  t = {self.t:+6.2f}  "
                f"{verdict} (seuil {self.seuil:.2f}, n={self.n})  "
                f"({self.favorables}/{self.n})")


# --- 4. LE DÉPOUILLEMENT -----------------------------------------------------


class Depouillement:
    """Collecte, valide, teste et publie — dans cet ordre, sans raccourci possible."""

    def __init__(self, manifeste: Manifeste, racine: str):
        self.manifeste = manifeste
        self.racine = racine
        self.runs: dict[str, dict[str, Any]] = {}
        self.exclusions: list[dict[str, str]] = []
        self.violations: list[str] = []
        self.resultats_gardes: list[dict[str, Any]] = []
        self._collecte_faite = False

    # -- collecte ------------------------------------------------------------

    def chemin_run(self, relatif: str) -> str:
        return os.path.join(self.racine, relatif)

    def collecter(self, lecteur: Callable[[str], dict[str, Any] | None]) -> None:
        """Parcourt TOUTE la cohorte prévue au manifeste, sans exception.

        `lecteur(chemin)` rend les données du run, ou `None` si la source est
        illisible. Quand le manifeste fixe un `jours_requis`, le lecteur doit
        fournir `jours_final` et un run trop court est écarté — un `t` calculé sur
        un run inachevé choisirait implicitement sa fenêtre (leçon du 20/08/2026).
        Aucune cellule ne peut être sautée : c'est ce qui rend l'exclusion
        silencieuse structurellement impossible.
        """
        for cle, relatif in self.manifeste.cohorte:
            chemin = self.chemin_run(relatif)
            if not os.path.exists(chemin):
                self._exclure(cle, f"fichier absent ({chemin})")
                continue
            donnees = lecteur(chemin)
            if not donnees:
                self._exclure(cle, "source illisible ou vide")
                continue
            if self.manifeste.jours_requis:
                jours = donnees.get("jours_final")
                if jours is None:
                    self._exclure(cle, "jours_final absent du log")
                    continue
                if jours < self.manifeste.jours_requis:
                    self._exclure(
                        cle, f"INACHEVÉ {jours}/{self.manifeste.jours_requis} jours")
                    continue
            self.runs[cle] = donnees
        self._collecte_faite = True

    def _exclure(self, cle: str, motif: str) -> None:
        prevue = next(
            (e for e in self.manifeste.exclusions_autorisees if e.get("run") == cle), None)
        if prevue is not None:
            self.exclusions.append(
                {"run": cle, "motif": motif, "statut": "prévue au manifeste",
                 "justification": prevue.get("motif", "")})
            return
        self.exclusions.append({"run": cle, "motif": motif, "statut": "NON PRÉVUE"})
        self.violations.append(f"couverture : {cle} — {motif}")

    # -- garde-fous ----------------------------------------------------------

    def verifier_gardes(self) -> None:
        """Deux formes de garde-fou, toutes deux BLOQUANTES.

        - cible ± tolérance (« gain_c1 ≡ 1,00 ») ;
        - plancher `minimum` (« le gain reste très au-dessus de 0,25 »), parce
          qu'un régime renormalisé n'a pas de valeur attendue exacte.
        """
        for garde in self.manifeste.gardes:
            variable = garde["variable"]
            minimum = garde.get("minimum")
            cible = None if minimum is not None else float(garde["cible"])
            tolerance = None if minimum is not None else float(garde["tolerance"])
            attendu = (f"> {float(minimum):g}" if minimum is not None
                       else f"{cible:.4f} ± {tolerance:g}")
            for bras in garde.get("bras", list(self.manifeste.bras)):
                valeurs = [self.runs[f"{bras}_g{g}"][variable]
                           for g in self.manifeste.graines
                           if f"{bras}_g{g}" in self.runs]
                if not valeurs:
                    self.violations.append(
                        f"garde-fou « {garde['nom']} » : aucune valeur pour {bras}")
                    continue
                moyenne = st.mean(valeurs)
                passe = (moyenne > float(minimum) if minimum is not None
                         else abs(moyenne - cible) <= tolerance)
                self.resultats_gardes.append(
                    {"garde": garde["nom"], "bras": bras, "variable": variable,
                     "moyenne": moyenne, "attendu": attendu, "passe": passe})
                if not passe:
                    self.violations.append(
                        f"garde-fou « {garde['nom']} » : {bras} {variable} = "
                        f"{moyenne:.4f}, attendu {attendu}")

    # -- validité ------------------------------------------------------------

    def exiger(self, condition: bool, message: str) -> bool:
        """Exigence propre à une campagne (données annexes, cohérence, effectifs).

        Rend `condition` pour rester utilisable en ligne, et enregistre une violation
        si elle est fausse — de sorte qu'une donnée annexe manquante bloque la
        publication au même titre qu'un run absent.
        """
        if not condition:
            self.violations.append(message)
        return condition

    def valide(self) -> bool:
        return not self.violations

    def code_sortie(self) -> int:
        if self.manifeste.confirmatoire and self.violations:
            return 1
        return 0

    def _exiger_validite(self, action: str) -> None:
        if self.manifeste.confirmatoire and self.violations:
            raise CampagneInvalide(
                f"{action} refusé — campagne invalide :\n  - "
                + "\n  - ".join(self.violations))

    # -- tests ---------------------------------------------------------------

    def deltas(self, bras_a: str, bras_b: str, variable: str) -> list[float]:
        self._exiger_validite(f"appariement {bras_a}/{bras_b}")
        return [self.runs[f"{bras_a}_g{g}"][variable] - self.runs[f"{bras_b}_g{g}"][variable]
                for g in self.manifeste.graines
                if f"{bras_a}_g{g}" in self.runs and f"{bras_b}_g{g}" in self.runs]

    def apparie(self, bras_a: str, bras_b: str, variable: str, label: str,
                retirer_extremes: int = 0) -> Resultat:
        return self.resultat_de(self.deltas(bras_a, bras_b, variable), label,
                                retirer_extremes=retirer_extremes)

    def resultat_de(self, deltas: Iterable[float], label: str,
                    retirer_extremes: int = 0) -> Resultat:
        d = list(deltas)
        resultat = self._tester(d, label)
        if retirer_extremes > 0:
            restants = sorted(d, key=abs)[:-retirer_extremes]
            if len(restants) >= 3:
                resultat.reduit = self._tester(
                    restants, f"  -> sans les {retirer_extremes} extrêmes")
        return resultat

    def _tester(self, d: list[float], label: str) -> Resultat:
        n = len(d)
        if n < 2:
            raise CampagneInvalide(f"{label} : n = {n}, aucun test possible")
        moyenne = st.mean(d)
        ecart = st.stdev(d)
        t = 0.0 if ecart == 0 else moyenne / (ecart / math.sqrt(n))
        return Resultat(
            label=label, delta=moyenne, t=t, n=n,
            favorables=sum(1 for x in d if x > 0),
            seuil=seuil_t(n, self.manifeste.comparaisons_prevues, self.manifeste.alpha),
            confirmatoire=self.manifeste.confirmatoire,
        )

    # -- rapport et publication ---------------------------------------------

    def rapport(self) -> str:
        lignes = [
            f"=== CAMPAGNE {self.manifeste.campagne} — mode {self.manifeste.mode.upper()} ===",
            f"couverture : {len(self.runs)}/{self.manifeste.runs_attendus} runs "
            + (f"({len(self.manifeste.bras)} bras × "
               f"{len(self.manifeste.graines)} graines)"
               if self.manifeste.bras else "(cohorte explicite)"),
        ]
        if self.exclusions:
            lignes.append(f"exclusions ({len(self.exclusions)}) :")
            for e in self.exclusions:
                suffixe = f" — {e['justification']}" if e.get("justification") else ""
                lignes.append(f"  ⛔ {e['run']:22} [{e['statut']}] {e['motif']}{suffixe}")
        else:
            lignes.append("exclusions : aucune")
        for g in self.resultats_gardes:
            etat = "OK" if g["passe"] else "!! ÉCHEC"
            lignes.append(
                f"  garde-fou « {g['garde']} » {g['bras']:10} {g['variable']} = "
                f"{g['moyenne']:.4f} (attendu {g['attendu']})  {etat}")
        if self.violations:
            lignes.append(f"🔴 CAMPAGNE INVALIDE — {len(self.violations)} violation(s) :")
            lignes.extend(f"  - {v}" for v in self.violations)
        else:
            lignes.append("✅ tous les garde-fous passent, couverture conforme")
        return "\n".join(lignes)

    def publier(self, chemin: str) -> bool:
        """Écrit l'agrégat — et ne l'écrit PAS si la campagne est invalide."""
        if not self.manifeste.confirmatoire:
            base, ext = os.path.splitext(chemin)
            chemin = f"{base}_exploratoire{ext}"
        elif self.violations:
            return False
        charge = {
            "campagne": self.manifeste.campagne,
            "mode": self.manifeste.mode,
            "couverture": {"obtenus": len(self.runs),
                           "attendus": self.manifeste.runs_attendus},
            "exclusions": self.exclusions,
            "gardes": self.resultats_gardes,
            "runs": self.runs,
        }
        with open(chemin, "w", encoding="utf-8") as fh:
            json.dump(charge, fh, ensure_ascii=False, indent=1)
        return True
