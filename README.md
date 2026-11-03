Mon Assistant Vocal Spotify 
assistant vocal en Python pour pouvoir contrôler Spotify en arrière-plan sans avoir à quitter mes parties. 
Il écoute en continu, réagit à un mot de réveil et gère mes musiques, mes playlists, le volume ou la file d'attente à la voix.

Ce que fait mon projet : 
Réveil vocal : S'agit dès que je dis Coucou Spotify ou des variantes comme Ouvre Spotify.
Lecture ciblée et fiable : Utilise le contexte de l'album pour lancer un morceau spécifique immédiatement en arrière-plan, sans bloquer. 
Recherche de playlists intelligente : Reconnaît mes playlists grâce à une recherche approximative avec TheFuzz même si je bégaye un peu ou prononce mal. 
File d'attente prioritaire : Permet d'ajouter un son à ma file d'attente principale sans fausse manipulation. 
Contrôle total : Je peux passer un morceau, reculer, mettre en pause, reprendre ou régler le volume en pourcentage. Le script cible automatiquement mon PC pour éviter les erreurs d'appareils. 
Optimisation CPU : Intègre des pauses pour ne pas faire laguer mon PC en plein jeu. 
Notifications bureau : Affiche des pop-ups discrets pour me confirmer chaque action.

Les technologies utilisées 
Python, Spotipy pour l'API Spotify, SpeechRecognition pour la reconnaissance vocale Google, 
TheFuzz pour le matching de texte, et Plyer pour les notifications Windows.

Installation Étape 1 : Je clone le projet en tapant git clone https://github.com/etiennedlt/spotify-ia.git puis cd spotify-ia. 
Étape 2 : J'installe les dépendances avec la commande pip install spotipy SpeechRecognition thefuzz plyer. 
Étape 3 : Je configure mon fichier config.py avec mes clés Spotify en renseignant CLIENT_ID, CLIENT_SECRET et REDIRECT_URI. 
Étape 4 : Je lance le tout en exécutant python main.py.
