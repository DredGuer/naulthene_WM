#!/usr/bin/env python3
"""VIS-01 — contrats du cerveau 3D (registre VIS-01, spec du 10/09/2026).

Aucune dépendance ajoutée : `http.server`/`socket`/`json` de la bibliothèque standard,
`numpy` déjà requis par le projet ; `torch` est importé UNIQUEMENT par les tests qui
instancient un vrai cerveau.

    NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests
"""
import unittest

import numpy as np


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
