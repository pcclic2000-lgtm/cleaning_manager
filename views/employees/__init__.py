# views/employees/__init__.py
"""Module employees — exports publics."""
import logging

logger = logging.getLogger(__name__)

from views.employees.employee_arret_dialog import EmployeeArretDialog
from views.employees.employee_dialog import EmployeeDialog
from views.employees.employee_view import EmployeeView

__all__ = ['EmployeeArretDialog', 'EmployeeDialog', 'EmployeeView']
