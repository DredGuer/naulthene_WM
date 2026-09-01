# Le banc de directivité — n=20 (31/08/2026)

Analyse : [DIRECTIVITE_31082026](../../docs/recherche/campagnes/DIRECTIVITE_31082026_le_goulot_est_moteur.md).

## Ce qu'on cherchait

`historique_episodes_niveau` — la maîtrise qui déclenche les promotions et à laquelle
dix-huit hypothèses ont été corrélées — mesure-t-elle la compétence réelle ?

**Réponse : partiellement.** `r = +0,3961` (`t = +1,83`, NS) — elle explique **16 %** de la
variance. Elle n'est pas inversée (la lecture du 30/08 à n=4 était un biais de sélection),
elle est **bruitée**.

**Et le vrai prédicteur est ailleurs** : `r(directivité, succès) = −0,8225` (`t = −5,96`),
**68 %** de la variance. Le goulot est **moteur**.

## Protocole

```bash
for n in $(cat liste16.txt); do
  WANDB_MODE=offline PYTHONPATH=src venv/bin/python \
    -m naulthene.instruments.sonde_plancher_geometrique \
    --brain "brains/30082026_plancher_n20/$n.brain" --episodes 300 \
    --json "brains/30082026_plancher_n20/res_$n.json"
done
```

- **20 cerveaux** (4 de la vague du 30/08 + 16) · `SimpleCrossingS9N1` · 300 épisodes
- **Graines de carte appariées** entre les 3 politiques et entre tous les cerveaux
- **Témoin aléatoire : 17/300 sur les 20 runs**, vérifié par assertion à chaque agrégation
- Chaque `.brain` lu depuis une **copie**, supprimée après mesure

### ⚠️ Échantillonnage — le point qui a tout changé

La vague du 30/08 (n=4) avait été choisie dans le **haut** de la distribution (25–45 %,
écart-type 7,4) et produisait `r = −0,89`, lu à tort comme une inversion. Les 16 suivants
ont été tirés **en partant des strates les plus rares** pour couvrir 0–45 % (écart-type
12,5). Le signe s'est inversé dès le 5ᵉ point.

## Fichiers

- `agregat.json` — les 20 points, **régénéré après le dernier run** (il était resté à n=14)
- `res_*.json` — un fichier par cerveau, avec maîtrise lue **dans le `.brain`**
- `run.log` — sortie brute (gitignoré ; tous les chiffres sont dans les JSON)

## ⚠️ Avertissements

1. **Deux versions du banc ont été jetées** avant celle-ci : vecteur bio nul (5 dimensions
   ont un neutre à **0,5**, pas 0) ; fuite de mémoire de travail entre épisodes + contexte
   épisodique nul. Tout chiffre antérieur est **caduc**.
2. **Le témoin « cerveau neuf » est inutilisable** : biais d'action arbitraire selon la
   graine Xavier (42 % avancer · 70 % tourner · 87 % done) → scores de 4,33 % à 22,67 %.
3. Les sources restent dans `brains/26082026_v4132_AB3_cursus/`, **jamais modifiées**.

---

> 🔴 **RÉSERVE D'INSTRUMENT — ajoutée le 01/09/2026.** Les chiffres de banc de ce document
> ont été produits par une sonde qui lisait la mémoire de travail au mauvais index
> (`penser()[1]`, la VALEUR, au lieu de `[4]`), un garde-fou la rejetant **en silence** :
> l'agent jouait **sans mémoire de travail ni contexte épisodique**. Re-mesuré sur `A_g66`,
> le succès passe de **37,33 % à 40,00 %** et la directivité de **14,21× à 14,92×**.
> Le **sens** des conclusions n'est pas inversé (l'aléatoire reste à 5,67 %, la compétence
> reste réelle), mais **les valeurs numériques sont à reprendre** et `r = −0,8225` est
> **non établie** tant que la cohorte n'est pas rejouée.
> Voir `docs/recherche/enquetes_closes/INSTRUMENT_01092026_la_memoire_du_banc.md`.
