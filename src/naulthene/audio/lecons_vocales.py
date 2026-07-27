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

v27.0 (expérimental, "École de la Parole & Synesthésie") : CacheReferencesVocales lit
d'abord la banque vocale disque (voix/<mot>/<mot>_NN.wav, voir
instruments/enregistreur_voix.py) — la voix RÉELLE de l'utilisateur — et ne replie sur
`say` que si aucune prise n'existe pour un mot donné. L'interface publique
(obtenir_pour_palier) ne change pas : les 3 consommateurs existants
(cursus_developpemental.py, cursus_bebe.py, instruments/lancer_arene.py) n'ont rien à
modifier.

Aucune dépendance au réseau de neurones ici — pur signal + orchestration du curriculum,
testable en isolation (comme `hemisphere_audio.py` et `professeur_gemma.py`).
"""

import subprocess
import tempfile
import unicodedata
from pathlib import Path

import numpy as np

from naulthene.audio.hemisphere_audio import (
    extraire_mfcc, VOYELLES_CIBLES, SAMPLE_RATE, estimer_formants_agrege,
)
import naulthene.audio.professeur_gemma as pg

RACINE_BANQUE = Path("voix")  # voix/<mot>/<mot>_NN.wav — voir instruments/enregistreur_voix.py


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


def _voyelle_dominante(mot: str) -> str:
    """Première voyelle connue de VOYELLES_CIBLES dans `mot`, accents dépliés (NFD).

    v27.0 (correctif) : sans le dépliage NFD, "clé" ne contient AUCUNE voyelle de
    VOYELLES_CIBLES ("é" ≠ "e") et retombait silencieusement sur le défaut "a" — la
    cible F1/F2 du palier "clé" aurait été celle de "a". Même risque latent sur tout
    mot accentué du curriculum (le palier 14 "prends clé" s'en sortait par chance,
    via la voyelle de "prends")."""
    plie = unicodedata.normalize("NFD", mot.lower())
    plie = "".join(c for c in plie if not unicodedata.combining(c))
    return next((c for c in plie if c in VOYELLES_CIBLES), "a")


def _mot_cible_du_palier(palier: int) -> tuple:
    """Retourne (mot_cible, formants_cibles) pour un palier du curriculum vocal —
    même logique que `client_professeur.lancer_lecon_parole` (lignes 88-100) : palier 1
    (Vocaliser) retombe sur "a" faute de cible précise ; les syllabes/mots (paliers 7+)
    retombent sur leur voyelle dominante (voir `_voyelle_dominante`), `VOYELLES_CIBLES`
    ne connaissant que les 5 voyelles simples. Ces formants théoriques ne servent que de
    repli — `CacheReferencesVocales` les remplace par les formants RÉELS (LPC) de la
    banque vocale quand elle existe pour ce mot (v27.0)."""
    lecon = pg.choisir_lecon(palier)
    mot_cible = lecon["cible"] or "a"

    formants_cibles = VOYELLES_CIBLES.get(mot_cible)
    if formants_cibles is None:
        formants_cibles = VOYELLES_CIBLES[_voyelle_dominante(mot_cible)]

    return mot_cible, formants_cibles


def _slug_mot(mot: str) -> str:
    """Normalise un mot en nom de fichier/dossier stable : minuscules, accents
    conservés (voix/clé/, pas voix/cle/ — le dossier reste lisible pour l'utilisateur
    qui enregistre), espaces → underscore ("ouvre porte" -> "ouvre_porte")."""
    return mot.lower().strip().replace(" ", "_")


def lister_prises(mot: str, racine: Path = RACINE_BANQUE) -> list:
    """Chemins des prises .wav existantes pour `mot`, triés. Liste VIDE si le dossier
    n'existe pas — jamais une exception : c'est le cas nominal avant tout
    enregistrement, et le signal de repli sur `say` pour CacheReferencesVocales."""
    dossier = racine / _slug_mot(mot)
    if not dossier.is_dir():
        return []
    return sorted(dossier.glob(f"{_slug_mot(mot)}_*.wav"))


def _references_depuis_banque(mot: str, racine: Path = RACINE_BANQUE) -> list:
    """Charge toutes les prises .wav de la banque disque pour `mot`. Liste VIDE =
    signal de repli sur `say`, pas une erreur : un utilisateur qui n'a jamais enregistré
    sa voix doit pouvoir lancer un cursus exactement comme avant la v27.0. Force le
    mono (moyenne des canaux) et le SAMPLE_RATE attendu — même contrat que
    `_reference_via_say`."""
    import soundfile as sf

    ondes = []
    for chemin in lister_prises(mot, racine=racine):
        try:
            onde, sr = sf.read(str(chemin), dtype="float32")
        except Exception:
            continue
        if onde.ndim > 1:
            onde = onde.mean(axis=1)
        if sr != SAMPLE_RATE:
            import librosa
            onde = librosa.resample(onde.astype(np.float64), orig_sr=sr, target_sr=SAMPLE_RATE).astype(np.float32)
        ondes.append(onde)
    return ondes


class CacheReferencesVocales:
    """Cache en mémoire des références audio du curriculum vocal — génère chaque
    référence UNE SEULE FOIS (au premier accès), pas à chaque tick. Le cursus vit
    des centaines de milliers de ticks vocaux (jusqu'à 1000 jours × 200 ticks
    d'après-midi) ; ré-invoquer `say`/`afconvert` à cette fréquence serait à la fois
    lent (latence process) et inutile, les références étant déterministes pour un mot
    donné. Clé de cache = le mot cible (pas le palier), pour dédupliquer naturellement
    les paliers qui partagent une voyelle dominante (voir `_mot_cible_du_palier`).

    v27.0 : source de la référence = banque vocale disque (voix de l'utilisateur) si
    des prises existent pour ce mot, sinon repli sur `say` — comportement identique à
    avant v27.0 tant qu'aucune prise n'a été enregistrée (voir
    instruments/enregistreur_voix.py)."""

    def __init__(self):
        self._cache_mfcc = {}          # mot -> vecteur MFCC MOYEN (liste de floats, DIM_MFCC dims)
        self._cache_formants = {}      # mot -> dict {"F1":.., "F2":..} — réels (LPC) si banque, théoriques sinon
        self._cache_mfcc_prises = {}   # mot -> liste de MFCC (np.ndarray) des prises INDIVIDUELLES
        self._nb_appels_say = 0        # compteur de vérification (voir tests)
        self._nb_prises_banque = 0     # nombre total de prises .wav effectivement chargées
        self.source_par_mot = {}       # mot -> "banque (N prise(s))" | "say (repli)"

    def _generer_si_absent(self, mot: str, formants_cibles: dict):
        if mot in self._cache_mfcc:
            return
        prises = _references_depuis_banque(mot)
        if prises:
            self._nb_prises_banque += len(prises)
            self.source_par_mot[mot] = f"banque ({len(prises)} prise(s))"
            mfcc_prises = [extraire_mfcc(p, sample_rate=SAMPLE_RATE) for p in prises]
            self._cache_mfcc_prises[mot] = mfcc_prises
            # Moyenne des MFCC (domaine cepstral, quasi-linéaire) plutôt que des ondes —
            # moyenner des ondes désalignées en phase les annulerait partiellement.
            self._cache_mfcc[mot] = np.mean(mfcc_prises, axis=0).tolist()
            # Cible F1/F2 = formants RÉELS estimés par LPC (médiane sur les prises) —
            # décision utilisateur v27.0 : l'agent doit être noté ET entraîné sur ce
            # qu'il entend réellement. Repli sur la table théorique si aucune prise
            # n'est acoustiquement exploitable (silence, clip...) — dégrade vers le
            # comportement pré-v27.0 plutôt que de casser le cursus.
            self._cache_formants[mot] = estimer_formants_agrege(prises, SAMPLE_RATE) or formants_cibles
        else:
            onde_reference = _reference_via_say(mot)
            self._nb_appels_say += 1
            self.source_par_mot[mot] = "say (repli)"
            mfcc = extraire_mfcc(onde_reference, sample_rate=SAMPLE_RATE)
            self._cache_mfcc_prises[mot] = [mfcc]
            self._cache_mfcc[mot] = mfcc.tolist()
            self._cache_formants[mot] = formants_cibles

    def obtenir_pour_palier(self, palier: int) -> tuple:
        """Retourne (mfcc: list, formants_cibles: dict) pour le palier donné, générant
        et mettant en cache la référence audio si c'est la première fois qu'elle est
        demandée. C'est la méthode d'entrée principale utilisée par la boucle du
        cursus à chaque tick d'après-midi vocal."""
        mot_cible, formants_cibles = _mot_cible_du_palier(palier)
        self._generer_si_absent(mot_cible, formants_cibles)
        return self._cache_mfcc[mot_cible], self._cache_formants[mot_cible]

    def obtenir_mfcc_prises(self, palier: int) -> list:
        """Les MFCC des prises INDIVIDUELLES du mot du palier (v27.0), pour le canal
        spectral de la récompense mixte (voir hemisphere_audio.recompense_vocale_mixte,
        noyau._evaluer_production_vocale). Distinct du MFCC MOYEN retourné par
        obtenir_pour_palier, qui reste l'ENTRÉE de l'oreille (porte_auditive)."""
        mot_cible, formants_cibles = _mot_cible_du_palier(palier)
        self._generer_si_absent(mot_cible, formants_cibles)
        return self._cache_mfcc_prises[mot_cible]

    def resume_banque(self) -> str:
        """Résumé lisible de la provenance des références en cache — combien viennent
        de la banque vocale de l'utilisateur vs du repli `say`."""
        n_banque = sum(1 for s in self.source_par_mot.values() if s.startswith("banque"))
        n_say = sum(1 for s in self.source_par_mot.values() if s.startswith("say"))
        return f"{n_banque} mot(s) depuis la banque ({self._nb_prises_banque} prise(s)), {n_say} depuis say"

    def prechauffer(self, paliers: list = None):
        """Génère par avance les références pour une liste de paliers (par défaut,
        tout le curriculum vocal) — utile pour éviter le premier appel `say` en plein
        milieu d'une journée déjà lancée. Purement optionnel : `obtenir_pour_palier`
        génère paresseusement de toute façon si on ne préchauffe pas."""
        if paliers is None:
            paliers = [lecon["palier"] for lecon in pg.CURRICULUM_VOCAL]
        for palier in paliers:
            self.obtenir_pour_palier(palier)
