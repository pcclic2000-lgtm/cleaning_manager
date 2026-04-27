# app.py — REDIRECTEUR (déprécié)
"""
Ce fichier existait en doublon de main.py.
Il est conservé pour compatibilité mais délègue entièrement à main.py.

Point d'entrée officiel : main.py
"""
from main import main
import sys

if __name__ == "__main__":
    sys.exit(main())
