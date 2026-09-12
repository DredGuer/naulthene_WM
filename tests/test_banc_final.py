#!/usr/bin/env python3
"""Contrats du banc final standardisé (chantier EVA-01).

    NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests -p "test_banc_final.py" -v

Ce que ces tests verrouillent :

- un nom de cerveau ambigu (`X_g11 2.brain`) doit faire ÉCHOUER le banc en le NOMMANT :
  ces fichiers existent réellement dans brains/08092026_sci01_balayage_K/ et leurs
  contenus diffèrent (CHANTIER_EVA-01 §3.5). Choisir en silence fausserait l'appariement ;
- le pool de graines d'évaluation ne doit jamais pouvoir collisionner avec le pool
  d'entraînement (5…199) ;
- `--episodes` n'a PAS de valeur par défaut : `n` est un résultat du pilote, pas une
  constante de confort (spec §8bis).
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from naulthene.instruments.banc_final import (  # noqa: E402
    BrasIntrouvable,
    EpisodesNonDerive,
    GraineEvalRefusee,
    NomAmbigue,
    exiger_episodes,
    lire_cohorte_explicite,
    lire_graines_du_manifeste,
    lister_cerveaux,
    main,
    resoudre_cohorte,
    verifier_graine_eval_base,
)


def _toucher(chemin):
    with open(chemin, "wb") as f:
        f.write(b"")


class TestListerCerveaux(unittest.TestCase):
    def test_trouve_les_noms_canoniques(self):
        with tempfile.TemporaryDirectory() as d:
            for g in (11, 22):
                _toucher(os.path.join(d, f"K8_NU_g{g}.brain"))
            trouves = lister_cerveaux(d, "K8_NU", [11, 22])
            self.assertEqual(sorted(trouves), [11, 22])
            self.assertTrue(trouves[11].endswith("K8_NU_g11.brain"))

    def test_refuse_un_nom_ambigu_en_le_nommant(self):
        with tempfile.TemporaryDirectory() as d:
            _toucher(os.path.join(d, "K8_NU_g11.brain"))
            _toucher(os.path.join(d, "K8_NU_g11 2.brain"))
            with self.assertRaises(NomAmbigue) as ctx:
                lister_cerveaux(d, "K8_NU", [11])
            self.assertIn("K8_NU_g11 2.brain", str(ctx.exception))

    def test_ignore_les_autres_bras(self):
        """Ne pas se contenter des CLÉS : le retour est indexé par graine, donc un cerveau
        d'un AUTRE bras écrase la même clé sans changer la liste des clés. Un motif qui
        ignorerait le préfixe de bras rendrait `{11: 'K8_NU_g11.brain'}` quand on demande
        K16_NU — contamination inter-bras invisible, et d'autant plus dangereuse que les
        6 bras partagent les MÊMES 20 graines.
        Les DEUX sens sont nécessaires : `sorted(os.listdir)` rend
        ['K16_NU_g11.brain', 'K8_NU_g11.brain'], donc pour le bras K8_NU le fichier demandé
        est traité EN DERNIER — un mutant « le dernier gagne » tombe alors sur le bon fichier
        par accident alphabétique. Seul le sens K16_NU, où le fichier demandé est traité en
        PREMIER, rend ce mutant visible — et « le dernier gagne » est exactement la sémantique
        du code réel (`canoniques[graine] = ...`, sans condition).
        """
        with tempfile.TemporaryDirectory() as d:
            _toucher(os.path.join(d, "K8_NU_g11.brain"))
            _toucher(os.path.join(d, "K16_NU_g11.brain"))
            for bras in ("K8_NU", "K16_NU"):
                with self.subTest(bras=bras):
                    trouves = lister_cerveaux(d, bras, [11])
                    self.assertEqual(sorted(trouves), [11])
                    self.assertTrue(
                        trouves[11].endswith(f"{bras}_g11.brain"),
                        f"le chemin résolu doit être celui du bras DEMANDÉ ({bras}) : {trouves[11]}")


class TestGardeFous(unittest.TestCase):
    def test_graine_eval_base_sous_le_minimum_est_refusee(self):
        with self.assertRaises(GraineEvalRefusee):
            verifier_graine_eval_base(500)
        verifier_graine_eval_base(10000)  # ne lève pas

    def test_episodes_non_derive_est_refuse(self):
        with self.assertRaises(EpisodesNonDerive):
            exiger_episodes(None)
        with self.assertRaises(EpisodesNonDerive):
            exiger_episodes(0)
        self.assertEqual(exiger_episodes(37), 37)


class TestManifesteDeCampagne(unittest.TestCase):
    def test_lit_les_graines_du_manifeste(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "manifeste.json"), "w", encoding="utf-8") as f:
                json.dump({"campagne": "essai", "graines": [11, 22, 33]}, f)
            self.assertEqual(lire_graines_du_manifeste(d), [11, 22, 33])

    def test_lit_les_graines_d_une_cohorte_explicite_runs(self):
        """Le manifeste connaît DEUX formes ; `runs` est une LISTE de dicts `{"nom": ...}`.
        N'en lire qu'une rendait un diagnostic FAUX sur un manifeste valide (cas réel :
        brains/02092026_rejeu_banc_corrige, 20 runs, mode explicite)."""
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "manifeste.json"), "w", encoding="utf-8") as f:
                json.dump({"campagne": "essai", "mode": "confirmatoire",
                           "runs": [{"nom": "A_g11", "fichier": "banc_A_g11.json"},
                                    {"nom": "B_g11", "fichier": "banc_B_g11.json"},
                                    {"nom": "B_g22", "fichier": "banc_B_g22.json"}]}, f)
            self.assertEqual(lire_graines_du_manifeste(d), [11, 22])





class TestCohorteExplicite(unittest.TestCase):
    """La spec exige une cohorte ENUMEREE quand un bras porte des surnumeraires : le glob
    refuserait K8_NU (2 doublons mesures le 12/09/2026), rendant le test d'acceptation
    impossible. Cette voie est l'echappatoire EXPLICITE et tracee."""

    def test_enumere_les_chemins_et_verifie_leur_existence(self):
        with tempfile.TemporaryDirectory() as d:
            a = os.path.join(d, "K8_NU_g11.brain")
            b = os.path.join(d, "K16_NU_g11.brain")
            _toucher(a)
            _toucher(b)
            inventaire = os.path.join(d, "cohorte.json")
            with open(inventaire, "w", encoding="utf-8") as f:
                json.dump({"K8_NU": {"11": a}, "K16_NU": {"11": b}}, f)
            cohorte = lire_cohorte_explicite(inventaire)
            self.assertEqual(sorted(cohorte), ["K16_NU", "K8_NU"])
            self.assertEqual(cohorte["K8_NU"][11], a)

    def test_un_chemin_absent_est_refuse_en_le_nommant(self):
        with tempfile.TemporaryDirectory() as d:
            inventaire = os.path.join(d, "cohorte.json")
            manquant = os.path.join(d, "absent.brain")
            with open(inventaire, "w", encoding="utf-8") as f:
                json.dump({"K8_NU": {"11": manquant}}, f)
            with self.assertRaises(ValueError) as ctx:
                lire_cohorte_explicite(inventaire)
            self.assertIn("absent.brain", str(ctx.exception))


