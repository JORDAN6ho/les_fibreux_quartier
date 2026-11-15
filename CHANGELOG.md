# Historique des versions

## Non publiée (15/11/2026)

- Correctif : une ambulance prioritaire ne reste plus bloquée au rouge après un recalcul d'itinéraire.
  Quand elle arrive par l'autre axe d'un carrefour qu'elle avait déjà réservé, la réservation est refaite
  sur le bon axe (`Quartier.forcer`). Test de non-régression ajouté dans `tests/test_feux.py`.

## 1.1 (31/10/2026)

- Dépôt de test du déploiement devenu le dépôt principal du projet.
- Serveur plus robuste : gravité non numérique, message JSON qui n'est pas un objet, port déjà utilisé ou
  invalide donnent un message clair au lieu d'arrêter le serveur ou le client.
- Client : une ligne illisible reçue du serveur est ignorée ; version affichée dans le titre.
- Console du serveur : nombre de clients, urgences demandées, commandes refusées.
- `stats.db` fermé proprement au Ctrl+C ; outil `python3 -m outils.trajets` pour relire les trajets.
- `install.sh` : vérification d'apt-get et rappel de la commande suivante.
- Tests : protocole, configuration, base, carte, feux, commandes, message d'état, outil ;
  `python3 -m tests` lance tout ; tests automatiques sur GitHub (Python 3.10 à 3.12).

## 1.0 (21/10/2026)

- Version commentée du quartier connecté, déployée sur les deux VM de l'IUT.
- Auto-recette : passe 1 avec 5 écarts corrigés, passe 2 sans écart (lignes 1 à 14 conformes).
