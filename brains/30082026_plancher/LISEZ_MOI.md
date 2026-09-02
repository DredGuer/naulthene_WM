# Le plancher géométrique — 30/08/2026

Analyse : [PLANCHER_30082026](../../docs/recherche/campagnes/PLANCHER_30082026_la_competence_existe_et_la_maitrise_ment.md).

## Ce qu'on cherchait

Les ~15 % du niveau 4 sont-ils une compétence ou le plancher géométrique de la carte ?

**Réponse : une compétence.** L'aléatoire fait 5,67 %, les entraînés 25,83 % agrégé
(`z = +13,56`). Mais les victoires restent **browniennes** (14–18× le plus court chemin).

## Protocole

```bash
WANDB_MODE=offline PYTHONPATH=src venv/bin/python \
    -m naulthene.instruments.sonde_plancher_geometrique \
    --brain brains/30082026_plancher/p_<graine>.brain --episodes 300
```

4 cerveaux (A_g155, A_g122, A_g166, A_g66) · `SimpleCrossingS9N1` · 300 épisodes ·
3 politiques (entraîné `eval()`, neuf Xavier, aléatoire) · **graines de carte appariées**.
Chaque `.brain` lu depuis une **copie** (`p_*.brain`), jamais en place.

## Résultats

| Cerveau | bus | Maîtrise run | Banc | z | Directivité |
|---|---:|---:|---:|---:|---:|
| A_g155 | 145 | 45,0 % | 7,67 % | +0,98 | 18,08× |
| A_g122 | 137 | 35,0 % | 27,33 % | +7,15 | 16,33× |
| A_g166 | 132 | 25,0 % | 31,00 % | +8,02 | 16,42× |
| A_g66 | 158 | 30,0 % | **37,33 %** | +9,44 | 14,21× |
| aléatoire | | | **5,67 %** | | 20,17× |

Marcheur aléatoire mesuré séparément sur **600 épisodes** : 4,50 % IC95 [3,1 ; 6,5].

## ⚠️ Trois avertissements

1. **Le témoin « neuf » (Xavier) est INUTILISABLE** : un réseau non entraîné a un biais
   d'action arbitraire selon sa graine (42 % avancer / 70 % tourner / 87 % done). Scores
   observés : 4,33 · 5,67 · 7,00 · **22,67 %**. Le témoin fiable est l'**aléatoire**
   (17/300 sur les 4 runs).
2. **`n = 4`** — sous la barre des 20 graines. L'inversion `r(maîtrise, banc) = −0,89`
   n'est **pas** significative (`t = −2,72` contre 4,30).
3. **Deux versions du banc ont été jetées** (vecteur bio nul ; fuite de mémoire de travail
   + contexte épisodique nul). Tout chiffre antérieur aux correctifs est **caduc**.

## Fichiers

- `resultats.log` — sortie brute des 4 cerveaux
- les `p_*.brain` sont des **copies de travail**, supprimées après mesure ; les sources
  restent dans `brains/26082026_v4132_AB3_cursus/`, intactes.

---

> 🔴 **RÉSERVE D'INSTRUMENT — ajoutée le 01/09/2026.** Les chiffres de banc de ce document
> ont été produits par une sonde qui lisait la mémoire de travail au mauvais index
> (`penser()[1]`, la VALEUR, au lieu de `[4]`), un garde-fou la rejetant **en silence** :
> l'agent jouait **sans mémoire de travail ni contexte épisodique**. Re-mesuré sur `A_g66`,
> le succès passe de **37,33 % à 40,00 %** et la directivité de **14,21× à 14,92×**.
> Le **sens** des conclusions n'est pas inversé (l'aléatoire reste à 5,67 %, la compétence
> reste réelle), mais **les valeurs numériques sont à reprendre** et `r = −0,8225` est
> **non établie** tant que la cohorte n'est pas rejouée.
>
> ✅ **RÉSERVE LEVÉE le 02/09/2026 — cohorte rejouée, 20/20.** La directivité **survit mais
> s'affaiblit** : −0,8225 → **−0,6794** (`t` = −3,93, n=20), 46 % de la variance au lieu de
> 68 %, et elle **ne passe plus** le retrait des 4 extrêmes (−0,478, `t` = −2,04, NS). Le
> témoin aléatoire est **invariant** (5,67 % sur 20/20). Chiffres courants :
> `docs/recherche/campagnes/REJEU_02092026_la_directivite_survit_affaiblie.md`.
> Voir `docs/recherche/enquetes_closes/INSTRUMENT_01092026_la_memoire_du_banc.md`.
