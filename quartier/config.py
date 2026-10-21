"""Lecture de la configuration réseau : arguments, config.ini, variables d'environnement."""
import argparse
import configparser
import os


def lire_reseau(role, description):
    """Retourne (hôte, port, fichier de config). Priorité : arguments, config.ini, environnement."""
    analyseur = argparse.ArgumentParser(description=description)
    analyseur.add_argument("--hote", help="adresse IP ou nom de machine")
    analyseur.add_argument("--port", type=int, help="port TCP")
    analyseur.add_argument("--config", default="config.ini", help="fichier de configuration")
    args = analyseur.parse_args()
    fichier = configparser.ConfigParser()
    fichier.read(args.config)
    # Le serveur lit son adresse d'écoute, le client l'adresse du serveur
    cle = "hote_serveur" if role == "serveur" else "hote_client"
    # Ordre de priorité : ligne de commande, puis config.ini, puis variables d'environnement
    hote = args.hote or fichier.get("reseau", cle, fallback=None) or os.environ.get("CARREFOUR_HOTE")
    port = args.port or fichier.get("reseau", "port", fallback=None) or os.environ.get("CARREFOUR_PORT")
    if not hote or not port:
        analyseur.error("adresse ou port introuvables : utiliser --hote et --port, config.ini "
                        "ou les variables CARREFOUR_HOTE et CARREFOUR_PORT")
    return hote, int(port), fichier
