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


# La graine de NAISSANCE : `base_weight` et `norme_naissance` de chaque
# `NaultheneLinearSynaptique` sont tirés du RNG torch AU MOMENT DE LA NAISSANCE. Deux
# cerveaux neufs ne sont donc comparables que si l'on seede AVANT `charger_ou_naitre()`.
# Mesuré (revue indépendante) : deux naissances seedées donnent 0 tick divergent sur 261.
#
# ⚠️ LA NAISSANCE NE TIRE **RIEN** DU `np.random` GLOBAL — vérifié, et l'hypothèse
# inverse a été testée avant d'être écartée. Mesuré : (1) `np.random.get_state()[2]`
# vaut **624 avant et après** un `charger_ou_naitre()` complet — zéro tirage consommé ;
# (2) deux naissances seedées en torch donnent le MÊME `state_dict`
# (`sha256 = 134895af4844680b`) que l'on seede `np.random` ou non ; (3) une empreinte
# LARGE de tout `vars(etat)` (`4817393f8d31475d`) reste identique quand les deux
# naissances partent de **deux états `np.random` différents**. Un `np.random.seed(...)`
# avant la naissance n'est donc pas seulement inutile : il **affaiblirait** ce test, en
# resynchronisant le flux global entre les deux passes — ce qui masquerait un
# `np.random.seed(graine)` manquant DANS l'évaluation (mesuré : mutant M1 tué aujourd'hui
# précisément parce que les deux flux np.random diffèrent).
GRAINE_DE_NAISSANCE: int = 20260912

# Bruit ambiant de DEUXIÈME passe, en tirages torch ET numpy consommés après la naissance
# et AVANT l'évaluation. Rôle : rendre les deux passes structurellement comparables à ce
# que vit le banc réel — `executer_banc` (tâche 5) évalue les cerveaux les uns après les
# autres dans le MÊME processus, donc les états ambiants des deux évaluations DIFFÈRENT.
# Sans cette dissymétrie, la graine de naissance resynchronise déjà torch et numpy : un
# `torch.manual_seed(graine)` retiré de la boucle d'évaluation reste alors invisible
# (mesuré : mutant M4 vert sans ce bruit, rouge avec). Le montant est arbitraire et sans
# effet sur le verdict (mesuré à 1, 37 et 101 : même résultat) ; seul compte le fait que
# les deux états initiaux diffèrent.
BRUIT_AMBIANT: int = 37


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
    """Le banc ACTUEL du dépôt n'est pas reproductible : `noyau.py` échantillonne l'action
    (`Categorical(...).sample()`) et l'ancien outil ne fixait aucune graine torch.

    ⚠️ Ce test évalue DEUX cerveaux NÉS SOUS LA MÊME GRAINE, chacun évalué UNE FOIS. Une
    version antérieure évaluait UN seul `etat` deux fois de suite : deux appels sur le même
    état ne mesurent pas la même chose, le cerveau portant un état d'un appel à l'autre
    (mesuré par la revue indépendante : carte 4, victoires **0, 0, 1** selon les appels, et un
    épisode qui passe de 61 à **88** ticks, soit **+44 %** sur `longueur_normalisee` ; ce
    constat est un prérequis de la tâche 5, qui doit fournir un état FRAIS par (bras, carte)).

    ⚠️ L'assertion porte sur le résultat COMPLET, pas sur un triplet. Trois générateurs
    décident d'un épisode (le monde via `_graine_episode`, le `np.random` global, torch) :
    deux passes peuvent partager un nombre de victoires tout en ayant joué des trajectoires
    différentes. Comparer `(gagnes, tronques, optimal)` est un critère FAIBLE ; ce que D1
    promet — un δ_A/A nul — est l'identité de l'évaluation, pas celle d'un résumé. Ce qui est
    comparé inclut donc `trajectoire`, le seul champ sensible au COMPORTEMENT.

    ⚠️ LA CARTE ÉVALUÉE EST LA 3, PAS LA 0 — et c'est mesuré. Sur la carte 0, un cerveau neuf
    est SUR SA PROPRE CARTE DE CURSUS : le tirage vaut 0 trois fois sur trois, donc
    `_appliquer_niveau_episode` ne remplace jamais l'environnement et un re-forçage manquant
    est **invisible** — mutation rejouée : 13 tests `OK` malgré le retrait. Sur la carte 3 (une
    carte du plan, `CARTES_GELEES = (3, 4)`), la dérive est réelle : épisode 1 à 324 ticks,
    puis les suivants sur `Empty-5x5` à 100 ticks. C'est aussi pourquoi la carte IMPOSÉE est
    nommée explicitement pour chaque épisode, au lieu de dépendre d'une égalité globale.

    ⚠️ DEUX MUTANTS SURVIVAIENT À LA SEULE ÉGALITÉ DES DEUX PASSES, ET C'EST MESURÉ — d'où les
    deux ajouts qui les tuent, chacun justifié par sa propre mesure :
      - **M4, le levier `torch.manual_seed(graine)`** : la graine de NAISSANCE resynchronise
        déjà le flux torch des deux passes, qui consomment ensuite exactement la même suite.
        Une ligne retirée dans la boucle d'évaluation restait donc invisible. D'où
        `BRUIT_AMBIANT` : les deux passes partent d'états ambiants DIFFÉRENTS, comme les
        évaluations successives du banc réel. M4 est alors tué — et tué par le SEUL champ
        `trajectoire` (mesuré : M4 + retrait de `trajectoire` redevient vert), ce qui prouve du
        même coup la nécessité du résumé de trajectoire exigé au correctif I2 ;
      - **M2, la graine du monde (`graine_run` / `episodes_vecus`)** : à la naissance,
        `graine_run` est ABSENT et `episodes_vecus` vaut **0** — dans les DEUX passes. Le
        compteur redémarre donc à l'identique, et deux passes également fausses restent égales
        entre elles. Aucune comparaison de passes ne peut voir ce mutant ; seule l'assertion
        `monde["graine"] == graine` le nomme, et c'est littéralement la promesse de D-2
        (« le monde est exactement `s` »).
    """

    def test_deux_evaluations_identiques_donnent_le_meme_resultat(self):
        import numpy as np
        import torch

        from naulthene.cerveau.persistance import PersistanceAnatomique
        from naulthene.instruments.banc_final import evaluer_cerveau_sur_carte

        def une_passe(bruit_ambiant: int):
            # La NAISSANCE est tirée du RNG torch : on seede AVANT de naître, sans quoi les
            # deux cerveaux comparés seraient deux individus différents.
            torch.manual_seed(GRAINE_DE_NAISSANCE)
            with tempfile.TemporaryDirectory() as d:
                etat = PersistanceAnatomique(
                    fichier=os.path.join(d, "neuf.brain")).charger_ou_naitre()
                etat.agent.eval()
                # ⚠️ LE BRUIT AMBIANT DIFFÈRE ENTRE LES DEUX PASSES (voir BRUIT_AMBIANT) :
                # c'est la condition du banc réel, où les évaluations se SUIVENT dans le même
                # processus. Un résultat ne vaut que s'il ne dépend ni de ce bruit, ni de
                # l'ordre des appels — c'est exactement ce que D1 promet.
                torch.manual_seed(0)
                np.random.seed(0)
                for _ in range(bruit_ambiant):
                    torch.rand(1)
                    np.random.random()
                resultat = evaluer_cerveau_sur_carte(etat, 3, [10000, 10001, 10002])
                etat.env.close()
                return resultat

        premiere, seconde = une_passe(0), une_passe(BRUIT_AMBIANT)

        from naulthene.cerveau.noyau import PROGRAMME
        carte_imposee = PROGRAMME[3][0]
        for episode in premiere["episodes"]:
            self.assertEqual(
                episode["env_id"], carte_imposee,
                "chaque épisode doit avoir joué la carte IMPOSÉE, pas une carte du cursus")
            # ⚠️ L'IDENTITÉ D'ÉPISODE EST `graine`, ET LE MONDE DOIT ÊTRE CETTE GRAINE.
            # C'est la promesse d'appariement des tâches 5-9 : à graine égale, deux bras
            # affrontent le MÊME monde. L'égalité des deux passes ne peut PAS la vérifier
            # seule — mesuré : `graine_run` est ABSENT et `episodes_vecus` vaut **0** à la
            # naissance dans les DEUX passes, donc le compteur redémarre à la même valeur et
            # un `episodes_vecus = graine` retiré laisse les deux passes se ressembler
            # (mutant M2 : vert sans cette assertion, rouge avec).
            self.assertEqual(
                episode["monde"]["graine"], episode["graine"],
                "le monde de l'épisode doit être celui de son identité `graine`")

        self.assertEqual(premiere, seconde,
                         "deux évaluations du MÊME cerveau doivent être identiques en tout")


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


