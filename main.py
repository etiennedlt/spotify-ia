import speech_recognition as sr
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

# Import de toutes les fonctions depuis ton fichier fonctions.py
from fonctions import (
    initialiser_spotify,
    lancer_morceau_specifique,
    lancer_playlist,
    ajouter_file_attente,
    afficher_popup
)

# ==========================================
# CONFIGURATIONS PRINCIPALES
# ==========================================
NOM_PLAYLIST_CIBLE = "All"  # Nom de la playlist principale pour la file d'attente

# --- 1. CONFIGURATION SPOTIFY ---
sp = initialiser_spotify(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

# --- 2. CONFIGURATION MICRO ---
recognizer = sr.Recognizer()
microphone = sr.Microphone()

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
            # 1. COMMANDE : LANCER UN TITRE SPÉCIFIQUE (DIRECT)
            # ==========================================
            if any(mot in commande for mot in ["joue", "mets", "chanson", "morceau", "titre"]) and "playlist" not in commande and "liste" not in commande:
                lancer_morceau_specifique(sp, commande)
                continue

            # ==========================================
            # 2. COMMANDE : LANCER UNE PLAYLIST
            # ==========================================
            elif "playlist" in commande or "liste" in commande:
                lancer_playlist(sp, commande)
                continue

            # ==========================================
            # 3. COMMANDES DE CONTRÔLE DE LECTURE & VOLUME
            # ==========================================
            mots_passe = ["passe", "suivant", "next", "pas", "passer", "paps"]
            mots_comeback = ["come-back", "come back", "comback", "précédent", "retour", "reviens", "recule"]
            mots_restart = ["restart", "reste", "recommence", "depuis le début", "début", "reset", "redémarre", "restar"]
            mots_pause = ["pause", "stop", "arrête", "interromps"]
            mots_play = ["play", "lance", "joue", "marche", "reprends"]

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

            elif any(mot in commande for mot in mots_pause):
                sp.pause_playback()
                print("⏸️ Lecture en pause.")
                afficher_popup("Spotify Controls", "⏸️ Musique en pause")
                continue

            elif any(mot in commande for mot in mots_play):
                sp.start_playback()
                print("▶️ Lecture relancée !")
                afficher_popup("Spotify Controls", "▶️ Lecture relancée !")
                continue

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
                continue

            # ==========================================
            # 4. CAS : AJOUTER À LA FILE D'ATTENTE
            # ==========================================
            elif any(mot in commande for mot in ["file", "fail", "fil", "five", "feel", "fille"]):
                ajouter_file_attente(sp, commande, NOM_PLAYLIST_CIBLE)

    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f"Erreur avec le service de reconnaissance vocale : {e}")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")