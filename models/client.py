# models/client.py - VERSION CORRIGÉE
from sqlalchemy import (
    Column, Integer, String, Date, Text, Boolean, Float, Numeric, ForeignKey, Enum as SQLEnum, func
)
from sqlalchemy.orm import relationship
from database.base import Base
from models.enums import StatutClient
from decimal import Decimal


class Client(Base):
    """Modèle pour les clients (orienté entreprise)"""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    code_client = Column(String(50), unique=True, index=True)

    # Raison sociale principale (utilisée pour les entreprises)
    raison_sociale = Column(String(200), nullable=True)

    # Champs "personne physique" pour compatibilité
    nom = Column(String(100), nullable=True)
    prenom = Column(String(100), nullable=True)

    @property
    def nom_complet(self):
        if self.raison_sociale:
            return self.raison_sociale
        if self.nom or self.prenom:
            return f"{(self.prenom or '').strip()} {(self.nom or '').strip()}".strip()
        return ""

    # Coordonnées / adresse
    entreprise = Column(String(200))
    adresse = Column(Text)
    ville = Column(String(100))
    code_postal = Column(String(20))
    pays = Column(String(100), default="Algérie")
    telephone = Column(String(20), nullable=True)
    telephone2 = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    site_web = Column(String(200), nullable=True)
    contact_nom = Column(String(150), nullable=True)

    # Statut et type
    statut = Column(SQLEnum(StatutClient), default=StatutClient.ACTIF)
    type_client = Column(String(50))

    # Informations commerciales / financières
    secteur_activite = Column(String(100))
    tva_intracommunautaire = Column(String(50))
    taux_tva = Column(Numeric(5, 2), default=Decimal('19.00'))

    solde_courant = Column(Numeric(12, 2), default=Decimal('0.00'))
    credit_max = Column(Numeric(12, 2), default=Decimal('0.00'))

    conditions_paiement = Column(String(50))
    mode_paiement_prefere = Column(String(50))
    banque = Column(String(150))
    numero_compte = Column(String(150))

    # Service / prestation
    frequence_nettoyage = Column(String(50))
    jours_prestation = Column(String(200))
    horaires_prestation = Column(String(200))
    source = Column(String(100))
    commercial_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    date_premier_contact = Column(Date)

    # Préférences
    preference_contact = Column(String(50))
    langue = Column(String(20), default="Français")

    # Notes et observations
    notes_internes = Column(Text)
    recommande = Column(Boolean, default=False)
    niveau_satisfaction = Column(Integer, default=0)

    # Documents
    contrat_path = Column(String(255))
    autres_documents = Column(Text)

    # Informations entreprise
    registre_commerce = Column(String(100))
    nif = Column(String(50))
    nis = Column(String(50))
    capital_social = Column(Numeric(15, 2), default=Decimal('0.00'))
    forme_juridique = Column(String(50))

    # ============ RELATIONS CORRIGÉES ============
    contrats = relationship("Contrat", back_populates="client", cascade="all, delete-orphan")
    factures = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")
    # =============================================

    # Suivi
    date_creation = Column(Date, nullable=False, server_default=func.current_date())
    date_modification = Column(Date)
    est_actif = Column(Boolean, default=True)

    def __repr__(self):
        code = self.code_client or "?"
        name = self.nom_complet or "Client"
        return f"<Client {code}: {name}>"


def generer_code_client(session, raison_sociale=None):
    """Génère un code client unique"""
    import random
    import string

    if not raison_sociale:
        letters = string.ascii_uppercase
        random_code = ''.join(random.choice(letters) for _ in range(6))
        base_code = f"CL-{random_code}"
    else:
        mots = raison_sociale.upper().split()
        lettres = []
        for mot in mots[:3]:
            if mot and mot[0].isalpha():
                lettres.append(mot[0])
        if len(lettres) >= 1:
            abbr = "".join(lettres[:3])
            base_code = "CL-" + abbr
        else:
            raison_clean = ''.join(c for c in raison_sociale.upper() if c.isalpha())[:3]
            base_code = f"CL-{raison_clean or 'CLI'}"

    clients_existants = session.query(Client).filter(
        Client.code_client.like(f"{base_code}-%")
    ).all()

    if not clients_existants:
        return f"{base_code}-001"

    numeros = []
    for client in clients_existants:
        if client.code_client:
            try:
                parts = client.code_client.split('-')
                if len(parts) >= 3:
                    num = int(parts[-1])
                    numeros.append(num)
            except (ValueError, IndexError):
                continue

    if not numeros:
        return f"{base_code}-001"

    next_num = max(numeros) + 1
    return f"{base_code}-{next_num:03d}"


def generer_code_client_simple(raison_sociale=None):
    """Version simplifiée sans session"""
    import random, string
    if not raison_sociale:
        random_code = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))
        return f"CL-{random_code}"

    raison_clean = ''.join(c for c in raison_sociale.upper() if c.isalpha() or c == '-')[:10]
    return f"CL-{raison_clean}"