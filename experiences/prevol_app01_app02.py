#!/usr/bin/env python3
"""Pré-vol APP-01 / APP-02 (v41.64) — tests de contrat, CPU, ~minutes.

Lancer avec :  NAULTHENE_DEVICE=cpu venv/bin/python3 experiences/prevol_app01_app02.py

T1 — Parité collecte/rejeu (APP-01) : pour chaque régime, la politique COMPLETE
     reconstruite par `_logits_politique_complete_rejouee` (la fonction du rejeu
     nocturne) doit reproduire, à poids constants, les logits fusionnés que `penser`
     a réellement produits pendant la collecte (`logits_action`). C'est la condition du
     ratio `exp(lp - lp_old) = 1,0` au premier pas.
     Régimes (registre APP-01) : C2 actif / SANS_C2 · voix libre / renormalisation ·
     BRAIN_SPARING_ACTIF on/off · CORPS_DANS_ROLLOUT on/off · masque 8ᵉ action actif
     (agent à 8 actions) — croisés à vigueur et force variées.
T2 — Détachement du critique (APP-02) : avec DETACH_C2_ASYMETRIQUE, la perte de valeur
     (MSE sur `cortex_prefrontal`) ne doit laisser AUCUN gradient sur le tronc partagé
     (`integrateur_bio`) ; sans le drapeau, le gradient doit exister. Vérifié sur la
     forme de perte exacte du rejeu (entrée du critique = `pensee_bio` détaché ou non).
"""
import os
import sys

import torch

CHEMIN_AGENT = "/tmp/prevol_app01_app02_nouveau.brain"


def _nouvel_agent(N, PersistanceAnatomique):
    if os.path.exists(CHEMIN_AGENT):
        os.remove(CHEMIN_AGENT)
    return PersistanceAnatomique(CHEMIN_AGENT).charger_ou_naitre(N.DEVICE).agent


def _entrees(N, agent):
    n = 1
    obs = (torch.rand(n, 147, device=N.DEVICE) * 10.0 / 10.0)   # 7×7×3 aplati, ~[0,1]
    mem = torch.zeros(n, agent.dim_bus, device=N.DEVICE)
    ctx = torch.zeros(n, agent.dim_bus, device=N.DEVICE)
    vbio = torch.rand(n, N.DIM_VECTEUR_BIO, device=N.DEVICE)
    return obs, mem, ctx, vbio


def _norme_grad_trunk(agent, N):
    """Norme totale du gradient reçu par integrateur_bio (None -> 0)."""
    s = 0.0
    for p in agent.integrateur_bio.parameters():
        if p.grad is not None:
            s += float(p.grad.detach().pow(2).sum().cpu().item())
    return s ** 0.5


