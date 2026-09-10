#!/usr/bin/env python3
"""VIS-01 — contrats du cerveau 3D (registre VIS-01, spec du 10/09/2026).

Aucune dépendance ajoutée : `http.server`/`socket`/`json` de la bibliothèque standard,
`numpy` déjà requis par le projet ; `torch` est importé UNIQUEMENT par les tests qui
instancient un vrai cerveau.

    NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests
"""
import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from naulthene.cerveau.telemetrie import serialiser   # tâche 4 : l'écouteur UDP reçoit des OCTETS


def json_strict(brut: bytes):
    """`json.loads` qui REJETTE les littéraux `NaN`/`Infinity` — ce que fait `JSON.parse`.

    ⚠️ `json.loads` seul les ACCEPTE (même `allow_nan=False` n'existe qu'à l'écriture) : un test
    qui se contenterait de `json.loads` sur un corps pollué passerait au vert et ne prouverait
    rien. `parse_constant` est le seul crochet qui reproduit la sévérité du navigateur.
    """
    def refuser(constante):
        raise ValueError(f"littéral non JSON dans le corps : {constante}")
    return json.loads(brut.decode("utf-8") if isinstance(brut, bytes) else brut,
                      parse_constant=refuser)


class TestCodecMatrices(unittest.TestCase):
    def test_quantification_respecte_la_borne_d_erreur(self):
        from naulthene.cerveau.telemetrie import quantifier_matrice, dequantifier_matrice
        rng = np.random.default_rng(11)
        m = rng.normal(0.0, 0.05, size=(145, 147)).astype(np.float32)
        octets, echelle = quantifier_matrice(m)
        self.assertEqual(len(octets), m.size)
        retour = dequantifier_matrice(octets, echelle, m.shape)
        erreur_max = float(np.max(np.abs(retour - m)))
        self.assertLessEqual(erreur_max, float(np.max(np.abs(m))) / 254.0 + 1e-9)

    def test_matrice_nulle_donne_echelle_un_et_octets_nuls(self):
        from naulthene.cerveau.telemetrie import quantifier_matrice, dequantifier_matrice
        m = np.zeros((8, 5), dtype=np.float32)
        octets, echelle = quantifier_matrice(m)
        self.assertEqual(echelle, 1.0)
        self.assertEqual(octets, bytes(40))
        self.assertTrue(np.array_equal(dequantifier_matrice(octets, echelle, m.shape), m))

    def test_base64_aller_retour(self):
        from naulthene.cerveau.telemetrie import encoder_octets, decoder_octets
        brut = bytes(range(256))
        self.assertEqual(decoder_octets(encoder_octets(brut)), brut)

    def test_poids_non_fini_donne_octets_nuls_et_echelle_un(self):
        """Ruling (revue tâche 1) : un poids NaN/inf est traité comme ABSENT.

        Sinon `echelle` devient `nan`, la trame `structure` part avec un `NaN` et
        `JSON.parse` la rejette côté navigateur — un cerveau dans un état inattendu doit
        être AFFICHÉ comme tel, jamais produire une trame invalide (spec §9).
        """
        from naulthene.cerveau.telemetrie import quantifier_matrice, dequantifier_matrice
        poison = (np.nan, np.inf, -np.inf)
        for valeur in poison:
            with self.subTest(valeur=valeur):
                m = np.full((8, 5), valeur, dtype=np.float32)
                m[0, 0] = 0.25
                octets, echelle = quantifier_matrice(m)
                self.assertEqual(octets, bytes(m.size))
                self.assertEqual(echelle, 1.0)
                retour = dequantifier_matrice(octets, echelle, m.shape)
                self.assertTrue(np.all(np.isfinite(retour)))
                self.assertTrue(np.array_equal(retour, np.zeros(m.shape, dtype=np.float32)))


class TestTramesEtDisposition(unittest.TestCase):
    def test_forme_du_cerveau_a_dim_bus_145(self):
        """Critère n°1 : `definir_couches(145)` reproduit EXACTEMENT les 12 formes mesurées.

        ⚠️ La table est comparée **en bloc** (`nom → (entree, sortie)`), jamais couche par
        couche : c'est le seul contrôle qui discrimine une permutation de deux `entree` entre
        deux couches de même produit/somme. Contre-exemple MESURÉ (revue de la tâche 2) :
        permuter `analyseur` `db`→`2*db` et `fusion_memoire` `2*db`→`db` laisse Σ sorties =
        1 182 et Σ synapses = 220 255 **inchangées**, et une comparaison sur 7 couches sur 12
        passe au vert. Les deux totaux dérivés du plan sont donc assertés EN PLUS de la table,
        jamais à sa place — ils ne suffisent pas seuls.

        Les 12 formes sont celles du tableau « Faits mesurés » du plan
        (`docs/ameliorations/PLAN_VIS-01_cerveau_3d.md`), relevées sur `K4_NU_g11.brain`.
        """
        from naulthene.cerveau.telemetrie import definir_couches
        liste = definir_couches(145)
        couches = {c["nom"]: (c["entree"], c["sortie"]) for c in liste}
        attendu = {
            "porte_visuelle": (147, 145),
            "porte_auditive": (130, 145),
            "hippocampe": (290, 145),
            "analyseur": (145, 145),
            "fusion_memoire": (290, 145),
            "integrateur_bio": (189, 145),   # 145 + 44 dims bio
            "tete_motrice": (145, 8),
            "cortex_prefrontal": (145, 1),
            "tete_vocale": (145, 8),
            "tete_requete": (145, 5),
            "generateur_attente": (153, 145),
            "generateur_attente_audio": (153, 145),
        }
        self.assertEqual(len(liste), 12)     # 12 ENTRÉES — un doublon de nom passerait sinon
        self.assertEqual(couches, attendu)   # les 12 formes, en bloc (noms ET valeurs)
        # Totaux dérivés du plan, calculés sur la table RENDUE par le module (pas sur le
        # littéral ci-dessus) : second témoin, plus faible, conservé explicitement.
        self.assertEqual(sum(sortie for _, sortie in couches.values()), 1182)
        self.assertEqual(sum(entree * sortie for entree, sortie in couches.values()), 220255)

    def test_disposition_deterministe(self):
        from naulthene.cerveau.telemetrie import definir_couches, disposition
        couches = definir_couches(16)
        a, b = disposition(couches), disposition(couches)
        self.assertEqual(set(a), set(b))
        for nom in a:
            self.assertTrue(np.array_equal(a[nom], b[nom]), nom)
            self.assertEqual(a[nom].shape, (couches[[c["nom"] for c in couches].index(nom)]["sortie"], 3))

    def test_les_trois_trames_survivent_au_transport(self):
        from naulthene.cerveau.telemetrie import (
            trame_structure, trame_activite, trame_evenement, serialiser, deserialiser)
        s = trame_structure([{"nom": "analyseur", "rang": 2, "entree": 16, "sortie": 16,
                              "echelle": 0.02, "poids_i8": "AAAA"}], [], {"jour": 1, "dim_bus": 16})
        a = trame_activite({"analyseur": "AAAA"}, {"dopamine": 0.3}, {"tick": 7})
        e = trame_evenement("choc_dopamine", {"tick": 7}, intensite=1.0)
        for trame in (s, a, e):
            self.assertEqual(deserialiser(serialiser(trame)), trame)

    def test_datagramme_malforme_ne_leve_jamais(self):
        from naulthene.cerveau.telemetrie import deserialiser
        self.assertIsNone(deserialiser(b"pas du json"))
        self.assertIsNone(deserialiser(b""))
        self.assertIsNone(deserialiser(b'{"sans": "type"}'))

    def test_serialiser_refuse_un_flottant_non_fini(self):
        """Ruling (revue tâche 1) : aucune trame invalide ne doit pouvoir partir.

        L'appelant PERD la trame (ValueError) plutôt que d'envoyer un JSON que le
        navigateur rejettera — l'échec est visible, jamais silencieux.
        """
        from naulthene.cerveau.telemetrie import serialiser, trame_activite
        for valeur in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(valeur=valeur):
                trame = trame_activite({}, {"dopamine": valeur}, {"tick": 7})
                with self.assertRaises(ValueError):
                    serialiser(trame)


