# models/paye_globale.py
"""
Modèle pour la gestion de la paie globale avec répartition par site
"""

from decimal import Decimal

from decimal import Decimal

from sqlalchemy import Column, Integer, Numeric, String, Float, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.base import Base
from datetime import date


class PayeGlobale(Base):
    """Paie globale mensuelle"""
    __tablename__ = "paye_globale"
    
    id = Column(Integer, primary_key=True)
    mois = Column(Integer, nullable=False)  # 1-12
    annee = Column(Integer, nullable=False)
    date_paiement = Column(Date, nullable=False, default=date.today)
    
    # Totaux globaux
    total_brut = Column(Numeric(14, 2), default=0.0)
    total_cnss = Column(Numeric(14, 2), default=0.0)  # Cotisations CNSS/CASNOS
    total_net = Column(Numeric(14, 2), default=0.0)
    
    # Statut
    est_valide = Column(Integer, default=0)  # 0=brouillon, 1=validé, 2=payé
    notes = Column(Text)
    
    # Relations
    repartitions = relationship("RepartitionPaie", back_populates="paye", cascade="all, delete-orphan")
    
    created_at = Column(Date, default=date.today)
    updated_at = Column(Date, onupdate=date.today)
    
    @property
    def periode(self):
        """Retourne la période au format MM/YYYY"""
        return f"{self.mois:02d}/{self.annee}"
    
    def __repr__(self):
        return f"<PayeGlobale {self.periode} - Total: {self.total_net:,.0f} DA>"


class RepartitionPaie(Base):
    """Répartition de la paie par site/client"""
    __tablename__ = "repartition_paie"
    
    id = Column(Integer, primary_key=True)
    # CORRECTION: Le nom de la colonne doit être 'paye_id' (pas 'paiye_id')
    paye_id = Column(Integer, ForeignKey("paye_globale.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    
    # Nom du site (si client non spécifié)
    nom_site = Column(String(200))
    
    # Montants
    montant_brut = Column(Numeric(14, 2), default=Decimal('0.00'))
    montant_cnss = Column(Numeric(14, 2), default=Decimal('0.00'))
    montant_net = Column(Numeric(14, 2), default=Decimal('0.00'))
    
    # Nombre d'agents affectés
    nombre_agents = Column(Integer, default=0)
    
    # Commentaire
    notes = Column(Text)
    
    # Relations
    paye = relationship("PayeGlobale", back_populates="repartitions")
    client = relationship("Client")
    
    @property
    def nom_affichage(self):
        """Nom du site pour affichage"""
        if self.client:
            return self.client.raison_sociale or self.client.nom_complet
        return self.nom_site or "Site sans nom"
    
    def __repr__(self):
        return f"<Repartition {self.nom_affichage}: {self.montant_net:,.0f} DA>"