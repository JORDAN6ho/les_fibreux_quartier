#!/usr/bin/env bash
set -e
ROLE="${1:-}"
if [ "$ROLE" != "serveur" ] && [ "$ROLE" != "client" ]; then
    echo "Usage : bash install.sh serveur   ou   bash install.sh client"
    exit 1
fi
# Le script utilise apt-get : il faut Ubuntu ou Debian
if ! command -v apt-get > /dev/null; then
    echo "apt-get introuvable : ce script est prévu pour Ubuntu 22.04 ou Debian 12"
    exit 1
fi
if [ "$ROLE" = "client" ]; then
    PAQUETS="python3 python3-venv python3-pip libxcb-cursor0 libxkbcommon-x11-0 libegl1 libgl1 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xkb1"
else
    PAQUETS="python3 python3-venv"
fi
sudo apt-get update
sudo apt-get install -y $PAQUETS
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "Python 3.10 ou plus est requis (version actuelle : $(python3 --version))"
    exit 1
fi
python3 -m venv venv
if [ "$ROLE" = "client" ]; then
    ./venv/bin/pip install -r requirements.txt
fi
echo "Installation terminée pour le rôle : $ROLE"
# Rappel de la commande suivante, pour ne pas avoir à rouvrir le README
if [ "$ROLE" = "serveur" ]; then
    echo "Étape suivante : python3 serveur.py   (adresse à donner au client : $(hostname -I | cut -d' ' -f1))"
else
    echo "Étape suivante : mettre l'adresse du serveur dans hote_client de config.ini, puis ./venv/bin/python client.py"
fi
