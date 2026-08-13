"""v39 — P14 : LA PROMOTION PAR CROISSANCE.

    « L'enfance n'a pas de promotions. »

Aucun enfant n'est téléporté dans un monde neuf le jour où il apprend à marcher — et on
ne lui efface pas la mémoire pour fêter ça. Or c'est exactement ce que fait le cursus :

    promotion  ->  env.close()  ->  creer_env(nouveau)  ->  reinitialiser_niveau()

H18 a montré la conséquence, mesurée : 4 repères `goal` écrits, 3 promotions, **0
survivant**. Le repère du but naît AU TICK DE LA VICTOIRE, donc quelques ticks avant la
promotion qu'il déclenche. L'agent perd sa carte du but à l'instant précis où il vient de
prouver qu'il l'avait acquise.

Ce banc teste l'alternative : **la carte GRANDIT autour de l'agent** au lieu d'être
remplacée. Le 5×5 reste littéralement *dans* le 8×8.

    ┌─────┐          ┌────────┐
    │ 5×5 │    ->    │ 5×5    │   le vécu reste valide
    └─────┘          │     ~~ │   l'inconnu est ajouté autour
                     └────────┘

C'est possible parce que le cursus v38 est **une seule tâche à 6 échelles**
(`DoorKey` 5×5 → 16×16) : une seule compétence change entre deux paliers voisins, donc
rien ne justifie de tout jeter.

--- Ce qui persiste, ce qui se réarme ---

    PERSISTE (c'est le but)              | SE RÉARME (sinon plus de tâche)
    -------------------------------------|--------------------------------
    la topologie déjà connue             | le but, reposé loin
    la position de l'agent               | la clé, reposée au sol
    la mémoire spatiale ENTIÈRE          | la porte, refermée et verrouillée
    l'empreinte de type (v39.0)          |

--- ⚠️ Le risque, instrumenté d'avance ---

Une carte qui grandit sans jamais se renouveler peut devenir un monde appris par cœur —
c'est le piège de `Empty-5x5` (1 seule configuration, H5). La croissance doit donc
**ajouter de l'inconnu**, pas seulement de la surface : la zone ajoutée reçoit de
nouveaux murs et de nouvelles ressources, tirés au sort.

Lancement (depuis la racine) :

    PYTHONPATH=src:experiences/v38 python experiences/v39/v39_p14_croissance.py \
        --jours 400 --graine 22 --croissance --brain brains/xxx.brain
"""
import argparse
import os
import random
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "experiences/v38")
os.environ.setdefault("WANDB_MODE", "offline")

import torch
from minigrid.core.grid import Grid
from minigrid.core.world_object import Door, Goal, Key, Wall

from naulthene.cerveau import noyau as N

# Les six échelles de la même tâche — identiques à 2a, pour rester comparable.
TAILLES = [5, 6, 8, 10, 12, 16]


def _grille_de(env):
    return env.unwrapped