class TestMainRefuseUnInventaireAMasVide(unittest.TestCase):
    """Le défaut I-3 était dans `main()`, pas dans le garde : il faut donc l'exercer par
    `main()` elle-même. Un garde posé sur le seul chemin glob laissait le succès silencieux
    intact sur la voie explicite — le chemin OBLIGATOIRE de la tâche 9."""

    def test_main_refuse_un_inventaire_explicite_avec_un_bras_vide(self):
        with tempfile.TemporaryDirectory() as d:
            chemin_brain = os.path.join(d, "K8_NU_g11.brain")
            _toucher(chemin_brain)
            with open(os.path.join(d, "manifeste.json"), "w", encoding="utf-8") as f:
                json.dump({"campagne": "essai", "graines": [11]}, f)
            inventaire = os.path.join(d, "cohorte.json")
            with open(inventaire, "w", encoding="utf-8") as f:
                json.dump({"K8_NU": {"11": chemin_brain}, "K2_NU": {}}, f)
            argv = ["banc_final", "--cohorte", d, "--bras", "K8_NU", "K2_NU",
                    "--episodes", "1", "--cohorte-explicite", inventaire]
            with mock.patch.object(sys, "argv", argv):
                with self.assertRaises(BrasIntrouvable) as ctx:
                    main()
            self.assertIn("K2_NU", str(ctx.exception))


