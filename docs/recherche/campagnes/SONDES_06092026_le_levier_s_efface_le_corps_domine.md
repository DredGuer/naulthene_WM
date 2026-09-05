# DEUX SONDES À COÛT ZÉRO — le levier de l'agent s'efface, le corps domine

**Date** : 2026-09-06 · **Statut** : ✅ **DEUX MESURES ÉTABLIES**, une hypothèse réfutée ·
**40 cerveaux × 1500 jours, n = 20 graines appariées** · coût : **zéro run**.

> Pistes §2.a et §8 du
> [PLAN_05092026](../../ameliorations/PLAN_05092026_toutes_les_pistes_classees.md).
> Les deux étaient des **prérequis** : chacune pouvait vider une piste avant qu'elle soit codée.

---

## A. §2.a — LE MODÈLE DU MONDE DISTINGUE-T-IL LES ACTIONS ?

### La question

C2 évalue ses 8 branches via `_predire_bus(pensee, action_onehot)` (`noyau.py:1103`). Si
JEPA produit le **même** futur quelle que soit l'action, `valeur_cumulee` est du bruit
**avant** normalisation — et aucune tête posée sur C2 (§5, la tête d'intention) ne pourrait
rien y changer.

**Mesure** : `ratio = δ_action / δ_temps`, où `δ_action` est la distance moyenne entre deux
futurs prédits d'actions différentes, et `δ_temps` la distance entre deux pensées réelles
successives. Le dénominateur est l'échelle du problème : *« de combien le monde bouge tout
seul en un tick »*.

### Le résultat, et le témoin qui le renverse

| | δ_action | δ_temps | **ratio** |
|---|---|---|---|
| **Cerveau NEUF** (Xavier, n=5) | 1,3987 | 0,2983 | **4,79** |
| **Cerveau ENTRAÎNÉ 1500 j** (n=40) | 0,2786 | 0,7410 | **0,48** |

**L'apprentissage divise la sensibilité à l'action par 10.**

Et les deux termes bougent **en sens opposés** : `δ_action` est divisé par 5 pendant que
`δ_temps` est multiplié par 2,5. Le modèle du monde devient **plus sensible au temps qui
passe** et **moins sensible à ce que l'agent décide**.

| | LIBRE | TÉMOIN | δ apparié |
|---|---|---|---|
| ratio moyen | 0,4880 | 0,4651 | +0,0228 (`t` = +0,318, **12/20**, NS) |

Aucune différence entre les deux régimes : **c'est une propriété de l'architecture**, pas du
gain de C1.

### Ce que ça ferme, ce que ça ouvre

✅ **La piste §5 (tête d'intention) SURVIT** : le ratio n'est pas nul (médiane 0,46, aucun
cerveau sous 0,10). JEPA n'est **pas** aveugle à l'action — il y a bien un signal à
départager. Ma prédiction pré-enregistrée (*« si ratio ≈ 0, §5 est vide »*) est réfutée dans
le sens favorable.

🔴 **Mais un fait nouveau apparaît, et il n'était dans aucune hypothèse** : le levier de
l'agent **s'efface au fil de l'apprentissage**. C'est cohérent avec les victoires browniennes
(14–18× le plus court chemin) et avec l'inertie de C2 — un C2 qui départage des futurs de
plus en plus semblables a de moins en moins à dire.

⚠️ **Ce que cette mesure NE dit PAS.** Une décroissance de `δ_action` peut être **saine** :
un modèle du monde qui apprend que la plupart des actions ne changent rien (tourner sur
place dans un couloir) *doit* prédire des futurs semblables. Rien ici n'établit que
`ratio = 0,48` soit pathologique — le seul point de comparaison est un réseau non entraîné,
qui n'est pas une référence de qualité (le témoin « cerveau neuf » est connu pour avoir un
biais d'action arbitraire selon sa graine). **Il manque le ratio d'un modèle du monde
COMPÉTENT**, qui n'existe pas dans le dépôt.

---

## B. §8 — LA PERMÉABILITÉ D'`integrateur_bio` : hypothèse de dilution RÉFUTÉE

### La question

Deux ajouts passifs en queue du vecteur bio (bit de portage, ancrage cinématique) ont donné
**deux effets nuls à n=20**. L'explication supposée était la **dilution** : une dimension
noyée dans 44 autres. Jamais mesurée.

**Mesure** : norme L2 du poids effectif (`base_weight + annexe_weight`, comme `forward`) par
colonne d'entrée, rapportée à la norme moyenne d'une colonne de **pensée visuelle**.

### Le résultat — le corps pèse 2,5 à 5,6× la vision

| Tranche | dims | ratio vs vision |
|---|---|---|
| **chimie** (odorat/goût) | 4 | **5,571** |
| **jauges** (satiété, hydratation, stimulation) | 3 | **5,548** |
| toucher | 4 | 3,942 |
| pression | 2 | 3,556 |
| **élan** (ancrage cinématique) | 2 | **3,413** |
| clinotaxie | 2 | 3,358 |
| rappel marquant | 2 | 3,263 |
| rappel spatial | 2 | 3,079 |
| thermoception | 2 | 2,525 |
| quête | 3 | 1,774 |
| portage | 1 | 0,271 |
| **quête vocale** | 8 | **0,055** |
| **Exo-Sens** | 8 | **0,055** |
| **présence auditive** | 1 | **0,055** |

🔴 **L'hypothèse de dilution est RÉFUTÉE.** Les sens ne sont pas ignorés : **chaque
dimension du corps pèse 2,5 à 5,6× une dimension de vision**. Le réseau écoute son corps
bien plus que ses yeux — ce qui recoupe indépendamment le `Bio` à **57,0 %** du gradient
([MIXAGE](../enquetes_closes/MIXAGE_04092026_les_termes_morts_ne_sont_pas_du_code_mort.md)).

### 🔴 Le résultat le plus important : une norme n'est PAS un usage

**`élan` pèse 3,41× la vision — et son effet comportemental fut mesuré NUL à n=20.**

C'est la démonstration directe, sur une dimension dont on connaît déjà le verdict, qu'un
poids élevé prouve qu'une **voie existe**, jamais qu'elle **porte de l'information**. Le
dépôt le savait en théorie (v37.0 : `tete_motrice` modifie 7,43 % de ses poids à norme
constante) ; c'en est la confirmation expérimentale.

> **Conséquence directe pour le plan : §7 (la trace du chemin en queue du vecteur bio) ne
> peut PAS être justifiée par « il faut vaincre la dilution ». Il n'y a pas de dilution.**
> Si un canal supplémentaire échoue, ce sera pour une autre raison — qui reste à trouver.

### Les trois canaux morts, et leur signature

`quête vocale`, `Exo-Sens` et `présence auditive` sont à **0,055** avec un σ inter-cerveaux
de **0,0119** — identique aux trois. C'est le **plancher Xavier jamais bougé** : la
signature exacte de l'hémisphère audio
([AUDIO](../enquetes_closes/AUDIO_05092026_un_hemisphere_deja_gele.md)). Trois canaux de
plus qui n'ont jamais reçu de gradient, pour la même raison : **hors de leur domaine** (pas
de leçon vocale, pas de plug C3, pas d'audio en cursus MiniGrid).

Le `portage` est différent : **12 cerveaux sur 40** l'ont fait monter jusqu'à 1,15 ; les 28
autres sont au plancher (médiane 0,058). Ce canal-là **vit**, chez ceux qui portent.

### ⚠️ Limites

1. **Une norme n'est pas un gradient.** Cette sonde mesure une *attention structurelle*, pas
   un flux d'information. La mesure décisive serait la norme du gradient de `perte_acteur`
   par colonne — plus coûteuse, non faite.
2. **Rien ici n'est relié à un juge.** Ni la maîtrise, ni la directivité, ni le niveau. Ce
   sont des diagnostics, pas des leviers.

---

## C. Ce que ces deux sondes changent au plan

| Piste | Avant | Après |
|---|---|---|
| **§5 tête d'intention** | conditionnée à §2.a | ✅ **débloquée** — JEPA distingue les actions |
| **§7 trace du chemin** | « bloquée par la dilution » | 🔴 **sa justification tombe** — il n'y a pas de dilution |
| **§8 perméabilité** | 🟡 diagnostic | ✅ **fait** — hypothèse réfutée |
| **nouveau** | — | 🔴 **le levier de l'agent s'efface** (δ_action ÷5 en 1500 j) |

---

*Outils créés : `sonde_jepa_action.py`, `sonde_permeabilite_bio.py` (lecture seule, `.brain`
copié avant chargement). Agrégat : `brains/06092026_sondes_zero_run/agregat.json`.*

---

## D. §7 — LA SECONDE TABLE DE MIXAGE : le critique mange 89 % de l'entrée de la décision

**Ajouté le 06/09, même campagne, 40 cerveaux × 300 ticks.**

### La question

La table de mixage des **récompenses** a été mesurée (`Bio` 57 %). Il en existe une
**seconde**, jamais mesurée, un étage plus bas : `perte_totale` somme JEPA + vocal + acteur
+ critique + entropie + distillation, puis **un seul `backward`, un seul Adam, un seul `lr`**.

**Mesure** : un `backward` par terme (jamais de `step`), norme du gradient reçue par couche.

### Le résultat

| Couche | jepa | acteur | **critique** | entropie |
|---|---|---|---|---|
| **`integrateur_bio`** | 4,00 % | **6,57 %** | **89,24 %** | 0,19 % |
| `tete_motrice` | — | **97,95 %** | — | 2,05 % |
| `cortex_prefrontal` | — | — | **100 %** | — |
| `generateur_attente` | **100 %** | — | — | — |

🔴 **`integrateur_bio` est sculptée à 89,24 % par le critique, contre 6,57 % par l'acteur —
un rapport de 13,6×.** Et ce n'est pas une moyenne trompeuse : **40 cerveaux sur 40**, ratio
médian **11,50×**, min **1,23×**, max **67,20×**.

Or `integrateur_bio` est **l'entrée unique de la décision** : `tete_motrice` ne lit que
`pensee_bio`, sa sortie. La couche qui décide de ce que l'agent perçoit de son corps est donc
formée à 89 % par un organe mesuré **inerte** ([ABLATION_C2](ABLATION_C2_05092026_l_organe_muet.md)).

### Le chaînon manquant du 05/09

| Bras | ratio critique/acteur | ‖grad acteur‖ | ‖grad critique‖ |
|---|---|---|---|
| **LIBRE** | **6,69×** | 0,05585 | 0,41676 |
| **TÉMOIN** | **16,38×** | 0,03635 | 0,83464 |
| apparié | δ = **−13,52×** · `t` = **−4,434** · n=20 | +54 % | −50 % |

**La voix libre ne touche pas au critique : elle rend sa voix à l'acteur** (+54 % de
gradient) *et* réduit de moitié celui du critique. Elle divise par 2,4 la domination.

C'est l'explication mécanique de
[ATROPHIE](ATROPHIE_05092026_la_boucle_de_compensation.md) : si C1 s'atrophie chez 20 témoins
sur 20, c'est que son gradient est étouffé à la source, dans la couche qui le nourrit.

### ⚠️ Limites

1. **Une norme de gradient n'est pas une direction.** Un gradient 13× plus grand peut
   pousser dans une direction inutile. Le test décisif serait le cosinus entre les deux.
2. **Mesuré à l'état courant** (jour ~1500), pas moyenné sur la vie. Le ratio à la naissance
   n'est pas connu.
3. **Ce n'est pas une pathologie établie.** Un critique qui reçoit plus de gradient qu'un
   acteur est **normal** en Actor-Critic (la MSE d'un critique mal calibré est grande). Ce
   qui est anormal serait que cela **empêche** l'acteur d'apprendre — non mesuré.
4. **Aucun lien à un juge.** Ni maîtrise, ni directivité, ni niveau.

### Ce que ça ouvre

🟢 **Une piste neuve, absente du plan du 05/09** : découpler les deux gradients dans
`integrateur_bio` — soit par un `lr` propre au critique **dérivé** du rapport mesuré (jamais
posé), soit par un `.detach()` du critique sur cette couche seule, à l'image du
`--detach-c2` en cours. Témoin apparié, 20 graines.

🔴 **CORRECTION — le `--detach-c2` en cours teste EXACTEMENT cela, pas « presque ».**
Vérifié dans le code après coup (`noyau.py:1556`) :

```python
_bio_pour_c2 = pensee_bio.detach() if DETACH_C2_ASYMETRIQUE else pensee_bio
valeur_etat_courant = self.cortex_prefrontal(_bio_pour_c2)
```

C'est **la ligne même** que cette sonde mesure. Le drapeau coupe le gradient du critique
vers `pensee_bio`, donc vers **`integrateur_bio`** — la couche à 89,24 %.

**Conséquence pour la lecture du verdict** (à ne pas réécrire après coup) :

| Issue du run | Lecture |
|---|---|
| **δ maîtrise significatif** | la domination du critique **était** le goulot ; découpler devient un levier, et ce n'est plus une piste mais un résultat |
| **δ nul** (prédiction pré-enregistrée) | 89,24 % de gradient **ne gêne pas** l'acteur ; la 3ᵉ limite ci-dessus est confirmée, et la piste « découpler les gradients » **se ferme** au lieu de s'ouvrir |

⚠️ Écrit **avant** le verdict, à ~jour 950/1500. La sonde a été faite sans savoir ce que le
run dirait ; le run a été lancé sans savoir ce que la sonde dirait.
