"""Tests de la géométrie et des itinéraires (quartier/carte.py).

Lancer depuis la racine : python -m tests.test_carte
"""
import math

from quartier import carte


def main():
    """Lance les tests de la carte."""
    # Longueur et point sur une ligne brisée en L de 300 + 400 pixels
    ligne = [(0, 0), (300, 0), (300, 400)]
    assert carte.longueur(ligne) == 700
    assert carte.point_sur(ligne, 150) == (150, 0, 1, 0)
    assert carte.point_sur(ligne, 500) == (300, 200, 0, 1)
    print("OK : longueur et point sur une ligne brisée")
    # FIN


if __name__ == "__main__":
    main()
