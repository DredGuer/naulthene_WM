# `taux_satiete`, la variable morte — et le vrai régulateur du tube digestif

**Nature : ENQUÊTE** (`docs/recherche/`, non normatif). Découvert le 20/08/2026 pendant la
campagne v41.30, en cherchant pourquoi l'énergie ne bougeait pas entre les deux bras.

---

## 1. Le fait

`taux_satiete` **n'est soustrait nulle part**. Un seul drain de satiété existe dans
`step_metabolisme` (`noyau.py:3192`) :

```python
self.satiete -= conversion / max(RENDEMENT_CONVERSION, 1e-6)
```

Vérifié empiriquement — agent qui ne mange pas, action nulle, 10 ticks :

| grandeur | valeur |
|---|---|
| `taux_satiete` configuré | 0,001750/tick |
| **baisse réelle de satiété** | **0,083333** sur 10 ticks |
| attendu si `taux_satiete` prélevé | 0,017500 |
| attendu si **seule la digestion** | **0,083333** ✅ |

La v41.2 a remplacé le prélèvement direct par la digestion et `taux_satiete` est resté en
place **sans consommateur**. Il n'est plus lu que par le constructeur.

⚠️ **Un commentaire du code affirme le contraire** (`noyau.py:2991`) : *« `taux_satiete` et
`taux_hydratation` le prélèvent déjà à chaque tick »*. Cette phrase est **fausse depuis la
v41.2** et sert de justification à ne pas facturer le basal dans l'effort d'action. À
vérifier lors du chantier : le basal est-il facturé quelque part, ou nulle part ?

## 2. Ce que ça invalide — mon propre correctif v41.30-fix2

`_rafraichir_rythme_metabolique` règle `moteur.taux_satiete` chaque nuit à partir du rythme
vécu. **Cette écriture n'a aucun effet.** L'affirmation « le rythme vécu règle la vitesse de
vidange » — écrite dans le CHANGELOG, les deux README et CLAUDE.md — est **inexacte** : le
rythme ne règle plus rien du tout depuis fix2.

C'est une erreur de ma part : j'ai branché un levier sur un câble sectionné sans vérifier
qu'il était encore connecté. Le banc à n=3 n'a pas pu le détecter (il mesurait le régime de
démarrage, où la portion — elle bien active — dominait).

## 3. Le vrai régulateur : `DEBIT_DIGESTIF_JOUR`

```
DEBIT_DIGESTIF_JOUR = DEPENSE_ENERGIE_JOUR × MARGE_DIGESTIVE = 2.0 × 1.5 = 3.0
vidange réelle = DEBIT / RENDEMENT_CONVERSION = 3,333 estomacs/jour
```

**Cette vidange est identique dans les deux bras**, quel que soit le besoin :

| bras | apport max prévu | vidange réelle | solde |
|---|---|---|---|
| DERIVE (besoin 1,70/axe) | 1,360/jour | **3,333** | **−3,33** |
| FOSSILE (besoin 2,80/axe) | 2,240/jour | **3,333** | **−3,33** |

Le solde est **rigoureusement le même**. C'est l'explication arithmétique complète de
l'invariance énergétique mesurée : aucun réglage en amont sur le besoin ne peut atteindre les
jauges tant que la vanne est verrouillée en aval.

## 4. Le chiffre de terrain qui devient limpide

Mesuré sur la campagne : l'agent mange **5,4 fois/jour** (DERIVE) / **5,6** (FOSSILE) pour un
besoin théorique de 1,7 à 2,8 — et reste à une énergie de **0,22**.

Il ne manque pas d'efficacité motrice : il trouve et mange plus de 5 fois par jour. Son tube
digestif évacue simplement les calories à un rythme calibré pour une vie hyper-dépensière qui
n'est plus la sienne.

## 5. `DEPENSE_ENERGIE_JOUR = 2.0` — le même défaut que le `4.0`

Le commentaire du code le dit lui-même : *« CALIBRÉ PAR MESURE… balayage 1.0 → 3.0 **à 3
repas/jour** »*. C'est un calibrage juste **le jour où il a été fait**, exactement comme
`EPISODES_PAR_JOURNEE_REFERENCE = 4.0` valait `400 ticks / patience ~95`.

Le besoin dérivé vaut aujourd'hui **1,7 à 2,0**, pas 3. Et comme `DEBIT_DIGESTIF_JOUR` en
dérive, toute la tuyauterie hérite de ce régime périmé.

## 6. La portée sur le résultat C2 — un effet COGNITIF pur

Lecture de l'utilisateur, conservée parce qu'elle est méthodologiquement importante :

> Si l'énergie avait augmenté dans le bras DÉRIVÉ, on aurait pu soupçonner que C2 parlait plus
> fort simplement parce qu'il était « mieux nourri » (artefact de `force = acceptation ×
> vigueur`). Or l'énergie est restée strictement identique.

L'écart observé sur le ratio C2/C1 ne peut donc **pas** être un artefact métabolique : il
vient de l'élasticité de la patience rendue au potentiomètre (fin du plafond fossile).

⚠️ **MAIS voir §7 — cet écart n'a PAS tenu jusqu'à 1500 jours.**

## 7. ⚠️ RECTIFICATION — le SIG sur C2 était TRANSITOIRE

Mesure du ratio C2/C1 selon la fenêtre, mêmes graines, mêmes runs :

| fenêtre | écart | t | graines favorables | verdict |
|---|---|---|---|---|
| j622 | +0,191 | +2,08 | 5/5 | NS |
| **j1046** | **+0,378** | **+3,68** | **5/5** | **SIG** |
| **j1479** | +0,474 | **+1,93** | **3/5** | **NS** |

Détail à j1479 : g1 **+1,202** · g2 −0,035 · g3 +0,617 · g4 −0,116 · g5 +0,704.

L'écart MOYEN augmente (+0,378 → +0,474) mais la **dispersion explose** : deux graines
passent en négatif. Le `t = +3,68` lu à j1046 était donc une **fenêtre favorable**, pas un
effet stable.

> 🔴 **Leçon de méthode.** J'ai annoncé « premier résultat significatif de la campagne » à
> j1046 sur n=5. C'était prématuré à double titre : sous le seuil des 20 graines du projet,
> **et** sur une fenêtre choisie sans que le run soit terminé. Un `t` calculé sur un run en
> cours n'est pas une mesure — c'est un instantané qui peut se retourner. Ne plus annoncer de
> significativité avant la fin des runs.

## 8. Ce qu'il reste à faire — chantier v41.31

1. **Trancher le sort de `taux_satiete`** : le rebrancher (le rythme piloterait enfin la
   vidange) ou le supprimer (et corriger le commentaire faux de `noyau.py:2991`). Ne pas
   laisser une variable morte que le code semble utiliser.
2. **Indexer la vitesse de digestion sur la dépense RÉELLE** de l'agent plutôt que sur
   `DEPENSE_ENERGIE_JOUR = 2.0`, constante héritée d'un régime à 3 repas/jour.
3. **Vérifier où le basal est facturé** — le commentaire qui justifiait son absence dans
   l'effort d'action repose sur une prémisse fausse.

⚠️ **Rien de tout cela ne doit être codé pendant que la campagne v41.30 tourne** : modifier le
métabolisme invaliderait les 40 runs en cours.
