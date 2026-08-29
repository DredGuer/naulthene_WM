# Le brain-sparing — le premier effet démontré du projet

**17/08/2026** — carnet de recherche, non normatif.
Campagne A/B sur la v41.16, issue de la synthèse biologique de l'utilisateur (lois A/B/C).

---

## 1. Le protocole

| | |
|---|---|
| Graines | **10 par bras**, mêmes mondes des deux côtés (v41.9) |
| Durée | 600 jours |
| Témoin | `--vigueur-sur-logits` → la vigueur écrase les logits (v41.15) |
| Variante | par défaut → brain-sparing + économie d'action |
| Ablation | vérifiée active par assertion runtime |

---

## 2. Les résultats

| graine | niv. témoin | niv. variante | ratio C2/C1 T | ratio V |
|---|---|---|---|---|
| g1 | 3 | **4** | 0,17 | 2,05 |
| g2 | 1 | **4** | 0,24 | 1,60 |
| g3 | 3 | 3 | 0,39 | 3,48 |
| g4 | 3 | **4** | 0,32 | 2,44 |
| g5 | 3 | 3 | 0,19 | 2,04 |
| g6 | 3 | **4** | 0,57 | 3,37 |
| g7 | 3 | **4** | 0,44 | 3,43 |
| g8 | 3 | **4** | 0,21 | 1,84 |
| g9 | 1 | **3** | 0,16 | 2,36 |
| g10 | 1 | **3** | 0,20 | 1,54 |

**Duels : la variante gagne 8, perd 0, fait 2 nuls.**

| Mesure | témoin | variante | écart |
|---|---|---|---|
| niveau max | 2,400 | **3,600** | **+1,200** |
| promotions | 1,400 | **2,600** | **+1,200** |
| énergie moyenne | 0,340 | **0,455** | +0,114 |
| vigueur moyenne | 0,277 | **0,363** | +0,086 |
| **ratio C2/C1** | 0,289 | **2,415** | **+2,126** |
| maîtrise finale | 18,5 % | 18,5 % | 0,000 |

### Le taux d'atteinte, avec intervalles de Wilson

| | témoin | variante | verdict |
|---|---|---|---|
| niveau ≥ 3 | 70 % [40–89] | **100 %** [72–100] | recouvrent |
| **niveau ≥ 4** | **0 %** [0–28] | **60 %** [31–83] | ✅ **DISJOINTS** |
| niveau ≥ 5 | 0 % [0–28] | 0 % [0–28] | recouvrent |

**Les intervalles sont disjoints au niveau 4.** C'est le premier effet du projet qui
survive au test qu'il s'est lui-même imposé.

Rappel du contexte : le niveau 4 n'avait **jamais** été franchi de façon reproductible.
La campagne du 16/08 mesurait **0 sur 20** graines à 2500 jours ; ici **6 sur 10** le
franchissent en 600 jours.

---

## 3. Ce que la mesure établit — et ce qu'elle n'établit pas

✅ **Établi** : le brain-sparing débloque le niveau 4 sur cet échantillon, avec des
intervalles disjoints. Le ratio C2/C1 passe de 0,29× à 2,42× — C2 devient enfin audible.

❌ **Non établi** :

- **n = 10, pas 20.** La règle du projet exige 20 graines. Les intervalles sont disjoints,
  ce qui est plus exigeant qu'un simple écart de moyennes, mais l'échantillon reste sous
  le seuil que le projet s'est fixé.
- **La maîtrise finale est identique** (18,5 % des deux côtés). L'agent atteint des
  paliers plus élevés sans mieux les maîtriser — il progresse plus vite, il ne comprend
  pas mieux.
- **Le niveau 5 reste à 0/10.** Un mur est franchi, le suivant tient.
- **La part causale de chaque correctif n'est pas séparée.** La variante porte le
  brain-sparing *et* l'économie d'action : on ne sait pas lequel produit l'effet.

⚠️ **Résultat favorable ⇒ vérification double** (règle de mesure §3). Deux contrôles
faits : l'ablation atteint bien le module (assertion runtime), et les deux bras tournent
sur les mêmes mondes (v41.9). Reste à confirmer sur 20 graines.

---

## 4. Pourquoi ça marche — le mécanisme

Le défaut mesuré : `vigueur` multipliait les **logits**. Or `softmax` est invariante par
translation mais **pas par échelle** — diviser l'écart entre 7 logits n'atténue pas une
préférence, elle l'**efface**.

```
vigueur 1.00 → entropie 0.955
vigueur 0.15 → entropie 0.999      (1/7 = 0.143 = hasard pur)
```

Et l'agent vivait à **énergie 0,041**, `400/400 ticks en basse énergie`, dès le jour 1 :
**toute sa vie, il décidait au hasard.**

Le correctif retire `vigueur` des logits (loi A : le cerveau survit) et l'ajoute au coût
d'action (loi B : le corps ralentit). La contrainte est **déplacée**, jamais supprimée —
ce que confirme la mesure : l'énergie moyenne *monte* (0,340 → 0,455), signe que l'agent
gère mieux son métabolisme, pas qu'on l'a exonéré.

---

## 5. Suite

1. **Rejouer à 20 graines** pour satisfaire la règle du projet.
2. **Séparer les deux correctifs** (brain-sparing seul / économie d'action seule) pour
   attribuer l'effet.
3. **Re-sonder C2** avec `sonde_utilite_c2.py` : à ratio 2,4×, C2 est-il enfin *causal*
   (taux de veto) ou seulement plus fort ?
