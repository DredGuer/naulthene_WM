# BRAS A — 200 JOURS : la netteté à l'asymptote

**Protocole écrit AVANT le lancement** (03/09/2026, 07h45). Suite directe de
[`VOIX_LIBRE_03092026`](../../docs/recherche/campagnes/VOIX_LIBRE_03092026_le_premier_levier_du_depot.md),
qui a mesuré **+12,43 pt** (`t = +5,21`, 18/20) — mais **sur une politique non asymptotique**.

## La question

À 100 jours, l'entropie jouée descendait **encore** dans **12 graines sur 15**
(−0,00745/jour), plateau extrapolé vers **j170-200**. Le +12,43 pt vaut donc pour « la
netteté à H ≈ 1,5 », **pas** pour la netteté que le mécanisme produit une fois stabilisé.

**La question posée : que vaut le levier quand la politique a fini de durcir ?**

Trois issues possibles, toutes informatives :

| Issue | Lecture |
|---|---|
| L'effet **grandit** | la netteté n'avait pas fini d'agir — le levier est plus fort qu'annoncé |
| L'effet **stagne** | +12,43 pt est le plafond du mécanisme ; il est déjà exprimé à j100 |
| L'effet **se réduit ou s'inverse** | ⚠️ « confiant dans l'erreur » (λ=0,9, 01/09) — une politique qui durcit sur une mauvaise direction empire |

## Le protocole

| Élément | Valeur |
|---|---|
| **Reprise** | les 40 cerveaux de `02092026_brasA_voix_libre/`, **copiés** dans ce dossier (règle : copier avant de reprendre — le `.brain` est écrasé à chaque nuit) |
| Jours | **+100 additionnels** (`--jours 100` sur un cerveau à j100 ⇒ **j200**) |
| Bras | LIBRE (`--gain-c1-libre`) vs TÉMOIN — **le trait est sérialisé**, mais le drapeau est repassé par sécurité et vérifié par `grep` |
| Graines | **les 20 mêmes**, appariées — la lignée est conservée, ce n'est pas une nouvelle loterie natale |
| Env | `MiniGrid-SimpleCrossingS9N1-v0` (banc forcé, identique) |
| Banc | `sonde_plancher_geometrique`, **300** épisodes, force = `acceptation()` |

**Ce qui ne change pas** : mêmes graines, même environnement, même instrument, même banc.
La **seule** variable est le nombre de jours. Les chiffres sont donc directement comparables
à ceux de j100.

## Les critères, posés d'avance

| Juge | Grandeur | Succès | Échec |
|---|---|---|---|
| **0. Asymptote atteinte ?** | pente de H sur les 20 derniers jours, bras LIBRE | \|pente\| < 0,002/j sur ≥ 15/20 graines | si elle descend encore, **la question reste ouverte** et 300 j serait nécessaire |
| **1. Netteté** | H jouée médiane au banc, LIBRE | **< 1,35** (était 1,513 à j100) | ≥ 1,50 : le durcissement s'est arrêté |
| **2. Succès** | δ apparié LIBRE − TÉMOIN | **> +12,43 pt** (l'effet grandit) ou stagne avec `t > 2,43` | δ **en baisse** = le levier s'épuise |
| **3. Directivité** | médiane LIBRE | **< 10×** (était 13,21×) | ≥ 12× : reste brownien |

⚠️ **Le juge 0 est nouveau et il conditionne l'interprétation** : si la politique n'a
toujours pas convergé à j200, aucun des trois autres ne dit « l'effet terminal », ils disent
« l'effet à j200 ». C'est la leçon du 03/09, écrite pour ne pas être refaite.

## Vérifications prévues au dépouillement

Les 8 de la campagne j100, à l'identique — **témoin aléatoire 5,67 %** (invariant),
saturation de budget (27,0×), graines à 0 victoire, **retrait des 4 extrêmes** (le test qui
a fait tomber la directivité), retrait des témoins au plancher, ratio C2/C1 (mode d'échec
v37.0, seuil 0,3), régime sérialisé 20/20, témoins non contaminés.

**Plus deux, propres à ce rejeu :**

- **Comparaison intra-lignée j100 → j200**, graine par graine : un cerveau qui *régresse*
  entre j100 et j200 est le signal « confiant dans l'erreur ». À compter explicitement.
- **Amplitude C1** : elle est passée de 1,215 (témoin) à 4,526 (libre) à j100. Si elle
  continue de croître sans borne, c'est le mode d'échec v37.0 qui revient par la fenêtre —
  à rapporter, **pas** à corriger en cours de campagne.

## Limites, écrites d'avance

1. **Banc forcé** : ne prouve toujours **rien** sur le cursus. Le passage en cursus complet
   (sans `--env-force`) reste l'étape suivante et obligatoire avant toute revendication.
2. **Lignée reprise, pas rejouée** : les 40 cerveaux héritent de leurs 100 premiers jours.
   C'est voulu (on mesure l'effet du temps supplémentaire, pas une nouvelle population) mais
   cela signifie que ce n'est **pas** une réplication indépendante du +12,43 pt.
3. n = 20, δ_A/A = 0 sur ce banc ; effet minimal détectable ≈ **6,3 pt** (cf.
   `DIMENSIONNEMENT.md`).

## Coût

40 runs × 100 jours ≈ **4 h 30** · 40 bancs × 300 épisodes ≈ **9 h 24**. Total **~14 h**.

## Commandes

```bash
zsh brains/03092026_brasA_200j/lancer.sh   # puis banc.sh
```

⚠️ **Vérifier `ps aux | grep lancer.sh` avant tout lancement** — deux lanceurs simultanés
ont corrompu un `.brain` le 02/09.
