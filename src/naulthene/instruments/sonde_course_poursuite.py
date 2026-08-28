# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde de course-poursuite — la tête motrice peut-elle rattraper l'axe informatif ?

Instrument (v41.36). Mesure les DEUX vitesses dans les mêmes conditions, nuit après nuit :

    la PROIE      — rotation de l'axe informatif (mesurée à graine FIXÉE)
    le PRÉDATEUR  — rotation de W vers l'axe, MESURÉE et non plus dérivée

⚠️ **LA VITESSE DU PRÉDATEUR EST MESURÉE, PAS CALCULÉE.** Une première estimation du
28/08 la dérivait d'une formule (`arctan(pas_relatif · cos / alignement)`) et donnait un
rapport ×46 — chiffre **retiré**, car sa proie était mesurée sans graine fixée et
contenait donc du bruit d'échantillonnage. Ici les deux grandeurs sortent du même
protocole.

Trois quantités par nuit :

| Grandeur | Ce qu'elle dit |
|---|---|
| `rot_axe` | de combien la cible a bougé |
| `rot_W` | de combien les lignes de `W` ont tourné (angle réel entre W_t et W_{t+1}) |
| `gain_align` | de combien l'alignement W↔axe a effectivement progressé |

⚠️ `rot_W` mesure un DÉPLACEMENT, pas un rapprochement : une tête qui tourne vite sans se
rapprocher court en rond. C'est `gain_align` qui dit si le prédateur gagne du terrain, et
les deux doivent être lus ensemble.

⚠️ **PLANCHER DE BRUIT** publié pour les deux mesures (deux appels sans nuit intercalée).

Cet instrument **entraîne** le cerveau qu'on lui donne mais ne le **sauvegarde jamais** —
travailler sur une copie reste la règle (§8).

Usage :
    PYTHONPATH=src python -m naulthene.instruments.sonde_course_poursuite <brain> \
        [--jours N] [--env ENV_ID] [--graine G] [--sortie f.json]
