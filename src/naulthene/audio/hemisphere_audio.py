"""
L'Hémisphère Auditif & Vocal (V22.0, expérimental) — Pur traitement du signal.

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test"), pas encore porté sur `agi_google_colab.py`. Voir
CONCEPTION_v22_audio.md pour le contexte narratif complet et readme.md pour la
section "Nouveautés v22.0".

Aucune dépendance au réseau de neurones ici — c'est le lobe temporal et l'appareil
phonatoire pris isolément, testables sans `AGI_Naulthene`. Quatre briques :

  1. `SynthetiseurFormants`  : vecteur 8-dim → onde audio (la BOUCHE physique).
  2. `extraire_mfcc`         : onde audio → vecteur MFCC (le son brut perçu par l'OREILLE).
  3. `distance_formants`     : récompense déterministe par tick (rapide, pas de LLM).
  4. Capture micro + Whisper : pour que l'utilisateur prononce le mot cible, et pour
     juger les mots plus complexes (palier 5 du curriculum vocal).

Le choix de synthèse par formants (décision utilisateur, voir CONCEPTION_v22_audio.md
§2-3) réduit l'espace de sortie vocal à ~8 nombres physiques plutôt qu'une onde brute
arbitraire — c'est ce qui rend le problème de babillage RL tractable (l'agent apprend
à « placer sa bouche », pas à halluciner un signal audio complet).
"""

import numpy as np

SAMPLE_RATE = 16000  # Hz — standard pour la parole (suffisant jusqu'à ~F3, cohérent avec Whisper)

# --- Bornes physiques des 8 paramètres de tete_vocale (sortie sigmoid [0,1] → mappée ici) ---
# f0 (fréquence fondamentale, pitch) et F1/F2/F3 (formants, résonances du conduit vocal) sont
# les paramètres classiques de synthèse de la parole (modèle source-filtre). F1_bw/F2_bw
# (largeurs de bande) contrôlent la netteté des résonances ; durée et amplitude ferment
# l'espace physique. Bornes calibrées sur les voyelles humaines usuelles (a/e/i/o/u).
BORNES_F0 = (80.0, 300.0)       # Hz — voix humaine grave à aiguë
BORNES_F1 = (250.0, 1000.0)     # Hz — hauteur de la langue (F1 bas = voyelle fermée)
BORNES_F2 = (700.0, 2500.0)     # Hz — avant/arrière de la langue
BORNES_F3 = (2000.0, 3500.0)    # Hz — timbre fin, moins critique pour l'identité vocalique
BORNES_BW = (50.0, 200.0)       # Hz — largeur de bande des résonances (netteté du timbre)
BORNES_DUREE = (0.1, 0.6)       # secondes — durée de la vocalisation
BORNES_AMPLITUDE = (0.1, 1.0)   # gain de sortie

# Cibles de référence pour les 5 voyelles (F1, F2 en Hz), valeurs phonétiques usuelles —
# utilisées par le curriculum vocal (professeur_gemma.py) pour fixer `formants_cibles`.
VOYELLES_CIBLES = {
    "a": {"F1": 730.0, "F2": 1090.0},
    "e": {"F1": 530.0, "F2": 1840.0},
    "i": {"F1": 270.0, "F2": 2290.0},
    "o": {"F1": 570.0, "F2": 840.0},
    "u": {"F1": 300.0, "F2": 870.0},
}


def _demapper(valeur_01: float, bornes: tuple) -> float:
    """Convertit une sortie sigmoid [0,1] de tete_vocale vers l'unité physique réelle."""
    lo, hi = bornes
    return lo + float(np.clip(valeur_01, 0.0, 1.0)) * (hi - lo)


