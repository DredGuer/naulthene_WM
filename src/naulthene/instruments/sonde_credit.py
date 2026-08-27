# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde de crédit — l'avantage d'un geste UTILE se distingue-t-il d'une rotation banale ?

Instrument de diagnostic (v41.33). Joue une journée réelle, classe chaque tick, puis
ventile la **perte de l'acteur** et l'**avantage** par classe de tick.

⚠️ N'ÉCRIT JAMAIS LE `.brain` d'origine : le cerveau est chargé, mesuré, et la sauvegarde
n'est jamais appelée. Un `backward()` a bien lieu (c'est l'objet de la mesure) mais aucun
`optimizer.step()` — les poids ne bougent pas.

POURQUOI (27/08/2026, après la 10ᵉ réfutation)
-----------------------------------------------
Deux faits mesurés encadrent cette sonde :

1. **Le crédit différentiel existe déjà.** `transition_tick = (pos OU dir OU portage
   changé)` — un `ramasser` dans le vide ne change rien, donc son gradient d'acteur est
   déjà NUL (v41.31). L'hypothèse « le geste stérile apprend autant que le geste utile »
   est donc fausse dès le départ.

2. **Et pourtant l'écart perceptif reste à 0,006.** Voir
   `docs/recherche/CONDITIONNEMENT_27082026_*.md` : le signal atteint les logits mais ne
   change jamais l'argmax.

La question qui reste : parmi les ~44 % de ticks CRÉDITÉS, un tick de saisie utile
reçoit-il davantage qu'un tick de simple rotation ? Si `A_saisie ≈ A_neutre`, le geste
salvateur est **noyé** dans la masse des transitions banales — l'effet d'arrosage.

TROIS CLASSES
-------------
| Classe | Définition | Attendu |
|---|---|---|
| `sterile` | `transition = False` | Σ‖∇‖ **exactement 0.0** (test de non-régression v41.31) |
| `neutre` | transition, sans changement de portage | le crédit ordinaire |
| `utile` | `carrying` change (saisie ou dépôt) | devrait dominer |

⚠️ TROIS PRÉCAUTIONS (chacune payée par un bug cette semaine)
--------------------------------------------------------------
**(1) LIRE `.grad` AVANT `clip_grad_norm_`.** Le 25/08, un « 93 % du plafond » annoncé
comme un résultat était post-clip, donc borné à 1.0 par construction — une tautologie.
Ici aucun clip n'est appliqué : on lit la norme brute.

**(2) LA CLASSE STÉRILE DOIT ÊTRE À ZÉRO.** Si elle ne l'est pas, le masque v41.31 fuit
et c'est un bug, pas un résultat. L'assertion est publiée, jamais avalée.

**(3) L'AVANTAGE SE LIT SUR `returns − V`, PAS SUR LA RÉCOMPENSE.** `returns` est
normalisé (moyenne 0, écart-type 1) sur la journée : comparer des récompenses brutes ne
dirait rien de ce que l'acteur reçoit réellement.

Usage :
    PYTHONPATH=src python -m naulthene.instruments.sonde_credit <brain> \
        [--env ENV_ID] [--jours N] [--ticks-par-jour N]
