"""v41.27 — BANC DE LA DOULEUR UNIQUE.

Vérifie que le modèle à UN SEUL état douloureux, alimenté par des couples
(pic, demi-vie), reproduit ce que l'utilisateur a décrit (19/08) :

  • une seule douleur, deux signatures : brûlure (vive, récupération LENTE) et choc
    mural (∝ vitesse d'impact, récupération RAPIDE) ;
  • le temps n'augmente PAS la douleur aiguë — il ALLONGE la récupération ;
  • indexation exponentielle dans les deux sens (le pic sature, la descente ralentit).

⚠️ CE BANC TESTE LE RÉGIME PERMANENT (400 ticks), pas seulement un transitoire de 8.
C'est l'erreur qui a fait passer la v41.26 : sa brûlure saturait à `pic/dissipation`
(×6,67) et un banc court ne pouvait pas le voir.

    PYTHONPATH=src python3 docs/recherche/scripts/banc_douleur_unique.py
"""
import naulthene.cerveau.noyau as n
from naulthene.cerveau.bus_sensoriel import DEMI_VIE_BRULURE, DEMI_VIE_CHOC


def corps():
    m = n.BiologicalHomeostasisEngine()
    m.satiete = m.hydratation = m.stimulation = m.energie = 1.0
    return m


def main():
    print("=" * 74)
    print("BANC DE LA DOULEUR UNIQUE — lue à la sortie du moteur")
    print("=" * 74)

    print("\n1. DEUX SIGNATURES, UNE SEULE DOULEUR (pic identique 0.30)")
    for lab, dv in (("brûlure (récup. LENTE)", DEMI_VIE_BRULURE),
                    ("choc   (récup. RAPIDE)", DEMI_VIE_CHOC)):
        m = corps()
        m.encaisser_douleur(0.30, dv)
        pic = m.douleur_corporelle()
        for _ in range(20):                       # 20 ticks sans nouvelle douleur
            m.encaisser_douleur(0.0, dv)
        print(f"   {lab}: pic {pic:.4f} -> après 20 ticks de repos {m.douleur_corporelle():.4f}")

    print("\n2. LE TEMPS N'AUGMENTE PAS LE PIC — il allonge la RÉCUPÉRATION")
    for expo in (1, 50, 200):
        m = corps()
        for _ in range(expo):
            m.encaisser_douleur(0.20, DEMI_VIE_BRULURE)
        pendant = m.douleur_corporelle()
        for _ in range(50):
            m.encaisser_douleur(0.0, DEMI_VIE_BRULURE)
        print(f"   exposé {expo:>3} ticks : douleur {pendant:.4f} | "
              f"après 50 ticks de repos {m.douleur_corporelle():.4f}")

    print("\n3. LE PIC SATURE (exponentielle vers le haut)")
    m = corps()
    for i in range(1, 6):
        m.encaisser_douleur(0.30, DEMI_VIE_BRULURE)
        print(f"   après {i} pic(s) de 0.30 : {m.douleur_corporelle():.4f}")

    print("\n4. RÉGIME PERMANENT — 400 ticks, par le CHEMIN RÉEL (step_metabolisme)")
    print("   ⚠️ passe par l'évacuation thermique : c'est le test que v41.26 ratait.")
    for lab, T in (("d=3 tiède", 0.096), ("d=2", 0.209),
                   ("d=1 adjacent", 0.457), ("d=0 DANS la lave", 1.0)):
        m = corps()
        for _ in range(400):
            m.satiete = m.hydratation = m.stimulation = m.energie = 1.0
            m.step_metabolisme(cout_action=0.1, erreur_jepa=0.0,
                               nouvelle_case_visitee=False, chaleur_apres=T)
        print(f"   {lab:18s} T={T:.3f} -> douleur permanente {m.douleur_corporelle():.4f}")
    print(f"   [v41.26 : 0.4317 partout dès d=1 — la brûlure amplifiait ×6,67]")

    print("\n5. LA VITESSE D'IMPACT — se cogner vite vs à l'arrêt")
    for v, lab in ((1.0, "pleine course"), (0.33, "au ralenti"), (0.10, "à l'arrêt")):
        m = corps()
        m.encaisser_douleur(v, DEMI_VIE_CHOC)
        print(f"   vitesse {v:.2f} ({lab:14s}) : douleur {m.douleur_corporelle():.4f}")

    print("\n6. LE ZÉRO EXISTE-T-IL ? (un corps au repos ne souffre pas)")
    m = corps()
    for _ in range(100):
        m.encaisser_douleur(0.0, DEMI_VIE_BRULURE)
    print(f"   100 ticks sans agression : douleur {m.douleur_corporelle():.6f}")
    print("=" * 74)


if __name__ == "__main__":
    main()
