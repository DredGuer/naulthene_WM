import re, math, json, os
GR=[11,22,33,44,55,66,77,88,99,111,122,133,144,155,166,177,188,199,211,222]
C="brains/27082026_v4133_portage_banc"
def extraire(p, fen=200):
    txt=open(p,errors='ignore').read(); nuits=txt.split("🌙 Jour ")[1:][-fen:]
    d={k:[] for k in ["portage","saisie_taux","recolte","energie","satiete","maitrise","victoires","jepa"]}
    for b in nuits:
        m=re.search(r'🔑 Portage ([\d.]+)%',b);  m and d["portage"].append(float(m.group(1)))
        m=re.search(r'saisie\(s\) → taux ([\d.]+)%',b); m and d["saisie_taux"].append(float(m.group(1)))
        m=re.search(r'récolté (\d+)',b); m and d["recolte"].append(int(m.group(1)))
        m=re.search(r'⚡ moy ([\d.]+)',b); m and d["energie"].append(float(m.group(1)))
        m=re.search(r'Satiété ([\d.]+)',b); m and d["satiete"].append(float(m.group(1)))
        m=re.search(r'maîtrise (\d+)%',b); m and d["maitrise"].append(int(m.group(1)))
        m=re.search(r'Erreur JEPA moy: ([\d.]+)',b); m and d["jepa"].append(float(m.group(1)))
    tot=re.findall(r'🏆 (\d+) victoire\(s\)',txt)
    out={k:(sum(v)/len(v) if v else None) for k,v in d.items()}
    out["victoires_fin"]=int(tot[-1]) if tot else None
    return out
R={}
for g in GR:
    R[str(g)]={b:extraire(f"{C}/{b}_g{g}.log") for b in "AB"}
def t_app(cle):
    dd=[]; a_=[]; b_=[]
    for g in GR:
        a=R[str(g)]["A"].get(cle); b=R[str(g)]["B"].get(cle)
        if a is None or b is None: continue
        dd.append(b-a); a_.append(a); b_.append(b)
    n=len(dd)
    if n<2: return None
    m=sum(dd)/n; sd=math.sqrt(sum((x-m)**2 for x in dd)/(n-1)); se=sd/math.sqrt(n) if sd>0 else 0
    return dict(n=n,A=sum(a_)/n,B=sum(b_)/n,delta=m,t=(m/se if se>0 else 0.0),
                ic=1.96*se,pos=sum(1 for x in dd if x>0))
print(f"{'metrique':<14}{'A (bit)':>10}{'B (temoin)':>12}{'delta':>10}{'IC95':>9}{'t':>8}   B>A")
print("-"*72)
out={}
for k in ["portage","saisie_taux","recolte","energie","satiete","maitrise","victoires_fin","jepa"]:
    r=t_app(k); out[k]=r
    if r: print(f"{k:<14}{r['A']:>10.3f}{r['B']:>12.3f}{r['delta']:>+10.3f}{r['ic']:>9.3f}{r['t']:>+8.2f}   {r['pos']}/{r['n']}")
json.dump(out,open(f"{C}/comportement.json","w"),indent=1)
