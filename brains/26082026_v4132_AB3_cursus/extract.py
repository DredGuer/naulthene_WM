import re, json, os, glob
GRAINES = [11,22,33,44,55,66,77,88,99,111,122,133,144,155,166,177,188,199,211,222]
def dernier_bilan(path, n=400):
    """Metriques agregees sur les N dernieres nuits."""
    txt = open(path, errors='ignore').read()
    # decoupe par nuit
    nuits = txt.split("🌙 Jour ")
    nuits = nuits[1:]
    tail = nuits[-n:]
    niv=[]; maitrise=[]; energie=[]; sat=[]; ratio=[]; accord=[]; jepa=[]; recolte=[]
    for b in tail:
        m = re.search(r'Niveau (\d+)/15 — maîtrise (\d+)%', b)
        if m: niv.append(int(m.group(1))); maitrise.append(int(m.group(2)))
        m = re.search(r'⚡ moy ([\d.]+) \(min', b)
        if m: energie.append(float(m.group(1)))
        m = re.search(r'Satiété ([\d.]+)', b)
        if m: sat.append(float(m.group(1)))
        m = re.search(r'ratio ([\d.]+)x\) \| accord ([\d.]+)%', b)
        if m: ratio.append(float(m.group(1))); accord.append(float(m.group(2)))
        m = re.search(r'Erreur JEPA moy: ([\d.]+)', b)
        if m: jepa.append(float(m.group(1)))
        m = re.search(r'récolté (\d+)', b)
        if m: recolte.append(int(m.group(1)))
    def mo(l): return sum(l)/len(l) if l else None
    # niveau FINAL atteint = max sur tout le run
    tous_niv = [int(x) for x in re.findall(r'Niveau (\d+)/15', txt)]
    return dict(niveau_max=max(tous_niv) if tous_niv else None,
                niveau_fin=niv[-1] if niv else None,
                maitrise=mo(maitrise), energie=mo(energie), satiete=mo(sat),
                ratio_c2c1=mo(ratio), accord=mo(accord), jepa=mo(jepa),
                recolte=mo(recolte), n_nuits=len(tail))
res={}
for g in GRAINES:
    for bras in "AB":
        p=f"{bras}_g{g}.log"
        if os.path.exists(p):
            res.setdefault(str(g),{})[bras]=dernier_bilan(p)
json.dump(res, open("resultats_bruts.json","w"), indent=1)
print(f"{len(res)} graines extraites")
