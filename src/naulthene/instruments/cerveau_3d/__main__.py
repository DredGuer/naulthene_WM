# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
VIS-01 — la CLI du cerveau 3D : le point d'entrée de l'instrument.

    PYTHONPATH=src venv/bin/python3 -m naulthene.instruments.cerveau_3d --source factice

⚠️ Aucune source n'est chargée ICI : `__main__` ne fait que choisir une source, monter le
`BusTrames`, réutiliser le serveur de la tâche 5 (**un seul** serveur, jamais un second) et
afficher ce qu'on regarde. Le mode `factice` n'importe ni `torch` ni `noyau` : la démonstration
de l'étape 0 doit s'ouvrir sur une machine qui n'a pas de cerveau.

⚠️ LECTURE SEULE, promesse du chantier (spec §8) : ce processus n'écrit aucun `.brain`, ne
charge aucun agent pour le mode `factice` et n'entraîne rien. La bannière le dit à l'écran, et
pas seulement dans ce fichier — une garantie qu'il faut lire dans le code n'est pas une garantie.

⚠️ Le mode `cerveau` (charger un `.brain` et l'attacher en hooks) est la tâche 8 : l'option
EXISTE dès maintenant — c'est le contrat de la CLI — et refuse proprement, sans importer `noyau`.
"""
from __future__ import annotations

import argparse
import sys
import threading
import time

from naulthene.cerveau.telemetrie import BusTrames
from naulthene.instruments.cerveau_3d.factice import DIM_BUS_FICTIF, boucle_factice
from naulthene.instruments.cerveau_3d.serveur import EcouteurUDP, ServeurCerveau3D

PORT_DEFAUT = 8770
HZ_DEFAUT = 15.0

# Le refus du mode `cerveau` — un texte qui dit POURQUOI, pas seulement « non ».
REFUS_CERVEAU = (
    "le mode « cerveau » n'est pas encore livré (tâche 8 de VIS-01) : aucune source n'a été\n"
    "lancée et AUCUN `.brain` n'a été chargé. Utilisez --source factice (démonstration, étape 0)"
)

GARANTIE_LECTURE_SEULE = ("⚠️  lecture seule : ce processus n'écrit aucun .brain et n'entraîne "
                          "rien.")


def construire_analyseur() -> argparse.ArgumentParser:
    """Les options du contrat (plan, tâche 6) — et rien de plus.

    ⚠️ `add_help=False` puis `-h/--aide/--help` déclarés à la main : le plan exige que la CLI
    RÉPONDE à `--aide` (français, comme le reste du dépôt), ce qu'argparse ne fournit pas seul.
    """
    analyseur = argparse.ArgumentParser(
        prog="python -m naulthene.instruments.cerveau_3d",
        description="VIS-01 — le cerveau 3D : une IRM vivante, en LECTURE SEULE.",
        epilog=("Étape 0 (démonstration) : --source factice, aucun cerveau chargé.\n"
                "Étape 2 (passerelle)      : --serveur-seul --udp 9998, puis un run qui émet\n"
                "                            vers udp:127.0.0.1:9998."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False)
    analyseur.add_argument("-h", "--aide", "--help", action="help",
                           help="affiche cette aide et sort")
    analyseur.add_argument("--source", choices=("factice", "cerveau"), default="factice",
                           help="qui produit les trames (défaut : factice)")
    analyseur.add_argument("--brain", default=None, metavar="CHEMIN",
                           help="le .brain à observer (mode « cerveau », tâche 8 : refusé)")
    analyseur.add_argument("--port", type=int, default=PORT_DEFAUT,
                           help=f"port d'écoute HTTP (défaut : {PORT_DEFAUT} ; 0 = port libre)")
    analyseur.add_argument("--hz", type=float, default=HZ_DEFAUT, metavar="CADENCE",
                           help=f"cadence d'émission de la source factice (défaut : {HZ_DEFAUT})")
    analyseur.add_argument("--udp", type=int, default=None, metavar="PORT",
                           help="écoute aussi les trames émises en UDP sur ce port (étape 2)")
    analyseur.add_argument("--serveur-seul", action="store_true",
                           help="ne produit AUCUNE trame locale : sert la page et reçoit l'UDP")
    analyseur.add_argument("--duree", type=float, default=None, metavar="SECONDES",
                           help="s'arrête tout seul après ce délai (défaut : jusqu'à Ctrl-C)")
    return analyseur


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


def _afficher_banniere(options, port, hote, ecouteur) -> None:
    """Ce qu'on regarde, où, et la garantie de lecture seule (ruling : lisible au lancement)."""
    if options.serveur_seul:
        source = "serveur seul — aucune trame produite ici"
        if ecouteur is not None:
            source = f"serveur seul — trames reçues en UDP sur le port {ecouteur.port}"
    else:
        source = f"factice (dim_bus fictif = {DIM_BUS_FICTIF})"
    print("🧠 Cerveau 3D — VIS-01", flush=True)
    print(f"   source     : {source}", flush=True)
    print(f"   serveur    : http://{hote}:{port}", flush=True)
    print(f"   {GARANTIE_LECTURE_SEULE}", flush=True)
    print(f"   → ouvrez http://{hote}:{port} dans un navigateur (Ctrl-C pour arrêter).",
          flush=True)


def main(argv=None) -> int:
    options = construire_analyseur().parse_args(argv)

    # Le mode `cerveau` : option présente (contrat), source absente (tâche 8). On refuse AVANT
    # de lier le port et sans importer `noyau` — un refus ne doit rien laisser derrière lui.
    if options.source == "cerveau":
        raise SystemExit(REFUS_CERVEAU)
    if options.hz <= 0.0:
        raise SystemExit(f"--hz invalide : {options.hz!r} (attendu > 0)")

    bus = BusTrames()
    arret = threading.Event()
    serveur, ecouteur, fil_source = None, None, None
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
            fil_source = threading.Thread(target=_cible_factice(bus, options, arret),
                                          name="source-factice", daemon=True)
            fil_source.start()

        _afficher_banniere(options, serveur.port, serveur.hote, ecouteur)

        if options.duree is not None:
            # Borné : on attend la fin de la source (ou le délai, s'il n'y en a pas), puis on
            # rend la main — c'est ce qui rend la CLI vérifiable sans navigateur ni Ctrl-C.
            if fil_source is not None:
                fil_source.join()
            else:
                time.sleep(max(0.0, float(options.duree)))
            return 0

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


if __name__ == "__main__":
    raise SystemExit(main())
