"""
Le Professeur Gemma (V22.0, expérimental) — Curriculum vocal & jugement périodique.

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test"), pas encore porté sur `agi_google_colab.py`. Voir
CONCEPTION_v22_audio.md §6 pour le contexte narratif complet.

Isolé du réseau de neurones (testable/mockable sans `AGI_Naulthene`) : ce module ne
connaît que des mots, des embeddings et des scores — jamais un tenseur PyTorch.

Appelle Ollama via son API HTTP locale (`localhost:11434`) plutôt que le module Python
`ollama` (absent du venv, l'API REST suffit avec `requests` seul — évite une dépendance
de plus pour un simple client HTTP).

⚠️ Contrainte mesurée (ce Mac, ce run) : `gemma4:e4b` met ~8 secondes pour une réponse
courte (modèle à raisonnement). C'est INCOMPATIBLE avec un jugement par tick RL — d'où
la séparation stricte : la récompense par tick vient de `hemisphere_audio.
recompense_formants` (déterministe, instantanée), Gemma n'intervient QUE pour :
  1. choisir la leçon du jour (curriculum vocal, peu fréquent) ;
  2. juger qualitativement en fin de leçon (périodique, pas par tick) ;
  3. produire l'embedding sémantique du mot (modèle d'embedding séparé, rapide).
"""

import json
import re

import numpy as np
import requests

OLLAMA_URL = "http://localhost:11434"
MODELE_PROFESSEUR = "gemma4:e4b"
MODELE_EMBEDDING = "tazarov/all-minilm-l6-v2-f32"  # 384 dims natives, réduites ensuite

TIMEOUT_GENERATION = 60.0   # secondes — Gemma e4b peut prendre ~8-20s selon le prompt
TIMEOUT_EMBEDDING = 15.0    # le modèle d'embedding est nettement plus rapide

# Curriculum vocal (voir CONCEPTION_v22_audio.md §7 et le plan v22.0), symétrique au
# cursus MiniGrid — réutilise GestionnaireCursusAbnegation (agi_local_test.py) côté
# appelant pour la logique de promotion par succès cumulés ; ce module ne fait que
# fournir le CONTENU de chaque palier.
#
# Paliers 12-14 (v25.0, Paradigme Bébé, expérimental) : extension du curriculum
# d'origine (11 paliers, v22.0) pour couvrir le mot "porte" et une première
# combinatoire Action+Objet minimale (roadmap "0→4 ans"). Chaque nouveau mot est géré
# automatiquement par lecons_vocales.CacheReferencesVocales (référence `say`, clé =
# mot) — sa voyelle dominante ("porte"→"o", "encore"→"o") doit rester une clé connue de
# hemisphere_audio.VOYELLES_CIBLES, réutilisée par _mot_cible_du_palier comme cible F1/F2
# de repli tant qu'aucune cible de syllabe/mot dédiée n'existe. Si tu ajoutes un mot
# dont AUCUNE voyelle du mot n'est dans VOYELLES_CIBLES, il faut d'abord y ajouter cette
# voyelle (voir hemisphere_audio.py). IMPORTANT : toute modification de cette liste doit
# être répercutée dans agi_local_test.py::NB_PALIERS_VOCAUX (utilisé par
# seuil_jour_vocal_reussi pour interpoler le seuil de promotion) — sinon l'interpolation
# du seuil École de Rattrapage devient incohérente avec la longueur réelle du curriculum.
CURRICULUM_VOCAL = [
    {"palier": 1, "nom": "Vocaliser", "cible": None},       # n'importe quel son voisé
    {"palier": 2, "nom": "Voyelle 'a'", "cible": "a"},
    {"palier": 3, "nom": "Voyelle 'e'", "cible": "e"},
    {"palier": 4, "nom": "Voyelle 'i'", "cible": "i"},
    {"palier": 5, "nom": "Voyelle 'o'", "cible": "o"},
    {"palier": 6, "nom": "Voyelle 'u'", "cible": "u"},
    {"palier": 7, "nom": "Syllabe 'ba'", "cible": "ba"},
    {"palier": 8, "nom": "Syllabe 'ma'", "cible": "ma"},
    {"palier": 9, "nom": "Syllabe 'pa'", "cible": "pa"},
    {"palier": 10, "nom": "Mot 'papa'", "cible": "papa"},
    {"palier": 11, "nom": "Mot 'maman'", "cible": "maman"},
    {"palier": 12, "nom": "Mot 'porte'", "cible": "porte"},
    {"palier": 13, "nom": "Combinatoire 'ouvre porte'", "cible": "ouvre porte"},
    {"palier": 14, "nom": "Combinatoire 'prends clé'", "cible": "prends clé"},
]


