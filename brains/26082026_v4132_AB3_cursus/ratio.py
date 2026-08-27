import re, math
GR=[11,22,33,44,55,66,77,88,99,111,122,133,144,155,166,177,188,199,211,222]
def comps(path, fen=400):
    txt=open(path,errors='ignore').read()
    nuits=txt.split("🌙 Jour ")[1:][-fen:]
    c1=[];c2=[];ent1=[];ent2=[];na1=[];na2=[]
    for b in nuits:
        m=re.search(r'C1=([\d.]+) C2=([\d.]+)', b)
        if m: c1.append(float(m.group(1))); c2.append(float(m.group(2)))
        m=re.search(r'C1 ([\d.]+) \| C2 ([\d.]+)', b)
        if m: ent1.append(float(m.group(1))); ent2.append(float(m.group(2)))
        m=re.search(r'actions distinctes : C1 (\d+), C2 (\d+)', b)
        if m: na1.append(int(m.group(1))); na2.append(int(m.group(2)))
    mo=lambda l: sum(l)/len(l) if l else 0
    return mo(c1),mo(c2),mo(ent1),mo(ent2),mo(na1),mo(na2)
labels=["ampl_C1","ampl_C2","entropie_C1","entropie_C2","n_act_C1","n_act_C2"]
data={l:[] for l in labels}
for g in GR:
    A=comps(f"A_g{g}.log"); B=comps(f"B_g{g}.log")
    for i,l in enumerate(labels): data[l].append((A[i],B[i]))
print(f"{'':<14}{'A':>9}{'B':>9}{'delta':>10}{'t':>8}")
print("-"*52)
for l in labels:
    d=[b-a for a,b in data[l]]; n=len(d); m=sum(d)/n
    sd=math.sqrt(sum((x-m)**2 for x in d)/(n-1)); se=sd/math.sqrt(n) if sd>0 else 1e-12
    ma=sum(a for a,b in data[l])/n; mb=sum(b for a,b in data[l])/n
    print(f"{l:<14}{ma:>9.3f}{mb:>9.3f}{m:>+10.3f}{m/se:>+8.2f}")
