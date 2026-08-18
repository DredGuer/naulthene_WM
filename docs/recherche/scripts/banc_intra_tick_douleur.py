"""v41.25-fix1 — BANC INTRA-TICK de la nociception thermique.

⚠️ RAISON D'ÊTRE. La v41.25 affirmait `r_bio = −1,000` pour un pas dans la lave. Ce
chiffre était mesuré **à la main**, hors du tick réel : deux appels à `calculer_deficit`
encadrant une affectation. Le moteur, lui, n'a JAMAIS produit cette valeur — il calculait
`deficit_avant` en interne APRÈS que la chaleur avait déjà été écrite, si bien que `T²`
figurait des deux côtés de la soustraction et disparaissait (écart mesuré : 0,000000).

Ce banc ne mesure donc **que la sortie de `step_metabolisme`**. Il n'a le droit de
recalculer aucun déficit lui-même : c'est précisément ce contournement qui a produit un
chiffre faux et l'a fait passer pour vérifié.

Lancement :
    PYTHONPATH=src python3 docs/recherche/scripts/banc_intra_tick_douleur.py
"""
import gymnasium as gym
import minigrid  # noqa: F401  (enregistre les environnements)
import naulthene.cerveau.noyau as n
from naulthene.cerveau.bus_sensoriel import BusSensoriel


def _moteur_neuf():
    m = n.BiologicalHomeostasisEngine()
    m.satiete = m.hydratation = m.stimulation = m.energie = 1.0
    m.chaleur = 0.0
    return m


def r_bio_transition(chaleur_depart, chaleur_arrivee, douleur=True):
    """r_bio TEL QUE LE MOTEUR LE RETOURNE, pour une transition thermique donnée."""
    n.DOULEUR_THERMIQUE_ACTIVE = douleur
    import sys
    mod = sys.modules.get("naulthene.cerveau.noyau")
    if mod is not None:
        mod.DOULEUR_THERMIQUE_ACTIVE = douleur
    m = _moteur_neuf()
    m.chaleur = chaleur_depart
    r_bio, _ = m.step_metabolisme(
        cout_action=0.1, erreur_jepa=0.0, nouvelle_case_visitee=False,
        chaleur_apres=chaleur_arrivee,
    )
    return r_bio


def main():
    print("=" * 70)
    print("BANC INTRA-TICK — r_bio lu À LA SORTIE de step_metabolisme")
    print("=" * 70)

    base = r_bio_transition(0.0, 0.0)
    print(f"\n1. TÉMOIN — aucune chaleur, aucune transition")
    print(f"   r_bio = {base:+.6f}   (coût métabolique seul)")

    print(f"\n2. TRANSITIONS THERMIQUES (douleur ACTIVE)")
    print(f"   {'de':>6} {'vers':>6} {'r_bio':>12} {'douleur':>12}")
    for a, b in [(0.0, 0.0), (0.0, 0.06), (0.0, 0.26), (0.0, 0.46), (0.46, 1.0), (0.0, 1.0)]:
        r = r_bio_transition(a, b)
        print(f"   {a:>6.2f} {b:>6.2f} {r:>12.6f} {r - base:>12.6f}")

    print(f"\n3. LE MÊME PAS, DOULEUR COUPÉE (témoin d'ablation)")
    on = r_bio_transition(0.0, 1.0, douleur=True)
    off = r_bio_transition(0.0, 1.0, douleur=False)
    print(f"   ON  = {on:+.6f}")
    print(f"   OFF = {off:+.6f}")
    print(f"   ÉCART = {on - off:+.6f}")

    print(f"\n4. S'ÉLOIGNER DU DANGER doit SOULAGER (r_bio positif)")
    fuite = r_bio_transition(1.0, 0.0)
    print(f"   1.00 -> 0.00 : r_bio = {fuite:+.6f}   ({'SOULAGEMENT' if fuite > base else 'AUCUN'})")

    print(f"\n5. LE TICK RÉEL — un vrai pas dans la lave sur LavaGapS5")
    env = gym.make("MiniGrid-LavaGapS5-v0")
    env.reset(seed=3)
    bus = BusSensoriel()
    bus.reinitialiser_episode(env)
    avant = bus.chaleur_seule(env)
    _, _, termine, _, _ = env.step(2)          # forward
    apres = bus.chaleur_seule(env)
    r = r_bio_transition(avant, apres)
    print(f"   chaleur {avant:.4f} -> {apres:.4f} | terminé={termine}")
    print(f"   r_bio = {r:+.6f}   (témoin {base:+.6f}, douleur {r - base:+.6f})")

    print("\n" + "=" * 70)
    ok = (on - off) < -0.01 and fuite > base
    print("VERDICT :", "✅ la douleur est produite PAR LE MOTEUR"
          if ok else "❌ la douleur reste annulée")
    print("=" * 70)


if __name__ == "__main__":
    main()
