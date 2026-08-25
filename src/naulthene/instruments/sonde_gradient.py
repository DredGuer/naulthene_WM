"""LA SONDE DE GRADIENT — l'apprentissage a-t-il seulement démarré ? (v33.1, expérimental)

Instrument de DIAGNOSTIC en lecture seule. Fait vivre à un cerveau une journée complète,
puis intercepte `apprendre_journee` pour mesurer ce qui arrive RÉELLEMENT à `tete_motrice`.

    Un gradient nul sur la tête motrice = 5000 jours de tirage au sort.

Motivation (banc d'ablation, 2026-08-05) : le cerveau `REFERENCE_5000j` joue l'action
`forward` dans **5,5 %** des cas et son entropie est de 1,840 sur un maximum de ln(7)=1,946
— quasi le hasard pur. À 700 jours : 5,7 % et 1,832. **En 4300 jours, rien n'a bougé.**
Deux explications possibles, que seule cette sonde sépare :

  (a) aucun gradient n'atteint la tête motrice → l'apprentissage n'a jamais démarré ;
  (b) le gradient arrive mais ne corrige rien → l'apprentissage démarre et échoue.

Ce sont deux problèmes opposés, avec deux réparations opposées. Les confondre coûterait un
cycle entier (leçon v33).

---
CE QUE LA SONDE MESURE

1. **Les récompenses du jour** — combien de ticks en reçoivent une, quelle somme.
   C'est l'entrée du calcul : sans récompense, tout le reste est mécaniquement nul.
2. **Les returns après normalisation** — `apprendre_journee` centre-réduit les returns.
   ⚠️ Point critique : si `std <= 1e-6` la normalisation est SAUTÉE (voir le code), mais
   si tous les rewards sont nuls, les returns le sont aussi et les avantages valent
   `-valeurs`, ce qui produit un gradient qui n'apprend RIEN d'utile.
3. **Les avantages** `returns - valeurs.detach()` — le signal qui pondère `log_prob`.
4. **La norme du gradient PAR COUCHE**, après `backward()` et avant `clip_grad_norm_`.
   C'est la mesure décisive : `tete_motrice.grad ≈ 0` ⇒ la politique ne bouge pas.
5. **La part de chaque terme de perte** (JEPA / acteur / critique / entropie) — pour voir
   qui domine réellement la descente de gradient.

Aucune écriture : le cerveau est chargé depuis une COPIE, jamais sauvegardé.

---
LANCEMENT

    PYTHONPATH=src python -m naulthene.instruments.sonde_gradient \\
        --brain brains/ablations/REFERENCE_5000j.brain --jours 3

    # Comparer deux âges de cerveau
    PYTHONPATH=src python -m naulthene.instruments.sonde_gradient \\
        --brain brains/ablations/REFERENCE_700j.brain --jours 3 --niveau 0
"""

import argparse
import os
import shutil

import torch

import naulthene.cerveau.noyau as nx
from naulthene.cerveau.persistance import PersistanceAnatomique


# --- 1. L'INTERCEPTION ---
#
# On ne modifie PAS `noyau.py` : on remplace `AGI_Naulthene.apprendre_journee` par une
# version instrumentée le temps de la sonde, puis on restaure l'originale. C'est la même
# discipline que le banc d'ablation — l'instrument ne laisse aucune trace dans le cerveau
# ni dans le code de production.

