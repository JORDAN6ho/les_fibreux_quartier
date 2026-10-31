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
    # Rogner retire le début et la fin ; décaler garde la longueur sur une ligne droite
    assert carte.longueur(carte.rogner([(0, 0), (100, 0)], 10, 20)) == 70
    assert carte.decaler([(0, 0), (100, 0)], 11) == [(0, 11), (100, 11)]
    print("OK : rogner et décaler une voie")
    # Graphe : chaque route est utilisable dans les deux sens, et chaque voie arrive sur un axe connu
    for rid, (a, b, _, _) in carte.ROUTES.items():
        assert (b, rid, 1) in carte.VOISINS[a] and (a, rid, -1) in carte.VOISINS[b]
    assert len(carte.VOIES) == 2 * len(carte.ROUTES)
    assert all(axe in ("ew", "ns") for _, axe in carte.ARRIVEES.values())
    print("OK : graphe des routes cohérent (deux sens par route)")
    # FIN


if __name__ == "__main__":
    main()
