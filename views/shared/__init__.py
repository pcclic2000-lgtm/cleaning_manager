# views/shared/__init__.py
"""Module shared — exports publics."""
import logging

logger = logging.getLogger(__name__)

from views.shared.bank_view import BankView, BankAccountDialog
from views.shared.expenses_view import ExpensesView

__all__ = ['BankView', 'BankAccountDialog', 'ExpensesView']
