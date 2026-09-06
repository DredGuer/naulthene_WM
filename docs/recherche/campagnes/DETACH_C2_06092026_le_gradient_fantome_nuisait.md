# LE GRADIENT FANTÔME DE C2 — il nuisait, et le couper est le premier levier du dépôt

**Date** : 2026-09-06 · **Statut** : ✅ **PREMIER RÉSULTAT POSITIF EN CURSUS COMPLET** ·
**n = 20 graines appariées × 1500 jours** · cursus complet, cerveaux neufs, 0 échec sur 20.

> **Protocole et 4 juges écrits AVANT le lancement** (`brains/05092026_detach_c2/LISEZ_MOI.md`),
> avec une **prédiction explicite** : *« la probabilité que ce bras trouve un effet est faible.
> Il est lancé parce que c'est la réserve que j'ai écrite moi-même dans le carnet précédent,
> pas parce que j'attends un résultat. »*
>
> 🔴 **Cette prédiction est RÉFUTÉE.**

---

## 1. Le résultat en une ligne

**Couper le gradient de C2 vers la couche partagée fait passer la maîtrise de 8,75 % à
14,00 %** — δ **+5,25 pt**, `t` = **+4,97**, **16/20 favorables**, et le résultat **survit au
retrait des 4 extrêmes** (`t` = +4,57), le test qui avait tué la directivité (02/09) et la
voix libre (04/09).

## 2. Les quatre juges

