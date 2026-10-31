import speech_recognition as sr
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# --- 1. CONFIGURATION SPOTIFY ---
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-modify-playback-state user-read-playback-state playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public"
))

# --- 2. CONFIGURATION MICRO ---
recognizer = sr.Recognizer()
microphone = sr.Microphone()

print("Assistant vocal prêt. Dites 'coucou spotify' suivi de votre commande...")


def trouver_playlist_par_nom(nom_cherche):
    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        if nom_cherche.lower() in playlist['name'].lower():
            return playlist['id']
    return None


with microphone as source:
    recognizer.adjust_for_ambient_noise(source)

while True:
    try:
        with microphone as source:
            print("\nJ'écoute...")
            # Temps d'écoute étendu à 10 secondes pour ne pas être coupé
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)

        texte = recognizer.recognize_google(audio, language="fr-FR").lower()
        print(f"Vous avez dit : {texte}")

        if "coucou spotify" in texte or "coupe spotify" in texte:
            print("✨ Mot de réveil détecté !")

            commande = texte.replace("coucou spotify", "").replace("coupe spotify", "").strip()

            # CAS 1 : Vous voulez l'ajouter à la FILE D'ATTENTE (en disant "file")
            if "file" in commande:
                morceau_cherche = (commande
                                   .replace("file", "")
                                   .replace("d'attente", "")
                                   .replace("ajoute", "")
                                   .replace("à", "")
                                   .strip())

                print(f"Recherche pour la file d'attente : '{morceau_cherche}'")

                resultats = sp.search(q=morceau_cherche, type='track', limit=1)
                tracks = resultats['tracks']['items']

                if tracks:
                    track_uri = tracks[0]['uri']
                    track_name = tracks[0]['name']
                    artist_name = tracks[0]['artists'][0]['name']

                    sp.add_to_queue(track_uri)
                    print(f"Succès ! '{track_name}' de {artist_name} a été ajouté à la file d'attente.")
                else:
                    print("Désolé, je n'ai pas trouvé cette chanson sur Spotify.")

            # CAS 2 : Vous voulez l'ajouter à la playlist ALL (en disant "old", "playlist" ou "liste")
            elif "old" in commande or "playlist" in commande or "liste" in commande:
                morceau_cherche = (commande
                                   .replace("playlist", "")
                                   .replace("liste", "")
                                   .replace("old", "")
                                   .replace("dans", "")
                                   .replace("à", "")
                                   .replace("la", "")
                                   .strip())

                print(f"Recherche pour la playlist 'all' : '{morceau_cherche}'")

                resultats = sp.search(q=morceau_cherche, type='track', limit=1)
                tracks = resultats['tracks']['items']

                if tracks:
                    track_uri = tracks[0]['uri']
                    track_name = tracks[0]['name']
                    artist_name = tracks[0]['artists'][0]['name']

                    playlist_id = trouver_playlist_par_nom("all")
                    if playlist_id:
                        sp.playlist_add_items(playlist_id, [track_uri])
                        print(f"Succès ! '{track_name}' de {artist_name} a été ajouté à votre playlist 'all'.")
                    else:
                        print("Je n'ai pas trouvé la playlist 'all'.")
                else:
                    print(f"Désolé, je n'ai pas trouvé la chanson '{morceau_cherche}' sur Spotify.")

            else:
                print("Commande non reconnue. Précisez 'file' ou 'old'.")

    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f"Erreur avec le service de reconnaissance vocale : {e}")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")