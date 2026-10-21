"""Protocole réseau : un message JSON par ligne."""
import json

ENCODAGE = "utf-8"


def encoder(message):
    """Transforme un dictionnaire en une ligne JSON prête à être envoyée."""
    # Sans espaces pour un message plus court ; le retour à la ligne marque la fin du message
    return (json.dumps(message, separators=(",", ":")) + "\n").encode(ENCODAGE)


def decoder(ligne):
    """Transforme une ligne reçue en dictionnaire."""
    return json.loads(ligne.decode(ENCODAGE))