class TestBusEtEmetteur(unittest.TestCase):
    def test_le_bus_ne_garde_que_la_derniere_activite(self):
        from naulthene.cerveau.telemetrie import BusTrames, trame_activite
        bus = BusTrames()
        for tick in (1, 2, 3):
            bus.publier_activite(trame_activite({}, {"tick": tick}, {"tick": tick}))
        self.assertEqual(bus.activite()["scalaires"]["tick"], 3)
        self.assertEqual(bus.sequence, 3)

    def test_file_d_evenements_bornee(self):
        from naulthene.cerveau.telemetrie import BusTrames, trame_evenement
        bus = BusTrames(taille_evenements=32)
        for i in range(40):
            bus.publier_evenement(trame_evenement("choc_dopamine", {"tick": i}))
        nouveaux, total = bus.evenements_depuis(0)
        self.assertEqual(total, 40)
        self.assertEqual(len(nouveaux), 32)
        self.assertEqual(nouveaux[-1]["tick"], 39)

    def test_cible_udp_invalide_refusee_au_demarrage(self):
        from naulthene.cerveau.telemetrie import analyser_cible_udp
        self.assertEqual(analyser_cible_udp("udp:127.0.0.1:9998"), ("127.0.0.1", 9998))
        for mauvaise in ("127.0.0.1:9998", "udp:127.0.0.1", "tcp:1.2.3.4:5"):
            with self.assertRaises(ValueError):
                analyser_cible_udp(mauvaise)

    def test_emetteur_livre_les_octets_et_ne_bloque_jamais(self):
        import socket as sock
        from naulthene.cerveau.telemetrie import EmetteurUDP, trame_evenement, serialiser
        ecoute = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        ecoute.bind(("127.0.0.1", 0))
        ecoute.settimeout(2.0)
        port = ecoute.getsockname()[1]
        emetteur = EmetteurUDP(f"udp:127.0.0.1:{port}")
        trame = trame_evenement("victoire", {"tick": 5})
        self.assertTrue(emetteur.envoyer(trame))
        recu, _ = ecoute.recvfrom(65535)
        self.assertEqual(recu, serialiser(trame))
        emetteur.fermer()
        ecoute.close()

    def test_envoi_vers_port_ferme_est_perdu_sans_exception(self):
        from naulthene.cerveau.telemetrie import EmetteurUDP, trame_evenement
        emetteur = EmetteurUDP("udp:127.0.0.1:1")   # port réservé, rien n'écoute
        for _ in range(3):
            emetteur.envoyer(trame_evenement("choc_dopamine", {"tick": 1}))
        self.assertGreaterEqual(emetteur.compteurs()["envoyees"] + emetteur.compteurs()["perdues"], 3)
        emetteur.fermer()

    def test_envoi_apres_fermeture_est_perdu_et_compte(self):
        """Témoin déterministe, hors réseau, que `perdues` s'incrémente vraiment.

        Un envoi vers un port fermé RÉUSSIT sur cette machine (le noyau accepte le datagramme),
        donc le test précédent passe avec `perdues == 0` : il ne prouve rien sur le compteur.
        Une socket fermée échoue à coup sûr (OSError), sans dépendre du réseau.
        """
        from naulthene.cerveau.telemetrie import EmetteurUDP, trame_evenement
        emetteur = EmetteurUDP("udp:127.0.0.1:1")
        emetteur.fermer()
        self.assertFalse(emetteur.envoyer(trame_evenement("choc_dopamine", {"tick": 1})))
        self.assertEqual(emetteur.compteurs()["perdues"], 1)
        self.assertEqual(emetteur.compteurs()["envoyees"], 0)

    def test_scalaire_numpy_non_serialisable_est_perdu_et_compte(self):
        """Cas RÉEL (spec §4) : `variance du bus` et `logits` sont des scalaires numpy.

        `json.dumps` lève `TypeError` sur `np.float32` / `np.int64` — une exception qui
        remonterait dans la boucle chaude du run (tâche 9) et tuerait l'entraînement. Elle doit
        être COMPTÉE comme une perte, jamais avalée ni propagée.
        """
        import numpy as np
        from naulthene.cerveau.telemetrie import EmetteurUDP, trame_activite
        emetteur = EmetteurUDP("udp:127.0.0.1:1")
        trame = trame_activite({}, {"variance_bus": np.float32(0.31), "logits": np.int64(3)}, {"tick": 1})
        self.assertFalse(emetteur.envoyer(trame))
        self.assertEqual(emetteur.compteurs()["perdues"], 1)
        self.assertEqual(emetteur.compteurs()["envoyees"], 0)
        emetteur.fermer()


class TestCompteurDeStructure(unittest.TestCase):
    def test_seconde_publication_de_structure_est_detectee(self):
        """Ruling (hérité d'une revue) : le bus doit rendre un CHANGEMENT de structure visible.

        `structure()` seule rend la même chose avant et après : un abonné (le flux SSE) ne peut
        donc pas savoir qu'une neurogenèse a changé `dim_bus`, et la spec §9 exige pourtant que le
        client RECONSTRUISE alors la scène. Un compteur de publications est l'extension minimale
        qui rend ce changement observable — il est asserté ici, dans le bus, parce que c'est le bus
        qui porte l'information.
        """
        from naulthene.cerveau.telemetrie import BusTrames, trame_structure
        bus = BusTrames()
        self.assertEqual(bus.sequence_structure, 0)          # rien de publié : aucun changement
        bus.publier_structure(trame_structure([], [], {"dim_bus": 16}))
        self.assertEqual(bus.sequence_structure, 1)          # 1re structure : à pousser
        bus.publier_structure(trame_structure([], [], {"dim_bus": 32}))   # neurogenèse
        self.assertEqual(bus.sequence_structure, 2)          # 2e structure : changement DÉTECTÉ
        self.assertEqual(bus.compteurs()["sequence_structure"], 2)
        self.assertEqual(bus.structure()["dim_bus"], 32)