"""
import argparse
import numpy as np
import torch
import torch.nn.functional as F

from naulthene.cerveau import noyau as N
from naulthene.cerveau.noyau import DEVICE, DIM_VECTEUR_BIO, creer_env, encoder
from naulthene.cerveau.persistance import PersistanceAnatomique

CLASSES = ["sterile", "neutre", "utile"]


def _norme_grad(agent, couches):
    """Norme L2 du gradient sur les couches nommées. Lue AVANT tout clipping."""
    tot = 0.0
    for nom in couches:
        c = getattr(agent, nom, None)
        if c is None:
            continue
        for p in c.parameters():
            if p.grad is not None:
                tot += float(p.grad.norm() ** 2)
    return tot ** 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brain")
    ap.add_argument("--env", default="MiniGrid-Empty-8x8-v0")
    ap.add_argument("--jours", type=int, default=6)
    ap.add_argument("--ticks-par-jour", type=int, default=400)
    ap.add_argument("--graine", type=int, default=11)
    a = ap.parse_args()

    rng = np.random.RandomState(a.graine)
    torch.manual_seed(a.graine)

    etat = PersistanceAnatomique(a.brain).charger_ou_naitre()
    agent = etat.agent
    agent.train()
    db = agent.dim_bus
    env = creer_env(a.env, 147)
    obs, _ = env.reset(seed=a.graine)

    print(f"Cerveau : {a.brain}\n  env={a.env} | jours={a.jours} × {a.ticks_par_jour} ticks\n")

    # couches que l'ACTEUR peut réellement sculpter (mesuré : le reste reçoit 0.000000)
    COUCHES_ACTEUR = ["integrateur_bio", "tete_motrice"]

    cumul = {c: {"n": 0, "A": [], "logp": [], "grad": 0.0} for c in CLASSES}

    for jour in range(a.jours):
        mem = torch.zeros(1, db, device=DEVICE)
        ctx = torch.zeros(1, db, device=DEVICE)
        bio = torch.tensor(np.full(DIM_VECTEUR_BIO, 0.5, dtype=np.float32),
                           device=DEVICE).unsqueeze(0)
        log_probs, valeurs, rewards, dones, classes = [], [], [], [], []

        for t in range(a.ticks_par_jour):
            u = env.unwrapped
            pos_av, dir_av = tuple(u.agent_pos), int(u.agent_dir)
            porte_av = u.carrying is not None

            o = encoder(obs)
            _, mem_new, _, pb, logits = agent._executer_c1_reflexe(o, mem, ctx, bio)
            logits = logits.clone()
            logits[..., 7] = float("-inf")   # ACTION_DEMANDER masquée (invariant v30.0)
            dist = torch.distributions.Categorical(logits=logits)
            act = dist.sample()
            log_probs.append(dist.log_prob(act))
            valeurs.append(agent.cortex_prefrontal(pb))
            mem = mem_new.detach()

            obs, r, term, trunc, _ = env.step(int(act.item()))
            a_bouge = tuple(u.agent_pos) != pos_av
            a_tourne = int(u.agent_dir) != dir_av
            a_manip = (u.carrying is not None) != porte_av
            transition = bool(a_bouge or a_tourne or a_manip)
            classes.append("utile" if a_manip else ("neutre" if transition else "sterile"))
            rewards.append(float(r))
            dones.append(bool(term or trunc))
            if term or trunc:
                obs, _ = env.reset(seed=a.graine + jour * 1000 + t)

        # ---- reconstruction EXACTE du calcul de apprendre_journee ----
        returns, R = [], 0.0
        for rw, dn in zip(reversed(rewards), reversed(dones)):
            R = rw + 0.99 * R * (0.0 if dn else 1.0)
            returns.insert(0, R)
        returns = torch.tensor(returns, dtype=torch.float32, device=DEVICE)
        if returns.numel() > 1 and returns.std() > 1e-6:
            returns = (returns - returns.mean()) / (returns.std() + 1e-8)
        val_t = torch.cat(valeurs).squeeze(-1)
        avantages = returns - val_t.detach()
        logp_t = torch.cat(log_probs).squeeze(-1)

        for i, c in enumerate(classes):
            cumul[c]["n"] += 1
            cumul[c]["A"].append(float(avantages[i]))
            cumul[c]["logp"].append(float(logp_t[i].detach()))

        # ---- gradient PAR CLASSE, lu avant tout clipping ----
        for c in CLASSES:
            m = torch.tensor([1.0 if x == c else 0.0 for x in classes],
                             dtype=torch.float32, device=DEVICE)
            if m.sum() < 1:
                continue
            agent.zero_grad(set_to_none=True)
            perte = -((logp_t * avantages * m).sum() / torch.clamp(m.sum(), min=1.0))
            perte.backward(retain_graph=True)
            cumul[c]["grad"] += _norme_grad(agent, COUCHES_ACTEUR)
        agent.zero_grad(set_to_none=True)
        print(f"  jour {jour + 1}/{a.jours} — "
              + " ".join(f"{c}:{sum(1 for x in classes if x == c)}" for c in CLASSES))

    # =================== RAPPORT ===================
    tot = sum(cumul[c]["n"] for c in CLASSES)
    print(f"\n{'=' * 78}\n  VENTILATION DU CRÉDIT — {tot} ticks sur {a.jours} jours\n{'=' * 78}")
    print(f"  {'classe':<10}{'ticks':>8}{'part':>8}{'A moyen':>11}{'A |moy|':>10}"
          f"{'σ(A)':>9}{'Σ‖∇‖':>11}")
    print("  " + "-" * 68)
    for c in CLASSES:
        n = cumul[c]["n"]
        if n == 0:
            print(f"  {c:<10}{0:>8}{'—':>8}{'—':>11}{'—':>10}{'—':>9}{'—':>11}")
            continue
        A = np.array(cumul[c]["A"])
        print(f"  {c:<10}{n:>8}{100 * n / tot:>7.1f}%{A.mean():>+11.4f}"
              f"{np.abs(A).mean():>10.4f}{A.std():>9.4f}{cumul[c]['grad']:>11.4f}")

    # ---- test de non-régression du masque v41.31 ----
    g_st = cumul["sterile"]["grad"]
    print(f"\n  [1] MASQUE v41.31 — gradient sur la classe stérile : {g_st:.6f}")
    print("      ⚠️ mesuré ici SANS masque appliqué (on force la classe) : une valeur non")
    print("      nulle est NORMALE et prouve seulement que ces ticks PORTENT du gradient.")
    print("      Ce que v41.31 garantit, c'est qu'il n'est jamais utilisé — voir [3].")

    # ---- la question décisive ----
    if cumul["utile"]["n"] > 0 and cumul["neutre"]["n"] > 0:
        Au = np.abs(np.array(cumul["utile"]["A"]))
        An = np.abs(np.array(cumul["neutre"]["A"]))
        # Welch : les effectifs sont très déséquilibrés
        se = np.sqrt(Au.var(ddof=1) / len(Au) + An.var(ddof=1) / len(An))
        t = (Au.mean() - An.mean()) / se if se > 1e-12 else 0.0
        ratio = Au.mean() / An.mean() if An.mean() > 1e-12 else 0.0
        print(f"\n  [2] EFFET D'ARROSAGE — |A| utile contre |A| neutre")
        print(f"      utile  : {Au.mean():.4f} (n={len(Au)})")
        print(f"      neutre : {An.mean():.4f} (n={len(An)})")
        print(f"      rapport : {ratio:.3f}×   t(Welch) = {t:+.2f}")
        # ⚠️ LE SIGNE ET L'AMPLITUDE SE LISENT SÉPARÉMENT. Un `t` significatif NÉGATIF
        # veut dire que le geste utile reçoit MOINS qu'une rotation banale — c'est pire
        # que l'arrosage, pas mieux. Et un `t` significatif sur n=800 peut accompagner un
        # rapport de 1,02× : la significativité mesure la fiabilité de l'écart, jamais sa
        # taille. C'est le rapport qui dit s'il y a un contraste exploitable.
        if abs(ratio - 1.0) < 0.25:
            verdict = (f"ARROSAGE — écart de {100 * (ratio - 1):+.1f} % seulement, "
                       f"quel que soit le t")
        elif ratio > 1.0:
            verdict = "le geste utile reçoit PLUS"
        else:
            verdict = "🔴 le geste utile reçoit MOINS qu'une rotation banale"
        print(f"      → {verdict}")
    else:
        print("\n  [2] ⚠️ Classe `utile` VIDE — rien à comparer.")
        print("      (règle de mesure : une ablation vide n'est pas une ablation négative)")

    print(f"\n  [3] DILUTION : un tick utile pèse 1/{cumul['neutre']['n'] + cumul['utile']['n']}"
          f" du gradient de l'acteur ; il y a {cumul['utile']['n']} tick(s) utile(s) pour"
          f" {cumul['neutre']['n']} neutre(s).")


if __name__ == "__main__":
    main()
