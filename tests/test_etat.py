"""Tests du message « etat » envoyé aux clients et des statistiques.

Lancer depuis la racine : python -m tests.test_etat
"""
import json

from quartier.carte import ROUTES
from quartier.simulation import Quartier


def main():
    """Vérifie le contenu du message d'état, qui doit rester du JSON valide."""
    q = Quartier(None)
    for _ in range(100):
        q.avancer()
    etat = q.instantane()
    assert etat["type"] == "etat" and etat["tick"] == q.tick
    assert set(etat["feux"]) == {"Q1", "Q2", "Q3", "Q4"}
    assert set(etat["routes"]) == set(ROUTES)
    assert json.loads(json.dumps(etat)) == etat, "l'état doit passer tel quel en JSON"
    print("OK : message d'état complet et sérialisable en JSON")

    stats = Quartier(None).statistiques()
    assert stats["vehicules"] == 0 and stats["trajet_avec"] is None and stats["recalculs"] == 0
    print("OK : statistiques d'un quartier vide")


if __name__ == "__main__":
    main()
