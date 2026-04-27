# views/payroll/__init__.py
"""Module payroll — exports publics."""
import logging

logger = logging.getLogger(__name__)

from views.payroll.payslip_view import ModernPayslipView
from views.payroll.payslip_dialog import ModernPayslipDialog
from views.payroll.paye_globale_view import PayeGlobaleView
from views.payroll.paye_globale_dialog import PayeGlobaleDialog
from views.payroll.cotisation_view import CotisationView

__all__ = [
    'ModernPayslipView', 'ModernPayslipDialog',
    'PayeGlobaleView', 'PayeGlobaleDialog', 'CotisationView',
]
