"""Affiche les trajets d'ambulance enregistrés dans stats.db, et la comparaison avec et sans priorité.

Lancer depuis la racine, sur la machine du serveur : python3 -m outils.trajets [chemin de la base]
"""
import json
import os
import sys

from quartier.base import Base


def afficher(chemin):
    """Affiche un tableau des trajets puis les moyennes ; retourne le nombre de trajets."""
    base = Base(chemin)
    trajets = base.lister_trajets()
    print(f"{'date':19}  {'trajet':9}  {'grav.':5}  {'priorité':8}  {'durée':>7}  itinéraire")
    for t in trajets:
        routes = "-".join(rid for rid, _ in json.loads(t["itineraire"]))
        print(f"{t['date']:19}  {t['depart'] + ' > ' + t['arrivee']:9}  {t['gravite']:<5}  "
              f"{'oui' if t['prioritaire'] else 'non':8}  {t['duree_s']:6.1f}s  {routes}")
    for prio, (moyenne, nombre) in base.moyennes().items():
        texte = f"{moyenne:.1f} s" if moyenne is not None else "aucun trajet"
        print(f"Moyenne {'avec' if prio else 'sans'} priorité : {texte} ({nombre} trajet(s))")
    base.fermer()
    return len(trajets)


def main():
    """Lit le chemin de la base en argument (stats.db par défaut)."""
    chemin = sys.argv[1] if len(sys.argv) > 1 else "stats.db"
    if not os.path.exists(chemin):
        sys.exit(f"{chemin} introuvable : lancer le serveur et terminer au moins un trajet d'ambulance")
    afficher(chemin)


if __name__ == "__main__":
    main()
