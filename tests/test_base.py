"""Tests de la base sqlite3 des trajets d'ambulance (en mémoire, aucun fichier créé).

Lancer depuis la racine : python -m tests.test_base
"""
import json

from quartier.base import Base


def main():
    """Enregistre deux trajets puis vérifie qu'ils sont relus dans l'ordre, avec leur itinéraire."""
    base = Base(":memory:")
    assert base.lister_trajets() == []
    for prio, duree in ((True, 31.5), (False, 44.0)):
        base.enregistrer_trajet({"depart": "E3", "arrivee": "E4", "gravite": 2, "prio": prio, "duree": duree,
                                 "est_adapt": 30.0, "est_fixe": 40.0, "recalculs": 0, "route": [["h34", 1]]})
    trajets = base.lister_trajets()
    assert [t["prioritaire"] for t in trajets] == [1, 0]
    assert [t["duree_s"] for t in trajets] == [31.5, 44.0]
    assert json.loads(trajets[0]["itineraire"]) == [["h34", 1]]
    base.fermer()
    print("OK : base (enregistrement et relecture des trajets)")


if __name__ == "__main__":
    main()
