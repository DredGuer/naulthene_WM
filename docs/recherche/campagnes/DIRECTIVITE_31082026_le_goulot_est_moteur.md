# La directivité — le premier prédicteur significatif du dépôt

**31/08/2026** · `recherche/campagnes/` · **n = 20 cerveaux**, la barre du projet

Suite du [banc du plancher géométrique](PLANCHER_30082026_la_competence_existe_et_la_maitrise_ment.md)
(30/08, n=4), étendu aux 20 cerveaux exigés par la règle de mesure §2.

---

## Verdict en trois phrases

> ✅ **La compétence est réelle** : 12,33 % en moyenne contre **5,67 %** pour un marcheur
> aléatoire, 7 cerveaux sur 20 au-dessus de l'IC du hasard, une pointe à **37,33 %** — dans
> la fourchette de PPO (27–40 %).
> 🟡 **La maîtrise en run n'est pas fausse, elle est BRUITÉE** : `r = +0,3961` (`t = +1,83`,
> NS) — elle explique **16 %** de la variance de la compétence réelle.
> 🔴 **Le seul prédicteur significatif est la DIRECTIVITÉ** : `r = −0,8225` (`t = −5,96`,
> n=19), **68 %** de la variance. Le goulot est **moteur**, pas perceptif.

---

## 1. Le protocole

| Élément | Valeur |
|---|---|
| Environnement | `MiniGrid-SimpleCrossingS9N1` — le niveau du plafond |
| Cerveaux | **20**, cohorte AB3 du 26/08, 1440 jours chacun |
| Épisodes | 300 par politique, **graines de carte appariées** |
| Politiques | entraîné (`eval()`), neuf (Xavier), **aléatoire** |
| Témoin | **17/300 = 5,67 % sur les 20 runs**, vérifié par assertion |
| Plus court chemin | médiane **12 pas** (BFS réel) · budget **324 ticks** |

**Échantillonnage équilibré, et c'est essentiel** : la première vague (n=4) avait été
choisie dans le **haut** de la distribution (25–45 %, écart-type 7,4). Les 16 suivants ont
été tirés en partant des strates les plus rares pour couvrir **0–45 %** (écart-type 12,5).
Sans cette correction, l'axe des x n'aurait pas eu la variance nécessaire.

---

## 2. Les vingt mesures

| Cerveau | bus | Maîtrise run | Banc | Directivité |
|---|---:|---:|---:|---:|
| A_g144 | 91 | 0,0 % | 1,33 % | 22,25× |
| A_g44 | 157 | 0,0 % | 1,33 % | 22,75× |
| A_g11 | 145 | 5,0 % | 1,00 % | 20,50× |
| A_g111 | 78 | 5,0 % | 15,00 % | 14,83× |
| A_g188 | 149 | 5,0 % | 20,67 % | 13,92× |
| B_g44 | 147 | 10,0 % | 2,33 % | 22,83× |
| A_g77 | 145 | 10,0 % | 9,33 % | 18,54× |
| B_g122 | 145 | 20,0 % | **0,00 %** | n/a |
| A_g222 | 145 | 20,0 % | 7,33 % | 16,79× |
| A_g33 | 141 | 20,0 % | 11,00 % | 19,17× |
| A_g177 | 149 | 25,0 % | 3,33 % | 19,21× |
| B_g188 | 153 | 25,0 % | 13,00 % | 15,67× |
| A_g133 | 147 | 25,0 % | 29,00 % | 13,83× |
| A_g166 | 132 | 25,0 % | 31,00 % | 16,42× |
| A_g66 | 158 | 30,0 % | **37,33 %** | **14,21×** |
| B_g11 | 92 | 35,0 % | 3,00 % | 22,17× |
| A_g122 | 137 | 35,0 % | 27,33 % | 16,33× |
| B_g144 | 150 | 35,0 % | 28,67 % | 14,67× |
| B_g211 | 155 | 40,0 % | 15,33 % | 18,04× |
| A_g155 | 145 | 45,0 % | 7,67 % | 18,08× |

---

## 3. ✅ La compétence est réelle

| | Valeur |
|---|---:|
| Succès moyen | **12,33 %** |
| Témoin aléatoire | **5,67 %** |
| Cerveaux au-dessus de l'IC du hasard | **7 / 20** |
| Meilleur | **37,33 %** (A_g66) — fourchette PPO 27–40 % |

**L'hypothèse du plancher géométrique est réfutée.** Elle prédisait un hasard à 10–15 % et
un entraîné indistinguable ; le hasard est à 5,67 % et sept cerveaux le dépassent nettement.

---

## 4. 🟡 La maîtrise en run : bruitée, pas fausse

`r(maîtrise, banc) = +0,3961`, `t = +1,83`, **n=20** — non significatif (seuil 2,39).

