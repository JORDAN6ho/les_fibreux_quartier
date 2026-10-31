"""Tests des commandes envoyées par le client (sans réseau).

Lancer depuis la racine : python -m tests.test_commandes
"""
from quartier.simulation import Quartier


def main():
    """Vérifie que chaque commande invalide renvoie une erreur au lieu de faire planter le serveur."""
    q = Quartier(None)
    erreurs = {
        "commande inconnue": {"nom": "danser"},
        "route ou état inconnu": {"nom": "route", "route": "z99", "etat": "bloquee"},
        "gravité invalide (1 à 3)": {"nom": "urgence", "depart": "E3", "arrivee": "E4", "gravite": "abc"},
    }
    for attendu, commande in erreurs.items():
        reponse = q.executer(commande)
        assert reponse == {"type": "erreur", "message": attendu}, (commande, reponse)
    assert q.executer({"nom": "urgence", "depart": "E3", "arrivee": "E4", "gravite": 7})["message"] \
        == "gravité invalide (1 à 3)"
    assert q.executer({"nom": "route", "route": "h12", "etat": "glissante"})["message"] == "route ou état inconnu"
    assert q.executer({"nom": "route", "route": "h12", "etat": "dense"}) is None
    assert q.etats_routes["h12"] == "dense"

    assert q.executer({"nom": "auto", "valeur": False}) is None and q.trafic_auto is False
    assert q.executer({"nom": "auto", "valeur": True}) is None and q.trafic_auto is True

    print("OK : commandes invalides refusées avec un message d'erreur")


if __name__ == "__main__":
    main()
