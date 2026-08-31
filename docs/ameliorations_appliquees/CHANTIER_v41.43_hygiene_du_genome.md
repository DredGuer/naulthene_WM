# Chantier v41.43 — l'hygiène du génome : P7 et P3

**30/08/2026** · document `ameliorations_appliquees/` : ce qui est **livré**, et ce qui a
été **écarté** en route.

Suite de l'[audit du génome](../etat_des_lieux/30082026_le_genome_audit_des_constantes.md)
(v41.41) et de la [cohorte du barème](../recherche/campagnes/COHORTE_30082026_le_bareme_ne_predit_rien.md)
(v41.42, 17ᵉ réfutation).

⚠️ **Ce chantier ne promet RIEN sur le plafond.** Dix-sept réfutations invitent à ne pas
présenter une correction de cohérence comme une piste de performance. Ce qui est corrigé
ici est **l'alignement du code sur le dogme**, mesuré — pas le niveau atteint, qui n'a pas
été mesuré.

---

## P7 — `MALUS_DOULEUR` supprimé ✅

**Ce qui a été fait** : suppression de la définition `MALUS_DOULEUR = -0.01` dans
`noyau.py`.

Retirée du **chemin** de récompense en v41.27 (la douleur passe par `calculer_deficit`,
donc par `r_bio`), la **définition** subsistait — lue par aucun code du noyau.

**Pourquoi ce n'était pas inoffensif** : une constante morte n'est pas inerte.
`sonde_recompense` l'a **ressuscitée pendant trois versions**, facturant un coût disparu
sur 57,8 % des ticks et **retournant le signe de sa conclusion** (solde affiché −4,1621
contre +0,4579 réel). C'était l'une des quatre récompenses posées de l'audit du dogme, et
celle qui rendait `mourir` (0.0) **moins cher** que `se cogner` (−0.01).

⚠️ **`colab.py` la conserve et l'UTILISE** (l. 1194). La suppression ne vaut que pour
`noyau.py`, conformément à la séparation essai/référence du projet — `colab.py` a
plusieurs versions de retard et son portage se fait mécanique par mécanique.

---

## P3 — l'échelle de la stagnation, dérivée du monde ✅

### 🔴 La proposition initiale était FAUSSE, et la mesure l'a corrigée

P3, tel qu'écrit dans l'audit du 30/08 au matin, disait :

> « La stagnation n'a pas besoin d'être *punie* — elle **coûte déjà**, par le métabolisme
> basal. Poser la pénalité **en plus** facture deux fois la même chose. »

**C'est faux.** Mesuré :

