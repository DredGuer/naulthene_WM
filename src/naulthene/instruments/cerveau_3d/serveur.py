# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
VIS-01 — le serveur du cerveau 3D : sert la page, pousse les trames, écoute l'UDP.

⚠️ Bibliothèque standard UNIQUEMENT (`http.server`, `socket`, `json`, `base64`) : aucune
dépendance n'est ajoutée au projet (spec §3). Le serveur ne connaît pas le cerveau : il ne
connaît que le `BusTrames` qu'on lui donne.

⚠️ Ne PAS activer HTTP/1.1 : le flux SSE n'a ni `Content-Length` ni `chunked`, et un client
HTTP/1.1 attendrait une fin de corps qui n'arrive jamais. En HTTP/1.0 (défaut), le corps se
termine à la fermeture de la connexion — exactement ce qu'est un flux continu.

⚠️ Le serveur est en LECTURE SEULE sur le bus : il ne publie rien, ne bloque rien, et un
navigateur qui disparaît (onglet fermé) ne remonte jamais dans le cerveau.
"""
from __future__ import annotations

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from naulthene.cerveau.telemetrie import deserialiser

TAILLE_MAX_DATAGRAMME = 65535       # plafond théorique d'un datagramme UDP
CADENCE_SSE = 0.05                  # 20 Hz de vérification ; le throttle réel est côté rapporteur


class ServeurCerveau3D:
    """Sert la page 3D et pousse les trames en SSE."""

    def __init__(self, bus, port=8770, hote="127.0.0.1", dossier_statique=None):
        self.bus = bus
        self.hote = hote
        self.dossier_statique = Path(dossier_statique or (Path(__file__).parent / "static"))
        self._serveur = ThreadingHTTPServer((hote, int(port)), self._fabriquer_gestionnaire())
        self._serveur.daemon_threads = True
        self.port = self._serveur.server_address[1]   # port RÉEL : `port=0` en choisit un libre
        self._arret = threading.Event()
        self._fil = None

    def _fabriquer_gestionnaire(self):
        serveur = self

        class Gestionnaire(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass   # pas de bruit dans la console d'un run en cours

            def do_GET(self):
                chemin = urlsplit(self.path).path
                if chemin == "/":
                    return self._fichier("index.html", "text/html; charset=utf-8")
                if chemin in ("/app.js", "/three.module.js"):
                    return self._fichier(chemin.lstrip("/"), "text/javascript; charset=utf-8")
                if chemin == "/structure":
                    return self._json(serveur.bus.structure() or {})
                if chemin == "/sante":
                    return self._json({"bus": serveur.bus.compteurs()})
                if chemin == "/flux":
                    return self._flux()
                self.send_error(404)

            def _fichier(self, nom, type_mime):
                fichier = serveur.dossier_statique / nom
                if not fichier.is_file():
                    return self.send_error(404, f"{nom} absent du dossier statique")
                donnees = fichier.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", type_mime)
                self.send_header("Content-Length", str(len(donnees)))
                self.end_headers()
                self.wfile.write(donnees)

            def _json(self, charge):
                donnees = json.dumps(charge, separators=(",", ":")).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(donnees)))
                self.end_headers()
                self.wfile.write(donnees)

            def _pousser_structure(self, sequence_vue):
                """Pousse la structure si le compteur du bus a bougé ; rend le compteur à retenir.

                ⚠️ Le compteur est lu AVANT la trame, jamais après : si une seconde structure est
                publiée entre les deux lectures, on la repousse une fois de trop (le client
                reconstruit deux fois sa scène) plutôt que de la MANQUER — une scène périmée est
                exactement le défaut que ce compteur existe pour éviter (spec §9 : la neurogenèse
                change `dim_bus`, le client reconstruit).
                """
                courante = serveur.bus.sequence_structure
                if courante == sequence_vue:
                    return sequence_vue
                structure = serveur.bus.structure()
                if structure is None:
                    return sequence_vue
                self._evenement_sse("structure", structure)
                return courante

            def _flux(self):
                """SSE : la structure d'abord (le client peut se dessiner), puis chaque nouvelle
                activité. Un navigateur qui ferme l'onglet casse le `write` — on sort sans bruit,
                le cerveau n'en sait rien."""
                try:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                    self.send_header("Cache-Control", "no-cache")
                    self.end_headers()

                    # 1. La structure AVANT toute activité : on ne dessine rien avant de savoir
                    #    combien de neurones il y a. On attend qu'il en existe une.
                    sequence_structure = -1
                    while not serveur._arret.is_set():
                        sequence_structure = self._pousser_structure(sequence_structure)
                        if sequence_structure >= 0:
                            break
                        time.sleep(CADENCE_SSE)

                    # 2. Puis l'activité (dernière trame seulement : on saute des images plutôt
                    #    que d'accumuler du passé), les événements, et CHAQUE changement de
                    #    structure (neurogenèse).
                    derniere_sequence = -1
                    dernier_evenement = 0
                    while not serveur._arret.is_set():
                        sequence_structure = self._pousser_structure(sequence_structure)
                        if serveur.bus.sequence != derniere_sequence:
                            activite = serveur.bus.activite()
                            if activite is not None:
                                derniere_sequence = serveur.bus.sequence
                                self._evenement_sse("activite", activite)
                        nouveaux, dernier_evenement = serveur.bus.evenements_depuis(dernier_evenement)
                        for evenement in nouveaux:
                            self._evenement_sse("evenement", evenement)
                        time.sleep(CADENCE_SSE)
                except (BrokenPipeError, ConnectionResetError, OSError):
                    return

            def _evenement_sse(self, nom, charge):
                corps = f"event: {nom}\ndata: {json.dumps(charge, separators=(',', ':'))}\n\n"
                self.wfile.write(corps.encode("utf-8"))
                self.wfile.flush()

        return Gestionnaire

    def demarrer_en_thread(self):
        self._fil = threading.Thread(target=self._serveur.serve_forever,
                                     name="serveur-cerveau-3d", daemon=True)
        self._fil.start()
        return self._fil

    def arreter(self):
        self._arret.set()
        self._serveur.shutdown()
        self._serveur.server_close()
        if self._fil is not None:
            self._fil.join(timeout=2.0)


