"""Test réseau : un client se connecte au serveur, envoie des commandes et reçoit l'état.

Lancer depuis la racine : python -m tests.test_reseau
"""
import configparser
import socket
import threading
import time

from quartier.protocole import decoder, encoder
from quartier.serveur_reseau import ServeurTCP, boucle_simulation
from quartier.simulation import Quartier


def main():
    """Démarre un serveur local, envoie une commande invalide puis une valide, et vérifie les réponses."""
    fichier = configparser.ConfigParser()
    fichier.read("config.ini")
    hote = fichier.get("reseau", "hote_client")
    port = fichier.getint("reseau", "port") + 1
    quartier = Quartier(None)
    serveur = ServeurTCP(quartier, hote, port)
    serveur.demarrer()
    arret = threading.Event()
    threading.Thread(target=boucle_simulation, args=(quartier, serveur, arret), daemon=True).start()
    time.sleep(0.3)
    with socket.create_connection((hote, port), timeout=5) as conn, conn.makefile("rb") as flux:
        conn.sendall(b"[1, 2]\n")
        conn.sendall(encoder({"type": "commande", "nom": "urgence", "depart": "E3", "arrivee": "E3",
                              "gravite": 1, "prioritaire": True}))
        conn.sendall(encoder({"type": "commande", "nom": "urgence", "depart": "E3", "arrivee": "E4",
                              "gravite": 2, "prioritaire": True}))
        erreurs, etat = [], None
        for _ in range(60):
            message = decoder(flux.readline())
            if message["type"] == "erreur":
                erreurs.append(message["message"])
            elif message["type"] == "etat" and message["ambulances"]:
                etat = message
                break
    arret.set()
    serveur.arreter()
    assert erreurs == ["message illisible", "départ ou arrivée invalide"], erreurs
    assert etat and etat["ambulances"][0]["prio"]
    print("OK : erreur renvoyée pour la commande invalide, ambulance reçue dans l'état :", etat["ambulances"][0]["route"])


if __name__ == "__main__":
    main()
