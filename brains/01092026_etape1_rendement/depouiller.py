"""Dépouillement de l'Étape 1 — écrit AVANT d'avoir vu le moindre résultat.

Juge de paix : la DIRECTIVITÉ au banc (< 6× succès, >= 12× échec).
Les runs d'entraînement produisent des `.brain` ; la directivité se mesure ensuite
au banc en lecture seule (`sonde_plancher_geometrique`, instrument corrigé).
"""
import glob, json, os, math, subprocess, sys

D = os.path.dirname(os.path.abspath(__file__))
GRAINES = [11,22,33,44,55,66,77,88,99,111,122,133,144,155,166,177,188,199,211,222]

def t_apparie(deltas):
    n=len(deltas)
    if n<2: return float("nan")
    m=sum(deltas)/n
    v=sum((d-m)**2 for d in deltas)/(n-1)
    return m/math.sqrt(v/n) if v>0 else float("inf")

def banc(brain, sortie):
    if os.path.exists(sortie): return
    subprocess.run([sys.executable,"-m","naulthene.instruments.sonde_plancher_geometrique",
                    "--brain",brain,"--episodes","150","--json",sortie],
                   env={**os.environ,"PYTHONPATH":"src","WANDB_MODE":"offline"},
                   cwd=os.path.join(D,"..",".."), capture_output=True)

if __name__=="__main__":
    paires=[]
    for g in GRAINES:
        for bras in ("ACTIF","TEMOIN"):
            b=f"{D}/{bras}_g{g}.brain"
            if os.path.exists(b): banc(b, f"{D}/banc_{bras}_g{g}.json")
    for g in GRAINES:
        try:
            a=json.load(open(f"{D}/banc_ACTIF_g{g}.json"))
            t=json.load(open(f"{D}/banc_TEMOIN_g{g}.json"))
        except FileNotFoundError:
            continue
        ka=a["resultats"]["entraîné (eval)"]; kt=t["resultats"]["entraîné (eval)"]
        paires.append({"graine":g,
            "actif_succes":100*ka["taux"], "temoin_succes":100*kt["taux"],
            "actif_direct":ka["directivite_mediane"], "temoin_direct":kt["directivite_mediane"],
            "actif_nvict":ka["n_victoires"], "temoin_nvict":kt["n_victoires"]})
    print(f"{'graine':>7} {'ACTIF %':>9} {'TEM %':>8} {'ACTIF dir':>10} {'TEM dir':>9}")
    for p in paires:
        da = p["actif_direct"]; dt = p["temoin_direct"]
        print(f"{p['graine']:>7} {p['actif_succes']:>9.2f} {p['temoin_succes']:>8.2f} "
              f"{(da if da else float('nan')):>10.2f} {(dt if dt else float('nan')):>9.2f}")
    ds=[p["actif_succes"]-p["temoin_succes"] for p in paires]
    dd=[p["actif_direct"]-p["temoin_direct"] for p in paires
        if p["actif_direct"] and p["temoin_direct"]]
    print(f"\nn paires = {len(paires)}")
    if ds: print(f"δ succès     = {sum(ds)/len(ds):+.3f} pt   t = {t_apparie(ds):+.3f}")
    if dd: print(f"δ directivité= {sum(dd)/len(dd):+.3f}×    t = {t_apparie(dd):+.3f}  (n={len(dd)})")
    ok=[p["actif_direct"] for p in paires if p["actif_direct"]]
    if ok: print(f"directivité ACTIF médiane = {sorted(ok)[len(ok)//2]:.2f}×  "
                 f"(juge de paix : < 6,0 succès · >= 12,0 échec)")
    json.dump(paires, open(f"{D}/agregat.json","w"), ensure_ascii=False, indent=2)
