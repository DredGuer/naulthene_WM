"""Combien de promotions le decalage d'un jour (§7 du chantier v41.4) a-t-il coutees ?

`facteur_guidage` est calcule en DEBUT de journee sur la fenetre de la VEILLE ;
`_maturite_niveau` est evalue la NUIT avec la maitrise DU JOUR. Le produit melange
donc deux instants, et sous-estime la maturite pendant les phases de progression.

Ce script rejoue le critere sur les logs en remplacant l'autonomie LUE par
l'autonomie COHERENTE avec la maitrise du jour meme, et compte les promotions
qui auraient eu lieu.

⚠️ Le resultat est une BORNE SUPERIEURE : une promotion plus tot vide la fenetre
et change toute la suite du run. Il dit « combien de fois le critere a refuse un
agent qui remplissait la condition », pas « combien de niveaux il aurait atteint ».
"""
import re, glob, os, sys

SEUIL_MATURITE = 0.400
SEUIL_FIN_SEVRAGE = 0.90
RE_MATU = re.compile(
    r"🌡️ ([\d.]+) / [\d.]+ — régularité (\d+)% × consolidation (\d+)% × autonomie (\d+)%")

def analyser(chemin):
    reelles = virtuelles = jours = 0
    with open(chemin, errors="ignore") as fh:
        for l in fh:
            if "[PROMOTION]" in l:
                reelles += 1
                continue
            m = RE_MATU.search(l)
            if not m:
                continue
            jours += 1
            mat = float(m.group(1))
            reg, cons = int(m.group(2)) / 100, int(m.group(3)) / 100
            auto_coherente = min(1.0, reg / SEUIL_FIN_SEVRAGE)
            if mat < SEUIL_MATURITE <= reg * cons * auto_coherente:
                virtuelles += 1
    return jours, reelles, virtuelles

def main(rep):
    print(f"{'run':>26s} {'jours':>6s} {'reelles':>8s} {'si synchrone':>13s} {'manquees':>9s}")
    for f in sorted(glob.glob(os.path.join(rep, "long414_*g*.log"))):
        j, r, v = analyser(f)
        print(f"{os.path.basename(f)[:-4]:>26s} {j:6d} {r:8d} {r+v:13d} {v:9d}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
