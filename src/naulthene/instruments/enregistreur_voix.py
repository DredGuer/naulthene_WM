# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
L'Enregistreur de Voix (v27.0, expérimental) — constitue la banque vocale de
l'utilisateur pour l'École de la Parole & Synesthésie.

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test"), pas encore porté sur `agi_google_colab.py`.

Enregistre la voix de l'utilisateur nommant les mots du curriculum vocal
(`professeur_gemma.CURRICULUM_VOCAL`) et les range dans `voix/<mot>/<mot>_NN.wav` —
convention lue par `lecons_vocales.CacheReferencesVocales` (repli automatique sur
`say` si aucune prise n'existe pour un mot, donc cet outil est purement optionnel :
tout cursus fonctionne sans lui).

Ne modifie jamais un `.brain` — c'est un outil d'observation/constitution de données,
pas un outil d'entraînement, cohérent avec l'esprit "instruments" du package (voir
__init__.py).

Usage :
    python -m naulthene.instruments.enregistreur_voix
    python -m naulthene.instruments.enregistreur_voix --mots a e i o u --prises 3
    python -m naulthene.instruments.enregistreur_voix --mots porte clé --prises 5 --pas-de-relecture
"""

import argparse
from pathlib import Path

import numpy as np

from naulthene.audio.hemisphere_audio import capture_micro, jouer_son_temps_reel, SAMPLE_RATE
from naulthene.audio.lecons_vocales import _slug_mot, lister_prises, RACINE_BANQUE
import naulthene.audio.professeur_gemma as pg


def chemin_dossier_mot(mot: str, racine: Path = RACINE_BANQUE) -> Path:
    return racine / _slug_mot(mot)


def enregistrer_prise(mot: str, duree: float = 2.0, racine: Path = RACINE_BANQUE) -> Path:
    """Capture `duree` secondes au micro, recadre le silence, et écrit la prise sous
    voix/<mot>/<mot>_NN.wav (NN = index suivant, jamais d'écrasement d'une prise
    existante). Retourne le chemin écrit.

    Le recadrage du silence (librosa.effects.trim) est le point le plus important de
    cet outil : capture_micro(2.0) capture souvent 1,5s de silence avant/après le mot
    prononcé, et extraire_mfcc (n_frames=10, sous-échantillonnage uniforme) capturerait
    alors surtout du vide plutôt que la voyelle/le mot réellement dit — les références
    micro seraient pires que `say`. Repli sur l'onde brute si le trim renvoie moins de
    512 échantillons (cas dégénéré : rien à recadrer, ou coupure trop agressive)."""
    import soundfile as sf
    import librosa

    onde = capture_micro(duree=duree, sample_rate=SAMPLE_RATE)
    recadree, _ = librosa.effects.trim(onde, top_db=30)
    if recadree.size < 512:
        recadree = onde

    dossier = chemin_dossier_mot(mot, racine=racine)
    dossier.mkdir(parents=True, exist_ok=True)
    index = len(lister_prises(mot, racine=racine)) + 1
    chemin = dossier / f"{_slug_mot(mot)}_{index:02d}.wav"
    sf.write(str(chemin), recadree.astype(np.float32), SAMPLE_RATE)
    return chemin


def lancer_session(mots: list = None, prises_par_mot: int = 3, duree: float = 2.0,
                    ecouter: bool = True, racine: Path = RACINE_BANQUE) -> None:
    """Boucle interactive : pour chaque mot, enregistre `prises_par_mot` prises, avec
    relecture immédiate et validation o/n (réenregistrement si refusé) sauf si
    `ecouter=False`. Défaut `mots=None` = toutes les cibles non-None du curriculum
    vocal (les paliers combinatoires "ouvre porte"/"prends clé" inclus)."""
    if mots is None:
        mots = sorted({lecon["cible"] for lecon in pg.CURRICULUM_VOCAL if lecon["cible"]})

    print(f"🎙️  Enregistreur de Voix — {len(mots)} mot(s), {prises_par_mot} prise(s) chacun.")
    print(f"   Banque : {racine.resolve()}\n")

    for mot in mots:
        deja = len(lister_prises(mot, racine=racine))
        print(f"── « {mot} » ({deja} prise(s) déjà enregistrée(s)) " + "─" * 20)
        for i in range(prises_par_mot):
            while True:
                input(f"   [{i + 1}/{prises_par_mot}] Appuie sur Entrée puis dis « {mot} » "
                      f"({duree:.1f}s d'enregistrement)...")
                chemin = enregistrer_prise(mot, duree=duree, racine=racine)
                print(f"   ✅ Enregistré : {chemin}")
                if not ecouter:
                    break
                onde, _ = __import__("soundfile").read(str(chemin), dtype="float32")
                jouer_son_temps_reel(onde, sample_rate=SAMPLE_RATE, bloquant=True)
                reponse = input("   Cette prise est-elle bonne ? [O/n] ").strip().lower()
                if reponse in ("", "o", "oui", "y", "yes"):
                    break
                chemin.unlink(missing_ok=True)
                print("   🔁 Prise rejetée, on recommence.")
        print()

    print("🏁 Session terminée.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enregistreur de Voix — banque vocale de l'utilisateur (Naulthène AGI v27.0)")
    parser.add_argument("--mots", nargs="+", default=None,
                        help="Mots à enregistrer (défaut : tout le curriculum vocal)")
    parser.add_argument("--prises", type=int, default=3, help="Nombre de prises par mot")
    parser.add_argument("--duree", type=float, default=2.0, help="Durée d'enregistrement par prise (secondes)")
    parser.add_argument("--pas-de-relecture", action="store_true",
                        help="Désactive la relecture/validation après chaque prise")
    args = parser.parse_args()

    lancer_session(mots=args.mots, prises_par_mot=args.prises, duree=args.duree,
                   ecouter=not args.pas_de_relecture)
