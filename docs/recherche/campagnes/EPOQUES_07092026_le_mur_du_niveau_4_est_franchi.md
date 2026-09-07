# LES ÉPOQUES DE LA NUIT — le mur du niveau 4 est franchi

**Date** : 2026-09-07 · **Statut** : ✅ **LE PLUS FORT RÉSULTAT DU DÉPÔT** ·
**n = 20 graines appariées × 3 bras × 1500 jours** · cursus complet, cerveaux neufs,
**0 échec sur 40 runs neufs**.

> **Protocole et 4 juges écrits AVANT le lancement** (`brains/06092026_epoques_nuit/LISEZ_MOI.md`),
> avec une **prédiction explicite** : *« je ne sais pas — la mesure des ~37 pas rend un effet
> plausible, mais elle ne dit rien du SIGNE »*, et une attente théorique : **`K8_NU` devait
> diverger** (policy gradient MC sans ratio d'importance) et **`K8_CLIP` gagner**.
>
> 🔴 **L'attente théorique est INVERSÉE par la mesure.**

---

## 1. Le résultat en une ligne

**Donner 8 pas de gradient par nuit au lieu d'un fait passer la maîtrise de 8,75 % à
19,00 %** (δ **+10,25 pt**, `t` = **+4,81**, 15/20, survit aux extrêmes à `t` = +3,62) —
**et 5 cerveaux sur 20 franchissent le niveau 5**, un palier que **40 runs sur 40** n'avaient
jamais atteint.

## 2. Les quatre juges

| Juge | Critère (posé d'avance) | K8_NU | K8_CLIP |
|---|---|---|---|
| **4. Garde-fou** `gain_c1` = 1,00 partout | — | ✅ **1,0000** | ✅ **1,0000** |
| **1. Maîtrise** δ > 0, `t` > 2,86 | vs témoin | ✅ **+10,25 · `t` = +4,81** · 15/20 | ❌ −1,00 · `t` = −0,47 |
| ↳ sans les 4 extrêmes | | ✅ **+7,19 · `t` = +3,62** | ❌ −3,13 · `t` = −1,62 |
| **2. Niveau** δ > 0, `t` > 2,86 | vs témoin | 🟡 +0,25 · `t` = +2,52 (**NS**) | ❌ 0,00 |
| **3. Mécaniste** entropie de C1 baisse | vs témoin | 🟡 −0,090 · `t` = −2,47 (**NS**) | ✅ −0,172 · `t` = **−5,35** |

**Comparaison directe des deux bras K8** : δ maîtrise **+11,25 pt**, `t` = **+4,48**, 15/20,
survit aux extrêmes (`t` = +3,14). **Le clipping ne dégrade pas seulement l'effet : il
l'annule.**

## 3. Le franchissement du niveau 5

| Bras | Niveau ≥ 5 | Maîtrise moyenne | Victoires (médiane) | Maîtrise 0 % |
|---|---|---|---|---|
| **TÉMOIN** (1 pas/nuit) | **0 / 20** | 8,75 % | 860 | 1 |
| **K8_NU** | **5 / 20** | **19,00 %** | **882** | 1 |
| **K8_CLIP** | 4 / 20 | 7,75 % | 678 | **7** |

Les cerveaux promus **restent** au niveau 5 : **453 à 890 nuits**. Ce n'est pas un passage
fugace suivi d'une rechute.

⚠️ **CORRECTION IMPORTANTE, faite en cours d'analyse.** J'ai d'abord calculé un Fisher sur
les **deux bras K8 agrégés** (9/40 contre 0/20) : `p < 0,00001`. **Le protocole ne prévoit
pas cette agrégation.** Bras par bras :

| Test | `p` | Verdict |
|---|---|---|
| K8_NU 5/20 contre 0/20 | **0,0236** | SIG au seuil 0,05 |
| K8_CLIP 4/20 contre 0/20 | 0,0530 | NS |
| **Avec Bonferroni** (3 métriques ⇒ 0,0167) | — | 🔴 **AUCUN des deux ne passe** |

**Le franchissement du niveau 5 n'est PAS établi au seuil corrigé.** C'est la maîtrise qui
porte le résultat, pas le niveau.

## 4. Les vérifications

| Vérification | Résultat |
|---|---|
| **Tautologie** (conditionné sur « les deux bras ont gagné ») | δ **inchangé** : +10,25, `t` = +4,81, n=20 |
| **Retrait des 4 extrêmes** | +7,19, `t` = **+3,62**, SIG — le test qui a tué la directivité et la voix libre |
| **Artefact de palier** | à **niveau 4 identique** : témoin **10,0 %** contre K8_NU **25,0 %** |
| **Garde-fou du régime** | `gain_c1` = 1,0000 dans les **trois** bras |
| **Le drapeau mord** | `[VARIANTE] 8 epoques` sur **40/40** logs (20 clippés, 20 nus) |
| **Runs inachevés** | **0** — les 40 ont atteint le jour 1500 |
| **Échecs** | **0 / 40** |

## 5. 🔴 Le résultat le plus contre-intuitif : le clipping NUIT

L'attente théorique était sans ambiguïté : plusieurs époques de policy gradient Monte-Carlo
**sans** ratio d'importance divergent — c'est la raison d'être de PPO. **C'est l'inverse qui
est mesuré.**

| | K8_NU | K8_CLIP |
|---|---|---|
| Maîtrise | **19,00 %** | 7,75 % (sous le témoin) |
| Cerveaux à maîtrise 0 % | 1 | **7** |
| Victoires médianes | 882 | **678** (contre 860 au témoin) |
| Entropie de C1 | −0,090 (NS) | **−0,172** (`t` = −5,35, SIG) |

**Lecture proposée, non démontrée** : le clipping borne le ratio à [0,8 ; 1,2], donc **empêche
la politique de s'éloigner** de celle qui a collecté la journée. Or c'est précisément ce
déplacement qui manque à Naulthène — il faut **~37 pas** pour franchir la marge de 0,392.
Le garde-fou de PPO protège d'une divergence qui, ici, **est le mécanisme recherché**.

Le juge 3 va dans ce sens : `K8_CLIP` **décide plus** (entropie −0,172, SIG) tout en
**réussissant moins**. Une politique qui se fige sans avoir bougé.

⚠️ **Ce n'est qu'une lecture.** Un bras à ε plus large (0,5 ? 1,0 ?) la testerait.

## 6. Ce que ça établit, ce que ça n'établit pas

**Établi** :
- Le nombre de pas de gradient **est** un levier réel, mesuré en cursus complet à n=20.
- Le **clipping annule l'effet** (comparaison directe : `t` = +4,48, 15/20).
- L'écart de maîtrise **survit** à la tautologie, aux extrêmes, et au contrôle de palier.

**NON établi** :
1. 🔴 **Le franchissement du niveau 5 ne passe pas Bonferroni** (`p` = 0,0236 contre 0,0167).
   Il est **suggestif**, pas démontré. Il faudrait n=40 pour trancher.
2. 🔴 **Le juge mécaniste ne passe pas pour `K8_NU`** (`t` = −2,47, NS). L'effet ne s'explique
   donc **pas** par la baisse de platitude que j'attendais — le mécanisme reste ouvert.
3. **`K = 8` est une constante posée.** Méthode v30.1 : mesurer le fixe d'abord, **dériver
   ensuite**. La forme finale devra émerger, jamais rester un 8 en dur.
4. **Le mur se déplace, il ne tombe pas** : 15/20 restent au niveau 4, et personne n'atteint
   le niveau 6. Le cursus compte **15 paliers**.

## 7. Le pré-vol qui a sauvé la campagne

⚠️ **Première version du code : 0 grandeur sur 6 divergeait entre K=1 et K=8.** Les 40 runs
auraient produit trois bras identiques.

**Cause** : `python -m` crée **deux copies du module** (`__main__` et
`naulthene.cerveau.noyau`). `traiter_tick` s'exécute dans la première, `apprendre_journee`
dans la seconde. Le drapeau ne surchargeait que `_module_reel` : la **collecte** des états
restait à `EPOQUES_NUIT = 1`, le buffer restait vide, les époques ne tournaient jamais —
**le bug v41.4 à l'identique**, malgré une assertion qui passait et un message affiché.

> **Un drapeau accepté, affiché, et dont l'assertion passe peut malgré tout ne rien faire.
> Seule la comparaison de deux runs sur des grandeurs INFORMATIVES le prouve.**

## 8. Protocole

```bash
zsh brains/06092026_epoques_nuit/lancer.sh      # 40 runs, 6 en parallele, ~2 h
python3 brains/06092026_epoques_nuit/depouiller.py
```

Bras TÉMOIN : **0 run neuf**, réutilise `04092026_cursus_complet` (mêmes graines, même
régime de voix libre). Agrégat : `brains/06092026_epoques_nuit/agregat.json`.

---

*27ᵉ hypothèse testée sur le plafond. La première qui déplace le mur.*
