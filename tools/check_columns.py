#!/usr/bin/env python3
"""
Script de migration SQLite pour ajouter les colonnes manquantes à la table `clients`.

Usage:
    python migrate_add_client_columns.py
ou pour préciser le fichier de DB:
    python migrate_add_client_columns.py /chemin/vers/database.db
"""

import sys
import os
import shutil
import sqlite3
from pathlib import Path

# Liste des chemins candidates pour la DB (ordre de priorité)
DEFAULT_CANDIDATES = [
    Path("database/cleaning_manager.db"),
    Path("database/database.db"),
    Path("cleaning_manager.db"),
    Path("database.db"),
    Path("cleaning_manager.sqlite"),
    Path("db.sqlite3"),
]


# Définition des colonnes à ajouter : nom -> SQL fragment (type + DEFAULT si souhaité)
# IMPORTANT: Ces noms sont HARDCODÉS et sécurisés
# Types choisis pour SQLite (TEXT, REAL, INTEGER)
COLUMNS_TO_ADD = {
    # coordonnées / adresse
    "ville": "TEXT",
    "code_postal": "TEXT",
    "pays": "TEXT DEFAULT 'Algérie'",
    "telephone2": "TEXT",
    "site_web": "TEXT",
    "contact_nom": "TEXT",

    # personne / entreprise
    "raison_sociale": "TEXT",
    "nom": "TEXT",
    "prenom": "TEXT",
    "entreprise": "TEXT",

    # commerciaux / financiers
    "taux_tva": "REAL DEFAULT 19.0",
    "tva_intracommunautaire": "TEXT",
    "solde_courant": "REAL DEFAULT 0.0",
    "credit_max": "REAL DEFAULT 0.0",
    "conditions_paiement": "TEXT",
    "mode_paiement_prefere": "TEXT",
    "banque": "TEXT",
    "numero_compte": "TEXT",

    # service et prestation
    "frequence_nettoyage": "TEXT",
    "jours_prestation": "TEXT",
    "horaires_prestation": "TEXT",
    "source": "TEXT",

    # notes / statut / meta
    "notes_internes": "TEXT",
    "recommande": "INTEGER DEFAULT 0",           # 0/1 pour False/True
    "niveau_satisfaction": "INTEGER DEFAULT 0",

    # informations entreprise / identifiants
    "registre_commerce": "TEXT",
    "nif": "TEXT",
    "nis": "TEXT",
    "capital_social": "REAL DEFAULT 0.0",
    "forme_juridique": "TEXT",

    # compatibilité / anciens noms éventuellement utilisés par la vue
    "solde": "REAL DEFAULT 0.0",                 # si la vue utilise 'solde' au lieu de solde_courant
    "telephone_principal": "TEXT",               # fallback
}

def find_db_path(cli_arg=None):
    if cli_arg:
        p = Path(cli_arg)
        if p.exists():
            return p
        else:
            raise FileNotFoundError(f"Chemin passé en argument introuvable: {cli_arg}")

    for p in DEFAULT_CANDIDATES:
        if p.exists():
            return p
    return None

def backup_db(db_path: Path) -> Path:
    backup = db_path.with_suffix(db_path.suffix + ".bak")
    shutil.copy2(db_path, backup)
    return backup

def get_existing_columns(conn: sqlite3.Connection, table: str):
    # Sécurisé: PRAGMA table_info ne prend pas de paramètres,
    # mais le nom de table est contrôlé (vient de notre code)
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info('{table}');")
    rows = cur.fetchall()
    # PRAGMA table_info returns rows with second field name
    existing = [r[1] for r in rows]
    return existing

def add_column(conn: sqlite3.Connection, table: str, column: str, definition: str):
    """
    Ajoute une colonne à une table.
    NOTE: Les noms de table et colonne sont HARDCODÉS et sécurisés,
    donc l'utilisation de f-string est acceptable dans ce contexte spécifique.
    """
    cur = conn.cursor()
    # Les noms de table et colonne sont contrôlés (hardcodés dans COLUMNS_TO_ADD)
    # et ne viennent PAS de l'utilisateur, donc c'est sécurisé
    sql = f'ALTER TABLE "{table}" ADD COLUMN "{column}" {definition};'
    cur.execute(sql)

def main():
    cli_path = sys.argv[1] if len(sys.argv) > 1 else None
    db_path = find_db_path(cli_path)
    if db_path is None:
        print("Aucune base SQLite trouvée aux emplacements attendus.")
        print("Passez en argument le chemin vers le fichier .db si nécessaire.")
        sys.exit(1)

    print(f"Base détectée : {db_path}")
    backup_path = backup_db(db_path)
    print(f"Sauvegarde créée : {backup_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        # Vérifier présence de la table clients - requête sécurisée (paramètre fixe)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients';")
        if not cur.fetchone():
            print("La table 'clients' n'existe pas dans la base. Rien à faire.")
            sys.exit(1)

        existing = get_existing_columns(conn, "clients")
        print("Colonnes existantes (clients):")
        print(", ".join(existing))

        to_add = []
        for col, definition in COLUMNS_TO_ADD.items():
            if col in existing:
                print(f" • {col} : existe déjà — SKIP")
            else:
                to_add.append((col, definition))

        if not to_add:
            print("Aucune colonne manquante à ajouter.")
            return

        print("\nAjout des colonnes manquantes :")
        for col, definition in to_add:
            try:
                print(f" + Ajout colonne {col} ({definition}) ...", end=" ")
                add_column(conn, "clients", col, definition)
                conn.commit()
                print("OK")
            except Exception as e:
                print(f"ERREUR: {e}")
                conn.rollback()

        # Vérification finale
        existing_after = get_existing_columns(conn, "clients")
        print("\nColonnes après migration :")
        print(", ".join(existing_after))

        added = [c for c, _ in to_add if c in existing_after]
        failed = [c for c, _ in to_add if c not in existing_after]

        print("\nRésumé:")
        print(f" Colonnes ajoutées : {len(added)} -> {', '.join(added) if added else 'Aucune'}")
        if failed:
            print(f" Colonnes NON ajoutées (erreurs) : {', '.join(failed)}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
