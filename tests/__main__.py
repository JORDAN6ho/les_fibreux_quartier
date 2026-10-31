"""Lance tous les tests d'un coup : python3 -m tests (depuis la racine du dépôt)."""
import time

from tests import (test_base, test_carte, test_commandes, test_config, test_etat, test_feux, test_outils,
                   test_protocole, test_reseau, test_simulation)

# Du plus rapide au plus long : une erreur simple apparaît tout de suite
MODULES = (test_protocole, test_config, test_base, test_outils, test_carte, test_feux, test_commandes, test_etat,
           test_reseau, test_simulation)

for module in MODULES:
    debut = time.time()
    print(f"--- {module.__name__}")
    module.main()
    print(f"    ({time.time() - debut:.1f} s)")
print("Tous les tests sont passés.")
