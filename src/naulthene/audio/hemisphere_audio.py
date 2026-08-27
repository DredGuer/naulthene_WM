# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
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

v27.0 (expérimental, "École de la Parole & Synesthésie") ajoute deux briques : un
estimateur de formants réels par analyse LPC (`estimer_formants_lpc`/
`estimer_formants_agrege`), pour que la cible F1/F2 vienne de la voix de l'utilisateur
plutôt que de la table théorique VOYELLES_CIBLES ; et une distance/récompense spectrale
MFCC↔MFCC (`distance_spectrale`/`recompense_spectrale`/`recompense_vocale_mixte`), pour
noter l'agent sur le son réellement synthétisé, pas seulement sur deux nombres. Voir
docs/ameliorations_appliquees/CONCEPTION_v22_audio.md §8.
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
        forme standard "resonator" (Klatt-like), stable pour freq < sample_rate/2.

        v27.0 : la récurrence IIR est vectorisée via scipy.signal.lfilter (même
        coefficients, même équation aux différences, sortie numériquement identique à
        la boucle Python d'origine — ~100x plus rapide). Nécessaire pour évaluer un
        canal spectral MFCC↔MFCC à chaque tick sans doubler la durée d'un run long (voir
        recompense_vocale_mixte). Repli sur la boucle Python si scipy est absent — ce
        module reste "pur numpy, deps lazy", scipy n'est qu'une accélération optionnelle."""
        freq = min(freq, self.sample_rate / 2.0 - 100.0)
        r = np.exp(-np.pi * bw / self.sample_rate)
        theta = 2.0 * np.pi * freq / self.sample_rate
        a1 = 2.0 * r * np.cos(theta)
        a2 = -r * r
        gain = (1.0 - r * r) * 0.5  # normalisation approximative de l'énergie de sortie

        try:
            from scipy.signal import lfilter
            return lfilter([gain], [1.0, -a1, -a2], signal)
        except ImportError:
            pass

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
                   n_frames: int = 10, standardisation: str = "echantillon") -> np.ndarray:
    """Onde audio → vecteur MFCC aplati de taille DIM_MFCC (13×10=130, voir
    agi_local_test.py), standardisé. C'est le "son brut" perçu par `porte_auditive` —
    la moitié physique de la double entrée auditive (l'autre moitié est l'embedding
    sémantique, voir professeur_gemma.py). Padding/troncature à `n_frames` frames
    temporelles fixes pour garantir une dimension constante quelle que soit la durée
    du son d'entrée.

    `standardisation` (v27.0) :
      - "echantillon" (défaut) : centre/réduit par la moyenne/écart-type du vecteur MFCC
        LUI-MÊME (CMVN par échantillon), plutôt que par MFCC_MOYENNE_EMPIRIQUE/
        MFCC_ECART_TYPE_EMPIRIQUE ci-dessus, calibrées une fois sur 7 références `say`.
        Avec une banque de prises micro réelles (v27.0, lecons_vocales), le niveau
        d'entrée varie de plusieurs dizaines de dB d'une prise à l'autre — une constante
        d'échelle fixe re-sature alors la sigmoid de tete_vocale exactement comme le bug
        v22.1 d'origine (voir MFCC_MOYENNE_EMPIRIQUE ci-dessus). Effet de bord assumé :
        cette standardisation détruit l'information de niveau absolu (pratique standard,
        dite CMVN) — acceptable ici car l'identité vocalique est portée par la FORME
        spectrale, pas le niveau, et le silence est codé en amont par obs_auditive=None
        (jamais par un vecteur MFCC nul).
      - "constantes" : comportement strictement v22.1 (MFCC_MOYENNE_EMPIRIQUE/
        MFCC_ECART_TYPE_EMPIRIQUE), conservé pour comparaison A/B."""
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

    if standardisation == "echantillon":
        mu = float(mfcc.mean())
        sigma = float(mfcc.std())
        mfcc = (mfcc - mu) / max(sigma, 1e-3)
    else:
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


# --- Analyse acoustique de références réelles (v27.0, "École de la Parole & Synesthésie") ---
# Jusqu'ici, la cible F1/F2 de toute leçon vocale venait de VOYELLES_CIBLES — une table
# théorique d'une voyelle moyenne d'un locuteur moyen. La v27.0 permet d'extraire les
# formants RÉELS d'un enregistrement (la voix de l'utilisateur, voir
# lecons_vocales.CacheReferencesVocales) et de comparer le son PRODUIT par l'agent, pas
# seulement les deux nombres qu'il a choisi d'émettre, à ce que l'utilisateur a
# réellement dit — récompense ET apprentissage doivent porter sur la même vérité.
ORDRE_LPC_PAR_KHZ = 2                # ordre LPC ≈ 2 + 2*sr_kHz → 2+16=18 à 16 kHz, règle
                                      # empirique classique pour l'analyse de la parole
LARGEUR_BANDE_MAX_FORMANT = 400.0    # Hz — au-delà, la racine LPC est trop amortie pour
                                      # être un vrai formant (bruit / pôle parasite)
FREQ_MIN_FORMANT = 90.0              # Hz — élimine les racines proches de la composante continue
FREQ_MAX_FORMANT = 5000.0
FENETRE_ANALYSE_LPC = 0.025          # 25 ms — fenêtre standard d'analyse de la parole
PAS_ANALYSE_LPC = 0.010              # 10 ms
PERCENTILE_ENERGIE_TRAME_LPC = 70    # ne garder que les trames au-delà de ce percentile
                                      # d'énergie (voir estimer_formants_lpc, étape 2bis)

POIDS_RECOMPENSE_FORMANTS = 0.6   # F1/F2 restent dominants : ce sont les SEULES dimensions
                                   # où tete_vocale reçoit un gradient MSE dirigé (voir
                                   # noyau._evaluer_production_vocale, indices [1, 2]).
POIDS_RECOMPENSE_SPECTRALE = 0.4  # le timbre global (MFCC) apporte la nuance que 2 formants
                                   # ne capturent pas, mais ne peut pas dominer un canal que
                                   # l'agent n'a AUCUN moyen direct d'optimiser (pas de
                                   # gradient dirigé dessus) — sinon le score devient
                                   # largement non-optimisable, plafond artificiel de
                                   # progression (même piège que l'ancien seuil fixe 0.5).
PERIODE_EVAL_SPECTRALE = 10       # le canal spectral (synthèse + MFCC de la production de
                                   # l'agent) coûte ~100x un score de formants même avec la
                                   # synthèse vectorisée (librosa.feature.mfcc reste une
                                   # STFT). Les paramètres vocaux varient très peu d'un tick
                                   # au suivant (le MFCC de référence est constant sur toute
                                   # une leçon), donc rafraîchir tous les PERIODE_EVAL_SPECTRALE
                                   # ticks ne perd quasi aucune information utile.


def estimer_formants_lpc(onde: np.ndarray, sample_rate: int = SAMPLE_RATE) -> dict | None:
    """Estime F1/F2 RÉELS d'un enregistrement par analyse LPC (Linear Predictive Coding)
    — le filtre INVERSE du modèle source-filtre de SynthetiseurFormants. Décision
    utilisateur v27.0 : l'agent doit être noté ET entraîné sur la voix de l'utilisateur,
    pas sur la table théorique VOYELLES_CIBLES.

    Algorithme :
      1. pré-accentuation y[n] = x[n] - 0.97*x[n-1] (compense la pente spectrale de
         -6 dB/octave de la source glottique — sans elle F1 est systématiquement
         sur-estimé en énergie et les formants hauts disparaissent) ;
      2. fenêtrage de Hamming sur des trames de FENETRE_ANALYSE_LPC, pas PAS_ANALYSE_LPC,
         en ne gardant que les trames au-delà du PERCENTILE_ENERGIE_TRAME_LPC-ième
         percentile d'énergie (le NOYAU stable de la voyelle, pas juste "au-dessus du
         silence") — un seuil relatif à la médiane laisse passer trop de trames
         d'attaque/chute où la résonance formantique est encore en train de s'établir :
         sur ces trames, la bande passante du pôle F1 dépasse souvent
         LARGEUR_BANDE_MAX_FORMANT et se fait filtrer, ce qui pousse F2 dans la case F1
         et fausse gravement la médiane (validé empiriquement : un seuil à 20% de la
         médiane donnait F1/F2 inversés sur ~40% des trames de "a", contre un signal
         propre et stable sur les trames de forte énergie) ;
      3. LPC d'ordre 2 + sample_rate//1000 par trame (librosa.lpc, algorithme de Burg) ;
      4. racines du polynôme LPC (np.roots), on garde le demi-plan imaginaire positif ;
      5. conversion en Hz : f = angle(r) * sr / (2*pi) ; largeur de bande :
         bw = -ln(|r|) * sr / pi ;
      6. filtrage des candidats : FREQ_MIN_FORMANT < f < FREQ_MAX_FORMANT et
         bw < LARGEUR_BANDE_MAX_FORMANT ; tri croissant ; F1 = 1er, F2 = 2e ;
      7. médiane inter-trames de F1 et de F2 (robuste aux trames aberrantes, contrairement
         à la moyenne).

    GARDE-FOU NON NÉGOCIABLE : F1/F2 sont clampés aux bornes physiques du synthétiseur
    (BORNES_F1/BORNES_F2) avant d'être retournés. Sans ce clamp, une cible LPC hors
    bornes serait physiquement INATTEIGNABLE par tete_vocale (sortie sigmoid démappée
    dans ces mêmes bornes) — la perte MSE plafonnerait, aucune promotion possible,
    rejouant le piège historique du seuil de promotion inatteignable sous une forme plus
    difficile à diagnostiquer (la cause serait dans un module signal, pas un seuil).

    Retourne {"F1": Hz, "F2": Hz} ou None si aucune trame exploitable (silence, clip,
    signal trop court, ou F1 >= F2 après clamp — trame incohérente) — None est un cas
    NORMAL que l'appelant doit gérer par repli sur VOYELLES_CIBLES, jamais une exception."""
    import librosa

    onde64 = np.asarray(onde, dtype=np.float64).flatten()
    if onde64.size < int(FENETRE_ANALYSE_LPC * sample_rate):
        return None

    preaccentue = np.append(onde64[0], onde64[1:] - 0.97 * onde64[:-1])

    taille_trame = int(FENETRE_ANALYSE_LPC * sample_rate)
    pas_trame = int(PAS_ANALYSE_LPC * sample_rate)
    fenetre = np.hamming(taille_trame)
    ordre = 2 + sample_rate // 1000

    energies = []
    trames = []
    for debut in range(0, max(1, len(preaccentue) - taille_trame + 1), pas_trame):
        trame = preaccentue[debut:debut + taille_trame]
        if trame.size < taille_trame:
            continue
        trames.append(trame * fenetre)
        energies.append(float(np.sum(trame ** 2)))

    if not trames:
        return None
    seuil_energie = float(np.percentile(energies, PERCENTILE_ENERGIE_TRAME_LPC))

    candidats_f1, candidats_f2, candidats_f3 = [], [], []
    for trame, energie in zip(trames, energies):
        if energie < seuil_energie:
            continue
        try:
            coeffs = librosa.lpc(trame, order=ordre)
        except Exception:
            continue
        racines = np.roots(coeffs)
        racines = racines[racines.imag > 0]
        if racines.size == 0:
            continue

        freqs = np.angle(racines) * sample_rate / (2.0 * np.pi)
        bws = -np.log(np.abs(racines) + 1e-12) * sample_rate / np.pi

        candidats = sorted(
            f for f, bw in zip(freqs, bws)
            if FREQ_MIN_FORMANT < f < FREQ_MAX_FORMANT and bw < LARGEUR_BANDE_MAX_FORMANT
        )
        if len(candidats) >= 2:
            candidats_f1.append(candidats[0])
            candidats_f2.append(candidats[1])
        if len(candidats) >= 3:
            candidats_f3.append(candidats[2])

    if not candidats_f1:
        return None

    f1 = float(np.clip(np.median(candidats_f1), *BORNES_F1))
    f2 = float(np.clip(np.median(candidats_f2), *BORNES_F2))
    if f1 >= f2:
        return None

    # v27.6 (décision utilisateur, "le cerveau doit intégrer le son peu importe la
    # forme, rien en dur, dynamique") : F3 vient EXACTEMENT du même mécanisme que
    # F1/F2 (racines LPC déjà calculées ci-dessus) — le 3e candidat trié, quand il
    # existe. Contrairement à F1/F2, l'absence de F3 exploitable n'invalide pas
    # l'estimation entière (F3 est physiquement "moins critique pour l'identité
    # vocalique", voir BORNES_F3) : repli sur None, géré par l'appelant.
    f3 = None
    if candidats_f3:
        f3 = float(np.clip(np.median(candidats_f3), *BORNES_F3))

    return {"F1": f1, "F2": f2, "F3": f3}


