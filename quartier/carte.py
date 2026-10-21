"""Géométrie du quartier : carrefours, routes, voies de circulation et itinéraires."""
import bisect
import heapq
import math

# Dimensions de la carte et des éléments, en pixels
LARGEUR = 1200
HAUTEUR = 820
DEMI_CARREFOUR = 34
VOIE = 11
ARRET = 18
LONGUEUR_VEHICULE = 22
ENTREES = ("E1", "E2", "E3", "E4")

# Position des 4 carrefours et des 4 entrées/sorties
NOEUDS = {
    "Q1": (330, 260), "Q2": (870, 260), "Q3": (330, 560), "Q4": (870, 560),
    "E1": (0, 260), "E2": (1200, 260), "E3": (0, 560), "E4": (1200, 560),
}
# Chaque route : (départ, arrivée, points du tracé, type).
# Deux routes peuvent relier les mêmes carrefours (h12 et c12)
ROUTES = {
    "h12": ("Q1", "Q2", [(330, 260), (870, 260)], "directe"),
    "h34": ("Q3", "Q4", [(330, 560), (870, 560)], "directe"),
    "v13": ("Q1", "Q3", [(330, 260), (330, 560)], "directe"),
    "v24": ("Q2", "Q4", [(870, 260), (870, 560)], "directe"),
    "c12": ("Q1", "Q2", [(330, 260), (330, 80), (870, 80), (870, 260)], "contournement"),
    "c34": ("Q3", "Q4", [(330, 560), (330, 740), (870, 740), (870, 560)], "contournement"),
    "e1": ("E1", "Q1", [(0, 260), (330, 260)], "entree"),
    "e2": ("E2", "Q2", [(1200, 260), (870, 260)], "entree"),
    "e3": ("E3", "Q3", [(0, 560), (330, 560)], "entree"),
    "e4": ("E4", "Q4", [(1200, 560), (870, 560)], "entree"),
}


def longueur(points):
    """Longueur d'une ligne brisée."""
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def point_sur(points, distance):
    """Point (x, y, dx, dy) situé à une distance donnée du début d'une ligne brisée."""
    # On parcourt les segments jusqu'à celui qui contient la distance demandée
    dernier = len(points) - 2
    for i, (a, b) in enumerate(zip(points, points[1:])):
        segment = math.dist(a, b)
        if distance <= segment or i == dernier:
            t = min(1.0, distance / segment)
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
                    (b[0] - a[0]) / segment, (b[1] - a[1]) / segment)
        distance -= segment


def rogner(points, debut, fin):
    """Raccourcit une ligne brisée au début et à la fin."""
    total = longueur(points)
    resultat = [point_sur(points, debut)[:2]]
    cumul = 0.0
    for a, b in zip(points, points[1:]):
        cumul += math.dist(a, b)
        if debut < cumul < total - fin:
            resultat.append(b)
    resultat.append(point_sur(points, total - fin)[:2])
    return resultat


def decaler(points, decalage):
    """Décale une ligne brisée vers sa droite (voie de circulation)."""
    # Vecteur perpendiculaire (vers la droite) de chaque segment
    normales = []
    for a, b in zip(points, points[1:]):
        d = math.dist(a, b)
        normales.append((-(b[1] - a[1]) / d, (b[0] - a[0]) / d))
    resultat = []
    for i, p in enumerate(points):
        if i == 0:
            m = normales[0]
        elif i == len(points) - 1:
            m = normales[-1]
        else:
            n1, n2 = normales[i - 1], normales[i]
            # Dans un angle, moyenne des deux normales, corrigée pour garder la même largeur de voie
            k = 1 + n1[0] * n2[0] + n1[1] * n2[1]
            m = ((n1[0] + n2[0]) / k, (n1[1] + n2[1]) / k)
        resultat.append((p[0] + m[0] * decalage, p[1] + m[1] * decalage))
    return resultat


def construire_voie(rid, sens):
    """Voie de circulation (à droite) d'une route dans un sens donné."""
    a, b, points, _ = ROUTES[rid]
    depart, arrivee = (a, b) if sens == 1 else (b, a)
    trace = list(points) if sens == 1 else list(reversed(points))
    # La voie s'arrête au bord des carrefours, pas en leur centre
    debut = DEMI_CARREFOUR if depart.startswith("Q") else 0
    fin = DEMI_CARREFOUR if arrivee.startswith("Q") else 0
    return decaler(rogner(trace, debut, fin), VOIE)


# Tables calculées une fois au démarrage : voies, longueurs,
# et pour chaque voie le carrefour et l'axe où elle arrive
VOIES = {(rid, sens): construire_voie(rid, sens) for rid in ROUTES for sens in (1, -1)}
LONGUEURS = {cle: longueur(voie) for cle, voie in VOIES.items()}
ARRIVEES = {}
for (_rid, _sens), _voie in VOIES.items():
    _noeud = ROUTES[_rid][1] if _sens == 1 else ROUTES[_rid][0]
    (_x1, _y1), (_x2, _y2) = _voie[-2], _voie[-1]
    ARRIVEES[(_rid, _sens)] = (_noeud, "ew" if abs(_x2 - _x1) > abs(_y2 - _y1) else "ns")

