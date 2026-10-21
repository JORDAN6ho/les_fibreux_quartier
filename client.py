"""Programme client : affiche le quartier et envoie les commandes (machine 2)."""
import sys

from PyQt6.QtWidgets import QApplication

from quartier.config import lire_reseau
from quartier.ihm import FenetreQuartier


def main():
    """Lance l'interface en plein écran."""
    hote, port, _ = lire_reseau("client", "Client du quartier connecté")
    # On ne passe pas nos options (--hote, --port) à Qt, qui ne les connaît pas
    app = QApplication(sys.argv[:1])
    fenetre = FenetreQuartier(hote, port)
    fenetre.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
