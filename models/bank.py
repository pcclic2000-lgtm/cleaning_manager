# models/bank.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.base import Base
import enum


class TransactionType(enum.Enum):
    DEPOT = "Dépôt"
    RETRAIT = "Retrait"
    VIREMENT = "Virement"
    FRAIS_BANCAIRES = "Frais bancaires"
    INTERETS = "Intérêts"


class BankAccount(Base):
    __tablename__ = "bank_accounts"
    
    id = Column(Integer, primary_key=True)
    nom_compte = Column(String(100), nullable=False)
    banque = Column(String(100), nullable=False)
    numero_compte = Column(String(50))
    rib = Column(String(50))
    solde_initial = Column(Float, default=0.0)
    solde_actuel = Column(Float, default=0.0)
    devise = Column(String(10), default="DA")
    est_actif = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relations
    transactions = relationship("BankTransaction", back_populates="compte")
    expenses = relationship("Expense", back_populates="bank_account")  # Relation avec Expense
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class BankExpenseCategory(Base):  # Nom différent pour éviter la confusion
    __tablename__ = "bank_expense_categories"
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    couleur = Column(String(20), default="#3498db")
    est_actif = Column(Boolean, default=True)
    
    # Relations - UNIQUEMENT avec BankTransaction
    transactions = relationship("BankTransaction", back_populates="categorie")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    
    id = Column(Integer, primary_key=True)
    compte_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=False)
    date_transaction = Column(DateTime, nullable=False)
    type_transaction = Column(Enum(TransactionType), nullable=False)
    montant = Column(Float, nullable=False)
    
    # Relations avec BankExpenseCategory (pas avec ExpenseCategory)
    categorie_id = Column(Integer, ForeignKey("bank_expense_categories.id"), nullable=True)
    beneficiaire = Column(String(200))
    description = Column(Text)
    reference = Column(String(100))
    source = Column(String(200))
    facture_id = Column(Integer, nullable=True)
    justificatif_path = Column(String(500))
    solde_apres = Column(Float)
    notes = Column(Text)
    
    # Relations
    compte = relationship("BankAccount", back_populates="transactions")
    categorie = relationship("BankExpenseCategory", back_populates="transactions")
    
    # Relation avec Expense (une transaction peut être liée à une dépense)
    expense = relationship(
        "Expense",
        foreign_keys="[Expense.bank_transaction_id]",
        back_populates="bank_transaction",
        uselist=False
    )
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    @property
    def est_entree(self):
        return self.type_transaction in [TransactionType.DEPOT, TransactionType.INTERETS]
    
    @property
    def est_sortie(self):
        return self.type_transaction in [TransactionType.RETRAIT, TransactionType.FRAIS_BANCAIRES, TransactionType.VIREMENT]