class EcouteurUDP:
    """Reçoit les trames d'un run extérieur (étape 2). Un datagramme illisible est COMPTÉ et
    ignoré : la boucle d'écoute ne meurt jamais d'une entrée malformée (spec §9)."""

    def __init__(self, bus, port=9998, hote="127.0.0.1"):
        self.bus = bus
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((hote, int(port)))
        self._socket.settimeout(0.2)     # pour pouvoir s'arrêter proprement
        self.port = self._socket.getsockname()[1]
        self._arret = threading.Event()
        self._recues, self._ignorees = 0, 0
        self._fil = None

    def _boucle(self):
        while not self._arret.is_set():
            try:
                octets, _ = self._socket.recvfrom(TAILLE_MAX_DATAGRAMME)
            except socket.timeout:
                continue
            except OSError:
                break
            trame = deserialiser(octets)
            if trame is None:
                self._ignorees += 1
                continue
            self._recues += 1
            genre = trame.get("type")
            if genre == "structure":
                self.bus.publier_structure(trame)
            elif genre == "activite":
                self.bus.publier_activite(trame)
            elif genre == "evenement":
                self.bus.publier_evenement(trame)

    def demarrer_en_thread(self):
        self._fil = threading.Thread(target=self._boucle, name="ecouteur-udp", daemon=True)
        self._fil.start()
        return self._fil

    def arreter(self):
        self._arret.set()
        if self._fil is not None:
            self._fil.join(timeout=2.0)
        try:
            self._socket.close()
        except OSError:
            pass

    def compteurs(self):
        return {"recues": self._recues, "ignorees": self._ignorees, "port": self.port}
