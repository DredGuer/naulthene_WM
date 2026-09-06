# LES ÉPOQUES DE LA NUIT — la politique reçoit-elle assez de pas de gradient ?

**Protocole écrit AVANT le lancement** (06/09/2026). Campagne `06092026_epoques_nuit`.
Piste §3 du [PLAN_05092026](../../docs/ameliorations/PLAN_05092026_toutes_les_pistes_classees.md),
classée 🟢 la plus haute et jamais testée.

## La question

**Mesuré (zéro run)** : la politique reçoit **UN SEUL pas de gradient par journée** de
~400 ticks. `apprendre_journee` fait un `step()`, `rever` en fait un second qui ne porte
**que JEPA** (vérifié : aucune `log_prob`, aucun avantage, aucune tête motrice).

| | Pas de politique | Ticks | Pas / tick |
|---|---|---|---|
| **PPO** (défauts SB3, même banc) | **23 680** | 152 043 | **0,1557** |
| **Naulthène** (vie entière) | **1 500** | ~600 000 | **0,0025** |

**63× moins de pas par tick vécu.**

**Et le mécanisme est mesuré** ([PLATITUDE](../../docs/recherche/campagnes/PLATITUDE_06092026_une_politique_sans_etat.md)) :

| Grandeur (LIBRE_g11, journée réelle de 400 ticks) | Valeur |
|---|---|
| Norme du gradient reçu par `tete_motrice` | 0,1417 |
| Variation des logits après **1 pas** Adam | **0,0107** |
| Marge argmax / 2ᵉ à franchir | **0,392** |
| **Fraction de la marge par pas** | **2,74 %** |
| **Pas nécessaires pour changer une décision** | **~37** |

> **L'agent fait 1 pas par jour là où il en faudrait ~37 pour changer un choix.**

## Les trois bras — et pourquoi trois

⚠️ **Règle §6.2** : plusieurs époques de policy gradient Monte-Carlo **sans ratio
d'importance divergent** — c'est la raison d'être du clipping de PPO. Tester « plus de pas »
sans tester « avec quel garde-fou » donnerait une ablation **confondue**.

| Bras | Contenu | Runs |
|---|---|---|
| **TEMOIN** | code actuel, 1 pas de politique par nuit | **0** — réutilise `04092026_cursus_complet` (bras LIBRE) |
| **K8_NU** | 8 époques sur la journée, **sans** ratio d'importance | 20 |
| **K8_CLIP** | 8 époques **avec** ratio d'importance clippé (ε = 0,2) | 20 |

40 runs neufs, 20 graines appariées (11 … 222) × 1500 jours, régime **voix libre**
(`--gain-c1-libre`) pour rester comparable au bras de référence. 6 en parallèle, ~10 h.

## ⚠️ Ce qui pourrait mal tourner, écrit d'avance

1. **K8_NU peut DIVERGER.** C'est le résultat attendu par la théorie. Si les deux bras K8
   échouent mais que NU échoue *plus fort*, c'est déjà une information.
2. **Sur-apprentissage d'une journée** de 400 ticks : 8 passes sur le même lot peut
   mémoriser le bruit. Non mesuré.
3. **Le coût de calcul monte** : 8 passes de rétropropagation par nuit. Vérifier que les
   runs finissent (garde `Jour 1500` au dépouillement).
4. **`K = 8` est une CONSTANTE POSÉE**, ce que le projet interdit à terme. Méthode v30.1 :
   **mesurer le fixe d'abord**, dériver ensuite. Si l'effet existe, la forme finale devra
   émerger (de la plasticité dopaminergique, comme `pourcentage_reve`).

## Les juges, posés d'avance

⚠️ **Bonferroni 3 métriques** ⇒ seuil `t` = **2,86**.

