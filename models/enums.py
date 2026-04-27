# models/enums.py - VERSION PROPRE
from enum import Enum

class StatutEmploye(str, Enum):
    ACTIF = "Actif"
    INACTIF = "Inactif"
    CONGE = "En congé"
    SUSPENDU = "Suspendu"

class TypeEmploye(str, Enum):
    PERMANENT = "Permanent"
    TEMPORAIRE = "Temporaire"
    INTERIMAIRE = "Intérimaire"
    STAGIAIRE = "Stagiaire"

class PosteEmploye(str, Enum):
    AGENT_DE_NETTOYAGE = "Agent de nettoyage"
    SUPERVISEUR = "Superviseur"
    CHEF_EQUIPE = "Chef d'équipe"
    MANAGER = "Manager"
    ADMINISTRATIF = "Administratif"

class JourSemaine(str, Enum):
    LUNDI = "Lundi"
    MARDI = "Mardi"
    MERCREDI = "Mercredi"
    JEUDI = "Jeudi"
    VENDREDI = "Vendredi"
    SAMEDI = "Samedi"
    DIMANCHE = "Dimanche"

class TypeHoraire(str, Enum):
    PLEIN_TEMPS = "Plein temps"
    MI_TEMPS = "Mi-temps"
    VARIABLE = "Variable"
    NUIT = "Nuit"
    JOUR = "Jour"

class StatutTache(str, Enum):
    A_FAIRE = "À faire"
    EN_COURS = "En cours"
    TERMINEE = "Terminée"
    ANNULEE = "Annulée"
    REPORTEE = "Reportée"

class PrioriteTache(str, Enum):
    BASSE = "Basse"
    NORMALE = "Normale"
    HAUTE = "Haute"
    URGENTE = "Urgente"

class TypeTache(str, Enum):
    NETTOYAGE = "Nettoyage"
    DESINFECTION = "Désinfection"
    LAVAGE = "Lavage"
    RANGEMENT = "Rangement"
    INSPECTION = "Inspection"
    MAINTENANCE = "Maintenance"

class StatutClient(str, Enum):
    ACTIF = "Actif"
    INACTIF = "Inactif"
    SUSPENDU = "Suspendu"
    PROSPECT = "Prospect"

class TypePaiement(str, Enum):
    ESPECES = "Espèces"
    CHEQUE = "Chèque"
    VIREMENT = "Virement"
    CARTE = "Carte bancaire"
    MOBILE = "Paiement mobile"

class InvoiceStatus(str, Enum):
    DRAFT = "Brouillon"
    SENT = "Envoyée"
    PENDING = "En attente"
    PARTIALLY_PAID = "Payée partiellement"
    PAID = "Payée"
    CANCELLED = "Annulée"

class PaymentMethod(str, Enum):
    CASH = "Espèces"
    CHECK = "Chèque"
    BANK_TRANSFER = "Virement bancaire"
    CREDIT_CARD = "Carte de crédit"
    MOBILE_PAYMENT = "Paiement mobile"
    OTHER = "Autre"

class EmployeeType(str, Enum):
    PERMANENT = "Permanent"
    TEMPORAIRE = "Temporaire"
    INTERIMAIRE = "Intérimaire"
    STAGIAIRE = "Stagiaire"
    CONTRACTUEL = "Contractuel"

class TypeContrat(Enum):
    MENSUEL = "Mensuel"
    TRIMESTRIEL = "Trimestriel"
    SEMESTRIEL = "Semestriel"
    ANNUEL = "Annuel"
    PONCTUEL = "Ponctuel"
    FORFAITAIRE = "Forfaitaire"

class FrequenceNettoyage(Enum):
    QUOTIDIEN = "Quotidien"
    HEBDOMADAIRE = "Hebdomadaire"
    BI_HEBDOMADAIRE = "Bi-hebdomadaire"
    MENSUEL = "Mensuel"
    TRIMESTRIEL = "Trimestriel"
    PONCTUEL = "Ponctuel"

class StatutContrat(Enum):
    BROUILLON = "Brouillon"
    EN_ATTENTE = "En attente de signature"
    ACTIF = "Actif"
    SUSPENDU = "Suspendu"
    RESILIE = "Résilié"
    EXPIRE = "Expiré"
    RENOUVELE = "Renouvelé"

class PeriodiciteFacturation(Enum):
    MENSUELLE = "Mensuelle"
    TRIMESTRIELLE = "Trimestrielle"
    SEMESTRIELLE = "Semestrielle"
    ANNUELLE = "Annuelle"
    PONCTUELLE = "Ponctuelle"

class TypeDocumentContrat(Enum):
    CONTRAT = "Contrat simple"
    MARCHE = "Marché public"
    CONVENTION = "Convention"