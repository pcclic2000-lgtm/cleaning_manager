# views/invoices/invoice_dialog.py
"""Dialogue de création / modification d'une facture."""
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

HAVE_WEBENGINE = False
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    HAVE_WEBENGINE = True
except Exception:
    HAVE_WEBENGINE = False

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets")

logger = logging.getLogger(__name__)

class InvoiceDialog(QDialog):
    """Dialogue pour créer/modifier une facture avec design professionnel"""

    invoice_saved = pyqtSignal()

    def __init__(self, client_id=None, invoice_id=None, contrat_id=None, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.invoice_id = invoice_id
        self.contrat_id = contrat_id
        self.items = []
        self.entreprise_info = self.load_entreprise_info()

        self.setWindowTitle("Modifier facture" if invoice_id else "Nouvelle facture")
        self.setModal(True)
        self.setMinimumSize(1000, 800)

        self.init_ui()
        self.load_data()

    def load_entreprise_info(self):
        """Charger les informations de l'entreprise depuis la base"""
        try:
            with get_session() as session:
                company = session.query(CompanyInfo).first()
                if company:
                    rib_formate = company.rib or ""
                    compte_ccp = getattr(company, 'compte_ccp', "") or ""

                    return {
                        'nom': company.nom or "Entreprise",
                        'adresse': company.adresse or "",
                        'ville': company.ville or "",
                        'telephone': company.telephone or "",
                        'email': company.email or "",
                        'site_web': company.site_web or "",
                        'rc': company.rc or "",
                        'nif': company.nif or "",
                        'nis': company.nis or "",
                        'art': company.art or "",
                        'rib': rib_formate,
                        'banque': company.banque or "",
                        'compte_ccp': compte_ccp,
                        'nom_directeur': company.nom_directeur or "",
                        'fonction_directeur': company.fonction_directeur or "",
                        'numero_employeur': company.numero_employeur or "",
                        'logo_path': company.logo_path if company.logo_path and os.path.exists(company.logo_path) else None,
                        'ccp_banque': company.ccp_banque or "",
                        'adresse_banque': company.adresse_banque or "",
                    }
                return {}
        except Exception as e:
            logger.error("Erreur chargement info entreprise: %s", e)
            return {}


    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Titre
        title_label = QLabel("✏️ ÉDITION DE FACTURE")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                background: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 4px;
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
                font-weight: bold;
            }
        """)

        # ── Tab Informations ──────────────────────────────────────────────────
        tab_info = QWidget()
        info_layout = QVBoxLayout()
        info_layout.setSpacing(15)

        # Client
        client_group = QGroupBox("👤 CLIENT")
        client_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #3498db;
            }
        """)
        client_form = QFormLayout()
        client_form.setSpacing(10)

        self.client_combo = QComboBox()
        self.client_combo.setMinimumHeight(35)
        self.load_clients()
        self.client_combo.currentIndexChanged.connect(self.load_contrats_for_client)

        self.invoice_number = QLineEdit()
        self.invoice_number.setPlaceholderText("Généré automatiquement")
        self.invoice_number.setReadOnly(True)
        self.invoice_number.setMinimumHeight(35)

        # Permettre l'édition manuelle du numéro via une checkbox
        self.edit_invoice_checkbox = QCheckBox("Modifier N°")
        self.edit_invoice_checkbox.setToolTip("Permet de modifier manuellement le numéro de facture")
        self.edit_invoice_checkbox.stateChanged.connect(self.toggle_invoice_number_editable)

        # Regrouper le QLineEdit et la checkbox sur la même ligne
        container = QWidget()
        _h = QHBoxLayout()
        _h.setContentsMargins(0, 0, 0, 0)
        _h.addWidget(self.invoice_number)
        _h.addWidget(self.edit_invoice_checkbox)
        container.setLayout(_h)

        client_form.addRow("Client*:", self.client_combo)
        client_form.addRow("N° Facture:", container)

        self.contrat_combo = QComboBox()
        self.contrat_combo.setMinimumHeight(35)
        self.contrat_combo.setToolTip("Sélectionnez le contrat lié à cette facture")
        client_form.addRow("Contrat lié:", self.contrat_combo)

        client_group.setLayout(client_form)
        info_layout.addWidget(client_group)

        # Dates
        dates_group = QGroupBox("📅 DATES")
        dates_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2ecc71;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #27ae60;
            }
        """)
        dates_layout = QFormLayout()
        dates_layout.setSpacing(10)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumHeight(35)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")

        self.due_date_edit = QDateEdit()
        self.due_date_edit.setDate(QDate.currentDate().addDays(30))
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setMinimumHeight(35)
        self.due_date_edit.setDisplayFormat("dd/MM/yyyy")

        dates_layout.addRow("Date facture*:", self.date_edit)
        dates_layout.addRow("Date échéance:", self.due_date_edit)

        # ── Période optionnelle ──────────────────────────────────────────────
        self.periode_checkbox = QCheckBox("Afficher la période (Du … Au …)")
        self.periode_checkbox.setToolTip(
            "Ajoute une ligne Période sur la facture PDF, sur la même ligne que DOIT"
        )
        self.periode_checkbox.stateChanged.connect(self.toggle_periode_fields)
        dates_layout.addRow("", self.periode_checkbox)

        # Conteneur Du / Au sur une seule ligne
        periode_container = QWidget()
        periode_h = QHBoxLayout()
        periode_h.setContentsMargins(0, 0, 0, 0)
        periode_h.setSpacing(8)

        self.periode_du = QDateEdit()
        self.periode_du.setCalendarPopup(True)
        self.periode_du.setDisplayFormat("dd/MM/yyyy")
        self.periode_du.setDate(QDate.currentDate().addDays(-30))
        self.periode_du.setMinimumHeight(32)
        self.periode_du.setEnabled(False)

        self.periode_au = QDateEdit()
        self.periode_au.setCalendarPopup(True)
        self.periode_au.setDisplayFormat("dd/MM/yyyy")
        self.periode_au.setDate(QDate.currentDate())
        self.periode_au.setMinimumHeight(32)
        self.periode_au.setEnabled(False)

        periode_h.addWidget(QLabel("Du :"))
        periode_h.addWidget(self.periode_du)
        periode_h.addWidget(QLabel("Au :"))
        periode_h.addWidget(self.periode_au)
        periode_container.setLayout(periode_h)
        self.periode_container = periode_container

        dates_layout.addRow("", periode_container)

        dates_group.setLayout(dates_layout)
        info_layout.addWidget(dates_group)

        # Statut & Paiement
        status_group = QGroupBox("💰 STATUT & PAIEMENT")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #f39c12;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #f39c12;
            }
        """)
        status_layout = QFormLayout()
        status_layout.setSpacing(10)

        self.status_combo = QComboBox()
        self.status_combo.addItems([s.value for s in InvoiceStatus])
        self.status_combo.setMinimumHeight(35)

        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems([p.value for p in PaymentMethod])
        self.payment_method_combo.setMinimumHeight(35)

        status_layout.addRow("Statut*:", self.status_combo)
        status_layout.addRow("Mode paiement:", self.payment_method_combo)

        status_group.setLayout(status_layout)
        info_layout.addWidget(status_group)

        info_layout.addStretch()
        tab_info.setLayout(info_layout)
        self.tabs.addTab(tab_info, "📋 Informations")

        # ── Tab Articles ──────────────────────────────────────────────────────
        tab_items = QWidget()
        items_layout = QVBoxLayout()
        items_layout.setSpacing(15)

        items_toolbar = QHBoxLayout()

        btn_add_item = QPushButton("➕ Ajouter article")
        btn_add_item.setStyleSheet("""
            QPushButton {
                background: #27ae60; color: white; border: none;
                padding: 8px 16px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: #219653; }
        """)
        btn_add_item.clicked.connect(self.add_item_dialog)

        btn_remove_item = QPushButton("🗑️ Supprimer")
        btn_remove_item.setStyleSheet("""
            QPushButton {
                background: #e74c3c; color: white; border: none;
                padding: 8px 16px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: #c0392b; }
        """)
        btn_remove_item.clicked.connect(self.remove_selected_item)

        items_toolbar.addWidget(btn_add_item)
        items_toolbar.addWidget(btn_remove_item)
        items_toolbar.addStretch()
        items_layout.addLayout(items_toolbar)

        # Table des articles
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(
            ["Description", "Quantité", "Prix unitaire", "TVA %", "Total HT", "Total TTC"]
        )
        self.items_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6; border-radius: 6px;
                background: white; gridline-color: #dee2e6;
            }
            QHeaderView::section {
                background: #34495e; color: white;
                padding: 10px; border: none; font-weight: bold;
            }
            QTableWidget::item { padding: 8px; }
        """)

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        items_layout.addWidget(self.items_table)

        # Totaux
        totals_group = QGroupBox("🧮 TOTAUX")
        totals_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #9b59b6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #9b59b6;
            }
        """)
        totals_layout = QFormLayout()
        totals_layout.setSpacing(10)

        self.subtotal_label = QLabel("0.00 DA")
        self.subtotal_label.setStyleSheet("font-size: 14px; color: #2c3e50;")

        self.tax_label = QLabel("0.00 DA")
        self.tax_label.setStyleSheet("font-size: 14px; color: #2c3e50;")

        self.total_label = QLabel("0.00 DA")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")

        totals_layout.addRow("Sous-total (HT):", self.subtotal_label)
        totals_layout.addRow("TVA:", self.tax_label)
        totals_layout.addRow("Total (TTC):", self.total_label)

        totals_group.setLayout(totals_layout)
        items_layout.addWidget(totals_group)

        tab_items.setLayout(items_layout)
        self.tabs.addTab(tab_items, "📦 Articles")

        # ── Tab Notes ─────────────────────────────────────────────────────────
        tab_notes = QWidget()
        notes_layout = QVBoxLayout()
        notes_layout.setSpacing(10)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notes internes...")
        self.notes_edit.setMinimumHeight(100)
        self.notes_edit.setStyleSheet("""
            QTextEdit { border: 1px solid #dee2e6; border-radius: 6px; padding: 8px; }
        """)

        self.terms_edit = QTextEdit()
        self.terms_edit.setPlaceholderText("Conditions de paiement...")
        self.terms_edit.setMinimumHeight(80)
        self.terms_edit.setStyleSheet("""
            QTextEdit { border: 1px solid #dee2e6; border-radius: 6px; padding: 8px; }
        """)

        notes_layout.addWidget(QLabel("📝 Notes internes:"))
        notes_layout.addWidget(self.notes_edit)
        notes_layout.addWidget(QLabel("📄 Conditions de paiement:"))
        notes_layout.addWidget(self.terms_edit)

        tab_notes.setLayout(notes_layout)
        self.tabs.addTab(tab_notes, "📄 Notes")

        layout.addWidget(self.tabs)

        # ── Boutons d'action ──────────────────────────────────────────────────
        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        self.btn_preview = QPushButton("👁️ Aperçu")
        self.btn_preview.setStyleSheet("""
            QPushButton {
                background: #3498db; color: white; border: none;
                padding: 10px 20px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        self.btn_preview.clicked.connect(self.preview_invoice)

        self.btn_export_pdf = QPushButton("📄 Exporter PDF")
        self.btn_export_pdf.setStyleSheet("""
            QPushButton {
                background: #f39c12; color: white; border: none;
                padding: 10px 20px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: #d35400; }
        """)
        self.btn_export_pdf.clicked.connect(self.export_pdf)

        self.btn_save = QPushButton("💾 Enregistrer")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: #27ae60; color: white; border: none;
                padding: 10px 30px; border-radius: 6px;
                font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background: #219653; }
        """)
        self.btn_save.clicked.connect(self.save_invoice)

        btn_cancel = QPushButton("❌ Annuler")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #e74c3c; color: white; border: none;
                padding: 10px 20px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: #c0392b; }
        """)
        btn_cancel.clicked.connect(self.reject)

        buttons.addWidget(self.btn_preview)
        buttons.addWidget(self.btn_export_pdf)
        buttons.addStretch()
        buttons.addWidget(self.btn_save)
        buttons.addWidget(btn_cancel)

        layout.addLayout(buttons)
        self.setLayout(layout)

        # ── Chargement des données ─────────────────────────────────────────────────

    def toggle_invoice_number_editable(self, state):
        """Active/désactive l'édition manuelle du numéro de facture."""
        editable = bool(state)  # stateChanged émet un int (0/2), pas Qt.CheckState
        self.invoice_number.setReadOnly(not editable)
        if not editable:
            # Si on désactive l'édition et qu'il n'y a pas de numéro, régénérer
            if not self.invoice_number.text().strip():
                try:
                    self.generate_invoice_number()
                except Exception:
                    pass
    
    def toggle_periode_fields(self, state):
        """Active/désactive les champs Du/Au selon la checkbox Période."""
        enabled = bool(state)
        self.periode_du.setEnabled(enabled)
        self.periode_au.setEnabled(enabled)

    def load_clients(self):
        with get_session() as session:
            clients = (session.query(Client)
                .filter(Client.est_actif == True)
                .order_by(Client.raison_sociale).all())
            self.client_combo.clear()
            self.client_combo.addItem("-- Sélectionnez un client --", None)
            for client in clients:
                label = f"{client.raison_sociale or client.nom_complet} ({client.code_client})"
                self.client_combo.addItem(label, client.id)

    def load_data(self):
        if not self.invoice_id:
            self.generate_invoice_number()
            if self.client_id:
                idx = self.client_combo.findData(self.client_id)
                if idx >= 0:
                    self.client_combo.setCurrentIndex(idx)
                # Pré-sélectionner le contrat si fourni
            if self.contrat_id:
                idx = self.contrat_combo.findData(self.contrat_id)
                if idx >= 0:
                    self.contrat_combo.setCurrentIndex(idx)
            return
        
        with get_session() as session:
            invoice = session.query(Invoice).filter(Invoice.id == self.invoice_id).first()
            if invoice:
                index = self.client_combo.findData(invoice.client_id)
            if index >= 0:
                self.client_combo.setCurrentIndex(index)
                
            # Le numéro est déjà au format 001/2026
            self.invoice_number.setText(invoice.invoice_number)
            if invoice.date:
                self.date_edit.setDate(QDate(invoice.date.year, invoice.date.month, invoice.date.day))
            if invoice.due_date:
                self.due_date_edit.setDate(QDate(invoice.due_date.year, invoice.due_date.month, invoice.due_date.day))
            if invoice.status:
                idx = self.status_combo.findText(invoice.status.value)
                if idx >= 0:
                    self.status_combo.setCurrentIndex(idx)
            if invoice.payment_method:
                idx = self.payment_method_combo.findText(invoice.payment_method.value)
                if idx >= 0:
                    self.payment_method_combo.setCurrentIndex(idx)

            # Récupérer le contrat_id lié à la facture si non fourni
            if not self.contrat_id and invoice.contrat_id:
                self.contrat_id = invoice.contrat_id

            # Sélectionner le contrat dans le combo après chargement du client
            if self.contrat_id:
                idx = self.contrat_combo.findData(self.contrat_id)
                if idx >= 0:
                    self.contrat_combo.setCurrentIndex(idx)

            self.items = []
            for it in invoice.items:
                obj = type('obj', (object,), {
                    'description': it.description,
                    'quantity': float(it.quantity),
                    'unit_price': float(it.unit_price),
                    'tax_rate': float(it.tax_rate)
                })
                self.items.append(obj)
            self.update_items_table()
            self.notes_edit.setText(invoice.notes or "")
            self.terms_edit.setText(invoice.terms or "")

            # views/invoice_view.py - Dans la classe InvoiceDialog, ajouter cette méthode

    def load_contrats_for_client(self):
        """Charge les contrats actifs du client sélectionné"""
        self.contrat_combo.clear()
        self.contrat_combo.addItem("-- Aucun contrat --", None)

        client_id = self.client_combo.currentData()
        if not client_id:
            return

        with get_session() as session:
            from models.contrat import Contrat
            from models.enums import StatutContrat

            contrats = (
            session.query(Contrat)
            .filter(Contrat.client_id == client_id)
            .order_by(Contrat.date_debut.desc())
            .all()
            )

            for contrat in contrats:
                # Label : numéro + ODS si disponible + statut
                label_parts = [contrat.numero_contrat]

                if contrat.numero_ods:
                    label_parts.append(f"ODS {contrat.numero_ods}")

                if contrat.type_facture and contrat.type_facture != "standard":
                    label_parts.append(f"[{contrat.type_facture}]")

                statut = contrat.statut.value if contrat.statut else ""
                if statut:
                    label_parts.append(f"({statut})")

                label = "  |  ".join(label_parts)
                self.contrat_combo.addItem(label, contrat.id)

            # Si un seul contrat actif, le sélectionner automatiquement
            if self.contrat_combo.count() == 2:  # "-- Aucun --" + 1 contrat
                self.contrat_combo.setCurrentIndex(1)

    
    def is_beni_messous_client(self):
        """Vérifie si le client est CHU Beni Messous"""
        client_id = self.client_combo.currentData()
        if not client_id:
            return False
        
        with get_session() as session:
            client = session.query(Client).filter(Client.id == client_id).first()
            if client and client.raison_sociale:
                client_name = client.raison_sociale.lower()
                return "beni messous" in client_name or "chu beni messous" in client_name
            return False

    def is_douera_client(self):
        """Vérifie si le client est CHU Douera"""
        client_id = self.client_combo.currentData()
        if not client_id:
            return False
        
        with get_session() as session:
            client = session.query(Client).filter(Client.id == client_id).first()
            if client and client.raison_sociale:
                client_name = client.raison_sociale.lower()
                return "chu douera" in client_name or "douera" in client_name
            return False
    
    def generate_invoice_number(self):
        """Génère un numéro de facture simple au format 001/2026"""
        try:
            with get_session() as session:
                today = datetime.date.today()
                annee = today.strftime("%Y")
                
                # Compter les factures de l'année en cours
                debut_annee = datetime.date(today.year, 1, 1)
                fin_annee = datetime.date(today.year, 12, 31)
                
                count = session.query(Invoice).filter(
                    Invoice.date >= debut_annee,
                    Invoice.date <= fin_annee
                ).count()
                
                # Numéro au format 001/2026 (avec 3 chiffres)
                numero = f"{count+1:03d}/{annee}"
                self.invoice_number.setText(numero)
                
                print(f"🔢 Numéro de facture généré: {numero}")
        except Exception as e:
            logger.info(f"❌ Erreur génération numéro: {e}")
            # Numéro de secours
            numero = f"001/{datetime.date.today().year}"
            self.invoice_number.setText(numero)

            # ── Gestion des articles ───────────────────────────────────────────────────

    def add_item_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter article")
        dialog.setModal(True)
        dialog.setMinimumWidth(500)

        layout = QFormLayout()
        layout.setSpacing(15)

        description = QTextEdit()
        description.setMaximumHeight(60)
        description.setPlaceholderText("Description de l'article...")

        quantity = QDoubleSpinBox()
        quantity.setRange(0.01, 10000)
        quantity.setValue(1.0)
        quantity.setDecimals(2)
        quantity.setSuffix(" unité(s)")

        unit_price = QDoubleSpinBox()
        unit_price.setRange(0, 1000000)
        unit_price.setDecimals(2)
        unit_price.setSuffix(" DA")
        unit_price.setValue(0.0)

        tax_rate = QDoubleSpinBox()
        tax_rate.setRange(0, 100)
        tax_rate.setDecimals(2)
        tax_rate.setSuffix(" %")
        tax_rate.setValue(19.0)

        layout.addRow("Description*:", description)
        layout.addRow("Quantité:", quantity)
        layout.addRow("Prix unitaire*:", unit_price)
        layout.addRow("TVA %:", tax_rate)

        buttons = QHBoxLayout()
        btn_ok = QPushButton("Ajouter")
        btn_ok.setStyleSheet("""
            QPushButton {
                background: #27ae60; color: white; border: none;
                padding: 8px 20px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: #219653; }
        """)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #e74c3c; color: white; border: none;
                padding: 8px 20px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: #c0392b; }
        """)

        def add_item():
            if not description.toPlainText().strip():
                QMessageBox.warning(dialog, "Erreur", "La description est obligatoire")
                return
            if unit_price.value() <= 0:
                QMessageBox.warning(dialog, "Erreur", "Le prix unitaire doit être supérieur à 0")
                return
            item = type('obj', (object,), {
                'description': description.toPlainText().strip(),
                'quantity': quantity.value(),
                'unit_price': unit_price.value(),
                'tax_rate': tax_rate.value()
            })
            self.items.append(item)
            self.update_items_table()
            dialog.accept()

        # Connexions placées en dehors de la fonction interne (fix indentation bug)
        btn_ok.clicked.connect(add_item)
        btn_cancel.clicked.connect(dialog.reject)

        buttons.addStretch()
        buttons.addWidget(btn_ok)
        buttons.addWidget(btn_cancel)
        layout.addRow(buttons)
        dialog.setLayout(layout)
        dialog.exec()

    def remove_selected_item(self):
        selected = self.items_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un article à supprimer")
            return
        row = selected[0].row()
        if row < len(self.items):
            reply = QMessageBox.question(
                self, "Confirmation",
                "Voulez-vous vraiment supprimer cet article ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.items.pop(row)
                self.update_items_table()

    def update_items_table(self):
        self.items_table.setRowCount(len(self.items))
        subtotal = Decimal('0.00')
        total_tax = Decimal('0.00')
        total = Decimal('0.00')

        for row, item in enumerate(self.items):
            qty = Decimal(str(item.quantity))
            price = Decimal(str(item.unit_price))
            tax_rate = Decimal(str(item.tax_rate))

            item_subtotal = qty * price
            item_tax = item_subtotal * (tax_rate / Decimal('100.00'))
            item_total = item_subtotal + item_tax

            self.items_table.setItem(row, 0, QTableWidgetItem(item.description))
            self.items_table.setItem(row, 1, QTableWidgetItem(f"{item.quantity:,.2f}"))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{item.unit_price:,.2f} DA"))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{item.tax_rate}%"))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"{item_subtotal:,.2f} DA"))
            self.items_table.setItem(row, 5, QTableWidgetItem(f"{item_total:,.2f} DA"))

            subtotal += item_subtotal
            total_tax += item_tax
            total += item_total

        self.subtotal_label.setText(f"{subtotal:,.2f} DA")
        self.tax_label.setText(f"{total_tax:,.2f} DA")
        self.total_label.setText(f"{total:,.2f} DA")

        # ── Sauvegarde ────────────────────────────────────────────────────────────

    def save_invoice(self):
        if self.client_combo.currentIndex() <= 0:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un client")
            return
        if not self.items:
            QMessageBox.warning(self, "Erreur", "Veuillez ajouter au moins un article")
            return
        # Valider le numéro de facture (toujours vérifier le format)
        numero = self.invoice_number.text().strip()
        if not numero:
            QMessageBox.warning(self, "Numéro manquant", "Le numéro de facture est vide.")
            return
        if not self.validate_invoice_number(numero):
            QMessageBox.warning(self, "Numéro invalide", "Le numéro de facture doit être au format 001/2026.")
            return
        
        client_id = self.client_combo.currentData()
        try:
            with get_session() as session:
                if self.invoice_id:
                    # MODIFICATION
                    invoice = session.query(Invoice).filter(Invoice.id == self.invoice_id).first()
                    if not invoice:
                        QMessageBox.critical(self, "Erreur", "Facture non trouvée")
                        return
                        
                    # IMPORTANT: Ne pas changer le numéro de facture lors de la modification
                    # Garder le numéro existant
                    current_invoice_number = invoice.invoice_number
                        
                    # Supprimer les anciens items
                    session.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).delete()
                    message = "Facture modifiée avec succès!"
                        
                else:
                    # CRÉATION
                    # Vérifier que le numéro de facture est au bon format
                    invoice_number = self.invoice_number.text()
                    if not self.validate_invoice_number(invoice_number):
                        QMessageBox.warning(self, "Erreur", 
                            "Le numéro de facture doit être au format 001/2026")
                        return
                        
                    # Vérifier l'unicité du numéro
                    existing = session.query(Invoice).filter(
                        Invoice.invoice_number == invoice_number
                    ).first()
                        
                    if existing:
                        QMessageBox.warning(self, "Erreur", 
                            f"Le numéro de facture {invoice_number} existe déjà. Veuillez en générer un nouveau.")
                        self.generate_invoice_number()
                        return
                        
                    invoice = Invoice(invoice_number=invoice_number, client_id=client_id)
                    session.add(invoice)
                    message = "Facture créée avec succès!"

                # Mettre à jour les champs (sauf le numéro pour la modification)
                invoice.date = self.date_edit.date().toPyDate()
                invoice.due_date = self.due_date_edit.date().toPyDate()

                try:
                    invoice.status = InvoiceStatus(self.status_combo.currentText())
                except Exception:
                    invoice.status = next(
                        (s for s in InvoiceStatus if s.value == self.status_combo.currentText()),
                        InvoiceStatus.DRAFT
                    )

                try:
                    invoice.payment_method = PaymentMethod(self.payment_method_combo.currentText())
                except Exception:
                    invoice.payment_method = next(
                        (p for p in PaymentMethod if p.value == self.payment_method_combo.currentText()),
                        None
                    )

                invoice.notes = self.notes_edit.toPlainText().strip() or None
                invoice.terms = self.terms_edit.toPlainText().strip() or None

                subtotal = Decimal('0.00')
                total_tax = Decimal('0.00')

                for item_data in self.items:
                    it = InvoiceItem(
                        description=item_data.description,
                        quantity=Decimal(str(item_data.quantity)),
                        unit_price=Decimal(str(item_data.unit_price)),
                        tax_rate=Decimal(str(item_data.tax_rate))
                    )
                    total_ht_decimal = it.quantity * it.unit_price
                    it.total_ht = float(total_ht_decimal)
                    total_ttc_decimal = total_ht_decimal * (Decimal('1.00') + (it.tax_rate / Decimal('100.00')))
                    it.total_ttc = float(total_ttc_decimal)
                    invoice.items.append(it)
                    subtotal += total_ht_decimal
                    total_tax += total_ht_decimal * (it.tax_rate / Decimal('100.00'))

                invoice.subtotal = float(subtotal)
                invoice.tax_amount = float(total_tax)
                invoice.total_amount = float(subtotal + total_tax)
                invoice.amount_paid = getattr(invoice, 'amount_paid', 0.0) or 0.0
                invoice.balance_due = invoice.total_amount - invoice.amount_paid
                # Lier la facture au contrat sélectionné
                contrat_id_selected = self.contrat_combo.currentData()
                invoice.contrat_id = contrat_id_selected  # None si aucun contrat choisi
                session.commit()
                self.invoice_saved.emit()
                QMessageBox.information(self, "Succès", message)
                self.accept()

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur: {str(e)}")
            import traceback
            traceback.print_exc()

    def validate_invoice_number(self, numero):
        """Valide que le numéro de facture est au format 001/2026"""
        import re
        pattern = r'^\d{3}/\d{4}$'
        if not re.match(pattern, numero):
            return False
        
        # Vérifier que l'année est valide (entre 2000 et 2100)
        annee = int(numero.split('/')[1])
        if annee < 2000 or annee > 2100:
            return False
        
        return True
    
        # ── Contexte facture ──────────────────────────────────────────────────────

    def build_invoice_context(self):
        """build_invoice_context() qui lit le contrat depuis le combo"""
        from decimal import Decimal
        from models.contrat import Contrat
        from models.client import Client

        ctx = {}
        client_id = self.client_combo.currentData()
        client = None
        contrat = None

        # Contrat sélectionné dans le combo (priorité) ou self.contrat_id
        contrat_id_effectif = self.contrat_combo.currentData() or self.contrat_id

        if client_id:
            with get_session() as session:
                client = session.query(Client).filter(Client.id == client_id).first()
                if contrat_id_effectif:
                    contrat = session.query(Contrat).filter(Contrat.id == contrat_id_effectif).first()

                ctx['company'] = self.entreprise_info

                ctx['client'] = {
                    'name':    (client.raison_sociale or client.nom_complet) if client else "",
                    'address': client.adresse or "" if client else "",
                    'phone':   client.telephone or "" if client else "",
                    'email':   client.email or "" if client else "",
                    'nif':     client.nif or "" if client else "",
                    'code':    client.code_client or "" if client else "",
                }

                ctx['contrat'] = {}
                if contrat:
                    ctx['contrat'] = {
                        'numero_contrat':    contrat.numero_contrat or "",
                        'type_facture':      contrat.type_facture or "standard",
                        'type_document':     contrat.type_document or "",
                        'numero_marche':     contrat.numero_marche or "",
                        'date_marche':       contrat.date_marche.strftime("%d/%m/%Y") if contrat.date_marche else "",
                        'numero_convention': contrat.numero_convention or "",
                        'date_convention':   contrat.date_convention.strftime("%d/%m/%Y") if contrat.date_convention else "",
                        'numero_ods':        contrat.numero_ods or "",
                        'date_ods':          contrat.date_ods.strftime("%d/%m/%Y") if contrat.date_ods else "",
                        'objet_ods':         contrat.objet_ods or "",
                        'signature_ods':     contrat.signature_ods or "",
                    }

                ctx['invoice'] = {
                    'number':         self.invoice_number.text(),
                    'date':           self.date_edit.date().toPyDate().strftime("%d/%m/%Y"),
                    'due_date':       self.due_date_edit.date().toPyDate().strftime("%d/%m/%Y"),
                    'status':         self.status_combo.currentText(),
                    'payment_method': self.payment_method_combo.currentText(),
                    'notes':          self.notes_edit.toPlainText(),
                    'terms':          self.terms_edit.toPlainText(),
                    'show_periode':   self.periode_checkbox.isChecked(),
                    'periode_du':     self.periode_du.date().toPyDate().strftime("%d/%m/%Y"),
                    'periode_au':     self.periode_au.date().toPyDate().strftime("%d/%m/%Y"),
                }

                ctx['items'] = []
                subtotal  = Decimal('0.00')
                total_tax = Decimal('0.00')

                for it in self.items:
                    qty      = Decimal(str(it.quantity))
                    price    = Decimal(str(it.unit_price))
                    tax_rate = Decimal(str(it.tax_rate))

                    ht  = qty * price
                    tax = ht * (tax_rate / Decimal('100.00'))
                    ttc = ht + tax

                    ctx['items'].append({
                        'description': it.description,
                        'quantity':    int(qty),
                        'unit_price':  float(price),
                        'tax_rate':    float(tax_rate),
                        'total_ht':    float(ht),
                        'total_ttc':   float(ttc),
                    })

                    subtotal  += ht
                    total_tax += tax

                ctx['summary'] = {
                    'subtotal': float(subtotal),
                    'tax':      float(total_tax),
                    'total':    float(subtotal + total_tax),
                }

                return ctx
                # ── Montant en lettres ────────────────────────────────────────────────────

    def montant_en_lettres(self, montant):
        """Convertit un montant en lettres (français)"""
        if montant is None:
            return ""

        unite = [
            "", "UN", "DEUX", "TROIS", "QUATRE", "CINQ", "SIX", "SEPT", "HUIT", "NEUF", "DIX",
            "ONZE", "DOUZE", "TREIZE", "QUATORZE", "QUINZE", "SEIZE", "DIX-SEPT", "DIX-HUIT", "DIX-NEUF"
        ]
        dizaine = [
            "", "DIX", "VINGT", "TRENTE", "QUARANTE", "CINQUANTE", "SOIXANTE",
            "SOIXANTE", "QUATRE-VINGT", "QUATRE-VINGT"
        ]

        def deux_chiffres(n):
            if n == 0:
                return ""
            if n < 20:
                return unite[n]
            dix = n // 10
            un = n % 10
            if dix == 7:
                return f"{dizaine[6]}-{unite[10 + un]}"
            if dix == 9:
                return f"{dizaine[8]}-{unite[10 + un]}"
            if dix == 8:
                if un == 0:
                    return "QUATRE-VINGTS"
                return f"{dizaine[8]}-{unite[un]}"
            if un == 0:
                return dizaine[dix]
            if un == 1 and dix != 8:
                return f"{dizaine[dix]}-ET-UN"
            return f"{dizaine[dix]}-{unite[un]}"

        def trois_chiffres(n):
            if n == 0:
                return ""
            centaine = n // 100
            reste = n % 100
            parties = []
            if centaine == 1:
                parties.append("CENT")
            elif centaine > 1:
                parties.append(f"{unite[centaine]} CENT{'S' if reste == 0 else ''}")
            if reste > 0:
                parties.append(deux_chiffres(reste))
            return " ".join(parties)

        try:
            montant_int = int(montant)
            if montant_int == 0:
                return "ZÉRO DINARS"
            if montant_int < 0:
                return f"MOINS {self.montant_en_lettres(-montant_int)}"

            milliards = montant_int // 1_000_000_000
            reste     = montant_int  % 1_000_000_000
            millions  = reste // 1_000_000
            reste     = reste  % 1_000_000
            milliers  = reste // 1_000
            unites_   = reste  % 1_000

            parties = []
            if milliards > 0:
                parties.append(f"{trois_chiffres(milliards)} MILLIARD{'S' if milliards > 1 else ''}")
            if millions > 0:
                parties.append(f"{trois_chiffres(millions)} MILLION{'S' if millions > 1 else ''}")
            if milliers > 0:
                if milliers == 1:
                    parties.append("MILLE")
                else:
                    parties.append(f"{trois_chiffres(milliers)} MILLE")
            if unites_ > 0:
                parties.append(trois_chiffres(unites_))

            return " ".join(parties) + " DINARS"
        except Exception:
            return f"{montant:,.0f} DINARS".replace(",", " ")
    def generate_invoice_html(self, context: dict) -> str:
        """Générer le HTML de la facture"""
        company = context['company']
        client = context['client']
        invoice = context['invoice']
        items = context['items']
        summary = context['summary']

        # Logo
        if company.get('logo_path'):
            logo_src = QUrl.fromLocalFile(company['logo_path']).toString()
            logo_html = f'<img src="{logo_src}" style="height:60px; width:auto; object-fit:contain;">'
        else:
            logo_html = f'<div style="font-size:24px;font-weight:bold;">{company.get("nom", "")}</div>'

        entreprise_info = f"""
        <div style="font-size: 10px; line-height: 1.4;">
            Entreprise de nettoyage – travaux &amp; services<br>
            Adresse : {company.get('adresse', '')}<br>
            Phone : {company.get('telephone', '')}<br>
            N.R.C {company.get('rc', '')}<br>
            N°article : {company.get('art', '')}<br>
            N.I.F {company.get('nif', '')}   N.I.S {company.get('nis', '')}<br>
            E-mail : {company.get('email', '')}<br>
            CCP : {company.get('compte_ccp', '')} | Banque : {company.get('banque', '')} | RIB : {company.get('rib', '')}
        </div>
        """

        # Références ODS (données réelles)
        ods_refs = ""
        contrat = context.get('contrat', {})
        if contrat.get('numero_ods'):
            ods_refs = f"""
            <div style="font-size: 11px; margin: 15px 0;">
                Relative au N° ODS : {contrat['numero_ods']} du {contrat['date_ods']}<br>
                {('<b>Objet :</b> ' + contrat['objet_ods']) if contrat.get('objet_ods') else ''}
            </div>
            """

        rows_html = ""
        for it in items:
            rows_html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #000;">{it['description']}</td>
                <td style="padding: 8px; border: 1px solid #000; text-align: center;">{it['quantity']:,.0f}</td>
                <td style="padding: 8px; border: 1px solid #000; text-align: right;">{it['unit_price']:,.2f}</td>
                <td style="padding: 8px; border: 1px solid #000; text-align: right;">{it['total_ht']:,.2f}</td>
            </tr>
            """

        total_en_lettres = self.montant_en_lettres(summary['total'])

        css = """
        <style>
            body { font-family: 'Times New Roman', Times, serif; margin: 2cm; line-height: 1.3; }
            .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 11px; }
            th { background-color: #f2f2f2; border: 1px solid #000; padding: 8px; text-align: center; font-weight: bold; }
            td { border: 1px solid #000; padding: 8px; }
            .total-lettres { font-size: 12px; font-weight: bold; margin: 30px 0; text-align: center; }
        </style>
        """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Facture {invoice['number']}</title>{css}</head>
        <body>
            <div class="header">
                <div>{logo_html}</div>
                <div>{entreprise_info}</div>
            </div>
            <div style="text-align:right; font-size:12px; margin:20px 0;">Date : {invoice['date']}</div>
            {ods_refs}
            <div style="font-size:12px; font-weight:bold; margin:20px 0;">Doit : {client.get('name', '')}</div>
            <table>
                <thead>
                    <tr>
                        <th>Désignation du service</th>
                        <th>Nombre Agents</th>
                        <th>Prix Unit HT</th>
                        <th>Total HT</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
            <div class="total-lettres">Arrêté la présente facture à la somme de : {total_en_lettres}</div>
        </body>
        </html>
        """
        return html

        # ── Aperçu ────────────────────────────────────────────────────────────────

    def preview_invoice(self):
        if self.client_combo.currentIndex() <= 0:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un client")
            return
        if not self.items:
            QMessageBox.warning(self, "Erreur", "Veuillez ajouter au moins un article")
            return

        ctx = self.build_invoice_context()
        html = self.generate_invoice_html(ctx)

        if HAVE_WEBENGINE:
            self._preview_with_webengine(html)
        else:
            self._preview_with_textdocument(html)

        # ── Export PDF ReportLab ───────────────────────────────────────────────────

        import os


    def export_pdf_reportlab(self):
        """Exporter la facture en PDF avec ReportLab - Structure adaptée selon le client"""
        if self.client_combo.currentIndex() <= 0:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un client")
            return
        if not self.items:
            QMessageBox.warning(self, "Erreur", "Veuillez ajouter au moins un article")
            return

        try:
            import calendar
            from datetime import datetime
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            ctx = self.build_invoice_context()
            client = ctx['client']
            contrat_ctx = ctx.get('contrat') or {}

            # Détection du type de facture via le champ type_facture du contrat
            type_facture = contrat_ctx.get('type_facture', 'standard')
            is_beni_messous = (type_facture == 'beni_messous')
            is_douera = (type_facture == 'chu_douera')

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exporter en PDF",
                f"{ctx['invoice']['number']}.pdf",
                "Fichiers PDF (*.pdf)"
            )
            if not file_path:
                return

            # Configuration du document
            FOOTER_HEIGHT = 4.0 * cm
            doc = SimpleDocTemplate(
                file_path, pagesize=A4,
                topMargin=0.8 * cm,
                bottomMargin=FOOTER_HEIGHT + 0.3 * cm,
                leftMargin=1.0 * cm,
                rightMargin=1.0 * cm
            )
            story = []
            styles = getSampleStyleSheet()

            # Styles communs
            title_style = ParagraphStyle(
                'TitleStyle', parent=styles['Normal'],
                fontName='Helvetica-Bold', fontSize=14 if is_beni_messous else 16,
                leading=18 if is_beni_messous else 20,
                alignment=0, spaceAfter=8, textColor=colors.HexColor('#2c3e50')
            )

            subtitle_style = ParagraphStyle(
                'SubtitleStyle', parent=styles['Normal'],
                fontName='Helvetica-Bold', fontSize=12, leading=16,
                alignment=0, spaceAfter=6, textColor=colors.HexColor('#34495e')
            )

            normal_style = ParagraphStyle(
                'NormalStyle', parent=styles['Normal'],
                fontName='Helvetica', fontSize=10, leading=14,
                alignment=0, spaceAfter=4, textColor=colors.HexColor('#2c3e50')
            )

            normal_bold_style = ParagraphStyle(
                'NormalBoldStyle', parent=normal_style,
                fontName='Helvetica-Bold', fontSize=10, leading=14
            )

            # FIX 2: date_style défini une seule fois (suppression de la redéfinition dans le bloc else)
            date_style = ParagraphStyle(
                'DateStyle', parent=normal_style,
                alignment=2, fontSize=10, textColor=colors.HexColor('#7f8c8d')
            )

            compact_style = ParagraphStyle(
                'CompactStyle', parent=styles['Normal'],
                fontName='Helvetica', fontSize=8, leading=10,
                spaceBefore=0, spaceAfter=2, textColor=colors.HexColor('#4a5568')
            )

            table_header_style = ParagraphStyle(
                'TableHeaderStyle', parent=styles['Normal'],
                fontName='Helvetica-Bold', fontSize=9, leading=12,
                alignment=1, textColor=colors.white if not is_beni_messous else colors.black
            )

            table_cell_style = ParagraphStyle(
                'TableCellStyle', parent=styles['Normal'],
                fontName='Helvetica', fontSize=9, leading=12, alignment=0
            )

            total_style = ParagraphStyle(
                'TotalStyle', parent=styles['Normal'],
                fontName='Helvetica-Bold', fontSize=11, leading=14,
                alignment=2, textColor=colors.HexColor('#27ae60')
            )

            montant_lettres_style = ParagraphStyle(
                'MontantLettresStyle', parent=styles['Normal'],
                fontName='Helvetica-Bold', fontSize=11, leading=16,
                alignment=1, spaceAfter=20, textColor=colors.HexColor('#2c3e50')
            )

            # =====================================================================
            # EN-TÊTE - COMMUN À TOUS
            # =====================================================================
            company = ctx['company']

            # Logo
            if company.get('logo_path') and os.path.exists(company['logo_path']):
                try:
                    logo = Image(company['logo_path'], width=2.5 * cm, height=1.5 * cm)
                    logo.hAlign = 'LEFT'
                    story.append(logo)
                except Exception as e:
                    logger.error("Erreur chargement logo: %s", e)
                    story.append(Paragraph(f"<b>{company.get('nom', '')}</b>", title_style))
            else:
                story.append(Paragraph(f"<b>{company.get('nom', '')}</b>", title_style))

            story.append(Spacer(1, 0.2 * cm))

            # Informations entreprise
            infos_entreprise = [
                "<b>Entreprise de nettoyage – travaux & services</b>",
                f"Adresse : {company.get('adresse', '22 Rue deux piliers Bouzaréah 16006 Alger Algérie')}",
                f"Phone : {company.get('telephone', '05552 88 30 50 / 0777 98 90 58')}",
            ]

            if is_beni_messous:
                infos_entreprise.append(
                    f"N.R.C {company.get('rc', '16/00 0980844B08')} N°article : {company.get('art', '16119102314')}"
                )
                infos_entreprise.append(
                    f"N.I.F {company.get('nif', '000816098084472')} N.I.S {company.get('nis', '0008 1611 01973 48')}"
                )
                infos_entreprise.append(
                    f"E-mail : {company.get('email', 'entsnet7@gmail.com')} Web site : www.entsnet.com"
                )
            else:
                infos_entreprise.append(
                    f"N.R.C {company.get('rc', '16/00 0980844B08')}   N°article : {company.get('art', '16119102314')}"
                )
                infos_entreprise.append(
                    f"N.I.F {company.get('nif', '000816098084472')}   N.I.S {company.get('nis', '0008 1611 01973 48')}"
                )
                infos_entreprise.append(
                    f"E-mail : {company.get('email', 'entsnet7@gmail.com')}   Web site : www.entsnet.com"
                )

            # Informations bancaires
            rib_text = company.get('rib', '')
            banque_text = company.get('banque', '')
            compte_ccp_text = company.get('compte_ccp', '')
            ccp_banque_text = company.get('ccp_banque', '')
            adresse_banque_text = company.get('adresse_banque', '')

            if is_beni_messous:
                if compte_ccp_text and banque_text and rib_text:
                    infos_entreprise.append(
                        f"Compte CCP N° {compte_ccp_text} Banque {banque_text} {rib_text}"
                    )
            else:
                infos_bancaires = []
                if compte_ccp_text:
                    infos_bancaires.append(f"CCP {compte_ccp_text}")
                if banque_text:
                    infos_bancaires.append(f"Compte Banque {banque_text}")
                if rib_text:
                    infos_bancaires.append(f"RIB {rib_text}")

                if infos_bancaires:
                    infos_entreprise.append("&nbsp;|&nbsp;".join(infos_bancaires))

            for info in infos_entreprise:
                if info.strip():
                    story.append(Paragraph(info, compact_style))

            story.append(Spacer(1, 0.1 * cm))

            # Ligne de séparation
            sep = Table([['']], colWidths=[19 * cm])
            sep.setStyle(TableStyle([
                ('LINEBELOW', (0, 0), (0, 0), 0.8, colors.HexColor('#bdc3c7')),
                ('BOTTOMPADDING', (0, 0), (0, 0), 0.2),
                ('TOPPADDING', (0, 0), (0, 0), 0.2),
            ]))
            story.append(sep)
            story.append(Spacer(1, 0.1 * cm))

            # =====================================================================
            # EN-TÊTE DE LA FACTURE
            # =====================================================================
            invoice = ctx['invoice']
            contrat_ctx = ctx.get('contrat') or {}
            client = ctx['client']

            # Numéro de facture
            if is_beni_messous:
                header_data = [
                    [Paragraph(f"FACTURE N° {invoice['number']}", title_style),
                    Paragraph(f"Date : {invoice['date']}", date_style)]
                ]
                header_table = Table(header_data, colWidths=[None, None])
                header_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('LEFTPADDING', (0, 0), (0, 0), 0),
                    ('RIGHTPADDING', (1, 0), (1, 0), 0),
                ]))
                story.append(header_table)

            story.append(Spacer(1, 0.2 * cm))

            # =====================================================================
            # RÉCUPÉRATION DES DONNÉES COMMUNES
            # =====================================================================
            items = ctx['items']
            summary = ctx['summary']

            # =====================================================================
            # SECTION SPÉCIFIQUE BENI MESSOUS
            # =====================================================================
            if is_beni_messous:
                # Données réelles du contrat
                numero_marche    = contrat_ctx.get('numero_marche', '')
                numero_ods       = contrat_ctx.get('numero_ods', '')
                date_ods         = contrat_ctx.get('date_ods', '')
                client_name_display = client.get('name', '')

                story.append(Paragraph(
                    f"Relative au marché N°{numero_marche} N° ODS : {numero_ods} {client_name_display} du {date_ods}",
                    normal_style
                ))
                story.append(Spacer(1, 0.1 * cm))

                objet_ods = contrat_ctx.get('objet_ods', '')
                if objet_ods:
                    story.append(Paragraph(objet_ods, normal_style))
                else:
                    story.append(Paragraph(
                        "La prise en charge des prestations de nettoyage des services du CHU de BENI MESSOUS LOTS N°03",
                        normal_style
                    ))
                story.append(Spacer(1, 0.2 * cm))

                # FIX 5: imports déplacés en haut du fichier (datetime, calendar)
                invoice_date = datetime.strptime(invoice['date'], "%d/%m/%Y")

                mois_actuel = invoice_date.strftime("%B %Y").upper()
                dernier_jour = calendar.monthrange(invoice_date.year, invoice_date.month)[1]

                line1_data = [
                    [Paragraph("<b>Droit :</b>", normal_bold_style),
                    Paragraph(f"<b>PERIODE : {mois_actuel}</b>", normal_bold_style)]
                ]
                line1_table = Table(line1_data, colWidths=[8 * cm, 8 * cm])
                line1_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('LEFTPADDING', (0, 0), (0, 0), 0),
                    ('RIGHTPADDING', (1, 0), (1, 0), 0),
                ]))
                story.append(line1_table)
                story.append(Spacer(1, 0.1 * cm))

                date_text = f"DU 01/{invoice_date.strftime('%m/%Y')} AU {dernier_jour:02d}/{invoice_date.strftime('%m/%Y')}"
                line2_data = [
                    [Paragraph(f"<b>{client_name_display}</b>", normal_bold_style),
                    Paragraph(date_text, normal_style)]
                ]
                line2_table = Table(line2_data, colWidths=[8 * cm, 8 * cm])
                line2_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('LEFTPADDING', (0, 0), (0, 0), 0),
                    ('RIGHTPADDING', (1, 0), (1, 0), 0),
                ]))
                story.append(line2_table)
                story.append(Spacer(1, 0.3 * cm))

                # =====================================================================
                # TABLEAU BENI MESSOUS
                # =====================================================================
                nb_jours_mois = calendar.monthrange(invoice_date.year, invoice_date.month)[1]

                table_data = []
                headers = [
                    "Désignation du service",
                    "Tranche horaire",
                    "Nombre d'agents",
                    "Prix U /jour",
                    "NOMBRE DE JOUR",
                    "Montant HT"
                ]
                table_data.append(headers)

                for item in items:
                    description = item['description']
                    montant_ht = item['total_ht']

                    designation = description
                    tranche = "Journée"
                    nb_agents = int(item['quantity'])
                    prix_jour = item['unit_price']
                    nb_jours = nb_jours_mois

                    if " - " in description:
                        parts = description.split(" - ")
                        if len(parts) >= 1:
                            designation = parts[0]
                        if len(parts) >= 2:
                            tranche = parts[1]
                        if len(parts) >= 3:
                            try:
                                nb_agents = int(parts[2])
                            except (ValueError, TypeError):
                                pass
                        if len(parts) >= 4:
                            try:
                                prix_jour = float(parts[3].replace(" ", ""))
                            except (ValueError, TypeError):
                                pass
                        if len(parts) >= 5:
                            try:
                                nb_jours = int(parts[4])
                            except (ValueError, TypeError):
                                pass

                    row = [
                        designation,
                        tranche,
                        f"{nb_agents:,.0f}",
                        f"{prix_jour:,.2f}".replace(",", " "),
                        str(nb_jours),
                        f"{montant_ht:,.2f}".replace(",", " ")
                    ]
                    table_data.append(row)

                for i in range(max(0, 7 - len(items))):
                    table_data.append(["", "", "", "", "", ""])

                table_data.append(['Montant Total (HT)', '', '', '', '', f"{summary['subtotal']:,.2f}".replace(",", " ")])
                table_data.append(['Montant TVA 19 %', '', '', '', '', f"{summary['tax']:,.2f}".replace(",", " ")])
                table_data.append(['Total (TTC)', '', '', '', '', f"{summary['total']:,.2f}".replace(",", " ")])

                col_widths = [6.5 * cm, 2.5 * cm, 1.8 * cm, 2.2 * cm, 2.0 * cm, 2.2 * cm]

                items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
                items_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                    ('ALIGN', (2, 1), (2, -1), 'CENTER'),
                    ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                    ('ALIGN', (4, 1), (4, -1), 'CENTER'),
                    ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
                    ('FONTNAME', (0, 1), (-1, -4), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -4), 8),
                    ('VALIGN', (0, 1), (-1, -4), 'MIDDLE'),
                    ('SPAN', (0, -3), (4, -3)),
                    ('SPAN', (0, -2), (4, -2)),
                    ('SPAN', (0, -1), (4, -1)),
                    ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
                    ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor('#f8f9fa')),
                    ('ALIGN', (0, -3), (4, -1), 'RIGHT'),
                    ('ALIGN', (5, -3), (5, -1), 'RIGHT'),
                    ('GRID', (0, 1), (-1, -4), 0.5, colors.HexColor('#cccccc')),
                    ('LINEBELOW', (0, -4), (-1, -4), 1, colors.HexColor('#000000')),
                    ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#000000')),
                ]))

                story.append(items_table)
                story.append(Spacer(1, 2.5 * cm))

            else:
                story.append(Paragraph(f"FACTURE N° {invoice['number']}", title_style))
                story.append(Spacer(1, 0.2 * cm))

                story.append(Paragraph(f"Date : {invoice['date']}", date_style))
                story.append(Spacer(1, 0.3 * cm))

                # Ligne ODS - toujours affichée
                numero_ods = (contrat_ctx.get('numero_ods') or '').strip()
                date_ods_val = (contrat_ctx.get('date_ods') or '').strip()
                objet = (contrat_ctx.get('objet_ods') or '').strip()

                if numero_ods:
                    if date_ods_val:
                        ods_text = f"<b>Relative au N°ODS :</b> {numero_ods} {client.get('name', '')} du {date_ods_val}"
                    else:
                        ods_text = f"<b>Relative au N°ODS :</b> {numero_ods} {client.get('name', '')}"

                    story.append(Paragraph(ods_text, normal_style))
                    story.append(Paragraph(
                        f"<b>Objet :</b> {objet}" if objet else "<b>Objet :</b> Prestations de nettoyage",
                        normal_style
                    ))
                    story.append(Spacer(1, 0.3 * cm))

                # ── DOIT + Période sur la même ligne ────────────────────
                show_periode = invoice.get('show_periode', False)
                if show_periode:
                    periode_du_val = invoice.get('periode_du', '')
                    periode_au_val = invoice.get('periode_au', '')
                    periode_right_style = ParagraphStyle(
                        'PeriodeRight', parent=normal_bold_style,
                        fontSize=10, alignment=2
                    )
                    doit_left_style = ParagraphStyle(
                        'DoitLeft', parent=subtitle_style,
                        alignment=0
                    )
                    doit_row = [[
                        Paragraph("DOIT :", doit_left_style),
                        Paragraph(
                            f"<b>Période : du {periode_du_val} au {periode_au_val}</b>",
                            periode_right_style
                        ),
                    ]]
                    doit_table = Table(doit_row, colWidths=[4 * cm, 13.2 * cm])
                    doit_table.setStyle(TableStyle([
                        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING',  (0, 0), (0, 0),   0),
                        ('RIGHTPADDING', (1, 0), (1, 0),   0),
                    ]))
                    story.append(doit_table)
                else:
                    story.append(Paragraph("DOIT :", subtitle_style))
                story.append(Paragraph(f"<b>{client.get('name', '')}</b>", normal_bold_style))
                story.append(Spacer(1, 0.4 * cm))

                # ===== NOUVEAU TABLEAU AVEC GESTION DES TEXTES LONGS =====

                # Style pour les cellules du tableau
                # ===== TABLEAU STANDARD AVEC WRAPPING AUTOMATIQUE =====

                cell_style = ParagraphStyle(
                    'CellStyle',
                    parent=normal_style,
                    fontSize=12,
                    leading=16,
                    alignment=0,
                    wordWrap='LTR',
                )

                cell_style_center = ParagraphStyle(
                    'CellStyleCenter',
                    parent=cell_style,
                    fontSize=12,
                    leading=16,
                    alignment=1,
                )

                cell_style_right = ParagraphStyle(
                    'CellStyleRight',
                    parent=cell_style,
                    fontSize=12,
                    leading=16,
                    alignment=2,
                )

                total_style_right = ParagraphStyle(
                    'TotalRight',
                    parent=cell_style,
                    fontSize=12,
                    leading=16,
                    alignment=2,
                    fontName='Helvetica-Bold',
                )

                # En-tête
                table_data = [[
                    Paragraph("Désignation", cell_style),
                    Paragraph("Nbre mois", cell_style_center),
                    Paragraph("Prix unité", cell_style_right),
                    Paragraph("Total HT", cell_style_right),
                ]]

                # Lignes articles — PAS de rowHeights fixé, ReportLab calcule automatiquement
                for item in items:
                    table_data.append([
                        Paragraph(item['description'], cell_style),
                        Paragraph(f"{item['quantity']:,.0f}", cell_style_center),
                        Paragraph(f"{item['unit_price']:,.2f} DA".replace(",", " "), cell_style_right),
                        Paragraph(f"{item['total_ht']:,.2f} DA".replace(",", " "), cell_style_right),
                    ])

                # Lignes vides pour atteindre le minimum de 8 lignes
                min_rows = 6
                row_heights = [None]  # en-tête : hauteur auto

                for item in items:
                    row_heights.append(None)  # lignes articles : hauteur auto selon contenu

                EMPTY_ROW_HEIGHT = 1.0 * cm  # hauteur des lignes vides
                for _ in range(max(0, min_rows - len(items))):
                    table_data.append([
                        Paragraph("", cell_style),
                        Paragraph("", cell_style_center),
                        Paragraph("", cell_style_right),
                        Paragraph("", cell_style_right),
                    ])
                    row_heights.append(EMPTY_ROW_HEIGHT)

                first_total_row = len(table_data)

                # lignes totaux : hauteur auto
                row_heights.append(None)  # sous-total
                row_heights.append(None)  # TVA
                row_heights.append(None)  # total TTC

                # Sous-total HT
                table_data.append([
                    Paragraph("", cell_style),
                    Paragraph("", cell_style_center),
                    Paragraph("Sous-total HT", total_style_right),
                    Paragraph(f"{summary['subtotal']:,.2f} DA".replace(",", " "), total_style_right),
                ])

                # TVA
                tax_rate_display = f"{items[0]['tax_rate']:.0f}" if items else "19"
                table_data.append([
                    Paragraph("", cell_style),
                    Paragraph("", cell_style_center),
                    Paragraph(f"TVA ({tax_rate_display}%)", total_style_right),
                    Paragraph(f"{summary['tax']:,.2f} DA".replace(",", " "), total_style_right),
                ])

                # Total TTC
                table_data.append([
                    Paragraph("", cell_style),
                    Paragraph("", cell_style_center),
                    Paragraph("Total TTC", total_style_right),
                    Paragraph(f"{summary['total']:,.2f} DA".replace(",", " "), total_style_right),
                ])

                r0 = first_total_row
                r1 = first_total_row + 1
                r2 = first_total_row + 2

                col_widths = [8.5 * cm, 2.8 * cm, 3.2 * cm, 4.5 * cm]

                # ⚠️ PAS de rowHeights → ReportLab adapte automatiquement selon le contenu
                # APRÈS
                items_table = Table(table_data, colWidths=col_widths, repeatRows=1, rowHeights=row_heights)

                items_table.setStyle(TableStyle([
                    # En-tête
                    ('BACKGROUND',     (0, 0),  (-1, 0),   colors.HexColor('#d0d8e4')),
                    ('TEXTCOLOR',      (0, 0),  (-1, 0),   colors.HexColor('#1a252f')),
                    ('FONTNAME',       (0, 0),  (-1, 0),   'Helvetica-Bold'),
                    ('FONTSIZE',       (0, 0),  (-1, 0),   12),
                    ('ALIGN',          (0, 0),  (-1, 0),   'CENTER'),
                    ('VALIGN',         (0, 0),  (-1, 0),   'MIDDLE'),
                    ('TOPPADDING',     (0, 0),  (-1, 0),   6),
                    ('BOTTOMPADDING',  (0, 0),  (-1, 0),   6),

                    # Données
                    ('VALIGN',         (0, 1),  (-1, r0-1), 'TOP'),
                    ('TOPPADDING',     (0, 1),  (-1, r0-1), 5),
                    ('BOTTOMPADDING',  (0, 1),  (-1, r0-1), 5),
                    ('LEFTPADDING',    (0, 0),  (-1, -1),   5),
                    ('RIGHTPADDING',   (0, 0),  (-1, -1),   5),

                    # Alternance couleurs
                    *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f9fafb'))
                    for i in range(2, r0, 2)],

                    # Grille données
                    ('GRID',           (0, 0),  (-1, r0-1), 0.5, colors.HexColor('#cccccc')),

                    # Séparateur avant totaux
                    ('LINEABOVE',      (0, r0), (-1, r0),   1.5, colors.HexColor('#2c3e50')),

                    # Zone totaux
                    ('BACKGROUND',     (0, r0), (-1, r2),   colors.HexColor('#f0f2f5')),
                    ('FONTNAME',       (0, r0), (-1, r2),   'Helvetica-Bold'),
                    ('FONTSIZE',       (0, r0), (-1, r2),   9),
                    ('VALIGN',         (0, r0), (-1, r2),   'MIDDLE'),
                    ('TOPPADDING',     (0, r0), (-1, r2),   4),
                    ('BOTTOMPADDING',  (0, r0), (-1, r2),   4),
                    ('ALIGN',          (2, r0), (3, r2),    'RIGHT'),

                    # Total TTC plus marqué
                    ('BACKGROUND',     (0, r2), (-1, r2),   colors.HexColor('#e8eaed')),
                    ('FONTSIZE',       (0, r2), (-1, r2),   10),
                    ('LINEABOVE',      (0, r1), (-1, r1),   0.3, colors.HexColor('#adb5bd')),
                    ('LINEABOVE',      (0, r2), (-1, r2),   0.8, colors.HexColor('#2c3e50')),

                    # Boîte extérieure
                    ('BOX',            (0, 0),  (-1, -1),   1.2, colors.HexColor('#2c3e50')),
                ]))

                story.append(items_table)
                story.append(Spacer(1, 0.8 * cm))

            # =====================================================================
            # MONTANT EN LETTRES
            # =====================================================================
            montant_lettres = self.montant_en_lettres(summary['total'])
            story.append(Paragraph(
                f"Arrêté la présente facture à la somme de : {montant_lettres}",
                montant_lettres_style
            ))

            # =====================================================================
            # PIED DE PAGE
            # =====================================================================
            def draw_footer(canvas_obj, doc_obj):
                canvas_obj.saveState()

                page_width, _ = A4
                footer_y_start = 0.7 * cm

                adresse = company.get('adresse', '22 Rue deux piliers Bouzaréah 16006 Alger Algérie')
                telephone = company.get('telephone', '05552 88 30 50 / 0777 98 90 58')
                rc = company.get('rc', '16/00 0980844B08')
                nif = company.get('nif', '000816098084472')
                nis = company.get('nis', '0008 1611 01973 48')
                art = company.get('art', '16119102314')
                email = company.get('email', 'entsnet7@gmail.com')

                banque_text = company.get('banque', 'BEA')
                compte_ccp_text = company.get('compte_ccp', '391677 CLE 39')
                ccp_banque_text = company.get('ccp_banque', '')
                adresse_banque_text = company.get('adresse_banque', '11 lotissement benhaddadi said cheraga Alger')
                rib_text = company.get('rib', '00039167700000391677')

                ligne_bancaire = []
                if banque_text:
                    ligne_bancaire.append(f"Compte Banque {banque_text}")
                if rib_text:
                    ligne_bancaire.append(f"RIB : {rib_text}")
                if ccp_banque_text:
                    ligne_bancaire.append(f"CCP Banque : {ccp_banque_text}")

                ligne_bancaire_str = "  ".join(ligne_bancaire) if ligne_bancaire else ""

                footer_lines = [
                    "Entreprise de nettoyage – travaux & services",
                    f"Adresse : {adresse}",
                    f"Phone : {telephone}  N.R.C  {rc}    N°article  {art}",
                    f"N.I.F   {nif}   N.I.S   {nis},   Email : {email}",
                ]

                if ligne_bancaire_str:
                    footer_lines.append(ligne_bancaire_str)

                if adresse_banque_text:
                    footer_lines.append(f"Adresse de la banque : {adresse_banque_text}")

                line_height = 0.4 * cm
                total_footer_height = len(footer_lines) * line_height

                sep_y = footer_y_start + total_footer_height + 0.2 * cm
                canvas_obj.setStrokeColor(colors.HexColor('#bdc3c7'))
                canvas_obj.setLineWidth(0.5)
                canvas_obj.line(1.0 * cm, sep_y, page_width - 1.0 * cm, sep_y)

                canvas_obj.setFont("Helvetica", 11)
                canvas_obj.setFillColor(colors.HexColor('#7f8c8d'))

                for i, line in enumerate(reversed(footer_lines)):
                    y = footer_y_start + i * line_height
                    canvas_obj.drawCentredString(page_width / 2, y, line)

                canvas_obj.restoreState()

            # Génération finale
            doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)

            QMessageBox.information(
                self, "Succès",
                f"PDF exporté avec succès !\n\nFichier : {file_path}"
            )

        except ImportError:
            QMessageBox.critical(self, "Erreur",
                "ReportLab n'est pas installé.\n\nVeuillez installer : pip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export PDF:\n{str(e)}")
            import traceback
            traceback.print_exc()

                # ── Aperçu QTextDocument ──────────────────────────────────────────────────

    def _preview_with_textdocument(self, html: str):
        dlg = QDialog(self)
        dlg.setWindowTitle("Aperçu - Facture")
        dlg.setModal(True)
        dlg.setMinimumSize(1000, 800)

        layout = QVBoxLayout()
        browser = QTextBrowser()
        browser.setHtml(html)
        layout.addWidget(browser)

        btns = QHBoxLayout()
        btn_print = QPushButton("🖨️ Imprimer")
        btn_pdf   = QPushButton("📄 Exporter PDF")
        btn_close = QPushButton("✕ Fermer")

        for btn in [btn_print, btn_pdf, btn_close]:
            btn.setMinimumHeight(40)

        btn_print.setStyleSheet("""
            QPushButton { background:#3498db; color:white; border:none; padding:10px 20px; border-radius:6px; font-weight:bold; }
            QPushButton:hover { background:#2980b9; }
        """)
        btn_pdf.setStyleSheet("""
            QPushButton { background:#27ae60; color:white; border:none; padding:10px 20px; border-radius:6px; font-weight:bold; }
            QPushButton:hover { background:#219653; }
        """)
        btn_close.setStyleSheet("""
            QPushButton { background:#95a5a6; color:white; border:none; padding:10px 20px; border-radius:6px; font-weight:bold; }
            QPushButton:hover { background:#7f8c8d; }
        """)

        def do_print():
            doc = QTextDocument()
            doc.setHtml(html)
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                doc.print(printer)

        def do_pdf():
            path, _ = QFileDialog.getSaveFileName(
                self, "Exporter en PDF",
                f"{self.invoice_number.text()}.pdf",
                "PDF Files (*.pdf)"
            )
            if not path:
                return
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            doc = QTextDocument()
            doc.setHtml(html)
            try:
                doc.print(printer)
                QMessageBox.information(self, "Export PDF", f"PDF enregistré:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible d'exporter en PDF:\n{e}")

        # ✅ Connexions AU MÊME NIVEAU que les définitions de fonctions (pas à l'intérieur de do_pdf)
        btn_print.clicked.connect(do_print)
        btn_pdf.clicked.connect(do_pdf)
        btn_close.clicked.connect(dlg.accept)

        btns.addWidget(btn_print)
        btns.addWidget(btn_pdf)
        btns.addStretch()
        btns.addWidget(btn_close)

        layout.addLayout(btns)
        dlg.setLayout(layout)
        dlg.exec()

            # ── Aperçu WebEngine ──────────────────────────────────────────────────────

    def _preview_with_webengine(self, html: str):
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
        except Exception:
            return self._preview_with_textdocument(html)

        view = QWebEngineView()
        view.setHtml(html, QUrl.fromLocalFile(os.path.abspath(ASSETS_DIR)))

        dlg = QDialog(self)
        dlg.setWindowTitle("Aperçu (Web) - Facture")
        dlg.setModal(True)
        dlg.setMinimumSize(1100, 850)

        layout = QVBoxLayout()
        layout.addWidget(view)

        btns = QHBoxLayout()
        btn_pdf = QPushButton("📄 Exporter PDF")
        btn_print = QPushButton("🖨️ Imprimer")
        btn_close = QPushButton("✕ Fermer")

        for btn in [btn_pdf, btn_print, btn_close]:
            btn.setMinimumHeight(40)

        btn_pdf.setStyleSheet("""
            QPushButton { background:#27ae60; color:white; border:none; padding:10px 20px; border-radius:6px; font-weight:bold; }
            QPushButton:hover { background:#219653; }
        """)
        btn_print.setStyleSheet("""
            QPushButton { background:#3498db; color:white; border:none; padding:10px 20px; border-radius:6px; font-weight:bold; }
            QPushButton:hover { background:#2980b9; }
        """)
        btn_close.setStyleSheet("""
            QPushButton { background:#95a5a6; color:white; border:none; padding:10px 20px; border-radius:6px; font-weight:bold; }
            QPushButton:hover { background:#7f8c8d; }
        """)

        def export_pdf():
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exporter en PDF",
                f"{self.invoice_number.text()}.pdf",
                "PDF Files (*.pdf)"
            )
            if not file_path:
                return
            page = view.page()

            def handle_pdf(result):
                try:
                    if isinstance(result, (bytes, bytearray)):
                        with open(file_path, "wb") as f:
                            f.write(result)
                        QMessageBox.information(self, "Export PDF", f"PDF enregistré:\n{file_path}")
                    else:
                        page.printToPdf(file_path)
                        QMessageBox.information(self, "Export PDF", f"PDF enregistré:\n{file_path}")
                except Exception as ex:
                    QMessageBox.critical(self, "Erreur", f"Erreur écriture PDF:\n{ex}")

                try:
                    page.printToPdf(handle_pdf)
                except TypeError:
                    try:
                        page.printToPdf(file_path)
                        QMessageBox.information(self, "Export PDF", f"PDF enregistré:\n{file_path}")
                    except Exception as ex:
                        QMessageBox.critical(self, "Erreur", f"Impossible d'exporter en PDF:\n{ex}")

                btn_pdf.clicked.connect(export_pdf)
                btn_print.clicked.connect(lambda: view.page().printToPdf(lambda _: None))
                btn_close.clicked.connect(dlg.accept)

                btns.addWidget(btn_pdf)
                btns.addWidget(btn_print)
                btns.addStretch()
                btns.addWidget(btn_close)

                layout.addLayout(btns)
                dlg.setLayout(layout)
                dlg.exec()

    def export_pdf(self):
        """Exporter la facture en PDF"""
        self.export_pdf_reportlab()


        # ══════════════════════════════════════════════════════════════════════════════
        # Vue principale
        # ══════════════════════════════════════════════════════════════════════════════