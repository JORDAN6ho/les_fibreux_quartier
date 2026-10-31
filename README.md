# Quartier connecté - Les Fibreux

**Groupe :** Les Fibreux - **Étudiants :** Jordan HO, Younès BACH
**Projets :** SAÉ 3.02 (Développer des applications communicantes) / R3.09 (Programmation événementielle)

Ceci est le **dépôt principal** du projet : https://github.com/JORDAN6ho/les_fibreux_quartier. C'est lui qui
est cloné sur les machines de recette et qui sert de référence pour la soutenance. Le code y est commenté.

Simulation d'un quartier de 4 carrefours (Q1 à Q4) reliés par 6 routes, dont 2 routes de contournement
(haut et bas), avec 4 entrées/sorties (E1 à E4). Une ambulance prioritaire reçoit un itinéraire calculé avec les
bouchons du moment (Dijkstra), les carrefours qu'elle va traverser sont préparés à l'avance, et l'itinéraire
est recalculé si une route se bloque.

## Architecture

Deux programmes qui communiquent par sockets TCP (messages JSON, un par ligne) :

| Programme | Machine | Rôle | Dépendances |
| --- | --- | --- | --- |
| `serveur.py` | VM 1 | Simule le quartier, décide des itinéraires et des stratégies, diffuse l'état | Aucune (Python standard) |
| `client.py` | VM 2 | Affiche la carte (PyQt6), envoie les commandes | PyQt6 |

