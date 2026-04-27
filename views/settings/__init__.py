# views/settings/__init__.py
"""Module settings — exports publics."""
import logging

logger = logging.getLogger(__name__)

from views.settings.settings_view import SettingsView
from views.settings.company_view import CompanyInfoView, CompanySettingsView

__all__ = ['SettingsView', 'CompanyInfoView', 'CompanySettingsView']
