"""
Le Démon Cognitif (V21.0, expérimental) — La Cuve de Maintien.

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test") : il n'est PAS porté sur `agi_google_colab.py`. Il tourne
en arrière-plan indéfiniment et héberge le cerveau (`AGI_Naulthene` + tout son état
biologique/curriculum, voir `EtatCognitif` dans agi_local_test.py) au-delà de la durée
de vie d'un seul process d'entraînement.

Métabolisme à 3 états (voir readme.md, section "Le Cerveau Persistant en Cuve") :

  1. L'Éveil (connexion active) : `_vivre_connexion` traite un tick complet par
     paquet réseau reçu — la faim augmente, les synapses s'activent, la LTP opère.
  2. Le Sommeil (déconnexion, ou seuil de ticks atteint en session) : consolidation
     (apprentissage + rêve adaptatif + ressort dopaminergique + thermostat de
     neurogenèse + cycle_sommeil_global), puis sauvegarde sur disque.
  3. La Cryostase (attente) : `socket.accept()` bloque, CPU à 0%, le temps est
     suspendu pour l'agent tant qu'aucun corps ne se connecte.

Modèle de temps hybride (v21.0, décision utilisateur) : combiner "1 connexion = 1
nuit" ET "seuil de ticks" plutôt que choisir l'un ou l'autre.

  - PENDANT une session active longue, une nuit COMPLÈTE (apprentissage RL + rêve +
    ressort + neurogenèse + cycle_sommeil) se déclenche dès que `ticks_par_jour`
    ticks se sont accumulés depuis la dernière nuit — l'agent peut vivre plusieurs
    journées subjectives au sein d'une seule connexion longue.
  - À LA DÉCONNEXION : si assez de ticks se sont accumulés depuis la dernière nuit
    (>= SEUIL_NUIT_A_LA_DECONNEXION), on liquide une nuit complète avant de
    sauvegarder. Sinon (l'agent vient tout juste de dormir, ou la session était très
    courte), on se contente d'une MICRO-SIESTE : une simple photographie de l'état
    courant sur le disque, SANS relancer un cycle d'érosion/rêve à vide — c'est la
    protection contre l'"Alzheimer numérique" (l'agent ne s'érode pas en boucle sur
    des sessions courtes et répétées).
  - HORS CONNEXION (cryostase) : `traiter_tick` n'est jamais appelé, donc aucune
    jauge biologique ne bouge et aucune synapse ne s'érode — le métabolisme s'arrête
    net, protection contre la famine hors connexion.

⚠️ Limite assumée de cette itération (voir readme.md et le plan v21.0) : le VRAI code
de `traiter_tick`/`step_metabolisme`/`DetecteurRessourcesBiologiques` lit les internes
MiniGrid (`env.unwrapped.agent_pos`, `.grid`, positions des `Ball` Nourriture/Eau) pour
la biologie et la mémoire spatiale. Un client purement "pixels + action" ne peut pas
transmettre ça par un simple flux JSON sans étendre significativement le protocole. Pour
cette itération, l'environnement MiniGrid tourne donc CÔTÉ SERVEUR (dans la Cuve) — le
Corps reste jetable et sans intelligence (il ne fait que déclencher les ticks et choisir
le niveau), mais le moteur physique lui-même vit dans le process du daemon. Le
découplage total (env chez le client, protocole étendu pour transmettre grille/positions)
est noté comme évolution future, pas comme un correctif oublié.
"""

import json
import socket

import numpy as np
import torch

from agi_local_test import (
    traiter_tick, executer_nuit, demarrer_journee, ticks_par_jour, DEVICE,
)
from persistance import PersistanceAnatomique

# Fraction de `ticks_par_jour` en dessous de laquelle, À LA DÉCONNEXION, on ne
# déclenche qu'une micro-sieste (simple save) plutôt qu'une nuit complète — évite
# d'éroder/rêver sur une poignée de ticks vécus. Valeur par défaut proposée dans le
# plan v21.0 : la moitié d'une journée subjective.
FRACTION_SEUIL_NUIT_A_LA_DECONNEXION = 0.5


