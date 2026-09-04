# CURSUS COMPLET — la voix libre franchit-elle le mur du niveau 5 ?

**Protocole écrit AVANT le lancement** (04/09/2026). C'est **le juge de paix** : les deux
campagnes précédentes ont mesuré la voix libre au **banc forcé**, qui ne prouve **rien** sur
le cursus (règle de mesure §6).

## La question

[j100](../../docs/recherche/campagnes/VOIX_LIBRE_03092026_le_premier_levier_du_depot.md) :
δ = **+12,43 pt**. [j200](../../docs/recherche/campagnes/VOIX_LIBRE_04092026_200_jours_le_temoin_s_effondre.md) :
δ = **+19,50 pt** (`t` = +9,58), et surtout le témoin **s'effondre** (−5,48 pt, 17/20).

Mais tout cela sur `--env-force SimpleCrossingS9N1` : la promotion était court-circuitée,
**le niveau restait à 1/15 par construction**. La question ouverte est donc entière :

> **Cette intégrité cognitive nouvelle permet-elle de FRANCHIR le mur ?**

Rappel de l'état de référence (campagne v41.29, 10 graines × 1500 j, régime témoin) :
**niveau 4/15 sur 10 graines / 10**, niveau 5 sur 2 seulement, et **aucun apprentissage au
palier atteint** (tendance de maîtrise jamais positive sur ~700 jours).

## Le protocole

| Élément | Valeur |
|---|---|
| Bras | **LIBRE** (`--gain-c1-libre`) vs **TÉMOIN** (gain v37.0) |
| Graines | **20**, appariées — les mêmes que les campagnes du banc |
| Jours | **1500** par run · **40 runs** |
| Environnement | **cursus complet, 15 niveaux** — ⚠️ **AUCUN `--env-force`** |
| Cerveaux | **neufs** — c'est une population indépendante, pas une reprise |
| Parallélisme | **6 runs simultanés** (M3 Pro 12 cœurs, ~700 Mo/run mesuré ⇒ ~4,2 Go / 36) |

⚠️ **Cerveaux neufs, et c'est délibéré** : les campagnes j100/j200 reprenaient une lignée,
donc n'étaient pas des réplications indépendantes. Ici on repart de zéro — ce run **réplique
ou non** le levier sur une population neuve, en plus de tester le cursus.

## Les critères, posés d'avance

| Juge | Grandeur | Succès | Échec |
|---|---|---|---|
| **1. Le mur du niveau 5** | niveau max atteint, bras LIBRE | **≥ 6/15 sur ≥ 10 graines** | ≤ 5 partout : le levier ne débloque pas le cursus |
| **2. Niveau, apparié** | δ niveau LIBRE − TÉMOIN | δ > 0 avec `t` > 2,43 (Bonferroni 3 métriques ⇒ **2,86**) | NS : l'effet du banc ne se transporte pas |
| **3. Apprentissage au palier** | tendance de maîtrise sur les 700 derniers jours | **positive** sur ≥ 10 graines LIBRE | ≤ 0 : le plafond n'est pas levé, seul le départ l'est |
| **4. Réplication du levier** | maîtrise moyenne finale, apparié | δ > 0 significatif | NS : le +19,50 pt était propre au banc forcé |

⚠️ **Bonferroni à 3 métriques** (niveau, maîtrise, tendance) ⇒ seuil `t` = **2,86**, pas 2,43.
Annoncé avant, pas après.

⚠️ **Le juge 3 est le plus important.** Franchir un palier de plus serait déjà un résultat,
mais le blocage du dépôt n'est pas « l'agent monte trop lentement », c'est **« l'agent
n'apprend pas au palier où il est »**. Un juge 1 positif avec un juge 3 négatif signifierait
que la voix libre donne un meilleur départ, pas une meilleure trajectoire.

## Vérifications prévues au dépouillement

| Vérification | Pourquoi |
|---|---|
| Drapeau `[BRAS A]` sur 20/20 LIBRE, 0/20 témoins contaminés | le régime a atteint l'individu (leçon v41.4) |
| Niveau atteint **par `env_id`**, jamais par index | un index se rétrograde silencieusement (invariant v35.0) |
| Promotion par **série** vs par **maîtrise** | la campagne v41.29 n'a promu QUE par série — si ça se reproduit, la maîtrise reste le vrai mur |
| Retrait des 4 extrêmes | le test qui a fait tomber la directivité |
| Graines à 0 victoire, saturation | comme aux campagnes précédentes |
| Ratio C2/C1 et amplitude C1 | mode d'échec v37.0 (seuil 0,3) — à **rapporter**, pas à corriger en cours |
| **Tautologie** | vérifier que la maîtrise n'est pas une mesure de victoire déguisée conditionnée sur « a gagné » |

## Limites, écrites d'avance

1. **1500 jours n'est pas l'infini** : la campagne v41.29 montrait un blocage stable sur
   ~700 jours au palier atteint. Si LIBRE franchit un palier au jour 1400, la tendance sera
   inexploitable — à signaler plutôt qu'à interpréter.
2. **Pas d'asymptote de netteté connue** : à j200, 20/20 cerveaux rebondissaient encore
   (juge 0 de la campagne précédente). Sur 1500 jours le régime d'entropie est **inconnu**.
3. **n = 20** : effet minimal détectable ≈ 6,3 pt de maîtrise (cf. `DIMENSIONNEMENT.md` de la
   campagne j100).
4. Le parallélisme à 6 ne change **rien** aux résultats (chaque run est indépendant et
   seedé), seulement le temps de calcul.

## Coût estimé

Un run de 1500 jours en cursus complet ≈ 60-90 min (les niveaux bas sont rapides). 40 runs
à 6 en parallèle ⇒ **~7 à 10 h**.

## Commandes

```bash
zsh brains/04092026_cursus_complet/lancer.sh    # 6 runs en parallele, reprend ou il s'arrete
```

⚠️ **Vérifier `ps aux | grep lancer.sh` avant tout lancement** — deux lanceurs simultanés ont
corrompu un `.brain` le 02/09.
