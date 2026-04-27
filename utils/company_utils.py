# utils/company_utils.py
from database.db import SessionLocal, get_session
from models.company import CompanyInfo, CompanySettings


def get_company_info():
    """Récupère les informations de l'entreprise"""
    with get_session() as session:
        company = session.query(CompanyInfo).first()
        return company


def get_company_settings():
    """Récupère les paramètres de l'entreprise"""
    with get_session() as session:
        settings = session.query(CompanySettings).first()
        return settings


def get_next_invoice_number():
    """Génère le prochain numéro de facture"""
    with get_session() as session:
        settings = session.query(CompanySettings).first()
        if not settings:
            return "FAC-001"
        
        number = settings.prochain_numero_facture
        settings.prochain_numero_facture += 1
        
        session.add(settings)
        session.commit()
        
        return f"{settings.prefix_facture}-{number:03d}"


def get_next_quote_number():
    """Génère le prochain numéro de devis"""
    with get_session() as session:
        settings = session.query(CompanySettings).first()
        if not settings:
            return "DEV-001"
        
        number = settings.prochain_numero_devis
        settings.prochain_numero_devis += 1
        
        session.add(settings)
        session.commit()
        
        return f"{settings.prefix_devis}-{number:03d}"


def get_company_address():
    """Retourne l'adresse complète de l'entreprise"""
    company = get_company_info()
    if not company:
        return ""
    
    parts = []
    if company.adresse:
        parts.append(company.adresse)
    if company.ville:
        parts.append(company.ville)
    if company.code_postal:
        parts.append(company.code_postal)
    
    return ", ".join(parts)
