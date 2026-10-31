import speech_recognition as sr
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from thefuzz import process, fuzz

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
        if nom_cherche.lower() == playlist['name'].lower():
            return playlist['id']
    return None


with microphone as source:
    recognizer.adjust_for_ambient_noise(source)

while True:
    try:
        with microphone as source:
            print("\nJ'écoute...")
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)

        texte = recognizer.recognize_google(audio, language="fr-FR").lower()
        print(f"Vous avez dit : {texte}")

        if "coucou spotify" in texte or "coupe spotify" in texte:
            print("✨ Mot de réveil détecté !")

            commande = texte.replace("coucou spotify", "").replace("coupe spotify", "").strip()

            if not commande:
                print("Je vous écoute... (veuillez donner votre commande)")
                continue

            # ==========================================
            # NOUVELLES COMMANDES DE CONTRÔLE DE LECTURE
            # ==========================================
            if "passe" in commande or "suivant" in commande or "next" in commande:
                sp.next_track()
                print("⏭️ Morceau suivant !")
                continue

            elif "come-back" in commande or "come back" in commande or "précédent" in commande or "retour" in commande:
                sp.previous_track()
                print("⏮️ Morceau précédent !")
                continue

            elif "restart" in commande or "recommence" in commande or "depuis le début" in commande:
                sp.seek_track(0)
                print("🔄 Morceau redémarré au début !")
                continue

            # --- DICTIONNAIRE D'ASSOCIATION POUR HOUDI ---
            corrections_houdi = {
                "opi": "op houdi",
                "op": "op houdi",
                "houdy": "houdi",
                "oudi": "houdi",
                "audi": "houdi",
                "haut dit": "houdi",
                "ou dit": "houdi"
            }

            for faux_mot, vrai_mot in corrections_houdi.items():
                if faux_mot in commande:
                    commande = commande.replace(faux_mot, vrai_mot)
                    print(f"Correction phonétique appliquée : '{faux_mot}' -> '{vrai_mot}'")

            # ==========================================
            # CAS 1 : Ajouter à la FILE D'ATTENTE
            # ==========================================
            if "file" in commande or "fail" in commande or "fil" in commande or "five" or "feel" in commande:
                morceau_cherche = (commande
                                   .replace("file", "")
                                   .replace("fail", "")
                                   .replace("fil", "")
                                   .replace("five", "")
                                   .replace("d'attente", "")
                                   .replace("ajoute", "")
                                   .replace("à", "")
                                   .strip())

                if morceau_cherche:
                    print(f"Recherche prioritaire (approximative) dans 'All' pour : '{morceau_cherche}'")

                    playlist_id = trouver_playlist_par_nom("All")
                    meilleur_track = None

                    if playlist_id:
                        playlist_tracks = sp.playlist_items(playlist_id, fields='items(track(name, artists, uri))')
                        pistes_playlist = []

                        for item in playlist_tracks['items']:
                            track = item.get('track')
                            if track:
                                text_ref = f"{track['artists'][0]['name']} {track['name']}".lower()
                                pistes_playlist.append((text_ref, track))

                        if pistes_playlist:
                            dict_choix = {text_ref: track for text_ref, track in pistes_playlist}
                            resultat, score = process.extractOne(
                                morceau_cherche,
                                dict_choix.keys(),
                                scorer=fuzz.partial_ratio
                            )

                            if score >= 70:
                                meilleur_track = dict_choix[resultat]
                                print(f"Correspondance approximative trouvée ({score}%) : '{resultat}'")

                    if meilleur_track:
                        track_uri = meilleur_track['uri']
                        track_name = meilleur_track['name']
                        artist_name = meilleur_track['artists'][0]['name']

                        sp.add_to_queue(track_uri)
                        print(f"Succès ! '{track_name}' de {artist_name} (trouvé dans 'All') a été ajouté à la file d'attente.")
                    else:
                        print(f"Non trouvé dans 'All'. Recherche globale sur Spotify pour : '{morceau_cherche}'")
                        resultats = sp.search(q=morceau_cherche, type='track', limit=10)
                        tracks = resultats['tracks']['items']

                        if tracks:
                            meilleur_track = tracks[0]
                            track_uri = meilleur_track['uri']
                            track_name = meilleur_track['name']
                            artist_name = meilleur_track['artists'][0]['name']

                            sp.add_to_queue(track_uri)
                            print(f"Succès ! '{track_name}' de {artist_name} (recherche globale) a été ajouté à la file d'attente.")
                        else:
                            print(f"Désolé, je n'ai trouvé aucun résultat pour '{morceau_cherche}'.")
                else:
                    print("Vous n'avez pas précisé le morceau à ajouter !")

            # ==========================================
            # CAS 2 : Ajouter à la playlist ALL
            # ==========================================
            elif "old" in commande or "playlist" in commande or "liste" in commande:
                morceau_cherche = (commande
                                   .replace("playlist", "")
                                   .replace("liste", "")
                                   .replace("old", "")
                                   .replace("dans", "")
                                   .replace("à", "")
                                   .replace("la", "")
                                   .strip())

                if morceau_cherche:
                    print(f"Recherche pour la playlist 'All' : '{morceau_cherche}'")

                    resultats = sp.search(q=morceau_cherche, type='track', limit=1)
                    tracks = resultats['tracks']['items']

                    if tracks:
                        track_uri = tracks[0]['uri']
                        track_name = tracks[0]['name']
                        artist_name = tracks[0]['artists'][0]['name']

                        playlist_id = trouver_playlist_par_nom("All")
                        if playlist_id:
                            playlist_tracks = sp.playlist_items(playlist_id, fields='items(track(uri))')
                            existing_uris = [
                                item['track']['uri']
                                for item in playlist_tracks['items']
                                if item and item.get('track') and 'uri' in item['track']
                            ]

                            if track_uri in existing_uris:
                                print(f"'{track_name}' de {artist_name} est déjà présent dans votre playlist 'All'.")
                            else:
                                sp.playlist_add_items(playlist_id, [track_uri])
                                print(f"Succès ! '{track_name}' de {artist_name} a été ajouté à votre playlist 'All'.")
                        else:
                            print("Je n'ai pas trouvé la playlist 'All'.")
                    else:
                        print(f"Désolé, je n'ai pas trouvé la chanson '{morceau_cherche}' sur Spotify.")
                else:
                    print("Vous n'avez pas précisé le morceau à ajouter à la playlist !")

    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f"Erreur avec le service de reconnaissance vocale : {e}")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")