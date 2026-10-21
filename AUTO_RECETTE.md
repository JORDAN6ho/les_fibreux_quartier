# Auto-recette : déploiement sur deux machines vierges

Durée visée : 15 minutes. Deux machines virtuelles Linux (Ubuntu 22.04 ou Debian 12) sur le même réseau.
VM 1 = serveur, VM 2 = client (avec bureau graphique). Noter les écarts dans la colonne « Observé ».

| N° | Machine | Étape | Résultat attendu | Observé |
| --- | --- | --- | --- | --- |
| 1 | VM 1 | `hostname -I` | Une adresse IP s'affiche, à noter | |
| 2 | VM 1 et 2 | `sudo apt-get install -y git`, `git clone <url> les_fibreux_quartier` puis `cd les_fibreux_quartier` | Le dossier contient `serveur.py`, `client.py`, `config.ini`, `install.sh` | |
| 3 | VM 1 | `bash install.sh serveur` | Message « Installation terminée pour le rôle : serveur » | |
| 4 | VM 2 | `bash install.sh client` | Message « Installation terminée pour le rôle : client » | |
| 5 | VM 1 | `python3 serveur.py` | « en écoute sur 0.0.0.0:5050 » | |
| 6 | VM 2 | Mettre l'adresse de la VM 1 dans `hote_client` de `config.ini` | Fichier enregistré | |
| 7 | VM 2 | `./venv/bin/python client.py` | Fenêtre plein écran, statut « Connecté à ... », voitures qui roulent | |
| 8 | VM 1 | Lire la console du serveur | « client connecté » avec l'adresse de la VM 2 | |
| 9 | VM 2 | Départ E3, arrivée E4, « Lancer l'ambulance » | Ambulance qui roule par la route directe, tracé bleu, bandeau rouge | |
| 10 | VM 2 | Cliquer deux fois sur la route Q3-Q4 (bloquée), relancer une ambulance E3 vers E4 | Le tracé passe par le contournement bas | |
| 11 | VM 2 | Décocher « Avec priorité », relancer E3 vers E4 | Trajet plus long ; les deux durées apparaissent dans les statistiques | |
| 11b | VM 2 | Laisser la route Q3-Q4 bloquée et observer les voitures arrivant de E3 ou E4 | Elles prennent le contournement bas au lieu d'attendre ; recliquer pour rendre la route fluide | |
| 11c | VM 2 | Lancer une ambulance, puis cliquer « Arrêter l'urgence » | L'ambulance disparaît, le bandeau rouge aussi, les feux reprennent leur cycle | |
| 12 | VM 1 et 2 | Ctrl+C sur le serveur ; le client affiche « Connexion perdue ». Relancer le serveur, fermer puis relancer le client | Redémarrage propre, le client se reconnecte | |
| 13 | VM 2 | `python3 -m tests.test_simulation` puis `python3 -m tests.test_reseau` (depuis le dossier) | Les tests se terminent sans erreur | |
| 14 | VM 1 | `python3 -c "import sqlite3; print(*sqlite3.connect('stats.db').execute('select * from trajet_ambulance'), sep=chr(10))"` | Les trajets d'ambulance sont listés | |

Problèmes fréquents : le client affiche « Connexion impossible » (mauvaise adresse, port 5050 bloqué par un
pare-feu) ; erreur Qt « xcb » au lancement du client (relancer `bash install.sh client`).
Redéploiement à zéro : supprimer le dossier, refaire les étapes 2 à 8.
