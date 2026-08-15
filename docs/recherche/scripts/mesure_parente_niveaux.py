"""Mesure la PARENTE reelle entre niveaux voisins du PROGRAMME.

Le report de maitrise (idee utilisateur) suppose qu'un niveau ressemble au
precedent. Cette mesure le verifie AVANT d'ecrire la mecanique, plutot que de
poser un facteur de report a la main.

Protocole : pour chaque niveau, on mesure des proprietes structurelles de la
carte sur N resets, sans agent. La parente = similarite de ces proprietes.
"""
import numpy as np, gymnasium as gym, minigrid, json, sys

PROGRAMME = [
    ("MiniGrid-Empty-5x5-v0",          "Nourrisson"),
    ("MiniGrid-Empty-Random-6x6-v0",   "Eveil"),
    ("MiniGrid-Empty-8x8-v0",          "Maternelle"),
    ("MiniGrid-SimpleCrossingS9N1-v0", "Primaire 1"),
    ("MiniGrid-LavaGapS5-v0",          "Primaire 2"),
    ("MiniGrid-Fetch-5x5-N2-v0",       "Primaire 3"),
    ("MiniGrid-GoToDoor-6x6-v0",       "College 1"),
    ("MiniGrid-DoorKey-5x5-v0",        "College 2"),
    ("MiniGrid-DoorKey-6x6-v0",        "College 3"),
    ("MiniGrid-DoorKey-8x8-v0",        "Lycee 1"),
    ("MiniGrid-Unlock-v0",             "Lycee 2"),
    ("MiniGrid-UnlockPickup-v0",       "Lycee 3"),
    ("MiniGrid-MemoryS7-v0",           "Universite"),
    ("MiniGrid-MultiRoom-N2-S4-v0",    "Doctorat 1"),
    ("MiniGrid-MultiRoom-N4-S5-v0",    "Doctorat 2"),
]

N_RESETS = 40

def profil(env_id):
    env = gym.make(env_id)
    libres, murs, objets, tailles, dist_but, types = [], [], [], [], [], set()
    for i in range(N_RESETS):
        env.reset(seed=i)
        g = env.unwrapped.grid
        w, h = g.width, g.height
        nl = nm = no = 0
        pos_but = None
        for y in range(h):
            for x in range(w):
                c = g.get(x, y)
                if c is None:
                    nl += 1
                else:
                    t = c.type
                    types.add(t)
                    if t == "wall":
                        nm += 1
                    else:
                        no += 1
                        if t == "goal":
                            pos_but = (x, y)
        libres.append(nl); murs.append(nm); objets.append(no); tailles.append(w * h)
        ap = env.unwrapped.agent_pos
        if pos_but is not None:
            dist_but.append(abs(ap[0]-pos_but[0]) + abs(ap[1]-pos_but[1]))
    env.close()
    return {
        "taille": float(np.mean(tailles)),
        "libres": float(np.mean(libres)),
        "murs": float(np.mean(murs)),
        "objets": float(np.mean(objets)),
        "densite_obstacle": float(np.mean(murs)) / float(np.mean(tailles)),
        "dist_but": float(np.mean(dist_but)) if dist_but else -1.0,
        "types": sorted(types - {"wall"}),
        "n_actions_utiles": len(sorted(types - {"wall"})),
    }

profils = {}
for env_id, nom in PROGRAMME:
    try:
        profils[env_id] = profil(env_id)
        p = profils[env_id]
        print(f"{nom:14s} {env_id:34s} taille {p['taille']:5.0f}  libres {p['libres']:5.1f}  "
              f"dens.obst {p['densite_obstacle']:.2f}  dist_but {p['dist_but']:5.1f}  "
              f"types {','.join(p['types']) if p['types'] else '-'}")
    except Exception as e:
        print(f"{nom:14s} ERREUR {e}")

print("\n=== PARENTE ENTRE NIVEAUX VOISINS ===")
print("(similarite = 1 - distance normalisee sur taille/libres/obstacles/types)")
axes = ["taille", "libres", "densite_obstacle", "dist_but"]
resultats = []
ids = [e for e, _ in PROGRAMME if e in profils]
for i in range(len(ids) - 1):
    a, b = profils[ids[i]], profils[ids[i+1]]
    # distance relative par axe, bornee
    ds = []
    for ax in axes:
        va, vb = a[ax], b[ax]
        if va <= 0 and vb <= 0:
            continue
        d = abs(va - vb) / max(abs(va), abs(vb), 1e-9)
        ds.append(min(1.0, d))
    d_struct = float(np.mean(ds))
    # nouveaute de vocabulaire : types presents dans b et absents de a
    ta, tb = set(a["types"]), set(b["types"])
    nouveaux = tb - ta
    d_types = len(nouveaux) / max(len(tb), 1)
    similarite = (1 - d_struct) * (1 - d_types)
    nom_a = [n for e, n in PROGRAMME if e == ids[i]][0]
    nom_b = [n for e, n in PROGRAMME if e == ids[i+1]][0]
    resultats.append({"de": nom_a, "vers": nom_b, "similarite": similarite,
                      "d_struct": d_struct, "nouveaux_types": sorted(nouveaux)})
    flag = "  <<< RUPTURE" if similarite < 0.5 else ""
    print(f"{i}->{i+1}  {nom_a:12s} -> {nom_b:12s}  similarite {similarite:.2f}  "
          f"(struct {1-d_struct:.2f}, nouveau: {','.join(sorted(nouveaux)) if nouveaux else '-'}){flag}")

json.dump({"profils": profils, "parente": resultats}, open(sys.argv[1], "w"), indent=1)
print(f"\n-> {sys.argv[1]}")