def estimer_pitch_f0(onde: np.ndarray, sample_rate: int = SAMPLE_RATE) -> float | None:
    """Estime f0 (fréquence fondamentale, la hauteur de voix perçue) RÉELLE d'un
    enregistrement par autocorrélation — technique standard de pitch-tracking,
    entièrement dérivée du signal, aucune valeur écrite en dur (décision utilisateur
    v27.6). Contrairement à l'analyse LPC (qui modélise le conduit vocal / les
    formants), f0 est la périodicité du signal glottique lui-même : on cherche le
    premier pic significatif de l'autocorrélation dans la plage physique BORNES_F0.

    Algorithme, par trame (mêmes fenêtres que estimer_formants_lpc, réutilise le même
    découpage temporel pour rester cohérent) :
      1. autocorrélation normalisée de la trame ;
      2. on ne cherche un pic que dans la plage de lags correspondant à BORNES_F0
         (une fréquence hors de la plage vocale humaine n'est pas un f0 plausible) ;
      3. pic retenu = maximum d'autocorrélation dans cette plage, converti en Hz ;
      4. médiane inter-trames (même robustesse qu'estimer_formants_lpc).

    Retourne None si aucune trame exploitable — cas normal (silence, bruit sans
    structure périodique claire), géré par repli chez l'appelant."""
    onde64 = np.asarray(onde, dtype=np.float64).flatten()
    if onde64.size < int(FENETRE_ANALYSE_LPC * sample_rate):
        return None

    taille_trame = int(FENETRE_ANALYSE_LPC * sample_rate)
    pas_trame = int(PAS_ANALYSE_LPC * sample_rate)
    fenetre = np.hamming(taille_trame)

    lag_min = int(sample_rate / BORNES_F0[1])  # f0 haute -> lag court
    lag_max = int(sample_rate / BORNES_F0[0])  # f0 basse -> lag long

    energies, trames = [], []
    for debut in range(0, max(1, len(onde64) - taille_trame + 1), pas_trame):
        trame = onde64[debut:debut + taille_trame]
        if trame.size < taille_trame:
            continue
        trames.append(trame * fenetre)
        energies.append(float(np.sum(trame ** 2)))
    if not trames:
        return None
    seuil_energie = float(np.percentile(energies, PERCENTILE_ENERGIE_TRAME_LPC))

    candidats_f0 = []
    for trame, energie in zip(trames, energies):
        if energie < seuil_energie or lag_max >= len(trame):
            continue
        autocorr = np.correlate(trame, trame, mode="full")[len(trame) - 1:]
        if autocorr[0] <= 0:
            continue
        autocorr = autocorr / autocorr[0]
        segment = autocorr[lag_min:lag_max + 1]
        if segment.size == 0 or float(np.max(segment)) < 0.3:  # pic trop faible = pas de vraie périodicité
            continue
        lag_pic = lag_min + int(np.argmax(segment))
        if lag_pic > 0:
            candidats_f0.append(sample_rate / lag_pic)

    if not candidats_f0:
        return None
    return float(np.clip(np.median(candidats_f0), *BORNES_F0))


