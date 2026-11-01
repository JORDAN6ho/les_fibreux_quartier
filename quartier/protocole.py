import json


def encoder(message): # message : le paramètre, c’est-à-dire l’objet Python (bibliothèque) à transformer.
    return (json.dumps(message, separators=(",", ":")) + "\n").encode()
    # json.dumps(message, ...) : transforme l’objet Python en chaîne de caractères JSON.
    # separators=(",", ":") : choisit les séparateurs utilisés dans le JSON pour la lisibilité.
    # + "\n" : ajoute un saut de ligne à la fin de la chaîne et indispansable car c’est lui qui marque la fin d’un message.
    # .encode() : convertit la chaîne (str) en octets (bytes), aussi indispensable car sinon ça crash.

def decoder(ligne):
    return json.loads(ligne) # json.loads(...) : transforme un texte JSON en objet Python
