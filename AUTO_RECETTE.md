# Auto-recette : déploiement sur deux machines virtuelles

**Objectif :** lancer le projet sur deux VM vierges en **15 minutes**, en suivant les étapes dans l'ordre.

- **VM 1 = serveur** : elle simule le quartier.
- **VM 2 = client** : elle affiche la carte (bureau graphique obligatoire).
- **Matériel** : un PC Windows de l'IUT avec Oracle VirtualBox, et deux VM créées à partir de l'image
  **Debian 12 du Disque Commun** de l'IUT, rangées dans **`C:\Temp`**.

> Dans les commandes, `toto` est le nom de l'utilisateur de la VM et `10.0.2.4` l'adresse de la VM 1 :
> remplacez-les par les vôtres.

## Étape 0 : importer les deux VM (VirtualBox)

Ne pas installer Debian soi-même : prendre l'image **Debian 12 du Disque Commun**.

1. Dans VirtualBox : **Fichier → Importer un appareil virtuel**, puis choisir l'image Debian 12 du Disque Commun.
2. Dans les réglages de l'import :
   - **Nom** : `Serveur_lesFibreux` ;
   - **Dossier de base des machines** : **`C:\Temp`** ;
   - **Politique d'adresse MAC** : générer de nouvelles adresses MAC pour toutes les cartes réseau.
3. Refaire la même chose pour la deuxième VM, avec le nom `Client_lesFibreux`, toujours dans `C:\Temp`.

## Étape 1 : créer le réseau des deux VM (PC Windows)

Les deux VM doivent être sur le même réseau pour se parler.

1. Ouvrir **PowerShell**.
2. Aller dans le dossier de VirtualBox :

   ```powershell
   cd "C:\Program Files\Oracle\VirtualBox"
   ```

3. Créer le réseau :

   ```powershell
   .\VBoxManage.exe natnetwork add --netname NatNetwork --network 10.0.2.0/24 --enable --dhcp on
   ```

Si le message dit que `NatNetwork` existe déjà, c'est bon : passer à l'étape 2.

## Étape 2 : régler les deux VM (VirtualBox, VM éteintes)

Pour chaque VM, ouvrir **Configuration** :

- **Réseau** → Mode d'accès : **Réseau NAT** → Nom : **NatNetwork**.
  (Pas « NAT » tout court : avec « NAT », les VM ne se voient pas.)
- **Affichage** → Mémoire vidéo : **128 Mo** → cocher **Activer l'accélération 3D**.
  (Facultatif, pour un affichage plus fluide. Si l'écran reste noir, décocher l'accélération 3D.)
- **VM 2 seulement** : Système → Mémoire vive : **4096 Mo**.

## Étape 3 : démarrer les VM

Démarrer la VM 1 (serveur) et la VM 2 (client), puis se connecter avec son utilisateur.

## Étape 4 : donner les droits sudo (les deux VM, une seule fois)

Sur Debian, l'utilisateur n'a souvent pas le droit d'utiliser `sudo`. Dans un terminal :

```bash
su -
usermod -aG sudo toto
exit
```

Les droits sudo ne sont pris en compte qu'après une nouvelle connexion de `toto` :

- **Méthode normale : redémarrer la VM.**
- **Plus rapide, sans redémarrer :** taper `su - toto` (mot de passe de `toto`). Ce terminal a tout de suite les
  droits sudo : faire la suite de l'installation dedans.

```bash
su - toto
```

> **Vérifier :** l'invite du terminal doit afficher `toto@...$` et pas `root@...#`.
> Toutes les étapes suivantes se font en `toto`, **jamais en root**.
>
> **Sur la VM 2 avec `su - toto` :** ce terminal sert à installer, mais il n'a pas accès à l'affichage. Pour
> lancer le client (étape 9), ouvrir **un nouveau terminal** depuis le bureau.

## Étape 5 : installer le serveur (VM 1)

```bash
hostname -I
```

➡️ Noter l'adresse affichée (exemple : `10.0.2.4`). C'est l'adresse du serveur.

```bash
sudo apt update && sudo apt install git -y
git clone https://github.com/JORDAN6ho/les_fibreux_quartier.git
cd les_fibreux_quartier
bash install.sh serveur
```

✅ Le dernier message doit être : `Installation terminée pour le rôle : serveur`.

## Étape 6 : installer le client (VM 2)

```bash
hostname -I
```

✅ L'adresse doit être **différente** de celle de la VM 1. Si les deux VM ont `10.0.2.15`, refaire l'étape 2.

```bash
sudo apt update && sudo apt install git -y
git clone https://github.com/JORDAN6ho/les_fibreux_quartier.git
cd les_fibreux_quartier
bash install.sh client
```

✅ Le dernier message doit être : `Installation terminée pour le rôle : client`.

## Étape 7 : lancer le serveur (VM 1)

```bash
python3 serveur.py
```

✅ Le serveur affiche qu'il est en écoute sur `0.0.0.0:5050`.

⚠️ **Laisser ce terminal ouvert** : fermer le terminal arrête le serveur.

## Étape 8 : donner l'adresse du serveur au client (VM 2)

Depuis le dossier `les_fibreux_quartier` :

```bash
nano config.ini
```

Remplacer la ligne `hote_client = 127.0.0.1` par l'adresse notée à l'étape 5 :

```ini
hote_client = 10.0.2.4
```

Enregistrer et quitter : **Ctrl+O**, **Entrée**, **Ctrl+X**.

## Étape 9 : lancer le client (VM 2, en toto)