class TestServeur(unittest.TestCase):
    """Le serveur local : page statique, `/structure`, flux SSE, écoute UDP.

    ⚠️ Les dossiers statiques de ces tests sont TEMPORAIRES et passés par `dossier_statique=` :
    la page RÉELLE (tâche 5) est vérifiée dans `TestPageEtVendor`, jamais ici.
    """

    @contextlib.contextmanager
    def _flux(self, port, delai=5.0):
        """Ouvre `/flux` et rend un lecteur BORNÉ des prochaines lignes.

        ⚠️ Un flux SSE ne se TERMINE jamais : le lire « jusqu'à la fin » revient à attendre un
        `socket.timeout`. On lit donc un NOMBRE de lignes, avec une échéance de secours — un
        dépassement n'est pas un échec, c'est un serveur qui n'a plus rien de neuf à dire.
        """
        import socket
        import time
        import urllib.request

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/flux", timeout=delai) as reponse:
            def lire(nb_lignes, delai_local=delai):
                lignes, fin = [], time.time() + delai_local
                while len(lignes) < nb_lignes and time.time() < fin:
                    try:
                        brut = reponse.readline()
                    except (socket.timeout, TimeoutError):
                        break
                    if not brut:
                        break
                    lignes.append(brut.decode("utf-8").rstrip())
                return lignes
            yield lire

    def _client_sse(self, port, nb_lignes=6, delai=5.0):
        """Les `nb_lignes` premières lignes de `/flux`.

        Le plan proposait 12 : comme le flux n'a pas de fin, les 6 lignes suivantes ne viendront
        jamais et le test paierait le délai entier. Six lignes = les DEUX événements complets
        (structure puis activité) qui arrivent réellement.
        """
        with self._flux(port, delai) as lire:
            return lire(nb_lignes, delai)

    @staticmethod
    def _rend_la_main(appel, delai=3.0):
        """`True` si `appel()` rend la main avant `delai` — jamais bloquant pour la suite.

        ⚠️ Un `arreter()` défaillant bloque POUR TOUJOURS (`shutdown()` attend un événement que
        seul `serve_forever()` arme : sondé par le reviewer, encore bloqué après 3 s). L'appeler
        directement ferait pendre toute la suite de tests : on l'exécute dans un fil DÉMON
        surveillé, et une exception est remontée à l'appelant, jamais avalée.
        """
        import threading
        resultat = {}

        def _appeler():
            try:
                appel()
            except BaseException as erreur:   # remontée telle quelle par l'appelant
                resultat["erreur"] = erreur

        fil = threading.Thread(target=_appeler, name="arret-sous-surveillance", daemon=True)
        fil.start()
        fil.join(timeout=delai)
        if fil.is_alive():
            return False
        if "erreur" in resultat:
            raise resultat["erreur"]
        return True

    @staticmethod
    def _evenements(lignes):
        """`[(nom, charge)]` — les lignes brutes d'un flux SSE, décodées."""
        trouves, nom = [], None
        for ligne in lignes:
            if ligne.startswith("event: "):
                nom = ligne[len("event: "):]
            elif ligne.startswith("data: ") and nom is not None:
                trouves.append((nom, json.loads(ligne[len("data: "):])))
            elif not ligne:
                nom = None
        return trouves

    def test_structure_et_flux_sse(self):
        import urllib.request
        from naulthene.cerveau.telemetrie import (BusTrames, trame_structure, trame_activite)
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        bus = BusTrames()
        bus.publier_structure(trame_structure([], [], {"dim_bus": 16}))
        serveur = ServeurCerveau3D(bus, port=0)
        serveur.demarrer_en_thread()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{serveur.port}/structure") as r:
                self.assertEqual(json.loads(r.read())["dim_bus"], 16)
            bus.publier_activite(trame_activite({}, {"tick": 1}, {"tick": 1}))
            lignes = self._client_sse(serveur.port)
            self.assertIn("event: structure", lignes)
            self.assertTrue(any(l.startswith("event: activite") for l in lignes))
            self.assertTrue(lignes[0].startswith("event: structure"), lignes)  # la structure D'ABORD
        finally:
            serveur.arreter()

    def test_seconde_structure_est_repoussee_sur_le_flux(self):
        """Le flux doit re-signaler une structure CHANGÉE, pas seulement celle de la connexion.

        La neurogenèse change `dim_bus` : sans ce second envoi, le navigateur garde une scène
        périmée (spec §9) alors que le cerveau, lui, a grandi.
        """
        from naulthene.cerveau.telemetrie import BusTrames, trame_structure
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        bus = BusTrames()
        bus.publier_structure(trame_structure([], [], {"dim_bus": 16}))
        serveur = ServeurCerveau3D(bus, port=0)
        serveur.demarrer_en_thread()
        try:
            with self._flux(serveur.port) as lire:
                premiers = self._evenements(lire(3))
                self.assertEqual([nom for nom, _ in premiers], ["structure"], premiers)
                self.assertEqual(premiers[0][1]["dim_bus"], 16)

                bus.publier_structure(trame_structure([], [], {"dim_bus": 32}))
                seconds = self._evenements(lire(3))
                self.assertEqual([nom for nom, _ in seconds], ["structure"], seconds)
                self.assertEqual(seconds[0][1]["dim_bus"], 32)
        finally:
            serveur.arreter()

    def test_evenement_publie_est_pousse_sur_le_flux(self):
        """Le troisième canal : un fait daté (choc dopaminergique, victoire, neurogenèse) part
        aussi vers le navigateur, et une seule fois — sinon la frise se remplit de doublons."""
        from naulthene.cerveau.telemetrie import BusTrames, trame_structure, trame_evenement
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        bus = BusTrames()
        bus.publier_structure(trame_structure([], [], {"dim_bus": 16}))
        serveur = ServeurCerveau3D(bus, port=0)
        serveur.demarrer_en_thread()
        try:
            with self._flux(serveur.port) as lire:
                self.assertEqual([nom for nom, _ in self._evenements(lire(3))], ["structure"])
                bus.publier_evenement(trame_evenement("choc_dopamine", {"tick": 12}, intensite=0.8))
                evenements = self._evenements(lire(3))
                self.assertEqual([nom for nom, _ in evenements], ["evenement"], evenements)
                self.assertEqual(evenements[0][1]["genre"], "choc_dopamine")
                self.assertEqual(evenements[0][1]["tick"], 12)
                # Un second fait : le curseur du flux doit repartir de LÀ où il en était (sinon
                # le premier événement serait renvoyé une seconde fois, et la frise doublerait).
                bus.publier_evenement(trame_evenement("victoire", {"tick": 13}))
                suivants = self._evenements(lire(3))
                self.assertEqual([nom for nom, _ in suivants], ["evenement"], suivants)
                self.assertEqual(suivants[0][1]["genre"], "victoire")
        finally:
            serveur.arreter()

    def test_client_neuf_ne_rejoue_pas_les_evenements_passes(self):
        """Ruling de revue (tâche 5) : le curseur des faits part du total COURANT, jamais de `0`.

        Pourquoi c'est nécessaire : la file d'événements est BORNÉE mais non vide — un
        rechargement de page (ou un second onglet) recevait donc tout le tampon du passé et
        racontait à nouveau des faits déjà consommés. Un client NEUF regarde le PRÉSENT.

        Le contrôle est BEHAVIORAL, pas structurel : trois faits sont publiés AVANT la connexion,
        puis un fait NOUVEAU. Le premier `evenement` reçu doit être le nouveau — sans le ruling,
        le premier reçu est le plus ancien du tampon.
        """
        from naulthene.cerveau.telemetrie import BusTrames, trame_evenement, trame_structure
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        bus = BusTrames()
        bus.publier_structure(trame_structure([], [], {"dim_bus": 16}))
        for tick in (0, 1, 2):                                  # le PASSÉ, déjà consommé
            bus.publier_evenement(trame_evenement("choc_dopamine", {"tick": tick}))
        serveur = ServeurCerveau3D(bus, port=0)
        serveur.demarrer_en_thread()
        try:
            with self._flux(serveur.port) as lire:
                premiers = self._evenements(lire(3))
                self.assertEqual([nom for nom, _ in premiers], ["structure"], premiers)

                bus.publier_evenement(trame_evenement("victoire", {"tick": 99}))
                recus = self._evenements(lire(3))
                self.assertEqual([nom for nom, _ in recus], ["evenement"], recus)
                self.assertEqual(recus[0][1]["genre"], "victoire", recus)
                self.assertEqual(recus[0][1]["tick"], 99, recus)
        finally:
            serveur.arreter()

    def test_activite_avec_valeur_non_finie_part_en_null_sur_le_flux(self):
        """I1 : une valeur NON FINIE présente dans le bus part en `null`, jamais en `NaN`.

        Le chemin est réellement atteignable : `json.loads` (donc `deserialiser`, donc
        l'écouteur UDP de cette tâche) ACCEPTE les littéraux `NaN`/`Infinity`. Un `NaN` publié
        ainsi dans le bus produisait `data: {...,"dopamine":NaN}` — que `JSON.parse` REJETTE :
        la page tombait au lieu d'afficher un cerveau dans un état inattendu (spec §9).

        Le corps est vérifié par l'absence de littéral ET par un parseur STRICT (celui de
        `json.loads` accepte `NaN` : il ne prouverait rien seul).
        """
        from naulthene.cerveau.telemetrie import BusTrames, trame_structure
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        bus = BusTrames()
        bus.publier_structure(trame_structure([], [], {"dim_bus": 16}))
        # Publiée EN MÉMOIRE, les trois valeurs non finies, à DEUX profondeurs : la conversion
        # doit être RÉCURSIVE (un `dict` de listes, pas seulement la racine).
        bus.publier_activite({"type": "activite", "version": 1, "tick": 1,
                              "scalaires": {"dopamine": float("nan"),
                                            "energie": float("inf"),
                                            "variance_bus": float("-inf")},
                              "matrices": {"analyseur": [0.5, float("nan")]}})
        serveur = ServeurCerveau3D(bus, port=0)
        serveur.demarrer_en_thread()
        try:
            lignes = self._client_sse(serveur.port)
            donnees = [l for l in lignes if l.startswith("data: ")]
            self.assertTrue(donnees, lignes)
            for ligne in donnees:                      # aucun littéral, sur AUCUN événement
                self.assertNotIn("NaN", ligne, ligne)
                self.assertNotIn("Infinity", ligne, ligne)
            charge = json_strict(donnees[-1][len("data: "):])
            self.assertEqual(charge["scalaires"]["dopamine"], None)
            self.assertEqual(charge["scalaires"]["energie"], None)
            self.assertEqual(charge["scalaires"]["variance_bus"], None)
            self.assertEqual(charge["matrices"]["analyseur"], [0.5, None])
            self.assertEqual(charge["tick"], 1)         # le reste de la trame est intact
        finally:
            serveur.arreter()

    def test_structure_avec_valeur_non_finie_part_en_null_sur_structure(self):
        """I1, sonde du reviewer rejouée de bout en bout : datagramme avec `NaN` littéral.

        Un vrai `EcouteurUDP` (celui de cette tâche) reçoit `{"type":"structure",...,
        "dim_bus":NaN}` — écrit par un émetteur qui n'est PAS `serialiser` (le seul protégé) —
        le publie dans le bus, et `/structure` doit servir un corps SANS littéral `NaN`.
        """
        import socket as sock
        import time
        import urllib.request
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.serveur import EcouteurUDP, ServeurCerveau3D

        bus = BusTrames()
        ecouteur = EcouteurUDP(bus, port=0)
        ecouteur.demarrer_en_thread()
        serveur = ServeurCerveau3D(bus, port=0)
        serveur.demarrer_en_thread()
        emetteur = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        try:
            emetteur.sendto(b'{"type":"structure","version":1,"dim_bus":NaN}',
                            ("127.0.0.1", ecouteur.port))
            limite = time.time() + 3.0
            while bus.structure() is None and time.time() < limite:
                time.sleep(0.05)
            self.assertIsNotNone(bus.structure(), "le datagramme NaN n'est pas arrivé au bus")
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{serveur.port}/structure", timeout=3.0) as r:
                brut = r.read()
            self.assertNotIn(b"NaN", brut, brut)
            self.assertNotIn(b"Infinity", brut, brut)
            charge = json_strict(brut)                  # ce que `JSON.parse` doit accepter
            self.assertIsNone(charge["dim_bus"])
            self.assertEqual(charge["type"], "structure")
        finally:
            serveur.arreter()
            ecouteur.arreter()
            emetteur.close()

    def test_flux_survit_a_une_trame_refusee_par_la_ceinture_stricte(self):
        """I1 : `allow_nan=False` est une CEINTURE — un `ValueError` ne tue pas le fil.

        Le `NaN` en CLÉ (jamais en valeur) n'est pas converti par l'assainissement des valeurs,
        mais `json.dumps(..., allow_nan=False)` le REFUSE (`ValueError`) : c'est exactement le
        cas que le ruling décrit. La trame refusée est sautée et COMPTÉE ; le flux continue de
        servir les suivantes (sans le `try/except`, le fil de gestion mourrait et plus rien
        n'arriverait ; sans `allow_nan=False`, la trame partirait en `{"NaN":1}`).

        ⚠️ On ATTEND que le refus ait eu lieu (compteur, lu par la route publique : une trame
        refusée ne produit AUCUNE ligne dans le flux) avant de publier la suivante. Sans cette
        attente, le canal d'activité n'ayant qu'un emplacement, la trame polluée pourrait être
        ÉCRASÉE avant d'être tentée — le test passerait alors sans rien prouver.
        """
        import time
        import urllib.error
        import urllib.request
        from naulthene.cerveau.telemetrie import BusTrames, trame_structure, trame_activite
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        bus = BusTrames()
        bus.publier_structure(trame_structure([], [], {"dim_bus": 16}))
        # Clé flottante non finie : `assainir_json` ne touche pas les CLÉS, la ceinture les refuse.
        bus.publier_activite({"type": "activite", "version": 1, "scalaires": {float("nan"): 1}})
        serveur = ServeurCerveau3D(bus, port=0)
        serveur.demarrer_en_thread()

        def _compteur_refus():
            with urllib.request.urlopen(f"http://127.0.0.1:{serveur.port}/sante",
                                        timeout=3.0) as r:
                return json.loads(r.read())["emissions_refusees"]

        try:
            with self._flux(serveur.port) as lire:
                self.assertEqual([nom for nom, _ in self._evenements(lire(3))], ["structure"])
                limite = time.time() + 5.0
                while _compteur_refus() < 1 and time.time() < limite:
                    time.sleep(0.02)
                self.assertEqual(_compteur_refus(), 1,
                                 "la trame à clé non finie n'a pas été ATTAQUÉE puis refusée")
                bus.publier_activite(trame_activite({}, {"tick": 2}, {"tick": 2}))
                suivants = self._evenements(lire(3))
                self.assertEqual([nom for nom, _ in suivants], ["activite"], suivants)
                self.assertEqual(suivants[0][1]["scalaires"]["tick"], 2)
            # La même ceinture sur la route JSON : la clé non finie est refusée ⇒ 500 COMPTÉ
            # (l'échec reste visible), jamais un corps que `JSON.parse` rejetterait.
            bus.publier_structure({"type": "structure", "version": 1, "dim_bus": 16,
                                   float("nan"): 1})
            with self.assertRaises(urllib.error.HTTPError) as capture:
                urllib.request.urlopen(f"http://127.0.0.1:{serveur.port}/structure", timeout=3.0)
            self.assertEqual(capture.exception.code, 500)
            self.assertEqual(_compteur_refus(), 2)
        finally:
            serveur.arreter()

    def test_flux_reste_en_http_1_0(self):
        """Ruling : le flux SSE n'a ni `Content-Length` ni `chunked`.

        En HTTP/1.1, un client attendrait une fin de corps qui n'arrive jamais — le corps se
        termine ici à la FERMETURE de la connexion, ce qui est exactement un flux continu.
        """
        import urllib.request
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        serveur = ServeurCerveau3D(BusTrames(), port=0)
        serveur.demarrer_en_thread()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{serveur.port}/flux", timeout=2.0) as r:
                self.assertEqual(r.version, 10)          # 10 = HTTP/1.0 (jamais 11)
                self.assertIsNone(r.headers["Content-Length"])
        finally:
            serveur.arreter()

    def test_page_et_ressources_servies_avec_leur_type(self):
        """`/` → `index.html` en `text/html`, `app.js`/`three.module.js` en `text/javascript`."""
        import tempfile
        import urllib.request
        from pathlib import Path
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        with tempfile.TemporaryDirectory() as dossier:
            Path(dossier, "index.html").write_text("<!doctype html><title>cerveau</title>",
                                                   encoding="utf-8")
            Path(dossier, "app.js").write_text("export const app = 1;\n", encoding="utf-8")
            Path(dossier, "three.module.js").write_text("export const three = 1;\n", encoding="utf-8")
            serveur = ServeurCerveau3D(BusTrames(), port=0, dossier_statique=dossier)
            serveur.demarrer_en_thread()
            try:
                for chemin, type_attendu in (("/", "text/html"),
                                             ("/app.js", "text/javascript"),
                                             ("/three.module.js", "text/javascript")):
                    with self.subTest(chemin=chemin):
                        with urllib.request.urlopen(
                                f"http://127.0.0.1:{serveur.port}{chemin}") as r:
                            self.assertEqual(r.status, 200)
                            self.assertEqual(r.headers["Content-Type"],
                                             type_attendu + "; charset=utf-8")
                            self.assertTrue(r.read())
            finally:
                serveur.arreter()

    def test_fichier_statique_absent_repond_404(self):
        """Le dossier statique est vide (page = tâche 5) : la route répond 404, elle ne plante pas."""
        import tempfile
        import urllib.error
        import urllib.request
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        with tempfile.TemporaryDirectory() as dossier:
            serveur = ServeurCerveau3D(BusTrames(), port=0, dossier_statique=dossier)
            serveur.demarrer_en_thread()
            try:
                for chemin in ("/", "/app.js", "/inconnu"):
                    with self.subTest(chemin=chemin):
                        with self.assertRaises(urllib.error.HTTPError) as capture:
                            urllib.request.urlopen(f"http://127.0.0.1:{serveur.port}{chemin}")
                        self.assertEqual(capture.exception.code, 404)
            finally:
                serveur.arreter()

    def test_sante_renvoie_les_compteurs_du_bus(self):
        import urllib.request
        from naulthene.cerveau.telemetrie import BusTrames, trame_activite, trame_structure
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        bus = BusTrames()
        bus.publier_structure(trame_structure([], [], {"dim_bus": 16}))
        bus.publier_activite(trame_activite({}, {"tick": 1}, {"tick": 1}))
        bus.publier_activite(trame_activite({}, {"tick": 2}, {"tick": 2}))
        serveur = ServeurCerveau3D(bus, port=0)
        serveur.demarrer_en_thread()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{serveur.port}/sante") as r:
                compteurs = json.loads(r.read())["bus"]
            self.assertEqual(compteurs["sequence"], 2)
            self.assertEqual(compteurs["sequence_structure"], 1)
        finally:
            serveur.arreter()

    def test_port_nul_expose_le_port_reellement_lie(self):
        """Critère n°4 : `port=0` lie un port LIBRE et `.port` dit lequel — sans quoi les tests se
        marcheraient dessus au hasard."""
        import urllib.request
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        serveur = ServeurCerveau3D(BusTrames(), port=0)
        serveur.demarrer_en_thread()
        try:
            self.assertGreater(serveur.port, 0)
            with urllib.request.urlopen(f"http://127.0.0.1:{serveur.port}/sante", timeout=2.0) as r:
                self.assertEqual(r.status, 200)   # c'est bien CE port qui répond
        finally:
            serveur.arreter()

    def test_arreter_rend_la_main_et_libere_le_port(self):
        """Critère n°4 : `arreter()` rend la main ET ne laisse ni fil ni socket derrière lui."""
        import urllib.request
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        serveur = ServeurCerveau3D(BusTrames(), port=0)
        serveur.demarrer_en_thread()
        port = serveur.port
        serveur.arreter()
        with self.assertRaises(OSError):        # plus personne n'écoute (URLError ⊂ OSError)
            urllib.request.urlopen(f"http://127.0.0.1:{port}/sante", timeout=1.0)
        second = ServeurCerveau3D(BusTrames(), port=port)   # le port est bien RENDU
        try:
            second.demarrer_en_thread()
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/sante", timeout=2.0) as r:
                self.assertEqual(r.status, 200)
        finally:
            second.arreter()

    def test_arreter_sans_demarrage_rend_la_main_et_libere_le_port(self):
        """I2 : `arreter()` sans `demarrer_en_thread()` ne doit PAS bloquer (sonde du reviewer).

        `shutdown()` attend un événement que seul `serve_forever()` arme : appelé sans démarrage
        il bloque INDÉFINIMENT, et `server_close()` n'est alors jamais atteint — le socket
        d'écoute reste lié. Le test ne se contente pas de mesurer la durée : il vérifie que le
        port est réellement RENDU.
        """
        import urllib.request
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        serveur = ServeurCerveau3D(BusTrames(), port=0)
        port = serveur.port
        self.assertTrue(self._rend_la_main(serveur.arreter),
                        "arreter() sans demarrer_en_thread() bloque encore")
        # Le socket est LIBÉRÉ : un second serveur reprend le même port (sinon EADDRINUSE).
        second = ServeurCerveau3D(BusTrames(), port=port)
        try:
            second.demarrer_en_thread()
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/sante", timeout=2.0) as r:
                self.assertEqual(r.status, 200)
        finally:
            second.arreter()

    def test_arreter_est_idempotent_sur_les_deux_chemins(self):
        """I2 : le ruling est « sûr ET idempotent », sur le chemin jamais démarré ET le démarré.

        Deux appels de suite, dans les deux états : le second ne doit ni bloquer, ni lever.
        """
        import urllib.request
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        jamais_demarre = ServeurCerveau3D(BusTrames(), port=0)
        self.assertTrue(self._rend_la_main(jamais_demarre.arreter))
        self.assertTrue(self._rend_la_main(jamais_demarre.arreter))   # idempotent

        demarre = ServeurCerveau3D(BusTrames(), port=0)
        demarre.demarrer_en_thread()
        port = demarre.port
        self.assertTrue(self._rend_la_main(demarre.arreter))
        self.assertTrue(self._rend_la_main(demarre.arreter))          # idempotent
        with self.assertRaises(OSError):            # plus personne n'écoute (URLError ⊂ OSError)
            urllib.request.urlopen(f"http://127.0.0.1:{port}/sante", timeout=1.0)

    def test_flux_ouvert_ne_bloque_pas_les_autres_requetes(self):
        """Critère n°2 : un client qui lit le flux n'empêche personne d'autre d'être servi.

        Un serveur mono-fil laisserait la seconde requête attendre la FIN du flux — c'est-à-dire
        toujours. On lit d'abord un événement (le flux est donc bien ouvert), puis on interroge
        `/sante` : il doit répondre sans attendre.
        """
        import urllib.request
        from naulthene.cerveau.telemetrie import BusTrames, trame_structure
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        bus = BusTrames()
        bus.publier_structure(trame_structure([], [], {"dim_bus": 16}))
        serveur = ServeurCerveau3D(bus, port=0)
        serveur.demarrer_en_thread()
        try:
            with self._flux(serveur.port) as lire:
                self.assertEqual([nom for nom, _ in self._evenements(lire(3))], ["structure"])
                with urllib.request.urlopen(
                        f"http://127.0.0.1:{serveur.port}/sante", timeout=2.0) as r:
                    self.assertEqual(r.status, 200)
        finally:
            serveur.arreter()

    def test_datagramme_malforme_ignore_puis_trame_valide_acceptee(self):
        import socket as sock
        import time
        from naulthene.cerveau.telemetrie import BusTrames, trame_activite
        from naulthene.instruments.cerveau_3d.serveur import EcouteurUDP

        bus = BusTrames()
        ecouteur = EcouteurUDP(bus, port=0)
        ecouteur.demarrer_en_thread()
        try:
            emetteur = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
            emetteur.sendto(b"pas du json", ("127.0.0.1", ecouteur.port))
            emetteur.sendto(b'{"sans": "type"}', ("127.0.0.1", ecouteur.port))
            time.sleep(0.4)
            self.assertIsNone(bus.activite())
            emetteur.sendto(serialiser(trame_activite({}, {"tick": 9}, {"tick": 9})),
                            ("127.0.0.1", ecouteur.port))
            limite = time.time() + 3.0
            while bus.activite() is None and time.time() < limite:
                time.sleep(0.05)
            self.assertEqual(bus.activite()["tick"], 9)
            self.assertGreaterEqual(ecouteur.compteurs()["ignorees"], 2)
            emetteur.close()
        finally:
            ecouteur.arreter()

    def test_datagramme_de_type_inconnu_est_compte_mais_ne_remplit_aucun_canal(self):
        """Un `type` que le serveur ne connaît pas ne doit pas se déguiser en trame valide.

        Comportement de la table de routage du plan : la trame est COMPTÉE (`recues`), publiée
        nulle part — elle ne doit surtout pas finir dans un canal par défaut. Le point laissé
        ouvert (une trame dont le `type` serait incohérent à cause du `**meta` des constructeurs)
        est signalé dans le rapport de la tâche.
        """
        import socket as sock
        import time
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.serveur import EcouteurUDP

        bus = BusTrames()
        ecouteur = EcouteurUDP(bus, port=0)
        ecouteur.demarrer_en_thread()
        try:
            emetteur = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
            emetteur.sendto(serialiser({"type": "type_que_le_serveur_ignore", "version": 1,
                                        "tick": 5}),
                            ("127.0.0.1", ecouteur.port))
            limite = time.time() + 3.0
            while ecouteur.compteurs()["recues"] < 1 and time.time() < limite:
                time.sleep(0.05)
            self.assertEqual(ecouteur.compteurs()["recues"], 1)
            self.assertEqual(ecouteur.compteurs()["ignorees"], 0)
            self.assertIsNone(bus.activite())
            self.assertIsNone(bus.structure())
            self.assertEqual(bus.evenements_depuis(0)[0], [])
            emetteur.close()
        finally:
            ecouteur.arreter()


