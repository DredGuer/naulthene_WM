"""
Le Tuteur de Parole (V22.0, expérimental) — le Corps auditif temps réel.

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test"), pas encore porté sur `agi_google_colab.py`. Voir
CONCEPTION_v22_audio.md et le plan v22.0 pour le contexte narratif complet.

Symétrique à `client_corps.py` (le Corps MiniGrid) mais pour l'oreille/la bouche :
un client jetable, sans intelligence propre, qui se connecte à la même Cuve
(`daemon_cerveau.py`) et orchestre une LEÇON DE PAROLE :

  1. Gemma (via `professeur_gemma.choisir_lecon`) annonce la cible du palier courant
     (ex: la voyelle "a").
  2. Une référence audio est produite — soit par `say` (macOS TTS, déterministe et
     rapide), soit par toi au micro (`hemisphere_audio.capture_micro`).
  3. Cette référence est encodée (MFCC ⊕ embedding sémantique) et envoyée à la Cuve à
     CHAQUE tick de la leçon, avec `formants_cibles` (les formants attendus pour la
     voyelle visée) — c'est ce qui ouvre le verrou décrit dans le plan v22.0 (Étape 5).
  4. La Cuve répond avec `parametres_vocaux` (les 8 params produits par `tete_vocale`) —
     synthétisés et JOUÉS IMMÉDIATEMENT dans les haut-parleurs (exigence explicite de
     l'utilisateur : entendre le babil en temps réel, dès qu'il est produit).
  5. À la fin de la leçon (N ticks), un bilan est affiché ; toutes les
     `LECONS_AVANT_JUGEMENT_GEMMA` leçons, Gemma est appelé pour un jugement qualitatif
     périodique (voir professeur_gemma.py — pas par tick, ~8-30s de latence mesurée).

Usage :
    python client_professeur.py --palier 2 --ticks 100
    python client_professeur.py --palier 2 --ticks 100 --micro   # ta voix au lieu de `say`
"""

import argparse
import json
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np

from hemisphere_audio import (
    SynthetiseurFormants, extraire_mfcc, jouer_son_temps_reel,
    capture_micro, transcrire_whisper, VOYELLES_CIBLES, SAMPLE_RATE,
)
import professeur_gemma as pg

LECONS_AVANT_JUGEMENT_GEMMA = 1  # périodicité du jugement qualitatif (voir professeur_gemma.py :
                                  # Gemma prend ~8-30s, jamais appelé par tick)


def _reference_via_say(mot: str) -> np.ndarray:
    """Génère l'audio de référence via `say` (macOS TTS, déjà installé/confirmé
    fonctionnel — voir CONCEPTION_v22_audio.md §5). Déterministe et instantané,
    contrairement à demander à l'utilisateur de parler à chaque tick."""
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


def _encoder_perception_audio(onde_reference: np.ndarray, mot: str) -> list:
    """v22.1 (correctif défaut 2, voir CONCEPTION_v22_audio.md) : porte_auditive ne
    reçoit plus QUE le son brut (MFCC, DIM_AUDIO_ENTREE=DIM_MFCC) — l'embedding
    sémantique du mot n'entre plus dans l'oreille (il aurait court-circuité l'écoute
    réelle, l'agent ignorant le son pour ne se fier qu'au concept). Le paramètre `mot`
    est conservé pour compatibilité de signature et un usage futur éventuel (v23+, voir
    Question ouverte B du plan v22.1), mais n'est plus utilisé ici."""
    return extraire_mfcc(onde_reference, sample_rate=SAMPLE_RATE).tolist()


