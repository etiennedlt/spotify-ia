import time
import speech_recognition as sr
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

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
NOM_PLAYLIST_CIBLE = "All"

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
            # 1. CAS : AJOUTER À LA FILE D'ATTENTE (Prioritaire)
            # ==========================================
            if any(mot in commande for mot in ["file", "fail", "fil", "five", "feel", "fille", "feels", "ajoute"]):
                ajouter_file_attente(sp, commande, NOM_PLAYLIST_CIBLE)
                continue

            # ==========================================
            # 2. COMMANDE : LANCER UNE PLAYLIST
            # ==========================================
            elif "playlist" in commande or "liste" in commande:
                lancer_playlist(sp, commande)
                continue

            # ==========================================
            # 3. COMMANDE : LANCER UN TITRE SPÉCIFIQUE
            # ==========================================
            elif any(mot in commande for mot in ["joue", "mets", "chanson", "morceau", "titre"]):
                lancer_morceau_specifique(sp, commande)
                continue

            # ==========================================
            # 4. COMMANDES DE CONTRÔLE DE LECTURE & VOLUME
            # ==========================================
            mots_passe = ["passe", "suivant", "next", "pas", "passer", "paps", "nex"]
            mots_comeback = ["come-back", "come back", "comback", "précédent", "retour", "reviens", "recule"]
            mots_restart = ["restart", "reste", "recommence", "depuis le début", "début", "reset", "redémarre", "restar"]
            mots_pause = ["pause", "stop", "arrête", "interromps"]
            mots_play = ["play", "lance", "joue", "marche", "reprends"]

            # Fonction utilitaire sécurisée : active le PC puis exécute l'action sans argument risqué
            def executer_commande_spotify(action_fonction, message_succes, popup_texte):
                try:
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
                            sp.transfer_playback(device_id=device_id, force_play=False)
                            time.sleep(0.2)
                        except Exception:
                            pass

                    action_fonction()

                    print(message_succes)
                    afficher_popup("Spotify Controls", popup_texte)
                except Exception as e:
                    print(f"Erreur de contrôle Spotify : {e}")

            if any(mot in commande for mot in mots_passe):
                executer_commande_spotify(lambda: sp.next_track(), "⏭️ Morceau suivant !", "⏭️ Morceau suivant !")
                continue

            elif any(mot in commande for mot in mots_comeback):
                executer_commande_spotify(lambda: sp.previous_track(), "⏮️ Morceau précédent !", "⏮️ Morceau précédent !")
                continue

            elif any(mot in commande for mot in mots_restart):
                executer_commande_spotify(lambda: sp.seek_track(0), "🔄 Morceau redémarré au début !", "🔄 Morceau redémarré au début !")
                continue

            elif any(mot in commande for mot in mots_pause):
                executer_commande_spotify(lambda: sp.pause_playback(), "⏸️ Lecture en pause.", "⏸️ Musique en pause")
                continue

            elif any(mot in commande for mot in mots_play):
                executer_commande_spotify(lambda: sp.start_playback(), "▶️ Lecture relancée !", "▶️ Lecture relancée !")
                continue

            elif "volume" in commande or any(mot == "son" for mot in commande.split()):
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

    except sr.UnknownValueError:
        time.sleep(0.5)
        pass
    except sr.RequestError as e:
        print(f"Erreur avec le service de reconnaissance vocale : {e}")
        time.sleep(2)
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        time.sleep(1)