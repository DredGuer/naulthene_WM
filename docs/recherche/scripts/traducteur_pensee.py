#!/usr/bin/env python3
"""LE TRADUCTEUR — met des mots sur les vecteurs, tick par tick (17/08/2026).

Question de l'utilisateur : *« On ne peut pas savoir par les logs ce que C2 dit à C1 ?
En mots simples. Presque voir la chaîne de penser, et extrapoler entre cerveaux. »*

Les logs ne peuvent PAS répondre : ils comptent les votes de chaque voix dans DEUX boîtes
séparées (`votes_c1_jour`, `votes_c2_jour`). Les COUPLES sont perdus à l'écriture — on sait
combien de fois chacun a dit quoi, jamais s'ils l'ont dit en même temps.

Ce script rejoue un cerveau dans son monde et écrit, pour chaque tick, une phrase
française : ce que le corps ressent, ce que chaque voix propose, qui l'emporte.

⚠️ CE QUI EST HONNÊTE ET CE QUI NE L'EST PAS
--------------------------------------------
HONNÊTE — les noms d'ACTIONS. MiniGrid les définit (`Actions.left`, `forward`...), l'agent
  joue exactement ces indices. Dire « C2 veut tourner à gauche » est une lecture, pas une
  interprétation.
HONNÊTE — les noms de SENSATIONS. Les dims du vecteur bio ont une position contractuelle
  (contrat append-only) et une origine documentée. Dire « satiété 0.02 » = « il a faim »
  est un changement d'unité, pas une projection.
PAS HONNÊTE, et donc ABSENT D'ICI — les MOTIFS. Écrire « C2 veut tourner PARCE QU'il sent
  la nourriture à droite » supposerait de connaître la raison du vote. Or C2 sort 7
  scalaires, sans justification. La corrélation « il tourne souvent quand l'odeur monte »
  est mesurable ; la causalité ne l'est pas. Le script mesure donc des COÏNCIDENCES et les
  nomme comme telles.

C'est la même discipline que l'invariant v36.0 : le cerveau ne sait pas ce qu'est une clé.
Le traducteur non plus. Il traduit des positions et des nombres, jamais des intentions.

Usage :
    PYTHONPATH=src python docs/recherche/scripts/traducteur_pensee.py <brain> \
        [--ticks 400] [--niveau 4] [--recit 60] [--json sortie.json]
"""
from __future__ import annotations
import argparse
import json
import math
from collections import Counter, defaultdict

import numpy as np
import torch

# --- Les 7 actions réelles de MiniGrid, dans l'ordre des indices joués ---------------
# Source : minigrid.core.actions.Actions. L'agent joue `min(a, 6)`.
ACTIONS = ["tourner à gauche", "tourner à droite", "avancer",
           "prendre / manger", "poser", "activer", "attendre"]
ACTIONS_COURT = ["←gauche", "→droite", "↑avancer", "✋manger", "↓poser", "⚙activer", "…attendre"]


def carte_vecteur_bio(mod) -> list[tuple[int, str]]:
    """(index, nom lisible) pour les dims qu'on sait nommer, d'après le contrat append-only.

    L'ordre est celui de `obtenir_vecteur_bio` : 3 jauges + quête(3) + rappel(2)
    + vocal(8) + sensoriel + marquant(2) + présence(1).
    """
    B = mod  # bus_sensoriel
    noms: list[tuple[int, str]] = [
        (0, "satiété"), (1, "hydratation"), (2, "stimulation"),
    ]
    i = 16                      # 3 jauges + 3 quête + 2 rappel + 8 vocal
    # --- vecteur sensoriel ---
    noms += [(i + 0, "contact frontal"), (i + 1, "objet en main")]
    i += B.DIM_TOUCHER          # 4 (dont cos/sin d'orientation)
    noms += [(i + 0, "odeur nourriture"), (i + 1, "odeur eau")]
    i += B.DIM_CHIMIE           # 4 (2 odorat + 2 goût)
    i += B.DIM_EXO              # 8 — dormant, aucun plug
    noms += [(i + 0, "Δ odeur nourriture"), (i + 1, "Δ odeur eau")]
    i += B.DIM_ODORAT_DELTA     # 2
    noms += [(i + 0, "chaleur (danger)"), (i + 1, "Δ chaleur")]
    i += B.DIM_THERMOCEPTION    # 2
    noms += [(i + 0, "encombrement"), (i + 1, "asymétrie gauche/droite")]
    i += B.DIM_PRESSION         # 2
    noms += [(i + 0, "valence du souvenir"), (i + 1, "confiance du souvenir")]
    return noms


