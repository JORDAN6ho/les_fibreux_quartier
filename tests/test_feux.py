"""Tests des feux d'un carrefour (classe Noeud) et des petites fonctions de calcul.

Lancer depuis la racine : python -m tests.test_feux
"""
from types import SimpleNamespace

from quartier.carte import ARRIVEES
from quartier.simulation import CYCLE, ORANGE, TOUT_ROUGE, VERT, Noeud, Quartier, freinage, moyenne


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
    # Non-régression : après un recalcul d'itinéraire, l'ambulance arrive par l'autre axe du même carrefour.
    # La réservation doit passer sur le nouvel axe, sinon le vert reste sur l'ancien et l'ambulance est bloquée.
    q = Quartier(None)
    noeud = "Q2"
    cle_ew = next(c for c, (nom, axe) in ARRIVEES.items() if nom == noeud and axe == "ew")
    cle_ns = next(c for c, (nom, axe) in ARRIVEES.items() if nom == noeud and axe == "ns")
    amb = SimpleNamespace(ident=1, so=0.0, trajet=SimpleNamespace(route=[cle_ew]))
    assert q.forcer(amb, 0, 100) == noeud and q.noeuds[noeud].forcage["axe"] == "ew"
    amb.trajet.route = [cle_ns]  # nouvel itinéraire : arrivée par l'axe nord-sud
    assert q.forcer(amb, 0, 100) == noeud and q.noeuds[noeud].forcage["axe"] == "ns"
    assert q.noeuds[noeud].etat()["ns"] == "vert"
    # Une autre ambulance ne doit pas pouvoir prendre la réservation
    autre = SimpleNamespace(ident=2, so=0.0, trajet=SimpleNamespace(route=[cle_ew]))
    assert q.forcer(autre, 0, 100) is None and q.noeuds[noeud].forcage["amb"] == 1
    print("OK : réservation d'un carrefour mise à jour après un changement d'axe de l'ambulance")
    # Choix de la stratégie : dégagement si au moins 3 véhicules sont devant l'ambulance, sinon onde verte
    q = Quartier(None)
    cle = next(c for c, (nom, _) in ARRIVEES.items() if nom == "Q2")
    amb = SimpleNamespace(ident=1, so=0.0, trajet=SimpleNamespace(route=[cle]))
    q.par_route[cle] = [SimpleNamespace(so=50.0 + 10 * i) for i in range(2)]
    q.forcer(amb, 0, 100)
    assert q.noeuds["Q2"].forcage["mode"] == "onde_verte"
    q.noeuds["Q2"].forcage = None
    q.par_route[cle].append(SimpleNamespace(so=80.0))
    q.forcer(amb, 0, 100)
    assert q.noeuds["Q2"].forcage["mode"] == "degagement"
    print("OK : onde verte avec moins de 3 véhicules devant, dégagement à partir de 3")
    # Petites fonctions : moyenne qui ignore les valeurs manquantes, freinage borné
    assert moyenne([]) is None and moyenne([None, 2, 4]) == 3
    assert freinage(0, 3) == 0 and freinage(1000, 3) == 3 and 0 < freinage(10, 3) < 3
    print("OK : moyenne et freinage")


if __name__ == "__main__":
    main()