Messages : `commande` (client vers serveur : lancer ou arrêter une urgence, route dense ou bloquée, ajout de
voiture, trafic automatique), `etat` (avec l'itinéraire de chaque ambulance) (serveur vers client, 11 fois par seconde), `erreur` (commande refusée).

## Protocole

Un message JSON par ligne, encodé en UTF-8 (`quartier/protocole.py`). Exemples :

```json
{"type":"commande","nom":"urgence","depart":"E3","arrivee":"E4","gravite":2,"prioritaire":true}
{"type":"commande","nom":"route","route":"h34","etat":"bloquee"}
{"type":"commande","nom":"ajout"}
{"type":"commande","nom":"auto","valeur":false}
{"type":"commande","nom":"fin_urgence"}
{"type":"erreur","message":"gravité invalide (1 à 3)"}
```

Le message `etat` contient : `tick`, `usagers` (position et angle de chaque véhicule), `feux` (couleur par axe
pour Q1 à Q4), `routes` (état et nombre de véhicules par sens), `ambulances` (itinéraire), `strategies`,
`serrer`, `compteurs` et `stats`. Une ligne illisible ou une commande invalide reçoit un message `erreur`, sans
couper la connexion.

## Installation (environ 10 minutes par machine, Ubuntu 22.04 ou Debian 12)

Sur chaque machine, l'utilisateur doit pouvoir utiliser `sudo`. Si `sudo true` répond « n'est pas dans le
fichier sudoers » (cas fréquent sur Debian), le corriger une fois avec le mot de passe root, puis se déconnecter
et se reconnecter :

```bash
su -c "/usr/sbin/usermod -aG sudo $USER"
```

Puis, sur chaque machine :

```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/JORDAN6ho/les_fibreux_quartier.git les_fibreux_quartier
cd les_fibreux_quartier
bash install.sh serveur     # sur la VM 1
bash install.sh client      # sur la VM 2 (installe aussi les bibliothèques graphiques de Qt)
```

Le dernier argument de `git clone` fixe le nom du dossier : `cd les_fibreux_quartier` fonctionne quel que soit
le nom du dépôt. `serveur.py`, `client.py` et `install.sh` sont à la racine du dépôt (pas de second dossier
`les_fibreux_quartier` à l'intérieur).

`bash install.sh` fonctionne même si le fichier a perdu son droit d'exécution (dépôt poussé depuis Windows).

Le script installe les paquets système, crée l'environnement virtuel (`venv`) et, pour le client, installe
`requirements.txt` (versions exactes : PyQt6 6.7.1, PyQt6-Qt6 6.7.3, PyQt6-sip 13.13.0). Python 3.10 ou plus
est requis.

## Configuration réseau

Aucune adresse n'est écrite dans le code. Ordre de priorité : arguments, `config.ini`, variables d'environnement
(`CARREFOUR_HOTE`, `CARREFOUR_PORT`, utilisées seulement si `config.ini` ne donne pas la valeur).

1. Sur la VM 1, relever son adresse IP : `hostname -I`
2. Sur la VM 2, ouvrir `config.ini` et mettre cette adresse dans `hote_client` (le port par défaut est 5050).
3. Ou, sans modifier le fichier : `./venv/bin/python client.py --hote <adresse IP du serveur> --port 5050`.

Le serveur écoute sur `hote_serveur` (`0.0.0.0` : toutes les interfaces). Le port TCP doit être joignable
depuis la VM 2 (pare-feu éventuel : `sudo ufw allow 5050/tcp`).

## Lancement

```bash
python3 serveur.py                 # VM 1 (Ctrl+C pour arrêter)
./venv/bin/python client.py        # VM 2
```

Sur la VM 1, après `bash install.sh serveur`, `python3` suffit : le serveur n'utilise que la bibliothèque standard.

## Utilisation du client

- **Lancer l'ambulance** : choisir départ, arrivée et gravité (1 à 3), puis le bouton rouge. Décocher « Avec
  priorité » pour lancer une ambulance sans régulation et comparer les temps de trajet dans les statistiques.
- **Arrêter l'urgence** : retire les ambulances en cours ; les feux reviennent au cycle normal après une phase
  tout-rouge de sécurité.
- **Cliquer sur une route** : elle passe à dense (orange, vitesse réduite), puis bloquée (rouge), puis fluide.
  L'itinéraire de l'ambulance, tracé en bleu, s'adapte. Les voitures dont la route suivante est bloquée prennent
  le contournement.
- **Gravité** (1 légère, 2 sérieuse, 3 vitale) : plus elle est haute, plus l'ambulance prioritaire roule vite et
  plus tôt les carrefours sont préparés devant elle.
- **Étiquettes sous les carrefours** : « onde verte » (carrefour fluide) ou « dégagement » (carrefour chargé :
  tout au rouge, attente de la sortie des véhicules, puis passage).
- **Bandeau rouge** « Il faut se serrer à droite ! » tant qu'une ambulance prioritaire est en route.
- Ajout de voitures (limite de 24). Trafic automatique : coché, des voitures entrent seules (jusqu'à 14) ;
  décoché, plus aucune n'entre et le quartier se vide.
- Les trajets d'ambulance terminés sont enregistrés dans `stats.db` (sqlite3) sur le serveur. Pour les afficher,
  avec la moyenne avec et sans priorité : `python3 -m outils.trajets` (sur la VM 1, depuis le dossier).

## Tests

```bash
python3 -m tests                    # tous les tests d'un coup (quelques secondes)
python3 -m tests.test_simulation    # itinéraires, urgences, stabilité, priorité contre sans priorité
python3 -m tests.test_reseau        # échange client/serveur en TCP
python3 -m tests.test_protocole     # messages JSON (aller-retour, accents, ligne illisible)
python3 -m tests.test_config        # ordre de priorité de la configuration, port invalide
python3 -m tests.test_base          # enregistrement et relecture des trajets dans sqlite3
python3 -m tests.test_carte         # géométrie, graphe des routes, Dijkstra, trajets
python3 -m tests.test_feux          # cycle des feux, forçage pour l'ambulance, tout-rouge de sécurité
python3 -m tests.test_commandes     # commandes invalides refusées sans faire planter le serveur
python3 -m tests.test_etat          # contenu du message d'état et statistiques
python3 -m tests.test_outils        # outil d'affichage des trajets
```

À lancer depuis le dossier `les_fibreux_quartier`, sur l'une ou l'autre VM : les tests n'utilisent que la
bibliothèque standard, le venv n'est pas nécessaire. Ils tournent aussi automatiquement sur GitHub à chaque
push (onglet *Actions*, fichier `.github/workflows/tests.yml`).

Si le serveur refuse de démarrer avec « impossible d'écouter », un ancien serveur tourne encore :
`pkill -f serveur.py`, puis relancer.

## Structure

```
serveur.py, client.py       points d'entrée
config.ini, install.sh, requirements.txt
quartier/carte.py           graphe des routes, voies, Dijkstra, trajets
quartier/simulation.py      feux, véhicules, urgences, statistiques
quartier/serveur_reseau.py  serveur TCP et boucle de simulation
quartier/client_reseau.py   connexion du client (QThread)
quartier/dessin.py, ihm.py  carte et fenêtre PyQt6
quartier/protocole.py, config.py, base.py
outils/trajets.py           affichage des trajets enregistrés dans stats.db
AUTO_RECETTE.md             tableau de recette sur deux machines vierges (résultats des passes)
GUIDE_RECETTE.md            guide pas à pas pour rejouer la recette
tests/                      tests automatiques (bibliothèque standard), lancés par python3 -m tests
```

## Travailler sur le dépôt

- `main` contient toujours une version qui s'installe et passe la recette.
- Chaque évolution se fait sur une branche, puis arrive sur `main` par une pull request relue par l'autre membre.
- Avant de fusionner : `python3 -m tests` doit passer (GitHub le vérifie aussi sur chaque pull request).
- Messages de commit en français, qui disent ce qui change (« README : ajout de l'installation de git »).

## Fonctionnalités (voir le Bilan_Projet.pdf)

Faites : séparation serveur/client sur deux machines, quartier à 4 carrefours et 2 contournements, feux,
véhicules qui roulent à droite et respectent les feux, mesure du trafic par route, itinéraire pondéré par le
trafic, événements (route dense ou bloquée), priorité d'urgence anticipée, stratégie adaptative et recalcul,
statistiques, stockage sqlite3, comparaison avec et sans priorité, installation et auto-recette.

Non développées : piétons et passages piétons, arbitrage entre plusieurs urgences simultanées, ambulance en
client socket indépendant, vélos, mode jour et nuit, météo, historique rejouable, graphiques.
