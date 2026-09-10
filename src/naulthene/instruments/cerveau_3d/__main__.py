# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
VIS-01 — la CLI du cerveau 3D : le point d'entrée de l'instrument.

    PYTHONPATH=src venv/bin/python3 -m naulthene.instruments.cerveau_3d --source factice
    PYTHONPATH=src venv/bin/python3 -m naulthene.instruments.cerveau_3d \\
        --source cerveau --brain brains/<campagne>/<cerveau>.brain

⚠️ Aucune source n'est chargée ICI : `__main__` ne fait que choisir une source, monter le
`BusTrames`, réutiliser le serveur de la tâche 5 (**un seul** serveur, jamais un second) et
afficher ce qu'on regarde.

⚠️ IMPORT PARESSEUX du mode `cerveau`. `naulthene.instruments.cerveau_3d.spectateur` (donc `torch`
et `noyau`) n'est importé QUE dans la branche du mode `cerveau`, à l'intérieur de `main`. Le mode
`factice` doit continuer de s'ouvrir sur une machine qui n'a **pas** de cerveau : c'est la promesse
de l'étape 0, et elle est figée par
`tests/test_cerveau_3d.py::TestCliModeCerveau::test_le_mode_factice_de_la_cli_ne_charge_toujours_pas_torch`.
L'import se fait quand même **avant** de lier le port : un `cerveau` qui ne peut pas charger son
moteur doit échouer NET, pas après avoir annoncé une URL.

⚠️ LECTURE SEULE, promesse du chantier (spec §8) : en mode `factice` (ou `--serveur-seul`) ce
processus ne charge aucun cerveau — il n'écrit donc rien et n'entraîne rien, la bannière le dit à
l'écran. En mode `cerveau`, la garantie est plus étroite et se dit autrement (`GARANTIE_CERVEAU`) :
**le FICHIER `.brain` n'est jamais ouvert en écriture**, mais le cerveau vit (`traiter_tick` grave
la LTP d'un pic de dopamine en mémoire) — voir la docstring de `spectateur.py`, et l'empreinte
SHA-256 imprimée à l'arrêt. Une garantie qu'il faut lire dans le code n'est pas une garantie.