# ---------------------------------------------------------------------------
# Tâche 5 — la page three.js et le vendor
# ---------------------------------------------------------------------------

STATIQUE = (Path(__file__).resolve().parent.parent
            / "src" / "naulthene" / "instruments" / "cerveau_3d" / "static")

# Noms STABLES de `app.js` — CONTRAT DE SONDE, déclaré dans l'en-tête du fichier livré. La sonde
# les exporte depuis une COPIE temporaire : le fichier livré, lui, n'exporte rien (un navigateur
# n'en a pas besoin, et `node --check` n'en dépend pas).
SONDE_EXPORTS = ("construireStructure, appliquerActivite, construireAretes, float16VersFloat32, "
                 "base64EnOctets, noeuds, aretes")

# Le seul élément qu'un navigateur apporte et que `node` n'a pas : le moteur de rendu WebGL.
# Tout le reste de la sonde est le VRAI `three.core.min.js` vendorisé.
SHIM_THREE = """\
// three.module.js de la SONDE : le vrai three.js vendorisé + un WebGLRenderer sans WebGL.
export * from './three.core.min.js';
export class WebGLRenderer {
  constructor() { this.domElement = { addEventListener() {} }; }
  setPixelRatio() {} setSize() {} render() {}
}
"""

# Valeurs que le float16 représenté sait distinguer : sous-normal, maximum, signe, zéro, arrondi.
VALEURS_FLOAT16_EXTREMES = (1.0, 0.5, -2.5, 0.0, 65504.0, 5.960464477539063e-08, 1e-05)

