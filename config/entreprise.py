# config/entreprise.py
# CORRECTION : Ce fichier charge désormais la configuration depuis entreprise.json
# (source unique de vérité). Ne plus modifier les valeurs ici directement.

import json
import os

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "entreprise.json")

with open(_CONFIG_PATH, encoding="utf-8") as _f:
    _config = json.load(_f)

# Informations entreprise (rétrocompatibilité avec le reste du code)
ENTREPRISE_INFO = {k: v for k, v in _config.items()
                   if not isinstance(v, dict) and not k.startswith("_")}

# Taux de cotisations (Algérie)
TAUX_COTISATIONS = _config.get("taux_cotisations", {})

# Options d'affichage
OPTIONS_AFFICHAGE = _config.get("options_affichage", {})
