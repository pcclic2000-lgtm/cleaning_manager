# scripts/update_contrat_table.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de mise à jour de la table contrat
Ajoute les colonnes pour:
- Type de document (Marché/Convention/Contrat)
- Informations Marché (numéro, date, autorité)
- Informations Convention (numéro, date, organisme)
- Informations ODS (numéro, date, objet, signataire, chemin fichier)
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect, text
from database.db import SQLALCHEMY_DATABASE_URL
from models.enums import TypeDocumentContrat


def check_column_exists(engine, table_name, column_name):
    """Vérifie si une colonne existe dans une table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_column_if_not_exists(engine, table_name, column_name, column_def):
    """Ajoute une colonne si elle n'existe pas"""
    if not check_column_exists(engine, table_name, column_name):
        print(f"➕ Ajout de la colonne '{column_name}'...")
        with engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_def}"))
            conn.commit()
        print(f"✅ Colonne '{column_name}' ajoutée avec succès!")
        return True
    else:
        print(f"⏭️ Colonne '{column_name}' existe déjà.")
        return False


def main():
    """Fonction principale de mise à jour"""
    print("=" * 70)
    print("🔧 MISE À JOUR DE LA TABLE CONTRAT")
    print("=" * 70)
    
    # Créer l'engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    table_name = "contrats"
    
    # Vérifier que la table existe
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        print(f"❌ La table '{table_name}' n'existe pas!")
        print("Veuillez d'abord créer la table contrat.")
        return
    
    print(f"\n📋 Analyse de la table '{table_name}'...")
    
    # ===== COLONNES POUR LE TYPE DE DOCUMENT =====
    print("\n--- Type de document ---")
    add_column_if_not_exists(
        engine, table_name, 
        "type_document", 
        "VARCHAR(50)"
    )
    
    # ===== COLONNES POUR MARCHÉ PUBLIC =====
    print("\n--- Informations Marché ---")
    add_column_if_not_exists(
        engine, table_name, 
        "numero_marche", 
        "VARCHAR(100)"
    )
    add_column_if_not_exists(
        engine, table_name, 
        "date_marche", 
        "DATE"
    )
    add_column_if_not_exists(
        engine, table_name, 
        "autorite_contractante", 
        "VARCHAR(200)"
    )
    
    # ===== COLONNES POUR CONVENTION =====
    print("\n--- Informations Convention ---")
    add_column_if_not_exists(
        engine, table_name, 
        "numero_convention", 
        "VARCHAR(100)"
    )
    add_column_if_not_exists(
        engine, table_name, 
        "date_convention", 
        "DATE"
    )
    add_column_if_not_exists(
        engine, table_name, 
        "organisme_convention", 
        "VARCHAR(200)"
    )
    
    # ===== COLONNES POUR ODS =====
    print("\n--- Informations ODS ---")
    add_column_if_not_exists(
        engine, table_name, 
        "numero_ods", 
        "VARCHAR(100)"
    )
    add_column_if_not_exists(
        engine, table_name, 
        "date_ods", 
        "DATE"
    )
    add_column_if_not_exists(
        engine, table_name, 
        "objet_ods", 
        "TEXT"
    )
    add_column_if_not_exists(
        engine, table_name, 
        "signature_ods", 
        "VARCHAR(100)"
    )
    add_column_if_not_exists(
        engine, table_name, 
        "ods_path", 
        "VARCHAR(500)"
    )
    
    # ===== COLONNES POUR MONTANT GLOBAL =====
    print("\n--- Montants globaux ---")
    add_column_if_not_exists(
        engine, table_name, 
        "montant_global_ht", 
        "NUMERIC(15,2) DEFAULT 0"
    )
    add_column_if_not_exists(
        engine, table_name, 
        "montant_global_ttc", 
        "NUMERIC(15,2) DEFAULT 0"
    )
    
    # ===== COLONNES POUR AVENANTS ODS =====
    print("\n--- Avenants ODS ---")
    add_column_if_not_exists(
        engine, table_name, 
        "avenants_ods", 
        "TEXT"
    )
    
    print("\n" + "=" * 70)
    print("✅ MISE À JOUR TERMINÉE!")
    print("=" * 70)
    
    # Afficher la structure finale
    print("\n📊 Structure finale de la table:")
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    for col in columns:
        print(f"   • {col['name']}: {col['type']}")


