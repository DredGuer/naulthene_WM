"""§6.a — les branches du rollout divergent-elles A L'HORIZON 7 ? (MES-02, v41.66)

Réécrit le 08/09/2026 au titre de **MES-02** (registre des problèmes à corriger) :
l'ancienne version **recopiait** la boucle de rollout de C2 (sauts, horizons,
continuation par argmax, projection du corps) au lieu d'observer le calcul réel. Toute
divergence future dans `_solliciter_c2_neocortex` ou `simuler_futur_et_planifier`
aurait fait mentir l'instrument — la même maladie que l'INSTRUMENT_01092026.

Cette version ne contient **AUCUNE boucle de rollout** :
  1. elle échantillonne des états RÉELS (environnement MiniGrid, chaîne mémorielle
     réelle, contexte épisodique réel — moyenne des bus latents comme le jour —, et
     corps réel AU REPOS via l'engin biologique du noyau, plus de zéro arbitraire) ;
  2. elle appelle la méthode **canonique** `AGI_Naulthene.simuler_futur_et_planifier`
     avec `trace_rollout`, la prise d'inspection lecture seule ajoutée en v41.66 ;
  3. la séparation inter-branches (`cdist` sur les 8 futurs) reste calculée ici — la
     **simulation** est dans le noyau, à un seul endroit.

Si les branches convergent à h=7, une tête d'intention lisant la pensée finale
filtrerait du bruit.
"""
import argparse, json, os, shutil, warnings
warnings.filterwarnings("ignore")
import numpy as np, torch


def separation_par_horizon(agent, N, n_etats=80, graine=7, horizons=(1, 3, 7)):
    env = N.gym.make("MiniGrid-LavaGapS5-v0")
    obs, _ = env.reset(seed=graine)
    rng = np.random.RandomState(graine)
    A = agent.num_actions

    # Corps réel AU REPOS (v41.66/MES-02) : l'engin biologique du noyau, non dégradé,
    # produit la représentation interne d'un corps calme (jauges hautes, quêtes au
    # neutre) — plus un vecteur bio nul imposé. Il n'est pas rythmé par l'épisode : la
    # mesure isole le rollout, pas le métabolisme. Utilisé seulement quand le cerveau
    # projette le corps dans ses futurs (CORPS_DANS_ROLLOUT_ACTIF), sinon None (miroir
    # exact du jour, où `_corps_c2 = None`).
    moteur_bio = N.BiologicalHomeostasisEngine(
        taux_satiete=N.TAUX_SATIETE, taux_hydratation=N.TAUX_HYDRATATION,
        taux_stimulation=N.TAUX_STIMULATION, seuil_critique=N.SEUIL_CRITIQUE_BIO,
        ticks_par_jour=N.ticks_par_jour)
    vbio_repos = torch.as_tensor(moteur_bio.obtenir_vecteur_bio(),
                                 dtype=torch.float32, device=N.DEVICE).unsqueeze(0)

    memoire = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    fenetre_bus = []                       # contexte épisodique réel (cf. vecteurs_episodiques)
    sep = {h: [] for h in horizons}

    with torch.no_grad():
        for _ in range(n_etats):
            # --- État réel du tick : obs → C1, chaîne mémorielle + contexte épisodique ---
            img = torch.tensor(obs["image"].reshape(1, -1), dtype=torch.float32,
                               device=N.DEVICE) / 10.0
            ctx = (torch.stack(fenetre_bus).mean(dim=0)
                   if fenetre_bus else agent.contexte_vide(1))
            (bus, mem_new, _pe, pensee_bio, _lg) = agent._executer_c1_reflexe(
                img, memoire, ctx, vbio_repos)
            fenetre_bus.append(bus.detach())
            if len(fenetre_bus) > N.CAPACITE_MEMOIRE:
                fenetre_bus.pop(0)

            # --- Rollout RÉEL : méthode canonique du noyau + trace lecture seule ---
            corps_c2 = (vbio_repos if (getattr(N, "CORPS_DANS_ROLLOUT_ACTIF", False)
                                       and vbio_repos is not None) else None)
            captures = {h: [] for h in horizons}

            def _trace(horizon=0, pensee_branche=None, **_autres):
                captures[horizon].append(pensee_branche)

            agent.simuler_futur_et_planifier(
                pensee_bio, mem_new, vecteur_bio=corps_c2, trace_rollout=_trace)

            # --- Séparation inter-branches sur les tenseurs RÉELLEMENT simulés ---
            for h in horizons:
                if captures[h]:
                    pb = torch.cat(captures[h], dim=0)      # (A, dim) — un état, un horizon
                    m = torch.cdist(pb, pb)
                    iu = torch.triu_indices(A, A, offset=1)
                    sep[h].append(float(m[iu[0], iu[1]].mean()))

            memoire = mem_new.detach()
            obs, _, te, tr, _ = env.step(int(rng.randint(0, 7)))
            if te or tr:
                obs, _ = env.reset(seed=int(rng.randint(0, 10 ** 6)))
                memoire = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
                fenetre_bus = []
    env.close()
    return {h: float(np.mean(v)) for h, v in sep.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    import naulthene.cerveau.noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique
    copie = os.path.join(os.path.dirname(a.brain) or ".", f".h7_{os.path.basename(a.brain)}")
    shutil.copy2(a.brain, copie)
    try:
        agent = PersistanceAnatomique(copie).charger_ou_naitre(N.DEVICE).agent
        agent.eval()
        s = separation_par_horizon(agent, N)
        r = {"brain": os.path.basename(a.brain), "separation": s,
             "ratio_h7_sur_h1": s[7] / (s[1] + 1e-12)}
        print(f"  {r['brain']:<26} h1 {s[1]:.5f}  h3 {s[3]:.5f}  h7 {s[7]:.5f}   "
              f"h7/h1 {r['ratio_h7_sur_h1']:.4f}")
        if a.json:
            json.dump(r, open(a.json, "w"), indent=1)
    finally:
        try:
            os.remove(copie)
        except OSError:
            pass


if __name__ == "__main__":
    main()
