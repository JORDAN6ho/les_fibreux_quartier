"""Test de l'outil d'affichage des trajets (outils/trajets.py).

Lancer depuis la racine : python -m tests.test_outils
"""
import contextlib
import io
import os
import tempfile

from outils.trajets import afficher
from quartier.base import Base


def main():
    """Crée une base temporaire avec un trajet et vérifie l'affichage."""
    with tempfile.TemporaryDirectory() as dossier:
        chemin = os.path.join(dossier, "stats.db")
        base = Base(chemin)
        base.enregistrer_trajet({"depart": "E3", "arrivee": "E4", "gravite": 2, "prio": True, "duree": 11.3,
                                 "est_adapt": 11.0, "est_fixe": 12.0, "recalculs": 0,
                                 "route": [["e3", 1], ["h34", 1], ["e4", -1]]})
        base.fermer()
        sortie = io.StringIO()
        with contextlib.redirect_stdout(sortie):
            assert afficher(chemin) == 1
    texte = sortie.getvalue()
    assert "e3-h34-e4" in texte and "Moyenne avec priorité : 11.3 s (1 trajet(s))" in texte, texte
    print("OK : outil d'affichage des trajets")


if __name__ == "__main__":
    main()
