"""Modèle du quartier : usagers, feux, urgences adaptatives, trafic et statistiques."""
import math
import random
import threading

from quartier.carte import (ARRET, ARRIVEES, ENTREES, LONGUEURS, LONGUEUR_VEHICULE, ROUTES, itineraire, trajet)

# Nombre de pas de simulation par seconde (toutes les durées sont comptées en pas)
TPS = 33
# Vitesses en pixels par pas : voiture, ambulance sans priorité, ambulance prioritaire selon la gravité
V_CIVIL = 1.6
V_AMBULANCE = 1.9
V_PRIORITE = {1: 2.6, 2: 3.4, 3: 4.0}
# Nombre maximal de véhicules ajoutés à la main, puis de voitures ajoutées par le trafic automatique
LIMITES = {"voiture": 24, "ambulance": 2}
AUTO_MAX = 14
# Durées des feux : 5 s de vert, 3 s d'orange, 2 s de tout-rouge ; un cycle complet couvre les deux axes
VERT, ORANGE, TOUT_ROUGE = 5 * TPS, 3 * TPS, 2 * TPS
CYCLE = 2 * (VERT + ORANGE + TOUT_ROUGE)
# Distance (pixels) dont les voitures se serrent à droite pour laisser passer l'ambulance
DECALAGE_DROITE = 9
ETATS_ROUTE = ("fluide", "dense", "bloquee")


def erreur(message):
    """Message d'erreur renvoyé au client."""
    return {"type": "erreur", "message": message}


def moyenne(valeurs):
    """Moyenne d'une liste, ou None si elle est vide."""
    valeurs = [v for v in valeurs if v is not None]
    return sum(valeurs) / len(valeurs) if valeurs else None


def freinage(distance, vitesse_max):
    """Vitesse maximale permettant de s'arrêter à la distance donnée."""
    # Plus l'obstacle est proche, plus la vitesse autorisée est faible (0 au contact)
    return max(0.0, min(vitesse_max, distance * 0.07))


class Noeud:
    """Feux d'un carrefour : cycle normal, forçage pour une urgence, retour au cycle."""

    def __init__(self, decalage):
        """Crée les feux d'un carrefour, décalés dans le cycle pour ne pas être tous synchronisés."""
        # Position dans le cycle des feux (en pas)
        self.t = decalage
        # Réglage imposé par une ambulance (axe, stratégie), None sinon
        self.forcage = None
        # Pas restants de tout-rouge de sécurité après une urgence
        self.retour = 0

    def avancer(self):
        """Fait avancer le cycle (arrêté pendant un forçage)."""
        # Pendant une urgence, le cycle est gelé : c'est l'ambulance qui décide des couleurs
        if self.forcage:
            return
        # Après une urgence : tout-rouge de sécurité, puis reprise du cycle au début
        if self.retour > 0:
            self.retour -= 1
            if self.retour == 0:
                self.t = 0
            return
        self.t = (self.t + 1) % CYCLE

    def etat(self):
        """État des feux des deux axes : {'ew': couleur, 'ns': couleur}."""
        f = self.forcage
        # Urgence : vert sur l'axe de l'ambulance, rouge sur l'autre
        # (vert tout de suite en onde verte, seulement une fois le carrefour vidé en dégagement)
        if f:
            autre = "ns" if f["axe"] == "ew" else "ew"
            vert = f["mode"] == "onde_verte" or f["pret"]
            return {f["axe"]: "vert" if vert else "rouge", autre: "rouge"}
        if self.retour > 0:
            return {"ew": "rouge", "ns": "rouge"}
        # Cycle normal : vert, orange puis tout-rouge pour l'axe est-ouest, puis pareil pour le nord-sud
        t = self.t
        for axe, autre in (("ew", "ns"), ("ns", "ew")):
            if t < VERT:
                return {axe: "vert", autre: "rouge"}
            if t < VERT + ORANGE:
                return {axe: "orange", autre: "rouge"}
            if t < VERT + ORANGE + TOUT_ROUGE:
                return {"ew": "rouge", "ns": "rouge"}
            t -= VERT + ORANGE + TOUT_ROUGE
        return {"ew": "rouge", "ns": "rouge"}


