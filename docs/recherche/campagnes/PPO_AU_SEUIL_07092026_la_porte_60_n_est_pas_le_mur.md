# PPO FACE À LA RÈGLE 60 % — la porte n'est pas le mur, le goulot est l'apprenant

**Date** : 2026-09-07 · **Statut** : ✅ **DÉPOUILLÉ** (5/5 runs, 0 échec) · **Nature** :
banc PPO — zéro ligne de `noyau.py` touchée (protocole A, pré-enregistré).

> Protocole : `brains/07092026_protoA_ppo_seuil60/LISEZ_MOI.md` · sortie brute :
> `analyse_fenetres.txt` · vecteurs : `ppo_g*.json` · pré-vol A/A : `prevol_aa.json`.
> Source : [protocoles en réserve §1](../../ameliorations/07092026_protocoles_en_reserve.md)
> et [point général du 07/09](../../etat_des_lieux/07092026_point_general_et_direction.md) §2.3.2.

## 1. La question

Le seuil de promotion du cursus (`TAUX_PROMOTION` = 60 % sur `FENETRE_PROMOTION` = 20
épisodes, victoire = `r > 0`) est **au-dessus de ce que PPO atteint** sur la vraie carte du
mur (`SimpleCrossingS9N1`, 36-40 % à 152 k pas). Le mur « Niveau 4/15 » est-il **en partie
une règle du cursus** ? Un PPO qui converge — lui — validerait-il ne serait-ce qu'une fois
une fenêtre de 20 à ≥ 12 victoires ?

## 2. Protocole et pré-vol

- **5 graines** (11, 22, 33, 44, 55) × **152 043 pas**, arch [69,69] (le meilleur bras du
  29/08), observation aplatie 7×7×3, `MlpPolicy`, 7 actions, récompense brute.
- Capture du vecteur binaire victoire/défaite **épisode par épisode pendant
  l'entraînement** (`Monitor`, victoire = `r > 0`), puis fenêtres glissantes de 20
  (`≥ 12/20`) **et** route série (2 victoires consécutives, l'autre branche du OU).
- **Pré-vol A/A** (18:13) : 2 × 20 k pas → **vecteurs bit-identiques** (64 épisodes × 2) :
  la capture est valide.

## 3. Résultats par graine

| Graine | Épisodes | Taux vie | **Fin de vie** (100 derniers) | MAX fenêtre 20 | Fenêtres ≥ 12/20 | Route série (2 conséc.) |
|---|---|---|---|---|---|---|
| g11 | 543 | 20,8 % | **40 %** | **12/20** | **5** (1,0 %) | 31 · max série 5 |
| g22 | 478 | 2,7 % | 10 % | 5/20 | 0 | 2 · max série 2 |
| g33 | 527 | 20,1 % | **47 %** | **12/20** | **8** (1,6 %) | 35 · max série 8 |
| g44 | 480 | 4,0 % | 8 % | 4/20 | 0 | 4 · max série 3 |
| g55 | 570 | 24,7 % | 31 % | **11/20** | 0 | 47 · max série 6 |

## 4. Les juges (posés d'avance)

| Juge | Grandeur | Mesuré | Verdict |
|---|---|---|---|
| **1. Porte 60 %** | ≥ 1 fenêtre ≥ 12/20, par graine | **2/5** (g11, g33 — celles qui convergent à ~45-50 %) | → verdict pré-enregistré : **le seuil n'est pas à lui seul le mur — le goulot est l'apprenant** |
| **2. Fidélité** | reproduction de la baseline 29/08 | fin de vie 10-47 % — l'étalement de la baseline (36,2 ± 13,3 à n=20) est reproduit, en plus étroit (n=5) | ✅ le banc mesure bien la même chose |
| **3. Route série** | occurrences de 2 victoires consécutives | **4/5 graines** déclenchent massivement la voie rapide (jusqu'à 47) | → un PPO **dans le cursus** (promotion = OU) ne resterait **pas** bloqué par la porte 60 % |

## 5. Ce que ça établit, ce que ça n'établit pas

**Établi** :
- La porte 60 % × 20 **n'est pas infranchissable pour un apprenant qui fonctionne** : PPO la
  passe dès qu'il converge à ~45 % (g11, g33). L'énoncé « le seuil exige 60 % quand PPO
  plafonne à 40 % » est **trop simple** : c'est le taux *de vie* qui plafonne à 36-40 %, pas
  la fenêtre locale d'un PPO convergent.
- Les **deux voies du OU** (série de 2 et porte 60 %) auraient promu un PPO placé dans le
  cursus : la voie rapide seule suffit (4/5 graines). **Le mur du niveau 4 ne s'explique pas
  par la règle de promotion.**
- La réponse à la question du point général (§2.3.2 « PPO resterait-il au niveau 4 ? ») est
  **non** — avec la réserve ci-dessous.

**NON établi** :
1. **n = 5**, sous la barre des 20 graines du dépôt. Le contraste (2/5) est net, pas fin.
2. **Deux graines convergent mal** (g22 → ~10 %, g44 → ~6-8 %, dernière fenêtre à 0 %) :
   c'est l'**instabilité propre de PPO** (hyperparamètres par défaut, sans échelonnage
   d'entropie), pas un artefact du script — mais ça borne ce que 5 graines peuvent dire.
3. Le banc entraîne PPO **de zéro sur la carte du mur** : un PPO ayant déjà passé les paliers
   0-3 dans le vrai cursus arriverait sur `SimpleCrossingS9N1` avec une politique déjà
   entraînée — la comparaison au curriculum réel reste indirecte.
4. Budget 152 043 pas et arch 69 seuls. L'ambiguïté g55 (11/20 à ~35 %, jamais 12) se
   trancherait à budget 600 k pas si on voulait la forme précise de la fonction de passage.

## 6. Décision qui s'ensuit (selon le LISEZ_MOI)

**Ne pas baisser `TAUX_PROMOTION`.** Le seuil n'étant pas la cause du blocage, le baisser
(proposition « ~35 % » du 07/09) promouvrait du bruit sans rien réparer — et la voie maîtrise
reste l'assurance de robustesse du cursus (invariants v35.0). L'ordre des décisions du point
général tient : **réparer l'apprenant** (balayage K/ε autour de K = 8, puis campagne de
soustraction) avant tout nouvel organe. Le protocole C (banc moteur minimal sous régime
réparé) et le balayage K/ε restent les prochaines étapes préparées.

## 7. Liens

- [Protocoles en réserve §1](../../ameliorations/07092026_protocoles_en_reserve.md) — les juges et la règle de décision
- [BASELINE_PPO_29082026](BASELINE_PPO_29082026_le_mur_n_existe_pas.md) — la référence 36-40 %
- [EPOQUES_07092026](EPOQUES_07092026_le_mur_du_niveau_4_est_franchi.md) — 5/20 promus **par la voie maîtrise** sous K8 (le seuil est atteignable par un apprenant réparé)
- [Point général du 07/09](../../etat_des_lieux/07092026_point_general_et_direction.md) §2.3.2 et §5.2

---

*Protocole A — lancé le 07/09 à 18:13 après le pré-vol A/A bit-identique, dépouillé à 18:15.
Répond « non » à la question « PPO resterait-il bloqué par le barème ? » : le barème n'est
pas le mur.*
