# SCI-01 — LE VERDICT À n=20 : la cloche est confirmée, le clip est inerte

**Date** : 2026-09-12 (campagne du 09-11/09/2026, dépouillée le 12/09) · **Statut** :
✅ **Wave 1 + Wave 2 terminées, dépouillées à n=20** · **n = 20 graines appariées × 6 bras
× 1500 jours = 120 runs, 0 échec** · code **v41.68** (et v41.76 pour les derniers bras — voir
§5, hétérogénéité **prouvée non-cognitive**) · socle voix libre + `--detach-c2`.

> Remplace le carnet de la Wave 1
> ([SCI01_WAVE1](SCI01_WAVE1_09092026_la_forme_en_cloche.md)) pour la conclusion :
> la Wave 1 donnait la forme à n=10, celle-ci la tranche à n=20.

---

## 1. Le résultat en une ligne

**Le franchissement du mur `SimpleCrossingS9N1` → `LavaGapS5` suit une CLOCHE nette en K —
0 · 1 · 13 · 18 · 4 sur 20 — avec un optimum à K=8, et le clipping ε=0,2 est INERTE**
(fraction clippée médiane ~8 %, K8_CLIP_e02 = 20/20, Fisher vs K8_NU `p` = 0,49).

## 2. Les juges (MES-01 strict, seuil Bonferroni dérivé de n=20 : 2,86)

| Bras | Franchissements | Maîtrise moy. | Maîtrise 0 % |
|---|---|---|---|
| K1_TEMOIN | **0/20** | 14,0 % | 0 |
| K2_NU | **1/20** | 20,0 % | 0 |
| K4_NU | **13/20** | 16,1 % | 1 |
| K8_NU | **18/20** | 12,0 % | 2 |
| K16_NU | **4/20** | 9,5 % | 5 |
| **K8_CLIP_e02** | **20/20** 🔴 | 12,5 % | 1 |

**Juge 1 — maîtrise appariée (le seul test formel) :**

| Comparaison | δ | `t` | Verdict | Extrêmes retirés |
|---|---|---|---|---|
| K2_NU − K1 | **+6,00 pt** | **+3,56** | ✅ **SIG** (seuil 2,86) | ❌ +3,75 · `t` = +2,32 NS (n=16) |
| K4_NU − K1 | +2,05 | +0,81 | NS | −1,81 NS |
| K8_NU − K1 | −2,00 | −0,80 | NS | −4,69 NS |
| K16_NU − K1 | −4,50 | −1,81 | NS | −1,56 NS |
| K8_CLIP − K8_NU | +0,50 | +0,19 | NS | +3,13 NS |

⚠️ **Ce juge reste CONFONDU PAR LE PALIER** : les franchisseurs sont mesurés dans
`LavaGapS5` (plus dur), les autres dans `SimpleCrossingS9N1`. Le seul SIG (K2) est un
artefact de cette confusion — K2 ne franchit pas (1/20), donc sa maîtrise est mesurée au
niveau 4, le palier facile. Il **ne survit d'ailleurs pas** au retrait des 4 extrêmes.
**Le juge 2 (niveau) porte la réponse.**

**Maîtrise à PALIER ÉGAL (niveau 4 seulement — la lecture propre) :**

| Bras | niv. 4 | n |
|---|---|---|
| K1_TEMOIN | 15,0 % | 20 |
| K2_NU | 20,0 % | 19 |
| K4_NU | 25,0 % | 7 |
| K8_NU | 27,5 % | 2 |
| K16_NU | 7,5 % | 16 |

À **palier égal**, la maîtrise **monte avec K** jusqu'à 8 (15 → 20 → 25 → 27,5 %), puis
**K16 s'effondre** (7,5 %). C'est la même cloche, lue sur la bonne échelle.

## 3. 🔴 Le clipping : la requalification est confirmée à n=20

| | 07/09 (rejeu faussé) | **12/09 (socle réparé, n=20)** |
|---|---|---|
| K8_CLIP vs témoin | −1,00 pt (« le clip nuit ») | **20/20 franchissements** |
| K8_CLIP vs K8_NU | — | δ +0,50 pt, `t` = +0,19 (**NS**), Fisher `p` = **0,49** |
| Fraction clippée | — | **5,3–12,6 %** (médiane ~8 %) |
| Ratio moyen | — | ~0,992–0,997 · p90 ~1,003–1,012 |

