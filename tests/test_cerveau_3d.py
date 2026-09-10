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
        from naulthene.cerveau.telemetrie import definir_couches
        couches = {c["nom"]: (c["entree"], c["sortie"]) for c in definir_couches(145)}
        self.assertEqual(len(couches), 12)
        self.assertEqual(couches["porte_visuelle"], (147, 145))
        self.assertEqual(couches["hippocampe"], (290, 145))
        self.assertEqual(couches["integrateur_bio"], (189, 145))   # 145 + 44 dims bio
        self.assertEqual(couches["tete_motrice"], (145, 8))
        self.assertEqual(couches["cortex_prefrontal"], (145, 1))
        self.assertEqual(couches["generateur_attente"], (153, 145))
        self.assertEqual(couches["tete_requete"], (145, 5))

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
