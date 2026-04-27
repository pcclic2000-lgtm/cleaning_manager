# tools/migrate_float_to_numeric.py
from sqlalchemy import text
from database.db import engine

MIGRATIONS = [
    # (table, colonne, nouveau_type, valeur_defaut)
    ("invoices", "subtotal",     "NUMERIC(12,2)", "0.00"),
    ("invoices", "tax_rate",     "NUMERIC(5,2)",  "19.00"),
    ("invoices", "tax_amount",   "NUMERIC(12,2)", "0.00"),
    ("invoices", "total_amount", "NUMERIC(12,2)", "0.00"),
    ("invoices", "amount_paid",  "NUMERIC(12,2)", "0.00"),
    ("invoices", "balance_due",  "NUMERIC(12,2)", "0.00"),
    ("clients", "taux_tva",      "NUMERIC(5,2)",  "19.00"),
    ("clients", "solde_courant", "NUMERIC(12,2)", "0.00"),
    ("clients", "credit_max",    "NUMERIC(12,2)", "0.00"),
    ("clients", "capital_social","NUMERIC(15,2)", "0.00"),
    ("cotisations", "montant_du",   "NUMERIC(12,2)", "0.00"),
    ("cotisations", "montant_paye", "NUMERIC(12,2)", "0.00"),
    ("expenses", "montant",        "NUMERIC(12,2)", "0.00"),
        ("paye_globale", "total_brut", "NUMERIC(14,2)", "0.00"),
        ("paye_globale", "total_cnss", "NUMERIC(14,2)", "0.00"),
        ("paye_globale", "total_net",  "NUMERIC(14,2)", "0.00"),
        ("repartition_paie", "montant_brut", "NUMERIC(14,2)", "0.00"),
        ("repartition_paie", "montant_cnss", "NUMERIC(14,2)", "0.00"),
        ("repartition_paie", "montant_net",  "NUMERIC(14,2)", "0.00"),
        # ... ajouter d'autres colonnes si nécessaire
    
]

# SQLite : NUMERIC et REAL sont des affinités de type,
# pas des types stricts → la migration est transparente,
# les valeurs existantes sont automatiquement converties.