⚠️ ÉTAPE 2 COMPLÈTE (tâche 11) : la trame `structure` (305 Ko) ne peut pas passer par UDP (plafond
dur de 65 507 octets), le run l'écrit donc dans `<brain>.vis01_structure.json`. `--structure-fichier
CHEMIN` fait relire ce fichier au serveur — au démarrage, puis à chaque changement — et le publie
dans le bus, sans quoi la page restait sur « en attente de la structure… » pendant qu'`activite` et
`evenement`, eux, arrivaient bien par UDP. L'option exige `--serveur-seul` : une source locale
publie déjà sa propre structure, et deux publieurs feraient clignoter la scène sans rien dire.

⚠️ LES REFUS SONT SYMÉTRIQUES (correction du 10/09/2026, vague finale, constat I6). Deux
combinaisons d'options étaient acceptées puis IGNORÉES EN SILENCE, c'est-à-dire qu'elles faisaient
montrer à la page autre chose que ce que l'auteur croyait regarder — les deux sont corrigées :

| Combinaison | Ce qui se passait | Correction |
|---|---|---|
| `--source factice --brain X` | le chemin était accepté puis jamais ouvert (l'aide de `--brain` annonçait « le `.brain` EXISTANT à observer » sans dire que le mode factice ne le lisait pas) | refus explicite dans `main`, avant de lier un port |
| une source `factice` qui meurt sur une exception | l'erreur était imprimée sur `stderr` mais le tableau de bord `issue` restait vide, donc la CLI rendait **0** | `issue["erreur"]` posé par `_cible_factice`, donc sortie ≠ 0 — le mode factice est désormais aussi strict que le mode `cerveau` |

Voir `tests/test_cerveau_3d.py::TestCliModeCerveau`.
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time

from naulthene.cerveau.telemetrie import BusTrames
from naulthene.instruments.cerveau_3d.factice import DIM_BUS_FICTIF, boucle_factice
from naulthene.instruments.cerveau_3d.serveur import (EcouteurUDP, ServeurCerveau3D,
                                                      VeilleurStructureFichier)

PORT_DEFAUT = 8770
HZ_DEFAUT = 15.0

GARANTIE_LECTURE_SEULE = ("⚠️  lecture seule : ce processus n'écrit aucun .brain et n'entraîne "
                          "rien.")

# La garantie du mode `cerveau` — plus étroite, et EXACTE. Elle ne dit pas « aucun poids modifié »
# (faux : `traiter_tick` → `fortifier_synapses` écrit en place dans `base_weight`/`myeline_M`, sans
# `backward()` et sans que `eval()` l'arrête) ; elle dit ce qui est vrai et vérifiable : le FICHIER
# n'est jamais ouvert en écriture.
GARANTIE_CERVEAU = ("⚠️  lecture seule du FICHIER : le `.brain` n'est jamais ouvert en écriture "
                    "(aucune sauvegarde, aucune nuit) — son empreinte SHA-256 est vérifiée avant/"
                    "après et imprimée à l'arrêt. ⚠️ En MÉMOIRE seulement, `traiter_tick` grave la "
                    "LTP d'un pic de dopamine (`fortifier_synapses`, en place, sans `backward()`) : "
                    "cette écriture ne repart jamais sur le disque.")


def construire_analyseur() -> argparse.ArgumentParser:
    """Les options du contrat (plan, tâche 6) — et rien de plus.

    ⚠️ `add_help=False` puis `-h/--aide/--help` déclarés à la main : le plan exige que la CLI
    RÉPONDE à `--aide` (français, comme le reste du dépôt), ce qu'argparse ne fournit pas seul.
    """
    analyseur = argparse.ArgumentParser(
        prog="python -m naulthene.instruments.cerveau_3d",
        description="VIS-01 — le cerveau 3D : une IRM vivante, en LECTURE SEULE.",
        epilog=("Étape 0 (démonstration) : --source factice, aucun cerveau chargé.\n"
                "Étape 1 (spectateur)    : --source cerveau --brain <chemin>, un VRAI .brain qui vit.\n"
                "Étape 2 (passerelle)    : --serveur-seul --udp 9998 --structure-fichier\n"
                "                          <brain>.vis01_structure.json, puis un run qui émet vers\n"
                "                          udp:127.0.0.1:9998 (l'activité par UDP, la structure par\n"
                "                          le fichier : 305 Ko ne passent pas dans un datagramme)."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False)
    analyseur.add_argument("-h", "--aide", "--help", action="help",
                           help="affiche cette aide et sort")
    analyseur.add_argument("--source", choices=("factice", "cerveau"), default="factice",
                           help="qui produit les trames (défaut : factice)")
    analyseur.add_argument("--brain", default=None, metavar="CHEMIN",
                           help="le `.brain` EXISTANT à observer (obligatoire en mode « cerveau » ; "
                                "un cerveau absent est refusé, jamais fait naître). ⚠️ Refusé "
                                "avec « --source factice » : la source synthétique n'ouvre aucun "
                                "`.brain`, et l'ignorer en silence ferait passer une forme "
                                "inventée pour un vrai cerveau")
    analyseur.add_argument("--port", type=int, default=PORT_DEFAUT,
                           help=f"port d'écoute HTTP (défaut : {PORT_DEFAUT} ; 0 = port libre)")
    analyseur.add_argument("--hz", type=float, default=HZ_DEFAUT, metavar="CADENCE",
                           help=f"cadence de PUBLICATION des trames (défaut : {HZ_DEFAUT} ; le tick "
                                f"du cerveau n'est jamais ralenti par l'affichage)")
    analyseur.add_argument("--udp", type=int, default=None, metavar="PORT",
                           help="écoute aussi les trames émises en UDP sur ce port (étape 2)")
    analyseur.add_argument("--serveur-seul", action="store_true",
                           help="ne produit AUCUNE trame locale : sert la page et reçoit l'UDP")
    analyseur.add_argument("--structure-fichier", default=None, metavar="CHEMIN",
                           help="le fichier où un run écrit sa trame `structure` "
                                "(<brain>.vis01_structure.json) : relu et publié au démarrage puis à "
                                "chaque changement — exigé par l'étape 2, la trame étant trop "
                                "grosse pour un datagramme UDP (à utiliser avec --serveur-seul)")
    analyseur.add_argument("--duree", type=float, default=None, metavar="SECONDES",
                           help="s'arrête tout seul après ce délai (défaut : jusqu'à Ctrl-C)")
    return analyseur


def _verifier_mode_cerveau(options) -> None:
    """Les refus du mode `cerveau` — AVANT de lier un port, d'importer `torch` ou d'ouvrir un
    fichier : un refus ne doit rien laisser derrière lui.

    Trois refus, et chacun dit POURQUOI (un « non » sans raison oblige à lire le code) :

    1. `--brain` manquant : la CLI ne devine pas un cerveau par défaut. Il n'en existe aucun
       « standard » dans ce dépôt (chaque campagne a son dossier), et en choisir un ferait observer
       à l'auteur autre chose que ce qu'il croit.
    2. `--brain` introuvable : `PersistanceAnatomique.charger_ou_naitre()` ferait NAÎTRE un cerveau
       neuf à cet emplacement (et ne l'écrirait même pas — le spectateur afficherait alors un
       cerveau de démonstration). Un spectateur ne crée jamais de fichier : on refuse, et on dit
       comment obtenir un vrai cerveau.
    3. `--serveur-seul` : nier la source locale ET demander un cerveau est contradictoire. Sans ce
       refus, `--brain X` serait ignoré en silence et l'écran resterait vide — un silence qui a
       l'air d'un cerveau lent.

    ⚠️ Les deux derniers sont SYMÉTRIQUES de deux refus du mode `factice` (constat I6, vague
    finale) : `--source factice --brain X` est refusé dans `main` pour la même raison, et une
    source factice qui meurt fait désormais sortir la CLI en erreur.
    """
    if options.serveur_seul:
        raise SystemExit(
            "--source cerveau et --serveur-seul sont contradictoires : --serveur-seul ne produit "
            "AUCUNE trame locale, donc le cerveau demandé ne serait jamais chargé (et la page "
            "resterait vide, ce qui est indiscernable d'un cerveau lent). Choisissez : "
            "« --source cerveau --brain CHEMIN » pour observer un .brain ici, ou "
            "« --serveur-seul --udp PORT » pour recevoir les trames d'un run (étape 2).")
    if not options.brain:
        raise SystemExit(
            "--source cerveau exige --brain CHEMIN : aucun cerveau n'a été chargé et le serveur "
            "n'a pas été monté. Exemple : "
            "--source cerveau --brain brains/08092026_sci01_balayage_K/K4_NU/K4_NU_g11.brain")
    if not os.path.isfile(options.brain):
        raise SystemExit(
            f"--brain {options.brain} est introuvable : rien n'a été chargé et AUCUN fichier n'a "
            f"été créé (un spectateur ne fait jamais naître un cerveau). Pour en obtenir un : "
            f"PYTHONPATH=src venv/bin/python3 -m naulthene.cerveau.noyau --jours 1 "
            f"--brain {options.brain}")


def _cible_factice(bus, options, arret, issue):
    """La source factice dans son fil, avec un échec VISIBLE — ET COMPTÉ COMME UN ÉCHEC.

    ⚠️ Une exception dans un fil meurt en silence : la page resterait figée sur une dernière
    image, ce qui est indiscernable d'un cerveau lent — exactement ce que la télémétrie refuse
    par ailleurs (spec §9 : un état inattendu est MONTRÉ, jamais corrigé en silence).
    `boucle_factice` est écrite pour ne jamais lever, mais « écrite pour » n'est pas « garanti ».

    🔴 CORRECTION DU 10/09/2026 (vague finale, constat I6) — `issue["erreur"]` est posé ICI.
    L'ancienne version armait `arret` en imprimant sur `stderr`, mais **ne posait pas
    `issue["erreur"]`** : le tableau de bord restait vide, donc `main` rendait **0** sur une
    source morte (`return 1 if isinstance(issue.get("erreur"), BaseException) else 0`). Un script
    qui teste la CLI, ou un `--duree` lancé dans un `&&`, lisait un succès là où la démonstration
    n'avait rien montré — le mode d'échec que la branche `cerveau` refusait déjà. La règle est
    donc rendue SYMÉTRIQUE : mourir est un échec dans les deux modes.
    """
    def cible():
        try:
            boucle_factice(bus, hz=options.hz, dim_bus=DIM_BUS_FICTIF, arret=arret,
                           duree=options.duree)
        except Exception as erreur:              # noqa: BLE001 — l'échec est RECOPIÉ à l'écran
            print(f"⚠️  la source factice s'est arrêtée sur une erreur : {erreur!r}",
                  file=sys.stderr, flush=True)
            issue["erreur"] = erreur
            arret.set()
    return cible


def _cible_cerveau(jouer_cerveau, bus, options, arret, issue):
    """Le spectateur-pilote dans son fil — même discipline d'échec VISIBLE que `_cible_factice`.

    `issue` est le tableau de bord du mode : `{"resultat": …}` en cas de succès, `{"erreur": …}`
    sinon. `main` s'en sert pour deux choses que le fil ne peut pas faire lui-même : rendre un
    code de sortie ≠ 0 quand le cerveau n'a pas pu être observé, et imprimer l'empreinte.
    """
    def cible():
        try:
            issue["resultat"] = jouer_cerveau(bus, options.brain, arret=arret,
                                              duree=options.duree, hz=options.hz)
        except Exception as erreur:              # noqa: BLE001 — l'échec est RECOPIÉ à l'écran
            print(f"⚠️  le spectateur s'est arrêté sur une erreur : {erreur!r}",
                  file=sys.stderr, flush=True)
            print("   ⚠️  aucune trame d'activité ne sera publiée, et AUCUN `.brain` n'a été "
                  "écrit.", file=sys.stderr, flush=True)
            issue["erreur"] = erreur
            arret.set()
    return cible


def _etat_structure_fichier(veilleur, bus) -> str:
    """Ce que la veille du fichier de structure peut dire MAINTENANT — une ligne, deux cas.

    ⚠️ Elle est écrite pour le cas PÉNIBLE, pas pour le cas nominal : un fichier absent, un chemin
    qui n'est pas un fichier, un JSON qui n'est pas une trame — la page, elle, restera sur « en
    attente de la structure… », et sans cette ligne ce silence serait indiscernable d'un run lent
    (spec §9 : un état inattendu est MONTRÉ). Le compteur d'absences est celui de la veille : il
    compte les TOURS, donc la durée de l'attente autant que son existence.
    """
    compteurs = veilleur.compteurs()
    trame = bus.structure()
    if trame is not None:
        return (f"{compteurs['chemin']} — structure chargée : "
                f"{len(trame.get('couches', []))} couche(s), dim_bus = {trame.get('dim_bus', '?')} "
                f"(relue à chaque changement, {compteurs['publications']} publication(s))")
    detail = (f"{compteurs['absences']} absence(s), {compteurs['illisibles']} illisible(s), "
              f"{compteurs['invalides']} invalide(s)")
    if compteurs["derniere_erreur"]:
        detail = f"{detail} — {compteurs['derniere_erreur']}"
    return (f"⚠️  {compteurs['chemin']} — AUCUNE structure lue ({detail}) : la page restera sur "
            f"« en attente de la structure… » jusqu'à ce qu'un run écrive ce fichier.")


def _afficher_banniere(options, port, hote, ecouteur, veilleur=None, bus=None) -> None:
    """Ce qu'on regarde, où, et la garantie de lecture seule (ruling : lisible au lancement)."""
    if options.serveur_seul:
        source = "serveur seul — aucune trame produite ici"
        if ecouteur is not None:
            source = f"serveur seul — trames reçues en UDP sur le port {ecouteur.port}"
        garantie = GARANTIE_LECTURE_SEULE
    elif options.source == "cerveau":
        source = f"cerveau RÉEL — {options.brain}"
        garantie = GARANTIE_CERVEAU
    else:
        source = f"factice (dim_bus fictif = {DIM_BUS_FICTIF})"
        garantie = GARANTIE_LECTURE_SEULE
    print("🧠 Cerveau 3D — VIS-01", flush=True)
    print(f"   source     : {source}", flush=True)
    print(f"   serveur    : http://{hote}:{port}", flush=True)
    if veilleur is not None:
        print(f"   structure  : {_etat_structure_fichier(veilleur, bus)}", flush=True)
    if options.source == "cerveau" and not options.serveur_seul:
        print(f"   cadence    : publication à {options.hz:g} Hz (le tick du cerveau, lui, n'est "
              f"jamais ralenti)", flush=True)
    print(f"   {garantie}", flush=True)
    print(f"   → ouvrez http://{hote}:{port} dans un navigateur (Ctrl-C pour arrêter).",
          flush=True)


def _afficher_bilan_structure(veilleur) -> None:
    """Le bilan de la veille, À L'ARRÊT — « ignoré, compté » doit se lire, pas se croire.

    Trois compteurs d'échec, et le compte des publications est le seul témoin que la page a VU
    quelque chose : `0 publication` sur un serveur qu'on croyait branché est le diagnostic, pas le
    détail.
    """
    compteurs = veilleur.compteurs()
    print(f"📡 structure : {compteurs['publications']} publication(s) depuis "
          f"{compteurs['chemin']} — {compteurs['absences']} absence(s), "
          f"{compteurs['illisibles']} illisible(s), {compteurs['invalides']} invalide(s).",
          flush=True)


def _afficher_empreinte(issue) -> None:
    """La preuve de lecture seule, À L'ÉCRAN — pas seulement dans le fichier de test.

    C'est la seule preuve que l'auteur puisse lire sans instrument : deux empreintes égales, et le
    nombre de ticks qui les sépare. Une empreinte DIFFÉRENTE est un défaut du spectateur, pas une
    observation : elle est criée sur `stderr`, et le chemin `--duree` sort alors en erreur
    (code ≠ 0). Sur le chemin Ctrl-C, l'arrêt demandé garde le code 0 — c'est l'arrêt qui est
    signalé, pas l'observation — mais le verdict, lui, est imprimé dans les deux cas.

    ⚠️ Le nombre annoncé comme « ticks observés » est `ticks_observes` (la SESSION), jamais
    `tick_absolu` (la VIE du cerveau, restaurée du `.brain` : 537 329 au chargement de
    `K4_NU_g11.brain`). Les confondre a produit un premier verdict qui annonçait « 538 834 ticks
    observés » après quatre secondes — mesuré, corrigé, et figé par le test de la tâche 8. Le
    compteur de vie reste affiché, mais nommé pour ce qu'il est.

    ⚠️ La SECONDE preuve (§10, « le cerveau observé ne dérive pas ») est imprimée ici aussi : les
    deux empreintes prouvent le FICHIER, elles ne disent RIEN de la mémoire où `traiter_tick` grave
    la LTP. Les normes de `base_weight` et de `myeline_M`, elles, la disent. Un écart y est
    **signalé sans changer le code de sortie** : sur un `.brain` sauvegardé en pleine journée
    (micro-sieste de la Cuve) la dérive est ATTENDUE — `trace_activation` y est non nulle — et
    déclarer en échec l'observation d'un cerveau vivant serait un mensonge de plus. Le verdict dit
    donc ce qu'il voit et à quoi s'attendre, il ne juge pas.
    """
    resultat = issue.get("resultat")
    if not isinstance(resultat, dict):
        return
    avant, apres = resultat["brain_sha256_avant"], resultat["brain_sha256_apres"]
    if avant == apres:
        print(f"🔒 empreinte du `.brain` : sha256 {avant} — inchangée après "
              f"{resultat['ticks_observes']} ticks observés (tick absolu du cerveau : "
              f"{resultat['tick_absolu']}) : fichier BIT-IDENTIQUE, aucune écriture sur le "
              f"disque.", flush=True)
    else:
        print(f"⚠️  LE FICHIER `.brain` A CHANGÉ : sha256 {avant} → {apres}. C'est un défaut du "
              f"spectateur (une sauvegarde a été ajoutée ?), pas une observation — le rapport est "
              f"invalide.", file=sys.stderr, flush=True)

    # `:.17g` et non `:.15e` : 17 chiffres significatifs sont ce qu'il faut pour qu'un `float64`
    # fasse l'aller-retour. À 15, deux normes séparées par un écart au 17ᵉ chiffre s'afficheraient
    # ÉGALES alors que le verdict, lui, les dit différentes — un affichage qui contredit le verdict
    # est pire qu'un affichage illisible.
    poids = " · ".join(f"{nom} {resultat[f'{nom}_norme_avant']:.17g} → "
                       f"{resultat[f'{nom}_norme_apres']:.17g}"
                       for nom in ("base_weight", "myeline_M"))
    if (resultat["base_weight_norme_avant"] == resultat["base_weight_norme_apres"]
            and resultat["myeline_M_norme_avant"] == resultat["myeline_M_norme_apres"]):
        print(f"🔒 normes des poids (mémoire) : {poids} — ÉGALES AU BIT après "
              f"{resultat['ticks_observes']} ticks : le cerveau observé n'a pas dérivé.",
              flush=True)
    else:
        print(f"⚠️  LES NORMES DE POIDS ONT CHANGÉ (mémoire) : {poids}. C'est la LTP d'un pic de "
              f"dopamine (`fortifier_synapses`, en place) : ATTENDUE sur un `.brain` sauvegardé en "
              f"pleine journée (trace d'éligibilité non nulle), INATTENDUE sur un `.brain` "
              f"sauvegardé après une nuit (`cycle_sommeil` remet `annexe_weight` ET "
              f"`trace_activation` à zéro). Le FICHIER, lui, est intact : rien n'est reparti sur le "
              f"disque.", file=sys.stderr, flush=True)


def main(argv=None) -> int:
    options = construire_analyseur().parse_args(argv)

    # Le mode `cerveau` : tous les refus AVANT de lier un port ou d'importer `torch` — un refus ne
    # doit rien laisser derrière lui, et une erreur de moteur doit sortir en erreur, pas après
    # avoir annoncé une URL.
    jouer_cerveau = None
    if options.source == "cerveau":
        _verifier_mode_cerveau(options)
        try:
            from naulthene.instruments.cerveau_3d.spectateur import jouer_cerveau
        except Exception as erreur:               # noqa: BLE001 — le refus est RECOPIÉ à l'écran
            raise SystemExit(f"--source cerveau exige le moteur du cerveau (torch, noyau) : "
                             f"{erreur!r}")
    elif options.brain:
        # 🔴 CORRECTION DU 10/09/2026 (vague finale, constat I6) — le refus SYMÉTRIQUE.
        # L'ancienne version acceptait `--source factice --brain X` puis **ignorait `--brain` en
        # silence** : `_verifier_mode_cerveau` n'est appelé que pour `--source cerveau`, et rien
        # n'était dit. L'auteur croyait donc regarder SON cerveau alors que la page montrait la
        # source synthétique — un mensonge par omission du même genre que ceux que la spec §9
        # interdit, et d'autant plus coûteux qu'un `.brain` de 1500 jours ne se distingue pas à
        # l'œil d'une sinusoïde bien réglée. On REFUSE au lieu d'avertir : un avertissement noyé
        # dans une bannière de sept lignes ne se lit pas, et le coût du refus est nul (il tombe
        # avant de lier un port, d'importer `torch` ou d'ouvrir un fichier).
        # ⚠️ DEUX configurations rendent `--brain` inerte, et le message dit LAQUELLE est la
        # bonne : un refus qui se trompe de cause oblige à relire le code (le refus est un
        # diagnostic, pas seulement un « non »).
        if options.serveur_seul:
            cause = ("--serveur-seul ne produit AUCUNE trame locale : ce cerveau ne serait "
                     "jamais chargé")
            remede = (f"« --source cerveau --brain {options.brain} » pour l'observer ici (sans "
                      f"--serveur-seul), ou « --serveur-seul --udp PORT » pour recevoir les "
                      f"trames d'un run (étape 2)")
        else:
            cause = ("--source factice est SYNTHÉTIQUE, elle n'ouvre aucun `.brain` : la page "
                     "montrerait une forme inventée, indiscernable d'un vrai cerveau")
            remede = (f"« --source cerveau --brain {options.brain} » pour observer ce fichier, ou "
                      f"« --source factice » seul pour la démonstration sans cerveau")
        raise SystemExit(
            f"--brain {options.brain} serait ignoré en silence : {cause}. C'est exactement le "
            f"mode d'échec que la spec §9 refuse (un silence qui a l'air d'un cerveau lent). "
            f"Choisissez : {remede}.")
    if options.hz <= 0.0:
        raise SystemExit(f"--hz invalide : {options.hz!r} (attendu > 0)")
    if options.structure_fichier and not options.serveur_seul:
        # Le refus est ici, AVANT de lier un port : une source locale publie DÉJÀ sa propre
        # structure, et deux publieurs feraient clignoter la scène (une relecture du fichier
        # écraserait la structure locale, et réciproquement) sans que rien à l'écran ne le dise.
        # Le fichier de structure est la moitié « étape 2 » de l'avenant : il vient d'un run
        # EXTÉRIEUR, donc d'un serveur qui n'en produit aucune.
        raise SystemExit(
            f"--structure-fichier {options.structure_fichier} exige --serveur-seul : ce fichier "
            f"est écrit par un run EXTERNE, et la source locale choisie ici publie déjà sa propre "
            f"structure — deux publieurs feraient clignoter la scène à chaque relecture. Pour "
            f"observer un run qui tourne ailleurs : « --serveur-seul --udp 9998 "
            f"--structure-fichier {options.structure_fichier} ».")

    bus = BusTrames()
    arret = threading.Event()
    serveur, ecouteur, veilleur, fil_source = None, None, None, None
    issue = {}                       # {"resultat": …} ou {"erreur": …} — le tableau de bord
    try:
        if options.structure_fichier:
            # Construit AVANT le serveur (qui n'en fait que l'OBSERVER pour `/sante`) et démarré
            # juste après lui : au retour de `demarrer_en_thread`, la structure déjà présente sur
            # le disque est publiée, donc la bannière et la première connexion la voient.
            veilleur = VeilleurStructureFichier(bus, options.structure_fichier)
        # Le serveur est monté en premier (`port=0` ⇒ le port réel est connu avant d'annoncer
        # l'URL) : la bannière ne doit jamais afficher un port qu'on n'écoute pas.
        serveur = ServeurCerveau3D(bus, port=options.port, veilleur_structure=veilleur)
        if options.udp is not None:
            # L'écouteur est un CHOIX explicite (`--udp`) : un port occupé lève ici, au
            # démarrage, jamais en silence au milieu d'un run.
            ecouteur = EcouteurUDP(bus, port=options.udp)
            ecouteur.demarrer_en_thread()
        serveur.demarrer_en_thread()
        if veilleur is not None:
            veilleur.demarrer_en_thread()

        if not options.serveur_seul:
            if options.source == "cerveau":
                cible, nom_du_fil = _cible_cerveau(jouer_cerveau, bus, options, arret, issue), \
                    "spectateur-cerveau"
            else:
                cible, nom_du_fil = _cible_factice(bus, options, arret, issue), "source-factice"
            fil_source = threading.Thread(target=cible, name=nom_du_fil, daemon=True)
            fil_source.start()

        _afficher_banniere(options, serveur.port, serveur.hote, ecouteur, veilleur, bus)

        if options.duree is not None:
            # Borné : on attend la fin de la source (ou le délai, s'il n'y en a pas), puis on
            # rend la main — c'est ce qui rend la CLI vérifiable sans navigateur ni Ctrl-C.
            if fil_source is not None:
                fil_source.join()
            else:
                time.sleep(max(0.0, float(options.duree)))
            # Un cerveau qui n'a pas pu être observé n'est PAS un succès : la CLI sort en erreur.
            return 1 if isinstance(issue.get("erreur"), BaseException) else 0

        while True:                      # jusqu'à Ctrl-C
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n⏹  arrêt demandé — fermeture du serveur.", flush=True)
        return 0
    finally:
        arret.set()
        if fil_source is not None:
            fil_source.join(timeout=2.0)
        if ecouteur is not None:
            ecouteur.arreter()
        if veilleur is not None:
            # Arrêté AVANT le serveur : plus personne ne publie dans le bus pendant que le
            # serveur ferme (le dernier tour de veille ne doit pas allonger l'arrêt).
            veilleur.arreter()
        if serveur is not None:
            serveur.arreter()
        _afficher_empreinte(issue)
        if veilleur is not None:
            _afficher_bilan_structure(veilleur)


if __name__ == "__main__":
    raise SystemExit(main())
