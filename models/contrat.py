# models/contrat.py - VERSION CORRIGÉE AVEC CHAÎNES POUR TOUTES LES RELATIONS
from sqlalchemy import (
    Column, Integer, String, Date, Float, Boolean, 
    ForeignKey, Text, Enum as SQLEnum, Numeric, func
)
from sqlalchemy.orm import relationship
from database.base import Base
from models.enums import TypeContrat, FrequenceNettoyage, StatutContrat, PeriodiciteFacturation, TypeDocumentContrat
from datetime import date, timedelta
import calendar


class Contrat(Base):
    """Modèle pour les contrats de prestation avec support Marché/Convention et ODS"""
    __tablename__ = "contrats"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    numero_contrat = Column(String(50), unique=True, index=True, nullable=False)
    
    # TYPE DE CONTRAT (NOUVEAU)
    type_document = Column(String(50), nullable=False, default="Contrat simple")
    type_facture = Column(String(50), default="standard")  # "standard", "beni_messous", "chu_douera"
    # =============================================
    
    # Informations générales
    type_contrat = Column(SQLEnum(TypeContrat), nullable=False, default=TypeContrat.MENSUEL)
    statut = Column(SQLEnum(StatutContrat), nullable=False, default=StatutContrat.BROUILLON)
    
    # Dates
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date, nullable=True)
    date_signature = Column(Date, nullable=True)
    date_resiliation = Column(Date, nullable=True)
    preavis_jours = Column(Integer, default=30)  # Préavis de résiliation en jours
    
    # ===== INFORMATIONS SPÉCIFIQUES MARCHÉ/CONVENTION =====
    numero_marche = Column(String(100), nullable=True)  # Numéro du marché public
    date_marche = Column(Date, nullable=True)          # Date d'attribution du marché
    autorite_contractante = Column(String(200), nullable=True)  # Autorité qui attribue le marché
    
    numero_convention = Column(String(100), nullable=True)  # Numéro de convention
    date_convention = Column(Date, nullable=True)           # Date de la convention
    organisme_convention = Column(String(200), nullable=True)  # Organisme partenaire
    
    # ===== INFORMATIONS ODS (Ordre de Service) =====
    numero_ods = Column(String(100), nullable=True)        # Numéro de l'Ordre de Service
    date_ods = Column(Date, nullable=True)                 # Date de l'ODS
    objet_ods = Column(String(500), nullable=True)         # Objet de l'ODS
    signature_ods = Column(String(100), nullable=True)     # Signataire de l'ODS
    
    # Documents ODS
    ods_path = Column(String(500), nullable=True)          # Chemin du fichier ODS
    avenants_ods = Column(Text, nullable=True)              # Liste des ODS modificatifs (JSON)
    
    # Période d'essai
    periode_essai_jours = Column(Integer, default=0)
    date_fin_essai = Column(Date, nullable=True)
    
    # Durée
    duree_mois = Column(Integer, nullable=False)  # Durée initiale en mois
    tacite_reconduction = Column(Boolean, default=True)
    
    # Tarification
    montant_mensuel_ht = Column(Numeric(12, 2), nullable=False, default=0.0)
    tva = Column(Numeric(5, 2), default=19.0)  # Taux TVA en %
    montant_mensuel_ttc = Column(Numeric(12, 2), nullable=False, default=0.0)
    montant_global_ht = Column(Numeric(15, 2), default=0.0)  # Montant total du marché/convention
    montant_global_ttc = Column(Numeric(15, 2), default=0.0)
    frais_installation = Column(Numeric(12, 2), default=0.0)
    caution = Column(Numeric(12, 2), default=0.0)
    
    # Facturation
    periodicite_facturation = Column(SQLEnum(PeriodiciteFacturation), 
                                      default=PeriodiciteFacturation.MENSUELLE)
    jour_facturation = Column(Integer, default=1)  # Jour du mois pour facturation
    delai_paiement_jours = Column(Integer, default=30)  # Délai de paiement
    
    # Détails du service
    frequence_nettoyage = Column(SQLEnum(FrequenceNettoyage), nullable=False)
    superficie = Column(Numeric(10, 2), nullable=True)
    nombre_pieces = Column(Integer, nullable=True)
    nombre_employes = Column(Integer, nullable=True)  # Nombre d'agents affectés
    heures_mensuelles = Column(Integer, nullable=True)  # Heures de prestation par mois
    
    # Horaires
    jours_prestation = Column(String(200))  # "Lundi, Mercredi, Vendredi"
    horaires_prestation = Column(String(200))  # "08:00-12:00, 14:00-18:00"
    
    # Lieu de prestation
    adresse_prestation = Column(Text, nullable=True)
    ville_prestation = Column(String(100), nullable=True)
    code_postal_prestation = Column(String(20), nullable=True)
    
    # Responsables côté client
    responsable_nom = Column(String(100))
    responsable_telephone = Column(String(20))
    responsable_email = Column(String(100))
    
    # Documents
    contrat_path = Column(String(500))
    avenants_path = Column(Text)  # JSON list des chemins d'avenants
    plans_path = Column(String(500))
    autres_documents = Column(Text)
    
    # Clauses particulières
    clauses_specifiques = Column(Text)
    conditions_resiliation = Column(Text)
    penalites_retard = Column(Text)
    
    # ============ RELATIONS CORRIGÉES (TOUTES EN CHAÎNES) ============
    client = relationship("Client", back_populates="contrats")
    factures_generees = relationship("Invoice", back_populates="contrat")
    
    # Utiliser des chaînes pour toutes les relations pour éviter les problèmes d'ordre d'import
    taches = relationship(
        "Tache",  # Chaîne, pas la classe
        back_populates="contrat", 
        cascade="all, delete-orphan"
    )
    
    affectations = relationship(
        "Affectation",  # Chaîne, pas la classe
        back_populates="contrat", 
        cascade="all, delete-orphan"
    )
    
    avenants = relationship(
        "AvenantContrat",  # Chaîne, pas la classe
        back_populates="contrat",
        cascade="all, delete-orphan"
    )
    
    historique_statuts = relationship(
        "HistoriqueContrat",  # Chaîne, pas la classe
        back_populates="contrat",
        cascade="all, delete-orphan"
    )
    # =============================================
    
    # Suivi
    date_creation = Column(Date, nullable=False, server_default=func.current_date())
    date_modification = Column(Date, onupdate=func.current_date())
    cree_par = Column(String(100))
    modifie_par = Column(String(100))
    
    
    @property
    def type_document_enum(self):
        """Retourne l'enum correspondant à la valeur texte"""
        from models.enums import TypeDocumentContrat
        mapping = {
            "Contrat simple": TypeDocumentContrat.CONTRAT,
            "Marché public": TypeDocumentContrat.MARCHE,
            "Convention": TypeDocumentContrat.CONVENTION
        }
        return mapping.get(self.type_document, TypeDocumentContrat.CONTRAT)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculer_montant_ttc()
        self.calculer_date_fin_essai()
    
    def calculer_montant_ttc(self):
        """Calcule le montant TTC à partir du HT et de la TVA"""
        ht = float(self.montant_mensuel_ht or 0)
        tva = float(self.tva or 0)
        self.montant_mensuel_ttc = ht * (1 + tva / 100)
        
        # Calculer le montant global si durée définie
        if self.duree_mois and self.montant_mensuel_ht:
            self.montant_global_ht = self.montant_mensuel_ht * self.duree_mois
            self.montant_global_ttc = self.montant_global_ht * (1 + tva / 100)
    
    def calculer_date_fin_essai(self):
        """Calcule la date de fin de période d'essai"""
        if self.date_debut and self.periode_essai_jours > 0:
            self.date_fin_essai = self.date_debut + timedelta(days=self.periode_essai_jours)
    
    def est_en_periode_essai(self, date_reference=None):
        """Vérifie si le contrat est en période d'essai"""
        if not date_reference:
            date_reference = date.today()
        if self.date_fin_essai:
            return date_reference <= self.date_fin_essai
        return False
    
    def est_actif(self, date_reference=None):
        """Vérifie si le contrat est actif à une date donnée"""
        if not date_reference:
            date_reference = date.today()
        
        if self.statut != StatutContrat.ACTIF:
            return False
        
        if date_reference < self.date_debut:
            return False
        
        if self.date_fin and date_reference > self.date_fin:
            return False
        
        return True
    
    def jours_restants(self):
        """Retourne le nombre de jours restants avant expiration"""
        if not self.date_fin:
            return None
        return (self.date_fin - date.today()).days
    
    def mois_restants(self):
        """Retourne le nombre de mois restants avant expiration"""
        jours = self.jours_restants()
        if jours is None:
            return None
        return max(0, jours // 30)
    
    def prochaine_echeance(self):
        """Retourne la prochaine date d'échéance (fin de contrat ou fin de période)"""
        if self.date_fin:
            return self.date_fin
        return self.date_debut + timedelta(days=365)  # Par défaut 1 an
    
    def prochaine_facturation(self):
        """Calcule la prochaine date de facturation"""
        today = date.today()
        
        if self.periodicite_facturation == PeriodiciteFacturation.MENSUELLE:
            # Facturation le jour_facturation du mois
            if today.day < self.jour_facturation:
                return date(today.year, today.month, self.jour_facturation)
            else:
                next_month = today.month + 1
                next_year = today.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                # Gérer les mois avec moins de jours
                last_day = calendar.monthrange(next_year, next_month)[1]
                jour = min(self.jour_facturation, last_day)
                return date(next_year, next_month, jour)
        
        return today + timedelta(days=30)  # Fallback
    
    def generer_facture(self, session, periode=None):
        """
        Génère une facture pour le contrat
        Retourne l'objet Invoice créé
        """
        from models.invoice import Invoice, InvoiceItem
        from models.enums import InvoiceStatus
        
        if not self.est_actif():
            raise ValueError("Impossible de facturer un contrat inactif")
        
        # Déterminer la période de facturation
        if not periode:
            periode = self.prochaine_facturation()
        
        # Construire la description avec les références
        description = f"Prestation de nettoyage - {self.frequence_nettoyage.value}\n"
        description += f"Contrat {self.numero_contrat}\n"
        
        if self.type_document == TypeDocumentContrat.MARCHE and self.numero_marche:
            description += f"Marché n°{self.numero_marche} du {self.date_marche.strftime('%d/%m/%Y')}\n"
        elif self.type_document == TypeDocumentContrat.CONVENTION and self.numero_convention:
            description += f"Convention n°{self.numero_convention} du {self.date_convention.strftime('%d/%m/%Y')}\n"
        
        if self.numero_ods:
            description += f"ODS n°{self.numero_ods} du {self.date_ods.strftime('%d/%m/%Y')}\n"
        
        description += f"Période: {periode.strftime('%B %Y')}"
        
        # Créer la facture
        invoice = Invoice(
            client_id=self.client_id,
            invoice_number=self._generer_numero_facture(session),
            date=date.today(),
            due_date=date.today() + timedelta(days=self.delai_paiement_jours),
            status=InvoiceStatus.DRAFT,
            notes=description,
            contrat_id=self.id
        )
        
        # Ajouter l'article principal
        item = InvoiceItem(
            description=description,
            quantity=1,
            unit_price=float(self.montant_mensuel_ht),
            tax_rate=float(self.tva),
            total_ht=float(self.montant_mensuel_ht),
            total_ttc=float(self.montant_mensuel_ttc)
        )
        
        invoice.items.append(item)
        invoice.subtotal = float(self.montant_mensuel_ht)
        invoice.tax_amount = float(self.montant_mensuel_ttc - self.montant_mensuel_ht)
        invoice.total_amount = float(self.montant_mensuel_ttc)
        invoice.balance_due = invoice.total_amount
        
        return invoice
    
    def _generer_numero_facture(self, session):
        """Génère un numéro de facture unique"""
        from models.invoice import Invoice
        year = date.today().year
        month = date.today().month
        prefix = f"FACT-{year}{month:02d}-"
        
        last_invoice = session.query(Invoice)\
            .filter(Invoice.invoice_number.like(f"{prefix}%"))\
            .order_by(Invoice.invoice_number.desc())\
            .first()
        
        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}{new_num:04d}"
    
    def __repr__(self):
        type_doc = self.type_document.value if self.type_document else "Contrat"
        return f"<{type_doc} {self.numero_contrat}: {self.client.nom_complet if self.client else 'Client inconnu'}>"


