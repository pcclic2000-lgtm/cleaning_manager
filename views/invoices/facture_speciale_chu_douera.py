# views/facture_speciale_chu_douera.py
"""
Dialogue pour la facture spéciale CHU Douera
Réutilise la classe InvoiceDialog existante avec des adaptations
"""

from views.invoices.invoice_dialog import InvoiceDialog


class FactureCHUDialog(InvoiceDialog):
    """Dialogue pour la facture spéciale CHU Douera"""
    
    def __init__(self, contrat_id=None, parent=None):
        # Récupérer le client_id à partir du contrat
        from database.db import SessionLocal, get_session
        from models.contrat import Contrat
        
        client_id = None
        if contrat_id:
            with get_session() as session:
                contrat = session.query(Contrat).filter(Contrat.id == contrat_id).first()
                if contrat and contrat.client:
                    client_id = contrat.client.id
        
                # Initialiser avec le client_id et contrat_id
                super().__init__(client_id=client_id, contrat_id=contrat_id, parent=parent)
        
                # Modifier le titre pour indiquer qu'il s'agit de CHU Douera
                self.setWindowTitle("🏥 Facture CHU Douera")
