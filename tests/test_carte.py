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
    # Dijkstra : route directe si tout est fluide, contournement si la directe coûte trop, rien si tout est coupé
    def cout(rid, sens):
        return carte.LONGUEURS[(rid, sens)]
    route, total = carte.itineraire("E3", "E4", cout)
    assert [rid for rid, _ in route] == ["e3", "h34", "e4"] and total < math.inf
    route, _ = carte.itineraire("E3", "E4", lambda rid, sens: math.inf if rid == "h34" else cout(rid, sens))
    assert "c34" in [rid for rid, _ in route]
    assert carte.itineraire("E3", "E4", lambda rid, sens: math.inf if rid == "e4" else cout(rid, sens)) == (None, math.inf)
    print("OK : Dijkstra (direct, contournement, aucun chemin)")
    # Trajet : continu, au moins aussi long que ses voies, et gardé en cache
    t = carte.trajet([("e3", 1), ("h34", 1), ("e4", -1)])
    assert t is carte.trajet([("e3", 1), ("h34", 1), ("e4", -1)])
    assert t.total >= sum(carte.LONGUEURS[c] for c in t.route) - 1e-6
    debut, fin = t.position(0), t.position(t.total)
    assert debut[0] < 1 and fin[0] > 1199, "le trajet E3 vers E4 traverse toute la carte"
    assert t.indice(0) == 0 and t.indice(t.total) == 2
    print("OK : trajet continu, mis en cache")


if __name__ == "__main__":
    main()
