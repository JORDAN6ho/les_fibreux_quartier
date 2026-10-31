"""Tests des feux d'un carrefour (classe Noeud) et des petites fonctions de calcul.

Lancer depuis la racine : python -m tests.test_feux
"""
from quartier.simulation import CYCLE, ORANGE, TOUT_ROUGE, VERT, Noeud, freinage, moyenne


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
    # Forçage pour une ambulance : le cycle est gelé ; en dégagement, vert seulement une fois le carrefour vidé
    n = Noeud(10)
    n.forcage = {"axe": "ns", "mode": "degagement", "pret": False}
    assert couleurs(n, 50)[-1] == {"ns": "rouge", "ew": "rouge"} and n.t == 10
    n.forcage["pret"] = True
    assert n.etat() == {"ns": "vert", "ew": "rouge"}
    n.forcage = {"axe": "ew", "mode": "onde_verte", "pret": False}
    assert n.etat() == {"ew": "vert", "ns": "rouge"}
    print("OK : forçage des feux (dégagement et onde verte)")
    # Après une urgence : tout-rouge de sécurité, puis reprise du cycle au début
    n = Noeud(200)
    n.retour = 3
    assert couleurs(n, 3) == [{"ew": "rouge", "ns": "rouge"}] * 3
    assert n.t == 0 and n.etat() == {"ew": "vert", "ns": "rouge"}
    print("OK : tout-rouge de sécurité puis reprise du cycle")
    # Petites fonctions : moyenne qui ignore les valeurs manquantes, freinage borné
    assert moyenne([]) is None and moyenne([None, 2, 4]) == 3
    assert freinage(0, 3) == 0 and freinage(1000, 3) == 3 and 0 < freinage(10, 3) < 3
    print("OK : moyenne et freinage")
    # FIN


if __name__ == "__main__":
    main()
