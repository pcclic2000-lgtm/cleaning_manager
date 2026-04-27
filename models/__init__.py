# models/__init__.py
"""
Point d'entrée pour tous les modèles avec gestion correcte des dépendances
"""

# 1. D'abord les modèles de base sans dépendances
from .enums import *
from .company import CompanyInfo, CompanySettings
from .client import Client

# 2. Ensuite les modèles qui dépendent des précédents
from .employee import Employee  # Employee avant Contrat car Contrat a une relation vers Affectation qui référence Employee

# 3. Modèle Affectation (dépend de Employee)
from .affectation import Affectation

# 4. Modèle Contrat (dépend de Client et Affectation)
from .contrat import Contrat

# 5. Modèle Tache (dépend de Employee et Contrat)
from .tache import Tache

# 6. Modèles de facturation
from .invoice import Invoice, InvoiceItem, InvoicePayment

# 7. Modèles bancaires et dépenses
from .bank import BankAccount, BankTransaction, TransactionType, BankExpenseCategory
from .expense import Expense

# 8. Forcer la configuration des mappers
from sqlalchemy.orm import configure_mappers
try:
    configure_mappers()
    print("✅ Mappers configurés avec succès")
except Exception as e:
    print(f"⚠️  Erreur lors de la configuration des mappers: {e}")