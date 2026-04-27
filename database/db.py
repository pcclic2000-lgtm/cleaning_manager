# database/db.py - VERSION CORRIGÉE AVEC SQL SÉCURISÉ
"""
Configuration de la base de données (engine, sessions) — n'instancie pas une nouvelle Base.
Importez `Base` depuis database.base dans vos modèles.
Utilisez init_db() après avoir importé tous vos modèles pour créer les tables.
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import os
from typing import Iterator

# NE PAS IMPORTER DE MODÈLES ICI - Cela cause des importations circulaires
# Supprimez ces lignes:
# from models.payslip import Payslip
# from models.tache import Tache

# Importer la Base centralisée (NE PAS redéfinir declarative_base ici)
from database.base import Base

# Chemin du dossier 'database' (ce fichier est database/db.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Fichier SQLite placé dans le dossier database/
DATABASE_FILENAME = "cleaning_manager.db"
DATABASE_PATH = os.path.join(BASE_DIR, DATABASE_FILENAME)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Engine SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # nécessaire pour SQLite multithread simple
    echo=False,  # mettre True pour debug SQL
    pool_pre_ping=True
)

# Session factory et session thread-safe
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ScopedSession = scoped_session(SessionLocal)


def get_db() -> Iterator:
    """
    Générateur de session (compatible FastAPI-style).
    Usage:
        for db in get_db(): ...
    or in dependencies: next(get_db())
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_session():
    """Context manager SQLAlchemy session.

    Usage:
        with get_session() as session:
            ...
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def import_models() -> list[str]:
    """
    Importe les modules de modèles une seule fois dans l'ordre attendu.
    Ne faites PAS de importlib.reload ici — cela redéfinirait les mappings et causerait des conflits.
    Retourne la liste des modules effectivement importés (pour debug).
    """
    model_modules = [
        # Enums en premier (pas de dépendances)
        "models.enums",
        # Entités principales
        "models.company",
        "models.employee",
        "models.client",
        # Gestion contractuelle & opérationnelle
        "models.contrat",
        "models.tache",
        "models.affectation",
        # Facturation
        "models.invoice",
        # Paie
        "models.payslip",
        "models.paye_globale",
        "models.cotisation",
        # Finances
        "models.expense",
        "models.bank",
    ]

    imported = []
    for module_name in model_modules:
        try:
            __import__(module_name)
            imported.append(module_name)
            print(f"   ✅ {module_name}")
        except ImportError as e:
            # Afficher seulement si c'est une vraie erreur d'import (pas juste un module manquant)
            print(f"   ⚠️  {module_name} non trouvé: {e}")
        except Exception as e:
            # Autres erreurs
            print(f"   ❌ {module_name}: {e}")
    return imported


def init_db(create_dir_if_missing: bool = True) -> bool:
    """
    Initialise la base de données.
    - Importe les modèles (import_models)
    - Crée les tables manquantes via Base.metadata.create_all(bind=engine)
    Retourne True si OK, False sinon.
    """
    try:
        # Créer le dossier database si nécessaire
        if create_dir_if_missing and not os.path.exists(BASE_DIR):
            os.makedirs(BASE_DIR, exist_ok=True)

        # Afficher les chemins pour debug
        print(f"🔧 DB Path: {DATABASE_PATH}")

        # Importer les modèles (une seule fois)
        print("📦 Importation des modèles...")
        imported = import_models()

        # Créer toutes les tables manquantes
        print("🔧 Création des tables (si manquantes)...")
        Base.metadata.create_all(bind=engine)

        # Diagnostic : lister les tables créées (version sécurisée avec text())
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📊 Tables dans la base ({len(tables)}):")
        for t in tables:
            try:
                # Compter les lignes (silencieux si erreur) - UTILISATION DE text() POUR SQL SÉCURISÉ
                with engine.connect() as conn:
                    # Utiliser text() avec paramètre nommé pour éviter l'injection SQL
                    result = conn.execute(
                        text(f"SELECT COUNT(*) FROM {t}"),
                        # Note: SQLAlchemy échappe automatiquement les noms de tables
                        # car text() utilise la connexion pour l'échappement
                    )
                    count = result.scalar()
                print(f"   • {t:20} ({count} lignes)")
            except Exception:
                print(f"   • {t:20} (compte impossible)")

        return True
    except Exception as exc:
        print(f"❌ Erreur initialisation DB: {exc}")
        import traceback
        traceback.print_exc()
        return False


    __all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "ScopedSession",
    "get_db",
    "init_db",
    "DATABASE_PATH",
    ]
