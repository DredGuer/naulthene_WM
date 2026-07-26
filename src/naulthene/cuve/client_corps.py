"""
L'Environnement de Test (V21.0, expérimental) — Le Corps jetable.

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test") : il n'est PAS porté sur `agi_google_colab.py`. Il n'a
aucune intelligence propre — c'est un simple pilote de session qui ouvre une
connexion vers la Cuve (`daemon_cerveau.py`), la maintient un certain temps, puis la
referme. Jetable : tu peux l'allumer, l'éteindre, le modifier librement sans jamais
toucher au cerveau lui-même.

⚠️ Honnêteté architecturale (voir la note de limite assumée en tête de
`daemon_cerveau.py`) : dans cette itération, l'environnement MiniGrid réel tourne
CÔTÉ SERVEUR (dans la Cuve), pas ici. Les détecteurs biologiques/spatiaux de l'agent
ont besoin des internes MiniGrid (positions, grille, objets) que ce client ne pourrait
pas transmettre sans un protocole beaucoup plus riche. Ce script envoie donc un
paquet de perception au format prévu par le design (pour préparer un futur
découplage total), mais c'est la Cuve qui exécute réellement `env.step()` en
interne — la `vision` envoyée ici sert de signal de présence/heartbeat, PAS
l'observation consommée par le réseau. Ne pas laisser croire à un lecteur pressé du
code que ce client "fait tourner MiniGrid côté client" : ce n'est pas encore le cas.
"""

import argparse
import json
import socket
import time


DELAI_SECURITE_DECONNEXION = 2.0  # secondes de battement après fermeture de la socket,
                                   # pour laisser la Cuve terminer sa sauvegarde disque
                                   # avant que le process client ne rende la main


def lancer_corps_artificiel(host="127.0.0.1", port=9999, duree_ticks=2000, delai_entre_ticks=0.0,
                             continu=False):
    """Ouvre une session avec la Cuve et envoie des paquets de perception jusqu'à
    `duree_ticks` ticks — ou indéfiniment si `continu=True` (jusqu'à Ctrl+C/SIGTERM) —
    puis se déconnecte PROPREMENT.

    Sécurité de déconnexion (protège le cerveau contre une coupure en plein calcul) :
    un Ctrl+C peut survenir à N'IMPORTE QUEL moment de la boucle, y compris juste après
    `sendall` — c'est-à-dire pendant que la Cuve est en train de traiter le tick (et
    potentiellement une nuit complète avec écriture sur le disque, voir
    CuveDeMaintien._processus_nocturne). Fermer le socket immédiatement à cet instant ne
    corromprait PAS le fichier .brain (torch.save écrit sur un fichier temporaire puis
    fait un remplacement atomique, voir persistance.py), mais on attend quand même
    explicitement la dernière réponse du serveur avant de fermer, pour être certain que
    le tick en cours (et une éventuelle nuit qu'il aurait déclenchée) est bien terminé
    côté serveur avant que ce process ne quitte."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    print(f"🧠 Connexion au Cerveau Naulthène réussie ! ({host}:{port})"
          + (" — mode continu (Ctrl+C pour arrêter)" if continu else ""))

    i = 0
    interrompu = False
    try:
        while continu or i < duree_ticks:
            # Paquet de perception au format du protocole (voir readme.md, section
            # "Le Nerf Optique") — vision vide/heartbeat dans cette itération, voir
            # la note d'honnêteté architecturale en tête de fichier.
            perception = {
                'tick_client': i,
                'vision': [],
                'recompense_environnement': 0.0,
                'fin_episode': False,
            }
            try:
                client.sendall(json.dumps(perception).encode('utf-8'))
                data = client.recv(4096)
            except KeyboardInterrupt:
                # Le Ctrl+C est intercepté ICI, à l'intérieur même de l'échange
                # réseau : on a déjà envoyé le paquet, on attend la réponse en cours
                # avant de sortir plutôt que de couper immédiatement la socket.
                interrompu = True
                print("\n🛑 Arrêt demandé (Ctrl+C) — attente de la fin du tick en cours côté Cuve...")
                try:
                    client.settimeout(30.0)
                    data = client.recv(4096)
                except (socket.timeout, OSError):
                    data = b""
                break

            if not data:
                print("🔌 La Cuve a fermé la connexion en premier.")
                break
            reponse = json.loads(data.decode('utf-8'))

            if i % 200 == 0:
                infos = reponse.get('infos_internes', {})
                print(f"   tick {i:5d} — action reçue: {reponse.get('action')} | "
                      f"dopamine: {infos.get('dopamine', float('nan')):.3f} | "
                      f"faim: {infos.get('faim', float('nan')):.3f} | "
                      f"tick_absolu Cuve: {reponse.get('tick_absolu')}")

            if delai_entre_ticks > 0:
                time.sleep(delai_entre_ticks)
            i += 1

    except KeyboardInterrupt:
        interrompu = True
        print("\n🛑 Arrêt demandé (Ctrl+C).")
    finally:
        client.close()
        print("🔌 Socket fermée. Sécurisation : pause de "
              f"{DELAI_SECURITE_DECONNEXION:.0f}s pour laisser la Cuve écrire son "
              "cerveau sur le disque avant de rendre la main...")
        time.sleep(DELAI_SECURITE_DECONNEXION)
        etat_txt = "interrompue (Ctrl+C)" if interrompu else "terminée normalement"
        print(f"✅ Déconnexion {etat_txt}. Le cerveau s'est endormi (nuit complète ou "
              "micro-sieste) et a été sauvegardé côté Cuve — tu peux vérifier son log.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Corps jetable — client de test pour la Cuve Naulthène (v21.0)")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument("--ticks", type=int, default=2000, help="Nombre de ticks de la session (ignoré si --continu)")
    parser.add_argument("--continu", action="store_true", help="Tourne indéfiniment jusqu'à Ctrl+C, au lieu d'un nombre de ticks fixe")
    parser.add_argument("--delai", type=float, default=0.0, help="Délai (s) entre deux ticks, 0 = aussi vite que possible")
    args = parser.parse_args()

    lancer_corps_artificiel(host=args.host, port=args.port, duree_ticks=args.ticks,
                             delai_entre_ticks=args.delai, continu=args.continu)
