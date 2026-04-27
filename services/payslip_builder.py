import logging

logger = logging.getLogger(__name__)

"""
Pattern Builder pour la création de fiches de paie
"""
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from models.payslip import Payslip
from models.employee import Employee
from database.db import SessionLocal, get_session


class PayslipBuilder:
    """Builder pour créer des fiches de paie étape par étape"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Réinitialise le builder"""
        self._payslip_data = {
            'components': {
                'base_salary': Decimal('0'),
                'overtime_hours': Decimal('0'),
                'overtime_rate': Decimal('0'),
                'bonus': Decimal('0'),
                'other_allowances': Decimal('0')
            },
            'deductions': {
                'cnass': Decimal('0'),
                'tax': Decimal('0'),
                'advance': Decimal('0'),
                'other_deductions': Decimal('0')
            },
            'period': {
                'month': datetime.now().month,
                'year': datetime.now().year
            },
            'working_days': {
                'total': 22,
                'actual': 22,
                'absent': 0
            },
            'status': 'BROUILLON'
        }
        return self
    
    def set_employee(self, employee_id: int) -> 'PayslipBuilder':
        """Définit l'employé"""
        with get_session() as session:
            employee = session.query(Employee).filter(Employee.id == employee_id).first()
            if employee:
                self._payslip_data['employee_id'] = employee_id
            # Récupérer le salaire de base de l'employé
            if employee.salaire:
                self._payslip_data['components']['base_salary'] = employee.salaire
            return self
    
    def set_period(self, month: int, year: int) -> 'PayslipBuilder':
        """Définit la période de paie"""
        if 1 <= month <= 12:
            self._payslip_data['period']['month'] = month
            self._payslip_data['period']['year'] = year
        return self
    
    def set_working_days(self, total_days: int, actual_days: int, absent_days: int = 0) -> 'PayslipBuilder':
        """Définit les jours de travail"""
        if 1 <= total_days <= 31 and 0 <= actual_days <= total_days:
            self._payslip_data['working_days']['total'] = total_days
            self._payslip_data['working_days']['actual'] = actual_days
            self._payslip_data['working_days']['absent'] = absent_days
        return self
    
    def set_base_salary(self, salary: Decimal) -> 'PayslipBuilder':
        """Définit le salaire de base"""
        if salary >= Decimal('0'):
            self._payslip_data['components']['base_salary'] = salary
        return self
    
    def set_overtime(self, hours: Decimal, rate: Optional[Decimal] = None) -> 'PayslipBuilder':
        """Définit les heures supplémentaires"""
        from services.payslip_calculator import PayslipCalculator
        
        self._payslip_data['components']['overtime_hours'] = hours
        
        if rate:
            self._payslip_data['components']['overtime_rate'] = rate
        elif self._payslip_data['components']['base_salary'] > Decimal('0'):
            # Calculer le taux horaire automatiquement
            hourly_rate = PayslipCalculator.calculate_base_hourly_rate(
                self._payslip_data['components']['base_salary']
            )
            self._payslip_data['components']['overtime_rate'] = hourly_rate * Decimal('1.5')
        
        return self
    
    def set_bonus(self, amount: Decimal, description: str = "") -> 'PayslipBuilder':
        """Définit les bonus"""
        if amount >= Decimal('0'):
            self._payslip_data['components']['bonus'] = amount
            self._payslip_data['bonus_description'] = description
        return self
    
    def set_allowances(self, amount: Decimal) -> 'PayslipBuilder':
        """Définit les allocations"""
        if amount >= Decimal('0'):
            self._payslip_data['components']['other_allowances'] = amount
        return self
    
    def set_deductions(self, cnass: Decimal = Decimal('0'),
                      tax: Decimal = Decimal('0'),
                      advance: Decimal = Decimal('0'),
                      other: Decimal = Decimal('0')) -> 'PayslipBuilder':
        """Définit les déductions"""
        self._payslip_data['deductions']['cnass'] = cnass if cnass >= Decimal('0') else Decimal('0')
        self._payslip_data['deductions']['tax'] = tax if tax >= Decimal('0') else Decimal('0')
        self._payslip_data['deductions']['advance'] = advance if advance >= Decimal('0') else Decimal('0')
        self._payslip_data['deductions']['other_deductions'] = other if other >= Decimal('0') else Decimal('0')
        return self
    
    def set_status(self, status: str) -> 'PayslipBuilder':
        """Définit le statut"""
        valid_statuses = ['BROUILLON', 'VALIDÉE', 'PAYÉE', 'ANNULÉE']
        if status in valid_statuses:
            self._payslip_data['status'] = status
        return self
    
    def calculate_totals(self) -> 'PayslipBuilder':
        """Calcule tous les totaux automatiquement"""
        from services.payslip_calculator import PayslipCalculator
        
        base_salary = self._payslip_data['components']['base_salary']
        working_days = self._payslip_data['working_days']
        
        # Salaire proportionnel
        proportional_salary = PayslipCalculator.calculate_proportional_salary(
            base_salary, working_days['total'], working_days['actual']
        )
        
        # Heures supplémentaires
        overtime_amount = (self._payslip_data['components']['overtime_hours'] * 
                         self._payslip_data['components']['overtime_rate'])
        
        # Salaire brut
        gross_salary = (proportional_salary + 
                       overtime_amount +
                       self._payslip_data['components']['bonus'] +
                       self._payslip_data['components']['other_allowances'])
        
        # Calcul des déductions automatiques si non spécifiées
        if self._payslip_data['deductions']['cnass'] == Decimal('0'):
            self._payslip_data['deductions']['cnass'] = PayslipCalculator.calculate_cnass_contribution(gross_salary)
        
        if self._payslip_data['deductions']['tax'] == Decimal('0'):
            self._payslip_data['deductions']['tax'] = PayslipCalculator.calculate_income_tax(gross_salary)
        
        # Total des déductions
        total_deductions = (self._payslip_data['deductions']['cnass'] +
                          self._payslip_data['deductions']['tax'] +
                          self._payslip_data['deductions']['advance'] +
                          self._payslip_data['deductions']['other_deductions'])
        
        # Salaire net
        net_salary = gross_salary - total_deductions
        
        # Stocker les totaux
        self._payslip_data['gross_salary'] = gross_salary
        self._payslip_data['total_deductions'] = total_deductions
        self._payslip_data['net_salary'] = net_salary
        
        return self
    
    def build(self) -> Payslip:
        """Construit et retourne l'objet Payslip"""
        # Validation
        self._validate()
        
        # Calcul des totaux si non fait
        if 'gross_salary' not in self._payslip_data:
            self.calculate_totals()
        
        # Création de l'objet Payslip
        payslip = Payslip()
        
        # Assignation des valeurs
        payslip.employee_id = self._payslip_data.get('employee_id')
        payslip.period_month = self._payslip_data['period']['month']
        payslip.period_year = self._payslip_data['period']['year']
        
        # Composantes
        payslip.base_salary = self._payslip_data['components']['base_salary']
        payslip.working_days = self._payslip_data['working_days']['total']
        payslip.actual_worked_days = self._payslip_data['working_days']['actual']
        payslip.overtime_hours = self._payslip_data['components']['overtime_hours']
        payslip.overtime_rate = self._payslip_data['components']['overtime_rate']
        payslip.overtime_amount = self._payslip_data['components']['overtime_hours'] * \
                                  self._payslip_data['components']['overtime_rate']
        payslip.bonus_amount = self._payslip_data['components']['bonus']
        payslip.other_allowances = self._payslip_data['components']['other_allowances']
        
        # Déductions
        payslip.cnass_deduction = self._payslip_data['deductions']['cnass']
        payslip.tax_deduction = self._payslip_data['deductions']['tax']
        payslip.advance_deduction = self._payslip_data['deductions']['advance']
        payslip.other_deductions = self._payslip_data['deductions']['other_deductions']
        
        # Totaux
        payslip.gross_salary = self._payslip_data['gross_salary']
        payslip.total_deductions = self._payslip_data['total_deductions']
        payslip.net_salary = self._payslip_data['net_salary']
        
        # Statut
        payslip.status = self._payslip_data['status']
        payslip.date_generation = datetime.now()
        
        return payslip
    
    def _validate(self):
        """Validation interne des données"""
        if 'employee_id' not in self._payslip_data:
            raise ValueError("L'ID de l'employé est requis")
        
        if self._payslip_data['components']['base_salary'] <= Decimal('0'):
            raise ValueError("Le salaire de base doit être positif")
        
        if self._payslip_data['working_days']['actual'] > self._payslip_data['working_days']['total']:
            raise ValueError("Les jours travaillés ne peuvent pas dépasser les jours ouvrés")
    
    def get_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des données"""
        return {
            'gross_salary': self._payslip_data.get('gross_salary', Decimal('0')),
            'total_deductions': self._payslip_data.get('total_deductions', Decimal('0')),
            'net_salary': self._payslip_data.get('net_salary', Decimal('0')),
            'status': self._payslip_data.get('status', 'BROUILLON')
        }