def _appeler_ollama_generate(prompt: str, modele: str = MODELE_PROFESSEUR,
                              timeout: float = TIMEOUT_GENERATION) -> str:
    """Appel bas niveau à /api/generate (non-streaming, réponse complète). Isolé pour
    pouvoir être mocké dans les tests — ne dépend d'aucun état du réseau de neurones."""
    reponse = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": modele, "prompt": prompt, "stream": False},
        timeout=timeout,
    )
    reponse.raise_for_status()
    return reponse.json()["response"]


def embedding_semantique(mot: str, dim_cible: int = 32) -> np.ndarray:
    """Mot → vecteur DIM_EMBED_SEMANTIQUE (32 dims par défaut, voir agi_local_test.py).
    Le modèle natif renvoie 384 dims ; réduction par moyenne de blocs contigus (simple,
    déterministe, sans entraînement supplémentaire) plutôt qu'une vraie projection
    apprise — suffisant pour donner un signal sémantique grossier à `porte_auditive`,
    qui apprendra à l'exploiter comme le reste de son entrée."""
    reponse = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": MODELE_EMBEDDING, "prompt": mot},
        timeout=TIMEOUT_EMBEDDING,
    )
    reponse.raise_for_status()
    vecteur = np.array(reponse.json()["embedding"], dtype=np.float32)

    if vecteur.shape[0] == dim_cible:
        return vecteur
    # Réduction par moyenne de blocs contigus (384 -> dim_cible), padding si le modèle
    # natif renvoyait déjà moins que dim_cible (cas dégénéré, garde-fou).
    if vecteur.shape[0] < dim_cible:
        return np.pad(vecteur, (0, dim_cible - vecteur.shape[0]))
    taille_bloc = vecteur.shape[0] // dim_cible
    reste = vecteur.shape[0] - taille_bloc * dim_cible
    tronque = vecteur[:vecteur.shape[0] - reste] if reste else vecteur
    return tronque.reshape(dim_cible, taille_bloc).mean(axis=1).astype(np.float32)


def choisir_lecon(palier_actuel: int) -> dict:
    """Retourne le palier de curriculum courant (contenu, pas la logique de
    promotion — celle-ci reste dans GestionnaireCursusAbnegation, réutilisé côté
    appelant). Purement déterministe (table statique) : pas besoin d'appeler Gemma
    pour ça, on réserve les ~8s de latence au jugement qualitatif, plus rare."""
    for lecon in CURRICULUM_VOCAL:
        if lecon["palier"] == palier_actuel:
            return lecon
    return CURRICULUM_VOCAL[-1]  # dernier palier atteint, on y reste (fin de cursus vocal)


def juger_qualitatif(mot_cible: str, transcription_produite: str,
                      score_formants_moyen: float) -> dict:
    """Jugement PÉRIODIQUE (fin de leçon, pas par tick — voir avertissement en tête de
    fichier). Renvoie un score [0,1] et un commentaire pédagogique en français. Sur
    échec réseau/Ollama (timeout, modèle absent), retourne un score neutre plutôt que
    de faire planter la leçon — Gemma est un professeur, pas un composant critique du
    pipeline de récompense par tick (qui continue de tourner sur les formants seuls)."""
    prompt = (
        f"Tu es un professeur de langage qui évalue une IA en apprentissage de la "
        f"parole. Le mot/son cible était : \"{mot_cible}\". "
        f"Ce que l'IA a produit (transcrit automatiquement) : \"{transcription_produite}\". "
        f"Le score de proximité acoustique mesuré (formants) est de {score_formants_moyen:.2f} "
        f"sur 1.0. Réponds UNIQUEMENT au format JSON strict : "
        f'{{"score": <nombre entre 0 et 1>, "commentaire": "<une phrase encourageante en français>"}}'
    )
    try:
        texte = _appeler_ollama_generate(prompt)
        match = re.search(r"\{.*\}", texte, re.DOTALL)
        if match:
            donnees = json.loads(match.group(0))
            return {
                "score": float(np.clip(donnees.get("score", score_formants_moyen), 0.0, 1.0)),
                "commentaire": str(donnees.get("commentaire", "")),
            }
    except (requests.RequestException, json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"   ⚠️  Professeur Gemma indisponible pour le jugement qualitatif ({e}) — "
              f"repli sur le score de formants seul.")

    return {"score": float(score_formants_moyen), "commentaire": ""}
