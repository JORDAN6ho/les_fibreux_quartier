"""Tests des feux d'un carrefour (classe Noeud) et des petites fonctions de calcul.

Lancer depuis la racine : python -m tests.test_feux
"""
from quartier.simulation import CYCLE, ORANGE, TOUT_ROUGE, VERT, Noeud


def couleurs(noeud, pas):
    """Liste des états des feux pendant un nombre de pas donné."""
    etats = []
    for _ in range(pas):
        etats.append(noeud.etat())
        noeud.avancer()
    return etats


def main():
    """Lance les tests des feux."""
    # Cycle normal : vert, orange, tout-rouge sur l'axe est-ouest, puis la même chose sur le nord-sud
    etats = couleurs(Noeud(0), CYCLE)
    assert etats[0] == {"ew": "vert", "ns": "rouge"}
    assert etats[VERT] == {"ew": "orange", "ns": "rouge"}
    assert etats[VERT + ORANGE] == {"ew": "rouge", "ns": "rouge"}
    assert etats[VERT + ORANGE + TOUT_ROUGE] == {"ns": "vert", "ew": "rouge"}
    assert not any(e["ew"] != "rouge" and e["ns"] != "rouge" for e in etats), "jamais deux axes ouverts"
    print("OK : cycle normal des feux, jamais deux axes ouverts en même temps")
    # FIN


if __name__ == "__main__":
    main()
