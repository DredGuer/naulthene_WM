"""v41.26 — BANC DE LA GRADATION NOCICEPTIVE.

Vérifie que les QUATRE PALIERS décrits par l'utilisateur (18/08) émergent de la formule,
sans qu'aucun ne soit codé :

    1. « ça va, c'est chaud »              → douleur RIGOUREUSEMENT NULLE
    2. « gênant mais supportable »         → croissance très lente
    3. « douloureux, tenable qq secondes » → croissance rapide ET cumul temporel
    4. « intense, recul réflexe + dégât »  → explosif

⚠️ Comme `banc_intra_tick_douleur.py`, ce banc lit UNIQUEMENT la sortie du moteur. Il lui
est interdit de recalculer une douleur à la main — c'est ce contournement qui a produit le
chiffre faux de la v41.25.

    PYTHONPATH=src python3 docs/recherche/scripts/banc_gradation_douleur.py
"""
import gymnasium as gym
import minigrid  # noqa: F401
import numpy as np
import naulthene.cerveau.noyau as n
from naulthene.cerveau.bus_sensoriel import lambda_diffusion_carte


def moteur():
    m = n.BiologicalHomeostasisEngine()
    m.satiete = m.hydratation = m.stimulation = m.energie = 1.0
    return m


def main():
    lam = lambda_diffusion_carte(5, 5)
    print("=" * 72)
    print("BANC DE GRADATION — douleur lue À LA SORTIE du moteur")
    print("=" * 72)

    print(f"\n1. LES QUATRE PALIERS (agent NEUF, habituation 0.000, λ={lam:.3f})")
    print(f"   {'dist':>5} {'chaleur':>9} {'douleur':>10}  palier")
    for d in range(0, 5):
        m = moteur()
        T = float(np.exp(-lam * d))
        m.encaisser_chaleur(T)
        dl = m.douleur_thermique()
        pal = ("4. intense (dégât)" if dl > 0.5 else
               "3. douloureux" if dl > 0.02 else
               "2. gênant" if dl > 1e-6 else "1. ça va — ZÉRO")
        print(f"   {d:>5} {T:>9.4f} {dl:>10.6f}  {pal}")

    print("\n2. LA DURÉE — « tenable quelques secondes » (palier 3, distance 1)")
    m = moteur()
    T = float(np.exp(-lam * 1))
    print(f"   {'tick':>5} {'brûlure':>10}")
    for t in range(1, 9):
        m.encaisser_chaleur(T)
        if t in (1, 2, 4, 8):
            print(f"   {t:>5} {m.douleur_thermique():>10.6f}")

    print("\n3. LA DISSIPATION — s'éloigner soulage")
    for t in range(1, 7):
        m.encaisser_chaleur(0.0)
    print(f"   après 6 ticks hors du danger : {m.douleur_thermique():.6f}")

    print("\n4. L'HABITUATION — vivre près du feu")
    m = moteur()
    T1 = float(np.exp(-lam * 1))
    m.encaisser_chaleur(T1)
    neuf = m.douleur_thermique()
    m2 = moteur()
    for _ in range(200):          # 200 ticks passés à distance 1
        m2.encaisser_chaleur(T1)
    m2.brulure = 0.0              # on isole l'habituation de la brûlure
    m2.encaisser_chaleur(T1)
    print(f"   agent NEUF        : douleur {neuf:.6f}")
    print(f"   agent HABITUÉ     : douleur {m2.douleur_thermique():.6f} "
          f"(habituation {m2.chaleur_habituee:.3f})")

    print("\n5. r_bio RÉEL — un pas dans la lave, produit par step_metabolisme")
    env = gym.make("MiniGrid-LavaGapS5-v0")
    env.reset(seed=3)
    from naulthene.cerveau.bus_sensoriel import BusSensoriel
    bus = BusSensoriel()
    bus.reinitialiser_episode(env)
    avant = bus.chaleur_seule(env)
    env.step(2)
    apres = bus.chaleur_seule(env)
    m = moteur()
    m.encaisser_chaleur(avant)
    m.brulure = 0.0
    r, _ = m.step_metabolisme(cout_action=0.1, erreur_jepa=0.0,
                              nouvelle_case_visitee=False, chaleur_apres=apres)
    print(f"   chaleur {avant:.4f} -> {apres:.4f}   r_bio = {r:+.6f}")

    print("\n6. LE REPOS EXISTE-T-IL ? (le défaut corrigé)")
    env = gym.make("MiniGrid-LavaGapS5-v0")
    sans_douleur = 0
    total = 0
    for s in range(20):
        env.reset(seed=s)
        u = env.unwrapped
        W, H = u.grid.width, u.grid.height
        lava = [(x, y) for x in range(W) for y in range(H)
                if getattr(u.grid.get(x, y), "type", None) == "lava"]
        for x in range(W):
            for y in range(H):
                if u.grid.get(x, y) is not None or not lava:
                    continue
                d = min(abs(x - a) + abs(y - b) for a, b in lava)
                mm = moteur()
                mm.encaisser_chaleur(float(np.exp(-lam * d)))
                total += 1
                sans_douleur += int(mm.douleur_thermique() <= 1e-6)
    print(f"   cases libres SANS aucune douleur : {100*sans_douleur/max(total,1):.0f}%")
    print(f"   (v41.25 : 0 % — la douleur était non nulle PARTOUT)")
    print("=" * 72)


if __name__ == "__main__":
    main()
