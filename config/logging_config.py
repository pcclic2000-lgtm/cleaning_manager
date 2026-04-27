"""
config/logging_config.py
========================
Configuration du système de logging avec rotation de fichiers.
Usage : appeler setup_logging() une seule fois au démarrage dans app.py.
"""
import logging
import logging.handlers
import sys
from config.settings import LOG_FILE, LOG_LEVEL, LOG_MAX_BYTES, LOG_BACKUP_COUNT

_FMT_CONSOLE = "%(levelname)-8s %(name)s — %(message)s"
_FMT_FILE    = "%(asctime)s  %(levelname)-8s  %(name)s  [%(filename)s:%(lineno)d]  %(message)s"
_DATE_FMT    = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    """
    Configure deux handlers :
      - Console  : WARNING+ en couleur (pas de spam au démarrage)
      - Fichier  : DEBUG+ avec rotation automatique (5 Mo × 3 fichiers)

    Appeler une seule fois au lancement de app.py.
    """
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)

    # Éviter les doublons si appelé plusieurs fois (tests, rechargement)
    if root.handlers:
        return

    # Handler console — WARNING et plus uniquement
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.WARNING)
    console.setFormatter(logging.Formatter(_FMT_CONSOLE))
    root.addHandler(console)

    # Handler fichier avec rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(logging.Formatter(_FMT_FILE, datefmt=_DATE_FMT))
        root.addHandler(file_handler)
    except OSError as e:
        # Si le fichier de log n'est pas accessible, on continue sans planter
        logging.warning("Impossible de créer le fichier de log : %s", e)
