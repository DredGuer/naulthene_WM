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
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time

from naulthene.cerveau.telemetrie import BusTrames
from naulthene.instruments.cerveau_3d.factice import DIM_BUS_FICTIF, boucle_factice
from naulthene.instruments.cerveau_3d.serveur import EcouteurUDP, ServeurCerveau3D

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
                "Étape 2 (passerelle)    : --serveur-seul --udp 9998, puis un run qui émet\n"
                "                          vers udp:127.0.0.1:9998."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False)
    analyseur.add_argument("-h", "--aide", "--help", action="help",
                           help="affiche cette aide et sort")
    analyseur.add_argument("--source", choices=("factice", "cerveau"), default="factice",
                           help="qui produit les trames (défaut : factice)")
    analyseur.add_argument("--brain", default=None, metavar="CHEMIN",
                           help="le `.brain` EXISTANT à observer (obligatoire en mode « cerveau » ; "
                                "un cerveau absent est refusé, jamais fait naître)")
    analyseur.add_argument("--port", type=int, default=PORT_DEFAUT,
                           help=f"port d'écoute HTTP (défaut : {PORT_DEFAUT} ; 0 = port libre)")
    analyseur.add_argument("--hz", type=float, default=HZ_DEFAUT, metavar="CADENCE",
                           help=f"cadence de PUBLICATION des trames (défaut : {HZ_DEFAUT} ; le tick "
                                f"du cerveau n'est jamais ralenti par l'affichage)")
    analyseur.add_argument("--udp", type=int, default=None, metavar="PORT",
                           help="écoute aussi les trames émises en UDP sur ce port (étape 2)")
    analyseur.add_argument("--serveur-seul", action="store_true",
                           help="ne produit AUCUNE trame locale : sert la page et reçoit l'UDP")
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


def _cible_factice(bus, options, arret):
    """La source factice dans son fil, avec un échec VISIBLE.

    ⚠️ Une exception dans un fil meurt en silence : la page resterait figée sur une dernière
    image, ce qui est indiscernable d'un cerveau lent — exactement ce que la télémétrie refuse
    par ailleurs (spec §9 : un état inattendu est MONTRÉ, jamais corrigé en silence).
    `boucle_factice` est écrite pour ne jamais lever, mais « écrite pour » n'est pas « garanti ».
    """
    def cible():
        try:
            boucle_factice(bus, hz=options.hz, dim_bus=DIM_BUS_FICTIF, arret=arret,
                           duree=options.duree)
        except Exception as erreur:              # noqa: BLE001 — l'échec est RECOPIÉ à l'écran
            print(f"⚠️  la source factice s'est arrêtée sur une erreur : {erreur!r}",
                  file=sys.stderr, flush=True)
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


def _afficher_banniere(options, port, hote, ecouteur) -> None:
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
    if options.source == "cerveau" and not options.serveur_seul:
        print(f"   cadence    : publication à {options.hz:g} Hz (le tick du cerveau, lui, n'est "
              f"jamais ralenti)", flush=True)
    print(f"   {garantie}", flush=True)
    print(f"   → ouvrez http://{hote}:{port} dans un navigateur (Ctrl-C pour arrêter).",
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
    if options.hz <= 0.0:
        raise SystemExit(f"--hz invalide : {options.hz!r} (attendu > 0)")

    bus = BusTrames()
    arret = threading.Event()
    serveur, ecouteur, fil_source = None, None, None
    issue = {}                       # {"resultat": …} ou {"erreur": …} — le tableau de bord
    try:
        # Le serveur est monté en premier (`port=0` ⇒ le port réel est connu avant d'annoncer
        # l'URL) : la bannière ne doit jamais afficher un port qu'on n'écoute pas.
        serveur = ServeurCerveau3D(bus, port=options.port)
        if options.udp is not None:
            # L'écouteur est un CHOIX explicite (`--udp`) : un port occupé lève ici, au
            # démarrage, jamais en silence au milieu d'un run.
            ecouteur = EcouteurUDP(bus, port=options.udp)
            ecouteur.demarrer_en_thread()
        serveur.demarrer_en_thread()

        if not options.serveur_seul:
            if options.source == "cerveau":
                cible, nom_du_fil = _cible_cerveau(jouer_cerveau, bus, options, arret, issue), \
                    "spectateur-cerveau"
            else:
                cible, nom_du_fil = _cible_factice(bus, options, arret), "source-factice"
            fil_source = threading.Thread(target=cible, name=nom_du_fil, daemon=True)
            fil_source.start()

        _afficher_banniere(options, serveur.port, serveur.hote, ecouteur)

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
        if serveur is not None:
            serveur.arreter()
        _afficher_empreinte(issue)


if __name__ == "__main__":
    raise SystemExit(main())
