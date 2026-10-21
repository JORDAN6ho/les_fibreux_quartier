# Auto-recette : déploiement sur deux machines vierges

Durée visée : 15 minutes. Deux machines virtuelles Linux (Ubuntu 22.04 ou Debian 12) sur le même réseau.
VM 1 = serveur, VM 2 = client (avec bureau graphique). Noter les écarts dans la colonne « Observé ».

## Passe 1 : 21/10/2026, PC de l'IUT (Jordan HO, seul)

- **Hôte** : PC Windows de l'IUT, Oracle VirtualBox, sans droits administrateur. VM rangées dans `C:\Temp`.
- **VM** : images Debian 12 fournies par l'IUT (OVA), avec bureau graphique. VM 1 `Serveur_lesFibreux` en
  10.0.2.3, VM 2 `Client_lesFibreux` (4 Go de mémoire) en 10.0.2.4.
- **Réseau** : « Réseau NAT » VirtualBox nommé `NatNetwork`, DHCP activé, commun aux deux VM.
- **Dépôt utilisé** : https://github.com/JORDAN6ho/les_fibreux_quartier (dépôt de test, version commentée).
- **Durée** : passe non chronométrée, faite en découvrant les VM et en corrigeant les écarts au fur et à mesure.
  Le temps de déploiement est à mesurer à la passe 2, en repartant de l'instantané « vierge ».
- **Lignes 8 à 14** : jouées après les lignes 1 à 7, toutes conformes.

### Écarts relevés

| | Écart | Cause | Correction |
| --- | --- | --- | --- |
| A | `sudo` : « toto is not in the sudoers file » sur les deux VM | Sur Debian, l'utilisateur créé n'a pas les droits sudo | `su -` puis `usermod -aG sudo toto`, déconnexion et reconnexion. Ajouté au README |
| B | Le menu de création du réseau NAT est introuvable dans VirtualBox ; avec le mode « NAT » simple, le client avait 10.0.2.15 et ne voyait pas le serveur | Interface VirtualBox réduite ; le mode « NAT » isole chaque VM | Réseau créé dans cmd : `VBoxManage natnetwork add --netname NatNetwork --network 10.0.2.0/24 --enable --dhcp on`, puis mode « Réseau NAT » sur les deux VM |
| C | Client : « Connexion impossible : [Errno 111] Connection refused », titre de la fenêtre en `127.0.0.1:5050` | `hote_client` de `config.ini` pas modifié ou pas enregistré | Mettre l'adresse de la VM 1 dans `hote_client`, enregistrer (Ctrl+O, Entrée, Ctrl+X dans nano). `--hote` marche aussi |
| D | `bash install.sh client` affiche « Usage : ... » | Argument mal tapé | Retaper exactement `bash install.sh client` |
| E | L'OVA « Serveur Debian 12 » ne fonctionnait pas | Non identifiée | Remplacée par une autre image Debian 12 de l'IUT |

## Passe 2 : 21/10/2026, même PC, depuis l'instantané « vierge »

- Les deux VM restaurées à l'instantané « vierge », puis déploiement en suivant uniquement le README
  (`git clone` du dépôt, `install.sh`, `config.ini`, lancement).
- **Résultat : les lignes 1 à 14 sont toutes conformes, sans aucun écart.**
- **Temps de déploiement** (du `git clone` au client « Connecté à ... ») : _à compléter_ min.

## Tableau de recette (passe 1)

| N° | Machine | Étape | Résultat attendu | Observé |
| --- | --- | --- | --- | --- |
| 1 | VM 1 | `hostname -I` | Une adresse IP s'affiche, à noter | OK : 10.0.2.3 (client : 10.0.2.4) |
| 2 | VM 1 et 2 | `sudo apt-get install -y git`, `git clone <url> les_fibreux_quartier` puis `cd les_fibreux_quartier` | Le dossier contient `serveur.py`, `client.py`, `config.ini`, `install.sh` | OK sur les deux VM, après avoir donné les droits sudo (voir écart A) |
| 3 | VM 1 | `bash install.sh serveur` | Message « Installation terminée pour le rôle : serveur » | OK |
| 4 | VM 2 | `bash install.sh client` | Message « Installation terminée pour le rôle : client » | 1er essai : message « Usage : ... » (argument mal tapé). 2e essai : OK |
| 5 | VM 1 | `python3 serveur.py` | « en écoute sur 0.0.0.0:5050 » | OK |
| 6 | VM 2 | Mettre l'adresse de la VM 1 dans `hote_client` de `config.ini` | Fichier enregistré | KO au 1er essai : fichier non modifié ou non enregistré, le client visait 127.0.0.1 (écart C). OK après correction |
| 7 | VM 2 | `./venv/bin/python client.py` | Fenêtre plein écran, statut « Connecté à ... », voitures qui roulent | 1er essai : fenêtre affichée mais « Connexion impossible : [Errno 111] Connection refused ». OK après l'étape 6 corrigée |
| 8 | VM 1 | Lire la console du serveur | « client connecté » avec l'adresse de la VM 2 | OK |
| 9 | VM 2 | Départ E3, arrivée E4, « Lancer l'ambulance » | Ambulance qui roule par la route directe, tracé bleu, bandeau rouge | OK |
| 10 | VM 2 | Cliquer deux fois sur la route Q3-Q4 (bloquée), relancer une ambulance E3 vers E4 | Le tracé passe par le contournement bas | OK |
| 11 | VM 2 | Décocher « Avec priorité », relancer E3 vers E4 | Trajet plus long ; les deux durées apparaissent dans les statistiques | OK |
| 11b | VM 2 | Laisser la route Q3-Q4 bloquée et observer les voitures arrivant de E3 ou E4 | Elles prennent le contournement bas au lieu d'attendre ; recliquer pour rendre la route fluide | OK |
| 11c | VM 2 | Lancer une ambulance, puis cliquer « Arrêter l'urgence » | L'ambulance disparaît, le bandeau rouge aussi, les feux reprennent leur cycle | OK |
| 12 | VM 1 et 2 | Ctrl+C sur le serveur ; le client affiche « Connexion perdue ». Relancer le serveur, fermer puis relancer le client | Redémarrage propre, le client se reconnecte | OK |
| 13 | VM 2 | `python3 -m tests.test_simulation` puis `python3 -m tests.test_reseau` (depuis le dossier) | Les tests se terminent sans erreur | OK |
| 14 | VM 1 | `python3 -c "import sqlite3; print(*sqlite3.connect('stats.db').execute('select * from trajet_ambulance'), sep=chr(10))"` | Les trajets d'ambulance sont listés | OK |

Problèmes fréquents : le client affiche « Connexion impossible » (mauvaise adresse, port 5050 bloqué par un
pare-feu) ; erreur Qt « xcb » au lancement du client (relancer `bash install.sh client`).
Redéploiement à zéro : supprimer le dossier, refaire les étapes 2 à 8.
