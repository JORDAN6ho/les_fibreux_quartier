import json


def encoder(message):
    return (json.dumps(message, separators=(",", ":")) + "\n").encode()


def decoder(ligne):
    return json.loads(ligne)
