# Campagne v41.33-banc — LE BIT DE PORTAGE sur banc forcé `DoorKey-6x6`

**Lancée le 27/08/2026.** 20 graines appariées × 400 jours × 2 bras = **40 runs**.
Remplace `brains/27082026_v4133_portage_ABLATION_VIDE/` — voir son
`POURQUOI_CETTE_CAMPAGNE_EST_VIDE.md`.

## ✅ CONTRÔLE PRÉALABLE — la variable VARIE

Le contrôle qui manquait à la première campagne, désormais obligatoire avant tout A/B :

```
5 jours sur DoorKey-6x6 :
  🔑 Portage 51.2% · 12.2% · 0.0% · 26.5% · 22.8%     → moyenne 22.5 %
```

Contre `0.0 %` sur les 400 jours du cursus complet, où l'agent bloque au niveau 4
(`SimpleCrossing`) et où le premier objet manipulable est au niveau 6.

## Protocole

| | |
|---|---|
| **Bras A** | nominal — le bit porte `carrying` |
| **Bras B** | `--sans-portage` — la 42ᵉ dim existe, l'information est à 0.0 |
| Env | `--env-force MiniGrid-DoorKey-6x6-v0` (identique aux deux bras) |
| Graines | 11 → 222 (20, appariées) |
| Jours | 400 |

⚠️ **Le témoin garde la DIMENSION et ne coupe que l'INFORMATION** (règle §6.3) : les deux
bras ont exactement la même architecture.

## ⚠️ Ce qu'un banc forcé PEUT et NE PEUT PAS prouver (règle §4)

**Peut** : que la proprioception permet au critique de distinguer « clé en main » de
« mains vides », donc que `A_saisie` se détache de `A_neutre`. C'est le mécanisme visé.

**Ne peut pas** : que le cursus se débloque. Le niveau reste à 1/15 **par construction**
(la promotion est court-circuitée). La nociception v41.25 était bonne sur `LavaGap` et
coûtait −25 % de récolte partout ailleurs — toute mécanique validée au banc **doit**
repasser en cursus complet avant d'être revendiquée.

## Ordre d'analyse — À LA FIN DES 40 RUNS, jamais avant

1. **`sonde_credit.py`** — `|A| utile` contre `|A| neutre`. Référence à battre : **0,86× à
   1,11 ×** (4 cerveaux, 27/08). C'est le juge.
2. **d de Cohen `V(porte)` vs `V(mains vides)`** — référence : **+0,119 / −0,117 / +0,090**.
3. **Comportement** — taux de saisie, récolte. Indice, jamais verdict à 400 jours.

⚠️ **AUCUN `t` AVANT LA FIN.** Leçons du 20/08 (`t=+3,68` → `+1,93`) et du 22/08
(maîtrise +4,95 à n=5 → +1,09 à n=20). Bonferroni si plusieurs métriques.

## Reproduction

```bash
brains/27082026_v4133_portage_banc/lancer.sh
```
