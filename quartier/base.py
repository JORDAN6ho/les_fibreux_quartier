"""Stockage des trajets d'ambulance dans une base sqlite3."""
import datetime
import json
import sqlite3
import threading


class Base:
    """Base de statistiques (fichier unique, aucun serveur à installer)."""

    def __init__(self, chemin):
        """Ouvre (ou crée) le fichier de base et la table des trajets."""
        # check_same_thread=False : la base est utilisée depuis le thread de simulation ;
        # le verrou protège les écritures
        self.connexion = sqlite3.connect(chemin, check_same_thread=False)
        self.verrou = threading.Lock()
        self.connexion.execute(
            "CREATE TABLE IF NOT EXISTS trajet_ambulance ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, depart TEXT, arrivee TEXT, gravite INTEGER, "
            "prioritaire INTEGER, duree_s REAL, estimation_adaptative_s REAL, estimation_fixe_s REAL, "
            "recalculs INTEGER, itineraire TEXT)"
        )

    def enregistrer_trajet(self, t):
        """Enregistre un trajet d'ambulance terminé (dictionnaire)."""
        with self.verrou:
            self.connexion.execute(
                "INSERT INTO trajet_ambulance (date, depart, arrivee, gravite, prioritaire, duree_s, "
                "estimation_adaptative_s, estimation_fixe_s, recalculs, itineraire) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (datetime.datetime.now().isoformat(timespec="seconds"), t["depart"], t["arrivee"], t["gravite"],
                 int(t["prio"]), t["duree"], t["est_adapt"], t["est_fixe"], t["recalculs"], json.dumps(t["route"])),
            )
            self.connexion.commit()
