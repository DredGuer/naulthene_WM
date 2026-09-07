#!/usr/bin/env python3
"""QUA-01 — contrats cognitifs rapides (CPU). Registre MES-01 livra les 40 tests
stdlib du dépouillement ; cette suite verrouille les contrats du NOYAU clos depuis
v41.67 : API-01 (SortiePenser), APP-01 (parité de forme du rejeu), APP-02 (gradient
nocturne étanche), MES-02 (sonde trace on/off).

Commande (CPU, une seule ligne, aucune dépendance externe) :

    NAULTHENE_DEVICE=cpu venv/bin/python -m unittest discover -s tests

La suite doit rester < ~5 s (import torch compris) sur CPU.
"""
import os
import shutil
import tempfile
import unittest

import torch

BRAIN_TMP = os.path.join(tempfile.gettempdir(), "qua01_contrats.brain")

MODULE_DEFAUTS = {
    "SANS_C2": False,
    "BRAIN_SPARING_ACTIF": True,
    "CORPS_DANS_ROLLOUT_ACTIF": True,
    "DETACH_C2_ASYMETRIQUE": False,
    "EPOQUES_NUIT": 1,
}


class _Base(unittest.TestCase):
    """Un agent neuf partagé par classe (création coûteuse), régime remis aux défauts."""

    @classmethod
    def setUpClass(cls):
        import naulthene.cerveau.noyau as N
        from naulthene.cerveau.persistance import PersistanceAnatomique
        cls.N = N
        if os.path.exists(BRAIN_TMP):
            os.remove(BRAIN_TMP)
        cls.agent = PersistanceAnatomique(BRAIN_TMP).charger_ou_naitre(N.DEVICE).agent
        cls.agent.eval()
        cls.Persistance = PersistanceAnatomique

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(BRAIN_TMP)
        except OSError:
            pass

    def setUp(self):
        for k, v in MODULE_DEFAUTS.items():
            setattr(self.N, k, v)
        self.agent.gain_c1_libre = True

    def _entrees(self, graine=0):
        g = torch.Generator(device="cpu").manual_seed(graine)
        N, ag = self.N, self.agent
        obs = torch.rand(1, 147, generator=g, device=N.DEVICE) / 10.0
        mem = torch.zeros(1, ag.dim_bus, device=N.DEVICE)
        ctx = torch.zeros(1, ag.dim_bus, device=N.DEVICE)
        vbio = torch.rand(1, N.DIM_VECTEUR_BIO, generator=g, device=N.DEVICE)
        return obs, mem, ctx, vbio

    def _logits_penser(self, obs, mem, ctx, vbio, force=0.5, vigueur=1.0):
        ag, N = self.agent, self.N
        ag.mesure_arbitrage = None
        with torch.no_grad():
            sortie = ag.penser(obs, mem, ctx, vbio, force_planification=force,
                               vigueur=vigueur, plugs_c3_disponibles=[])
            gain = ag.mesure_arbitrage["gain_c1"] if ag.mesure_arbitrage else 1.0
            facteur = 1.0 if N.BRAIN_SPARING_ACTIF else float(vigueur)
            k1 = float(gain) * facteur
            k2 = float(force) * facteur
            rejoues, _ = ag._logits_politique_complete_rejouee(
                obs, mem, ctx, vbio,
                torch.tensor([[k1]], device=N.DEVICE, dtype=torch.float32),
                torch.tensor([[k2]], device=N.DEVICE, dtype=torch.float32))
        return sortie, rejoues


class TestApi01SortiePenser(_Base):
    def test_index_nom_deballage_identiques(self):
        obs, mem, ctx, vbio = self._entrees(1)
        with torch.no_grad():
            out = self.agent.penser(obs, mem, ctx, vbio, force_planification=0.5,
                                    vigueur=1.0, plugs_c3_disponibles=[])
        self.assertIsInstance(out, tuple)
        self.assertEqual(len(out), 8)
        for i, champ in enumerate(out._fields):
            a, b = out[i], getattr(out, champ)
            egal = bool(torch.equal(a, b)) if isinstance(a, torch.Tensor) else bool(a == b)
            self.assertTrue(egal, f"index {i} != nom {champ}")
        a, b, c, d, e, f_, g, h = out
        self.assertTrue(torch.equal(a, out.logits_action))
        self.assertTrue(torch.equal(e, out.memoire_actuelle))   # l'ancien piège [1] vs [4]
        self.assertTrue(torch.equal(out[1], out.valeur_etat_courant))
        self.assertEqual(type(out).__name__, "SortiePenser")


