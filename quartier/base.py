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

    def fermer(self):
        """Ferme le fichier de base (appelé à l'arrêt du serveur)."""
        with self.verrou:
            self.connexion.close()

    def lister_trajets(self):
        """Retourne les trajets enregistrés, du plus ancien au plus récent, sous forme de dictionnaires."""
        with self.verrou:
            curseur = self.connexion.execute("SELECT * FROM trajet_ambulance ORDER BY id")
            colonnes = [c[0] for c in curseur.description]
            return [dict(zip(colonnes, ligne)) for ligne in curseur.fetchall()]

    def moyennes(self):
        """Durée moyenne (s) et nombre de trajets, avec et sans priorité : {True: (moyenne, n), False: ...}."""
        with self.verrou:
            lignes = self.connexion.execute(
                "SELECT prioritaire, AVG(duree_s), COUNT(*) FROM trajet_ambulance GROUP BY prioritaire").fetchall()
        resultat = {True: (None, 0), False: (None, 0)}
        for prio, moyenne, nombre in lignes:
            resultat[bool(prio)] = (moyenne, nombre)
        return resultat
