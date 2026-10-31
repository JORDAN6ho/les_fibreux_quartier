"""Connexion du client au serveur, dans un QThread."""
import socket
import threading

from PyQt6.QtCore import QThread, pyqtSignal

from quartier.protocole import decoder, encoder


class ClientReseau(QThread):
    """Reçoit les messages du serveur et les transmet à l'interface par signaux Qt."""

    # Signaux Qt : seul moyen de passer des données du thread réseau à l'interface
    message = pyqtSignal(dict)
    statut = pyqtSignal(str)

    def __init__(self, hote, port):
        """Garde l'adresse du serveur ; la connexion se fait dans run()."""
        super().__init__()
        self.hote, self.port = hote, port
        self.socket = None
        self.verrou = threading.Lock()

    def run(self):
        """Se connecte puis lit les messages ligne par ligne."""
        try:
            # run() s'exécute dans le thread réseau, pas dans celui de l'interface
            self.socket = socket.create_connection((self.hote, self.port), timeout=5)
        except OSError as erreur:
            self.statut.emit(f"Connexion impossible : {erreur}")
            return
        # Le délai de 5 s ne sert qu'à la connexion ; ensuite on attend les messages sans limite
        self.socket.settimeout(None)
        self.statut.emit(f"Connecté à {self.hote}:{self.port}")
        try:
            with self.socket.makefile("rb") as flux:
                for ligne in flux:
                    try:
                        message = decoder(ligne)
                    except ValueError:
                        # Ligne abîmée : on l'ignore plutôt que de perdre la connexion
                        continue
                    # emit() transmet le message au slot de la fenêtre, exécuté dans le thread de Qt
                    self.message.emit(message)
        except OSError:
            pass
        self.statut.emit("Connexion perdue")

    def envoyer(self, message):
        """Envoie une commande au serveur."""
        if self.socket is None:
            return
        try:
            # Envoi appelé depuis l'interface : le verrou évite deux envois mélangés
            with self.verrou:
                self.socket.sendall(encoder(message))
        except OSError:
            self.statut.emit("Envoi impossible : connexion perdue")

    def arreter(self):
        """Ferme la connexion pour terminer le thread."""
        if self.socket:
            try:
                # shutdown débloque la lecture en cours dans run(), ce qui termine le thread
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.socket.close()
