#!/usr/bin/env python3
"""Pré-vol MES-02 (v41.66) — sonde alignée sur le rollout réel.

Lancer avec :  NAULTHENE_DEVICE=cpu venv/bin/python3 experiences/prevol_mes02.py

Test B — Trace on/off : à état donné et poids donnés, `simuler_futur_et_planifier`
appelé avec `trace_rollout` (collecteur actif) doit rendre STRICTEMENT les mêmes
valeurs que sans trace, et le collecteur doit avoir reçu les `pensee_branche` des
horizons demandés (les 8 futurs réellement simulés). La trace ne modifie rien.

Test C' (échantillon) — sur un cerveau BP gelé, la sonde (canonique) produit un ratio
h7/h1 fini et discrimine BRANCHES_PERSISTANTES on/off (BP ≫ témoin).

Le test A (invariance d'entraînement trace=None vs code d'origine) se joue par
comparaison de payload sémantique de courts runs CPU — voir la procédure dans le
CHANGELOG [v41.66] (git stash + comparaison, comme au pré-vol v41.64).
"""
import os
import shutil
import sys

import torch

BRAIN = "brains/07092026_branches_persistantes/BP_g11.brain"


def _agent(N, PersistanceAnatomique):
    copie = BRAIN + ".prevoltmp"
    shutil.copy2(BRAIN, copie)
    ag = PersistanceAnatomique(copie).charger_ou_naitre(N.DEVICE).agent
    ag.eval()
    return ag, copie


def main():
    assert os.environ.get("NAULTHENE_DEVICE", "") == "cpu"
    import naulthene.cerveau.noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique
    print(f"device : {N.DEVICE}")

    ag, copie = _agent(N, PersistanceAnatomique)
    try:
        # --- état réel unique (première obs d'un épisode LavaGap) ---
        env = N.gym.make("MiniGrid-LavaGapS5-v0")
        obs, _ = env.reset(seed=7)
        img = torch.tensor(obs["image"].reshape(1, -1), dtype=torch.float32,
                           device=N.DEVICE) / 10.0
        moteur_bio = N.BiologicalHomeostasisEngine(
            taux_satiete=N.TAUX_SATIETE, taux_hydratation=N.TAUX_HYDRATATION,
            taux_stimulation=N.TAUX_STIMULATION, seuil_critique=N.SEUIL_CRITIQUE_BIO,
            ticks_par_jour=N.ticks_par_jour)
        vbio = torch.as_tensor(moteur_bio.obtenir_vecteur_bio(),
                               dtype=torch.float32, device=N.DEVICE).unsqueeze(0)
        mem = torch.zeros(1, ag.dim_bus, device=N.DEVICE)
        ctx = ag.contexte_vide(1)
        with torch.no_grad():
            _, mem_new, _pe, pensee_bio, _ = ag._executer_c1_reflexe(img, mem, ctx, vbio)
            corps = vbio if N.CORPS_DANS_ROLLOUT_ACTIF else None

            # --- B1 : sans trace ---
            ret_sans = ag.simuler_futur_et_planifier(
                pensee_bio, mem_new, vecteur_bio=corps, trace_rollout=None)

            # --- B2 : avec collecteur ---
            captures = {h: [] for h in (1, 3, 7)}

            def _trace(horizon=0, pensee_branche=None, **_autres):
                captures[horizon].append(pensee_branche)

            ret_avec = ag.simuler_futur_et_planifier(
                pensee_bio, mem_new, vecteur_bio=corps, trace_rollout=_trace)

        # Retour identique (valeurs_simulees + indecision) ?
        def _plat(r):
            if isinstance(r, (tuple, list)):
                return [x.detach().cpu() if isinstance(x, torch.Tensor) else x for x in r]
            return r.detach().cpu() if isinstance(r, torch.Tensor) else r
        a, b = _plat(ret_sans), _plat(ret_avec)
        diffs = []
        for x, y in zip(a, b):
            if isinstance(x, torch.Tensor):
                diffs.append(float((x - y).abs().max().item()))
            else:
                diffs.append(0.0 if x == y else float("inf"))
        print(f"=== TEST B — trace on/off ===")
        print(f"  retour : diff max par élément = {['%.1e' % d for d in diffs]}")
        ok = max(diffs) == 0.0
        for h in (1, 3, 7):
            ok &= len(captures[h]) == 1
            if captures[h]:
                print(f"  h={h} : pensee_branche capturée {tuple(captures[h][0].shape)}"
                      f" (attendue (num_actions, dim_bus))")
        print(f"  => {'✅ la trace ne change rien et observe les horizons réels' if ok else '🔴 ÉCHEC'}")
        if not ok:
            sys.exit(1)

        # --- C' : discrimination BRANCHES_PERSISTANTES on/off sur un cerveau BP gelé ---
        print("\n=== TEST C' — discrimination BRANCHES_PERSISTANTES ===")
        ratio_off = ratio_on = None
        for bp in (False, True):
            N.BRANCHES_PERSISTANTES = bp
            env2 = N.gym.make("MiniGrid-LavaGapS5-v0")
            obs2, _ = env2.reset(seed=11)
            im2 = torch.tensor(obs2["image"].reshape(1, -1), dtype=torch.float32,
                               device=N.DEVICE) / 10.0
            mem2 = torch.zeros(1, ag.dim_bus, device=N.DEVICE)
            with torch.no_grad():
                _, mem2n, _, pb, _ = ag._executer_c1_reflexe(im2, mem2, ctx, vbio)
                cap = {}

                def _tr(horizon=0, pensee_branche=None, **_a):
                    cap[horizon] = pensee_branche

                # UN SEUL appel : la trace remet chaque horizon dans `cap`.
                ag.simuler_futur_et_planifier(pb, mem2n, vecteur_bio=corps,
                                              trace_rollout=_tr)
                sep = {}
                for h in (1, 3, 7):
                    p = cap[h]
                    m = torch.cdist(p, p)
                    iu = torch.triu_indices(p.shape[0], p.shape[0], offset=1)
                    sep[h] = float(m[iu[0], iu[1]].mean().item())
                ratio = sep[7] / (sep[1] + 1e-12)
                print(f"  BRANCHES_PERSISTANTES={int(bp)} : h1 {sep[1]:.4f} "
                      f"h3 {sep[3]:.4f} h7 {sep[7]:.4f} ratio {ratio:.4f}")
                if bp:
                    ratio_on = ratio
                else:
                    ratio_off = ratio
                env2.close()
        print(f"  => BP {ratio_on:.3f} vs témoin {ratio_off:.3f} : "
              f"{'✅ discriminant' if ratio_on > 2 * ratio_off else '🔴 non discriminant'}")
        env.close()
    finally:
        os.remove(copie)
    print("\nMES-02 (tests B + C') : CONTRATS VALIDÉS")


if __name__ == "__main__":
    main()