def phrase_corps(vbio: np.ndarray, carte: list[tuple[int, str]]) -> str:
    """Traduit l'état du corps en une phrase. Seuils de VOCABULAIRE, pas de décision.

    ⚠️ Ces seuils ne pilotent RIEN dans l'agent — ils choisissent un adjectif français
    pour un affichage humain. Le dogme « rien en dur » porte sur le chemin cognitif ;
    ici on est dans un outil de lecture, hors du cerveau.
    """
    d = {n: float(vbio[i]) for i, n in carte if i < len(vbio)}
    m = []
    s, h = d.get("satiété", 0.5), d.get("hydratation", 0.5)
    m.append("affamé" if s < 0.15 else "repu" if s > 0.7 else f"faim modérée")
    m.append("assoiffé" if h < 0.15 else "désaltéré" if h > 0.7 else "soif modérée")
    if d.get("contact frontal", 0) > 0.5:
        m.append("nez contre un obstacle")
    if d.get("chaleur (danger)", 0) > 0.05:
        c = d["chaleur (danger)"]
        m.append(f"{'BRÛLANT' if c > 0.5 else 'chaleur proche'} ({c:.2f})")
    on, oe = d.get("odeur nourriture", 0), d.get("odeur eau", 0)
    if on > 0.05 or oe > 0.05:
        m.append(f"odeurs N{on:.2f}/E{oe:.2f}")
    don = d.get("Δ odeur nourriture", 0.5)
    if abs(don - 0.5) > 0.05:
        m.append("se rapproche de la nourriture" if don > 0.5 else "s'en éloigne")
    if d.get("encombrement", 0) > 0.5:
        m.append(f"coincé ({d['encombrement']:.2f})")
    val = d.get("valence du souvenir", 0.5)
    if d.get("confiance du souvenir", 0) > 0.2 and abs(val - 0.5) > 0.1:
        m.append("bon souvenir ici" if val > 0.5 else "mauvais souvenir ici")
    return ", ".join(m)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("brain")
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--graine", type=int, default=7)
    ap.add_argument("--niveau", type=int, default=None)
    ap.add_argument("--recit", type=int, default=40,
                    help="nombre de ticks racontés en clair (0 = aucun)")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    from naulthene.cerveau import noyau as N
    from naulthene.cerveau import bus_sensoriel as B
    from naulthene.cerveau.persistance import PersistanceAnatomique

    torch.manual_seed(args.graine)
    np.random.seed(args.graine)

    etat = PersistanceAnatomique(args.brain).charger_ou_naitre()
    agent = etat.agent
    agent.eval()
    carte = carte_vecteur_bio(B)

    nom = args.brain.split("/")[-1]
    if args.niveau is not None:
        etat.niveau_actuel = int(args.niveau)
        etat.env_id, etat.nom_classe = N.PROGRAMME[etat.niveau_actuel]
        etat.env.close()
        etat.env = N.creer_env(etat.env_id, N.DIM_VISUELLE)
        etat.doorkey_actif = N.est_doorkey(etat.env_id)
        if etat.doorkey_actif and etat.detecteur is None:
            etat.detecteur = N.DetecteurJalonsDoorKey()

    print(f"\n{'='*78}")
    print(f"CHAÎNE DE PENSÉE — {nom}")
    print(f"  {etat.nom_classe} ({etat.env_id}) | bus {agent.dim_bus} dims | "
          f"tick absolu {etat.tick_absolu}")
    print(f"{'='*78}")

    def _nouvel_episode():
        obs, _ = N._reset_seede(etat)
        etat.etat_courant = N.encoder(obs)
        etat.memoire_tampon = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
        etat.vecteurs_episodiques = []
        etat.detecteur_ressources_bio.reinitialiser_episode(etat.env)
        etat.bus_sensoriel.reinitialiser_episode(etat.env)
        etat.positions_visitees_episode = set()

    _nouvel_episode()

    # LA MATRICE DES COUPLES — ce que les logs ne gardent pas.
    couples = np.zeros((7, 7), dtype=int)
    vetos = 0
    n = 0
    # coïncidences sensation × vote de C2 (jamais présentées comme des causes)
    coinc = defaultdict(lambda: np.zeros(7, dtype=int))
    sensations_vues = Counter()
    recit = []

    with torch.no_grad():
        for t in range(args.ticks):
            obs = N.encoder(etat.env.unwrapped.gen_obs())
            memoire = etat.memoire_tampon if etat.memoire_tampon is not None else \
                torch.zeros(1, agent.dim_bus, device=N.DEVICE)
            contexte = (torch.stack(etat.vecteurs_episodiques).mean(dim=0)
                        if etat.vecteurs_episodiques
                        else torch.zeros(1, agent.dim_bus, device=N.DEVICE))
            brut = etat.moteur_bio.obtenir_vecteur_bio(
                signaux_sensoriels=etat.bus_sensoriel.interpreter(etat.env))
            vbio = torch.tensor([brut], dtype=torch.float32, device=N.DEVICE)

            (_bus, mem_act, _pe, pensee_bio, logits_c1) = \
                agent._executer_c1_reflexe(obs, memoire, contexte, vbio)
            valeurs_c2, _ind = agent._solliciter_c2_neocortex(
                pensee_bio, mem_act, vecteur_bio=vbio)

            a1 = int(logits_c1.view(-1)[:7].argmax().item())
            a2 = int(valeurs_c2.view(-1)[:7].argmax().item())
            # ⚠️ NE PAS lire `force_planification_jour` sur l'état : c'est un ACCUMULATEUR
            # JOURNALIER, remis à 0 par `_reinitialiser_buffers_journee`. Sur un `.brain`
            # fraîchement chargé il vaut 0.0 — une première version de cette sonde
            # multipliait donc C2 par zéro et mesurait « veto 0/300 », un artefact parfait
            # (et flatteur : il « confirmait » que C2 ne sert à rien). C'est exactement le
            # piège du §3 de la règle de mesure : un résultat trop propre est suspect.
            #
            # La fusion réelle de `penser()` est `logits_c1 * gain_c1 + valeurs_c2 * force`,
            # où `force = agent.acceptation()` (v40.1, recalculée chaque nuit en
            # [noyau.py:6614]) et `gain_c1` est publié dans `mesure_arbitrage`.
            # `acceptation()` est une méthode de l'agent, donc disponible sur un `.brain`
            # rechargé — contrairement à l'accumulateur journalier.
            m = getattr(agent, "mesure_arbitrage", None) or {}
            gain_c1 = float(m.get("gain_c1", 1.0))
            force = float(agent.acceptation())
            fusion = (logits_c1 * gain_c1 + valeurs_c2 * force).view(-1)[:7]
            af = int(fusion.argmax().item())

            couples[a1, a2] += 1
            if af != a1:
                vetos += 1
            n += 1

            vb = np.asarray(brut, dtype=float)
            d = {nm: float(vb[i]) for i, nm in carte if i < len(vb)}
            for cle, actif in (
                ("a faim (satiété<0.15)", d.get("satiété", 1) < 0.15),
                ("obstacle devant", d.get("contact frontal", 0) > 0.5),
                ("chaleur proche", d.get("chaleur (danger)", 0) > 0.05),
                ("sent la nourriture", d.get("odeur nourriture", 0) > 0.05),
                ("coincé", d.get("encombrement", 0) > 0.5),
                ("mauvais souvenir ici", d.get("valence du souvenir", .5) < 0.4
                 and d.get("confiance du souvenir", 0) > 0.2),
            ):
                if actif:
                    coinc[cle][a2] += 1
                    sensations_vues[cle] += 1

            if len(recit) < args.recit:
                recit.append((t, phrase_corps(vb, carte), a1, a2, af,
                              float(logits_c1.view(-1)[:7].std().item()),
                              float(valeurs_c2.view(-1)[:7].std().item())))

            joue = int(torch.distributions.Categorical(logits=fusion).sample().item())
            obs_s, _r, term, trunc, _ = etat.env.step(min(joue, 6))
            etat.etat_courant = N.encoder(obs_s)
            etat.memoire_tampon = mem_act
            if term or trunc:
                _nouvel_episode()

    # ---------- 1. LE RÉCIT ----------
    if recit:
        print(f"\n{'-'*78}\n1. LE RÉCIT — {len(recit)} premiers ticks en clair\n{'-'*78}")
        for (t, corps, a1, a2, af, s1, s2) in recit:
            fleche = "  ⚔️ C2 L'EMPORTE" if af != a1 else ""
            daccord = " (d'accord)" if a1 == a2 else ""
            print(f"t{t:>4} │ {corps[:56]:<56}")
            print(f"      │ C1 «{ACTIONS[a1]:<17}» ({s1:.2f})  "
                  f"C2 «{ACTIONS[a2]:<17}» ({s2:.2f}){daccord}")
            print(f"      │ → joue «{ACTIONS[af]}»{fleche}")

    # ---------- 2. LA MATRICE DES COUPLES ----------
    print(f"\n{'-'*78}\n2. QUI DIT QUOI QUAND — la matrice que les logs ne gardent pas\n{'-'*78}")
    print(f"{'C1 dit ↓ / C2 dit →':<22}" + "".join(f"{a:>10}" for a in ACTIONS_COURT))
    for i in range(7):
        if couples[i].sum() == 0:
            continue
        print(f"{ACTIONS[i]:<22}" + "".join(
            f"{couples[i, j]:>10}" if couples[i, j] else f"{'·':>10}" for j in range(7)))
    accord = int(np.trace(couples))
    print(f"\n  accord (même case diagonale) : {accord}/{n} = {accord/max(1,n):6.1%}")
    print(f"  veto de C2 (l'action jouée ≠ celle de C1) : {vetos}/{n} = {vetos/max(1,n):6.1%}")

    # ---------- 3. LES PHRASES ----------
    print(f"\n{'-'*78}\n3. EN MOTS SIMPLES — ce que C2 répond le plus souvent à C1\n{'-'*78}")
    lignes = []
    for i in range(7):
        tot = couples[i].sum()
        if tot < max(3, n * 0.02):
            continue
        j = int(couples[i].argmax())
        part = couples[i, j] / tot
        if i == j:
            lignes.append(f"  Quand C1 veut « {ACTIONS[i]} », C2 est D'ACCORD "
                          f"{part:.0%} du temps ({tot} tick(s)).")
        else:
            lignes.append(f"  Quand C1 veut « {ACTIONS[i]} », C2 répond "
                          f"« plutôt {ACTIONS[j]} » {part:.0%} du temps ({tot} tick(s)).")
    print("\n".join(lignes) if lignes else "  (aucun couple assez fréquent)")

    # ---------- 4. COÏNCIDENCES ----------
    print(f"\n{'-'*78}\n4. COÏNCIDENCES corps ↔ vote de C2")
    print(f"   ⚠️ des COÏNCIDENCES, pas des causes : C2 ne justifie jamais son vote.\n{'-'*78}")
    if sensations_vues:
        for cle, cnt in sensations_vues.most_common():
            h = coinc[cle]
            j = int(h.argmax())
            print(f"  {cle:<26} ({cnt:>4} tick(s)) → C2 vote surtout "
                  f"« {ACTIONS[j]} » ({h[j]/max(1,h.sum()):.0%})")
    else:
        print("  aucune sensation notable rencontrée sur cette fenêtre")

    if args.json:
        with open(args.json, "w") as f:
            json.dump({"brain": nom, "n": n, "accord": accord / max(1, n),
                       "veto": vetos / max(1, n), "couples": couples.tolist(),
                       "coincidences": {k: v.tolist() for k, v in coinc.items()}},
                      f, indent=1)
        print(f"\n  → {args.json}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
