# Campagne v41.33 — LE BIT DE PORTAGE (proprioception de la charge)

**Lancée le 27/08/2026.** 20 graines appariées × 400 jours × 2 bras = **40 runs**.

## Ce qu'on cherche

L'agent est atteint d'**agnosie proprioceptive** : le critique distingue très bien un objet
en face d'un mur (d de Cohen +0,651 à +1,214, 3 cerveaux), mais **pas** « je porte un
objet » de « mains vides » (d = +0,119 / −0,117 / +0,090, signe instable).

Cause mesurée : des 41 dims du vecteur bio, **zéro** n'encodait l'inventaire (écart max
0,00001013 sur 4000 ticks). Aucune quantité de gradient ne fait apprendre une variable
absente de l'entrée.

Conséquence sur le crédit : `|A| utile / |A| neutre` entre **0,86× et 1,11×** sur
4 cerveaux — saisir une clé rapporte, à ±13 % près, ce que rapporte un quart de tour.

## Protocole

| | |
|---|---|
| **Bras A** | nominal — le bit porte `carrying` (0.0 / 1.0) |
| **Bras B** | `--sans-portage` — la 42ᵉ dim EXISTE mais reste à 0.0 |
| Graines | 11 22 33 44 55 66 77 88 99 111 122 133 144 155 166 177 188 199 211 222 |
| Jours | 400 |
| Env | cursus complet (pas de `--env-force`) |

⚠️ **Le témoin garde la DIMENSION et ne coupe que l'INFORMATION** (règle §6.3). Retirer la
colonne changerait la largeur d'`integrateur_bio` : on mesurerait « réseau large contre
réseau étroit », pas « avec ou sans proprioception ». Les deux bras ont exactement la même
architecture.

## Pourquoi 400 jours et pas 1440

Trop court pour juger la maîtrise du cursus. Largement suffisant pour que l'optimiseur
sculpte la 42ᵉ colonne — si l'information sert, le réseau s'y accroche bien avant.
Ce run répond à « l'agnosie est-elle levée ? », pas à « le cursus est-il débloqué ? ».

## Validations faites AVANT le lancement

| Test | Résultat |
|---|---|
| Contrat append-only | `portage=1.0` change **1 dim sur 42**, à l'indice **41** (la dernière) |
| Greffe 41→42 | `integrateur_bio` 186→187, acquis préservés (norme 5,691216) |
| Nuit complète post-greffe | **3 nuits**, aucun crash (le bug v32.0 n'apparaît qu'à `executer_nuit`) |
| Le bit varie en jeu | 28,3 % des ticks à 1.0, **accord 100 %** avec `carrying` |
| Le témoin atteint le module | `🔬 [ABLATION] bit de portage v41.33 COUPÉ` + assertion runtime |

## ⚠️ AUCUN `t` AVANT LA FIN DES 40 RUNS

Leçon du 20/08 (`t=+3,68` à mi-parcours → `+1,93` à la fin) et du 22/08 (maîtrise +4,95 à
n=5 → +1,09 à n=20). Un `t` sur un run inachevé choisit implicitement sa fenêtre.

**Correction de Bonferroni** obligatoire dès qu'on teste plusieurs métriques.

## Ordre d'analyse arrêté

1. **`sonde_credit.py` d'abord** — c'est le mécanisme visé, et il se lit sur le `.brain`
   final (mesure directe, la nature la plus fiable du §4). La question : `A_saisie` se
   détache-t-il enfin de `A_neutre` ?
2. **Le critique ensuite** — le d de Cohen porte/vide est-il sorti de 0,1 ?
3. **Le comportement en dernier** — taux de saisie, récolte, maîtrise. À 400 jours, une
   maîtrise plate ne réfute PAS le mécanisme ; un crédit resté plat, si.

## Reproduction

```bash
brains/27082026_v4133_portage/lancer.sh
```
