# 27/08/2026 — Le « Clic! » immédiat : mesuré avant d'être codé, et réfuté.

> Treizième réfutation — mais celle-ci n'a coûté **aucune nuit de calcul**.
> Non normatif — carnet d'enquête. Suite de `CREDIT_27082026_*.md`.

## La proposition testée

Après la campagne v41.33 (l'agnosie levée, le crédit toujours plat), la piste proposée
était l'**attribution de crédit temporel** : payer l'acteur au tick exact du geste, en
comparant `V(s_{t+1})` à `V(s_t)`, au lieu d'attendre le retour de fin d'épisode.
Analogie du clicker de dressage : le chien doit entendre *Clic!* à 10 h, pas recevoir sa
gamelle à 20 h.

**Le diagnostic sous-jacent était juste. La solution ne fonctionne pas.**

## Ce que le code fait vraiment (deux précisions)

1. **Ce n'est pas « la gamelle du soir ».** `R = r + γ·R_suivant` avec `γ = 0.99` et remise
   à zéro aux frontières d'épisode (`dones`) : le retour est déjà escompté et borné à
   l'épisode. Un geste du matin ne reçoit pas le crédit du soir.
2. **Mais `V(s')` n'entre nulle part.** La formule est `A = returns_normalisés − V(s)` —
   Monte-Carlo pur, où `V` ne sert que de baseline. Le critique sait désormais que
   `V(porte) > V(vide)` (d = +1,43), et **cette différence n'est jamais lue**. C'est
   exactement le défaut visé.

## Le fait qui semblait tout valider

Contrefactuel pur — même état, même mémoire, on ne bascule *que* le bit :

| Cerveau | V(bit=1) − V(bit=0) | mouvement typique de V par tick | part |
|---|---|---|---|
| A_g11 | **+0,324667** ±0,017 | 0,089904 | **361 %** |
| A_g44 | **+0,437267** ±0,017 | 0,108533 | **403 %** |

**Le Clic! existe dans la tête du critique** : porter vaut 3,6× à 4,0× le mouvement
ordinaire de la valeur. Le signal est là, massif, et parfaitement stable (σ ≈ 0,017).

## Le fait qui l'invalide

Le saut **réellement observé** au tick d'une saisie, en jeu :

| Cerveau | `V(s')−V(s)` sur une saisie | sur un tick neutre |
|---|---|---|
| A_g11 | +0,005592 | **+0,014981** (2,7× plus) |
| A_g22 | +0,006590 | +0,001560 |
| A_g44 | +0,018773 | +0,003792 |

**Le saut causal de +0,325 ne se retrouve pas dans le saut observé.** Entre `s` et `s'`,
la vue a changé *aussi* — et son bruit (0,090/tick, orienté aléatoirement) noie un signal
pourtant 3,6× plus grand en amplitude. Sur g11 le tick banal saute **plus** que la saisie.

## Les trois formes d'avantage, mesurées sur 8 cerveaux

Mêmes trajectoires, mêmes ticks, trois formules :

| Graine | MC (code actuel) | TD(0) — le Clic! | GAE(λ=0,95) | n utile |
|---|---|---|---|---|
| g11 | 1,194× | 0,558× | 1,019× | 55 |
| g22 | 1,819× | 0,882× | 1,220× | 52 |
| g33 | 1,307× | 0,578× | 1,003× | 50 |
| g44 | 1,018× | 1,620× | 1,162× | 92 |
| g55 | 1,137× | 0,351× | 1,039× | 76 |
| g66 | 1,364× | 0,921× | 1,129× | 37 |
| g77 | 1,114× | 1,135× | 1,109× | 66 |
| g88 | 1,243× | 2,953× | 1,609× | 34 |
| **moyenne** | **1,275×** | **1,125×** | **1,161×** | |

**Aucune ne contraste le geste utile**, et le code actuel est le *moins mauvais* des trois.
TD(0) est en outre très instable (0,351× à 2,953×, un facteur 8,4 entre graines) — ce qui
est attendu d'une estimation à un seul pas sur un signal bruité.

## Pourquoi le Clic! ne peut pas marcher ici

Le clicker du dresseur suppose que **l'observateur voit l'exploit et rien d'autre**. Ici,
`V(s')` mélange inséparablement trois changements simultanés : le portage (+0,325), la vue
(±0,090 de bruit non orienté), et la mémoire récurrente. Le TD(0) ne sait pas les
distinguer — il lit leur somme.

Autrement dit : **le problème n'est pas *quand* on paie, mais que le signal de paiement est
mélangé à trois autres au moment où on le lit.**

## Ce que cela ferme et ce que cela ouvre

**Fermé** : passer l'acteur en TD(0) ou en GAE. Mesuré sur 8 cerveaux × 2000 ticks, sans
lancer une seule campagne.

**Ouvert** : le `.detach()` de la l. 1149 reste le seul chantier structurel identifié et
jamais testé — l'acteur et le critique n'envoient **aucun** gradient à la perception
(mesuré : 0,000000), donc seul le JEPA sculpte ce que l'agent apprend à voir. Un signal de
valeur qui atteindrait `porte_visuelle` pourrait *réduire* le bruit perceptif qui noie
aujourd'hui le Clic! — mais c'est une hypothèse, et elle exige un A/B à elle seule.

## Instruments (lecture seule, versionnés)

- `src/naulthene/instruments/sonde_avantage.py` — compare MC / TD(0) / GAE sur les mêmes
  trajectoires
- `src/naulthene/instruments/sonde_effet_causal_bit.py` — effet causal pur d'une dimension
  du vecteur bio sur `V`, par contrefactuel à état identique

```bash
PYTHONPATH=src python -m naulthene.instruments.sonde_avantage
PYTHONPATH=src python -m naulthene.instruments.sonde_effet_causal_bit <brain>
```
