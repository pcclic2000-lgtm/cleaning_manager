# models/employee.py - VERSION CORRIGÉE
from sqlalchemy import Column, Integer, String, Date, Boolean, func, Float, Numeric
from sqlalchemy.orm import relationship
from database.base import Base
from datetime import datetime, date



class Employee(Base):
    """Modèle pour les employés"""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    code_employe = Column(String(50), unique=True, nullable=False)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    poste = Column(String(100), default="Employé")

    adresse = Column(String(255))
    telephone = Column(String(20), nullable=False)
    email = Column(String(100))

    date_naissance = Column(Date)
    situation_familiale = Column(String(50), default="Célibataire")
    genre = Column(String, nullable=True)
    numero_secu = Column(String(50))

    date_embauche = Column(Date, nullable=False)
    salaire = Column(Numeric(12, 2), default=0.0)

    date_arret = Column(Date, nullable=True)
    raison_arret = Column(String(200), nullable=True)

    date_creation = Column(Date, server_default=func.current_date())
    est_actif = Column(Boolean, default=True)

    # ============ RELATIONS CORRIGÉES ============
    taches = relationship("Tache", back_populates="employee", cascade="all, delete-orphan")
    affectations = relationship("Affectation", back_populates="employee", cascade="all, delete-orphan")
    # =============================================

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    @property
    def est_inactif(self):
        return not self.est_actif

    @property
    def duree_emploi(self):
        if not self.date_embauche:
            return 0

        date_fin = self.date_arret if self.date_arret else date.today()
        return (date_fin - self.date_embauche).days

    @property
    def duree_emploi_annees(self):
        jours = self.duree_emploi
        return jours / 365.25

    def peut_etre_affecte(self):
        return self.est_actif and not self.date_arret

    def __repr__(self):
        status = "Actif" if self.est_actif else "Inactif"
        return f"<Employee {self.code_employe}: {self.nom_complet} ({status})>"


def generer_matricule(session, nom, prenom, max_retries=20):
    """Génère un matricule unique pour un employé.

    Évite les collisions en vérifiant l'unicité avant de retourner le matricule.
    - Le format est EMP-YYYYMM-XXXX
    - Le suffixe est calculé à partir de l'ensemble des matricules existants
      pour le mois courant.
    - En cas de collision (concurrence), on réessaye jusqu'à max_retries.

    Retourne:
        str: matricule unique.

    Lève:
        ValueError: si aucun matricule unique n'a pu être généré.
    """
    date_part = datetime.now().strftime("%Y%m")
    prefix = f"EMP-{date_part}-"

    for attempt in range(1, max_retries + 1):
        # Obtenir la liste des séquences déjà utilisées pour le mois
        codes = session.query(Employee.code_employe).filter(
            Employee.code_employe.like(f"{prefix}%")
        ).all()

        used_numbers = set()
        for (full_code,) in codes:
            try:
                used_numbers.add(int(full_code.split("-")[-1]))
            except Exception:
                continue

        # Séquence candidate le plus petit disponible
        candidate_number = 1
        while candidate_number in used_numbers:
            candidate_number += 1

        # En cas de réessai complet, on incrémente pour éviter blocage
        candidate_number += (attempt - 1)

        candidate = f"{prefix}{candidate_number:04d}"

        exists = session.query(Employee).filter_by(code_employe=candidate).first()
        if not exists:
            return candidate

        # Si collision détectée, continuer/retry

    raise ValueError(
        f"Impossible de générer un matricule unique après {max_retries} tentatives."
    )