class Usager:
    """Un véhicule (voiture ou ambulance) qui suit un trajet."""

    def __init__(self, ident, genre, route, naissance, depart, arrivee, prio=False, gravite=1):
        """Crée un véhicule au début de son trajet."""
        self.ident, self.genre, self.prio, self.gravite = ident, genre, prio, gravite
        self.trajet = trajet(route)
        self.naissance, self.depart, self.arrivee = naissance, depart, arrivee
        # s : distance parcourue, v : vitesse, decalage : écart sur le côté quand il se serre à droite
        self.s = self.v = self.decalage = 0.0
        self.attente = self.recalculs = 0
        # k : numéro de la route actuelle dans le trajet, cle : (route, sens),
        # so : distance depuis le début de cette route, boite : carrefour traversé
        self.k, self.cle, self.so, self.boite = 0, route[0], 0.0, None
        self.est_adapt = self.est_fixe = None
        self.x = self.y = self.dx = self.dy = 0.0
        self.placer()

    def placer(self):
        """Calcule la position et la direction à partir de la distance parcourue."""
        x, y, self.dx, self.dy = self.trajet.position(self.s)
        # Le décalage se fait perpendiculairement au sens de la marche
        self.x = x - self.dy * self.decalage
        self.y = y + self.dx * self.decalage


