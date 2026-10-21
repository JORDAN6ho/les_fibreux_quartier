"""Programme serveur : simule le quartier et sert les clients (machine 1)."""
import logging
import threading

from quartier.base import Base
from quartier.config import lire_reseau
from quartier.serveur_reseau import ServeurTCP, boucle_simulation
from quartier.simulation import Quartier


def main():
    """Lance le serveur jusqu'à Ctrl+C."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [serveur] %(message)s", datefmt="%H:%M:%S")
    hote, port, fichier = lire_reseau("serveur", "Serveur du quartier connecté")
    base = Base(fichier.get("base", "chemin", fallback="stats.db"))
    quartier = Quartier(base)
    serveur = ServeurTCP(quartier, hote, port)
    serveur.demarrer()
    logging.info("en écoute sur %s:%s (Ctrl+C pour arrêter)", hote, port)
    # Event qui arrête la boucle de simulation quand on fait Ctrl+C
    arret = threading.Event()
    try:
        # La simulation tourne dans le thread principal, le réseau dans ses propres threads
        boucle_simulation(quartier, serveur, arret)
    except KeyboardInterrupt:
        arret.set()
        serveur.arreter()
        logging.info("serveur arrêté")


if __name__ == "__main__":
    main()