| Juge | Grandeur | Le levier EXISTE si | Il est NEUTRE si |
|---|---|---|---|
| **1. Maîtrise** | δ K8 − TEMOIN | δ > 0, `t` > 2,86 | δ ≈ 0 |
| **2. Niveau** | idem | δ > 0, `t` > 2,86 | ⚠️ **probablement SATURÉ** (40/40 au niveau 4) |
| **3. Platitude** | ratio inter/intra des logits | **baisse** vers celui de PPO (0,06) | reste ~3,9 |
| **4. Garde-fou** | nombre de `step()` de politique par nuit | — | doit valoir **8** dans les bras K8, **1** au témoin |

**Le juge 3 est le juge MÉCANISTE** : il dit si l'intervention a fait ce qu'elle prétend,
indépendamment du résultat comportemental. Un bras qui améliore la maîtrise **sans** réduire
la platitude aurait agi par un autre chemin.

## Interprétation prévue AVANT de voir les chiffres

| Résultat | Lecture |
|---|---|
| **K8_CLIP positif, K8_NU négatif** | l'anémie de l'optimiseur **est** le goulot, et le clipping est nécessaire — résultat le plus attendu |
| **Les deux positifs** | le nombre de pas suffit, le garde-fou est superflu à ce régime |
| **Les deux nuls** | ❌ la piste 🟢 la plus haute du plan **tombe** ; l'écart avec PPO est ailleurs |
| **Les deux négatifs** | l'apprentissage actuel est déjà à son optimum de pas ; sur-apprentissage confirmé |

⚠️ **Prédiction honnête** : je ne sais pas. Contrairement à `--detach-c2` (où j'avais prédit
« rien » et me suis trompé), la mesure des ~37 pas rend un effet **plausible** — mais elle ne
dit rien du **signe**, puisqu'un gradient plus appliqué peut aussi bien creuser une bonne
dépendance qu'amplifier du bruit.

## Le protocole

```bash
zsh brains/06092026_epoques_nuit/lancer.sh
python3 brains/06092026_epoques_nuit/depouiller.py
```

---

## Le pré-vol du 06/09 — il a attrapé un bug qui aurait vidé la campagne

⚠️ **Première version : 0 grandeur sur 6 divergeait entre K=1 et K=8.** Les 7 pas
supplémentaires n'avaient **aucun effet**. Lancée telle quelle, la campagne aurait produit
trois bras identiques en 10 h de calcul — **le bug v41.4 à l'identique**.

**Cause** : `python -m naulthene.cerveau.noyau` crée **DEUX copies** du module —
`__main__` et `naulthene.cerveau.noyau`. `traiter_tick` s'exécute dans la première,
`apprendre_journee` (méthode de l'agent importé) dans la seconde. Le drapeau ne surchargeait
que `_module_reel` : la **collecte** des états restait donc à `EPOQUES_NUIT = 1`, le buffer
restait vide, et les époques ne s'exécutaient jamais.

**Correctif** : surcharger `globals()` **et** `_module_reel`, avec assertion sur les deux.
C'est le motif que le dépôt applique déjà pour `HERITAGE_SEVRAGE_ACTIF` (v41.4).

### Le pré-vol, après correctif

| Vérification | Résultat |
|---|---|
| **K=1 bit-identique** à l'existant | ✅ 9 lignes clés identiques (test `git stash`) |
| **K=8 diverge de K=1** | ✅ **5 grandeurs sur 6** — H(C1) 0,709 → **0,496** dès 3 jours |
| **Les deux bras K8 diffèrent** | ✅ JEPA 0,0419 / 0,0408 · C1 1,689 / 1,840 |
| **Le drapeau s'annonce** | ✅ `[VARIANTE] 8 epoques ... ratio clippe : OUI/NON` |

> **Leçon** : un drapeau accepté par argparse, affiché à l'écran, avec une assertion qui
> passe, peut malgré tout ne rien faire. Seule la comparaison de deux runs sur des
> grandeurs **informatives** le prouve. ⚠️ Et « informatives » compte : mon premier test du
> 05/09 comparait `Réc. moyenne`, nulle des deux côtés à 3 jours — **un test qui ne peut pas
> échouer ne vérifie rien.**
