# Le frein de la neurogenèse — comment j'ai cassé l'auto-stabilisation, et ce qui la restaure

**17/08/2026** — carnet de recherche, non normatif.
Question de l'utilisateur : *« C'est quoi la différence entre avant V30 où le système se
stabilisait tout seul et maintenant ? »* puis *« Je ne vois que des conditions… alors qu'il
faudrait des formules. »*

Les deux remarques pointent le même endroit, et elles ont toutes les deux raison.

---

## 1. Le constat qui a lancé l'enquête

Lecture directe des `.brain` V30 archivés :

| cerveau V30 | dim_bus final | ticks |
|---|---|---|
| `naulthene_cursus.brain` | **48** | 120 000 |
| `naulthene_cursus_ancien_1024j` | **48** | 409 307 |
| `naulthene_parole.brain` | **48** | 480 000 |
| `020820261313_V30_700_RMD` | **48** | 280 000 |

**La V30 se stabilisait à 48, avec un plafond à 96.** Elle s'arrêtait à mi-chemin du mur.

Après la v41.21 : **20/20 collent au plafond**, quel qu'il soit (96, puis 160 après
v41.22). Le système ne s'auto-limitait plus.

---

## 2. La cause — une régression que j'ai introduite

La condition historique était :

```python
if variance_erreur < 0.005 and moyenne_glissante > seuil_base * 1.5:
    seuil_base = 0.7 * seuil_base + 0.3 * moyenne_glissante
```

En v41.21 j'ai jugé cette ligne « inopérante » parce que `variance < 0.005` est **toujours
vraie** (variance réelle ~4e-6, mille fois sous le seuil) — ce qui est exact. Mais j'en ai
conclu que la ligne entière ne discriminait rien, et je l'ai remplacée par la seule
condition cosmologique `cohésion > friction`.

**Le second membre, lui, était bien vivant.** `moyenne > seuil_base × 1.5` faisait **monter
`seuil_base` vers l'erreur réelle**. Ce rattrapage est exactement ce qui éteignait la
neurogenèse : quand la référence rejoint l'erreur, le signal de détresse disparaît.

> J'ai jugé la ligne sur son membre mort et jeté le membre vivant avec.

C'est le §3 de la règle de mesure appliqué à l'envers : j'ai trouvé une explication
élégante (« encore une échelle absolue, comme `SEUIL_CRISTAL` ») et je ne l'ai pas
confrontée au **comportement** du système avant d'agir.

---

## 3. Le second défaut, plus profond : il n'y avait que des `if`

Remarque de l'utilisateur : *« je ne vois que des conditions ».*

Comptés dans le bloc du thermostat (40 lignes) : **9 branches** et **5 nombres nus**
(`1.5`, `0.8`, `0.1`, `min(5`, `+16`). J'avais remplacé `variance < 0.005` par
`cohésion > friction` — **un seuil par un autre seuil**, mieux habillé.

Et la transposition cosmologique elle-même était incomplète. Dans le modèle
[`naulthene_cosmologie/`](../naulthene_cosmologie/), `C(c) > ln(N)` n'est pas le mécanisme :
c'est la **conséquence** d'un potentiel dont le système descend le gradient. J'avais pris
le résultat en jetant la machine.

---

## 4. Le correctif — deux pressions continues, aucun seuil

Arbitrage utilisateur : l'**Option B**, les deux forces en OU.

```python
exigence = 1.0 + 1.0 / JOURS_ENTRE_MUTATIONS          # 1,20 — remplace le 1.5 posé

pression_structure   = (coh/fr) / (1 + coh/fr)        # limite physique (Landau)
_ecart               = moyenne / (seuil_base × exigence)
pression_habituation = _ecart / (1 + _ecart)          # limite d'habituation

pas = max(pression_structure, pression_habituation)   # le « OU » devient un max continu
seuil_base = (1 - pas) · seuil_base + pas · moyenne
```

Trois propriétés :

- **`x/(1+x)` est une saturation** : pas de pente réglable, pas de point de bascule. Une
  force faible recalibre un peu, une force forte recalibre beaucoup.
- **Le « OU » logique devient un `max` continu** — c'est ce qui fait disparaître le `if`.
- **L'exigence dérive de la fenêtre** : `1 + 1/fenêtre`. Un agent qui observe sur 5 nuits
  tolère 20 % d'écart ; sur 20 nuits il n'en tolérerait que 5 %.

### Deux erreurs corrigées en chemin

**(a)** J'avais écrit `pas = pression / fenêtre`. Faux : la fenêtre gouverne l'**exigence**,
jamais la **vitesse**. En divisant deux fois, j'écrasais le recalibrage et reproduisais le
défaut de la v41.21.

**(b)** Ma première simulation concluait « l'Option B ne stabilise pas ». Elle était fausse
— j'y injectais un bruit artificiel qui relançait les mutations en permanence. Nettoyée,
elle donne :

| variante | dim_bus final | mutations |
|---|---|---|
| v41.21 (ma régression) | 80 | 4 |
| V30 historique | 128 | 7 |
| **Option B** | **48** | **2** |

48 — exactement la valeur des `.brain` V30 réels.

---

## 5. La mesure en réel — le frein fonctionne, mais le plafond masque tout

3 graines × 200 jours, plafond machine à 160 :

| graine | dim_bus final | dernière mutation | jours sans croissance |
|---|---|---|---|
| g33 | 160 | jour 94 | **106** |
| g7 | 160 | jour 86 | **114** |
| g11 | 160 | jour 80 | **120** |

⚠️ **Lu vite, c'est un échec** (160/160, comme avant). Lu correctement, c'est l'inverse :
l'état final du `.brain` g7 donne `seuil_base = 0.00381` contre une erreur JEPA de
**0.0032**. La référence a **rattrapé l'erreur**, et l'agent n'a plus muté depuis 114 jours.

**Le frein a bien mordu.** Le 160 n'est pas un emballement : c'est ce que l'agent a accumulé
pendant ses 86 premiers jours, avant que le rattrapage n'opère.

### Le test qui tranche

Tant que `dim_bus` finit **exactement au plafond**, on mesure le plafond, pas le frein.
D'où `NAULTHENE_PLAFOND_BUS=512` (banc de mesure, jamais lu par la décision) : plafond hors
de portée, et on regarde **où la croissance se pose**.

Premiers points à 60 jours : `dim_bus` 112–128 sur trois graines, avec un plafond à 512 —
les cerveaux ne foncent pas au mur. Résultat complet en cours.

---

## 6. Ce qui reste ouvert

1. **Où se pose la croissance sans plafond ?** C'est la campagne de nuit (10 graines ×
   1500 jours à plafond 512). Si elle se stabilise autour de 112–160, le frein suffit et
   `DIM_BUS_MAX` redevient décoratif.
2. **Un cerveau plus gros aide-t-il ?** Rien ne le montre à ce jour : v41.22 (96 vs 160)
   donne **8/10 au niveau 4 des deux côtés**, pour −34 % d'énergie et +62 % d'effort côté
   160. La croissance coûte, elle ne rapporte pas encore.
3. **Les 5 nombres nus restants du déclencheur** (`1.5`, `0.8`, `0.1`, `min(5`, `+16`) —
   ils gouvernent la période réfractaire et la fonte de `seuil_actuel`. Ils sont hors du
   correctif de cette page et restent à traiter.
