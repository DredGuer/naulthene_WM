# Revue complète du cerveau — audit du dogme « rien en dur »

**17/08/2026** — carnet de recherche, non normatif.
Demande de l'utilisateur : *« Fais une review complète de toute la partie cerveau. S'il y a
le moindre élément en dur dis-le moi, il faut qu'on le corrige, c'est contre le dogme. »*

**Périmètre audité : 12 330 lignes** (`noyau.py` 9 277, `bus_sensoriel.py` 919,
`persistance.py` 686, `colab.py` 1 438) + `exocortex/` (552).
**209 constantes de module** examinées.

---

## 0. Le critère appliqué

Le dogme n'interdit pas les nombres — il interdit qu'un nombre **décide à la place de
l'agent**. La grille de lecture, dérivée de CLAUDE.md :

| Nature | Verdict | Exemple |
|---|---|---|
| **BORNE** (clip, plancher, plafond) | ✅ conforme | `VIGUEUR_PLANCHER`, `DOPAMINE_MIN/MAX` |
| **DÉRIVÉE** (calculée d'une mesure) | ✅ conforme | `VIGUEUR_MIN_C1`, `lambda_diffusion_carte` |
| **AFFICHAGE** (emoji, libellé) | ✅ hors dogme | `if _f < 0.15: "🌱"` |
| **PROPRIÉTÉ DU MONDE** (décrit l'env.) | 🟡 toléré | `PROFILS_NUTRITIONNELS` |
| **SEUIL DE DÉCISION** (oriente le comportement) | ❌ **violation** | ce qui suit |

---

## 1. Ce qui est PROPRE — et mérite d'être dit

L'audit du **chemin de décision lui-même** ne trouve **aucune violation** :

- **`penser()`** (1163-1460) : 5 `if` au total — 2 drapeaux d'ablation
  (`BRAIN_SPARING_ACTIF`, `TAUX_DISTILLATION_C1 > 0`), 1 masque C3, 2 gardes de forme
  tensorielle. **Zéro seuil comportemental.**
- **`simuler_futur_et_planifier()`** (962-1110) : 2 `if` — `i == 0 and saut == 0` (structure
  du rollout) et `vecteur_bio is not None` (garde). **Aucun nombre nu.**
- **`vigueur()`** : `énergie ** κ` borné — une puissance continue, pas un seuil.
- **`acceptation()`** : produit de deux grandeurs dans [0,1], aucune constante.
- **`bus_sensoriel.py`** : les seuls littéraux sont `/4.0` (moyenne de 4 capteurs), `/2.0`
  (remap [−1,1]→[0,1]), `π/2` (géométrie). **Tous structurels.**
- **`_besoin_dominant`** : `max()` tranche l'ordre des besoins — l'ancien
  `Nourriture > Eau > Stimulation` en dur a bien été supprimé.

> Le cœur cognitif tient le dogme. Les violations sont **en périphérie** : métabolisme,
> curriculum, thermostat.

---

## 2. ❌ VIOLATION 1 — la table de coût par action (la plus nette)

[`noyau.py:2452`](../../src/naulthene/cerveau/noyau.py#L2452)

```python
COUT_CORPOREL_PAR_ACTION = {
    0: 0.2,  # left
    1: 0.2,  # right
    2: 0.5,  # forward
    3: 0.8,  # pickup
    4: 0.8,  # drop
    5: 0.6,  # toggle
    6: 0.1,  # done — quasi inaction
}
```

**Sept valeurs déclarées, indexées par l'action MiniGrid, avec les noms en commentaire.**
C'est structurellement identique à la table `lava = danger` que l'invariant v36.0 interdit —
seulement déplacée du *quoi* vers le *combien*.

**Pourquoi c'est grave** : ce dictionnaire est lu à **chaque tick** par
`calculer_effort_metabolique` (ligne 2560) et pèse **80 %** de l'effort
(`POIDS_CORPS = 0.80`). Il décide donc en permanence de ce que coûte vivre — et donc de
l'énergie, donc de la vigueur, donc de tout l'arbitrage. Ces sept nombres n'ont **jamais été
mesurés** : ils sont posés a priori.

**Conséquence concrète mesurée aujourd'hui** : `manger` (0,8) coûte **4× plus cher** que
`tourner` (0,2). Or l'autopsie d'`esprit_g7` montre une efficacité du geste manger de
16,3 % — l'agent paie donc le tarif maximal pour un geste qui échoue 5 fois sur 6. Rien ne
dit que ce barème soit juste ; il n'a jamais été confronté à une mesure.

**Correctif conforme au dogme** : dériver le coût de ce que l'action **fait réellement** —
un déplacement effectif coûte, un geste bloqué par un mur coûte moins, une rotation coûte
la même chose quel que soit l'index. Le monde fournit déjà l'information (position avant/
après, succès du `pickup`). Méthode imposée par CLAUDE.md : **instrumenter et mesurer
d'abord**, puis remplacer.

---

## 3. ❌ VIOLATION 2 — le thermostat de neurogenèse

[`noyau.py:8244-8250`](../../src/naulthene/cerveau/noyau.py#L8244)

```python
if len(etat.historique_erreurs) > 3:      # fenêtre en dur
    etat.historique_erreurs.pop(0)
if len(etat.historique_erreurs) == 3:
    if variance_erreur < 0.005 and moyenne_glissante > etat.seuil_base * 1.5:
        etat.seuil_base = (0.7 * etat.seuil_base) + (0.3 * moyenne_glissante)
```

**Cinq nombres nus** (`3`, `0.005`, `1.5`, `0.7`, `0.3`), aucun nommé, aucun mesuré. Et
c'est un **vrai `if` de décision** : il modifie `seuil_base`, qui pilote la neurogenèse —
donc la croissance du cerveau.

**Ce n'est pas théorique** : mesuré sur les 600 nuits d'`esprit_g7`, **3 mutations** et
**3 guérisons** ont été déclenchées par cette branche. Elle agit.

Le `0.005` est le plus suspect : c'est une variance **absolue** comparée à une erreur JEPA
qui vaut ~0,012 sur ce cerveau. C'est exactement le défaut de `SEUIL_CRISTAL` (jamais
franchi, 0,80 contre une myéline réelle de 0,0038) et de `q_ref = 1.0` (500× trop grand),
tous deux documentés en v37.0 : **une échelle absolue posée a priori, jamais confrontée à la
mesure.**

**Correctif conforme** : la variance doit être **relative** à l'erreur courante
(coefficient de variation), et la fenêtre de 3 nuits dérivée du rythme réel de
consolidation.

---

## 4. ❌ VIOLATION 3 — les coefficients nus de P17

[`noyau.py:6178-6226`](../../src/naulthene/cerveau/noyau.py#L6178)

```python
_croissance = (0.15 + 0.85 * avancement) * (1.0 + maitrise) / (1.0 + TAUX_PROMOTION)
poids_defi  = max(defi_reference * 0.5, 1.0 - poids_revision - poids_incursion)
etalement   = max(0.5, ETALEMENT_MAX_CURSUS * (1.0 - maitrise))
sigma_d     = max(0.4, etalement * 0.6)
```

Le fichier est **exemplaire dans son commentaire** — il explique que le plancher du défi est
« DÉRIVÉ du point de passage P17, pas posé ». Mais **`0.5`, `0.15/0.85`, `0.4`, `0.6` ne
sont dérivés de rien** : ce sont des réglages de forme, écrits à la main.

C'est le cas visé par l'avertissement de CLAUDE.md : *« remplacer un chiffre arbitraire par
une formule arbitraire ne vaut pas mieux, elle est juste plus difficile à remettre en
cause. »* Quatre constantes nues cachées dans une formule qui a l'air dérivée.

**Gravité tempérée** : le factoriel d'aujourd'hui a montré que le mur du niveau 4 n'était
**pas** P17 mais la décision (loi A). P17 n'est donc pas le blocage n°1 — mais il reste
non conforme.

---

## 5. 🟡 TOLÉRÉS — et pourquoi

| Élément | Ligne | Verdict |
|---|---|---|
| `PROFILS_NUTRITIONNELS` | 4637 | **décrit le MONDE**, pas la connaissance de l'agent. Une pomme *contient* des calories, ce n'est pas une croyance. Même statut que `DetecteurRessourcesBiologiques`. Le commentaire le dit explicitement. |
| `t == "wall"` | 6387 | **instrumentation** — calcul de densité de murs pour la parenté de cartes. Ne touche pas la décision. |
| `type == "ball"` | 6539 | **instrumentation** — compte les ressources pour la télémétrie. |
| `MOTS_OBJETS` (`"lava": "lave"`) | 3709 | **hémisphère vocal** — traduction pour la parole, jamais lue par la décision. |
| `if _f < 0.15: "🌱"` | 8316+ | **affichage** — choisit un emoji. Hors dogme. |
| `rever(batch_size=32)` | 1694 | défaut de signature **toujours écrasé** par l'appelant (`pourcentage_reve` adaptatif). Inoffensif, mais trompeur. |
| `cycle_sommeil(q_ref=1.0)` | 179 | idem — `echelle_myeline` (v37.0) le remplace à l'appel. |
| `POIDS_CERVEAU/CORPS 20/80` | 2405 | **hypothèse de conception assumée** (« Métabolisme 20/80 », v19.0), documentée et nommée. Discutable, pas caché. |

---

## 5 bis. ÉTAT APRÈS CORRECTIFS (mis à jour le 17/08 au soir)

| # | Violation | État | Version |
|---|---|---|---|
| 1 | `COUT_CORPOREL_PAR_ACTION` (7 valeurs) | ✅ **levée** — effort = travail physique | v41.20 |
| 2 | thermostat (5 nombres nus) | ✅ **levée** — cohésion/friction cosmologique | v41.21 |
| 3 | P17 (4 coefficients de forme) | 🟡 **conservée sciemment** — voir ci-dessous | — |
| — | `rayon = 0.5` (introduit en v41.20) | ✅ **levé** — `PAS_GRILLE / 2` | v41.21 |
| — | `POIDS_CORPS` / `POIDS_CERVEAU` | ✅ **dérivés** — loi des 2 % / 20 % | v41.21 |

### Pourquoi P17 est conservée en l'état

Décision utilisateur, et elle est fondée : **P17 est le mécanisme d'apprentissage du
cursus**, celui qui permet au système de progresser *sans retour en arrière*. Ses quatre
coefficients (`0.15/0.85`, `0.5`, `0.4`, `0.6`) règlent la **forme** d'une distribution,
pas un seuil de décision comportementale — ils décident *combien* de révision, jamais *si*
l'agent doit réviser.

S'y ajoute une mesure : le plan factoriel du 17/08 a montré que le mur du niveau 4
**n'était pas P17** mais la décision (loi A, brain-sparing). Toucher à ces coefficients
maintenant reviendrait à modifier un mécanisme qui n'est pas le blocage, avec le risque de
casser la seule voie de progression du cursus.

⚠️ Elle reste néanmoins une non-conformité, et doit être retraitée si une mesure la
désigne un jour comme limitante.

### Ce qui reste toléré, et pourquoi

| Élément | Statut |
|---|---|
| `SOUVENIRS_PAR_DIM` | facteur d'échelle (slots mémoire par dimension) — calibré par mesure en v31.0 |
| `EXTENSION_PATIENCE_SURSAUT = 50` | **signal d'entrée mort** : taux de succès du sursaut mesuré à **4 %**, 96 % des nuits à zéro. Rendre la constante adaptative sur une variable qui ne varie pas ajouterait de la complexité pour un effet nul (défaut `SEUIL_CRISTAL` / `indecision_c2`) |
| `DIM_BUS_MAX = 96` | plafond **quasi jamais atteint** : 1 cerveau sur 40. Ce n'est pas lui qui limite la croissance, c'était le thermostat (corrigé en v41.21) |
| `FRACTION_MASSE_CERVEAU`, `FRACTION_ENERGIE_CERVEAU` | **mesures biologiques** sur le vivant, pas des réglages |
| `PAS_GRILLE` | propriété de l'environnement (MiniGrid est discret) |

---

## 6. Synthèse

| # | Violation | Chemin cognitif ? | Agit réellement ? | Priorité |
|---|---|---|---|---|
| 1 | `COUT_CORPOREL_PAR_ACTION` — 7 valeurs déclarées | **oui, chaque tick** | **oui, 80 % de l'effort** | 🔴 **haute** |
| 2 | thermostat neurogenèse — 5 nombres nus | non (nocturne) | **oui, 3 mutations/600 nuits** | 🟠 moyenne |
| 3 | P17 — 4 coefficients de forme | non (curriculum) | oui, mais pas le blocage | 🟡 basse |

**Le cœur (C1, C2, rollout, sens, arbitrage) est conforme.** Les trois violations sont
périphériques mais réelles, et la n°1 est structurellement la même faute que celle
interdite par l'invariant v36.0 : une table de valeurs déclarée par index d'action.

⚠️ **Aucune ligne de `src/` n'a été modifiée par cette revue.** La méthode du projet impose
d'**instrumenter et mesurer avant** de rendre une constante adaptative — remplacer ces sept
nombres par sept autres nombres, ou par une formule inventée, reproduirait exactement la
faute. Le correctif de la violation n°1 demande d'abord une mesure du coût réel par action,
qui n'existe pas aujourd'hui.