class TestInstrumentIndisponible(unittest.TestCase):
    """Un garde non PROUVÉ branché ne garde rien — leçon de la tâche 3, où un garde posé sur
    le seul chemin glob laissait le succès silencieux intact sur la voie explicite. Ce test
    retire donc les instruments EN MÉMOIRE et exige que la mesure soit REFUSÉE.

    Sans ces gardes, un renommage dans `noyau.py` ferait tomber tous les `retour` à 0,0
    (`mix_somme.get("Env", 0.0)`) et toutes les empreintes de monde à vide
    (`getattr(detecteur, "positions_food", None)`) : des métriques fausses, publiées sans une
    seule erreur, alors que `retour_moyen` appartient à la famille de métriques gelée.
    """

    def test_un_instrument_retire_empeche_la_mesure(self):
        from naulthene.cerveau.persistance import PersistanceAnatomique
        from naulthene.instruments.banc_final import (InstrumentIndisponible,
                                                      evaluer_cerveau_sur_carte)

        with tempfile.TemporaryDirectory() as d:
            etat = PersistanceAnatomique(
                fichier=os.path.join(d, "neuf.brain")).charger_ou_naitre()
            etat.agent.eval()
            evaluer_cerveau_sur_carte(etat, 0, [10000], max_ticks=5)  # la sonde a parlé

            # 1. L'instrument RETIRÉ en mémoire : le canal de récompense d'environnement.
            etat.mix_somme.pop("Env")
            with self.assertRaises(InstrumentIndisponible) as ctx:
                evaluer_cerveau_sur_carte(etat, 0, [10001], max_ticks=5)
            self.assertIn("Env", str(ctx.exception))

            # 2. Le second instrument : les positions semées, sans lesquelles l'empreinte du
            #    monde serait publiée VIDE. On restaure d'abord le canal de récompense, sinon
            #    le garde n° 1 crierait avant que celui-ci ne soit atteint.
            etat.mix_somme["Env"] = 0.0
            del etat.detecteur_ressources_bio.positions_food
            with self.assertRaises(InstrumentIndisponible) as ctx:
                evaluer_cerveau_sur_carte(etat, 0, [10002], max_ticks=5)
            self.assertIn("positions_food", str(ctx.exception))

            etat.env.close()


if __name__ == "__main__":
    unittest.main()
