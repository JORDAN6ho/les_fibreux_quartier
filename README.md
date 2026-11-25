# Quartier connecté - Les Fibreux

**Groupe :** Les Fibreux - **Étudiants :** Jordan HO, Younès BACH
**Projets :** SAÉ 3.02 (Développer des applications communicantes) / R3.09 (Programmation événementielle)

Ceci est le **dépôt principal** du projet : https://github.com/JORDAN6ho/les_fibreux_quartier. C'est lui qui
est cloné sur les machines de recette et qui sert de référence pour la soutenance. Le code y est commenté.

Simulation d'un quartier de 4 carrefours (Q1 à Q4) reliés par 6 routes, dont 2 routes de contournement
(haut et bas), avec 4 entrées/sorties (E1 à E4). Une ambulance prioritaire reçoit un itinéraire calculé avec les
bouchons du moment (Dijkstra), les carrefours qu'elle va traverser sont préparés à l'avance, et l'itinéraire
est recalculé si une route se bloque.

## Sommaire

1. [Livrables](#livrables)
2. [Démarrage rapide sur un seul poste](#démarrage-rapide-sur-un-seul-poste)
3. [Comment ça marche](#comment-ça-marche)
4. [Architecture](#architecture)
5. [Protocole](#protocole)
6. [Installation sur deux machines](#installation-sur-deux-machines)
7. [Configuration réseau](#configuration-réseau)
8. [Lancement](#lancement)
9. [Utilisation du client](#utilisation-du-client)
10. [Tests](#tests)
11. [Dépannage](#dépannage)
12. [Structure](#structure)
13. [Travailler sur le dépôt](#travailler-sur-le-dépôt)
14. [Fonctionnalités](#fonctionnalités-voir-le-bilan_projetpdf)

## Livrables

Tous les livrables demandés sont à la racine du dépôt :

| Fichier | Contenu |
| --- | --- |
| `README.md` | Ce document : présentation, installation, utilisation, tests, dépannage |
| `requirements.txt` | Bibliothèques du client avec leurs versions exactes (PyQt6) |
| `serveur.py`, `client.py`, `quartier/` | Le code, commenté, avec des docstrings |
| [`Bilan_Projet.pdf`](Bilan_Projet.pdf) | Bilan du projet : fonctionnalités faites ou non par rapport au cahier des charges (Must, Should, Could have), conclusions technique et organisationnelle, planning prévu et réalisé, heures relevées par semaine |
| [`IAGraphie.pdf`](IAGraphie.pdf) | Usage de l'IA dans le projet : ce qui a été fait par nous et par l'IA à chaque phase, demandes principales, regard critique, vérifications et réflexion éthique |

Documents complémentaires : [`CHANGELOG.md`](CHANGELOG.md) (historique des versions),
[`AUTO_RECETTE.md`](AUTO_RECETTE.md) (résultats de la recette sur deux machines vierges) et
[`GUIDE_RECETTE.md`](GUIDE_RECETTE.md) (guide pour rejouer cette recette).

## Démarrage rapide sur un seul poste

Pour essayer le projet sur une seule machine (Ubuntu, Debian ou WSL sous Windows), le serveur et le client
tournent côte à côte. `config.ini` pointe déjà sur `127.0.0.1` (la machine elle-même).

```bash
git clone https://github.com/JORDAN6ho/les_fibreux_quartier.git les_fibreux_quartier
cd les_fibreux_quartier
bash install.sh client             # une seule fois : crée le venv et installe PyQt6
```

Puis dans **deux terminaux**, dans cet ordre :

```bash
python3 serveur.py                 # terminal 1 : le serveur, à laisser tourner
./venv/bin/python client.py        # terminal 2 : la fenêtre du quartier
```

> **Toujours lancer le serveur en premier.** Sans serveur, le client affiche « Connexion impossible » et les
> boutons « Ajouter une voiture » et « Lancer l'ambulance » restent vides : leur texte (avec les compteurs)
> vient du serveur.

Sous WSL, la fenêtre s'affiche grâce à WSLg (Windows 11 ou Windows 10 à jour). Pour le déploiement réel sur deux
machines, voir [Installation sur deux machines](#installation-sur-deux-machines).

## Comment ça marche

### Le quartier

```
              ┌──────── contournement haut (c12) ────────┐
              │                                          │
  E1 ────────Q1──────────── route directe (h12) ─────────Q2──────── E2
              │                                          │
            (v13)                                      (v24)
              │                                          │
  E3 ────────Q3──────────── route directe (h34) ─────────Q4──────── E4
              │                                          │
              └──────── contournement bas (c34) ─────────┘
```

- **Q1 à Q4** : les 4 carrefours, chacun avec deux axes de feux (est-ouest et nord-sud).
- **E1 à E4** : les entrées et sorties ; chaque véhicule entre par l'une et sort par une autre.
- **Les contournements** relient les mêmes carrefours que les routes directes, mais sont plus longs
  (900 pixels contre 540) : ce sont des routes de secours.

### Les feux

Chaque carrefour suit un cycle : **5 s de vert, 3 s d'orange, 2 s de tout-rouge** sur un axe, puis la même
chose sur l'autre axe. Les deux axes ne sont jamais ouverts en même temps. Le tout-rouge laisse le temps au
carrefour de se vider.

### Le choix de l'itinéraire (Dijkstra)

Le quartier est un graphe : les carrefours et entrées sont les nœuds, les routes sont les arêtes. L'algorithme
de **Dijkstra** (`quartier/carte.py`) cherche le chemin dont le **coût total** est le plus faible. Le coût d'une
route n'est pas le même pour tout le monde :

| Véhicule | Coût d'une route | Conséquence |
| --- | --- | --- |
| Voiture | Sa longueur (à ±5 % près, pour répartir les voitures) ; infini si elle est **bloquée** | Une voiture ne prend un contournement que si la route directe est bloquée |
| Ambulance prioritaire | Longueur × **facteur de bouchon** (de 1 si la route est vide à 4 si elle est pleine), ×3 si la route est **dense** ; infini si elle est **bloquée** | L'ambulance évite les routes chargées, denses ou bloquées |

Exemple : la route directe Q1-Q2 mesure 540 pixels et le contournement haut 900. L'ambulance passe par le
contournement dès que la route directe coûte plus de 900 : si elle est marquée dense (540 × 3 = 1 620), ou si
environ 4 véhicules ou plus y circulent. C'est pourquoi **les contournements restent souvent vides** tant
qu'aucune route n'est rendue dense ou bloquée : c'est voulu, ils servent en cas de problème.

### La priorité de l'ambulance

1. **Préparation à l'avance** : les carrefours de l'itinéraire sont préparés 7, 9 ou 11 s avant l'arrivée de
   l'ambulance, selon la gravité (plus elle est grave, plus c'est tôt).
2. **Stratégie choisie pour chaque carrefour** (`Quartier.forcer` dans `quartier/simulation.py`) :
   - **onde verte** : moins de 3 véhicules devant l'ambulance, son axe passe au vert et elle traverse sans
     s'arrêter ;
   - **dégagement** : au moins 3 véhicules devant elle, le carrefour passe au tout-rouge pour se vider, puis
     l'axe de l'ambulance passe au vert quand elle est à moins de 4 s.
3. **Les voitures se serrent à droite** sur la route de l'ambulance (bandeau « Il faut se serrer à droite ! »).
4. **Recalcul d'itinéraire** environ une fois par seconde : l'ambulance change de chemin si le sien est bloqué ou
   si un autre est au moins 15 % moins cher. Si elle arrive alors par l'autre axe d'un carrefour déjà
   réservé, la réservation passe sur le nouvel axe (correctif du 15/11).
5. **Après le passage** : tout-rouge de sécurité de 2 s, puis le carrefour reprend son cycle normal.

## Architecture

Deux programmes qui communiquent par sockets TCP (messages JSON, un par ligne) :

| Programme | Machine | Rôle | Dépendances |
| --- | --- | --- | --- |
| `serveur.py` | VM 1 | Simule le quartier, décide des itinéraires et des stratégies, diffuse l'état | Aucune (Python standard) |
| `client.py` | VM 2 | Affiche la carte (PyQt6), envoie les commandes | PyQt6 |

Messages : `commande` (client vers serveur : lancer ou arrêter une urgence, route dense ou bloquée, ajout de
voiture, trafic automatique), `etat` (avec l'itinéraire de chaque ambulance) (serveur vers client, 11 fois par seconde), `erreur` (commande refusée).

```
   VM 2 : client.py                               VM 1 : serveur.py
 ┌───────────────────────┐   commande (JSON)   ┌──────────────────────────┐
 │ Fenêtre PyQt6         │ ──────────────────► │ Thread par client        │
 │   ▲ signal Qt         │                     │   └► Quartier.executer() │
 │ QThread ClientReseau  │ ◄────────────────── │ Boucle de simulation     │
 └───────────────────────┘   etat (JSON)       │   (33 pas par seconde)   │
                             11 fois/s         └──────────────────────────┘
```

**Threads du serveur** (`quartier/serveur_reseau.py`, `serveur.py`) :

- un thread qui **accepte** les nouvelles connexions ;
- un thread **par client**, qui lit ses commandes ligne par ligne ;
- la **boucle de simulation**, dans le thread principal : 33 pas par seconde, et l'état est envoyé à tous les
  clients un pas sur trois ;
- un `Lock` protège la simulation (une commande ne la modifie pas pendant un pas) et un autre la liste des
  clients ; un `Event` arrête proprement la boucle au Ctrl+C.

**Thread du client** (`quartier/client_reseau.py`) : la connexion tourne dans un `QThread` qui émet un
`pyqtSignal` à chaque message reçu. La fenêtre reçoit ce signal dans le thread de Qt : **aucun thread ne
modifie l'interface directement**, comme l'exige Qt.

## Protocole

Un message JSON par ligne, encodé en UTF-8 (`quartier/serveur_reseau.py`). Exemples :

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

## Installation sur deux machines

Il faut deux VM dans VirtualBox : **VM 1 = serveur**, **VM 2 = client** (avec bureau graphique). Compter
environ **15 minutes**. Remplacez `toto` par votre utilisateur et `10.0.2.4` par l'adresse de votre VM 1.

**0. Importer les deux VM** à partir de l'image **Debian 12 du Disque Commun** de l'IUT : dans VirtualBox,
**Fichier → Importer un appareil virtuel**, dossier de base des machines **`C:\Temp`**, et nouvelles adresses
MAC. Une fois pour `Serveur_lesFibreux`, une fois pour `Client_lesFibreux`.

**1. Créer le réseau des VM** : sur le PC Windows, dans PowerShell.

```powershell
cd "C:\Program Files\Oracle\VirtualBox"
.\VBoxManage.exe natnetwork add --netname NatNetwork --network 10.0.2.0/24 --enable --dhcp on
```

**2. Régler les deux VM** : VM éteintes, dans Configuration de chaque VM.

- **Réseau** : Réseau NAT, nom `NatNetwork` (pas « NAT » tout court).
- **Affichage** : mémoire vidéo 128 Mo, accélération 3D cochée, pour un affichage plus fluide.

**3. Démarrer les deux VM**, puis donner les droits sudo sur chacune (une seule fois) :

```bash
su -
usermod -aG sudo toto
exit
```

Puis **redémarrer la VM** pour que les droits sudo comptent, ou, plus rapide, taper `su - toto` et continuer
dans ce terminal (sur la VM 2, lancer ensuite le client dans un nouveau terminal ouvert depuis le bureau).
Ensuite, toujours travailler en `toto@...$`, **jamais en root**.

**4. VM 1 (serveur)**

```bash
hostname -I                                   # noter l'adresse, ex. 10.0.2.4
sudo apt update && sudo apt install git -y
git clone https://github.com/JORDAN6ho/les_fibreux_quartier.git
cd les_fibreux_quartier
bash install.sh serveur
```

**5. VM 2 (client)**

```bash
hostname -I                                   # doit être différente de la VM 1
sudo apt update && sudo apt install git -y
git clone https://github.com/JORDAN6ho/les_fibreux_quartier.git
cd les_fibreux_quartier
bash install.sh client
```

Chaque installation se termine par `Installation terminée pour le rôle : ...`.

## Configuration réseau

Sur la VM 2, mettre l'adresse de la VM 1 dans `config.ini` :

```bash
nano config.ini
```

```ini
hote_client = 10.0.2.4
```

Revérifier l'adresse avec `hostname -I` sur la VM 1, puis enregistrer le fichier et quitter l'éditeur. Le port
par défaut est 5050.

## Lancement

**Toujours le serveur d'abord, puis le client.**

```bash
python3 serveur.py                  # VM 1 : laisser le terminal ouvert (Ctrl+C pour arrêter)
./venv/bin/python client.py         # VM 2 : en utilisateur normal, pas en root
```

La fenêtre s'ouvre avec le statut « Connecté à 10.0.2.4:5050 ». Sans modifier `config.ini`, on peut aussi lancer
`./venv/bin/python client.py --hote 10.0.2.4`.

Le détail de chaque étape, les vérifications et les problèmes fréquents sont dans
[`AUTO_RECETTE.md`](AUTO_RECETTE.md).

## Utilisation du client

La fenêtre a deux parties : **la carte** à gauche (carrefours, feux, véhicules, itinéraire de l'ambulance en
bleu) et **le panneau de commande** à droite (état de la connexion, boutons, statistiques).

### Premier essai : un scénario en 4 étapes

1. **Observer le trafic normal** : laisser « Trafic automatique » coché quelques secondes. Les voitures entrent,
   respectent les feux et ressortent ; les contournements restent vides, car les routes directes sont plus
   courtes.
2. **Lancer une ambulance prioritaire** : départ E3, arrivée E4, gravité 2, « Avec priorité » coché, puis
   « Lancer l'ambulance ». Son itinéraire s'affiche en bleu, le bandeau rouge apparaît, les feux passent au
   vert devant elle. Noter « Trajet ambulance avec priorité » dans les statistiques (environ 11 s).
3. **Comparer sans priorité** : décocher « Avec priorité » et relancer le même trajet. L'ambulance s'arrête
   aux feux comme les autres : « Trajet ambulance sans priorité » est environ trois fois plus long.
4. **Bloquer une route** : cliquer deux fois sur la route directe Q3-Q4 (dense, puis bloquée), puis relancer
   une ambulance prioritaire E3 vers E4 : elle passe par le contournement du bas.

### Les commandes en détail

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
python3 -m tests.test_simulation    # itinéraires, recalcul, urgences, stabilité, priorité contre sans priorité
python3 -m tests.test_reseau        # échange client/serveur en TCP
python3 -m tests.test_protocole     # messages JSON (aller-retour, accents, ligne illisible)
python3 -m tests.test_config        # ordre de priorité de la configuration, port invalide
python3 -m tests.test_base          # enregistrement et relecture des trajets dans sqlite3
python3 -m tests.test_carte         # géométrie, graphe des routes, Dijkstra, trajets
python3 -m tests.test_feux          # cycle des feux, forçage, onde verte ou dégagement, changement d'axe, tout-rouge
python3 -m tests.test_commandes     # commandes invalides refusées sans faire planter le serveur
python3 -m tests.test_etat          # contenu du message d'état et statistiques
python3 -m tests.test_outils        # outil d'affichage des trajets
```

À lancer depuis le dossier `les_fibreux_quartier`, sur l'une ou l'autre VM : les tests n'utilisent que la
bibliothèque standard, le venv n'est pas nécessaire. Ils tournent aussi automatiquement sur GitHub à chaque
push (onglet *Actions*, fichier `.github/workflows/tests.yml`).

## Dépannage

| Symptôme | Solution |
| --- | --- |
| `... n'est pas dans le fichier sudoers` | `su -`, `usermod -aG sudo toto`, `exit`, puis redémarrer la VM ou taper `su - toto` |
| Client : « Connexion impossible » | Vérifier `hote_client` dans `config.ini`, puis `ping <adresse VM 1>` ; sous VirtualBox, mettre les deux VM en « Réseau NAT » commun |
| Serveur : « impossible d'écouter » | Un ancien serveur tourne encore : `pkill -f serveur.py`, puis relancer |
| Serveur : « port invalide » | Corriger `port` dans `config.ini` (nombre entre 1 et 65535) |
| Client : erreur Qt « xcb » | Relancer `bash install.sh client`, ou essayer `QT_QPA_PLATFORM=xcb ./venv/bin/python client.py` |
| `Could not get lock /var/lib/dpkg/lock-frontend` | Mises à jour automatiques d'Ubuntu en cours : attendre puis relancer |
| Client : boutons « Ajouter une voiture » et « Lancer l'ambulance » vides | Le serveur n'est pas lancé (voir le message « Connexion impossible » en haut du panneau) : lancer `python3 serveur.py` d'abord |
| WSL : avertissements `libEGL warning` ou `MESA ... ZINK` au lancement du client | Sans gravité : Qt ne trouve pas de pilote graphique et passe en rendu logiciel. Pour les éviter : `LIBGL_ALWAYS_SOFTWARE=1 ./venv/bin/python client.py` |
| WSL : la fenêtre ne s'ouvre pas | Mettre WSL à jour pour avoir WSLg : `wsl --update` puis `wsl --shutdown` dans PowerShell |

## Structure

```
serveur.py, client.py       points d'entrée
config.ini, install.sh, requirements.txt
quartier/carte.py           graphe des routes, voies, Dijkstra, trajets
quartier/simulation.py      feux, véhicules, urgences, statistiques
quartier/serveur_reseau.py  serveur TCP et boucle de simulation
quartier/client_reseau.py   connexion du client (QThread)
quartier/dessin.py, ihm.py  carte et fenêtre PyQt6
quartier/config.py, base.py
outils/trajets.py           affichage des trajets enregistrés dans stats.db
Bilan_Projet.pdf            bilan du projet (livrable)
IAGraphie.pdf               usage de l'IA dans le projet (livrable)
CHANGELOG.md                historique des versions
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

| Priorité (cahier des charges) | Faites | Non développées |
| --- | --- | --- |
| **Must have** (14 sur 14) | Séparation serveur/client sur deux machines, quartier à 4 carrefours et 2 contournements, feux, véhicules qui roulent à droite et respectent les feux, protocole JSON, client Qt avec signaux et slots, mesure du trafic par route, itinéraire pondéré par le trafic (Dijkstra), choix automatique du contournement, événements (route dense ou bloquée), priorité d'urgence anticipée, stratégie adaptative et recalcul, installation et auto-recette | — |
| **Should have** (3 sur 6) | Statistiques stockées en base (sqlite3), comparaison avec et sans priorité, panneau de commande (ajout avec limite, trafic automatique, arrêt de l'urgence) | Piétons et passages piétons, arbitrage entre plusieurs urgences simultanées, ambulance en client socket indépendant |
| **Could have** | — | Vélos, mode jour et nuit, météo, historique rejouable, graphiques |

Le détail (ce qui le prouve dans le code et les tests) est dans le [`Bilan_Projet.pdf`](Bilan_Projet.pdf).
