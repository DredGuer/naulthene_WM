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
v41.2**.

> ✅ **VÉRIFIÉ le 20/08 — mais le BASAL EST BIEN FACTURÉ, ailleurs.** J'avais laissé ouverte
> la crainte qu'il ne le soit nulle part et que l'inaction soit « subventionnée ». Mesuré :
> un agent **totalement inactif, estomac vide**, perd **0,325000** d'énergie en 100 ticks —
> exactement `100 × (DEPENSE_ENERGIE_JOUR / 400) × METABOLISME_BASAL_PART`.
>
> Le basal est prélevé dans la **dépense énergétique**, pas dans la satiété :
> `depense = depense_energie × (BASAL + (1 − BASAL) × cout_action × vigueur)`.
> À `cout_action = 0`, l'agent paie donc **65 % du tarif plein** — l'inaction n'est pas gratuite.
>
> Conclusion : le commentaire est faux sur le **POURQUOI** (il invoque `taux_satiete`, mort),
> mais la **règle qu'il défend reste juste** — ne pas re-facturer le basal dans l'effort
> d'action, puisque `METABOLISME_BASAL_PART` s'en charge. Il faut corriger le texte, pas le
> comportement.

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

## 6bis. D'où vient la dispersion — hypothèse testée, partiellement confirmée

Hypothèse (utilisateur) : en fin de parcours les agents ne vivent plus les mêmes vies — les
graines qui franchissent un palier sollicitent C2 en permanence, celles restées sur un
plateau stabilisent un réflexe C1.

Testé sur les 5 graines, écart C2/C1 à j1479 :

| graine | niveau DERIVE | niveau FOSSILE | écart |
|---|---|---|---|
| g1 | **5** | 4 | **+1,202** |
| g3 | 4 | **5** | +0,617 |
| g5 | 4 | 4 | +0,704 |
| g2 | 4 | 4 | −0,035 |
| g4 | 4 | 4 | −0,116 |

Moyenne **avec** un niveau 5 : **+0,909** · **sans** : **+0,184**. La direction est la bonne.

⚠️ **Mais deux observations l'empêchent d'être une explication complète.** (1) g3 a son
niveau 5 **du côté FOSSILE** et son écart reste **positif** (+0,617) : si la profondeur du
cursus expliquait tout, il serait négatif. (2) g5 (+0,704) n'a **aucun** niveau 5 et devance
g3 qui en a un. La profondeur atteinte explique **une partie** de la dispersion, pas sa
totalité — n=5 ne permet pas d'aller plus loin.

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
3. **Corriger le commentaire de `noyau.py:2991`** — sa prémisse est fausse (`taux_satiete`
   est mort) mais sa conclusion est juste (`METABOLISME_BASAL_PART` facture bien le basal,
   vérifié : 0,325000 sur 100 ticks d'inaction). C'est le TEXTE qu'il faut réparer, pas le
   comportement. Aucune urgence fonctionnelle.

⚠️ **Rien de tout cela ne doit être codé pendant que la campagne v41.30 tourne** : modifier le
métabolisme invaliderait les 40 runs en cours.
