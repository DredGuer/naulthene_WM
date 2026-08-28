# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde de dérive LONGUE — la rotation de l'axe décroît-elle avec la maturité ?

Instrument (v41.36). Fait vieillir un cerveau et mesure la rotation de l'axe informatif
**à chaque nuit**, pour trancher entre deux hypothèses qui prédisent des courbes opposées :

    MATURATION  : la rotation décroît vers ~0 quand le monde est encodé
                  → aucune correction architecturale n'est justifiée, il faut du temps
    CHRONIQUE   : la rotation reste stable ou oscille indéfiniment
                  → la dérive est structurelle, une correction se justifie

⚠️ **DEUX AXES, ET C'EST LE CŒUR DE LA MESURE.** `pensee_bio` mélange la perception et le
corps. On mesure donc séparément :

    axe VISUEL     — mesuré à `vecteur_bio` GELÉ (0,5 partout) : seule la vue varie
    axe COMPLET    — mesuré au `vecteur_bio` réel : vue + faim + soif + douleur

Si le visuel se fige mais que le complet continue de tourner, la dérive est **métabolique**
et aucune stabilisation du JEPA ne la réglera. C'est l'hypothèse de l'oscillation
métabolique, et elle est distinguable de l'hypothèse perceptive par cette seule mesure.

⚠️ **UN CHIFFRE DE ROTATION NE VEUT RIEN DIRE SEUL.** La sonde publie aussi l'erreur JEPA
de la nuit — pour vérifier si la rotation suit l'apprentissage du modèle du monde — et un
**plancher de bruit** : la rotation mesurée entre deux appels SANS aucune nuit
intercalée, qui donne la variabilité d'échantillonnage de la sonde elle-même.

⚠️ Cet instrument **entraîne** le cerveau qu'on lui donne (il le fait vieillir) mais ne le
**sauvegarde jamais**. Travailler sur une **copie** reste la règle (§8).

Usage :
    PYTHONPATH=src python -m naulthene.instruments.sonde_derive_longue <brain> \
        [--jours N] [--env ENV_ID] [--graine G] [--sortie fichier.json]
