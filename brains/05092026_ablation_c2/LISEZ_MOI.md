# L'ABLATION PROPRE DE C2 — le néo-cortex sert-il, quand le réflexe respire ?

**Protocole écrit AVANT le lancement** (05/09/2026). Campagne `05092026_ablation_c2`.

## La question

Le dépôt affirme depuis des mois que **« couper C2 ne change le score de 0,0 point sur les
6 niveaux »** (78 cellules d'ablation). Ce résultat est **CONFONDU**.

🔴 **Vérifié dans le code le 05/09** : la lésion `c2_coupe` du banc
(`banc_ablation.py:246`) coupe C2 en posant `force_planification = 0`. Or le gain de C1 vaut
`clamp(vigueur_min_c1(force) / amplitude_c1, 0.25, 4)` avec `vigueur_min_c1(f) = 2.1 × f`
(`noyau.py:5362`) : à `force = 0`, le numérateur s'annule et **`gain_c1` est plaqué à sa
borne basse, 0,25**.

> **L'ablation historique ne coupait pas C2 : elle coupait C2 ET étranglait C1 à un quart.**
> Règle de mesure §6.2 — une ablation confondue ne dit pas lequel des deux agissait.

⚠️ **Deux faits qui rectifient le récit du projet** :
1. `c2_coupe` **n'existe que dans le banc**, jamais dans le cursus — le « 0,0 pt » vient d'un
   banc court sur cerveau entraîné, jamais d'une campagne de 1500 jours.
2. Aucun drapeau ne coupait C2 dans le cursus avant aujourd'hui. **`--sans-c2` est créé pour
   cette campagne** (v41.57).

## Ce que `--sans-c2` fait, et ne fait pas

| | |
|---|---|
| ✅ Retire la **voix** de C2 de la fusion : `logits_finaux = voix_c1` | `noyau.py:1526` |
| ✅ Laisse `force_planification` **intacte** ⇒ `gain_c1` identique au bras de référence | c'est toute la différence avec `c2_coupe` |
| ✅ C2 **continue de tourner** (rollout, budget, télémétrie) | même discipline que `--sans-gradient-c2` |
| ❌ Ne touche pas `simuler_futur_et_planifier` | seule la voix est retirée, pas l'organe |

## Le protocole — 3 bras, et pourquoi 3

C2 et le gain sont **couplés** : deux bras donneraient à nouveau une ablation confondue
(règle §6.2 — « si deux mécaniques sont couplées, il faut trois bras »).

| Bras | `gain_c1` | Voix de C2 | Ce qu'il isole | Runs |
|---|---|---|---|---|
| **LIBRE** | ≡ 1 | active | référence saine | **0** — les 20 runs de `04092026_cursus_complet` |
| **LIBRE_SANS_C2** | ≡ 1 | **coupée** | **l'effet propre de C2** | 20 |
| **TEMOIN_SANS_C2** | v37.0 | **coupée** | la part du gain dans le « 0,0 pt » historique | 20 |

20 graines appariées × 1500 jours · **40 runs neufs** · 6 en parallèle · ~8 h.
Graines : les mêmes que les trois campagnes précédentes (11 … 222).

```bash
zsh brains/05092026_ablation_c2/lancer.sh
```

## Les juges, posés d'avance

⚠️ **Bonferroni à 3 métriques** (niveau, maîtrise, amplitude C1) ⇒ seuil `t` = **2,86**.

| Juge | Comparaison | C2 est UTILE si | C2 est INERTE si |
|---|---|---|---|
| **1. Maîtrise** | LIBRE − LIBRE_SANS_C2 | δ > 0, `t` > 2,86 | δ ≈ 0 |
| **2. Niveau** | LIBRE − LIBRE_SANS_C2 | δ > 0, `t` > 2,86 | δ ≈ 0 |
| **3. Confusion historique** | LIBRE_SANS_C2 − TEMOIN_SANS_C2 | — | δ > 0 significatif ⇒ **le « 0,0 pt » était bien confondu** |
| **4. Le gain reste intact** | `gain_c1` moyen | — | doit valoir **1,00** en LIBRE_SANS_C2 et **≫ 0,25** en TEMOIN_SANS_C2 |

⚠️ **Le juge 3 est le vrai enjeu méthodologique** : il mesure ce que l'ablation historique
attribuait à C2 alors que ça venait de l'étranglement de C1.

⚠️ **Le juge 4 est un garde-fou, pas un résultat** : s'il échoue, la campagne est invalide.

## Interprétation prévue AVANT de voir les chiffres

| Résultat | Lecture |
|---|---|
| Juges 1-2 **positifs** | C2 sert dès que C1 respire — **la refonte de C2 n'est pas justifiée**, il faut l'amplifier |
| Juges 1-2 **nuls** | C2 est **réellement inerte**, cette fois sans confusion ⇒ la refonte en générateur d'intention devient justifiée par la mesure |
| Juges 1-2 **négatifs** | C2 **nuit** — hypothèse à ne pas écarter d'avance |

⚠️ Un δ nul serait un **résultat**, pas un échec de campagne — à condition que le juge 4 passe.

## Vérifications au dépouillement

| Vérification | Pourquoi |
|---|---|
| `[ABLATION] C2 MUET` sur 40/40 | le drapeau a atteint l'individu (leçon v41.4) |
| `[BRAS A]` sur 20/20 LIBRE_SANS_C2, **0/20** TEMOIN_SANS_C2 | pas de contamination croisée |
| Niveau lu par `env_id`, jamais par index | invariant v35.0 |
| Test des extrêmes (retrait des 4) | c'est lui qui a tué la directivité (02/09) et le juge 2 du cursus (04/09) |
| Test de tautologie | conditionner sur « a gagné au moins une fois » |
| `δ_A/A` reporté à côté du résultat | plancher réel de détection |

## Pré-vol (fait le 05/09, avant lancement)

| Test | Résultat |
|---|---|
| Syntaxe (`ast.parse`) | ✅ |
| Assertion runtime `SANS_C2 is True` | ✅ atteinte |
| `gain_c1` en LIBRE_SANS_C2 | ✅ **×1,00** (inchangé) |
| `gain_c1` en TEMOIN_SANS_C2 | ✅ **×0,86** vs 0,88 en référence — **pas d'étranglement** (contre 0,25 pour `c2_coupe`) |
| La lésion change le comportement | ✅ **5/5 grandeurs** divergent sur 3 nuits (accord, H, JEPA, gestes stériles, C1) |
| **A/A (2 runs identiques, 40 j)** | ✅ **BIT-IDENTIQUES** (seules diffèrent les lignes portant le nom du fichier `.brain`) ⇒ **δ_A/A = 0,000000** |

> **Le banc est déterministe.** Tout écart A/B mesuré sera un effet réel, pas du bruit de
> harnais. Niveau 2, maîtrise 55 %, `C1 = 3,975`, `gain ×1,00` — identiques sur les deux
> répliques. `brains/AA_ablation_c2_05092026/`.

⚠️ **Fausse alerte consignée** : mon premier test de non-régression comparait `Réc. moyenne`,
qui vaut **0,000 dans les deux bras** sur 3 jours (un agent neuf ne gagne rien si tôt). Le
test ne pouvait rien discriminer — ce n'était pas le bug v41.4, c'était un mauvais choix de
grandeur. *Un test qui ne peut pas échouer ne vérifie rien.*
