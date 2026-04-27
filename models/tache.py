# models/tache.py - VERSION CORRIGÉE
from sqlalchemy import Column, Integer, String, Text, Date, Time, Boolean, ForeignKey, Float, Enum as SQLEnum, func
from sqlalchemy.orm import relationship
from database.base import Base
from models.enums import StatutTache, PrioriteTache, TypeTache


class Tache(Base):
    """Modèle pour les tâches de nettoyage"""
    __tablename__ = "taches"
    
    id = Column(Integer, primary_key=True, index=True)
    contrat_id = Column(Integer, ForeignKey("contrats.id"), nullable=False)
    titre = Column(String(200), nullable=False)
    description = Column(Text)
    
    type_tache = Column(SQLEnum(TypeTache), nullable=False)
    priorite = Column(SQLEnum(PrioriteTache), default=PrioriteTache.NORMALE)
    statut = Column(SQLEnum(StatutTache), default=StatutTache.A_FAIRE)
    
    # Planning
    date_prevue = Column(Date, nullable=False)
    heure_prevue = Column(Time)
    duree_estimee = Column(Integer)
    
    # Exécution
    date_realisation = Column(Date)
    heure_debut = Column(Time)
    heure_fin = Column(Time)
    duree_reelle = Column(Integer)
    
    # Employés affectés
    employee_id = Column(Integer, ForeignKey("employees.id"))
    
    # Évaluation
    note_satisfaction = Column(Integer)
    commentaires = Column(Text)
    
    # Matériel utilisé
    materiel_utilise = Column(Text)
    produits_utilises = Column(Text)
    
    # ============ RELATIONS CORRIGÉES ============
    contrat = relationship("Contrat", back_populates="taches")
    employee = relationship("Employee", back_populates="taches")
    # =============================================
    
    # Suivi
    date_creation = Column(Date, nullable=False, server_default=func.current_date())
    date_modification = Column(Date)
    
    def __repr__(self):
        return f"<Tache {self.titre} - {self.statut.value}>"