def lancer_lecon_parole(host="127.0.0.1", port=9999, palier=1, duree_ticks=100,
                          utiliser_micro=False, delai_entre_ticks=0.5):
    """Orchestre une leçon de parole complète sur `duree_ticks` ticks, connectée à la
    Cuve. `delai_entre_ticks` (0.5s par défaut, contrairement à client_corps.py qui va
    "aussi vite que possible") laisse le temps d'ENTENDRE chaque son produit avant le
    suivant — le babillage n'a pas besoin d'être aussi rapide qu'un tick MiniGrid."""
    lecon = pg.choisir_lecon(palier)
    mot_cible = lecon["cible"] or "a"  # palier 1 (Vocaliser) n'a pas de cible précise, on utilise 'a' comme référence
    print(f"🎓 Leçon de parole — Palier {lecon['palier']} : {lecon['nom']} (cible: \"{mot_cible}\")")

    formants_cibles = VOYELLES_CIBLES.get(mot_cible)
    if formants_cibles is None:
        # Syllabes/mots (paliers 7+) : pas de cible F1/F2 simple dans VOYELLES_CIBLES —
        # on retombe sur la voyelle dominante du mot pour garder une récompense par
        # tick exploitable (le jugement fin revient à Gemma en périodique, voir §6).
        premiere_voyelle = next((c for c in mot_cible if c in VOYELLES_CIBLES), "a")
        formants_cibles = VOYELLES_CIBLES[premiere_voyelle]
        print(f"   (pas de cible formants directe pour \"{mot_cible}\", "
              f"utilisation de la voyelle dominante \"{premiere_voyelle}\")")

    if utiliser_micro:
        print("🎤 Prononce le mot/son cible au micro (2 secondes)...")
        onde_reference = capture_micro(duree=2.0, sample_rate=SAMPLE_RATE)
    else:
        onde_reference = _reference_via_say(mot_cible)
    print(f"🔊 Référence ({'micro' if utiliser_micro else 'say'}) : {len(onde_reference)/SAMPLE_RATE:.2f}s")

    perception_audio = _encoder_perception_audio(onde_reference, mot_cible)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    print(f"🧠 Connexion au Cerveau Naulthène réussie ! ({host}:{port}) — mode leçon de parole")

    synth = SynthetiseurFormants()
    scores = []
    interrompu = False

    try:
        for tick in range(duree_ticks):
            paquet = {
                'tick_client': tick,
                'vision': [],
                'audio': perception_audio,
                'formants_cibles': formants_cibles,
                'recompense_environnement': 0.0,
                'fin_episode': False,
            }
            try:
                client.sendall(json.dumps(paquet).encode('utf-8'))
                data = client.recv(16384)
            except KeyboardInterrupt:
                interrompu = True
                print("\n🛑 Arrêt demandé (Ctrl+C) — attente de la fin du tick en cours côté Cuve...")
                try:
                    client.settimeout(30.0)
                    data = client.recv(16384)
                except (socket.timeout, OSError):
                    data = b""
                break

            if not data:
                print("🔌 La Cuve a fermé la connexion en premier.")
                break

            reponse = json.loads(data.decode('utf-8'))
            infos = reponse.get('infos_internes', {})
            vecteur_vocal = infos.get('parametres_vocaux')

            if vecteur_vocal:
                # LA BOUCHE en action : synthèse + lecture IMMÉDIATE (temps réel,
                # exigence explicite utilisateur "je veux entendre ce qu'il dit en
                # temps réel dès qu'il le fait").
                onde_produite = synth.synthetiser(vecteur_vocal)
                jouer_son_temps_reel(onde_produite, sample_rate=SAMPLE_RATE, bloquant=True)

                formants_produits = synth.parametres_depuis_vecteur(vecteur_vocal)
                from hemisphere_audio import recompense_formants
                score = recompense_formants(formants_cibles, formants_produits)
                scores.append(score)
                barre = "█" * int(score * 20)
                print(f"   tick {tick:4d} — score formants: {score:.3f} {barre}")

            try:
                if delai_entre_ticks > 0:
                    time.sleep(delai_entre_ticks)
            except KeyboardInterrupt:
                # Bug corrigé : un Ctrl+C pendant cette pause (hors de l'échange
                # réseau) n'était rattrapé par AUCUN except — il remontait tel quel et
                # crashait le client avec une traceback, sans bilan ni fermeture
                # propre. On le traite maintenant exactement comme un Ctrl+C pendant
                # sendall/recv : on sort proprement de la boucle vers le bilan de fin.
                interrompu = True
                print("\n🛑 Arrêt demandé (Ctrl+C).")
                break

    finally:
        client.close()

    if scores:
        score_moyen = float(np.mean(scores))
        print(f"\n📊 Bilan de la leçon : score moyen = {score_moyen:.3f} sur {len(scores)} ticks vocalisés")

        if not interrompu:
            print("🧑‍🏫 Jugement qualitatif du Professeur Gemma (peut prendre 10-30s)...")
            # Transcrit le dernier son produit pour donner à Gemma quelque chose de
            # concret à juger (Gemma n'entend pas le .wav directement, voir
            # professeur_gemma.py et CONCEPTION_v22_audio.md §6).
            dernier_son = synth.synthetiser(vecteur_vocal) if vecteur_vocal else np.zeros(1600, dtype=np.float32)
            try:
                transcription = transcrire_whisper(dernier_son, sample_rate=SAMPLE_RATE)
            except Exception as e:
                transcription = f"(transcription indisponible: {e})"
            jugement = pg.juger_qualitatif(mot_cible, transcription, score_moyen)
            print(f"   Score Gemma: {jugement['score']:.2f} — {jugement['commentaire']}")
    else:
        print("\n⚠️  Aucun tick vocalisé (déconnexion précoce ?)")

    print("✅ Leçon terminée." + (" (interrompue par Ctrl+C)" if interrompu else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tuteur de parole — client de leçon vocale Naulthène (v22.0)")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument("--palier", type=int, default=1, help="Palier du curriculum vocal (voir professeur_gemma.CURRICULUM_VOCAL)")
    parser.add_argument("--ticks", type=int, default=100, help="Nombre de ticks de la leçon")
    parser.add_argument("--micro", action="store_true", help="Utilise ton micro comme référence au lieu de `say`")
    parser.add_argument("--delai", type=float, default=0.5, help="Délai (s) entre deux ticks, pour laisser le temps d'écouter")
    args = parser.parse_args()

    lancer_lecon_parole(host=args.host, port=args.port, palier=args.palier,
                          duree_ticks=args.ticks, utiliser_micro=args.micro,
                          delai_entre_ticks=args.delai)
