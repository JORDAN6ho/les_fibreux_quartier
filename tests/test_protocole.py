"""Tests du protocole : un message JSON par ligne.

Lancer depuis la racine : python -m tests.test_protocole
"""
from quartier.protocole import decoder, encoder


def main():
    """Vérifie l'aller-retour encoder/decoder, les accents et le rejet d'une ligne illisible."""
    message = {"type": "commande", "nom": "urgence", "depart": "E3", "arrivee": "E4", "gravite": 2,
               "prioritaire": True}
    ligne = encoder(message)
    assert ligne.endswith(b"\n") and ligne.count(b"\n") == 1, "un message = une seule ligne"
    assert b" " not in ligne, "pas d'espaces inutiles dans le message"
    assert decoder(ligne) == message

    accents = {"type": "erreur", "message": "départ ou arrivée invalide"}
    assert decoder(encoder(accents)) == accents

    try:
        decoder(b"pas du json\n")
    except ValueError:
        pass
    else:
        raise AssertionError("une ligne illisible doit lever ValueError (le serveur l'ignore)")
    print("OK : protocole (aller-retour, accents, ligne illisible)")


if __name__ == "__main__":
    main()
