"""
config/settings.py
==================
Configuration centralisée de l'application.
Toutes les constantes applicatives passent par ici.
"""
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Chemins racine ─────────────────────────────────────────────────────────
ROOT_DIR    = Path(__file__).resolve().parent.parent
CONFIG_DIR  = ROOT_DIR / "config"
ASSETS_DIR  = ROOT_DIR / "assets"
LOGS_DIR    = ROOT_DIR / "logs"
DB_DIR      = ROOT_DIR / "database"

# Répertoires créés automatiquement au démarrage
RUNTIME_DIRS = [
    ROOT_DIR / "models",
    ROOT_DIR / "views",
    ASSETS_DIR,
    ROOT_DIR / "reports",
    ROOT_DIR / "exports",
    LOGS_DIR,
    DB_DIR,
]

# ── Base de données ────────────────────────────────────────────────────────
DB_PATH = DB_DIR / "cleaning_manager.db"
DB_URL  = f"sqlite:///{DB_PATH}"

# ── Logging ────────────────────────────────────────────────────────────────
LOG_FILE         = LOGS_DIR / "app.log"
LOG_LEVEL        = logging.DEBUG
LOG_MAX_BYTES    = 5 * 1024 * 1024   # 5 Mo par fichier
LOG_BACKUP_COUNT = 3                  # 3 fichiers de rotation

# ── Interface ──────────────────────────────────────────────────────────────
APP_MIN_WIDTH  = 1024
APP_MIN_HEIGHT = 768

# ── Config entreprise ──────────────────────────────────────────────────────
_ENTREPRISE_PATH = CONFIG_DIR / "entreprise.json"


def load_entreprise_config() -> dict[str, Any]:
    """
    Charge la configuration entreprise depuis entreprise.json.
    Lève une exception explicite si le fichier est absent ou corrompu,
    afin d'échouer tôt avec un message clair plutôt qu'une KeyError tardive.
    """
    if not _ENTREPRISE_PATH.exists():
        raise FileNotFoundError(
            f"Fichier de configuration introuvable : {_ENTREPRISE_PATH}\n"
            "Créez config/entreprise.json à partir du template entreprise.json.example."
        )
    try:
        with open(_ENTREPRISE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"config/entreprise.json est invalide (JSON malformé) : {exc}"
        ) from exc


# Chargement à l'import — échoue tôt et clairement
try:
    _cfg = load_entreprise_config()
except (FileNotFoundError, ValueError) as _e:
    logger.critical("Impossible de charger la configuration entreprise : %s", _e)
    _cfg = {}

ENTREPRISE_INFO: dict[str, Any]     = {k: v for k, v in _cfg.items()
                                    if not isinstance(v, dict) and not k.startswith("_")}
TAUX_COTISATIONS: dict[str, float]  = _cfg.get("taux_cotisations", {})
OPTIONS_AFFICHAGE: dict[str, Any]   = _cfg.get("options_affichage", {})
