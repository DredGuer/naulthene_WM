# Sondes à coût zéro — 06/09/2026

Quatre mesures faites **sans lancer un seul run**, sur les 40 `.brain` de
`04092026_cursus_complet` (20 graines × 2 bras). Aucune écriture : chaque `.brain` est
**copié** avant chargement (règle de mesure §8).

| Sous-dossier | Question | Résultat | Carnet |
|---|---|---|---|
| `jepa_action/` | le modèle du monde distingue-t-il les actions ? | ✅ oui, ratio **0,48** — mais **÷10** depuis la naissance (4,79) | [SONDES_06092026](../../docs/recherche/campagnes/SONDES_06092026_le_levier_s_efface_le_corps_domine.md) |
| `permeabilite/` | les sens sont-ils dilués dans `integrateur_bio` ? | ❌ **réfuté** — le corps pèse **2,5 à 5,6×** la vision | idem |
| `mixage_pertes/` | quel terme de perte sculpte quelle couche ? | 🔴 le **critique prend 89,24 %** du gradient d'`integrateur_bio` | idem |
| `horizon7/` | les branches du rollout divergent-elles à h=7 ? | 🔴 **97 % de séparation perdue** — cause : `argmax(tete_motrice)` | [ROLLOUT_06092026](../../docs/recherche/campagnes/ROLLOUT_06092026_le_trou_noir_du_reflexe.md) |
| `platitude_c1/` | pourquoi la politique de C1 est-elle figée ? | 🔴 ratio inter/intra **3,91** contre **0,06** chez PPO | [PLATITUDE_06092026](../../docs/recherche/campagnes/PLATITUDE_06092026_une_politique_sans_etat.md) |
| `c1_branches/` | C1 vote-t-il pareil sur les 8 branches ? | 🟡 **61,3 %** des ticks, mais dispersion 2,5–100 % | idem |
| `relu_mortes/` | combien de neurones sont éteints ? | 🔴 **56 %** dans `pensee_bio`, **40/40 cerveaux** | idem |

Agrégats machine : `agregat.json` et `agregat_platitude.json`.

⚠️ **Ces sondes sont des DIAGNOSTICS, pas des leviers.** Aucune n'établit de lien causal
avec le plafond. Deux d'entre elles ont cependant **prédit** un levier confirmé ensuite :
le mixage des pertes (→ `--detach-c2`, +5,25 pt) et le comptage des pas de gradient
(→ `--epoques-nuit 8`, +10,25 pt).
