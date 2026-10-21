"""Dessin de la carte, des feux et des véhicules avec les classes graphiques de Qt."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPainterPath, QPen
from PyQt6.QtWidgets import (QGraphicsEllipseItem, QGraphicsItemGroup, QGraphicsLineItem, QGraphicsPathItem,
                             QGraphicsRectItem, QGraphicsSimpleTextItem)

from quartier.carte import (ARRIVEES, DEMI_CARREFOUR, HAUTEUR, LARGEUR, LONGUEURS, NOEUDS, ROUTES, VOIE, VOIES,
                            longueur, point_sur)

ALLUME = {"rouge": "#ff3b30", "orange": "#ffab00", "vert": "#34d058"}
ETEINT = {"rouge": "#3a1210", "orange": "#3d2c00", "vert": "#0f2e17"}
COULEURS_VOITURES = ["#e74c3c", "#3498db", "#f1c40f", "#2ecc71", "#9b59b6", "#e67e22", "#1abc9c"]
BLANC = "#f2f2f2"
COULEURS_BATIMENTS = ["#c9b79c", "#b5a48b", "#d7c9b0", "#a89f91", "#c4a68a"]
# Décor : rectangles (x, y, largeur, hauteur) des immeubles placés entre les routes
BATIMENTS = [
    (30, 30, 110, 70), (160, 30, 110, 70), (30, 120, 80, 60), (130, 120, 140, 60),
    (930, 30, 110, 70), (1060, 30, 110, 70), (930, 120, 140, 60), (1090, 120, 80, 60),
    (390, 120, 90, 65), (510, 120, 180, 65), (720, 120, 90, 65),
    (30, 310, 110, 80), (160, 310, 100, 80), (30, 410, 230, 75),
    (940, 310, 100, 80), (1060, 310, 110, 80), (940, 410, 230, 75),
    (390, 635, 120, 65), (540, 635, 120, 65), (690, 635, 120, 65),
    (30, 640, 110, 70), (160, 640, 100, 70), (940, 640, 100, 70), (1060, 640, 110, 70),
]
PARC = (410, 330, 380, 160)
ARBRES = [(440, 360), (500, 450), (530, 365), (660, 460), (700, 360), (760, 440),
          (290, 15), (910, 15), (15, 790), (290, 790), (910, 790), (1185, 790)]


def brosse(couleur):
    """Pinceau uni de la couleur donnée."""
    return QBrush(QColor(couleur))


def forme(parent, item, fond=None, trait=None, epaisseur=1):
    """Règle les couleurs d'une forme et l'ajoute à un groupe ou à une scène."""
    item.setBrush(brosse(fond) if fond else QBrush(Qt.BrushStyle.NoBrush))
    item.setPen(QPen(QColor(trait), epaisseur) if trait else QPen(Qt.PenStyle.NoPen))
    if isinstance(parent, QGraphicsItemGroup):
        parent.addToGroup(item)
    else:
        parent.addItem(item)
    return item


def rect(parent, x, y, largeur, hauteur, couleur):
    """Rectangle plein sans contour."""
    return forme(parent, QGraphicsRectItem(x, y, largeur, hauteur), couleur)


def arrondi(x, y, largeur, hauteur, rayon):
    """Rectangle aux coins arrondis."""
    chemin = QPainterPath()
    chemin.addRoundedRect(x, y, largeur, hauteur, rayon, rayon)
    return QGraphicsPathItem(chemin)


def texte(scene, contenu, x, y, couleur=BLANC, taille=11):
    """Texte posé sur la scène."""
    item = QGraphicsSimpleTextItem(contenu)
    item.setBrush(brosse(couleur))
    police = item.font()
    police.setPixelSize(taille)
    police.setBold(True)
    item.setFont(police)
    item.setPos(x, y)
    item.setZValue(30)
    scene.addItem(item)
    return item


class ItemRoute(QGraphicsPathItem):
    """Route cliquable : un clic change son état (fluide, dense, bloquée)."""

    def __init__(self, rid, chemin, rappel):
        """Garde l'identifiant de la route et la fonction à appeler lors d'un clic."""
        super().__init__(chemin)
        self.rid, self.rappel = rid, rappel

    def mousePressEvent(self, event):
        """Signale le clic à la fenêtre, qui envoie la commande au serveur."""
        self.rappel(self.rid)


class Feu(QGraphicsItemGroup):
    """Feu tricolore : boîtier arrondi et trois lampes."""

    def __init__(self, rayon=4):
        """Dessine le boîtier et les trois lampes, rouge allumé au départ."""
        super().__init__()
        marge, d = 4, 2 * rayon
        self.largeur, self.hauteur = d + 2 * marge, 3 * (d + marge) + marge
        forme(self, arrondi(0, 0, self.largeur, self.hauteur, 4), "#1c1c1c", "#000000")
        self.lampes = {}
        for i, couleur in enumerate(("rouge", "orange", "vert")):
            self.lampes[couleur] = forme(self, QGraphicsEllipseItem(marge, marge + i * (d + marge), d, d))
        self.set_etat("rouge")

    def set_etat(self, couleur):
        """Allume la lampe de la couleur donnée."""
        for nom, lampe in self.lampes.items():
            lampe.setBrush(brosse(ALLUME[nom] if nom == couleur else ETEINT[nom]))


def trace(points):
    """Chemin Qt qui suit une ligne brisée."""
    chemin = QPainterPath()
    chemin.moveTo(*points[0])
    for p in points[1:]:
        chemin.lineTo(*p)
    return chemin


def stylo(couleur, epaisseur, style=Qt.PenStyle.SolidLine):
    """Stylo à bouts plats."""
    return QPen(QColor(couleur), epaisseur, style, Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.RoundJoin)


def construire_paysage(scene):
    """Décor simple entre les routes : immeubles vus de dessus, un parc et des arbres."""
    for i, (x, y, largeur, hauteur) in enumerate(BATIMENTS):
        couleur = COULEURS_BATIMENTS[i % len(COULEURS_BATIMENTS)]
        forme(scene, QGraphicsRectItem(x, y, largeur, hauteur), couleur, "#6d6253", 2)
        forme(scene, QGraphicsRectItem(x + 8, y + 8, largeur - 16, hauteur - 16),
              QColor(couleur).darker(112).name())
    x, y, largeur, hauteur = PARC
    forme(scene, arrondi(x, y, largeur, hauteur, 14), "#4f8f3a", "#3d7a2c", 2)
    forme(scene, QGraphicsEllipseItem(x + 150, y + 55, 80, 50), "#5dade2", "#3b8fc4", 2)
    texte(scene, "parc", x + 172, y + 110, "#e8f5e0", 12).setZValue(1)
    for x, y in ARBRES:
        forme(scene, QGraphicsEllipseItem(x - 13, y - 13, 26, 26), "#2e7d32", "#1b5e20", 2)


def construire_decor(scene, rappel):
    """Dessine la carte et retourne les éléments à mettre à jour (routes, feux, stratégies)."""
    scene.setBackgroundBrush(brosse("#6aa84f"))
    scene.setSceneRect(0, 0, LARGEUR, HAUTEUR)
    construire_paysage(scene)
    routes = {}
    for rid, (_, _, points, genre) in ROUTES.items():
        chemin = trace(points)
        # Les contournements ont une bordure rouge pour les repérer
        if genre == "contournement":
            bord = QGraphicsPathItem(chemin)
            bord.setPen(stylo("#d94f4f", 46))
            scene.addItem(bord)
        route = ItemRoute(rid, chemin, rappel)
        route.setPen(stylo("#4a4a4a", 40))
        scene.addItem(route)
        axe = QGraphicsPathItem(chemin)
        axe.setPen(stylo(BLANC, 2, Qt.PenStyle.DashLine))
        axe.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        scene.addItem(axe)
        x, y, _, _ = point_sur(points, longueur(points) / 2)
        routes[rid] = (axe, texte(scene, "", x - 30, y - 24, "#ffffff", 12))
    strategies = {}
    for nom, (x, y) in NOEUDS.items():
        if nom.startswith("Q"):
            rect(scene, x - DEMI_CARREFOUR, y - DEMI_CARREFOUR, 2 * DEMI_CARREFOUR, 2 * DEMI_CARREFOUR, "#555555")
            texte(scene, nom, x - 9, y - 9, BLANC, 15)
            strategies[nom] = texte(scene, "", x - 34, y + 42, "#ffffff", 12)
    texte(scene, "E1 entrée/sortie", 6, 222)
    texte(scene, "E3 entrée/sortie", 6, 522)
    texte(scene, "E2 entrée/sortie", LARGEUR - 118, 222)
    texte(scene, "E4 entrée/sortie", LARGEUR - 118, 522)
    texte(scene, "contournement haut", 540, 50)
    texte(scene, "contournement bas", 540, 756)
    feux = {}
    # Un feu par voie qui arrive dans un carrefour, placé à droite de la voie avant la ligne d'arrêt
    for cle, (noeud, axe) in ARRIVEES.items():
        if not noeud.startswith("Q"):
            continue
        (x1, y1), (x2, y2) = VOIES[cle][-2], VOIES[cle][-1]
        # d : direction de la voie arrondie à l'un des 4 sens (droite, gauche, haut, bas)
        d = ((x2 - x1) / abs(x2 - x1 or 1) if abs(x2 - x1) > abs(y2 - y1) else 0.0,
             (y2 - y1) / abs(y2 - y1 or 1) if abs(y2 - y1) >= abs(x2 - x1) else 0.0)
        feu = Feu()
        feu.setPos(x2 - d[0] * 16 - d[1] * (VOIE + 28) - feu.largeur / 2,
                   y2 - d[1] * 16 + d[0] * (VOIE + 28) - feu.hauteur / 2)
        feu.setZValue(50)
        scene.addItem(feu)
        feux.setdefault((noeud, axe), []).append(feu)
    return {"routes": routes, "feux": feux, "strategies": strategies}


def colorer_route(axe, etiquette, etat, densite):
    """Colore l'axe d'une route selon son état forcé ou sa densité mesurée."""
    # L'état forcé par un clic l'emporte sur la densité mesurée
    if etat == "bloquee":
        axe.setPen(stylo("#ff3b30", 6))
        etiquette.setText("BLOQUÉE")
    elif etat == "dense":
        axe.setPen(stylo("#ffab00", 5))
        etiquette.setText("dense (forcé)")
    elif densite >= 0.7:
        axe.setPen(stylo("#ff3b30", 4))
        etiquette.setText("")
    elif densite >= 0.35:
        axe.setPen(stylo("#ffab00", 4))
        etiquette.setText("")
    else:
        axe.setPen(stylo(BLANC, 2, Qt.PenStyle.DashLine))
        etiquette.setText("")


def densite_route(rid, n):
    """Densité mesurée d'une route : véhicules par emplacement de 34 pixels."""
    return max(n[0] * 34 / LONGUEURS[(rid, 1)], n[1] * 34 / LONGUEURS[(rid, -1)])


