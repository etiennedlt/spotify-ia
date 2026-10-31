import os
import time
import speech_recognition as sr
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from thefuzz import process, fuzz
from plyer import notification

# ==========================================
# CONFIGURATIONS PRINCIPALES (MODIFIABLES ICI)
# ==========================================
NOM_PLAYLIST_CIBLE = "All"  # Nom de la playlist principale pour la file d'attente
DUREE_POPUP = 10  # Temps d'affichage du pop-up en secondes

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
    """Affiche une notification pop-up sur le bureau."""
    try:
        notification.notify(
            title=titre,
            message=message,
            app_name="Assistant Spotify",
            timeout=DUREE_POPUP,
            pos="bottom_left"
        )
    except Exception:
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
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=15)

        texte = recognizer.recognize_google(audio, language="fr-FR").lower()
        print(f"Vous avez dit : {texte}")

        if "coucou spotify" in texte or "coupe spotify" in texte or "écoute spotify" in texte or "ouvre spotify" in texte:
            print("✨ Mot de réveil détecté !")

            commande = (texte
                        .replace("coucou spotify", "")
                        .replace("coupe spotify", "")
                        .replace("écoute spotify", "")
                        .replace("ouvre spotify", "")
                        .strip())

            if not commande:
                print("Je vous écoute... (veuillez donner votre commande)")
                continue

            # ==========================================
            # COMMANDES DE CONTRÔLE DE LECTURE & VOLUME
            # ==========================================
            mots_passe = ["passe", "suivant", "next", "pas", "passer", "paps"]
            mots_comeback = ["come-back", "come back", "comback", "précédent", "retour", "reviens", "recule"]
            mots_restart = ["restart", "reste", "recommence", "depuis le début", "début", "reset", "redémarre",
                            "restar"]
            mots_pause = ["pause", "stop", "arrête", "interromps"]
            mots_play = ["play", "lance", "mets", "joue", "marche", "reprends"]

            if any(mot in commande for mot in mots_passe):
                sp.next_track()
                print("⏭️ Morceau suivant !")
                afficher_popup("Spotify Controls", "⏭️ Morceau suivant !")

            elif any(mot in commande for mot in mots_comeback):
                sp.previous_track()
                print("⏮️ Morceau précédent !")
                afficher_popup("Spotify Controls", "⏮️ Morceau précédent !")

            elif any(mot in commande for mot in mots_restart):
                sp.seek_track(0)
                print("🔄 Morceau redémarré au début !")
                afficher_popup("Spotify Controls", "🔄 Morceau redémarré au début !")

            elif any(mot in commande for mot in mots_pause):
                sp.pause_playback()
                print("⏸️ Lecture en pause.")
                afficher_popup("Spotify Controls", "⏸️ Musique en pause")

            elif any(mot in commande for mot in
                     mots_play) and "playlist" not in commande and "liste" not in commande and not any(
                    m in commande for m in ["chanson", "morceau", "titre"]):
                sp.start_playback()
                print("▶️ Lecture relancée !")
                afficher_popup("Spotify Controls", "▶️ Lecture relancée !")

            elif "volume" in commande or "son" in commande:
                mots_cmd = commande.split()
                volume_cible = None
                for mot in mots_cmd:
                    if mot.isdigit():
                        volume_cible = int(mot)
                        break

                if volume_cible is not None:
                    volume_cible = max(0, min(100, volume_cible))
                    sp.volume(volume_cible)
                    print(f"🔊 Volume réglé à {volume_cible}%")
                    afficher_popup("Spotify Volume", f"🔊 Volume : {volume_cible}%")
                else:
                    print("⚠️ Précisez un niveau de volume en pourcentage (ex: volume 50).")

            # ==========================================
            # COMMANDE : LANCER UNE PLAYLIST
            # ==========================================
            elif "playlist" in commande or "liste" in commande:
                playlists_disponibles = [
                    "wintersong", "cold winter", "All", "My world",
                    "Chlii2", "Honez", "Summer song", "instru",
                    "Rock", "Grosse prod", "chill vibe", "Kiff 2", "Just kiff"
                ]

                nom_demande = (commande
                               .replace("playlist", "")
                               .replace("liste", "")
                               .replace("lance", "")
                               .replace("mets", "")
                               .replace("la", "")
                               .replace("de", "")
                               .strip())

                if nom_demande:
                    playlists_lower = {p.lower(): p for p in playlists_disponibles}
                    meilleur_match_lower, score = process.extractOne(
                        nom_demande,
                        playlists_lower.keys(),
                        scorer=fuzz.partial_ratio
                    )

                    if score >= 40:
                        vrai_nom_playlist = playlists_lower[meilleur_match_lower]
                        print(f"Playlist reconnue : '{vrai_nom_playlist}' (score : {score})")

                        playlist_id = trouver_playlist_par_nom(vrai_nom_playlist)

                        if playlist_id:
                            try:
                                playlist_uri = f"spotify:playlist:{playlist_id}"
                                os.system(f"start {playlist_uri}")
                                time.sleep(1.5)

                                devices = sp.devices()
                                device_id = None
                                if devices and devices.get('devices'):
                                    for d in devices['devices']:
                                        if d['type'].lower() == 'computer':
                                            device_id = d['id']
                                            break
                                    if not device_id:
                                        device_id = devices['devices'][0]['id']

                                if device_id:
                                    sp.start_playback(device_id=device_id, context_uri=playlist_uri)
                                else:
                                    sp.start_playback(context_uri=playlist_uri)

                                msg = f"Lancement de la playlist '{vrai_nom_playlist}' !"
                                print(f"▶️ {msg}")
                                afficher_popup("Playlist Spotify 🎵", msg)
                            except Exception as e:
                                print(f"Note (ouverture simple effectuée) : {e}")
                                afficher_popup("Playlist Spotify 🎵", f"Ouverture de '{vrai_nom_playlist}'")
                        else:
                            print(f"⚠️ La playlist '{vrai_nom_playlist}' n'a pas été trouvée sur ton compte.")
                    else:
                        print(f"⚠️ Aucun rapport avec tes playlists pour '{nom_demande}'.")
                else:
                    print("Tu n'as pas précisé le nom de la playlist !")

            # ==========================================
            # COMMANDE : LANCER UN TITRE SPÉCIFIQUE
            # ==========================================
            elif any(mot in commande for mot in ["joue", "mets", "chanson", "morceau",
                                                 "titre"]) and "playlist" not in commande and "liste" not in commande:
                morceau_demande = (commande
                                   .replace("joue", "")
                                   .replace("mets", "")
                                   .replace("la", "")
                                   .replace("le", "")
                                   .replace("chanson", "")
                                   .replace("morceau", "")
                                   .replace("titre", "")
                                   .strip())

                if morceau_demande:
                    print(f"Recherche du morceau : '{morceau_demande}'")
                    try:
                        resultats = sp.search(q=morceau_demande, type='track', limit=1)
                        tracks = resultats['tracks']['items']

                        if tracks:
                            meilleur_track = tracks[0]
                            track_uri = meilleur_track['uri']
                            track_name = meilleur_track['name']
                            artist_name = meilleur_track['artists'][0]['name']

                            # On lance directement via l'URI Windows, sans passer par l'API restrictive
                            os.system(f"start {track_uri}")

                            msg = f"Lecture de '{track_name}' par {artist_name} !"
                            print(f"▶️ {msg}")
                            afficher_popup("Spotify 🎵", msg)
                        else:
                            print(f"⚠️ Aucun titre trouvé pour '{morceau_demande}'.")
                            afficher_popup("Erreur Spotify", "Titre introuvable")
                    except Exception as e:
                        print(f"Erreur lors de la recherche : {e}")
                else:
                    print("Tu n'as pas précisé le titre de la chanson !")

            # ==========================================
            # CAS : AJOUTER À LA FILE D'ATTENTE
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
                    print(f"Recherche dans '{NOM_PLAYLIST_CIBLE}' pour : '{morceau_cherche}'")
                    playlist_id = trouver_playlist_par_nom(NOM_PLAYLIST_CIBLE)
                    meilleur_track = None

                    if playlist_id:
                        playlist_tracks = sp.playlist_items(playlist_id, limit=100,
                                                            fields='items(track(name, artists, uri))')
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
                        print(f"Non trouvé dans '{NOM_PLAYLIST_CIBLE}'. Recherche globale...")
                        resultats = sp.search(q=morceau_cherche, type='track', limit=1)
                        tracks = resultats['tracks']['items']

                        if tracks:
                            meilleur_track = tracks['0'] if isinstance(tracks, dict) else tracks[0]
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
                    print("Tu n'as pas précisé le morceau à ajouter !")

    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f"Erreur avec le service de reconnaissance vocale : {e}")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")