def estimer_duree_amplitude(onde: np.ndarray, sample_rate: int = SAMPLE_RATE) -> tuple:
    """Durée et amplitude RÉELLES d'un enregistrement — mesures directes du signal,
    aucune estimation nécessaire (contrairement aux formants/f0, ce sont des propriétés
    physiques immédiates de l'onde). Durée = longueur réelle de l'enregistrement (déjà
    recadré du silence par instruments/enregistreur_voix.py, voir son docstring) ;
    amplitude = crête absolue normalisée. Les deux sont clampées aux bornes physiques du
    synthétiseur (BORNES_DUREE/BORNES_AMPLITUDE) — même garde-fou que les formants : une
    cible hors bornes serait inatteignable par tete_vocale."""
    onde64 = np.asarray(onde, dtype=np.float64).flatten()
    duree = float(np.clip(onde64.size / sample_rate, *BORNES_DUREE))
    amplitude = float(np.clip(np.max(np.abs(onde64)) if onde64.size else 0.0, *BORNES_AMPLITUDE))
    return duree, amplitude


def estimer_parametres_vocaux_complets(onde: np.ndarray, sample_rate: int = SAMPLE_RATE) -> dict:
    """v27.6 (décision utilisateur) : les 8 paramètres physiques de tete_vocale (voir
    SynthetiseurFormants.parametres_depuis_vecteur pour l'ordre canonique), TOUS extraits
    dynamiquement d'un enregistrement réel — aucune valeur écrite en dur. Combine
    estimer_formants_lpc (F1/F2/F3), estimer_pitch_f0 (f0), estimer_duree_amplitude
    (durée/amplitude). F1_bw/F2_bw n'ont pas d'équivalent physique mesurable simplement
    par LPC (la largeur de bande RÉELLE d'un formant humain varie trop selon la méthode
    d'estimation pour servir de cible fiable) — repli sur le CENTRE de BORNES_BW, qui
    reste une plage de synthèse, pas une valeur de voix théorique.

    Toute dimension non estimable (silence, signal trop court, pas de périodicité
    claire) retombe sur le CENTRE de sa borne physique respective plutôt que d'échouer
    entièrement — un repli neutre (0.5 en espace [0,1]) est préférable à l'absence totale
    de cible sur cette dimension, cohérent avec le traitement des dimensions non
    contraintes de `_construire_cible_vocale` (noyau.py)."""
    formants = estimer_formants_lpc(onde, sample_rate)
    f0 = estimer_pitch_f0(onde, sample_rate)
    duree, amplitude = estimer_duree_amplitude(onde, sample_rate)

    return {
        "f0": f0 if f0 is not None else float(np.mean(BORNES_F0)),
        "F1": formants["F1"] if formants else float(np.mean(BORNES_F1)),
        "F2": formants["F2"] if formants else float(np.mean(BORNES_F2)),
        "F3": (formants.get("F3") if formants else None) or float(np.mean(BORNES_F3)),
        "F1_bw": float(np.mean(BORNES_BW)),
        "F2_bw": float(np.mean(BORNES_BW)),
        "duree": duree,
        "amplitude": amplitude,
    }