| Juge | Critère (posé d'avance) | Mesuré | Verdict |
|---|---|---|---|
| **4. Garde-fou** | `gain_c1` = 1,00 dans les deux bras | **1,0000 / 1,0000** | ✅ **PASSE** |
| **1. Maîtrise** | δ > 0, `t` > 2,86 | δ **+5,250** · `t` = **+4,97** · 16/20 | ✅ **PASSE** |
| **2. Niveau** | δ > 0, `t` > 2,86 | δ = 0,000 · **20/20 au niveau 4 dans les deux bras** | ⚠️ **SATURÉ** (prévu) |
| **3. Amplitude C1** | δ > 0 significatif | δ +0,014 · `t` = +0,09 | ❌ **NUL** |

### Le détail, graine par graine

| | LIBRE | LIBRE_DETACH | δ |
|---|---|---|---|
| Maîtrise moyenne | **8,75 %** | **14,00 %** | **+5,25 pt** (+60 % relatif) |
| Favorables | — | — | **16 / 20** |
| Nuls | — | — | 3 |
| Défavorables | — | — | **1** (`g177`, −5 pt) |
| Victoires cumulées (médiane) | 860 | **926** | +66 |

## 3. Les vérifications — toutes passées, deux réserves consignées

| Vérification | Résultat |
|---|---|
| **Tautologie** (conditionné sur « les deux bras ont gagné ») | δ **inchangé** : +5,250, `t` = +4,97, n=20 — les 20 paires ont gagné |
| **Retrait des 4 extrêmes** | δ +3,438, `t` = **+4,57**, **SIG** — ✅ le test qui a tué deux résultats précédents |
| **Artefact de palier** | **40/40 au niveau 4** ⇒ maîtrise comparée à palier identique : **10,0 % contre 15,0 %** |
| **Garde-fou du régime** | `gain_c1` = 1,0000 dans les deux bras : la voix libre est bien active des deux côtés |
| **Runs inachevés** | **0** — les 20 ont atteint le jour 1500 (garde explicite dans le dépouilleur) |
| **Échecs** | **0 / 20** |

### ⚠️ Réserve 1 — les victoires cumulées ne survivent PAS aux extrêmes

La maîtrise est quantifiée par pas de **5 %** (fenêtre de 20 épisodes), donc son effet
minimal détectable **est** 5 pt. J'ai vérifié sur une grandeur **continue** :

| Victoires cumulées | δ | `t` |
|---|---|---|
| Toutes les paires | **+64,4** | **+3,42** ✅ |
| **Sans les 4 extrêmes** | +34,4 | **+2,35** ❌ **NS** |

**Le signal est plus faible sur la grandeur continue.** Il confirme le **sens** (16/20
favorables, +7,5 % de victoires) mais pas la force du juge 1.

### ⚠️ Réserve 2 — les deux juges ne concordent pas au niveau individuel

`r(δ maîtrise, δ victoires) = **+0,0599**`. Ce n'est **pas** une contradiction : les deux
juges mesurent des **fenêtres différentes** — la maîtrise est la médiane des **100 dernières
nuits** (l'état final), les victoires le **cumul sur 1500 jours** (l'intégrale de la vie). Un
cerveau peut gagner beaucoup tôt puis stagner. Mais cela signifie que **le gain de maîtrise
n'est pas réductible à « il gagne plus »** : c'est un gain de **compétence finale**.

## 4. Ce que ça établit

🔴 **La réserve du carnet du 05/09 est levée — et dans le sens inverse de celui attendu.**

L'[ablation propre de C2](ABLATION_C2_05092026_l_organe_muet.md) avait conclu *« C2 est
inerte »* en laissant explicitement ouverte une question :

> ⚠️ *« C2 tourne toujours : seule sa voix est retirée. Son gradient continue d'irriguer le
> tronc via `integrateur_bio`. Cette campagne ne dit rien de ce canal-là. »*

**Réponse : ce canal NUISAIT.** La voix de C2 est inerte, mais son **gradient** dégradait la
représentation viscérale. « C2 est inerte » devient donc :

> **La voix de C2 ne sert à rien, et son gradient nuit.**

### Le mécanisme, mesuré indépendamment le même jour

La [sonde de mixage des pertes](SONDES_06092026_le_levier_s_efface_le_corps_domine.md#d-§7--la-seconde-table-de-mixage--le-critique-mange-89--de-lentrée-de-la-décision)
avait mesuré, **avant** ce verdict et sans le connaître, que le critique consomme **89,24 %**
du gradient d'`integrateur_bio` contre **6,57 %** pour l'acteur — **40 cerveaux sur 40**.

`--detach-c2` coupe exactement cette voie (`noyau.py:1556`). **La sonde a prédit le levier,
la campagne l'a confirmé** — et le tableau d'interprétation écrit d'avance dans ce carnet
disait : *« δ significatif ⇒ la domination du critique était le goulot ».*

### ⚠️ Ce que ça n'établit PAS

1. **Le mur du niveau 4 TIENT** : 20/20 dans les deux bras, aucun franchissement. Le juge
   « niveau » est **saturé** — son δ = 0 est un **plafond**, pas une absence d'effet. Ce
   résultat améliore la compétence **dans** le palier, il ne débloque pas le cursus.
2. **La représentation ne change pas** (juge 3, `t` = +0,09) : la maîtrise monte **sans** que
   C1 parle plus fort. Le mécanisme exact reste à établir.
3. **Un seul run par graine et par bras.** Le δ_A/A de ce banc est 0,000000 (mesuré le 05/09),
   donc le plancher de détection est nul — mais la variance inter-graines reste élevée.

## 5. Ce que ça ouvre

🟢 **Le premier levier réel du dépôt en cursus complet.** Contrairement à la voix libre
(+19,50 pt au banc forcé, **non transporté** au cursus), celui-ci est mesuré **directement en
cursus complet**, cerveaux neufs, sans `--env-force`.

**Prochaine question, non tranchée** : `--detach-c2` coupe *tout* le gradient de C2 vers le
tronc. La sonde suggère une alternative plus fine — un **`lr` propre au critique, dérivé du
rapport 89/6,57 mesuré**, jamais posé. Un bras de plus le dira.

⚠️ **À ne pas faire** : conclure que « C2 doit être supprimé ». Le critique **continue
d'apprendre** dans ce bras (`cortex_prefrontal` reçoit son gradient normalement) ; seul son
effet **sur la couche partagée** est coupé. Retirer le critique dégraderait les avantages
fournis à l'acteur — c'est précisément pourquoi `--detach-c2` a été choisi plutôt que
`--sans-gradient-c2` (voir le LISEZ_MOI).

---

## 6. Protocole

```bash
zsh brains/05092026_detach_c2/lancer.sh      # 20 runs, 6 en parallele, ~5 h
python3 brains/05092026_detach_c2/depouiller.py
```

Bras LIBRE : **0 run neuf**, réutilise `04092026_cursus_complet` (20 graines appariées,
même code, même régime de voix libre). Agrégat : `brains/05092026_detach_c2/agregat.json`.

---

*26ᵉ hypothèse testée sur le plafond. La première qui passe tous ses juges — sans lever le
mur pour autant.*
