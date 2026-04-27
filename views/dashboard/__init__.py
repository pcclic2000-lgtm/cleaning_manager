# views/dashboard/__init__.py
"""Module dashboard — exports publics."""
import logging

logger = logging.getLogger(__name__)

from views.dashboard.dashboard_view import DashboardView

__all__ = ['DashboardView']
