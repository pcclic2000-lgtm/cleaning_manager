# models/cotisation.py
"""
Modèle Cotisation — CNAS, CASNOS, CACOBATPH, G50
"""
from sqlalchemy import Column, Integer, String, Numeric, Float, Date, Text, Enum as SAEnum
from sqlalchemy.orm import validates
from database.base import Base
import enum
from datetime import date
from decimal import Decimal

class TypeCotisation(str, enum.Enum):
    CNAS      = "CNAS"
    CASNOS    = "CASNOS"
    CACOBATPH = "CACOBATPH"
    G50       = "G50"


class PeriodeCotisation(str, enum.Enum):
    MENSUELLE    = "MENSUELLE"
    TRIMESTRIELLE = "TRIMESTRIELLE"
    ANNUELLE     = "ANNUELLE"


class StatutCotisation(str, enum.Enum):
    EN_ATTENTE = "EN_ATTENTE"
    PAYE       = "PAYE"
    EN_RETARD  = "EN_RETARD"


class Cotisation(Base):
    __tablename__ = "cotisations"

    id              = Column(Integer, primary_key=True, index=True)

    # Identification
    type_cotisation = Column(SAEnum(TypeCotisation),    nullable=False)
    periode_type    = Column(SAEnum(PeriodeCotisation), nullable=False, default=PeriodeCotisation.MENSUELLE)

    # Période concernée
    annee           = Column(Integer,  nullable=False)
    mois            = Column(Integer,  nullable=True)   # 1-12, None si trimestriel/annuel
    trimestre       = Column(Integer,  nullable=True)   # 1-4, None si mensuel/annuel

    # Montants
    montant_du      = Column(Numeric(12, 2),    nullable=False, default=Decimal('0.00'))
    montant_paye    = Column(Numeric(12, 2),    nullable=False, default=Decimal('0.00'))

    # Dates
    date_limite     = Column(Date,     nullable=True)
    date_paiement   = Column(Date,     nullable=True)

    # Statut
    statut          = Column(SAEnum(StatutCotisation), nullable=False,
                              default=StatutCotisation.EN_ATTENTE)

    # Pièce justificative
    numero_piece    = Column(String(100), nullable=True)
    chemin_piece    = Column(String(500), nullable=True)

    # Notes
    notes           = Column(Text, nullable=True)

    @property
    def solde(self) -> Decimal:
        return self.montant_du - self.montant_paye

    @property
    def label_periode(self) -> str:
        MOIS = ["", "Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
                "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
        if self.mois:
            return f"{MOIS[self.mois]} {self.annee}"
        if self.trimestre:
            return f"T{self.trimestre} {self.annee}"
        return str(self.annee)

    def __repr__(self):
        return f"<Cotisation {self.type_cotisation} {self.label_periode} — {self.statut}>"