COUCHES_SUIVIES = (
    "tete_motrice",           # LA politique — c'est elle qui décide de l'action
    "integrateur_bio",        # l'entrée des sens faibles
    "porte_visuelle",         # la vue
    "analyseur", "hippocampe", "fusion_memoire",
    "generateur_attente",     # le JEPA
    # --- v41.32 : LES CINQ COUCHES MANQUANTES ---
    #
    # 🔴 Mesuré le 25/08 : les sept couches ci-dessus ne totalisaient que **51 %** de la
    # norme brute du gradient. La moitié du budget d'apprentissage n'était attribuée à
    # personne — une « matière noire » invisible à la sonde.
    #
    # Ces cinq-là complètent le réseau. Deux d'entre elles sont des suspects directs :
    #   - `cortex_prefrontal` (C2) : couper C2 ne change le score de 0,0 pt sur 6 niveaux
    #     (v41.29, 78 cellules d'ablation) — s'il consomme du gradient, il en dissipe ;
    #   - l'hémisphère audio (`porte_auditive`, `generateur_attente_audio`, `tete_vocale`) :
    #     24 % des paramètres pour une faculté qu'aucun niveau MiniGrid n'exerce.
    "cortex_prefrontal",      # C2 — la délibération
    "porte_auditive",         # l'ouïe (aucun son dans MiniGrid)
    "generateur_attente_audio",  # le JEPA audio
    "tete_vocale",            # la bouche
    "tete_requete",           # le routage C3 (aucun plug enregistré)
)