# Graphe pour Dijkstra : pour chaque nœud, la liste des (voisin, route, sens)
VOISINS = {n: [] for n in NOEUDS}
for _rid, (_a, _b, _, _) in ROUTES.items():
    VOISINS[_a].append((_b, _rid, 1))
    VOISINS[_b].append((_a, _rid, -1))


def courbe(a, controle, b, t):
    """Point d'une courbe de Bézier quadratique (virage dans un carrefour)."""
    x = (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * controle[0] + t ** 2 * b[0]
    y = (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * controle[1] + t ** 2 * b[1]
    return (x, y)


def itineraire(depart, arrivee, cout):
    """Plus court chemin (Dijkstra) sur le graphe des routes, qui peut avoir plusieurs routes entre deux carrefours.

    Retourne (liste de (route, sens), coût total) ou (None, infini).
    """
    # meilleur : plus petit coût connu pour atteindre chaque nœud ; precedent : par où on y est arrivé
    meilleur = {n: math.inf for n in NOEUDS}
    meilleur[depart] = 0.0
    precedent = {}
    file = [(0.0, depart)]
    while file:
        # On traite toujours le nœud le moins cher de la file de priorité
        cumul, noeud = heapq.heappop(file)
        # Entrée périmée : on a déjà trouvé mieux pour ce nœud
        if cumul > meilleur[noeud]:
            continue
        if noeud == arrivee:
            break
        # On regarde chaque route sortante (une route bloquée a un coût infini)
        for voisin, rid, sens in VOISINS[noeud]:
            total = cumul + cout(rid, sens)
            if total < meilleur[voisin]:
                meilleur[voisin] = total
                precedent[voisin] = (noeud, (rid, sens))
                heapq.heappush(file, (total, voisin))
    if meilleur[arrivee] == math.inf:
        return None, math.inf
    # On remonte les prédécesseurs depuis l'arrivée pour reconstruire le chemin
    route = []
    noeud = arrivee
    while noeud != depart:
        noeud, cle = precedent[noeud]
        route.append(cle)
    route.reverse()
    return route, meilleur[arrivee]


class Trajet:
    """Chemin continu d'un véhicule : routes successives reliées par des virages."""

    def __init__(self, route):
        """Assemble les voies du trajet en une seule ligne, avec un virage à chaque carrefour."""
        self.route = list(route)
        self.points, self.cumul, self.debuts, self.fins = [], [], [], []
        for k, cle in enumerate(self.route):
            voie = VOIES[cle]
            if self.points:
                self.ajouter(self.relier(voie, ARRIVEES[self.route[k - 1]][0]))
            # debuts et fins : distance à laquelle chaque route commence et finit sur le trajet
            self.debuts.append(self.cumul[-1] if self.cumul else 0.0)
            self.ajouter(voie)
            self.fins.append(self.cumul[-1])
        self.total = self.cumul[-1]

    def ajouter(self, nouveaux):
        """Ajoute des points en ignorant les doublons."""
        for p in nouveaux:
            if not self.points:
                self.points.append(p)
                self.cumul.append(0.0)
            elif math.dist(self.points[-1], p) > 1e-6:
                self.cumul.append(self.cumul[-1] + math.dist(self.points[-1], p))
                self.points.append(p)

    def relier(self, voie, noeud):
        """Points du virage entre la fin du trajet actuel et le début de la voie suivante."""
        a, b = self.points[-1], voie[0]
        d1 = (a[0] - self.points[-2][0], a[1] - self.points[-2][1])
        d2 = (voie[1][0] - b[0], voie[1][1] - b[1])
        # Produit vectoriel nul : on va tout droit, pas besoin de virage
        if abs(d1[0] * d2[1] - d1[1] * d2[0]) < 1e-6 * math.hypot(*d1) * math.hypot(*d2):
            return [b]
        return [courbe(a, NOEUDS[noeud], b, i / 6) for i in range(1, 7)]

    def position(self, s):
        """Position (x, y) et direction (dx, dy) à la distance s du début."""
        # Recherche dichotomique du segment qui contient la distance s
        i = min(max(bisect.bisect_right(self.cumul, s) - 1, 0), len(self.points) - 2)
        a, b = self.points[i], self.points[i + 1]
        d = self.cumul[i + 1] - self.cumul[i]
        t = min(1.0, max(0.0, (s - self.cumul[i]) / d))
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, (b[0] - a[0]) / d, (b[1] - a[1]) / d)

    def indice(self, s):
        """Indice de la route sur laquelle (ou juste après laquelle) se trouve la distance s."""
        return max(bisect.bisect_right(self.debuts, s) - 1, 0)


# Un trajet ne change jamais : on le garde en mémoire pour ne pas le recalculer
_CACHE = {}


def trajet(route):
    """Retourne le Trajet d'une route, en le calculant une seule fois."""
    cle = tuple(route)
    if cle not in _CACHE:
        _CACHE[cle] = Trajet(route)
    return _CACHE[cle]
