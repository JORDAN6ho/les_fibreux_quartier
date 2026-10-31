# Guide de recette pas à pas : deux VM vierges, uniquement avec le README

*Les Fibreux (Jordan HO, Younès BACH). Ce guide sert à remplir la colonne « Observé » d'`AUTO_RECETTE.md`.*

**Objectif :** partir de deux machines Linux qui viennent d'être installées, et arriver à une ambulance qui
roule sur le client en **moins de 15 minutes**, en ne suivant **que le README** du dépôt. Tout ce qu'il a fallu
faire en dehors du README est un écart : on le note, puis on corrige le README.

---

## 0. Avant de lancer le chrono (non compté dans les 15 minutes)

### 0.1 Le dépôt

- Le dépôt principal est https://github.com/JORDAN6ho/les_fibreux_quartier. Il contient directement
  `serveur.py`, `client.py`, `install.sh`, etc. à sa racine (pas de dossier `les_fibreux_quartier/` en double).
- La ligne `git clone` du README pointe bien vers cette URL.
- Le dépôt est **public**, ou bien vous avez un jeton d'accès sous la main (`git clone` demandera un identifiant).
- Pas de `venv/` ni de `stats.db` dans le dépôt (le `.gitignore` les exclut déjà).

### 0.2 Les deux VM

