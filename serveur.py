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
    try:
        serveur.demarrer()
    except OSError as erreur:
        # Cas fréquent : un ancien serveur tourne encore (« Address already in use »)
        logging.error("impossible d'écouter sur %s:%s : %s", hote, port, erreur)
        logging.error("un autre serveur tourne peut-être encore : pkill -f serveur.py, puis relancer")
        base.fermer()
        raise SystemExit(1)
    logging.info("en écoute sur %s:%s (Ctrl+C pour arrêter)", hote, port)
    # Event qui arrête la boucle de simulation quand on fait Ctrl+C
    arret = threading.Event()
    try:
        # La simulation tourne dans le thread principal, le réseau dans ses propres threads
        boucle_simulation(quartier, serveur, arret)
    except KeyboardInterrupt:
        arret.set()
        serveur.arreter()
        # Ferme proprement stats.db pour ne pas laisser d'écriture en suspens
        base.fermer()
        logging.info("serveur arrêté")


if __name__ == "__main__":
    main()
