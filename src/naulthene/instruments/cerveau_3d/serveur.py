# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
VIS-01 — le serveur du cerveau 3D : sert la page, pousse les trames, écoute l'UDP.

⚠️ Bibliothèque standard UNIQUEMENT (`http.server`, `socket`, `json`, `stat`, `threading`,
`time`, `pathlib`, `urllib.parse`) : aucune dépendance n'est ajoutée au projet (spec §3). Le
serveur ne connaît pas le cerveau : il ne connaît que le `BusTrames` qu'on lui donne.

⚠️ Rétractation du 10/09/2026 (vague finale, constat I7 — nit) : cet énoncé citait `base64`
parmi les modules utilisés. **C'était faux** : `base64` n'est ni importé ni utilisé ici (il l'est
dans `telemetrie.py`, qui encode les matrices de poids). Remplacé par la liste RÉELLE des
imports, pour que la phrase reste vérifiable en trois lignes.

⚠️ Ne PAS activer HTTP/1.1 : le flux SSE n'a ni `Content-Length` ni `chunked`, et un client
HTTP/1.1 attendrait une fin de corps qui n'arrive jamais. En HTTP/1.0 (défaut), le corps se
termine à la fermeture de la connexion — exactement ce qu'est un flux continu.

⚠️ Le serveur est en LECTURE SEULE sur le bus : il ne publie rien, ne bloque rien, et un
navigateur qui disparaît (onglet fermé) ne remonte jamais dans le cerveau.

⚠️ Les deux SOURCES de l'étape 2 vivent ici, et aucune n'appartient au serveur HTTP : `EcouteurUDP`
reçoit `activite` et `evenement` (datagrammes), `VeilleurStructureFichier` relit la trame
`structure` dans son FICHIER — elle ne peut pas passer par UDP (305 086 octets mesurés contre un
plafond dur de 65 507), et personne ne lisait ce fichier avant la tâche 11 : la page restait sur
« en attente de la structure… ».

⚠️ Invariant d'ÉMISSION (ruling de revue — I1) : AUCUN corps JSON servi (`/structure`,
`/sante`, `/flux`) ne peut contenir un littéral `NaN`/`Infinity`, que `JSON.parse` rejette.
Tout passe par `assainir_json` (une valeur non finie devient `null`), et `allow_nan=False`
reste en ceinture à l'intérieur des `try/except` — un `ValueError` n'est pas un `OSError` :
non rattrapé, il tuerait le fil de gestion.

