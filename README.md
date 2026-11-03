Mon Assistant Vocal Spotify (Gaming Mode) fonctionne grâce à l'association de deux scripts principaux en Python qui tournent ensemble pour l'écoute et les actions.

Du côté de la structure, tout repose sur main.py et fonctions.py. Le script principal main.py utilise la bibliothèque SpeechRecognition pour écouter en continu le microphone de mon PC. Il filtre les bruits ambiants et reste en veille jusqu'à entendre le mot de réveil, comme Coucou Spotify. Dès qu'il l'entend, il isole la commande qui suit et l'analyse selon un ordre logique de priorités.

Pour ce qui est des actions, il fait appel au fichier fonctions.py qui communique avec Spotify via la bibliothèque Spotipy. Pour contourner les limitations de l'API en arrière-plan qui posent souvent problème en jeu, chaque lancement de morceau recherche la piste et utilise le contexte de son album pour forcer la lecture proprement. J'utilise aussi la bibliothèque TheFuzz pour faire de la recherche textuelle approximative, ce qui me permet de retrouver mes playlists ou mes morceaux même si la reconnaissance vocale fait de petites fautes.

Enfin, pour éviter les erreurs de lecture lorsque Spotify est fermé ou en veille, le code récupère l'identifiant de mon PC en tant qu'appareil actif et envoie les commandes de lecture, de pause ou de navigation de manière sécurisée. Des notifications visuelles discrètes s'affichent sur le bureau via Plyer pour me confirmer chaque action, et le tout intègre des pauses temporelles pour ne pas consommer de ressources et préserver les performances de mon PC pendant que je joue.

Installation
Étape 1 : Je clone le projet en tapant git clone https://github.com/etiennedlt/spotify-ia.git puis cd spotify-ia.
Étape 2 : J'installe les dépendances avec la commande pip install spotipy SpeechRecognition thefuzz plyer.
Étape 3 : Je configure mon fichier config.py avec mes clés Spotify en renseignant CLIENT_ID, CLIENT_SECRET et REDIRECT_URI.
Étape 4 : Je lance le tout en exécutant python main.py.
