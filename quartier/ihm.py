"""Fenêtre du client : carte du quartier, commandes et statistiques."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QFrame, QGraphicsPathItem, QGraphicsScene, QGraphicsView,
                             QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget)

from quartier.carte import ENTREES, trajet
from quartier.client_reseau import ClientReseau
from quartier.dessin import brosse, colorer_route, construire_decor, creer_vehicule, densite_route, trace
from quartier.simulation import ETATS_ROUTE, LIMITES

LIBELLES = {"onde_verte": "onde verte", "degagement": "dégagement"}
GRAVITES = ("légère", "sérieuse", "vitale")


def valeur(nombre, unite=""):
    """Formate un nombre pour l'affichage ('-' s'il n'existe pas encore)."""
    return "-" if nombre is None else f"{nombre:.1f}{unite}"


class VueQuartier(QGraphicsView):
    """Vue qui garde toute la carte visible quand la fenêtre change de taille."""

    def resizeEvent(self, event):
        """Réajuste le zoom pour que toute la carte reste visible."""
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class FenetreQuartier(QMainWindow):
    """Fenêtre qui affiche l'état reçu du serveur et lui envoie les commandes."""

    def __init__(self, hote, port):
        """Construit la fenêtre puis lance le thread réseau."""
        super().__init__()
        self.setWindowTitle(f"Les Fibreux - Quartier connecté ({hote}:{port})")
        self.scene = QGraphicsScene()
        self.decor = construire_decor(self.scene, self.changer_route)
        self.vehicules, self.itineraires, self.etats_routes = {}, {}, {}

        self.vue = VueQuartier(self.scene)
        self.vue.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.vue.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.vue.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.banniere = QLabel("Il faut se serrer à droite !")
        self.banniere.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.banniere.setStyleSheet("background:#c0392b;color:white;font:bold 18px;padding:6px")
        self.banniere.setVisible(False)
        gauche = QVBoxLayout()
        gauche.addWidget(self.banniere)
        gauche.addWidget(self.vue, 1)
        central = QWidget()
        disposition = QHBoxLayout(central)
        disposition.addLayout(gauche, 1)
        disposition.addWidget(self.creer_panneau())
        self.setCentralWidget(central)

        self.reseau = ClientReseau(hote, port)
        # Les messages du thread réseau arrivent dans recevoir() par signal/slot, dans le thread de Qt
        self.reseau.message.connect(self.recevoir)
        self.reseau.statut.connect(self.statut.setText)
        self.reseau.start()

    def commande(self, nom, **options):
        """Envoie une commande au serveur."""
        self.reseau.envoyer({"type": "commande", "nom": nom, **options})

    def bouton(self, texte, action):
        """Crée un bouton relié à une action sans argument."""
        bouton = QPushButton(texte)
        bouton.clicked.connect(lambda _=False: action())
        return bouton

    def liste(self, valeurs, defaut):
        """Crée une liste déroulante."""
        liste = QComboBox()
        liste.addItems(valeurs)
        liste.setCurrentText(defaut)
        return liste

    def creer_panneau(self):
        """Construit le panneau de droite : commandes, urgence et statistiques."""
        panneau = QFrame()
        panneau.setFixedWidth(330)
        mise = QVBoxLayout(panneau)
        self.statut = QLabel("Connexion en cours...")
        self.statut.setWordWrap(True)
        mise.addWidget(self.statut)
        self.bouton_voiture = self.bouton("", lambda: self.commande("ajout"))
        mise.addWidget(self.bouton_voiture)
        auto = QCheckBox("Trafic automatique")
        auto.setChecked(True)
        auto.toggled.connect(lambda etat: self.commande("auto", valeur=etat))
        mise.addWidget(auto)
        mise.addWidget(self.aide("Coché : des voitures entrent seules dans le quartier (jusqu'à 14). "
                                 "Décoché : plus aucune voiture n'entre, le quartier se vide."))
        mise.addWidget(QLabel("Urgence : départ, arrivée, gravité"))
        ligne = QHBoxLayout()
        self.depart = self.liste(ENTREES, "E3")
        self.arrivee = self.liste(ENTREES, "E4")
        self.gravite = self.liste([f"{i} - {nom}" for i, nom in enumerate(GRAVITES, 1)], "2 - sérieuse")
        for element in (self.depart, self.arrivee, self.gravite):
            ligne.addWidget(element)
        mise.addLayout(ligne)
        mise.addWidget(self.aide("Plus la gravité est haute, plus l'ambulance prioritaire roule vite "
                                 "et plus tôt les feux sont préparés devant elle."))
        self.priorite = QCheckBox("Avec priorité (décocher pour comparer)")
        self.priorite.setChecked(True)
        mise.addWidget(self.priorite)
        self.bouton_ambulance = self.bouton("", self.lancer_ambulance)
        self.bouton_ambulance.setStyleSheet("background:#c0392b;color:white;font-weight:bold;padding:8px")
        mise.addWidget(self.bouton_ambulance)
        mise.addWidget(self.bouton("Arrêter l'urgence", lambda: self.commande("fin_urgence")))
        mise.addWidget(self.aide("Clique sur une route pour la rendre dense ou bloquée."))
        mise.addWidget(QLabel("Statistiques :"))
        self.stats = QLabel()
        self.stats.setWordWrap(True)
        mise.addWidget(self.stats)
        mise.addStretch()
        return panneau

    def aide(self, contenu):
        """Petit texte d'explication en gris."""
        label = QLabel(contenu)
        label.setWordWrap(True)
        label.setStyleSheet("color:#666666;font-size:11px")
        return label

    def lancer_ambulance(self):
        """Demande une ambulance avec les réglages choisis."""
        self.commande("urgence", depart=self.depart.currentText(), arrivee=self.arrivee.currentText(),
                      gravite=self.gravite.currentIndex() + 1, prioritaire=self.priorite.isChecked())

    def changer_route(self, rid):
        """Fait passer une route à l'état suivant : fluide, dense, bloquée."""
        etat = self.etats_routes.get(rid, "fluide")
        # État suivant dans l'ordre fluide, dense, bloquée, puis retour à fluide
        self.commande("route", route=rid, etat=ETATS_ROUTE[(ETATS_ROUTE.index(etat) + 1) % 3])

    def recevoir(self, message):
        """Slot : traite un message reçu du serveur."""
        if message.get("type") == "etat":
            self.maj_etat(message)
        elif message.get("type") == "erreur":
            self.statut.setText("Serveur : " + message["message"])

    def maj_etat(self, etat):
        """Redessine la carte à partir de l'état envoyé par le serveur."""
        # Le gyrophare change de couleur tous les 6 pas de simulation
        clignote = (etat["tick"] // 6) % 2 == 0
        presents = set()
        for u in etat["usagers"]:
            presents.add(u["id"])
            # Chaque véhicule est créé une seule fois, puis seulement déplacé
            item = self.vehicules.get(u["id"])
            if item is None:
                item = creer_vehicule(u["g"], u["id"])
                self.scene.addItem(item)
                self.vehicules[u["id"]] = item
            item.setPos(u["x"], u["y"])
            item.setRotation(u["a"])
            if item.gyro:
                item.gyro[0].setBrush(brosse("#2d7bff" if clignote else "#0a1f5c"))
                item.gyro[1].setBrush(brosse("#0a1f5c" if clignote else "#2d7bff"))
        # Les véhicules absents de l'état sont arrivés : on les retire de la scène
        for ident in [i for i in self.vehicules if i not in presents]:
            self.scene.removeItem(self.vehicules.pop(ident))

        for (noeud, axe), feux in self.decor["feux"].items():
            for feu in feux:
                feu.set_etat(etat["feux"][noeud][axe])
        for rid, infos in etat["routes"].items():
            self.etats_routes[rid] = infos["etat"]
            axe, etiquette = self.decor["routes"][rid]
            colorer_route(axe, etiquette, infos["etat"], densite_route(rid, infos["n"]))
        for noeud, texte in self.decor["strategies"].items():
            texte.setText(LIBELLES.get(etat["strategies"].get(noeud), ""))
        self.maj_itineraires(etat["ambulances"])
        prioritaires = [a["gravite"] for a in etat["ambulances"] if a["prio"]]
        if prioritaires:
            self.banniere.setText(f"Ambulance en urgence {GRAVITES[max(prioritaires) - 1]} : "
                                  "il faut se serrer à droite !")
        self.banniere.setVisible(etat["serrer"])
        self.maj_panneau(etat)

    def maj_itineraires(self, ambulances):
        """Trace en bleu l'itinéraire des ambulances prioritaires."""
        actuelles = {a["id"]: tuple(map(tuple, a["route"])) for a in ambulances if a["prio"]}
        # On efface les tracés des ambulances parties ou dont l'itinéraire a changé
        for ident in [i for i in self.itineraires if i not in actuelles or self.itineraires[i][0] != actuelles[i]]:
            self.scene.removeItem(self.itineraires.pop(ident)[1])
        for ident, route in actuelles.items():
            if ident not in self.itineraires:
                item = QGraphicsPathItem(trace(trajet(route).points))
                item.setPen(QPen(QColor("#378ADD"), 5))
                item.setZValue(5)
                item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
                self.scene.addItem(item)
                self.itineraires[ident] = (route, item)

    def maj_panneau(self, etat):
        """Met à jour les compteurs et les statistiques."""
        c, s = etat["compteurs"], etat["stats"]
        self.bouton_voiture.setText(f"Ajouter une voiture ({c['voiture']}/{LIMITES['voiture']})")
        self.bouton_ambulance.setText(f"Lancer l'ambulance ({c['ambulance']}/{LIMITES['ambulance']})")
        self.stats.setText(
            f"Véhicules : {s['vehicules']}\n"
            f"Attente moyenne : {valeur(s['attente'], ' s')}\n"
            f"Trajet ambulance avec priorité : {valeur(s['trajet_avec'], ' s')}\n"
            f"Trajet ambulance sans priorité : {valeur(s['trajet_sans'], ' s')}\n"
            f"Estimation itinéraire adaptatif : {valeur(s['estimation_adaptative'], ' s')}\n"
            f"Estimation itinéraire fixe : {valeur(s['estimation_fixe'], ' s')}\n"
            f"Recalculs d'itinéraire : {s['recalculs']}"
        )

    def closeEvent(self, event):
        """Ferme proprement la connexion avant de quitter."""
        self.reseau.arreter()
        self.reseau.wait(2000)
        super().closeEvent(event)