class CuveDeMaintien:
    """Le daemon qui héberge la Conscience. Un seul cerveau par Cuve, un seul client
    à la fois (le protocole ne prévoit pas de connexions concurrentes — un corps à la
    fois habite l'agent, comme un seul flux de conscience à la fois)."""

    def __init__(self, port=9999, fichier_cerveau="naulthene_v21.brain", activer_wandb=False):
        self.port = port
        self.persistance = PersistanceAnatomique(fichier=fichier_cerveau)
        self.seuil_nuit_a_la_deconnexion = max(1, int(ticks_par_jour * FRACTION_SEUIL_NUIT_A_LA_DECONNEXION))

        # --- Résurrection (ou naissance) ---
        self.etat = self.persistance.charger_ou_naitre()
        self.ticks_depuis_derniere_nuit = 0

        self.wandb_actif = activer_wandb
        if self.wandb_actif:
            import wandb
            wandb.init(project="Naulthene-AGI", name="Run_21_Cuve_Daemon")
            self._wandb = wandb
        else:
            self._wandb = None

    # ------------------------------------------------------------------
    # Cycle de vie principal
    # ------------------------------------------------------------------

    def demarrer(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', self.port))
        server.listen(1)

        print(f"🔮 Cuve activée sur le port {self.port}. Cerveau en Cryostase. "
              f"En attente de connexion...")

        try:
            while True:
                # ---> CRYOSTASE : bloque ici indéfiniment à 0% CPU <---
                client, adresse = server.accept()
                print(f"⚡ ÉVEIL ! Connexion du système nerveux périphérique : {adresse}")

                try:
                    self._vivre_connexion(client)
                finally:
                    client.close()

                # ---> SOMMEIL : l'environnement vient de se débrancher <---
                print("🌙 Perte du signal. Décision du régime de sommeil...")
                self._processus_nocturne()
                print("❄️ Cerveau replongé en Cryostase.")
        except KeyboardInterrupt:
            print("🛑 Arrêt du serveur demandé (Ctrl+C). Sauvegarde d'urgence...")
            self.persistance.sauvegarder(self.etat)
        finally:
            server.close()
            if self._wandb is not None:
                self._wandb.finish()

    # ------------------------------------------------------------------
    # Éveil
    # ------------------------------------------------------------------

    def _vivre_connexion(self, client):
        """Boucle de conscience active : perception → pensée → action, un tick complet
        par paquet réseau reçu. Le protocole côté Corps sert de déclencheur/heartbeat —
        c'est `etat.env` (côté Cuve) qui reste la source de vérité de l'observation
        réelle, voir la note de limite assumée en tête de fichier. On ne redémarre une
        `demarrer_journee` explicite qu'à la toute première connexion vécue par ce
        process (l'état a déjà `etat_courant` sinon, restauré par la persistance ou
        laissé par la session précédente)."""
        if self.etat.etat_courant is None:
            demarrer_journee(self.etat)

        while True:
            data = client.recv(16384)
            if not data:
                break  # le corps s'est déconnecté

            try:
                perception = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError:
                continue  # paquet corrompu/partiel, on ignore plutôt que de planter la Cuve

            # --- Ouverture du verrou v22.0 (voir plan v22.0, Étape 5) : jusqu'ici la
            # Cuve ignorait tout le contenu du paquet reçu (limite assumée v21.0, voir
            # note en tête de fichier). L'audio est le premier canal réellement transmis
            # — 'audio' (le son brut MFCC seul depuis v22.1, DIM_AUDIO_ENTREE dims — voir
            # correctif défaut 2 dans CONCEPTION_v22_audio.md, l'embedding sémantique
            # n'entre plus dans l'oreille) et 'formants_cibles' (dict F1/F2, présent
            # seulement pendant une leçon vocale pilotée par client_professeur.py, injecté
            # dans le vecteur bio comme une quête plutôt que dans l'audio) sont optionnels :
            # absents, le tick se comporte exactement comme avant v22.0 (silence, pas de
            # récompense vocale).
            obs_auditive = None
            audio_brut = perception.get('audio')
            if audio_brut is not None:
                obs_auditive = torch.tensor([audio_brut], dtype=torch.float32, device=DEVICE)
            formants_cibles = perception.get('formants_cibles')

            infos_tick = traiter_tick(self.etat, obs_auditive=obs_auditive, formants_cibles=formants_cibles)
            self.ticks_depuis_derniere_nuit += 1

            reponse = {
                'action': infos_tick['action'],
                'infos_internes': infos_tick['infos_internes'],
                'tick_absolu': self.etat.tick_absolu,
            }
            client.sendall(json.dumps(reponse).encode('utf-8'))

            # --- Nuit complète IN-SESSION dès qu'une journée subjective est vécue ---
            # L'agent peut ainsi traverser plusieurs "journées" au sein d'une seule
            # connexion longue, sans attendre la déconnexion pour consolider.
            if self.ticks_depuis_derniere_nuit >= ticks_par_jour:
                print(f"   🌒 Journée subjective complète ({ticks_par_jour} ticks) — "
                      f"nuit in-session.")
                self._executer_nuit_complete()
                demarrer_journee(self.etat)

    # ------------------------------------------------------------------
    # Sommeil
    # ------------------------------------------------------------------

    def _executer_nuit_complete(self):
        """Le rituel d'extinction complet : apprentissage + rêve adaptatif + ressort
        dopaminergique + thermostat de neurogenèse + cycle_sommeil_global (tout ce que
        fait `executer_nuit` dans agi_local_test.py), puis cristallisation sur disque."""
        log = executer_nuit(self.etat)
        if self._wandb is not None:
            self._wandb.log(log)
        self.persistance.sauvegarder(self.etat)
        self.ticks_depuis_derniere_nuit = 0

    def _processus_nocturne(self):
        """Appelée à CHAQUE déconnexion. Décide entre nuit complète et micro-sieste
        selon combien de ticks se sont accumulés depuis la dernière nuit (in-session ou
        précédente déconnexion) :

          - Assez de ticks vécus (>= seuil_nuit_a_la_deconnexion) → une vraie nuit
            n'a pas encore eu lieu pour cette portion de vécu : on la liquide avant de
            sauvegarder, exactement comme la fin de journée du mode standalone.
          - Trop peu de ticks (l'agent vient de dormir en session, ou la connexion a
            été très courte) → MICRO-SIESTE : simple sauvegarde de l'état courant, sans
            ré-éroder/rejouer un cerveau qui n'a presque rien vécu depuis sa dernière
            vraie nuit. Protection explicite contre l'érosion en boucle à vide."""
        if self.ticks_depuis_derniere_nuit >= self.seuil_nuit_a_la_deconnexion:
            print(f"   🌕 {self.ticks_depuis_derniere_nuit} ticks vécus depuis la dernière nuit "
                  f"(seuil: {self.seuil_nuit_a_la_deconnexion}) — nuit complète.")
            self._executer_nuit_complete()
        else:
            print(f"   🌗 Micro-sieste ({self.ticks_depuis_derniere_nuit} ticks vécus, "
                  f"sous le seuil de {self.seuil_nuit_a_la_deconnexion}) — simple cristallisation, "
                  f"pas d'érosion ni de rêve pour préserver le cerveau.")
            self.persistance.sauvegarder(self.etat)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cuve de Maintien — daemon persistant Naulthène AGI (v21.0)")
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument("--brain", type=str, default="naulthene_v21.brain")
    parser.add_argument("--wandb", action="store_true", help="Active le logging W&B (désactivé par défaut)")
    args = parser.parse_args()

    cuve = CuveDeMaintien(port=args.port, fichier_cerveau=args.brain, activer_wandb=args.wandb)
    cuve.demarrer()
