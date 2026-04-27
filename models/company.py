# models/company.py - VERSION MISE À JOUR AVEC ADRESSE BANCAIRE
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from database.base import Base


class CompanyInfo(Base):
    """Informations de l'entreprise"""
    __tablename__ = "company_info"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(200), nullable=False)
    adresse = Column(Text)
    ville = Column(String(100))
    code_postal = Column(String(20))
    telephone = Column(String(50))
    email = Column(String(100))
    site_web = Column(String(100))
    rc = Column(String(50), comment="Registre de commerce")
    nif = Column(String(50), comment="Numéro d'identification fiscale")
    nis = Column(String(50), comment="Numéro d'identification statistique")
    art = Column(String(50), comment="Numéro d'article")
    
    # NOUVEAU CHAMPS AJOUTÉS
    numero_employeur = Column(String(50), comment="Numéro employeur")
    nom_directeur = Column(String(100), comment="Nom et prénom du directeur")
    fonction_directeur = Column(String(50), comment="Fonction du directeur (Gérant, Directeur, etc.)")
    
    # Informations bancaires - SIMPLIFIÉES
    rib = Column(String(100), comment="Relevé d'Identité Bancaire")
    banque = Column(String(100), comment="Nom de la banque")
    
    # NOUVEAU : Compte CCP complet
    compte_ccp = Column(String(50), comment="Compte CCP complet (ex: 371997 CLE 06)")
    
    # ===== NOUVEAUX CHAMPS BANCAIRES =====
    adresse_banque = Column(Text, comment="Adresse de la banque")
    ccp_banque = Column(String(50), comment="CCP de la banque (si différent)")
    # =====================================
    
    # Logo de l'entreprise (chemin du fichier)
    logo_path = Column(String(500))
    
    # Paramètres généraux
    devise = Column(String(10), default="DA")
    pays = Column(String(100), default="Algérie")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Méthode pour obtenir le nom du signataire
    def get_signe_par(self):
        """Retourne le nom et la fonction du directeur pour les signatures"""
        if self.nom_directeur and self.fonction_directeur:
            return f"{self.nom_directeur}\n{self.fonction_directeur}"
        elif self.nom_directeur:
            return self.nom_directeur
        return ""


class CompanySettings(Base):
    """Paramètres de l'application"""
    __tablename__ = "company_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Paramètres des factures
    prefix_facture = Column(String(10), default="FAC")
    prefix_devis = Column(String(10), default="DEV")
    prefix_bon = Column(String(10), default="BON")
    
    # Numérotation
    prochain_numero_facture = Column(Integer, default=1)
    prochain_numero_devis = Column(Integer, default=1)
    prochain_numero_bon = Column(Integer, default=1)
    
    # Options de facturation
    taux_tva = Column(Integer, default=19, comment="Taux de TVA en pourcentage")
    mention_legale = Column(Text, default="TVA non applicable, article 293 B du CGI")
    conditions_paiement = Column(Text, default="Paiement à 30 jours")
    
    # Paramètres d'impression
    entete_facture = Column(Text, default="Facture")
    pied_facture = Column(Text, default="Merci pour votre confiance")
    
    # Paramètres de sauvegarde
    auto_sauvegarde = Column(Boolean, default=True)
    frequence_sauvegarde = Column(Integer, default=7, comment="En jours")
    
    # Sécurité
    mot_de_passe_admin = Column(String(100))
    session_timeout = Column(Integer, default=30, comment="En minutes")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())