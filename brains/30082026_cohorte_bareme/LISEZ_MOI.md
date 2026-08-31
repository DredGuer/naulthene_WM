# Cohorte du barème — 30/08/2026

Réplication à n=40 de l'[audit du génome](../../docs/etat_des_lieux/30082026_le_genome_audit_des_constantes.md).
Analyse complète : [COHORTE_30082026](../../docs/recherche/campagnes/COHORTE_30082026_le_bareme_ne_predit_rien.md).

## Ce qu'on cherchait

« Un cerveau qui écoute un peu plus le monde s'en sort-il mieux ? »

**Réponse : non — la corrélation est une TAUTOLOGIE.** `part_monde > 0` signifie « ce
cerveau a gagné », et la maîtrise est un taux de victoire. Dix-septième réfutation.

## Protocole

**Aucun run lancé.** Les 40 cerveaux existaient déjà (cohorte AB3 du 26/08).

```bash
WANDB_MODE=offline PYTHONPATH=src venv/bin/python \
    -m naulthene.instruments.cohorte_bareme \
    --dossier brains/26082026_v4132_AB3_cursus --bras A_ --niveau 3 --jours 2 \
    --sortie brains/30082026_cohorte_bareme/cohorte_A_niv3.json
# idem --bras B_
```

- 20 graines × 2 bras · niveau **3** forcé · 800 ticks/cerveau
- Doublons Finder (`X 2.brain`) **exclus**
- Chaque `.brain` lu depuis une **copie**, jamais en place
- Sonde vérifiée nettoyée AVANT lancement (disque + `__pycache__` purgé + module en mémoire)

## Résultats

| Prédicteur | r (n=40) | t | Réplique A/B |
|---|---:|---:|---|
| part du MONDE | +0,4191 | +2,85 | ✅ oui |
| part CURIOSITÉ | −0,0173 | −0,11 | ❌ signe s'inverse |
| solde hors monde | +0,3745 | +2,49 | ✅ oui |

**Test de tautologie** — chez les seuls cerveaux ayant gagné (n=36) : `t = +2,34`, **sous
le seuil de Bonferroni (2,39)**. Le signal était « avoir gagné », pas « combien écouter ».

## Fichiers

- `cohorte_A_niv3.json` / `cohorte_B_niv3.json` — mesures par cerveau + corrélations
- `cohorte_A_niv3.log` / `cohorte_B_niv3.log` — sorties console complètes
  ⚠️ **non versionnés** (`brains/**/*.log` est gitignoré) : ils restent sur le disque
  local. Les JSON, eux, sont versionnés et portent l'intégralité des chiffres — c'est
  l'agrégat qui survit, conformément à la règle de gestion des données.

Les `.brain` sources restent dans `brains/26082026_v4132_AB3_cursus/` — **non copiés ici**,
ils n'ont jamais été modifiés (lecture sur copie temporaire, supprimée après usage).