SONDE_JS = r"""
// sonde.mjs — exécute la page LIVRÉE sous `node`, contre le VRAI three.js vendorisé.
//
// Ce que la sonde prouve : la LOGIQUE de la page (décodage base64/float16, 12 plaques, colonne
// du bus, seuil, activation absente → gris) et le fait que le vendor FONCTIONNE (REVISION 180,
// vraies classes InstancedMesh/Color/BufferGeometry). Ce qu'elle ne prouve pas : le RENDU
// (aucun WebGL ici) — il est vérifié par l'auteur dans un navigateur.
import { readFileSync } from 'node:fs';

const trames = JSON.parse(readFileSync(new URL('./trames.json', import.meta.url), 'utf8'));
const journal = {};

// --- 1. Le DOM minimal : les seules globales que la page reçoit d'un navigateur.
const elements = new Map();
function element(id) {
  if (!elements.has(id)) {
    elements.set(id, { id, textContent: '', value: '', ecouteurs: {},
                       addEventListener(nom, f) { this.ecouteurs[nom] = f; } });
  }
  return elements.get(id);
}
globalThis.document = { body: { appendChild() {} }, getElementById: element };
globalThis.addEventListener = () => {};
globalThis.innerWidth = 1200;
globalThis.innerHeight = 800;
globalThis.devicePixelRatio = 1;
globalThis.requestAnimationFrame = () => 0;
globalThis.EventSource = class {
  constructor(url) { this.url = url; this.ecouteurs = {}; globalThis.__flux = this; }
  addEventListener(nom, f) { this.ecouteurs[nom] = f; }
};
if (process.env.SANS_GETFLOAT16 === '1') delete DataView.prototype.getFloat16;

// --- 2. La page livrée (le seul ajout de la sonde : la ligne `export`).
const app = await import('./app.js');
const three = await import('./three.module.js');
journal.revision = three.REVISION;
journal.sse = globalThis.__flux ? globalThis.__flux.url : null;
journal.sse_evenements = Object.keys(globalThis.__flux ? globalThis.__flux.ecouteurs : {});

// --- 3. La structure : plaques, positions, colonne du bus.
function couleursLues() {
  const attribut = app.noeuds.maillage.instanceColor;
  const sortie = [];
  if (!attribut) return sortie;
  for (let i = 0; i < app.noeuds.maillage.count; i++) {
    sortie.push([attribut.array[i * 3], attribut.array[i * 3 + 1], attribut.array[i * 3 + 2]]);
  }
  return sortie;
}
app.construireStructure(trames.structure);
journal.nb_couches = app.noeuds.couches.length;
journal.nb_instances = app.noeuds.maillage.count;
journal.debuts = app.noeuds.couches.map(c => c._debut);
journal.positions = app.noeuds.positions;
journal.colonne = app.noeuds.colonne;
journal.texte_structure = element('structure').textContent;
journal.couleurs_construction = couleursLues();

// --- 4. Le seuil, par l'ÉVÉNEMENT du curseur (jamais un appel interne).
function reglerSeuil(valeur) {
  const curseur = element('seuil');
  curseur.value = String(valeur);
  curseur.ecouteurs.input();
  return { paires: app.aretes.paires.length,
           sommets: app.aretes.lignes.geometry.getAttribute('position').array.length,
           texte: element('valeur-seuil').textContent };
}
journal.seuil_0 = reglerSeuil(0);
journal.seuil_15 = reglerSeuil(15);
journal.seuil_60 = reglerSeuil(60);
journal.seuil_100 = reglerSeuil(100);
journal.seuil_15_bis = reglerSeuil(15);

const sommets = app.aretes.lignes.geometry.getAttribute('position').array;
// ⚠️ `Math.fround` : les positions vivent en float64 dans `noeuds.positions` et sont ÉCRITES en
// float32 dans le tampon de la géométrie. Comparer les deux représentations sans arrondir ferait
// échouer la sonde sur un artefact de précision, pas sur un défaut de la page.
const points = new Set();
for (let k = 0; k < app.noeuds.colonne.taille; k++) {
  const p = app.noeuds.positions[app.noeuds.colonne.debut + k];
  points.add(Math.fround(p[0]) + '|' + Math.fround(p[1]) + '|' + Math.fround(p[2]));
}
let nulles = 0, horsColonne = 0;
for (let k = 0; k < app.aretes.paires.length; k++) {
  const a = [sommets[k * 6], sommets[k * 6 + 1], sommets[k * 6 + 2]];
  const b = [sommets[k * 6 + 3], sommets[k * 6 + 4], sommets[k * 6 + 5]];
  if (a[0] === b[0] && a[1] === b[1] && a[2] === b[2]) nulles++;
  if (!points.has(a[0] + '|' + a[1] + '|' + a[2])) horsColonne++;
}
journal.aretes_nulles = nulles;
journal.aretes_hors_colonne = horsColonne;
journal.hors_bornes = app.aretes.horsBornes;

// --- 5. Le décodage float16, sur des valeurs extrêmes.
journal.repli = Array.from(app.float16VersFloat32(app.base64EnOctets(trames.repli)));
journal.repli_sans_natif = typeof DataView.prototype.getFloat16 === 'function';

// --- 6. L'activité : une couche ABSENTE (`null`), une couche NULLE, le reste allumé.
app.appliquerActivite(trames.activite);
journal.couleurs = couleursLues();
journal.texte_infos = element('infos').textContent;

console.log(JSON.stringify(journal));
"""


