"""SONDE §8 — LA PERMÉABILITÉ D'`integrateur_bio` : quel sens le réseau ÉCOUTE-T-IL ?

`integrateur_bio : dim_bus + DIM_VECTEUR_BIO → dim_bus` fusionne la pensée visuelle avec
les 44 dimensions du corps. Deux ajouts passifs en queue de ce vecteur (bit de portage,
ancrage cinématique) ont donné DEUX EFFETS NULS à n=20 — sans qu'on ait jamais mesuré si
le réseau écoute cette entrée.

Cette sonde lit, colonne par colonne, la norme du poids EFFECTIF (base + annexe, comme en
`forward`) et la rapporte à la norme moyenne d'une colonne de pensée visuelle. C'est un
rapport d'ATTENTION STRUCTURELLE : combien de poids le réseau consacre à cette dimension.

⚠️ CE QUE CETTE SONDE NE DIT PAS. Une norme n'est pas un gradient : le dépôt a déjà mesuré
qu'une couche peut modifier 7,43 % de ses poids en 5 nuits à norme constante (v37.0). Un
poids élevé prouve qu'une voie EXISTE, jamais qu'elle PORTE de l'information. C'est un
plancher de diagnostic, pas une preuve d'usage.

⚠️ LECTURE SEULE, le .brain est COPIÉ avant chargement (règle de mesure §8).
"""
import argparse, json, os, shutil, warnings
warnings.filterwarnings("ignore")

import torch


def tranches(N):
    """Le contrat append-only de `obtenir_vecteur_bio`, en (nom, largeur)."""
    return [
        ("jauges",            3),
        ("quete",             3),
        ("rappel_spatial",    2),
        ("quete_vocale",      8),
        ("toucher",           N.DIM_TOUCHER),
        ("chimie",            N.DIM_CHIMIE),
        ("exo_sens",          N.DIM_EXO),
        ("clinotaxie",        N.DIM_ODORAT_DELTA),
        ("thermoception",     N.DIM_THERMOCEPTION),
        ("pression",          N.DIM_PRESSION),
        ("rappel_marquant",   N.DIM_RAPPEL_MARQUANT),
        ("presence_auditive", N.DIM_PRESENCE_AUDITIVE),
        ("portage",           N.DIM_PORTAGE),
        ("elan",              getattr(N, "DIM_ELAN", 2)),   # ancrage cinematique, v41.49
    ]


def mesurer(agent, N):
    couche = agent.integrateur_bio
    W = (couche.base_weight + couche.annexe_weight).detach()   # (out, in), comme forward
    dim_bus = agent.dim_bus

    # norme L2 par COLONNE d'entrée : ce que le réseau consacre à cette dimension
    par_colonne = W.norm(dim=0)
    ref_vision = float(par_colonne[:dim_bus].mean())         # l'échelle : une dim de pensée

    decoupe, i = {}, dim_bus
    for nom, larg in tranches(N):
        if larg <= 0:
            continue
        bloc = par_colonne[i:i + larg]
        decoupe[nom] = {
            "largeur": int(larg),
            "norme_moy": float(bloc.mean()),
            "ratio_vs_vision": float(bloc.mean() / (ref_vision + 1e-12)),
        }
        i += larg
    assert i == W.shape[1], f"decoupe {i} != entree {W.shape[1]} — le contrat a bouge"
    return ref_vision, decoupe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    import naulthene.cerveau.noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique

    copie = os.path.join(os.path.dirname(a.brain) or ".",
                         f".sonde_perm_{os.path.basename(a.brain)}")
    shutil.copy2(a.brain, copie)
    try:
        agent = PersistanceAnatomique(copie).charger_ou_naitre(N.DEVICE).agent
        agent.eval()
        ref, d = mesurer(agent, N)
        r = {"brain": os.path.basename(a.brain), "dim_bus": int(agent.dim_bus),
             "ref_vision": ref, "tranches": d}
        print(f"  {r['brain']:<26} ref_vision {ref:.4f}")
        for k, v in d.items():
            print(f"      {k:<20}{v['largeur']:>3}d  ratio {v['ratio_vs_vision']:>7.3f}")
        if a.json:
            json.dump(r, open(a.json, "w"), indent=1)
    finally:
        try:
            os.remove(copie)
        except OSError:
            pass


if __name__ == "__main__":
    main()