def instrumenter(agent, journal):
    """Remplace `apprendre_journee` par une version qui mesure tout avant de déléguer."""
    originale = agent.apprendre_journee

    # ⚠️ `**extra` est indispensable : `apprendre_journee` a gagné des paramètres depuis
    # l'écriture de cette sonde (v33.1) — `chocs_dopamine` (v37.1, distillation sélective)
    # et `transitions` (v41.31, gradient causal). Une signature figée casse la sonde à
    # chaque évolution du noyau, et le crash survient DANS `executer_nuit`, donc après une
    # journée complète de calcul. Tout est repassé tel quel à l'originale.
    def sonde(jepa_losses, log_probs, entropies, valeurs, rewards, dones,
              gamma=0.95, coeff_entropie=0.02, pertes_vocales=None, **extra):
        mesure = {
            "ticks": len(rewards),
            "rewards_non_nuls": sum(1 for r in rewards if r != 0.0),
            "rewards_somme": float(sum(rewards)),
            "rewards_max": float(max(rewards)) if rewards else 0.0,
            "dones": sum(1 for d in dones if d),
            "log_probs": len(log_probs),
        }

        # --- Rejeu EXACT du calcul de `apprendre_journee`, en lecture seule ---
        if log_probs:
            returns, R = [], 0.0
            for r, d in zip(reversed(rewards), reversed(dones)):
                R = r + gamma * (0.0 if d else R)
                returns.insert(0, R)
            rt = torch.tensor(returns, dtype=torch.float32, device=nx.DEVICE)
            mesure["returns_std_avant"] = float(rt.std()) if rt.numel() > 1 else 0.0
            mesure["returns_abs_moy_avant"] = float(rt.abs().mean())
            # La normalisation n'a lieu que si l'écart-type est significatif.
            mesure["normalisation_appliquee"] = bool(
                rt.numel() > 1 and rt.std() > 1e-6
            )
            if mesure["normalisation_appliquee"]:
                rt = (rt - rt.mean()) / (rt.std() + 1e-8)

            vt = torch.cat(valeurs).squeeze(-1)
            av = rt - vt.detach()
            mesure["valeurs_abs_moy"] = float(vt.abs().mean())
            mesure["avantages_abs_moy"] = float(av.abs().mean())
            mesure["avantages_std"] = float(av.std()) if av.numel() > 1 else 0.0
            mesure["entropie_moy"] = float(torch.cat(entropies).squeeze(-1).mean())

        # --- La vraie mise à jour, puis lecture des gradients AVANT qu'ils soient perdus ---
        #
        # `apprendre_journee` appelle `optimizer.step()` puis rend la main ; les `.grad`
        # sont encore présents à ce moment (ils ne sont remis à zéro qu'au DÉBUT de
        # l'appel suivant, via `zero_grad`). On peut donc les lire juste après.
        # --- v41.32 : LA NORME BRUTE, AVANT CLIPPING ---
        #
        # 🔴 CE QUE ÇA CORRIGE. `apprendre_journee` fait `backward()` -> `clip_grad_norm_`
        # -> `step()`, puis rend la main. Lire les `.grad` APRÈS l'appel donne donc la
        # valeur POST-CLIP, jamais la brute — et la norme globale y est mécaniquement
        # bornée à 1.0. J'ai d'abord lu 0,9315 en croyant mesurer le gradient réel : c'est
        # en réalité la valeur déjà écrasée. Une norme post-clip ne peut par construction
        # jamais démontrer que le clip se déclenche.
        #
        # `clip_grad_norm_` RETOURNE la norme totale AVANT écrêtage. On l'intercepte donc
        # le temps de l'appel, ce qui donne la seule mesure honnête : la norme brute, et
        # le fait que le couperet soit tombé ou non.
        _brut = {}
        _clip_reel = torch.nn.utils.clip_grad_norm_

        def _clip_espion(params, max_norm, *a, **k):
            # ⚠️ v41.32-fix2 — LES PARTS SE LISENT **AVANT** `_clip_reel`, jamais après.
            #
            # 🔴 Bug corrigé : je lisais les `.grad` APRÈS l'appel réel, donc après que le
            # clip les avait tous divisés. Signature du défaut : racine(Σ carrés) valait
            # **1.000000 EXACTEMENT** sur 6/6 jours — la norme post-clip, par construction.
            # J'en avais conclu à « 84 % de gradient manquant » alors qu'il n'existe que
            # 12 paramètres dans tout le réseau (un `annexe_weight` par couche, vérifié) :
            # la somme des carrés DOIT égaler la norme globale au carré.
            #
            # C'est le même défaut que celui déjà corrigé deux fois dans cette campagne
            # (chaleur v41.25-fix1, discrimination fix1) : lire une grandeur après
            # l'opération qui la modifie.
            parts = {}
            for nom_c in COUCHES_SUIVIES:
                c = getattr(agent, nom_c, None)
                if c is None:
                    continue
                acc = 0.0
                for prm in c.parameters():
                    if prm.grad is not None:
                        acc += float(prm.grad.detach().norm() ** 2)
                parts[nom_c] = acc ** 0.5
            _brut["parts"] = parts
            totale = _clip_reel(params, max_norm, *a, **k)
            _brut["norme"] = float(totale)
            _brut["plafond"] = float(max_norm)
            _brut["clippe"] = float(totale) > float(max_norm)
            return totale

        torch.nn.utils.clip_grad_norm_ = _clip_espion
        try:
            perte = originale(jepa_losses, log_probs, entropies, valeurs, rewards, dones,
                              gamma=gamma, coeff_entropie=coeff_entropie,
                              pertes_vocales=pertes_vocales, **extra)
        finally:
            torch.nn.utils.clip_grad_norm_ = _clip_reel
        mesure["norme_brute"] = _brut.get("norme")
        mesure["clippe"] = _brut.get("clippe")
        mesure["plafond"] = _brut.get("plafond")
        mesure["parts_brutes"] = _brut.get("parts")
        mesure["perte_totale"] = perte

        normes = {}
        for nom in COUCHES_SUIVIES:
            couche = getattr(agent, nom, None)
            if couche is None:
                continue
            total = 0.0
            for p in couche.parameters():
                if p.grad is not None:
                    total += float(p.grad.detach().norm() ** 2)
            normes[nom] = total ** 0.5
        mesure["gradients"] = normes

        # --- v41.32 : LE THRASHING — le gradient s'annule-t-il d'un jour à l'autre ? ---
        #
        # Une norme de gradient faible a DEUX causes opposées, et les confondre coûte un
        # cycle (même leçon que (a)/(b) en tête de ce module) :
        #   (1) le gradient est MINUSCULE — le signal ne modifie rien ;
        #   (2) le gradient est GRAND mais s'ANNULE — l'agent est poussé dans un sens le
        #       jour J, dans le sens opposé le jour J+1, et le poids ne bouge pas.
        #
        # Le discriminant est le rapport ‖Σg‖ / Σ‖g‖ sur plusieurs jours :
        #   proche de 1 -> tous les pas sont ALIGNÉS (cause 1, gradient faible mais cohérent)
        #   proche de 0 -> les pas s'ANNULENT (cause 2, thrashing)
        #
        # ⚠️ On accumule le VECTEUR, pas la norme : c'est tout l'intérêt. Sommer des normes
        # ne peut jamais révéler une annulation.
        g = agent.tete_motrice.annexe_weight.grad
        if g is not None:
            gd = g.detach().clone()
            if _accum["somme"] is None:
                _accum["somme"] = torch.zeros_like(gd)
            _accum["somme"] += gd
            _accum["somme_normes"] += float(gd.norm())
            _accum["n"] += 1
            mesure["grad_jour"] = float(gd.norm())
            mesure["grad_cumul"] = float(_accum["somme"].norm())
            mesure["grad_somme_normes"] = _accum["somme_normes"]
        journal.append(mesure)
        return perte

    agent.apprendre_journee = sonde
    return originale


