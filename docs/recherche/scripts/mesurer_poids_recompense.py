"""Q3-suite — De quoi la recompense est-elle FAITE ?

`recompense_interne` somme huit termes. Si l'un domine, c'est lui que l'agent
apprend, quoi qu'on ait voulu lui enseigner. Personne ne l'a jamais mesure.

Protocole : rejouer des episodes reels avec la boucle du projet et accumuler
chaque terme separement, en valeur absolue (ce qui compte pour le gradient
c'est l'amplitude, pas le signe).
"""
import sys, numpy as np
sys.path.insert(0, "src")
import naulthene.cerveau.noyau as n
import gymnasium as gym, minigrid

TICKS, N_EP = 400, 20

def mesurer(env_id, graine):
    env = gym.make(env_id); env.reset(seed=graine)
    det = n.DetecteurRessourcesBiologiques(); det.reinitialiser_episode(env)
    bio = n.BiologicalHomeostasisEngine()
    rng = np.random.RandomState(graine)
    acc = {"recompense_env": 0.0, "r_bio": 0.0}
    n_vict = 0
    for t in range(TICKS):
        a = rng.randint(0, 7)
        obs, r, term, trunc, info = env.step(a)
        mf, mw = det.evaluer_tick(env, action_item=a)
        d_avant = bio.calculer_deficit()
        if mf: bio.consommer_ressource("FOOD")
        if mw: bio.consommer_ressource("WATER")
        r_bio, _ = bio.step_metabolisme(cout_action=0.5, erreur_jepa=0.1,
                                           nouvelle_case_visitee=False)
        if mf or mw:
            r_bio += d_avant - bio.calculer_deficit()
        acc["recompense_env"] += abs(float(r))
        acc["r_bio"] += abs(float(r_bio))
        if float(r) > 0: n_vict += 1
        if bio.est_mort(): break
        if term or trunc:
            env.reset(); det.reinitialiser_episode(env)
    env.close()
    return acc, n_vict

print("De quoi la recompense est-elle faite ? (amplitude cumulee sur 400 ticks)\n")
for env_id, nom in n.PROGRAMME[:3]:
    tot = {"recompense_env": 0.0, "r_bio": 0.0}; V = 0
    for g in range(N_EP):
        a, v = mesurer(env_id, g)
        for k in tot: tot[k] += a[k]
        V += v
    s = sum(tot.values())
    print(f"=== {nom} ({V/N_EP:.1f} victoire(s) par 400 ticks) ===")
    for k, v in sorted(tot.items(), key=lambda x: -x[1]):
        print(f"    {k:18s} {v/N_EP:8.2f}  {100*v/s:5.1f} %")