def _structure_pour_la_sonde(dim_bus=16, graine=11):
    """Une trame `structure` RÉELLE (constructeurs de la tâche 2), à `dim_bus = 16`."""
    from naulthene.cerveau.telemetrie import (DIM_AUDIO_ENTREE, DIM_VECTEUR_BIO, DIM_VISUELLE,
                                              NUM_ACTIONS, definir_couches, disposition,
                                              encoder_octets, quantifier_matrice,
                                              trame_structure)
    couches = definir_couches(dim_bus)
    geometrie, rng = disposition(couches), np.random.default_rng(graine)
    encodees = []
    for couche in couches:
        poids = rng.normal(0.0, 0.05,
                           size=(couche["sortie"], couche["entree"])).astype(np.float32)
        octets, echelle = quantifier_matrice(poids)
        encodees.append({**couche, "echelle": echelle, "poids_i8": encoder_octets(octets),
                         "positions": encoder_octets(
                             geometrie[couche["nom"]].astype(np.float16).tobytes())})
    bornes = [
        {"nom": "vision", "dim": DIM_VISUELLE, "couche": "porte_visuelle",
         "rang_entree": [0, DIM_VISUELLE]},
        {"nom": "audio", "dim": DIM_AUDIO_ENTREE, "couche": "porte_auditive",
         "rang_entree": [0, DIM_AUDIO_ENTREE]},
        # ⚠️ Le vecteur bio arrive APRÈS le bus (`cat([pensee, vecteur_bio])`, noyau.py)…
        {"nom": "vecteur_bio", "dim": DIM_VECTEUR_BIO, "couche": "integrateur_bio",
         "rang_entree": [dim_bus, dim_bus + DIM_VECTEUR_BIO]},
        # … alors que les actions arrivent AVANT le bus (`cat([actions_onehot, pensee])`).
        {"nom": "actions", "dim": NUM_ACTIONS, "couche": "generateur_attente",
         "rang_entree": [0, NUM_ACTIONS]},
        {"nom": "actions", "dim": NUM_ACTIONS, "couche": "generateur_attente_audio",
         "rang_entree": [0, NUM_ACTIONS]},
    ]
    return trame_structure(encodees, bornes,
                           {"jour": 4, "tick_absolu": 57, "dim_bus": dim_bus,
                            "niveau": {"index": 0, "affiche": "1/15",
                                       "env_id": "MiniGrid-Empty-5x5-v0"}})


def _activite_pour_la_sonde(structure, graine=12):
    """`analyseur` ABSENTE (`null`), `porte_visuelle` NULLE, le reste allumé (`float16`)."""
    from naulthene.cerveau.telemetrie import encoder_octets, trame_activite
    rng, neurones = np.random.default_rng(graine), {}
    for couche in structure["couches"]:
        if couche["nom"] == "analyseur":
            neurones[couche["nom"]] = None                        # ABSENTE → neurones GRIS
        elif couche["nom"] == "porte_visuelle":
            neurones[couche["nom"]] = encoder_octets(
                np.zeros(couche["sortie"], dtype=np.float16).tobytes())   # nulle → gris aussi
        else:
            neurones[couche["nom"]] = encoder_octets(
                rng.uniform(0.2, 1.0, size=couche["sortie"]).astype(np.float16).tobytes())
    return trame_activite(neurones,
                          {"dopamine": 0.31, "force_planification": None, "action": None},
                          {"jour": 4, "tick": 57})


def _trames_pour_la_sonde():
    from naulthene.cerveau.telemetrie import encoder_octets
    structure = _structure_pour_la_sonde()
    return {"structure": structure,
            "activite": _activite_pour_la_sonde(structure),
            "repli": encoder_octets(np.asarray(VALEURS_FLOAT16_EXTREMES,
                                               dtype=np.float16).tobytes())}


_SONDES = {}


def _sonde_de_la_page(sans_natif=False):
    """Exécute la page livrée sous `node` (VRAI three.js vendorisé) et rend son journal.

    `sans_natif=True` retire `DataView.prototype.getFloat16` AVANT l'import de la page : c'est
    le navigateur ancien — ou Node 22 — et la page doit s'y comporter à l'identique.
    """
    if sans_natif in _SONDES:
        return _SONDES[sans_natif]
    with tempfile.TemporaryDirectory() as dossier:
        dossier = Path(dossier)
        shutil.copyfile(STATIQUE / "three.core.min.js", dossier / "three.core.min.js")
        (dossier / "three.module.js").write_text(SHIM_THREE, encoding="utf-8")
        (dossier / "app.js").write_text((STATIQUE / "app.js").read_text(encoding="utf-8")
                                        + f"\nexport {{ {SONDE_EXPORTS} }};\n", encoding="utf-8")
        (dossier / "sonde.mjs").write_text(SONDE_JS, encoding="utf-8")
        (dossier / "trames.json").write_text(json.dumps(_trames_pour_la_sonde()), encoding="utf-8")
        resultat = subprocess.run([shutil.which("node"), "sonde.mjs"], cwd=str(dossier),
                                  capture_output=True, text=True, timeout=180,
                                  env={**os.environ,
                                       "SANS_GETFLOAT16": "1" if sans_natif else "0"})
        if resultat.returncode != 0:
            raise AssertionError(f"la sonde est sortie en {resultat.returncode} :\n"
                                 f"{resultat.stderr[-4000:]}")
        journal = json.loads(resultat.stdout.strip().splitlines()[-1])
    _SONDES[sans_natif] = journal
    return journal