class AvenantContrat(Base):
    """Modèle pour les avenants aux contrats"""
    __tablename__ = "avenants_contrat"
    
    id = Column(Integer, primary_key=True, index=True)
    contrat_id = Column(Integer, ForeignKey("contrats.id"), nullable=False)
    numero_avenant = Column(String(20), nullable=False)
    date_avenant = Column(Date, nullable=False, server_default=func.current_date())
    
    # Modifications
    nouveau_montant = Column(Numeric(12, 2))
    nouvelle_duree = Column(Integer)
    nouvelle_date_fin = Column(Date)
    modifications = Column(Text)  # Description des modifications
    
    # Statut
    est_signe = Column(Boolean, default=False)
    date_signature = Column(Date)
    
    # Document
    document_path = Column(String(500))
    
    # ============ RELATIONS CORRIGÉES ============
    contrat = relationship("Contrat", back_populates="avenants")
    # =============================================
    
    def __repr__(self):
        return f"<Avenant {self.numero_avenant} du {self.date_avenant}>"


class HistoriqueContrat(Base):
    """Historique des actions sur le contrat"""
    __tablename__ = "historique_contrat"
    
    id = Column(Integer, primary_key=True, index=True)
    contrat_id = Column(Integer, ForeignKey("contrats.id"), nullable=False)
    date_action = Column(Date, nullable=False, server_default=func.current_date())
    heure_action = Column(String(8))  # HH:MM:SS
    action = Column(String(100), nullable=False)
    
    ancien_statut = Column(String(50))
    nouveau_statut = Column(String(50))
    
    utilisateur = Column(String(100))
    commentaire = Column(Text)
    
    # ============ RELATIONS CORRIGÉES ============
    contrat = relationship("Contrat", back_populates="historique_statuts")
    # =============================================
    
    def __repr__(self):
        return f"<Historique {self.date_action}: {self.action}>"