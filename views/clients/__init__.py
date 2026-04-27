# views/clients/__init__.py
"""Module clients — exports publics."""
import logging

logger = logging.getLogger(__name__)

from views.clients.clients_view import ClientsView, ClientDialog

__all__ = ['ClientsView', 'ClientDialog']