class TestApp01PariteRejeu(_Base):
    def _cellule(self, sans_c2, sparing, corps, libre, vigueur, force):
        N = self.N
        N.SANS_C2, N.BRAIN_SPARING_ACTIF = sans_c2, sparing
        N.CORPS_DANS_ROLLOUT_ACTIF = corps
        self.agent.gain_c1_libre = libre
        obs, mem, ctx, vbio = self._entrees(graine=int(force * 1000) % 1000)
        sortie, rejoues = self._logits_penser(obs, mem, ctx, vbio, force=force,
                                              vigueur=vigueur)
        jour = sortie.logits_action
        delta = float((jour[..., :N.NUM_ACTIONS_BASE]
                       - rejoues[..., :N.NUM_ACTIONS_BASE]).abs().max().item())
        if self.agent.num_actions > N.NUM_ACTIONS_BASE:
            self.assertTrue(bool((jour[..., N.NUM_ACTIONS_BASE:] == float("-inf")).all()))
            self.assertTrue(bool((rejoues[..., N.NUM_ACTIONS_BASE:] == float("-inf")).all()))
        self.assertLessEqual(delta, 1e-4, f"régime {sans_c2}/{sparing}/{corps}/{libre}")

    def test_parite_tous_regimes(self):
        for sans_c2 in (False, True):
            for sparing in (False, True):
                for corps in (False, True):
                    for libre in (True, False):
                        self._cellule(sans_c2, sparing, corps, libre,
                                      vigueur=0.9 if not sparing else 1.0, force=0.6)


class TestApp02GradientEtanche(_Base):
    def _norme_grad_integrateur(self):
        s = 0.0
        for p in self.agent.integrateur_bio.parameters():
            if p.grad is not None:
                s += float(p.grad.detach().pow(2).sum().cpu().item())
        return s ** 0.5

    def test_gradient_critique_zero_sous_detach(self):
        N, ag = self.N, self.agent
        ag.train()
        obs, mem, ctx, vbio = self._entrees(2)
        _, _, _, pensee_bio, _ = ag._executer_c1_reflexe(obs, mem, ctx, vbio)
        cible = torch.zeros_like(ag.cortex_prefrontal(pensee_bio))
        # Sans detach : le gradient du critique atteint integrateur_bio.
        N.DETACH_C2_ASYMETRIQUE = False
        ag.optimizer.zero_grad(set_to_none=True)
        torch.nn.functional.mse_loss(ag.cortex_prefrontal(pensee_bio), cible).backward()
        g_libre = self._norme_grad_integrateur()
        # Avec detach (règle appliquée sur CHAQUE passe du rejeu, v41.64) : 0 exact.
        N.DETACH_C2_ASYMETRIQUE = True
        ag.optimizer.zero_grad(set_to_none=True)
        entree = pensee_bio.detach()
        torch.nn.functional.mse_loss(ag.cortex_prefrontal(entree), cible).backward()
        g_detache = self._norme_grad_integrateur()
        self.assertGreater(g_libre, 0.0)
        self.assertEqual(g_detache, 0.0)


class TestMes02SondeTrace(_Base):
    def test_trace_off_inchange_et_on_capture(self):
        obs, mem, ctx, vbio = self._entrees(3)
        _, mem_new, _, pensee, _ = self.agent._executer_c1_reflexe(obs, mem, ctx, vbio)
        with torch.no_grad():
            ret_sans = self.agent.simuler_futur_et_planifier(pensee, mem_new,
                                                             vecteur_bio=None)
            captures = {}

            def _trace(horizon=0, pensee_branche=None, **_a):
                captures[horizon] = pensee_branche

            ret_avec = self.agent.simuler_futur_et_planifier(
                pensee, mem_new, vecteur_bio=None, trace_rollout=_trace)
        for x, y in zip(ret_sans, ret_avec):
            if isinstance(x, torch.Tensor):
                self.assertEqual(float((x - y).abs().max().item()), 0.0)
        for h in (1, 3, 7):
            self.assertIn(h, captures)
            self.assertEqual(tuple(captures[h].shape),
                             (self.agent.num_actions, self.agent.dim_bus))


if __name__ == "__main__":
    unittest.main(verbosity=2)
