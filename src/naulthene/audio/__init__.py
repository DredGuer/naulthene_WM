"""
L'Hémisphère Audio — modalité vocale de Naulthène AGI.

- `hemisphere_audio` : traitement bas niveau (formants, MFCC, synthèse, micro,
  transcription Whisper).
- `lecons_vocales` : cache de références vocales générées via la synthèse
  vocale macOS (`say`).
- `professeur_gemma` : le "Professeur", appelle un modèle Gemma via Ollama en
  HTTP local (`http://localhost:11434`).
"""
