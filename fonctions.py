import os
import time
from plyer import notification
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from thefuzz import process, fuzz


def initialiser_spotify(client_id, client_secret, redirect_uri):
    # Ajout des scopes indispensables pour les playlists et la lecture
    scope = (
        "user-modify-playback-state "
        "user-read-playback-state "
        "user-read-currently-playing "
        "playlist-read-private "
        "playlist-read-collaborative"
    )

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        cache_path=".cache"  # Important pour stocker le token
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def afficher_popup(titre, message, duree=5):
    """Affiche une notification pop-up sur le bureau."""
    try:
        notification.notify(
            title=titre,
            message=message,
            app_name="Assistant Spotify",
            timeout=duree,
            pos="bottom_left"
        )
    except Exception:
        notification.notify(
            title=titre,
            message=message,
            app_name="Assistant Spotify",
            timeout=duree
        )


def trouver_playlist_par_nom(sp, nom_cherche):
    """Recherche l'ID d'une playlist par son nom sur le compte utilisateur."""
    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        if nom_cherche.lower() == playlist['name'].lower():
            return playlist['id']
    return None


def lancer_morceau_specifique(sp, commande):
    """Lance un morceau immédiatement en utilisant son album comme contexte (100% fiable en arrière-plan)."""
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
        print(f"Recherche et lancement immédiat de : '{morceau_demande}'")
        try:
            q_clean = morceau_demande.replace('é', 'e').replace('è', 'e').replace('ê', 'e')
            resultats = sp.search(q=q_clean, type='track', limit=1)
            tracks = resultats.get('tracks', {}).get('items', [])

            if tracks:
                meilleur_track = tracks[0]
                track_uri = meilleur_track['uri']
                track_name = meilleur_track['name']
                artist_name = meilleur_track['artists'][0]['name']
                album_uri = meilleur_track['album']['uri']  # Récupération de l'album de la piste

                # Récupération de l'appareil actif (PC)
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
                    try:
                        sp.transfer_playback(device_id=device_id, force_play=True)
                    except Exception:
                        pass

                    # Lancement via le contexte de l'album + offset sur la piste exacte
                    sp.start_playback(
                        device_id=device_id,
                        context_uri=album_uri,
                        offset={"uri": track_uri}
                    )
                else:
                    sp.start_playback(
                        context_uri=album_uri,
                        offset={"uri": track_uri}
                    )

                msg = f"Lecture immédiate : '{track_name}' de {artist_name}"
                print(f"▶️ {msg}")
                afficher_popup("Spotify 🎵", msg)
            else:
                print(f"⚠️ Aucun titre trouvé pour '{morceau_demande}'.")
                afficher_popup("Erreur Spotify", "Titre introuvable")
        except Exception as e:
            print(f"Erreur lors du lancement direct : {e}")
    else:
        print("Tu n'as pas précisé le titre de la chanson !")


def lancer_playlist(sp, commande):
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

            playlist_id = trouver_playlist_par_nom(sp, vrai_nom_playlist)

            if playlist_id:
                try:
                    playlist_uri = f"spotify:playlist:{playlist_id}"

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
                        try:
                            sp.transfer_playback(device_id=device_id, force_play=True)
                        except Exception:
                            pass
                        sp.start_playback(device_id=device_id, context_uri=playlist_uri)
                    else:
                        sp.start_playback(context_uri=playlist_uri)

                    msg = f"Lancement de la playlist '{vrai_nom_playlist}' !"
                    print(f"▶️ {msg}")
                    afficher_popup("Playlist Spotify 🎵", msg)
                except Exception as e:
                    print(f"Erreur lors du lancement de la playlist : {e}")
                    afficher_popup("Playlist Spotify 🎵", "Erreur de lancement")
            else:
                print(f"⚠️ La playlist '{vrai_nom_playlist}' n'a pas été trouvée sur ton compte.")
        else:
            print(f"⚠️ Aucun rapport avec tes playlists pour '{nom_demande}'.")
    else:
        print("Tu n'as pas précisé le nom de la playlist !")


def ajouter_file_attente(sp, commande, playlist_cible):
    """Ajoute un morceau à la file d'attente."""
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
        print(f"Recherche dans '{playlist_cible}' pour : '{morceau_cherche}'")
        playlist_id = trouver_playlist_par_nom(sp, playlist_cible)
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
            print(f"Non trouvé dans '{playlist_cible}'. Recherche globale...")
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
        print("Tu n'as pas précisé le morceau à ajouter !")