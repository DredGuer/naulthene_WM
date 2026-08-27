# 27/08/2026 — L'arrosage du crédit, confirmé. Et la vue est orpheline de l'incitation.

> Onzième réfutation, et un fait structurel neuf. Non normatif — carnet d'enquête.
> Suite de `CONDITIONNEMENT_27082026_le_signal_arrive_et_ne_sert_a_rien.md`.

## Fait structurel — QUI sculpte la perception ?

Trois pertes injectées séparément, normes de gradient lues par couche :

| Couche | depuis JEPA | depuis ACTEUR | depuis CRITIQUE |
|---|---|---|---|
| `porte_visuelle` | **0,033868** | **0,000000** | **0,000000** |
| `hippocampe` | 0,042690 | 0,000000 | 0,000000 |
| `analyseur` | 0,105406 | 0,000000 | 0,000000 |
| `fusion_memoire` | 0,000000 | 0,000000 | 0,000000 |
| `integrateur_bio` | 0,000000 | **3,370580** | **4,332367** |
| `tete_motrice` | 0,000000 | **2,858138** | 0,000000 |
| `cortex_prefrontal` | 0,000000 | 0,000000 | **1,454385** |
| `generateur_attente` | 0,399022 | 0,000000 | 0,000000 |

**La vue ne reçoit du gradient QUE du JEPA.** L'acteur et le critique lui envoient
exactement zéro — le `.detach()` de la l. 1149 coupe le tronc perceptif des deux têtes.

Conséquence pour toute la stratégie : **aucune incitation, si bien contrastée soit-elle,
ne peut sculpter la représentation perceptive.** Améliorer l'avantage ne changera rien au
d' de `bus_latent` (0,607) : ce chemin de gradient n'existe pas. L'acteur ne peut agir
que sur **deux couches** — `integrateur_bio` et `tete_motrice` — et travaille sur une
représentation qu'il ne lui est pas permis de modifier.

Cela invalide l'idée que « la représentation est sculptée par l'incitation ». Ici, non.

## L'arrosage — instrument `sonde_credit.py`

Ventilation de la perte de l'acteur en trois classes de ticks, sur
`MiniGrid-DoorKey-6x6-v0`, 6 jours × 400 ticks. `.grad` lu **avant tout clipping**.

### A_g11

| classe | ticks | part | A moyen | \|A\| moyen | σ(A) | Σ‖∇‖ |
|---|---|---|---|---|---|---|
| stérile | 1554 | 64,8 % | +0,0633 | 0,0661 | 0,0236 | 0,1730 |
| neutre | 761 | 31,7 % | +0,0601 | 0,0638 | 0,0267 | 0,3415 |
| **utile** | **85** | **3,5 %** | +0,0502 | **0,0550** | 0,0293 | 0,2508 |

### Réplication — 4 cerveaux

| Cerveau | \|A\| utile | \|A\| neutre | rapport | t (Welch) |
|---|---|---|---|---|
| A_g11 | 0,0550 | 0,0638 | **0,862×** | −4,12 |
| A_g22 | 0,8481 | 0,7626 | **1,112×** | +3,00 |
| A_g44 | 0,3954 | 0,3651 | **1,083×** | +3,91 |
| A_g111 | 0,3139 | 0,3089 | **1,016×** | +0,89 |

**Le signe n'est pas stable ; l'amplitude l'est parfaitement.** Le rapport reste entre
**0,86× et 1,11×** sur les 4 cerveaux. Saisir une clé rapporte, à ±13 % près, ce que
rapporte un quart de tour sur place.

Trois `t` sur quatre sont significatifs — et ne veulent rien dire ici. Sur n≈800, un `t`
significatif accompagne un rapport de **1,016×**. **La significativité mesure la
fiabilité de l'écart, jamais sa taille.** C'est le rapport qui dit s'il existe un
contraste exploitable, et il n'y en a pas.

### La dilution, chiffrée

**85 ticks utiles pour 761 neutres** (3,5 % contre 31,7 %). Même à crédit unitaire égal,
le geste utile pèse **1/10ᵉ** du gradient de l'acteur. À crédit unitaire égal *et*
amplitude égale, il ne peut structurellement pas émerger.

## Une erreur de lecture commise et corrigée

