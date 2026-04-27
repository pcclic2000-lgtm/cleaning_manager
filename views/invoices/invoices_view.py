# views/invoices/invoices_view.py
"""Vue principale de la liste et gestion des factures."""
import logging
import os
import datetime
from decimal import Decimal

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QLineEdit, QLabel, QFormLayout, QComboBox,
    QTextEdit, QDoubleSpinBox, QHeaderView, QTabWidget,
    QMenu, QAbstractItemView, QDateEdit, QGroupBox,
    QFileDialog, QTextBrowser, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QPoint, QUrl, QTimer
from PyQt6.QtGui import QAction, QTextDocument, QFont
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from database.db import SessionLocal, get_session
from models.client import Client
from models.invoice import Invoice, InvoiceItem, InvoicePayment
from models.enums import InvoiceStatus, PaymentMethod
from models.company import CompanyInfo, CompanySettings
from models.contrat import Contrat
from views.invoices.invoice_dialog import InvoiceDialog

logger = logging.getLogger(__name__)

class InvoicesView(QWidget):
    """Vue principale pour la gestion des factures"""

    def __init__(self, client_id=None):
        super().__init__()
        self.client_id = client_id
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Titre
        title = QLabel("🧾 GESTION DES FACTURES")
        title.setStyleSheet("""
            font-size: 22px; font-weight: bold; color: #2c3e50;
            padding: 15px;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-radius: 10px; border-left: 5px solid #3498db;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Barre d'outils
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # ===== BOUTON NOUVELLE FACTURE AVEC MENU =====
        self.btn_add = QPushButton("➕ Nouvelle facture ▼")
        self.btn_add.setStyleSheet("""
            QPushButton { 
                padding:10px 20px; 
                border:none; 
                border-radius:6px; 
                font-weight:bold;
                font-size:13px; 
                min-height:40px; 
                background:#27ae60; 
                color:white; 
            }
            QPushButton:hover { 
                background:#219653; 
            }
            QPushButton:pressed { 
                background:#1e8449; 
            }
            QPushButton::menu-indicator { 
                image: none; 
                padding-right: 5px; 
            }
        """)
        
        # Créer le menu
        self.invoice_menu = QMenu()
        self.invoice_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
            QMenu::item:disabled {
                color: #bdc3c7;
            }
        """)
        
        # Actions du menu
        self.act_standard = QAction("📄 Facture Standard", self)
        self.act_standard.triggered.connect(lambda: self.add_invoice("standard"))
        self.invoice_menu.addAction(self.act_standard)
        
        self.act_douera = QAction("🏥 Facture CHU Douera", self)
        self.act_douera.triggered.connect(lambda: self.add_invoice("douera"))
        self.invoice_menu.addAction(self.act_douera)
        
        self.act_beni = QAction("🏥 Facture CHU Beni Messous", self)
        self.act_beni.triggered.connect(lambda: self.add_invoice("beni_messous"))
        self.invoice_menu.addAction(self.act_beni)
        
        self.btn_add.setMenu(self.invoice_menu)
        # ==============================================

        # Bouton Modifier
        self.btn_edit = QPushButton("✏️ Modifier")
        self.btn_edit.setStyleSheet("""
            QPushButton { 
                padding:10px 20px; 
                border:none; 
                border-radius:6px; 
                font-weight:bold;
                font-size:13px; 
                min-height:40px; 
                background:#3498db; 
                color:white; 
            }
            QPushButton:hover { 
                background:#2980b9; 
            }
            QPushButton:pressed { 
                background:#2471a3; 
            }
        """)
        
        # Bouton Supprimer
        self.btn_delete = QPushButton("🗑️ Supprimer")
        self.btn_delete.setStyleSheet("""
            QPushButton { 
                padding:10px 20px; 
                border:none; 
                border-radius:6px; 
                font-weight:bold;
                font-size:13px; 
                min-height:40px; 
                background:#e74c3c; 
                color:white; 
            }
            QPushButton:hover { 
                background:#c0392b; 
            }
            QPushButton:pressed { 
                background:#a93226; 
            }
        """)
        
        # Bouton Aperçu
        self.btn_preview = QPushButton("👁️ Aperçu")
        self.btn_preview.setStyleSheet("""
            QPushButton { 
                padding:10px 20px; 
                border:none; 
                border-radius:6px; 
                font-weight:bold;
                font-size:13px; 
                min-height:40px; 
                background:#f39c12; 
                color:white; 
            }
            QPushButton:hover { 
                background:#d35400; 
            }
            QPushButton:pressed { 
                background:#ba4a00; 
            }
        """)
        
        # Bouton Exporter PDF
        self.btn_export = QPushButton("📄 Exporter PDF")
        self.btn_export.setStyleSheet("""
            QPushButton { 
                padding:10px 20px; 
                border:none; 
                border-radius:6px; 
                font-weight:bold;
                font-size:13px; 
                min-height:40px; 
                background:#9b59b6; 
                color:white; 
            }
            QPushButton:hover { 
                background:#8e44ad; 
            }
            QPushButton:pressed { 
                background:#7d3c98; 
            }
        """)
        
        # Bouton Actualiser
        self.btn_refresh = QPushButton("🔄 Actualiser")
        self.btn_refresh.setStyleSheet("""
            QPushButton { 
                padding:10px 20px; 
                border:none; 
                border-radius:6px; 
                font-weight:bold;
                font-size:13px; 
                min-height:40px; 
                background:#95a5a6; 
                color:white; 
            }
            QPushButton:hover { 
                background:#7f8c8d; 
            }
            QPushButton:pressed { 
                background:#707b7c; 
            }
        """)

        # Connexions des boutons
        self.btn_edit.clicked.connect(self.edit_selected_invoice)
        self.btn_delete.clicked.connect(self.delete_selected_invoice)
        self.btn_preview.clicked.connect(self.preview_selected_invoice)
        self.btn_export.clicked.connect(self.export_selected_invoice_pdf)
        self.btn_refresh.clicked.connect(self.load_data)

        # Ajout des boutons à la barre d'outils
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        toolbar.addWidget(self.btn_preview)
        toolbar.addWidget(self.btn_export)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_refresh)
        
        layout.addLayout(toolbar)

        # Barre de recherche et filtres
        filter_layout = QHBoxLayout()
        
        # Champ de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher par numéro, client...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        
        # Filtre par statut
        self.filter_status = QComboBox()
        self.filter_status.addItems(["Tous les statuts", "Brouillon", "Envoyée", "Payée", "En retard"])
        self.filter_status.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 13px;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #2c3e50;
                width: 0;
                height: 0;
                margin-right: 10px;
            }
        """)
        self.filter_status.currentTextChanged.connect(self.load_data)
        
        filter_layout.addWidget(self.search_input, 1)
        filter_layout.addWidget(QLabel("Statut:"))
        filter_layout.addWidget(self.filter_status)
        
        layout.addLayout(filter_layout)

        # Table des factures
        self.table = QTableWidget()
        self.table.setColumnCount(10)  # Augmenté à 10 pour ajouter le type de facture
        self.table.setHorizontalHeaderLabels([
            "ID", "N° Facture", "Type", "Client", "Date", "Échéance",
            "Total TTC", "Payé", "Reste", "Statut"
        ])
        self.table.setColumnHidden(0, True)  # Cacher l'ID

        # Style de la table
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background: white;
                gridline-color: #dee2e6;
                selection-background-color: #d4edda;
                selection-color: #155724;
            }
            QHeaderView::section {
                background: #34495e;
                color: white;
                padding: 12px 8px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #f8f9fa;
            }
            QTableWidget::item:selected {
                background: #d4edda;
                color: #155724;
            }
            QTableWidget::item:hover {
                background: #f1f9ff;
            }
        """)

        # Configuration des colonnes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # N° Facture
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Client
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Échéance
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Total
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Payé
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Reste
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Statut

        # Largeurs spécifiques
        self.table.setColumnWidth(1, 120)  # N° Facture
        self.table.setColumnWidth(2, 100)  # Type
        self.table.setColumnWidth(4, 100)  # Date
        self.table.setColumnWidth(5, 100)  # Échéance
        self.table.setColumnWidth(6, 120)  # Total
        self.table.setColumnWidth(7, 100)  # Payé
        self.table.setColumnWidth(8, 100)  # Reste
        self.table.setColumnWidth(9, 100)  # Statut

        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Double-clic pour modifier
        self.table.doubleClicked.connect(self.on_table_double_click)

        # Menu contextuel
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.table)

        # Barre de statut avec résumé
        status_layout = QHBoxLayout()
        
        self.total_invoices_label = QLabel("Total: 0 facture(s)")
        self.total_invoices_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                padding: 8px;
                background: #ecf0f1;
                border-radius: 4px;
            }
        """)
        
        self.total_amount_label = QLabel("Montant total: 0 DA")
        self.total_amount_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                font-weight: bold;
                padding: 8px;
                background: #e8f8f5;
                border-radius: 4px;
            }
        """)
        
        self.paid_amount_label = QLabel("Payé: 0 DA")
        self.paid_amount_label.setStyleSheet("""
            QLabel {
                color: #2980b9;
                font-weight: bold;
                padding: 8px;
                background: #ebf5fb;
                border-radius: 4px;
            }
        """)
        
        self.due_amount_label = QLabel("Dû: 0 DA")
        self.due_amount_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-weight: bold;
                padding: 8px;
                background: #fdedec;
                border-radius: 4px;
            }
        """)
        
        status_layout.addWidget(self.total_invoices_label)
        status_layout.addWidget(self.total_amount_label)
        status_layout.addWidget(self.paid_amount_label)
        status_layout.addWidget(self.due_amount_label)
        status_layout.addStretch()
        
        layout.addLayout(status_layout)

        self.setLayout(layout)

    def load_data(self):
        try:
            with get_session() as session:
                query = session.query(Invoice).join(Client)
                if self.client_id:
                    query = query.filter(Invoice.client_id == self.client_id)

                # Filtre par statut
                status_filter = self.filter_status.currentText()
                if status_filter == "Brouillon":
                    query = query.filter(Invoice.status == InvoiceStatus.DRAFT)
                elif status_filter == "Envoyée":
                    query = query.filter(Invoice.status == InvoiceStatus.SENT)
                elif status_filter == "Payée":
                    query = query.filter(Invoice.status == InvoiceStatus.PAID)
                elif status_filter == "En retard":
                    query = query.filter(Invoice.status == InvoiceStatus.OVERDUE)

                invoices = query.order_by(Invoice.date.desc()).all()
                self.table.setRowCount(len(invoices))

                for row, invoice in enumerate(invoices):
                    # Col 0 : ID (caché)
                    self.table.setItem(row, 0, QTableWidgetItem(str(invoice.id)))

                    # Col 1 : N° Facture
                    self.table.setItem(row, 1, QTableWidgetItem(invoice.invoice_number or ""))

                    # Col 2 : Type (via contrat ou nom client)
                    invoice_type = "Standard"
                    if invoice.contrat_id:
                        try:
                            from models.contrat import Contrat
                            contrat = session.query(Contrat).filter(
                                Contrat.id == invoice.contrat_id
                            ).first()
                            if contrat and contrat.type_facture:
                                t = contrat.type_facture
                                if t == "beni_messous":
                                    invoice_type = "Béni Messous"
                                elif t == "chu_douera":
                                    invoice_type = "CHU Douera"
                                else:
                                    invoice_type = "Standard"
                        except Exception:
                            pass
                    elif invoice.client and invoice.client.raison_sociale:
                        name = invoice.client.raison_sociale.lower()
                        if "beni messous" in name:
                            invoice_type = "Béni Messous"
                        elif "douera" in name:
                            invoice_type = "CHU Douera"
                    self.table.setItem(row, 2, QTableWidgetItem(invoice_type))

                    # Col 3 : Client
                    if invoice.client:
                        client_name = invoice.client.raison_sociale or invoice.client.nom_complet or ""
                        if invoice.client.code_client:
                            client_name += f" ({invoice.client.code_client})"
                    else:
                        client_name = "Client inconnu"
                    self.table.setItem(row, 3, QTableWidgetItem(client_name))

                    # Col 4 : Date
                    date_str = invoice.date.strftime("%d/%m/%Y") if invoice.date else ""
                    self.table.setItem(row, 4, QTableWidgetItem(date_str))

                    # Col 5 : Échéance
                    due_date_str = invoice.due_date.strftime("%d/%m/%Y") if invoice.due_date else ""
                    self.table.setItem(row, 5, QTableWidgetItem(due_date_str))

                    # Col 6 : Total TTC
                    total_item = QTableWidgetItem(f"{(invoice.total_amount or 0):,.2f} DA")
                    total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 6, total_item)

                    # Col 7 : Payé
                    paid_item = QTableWidgetItem(f"{(invoice.amount_paid or 0):,.2f} DA")
                    paid_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 7, paid_item)

                    # Col 8 : Reste (balance_due)
                    balance = float(invoice.balance_due or 0) or (
                        float(invoice.total_amount or 0) - float(invoice.amount_paid or 0)
                    )
                    balance_item = QTableWidgetItem(f"{balance:,.2f} DA")
                    balance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    balance_item.setForeground(
                        Qt.GlobalColor.darkRed if balance > 0 else Qt.GlobalColor.darkGreen
                    )
                    self.table.setItem(row, 8, balance_item)

                    # Col 9 : Statut
                    status_text = invoice.status.value if invoice.status else "Inconnu"
                    status_item = QTableWidgetItem(status_text)
                    if invoice.status == InvoiceStatus.PAID:
                        status_item.setForeground(Qt.GlobalColor.darkGreen)
                    elif invoice.status == InvoiceStatus.PENDING:
                        status_item.setForeground(Qt.GlobalColor.darkRed)
                    elif invoice.status == InvoiceStatus.DRAFT:
                        status_item.setForeground(Qt.GlobalColor.darkGray)
                    self.table.setItem(row, 9, status_item)

            # ✅ Appel au résumé APRÈS le chargement
            self.update_status_summary()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur de chargement: {str(e)}")
            import traceback
            traceback.print_exc()

    def get_selected_invoice_id(self):
        selected = self.table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        id_item = self.table.item(row, 0)
        try:
            return int(id_item.text())
        except Exception:
            return None

    def add_invoice(self, invoice_type="standard"):
        """Ajouter une nouvelle facture selon le type"""
        client_id = self.client_id  # Si un client est déjà filtré
        
        if invoice_type == "beni_messous":
            from .benimessous_invoice import BeniMessousInvoiceDialog
            dialog = BeniMessousInvoiceDialog(client_id=client_id, parent=self)
            dialog.invoice_saved.connect(self.load_data)
            dialog.exec()
        else:
            # Standard ou Douera (même structure)
            from .invoice_dialog import InvoiceDialog
            dialog = InvoiceDialog(client_id=client_id, parent=self)
            dialog.invoice_saved.connect(self.load_data)
            dialog.exec()

    
    def get_invoice_contrat_id(self, invoice_id):
        """Récupère le contrat_id lié à une facture"""
        try:
            with get_session() as session:
                invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
                return invoice.contrat_id if invoice else None
        except Exception as e:
            logger.error("Erreur récupération contrat_id: %s", e)
            return None


    def get_invoice_type(self, invoice_id):
        """Détermine le type de facture via le contrat lié (type_facture)"""
        try:
            with get_session() as session:
                invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
                if not invoice:
                    return "standard"

                if invoice.contrat_id:
                    contrat = session.query(Contrat).filter(
                        Contrat.id == invoice.contrat_id
                    ).first()
                    if contrat and contrat.type_facture:
                        return contrat.type_facture  # "standard", "beni_messous", "chu_douera"

                if invoice.client and invoice.client.raison_sociale:
                    name = invoice.client.raison_sociale.lower()
                    if "beni messous" in name:
                        return "beni_messous"
                    elif "douera" in name:
                        return "chu_douera"

                return "standard"
        except Exception as e:
            logger.error("Erreur détection type facture: %s", e)
            return "standard"


    def edit_selected_invoice(self):
        invoice_id = self.get_selected_invoice_id()
        if not invoice_id:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une facture à modifier")
            return

        invoice_type = self.get_invoice_type(invoice_id)
        contrat_id = self.get_invoice_contrat_id(invoice_id)
        print(f"📝 Modification facture {invoice_id} — type: {invoice_type} — contrat_id: {contrat_id}")

        if invoice_type == "beni_messous":
            from .benimessous_invoice import BeniMessousInvoiceDialog
            dialog = BeniMessousInvoiceDialog(
                invoice_id=invoice_id,
                contrat_id=contrat_id,
                parent=self
            )
        else:
            dialog = InvoiceDialog(
                invoice_id=invoice_id,
                contrat_id=contrat_id,
                parent=self
            )

        dialog.invoice_saved.connect(self.load_data)
        dialog.exec()

    def delete_selected_invoice(self):
        invoice_id = self.get_selected_invoice_id()
        if not invoice_id:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une facture à supprimer")
            return

        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment supprimer cette facture ?\nCette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            with get_session() as session:
                inv = session.query(Invoice).filter(Invoice.id == invoice_id).first()
                if not inv:
                    QMessageBox.warning(self, "Erreur", "Facture non trouvée")
                    return

                session.delete(inv)
                session.commit()
                QMessageBox.information(self, "Succès", "Facture supprimée avec succès")
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur suppression: {e}")


    def preview_selected_invoice(self):
        invoice_id = self.get_selected_invoice_id()
        if not invoice_id:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une facture à prévisualiser")
            return

        contrat_id = self.get_invoice_contrat_id(invoice_id)
        dialog = InvoiceDialog(
            invoice_id=invoice_id,
            contrat_id=contrat_id,
            parent=self
        )
        try:
            dialog.preview_invoice()
        finally:
            dialog.close()

    def export_selected_invoice_pdf(self):
        invoice_id = self.get_selected_invoice_id()
        if not invoice_id:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une facture à exporter")
            return

        contrat_id = self.get_invoice_contrat_id(invoice_id)
        dialog = InvoiceDialog(
            invoice_id=invoice_id,
            contrat_id=contrat_id,
            parent=self
        )
        try:
            dialog.export_pdf()
        finally:
            dialog.close()

    def show_context_menu(self, pos: QPoint):
        global_pos = self.table.viewport().mapToGlobal(pos)
        idx = self.table.indexAt(pos)

        menu = QMenu()
        
        # ===== SOUS-MENU POUR NOUVELLE FACTURE =====
        add_menu = menu.addMenu("➕ Nouvelle facture")
        
        act_standard = QAction("📄 Facture Standard", self)
        act_standard.triggered.connect(lambda: self.add_invoice("standard"))
        add_menu.addAction(act_standard)
        
        act_douera = QAction("🏥 Facture CHU Douera", self)
        act_douera.triggered.connect(lambda: self.add_invoice("douera"))
        add_menu.addAction(act_douera)
        
        act_beni = QAction("🏥 Facture CHU Beni Messous", self)
        act_beni.triggered.connect(lambda: self.add_invoice("beni_messous"))
        add_menu.addAction(act_beni)
        # ============================================

        if idx.isValid():
            self.table.selectRow(idx.row())

            act_edit = QAction("✏️ Modifier", self)
            act_edit.triggered.connect(self.edit_selected_invoice)
            menu.addAction(act_edit)

            act_delete = QAction("🗑️ Supprimer", self)
            act_delete.triggered.connect(self.delete_selected_invoice)
            menu.addAction(act_delete)

            menu.addSeparator()

            act_preview = QAction("👁️ Aperçu", self)
            act_preview.triggered.connect(self.preview_selected_invoice)
            menu.addAction(act_preview)

            act_export = QAction("📄 Exporter PDF", self)
            act_export.triggered.connect(self.export_selected_invoice_pdf)
            menu.addAction(act_export)
        else:
            act_refresh = QAction("🔄 Actualiser", self)
            act_refresh.triggered.connect(self.load_data)
            menu.addAction(act_refresh)

        menu.exec(global_pos)

    def filter_table(self, text):
        for row in range(self.table.rowCount()):
            visible = False
            for col in [1, 2, 3]:  # N° Facture, Type, Client
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    visible = True
                    break
            self.table.setRowHidden(row, not visible)
        # ✅ Recalculer le résumé sur les lignes visibles uniquement
        self.update_status_summary()
    
    def on_table_double_click(self, index):
        """Gère le double-clic sur une ligne"""
        self.edit_selected_invoice()

    def update_status_summary(self):
        """Met à jour le résumé des factures"""
        total_count = 0
        total_amount = 0.0
        total_paid = 0.0
        total_due = 0.0

        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row):
                continue
                
            total_count += 1
            
            try:
                def parse_amount(col, r=row):
                    """Parse un montant au format français: 1 234,50 DA"""
                    item = self.table.item(r, col)
                    if not item:
                        return 0.0
                        
                    txt = item.text().strip()
                    if not txt:
                        return 0.0
                    
                    # Étape 1: Supprimer " DA"
                    txt = txt.replace(" DA", "").strip()
                    
                    # Étape 2: Supprimer espaces (séparateurs de milliers)
                    txt = txt.replace(" ", "")
                    txt = txt.replace("\u202f", "")  # espace insécable
                    txt = txt.replace("\u00a0", "")  # espace non-breaking
                    
                    # Étape 3: Remplacer virgule par point (important!)
                    txt = txt.replace(",", ".")
                    
                    if not txt:
                        return 0.0
                    
                    try:
                        return float(txt)
                    except ValueError as e:
                        logger.debug(f"Parse error for '{txt}': {e}")
                        return 0.0

                # Calculer les totaux
                total_amount += parse_amount(6)  # Col 6: Total TTC
                total_paid += parse_amount(7)    # Col 7: Payé
                total_due += parse_amount(8)     # Col 8: Reste

            except Exception as e:
                logger.debug(f"Error parsing row {row}: {e}")
                continue

        # Mise à jour des labels
        self.total_invoices_label.setText(f"Total: {total_count} facture(s)")
        
        # Format français: 1 234,50 DA (espace pour milliers, virgule pour décimales)
        self.total_amount_label.setText(
            f"Montant total: {total_amount:,.2f} DA".replace(",", " ")
        )
        self.paid_amount_label.setText(
            f"Payé: {total_paid:,.2f} DA".replace(",", " ")
        )
        self.due_amount_label.setText(
            f"Dû: {total_due:,.2f} DA".replace(",", " ")
        )