def creer_vehicule(genre, ident):
    """Image d'un véhicule vu de dessus, tourné vers la droite et centré sur l'origine."""
    groupe = QGraphicsItemGroup()
    groupe.gyro = None
    if genre == "ambulance":
        forme(groupe, arrondi(-12, -6, 24, 12, 3), "#ffffff", "#555555")
        rect(groupe, -12, -1, 24, 2, "#d32f2f")
        rect(groupe, -4, -1.5, 7, 3, "#d32f2f")
        rect(groupe, -1.5, -4, 3, 8, "#d32f2f")
        forme(groupe, QGraphicsRectItem(7, -5, 4, 10), "#37474f")
        groupe.gyro = (forme(groupe, QGraphicsEllipseItem(1, -6, 4, 4), "#2d7bff"),
                       forme(groupe, QGraphicsEllipseItem(1, 2, 4, 4), "#0a1f5c"))
    else:
        forme(groupe, arrondi(-11, -5.5, 22, 11, 3), COULEURS_VOITURES[ident % len(COULEURS_VOITURES)], "#222222")
        forme(groupe, QGraphicsRectItem(2, -4, 5, 8), "#2c3e50")
        forme(groupe, QGraphicsRectItem(-7, -4, 4, 8), "#2c3e50")
        rect(groupe, 10, -4, 1.5, 2.5, "#fff59d")
        rect(groupe, 10, 1.5, 1.5, 2.5, "#fff59d")
    groupe.setZValue(10)
    return groupe
