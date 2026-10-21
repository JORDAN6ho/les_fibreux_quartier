"""Tests du modèle sans réseau ni interface.

Lancer depuis la racine : python -m tests.test_simulation
"""
import math
import random

from quartier.simulation import Quartier


def preparer(graine, etats=()):
    """Quartier chauffé pendant 20 s, avec des routes éventuellement modifiées."""
    random.seed(graine)
    q = Quartier(None)
    for rid, etat in etats:
        q.executer({"nom": "route", "route": rid, "etat": etat})
    for _ in range(660):
        q.avancer()
    return q


def lancer(q, depart, arrivee, prioritaire):
    """Demande une ambulance et avance jusqu'à son entrée dans le quartier."""
    assert q.executer({"nom": "urgence", "depart": depart, "arrivee": arrivee, "gravite": 2,
                       "prioritaire": prioritaire}) is None
    for _ in range(400):
        q.avancer()
        for u in q.usagers:
            if u.genre == "ambulance":
                return u
    raise AssertionError("l'ambulance n'est pas entrée")


def route_choisie(depart, arrivee, etats):
    """Itinéraire choisi par le serveur pour une ambulance prioritaire."""
    q = preparer(1, etats)
    return {rid for rid, _ in lancer(q, depart, arrivee, True).trajet.route}


def duree(prioritaire, graine):
    """Durée (s) d'un trajet E3 vers E4 avec ou sans priorité."""
    q = preparer(graine)
    lancer(q, "E3", "E4", prioritaire)
    for _ in range(6000):
        q.avancer()
        if q.trajets:
            return q.trajets[0]["duree"]
    raise AssertionError("l'ambulance n'est pas arrivée")


def main():
    """Lance tous les tests du modèle et s'arrête à la première erreur."""
    assert "h34" in route_choisie("E3", "E4", [])
    assert "c34" in route_choisie("E3", "E4", [("h34", "dense")])
    assert "c34" in route_choisie("E3", "E4", [("h34", "bloquee")])
    assert "h34" not in route_choisie("E3", "E4", [("h34", "bloquee")])
    print("itinéraires : direct si fluide, contournement si dense ou bloqué")

    for bloquee in ("h12", "h34"):
        q = preparer(6)
        q.executer({"nom": "route", "route": bloquee, "etat": "bloquee"})
        arrivees = len(q.attentes)
        for _ in range(60 * 33):
            q.avancer()
        coincees = [u for u in q.usagers if u.cle and u.k + 1 < len(u.trajet.route)
                    and u.trajet.route[u.k + 1][0] == bloquee]
        assert not coincees, f"{len(coincees)} voitures attendent devant {bloquee}"
        assert len(q.attentes) - arrivees > 10, "le trafic ne s'écoule plus"
    print("voitures : contournement pris quand la route directe est bloquée")

    q = preparer(7)
    assert q.executer({"nom": "fin_urgence"}) is not None
    lancer(q, "E3", "E4", True)
    for _ in range(60):
        q.avancer()
    assert any(n.forcage for n in q.noeuds.values())
    assert q.executer({"nom": "fin_urgence"}) is None
    for _ in range(100):
        q.avancer()
    assert q.compter("ambulance") == 0 and not q.trajets
    assert all(n.forcage is None for n in q.noeuds.values())
    print("arrêt d'urgence : ambulance retirée, feux revenus au cycle normal")

    q = preparer(2)
    for t in range(40000):
        if t % 1500 == 100:
            q.executer({"nom": "urgence", "depart": random.choice(["E1", "E2", "E3", "E4"]),
                        "arrivee": random.choice(["E1", "E2", "E3", "E4"]), "gravite": random.randint(1, 3),
                        "prioritaire": random.random() < 0.7})
        if t == 9000:
            q.executer({"nom": "route", "route": "h12", "etat": "bloquee"})
        if t == 15000:
            q.executer({"nom": "route", "route": "h12", "etat": "fluide"})
        q.avancer()
        for u in q.usagers:
            assert math.isfinite(u.x) and math.isfinite(u.y)
    stats = q.statistiques()
    print("stats après 20 minutes simulées :", stats)
    assert len(q.attentes) > 50
    assert all(n.forcage is None for n in q.noeuds.values()) or q.compter("ambulance") > 0

    avec = [duree(True, g) for g in (3, 4, 5)]
    sans = [duree(False, g) for g in (3, 4, 5)]
    print("durées avec priorité :", [round(d, 1) for d in avec], "sans priorité :", [round(d, 1) for d in sans])
    assert sum(avec) < sum(sans)


if __name__ == "__main__":
    main()