class TestPageEtVendor(unittest.TestCase):
    """Les fichiers livrés et le vendor de three.js — pinné, complet, servi localement."""

    def test_fichiers_statiques_presents(self):
        for nom in ("index.html", "app.js", "three.module.js", "LICENSE-three.txt"):
            self.assertTrue((STATIQUE / nom).is_file(), nom)
        self.assertEqual((STATIQUE / "three.module.js").stat().st_size, 338908)
        licence = (STATIQUE / "LICENSE-three.txt").read_text(encoding="utf-8")
        self.assertIn("MIT", licence)
        self.assertIn("three.js", licence)

    @unittest.skipUnless(shutil.which("node"), "node absent : la page n'est pas vérifiée")
    def test_app_js_est_du_javascript_valide(self):
        resultat = subprocess.run(["node", "--check", str(STATIQUE / "app.js")],
                                  capture_output=True, text=True)
        self.assertEqual(resultat.returncode, 0, resultat.stderr)

    def test_index_reference_le_module_et_le_vendor(self):
        page = (STATIQUE / "index.html").read_text(encoding="utf-8")
        self.assertIn("./app.js", page)
        self.assertIn("./three.module.js", page)

    def test_aucun_chargement_reseau_dans_la_page(self):
        """Contrainte globale VIS-01 : le runtime ne dépend JAMAIS d'un CDN."""
        for nom in ("index.html", "app.js"):
            with self.subTest(fichier=nom):
                texte = (STATIQUE / nom).read_text(encoding="utf-8")
                for interdit in ("http://", "https://", "//unpkg", "//cdn"):
                    self.assertNotIn(interdit, texte, f"{nom} charge quelque chose du réseau")

    def test_le_vendor_est_complet_et_servi(self):
        """Critère n°3, étendu à ce que le vendor IMPORTE — le défaut mesuré le 10/09/2026.

        ⚠️ `build/three.module.min.js` de la v0.180.0 (338 908 octets, le fichier que le plan
        épingle) n'est **PAS autonome** : sa sixième ligne importe `"./three.core.min.js"`
        (381 124 octets), qui porte les classes partagées (`InstancedMesh`, `Color`, `Scene`,
        `SphereGeometry`…). Vendoriser le seul fichier pinné produit donc un 404 sur le core, et
        la page ne s'affiche jamais — sans qu'aucun test de taille ne s'en aperçoive.

        Ce test exige que CHAQUE import relatif du vendor existe sur le disque ET soit servi en
        `text/javascript` : c'est le seul contrôle qui relie le contenu du fichier pinné au
        dossier statique.
        """
        import re
        import urllib.request
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        source = (STATIQUE / "three.module.js").read_text(encoding="utf-8")
        dependances = sorted(set(re.findall(r'from"(\.[^"]+)"', source)))
        serveur = ServeurCerveau3D(BusTrames(), port=0)
        serveur.demarrer_en_thread()
        try:
            for dependance in dependances:
                with self.subTest(dependance=dependance):
                    chemin = "/" + dependance.lstrip("./")
                    fichier = STATIQUE / chemin.lstrip("/")
                    self.assertTrue(fichier.is_file(),
                                    f"le vendor importe {dependance}, qui n'est pas vendorisé")
                    with urllib.request.urlopen(
                            f"http://127.0.0.1:{serveur.port}{chemin}") as r:
                        self.assertEqual(r.status, 200)
                        self.assertEqual(r.headers["Content-Type"],
                                         "text/javascript; charset=utf-8")
                        self.assertEqual(len(r.read()), fichier.stat().st_size)
        finally:
            serveur.arreter()

    def test_la_page_reelle_est_servie_avec_son_type(self):
        """Critère n°2, sur le dossier statique PAR DÉFAUT de `ServeurCerveau3D`."""
        import urllib.request
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.serveur import ServeurCerveau3D

        serveur = ServeurCerveau3D(BusTrames(), port=0)
        serveur.demarrer_en_thread()
        try:
            for chemin, type_attendu in (("/", "text/html"),
                                         ("/app.js", "text/javascript"),
                                         ("/three.module.js", "text/javascript"),
                                         ("/three.core.min.js", "text/javascript")):
                with self.subTest(chemin=chemin):
                    fichier = STATIQUE / ("index.html" if chemin == "/" else chemin.lstrip("/"))
                    with urllib.request.urlopen(
                            f"http://127.0.0.1:{serveur.port}{chemin}") as r:
                        self.assertEqual(r.status, 200)
                        self.assertEqual(r.headers["Content-Type"],
                                         type_attendu + "; charset=utf-8")
                        self.assertEqual(len(r.read()), fichier.stat().st_size)
        finally:
            serveur.arreter()


@unittest.skipUnless(shutil.which("node"), "node absent : la logique de la page n'est pas vérifiée")
class TestLogiqueDeLaPage(unittest.TestCase):
    """La page exécutée sous `node`, contre le VRAI three.js vendorisé (sonde).

    ⚠️ Ce que cette classe prouve : la LOGIQUE (décodage, 12 plaques, colonne du bus, seuil,
    activation absente → neurone gris) et que le vendor fonctionne réellement (`REVISION`,
    `InstancedMesh`, `Color`, `BufferGeometry`). Ce qu'elle ne prouve PAS : le RENDU — aucun
    WebGL ici. Le rendu est vérifié par l'auteur dans un navigateur (commande dans le rapport).
    """

    @classmethod
    def setUpClass(cls):
        cls.sonde = _sonde_de_la_page()
        cls.sonde_sans_natif = _sonde_de_la_page(sans_natif=True)
        cls.structure = _structure_pour_la_sonde()
        cls.rangs = {couche["nom"]: i for i, couche in enumerate(cls.structure["couches"])}

    def _debut_de(self, nom):
        return self.sonde["debuts"][self.rangs[nom]]

    def _sortie_de(self, nom):
        return self.structure["couches"][self.rangs[nom]]["sortie"]

    def test_le_vendor_est_bien_three_js_0_180_0(self):
        self.assertEqual(self.sonde["revision"], "180")

    def test_douze_plaques_et_la_colonne_du_bus(self):
        sorties = [couche["sortie"] for couche in self.structure["couches"]]
        attendus, curseur = [], 0
        for sortie in sorties:
            attendus.append(curseur)
            curseur += sortie
        self.assertEqual(self.sonde["nb_couches"], 12)
        self.assertEqual(self.sonde["debuts"], attendus)
        self.assertEqual(self.sonde["colonne"]["debut"], sum(sorties))
        self.assertEqual(self.sonde["colonne"]["taille"], 16)
        self.assertEqual(self.sonde["nb_instances"], sum(sorties) + 16)
        self.assertIn("12 couches", self.sonde["texte_structure"])
        # La colonne est bien une colonne : au centre, répartie sur la profondeur des plaques.
        colonne = [self.sonde["positions"][self.sonde["colonne"]["debut"] + k]
                   for k in range(self.sonde["colonne"]["taille"])]
        self.assertTrue(all(p[0] == 0.0 and p[1] == 0.0 for p in colonne))
        self.assertEqual(len({p[2] for p in colonne}), 16)

    def test_les_positions_decodees_sont_celles_du_serveur(self):
        """Le décodage base64/float16 doit rendre EXACTEMENT la géométrie calculée en Python."""
        from naulthene.cerveau.telemetrie import definir_couches, disposition
        geometrie = disposition(definir_couches(16))
        for couche in definir_couches(16):
            debut = self._debut_de(couche["nom"])
            attendu = geometrie[couche["nom"]].astype(np.float16).astype(np.float64)
            for i in range(couche["sortie"]):
                for axe in range(3):
                    self.assertAlmostEqual(self.sonde["positions"][debut + i][axe],
                                           float(attendu[i, axe]), places=6,
                                           msg=f"{couche['nom']} neurone {i} axe {axe}")

    def test_le_decodeur_float16_est_exact_sans_getfloat16(self):
        """Ruling : `DataView.getFloat16` peut manquer (Node 22, navigateur ancien) — et il lit
        en GROS-boutiste par défaut, alors que numpy écrit en PETIT-boutiste. La page ne doit
        donc pas en dépendre : le décodage est identique avec et sans."""
        attendu = [float(np.float16(v)) for v in VALEURS_FLOAT16_EXTREMES]
        self.assertEqual(self.sonde_sans_natif["repli_sans_natif"], False)
        for journal in (self.sonde, self.sonde_sans_natif):
            with self.subTest(natif=journal["repli_sans_natif"]):
                self.assertEqual(len(journal["repli"]), len(attendu))
                for obtenu, valeur in zip(journal["repli"], attendu):
                    self.assertAlmostEqual(obtenu, valeur, places=12)
        self.assertEqual(self.sonde["repli"], self.sonde_sans_natif["repli"])

    def test_le_seuil_change_le_nombre_d_aretes(self):
        """Critère de la tâche : le curseur doit changer VISIBLEMENT le nombre d'arêtes."""
        sonde = self.sonde
        for nom in ("seuil_0", "seuil_15", "seuil_60", "seuil_100", "seuil_15_bis"):
            self.assertEqual(sonde[nom]["sommets"], sonde[nom]["paires"] * 6, nom)
        self.assertGreater(sonde["seuil_0"]["paires"], sonde["seuil_15"]["paires"])
        self.assertGreater(sonde["seuil_15"]["paires"], sonde["seuil_60"]["paires"])
        self.assertGreater(sonde["seuil_60"]["paires"], sonde["seuil_100"]["paires"])
        self.assertEqual(sonde["seuil_15"]["texte"], "0.15")
        self.assertEqual(sonde["seuil_15_bis"]["paires"], sonde["seuil_15"]["paires"])
        self.assertIn("arêtes", sonde["texte_structure"])

    def test_les_aretes_relient_deux_neurones_distincts_de_la_colonne(self):
        """`rafraichirAretes` doit écrire deux EXTRÉMITÉS DISTINCTES, dont le neurone d'entrée.

        ⚠️ La version du plan reliait un neurone à lui-même (`const b = a`) : toutes les arêtes
        avaient une longueur NULLE, donc invisibles à l'écran alors que le compte affiché, lui,
        était juste — le seuil semblait « ne rien changer ». Le contrôle n'est pas un compte mais
        une GÉOMÉTRIE : chaque arête part d'un neurone de la colonne du bus (§5) et arrive
        ailleurs."""
        paires = self.sonde["seuil_15"]["paires"]
        self.assertGreater(paires, 0)
        self.assertEqual(self.sonde["aretes_hors_colonne"], 0,
                         "des arêtes ne partent pas d'un neurone de la colonne du bus")
        self.assertLess(self.sonde["aretes_nulles"], 0.01 * paires,
                        "des arêtes relient un neurone à lui-même (invisibles)")
        self.assertGreater(self.sonde["hors_bornes"], 0,
                           "les entrées non neuronales (bornes §5) ne sont pas comptées à part")

    def test_activation_absente_ou_nulle_donne_un_neurone_gris(self):
        """Ruling : `null` (ou une valeur absente) = activation ABSENTE → neurone GRIS.

        Le gris est celui de l'activation NULLE (`t = 0`) : la page ne distingue pas un `null`
        d'un zéro, mais ne l'INVENTE jamais non plus (spec §9)."""
        gris = [0.12, 0.12, 0.16]
        for nom in ("analyseur", "porte_visuelle"):
            debut = self._debut_de(nom)
            for i in range(self._sortie_de(nom)):
                for axe in range(3):
                    self.assertAlmostEqual(self.sonde["couleurs"][debut + i][axe], gris[axe],
                                           places=5, msg=f"{nom} neurone {i}")
        # Une plaque nourrie s'allume : sans quoi le test précédent serait vrai d'une page morte.
        debut = self._debut_de("tete_motrice")
        lumineux = [c[0] for c in self.sonde["couleurs"][debut:debut + self._sortie_de(
            "tete_motrice")]]
        self.assertGreater(max(lumineux), 0.5, lumineux)
        # La colonne du bus n'est ni allumée ni inventée : elle n'est pas dans la trame d'activité.
        base = self.sonde["colonne"]["debut"]
        self.assertLess(max(c[0] for c in self.sonde["couleurs"][base:base + 16]), 0.5)

    def test_les_scalaires_nuls_ne_cassent_pas_la_ligne_d_infos(self):
        """`force_planification`/`action` à `null` : la ligne s'écrit quand même (spec §9)."""
        infos = self.sonde["texte_infos"]
        self.assertIn("tick 57", infos)
        self.assertIn("dopamine 0.310", infos)
        self.assertIn("planification 0.00", infos)
        self.assertIn("action —", infos)

    def test_la_page_se_connecte_au_flux_et_ecoute_les_trois_canaux(self):
        self.assertEqual(self.sonde["sse"], "/flux")
        self.assertEqual(sorted(self.sonde["sse_evenements"]),
                         ["activite", "evenement", "structure"])

    def test_toutes_les_instances_sont_colorees_des_la_construction(self):
        """`InstancedMesh` alloue ses couleurs à BLANC : un neurone oublié serait éclatant."""
        for i, couleur in enumerate(self.sonde["couleurs_construction"]):
            # 0,21 et non 0,20 : la couleur transite par un `Float32Array` (0,20 → 0,200000003).
            self.assertLessEqual(max(couleur), 0.21, f"instance {i} non colorée : {couleur}")