# Accumulateur du vecteur gradient de `tete_motrice`, partagé entre les jours de la sonde.
# Module-level par simplicité : la sonde est un instrument mono-run, jamais réentrant.
_accum = {"somme": None, "somme_normes": 0.0, "n": 0}


# --- 2. LE RAPPORT ---

def afficher(journal, nom_cerveau, niveau):
    print("\n" + "=" * 100)
    print(f"  SONDE DE GRADIENT — {os.path.basename(nom_cerveau)} — {niveau}")
    print("=" * 100)

    print(f"\n  {'jour':>5} {'ticks':>6} {'r≠0':>5} {'Σr':>9} {'r_max':>7} "
          f"{'|ret|':>8} {'norm?':>6} {'|avant|':>9} {'entropie':>9} {'perte':>9}")
    print("  " + "-" * 94)
    for i, m in enumerate(journal, 1):
        print(f"  {i:>5} {m['ticks']:>6} {m['rewards_non_nuls']:>5} "
              f"{m['rewards_somme']:>9.4f} {m['rewards_max']:>7.3f} "
              f"{m.get('returns_abs_moy_avant', 0):>8.4f} "
              f"{'oui' if m.get('normalisation_appliquee') else 'NON':>6} "
              f"{m.get('avantages_abs_moy', 0):>9.4f} "
              f"{m.get('entropie_moy', 0):>9.4f} {m['perte_totale']:>9.4f}")

    print(f"\n  NORMES DE GRADIENT PAR COUCHE (après backward, avant clipping)")
    print("  " + "-" * 94)
    couches = [c for c in COUCHES_SUIVIES if c in journal[0]["gradients"]]
    print(f"  {'jour':>5} " + " ".join(f"{c[:13]:>14}" for c in couches))
    for i, m in enumerate(journal, 1):
        print(f"  {i:>5} " + " ".join(f"{m['gradients'][c]:>14.6f}" for c in couches))

    # --- v41.32 : LE THRASHING ---
    if any("grad_cumul" in m for m in journal):
        print(f"\n  ALIGNEMENT DU GRADIENT SUR tete_motrice (le gradient s'annule-t-il ?)")
        print("  " + "-" * 94)
        print(f"  {'jour':>5} {'‖g_jour‖':>14} {'‖Σg‖ (cumul)':>16} {'Σ‖g‖':>14} {'alignement':>12}")
        for i, m in enumerate(journal, 1):
            if "grad_cumul" not in m:
                continue
            al = m["grad_cumul"] / max(m["grad_somme_normes"], 1e-12)
            print(f"  {i:>5} {m['grad_jour']:>14.6f} {m['grad_cumul']:>16.6f} "
                  f"{m['grad_somme_normes']:>14.6f} {al:>12.4f}")
        dernier = [m for m in journal if "grad_cumul" in m][-1]
        align = dernier["grad_cumul"] / max(dernier["grad_somme_normes"], 1e-12)
        print()
        print(f"  ALIGNEMENT FINAL : {align:.4f}   (1 = pas tous alignés, 0 = ils s'annulent)")
        # Repère de lecture, pas un seuil de décision : la valeur attendue pour des pas
        # INDÉPENDANTS est ~1/sqrt(n) — c'est la marche aléatoire, ni alignement ni
        # annulation active. On la publie à côté plutôt que de trancher à sa place.
        n = dernier and len([m for m in journal if "grad_cumul" in m])
        print(f"  Repère marche aléatoire (1/√n, n={n}) : {1.0 / max(n, 1) ** 0.5:.4f}")

    # --- v41.32 : LE CLIPPING SE DÉCLENCHE-T-IL ? ---
    _avec = [m for m in journal if m.get("norme_brute") is not None]
    if _avec:
        print(f"\n  NORME GLOBALE **AVANT** CLIPPING (plafond = {_avec[0]['plafond']:.2f})")
        print("  " + "-" * 94)
        print(f"  {'jour':>5} {'norme brute':>14} {'clippé ?':>10} {'facteur':>10}"
              f"   part du budget brut : corps / décision / vue")
        for i, m in enumerate(_avec, 1):
            f = m["plafond"] / m["norme_brute"] if m["norme_brute"] > m["plafond"] else 1.0
            pb = m.get("parts_brutes") or {}
            n = m["norme_brute"]
            det = " ".join(f"{100*pb.get(k, 0.0)/max(n, 1e-12):>5.1f}%"
                           for k in ("integrateur_bio", "tete_motrice", "porte_visuelle"))
            # ⚠️ Les parts sont des normes L2 : leur SOMME dépasse la norme globale (le
            # carré de la somme n'est pas la somme des carrés). On rapporte donc la somme
            # des CARRÉS, seule grandeur qui se conserve — sans quoi un « résidu » apparaît
            # là où il n'y en a pas.
            _somme_carres = sum(v * v for v in pb.values())
            det += f"   Σ(carrés)/n² = {100 * _somme_carres / max(n * n, 1e-12):>5.1f}%"
            print(f"  {i:>5} {m['norme_brute']:>14.6f} {'OUI' if m['clippe'] else 'non':>10} "
                  f"{f:>10.4f}   {det}")
        n_clip = sum(1 for m in _avec if m["clippe"])
        moy = sum(m["norme_brute"] for m in _avec) / len(_avec)
        print()
        print(f"  Nuits clippées : {n_clip}/{len(_avec)} ({100*n_clip/len(_avec):.0f} %)")
        print(f"  Norme brute moyenne : {moy:.6f}   (plafond {_avec[0]['plafond']:.2f})")
        if n_clip == 0:
            print("  🟢 Le clipping ne se déclenche JAMAIS — il n'explique pas le plafond.")
        elif n_clip == len(_avec):
            print("  🔴 Le clipping se déclenche à CHAQUE nuit — le budget est saturé en permanence.")

    # --- Verdict ---
    print("\n" + "=" * 100)
    moy_motrice = sum(m["gradients"].get("tete_motrice", 0) for m in journal) / len(journal)
    moy_jepa = sum(m["gradients"].get("generateur_attente", 0) for m in journal) / len(journal)
    r_tot = sum(m["rewards_non_nuls"] for m in journal)
    print(f"  Gradient moyen sur tete_motrice : {moy_motrice:.6f}")
    print(f"  Gradient moyen sur le JEPA      : {moy_jepa:.6f}")
    print(f"  Ticks avec récompense non nulle : {r_tot} / "
          f"{sum(m['ticks'] for m in journal)}")

    print()
    if moy_motrice < 1e-6:
        print("  🔴 VERDICT (a) : AUCUN gradient n'atteint la tête motrice.")
        print("     L'apprentissage de la politique n'a JAMAIS démarré — les jours de run")
        print("     ne sont que des tirages au sort. Chercher en AMONT (récompense, buffers).")
    elif r_tot == 0:
        print("  🟠 VERDICT (a-bis) : un gradient existe, mais AUCUNE récompense ne l'a produit.")
        print("     Il ne vient que du critique et de l'entropie — il pousse la politique")
        print("     SANS information sur ce qui est bon. C'est du bruit dirigé, pas un apprentissage.")
    else:
        print("  🟢 VERDICT (b) : le gradient arrive ET des récompenses existent.")
        print("     L'apprentissage démarre — le problème est en AVAL (échelle, arbitrage,")
        print("     ou signal trop rare pour surmonter l'entropie).")
    print("=" * 100)