def estimer_formants_agrege(prises: list, sample_rate: int = SAMPLE_RATE) -> dict | None:
    """Agrège les estimations LPC de plusieurs prises du MÊME mot par MÉDIANE de F1 et
    de F2 séparément (pas moyenne : une prise ratée — toux, saturation, mauvais micro —
    décale la moyenne d'une centaine de Hz, la médiane l'ignore dès 3 prises). Ignore
    les prises dont estimer_formants_lpc renvoie None. Retourne None si aucune prise
    n'est exploitable — l'appelant (CacheReferencesVocales) replie alors sur
    VOYELLES_CIBLES, garantissant qu'une banque de mauvaise qualité dégrade vers le
    comportement pré-v27.0 plutôt que de casser le cursus."""
    estimations = [estimer_formants_lpc(p, sample_rate) for p in prises]
    estimations = [e for e in estimations if e is not None]
    if not estimations:
        return None
    return {
        "F1": float(np.median([e["F1"] for e in estimations])),
        "F2": float(np.median([e["F2"] for e in estimations])),
    }


def estimer_parametres_vocaux_agreges(prises: list, sample_rate: int = SAMPLE_RATE) -> dict:
    """v27.6 : équivalent multi-prises d'estimer_parametres_vocaux_complets — médiane
    de chaque dimension estimée sur TOUTES les prises exploitables (même logique de
    robustesse qu'estimer_formants_agrege). Ne retourne jamais None : une prise absente
    sur une dimension particulière (ex. f0 non détecté sur une prise bruitée) est
    simplement exclue de la médiane de CETTE dimension, pas de toutes — si AUCUNE prise
    n'est exploitable pour une dimension donnée, repli sur le centre de sa borne
    physique (même principe que estimer_parametres_vocaux_complets)."""
    if not prises:
        return estimer_parametres_vocaux_complets(np.zeros(1, dtype=np.float32), sample_rate)

    par_dimension = {"f0": [], "F1": [], "F2": [], "F3": [], "duree": [], "amplitude": []}
    for onde in prises:
        params = estimer_parametres_vocaux_complets(onde, sample_rate)
        for cle in par_dimension:
            par_dimension[cle].append(params[cle])

    return {
        "f0": float(np.median(par_dimension["f0"])),
        "F1": float(np.median(par_dimension["F1"])),
        "F2": float(np.median(par_dimension["F2"])),
        "F3": float(np.median(par_dimension["F3"])),
        "F1_bw": float(np.mean(BORNES_BW)),
        "F2_bw": float(np.mean(BORNES_BW)),
        "duree": float(np.median(par_dimension["duree"])),
        "amplitude": float(np.median(par_dimension["amplitude"])),
    }