def agrandir_monde(env, nouvelle_taille, rng):
    """Fait GRANDIR la grille autour de l'agent, sans rien détruire de connu.

    L'ancienne grille est recopiée telle quelle dans le coin haut-gauche de la nouvelle ;
    la bordure de murs est reconstruite au nouveau périmètre ; la zone gagnée reçoit de
    l'inconnu (murs épars + ressources), pour que grandir ne soit pas seulement « plus de
    vide ».

    Retourne False si la taille demandée n'est pas une croissance (sécurité).
    """
    e = _grille_de(env)
    ancienne = e.grid.width
    if nouvelle_taille <= ancienne:
        return False

    ancienne_grille = e.grid
    neuve = Grid(nouvelle_taille, nouvelle_taille)

    # 1. Recopie de l'ancien monde, EN L'ÉTAT — c'est tout l'intérêt de la manœuvre.
    #    On saute l'ancienne bordure droite/basse : elle devient de l'intérieur.
    for x in range(ancienne):
        for y in range(ancienne):
            objet = ancienne_grille.get(x, y)
            bord_ancien = (x == ancienne - 1) or (y == ancienne - 1)
            if bord_ancien and isinstance(objet, Wall):
                continue          # ce mur n'est plus une frontière : il disparaît
            if objet is not None:
                neuve.set(x, y, objet)

    # 2. La nouvelle bordure.
    neuve.wall_rect(0, 0, nouvelle_taille, nouvelle_taille)

    # --- v39-fix (R4) : PROLONGER LE MUR DE SÉPARATION ---
    #
    # 🔴 CE QUE ÇA CORRIGE (mesuré par BFS sur 200 configurations) : **92 %** des cartes
    # agrandies étaient solvables SANS clé ni porte.
    #
    # Dans DoorKey, le mur intérieur ne sépare la carte en deux pièces que parce qu'il
    # BUTTE sur la bordure extérieure. En agrandissant, la bordure recule — mais le mur
    # garde sa longueur d'origine, ne touche plus rien, et l'agent le contourne :
    #
    #     AVANT (5×5)        APRÈS, sans ce correctif (8×8)
    #       #####              ########
    #       #.D.#              #.D....#
    #       #@#.#              #@#...G#    ← le mur s'arrête ici
    #       #k#G#              #k#....#    ← on passe par-dessous
    #       #####              #......#
    #
    # La séparation en deux pièces est L'INVARIANT DE LA TÂCHE : elle doit survivre à
    # l'agrandissement au même titre que la clé et la porte. On prolonge donc la colonne
    # du mur intérieur jusqu'à la nouvelle bordure.
    colonne_mur = None
    for x in range(1, ancienne - 1):
        # la colonne de séparation est celle qui porte la porte
        if any(type(ancienne_grille.get(x, y)).__name__ == "Door"
               for y in range(ancienne)):
            colonne_mur = x
            break
    if colonne_mur is not None:
        for y in range(1, nouvelle_taille - 1):
            if neuve.get(colonne_mur, y) is None:
                neuve.set(colonne_mur, y, Wall())

    # 3. De l'INCONNU dans la zone gagnée (sinon on n'ajoute que du vide, et le monde
    #    devient un couloir appris par cœur — le piège de H5).
    cases_neuves = [(x, y)
                    for x in range(1, nouvelle_taille - 1)
                    for y in range(1, nouvelle_taille - 1)
                    if (x >= ancienne - 1 or y >= ancienne - 1)
                    and neuve.get(x, y) is None]
    rng.shuffle(cases_neuves)
    n_murs = max(1, len(cases_neuves) // 12)
    for (x, y) in cases_neuves[:n_murs]:
        neuve.set(x, y, Wall())

    e.grid = neuve
    e.width = nouvelle_taille
    e.height = nouvelle_taille
    return True


def rearmer_tache(env, rng):
    """Repose un but atteignable, remet la clé au sol, reverrouille la porte.

    Repris tel quel de 2a (`_rearmer_tache`) : sans ce réarmement, la continuité rend la
    tâche triviale — trois états sont absorbants (clé en main, porte ouverte, souvenirs
    figés). Vérifié au smoke test de 2a : portage 100 %, 1 souvenir figé.
    """
    e = _grille_de(env)
    ax, ay = int(e.agent_pos[0]), int(e.agent_pos[1])

    def _zone_sans_porte(grille_env, depart):
        """Cases atteignables sans franchir de porte (une porte verrouillée = un mur)."""
        g = grille_env.grid
        vus, pile = {depart}, [depart]
        while pile:
            x, y = pile.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if not (0 <= n[0] < g.width and 0 <= n[1] < g.height) or n in vus:
                    continue
                if type(g.get(*n)).__name__ in ("Wall", "Door"):
                    continue
                vus.add(n)
                pile.append(n)
        return vus

    def libres():
        return [(x, y) for x in range(1, e.grid.width - 1)
                for y in range(1, e.grid.height - 1)
                if e.grid.get(x, y) is None and (x, y) != (ax, ay)]

    # Le but : retiré, reposé LOIN (un but sous les pieds ne demande aucun déplacement).
    for x in range(e.grid.width):
        for y in range(e.grid.height):
            if isinstance(e.grid.get(x, y), Goal):
                e.grid.set(x, y, None)
    cases = libres()
    if not cases:
        return False

    # v39-fix (R5) : le but doit rester DERRIÈRE la porte — même correctif que 2a.
    # Sans lui, reposer le but « loin » suffisait à le placer dans la pièce de départ,
    # rendant clé et porte inutiles (mesuré : jusqu'à 48,7 % des cartes en 16×16).
    zone_ouverte = _zone_sans_porte(e, (ax, ay))
    derriere = [p for p in cases if p not in zone_ouverte]
    candidates = derriere if derriere else cases

    dmax = max(abs(x - ax) + abs(y - ay) for x, y in candidates)
    loin = [p for p in candidates if abs(p[0] - ax) + abs(p[1] - ay) >= dmax * 0.5]
    gx, gy = loin[rng.randrange(len(loin))]
    e.grid.set(gx, gy, Goal())

    # La porte : refermée et reverrouillée — c'est la compétence centrale de DoorKey.
    for x in range(e.grid.width):
        for y in range(e.grid.height):
            o = e.grid.get(x, y)
            if isinstance(o, Door):
                o.is_open = False
                o.is_locked = True

    # La clé : si l'agent la tient, elle retourne au sol.
    if getattr(e, "carrying", None) is not None:
        cases = libres()
        if cases:
            kx, ky = cases[rng.randrange(len(cases))]
            e.grid.set(kx, ky, e.carrying)
            e.carrying = None

    e.step_count = 0
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jours", type=int, default=400)
    p.add_argument("--brain", type=str, required=True)
    p.add_argument("--graine", type=int, default=None)
    p.add_argument("--croissance", action="store_true",
                   help="active la croissance (sans ce flag = TÉMOIN, promotions classiques)")
    a = p.parse_args()

    if a.graine is not None:
        torch.manual_seed(a.graine)
        N.np.random.seed(a.graine)
        random.seed(a.graine)

    rng = random.Random(a.graine or 0)

    # Même configuration que 2a, pour rester comparable.
    N.BUS_REFERENCE_INITIAL = 64
    N.PROGRAMME[:] = [(f"MiniGrid-DoorKey-{t}x{t}-v0", f"DoorKey {t}×{t}") for t in TAILLES]
    N.TAUX_PROMOTION = 0.35
    N.VICTOIRES_REQUISES = 1

    stats = {"croissances": 0, "continuations": 0}

    if a.croissance:
        # --- LE CŒUR DE P14 : la promotion ne remplace plus le monde, elle l'agrandit ---
        #
        # ⚠️ La séquence du noyau (noyau.py:5581-5584) est :
        #       etat.env.close()  ->  creer_env(...)  ->  reinitialiser_niveau()
        #
        # `close()` s'exécute AVANT `creer_env`, donc au moment où notre remplaçant est
        # appelé, l'environnement courant est déjà fermé. On ne peut pas le récupérer
        # depuis l'intérieur de `creer_env` : il faut le garder par ailleurs. C'est le
        # rôle de `etat_ref`, alimenté par le neutralisant de `close()` ci-dessous —
        # sur un env MiniGrid pur, `close()` ne libère aucune ressource système, le
        # neutraliser est sans effet de bord.
        vrai_creer = N.creer_env
        etat_ref = {}

        # ⚠️ Deux pièges trouvés au smoke test, et corrigés ici :
        #
        # 1. `close()` est appelé sur un env EMBALLÉ (wrappers gym) : patcher
        #    `gymnasium.Env.close` ne l'intercepte donc pas de façon fiable. On mémorise
        #    plutôt le monde à sa CRÉATION, ce qui est le seul point de passage garanti.
        # 2. `persistance.py` fait `from ...noyau import creer_env` À L'IMPORT : sa
        #    référence est figée et ne verrait jamais notre remplaçant. On patche donc
        #    les deux espaces de noms (voir plus bas).
        #
        # Sans ces deux corrections : « 0 croissance » alors que 3 promotions réelles
        # avaient bien eu lieu — le hook semblait posé et ne servait à rien.

        def creer_env_croissant(env_id, dim_visuelle, *args, **kwargs):
            """Au premier appel : création normale. Ensuite : on AGRANDIT l'existant."""
            env_courant = etat_ref.get("env")
            try:
                taille = int(env_id.split("DoorKey-")[1].split("x")[0])
            except (IndexError, ValueError):
                taille = None

            if env_courant is not None and taille is not None \
                    and agrandir_monde(env_courant, taille, rng):
                stats["croissances"] += 1
                rearmer_tache(env_courant, rng)
                print(f"   🌱 [CROISSANCE] le monde grandit vers {taille}×{taille} — "
                      f"le vécu reste valide, l'inconnu est ajouté autour", flush=True)
                return env_courant

            neuf = vrai_creer(env_id, dim_visuelle, *args, **kwargs)
            # Le noyau fait `etat.env.close()` JUSTE AVANT d'appeler `creer_env` : sur un
            # env MiniGrid pur, `close()` ne libère aucune ressource système, mais il
            # rendrait l'objet inutilisable pour la croissance. On le neutralise sur
            # l'INSTANCE (pas sur la classe : moins intrusif, et ça survit aux wrappers).
            neuf.close = lambda *a, **k: None
            etat_ref["env"] = neuf      # seul point de passage garanti
            return neuf

        N.creer_env = creer_env_croissant

        # ⚠️ `persistance.py` fait `from ...noyau import creer_env` À L'IMPORT : sa
        # référence est donc figée et ne verrait jamais notre remplaçant. Le premier
        # smoke test l'a montré — « 0 croissance » alors que le hook semblait posé.
        # On patche donc les deux espaces de noms.
        from naulthene.cerveau import persistance as _persist
        _persist.creer_env = creer_env_croissant

        # La mémoire NE DOIT PAS être effacée : les coordonnées restent valides puisque
        # l'ancienne carte est incluse dans la nouvelle. C'est tout le propos de P14.
        N.MemoireEpisodiqueSpatiale.reinitialiser_niveau = lambda self: None

    nom = "P14_CROISSANCE" if a.croissance else "P14_TEMOIN"
    print(f"\n🌱 v39 P14 — {nom}   (graine {a.graine})\n", flush=True)
    print("   la carte grandit autour de l'agent, la mémoire survit"
          if a.croissance else "   promotions classiques : nouveau monde, mémoire effacée")
    print(flush=True)

    import v38_2a_continuite as X
    sys.argv = ["x", "--jours", str(a.jours), "--graine", str(a.graine),
                "--continu", "--patience-surface", "--brain", a.brain]
    try:
        X.main()
    except SystemExit:
        pass

    print(f"\n✅ {nom} — {stats['croissances']} croissance(s) de monde", flush=True)


if __name__ == "__main__":
    main()