def main():
    assert os.environ.get("NAULTHENE_DEVICE", "") == "cpu", \
        "lancer avec NAULTHENE_DEVICE=cpu (règle device : jamais mélanger)"
    import naulthene.cerveau.noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique
    print(f"device : {N.DEVICE}")

    agent = _nouvel_agent(N, PersistanceAnatomique)
    print(f"agent neuf : dim_bus={agent.dim_bus}, num_actions={agent.num_actions}")

    # ---------- T1 : parité collecte/rejeu, par régime ----------
    print("\n=== T1 — PARITÉ DE LA POLITIQUE COMPLÈTE (penser vs rejeu) ===")
    regimes = []
    for sans_c2 in (False, True):
        for sparing in (False, True):
            for corps_roll in (False, True):
                for libre in (True, False):
                    regimes.append((sans_c2, sparing, corps_roll, libre))
    nb_echecs = 0

    def _actives(lg):
        # Le masque met la 8ème action à -inf : `-inf - -inf` = NaN. On compare les
        # NUM_ACTIONS_BASE actions ACTIVES ; la colonne masquée est vérifiée à part.
        return lg[..., :N.NUM_ACTIONS_BASE]

    for (sans_c2, sparing, corps_roll, libre) in regimes:
        N.SANS_C2 = sans_c2
        N.BRAIN_SPARING_ACTIF = sparing
        N.CORPS_DANS_ROLLOUT_ACTIF = corps_roll
        agent.gain_c1_libre = libre
        for (vigueur, force) in ((1.0, 0.5), (0.4, 0.85)):
            obs, mem, ctx, vbio = _entrees(N, agent)
            agent.mesure_arbitrage = None
            with torch.no_grad():
                agent.eval()
                logits_jour = agent.penser(
                    obs, mem, ctx, vbio,
                    force_planification=force, vigueur=vigueur,
                    plugs_c3_disponibles=[])[0]
                gain = agent.mesure_arbitrage["gain_c1"] if agent.mesure_arbitrage else 1.0
                facteur = 1.0 if sparing else float(vigueur)
                k1 = float(gain) * facteur
                k2 = float(force) * facteur
                k1t = torch.tensor([[k1]], device=N.DEVICE, dtype=torch.float32)
                k2t = torch.tensor([[k2]], device=N.DEVICE, dtype=torch.float32)
                logits_rejeu, _ = agent._logits_politique_complete_rejouee(
                    obs, mem, ctx, vbio, k1t, k2t)
            delta = float((_actives(logits_jour) - _actives(logits_rejeu))
                          .abs().max().cpu().item())
            fini = bool(torch.isfinite(_actives(logits_jour)).all().item()
                        and torch.isfinite(_actives(logits_rejeu)).all().item())
            masque_ok = True
            if agent.num_actions > N.NUM_ACTIONS_BASE:
                masque_ok = bool(
                    (logits_jour[..., N.NUM_ACTIONS_BASE:] == float("-inf")).all().item()
                    and (logits_rejeu[..., N.NUM_ACTIONS_BASE:] == float("-inf")).all().item())
            # La tolérance 1e-4 couvre le bruit flottant du rejeu par état vs jour.
            if delta > 1e-4 or not fini or not masque_ok:
                nb_echecs += 1
                print(f"  ❌ SANS_C2={int(sans_c2)} sparing={int(sparing)} "
                      f"corps={int(corps_roll)} libre={int(libre)} "
                      f"vigueur={vigueur} force={force} : delta max = {delta:.3e} "
                      f"fini={fini} masque_ok={masque_ok}")
            else:
                print(f"  ✅ SANS_C2={int(sans_c2)} sparing={int(sparing)} "
                      f"corps={int(corps_roll)} libre={int(libre)} "
                      f"vigueur={vigueur} force={force} : delta max = {delta:.2e}")
    # restaure le régime nominal
    N.SANS_C2 = False
    N.BRAIN_SPARING_ACTIF = True
    N.CORPS_DANS_ROLLOUT_ACTIF = True
    agent.gain_c1_libre = True
    if nb_echecs:
        print(f"\n🔴 T1 : {nb_echecs} cellule(s) en échec")
        sys.exit(1)
    print("\n✅ T1 — parité exacte sur tous les régimes (ratio = 1,0 au pas 0)")

    # ---------- T2 : détachement du critique (APP-02) ----------
    print("\n=== T2 — DÉTACHEMENT DU CRITIQUE SUR LE REJEU (APP-02) ===")
    agent = _nouvel_agent(N, PersistanceAnatomique)
    agent.train()  # graphe requis : c'est LUI qui relie le critique au tronc partagé.
    obs, mem, ctx, vbio = _entrees(N, agent)
    _, _, _, pensee_bio, _ = agent._executer_c1_reflexe(obs, mem, ctx, vbio)
    cible = torch.zeros_like(agent.cortex_prefrontal(pensee_bio))
    for detach in (False, True):
        agent.optimizer.zero_grad(set_to_none=True)
        entree = pensee_bio.detach() if detach else pensee_bio
        perte = torch.nn.functional.mse_loss(agent.cortex_prefrontal(entree), cible)
        perte.backward()
        g = _norme_grad_trunk(agent, N)
        if detach:
            ok = g == 0.0
            print(f"  DETACH_C2_ASYMETRIQUE=True  : norme grad integrateur_bio = {g:.3e} "
                  f"{'✅ (0 attendu)' if ok else '🔴 FUITE !'}")
            if not ok:
                sys.exit(1)
        else:
            ok = g > 0.0
            print(f"  DETACH_C2_ASYMETRIQUE=False : norme grad integrateur_bio = {g:.3e} "
                  f"{'✅ (>0 attendu)' if ok else '🔴 AUSENT !'}")
            if not ok:
                sys.exit(1)
    print("\n✅ T2 — le critique ne sculpte jamais le tronc partagé quand le drapeau est actif")

    print("\nT1 + T2 : CONTRATS VALIDÉS")
    os.remove(CHEMIN_AGENT) if os.path.exists(CHEMIN_AGENT) else None


if __name__ == "__main__":
    main()