```bash
./venv/bin/python client.py
```

✅ La fenêtre du quartier s'ouvre, le statut indique « Connecté à 10.0.2.4:5050 » et les voitures roulent.

Autre possibilité, sans modifier `config.ini` : `./venv/bin/python client.py --hote 10.0.2.4`

**C'est lancé !** Pour arrêter : fermer la fenêtre du client, puis Ctrl+C sur le serveur.

## Ça ne marche pas ?

| Problème | Solution |
| --- | --- |
| `toto is not in the sudoers file` | Refaire l'étape 4, sans oublier de redémarrer la VM ou de taper `su - toto` |
| PowerShell : `VBoxManage` introuvable | Vérifier l'étape 1 : `cd` dans le dossier de VirtualBox et `.\` devant `VBoxManage.exe` |
| `could not connect to display` puis `Aborted` | Le client est lancé en root, ou dans le terminal du `su - toto` : ouvrir un nouveau terminal depuis le bureau, vérifier que l'invite est `toto@...$`, relancer |
| Client : « Connexion impossible » | Serveur pas lancé (étape 7), mauvaise adresse dans `config.ini` (étape 8), ou VM pas en « Réseau NAT » (étape 2) |
| Les deux VM ont l'adresse `10.0.2.15` | Elles sont en « NAT » simple : refaire l'étape 2 |
| Les deux VM ont la même adresse, mais pas `10.0.2.15` | Même adresse MAC (la même image importée deux fois) : réimporter la VM 2 en générant de nouvelles adresses MAC (étape 0) |
| `bash install.sh` affiche « Usage : ... » | Retaper exactement `bash install.sh serveur` ou `bash install.sh client` |
| Serveur : « impossible d'écouter » | Un ancien serveur tourne encore : `pkill -f serveur.py`, puis relancer |
| Erreur Qt « xcb » alors que l'invite est bien `toto@...$` | Relancer `bash install.sh client`, puis `QT_QPA_PLATFORM=xcb ./venv/bin/python client.py` |

## Vérification de fonctionnement

À faire une fois le client connecté. Noter le résultat dans la colonne « Observé ».

| N° | Machine | Action | Résultat attendu | Observé |
| --- | --- | --- | --- | --- |
| 1 | VM 1 | Lire le terminal du serveur | « client connecté » avec l'adresse de la VM 2 | |
| 2 | VM 2 | Départ E3, arrivée E4, bouton rouge « Lancer l'ambulance » | L'ambulance roule, tracé bleu, bandeau « Il faut se serrer à droite ! » | |
| 3 | VM 2 | Cliquer deux fois sur la route Q3-Q4 (bloquée), relancer une ambulance E3 → E4 | Le tracé passe par le contournement bas | |
| 4 | VM 2 | Laisser Q3-Q4 bloquée, observer les voitures | Elles prennent le contournement au lieu d'attendre | |
| 5 | VM 2 | Décocher « Avec priorité », relancer E3 → E4 | Trajet plus long ; les deux durées apparaissent dans les statistiques | |
| 6 | VM 2 | Lancer une ambulance, puis « Arrêter l'urgence » | L'ambulance et le bandeau disparaissent, les feux reprennent leur cycle | |
| 7 | VM 1 et 2 | Ctrl+C sur le serveur, puis le relancer ; fermer et relancer le client | Le client affiche « Connexion perdue », puis se reconnecte | |
| 8 | VM 2 | `python3 -m tests` depuis le dossier du projet | « Tous les tests sont passés » | |
| 9 | VM 1 | `python3 -m outils.trajets` | Les trajets d'ambulance s'affichent, avec la moyenne avec et sans priorité | |

## Historique des passes

### Passe 1 : 21/10/2026, PC de l'IUT (Jordan HO)

Images Debian 12 du Disque Commun de l'IUT, VM rangées dans `C:\Temp`, VirtualBox sans droits administrateur. Cinq écarts trouvés et corrigés :

| | Écart | Correction |
| --- | --- | --- |
| A | `sudo` refusé : « toto is not in the sudoers file » | `su -`, `usermod -aG sudo toto`, puis redémarrage de la VM ou `su - toto` (étape 4) |
| B | Menu de création du réseau NAT introuvable ; en « NAT » simple, les VM ne se voient pas | Réseau créé avec `VBoxManage natnetwork add` (étape 1), mode « Réseau NAT » (étape 2) |
| C | Client : « Connexion impossible », il visait `127.0.0.1` | `hote_client` modifié et enregistré dans `config.ini` (étape 8) |
| D | `bash install.sh client` affiche « Usage : ... » | Argument retapé exactement |
| E | Une image « Serveur Debian 12 » ne démarrait pas | Remplacée par l'image Debian 12 du Disque Commun |

### Passe 2 : 21/10/2026, même PC, depuis l'instantané « vierge » (Jordan HO)

Déploiement en suivant uniquement le README : **toutes les vérifications conformes, sans écart**, en
15 minutes au maximum (du `git clone` au client « Connecté à ... »).

### Passe 3 : 25/11/2026, PC de l'IUT (Younès BACH)

Déploiement en suivant les étapes ci-dessus. Un nouvel écart trouvé :

| | Écart | Correction |
| --- | --- | --- |
| F | Client : `qt.qpa.xcb: could not connect to display`, puis `Aborted` | Le client était lancé en root (resté connecté après `su -`) : `exit`, puis installation et lancement en utilisateur normal. Avertissement ajouté à l'étape 4 et dans « Ça ne marche pas ? » |