| | VM 1 : serveur | VM 2 : client |
| --- | --- | --- |
| Système | Ubuntu 22.04 ou Debian 12 (le bureau n'est pas obligatoire) | Ubuntu 22.04 ou Debian 12 **avec bureau graphique** |
| Mémoire | 2 Go | 4 Go |
| Disque | 15 Go | 25 Go |

1. Installer le système sur les deux VM, sans rien ajouter d'autre (pas de git, pas de Python en plus).
2. **Réseau : les deux VM doivent se voir.** Dans VirtualBox, le mode « NAT » par défaut ne marche pas (les deux
   VM ont la même adresse 10.0.2.15 et ne se voient pas). Choisir, pour les deux VM :
   - « Réseau NAT » (même réseau NAT pour les deux, créé dans *Fichier > Outils > Gestionnaire de réseau*), ou
   - « Accès par pont » (les VM prennent une adresse sur le réseau de la salle).
   Avec VMware : « NAT » ou « Bridged » sur les deux, c'est bon dans les deux cas.
3. Vérifier que l'utilisateur peut faire `sudo` : `sudo true` ne doit pas répondre « n'est pas dans le fichier
   sudoers ». Sur Debian 12, si un mot de passe root a été donné à l'installation, l'utilisateur n'a pas `sudo` :
   `su -`, puis `usermod -aG sudo <utilisateur>`, puis se déconnecter et se reconnecter.
4. Vérifier qu'Internet marche dans chaque VM (`ping -c 2 deb.debian.org`).
5. Sur Ubuntu, au premier démarrage, les mises à jour automatiques bloquent `apt` pendant quelques minutes
   (« Could not get lock »). Attendre qu'elles finissent avant de lancer le chrono.
6. **Prendre un instantané (snapshot) de chaque VM et l'appeler « vierge ».** C'est lui qui permet de refaire
   la recette depuis zéro autant de fois que nécessaire, et de la refaire en soutenance si besoin.

### 0.3 Préparer la feuille

Ouvrir `AUTO_RECETTE.md` (sur votre PC, pas dans les VM). Pour chaque ligne, la colonne « Observé » recevra :

- `OK (hh:mm)` si le résultat est celui attendu, avec l'heure ;
- sinon le **message exact** affiché, ce qui a été fait pour s'en sortir, et l'heure. Exemple :
  `KO 14:07 : « bash: git: command not found », installé à la main avec apt` ;
- `Non fait` avec la raison si l'étape n'a pas pu être jouée.

Noter l'heure de départ en haut du fichier : `Recette du jj/mm, début hh:mm, VM Ubuntu 22.04 / Debian 12`.

---

## 1. Le chrono démarre : installation (cible : 10 minutes)

On ouvre le README du dépôt **dans un navigateur sur le PC hôte** (page GitHub), et on tape les commandes dans
un terminal de chaque VM. Les deux VM peuvent être installées en même temps.

| Temps | Où | Ce qu'on fait (section du README) | Ligne d'AUTO_RECETTE |
| --- | --- | --- | --- |
| 0:00 | VM 1 | `hostname -I`, noter la première adresse (par exemple 10.0.2.4 ou 192.168.1.42) | 1 |
| 0:01 | VM 1 et 2 | *Installation* : installer git, `git clone ... les_fibreux_quartier`, `cd les_fibreux_quartier`, `ls` | 2 |
| 0:03 | VM 1 | `bash install.sh serveur` (mot de passe sudo demandé) | 3 |
| 0:03 | VM 2 | `bash install.sh client`. C'est l'étape la plus longue : PyQt6 fait environ 80 Mo à télécharger | 4 |

Points à surveiller et à noter :

- Le script se termine bien par « Installation terminée pour le rôle : ... ». S'il s'arrête avant, `set -e` a
  coupé sur une erreur : copier les dernières lignes dans « Observé ».
- Sur la VM 2, `./venv/bin/pip list` doit montrer `PyQt6 6.7.1`, `PyQt6-Qt6 6.7.3`, `PyQt6_sip 13.13.0`.
- Noter la durée de `install.sh client` : si elle dépasse 6 ou 7 minutes, la marge de 15 minutes est fragile
  (réseau de la salle lent). Le dire dans le bilan.

## 2. Configuration et lancement (cible : 3 minutes)

| Temps | Où | Ce qu'on fait (section du README) | Ligne |
| --- | --- | --- | --- |
| ~0:10 | VM 1 | *Lancement* : `python3 serveur.py` | 5 |
| ~0:11 | VM 2 | *Configuration réseau* : `nano config.ini`, mettre l'adresse de la VM 1 dans `hote_client`, enregistrer (Ctrl+O, Entrée, Ctrl+X) | 6 |
| ~0:12 | VM 2 | `./venv/bin/python client.py`, **dans un terminal du bureau graphique** (pas en SSH) | 7 |
| ~0:12 | VM 1 | Lire la console du serveur | 8 |

- Si le client affiche « Connexion impossible » : vérifier l'adresse dans `config.ini`, puis depuis la VM 2
  `ping <adresse VM 1>`. Si le ping échoue, c'est le réseau des VM (voir 0.2), pas le programme. Si le ping
  passe mais pas la connexion, essayer `sudo ufw allow 5050/tcp` sur la VM 1 (comme dans le README).
- Si le client s'arrête avec une erreur Qt (« xcb » ou « wayland ») : relancer `bash install.sh client`, puis
  essayer `QT_QPA_PLATFORM=xcb ./venv/bin/python client.py`. Noter le message exact : c'est un écart à corriger
  dans le README si la deuxième commande a été nécessaire.

**Arrêter le chrono ici** dès que la fenêtre affiche « Connecté à ... » et que des voitures roulent. Noter
l'heure : c'est **le temps de déploiement** à annoncer (objectif : moins de 15 minutes).

## 3. Vérifications fonctionnelles (hors chrono, environ 10 minutes)

Toujours en suivant le README, section *Utilisation du client*.

| Ligne | Ce qu'on fait | Ce qu'on regarde |
| --- | --- | --- |
| 9 | Départ E3, arrivée E4, « Lancer l'ambulance » | Tracé bleu par la route directe, bandeau rouge « Il faut se serrer à droite ! » |
| 10 | Cliquer deux fois sur la route Q3-Q4 (elle devient rouge), relancer E3 vers E4 | Le tracé passe par le contournement bas |
| 11 | Sans toucher à Q3-Q4, décocher « Avec priorité », relancer E3 vers E4 | Trajet plus long ; les deux durées apparaissent dans les statistiques |
| 11b | Q3-Q4 toujours bloquée, regarder les voitures venant de E3 ou E4 | Elles prennent le contournement bas ; recliquer pour rendre la route fluide |
| 11c | Lancer une ambulance, puis « Arrêter l'urgence » | Ambulance et bandeau disparaissent, feux de nouveau en cycle normal |
| 12 | Ctrl+C sur la VM 1, puis relancer `python3 serveur.py` | Le client affiche « Connexion perdue ». **Le client ne se reconnecte pas tout seul** : le fermer et le relancer |
| 13 | VM 2, dans le dossier : `python3 -m tests.test_simulation` puis `python3 -m tests.test_reseau` | Fin sans erreur (quelques secondes) |
| 14 | VM 1, dans le dossier : la commande `python3 -c "import sqlite3; ..."` de la ligne 14 | Les trajets d'ambulance des lignes 9 à 11 sont listés |

## 4. Après la recette

1. Noter l'heure de fin et le **temps de déploiement** (fin de l'étape 2) en haut d'`AUTO_RECETTE.md`.
2. Pour chaque écart noté, corriger le README (ou `install.sh`) dans un commit séparé, avec un message qui dit
   ce qui a été corrigé (« README : ajout de l'installation de git »). Ces commits comptent dans les 50.
3. Revenir à l'instantané « vierge » des deux VM et **refaire la recette complète** jusqu'à zéro écart.
   Garder dans `AUTO_RECETTE.md` le tableau de la dernière passe, et mentionner les passes précédentes
   et leurs écarts dans le Bilan_Projet.pdf.
4. Idéalement, faire jouer une passe par un autre groupe, avec seulement l'URL du dépôt : c'est ce que fera
   le professeur.

## Aide-mémoire des pièges connus

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| `git: command not found` | git absent d'une installation vierge | `sudo apt-get install -y git` (première ligne du README) |
| `Could not get lock /var/lib/dpkg/lock-frontend` | mises à jour automatiques d'Ubuntu en cours | attendre puis relancer |
| `... n'est pas dans le fichier sudoers` | Debian avec mot de passe root | voir 0.2, point 3 |
| `cd: les_fibreux_quartier: Aucun fichier ou dossier` | `git clone` lancé sans le dernier argument | relancer la commande exacte du README |
| « Connexion impossible » | mauvaise adresse, VM en mode NAT simple, pare-feu | voir section 2 |
| Erreur Qt « xcb » ou « wayland » | bibliothèques graphiques ou session | voir section 2 |
| `Address already in use` au lancement du serveur | un ancien serveur tourne encore | `pkill -f serveur.py` puis relancer |
