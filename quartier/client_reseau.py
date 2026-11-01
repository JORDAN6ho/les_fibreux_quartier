import socket
import threading

from PyQt6.QtCore import QThread, pyqtSignal

from quartier.protocole import decoder, encoder


class ClientReseau(QThread):
    message = pyqtSignal(dict)
    statut = pyqtSignal(str)

    def __init__(self, hote, port):
        super().__init__()
        self.hote, self.port = hote, port
        self.socket = None
        self.verrou = threading.Lock()

    def run(self):
        try:
            self.socket = socket.create_connection((self.hote, self.port), timeout=5)
        except OSError as erreur:
            self.statut.emit(f"Connexion impossible : {erreur}")
            return
        self.socket.settimeout(None)
        self.statut.emit(f"Connecté à {self.hote}:{self.port}")
        try:
            with self.socket.makefile("rb") as flux:
                for ligne in flux:
                    try:
                        self.message.emit(decoder(ligne))
                    except ValueError:
                        continue