def distance_spectrale(mfcc_a, mfcc_b) -> float:
    """Distance cosinus normalisée dans [0,1] entre deux vecteurs MFCC de DIM_MFCC dims
    (0 = timbres identiques, 1 = orthogonaux/opposés) : d = (1 - cos(a,b)) / 2.

    Cosinus et non L2 : après la standardisation par échantillon (v27.0,
    extraire_mfcc), seule la FORME du vecteur porte de l'information — sa norme est
    artificiellement ramenée à ~sqrt(DIM_MFCC) pour tout son, donc une L2 mesurerait
    surtout du bruit de normalisation. Le cosinus est invariant à cette normalisation,
    ce qui le rend aussi invariant au volume de la prise micro (une prise forte et une
    prise faible du même « a » donnent la même distance) — exactement la propriété
    voulue d'une banque de prises hétérogènes."""
    a = np.asarray(mfcc_a, dtype=np.float64).flatten()
    b = np.asarray(mfcc_b, dtype=np.float64).flatten()
    norme_a = np.linalg.norm(a)
    norme_b = np.linalg.norm(b)
    if norme_a < 1e-9 or norme_b < 1e-9:
        return 1.0
    cos = float(np.dot(a, b) / (norme_a * norme_b))
    cos = max(-1.0, min(1.0, cos))
    return (1.0 - cos) / 2.0


