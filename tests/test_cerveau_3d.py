#!/usr/bin/env python3
"""VIS-01 — contrats du cerveau 3D (registre VIS-01, spec du 10/09/2026).

Aucune dépendance ajoutée : `http.server`/`socket`/`json` de la bibliothèque standard,
`numpy` déjà requis par le projet ; `torch` est importé UNIQUEMENT par les tests qui
instancient un vrai cerveau.

    NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests
"""
import contextlib
import json
import unittest

import numpy as np

from naulthene.cerveau.telemetrie import serialiser   # tâche 4 : l'écouteur UDP reçoit des OCTETS


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

    ⚠️ AUCUN fichier n'est créé sous `src/naulthene/instruments/cerveau_3d/static/` (la page est la
    tâche 5) : les dossiers statiques de ces tests sont TEMPORAIRES et passés par
    `dossier_statique=`.
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
