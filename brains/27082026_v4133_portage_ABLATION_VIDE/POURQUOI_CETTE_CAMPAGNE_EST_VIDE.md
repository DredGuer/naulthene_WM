# ⚠️ CAMPAGNE INEXPLOITABLE — ablation VIDE, pas négative

**Arrêtée le 27/08/2026 après 16 runs sur 40.** Conservée comme trace de l'erreur, jamais
supprimée (règle §7 : toujours archiver).

## Ce qui s'est passé

Le bit de portage a été mesuré sur un cursus complet. L'agent bloque au **niveau 4/15**
(`SimpleCrossingS9N1`). Or :

| Niveau | Env | Objet manipulable ? |
|---|---|---|
| 4 | `SimpleCrossingS9N1` | ❌ **aucun** |
| 6 | `Fetch-5x5-N2` | ✅ premier objet à ramasser |
| 8 | `DoorKey-5x5` | ✅ première clé |

**`🔑 Portage 0.0%` sur les 400 jours des 400 bilans.** La variable indépendante était
verrouillée à 0,0 dans LES DEUX BRAS.

Vérifié : `diff A_g11.log B_g11.log` ne retourne que le **nom du fichier**. Les deux bras
sont bit-identiques sur 18 192 lignes.

## L'erreur exacte

Le bit a été validé sur `DoorKey-6x6` — un environnement du **niveau 9** — où il varie
correctement (28,3 % des ticks à 1,0, accord 100 % avec `carrying`). Puis la campagne a
été lancée sur le **cursus complet**, où cet environnement n'est jamais atteint.

C'est le piège que la règle de mesure §4 décrit déjà, mot pour mot, pour la nociception
v41.25 : *« la lave n'apparaît qu'au niveau 5 et l'agent est bloqué au 4 […] une ablation
VIDE, pas négative »*. Reproduit à un niveau près, malgré la règle écrite.

## Ce que cela ne prouve PAS

**Le mécanisme n'est pas réfuté — il n'a pas été testé.** Aucune conclusion sur le bit de
portage ne peut être tirée de ces 16 runs.

## Le code, lui, est valide

Toutes les validations d'intégration ont passé et restent acquises :

| Test | Résultat |
|---|---|
| Contrat append-only | 1 dim sur 42 change, à l'indice 41 |
| Greffe 41→42 | `integrateur_bio` 186→187, acquis préservés (norme 5,691216) |
| Nuit complète post-greffe | 3 nuits, aucun crash |
| Le bit varie (sur DoorKey) | 28,3 % à 1,0, accord 100 % |
| Le témoin atteint le module | assertion runtime OK |

## La leçon à ajouter au protocole

**Avant tout A/B : vérifier que la variable indépendante VARIE dans le bras nominal.**
Une seule ligne de log l'aurait montré (`🔑 Portage 0.0%`). Ce contrôle doit précéder le
lancement, au même titre que le test A/A — il coûte un run de 5 jours.

Suite : `brains/27082026_v4133_portage_banc/` (banc forcé `DoorKey-6x6`).