def recompense_spectrale(mfcc_reference, mfcc_produit, tolerance: float = 0.5) -> float:
    """Convertit distance_spectrale en score [0,1], même forme linéaire continue que
    recompense_formants : max(0, 1 - d/tolerance). tolerance=0.5 (vs 0.35 pour les
    formants) car la distance cosinus sur MFCC est structurellement plus tassée — à
    recalibrer empiriquement sur les premières prises réelles."""
    d = distance_spectrale(mfcc_reference, mfcc_produit)
    return float(max(0.0, 1.0 - d / tolerance))


def recompense_vocale_mixte(formants_cibles: dict, formants_produits: dict,
                             mfcc_references: list = None, mfcc_produit=None,
                             poids_formants: float = POIDS_RECOMPENSE_FORMANTS,
                             poids_spectral: float = POIDS_RECOMPENSE_SPECTRALE) -> tuple:
    """Score acoustique final (décision utilisateur v27.0 : spectral + formants réels).
    Retourne (score_mixte, score_formants, score_spectral) — les trois pour la
    télémétrie, seul le premier pilote dopamine/promotion.

    score_mixte = poids_formants * score_formants + poids_spectral * score_spectral,
    avec poids_formants + poids_spectral == 1.0 donc score_mixte ∈ [0,1] — invariant
    STRUCTURANT : le score devient poids_vocal côté noyau.py, lui-même facteur du choc
    dopaminergique (DOPAMINE_MAX - d) * TAUX_CHOC_BASE * poids, qui suppose un poids
    borné dans [0,1].

    Quand mfcc_references est None ou vide (aucune prise en banque, repli `say`), le
    score spectral n'est PAS calculé et le score mixte se réduit EXACTEMENT à
    recompense_formants — rétrocompatibilité stricte avec tous les runs pré-v27.0.

    Sur plusieurs prises de référence : on prend le MAXIMUM des scores spectraux (pas
    la moyenne) — « ressembler à AU MOINS UNE prononciation valide de l'utilisateur »
    est le bon critère ; moyenner pénaliserait l'agent pour la variabilité naturelle
    entre les prises de l'utilisateur lui-même."""
    assert abs((poids_formants + poids_spectral) - 1.0) < 1e-9, \
        "poids_formants + poids_spectral doit valoir 1.0 (invariant score_mixte ∈ [0,1])"

    score_formants = recompense_formants(formants_cibles, formants_produits)

    if not mfcc_references or mfcc_produit is None:
        return score_formants, score_formants, 0.0

    score_spectral = max(recompense_spectrale(ref, mfcc_produit) for ref in mfcc_references)
    score_mixte = poids_formants * score_formants + poids_spectral * score_spectral
    return score_mixte, score_formants, score_spectral