def update_with_default_values():
    """Met à jour les enregistrements existants avec des valeurs par défaut"""
    print("\n" + "=" * 70)
    print("🔄 MISE À JOUR DES VALEURS PAR DÉFAUT")
    print("=" * 70)
    
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        # Mettre à jour type_document pour les contrats existants
        result = conn.execute(
            text("UPDATE contrats SET type_document = 'Contrat simple' WHERE type_document IS NULL")
        )
        print(f"✅ {result.rowcount} contrat(s) mis à jour avec type 'Contrat simple'")
        
        conn.commit()
    
    print("✅ Mise à jour des valeurs par défaut terminée!")


def create_avenants_table():
    """Crée la table des avenants si elle n'existe pas"""
    print("\n" + "=" * 70)
    print("📋 VÉRIFICATION DE LA TABLE AVENANTS")
    print("=" * 70)
    
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    if "avenants_contrat" not in inspector.get_table_names():
        print("Création de la table 'avenants_contrat'...")
        
        create_table_sql = """
        CREATE TABLE avenants_contrat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contrat_id INTEGER NOT NULL,
            numero_avenant VARCHAR(20) NOT NULL,
            date_avenant DATE NOT NULL,
            nouveau_montant NUMERIC(12,2),
            nouvelle_duree INTEGER,
            nouvelle_date_fin DATE,
            modifications TEXT,
            est_signe BOOLEAN DEFAULT 0,
            date_signature DATE,
            document_path VARCHAR(500),
            FOREIGN KEY (contrat_id) REFERENCES contrats(id) ON DELETE CASCADE
        )
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        
        print("✅ Table 'avenants_contrat' créée avec succès!")
    else:
        print("⏭️ La table 'avenants_contrat' existe déjà.")


def create_historique_table():
    """Crée la table d'historique si elle n'existe pas"""
    print("\n" + "=" * 70)
    print("📋 VÉRIFICATION DE LA TABLE HISTORIQUE")
    print("=" * 70)
    
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    if "historique_contrat" not in inspector.get_table_names():
        print("Création de la table 'historique_contrat'...")
        
        create_table_sql = """
        CREATE TABLE historique_contrat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contrat_id INTEGER NOT NULL,
            date_action DATE NOT NULL,
            heure_action VARCHAR(8),
            action VARCHAR(100) NOT NULL,
            ancien_statut VARCHAR(50),
            nouveau_statut VARCHAR(50),
            utilisateur VARCHAR(100),
            commentaire TEXT,
            FOREIGN KEY (contrat_id) REFERENCES contrats(id) ON DELETE CASCADE
        )
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        
        print("✅ Table 'historique_contrat' créée avec succès!")
    else:
        print("⏭️ La table 'historique_contrat' existe déjà.")


def verify_installation():
    """Vérifie que toutes les colonnes sont bien présentes"""
    print("\n" + "=" * 70)
    print("🔍 VÉRIFICATION FINALE")
    print("=" * 70)
    
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    required_columns = [
        "type_document",
        "numero_marche", "date_marche", "autorite_contractante",
        "numero_convention", "date_convention", "organisme_convention",
        "numero_ods", "date_ods", "objet_ods", "signature_ods", "ods_path",
        "montant_global_ht", "montant_global_ttc",
        "avenants_ods"
    ]
    
    existing_columns = [col['name'] for col in inspector.get_columns("contrats")]
    
    missing = []
    for col in required_columns:
        if col not in existing_columns:
            missing.append(col)
    
    if missing:
        print("❌ Colonnes manquantes:")
        for col in missing:
            print(f"   • {col}")
    else:
        print("✅ Toutes les colonnes sont présentes!")
    
    # Vérifier les tables
    tables = inspector.get_table_names()
    if "avenants_contrat" in tables:
        print("✅ Table 'avenants_contrat' présente")
    else:
        print("❌ Table 'avenants_contrat' manquante")
    
    if "historique_contrat" in tables:
        print("✅ Table 'historique_contrat' présente")
    else:
        print("❌ Table 'historique_contrat' manquante")


    if __name__ == "__main__":
    try:
        # 1. Mettre à jour la table contrat
        main()
        
        # 2. Mettre à jour les valeurs par défaut
        update_with_default_values()
        
        # 3. Créer les tables supplémentaires
        create_avenants_table()
        create_historique_table()
        
        # 4. Vérification finale
        verify_installation()
        
        print("\n" + "=" * 70)
        print("🎉 TOUTES LES MISES À JOUR ONT ÉTÉ APPLIQUÉES AVEC SUCCÈS!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
