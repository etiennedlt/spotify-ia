import speech_recognition as sr
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from thefuzz import process, fuzz
from plyer import notification

# ==========================================
# CONFIGURATIONS PRINCIPALES (MODIFIABLES ICI)
# ==========================================
NOM_PLAYLIST_CIBLE = "All"  # Nom de la playlist principale
DUREE_POPUP = 10            # Temps d'affichage du pop-up en secondes

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


def afficher_popup(titre, message):
    """Affiche une notification pop-up sur le bureau en bas à gauche."""
    try:
        notification.notify(
            title=titre,
            message=message,
            app_name="Assistant Spotify",
            timeout=DUREE_POPUP,
            pos="bottom_right"  # Demande d'affichage en bas à gauche
        )
    except Exception:
        # Fallback si l'OS ne supporte pas le positionnement direct
        notification.notify(
            title=titre,
            message=message,
            app_name="Assistant Spotify",
            timeout=DUREE_POPUP
        )


def trouver_playlist_par_nom(nom_cherche):
    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        if nom_cherche.lower() == playlist['name'].lower():
            return playlist['id']
    return None


print("Assistant vocal prêt. Dites 'coucou spotify' suivi de votre commande...")

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
            # COMMANDES DE CONTRÔLE DE LECTURE (LAXISTES)
            # ==========================================
            mots_passe = ["passe", "suivant", "next", "pas", "passer", "paps"]
            mots_comeback = ["come-back", "come back", "comback", "précédent", "retour", "reviens", "recule"]
            mots_restart = ["restart", "reste", "recommence", "depuis le début", "début", "reset", "redémarre", "restar"]

            if any(mot in commande for mot in mots_passe):
                sp.next_track()
                print("⏭️ Morceau suivant !")
                afficher_popup("Spotify Controls", "⏭️ Morceau suivant !")
                continue

            elif any(mot in commande for mot in mots_comeback):
                sp.previous_track()
                print("⏮️ Morceau précédent !")
                afficher_popup("Spotify Controls", "⏮️ Morceau précédent !")
                continue

            elif any(mot in commande for mot in mots_restart):
                sp.seek_track(0)
                print("🔄 Morceau redémarré au début !")
                afficher_popup("Spotify Controls", "🔄 Morceau redémarré au début !")
                continue

            # --- DICTIONNAIRE D'ASSOCIATION POUR HOUDI ---
            corrections_houdi = {
                " opi": "op houdi",
                " op": "op houdi",
                " houdy": "houdi",
                " oudi": "houdi",
                " audi": "houdi",
                " haut dit": "houdi",
                " ou dit": "houdi"
            }

            for faux_mot, vrai_mot in corrections_houdi.items():
                if faux_mot in commande:
                    commande = commande.replace(faux_mot, vrai_mot)
                    print(f"Correction phonétique appliquée : '{faux_mot}' -> '{vrai_mot}'")

            # ==========================================
            # CAS 2 : Ajouter à la playlist (RAPIDE)
            # ==========================================
            if "old" in commande or "playlist" in commande or "liste" in commande:
                morceau_cherche = (commande
                                   .replace("playlist", "")
                                   .replace("liste", "")
                                   .replace("old", "")
                                   .replace("dans", "")
                                   .replace("à", "")
                                   .replace("la", "")
                                   .strip())

                if morceau_cherche:
                    print(f"Recherche pour la playlist '{NOM_PLAYLIST_CIBLE}' : '{morceau_cherche}'")

                    resultats = sp.search(q=morceau_cherche, type='track', limit=1)
                    tracks = resultats['tracks']['items']

                    if tracks:
                        track_uri = tracks[0]['uri']
                        track_name = tracks[0]['name']
                        artist_name = tracks[0]['artists'][0]['name']

                        playlist_id = trouver_playlist_par_nom(NOM_PLAYLIST_CIBLE)
                        if playlist_id:
                            sp.playlist_add_items(playlist_id, [track_uri])
                            msg = f"'{track_name}' de {artist_name} ajouté à '{NOM_PLAYLIST_CIBLE}'."
                            print(f"Succès ! {msg}")
                            afficher_popup(f"Playlist {NOM_PLAYLIST_CIBLE} 🎵", msg)
                        else:
                            print(f"Je n'ai pas trouvé la playlist '{NOM_PLAYLIST_CIBLE}'.")
                    else:
                        print(f"Désolé, je n'ai pas trouvé la chanson '{morceau_cherche}' sur Spotify.")
                else:
                    print("Vous n'avez pas précisé le morceau à ajouter à la playlist !")

            # ==========================================
            # CAS 1 : Ajouter à la FILE D'ATTENTE (RAPIDE)
            # ==========================================
            elif any(mot in commande for mot in ["file", "fail", "fil", "five", "feel", "fille"]):
                morceau_cherche = (commande
                                   .replace("file", "")
                                   .replace("fail", "")
                                   .replace("fille", "")
                                   .replace("feel", "")
                                   .replace("fil", "")
                                   .replace("five", "")
                                   .replace("d'attente", "")
                                   .replace("ajoute", "")
                                   .replace("à", "")
                                   .strip())

                if morceau_cherche:
                    print(f"Recherche prioritaire dans '{NOM_PLAYLIST_CIBLE}' pour : '{morceau_cherche}'")

                    playlist_id = trouver_playlist_par_nom(NOM_PLAYLIST_CIBLE)
                    meilleur_track = None

                    if playlist_id:
                        playlist_tracks = sp.playlist_items(playlist_id, limit=100, fields='items(track(name, artists, uri))')
                        pistes_playlist = []

                        for item in playlist_tracks.get('items', []):
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

                    if meilleur_track:
                        track_uri = meilleur_track['uri']
                        track_name = meilleur_track['name']
                        artist_name = meilleur_track['artists'][0]['name']

                        sp.add_to_queue(track_uri)
                        msg = f"'{track_name}' de {artist_name} ajouté à la file d'attente."
                        print(f"Succès ! {msg}")
                        afficher_popup("File d'attente 🎧", msg)
                    else:
                        print(f"Non trouvé dans '{NOM_PLAYLIST_CIBLE}'. Recherche globale pour : '{morceau_cherche}'")
                        resultats = sp.search(q=morceau_cherche, type='track', limit=1)
                        tracks = resultats['tracks']['items']

                        if tracks:
                            meilleur_track = tracks[0]
                            track_uri = meilleur_track['uri']
                            track_name = meilleur_track['name']
                            artist_name = meilleur_track['artists'][0]['name']

                            sp.add_to_queue(track_uri)
                            msg = f"'{track_name}' de {artist_name} ajouté à la file d'attente."
                            print(f"Succès ! {msg}")
                            afficher_popup("File d'attente 🎧", msg)
                        else:
                            print(f"Désolé, aucun résultat pour '{morceau_cherche}'.")
                else:
                    print("Vous n'avez pas précisé le morceau à ajouter !")

    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f"Erreur avec le service de reconnaissance vocale : {e}")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")