class Quartier:
    """Le quartier de 4 carrefours : feux, usagers, urgences, événements et statistiques."""

    def __init__(self, base=None):
        """Crée un quartier : feux au cycle normal, toutes les routes fluides, aucun véhicule."""
        # Verrou partagé entre le thread de simulation et les threads des clients
        self.verrou = threading.RLock()
        self.base = base
        self.prochain_id = 1
        self.trafic_auto = True
        self.usagers = []
        self.tick = 0
        # Les 4 carrefours démarrent à des moments différents du cycle
        self.noeuds = {q: Noeud(i * 150) for i, q in enumerate(("Q1", "Q2", "Q3", "Q4"))}
        self.etats = {q: n.etat() for q, n in self.noeuds.items()}
        self.etats_routes = {rid: "fluide" for rid in ROUTES}
        # Index des véhicules par route et par carrefour, recalculés à chaque pas
        self.par_route, self.dans_boite = {}, {}
        self.routes_serrees, self.strategies = set(), {}
        self.attentes = []
        self.trajets = []
        # Ambulances demandées qui attendent que leur entrée soit libre
        self.demandes = []

    def compter(self, genre):
        """Nombre de véhicules présents d'un genre donné."""
        return sum(1 for u in self.usagers if u.genre == genre)

    def executer(self, c):
        """Exécute une commande venue d'un client ; retourne un message d'erreur ou None."""
        # Le verrou empêche de modifier le quartier pendant que la simulation avance
        with self.verrou:
            nom = c.get("nom")
            if nom == "auto":
                self.trafic_auto = bool(c.get("valeur"))
            elif nom == "ajout":
                return self.ajouter_voiture()
            elif nom == "urgence":
                return self.lancer_ambulance(c.get("depart"), c.get("arrivee"),
                                             int(c.get("gravite", 1)), bool(c.get("prioritaire", True)))
            elif nom == "fin_urgence":
                return self.arreter_urgences()
            elif nom == "route":
                if c.get("route") not in ROUTES or c.get("etat") not in ETATS_ROUTE:
                    return erreur("route ou état inconnu")
                self.etats_routes[c["route"]] = c["etat"]
            else:
                return erreur("commande inconnue")
        return None

    def cout_statique(self, rid, sens):
        """Coût d'une route sans tenir compte du trafic (avec un peu de variété), infini si elle est bloquée."""
        if self.etats_routes[rid] == "bloquee":
            return math.inf
        # Le petit hasard répartit les voitures quand deux chemins ont presque la même longueur
        return LONGUEURS[(rid, sens)] * random.uniform(0.95, 1.05)

    def cout_urgence(self, rid, sens):
        """Coût d'une route pour une ambulance : longueur multipliée par un facteur de bouchon."""
        etat = self.etats_routes[rid]
        if etat == "bloquee":
            return math.inf
        longueur = LONGUEURS[(rid, sens)]
        # Facteur de bouchon : de 1 (route vide) à 4 (route pleine), un véhicule occupant environ 34 pixels
        facteur = 1 + 3 * min(1.0, len(self.par_route.get((rid, sens), ())) * 34 / longueur)
        # Une route marquée dense coûte en plus trois fois plus cher
        return longueur * facteur * (3 if etat == "dense" else 1)

    def estimer(self, route, gravite):
        """Durée estimée (secondes) d'une route avec le trafic actuel."""
        # Coût en pixels converti en secondes : divisé par la vitesse, puis par le nombre de pas par seconde
        cout = sum(self.cout_urgence(*cle) for cle in route)
        return None if math.isinf(cout) else cout / V_PRIORITE[gravite] / TPS

    def entree_libre(self, cle):
        """Vrai si le début de la route est libre pour y faire entrer un véhicule."""
        # Aucun véhicule dans les 45 premiers pixels de la route
        return all(w.so > 45 for w in self.par_route.get(cle, ()))

    def ajouter_voiture(self):
        """Ajoute une voiture avec un trajet aléatoire ; retourne une erreur éventuelle."""
        if self.compter("voiture") >= LIMITES["voiture"]:
            return erreur("limite de voitures atteinte")
        depart, arrivee = random.sample(ENTREES, 2)
        route, _ = itineraire(depart, arrivee, self.cout_statique)
        if route is None or not self.entree_libre(route[0]):
            return erreur("entrée occupée, réessayer")
        self.usagers.append(Usager(self.prochain_id, "voiture", route, self.tick, depart, arrivee))
        self.prochain_id += 1
        return None

    def lancer_ambulance(self, depart, arrivee, gravite, prioritaire):
        """Demande une ambulance, avec ou sans priorité (sans : sert de comparaison)."""
        if depart not in ENTREES or arrivee not in ENTREES or depart == arrivee:
            return erreur("départ ou arrivée invalide")
        if gravite not in V_PRIORITE:
            return erreur("gravité invalide (1 à 3)")
        if self.compter("ambulance") + len(self.demandes) >= LIMITES["ambulance"]:
            return erreur("limite d'ambulances atteinte")
        # Mesure du trafic à jour avant de vérifier qu'un itinéraire existe
        self.indexer()
        if itineraire(depart, arrivee, self.cout_urgence)[0] is None:
            return erreur("aucun itinéraire possible")
        self.demandes.append({"depart": depart, "arrivee": arrivee, "gravite": gravite,
                              "prio": prioritaire, "tick": self.tick})
        return None

    def arreter_urgences(self):
        """Retire les ambulances en cours et annule les demandes ; les feux reviennent au cycle normal."""
        if not self.demandes and not self.compter("ambulance"):
            return erreur("aucune urgence en cours")
        self.usagers = [u for u in self.usagers if u.genre != "ambulance"]
        self.demandes = []
        return None

    def traiter_demandes(self):
        """Fait entrer les ambulances demandées dès que leur entrée est libre (10 s d'attente au maximum)."""
        for d in list(self.demandes):
            # Demande abandonnée si l'entrée reste occupée plus de 10 s
            if self.tick - d["tick"] > 10 * TPS:
                self.demandes.remove(d)
                continue
            # Itinéraire fixe (sans trafic) et adaptatif (avec trafic) ; sans priorité, l'ambulance garde le fixe
            fixe, _ = itineraire(d["depart"], d["arrivee"], self.cout_statique)
            route = itineraire(d["depart"], d["arrivee"], self.cout_urgence)[0] if d["prio"] else fixe
            if route is None or not self.entree_libre(route[0]):
                continue
            u = Usager(self.prochain_id, "ambulance", route, self.tick, d["depart"], d["arrivee"],
                       d["prio"], d["gravite"])
            # Estimations gardées pour comparer les deux itinéraires dans les statistiques
            u.est_adapt, u.est_fixe = self.estimer(route, d["gravite"]), self.estimer(fixe, d["gravite"])
            self.usagers.append(u)
            self.prochain_id += 1
            self.demandes.remove(d)

    def indexer(self):
        """Classe les véhicules par route (ou par carrefour s'ils sont dans un virage)."""
        self.par_route, self.dans_boite = {}, {}
        for u in self.usagers:
            u.k = u.trajet.indice(u.s)
            # Encore sur la route : rangé par route ; sinon il est dans le virage d'un carrefour
            if u.s <= u.trajet.fins[u.k]:
                u.cle, u.so, u.boite = u.trajet.route[u.k], u.s - u.trajet.debuts[u.k], None
                self.par_route.setdefault(u.cle, []).append(u)
            else:
                u.cle, u.boite = None, ARRIVEES[u.trajet.route[u.k]][0]
                self.dans_boite.setdefault(u.boite, []).append(u)

    def avancer(self):
        """Fait avancer la simulation d'un pas de temps."""
        self.tick += 1
        # Trafic automatique : environ une voiture toutes les 1,2 s, sans dépasser AUTO_MAX
        if self.trafic_auto and random.random() < 0.025 and self.compter("voiture") < AUTO_MAX:
            self.ajouter_voiture()
        # Mesure du trafic : qui est sur quelle route, qui est dans quel carrefour
        self.indexer()
        self.traiter_demandes()
        self.indexer()
        # Les voitures (et les ambulances sans priorité) évitent les routes bloquées
        for u in self.usagers:
            if not u.prio:
                self.contourner(u)
        # Puis les urgences, les feux et enfin le déplacement de chaque véhicule
        self.gerer_urgences()
        for n in self.noeuds.values():
            n.avancer()
        self.etats = {q: n.etat() for q, n in self.noeuds.items()}
        for u in list(self.usagers):
            self.deplacer(u)

    def contourner(self, u):
        """Change l'itinéraire d'un véhicule dont la prochaine route est bloquée, s'il existe un autre chemin."""
        route = u.trajet.route
        if u.cle is None or u.k + 1 >= len(route) or self.etats_routes[route[u.k + 1][0]] != "bloquee":
            return
        # Nouveau chemin depuis le carrefour où il arrive ; il reste sur sa route actuelle jusque-là
        nouveau, _ = itineraire(ARRIVEES[u.cle][0], u.arrivee, self.cout_statique)
        if nouveau is not None:
            u.trajet = trajet([u.cle] + nouveau)
            u.s, u.k = u.so, 0

    def recalculer(self, u):
        """Recalcule l'itinéraire d'une ambulance au prochain carrefour si c'est nettement mieux."""
        cle = u.trajet.route[u.k]
        noeud = ARRIVEES[cle][0]
        reste = u.trajet.route[u.k + 1:]
        nouveau, cout_nouveau = itineraire(noeud, u.arrivee, self.cout_urgence)
        if nouveau is None or nouveau == reste:
            return
        cout_actuel = sum(self.cout_urgence(*c) for c in reste)
        # On change seulement si l'ancien chemin est bloqué ou si le nouveau est au moins 15 % moins cher
        if math.isinf(cout_actuel) or cout_nouveau < 0.85 * cout_actuel:
            decalage = u.s - u.trajet.debuts[u.k]
            u.trajet = trajet([cle] + nouveau)
            u.s, u.k, u.recalculs = decalage, 0, u.recalculs + 1

    def gerer_urgences(self):
        """Prépare à l'avance les carrefours traversés par les ambulances prioritaires."""
        self.routes_serrees = set()
        self.strategies = {}
        actifs = set()
        for u in self.usagers:
            if u.genre != "ambulance" or not u.prio:
                continue
            # Recalcul environ une fois par seconde, à un moment différent pour chaque ambulance
            if self.tick % 30 == u.ident % 30 and u.cle is not None and u.k < len(u.trajet.route) - 1:
                self.recalculer(u)
            route = u.trajet.route
            # Sur la route actuelle et la suivante, les voitures se serrent à droite
            self.routes_serrees.add(route[u.k])
            if u.k + 1 < len(route):
                self.routes_serrees.add(route[u.k + 1])
            # Les feux sont préparés 7, 9 ou 11 s à l'avance selon la gravité
            preparation = (5 + 2 * u.gravite) * TPS
            for j in range(u.k, len(route) - 1):
                # Temps (en pas) avant que l'ambulance atteigne la ligne d'arrêt du carrefour j
                delai = (u.trajet.fins[j] - ARRET - u.s) / V_PRIORITE[u.gravite]
                if delai <= preparation:
                    noeud = self.forcer(u, j, delai)
                    if noeud:
                        actifs.add(noeud)
        # Carrefours que plus aucune ambulance ne réclame : tout-rouge de sécurité puis cycle normal
        for nom, n in self.noeuds.items():
            if n.forcage and nom not in actifs:
                n.forcage, n.retour = None, TOUT_ROUGE

    def forcer(self, u, j, delai):
        """Choisit la stratégie d'un carrefour pour l'ambulance : onde verte ou dégagement."""
        cle = u.trajet.route[j]
        nom, axe = ARRIVEES[cle]
        n = self.noeuds[nom]
        if n.forcage is None:
            # Stratégie choisie une seule fois :
            # dégagement si au moins 3 véhicules sont devant l'ambulance, sinon onde verte
            devant = [w for w in self.par_route.get(cle, ()) if w is not u and w.so > u.so]
            mode = "degagement" if len(devant) >= 3 else "onde_verte"
            n.forcage = {"amb": u.ident, "axe": axe, "mode": mode, "pret": False}
        f = n.forcage
        # Un carrefour déjà réservé par une autre ambulance n'est pas modifié
        if f["amb"] != u.ident:
            return None
        if f["mode"] == "degagement":
            # En dégagement, le vert n'est donné que quand le carrefour est vide et l'ambulance à moins de 4 s
            f["pret"] = not self.dans_boite.get(nom) and delai <= 4 * TPS
        self.strategies[nom] = f["mode"]
        return nom

    def vitesse_max(self, u):
        """Vitesse maximale d'un véhicule sur sa route actuelle."""
        vitesse = V_PRIORITE[u.gravite] if u.prio else V_AMBULANCE if u.genre == "ambulance" else V_CIVIL
        # Une route dense divise la vitesse par deux
        if u.cle and self.etats_routes[u.cle[0]] == "dense":
            vitesse *= 0.5
        return vitesse

    def doit_s_arreter(self, u, distance):
        """Vrai si le véhicule doit s'arrêter à la ligne d'arrêt du prochain carrefour."""
        noeud, axe = ARRIVEES[u.cle]
        couleur = self.etats[noeud][axe]
        # Arrêt si le feu est rouge ou si la route suivante est bloquée (l'ambulance a le vert grâce à la priorité)
        if self.etats_routes[u.trajet.route[u.k + 1][0]] == "bloquee" or couleur == "rouge":
            return True
        # À l'orange, on ne s'arrête que si on a la place de freiner
        if couleur == "orange" and not u.prio:
            return distance > 4 * u.v + 6 or u.v < 0.6
        # On n'entre pas dans un carrefour encore occupé par un véhicule de l'autre axe
        for w in self.dans_boite.get(noeud, ()):
            if ARRIVEES[w.trajet.route[w.k]][1] != axe and distance < 30:
                return True
        return False

    def ecart_devant(self, u):
        """Distance au véhicule qui précède (même voie, route suivante comprise), ou None."""
        ecart = None
        # L'ambulance prioritaire ignore les voitures déjà serrées à droite (elle passe à côté)
        for w in self.par_route.get(u.cle, ()) if u.cle else ():
            if w is not u and w.so > u.so and not (u.prio and w.genre == "voiture" and w.decalage > 4):
                ecart = w.so - u.so if ecart is None else min(ecart, w.so - u.so)
        # Personne devant sur cette route : on regarde le début de la route suivante
        if ecart is None and u.k + 1 < len(u.trajet.route):
            reste = u.trajet.debuts[u.k + 1] - u.s
            if reste < 90:
                for w in self.par_route.get(u.trajet.route[u.k + 1], ()):
                    if not (u.prio and w.genre == "voiture" and w.decalage > 4):
                        ecart = reste + w.so if ecart is None else min(ecart, reste + w.so)
        return ecart

    def deplacer(self, u):
        """Met à jour la vitesse puis la position d'un véhicule."""
        maximum = self.vitesse_max(u)
        cible = maximum
        derniere = u.k >= len(u.trajet.route) - 1
        ligne = u.trajet.fins[u.k] - ARRET
        distance = ligne - u.s
        # Ralentir pour s'arrêter au feu si nécessaire
        if u.cle is not None and not derniere and distance >= 0 and self.doit_s_arreter(u, distance):
            cible = min(cible, freinage(distance, maximum))
        # Distance de sécurité avec le véhicule de devant (c'est ce qui crée les files d'attente)
        ecart = self.ecart_devant(u)
        if ecart is not None:
            cible = min(cible, freinage(ecart - LONGUEUR_VEHICULE - 8, maximum))
        # Décalage sur le côté : les voitures se serrent à droite, l'ambulance se place au milieu
        voulu = 0.0
        if u.cle in self.routes_serrees:
            voulu = -8.0 if u.prio else DECALAGE_DROITE if u.genre == "voiture" else 0.0
        u.decalage += max(-0.8, min(0.8, voulu - u.decalage))
        # Accélération douce, freinage plus fort
        u.v = min(cible, u.v + 0.08) if u.v < cible else max(cible, u.v - 0.25)
        u.s += u.v
        # Un véhicule presque arrêté compte comme en attente
        if u.v < 0.15:
            u.attente += 1
        if u.s >= u.trajet.total:
            self.terminer(u)
        else:
            u.placer()

    def terminer(self, u):
        """Retire un véhicule arrivé et enregistre ses statistiques."""
        self.usagers.remove(u)
        self.attentes.append(u.attente / TPS)
        # Les trajets d'ambulance sont gardés pour les statistiques et enregistrés dans sqlite3
        if u.genre == "ambulance":
            t = {"depart": u.depart, "arrivee": u.arrivee, "gravite": u.gravite, "prio": u.prio,
                 "duree": (self.tick - u.naissance) / TPS, "est_adapt": u.est_adapt, "est_fixe": u.est_fixe,
                 "recalculs": u.recalculs, "route": [list(c) for c in u.trajet.route]}
            self.trajets.append(t)
            if self.base:
                self.base.enregistrer_trajet(t)

    def statistiques(self):
        """Statistiques en direct du quartier."""
        avec = [t for t in self.trajets if t["prio"]]
        sans = [t for t in self.trajets if not t["prio"]]
        return {
            "vehicules": len(self.usagers),
            # Attente moyenne sur les 20 derniers véhicules arrivés
            "attente": moyenne(self.attentes[-20:]),
            "trajet_avec": moyenne([t["duree"] for t in avec]),
            "trajet_sans": moyenne([t["duree"] for t in sans]),
            "estimation_adaptative": moyenne([t["est_adapt"] for t in avec]),
            "estimation_fixe": moyenne([t["est_fixe"] for t in avec]),
            "recalculs": sum(t["recalculs"] for t in avec),
        }

    def instantane(self):
        """Photographie de l'état courant, envoyée aux clients."""
        # Clés courtes (g, p, x, y, a) pour alléger le message envoyé 11 fois par seconde
        usagers = [{"id": u.ident, "g": u.genre, "p": u.prio, "x": round(u.x, 1), "y": round(u.y, 1),
                    "a": round(math.degrees(math.atan2(u.dy, u.dx)), 1)} for u in self.usagers]
        routes = {rid: {"etat": self.etats_routes[rid],
                        "n": [len(self.par_route.get((rid, 1), ())), len(self.par_route.get((rid, -1), ()))]}
                  for rid in ROUTES}
        ambulances = [{"id": u.ident, "prio": u.prio, "gravite": u.gravite, "route": [list(c) for c in u.trajet.route]}
                      for u in self.usagers if u.genre == "ambulance"]
        return {"type": "etat", "tick": self.tick, "auto": self.trafic_auto,
                "usagers": usagers, "feux": self.etats, "routes": routes, "ambulances": ambulances,
                "strategies": self.strategies, "serrer": bool(self.routes_serrees),
                "compteurs": {"voiture": self.compter("voiture"),
                              "ambulance": self.compter("ambulance") + len(self.demandes)}, "stats": self.statistiques()}
