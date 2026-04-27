import logging

logger = logging.getLogger(__name__)

"""
Service de calcul de paie
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional
from datetime import datetime

class PayslipCalculator:
    """Classe dédiée aux calculs de paie selon la législation algérienne"""
    
    # Taux CNAS standard (employeur + salarié)
    CNAS_PERCENTAGE = Decimal('0.09')  # 9%
    
    # Tranches d'imposition (IRG) pour 2024
    TAX_BRACKETS = [
        {'min': Decimal('0'), 'max': Decimal('18000'), 'rate': Decimal('0')},
        {'min': Decimal('18001'), 'max': Decimal('30000'), 'rate': Decimal('0.20')},
        {'min': Decimal('30001'), 'max': Decimal('50000'), 'rate': Decimal('0.30')},
        {'min': Decimal('50001'), 'max': Decimal('80000'), 'rate': Decimal('0.35')},
        {'min': Decimal('80001'), 'max': Decimal('160000'), 'rate': Decimal('0.40')},
        {'min': Decimal('160001'), 'max': None, 'rate': Decimal('0.45')}
    ]
    
    @staticmethod
    def calculate_proportional_salary(base_salary: Decimal, 
                                     working_days: int, 
                                     actual_days: int) -> Decimal:
        """
        Calcule le salaire proportionnel aux jours travaillés
        """
        if working_days <= 0:
            return Decimal('0')
        
        daily_rate = base_salary / Decimal(str(working_days))
        proportional = daily_rate * Decimal(str(actual_days))
        return proportional.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_overtime_amount(hours: Decimal, 
                                 base_hourly_rate: Decimal,
                                 multiplier: Decimal = Decimal('1.5')) -> Decimal:
        """
        Calcule le montant des heures supplémentaires
        Taux majoré de 50% par défaut
        """
        return (hours * base_hourly_rate * multiplier).quantize(Decimal('0.01'))
    
    @staticmethod
    def calculate_cnass_contribution(taxable_amount: Decimal) -> Decimal:
        """
        Calcule la cotisation CNAS (9% du salaire brut)
        """
        return (taxable_amount * PayslipCalculator.CNAS_PERCENTAGE).quantize(Decimal('0.01'))
    
    @staticmethod
    def calculate_income_tax(taxable_amount: Decimal) -> Decimal:
        """
        Calcule l'impôt sur le revenu selon les tranches algériennes
        """
        tax = Decimal('0')
        remaining_income = taxable_amount
        
        for bracket in PayslipCalculator.TAX_BRACKETS:
            if remaining_income <= Decimal('0'):
                break
            
            bracket_max = bracket['max'] if bracket['max'] else Decimal('999999999')
            bracket_min = bracket['min']
            
            if remaining_income > bracket_min:
                taxable_in_bracket = min(remaining_income - bracket_min, 
                                        bracket_max - bracket_min)
                if taxable_in_bracket > Decimal('0'):
                    tax += taxable_in_bracket * bracket['rate']
        
        return tax.quantize(Decimal('0.01'))
    
    @staticmethod
    def calculate_all_deductions(gross_salary: Decimal, 
                                advance: Decimal = Decimal('0'),
                                other_deductions: Decimal = Decimal('0')) -> Dict[str, Decimal]:
        """
        Calcule toutes les déductions automatiquement
        """
        cnass = PayslipCalculator.calculate_cnass_contribution(gross_salary)
        tax = PayslipCalculator.calculate_income_tax(gross_salary)
        
        total_deductions = cnass + tax + advance + other_deductions
        
        return {
            'cnass': cnass,
            'tax': tax,
            'advance': advance,
            'other_deductions': other_deductions,
            'total': total_deductions
        }
    
    @staticmethod
    def calculate_net_salary(gross_salary: Decimal, 
                           deductions: Dict[str, Decimal]) -> Decimal:
        """
        Calcule le salaire net
        """
        return (gross_salary - deductions['total']).quantize(Decimal('0.01'))
    
    @staticmethod
    def calculate_base_hourly_rate(monthly_salary: Decimal, 
                                  monthly_hours: Decimal = Decimal('173.33')) -> Decimal:
        """
        Calcule le taux horaire de base (173.33 heures/mois standard)
        """
        return (monthly_salary / monthly_hours).quantize(Decimal('0.01'))
    
    @staticmethod
    def validate_payslip_totals(payslip_data: Dict[str, Any]) -> bool:
        """
        Valide la cohérence des totaux d'une fiche de paie
        """
        try:
            gross = payslip_data.get('gross_salary', Decimal('0'))
            total_deductions = payslip_data.get('total_deductions', Decimal('0'))
            net = payslip_data.get('net_salary', Decimal('0'))
            
            calculated_net = gross - total_deductions
            
            # Tolérance de 0.01 DA pour les arrondis
            return abs(net - calculated_net) <= Decimal('0.01')
        except Exception:
            return False
