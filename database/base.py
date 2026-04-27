# database/base.py
"""
Définition unique de la Base déclarative pour SQLAlchemy.
Tous les modèles doivent importer Base depuis ce fichier :
    from database.base import Base
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()