"""
import argparse, json, numpy as np, torch
from naulthene.cerveau.noyau import DEVICE, DIM_VECTEUR_BIO, creer_env, encoder
from naulthene.cerveau.persistance import PersistanceAnatomique

def _axe(ag, env, mem, ctx, bio, graine, n=1200, cap=100):
    o, _ = env.reset(seed=graine); r = np.random.RandomState(7); C = {"a": [], "b": []}
    for t in range(n):
        img = o["image"] if isinstance(o, dict) else None
        if img is not None:
            k = "a" if (img[:, :, 0] == 8).any() else "b"
            if len(C[k]) < cap: C[k].append(encoder(o))
        o, _, te, tr, _ = env.step(int(r.randint(0, 7)))
        if te or tr: o, _ = env.reset(seed=graine + t)
    if len(C["a"]) < 20 or len(C["b"]) < 20: return None
    def moy(l):
        v = []
        with torch.no_grad():
            for x in l:
                _, _, _, p, _ = ag._executer_c1_reflexe(x, mem, ctx, bio)
                v.append(p.cpu().numpy().ravel())
        return np.array(v).mean(0)
    a = moy(C["a"]) - moy(C["b"]); nn = np.linalg.norm(a)
    return a / nn if nn > 1e-12 else None

def _rot(u, v):
    if u is None or v is None or len(u) != len(v): return None
    return float(np.degrees(np.arccos(np.clip(float(np.dot(u, v)), -1.0, 1.0))))

def _W(ag):
    tm = ag.tete_motrice
    w = tm.base_weight.detach().clone()
    try: w = w + tm.annexe_weight.detach()
    except Exception: pass
    return w.cpu().numpy()

def _rot_W(A, B):
    """Rotation moyenne des 7 lignes jouables entre deux instants."""
    if A.shape != B.shape: return None
    r = []
    for i in range(min(7, A.shape[0])):
        a, b = A[i], B[i]
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na < 1e-12 or nb < 1e-12: continue
        r.append(np.degrees(np.arccos(np.clip(np.dot(a, b) / (na * nb), -1, 1))))
    return float(np.mean(r)) if r else None

def _align(W, axe):
    return float(np.mean([abs(np.dot(w, axe) / (np.linalg.norm(w) + 1e-12))
                          for w in W[:7]]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brain"); ap.add_argument("--jours", type=int, default=200)
    ap.add_argument("--env", default="MiniGrid-SimpleCrossingS9N1-v0")
    ap.add_argument("--graine", type=int, default=11)
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--sortie", default=None)
    a = ap.parse_args()
    rng = np.random.RandomState(a.graine); torch.manual_seed(a.graine)
    etat = PersistanceAnatomique(a.brain).charger_ou_naitre(); ag = etat.agent; db = ag.dim_bus
    env = creer_env(a.env, 147); obs, _ = env.reset(seed=a.graine)
    envm = creer_env(a.env, 147)
    mem0 = torch.zeros(1, db, device=DEVICE); ctx = torch.zeros(1, db, device=DEVICE)
    bio_g = torch.full((1, DIM_VECTEUR_BIO), 0.5, device=DEVICE)

    p1 = _axe(ag, envm, mem0, ctx, bio_g, a.graine)
    p2 = _axe(ag, envm, mem0, ctx, bio_g, a.graine)
    print(f"Cerveau : {a.brain}  ({a.env}, {a.jours} nuits)")
    print(f"  ⚠️ plancher de bruit sur l'axe : {_rot(p1, p2):.4f}°  (rot_W n'en a pas : W est déterministe)\n")
    print(f"  {'nuit':>6}{'rot_AXE':>11}{'rot_W':>10}{'align':>10}{'gain':>11}")
    print("  " + "-" * 48)
    ax = p2; W0 = _W(ag); al0 = _align(W0, ax); hist = []
    ag.train()
    for jour in range(a.jours):
        lps=[];vals=[];ents=[];rws=[];dns=[];trs=[];jp=[]
        mem = torch.zeros(1, db, device=DEVICE)
        for t in range(a.ticks):
            u = env.unwrapped; pav, dav = tuple(u.agent_pos), int(u.agent_dir)
            po = u.carrying is not None
            vb = np.asarray(etat.moteur_bio.obtenir_vecteur_bio(), dtype=np.float32)
            bio = torch.tensor(vb, device=DEVICE).unsqueeze(0)
            bus, mn, _, pb, lg = ag._executer_c1_reflexe(encoder(obs), mem, ctx, bio)
            lg2 = lg.clone(); lg2[..., 7] = float("-inf")
            d = torch.distributions.Categorical(logits=lg2); act = d.sample()
            lps.append(d.log_prob(act)); ents.append(d.entropy())
            vals.append(ag.cortex_prefrontal(pb))
            oh = torch.zeros(1, ag.actions_eye.shape[0], device=DEVICE); oh[0, int(act.item())] = 1.0
            jp.append(torch.nn.functional.mse_loss(ag._predire_bus(pb.detach(), oh), bus.detach()))
            mem = mn.detach(); obs, r, te, tr, _ = env.step(int(act.item()))
            trs.append(bool(tuple(u.agent_pos) != pav or int(u.agent_dir) != dav
                            or (u.carrying is not None) != po))
            rws.append(float(r)); dns.append(bool(te or tr))
            if te or tr: obs, _ = env.reset(seed=a.graine + jour * 1000 + t)
        ag.apprendre_journee(jp, lps, ents, vals, rws, dns, coeff_entropie=0.01, transitions=trs)
        nax = _axe(ag, envm, mem0, ctx, bio_g, a.graine); W1 = _W(ag)
        ra, rw = _rot(ax, nax), _rot_W(W0, W1)
        al1 = _align(W1, nax) if nax is not None else None
        gain = (al1 - al0) if (al1 is not None and al0 is not None) else None
        hist.append({"nuit": jour+1, "rot_axe": ra, "rot_W": rw,
                     "align": al1, "gain": gain})
        if (jour+1) % 10 == 0 or jour == 0:
            f=lambda x,u="°": f"{x:.3f}{u}" if x is not None else "  —  "
            print(f"  {jour+1:>6}{f(ra):>11}{f(rw):>10}{f(al1,''):>10}{f(gain,''):>11}")
        ax, W0, al0 = nax, W1, al1
    if a.sortie:
        json.dump(hist, open(a.sortie, "w"), indent=1); print(f"\n  → {a.sortie}")
    ra=[h["rot_axe"] for h in hist if h["rot_axe"]]; rw=[h["rot_W"] for h in hist if h["rot_W"]]
    g=[h["gain"] for h in hist if h["gain"] is not None]
    if ra and rw:
        print(f"\n  LA PROIE     — l'axe tourne de : {np.mean(ra):.4f}°/nuit")
        print(f"  LE PRÉDATEUR — W tourne de     : {np.mean(rw):.4f}°/nuit")
        print(f"  RAPPORT proie/prédateur        : ×{np.mean(ra)/max(np.mean(rw),1e-9):.1f}")
        print(f"\n  GAIN D'ALIGNEMENT net          : {np.mean(g):+.6f}/nuit"
              f"  → {'le prédateur GAGNE du terrain' if np.mean(g)>0 else 'il PERD du terrain'}")
        print(f"  alignement : {hist[0]['align']:.4f} → {hist[-1]['align']:.4f}")

if __name__ == "__main__":
    main()
