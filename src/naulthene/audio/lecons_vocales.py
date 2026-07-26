"""
Le Générateur de Leçons Vocales côté Serveur (V23.0, expérimental) — pour le Cursus
Développemental par Ères.

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test"), pas encore porté sur `agi_google_colab.py`. Voir le plan
v23.0 et `readme.md` (section "Le Cursus Développemental par Ères") pour le contexte.

Jusqu'à la v22.1, toute la génération de référence audio (dire un mot via `say`, le
convertir en MFCC) vivait côté CLIENT (`client_professeur.py`), pilotée manuellement
par un humain qui lance une leçon ponctuelle (`--palier N`). Le Cursus Développemental
tourne en STANDALONE, sans client réseau (décision utilisateur, voir le plan v23.0) —
il a donc besoin de sa propre génération de références, appelée directement par la
boucle du cursus (`cursus_developpemental.py`), sans passer par un socket.

Aucune dépendance au réseau de neurones ici — pur signal + orchestration du curriculum,
testable en isolation (comme `hemisphere_audio.py` et `professeur_gemma.py`).
"""

import subprocess
import tempfile
from pathlib import Path

import numpy as np

from naulthene.audio.hemisphere_audio import extraire_mfcc, VOYELLES_CIBLES, SAMPLE_RATE
import naulthene.audio.professeur_gemma as pg


def _reference_via_say(mot: str) -> np.ndarray:
    """Génère l'audio de référence via `say` (macOS TTS). Identique en logique à
    `client_professeur._reference_via_say` (déjà validé fonctionnel, voir
    CONCEPTION_v22_audio.md §5) — dupliqué ici plutôt que déplacé, pour ne prendre
    aucun risque sur le client déjà en usage (voir Question ouverte du plan v23.0 sur
    un futur partage de code entre les deux)."""
    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as f:
        chemin_aiff = f.name
    try:
        subprocess.run(["say", "-o", chemin_aiff, mot], check=True, capture_output=True)
        chemin_wav = chemin_aiff.replace(".aiff", ".wav")
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@" + str(SAMPLE_RATE),
                         chemin_aiff, chemin_wav], check=True, capture_output=True)
        import soundfile as sf
        onde, sr = sf.read(chemin_wav, dtype="float32")
        if onde.ndim > 1:
            onde = onde.mean(axis=1)
        return onde
    finally:
        Path(chemin_aiff).unlink(missing_ok=True)
        Path(chemin_aiff.replace(".aiff", ".wav")).unlink(missing_ok=True)


def _mot_cible_du_palier(palier: int) -> tuple:
    """Retourne (mot_cible, formants_cibles) pour un palier du curriculum vocal —
    même logique que `client_professeur.lancer_lecon_parole` (lignes 88-100) : palier 1
    (Vocaliser) retombe sur "a" faute de cible précise ; les syllabes/mots (paliers 7+)
    retombent sur leur voyelle dominante, `VOYELLES_CIBLES` ne connaissant que les 5
    voyelles simples."""
    lecon = pg.choisir_lecon(palier)
    mot_cible = lecon["cible"] or "a"

    formants_cibles = VOYELLES_CIBLES.get(mot_cible)
    if formants_cibles is None:
        premiere_voyelle = next((c for c in mot_cible if c in VOYELLES_CIBLES), "a")
        formants_cibles = VOYELLES_CIBLES[premiere_voyelle]

    return mot_cible, formants_cibles


class CacheReferencesVocales:
    """Cache en mémoire des références audio du curriculum vocal — génère chaque
    référence UNE SEULE FOIS (au premier accès), pas à chaque tick. Le cursus vit
    des centaines de milliers de ticks vocaux (jusqu'à 1000 jours × 200 ticks
    d'après-midi) ; ré-invoquer `say`/`afconvert` à cette fréquence serait à la fois
    lent (latence process) et inutile, les références étant déterministes pour un mot
    donné. Clé de cache = le mot cible (pas le palier), pour dédupliquer naturellement
    les paliers qui partagent une voyelle dominante (voir `_mot_cible_du_palier`)."""

    def __init__(self):
        self._cache_mfcc = {}          # mot -> vecteur MFCC (liste de floats, DIM_MFCC dims)
        self._cache_formants = {}      # mot -> dict {"F1":.., "F2":..}
        self._nb_appels_say = 0        # compteur de vérification (voir tests)

    def _generer_si_absent(self, mot: str, formants_cibles: dict):
        if mot in self._cache_mfcc:
            return
        onde_reference = _reference_via_say(mot)
        self._nb_appels_say += 1
        self._cache_mfcc[mot] = extraire_mfcc(onde_reference, sample_rate=SAMPLE_RATE).tolist()
        self._cache_formants[mot] = formants_cibles

    def obtenir_pour_palier(self, palier: int) -> tuple:
        """Retourne (mfcc: list, formants_cibles: dict) pour le palier donné, générant
        et mettant en cache la référence audio si c'est la première fois qu'elle est
        demandée. C'est la méthode d'entrée principale utilisée par la boucle du
        cursus à chaque tick d'après-midi vocal."""
        mot_cible, formants_cibles = _mot_cible_du_palier(palier)
        self._generer_si_absent(mot_cible, formants_cibles)
        return self._cache_mfcc[mot_cible], self._cache_formants[mot_cible]

    def prechauffer(self, paliers: list = None):
        """Génère par avance les références pour une liste de paliers (par défaut,
        tout le curriculum vocal) — utile pour éviter le premier appel `say` en plein
        milieu d'une journée déjà lancée. Purement optionnel : `obtenir_pour_palier`
        génère paresseusement de toute façon si on ne préchauffe pas."""
        if paliers is None:
            paliers = [lecon["palier"] for lecon in pg.CURRICULUM_VOCAL]
        for palier in paliers:
            self.obtenir_pour_palier(palier)
