# models/expense.py - Version finale
from sqlalchemy import Column, Integer, Numeric, String, Float, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.base import Base


class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True)
    libelle = Column(String(200), nullable=False)
    categorie = Column(String(100))
    montant = Column(Numeric(12, 2), nullable=False)  # <-- C'est la seule colonne de montant
    date_depense = Column(Date, nullable=False)
    moyen_paiement = Column(String(50))
    description = Column(Text)
    
    # Clés étrangères pour les liaisons bancaires
    bank_account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=True)
    bank_transaction_id = Column(Integer, ForeignKey("bank_transactions.id"), nullable=True)
    
    # Relations avec les modèles bancaires
    bank_account = relationship(
        "BankAccount",
        foreign_keys=[bank_account_id],
        back_populates="expenses"
    )
    
    bank_transaction = relationship(
        "BankTransaction",
        foreign_keys=[bank_transaction_id],
        back_populates="expense",
        uselist=False
    )