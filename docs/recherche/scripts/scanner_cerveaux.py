"""Scanner comparatif : qu'est-ce qui distingue les MEILLEURS cerveaux des PIRES ?

Question posee par l'utilisateur le 16/08 : « la cle est dans la gestion entre
C1 et C2, la memorisation et la compression des elements abstraits ». Ce script
compare, sur les memes grandeurs, les cerveaux promus et les cerveaux bloques.

Il ne modifie rien : lecture seule des .brain.
"""
import sys, glob, os, re, torch
from statistics import mean

COUCHES = ("porte_visuelle", "porte_auditive", "hippocampe", "fusion_memoire",
           "integrateur_bio", "generateur_attente", "analyseur",
           "tete_motrice", "cortex_prefrontal")


def scanner(path):
    ck = torch.load(path, map_location="cpu", weights_only=False)
    sd = ck["state_dict"]
    d = {"jour": ck.get("jour", 0), "victoires": ck.get("victoires_totales", 0),
         "env": ck.get("env_id", "?"), "dim_bus": ck.get("dim_bus", 0)}

    # --- santé synaptique par couche : norme et myéline ---
    for n in COUCHES:
        b = sd.get(f"{n}.base_weight")
        m = sd.get(f"{n}.myeline_M")
        d[f"norme_{n}"] = float(b.norm()) if b is not None else 0.0
        if m is not None and m.numel() > 1:
            q = m.flatten().kthvalue(max(1, int(0.75 * m.numel()))).values
            d[f"myel_{n}"] = float(q)
        else:
            d[f"myel_{n}"] = 0.0

    # --- ABSTRACTION : ce que l'agent a appris par TYPE (empreinte v39) ---
    emp = ck.get("empreinte_types", {}) or {}
    d["n_types"] = len(emp)
    d["types"] = {k: (v.get("valence", 0.0), v.get("confirmations", 0))
                  for k, v in emp.items()} if isinstance(emp, dict) else {}

    # --- MEMOIRE : combien de reperes, combien confirmes ---
    souv = ck.get("souvenirs_spatiaux", ck.get("memoire_souvenirs", [])) or []
    d["n_souvenirs"] = len(souv)
    if souv and isinstance(souv[0], dict):
        d["conf_moy"] = mean(s.get("confirmations", 1) for s in souv)
        d["valence_moy"] = mean(s.get("valence", 0.0) for s in souv)
    else:
        d["conf_moy"] = d["valence_moy"] = 0.0

    # --- METABOLISME / ETAT ---
    for k in ("teneur_dopamine", "envie_de_vivre", "vecu_okay", "vecu_danger",
              "satiete", "hydratation", "energie", "plasticite_base"):
        d[k] = ck.get(k, None)
    return d


def main(rep, promus, bloques):
    scans = {}
    for f in sorted(glob.glob(os.path.join(rep, "*.brain"))):
        m = re.search(r"_g(\d+)_RMD\.brain$", f)
        if not m or " " in os.path.basename(f):
            continue
        scans[int(m.group(1))] = scanner(f)

    A = [scans[g] for g in promus if g in scans]
    B = [scans[g] for g in bloques if g in scans]
    print(f"MEILLEURS (niveau 3) : {len(A)} cerveaux — {promus}")
    print(f"PIRES (niveau 1)     : {len(B)} cerveaux — {bloques}\n")

    def cmp(cle, fmt="{:.4f}"):
        a = [x[cle] for x in A if isinstance(x.get(cle), (int, float))]
        b = [x[cle] for x in B if isinstance(x.get(cle), (int, float))]
        if not a or not b:
            return
        ma, mb = mean(a), mean(b)
        ecart = (ma - mb) / abs(mb) * 100 if mb else float("inf")
        flag = "  <<<" if abs(ecart) > 25 else ""
        print(f"  {cle:32s} {fmt.format(ma):>12s} {fmt.format(mb):>12s} {ecart:+7.0f} %{flag}")

    print(f"  {'grandeur':32s} {'MEILLEURS':>12s} {'PIRES':>12s} {'ecart':>9s}")
    print("  " + "-" * 70)
    for c in ("victoires", "dim_bus", "n_types", "n_souvenirs", "conf_moy",
              "valence_moy", "teneur_dopamine", "envie_de_vivre",
              "vecu_okay", "vecu_danger", "plasticite_base"):
        cmp(c)
    print()
    for n in COUCHES:
        cmp(f"norme_{n}")
    print()
    for n in COUCHES:
        cmp(f"myel_{n}", "{:.6f}")

    print("\n  --- ABSTRACTION : types appris ---")
    for lab, grp in (("MEILLEURS", A), ("PIRES", B)):
        tous = {}
        for x in grp:
            for t, (v, c) in x.get("types", {}).items():
                tous.setdefault(t, []).append((v, c))
        print(f"  {lab} :")
        for t, vals in sorted(tous.items(), key=lambda kv: -mean(c for _, c in kv[1])):
            print(f"    {t:14s} valence {mean(v for v,_ in vals):+.3f}  "
                  f"confirmations {mean(c for _,c in vals):8.0f}  (sur {len(vals)} cerveaux)")


if __name__ == "__main__":
    promus = [66, 77, 177, 22, 55, 199, 211, 122, 11, 88, 144, 99, 133, 111, 44, 155]
    bloques = [33, 188, 222]
    main(sys.argv[1], promus, bloques)
