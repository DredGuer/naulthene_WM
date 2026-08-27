import re, os, math
GR=[11,22,33,44,55,66,77,88,99,111,122,133,144,155,166,177,188,199,211,222]
def maitrise_par_fenetre(path, fen):
    txt=open(path,errors='ignore').read()
    nuits=txt.split("🌙 Jour ")[1:]
    vals=[]
    for b in nuits[-fen:]:
        m=re.search(r'maîtrise (\d+)%', b)
        if m: vals.append(int(m.group(1)))
    return sum(vals)/len(vals) if vals else None
for fen in [100,400,720,1440]:
    d=[]
    for g in GR:
        a=maitrise_par_fenetre(f"A_g{g}.log",fen); b=maitrise_par_fenetre(f"B_g{g}.log",fen)
        if a is not None and b is not None: d.append(b-a)
    n=len(d); m=sum(d)/n; sd=math.sqrt(sum((x-m)**2 for x in d)/(n-1)); se=sd/math.sqrt(n)
    print(f"fenetre {fen:>5} nuits : delta = {m:+7.3f}  t = {m/se:+6.2f}  (B>A : {sum(1 for x in d if x>0)}/{n})")
