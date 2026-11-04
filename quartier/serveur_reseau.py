import logging
import json
import threading
import socket 

def encoder(message): # message : le paramètre, c’est-à-dire l’objet Python (bibliothèque) à transformer.
    return (json.dumps(message, separators=(",", ":")) + "\n").encode()
    # json.dumps(message, ...) : transforme l’objet Python en chaîne de caractères JSON.
    # separators=(",", ":") : choisit les séparateurs utilisés dans le JSON pour la lisibilité.
    # + "\n" : ajoute un saut de ligne à la fin de la chaîne et indispansable car c’est lui qui marque la fin d’un message.
    # .encode() : convertit la chaîne (str) en octets (bytes), aussi indispensable car sinon ça crash.

def decoder(ligne):
    return json.loads(ligne) # json.loads(...) : transforme un texte JSON en objet Python

class ServeurTCP:
    def __init__(self, quartier, hote, port):
        self.quartier = quartier  # quartier : la simulation, pour exécuter les commandes des clients
        self.hote = hote  # hote : l'adresse IP où le serveur écoute
        self.port = port  # port : le numéro de port (lu dans config.ini)
        self.socket = None  # None : pas encore de socket tant que demarrer() n'est pas appelé
        self.clients = []  # clients : la liste des connexions des clients connectés
        self.verrou = threading.Lock()  # verrou : évite que deux threads touchent la liste en même temps

    def demarrer(self):
        """Ouvre le port et commence à accepter les clients."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # AF_INET : adresse IPv4, SOCK_STREAM : TCP.
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # SO_REUSEADDR : on peut relancer le serveur tout de suite sur le même port sans erreur « adresse déjà utilisée ».
        self.socket.bind((self.hote, self.port))  # bind : attache le socket à l'adresse et au port
        self.socket.listen()  # listen : le serveur attend les connexions
        threading.Thread(target=self.accepter, daemon=True).start()
        # target=self.accepter : le thread fait tourner accepter().
        # daemon=True : le thread s'arrête tout seul quand le programme se ferme.

    def accepter(self):
        """Permet que les clients lancent un thread pour chacun."""
        while True:
            try:
                conn, adresse = self.socket.accept()
                # accept : bloque jusqu'à ce qu'un client arrive, renvoie sa connexion et son adresse.
                # conn : la connexion avec ce client, adresse : son IP et son port.
            except OSError:
                return  # OSError : le port a été fermé par arreter(), on sort
            with self.verrou:
                self.clients.append(conn)  # append : ajoute le client à la liste
            logging.info("client connecté : %s", adresse[0])  # adresse[0] : l'IP du client
            # logging.info(...) : écrit un message dans le journal du serveur.
            # %s : remplacé par adresse[0], c'est-à-dire l'IP du client.
            threading.Thread(target=self.gerer_client, args=(conn,), daemon=True).start()
            # Un thread par client : chaque client est écouté en même temps que les autres.
            # target=self.gerer_client : le thread fait tourner gerer_client().
            # args=(conn,) : donne la connexion au thread, la virgule est obligatoire pour un tuple d'un seul élément.

    
    def arreter(self):
        """ferme le port et coupe toutes les connexions."""
        self.socket.close()
        # close() : ferme le port, plus aucun client ne peut se connecter.
        # Ça fait aussi lever une OSError dans accepter(), qui s'arrête.
        with self.verrou:
            # with self.verrou : on prend le verrou, aucun autre thread ne touche la liste pendant ce bloc.
            # Le verrou est rendu tout seul à la fin du bloc with.
            for conn in self.clients:
                # for conn in self.clients : on passe sur chaque client connecté, conn est sa connexion.
                conn.close()
                # conn.close() : coupe la connexion de ce client.
            self.clients.clear()
            # clear() : vide la liste, il n'y a plus de client.
    

    def retirer(self, conn):
        """ça enlève un client de la liste."""
        with self.verrou:
            if conn in self.clients:
                # conn in self.clients : vrai si le client est encore dans la liste.
                # ça évite de le retirer deux fois (ça planterait avec remove).
                self.clients.remove(conn)
                # remove(conn) : enlève ce client de la liste.
                logging.info("client déconnecté")
        conn.close()
        # conn.close() : ferme la connexion, même si le client n'était plus dans la liste.
    

    def envoyer(self, conn, message):
        """envoie un message à un seul client."""
        # conn : le client à qui envoyer, message : le dictionnaire à envoyer.
        try:
            with self.verrou:
                # verrou : deux threads ne peuvent pas écrire en même temps, sinon les messages se mélangent.
                conn.sendall(encoder(message))
                # encoder(message) : transforme le dictionnaire en ligne JSON en octets.
                # sendall(...) : envoie tous les octets, même si ça prend plusieurs envois.
            return True
            # True : le message est bien parti.
        except OSError:
            return False
            # OSError : la connexion est coupée, False prévient diffuser que ce client n'est plus là.

    #def gerer_client(self, conn):