> ⚠️ **RÉTRACTATION.** Le 30/08 j'ai rapporté `r = −0,89` sur **quatre** cerveaux et évoqué
> que la maîtrise pourrait mesurer *l'inverse* de la compétence. **C'était un biais de
> sélection que j'avais introduit** : ces quatre cerveaux avaient tous une maîtrise
> **élevée** (25–45 %). Sur une plage étroite et tronquée par le haut, le bruit domine la
> pente. Dès l'ajout du cinquième point, `r` passait de **−0,89 à +0,35**. Même mécanisme
> que `maîtrise ~ énergie` (+0,710 à n=10 → −0,059 à n=20, rétracté le 29/08).

**Le vrai défaut est la dispersion intra-strate :**

| Maîtrise | n | Étendue au banc |
|---:|---:|---:|
| 5,0 % | 3 | **19,67 pt** (1,00 → 20,67 %) |
| 20,0 % | 3 | 11,00 pt |
| 25,0 % | 4 | **27,67 pt** (3,33 → 31,00 %) |
| 35,0 % | 3 | **25,67 pt** (3,00 → 28,67 %) |

| | Valeur |
|---|---:|
| Variance **inter**-strates | 1425,0 |
| Variance **intra**-strate | 1235,1 |
| Ratio | **1,15** |

`historique_episodes_niveau` explique **16 %** de la variance (`r² = 0,157`). À maîtrise
identique, deux cerveaux vont de 3,00 % à 28,67 %.

> **Ce n'est pas un mirage comptable, c'est un instrument lâche.** Cela explique pourquoi
> les corrélations bâties dessus étaient instables : la cible était trop bruitée pour
> détecter un effet modeste. Les dix-huit réfutations ne sont pas invalidées — mais celles
> qui reposaient sur cette seule sortie avaient une **puissance plus faible qu'annoncé**.

---

## 5. 🔴 La directivité — 68 % de la variance

| Prédicteur | `r` | `t` | `r²` | Verdict (seuil 2,39) |
|---|---:|---:|---:|---|
| Maîtrise run | +0,3961 | +1,83 | 0,157 | non significatif |
| `dim_bus` | +0,1936 | +0,84 | 0,037 | non significatif |
| **Directivité** | **−0,8225** | **−5,96** | **0,677** | 🔴 **SIGNIFICATIF** |

### Trois vérifications, toutes passées

1. **Pas de saturation de budget.** Le plafond arithmétique est `324/12 = 27,0×` ; la pire
   directivité observée est **22,83×**, et **0 cerveau sur 13** dépasse 24×. Les cerveaux
   lents avaient encore de la marge — la corrélation n'est pas une contrainte de budget.
2. **Pas de tautologie.** Les deux grandeurs ne partagent aucun terme : la directivité se
   calcule sur les épisodes **gagnés**, le succès compte **combien** le sont. `B_g122` le
   démontre : **0,00 % de succès et aucune directivité définie**.
3. **Survit au retrait des extrêmes.** Sans les 2 meilleurs et 2 pires : `r = −0,7771`,
   `t = −3,27`, n=9 — **toujours au-dessus du seuil**.

---

## 6. Ce que cela change pour le projet

**La question n'est plus « pourquoi l'agent ne comprend pas ».** L'amont est disculpé :
représentation nette (`d' ≈ 3`, 4,5× celle de PPO qui réussit mieux), gradient qui arrive,
signal dense à 86 %. Dix-huit hypothèses l'ont établi.

**La question est : pourquoi la politique motrice DIFFUSE au lieu de VISER.**

Ce qui sépare un cerveau à 3 % d'un cerveau à 37 % est son coefficient de diffusion
spatiale — **22,8× contre 13,9×** le plus court chemin. Et même le meilleur consomme encore
**14× la distance minimale** : ~167 ticks pour un trajet de 12 pas.

L'agent ne compose pas de séquence orientée dans le temps. Il **resserre sa marche
aléatoire**, il ne la remplace pas par une trajectoire.

---

## 7. Limites

| Limite | Portée |
|---|---|
| **Vecteur bio figé** au régime neutre | en run il évolue (faim, énergie, odorat) ; le banc mesure la politique privée de son signal métabolique variable |
| **Aucun apprentissage** (`eval()`) | politique gelée, pas la dynamique |
| **Un seul environnement** | `SimpleCrossingS9N1` ; rien ne dit que le motif tient ailleurs |
| **Corrélationnel** | `directivité → succès` n'est pas établi causalement ; les deux pourraient dépendre d'un tiers facteur non mesuré |
| **n = 19** pour la directivité | `B_g122` n'a aucune victoire, donc aucune directivité définie |

⚠️ **Deux versions antérieures de ce banc ont été jetées** (vecteur bio nul là où cinq
dimensions ont un neutre à 0,5 ; fuite de mémoire de travail + contexte épisodique nul).
Tout chiffre produit avant ces correctifs est **caduc**.

⚠️ **Le témoin « cerveau neuf » reste inutilisable** — un réseau Xavier a un biais d'action
arbitraire selon sa graine (42 % avancer · 70 % tourner · 87 % done), d'où des scores de
4,33 % à 22,67 %. Seul le témoin **aléatoire** est stable.
