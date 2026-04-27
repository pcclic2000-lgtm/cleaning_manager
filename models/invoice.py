# models/invoice.py - VERSION CORRIGÉE
from sqlalchemy import Column, Integer, Numeric, String, Date, Float, Boolean, ForeignKey, Text, Enum as SQLEnum, func
from sqlalchemy.orm import relationship
from database.base import Base
from models.enums import InvoiceStatus, PaymentMethod


class Invoice(Base):
    """Modèle pour les factures"""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    contrat_id = Column(Integer, ForeignKey("contrats.id"), nullable=True, index=True)
    
    # Dates
    date = Column(Date, nullable=False, server_default=func.current_date())
    due_date = Column(Date)
    
    # Montants
    subtotal = Column(Numeric(12, 2), default=0.0)        # HT
    tax_rate = Column(Numeric(5, 2), default=0.0)        # en pourcentage
    tax_amount = Column(Numeric(12, 2), default=0.0)      # montant de la TVA
    total_amount = Column(Numeric(12, 2), default=0.0)    # TTC
    amount_paid = Column(Numeric(12, 2), default=0.0)
    balance_due = Column(Numeric(12, 2), default=0.0)
    
    # Statut et paiement
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    payment_method = Column(SQLEnum(PaymentMethod))
    
    # Notes / conditions
    notes = Column(Text)
    terms = Column(Text)
    
    # ============ RELATIONS CORRIGÉES ============
    client = relationship("Client", back_populates="factures")
    contrat = relationship("Contrat", back_populates="factures_generees")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("InvoicePayment", back_populates="invoice", cascade="all, delete-orphan")
    # =============================================
    
    # Suivi
    created_at = Column(Date, server_default=func.current_date())
    updated_at = Column(Date, onupdate=func.current_date())
    
    def __repr__(self):
        return f"<Invoice {self.invoice_number} - client_id={self.client_id} - total={self.total_amount}>"


class InvoiceItem(Base):
    """Ligne d'une facture"""
    __tablename__ = "invoice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    description = Column(String(200), nullable=False)
    quantity = Column(Numeric(8, 3), default=1.0)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0.0)
    
    total_ht = Column(Numeric(12, 2), default=0.0)
    total_ttc = Column(Numeric(12, 2), default=0.0)
    
    # ============ RELATIONS CORRIGÉES ============
    invoice = relationship("Invoice", back_populates="items")
    # =============================================
    
    def __repr__(self):
        return f"<InvoiceItem {self.description} x {self.quantity}>"


class InvoicePayment(Base):
    """Paiement d'une facture"""
    __tablename__ = "invoice_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False, server_default=func.current_date())
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    reference = Column(String(100))
    
    note = Column(Text)
    
    # ============ RELATIONS CORRIGÉES ============
    invoice = relationship("Invoice", back_populates="payments")
    # =============================================
    
    def __repr__(self):
        return f"<InvoicePayment {self.amount} - {self.payment_method}>"