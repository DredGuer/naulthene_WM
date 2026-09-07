# SCI-01 — BALAYAGE K/ε SUR L'APPRENANT RÉPARÉ (v41.68)

**Date** : 2026-09-08 · **Statut** : 📋 protocole écrit AVANT lancement · **n** : 20 graines ×
1500 jours par bras (voir « Calibrage » pour le lancement par vagues) · code **v41.68**.

> Contexte : le point K=8 (+10,25 pt, 07/09) a été mesuré avec le **rejeu faussé**
> (APP-01, C1 seul la nuit) — il n'est plus un témoin valide pour l'apprenant réparé.
> SCI-01 re-mesure la **forme** de l'effet du nombre d'époques et de ε **sur le socle sain**
> (voix libre + `--detach-c2` constants sur TOUS les bras, y compris le témoin K=1).
> Source : registre SCI-01, [protocoles en réserve](../../docs/ameliorations/07092026_protocoles_en_reserve.md) §2.

## 1. La question

`K` (époques de politique par nuit) : l'effet est-il **monotone**, **saturé** ou
**retourné** ? `ε` (clip PPO, à K=8) : le « le clipping NUIT » du 07/09 tient-il quand le
ratio est enfin calculé sur la bonne politique ?

## 2. Bras (Wave 1) — le calibrage anti-saturation

Tous les bras : `--gain-c1-libre --detach-c2` (constants) + le `K`/clip du bras.

| Bras | `--epoques-nuit` | clip | Rôle |
|---|---|---|---|
| **K1_TEMOIN** | 1 | non | témoin réparé — « un pas par nuit » sur le nouvel apprenant |
| **K2_NU** | 2 | non | forme basse |
| **K4_NU** | 4 | non | forme |
| **K8_NU** | 8 | non | point publié, re-mesuré proprement |
| **K16_NU** | 16 | non | forme haute (sur-apprentissage possible) |
| **K8_CLIP_e02** | 8 | `ε = 0,2` | isole l'effet du clip au K du point publié |

**Wave 2 (différée, décision après Wave 1)** : `K8_CLIP_e5` (et éventuellement `K4_CLIP`),
**ne brûle pas 40 runs d'avance** — c'est le calibrage demandé. ⚠️ `ε = 0,5` suppose un
paramètre de clip réglable (constant `EPSILON_CLIP` aujourd'hui) : petit changement de code
à faire **avant** la Wave 2, jamais dans la Wave 1.

## 3. Juges (pré-enregistrés) — convention MES-04 (famille de 3 / 5)

Seuil dérivé par `depouillement.seuil_t` (α = 0,05 bilatéral, Bonferroni sur le nombre de
comparaisons déclaré au manifeste). Famille primaire : les 5 comparaisons K-vs-K1 et
CLIP-vs-K8_NU.

| Juge | Grandeur | AIDE si |
|---|---|---|
| **1. Maîtrise** | δ apparié vs K1_TEMOIN (et CLIP vs K8_NU) | δ > 0, `t` > seuil, survit au retrait des 4 extrêmes |
| **2. Niveau** | franchissement (Fisher bras par bras) | — |
| **3. FORME de K** (juge de réalité de SCI-01) | maîtrise(K) vs K — monotone ? saturée ? retournée ? | lecture graphique + δ par palier de K |
| **4. Mécaniste ε** | distribution du ratio `exp(lp − lp_old)` **et fraction clippée** (logs `Rejouer` console/W&B, v41.64/68) | NU : ratio libre autour de ~1 puis divergence progressive ; CLIP : ratio borné [1−ε, 1+ε], fraction clippée mesurée |

Indicateurs clés par nuit, **extractibles des `*.log`** (ligne console `Rejouer (v41.68)` :
parité max, entropie moy, ratio moy, p90, fraction clippée) **et** clés W&B `Rejouer_*`.

## 4. Pré-vol obligatoire (avant toute vague de 1500 jours)

1. **Manifeste** : format validé par chargement `Manifeste.depuis_fichier` (bras, graines,
   gardes, famille).
2. **Deux nuits réelles** sur un run court (CPU, graine 11, `K8_NU`, `--jours 2`) :
   exit 0 · deux bilans `🌙 Jour` · **aucune** violation du garde de parité de forme
   (v41.64) · ligne `Rejouer (v41.68)` présente à chaque nuit.
3. **Garde-fou bit** (v41.4/62) : le drapeau `[VARIANTE] N epoques` doit apparaître dans
   chaque log (40/40 attendu en vague).

## 5. Protocole de lancement

```bash
zsh brains/08092026_sci01_balayage_K/lancer.sh        # vagues de 6 en parallèle
```

Dépouillement (après complétude) : `depouiller_SCI01.py` + manifeste strict — aucun
`agregat` sur campagne incomplète (MES-01).

## 6. Limites et règles

- Les cerveaux K1_K8 du 07/09 **ne sont pas** des témoins valides (rejeu faussé) : aucun
  run n'est réutilisé, tout est neuf sur le code v41.68.
- `K` reste une constante de campagne : la forme mesurée ici décidera d'une **règle
  dérivée** (méthode v30.1) ou du maintien d'un hyperparamètre posé (registre SCI-01).
- Niveau : le juge « niveau » peut saturer (plafond niv. 4-5) — la maîtrise porte la
  réponse, comme pour EPOQUES.

## 7. Liens

- Registre [SCI-01](../../docs/ameliorations/REGISTRE_PROBLEMES_A_CORRIGER.md)
- APP-01/02 (v41.64), MES-01 (v41.65), MES-02 (v41.66), MES-04/API-01 (v41.67)
- Convention statistique : famille déclarée, `t` dérivé (MES-04, 08/09).
