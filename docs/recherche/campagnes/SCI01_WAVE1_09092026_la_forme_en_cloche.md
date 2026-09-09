# BALAYAGE K/ε SUR L'APPRENANT RÉPARÉ (SCI-01 Wave 1) — la forme en cloche

**Date** : 2026-09-09 (dépouillé le 09/09 20:30) · **Statut** : 🟡 **Wave 1 terminée,
dépouillée — verdict final en attente de la Wave 2 (n=20)** · **n = 10 graines appariées
× 6 bras × 1500 jours** · socle réparé (voix libre + `--detach-c2` constants), cerveaux
neufs, code **v41.68**, **0 échec sur 60 runs**.

> **Protocole et 4 juges écrits AVANT le lancement**
> (`brains/08092026_sci01_balayage_K/LISEZ_MOI.md`). La campagne re-mesure le point K=8 du
> 07/09 (mesuré avec le **rejeu faussé** APP-01, donc témoin invalide) sur le socle sain.
> Question : la forme de l'effet de K — monotone, saturée, en cloche ? Et le signe du clip
> ε = 0,2 à K=8 tient-il quand le ratio est calculé sur la politique complète C1+C2 ?

---

## 1. Le résultat en une ligne (comptage — pas un test)

**Le franchissement du mur `SimpleCrossingS9N1` → `LavaGapS5` suit une CLOCHE en K** :
**0/10 → 0/10 → 8/10 → 10/10 → 3/10** pour K = 1, 2, 4, 8, 16. **L'optimum est K=8.**
Et **le clipping ε=0,2 ne nuit plus** : K8_CLIP_e02 fait **10/10**, comme K8_NU.

## 2. Les juges — résultats stricts (MES-01, seuil Bonferroni famille de 5)

| Bras | Franchissements | Maîtrise moy. | Maîtrise 0 % |
|---|---|---|---|
| K1_TEMOIN | 0/10 | 15,5 % | 0 |
| K2_NU | 0/10 | 21,5 % | 0 |
| K4_NU | **8/10** | 14,75 % | 1 |
| K8_NU | **10/10** | 8,5 % | 2 |
| K16_NU | 3/10 | 10,75 % | 2 |
| K8_CLIP_e02 | **10/10** | 12,0 % | 1 |

**Juge 1 (maîtrise appariée vs K1)** : tous **NS** (`t` max +2,45 < seuil 3,25 à n=10).
⚠️ **Ce juge est CONFONDU PAR LE PALIER** : les franchisseurs sont mesurés dans `LavaGapS5`
(plus dur) et les non-franchisseurs dans `SimpleCrossingS9N1` — comparer leurs maîtrises
reviendrait à comparer des classes différentes. La vérif « palier égal » est la seule lisible
(niveau 4 : K1 = 15 % · K2 = 25 % ; niveau 5 : K8_NU = 7,5 % — la baisse est la carte, pas
le cerveau). **Le niveau porte la réponse.**

**Juge 2 (niveau)** : tableau ci-dessus — la cloche.

**Juge 3 (forme de K)** : 0 → 0 → 8 → 10 → 3. **Cloche, optimum K=8, retombée à K=16**
(sur-apprentissage probable — maîtrises finales souvent 0 % chez K16, signe d'instabilité).

**Juge 4 (mécaniste ε — ratio/clippés)** : télémétrie `Rejouer` présente **uniquement sur
K8_CLIP_e02** (bras NU : ratio non logué hors `RATIO_CLIPPE_ACTIF`, réserve au journal).
Résultat : ratio moyen **~0,994**, p90 **~1,006**, **fraction clippée 5,3–10,8 %** (médiane
~8 %). Le clip est **quasi inactif** : le ratio ne s'écarte déjà presque jamais de 1, donc
ε=0,2 ne mord presque pas — NU et CLIP sont pratiquement identiques, ce qui explique
l'absence d'effet du clip **dans les deux sens**.

## 3. 🔴 Le clipping du 07/09 est requalifié

Au 07/09 (rejeu faussé) : « le clipping nuit » (−1,00 pt, 7 cerveaux à 0 %). Sur le socle
réparé : **K8_CLIP_e02 = 10/10, K8_NU = 10/10** — le clip ne nuit **plus**. Deux lectures
possibles, non départagées à n=10 : (a) le « le clip nuit » était un artefact du rejeu faussé
(APP-01) ; (b) le clip est simplement inactif à ε=0,2 parce que le ratio est déjà sain
(fraction clippée ~8 %). Le juge 4 plaide pour (b) — mais (a) n'est pas exclu.

## 4. Réserves (honnêteté MES-01)

- **n=10, aucun `t` ne passe Bonferroni** (seuil 3,25, famille 5). Les franchissements sont
  des **comptages**, pas des tests.
- Le juge maîtrise est **ininterprétable en niveau croisé** (piège de palier) — seule la
  comparaison « palier égal » est propre, et elle est à petit n (niv. 4 : K4 n=2, K16 n=7).
- K reste une **constante de campagne** : la cloche suggère un optimum vers K=8, mais une
  règle dérivée (méthode v30.1) exige la Wave 2 à n=20 et, idéalement, des K entre 8 et 16.
- L'estimation de lancement (~18-22 h) est **dépassée d'un facteur ~2** (rythme réel des
  bras lourds : ~2,7 j/min K16 · ~5,8 j/min K8_CLIP) — écart consigné au journal.

## 5. Ce que la Wave 2 devra trancher

1. La cloche tient-elle à n=20 (graines 122→222) ?
2. K=8 est-il vraiment l'optimum, ou la forme est-elle un plateau 4–8 avec chute à 16 ?
3. Le clip à ε=0,2 est-il inerte (fraction ~8 %) — et un ε plus serré changerait-il le signe ?

**Outils** : `brains/08092026_sci01_balayage_K/depouiller_SCI01.py` (défaut
`manifeste_wave1.json`) · `agregat_wave1.json` (60 runs) · protocole `LISEZ_MOI.md`.
