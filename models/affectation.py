# models/affectation.py - CORRECTION COMPLÈTE
from sqlalchemy import Column, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship
from database.base import Base


class Affectation(Base):
    """Modèle pour les affectations d'employés aux contrats"""
    __tablename__ = "affectations"
    
    id = Column(Integer, primary_key=True, index=True)
    contrat_id = Column(Integer, ForeignKey("contrats.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date)
    
    # Relations correctes avec back_populates
    contrat = relationship("Contrat", back_populates="affectations")
    employee = relationship("Employee", back_populates="affectations")
    
    def __repr__(self):
        return f"<Affectation Contrat:{self.contrat_id} - Employee:{self.employee_id}>"