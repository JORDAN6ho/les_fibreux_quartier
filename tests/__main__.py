"""Lance tous les tests d'un coup : python3 -m tests (depuis la racine du dépôt)."""
import time

from tests import test_base, test_config, test_protocole, test_reseau, test_simulation

for module in (test_protocole, test_config, test_base, test_reseau, test_simulation):
    debut = time.time()
    print(f"--- {module.__name__}")
    module.main()
    print(f"    ({time.time() - debut:.1f} s)")
print("Tous les tests sont passés.")
