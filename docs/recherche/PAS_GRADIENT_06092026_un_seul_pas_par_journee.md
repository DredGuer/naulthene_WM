# UN SEUL PAS DE GRADIENT PAR JOURNÉE — la mesure qui manquait

**Date** : 2026-09-06 · **Statut** : ✅ **MESURE DIRECTE** (lecture de code + comptage
SB3), aucune interprétation causale · coût : **zéro run**.

> Piste §3 du [PLAN_05092026](../ameliorations/PLAN_05092026_toutes_les_pistes_classees.md),
> classée 🟢 la plus haute et **non touchée** par les mesures de la nuit du 05→06/09.
> Ce document établit seulement **le fait**, pas son effet.

---

## 1. Le comptage

### Naulthène — 2 pas par nuit, dont 1 seul pour la politique

| Site | `optimizer.step()` | Ce que porte le gradient |
|---|---|---|
| `apprendre_journee` (`noyau.py:1954`) | 1 | JEPA + vocal + **acteur** + **critique** + entropie + distillation |
| `rever` (`noyau.py:2007`) | 1 | **JEPA seul** — vérifié : aucune `log_prob`, aucun avantage, aucune tête motrice dans `rever` |

**La politique reçoit donc exactement UN pas de gradient par journée de ~400 ticks.**
Sur une vie de 1500 jours : **1 500 pas** pour ~600 000 ticks vécus.

### PPO — 23 680 pas sur le même banc

Défauts SB3 mesurés (`n_steps` 2048, `batch_size` 64, `n_epochs` 10), sur les
**152 043 pas** du banc (le `tick_absolu` réel de A_g11 à 400 jours, v41.38) :

```
74 rollouts × 10 époques × 32 minibatches = 23 680 pas d'optimiseur
```

### L'écart

| | Pas de politique | Ticks vécus | **Pas par tick** |
|---|---|---|---|
| **PPO** | **23 680** | 152 043 | **0,1557** |
| **Naulthène** | **1 500** | ~600 000 | **0,0025** |

> **PPO fait 15,8× plus de pas de gradient sur 4× moins d'expérience — soit 63× plus de
> pas par tick vécu.**

## 2. Pourquoi ce fait n'avait jamais été relevé

Le dépôt a testé, à n=20, **tout ce qui entoure** ce pas de gradient :

| Testé | Verdict |
|---|---|
| le crédit temporel (MC / TD(0) / GAE) | MC est le moins mauvais |
| la normalisation des retours par épisode | **pire** (60 tirages sur 60) |
| le coefficient d'entropie | 0,44–1,05 % du gradient de l'avantage |
| le detach asymétrique (AB3) | `t` = −0,70 |
| la densité de la récompense | 86 % du signal est dense |
| le barème, la curiosité, le rendement mécanique | réfutés |

**Le NOMBRE de fois où ce gradient est appliqué n'a jamais été touché.** C'est un angle
mort, pas une piste écartée.

## 3. ⚠️ Ce que cette mesure NE dit PAS

1. **Elle n'établit aucun lien avec le plafond.** C'est un comptage, pas une expérience.
   Le dépôt a déjà réfuté 25 hypothèses séduisantes ; celle-ci n'a aucun statut supérieur
   tant qu'un A/B apparié n'a pas tourné.
2. **Plus de pas peut être PIRE.** Le policy gradient Monte-Carlo sans ratio d'importance
   **diverge** sur plusieurs époques — c'est précisément la raison d'être du clipping de
   PPO. Un bras « K époques » sans garde-fou pourrait dégrader la politique.
3. **Le rêve n'est pas inutile pour autant** : il fait un vrai pas de gradient JEPA, sur un
   lot rejoué par importance. Ce document dit seulement qu'il n'apprend **aucune action**.
4. **Un nombre d'époques est une constante posée.** Le projet interdit d'en figer une sans
   l'avoir d'abord mesurée (méthode v30.1 : mesurer le fixe, puis dériver).

## 4. Le test qui trancherait

**Trois bras** (patience et clipping sont couplés — règle §6.2), 20 graines appariées,
1500 jours :

| Bras | Contenu |
|---|---|
| **témoin** | le code actuel, 1 pas |
| **K=8 nu** | 8 pas de gradient sur la journée, sans ratio d'importance |
| **K=8 clippé** | 8 pas avec ratio d'importance clippé (le garde-fou de PPO) |

Coût : ~12 h (60 runs, 6 en parallèle). Témoin atteint : **compter les `step()` dans le
bilan de nuit**, avec assertion runtime (le drapeau doit mordre **dans le module**, bug
v41.4).

Juges : **J1 maîtrise** (`t` > 2,86, Bonferroni 3 métriques) et **J2 directivité**.
⚠️ Le juge « niveau » est **saturé** (40/40 au plafond du niveau 4) : il ne parlera qu'en
cas de franchissement.

---

*Mesure directe. Aucun run de cursus. À ne pas citer comme une cause du plafond.*