⚠️ Invariant de ROBUSTESSE DU PARSING (constat I4, vague finale) : un datagramme n'est JAMAIS
une entrée de confiance. `deserialiser` (`telemetrie.py`) rattrape `RecursionError` en plus des
erreurs de décodage, et les deux ceintures d'émission ci-dessus rattrapent `RecursionError` en
plus de `ValueError`/`TypeError` — parce qu'`assainir_json` est RÉCURSIF : mesuré, une charge
imbriquée à 1 000 niveaux franchit `json.loads` (donc `deserialiser`) et le fait lever. Sans ces
trois filets, le fil `ecouteur-udp` ou le fil de gestion mourait **sans message ni compteur**.
"""
from __future__ import annotations

import json
import math
import os
import socket
import stat
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from naulthene.cerveau.telemetrie import deserialiser

TAILLE_MAX_DATAGRAMME = 65535       # plafond théorique d'un datagramme UDP
CADENCE_SSE = 0.05                  # 20 Hz de vérification ; le throttle réel est côté rapporteur


def assainir_json(charge):
    """Rend `charge` sérialisable : toute valeur NON FINIE devient `None` (`null`).

    ⚠️ Ruling de revue (I1) : c'est le SEUL chemin d'assainissement, partagé par `_json`
    (`/structure`, `/sante`) et par `_evenement_sse` — jamais deux sérialisations différentes.

    Pourquoi c'est nécessaire : `json.loads` — donc `deserialiser`, donc l'écouteur UDP de
    cette tâche — ACCEPTE les littéraux `NaN`/`Infinity`. `serialiser` ne protège que
    l'ÉMETTEUR : un `NaN` reçu par UDP arrive donc TEL QUEL dans le bus, et ressortait TEL
    QUEL sur le fil. `JSON.parse` rejette `data: {"dopamine":NaN}` : la page tombait au lieu
    d'afficher un cerveau dans un état inattendu (spec §9). Devenu `null`, le cerveau est
    affiché comme tel — même ruling qu'un poids non fini traité comme ABSENT (tâche 1) — et
    le serveur, lui, garde la trace du défaut (compteur `emissions_refusees`).

    La conversion est RÉCURSIVE (dicts et listes, à toute profondeur) ; les autres scalaires
    (`int`, `str`, `bool`, `None`) sont rendus tels quels, et les clés ne sont pas touchées.
    """
    if isinstance(charge, float):                      # `bool` n'est pas un `float` : intact
        return charge if math.isfinite(charge) else None
    if isinstance(charge, dict):
        return {cle: assainir_json(valeur) for cle, valeur in charge.items()}
    if isinstance(charge, (list, tuple)):
        return [assainir_json(valeur) for valeur in charge]
    return charge


class ServeurCerveau3D:
    """Sert la page 3D et pousse les trames en SSE."""

    def __init__(self, bus, port=8770, hote="127.0.0.1", dossier_statique=None,
                 veilleur_structure=None):
        self.bus = bus
        self.hote = hote
        self.dossier_statique = Path(dossier_statique or (Path(__file__).parent / "static"))
        self._veilleur_structure = veilleur_structure   # purement OBSERVÉ (`/sante`), jamais piloté
        self._serveur = ThreadingHTTPServer((hote, int(port)), self._fabriquer_gestionnaire())
        self._serveur.daemon_threads = True
        self.port = self._serveur.server_address[1]   # port RÉEL : `port=0` en choisit un libre
        self._arret = threading.Event()
        self._fil = None
        self._ferme = False              # `arreter()` idempotent (ruling I2)
        self._emissions_refusees = 0     # ceinture stricte : trames non sérialisables SAUTÉES

    def _fabriquer_gestionnaire(self):
        serveur = self

        class Gestionnaire(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass   # pas de bruit dans la console d'un run en cours

            def do_GET(self):
                chemin = urlsplit(self.path).path
                if chemin == "/":
                    return self._fichier("index.html", "text/html; charset=utf-8")
                # ⚠️ `/three.core.min.js` (tâche 5) : le vendor de three.js v0.180.0 n'est PAS un
                # fichier unique — `three.module.min.js` (338 908 octets, le fichier épinglé par le
                # plan) importe statiquement son core (381 124 octets : `Color`, `InstancedMesh`,
                # `Scene`…). Servir le seul fichier pinné fait répondre 404 sur le core, et la page
                # ne s'affiche jamais — défaut mesuré le 10/09/2026, cf. rapport de la tâche 5.
                if chemin in ("/app.js", "/three.module.js", "/three.core.min.js"):
                    return self._fichier(chemin.lstrip("/"), "text/javascript; charset=utf-8")
                if chemin == "/structure":
                    return self._json(serveur.bus.structure() or {})
                if chemin == "/sante":
                    return self._json(serveur._sante())
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
                try:
                    donnees = json.dumps(assainir_json(charge), separators=(",", ":"),
                                         allow_nan=False).encode("utf-8")
                except (ValueError, TypeError, RecursionError) as erreur:
                    # Ceinture : `assainir_json` rend ce chemin inatteignable pour une VALEUR
                    # non finie ; il reste une clé flottante non finie, que `allow_nan=False`
                    # refuse. L'échec est COMPTÉ et rendu visible (500), jamais silencieux.
                    # ⚠️ `RecursionError` (constat I4, vague finale) : `assainir_json` est
                    # RÉCURSIF, et une charge profondément imbriquée le fait lever — mesuré,
                    # 1 000 niveaux passent `json.loads` (donc `deserialiser`) et le font lever.
                    serveur._emissions_refusees += 1
                    return self.send_error(500, f"charge non serialisable : {erreur}")
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

                    # Le curseur des FAITS part du total COURANT, jamais de `0` (ruling de la
                    # tâche 5) : la file d'événements est bornée mais non vide, si bien qu'un
                    # client NEUF — un rechargement de page, un second onglet — recevait tout le
                    # tampon du passé et racontait à nouveau des faits déjà consommés. Un client
                    # neuf regarde le PRÉSENT ; ce qui est publié après sa connexion, en revanche,
                    # lui appartient (d'où la lecture ICI, avant l'attente de la structure).
                    dernier_evenement = serveur.bus.compteurs()["evenements_total"]

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
                """Un événement SSE — sérialisation STRICTE, mais l'échec ne tue pas le fil.

                `assainir_json` a déjà remplacé toute valeur non finie par `null` ; le
                `allow_nan=False` qui suit est la CEINTURE, et il est DANS un `try/except`
                parce qu'un `ValueError` n'est pas un `OSError` : laissé filer, il sortait de
                la boucle de `_flux`, tuait le fil de gestion et se rejouait à chaque
                reconnexion tant que la trame polluée restait dans le bus. Ici la trame est
                SAUTÉE et COMPTÉE, et le flux continue de servir les suivantes. (`TypeError`
                est rattrapé de même : un scalaire non sérialisable publié en mémoire — le cas
                `np.float32` de la spec §4 — ne doit pas tuer le fil non plus.)

                ⚠️ `RecursionError` AJOUTÉ le 10/09/2026 (constat I4, vague finale) — et ce n'est
                pas une ceinture de confort : `assainir_json` est RÉCURSIF, et il existe une
                fenêtre MESURÉE où `json.loads` accepte une charge que lui refuse (1 000 niveaux
                d'imbrication passent le parseur, 800 passent les deux). Une telle trame franchit
                donc `deserialiser`, entre dans le bus, et tuait le fil de gestion à la première
                connexion — le même mode d'échec silencieux que le constat I4 dénonce côté écoute.
                """
                try:
                    charge_propre = json.dumps(assainir_json(charge), separators=(",", ":"),
                                               allow_nan=False)
                except (ValueError, TypeError, RecursionError):
                    serveur._emissions_refusees += 1
                    return
                corps = f"event: {nom}\ndata: {charge_propre}\n\n"
                self.wfile.write(corps.encode("utf-8"))
                self.wfile.flush()

        return Gestionnaire

    def _sante(self) -> dict:
        """Les compteurs de santé — le bus, les émissions refusées, et l'état du fichier.

        ⚠️ Le bloc `structure_fichier` n'apparaît QUE si un veilleur a été fourni : une clé
        toujours présente et toujours `null` ferait croire à un fichier surveillé qui ne
        répond pas. Quand il est là, il dit le chemin, les publications et les ÉCHECS
        (absences, lectures impossibles, JSON invalide) — c'est ce qui distingue « la page
        attend un run » de « la page attend un fichier qu'on ne sait pas lire ».
        """
        charge = {"bus": self.bus.compteurs(),
                  "emissions_refusees": self._emissions_refusees}
        if self._veilleur_structure is not None:
            charge["structure_fichier"] = self._veilleur_structure.compteurs()
        return charge

    def demarrer_en_thread(self):
        self._fil = threading.Thread(target=self._serveur.serve_forever,
                                     name="serveur-cerveau-3d", daemon=True)
        self._fil.start()
        return self._fil

    def arreter(self):
        """Arrête le serveur — SÛR sur les DEUX chemins (jamais démarré / démarré) et IDEMPOTENT.

        ⚠️ Ruling de revue (I2) : `shutdown()` attend un événement que seul `serve_forever()`
        arme. Appelé sans démarrage, il bloque INDÉFINIMENT — et `server_close()` n'est alors
        jamais atteint, si bien que le socket d'écoute RESTE LIÉ. On ne l'appelle donc que si
        le fil de service tourne VRAIMENT (`is_alive()`, et non `is not None` : après un
        premier `arreter()`, ou après la fin du fil, `shutdown()` n'a plus rien à attendre) ;
        le socket est libéré dans TOUS les cas, et un second appel ne fait rien de plus.
        (L'idempotence est garantie pour des appels SÉQUENTIELS : deux `arreter()` simultanés
        ne sont pas un cas d'usage — le serveur est local, piloté par un seul appelant.)
        """
        self._arret.set()          # les flux SSE ouverts sortent de leur boucle au prochain tour
        if self._ferme:
            return
        self._ferme = True
        if self._fil is not None and self._fil.is_alive():
            self._serveur.shutdown()
            self._fil.join(timeout=2.0)
        self._serveur.server_close()


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


# --- Le veilleur du FICHIER de structure (tâche 11 — la seconde moitié de l'avenant) ---------

CADENCE_VEILLE_STRUCTURE = 1.0     # une relecture par seconde : la neurogenèse est rare
TAILLE_MAX_STRUCTURE = 64 << 20    # 64 Mio — très au-dessus d'une trame (305 Ko), très en
                                   # dessous d'un `.brain` (qu'on ne doit pas lire par erreur)


class VeilleurStructureFichier:
    """Publie dans le bus la trame `structure` qu'un run écrit dans un FICHIER.

    🔴 POURQUOI CE FICHIER, ET POURQUOI CE LECTEUR. La trame `structure` mesure 305 086 octets à
    `dim_bus = 145` pour un plafond DUR de 65 507 octets par datagramme UDP : elle ne peut pas
    passer par le réseau (avenant de protocole du 10/09/2026). Le run l'écrit donc à côté du
    `.brain` (`<brain>.vis01_structure.json`, écriture ATOMIQUE — fichier temporaire puis
    `os.replace`) au montage et après CHAQUE neurogenèse. L'ÉMETTEUR était fait ; PERSONNE ne
    lisait le fichier : `GET /structure` rendait `{}` et la page restait indéfiniment sur « en
    attente de la structure… ». C'est la moitié manquante de l'étape 2 que ce lecteur ferme.

    ⚠️ IL VIT DANS SON PROPRE FIL DE VEILLE (`daemon`), à BASSE FRÉQUENCE (1 Hz par défaut) : le
    serveur ne fait AUCUN accès disque sur sa voie chaude (la boucle SSE, le fil de gestion), donc
    un fichier lent, énorme ou inaccessible ne ralentit ni le flux ni les requêtes HTTP. La
    relecture est déclenchée par la SIGNATURE du fichier — `(mtime en nanosecondes, taille)`, lue
    par `stat()`, jamais par une lecture périodique : l'écriture étant atomique, `mtime_ns` change
    à chaque publication de l'émetteur, et une signature identique veut dire « rien de neuf », pas
    « peut-être ». (Un fichier recopié en conservant `mtime` serait donc manqué : c'est un cas
    qu'aucun émetteur réel ne produit, et le prix d'une relecture systématique — 305 Ko par
    seconde — ne vaut pas d'être payé pour lui.)

    ⚠️ AUCUNE EXCEPTION NE REMONTE, JAMAIS (exigence n°4 du brief) : fichier ABSENT, ILLISIBLE
    (permissions, chemin qui n'est pas un fichier ordinaire) ou MALFORMÉ (JSON cassé, JSON valide
    qui n'est pas une trame `structure`), l'anomalie est COMPTÉE, la dernière structure valide
    RESTE publiée, et la page garde son message d'attente. Même discipline que
    `EcouteurUDP._boucle` (un datagramme illisible ne tue pas la boucle) et que
    `EmetteurUDP.envoyer` (une trame perdue est comptée, pas propagée) : un instrument ne tue pas
    ce qu'il observe, et un silence inexpliqué est pire qu'un échec dit.
    """

    def __init__(self, bus, chemin, periode=CADENCE_VEILLE_STRUCTURE,
                 taille_max=TAILLE_MAX_STRUCTURE):
        if not chemin:
            raise ValueError(
                "un veilleur de structure exige un CHEMIN : un chemin vide serait un silence qui "
                "a l'air d'un run qui n'écrit pas encore.")
        self.bus = bus
        self.chemin = Path(chemin)
        self.periode = float(periode)
        self.taille_max = int(taille_max)
        self._signature = None          # `(mtime_ns, taille)` de la dernière version EXAMINÉE
        self._publications = 0
        self._absences = 0
        self._illisibles = 0
        self._invalides = 0
        self._derniere_erreur = None
        self._arret = threading.Event()
        self._fil = None

    def relire(self, force=False) -> bool:
        """Un tour de veille : publie la structure si le fichier a changé ; rend `True` alors.

        `force=True` ignore la signature (premier tour, ou relecture demandée à la main) ;
        `force=False` — le tour ordinaire — ne touche pas au disque quand la signature n'a pas
        bougé.

        ⚠️ La signature est mémorisée AVANT la lecture, et pour TOUS les cas : un fichier malformé
        qui ne change pas n'est pas relu en boucle (sinon la veille deviendrait un martèlement
        disque), et il est relu dès qu'il change — ce qui est exactement ce qui se passe quand le
        run le réécrit.
        """
        try:
            information = os.stat(self.chemin)
        except OSError as erreur:
            self._absences += 1
            self._derniere_erreur = f"{type(erreur).__name__}: {erreur}"
            self._signature = None      # une réapparition sera relue, fût-ce à `mtime` identique
            return False
        if not stat.S_ISREG(information.st_mode):
            # ⚠️ On ne tente même pas `open()` : sur un FIFO ou un périphérique, l'ouverture peut
            # BLOQUER indéfiniment (un tube nommé attend un écrivain) — le fil de veille resterait
            # pendu, et avec lui toute surveillance ultérieure. Seul un fichier ORDINAIRE peut
            # porter une trame écrite par `os.replace`.
            self._illisibles += 1
            self._derniere_erreur = "ce chemin n'est pas un fichier ordinaire"
            self._signature = None
            return False
        signature = (information.st_mtime_ns, information.st_size)
        if not force and signature == self._signature:
            return False
        self._signature = signature
        if information.st_size > self.taille_max:
            # Garde de TAILLE : `--structure-fichier` pointé par erreur sur un `.brain` (des
            # centaines de Mio de tenseurs) ne doit pas remplir la mémoire du serveur pour être
            # rejeté ensuite. La borne est très au-dessus d'une trame réelle (305 Ko à
            # `dim_bus = 145`) : elle ne refuse rien de légitime.
            self._invalides += 1
            self._derniere_erreur = (f"{information.st_size} octets : au-delà du plafond de "
                                     f"{self.taille_max} octets, ce n'est pas une trame "
                                     f"`structure`")
            return False
        try:
            with open(self.chemin, "rb") as fichier:
                octets = fichier.read()
        except OSError as erreur:       # permissions, fichier disparu entre `stat` et `open`…
            self._illisibles += 1
            self._derniere_erreur = f"{type(erreur).__name__}: {erreur}"
            return False
        trame = deserialiser(octets)    # `None` sur JSON cassé ou sur un objet sans `type`
        if not isinstance(trame, dict) or trame.get("type") != "structure" \
                or not isinstance(trame.get("couches"), list):
            # JSON valide mais mauvaise trame : la publier ferait dessiner au navigateur une scène
            # sans plaques, c'est-à-dire un écran noir qui a l'air d'un cerveau vide — exactement
            # ce que la page dit « en attente » plutôt que de mentir (spec §9).
            self._invalides += 1
            self._derniere_erreur = "JSON lu, mais ce n'est pas une trame `structure`"
            return False
        self.bus.publier_structure(trame)
        self._publications += 1
        return True

    def demarrer_en_thread(self):
        """Premier tour SYNCHRONE (la structure est publiée quand cette méthode rend la main),
        puis un fil de veille démon qui repasse toutes les `periode` secondes."""
        self.relire(force=True)
        self._fil = threading.Thread(target=self._boucle, name="veilleur-structure", daemon=True)
        self._fil.start()
        return self._fil

    def _boucle(self):
        # `Event.wait` et non `time.sleep` : l'arrêt est IMMÉDIAT (un `join` de 2 s qui devrait
        # attendre la fin du sommeil laisserait un fil vivant derrière un serveur déjà fermé).
        while not self._arret.wait(self.periode):
            self.relire()

    def arreter(self):
        self._arret.set()
        if self._fil is not None:
            self._fil.join(timeout=2.0)

    def compteurs(self):
        """Les compteurs de la veille. `absences` compte un tour de veille, pas une transition :
        un fichier absent pendant 10 s à 1 Hz compte 10 absences (le chiffre dit la DURÉE de
        l'attente autant que son existence). `derniere_erreur` n'est jamais effacée : elle dit ce
        qui a raté, même si tout va bien maintenant."""
        return {"chemin": str(self.chemin),
                "publications": self._publications,
                "absences": self._absences,
                "illisibles": self._illisibles,
                "invalides": self._invalides,
                "derniere_erreur": self._derniere_erreur}