Le premier verdict automatique de la sonde affichait, pour A_g11, *« le geste utile SE
DISTINGUE »* sur un `t = −4,12`. C'est faux : le `t` était **significatif dans le mauvais
sens** — le geste utile recevait 13,8 % de **moins**. Le seuil ne testait que `abs(t)`.
Corrigé : le verdict lit désormais le **rapport** (l'amplitude) et le **signe**
séparément, et déclare l'arrosage dès que l'écart est sous 25 %, quel que soit le `t`.

## Ce que cela ferme et ce que cela ouvre

**Fermé** : « le geste stérile apprend autant que le geste utile ». Faux depuis la v41.31 —
un `ramasser` dans le vide ne franchit pas `transition_tick`, son gradient d'acteur est nul.

**Confirmé** : l'effet d'arrosage, mais **entre transitions**. Parmi les ~35 % de ticks
crédités, rien ne distingue une saisie d'une rotation. Le masque v41.31 sépare bien
*bouger* de *ne rien faire* ; il ne sépare pas *réussir* de *bouger*.

**Ouvert, et c'est le point neuf** : même un crédit parfaitement contrasté n'atteindrait
que `integrateur_bio` et `tete_motrice`. La perception, elle, resterait sculptée par le
seul JEPA — qui apprend à prédire, jamais à valoriser. Deux chantiers distincts en
découlent, et il faut les mesurer séparément :

1. **Contraste du crédit** — un tick de transition utile devrait recevoir davantage.
   Attention : ce serait une récompense en dur si le supplément est posé ; il doit dériver
   de quelque chose de vécu.
2. **Le `.detach()` de la l. 1149** — non documenté, jamais mesuré, il prive la perception
   de tout signal de valeur. Le retirer est un A/B à part entière, jamais un ajustement.

## Reproduction

```bash
PYTHONPATH=src python -m naulthene.instruments.sonde_credit \
    brains/26082026_v4132_AB3_cursus/A_g11.brain --env MiniGrid-DoorKey-6x6-v0 --jours 6
```

---

# Addendum du même jour — le critique n'est pas aveugle. C'est le PORTAGE qui n'existe pas.

Hypothèse testée (proposition utilisateur) : *le critique évalue la pomme et le mur à la
même valeur parce que le `.detach()` l'empêche de sculpter la vue ; d'où V plat, d'où A
plat*. Chaîne causale cohérente — mais son premier maillon est faux.

## [A] Le critique voit TRÈS BIEN l'objet en face

`V(état)` mesuré sur 6000 ticks, `DoorKey-6x6` :

| Cerveau | V(objet en face) | V(mur en face) | écart | t | **d de Cohen** |
|---|---|---|---|---|---|
| A_g11 | −0,048957 | −0,083382 | +0,034 | +29,68 | **+1,154** |
| A_g22 | +0,803938 | +0,698647 | +0,105 | +17,38 | **+0,651** |
| A_g44 | +0,421896 | +0,334844 | +0,087 | +33,70 | **+1,214** |

**d de 0,65 à 1,21 — une séparation FORTE**, très supérieure au d' de 0,42–0,61 de la tête
motrice. Le critique discrimine *mieux* que l'acteur. L'hypothèse « le critique est
condamné à évaluer le monde à travers les lunettes du JEPA et n'y arrive pas » est
**réfutée** : il y arrive.

## [B] Mais il ne voit pas qu'il PORTE quelque chose

| Cerveau | V(porte un objet) | V(mains vides) | écart | **d de Cohen** |
|---|---|---|---|---|
| A_g11 | −0,062262 | −0,066534 | +0,004 | **+0,119** |
| A_g22 | +0,734264 | +0,754369 | −0,020 | **−0,117** |
| A_g44 | +0,380426 | +0,372582 | +0,008 | **+0,090** |

**d ≈ 0,1, et le signe s'inverse.** Or c'est exactement la variable dont dépend le TD-error
d'une saisie : si `V(porte la clé) ≈ V(mains vides)`, `A_saisie` ne peut pas produire de
pic. La planéité de l'avantage sur les gestes utiles est **entièrement expliquée par là**.

## La cause : le portage n'est présent dans AUCUNE entrée dédiée

Vecteur bio, 41 dims, 4000 ticks :

```
Écart max entre les deux moyennes : 0.00001013
Nb de dims avec un écart > 1e-4   : 0 / 41
```

**Zéro dimension sur 41 ne distingue « je porte » de « mains vides ».** Le vecteur bio
encode 3 jauges, la quête, le rappel spatial, 8 dims vocales, le toucher, la chimie,
l'Exo-Sens, la clinotaxie, le rappel marquant, la présence auditive — **pas l'inventaire**.

L'information existe pourtant dans la vue (d de Cohen global **6,73** : l'objet a disparu
de la grille), et elle traverse le tronc. Mais elle y arrive comme un **indice indirect**,
confondu avec « un objet a été déplacé quelque part ». Rien n'oblige le réseau à le lire
comme « je possède ». Le critique reçoit un signal massif et l'aplatit à d = 0,12.

## Ce que cela change pour le plan

Le `.detach()` reste un chantier légitime — mais **ce n'est pas la cause du crédit plat**,
et le retirer ne créerait pas le contraste espéré : on donnerait à l'acteur et au critique
le pouvoir de sculpter une représentation où la variable pertinente n'est **de toute façon
pas nommée**.

Deux chantiers, dans cet ordre :

1. **Le bit de portage.** Une dimension en queue du vecteur bio (contrat append-only,
   invariant v29.0) + greffe `persistance` par recopie. C'est exactement le chantier déjà
   nommé en v39.0 pour le *bit de présence auditive*, et jamais fait pour le portage.
   ⚠️ Ce n'est **pas** une récompense en dur : c'est une **perception**, au même titre que
   la faim. Le réseau reste libre d'en faire ce qu'il veut — rien ne déclare qu'être chargé
   est bon.
2. **Le `.detach()` l. 1149** — à mesurer séparément, après, et jamais dans le même bras
   (règle de mesure §6.2 : un seul bras par mécanique).

⚠️ Ordre non négociable : tester le `.detach()` d'abord mesurerait le pouvoir de sculpter
une représentation à qui il manque encore l'information.
