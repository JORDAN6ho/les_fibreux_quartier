"""Serveur TCP : accepte les clients, exécute leurs commandes et diffuse l'état du quartier."""
import logging
import socket
import threading
import time

from quartier.protocole import decoder, encoder


class ServeurTCP:
    """Serveur socket TCP (un thread par client) qui diffuse des messages JSON."""

    def __init__(self, quartier, hote, port):
        """Prépare le serveur sans encore ouvrir le port."""
        self.quartier, self.hote, self.port = quartier, hote, port
        # Sockets des clients connectés, protégées par le verrou
        self.clients = []
        self.verrou = threading.Lock()
        # Event levé tant que le serveur doit accepter des clients
        self.actif = threading.Event()
        self.socket = None

    def demarrer(self):
        """Ouvre le port et lance l'écoute dans un thread."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Permet de relancer le serveur tout de suite sur le même port
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.hote, self.port))
        self.socket.listen()
        self.actif.set()
        # accept() est bloquant : on l'exécute dans son propre thread
        threading.Thread(target=self.accepter, daemon=True).start()

    def arreter(self):
        """Arrête l'écoute et ferme les connexions."""
        self.actif.clear()
        self.socket.close()
        with self.verrou:
            for conn in self.clients:
                conn.close()
            self.clients.clear()

    def accepter(self):
        """Accepte les nouveaux clients."""
        while self.actif.is_set():
            try:
                conn, adresse = self.socket.accept()
            except OSError:
                break
            logging.info("client connecté : %s:%s", *adresse[:2])
            with self.verrou:
                self.clients.append(conn)
            # Un thread par client, pour que chacun soit servi sans bloquer les autres
            threading.Thread(target=self.gerer_client, args=(conn,), daemon=True).start()

    def gerer_client(self, conn):
        """Lit les commandes d'un client et y répond."""
        try:
            # makefile permet de lire la socket ligne par ligne (un message JSON par ligne)
            with conn.makefile("rb") as flux:
                for ligne in flux:
                    try:
                        message = decoder(ligne)
                    except ValueError:
                        logging.warning("message illisible ignoré")
                        self.envoyer(conn, {"type": "erreur", "message": "message illisible"})
                        continue
                    if message.get("type") == "commande":
                        reponse = self.quartier.executer(message)
                        if reponse:
                            self.envoyer(conn, reponse)
        # Client déconnecté brutalement : on le retire quand même
        except OSError:
            pass
        self.retirer(conn)

    def retirer(self, conn):
        """Retire un client déconnecté."""
        with self.verrou:
            if conn in self.clients:
                self.clients.remove(conn)
                logging.info("client déconnecté")
        conn.close()

    def envoyer(self, conn, message):
        """Envoie un message à un client ; retourne False si la connexion est coupée."""
        try:
            # Le verrou évite que deux threads écrivent en même temps sur une socket
            with self.verrou:
                conn.sendall(encoder(message))
            return True
        except OSError:
            return False

    def diffuser(self, message):
        """Envoie un message à tous les clients connectés."""
        with self.verrou:
            # Copie de la liste pour ne pas garder le verrou pendant les envois
            clients = list(self.clients)
        for conn in clients:
            if not self.envoyer(conn, message):
                self.retirer(conn)


def boucle_simulation(quartier, serveur, arret):
    """Fait avancer la simulation (33 pas par seconde) et diffuse l'état 11 fois par seconde."""
    compteur = 0
    while not arret.is_set():
        debut = time.time()
        # Le verrou empêche une commande d'un client de modifier le quartier en plein calcul
        with quartier.verrou:
            quartier.avancer()
            # L'état n'est envoyé qu'un pas sur trois pour ne pas surcharger le réseau
            etat = quartier.instantane() if compteur % 3 == 0 else None
        if etat:
            serveur.diffuser(etat)
        compteur += 1
        # On attend le reste des 30 ms pour garder un rythme régulier
        time.sleep(max(0.0, 0.03 - (time.time() - debut)))
