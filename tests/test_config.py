"""Tests de la lecture de la configuration réseau (arguments, config.ini, environnement).

Lancer depuis la racine : python -m tests.test_config
"""
import os
import sys
import tempfile

from quartier.config import lire_reseau


def lire(arguments, contenu_ini, environnement=None):
    """Appelle lire_reseau comme si le client était lancé avec ces arguments et ce config.ini."""
    with tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False) as ini:
        ini.write(contenu_ini)
    ancien_argv, ancien_env = sys.argv, dict(os.environ)
    try:
        sys.argv = ["client.py", "--config", ini.name, *arguments]
        os.environ.pop("CARREFOUR_HOTE", None)
        os.environ.pop("CARREFOUR_PORT", None)
        os.environ.update(environnement or {})
        hote, port, _ = lire_reseau("client", "test")
        return hote, port
    finally:
        sys.argv = ancien_argv
        os.environ.clear()
        os.environ.update(ancien_env)
        os.remove(ini.name)


def main():
    """Vérifie l'ordre de priorité : arguments, puis config.ini, puis variables d'environnement."""
    ini = "[reseau]\nhote_serveur = 0.0.0.0\nhote_client = 10.0.2.3\nport = 5050\n"
    assert lire([], ini) == ("10.0.2.3", 5050)
    assert lire(["--hote", "192.168.1.42", "--port", "6000"], ini) == ("192.168.1.42", 6000)
    assert lire([], ini, {"CARREFOUR_HOTE": "1.2.3.4"}) == ("10.0.2.3", 5050), "config.ini passe avant l'environnement"
    assert lire([], "[reseau]\n", {"CARREFOUR_HOTE": "1.2.3.4", "CARREFOUR_PORT": "7000"}) == ("1.2.3.4", 7000)
    for mauvais in ("abc", "0", "70000"):
        try:
            lire(["--hote", "10.0.2.3"], f"[reseau]\nport = {mauvais}\n")
        except SystemExit:
            pass
        else:
            raise AssertionError(f"le port {mauvais} aurait dû être refusé")
    print("OK : configuration (arguments, puis config.ini, puis environnement)")


if __name__ == "__main__":
    main()