**Le clip ne nuit pas, et il ne sert presque à rien** : le ratio d'importance du socle réparé
reste collé autour de 1, donc ε=0,2 ne mord que sur ~8 % des échantillons. Les deux bras K8
(NU et CLIP) sont **statistiquement indiscernables** (`p` = 0,49). L'énoncé « le clipping de
PPO nuit » du 07/09 était un **artefact du rejeu faussé** (APP-01), pas une propriété du clip.

## 4. Ce qui est établi, et ce qui ne l'est pas

**Établi** :
- La **forme en cloche** de l'effet de K sur le franchissement du mur : 0/20 → 1/20 → 13/20 →
  **18/20** → 4/20. Optimum **K=8**, effondrement à **K=16** (sur-apprentissage : 5 cerveaux
  à maîtrise 0 % chez K16, contre 1 chez K4).
- Le **clip ε=0,2 est inerte** sur le socle réparé — et l'ancien « il nuit » est requalifié.
- K=4 est un **saut de phase** (1/20 à K2 → 13/20 à K4) : il existe un seuil, pas une pente.

**Non établi** :
- **Aucun `t` de maîtrise n'est interprétable** (confusion de palier) : la cloche repose sur
  des **comptages**, pas sur un test. Le seul SIG est un artefact, et il tombe aux extrêmes.
- K=8 **n'est pas dérivé** d'une grandeur vécue : c'est toujours une **constante de campagne**
  (méthode v30.1 : mesurer le fixe, dériver ensuite). La cloche justifie de **garder K=8**,
  pas encore une règle adaptative.
- Le **juge 4 est partiel** : la télémétrie du ratio n'existe que sur le bras CLIP (réserve
  consignée au journal des runs) — impossible de comparer la distribution du ratio NU vs CLIP.
- Rien n'est dit au-delà du **niveau 5** : personne n'atteint le niveau 6, le cursus en compte 15.

## 5. ⚠️ Hétérogénéité de code pendant la campagne — mesurée et requalifiée

**Constat** : la Wave 2 a tourné du 09/09 23:11 au 11/09 23:15, pendant que 4 commits **VIS-01**
(10/09 16:03 → 20:12) modifiaient `noyau.py` (**+352 lignes**, en-tête porté à v41.75/41.76).
Les bras K1→K8 ont donc tourné sous **v41.68**, K16 à cheval, K8_CLIP sous **v41.76**.

**Vérification A/A (12/09, `--graine 11`, 10 jours, 8 époques/nuit, sans `--telemetrie-3d`, sur
worktree `44a45a7` = v41.68 vs HEAD = v41.76)** :

| Contrôle | Résultat |
|---|---|
| 9 lignes clés du bilan (Cursus, Arbitrage C1/C2, Chrono, JEPA, Mémoire, Maîtrise, Énergie, Rejouer) | ✅ **identiques** |
| Logs complets (505 lignes chacun) | ✅ **identiques** hors nom de fichier `.brain` |
| Séquence des jours (`🌙 Jour N`) | ✅ identique |
| **Payload sémantique des `.brain`** (47 tenseurs/scalaires) | ✅ **aucune différence** |

**Conclusion** : les changements VIS-01 sont de la **télémétrie opt-in** (`--telemetrie-3d`,
absent des lanceurs de campagne) et **ne touchent pas la dynamique d'apprentissage** — la
cohorte est **fonctionnellement homogène**. Réserve consignée : la règle « même code » n'a pas
été respectée *littéralement* ; elle l'est *fonctionnellement*, sur preuve mesurée.

## 6. Outils et traces

- Protocole pré-enregistré : `brains/08092026_sci01_balayage_K/LISEZ_MOI.md`
- Dépouillement : `depouiller_SCI01.py manifeste.json` → `depouillement_final_n20.txt`
- Agrégat : `agregat_wave1.json` (60 runs) · `agregat.json` (120 runs)
- Manifestes : `manifeste_wave1.json` (10 graines) · `manifeste.json` (20 graines)
- Instrument corrigé au passage : `journal_cursus.py` — le motif jetait les **nuits de
  promotion** (`maîtrise —`), ce qui a produit un **faux refus de couverture** MES-01 sur
  `K8_NU_g144` (promu au jour 1500). Re-dépouillement des 6 campagnes publiées : **0 verdict
  changé** (5 strictement identiques, BP marginalement déplacé mais NS→NS).
