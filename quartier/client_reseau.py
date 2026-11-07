"""Connexion du client au serveur, dans un QThread."""
import socket
import threading

from PyQt6.QtCore import QThread, pyqtSignal

# Même format de message que le serveur : on réutilise ses deux fonctions
from quartier.serveur_reseau import decoder, encoder


class ClientReseau(QThread):
    """Reçoit les messages du serveur et les passe à l'interface par signaux Qt."""

    message = pyqtSignal(dict)
    statut = pyqtSignal(str)

    def __init__(self, hote, port):
        """Garde l'adresse du serveur ; la connexion se fait dans run()."""
        super().__init__()
        self.hote, self.port = hote, port
        self.socket = None
        self.verrou = threading.Lock()

    def run(self):
        """Se connecte au serveur puis lit les messages ligne par ligne."""
        try:
            self.socket = socket.create_connection((self.hote, self.port), timeout=5)
        except OSError as erreur:
            self.statut.emit(f"Connexion impossible : {erreur}")
            return
        self.socket.settimeout(None)  # les 5 s ne servaient qu'à la connexion
        self.statut.emit(f"Connecté à {self.hote}:{self.port}")
        try:
            with self.socket.makefile("rb") as flux:
                for ligne in flux:
                    try:
                        message = decoder(ligne)
                    except ValueError:
                        continue
                    if isinstance(message, dict):
                        self.message.emit(message)
        except OSError:
            pass
        self.statut.emit("Connexion perdue")

    def envoyer(self, message):
        """Envoie une commande au serveur (appelé depuis l'interface)."""
        if self.socket is None:
            return
        try:
            with self.verrou:
                self.socket.sendall(encoder(message))
        except OSError:
            self.statut.emit("Envoi impossible : connexion perdue")

    def arreter(self):
        """Ferme la connexion, ce qui termine la boucle de run()."""
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.socket.close()