class SynthetiseurFormants:
    """Synthèse par formants (modèle source-filtre) : une source glottique (train
    d'impulsions à f0, approximant les cordes vocales) traverse une cascade de 3
    résonateurs (F1/F2/F3, approximant le conduit vocal) implémentés en filtres
    résonants du second ordre (biquad). Pur numpy — aucune dépendance lourde,
    cohérent avec le principe d'un espace vocal petit et réellement apprenable."""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate

    def parametres_depuis_vecteur(self, vecteur_8d) -> dict:
        """Démappe le vecteur brut [0,1]^8 produit par `tete_vocale` (sortie sigmoid)
        vers les 8 paramètres physiques nommés. Ordre fixe, cohérent avec DIM_VOCALE=8
        (voir agi_local_test.py) : f0, F1, F2, F3, F1_bw, F2_bw, duree, amplitude."""
        v = np.asarray(vecteur_8d, dtype=np.float64).reshape(-1)
        assert v.shape[0] == 8, f"attendu un vecteur de 8 paramètres vocaux, reçu {v.shape[0]}"
        return {
            "f0": _demapper(v[0], BORNES_F0),
            "F1": _demapper(v[1], BORNES_F1),
            "F2": _demapper(v[2], BORNES_F2),
            "F3": _demapper(v[3], BORNES_F3),
            "F1_bw": _demapper(v[4], BORNES_BW),
            "F2_bw": _demapper(v[5], BORNES_BW),
            "duree": _demapper(v[6], BORNES_DUREE),
            "amplitude": _demapper(v[7], BORNES_AMPLITUDE),
        }

    def _source_glottique(self, f0: float, duree: float) -> np.ndarray:
        """Train d'impulsions périodique à f0, lissé (approxime le flux glottique
        pulsé des cordes vocales) — la source d'énergie brute avant filtrage formantique."""
        n = int(self.sample_rate * duree)
        t = np.arange(n) / self.sample_rate
        phase = (t * f0) % 1.0
        # Impulsion douce (montée rapide, décroissance exponentielle) plutôt qu'un Dirac
        # pur, pour éviter un spectre trop riche en aliasing à cette fréquence d'échantillonnage.
        source = np.exp(-phase * 40.0) - np.exp(-((1.0 - phase) % 1.0) * 40.0) * 0.3
        return source.astype(np.float64)

    def _resonateur(self, signal: np.ndarray, freq: float, bw: float) -> np.ndarray:
        """Filtre résonant du second ordre (biquad passe-bande) centré sur `freq`,
        de largeur `bw` — un formant du conduit vocal. Coefficients dérivés de la
        forme standard "resonator" (Klatt-like), stable pour freq < sample_rate/2."""
        freq = min(freq, self.sample_rate / 2.0 - 100.0)
        r = np.exp(-np.pi * bw / self.sample_rate)
        theta = 2.0 * np.pi * freq / self.sample_rate
        a1 = 2.0 * r * np.cos(theta)
        a2 = -r * r
        gain = (1.0 - r * r) * 0.5  # normalisation approximative de l'énergie de sortie

        sortie = np.zeros_like(signal)
        y1, y2 = 0.0, 0.0
        for i, x in enumerate(signal):
            y0 = gain * x + a1 * y1 + a2 * y2
            sortie[i] = y0
            y2 = y1
            y1 = y0
        return sortie

    def synthetiser(self, vecteur_8d) -> np.ndarray:
        """Vecteur 8-dim → onde audio mono float32 dans [-1, 1], prête pour lecture
        (sounddevice) ou extraction MFCC. Cascade : source glottique → F1 → F2 → F3,
        puis normalisation par l'amplitude cible."""
        p = self.parametres_depuis_vecteur(vecteur_8d)
        source = self._source_glottique(p["f0"], p["duree"])

        signal = self._resonateur(source, p["F1"], p["F1_bw"])
        signal = self._resonateur(signal, p["F2"], p["F2_bw"])
        # F3 réutilise une largeur de bande standard (moins critique pour l'identité
        # vocalique que F1/F2, pas besoin d'un 6e paramètre dédié dans DIM_VOCALE).
        signal = self._resonateur(signal, p["F3"], 150.0)

        pic = np.max(np.abs(signal)) + 1e-8
        signal = (signal / pic) * p["amplitude"]

        # Fondu d'attaque/chute (10 ms) pour éviter les clics audibles en lecture live.
        n_fade = min(len(signal) // 4, int(0.01 * self.sample_rate))
        if n_fade > 0:
            fenetre = np.linspace(0.0, 1.0, n_fade)
            signal[:n_fade] *= fenetre
            signal[-n_fade:] *= fenetre[::-1]

        return signal.astype(np.float32)


def jouer_son_temps_reel(onde: np.ndarray, sample_rate: int = SAMPLE_RATE, bloquant: bool = False):
    """Joue l'onde immédiatement dans les haut-parleurs — c'est ce qui permet
    d'ENTENDRE le babil de l'agent en direct (exigence explicite de l'utilisateur).
    `bloquant=False` par défaut pour ne pas geler la boucle de leçon/tick pendant la
    lecture ; passer `bloquant=True` pour un usage hors boucle temps réel (debug)."""
    import sounddevice as sd
    sd.play(onde, samplerate=sample_rate)
    if bloquant:
        sd.wait()


# v22.1 (correctif bug, détecté sur un run réel via client_professeur.py) :
# `librosa.feature.mfcc` retourne des coefficients bruts d'amplitude très variable —
# mesuré sur 7 références `say` (voyelles + mots) : min≈-627, écart-type≈120, dominés
# par le coefficient 0 (énergie globale). Ce vecteur, multiplié par les poids de
# porte_auditive, sature complètement la sigmoid de tete_vocale (paramètres vocaux
# figés à 0.0/1.0 exacts), rendant tout apprentissage vocal impossible — le score de
# formants restait bloqué à 0.000 sur un run réel. Standardisation (centrage +
# réduction) plutôt qu'une simple division : plus robuste face à la grande variance du
# coefficient d'énergie que ne l'est une constante d'échelle fixe.
MFCC_MOYENNE_EMPIRIQUE = -180.0  # ordre de grandeur mesuré (voix humaine, réf. `say`)
MFCC_ECART_TYPE_EMPIRIQUE = 120.0


def extraire_mfcc(onde: np.ndarray, sample_rate: int = SAMPLE_RATE, n_mfcc: int = 13,
                   n_frames: int = 10) -> np.ndarray:
    """Onde audio → vecteur MFCC aplati de taille DIM_MFCC (13×10=130, voir
    agi_local_test.py), standardisé. C'est le "son brut" perçu par `porte_auditive` —
    la moitié physique de la double entrée auditive (l'autre moitié est l'embedding
    sémantique, voir professeur_gemma.py). Padding/troncature à `n_frames` frames
    temporelles fixes pour garantir une dimension constante quelle que soit la durée
    du son d'entrée. Voir MFCC_MOYENNE_EMPIRIQUE/MFCC_ECART_TYPE_EMPIRIQUE ci-dessus
    pour le correctif de saturation (v22.1)."""
    import librosa

    onde64 = onde.astype(np.float64)
    if onde64.size < 512:
        onde64 = np.pad(onde64, (0, 512 - onde64.size))

    mfcc = librosa.feature.mfcc(y=onde64, sr=sample_rate, n_mfcc=n_mfcc)  # (n_mfcc, n_frames_reelles)

    if mfcc.shape[1] < n_frames:
        mfcc = np.pad(mfcc, ((0, 0), (0, n_frames - mfcc.shape[1])))
    else:
        # Sous-échantillonne uniformément plutôt que de tronquer brutalement la fin —
        # préserve la forme temporelle globale du son même s'il est plus long que prévu.
        indices = np.linspace(0, mfcc.shape[1] - 1, n_frames).astype(int)
        mfcc = mfcc[:, indices]

    mfcc = (mfcc - MFCC_MOYENNE_EMPIRIQUE) / MFCC_ECART_TYPE_EMPIRIQUE
    return mfcc.flatten().astype(np.float32)  # (n_mfcc * n_frames,) = (DIM_MFCC,)


def distance_formants(cible: dict, produit: dict) -> float:
    """Distance normalisée entre les formants cibles (ex: VOYELLES_CIBLES["a"]) et les
    formants réellement produits par l'agent (voir parametres_depuis_vecteur). C'est LA
    récompense par tick (déterministe, instantanée — pas d'appel LLM, voir
    CONCEPTION_v22_audio.md §6 : Gemma met ~8s par réponse, incompatible avec le RL par
    tick). Retourne une distance brute ; `recompense_formants` la convertit en score."""
    dF1 = (cible["F1"] - produit["F1"]) / (BORNES_F1[1] - BORNES_F1[0])
    dF2 = (cible["F2"] - produit["F2"]) / (BORNES_F2[1] - BORNES_F2[0])
    return float(np.sqrt(dF1 ** 2 + dF2 ** 2))


def recompense_formants(cible: dict, produit: dict, tolerance: float = 0.35) -> float:
    """Convertit la distance de formants en score de récompense [0,1] — 1.0 si les
    formants produits tombent pile sur la cible, décroissant linéairement jusqu'à 0
    au-delà de `tolerance`. Récompense CONTINUE (pas 0/1 binaire) : « se rapprocher »
    compte déjà, ce qui donne un gradient de progression au babillage plutôt qu'un mur
    de récompense creuse (voir CONCEPTION_v22_audio.md §3)."""
    d = distance_formants(cible, produit)
    return float(max(0.0, 1.0 - d / tolerance))


def capture_micro(duree: float = 2.0, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Enregistre `duree` secondes depuis le micro par défaut du système — pour que
    l'utilisateur prononce lui-même le mot cible (entrée réelle, complémentaire à `say`
    pour générer une référence synthétique). Bloquant (l'enregistrement doit se
    terminer avant de continuer la leçon)."""
    import sounddevice as sd
    onde = sd.rec(int(duree * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    return onde.flatten()


_modele_whisper = None  # chargé paresseusement (modèle lourd, ~150 Mo pour "base")


def transcrire_whisper(onde: np.ndarray, sample_rate: int = SAMPLE_RATE, modele: str = "base") -> str:
    """Transcrit une onde audio en texte via Whisper (local, pas d'appel réseau) —
    utilisé pour le palier 5 du curriculum vocal (mots courts, voir
    CONCEPTION_v22_audio.md §7) et pour donner à Gemma une description textuelle du
    son produit par l'agent (Gemma ne peut pas "entendre" un .wav directement)."""
    import whisper

    global _modele_whisper
    if _modele_whisper is None or getattr(_modele_whisper, "_nom_modele", None) != modele:
        _modele_whisper = whisper.load_model(modele)
        _modele_whisper._nom_modele = modele

    onde16 = onde.astype(np.float32)
    if sample_rate != 16000:
        import librosa
        onde16 = librosa.resample(onde16, orig_sr=sample_rate, target_sr=16000)

    resultat = _modele_whisper.transcribe(onde16, language="fr", fp16=False)
    return resultat["text"].strip()
