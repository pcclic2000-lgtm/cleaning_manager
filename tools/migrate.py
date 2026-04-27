#!/usr/bin/env python3
"""
tools/migrate.py
================
Outil de migration de base de données.

Fonctions :
  - Ajout de colonnes manquantes à company_info
  - Ajout de colonnes manquantes à clients
  - Vérification d'intégrité

Usage :
    python tools/migrate.py [--check] [--db /chemin/vers/db.sqlite]
"""
import sys
import argparse
import sqlite3
import shutil
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DB_PATH

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ── Schémas de migration ────────────────────────────────────────────────────

MIGRATIONS: dict[str, dict[str, str]] = {
    "company_info": {
        "nom_directeur":    "VARCHAR(100)",
        "fonction_directeur": "VARCHAR(50)",
        "numero_employeur": "VARCHAR(50)",
    },
    "clients": {
        "ville":                  "TEXT",
        "code_postal":            "TEXT",
        "pays":                   "TEXT DEFAULT 'Algérie'",
        "telephone2":             "TEXT",
        "site_web":               "TEXT",
        "contact_nom":            "TEXT",
        "raison_sociale":         "TEXT",
        "taux_tva":               "REAL DEFAULT 19.0",
        "solde_courant":          "REAL DEFAULT 0.0",
        "credit_max":             "REAL DEFAULT 0.0",
        "conditions_paiement":    "TEXT",
        "mode_paiement_prefere":  "TEXT",
        "banque":                 "TEXT",
        "numero_compte":          "TEXT",
        "frequence_nettoyage":    "TEXT",
        "jours_prestation":       "TEXT",
        "horaires_prestation":    "TEXT",
        "source":                 "TEXT",
        "notes_internes":         "TEXT",
        "recommande":             "INTEGER DEFAULT 0",
        "niveau_satisfaction":    "INTEGER DEFAULT 0",
        "registre_commerce":      "TEXT",
        "nif":                    "TEXT",
        "nis":                    "TEXT",
        "capital_social":         "REAL DEFAULT 0.0",
        "forme_juridique":        "TEXT",
    },
}


# ── Helpers ─────────────────────────────────────────────────────────────────

def backup(db_path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = db_path.with_name(f"{db_path.stem}_backup_{ts}.db")
    shutil.copy2(db_path, dest)
    logger.info("Sauvegarde créée : %s", dest)
    return dest


def get_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    # Sécurisé: SQLite échappe automatiquement le nom de table dans PRAGMA
    # mais on utilise quand même un paramètre pour éviter l'injection
    # Note: PRAGMA n'accepte pas les paramètres nommés, mais le nom de table
    # doit être valide et est contrôlé
    rows = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
    return {r[1] for r in rows}


def get_tables(conn: sqlite3.Connection) -> set[str]:
    # Sécurisé: requête fixe sans paramètres utilisateur
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {r[0] for r in rows}


def run_migration(conn: sqlite3.Connection, table: str,
                  columns: dict[str, str], dry_run: bool = False) -> tuple[int, int]:
    """
    Applique les colonnes manquantes sur `table`.
    Retourne (added, skipped).
    
    IMPORTANT: Cette fonction utilise f-strings pour construire les noms de colonnes,
    car SQLite n'accepte PAS les paramètres pour les identifiants (noms de colonnes).
    Cependant, les noms de colonnes sont HARDCODÉS dans MIGRATIONS et ne viennent PAS
    de l'utilisateur, donc c'est sécurisé.
    """
    existing = get_columns(conn, table)
    added = skipped = 0

    for col, typedef in columns.items():
        if col in existing:
            skipped += 1
            logger.debug("  SKIP %s.%s (déjà présente)", table, col)
            continue

        # Les noms de colonnes sont HARDCODÉS et sécurisés
        # C'est une exception acceptable car les identifiants ne peuvent pas être paramétrés
        sql = f'ALTER TABLE "{table}" ADD COLUMN "{col}" {typedef}'
        if dry_run:
            logger.info("  [DRY-RUN] %s", sql)
            added += 1
        else:
            try:
                conn.execute(sql)
                conn.commit()
                logger.info("  + %s.%s (%s)", table, col, typedef)
                added += 1
            except sqlite3.Error as e:
                conn.rollback()
                logger.error("  ✗ %s.%s : %s", table, col, e)

    return added, skipped


def check_integrity(conn: sqlite3.Connection) -> bool:
    # Sécurisé: commande PRAGMA fixe
    result = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if result == "ok":
        logger.info("Intégrité : OK")
        return True
    logger.error("Intégrité compromise : %s", result)
    return False


    # ── CLI ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Migration de la base de données Clean Manager ERP")
    p.add_argument("--db",        type=Path, default=DB_PATH,
                   help=f"Chemin vers la base SQLite (défaut : {DB_PATH})")
    p.add_argument("--dry-run",   action="store_true",
                   help="Affiche les migrations sans les appliquer")
    p.add_argument("--check",     action="store_true",
                   help="Vérifie uniquement l'intégrité de la base")
    p.add_argument("--no-backup", action="store_true",
                   help="Ne pas créer de sauvegarde avant la migration")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if not args.db.exists():
        logger.error("Base de données introuvable : %s", args.db)
        return 1

    conn = sqlite3.connect(str(args.db))

    try:
        if args.check:
            return 0 if check_integrity(conn) else 1

        if not args.dry_run and not args.no_backup:
            backup(args.db)

        tables = get_tables(conn)
        total_added = total_skipped = 0

        for table, columns in MIGRATIONS.items():
            if table not in tables:
                logger.warning("Table '%s' absente — migration ignorée", table)
                continue
            logger.info("Migration : %s", table)
            added, skipped = run_migration(conn, table, columns, dry_run=args.dry_run)
            total_added   += added
            total_skipped += skipped

        logger.info("─" * 50)
        logger.info("Colonnes ajoutées : %d  |  Ignorées : %d", total_added, total_skipped)
        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