# ---------------------------------------------------------------------------
# Tâche 6 — la source factice, la CLI et la démonstration (étape 0)
# ---------------------------------------------------------------------------

RACINE_DEPOT = Path(__file__).resolve().parent.parent


class TestSourceFactice(unittest.TestCase):
    """La démonstration de l'étape 0 : un cerveau SYNTHÉTIQUE, sans `torch` ni `.brain`.

    ⚠️ Ces tests sont aussi la FIXTURE des tests du rendu (ruling du plan) : le mode factice
    n'est pas jetable, c'est ce qui permet de regarder la page et le serveur sans cerveau.
    """

    def test_forme_factice_egale_forme_reelle(self):
        """La fixture ne doit pas dériver de l'architecture réelle.

        ⚠️ C'est la garantie que `definir_couches` cite dans sa propre docstring — et c'est le nom
        qu'elle cite (`test_forme_factice_egale_forme_reelle`). L'esquisse de code du plan
        l'appelle `test_la_forme_factice_egale_la_forme_reelle` : un seul nom peut exister, sans
        quoi la citation de `telemetrie.py` pointerait dans le vide.

        La table doit décrire les couches d'un agent NEUF, comparées **en bloc** (`nom →
        (entree, sortie)`), jamais couche par couche — seule la comparaison en bloc discrimine
        une permutation de deux `entree` entre deux couches de même produit (cf. le
        contre-exemple mesuré du test de la tâche 2). Un agent neuf suffit : `dim_bus` ne change
        pas les formes relatives, et les `entree` non multiples du bus (`153 = 145 + 8`,
        `189 = 145 + 44`) sont vérifiés à `dim_bus = 16`.
        """
        from naulthene.cerveau.noyau import AGI_Naulthene, DIM_VISUELLE
        from naulthene.cerveau.telemetrie import definir_couches
        couches = definir_couches(16)
        agent = AGI_Naulthene(dim_visuelle=DIM_VISUELLE, dim_bus=16)
        reelles = {c["nom"]: (getattr(agent, c["nom"]).in_features,
                              getattr(agent, c["nom"]).out_features) for c in couches}
        attendues = {c["nom"]: (c["entree"], c["sortie"]) for c in couches}
        self.assertEqual(reelles, attendues)

    def test_boucle_factice_publie_structure_et_activite(self):
        """Critère n°1 : ~1 s à 20 Hz ⇒ une structure de 12 couches et ≥ 10 trames d'activité.

        ⚠️ Le seuil asserté est 10 et non 20 : les 20 trames attendues dépendent de
        l'ordonnancement de la machine, et exiger le maximum exact ferait échouer le test au
        premier hoquet sans qu'aucun contrat soit cassé. 10 est le plancher que la boucle ne
        peut pas manquer — elle publie sa première trame AVANT de dormir.
        """
        from naulthene.cerveau.telemetrie import BusTrames
        from naulthene.instruments.cerveau_3d.factice import boucle_factice
        bus = BusTrames()
        boucle_factice(bus, hz=20.0, dim_bus=16, duree=1.0)
        self.assertIsNotNone(bus.structure())
        self.assertEqual(len(bus.structure()["couches"]), 12)
        self.assertGreaterEqual(bus.sequence, 10)
        self.assertIn("porte_visuelle", bus.activite()["neurones"])

    def test_cli_repond_a_l_aide(self):
        """`--aide` est le contrat de la CLI (et non `--help` seul) : la sortie la NOMME.

        ⚠️ Trois assertions AJOUTÉES au test du plan, parce que le test tel qu'il est écrit
        passe au vert sur la panne même qu'il doit détecter : `python -m <paquet>` sans
        `__main__.py` écrit `No module named naulthene.instruments.cerveau_3d.__main__` — une
        sortie qui CONTIENT déjà la chaîne `cerveau_3d`. Sans le code de retour, le test ne
        distinguait pas « la CLI répond » de « la CLI n'existe pas ».
        """
        resultat = subprocess.run(
            ["venv/bin/python3", "-m", "naulthene.instruments.cerveau_3d", "--aide"],
            cwd=str(RACINE_DEPOT),          # `PYTHONPATH=src` est RELATIF à la racine du dépôt
            env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"}, capture_output=True, text=True,
            timeout=120)
        sortie = resultat.stdout + resultat.stderr
        self.assertEqual(resultat.returncode, 0, sortie[-2000:])
        self.assertNotIn("No module named", sortie)
        self.assertIn("cerveau_3d", sortie)
        # Les options du contrat (plan, tâche 6) sont TOUTES annoncées par l'aide.
        for option in ("--source", "--brain", "--port", "--hz", "--udp",
                       "--serveur-seul", "--duree"):
            self.assertIn(option, sortie, f"{option} absent de l'aide")

    def test_le_mode_factice_ne_charge_ni_torch_ni_noyau(self):
        """Point n°1 de la tâche : `factice` doit tourner sur une machine SANS cerveau.

        ⚠️ Mesuré dans un INTERPRÉTEUR NEUF (`-c`), jamais dans le processus de test : la suite
        importe `torch` (le test d'anti-dérive ci-dessus), donc `sys.modules` y est contaminé et
        un test en cours de processus passerait au vert sans rien prouver — même piège que
        `json.loads`, qui accepte `NaN` alors que `JSON.parse` le refuse (cf. `json_strict`).
        """
        code = ("import sys\n"
                "import naulthene.instruments.cerveau_3d.factice\n"
                "charges = sorted(m for m in sys.modules\n"
                "                 if m == 'torch' or m.startswith('torch.')\n"
                "                 or m == 'naulthene.cerveau.noyau')\n"
                "print('|'.join(charges))\n")
        resultat = subprocess.run(
            [sys.executable, "-c", code], cwd=str(RACINE_DEPOT),
            env={**os.environ, "PYTHONPATH": "src"}, capture_output=True, text=True, timeout=180)
        self.assertEqual(resultat.returncode, 0, resultat.stderr[-2000:])
        self.assertEqual(resultat.stdout.strip(), "",
                         f"la source factice a chargé un cerveau : {resultat.stdout.strip()}")

    def test_cli_affiche_l_url_du_serveur_et_sort_apres_la_duree(self):
        """Critère n°3, seconde moitié : la CLI annonce l'URL, puis rend la main sur `--duree`.

        `--port 0` laisse le système choisir un port LIBRE, que la bannière affiche tel quel
        (c'est le port réellement lié, jamais celui demandé) : deux exécutions simultanées ne se
        marchent pas dessus. Le processus doit se terminer SEUL — sinon `timeout` le tue et
        l'assertion ne dit plus rien.
        """
        resultat = subprocess.run(
            ["venv/bin/python3", "-m", "naulthene.instruments.cerveau_3d",
             "--source", "factice", "--port", "0", "--duree", "1"],
            cwd=str(RACINE_DEPOT),
            env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"}, capture_output=True, text=True,
            timeout=90)
        self.assertEqual(resultat.returncode, 0, resultat.stderr[-2000:])
        self.assertIn("http://127.0.0.1:", resultat.stdout)
        self.assertIn("lecture seule", resultat.stdout)