"""
import argparse, json, numpy as np, torch
from naulthene.cerveau.noyau import DEVICE, DIM_VECTEUR_BIO, creer_env, encoder
from naulthene.cerveau.persistance import PersistanceAnatomique

def _axe(ag, env, mem, ctx, bio, graine, n=1200, cap=100):
    """Direction `mean(but visible) − mean(but absent)` dans `pensee_bio`, normalisée."""
    o, _ = env.reset(seed=graine)
    r = np.random.RandomState(7)
    C = {"a": [], "b": []}
    for t in range(n):
        img = o["image"] if isinstance(o, dict) else None
        if img is not None:
            k = "a" if (img[:, :, 0] == 8).any() else "b"
            if len(C[k]) < cap:
                C[k].append(encoder(o))
        o, _, te, tr, _ = env.step(int(r.randint(0, 7)))
        if te or tr:
            o, _ = env.reset(seed=graine + t)
    if len(C["a"]) < 20 or len(C["b"]) < 20:
        return None
    def moy(lst):
        v = []
        with torch.no_grad():
            for x in lst:
                _, _, _, p, _ = ag._executer_c1_reflexe(x, mem, ctx, bio)
                v.append(p.cpu().numpy().ravel())
        return np.array(v).mean(0)
    a = moy(C["a"]) - moy(C["b"])
    n_ = np.linalg.norm(a)
    return a / n_ if n_ > 1e-12 else None

def _rot(u, v):
    """Rotation en degrés entre deux directions unitaires."""
    if u is None or v is None or len(u) != len(v):
        return None
    return float(np.degrees(np.arccos(np.clip(float(np.dot(u, v)), -1.0, 1.0))))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brain")
    ap.add_argument("--jours", type=int, default=300)
    ap.add_argument("--env", default="MiniGrid-SimpleCrossingS9N1-v0")
    ap.add_argument("--graine", type=int, default=11)
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--sortie", default=None)
    a = ap.parse_args()

    rng = np.random.RandomState(a.graine); torch.manual_seed(a.graine)
    etat = PersistanceAnatomique(a.brain).charger_ou_naitre()
    ag = etat.agent; db = ag.dim_bus
    env = creer_env(a.env, 147); obs, _ = env.reset(seed=a.graine)
    env_mes = creer_env(a.env, 147)
    mem0 = torch.zeros(1, db, device=DEVICE); ctx = torch.zeros(1, db, device=DEVICE)
    bio_gele = torch.full((1, DIM_VECTEUR_BIO), 0.5, device=DEVICE)

    def bio_reel():
        v = np.asarray(etat.moteur_bio.obtenir_vecteur_bio(), dtype=np.float32)
        return torch.tensor(v, device=DEVICE).unsqueeze(0)

    # --- plancher de bruit : deux appels SANS nuit intercalée ---
    p1 = _axe(ag, env_mes, mem0, ctx, bio_gele, a.graine)
    p2 = _axe(ag, env_mes, mem0, ctx, bio_gele, a.graine)
    plancher = _rot(p1, p2)
    print(f"Cerveau : {a.brain}  ({a.env}, {a.jours} jours)")
    print(f"  ⚠️ plancher de bruit de la sonde (2 appels, 0 nuit) : {plancher:.4f}°")
    print(f"  Toute rotation sous ce seuil n'est pas lisible.\n")
    print(f"  {'nuit':>6}{'rot. VISUEL':>14}{'rot. COMPLET':>15}{'JEPA':>10}{'dim':>6}")
    print("  " + "-" * 53)

    hist = []
    a_vis = p2
    a_cpl = _axe(ag, env_mes, mem0, ctx, bio_reel(), a.graine)
    ag.train()
    for jour in range(a.jours):
        lps = []; vals = []; ents = []; rws = []; dns = []; trs = []; jp = []
        mem = torch.zeros(1, db, device=DEVICE)
        for t in range(a.ticks):
            u = env.unwrapped
            pav, dav = tuple(u.agent_pos), int(u.agent_dir)
            po = u.carrying is not None
            bus, mn, _, pb, lg = ag._executer_c1_reflexe(encoder(obs), mem, ctx, bio_reel())
            lg2 = lg.clone(); lg2[..., 7] = float("-inf")
            d = torch.distributions.Categorical(logits=lg2); act = d.sample()
            lps.append(d.log_prob(act)); ents.append(d.entropy())
            vals.append(ag.cortex_prefrontal(pb))
            oh = torch.zeros(1, ag.actions_eye.shape[0], device=DEVICE)
            oh[0, int(act.item())] = 1.0
            jp.append(torch.nn.functional.mse_loss(ag._predire_bus(pb.detach(), oh),
                                                   bus.detach()))
            mem = mn.detach()
            obs, r, te, tr, _ = env.step(int(act.item()))
            trs.append(bool(tuple(u.agent_pos) != pav or int(u.agent_dir) != dav
                            or (u.carrying is not None) != po))
            rws.append(float(r)); dns.append(bool(te or tr))
            if te or tr:
                obs, _ = env.reset(seed=a.graine + jour * 1000 + t)
        jepa = float(np.mean([float(x.item()) for x in jp]))
        ag.apprendre_journee(jp, lps, ents, vals, rws, dns,
                             coeff_entropie=0.01, transitions=trs)
        n_vis = _axe(ag, env_mes, mem0, ctx, bio_gele, a.graine)
        n_cpl = _axe(ag, env_mes, mem0, ctx, bio_reel(), a.graine)
        rv, rc = _rot(a_vis, n_vis), _rot(a_cpl, n_cpl)
        hist.append({"nuit": jour + 1, "rot_visuel": rv, "rot_complet": rc,
                     "jepa": jepa, "dim_bus": ag.dim_bus})
        a_vis, a_cpl = n_vis, n_cpl
        if (jour + 1) % 10 == 0 or jour == 0:
            fv = f"{rv:.3f}°" if rv is not None else "  —  (dim changée)"
            fc = f"{rc:.3f}°" if rc is not None else "  —  "
            print(f"  {jour+1:>6}{fv:>14}{fc:>15}{jepa:>10.5f}{ag.dim_bus:>6}")

    if a.sortie:
        json.dump({"plancher_bruit": plancher, "historique": hist},
                  open(a.sortie, "w"), indent=1)
        print(f"\n  → {a.sortie}")
    v = [h["rot_visuel"] for h in hist if h["rot_visuel"] is not None]
    if len(v) >= 40:
        q = len(v) // 4
        print(f"\n  TENDANCE (axe visuel) : premier quart {np.mean(v[:q]):.3f}°/nuit "
              f"→ dernier quart {np.mean(v[-q:]):.3f}°/nuit")
        print(f"  → {'DÉCROÎT (maturation)' if np.mean(v[-q:]) < 0.7*np.mean(v[:q]) else 'NE DÉCROÎT PAS (chronique)'}")

if __name__ == "__main__":
    main()
