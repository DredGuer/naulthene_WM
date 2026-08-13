"""Sonde des poids — état de santé synaptique couche par couche.

Instrument de diagnostic **en lecture seule** (v37.0) : ouvre un `.brain` et affiche,
pour chaque `NaultheneLinearSynaptique`, la norme du poids de base rapportée à sa
`norme_naissance`. C'est la mesure directe de l'érosion nocturne cumulée.

Ne sauvegarde jamais, ne fait jamais tourner d'apprentissage.

Ce qu'il faut lire :

- **ratio = |base| / norme_naissance** — la fraction de sa force de naissance qu'une
  couche a conservée. Un ratio à **exactement 10,00 %** signifie que la couche est collée
  au plancher vital (`FRACTION_NORME_MIN_COUCHE = 0.10`, v34.0-fix1) : elle est vivante
  *uniquement* parce que le garde-fou l'a retenue. Vivante, mais très affaiblie.
- **|annexe|** — le poids appris de la journée, avant consolidation nocturne. À 0,0000
  partout, le cerveau n'apprend plus rien : pas de gradient, donc pas de myéline, donc
  érosion à taux plein la nuit suivante.
- **myéline** — ne peut venir QUE du gradient (`myeline_M = max(myeline_M, |annexe|)`).
  Rappel mesuré : le maximum observé sur les cerveaux du dépôt est 0,0038, très loin de
  `SEUIL_CRISTAL = 0.80` — la Cristallisation Souple v26.0 ne s'est jamais déclenchée.

Diagnostic de référence, cerveau `070820261310_V36_600_RMD.brain` : **6 couches sur 12**
collées au plancher vital, dont `tete_motrice` et `cortex_prefrontal` — les deux têtes de
décision. `annexe = 0` partout. Voir `docs/ameliorations_appliquees/CHANTIER_v37_equilibre_c1_c2.md` §2.2 et §3.

Usage :
    PYTHONPATH=src python -m naulthene.instruments.sonde_poids <brain>
"""

import argparse

import torch

from naulthene.cerveau import noyau as N
from naulthene.cerveau.persistance import PersistanceAnatomique

TOLERANCE_PLANCHER = 0.005  # marge sous laquelle un ratio est considéré « collé au plancher »


def sonder(chemin_brain: str) -> None:
    etat = PersistanceAnatomique(chemin_brain).charger_ou_naitre()
    cerveau = etat.agent

    print(f"\n{'couche':<28}{'|base|':>10}{'|annexe|':>11}{'myéline':>11}"
          f"{'naissance':>11}{'ratio':>9}")
    print("─" * 80)

    au_plancher = []
    for nom, module in cerveau.named_modules():
        if not hasattr(module, "base_weight"):
            continue
        base = module.base_weight.norm().item()
        annexe = getattr(module, "annexe_weight", None)
        myeline = getattr(module, "myeline_M", None)
        naissance = getattr(module, "norme_naissance", None)

        n_annexe = annexe.norm().item() if annexe is not None else float("nan")
        n_myeline = myeline.max().item() if myeline is not None else float("nan")
        n_naissance = naissance.item() if naissance is not None else float("nan")
        ratio = base / max(1e-9, n_naissance)

        marque = ""
        if abs(ratio - N.FRACTION_NORME_MIN_COUCHE) < TOLERANCE_PLANCHER:
            marque = "  ← plancher"
            au_plancher.append(nom)

        print(f"{nom:<28}{base:>10.4f}{n_annexe:>11.4f}{n_myeline:>11.6f}"
              f"{n_naissance:>11.4f}{ratio:>8.2%}{marque}")

    print("─" * 80)
    total = sum(1 for _, m in cerveau.named_modules() if hasattr(m, "base_weight"))
    if au_plancher:
        print(f"⚠️  {len(au_plancher)}/{total} couches collées au plancher vital "
              f"({N.FRACTION_NORME_MIN_COUCHE:.0%} de la naissance) :")
        for nom in au_plancher:
            print(f"      • {nom}")
        print("   Elles ne survivent que par le garde-fou v34.0-fix1 — vivantes mais affaiblies.")
    else:
        print(f"✅ Aucune couche au plancher vital ({total} couches saines).")

    # Échelle réelle des deux têtes de décision : c'est ce qui fixe le rapport de force
    # C1/C2 dans la fusion, indépendamment de force_planification.
    with torch.no_grad():
        entree = torch.randn(200, cerveau.integrateur_bio.base_weight.shape[0],
                             device=cerveau.actions_eye.device)
        logits = cerveau.tete_motrice(entree)
        valeurs = cerveau.cortex_prefrontal(entree)
    amplitude = (logits.max(1).values - logits.min(1).values).mean().item()
    print(f"\n  tête motrice (C1)      : σ={logits.std().item():.5f}  amplitude={amplitude:.5f}")
    print(f"  cortex préfrontal (C2) : σ={valeurs.std().item():.5f}")


def main() -> None:
    p = argparse.ArgumentParser(description="État de santé synaptique d'un .brain (lecture seule).")
    p.add_argument("brain", help="chemin du .brain à sonder")
    sonder(p.parse_args().brain)


if __name__ == "__main__":
    main()
