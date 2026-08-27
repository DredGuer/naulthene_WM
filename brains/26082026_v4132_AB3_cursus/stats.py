import json, math
R=json.load(open("resultats_bruts.json"))
GR=sorted(R.keys(), key=int)
def t_apparie(cle):
    d=[]
    for g in GR:
        a=R[g]["A"].get(cle); b=R[g]["B"].get(cle)
        if a is None or b is None: continue
        d.append(b-a)
    n=len(d)
    if n<2: return None
    m=sum(d)/n
    var=sum((x-m)**2 for x in d)/(n-1)
    sd=math.sqrt(var)
    se=sd/math.sqrt(n) if sd>0 else 0
    t=m/se if se>0 else 0.0
    ic=1.96*se
    pos=sum(1 for x in d if x>0); neg=sum(1 for x in d if x<0)
    return dict(n=n, moy_A=sum(R[g]["A"][cle] for g in GR if R[g]["A"].get(cle) is not None)/n,
                moy_B=sum(R[g]["B"][cle] for g in GR if R[g]["B"].get(cle) is not None)/n,
                delta=m, sd=sd, t=t, ic95=ic, pos=pos, neg=neg, nul=n-pos-neg)

print(f"{'metrique':<14}{'A':>9}{'B':>9}{'delta':>10}{'IC95':>10}{'t':>8}   B>A")
print("-"*72)
out={}
for k in ["niveau_max","niveau_fin","maitrise","energie","satiete","ratio_c2c1","accord","jepa","recolte"]:
    r=t_apparie(k)
    out[k]=r
    if r:
        print(f"{k:<14}{r['moy_A']:>9.3f}{r['moy_B']:>9.3f}{r['delta']:>+10.3f}{r['ic95']:>10.3f}{r['t']:>+8.2f}   {r['pos']}/{r['n']}")
json.dump(out, open("stats_appariees.json","w"), indent=1)
print()
print("=== NIVEAU MAX par graine (A -> B) ===")
for g in GR:
    a=R[g]["A"]["niveau_max"]; b=R[g]["B"]["niveau_max"]
    fl = "  <<< B+" if b>a else ("  <<< A+" if a>b else "")
    print(f"  g{g:<5} {a} -> {b}{fl}")
