# models/payslip.py
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.base import Base
from datetime import date
from decimal import Decimal, ROUND_HALF_UP


class Payslip(Base):
    """Modèle pour les fiches de paie des employés"""
    __tablename__ = "payslips"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    period_month = Column(Integer, nullable=False)  # Mois (1-12)
    period_year = Column(Integer, nullable=False)  # Année
    date_generation = Column(Date, server_default=func.current_date())
    
    # Salaire de base - avec valeur par défaut
    base_salary = Column(DECIMAL(12, 2), nullable=False, default=Decimal('0.00'))
    working_days = Column(Integer, default=22)  # Jours travaillés dans le mois
    actual_worked_days = Column(Integer, default=22)  # Jours réellement travaillés
    daily_rate = Column(DECIMAL(10, 2), nullable=False, default=Decimal('0.00'))  # Taux journalier
    
    # Absences et congés - avec valeurs par défaut
    absent_days = Column(Integer, default=0)
    leave_days = Column(Integer, default=0)
    leave_with_pay = Column(Integer, default=0)
    leave_without_pay = Column(Integer, default=0)
    sick_days = Column(Integer, default=0)
    
    # Heures supplémentaires - avec valeurs par défaut
    overtime_hours = Column(Integer, default=0)
    overtime_rate = Column(DECIMAL(10, 2), default=Decimal('0.00'))
    overtime_amount = Column(DECIMAL(12, 2), default=Decimal('0.00'))
    
    # Prime et bonus - avec valeurs par défaut
    bonus_amount = Column(DECIMAL(12, 2), default=Decimal('0.00'))
    bonus_description = Column(String(255))
    other_allowances = Column(DECIMAL(12, 2), default=Decimal('0.00'))
    
    # Déductions - avec valeurs par défaut
    cnass_deduction = Column(DECIMAL(12, 2), default=Decimal('0.00'))  # CNAS
    tax_deduction = Column(DECIMAL(12, 2), default=Decimal('0.00'))    # Impôt
    advance_deduction = Column(DECIMAL(12, 2), default=Decimal('0.00')) # Avance
    other_deductions = Column(DECIMAL(12, 2), default=Decimal('0.00'))
    deduction_description = Column(Text)
    
    # Totaux - avec valeurs par défaut
    gross_salary = Column(DECIMAL(12, 2), nullable=False, default=Decimal('0.00'))
    total_deductions = Column(DECIMAL(12, 2), nullable=False, default=Decimal('0.00'))
    net_salary = Column(DECIMAL(12, 2), nullable=False, default=Decimal('0.00'))
    
    # Statut et paiement
    status = Column(String(50), default="GÉNÉRÉE")  # GÉNÉRÉE, VALIDÉE, PAYÉE
    payment_date = Column(Date)
    payment_method = Column(String(50))
    payment_reference = Column(String(100))
    
    # Relations
    employee = relationship("Employee", backref="payslips")
    
    # Notes
    notes = Column(Text)
    generated_by = Column(String(100))
    
    def __repr__(self):
        return f"<Payslip {self.period_month:02d}/{self.period_year} - {self.employee.nom_complet if self.employee else 'N/A'}>"
    
    @property
    def period_str(self):
        return f"{self.period_month:02d}/{self.period_year}"
    
    def calculate_totals(self):
        """Calcule les totaux automatiquement avec gestion des valeurs None"""
        try:
            # S'assurer que toutes les valeurs Decimal ne sont pas None
            base_salary = self._ensure_decimal(self.base_salary)
            overtime_amount = self._ensure_decimal(self.overtime_amount)
            bonus_amount = self._ensure_decimal(self.bonus_amount)
            other_allowances = self._ensure_decimal(self.other_allowances)
            cnass_deduction = self._ensure_decimal(self.cnass_deduction)
            tax_deduction = self._ensure_decimal(self.tax_deduction)
            advance_deduction = self._ensure_decimal(self.advance_deduction)
            other_deductions = self._ensure_decimal(self.other_deductions)
            
            # S'assurer que les valeurs entières ne sont pas None
            working_days = self.working_days if self.working_days is not None else 22
            actual_worked_days = self.actual_worked_days if self.actual_worked_days is not None else working_days
            leave_without_pay = self.leave_without_pay if self.leave_without_pay is not None else 0
            
            # Taux journalier (ne pas diviser par zéro)
            if working_days > 0:
                daily_rate = base_salary / Decimal(str(working_days))
            else:
                daily_rate = Decimal('0.00')
            
            self.daily_rate = daily_rate.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Salaire de base proportionnel
            base_proportional = daily_rate * Decimal(str(actual_worked_days))
            
            # Congés sans solde
            unpaid_leave_deduction = daily_rate * Decimal(str(leave_without_pay))
            
            # Salaire brut
            gross = (
                base_proportional
                + overtime_amount
                + bonus_amount
                + other_allowances
                - unpaid_leave_deduction
            )
            
            # Total déductions
            total_deductions = (
                cnass_deduction
                + tax_deduction
                + advance_deduction
                + other_deductions
            )
            
            # Salaire net
            net = gross - total_deductions
            
            # Mettre à jour les attributs
            self.gross_salary = gross.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.total_deductions = total_deductions.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.net_salary = net.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            return self.net_salary
            
        except Exception as e:
            print(f"Erreur dans calculate_totals: {e}")
            # Valeurs par défaut en cas d'erreur
            self.gross_salary = Decimal('0.00')
            self.total_deductions = Decimal('0.00')
            self.net_salary = Decimal('0.00')
            return Decimal('0.00')
    
    def _ensure_decimal(self, value):
        """S'assure qu'une valeur est un Decimal, pas None"""
        if value is None:
            return Decimal('0.00')
        elif isinstance(value, Decimal):
            return value
        else:
            try:
                return Decimal(str(value))
            except:
                return Decimal('0.00')
    
    def calculate_cnass_auto(self):
        """Calculer automatiquement la CNAS (9% du salaire brut)"""
        try:
            gross = self._ensure_decimal(self.gross_salary)
            cnass = gross * Decimal('0.09')  # 9%
            self.cnass_deduction = cnass.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.calculate_totals()  # Recalculer les totaux
            return self.cnass_deduction
        except Exception:
            self.cnass_deduction = Decimal('0.00')
            return Decimal('0.00')