| Grandeur | Ce qu'elle facture | Valeur |
|---|---|---|
| Métabolisme basal | le **TEMPS** (chaque tick, quoi qu'il arrive) | 0,003250/tick |
| Pénalité de stagnation | la **REDONDANCE SPATIALE** (revenir sur ses pas) | `1.5 ** occurrences` |

**Un agent qui avance en ligne droite paie le basal et RIEN en stagnation.** Ce ne sont
pas les mêmes grandeurs — supprimer la seconde aurait retiré le **seul signal
anti-piétinement** du barème. La proposition est **écartée telle quelle**, et c'est
consigné ici précisément pour qu'elle ne soit pas ré-proposée.

### Le vrai défaut : l'échelle n'était reliée à rien

`PENALITE_STAGNATION_BASE = 0.015` n'était indexée ni sur ce que vaut une victoire, ni sur
le vécu de l'agent. Mesuré sur **40 cerveaux** (800 ticks) :

| Constat | Valeur |
|---|---:|
| Stagnation cumulée par cerveau | **−14,44** |
| Victoires réellement obtenues | 2 à 3 |
| **Équivalent en victoires effacées** | **14,4** |
| Ticks de piétinement annulant une victoire | **8,8** |

### La dérivation

Une victoire MiniGrid rapporte `1 − 0.9 × (pas/max_steps)`, donc au **pire** `0.1`
(victoire à l'ultime tick). Le budget de douleur d'un épisode entièrement piétiné ne doit
pas dépasser ce pire gain — sinon l'échec rapide devient préférable à l'exploration, et
**l'agent a raison de renoncer**.

```python
pénalité_unitaire = GAIN_MINIMAL_VICTOIRE / max_steps
```

`max_steps` est une propriété **du monde**, déjà lue par `_budget_natif_carte` (v41.30,
même précédent que la patience). L'écart avec la constante posée **grandit avec la carte** :

| Carte | `max_steps` | Dérivé | Posé | Écart |
|---|---:|---:|---:|---:|
| `Empty-5x5` | 100 | 0,001000 | 0,015 | **15,0×** |
| `SimpleCrossingS9N1` | 324 | 0,000309 | 0,015 | **48,6×** |
| `DoorKey-8x8` | 640 | 0,000156 | 0,015 | **96,0×** |

C'est une explication *mécanique* de pourquoi les grands niveaux sont invivables : plus la
carte est vaste, plus la taxe posée est disproportionnée.

### Effet mesuré sur le barème (A/B, même graine)

`A_g11`, niveau 3, 800 ticks, un seul facteur changé :

| | FOSSILE | DÉRIVÉ | Facteur |
|---|---:|---:|---:|
| Stagnation | −14,0527 | **−0,4156** | **÷33,8** |
| Total positif | 14,5106 | 15,9185 | ×1,10 |
| **Solde net** | **+0,4579** | **+15,5029** | **×33,9** |

⚠️ **Ce que ce chiffre n'est PAS** : une amélioration de performance. C'est une correction
d'**échelle**, mesurée sur **un** cerveau, **sans aucun run**. Ni le niveau ni la maîtrise
n'ont été mesurés.

---

## Invariants posés par ce chantier

1. **L'échelle se recalcule à chaque CARTE, jamais par tick.** `max_steps` ne change qu'au
   changement de niveau. Même discipline que `ajuster_capacite` (v31.0) et le rythme
   métabolique (v41.30) — une échelle fluctuant en cours d'épisode rendrait la douleur
   illisible pour l'agent **et** pour le diagnostic.

2. **`GAIN_MINIMAL_VICTOIRE = 0.1` est une BORNE lue dans le monde**, pas un réglage :
   c'est `1 − 0.9`, la valeur que MiniGrid lui-même attribue à une victoire in extremis.
   Le choix du **pire** cas plutôt que de la victoire moyenne est conservateur et assumé —
   une pénalité trop faible laisse piétiner, une trop forte fait renoncer, et c'est le
   second défaut qui a été mesuré.

3. **Le repli hors MiniGrid est défensif** : sans carte (vocal isolé, rêve), `max_steps`
   n'existe pas et on retombe sur la valeur de construction. Vérifié : `env=None` →
   0,015000.

4. **Le témoin `--stagnation-fossile` restitue EXACTEMENT l'ancien comportement.** Vérifié
   au dix-millième : −14,0527 et +0,4579, identiques aux mesures d'origine. Le drapeau est
   **branché dans le module nommé avec assertion runtime** — sans quoi les deux bras
   seraient identiques sans que rien ne le signale (bug v41.4, trois bras confondus).

---

## Ce qui reste ouvert

- **Aucune mesure comportementale.** Le niveau atteint et la maîtrise sous échelle dérivée
  ne sont **pas** mesurés. Une campagne appariée (20 graines, cursus complet, témoin
  `--stagnation-fossile`) serait nécessaire pour affirmer quoi que ce soit — et **rien
  dans ce chantier ne la justifie à lui seul**.
- **La curiosité reste non dérivée** (P4) : `PLAFOND_ERREUR_DOPAMINE = 2.0` pèse ~40 % du
  signal positif et son effet mesuré est **du bruit** (signe qui s'inverse entre bras).
- **`SEUIL_CRISTAL = 0.80`** (P6) reste vivant dans le code et jamais franchi (myéline max
  mesurée 0,0038, soit 210× moins).
- **`COULEUR_FOOD`/`COULEUR_WATER`** (P8) restent dans `noyau.py`.
