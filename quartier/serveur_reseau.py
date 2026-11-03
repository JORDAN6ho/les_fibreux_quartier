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