# --- 3. POINT D'ENTRÉE ---

def main():
    p = argparse.ArgumentParser(description="Sonde de gradient — l'apprentissage démarre-t-il ?")
    p.add_argument("--brain", required=True)
    p.add_argument("--jours", type=int, default=3)
    p.add_argument("--niveau", type=int, default=None,
                   help="indice du PROGRAMME (défaut : celui du .brain)")
    p.add_argument("--graine", type=int, default=1789)
    # v41.32 — ABLATION « PISTE A » : le thrashing vient-il de l'INSTABILITÉ DU MONDE ?
    #
    # `--niveau` ne suffit PAS : il fixe l'env au démarrage, mais `demarrer_journee` peut
    # ensuite changer de carte à chaque journée (P17, distribution du cursus — observé
    # « 1 révision · 2 révisions » pendant la mesure du 25/08). Le seul verrou réel est
    # `ENV_FORCE`, lu par `demarrer_journee` (l. ~7386) : quand il est non-nul, le
    # PROGRAMME entier est remplacé par ce seul niveau, répété.
    p.add_argument("--env-force", type=str, default=None,
                   help="verrouille la carte pour TOUS les jours (ablation P17)")
    p.add_argument("--soif-figee", action="store_true",
                   help="ABLATION piste C : hydratation figée à 1.0 (un seul axe corporel)")
    args = p.parse_args()

    if not os.path.exists(args.brain):
        raise SystemExit(f"❌ Cerveau introuvable : {args.brain}")

    # Copie de travail : la sonde fait vivre de vraies journées (donc apprend), il est
    # hors de question de toucher au cerveau de référence.
    dossier = os.path.join(os.path.dirname(args.brain) or ".", "_sonde")
    os.makedirs(dossier, exist_ok=True)
    copie = os.path.join(dossier, "sonde.brain")
    shutil.copy2(args.brain, copie)

    torch.manual_seed(args.graine)

    # ⚠️ Posé AVANT `charger_ou_naitre` : la naissance lit déjà `ENV_FORCE` (l. 7065).
    if args.env_force:
        nx.ENV_FORCE = args.env_force
    # v41.32 — piste C. Écriture + VÉRIFICATION que le drapeau a atteint le module :
    # c'est le bug v41.4 (drapeau accepté par l'argparse mais jamais lu), qui avait rendu
    # trois bras de campagne rigoureusement identiques.
    if args.soif_figee:
        nx.SOIF_FIGEE = True
        from naulthene.cerveau.noyau import SOIF_FIGEE as _verif
        assert _verif is True, "l'ablation n'a pas atteint le module — campagne invalide"
        print("🔬 [ABLATION] axe hydrique GELÉ — le corps ne tire plus que sur la faim")

    etat = PersistanceAnatomique(copie).charger_ou_naitre()
    if args.niveau is not None:
        env_id, nom = nx.PROGRAMME[args.niveau]
        etat.env.close()
        etat.env = nx.creer_env(env_id, nx.DIM_VISUELLE)
        etat.env_id, etat.nom_classe = env_id, nom

    journal = []
    originale = instrumenter(etat.agent, journal)

    print(f"\n🔬 SONDE DE GRADIENT — {args.jours} journée(s) complète(s) sur {etat.nom_classe}")
    for j in range(args.jours):
        nx.demarrer_journee(etat)
        for _ in range(nx.ticks_par_jour):
            nx.traiter_tick(etat)
        # `executer_nuit` déclenche apprendre_journee (intercepté) puis le rêve/sommeil.
        nx.executer_nuit(etat)
        print(f"   jour {j+1}/{args.jours} ✓")

    etat.agent.apprendre_journee = originale
    etat.env.close()

    if not journal:
        raise SystemExit("❌ `apprendre_journee` n'a jamais été appelée — rien à mesurer.")
    afficher(journal, args.brain, etat.nom_classe)

    try:
        shutil.rmtree(dossier)
    except OSError:
        pass


if __name__ == "__main__":
    main()