class TestBrasIntrouvable(unittest.TestCase):
    """Un bras qui ne résout RIEN est une faute de frappe, pas une cohorte vide : sortir en 0
    en affichant `{'K16_NU_TYPO': 0}` était un succès silencieux (constat I-3)."""

    def test_un_bras_sans_cerveau_est_refuse_en_le_nommant(self):
        with tempfile.TemporaryDirectory() as d:
            _toucher(os.path.join(d, "K8_NU_g11.brain"))
            with self.assertRaises(BrasIntrouvable) as ctx:
                resoudre_cohorte(d, ["K8_NU_TYPO"], [11])
            self.assertIn("K8_NU_TYPO", str(ctx.exception))


class TestReproductibilite(unittest.TestCase):
    """Le banc ACTUEL n'est pas reproductible : noyau.py échantillonne l'action
    (Categorical(...).sample()) et evaluer_cerveau.py ne fixe aucune graine torch.
    Ce test verrouille le correctif : même cerveau + mêmes graines => mêmes résultats."""

    def test_deux_evaluations_identiques_donnent_le_meme_resultat(self):
        """⚠️ LE CERVEAU EST CONSTRUIT UNE SEULE FOIS, et c'est le POINT du test.

        La référence gelée appelait `une_passe()` deux fois avec, DANS chaque passe, un
        `charger_ou_naitre()` : elle comparait donc DEUX INDIVIDUS différents. La naissance
        n'est pas reproductible — `base_weight`/`norme_naissance` de chaque
        `NaultheneLinearSynaptique` sont tirés du RNG torch au moment de la naissance —
        et le test ne passait que lorsque les deux cerveaux tiraient le même nombre de
        victoires. Mesuré : `(1, 0, 4)` contre `(0, 0, 4)` sur la suite complète.

        Ce que le banc promet — le δ_A/A, attendu nul — est la reproductibilité pour un
        MÊME cerveau (c'est le cas réel : les tâches 5 à 9 rechargent des `.brain`). Le
        test le vérifie donc ainsi, sans changer ce qui est comparé.
        """
        from naulthene.cerveau.persistance import PersistanceAnatomique
        from naulthene.instruments.banc_final import evaluer_cerveau_sur_carte

        with tempfile.TemporaryDirectory() as d:
            etat = PersistanceAnatomique(
                fichier=os.path.join(d, "neuf.brain")).charger_ou_naitre()
            etat.agent.eval()
            premiere = evaluer_cerveau_sur_carte(etat, 0, [10000, 10001, 10002])
            seconde = evaluer_cerveau_sur_carte(etat, 0, [10000, 10001, 10002])
            etat.env.close()

        self.assertEqual(
            (premiere["gagnes"], premiere["tronques"], premiere["optimal"]),
            (seconde["gagnes"], seconde["tronques"], seconde["optimal"]))


class TestEpisodeTronque(unittest.TestCase):
    def test_un_episode_non_termine_est_compte_comme_echec_et_marque(self):
        """Un épisode qui n'atteint pas `fin_episode` dans le budget doit apparaître
        comme ÉCHEC avec `tronque=True` — jamais disparaître du dénominateur."""
        from naulthene.cerveau.persistance import PersistanceAnatomique
        from naulthene.instruments.banc_final import evaluer_cerveau_sur_carte

        with tempfile.TemporaryDirectory() as d:
            etat = PersistanceAnatomique(
                fichier=os.path.join(d, "neuf.brain")).charger_ou_naitre()
            etat.agent.eval()
            r = evaluer_cerveau_sur_carte(etat, 0, [10000], max_ticks=3)  # budget ridicule
            etat.env.close()
        self.assertEqual(len(r["episodes"]), 1)
        self.assertTrue(r["episodes"][0]["tronque"])
        self.assertFalse(r["episodes"][0]["gagne"])
        self.assertEqual(r["gagnes"], 0)
        self.assertIsInstance(r["episodes"][0]["retour"], float)
        self.assertIsNone(r["episodes"][0]["longueur_normalisee"])  # pas de gain => absente


if __name__ == "__main__":
    unittest.main()
