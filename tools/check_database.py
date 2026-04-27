#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script minimal pour ajouter rapidement les colonnes
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect, text
from database.db import SQLALCHEMY_DATABASE_URL


def main():
    print("Ajout des colonnes à la table company_info...")
    
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    # Vérifier les colonnes existantes
    existing = [col['name'] for col in inspector.get_columns('company_info')]
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Ajouter nom_directeur
            if 'nom_directeur' not in existing:
                conn.execute(text("ALTER TABLE company_info ADD COLUMN nom_directeur VARCHAR(100)"))
                print("✓ Colonne 'nom_directeur' ajoutée")
            
            # Ajouter fonction_directeur
            if 'fonction_directeur' not in existing:
                conn.execute(text("ALTER TABLE company_info ADD COLUMN fonction_directeur VARCHAR(50)"))
                print("✓ Colonne 'fonction_directeur' ajoutée")
            
            # Ajouter numero_employeur (si pas déjà présent)
            if 'numero_employeur' not in existing:
                conn.execute(text("ALTER TABLE company_info ADD COLUMN numero_employeur VARCHAR(50)"))
                print("✓ Colonne 'numero_employeur' ajoutée")
            
            trans.commit()
            print("\n✅ Toutes les colonnes ont été ajoutées avec succès!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Erreur: {e}")
            return False
    
    return True


if __name__ == "__main__":
    main()
