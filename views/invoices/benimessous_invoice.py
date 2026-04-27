# views/benimessous_invoice.py - Version avec le format exact du PDF

import os
import datetime
from decimal import Decimal
import calendar

from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QLineEdit, QLabel, QFormLayout, QComboBox,
    QTextEdit, QDoubleSpinBox, QHeaderView, QTabWidget, QSizePolicy,
    QGroupBox, QDateEdit, QFileDialog, QSpinBox, QDialogButtonBox, QCheckBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate

from database.db import SessionLocal
from models.client import Client
from models.invoice import Invoice, InvoiceItem, InvoicePayment
from models.enums import InvoiceStatus, PaymentMethod
from models.company import CompanyInfo
from models.contrat import Contrat


class BeniMessousInvoiceDialog(QDialog):
    """Dialogue pour les factures spéciales CHU Beni Messous"""
    
    invoice_saved = pyqtSignal()
    
    def __init__(self, client_id=None, contrat_id=None, invoice_id=None, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.contrat_id = contrat_id
        self.invoice_id = invoice_id
        self.items = []
        self.entreprise_info = self.load_entreprise_info()
        
        self.setWindowTitle("Facture CHU Beni Messous")
        self.setModal(True)
        self.setMinimumSize(1100, 850)
        
        self.init_ui()
        # Charger les données si c'est une modification
        if invoice_id:
            self.load_data()
        else:
            # Nouvelle facture
            self.generate_invoice_number()
            if client_id:
                self.set_client(client_id)
    
    def load_entreprise_info(self):
        """Charger les informations de l'entreprise"""
        session = SessionLocal()
        try:
            company = session.query(CompanyInfo).first()
            if company:
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
                    'rib': company.rib or "",
                    'banque': company.banque or "",
                    'compte_ccp': getattr(company, 'compte_ccp', "") or "",
                    'nom_directeur': company.nom_directeur or "",
                    'fonction_directeur': company.fonction_directeur or "",
                    'logo_path': company.logo_path if company.logo_path and os.path.exists(company.logo_path) else None
                }
            return {}
        finally:
            session.close()
    
    def init_ui(self):
        from PyQt6.QtWidgets import (
            QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
            QLineEdit, QTextEdit, QComboBox, QCheckBox,
            QPushButton, QGroupBox, QDateEdit, QTableWidget,
            QHeaderView, QSizePolicy, QScrollArea, QWidget
        )
        from PyQt6.QtCore import Qt, QDate

        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        # ===================== MAIN LAYOUT =====================
        main_layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)

        # ===================== TITRE =====================
        title = QLabel("🏥 FACTURE CHU BENI MESSOUS")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 5px solid #9b59b6;
        """)
        layout.addWidget(title)

        # ===================== CLIENT =====================
        client_group = QGroupBox("👤 CLIENT")
        client_layout = QGridLayout()
        client_layout.setColumnStretch(1, 1)
        client_layout.setColumnStretch(2, 1)

        self.client_combo = QComboBox()
        self.client_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.load_clients()
        self.client_combo.currentIndexChanged.connect(self.on_client_changed)

        self.invoice_number = QLineEdit()
        self.invoice_number.setReadOnly(True)
        self.invoice_number.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.chk_link_contrat = QCheckBox("Lier à un contrat")
        self.chk_link_contrat.toggled.connect(self.toggle_contrat)

        self.contrat_combo = QComboBox()
        self.contrat_combo.setEnabled(False)
        self.contrat_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.contrat_combo.currentIndexChanged.connect(self.on_contrat_changed)

        client_layout.addWidget(QLabel("Client *:"), 0, 0)
        client_layout.addWidget(self.client_combo, 0, 1, 1, 2)

        client_layout.addWidget(QLabel("N° Facture:"), 1, 0)
        client_layout.addWidget(self.invoice_number, 1, 1, 1, 2)

        client_layout.addWidget(self.chk_link_contrat, 2, 1, 1, 2)

        client_layout.addWidget(QLabel("Contrat:"), 3, 0)
        client_layout.addWidget(self.contrat_combo, 3, 1, 1, 2)

        client_group.setLayout(client_layout)
        layout.addWidget(client_group)

        # ===================== DATES =====================
        dates_group = QGroupBox("📅 DATES")
        dates_layout = QHBoxLayout()

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)

        self.due_date_edit = QDateEdit(QDate.currentDate().addDays(30))
        self.due_date_edit.setCalendarPopup(True)

        dates_layout.addWidget(QLabel("Date facture:"))
        dates_layout.addWidget(self.date_edit)
        dates_layout.addStretch()

        dates_layout.addWidget(QLabel("Date échéance:"))
        dates_layout.addWidget(self.due_date_edit)
        dates_layout.addStretch()

        dates_group.setLayout(dates_layout)
        layout.addWidget(dates_group)

        # ===================== INFOS =====================
        info_group = QGroupBox("📋 INFORMATIONS SPÉCIFIQUES")
        info_layout = QGridLayout()
        info_layout.setColumnStretch(1, 1)
        info_layout.setColumnStretch(3, 1)

        self.numero_marche = QLineEdit("")
        self.numero_marche.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.date_marche = QDateEdit(QDate(2025, 3, 27))
        self.date_marche.setCalendarPopup(True)

        self.numero_ods = QLineEdit("")
        self.numero_ods.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.date_ods = QDateEdit(QDate(2025, 3, 27))
        self.date_ods.setCalendarPopup(True)

        self.objet_ods = QTextEdit()
        self.objet_ods.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.objet_ods.setMinimumHeight(80)
        self.objet_ods.setText("")
        

        info_layout.addWidget(QLabel("N° Marché:"), 0, 0)
        info_layout.addWidget(self.numero_marche, 0, 1)

        info_layout.addWidget(QLabel("Date Marché:"), 0, 2)
        info_layout.addWidget(self.date_marche, 0, 3)

        info_layout.addWidget(QLabel("N° ODS:"), 1, 0)
        info_layout.addWidget(self.numero_ods, 1, 1)

        info_layout.addWidget(QLabel("Date ODS:"), 1, 2)
        info_layout.addWidget(self.date_ods, 1, 3)

        info_layout.addWidget(QLabel("Objet:"), 2, 0)
        info_layout.addWidget(self.objet_ods, 2, 1, 1, 3)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # ===================== TABLE SERVICES =====================
        table_group = QGroupBox("📋 SERVICES")
        table_layout = QVBoxLayout(table_group)

        # ---------- Barre d'outils ----------
        toolbar = QHBoxLayout()

        btn_add = QPushButton("➕ Ajouter service")
        btn_add.setStyleSheet(
            "background: #27ae60; color: white; padding: 8px 16px; "
            "border-radius: 6px; font-weight: bold;"
        )
        btn_add.clicked.connect(self.add_service)

        btn_remove = QPushButton("🗑️ Supprimer")
        btn_remove.setStyleSheet(
            "background: #e74c3c; color: white; padding: 8px 16px; "
            "border-radius: 6px; font-weight: bold;"
        )
        btn_remove.clicked.connect(self.remove_selected_service)

        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_remove)
        toolbar.addStretch()

        table_layout.addLayout(toolbar)

        # ---------- Tableau ----------
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(6)
        self.services_table.setRowCount(0)
        self.services_table.setMinimumHeight(250)

        self.services_table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.services_table.setHorizontalHeaderLabels([
            "Désignation du service",
            "Tranche horaire",
            "Nb agents",
            "Prix U/jour",
            "Nb jours",
            "Montant HT"
        ])

        header = self.services_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        table_layout.addWidget(self.services_table)

        # Ajouter le group principal
        layout.addWidget(table_group)

        # Donner plus d'espace au tableau
        layout.setStretchFactor(table_group, 3)

        # ===================== TOTAUX =====================
        totals_group = QGroupBox("🧮 TOTAUX")
        totals_layout = QGridLayout()
        totals_layout.setColumnStretch(1, 1)

        self.total_ht_label = QLabel("0.00 DA")
        self.tva_label = QLabel("0.00 DA")
        self.total_ttc_label = QLabel("0.00 DA")

        totals_layout.addWidget(QLabel("Montant HT:"), 0, 0)
        totals_layout.addWidget(self.total_ht_label, 0, 1)

        totals_layout.addWidget(QLabel("TVA 19%:"), 1, 0)
        totals_layout.addWidget(self.tva_label, 1, 1)

        totals_layout.addWidget(QLabel("Total TTC:"), 2, 0)
        totals_layout.addWidget(self.total_ttc_label, 2, 1)

        totals_group.setLayout(totals_layout)
        layout.addWidget(totals_group)

        layout.addStretch()

        # Boutons
        buttons = QHBoxLayout()
        
        btn_save = QPushButton("💾 Enregistrer")
        btn_save.setStyleSheet("background: #27ae60; color: white; padding: 12px 30px; border-radius: 6px; font-weight: bold; font-size: 14px;")
        btn_save.clicked.connect(self.save_invoice)
        
        btn_cancel = QPushButton("❌ Annuler")
        btn_cancel.setStyleSheet("background: #e74c3c; color: white; padding: 12px 20px; border-radius: 6px; font-weight: bold;")
        btn_cancel.clicked.connect(self.reject)
        
        buttons.addStretch()
        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)
        
        layout.addLayout(buttons)
        self.setLayout(layout)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.generate_invoice_number()

    def load_clients(self):
        """Charge la liste des clients actifs"""
        session = SessionLocal()
        try:
            clients = session.query(Client).filter(Client.est_actif == True).order_by(Client.raison_sociale).all()
            self.client_combo.clear()
            self.client_combo.addItem("-- Sélectionnez un client --", None)
            for client in clients:
                label = f"{client.raison_sociale} ({client.code_client})"
                self.client_combo.addItem(label, client.id)
            
            if self.client_id:
                self.set_client(self.client_id)
        finally:
            session.close()
    
    def set_client(self, client_id):
        """Sélectionne un client spécifique"""
        index = self.client_combo.findData(client_id)
        if index >= 0:
            self.client_combo.setCurrentIndex(index)
    
    def on_client_changed(self, index):
        """Quand le client change, recharge les contrats si nécessaire"""
        client_id = self.client_combo.currentData()
        if client_id and self.chk_link_contrat.isChecked():
            self.load_contrats(client_id)
        elif not client_id:
            self.contrat_combo.clear()
            self.contrat_combo.addItem("-- Sélectionnez un contrat --", None)
            self.clear_contrat_info()
    
    def toggle_contrat(self, checked):
        """Active/désactive la sélection de contrat"""
        self.contrat_combo.setEnabled(checked)
        if checked:
            # Si coché, charger les contrats du client sélectionné
            client_id = self.client_combo.currentData()
            if client_id:
                self.load_contrats(client_id)
            else:
                QMessageBox.warning(self, "Attention", "Veuillez d'abord sélectionner un client")
                self.chk_link_contrat.setChecked(False)
        else:
            # Si décoché, vider les champs et le combobox
            self.contrat_combo.clear()
            self.contrat_combo.addItem("-- Sélectionnez un contrat --", None)
            self.clear_contrat_info()
    
    def load_contrats(self, client_id):
        """Charge les contrats du client"""
        session = SessionLocal()
        try:
            from models.contrat import Contrat
            from models.enums import StatutContrat
            contrats = session.query(Contrat).filter(
                Contrat.client_id == client_id,
                Contrat.statut == StatutContrat.ACTIF
            ).order_by(Contrat.date_debut.desc()).all()
            
            self.contrat_combo.clear()
            self.contrat_combo.addItem("-- Sélectionnez un contrat --", None)
            
            if contrats:
                for contrat in contrats:
                    # Déterminer le type pour l'affichage
                    type_display = ""
                    if contrat.type_document == "Marché public" and contrat.numero_marche:
                        type_display = f" (Marché {contrat.numero_marche})"
                    elif contrat.type_document == "Convention" and contrat.numero_convention:
                        type_display = f" (Convention {contrat.numero_convention})"
                    elif contrat.numero_ods:
                        type_display = f" (ODS {contrat.numero_ods})"
                    
                    label = f"{contrat.numero_contrat}{type_display} - {contrat.type_document}"
                    self.contrat_combo.addItem(label, contrat.id)
                print(f"✅ {len(contrats)} contrat(s) chargé(s)")
            else:
                print(f"ℹ️ Aucun contrat actif pour ce client")
                
        except Exception as e:
            print(f"❌ Erreur chargement contrats: {e}")
        finally:
            session.close()

    # views/benimessous_invoice.py - Ajouter cette méthode

    def load_contrat_info(self, contrat_id):
        """Charge les informations du contrat sélectionné"""
        if not contrat_id:
            return
        
        session = SessionLocal()
        try:
            contrat = session.query(Contrat).filter(Contrat.id == contrat_id).first()
            if contrat:
                print(f"📋 Chargement du contrat: {contrat.numero_contrat}")
                print(f"   Type document: {contrat.type_document}")
                print(f"   N° marché: {contrat.numero_marche}")
                print(f"   Date marché: {contrat.date_marche}")
                print(f"   N° ODS: {contrat.numero_ods}")
                print(f"   Date ODS: {contrat.date_ods}")
                print(f"   Objet ODS: {contrat.objet_ods}")
                
                # N° Marché (priorité au marché, puis convention)
                if contrat.numero_marche:
                    self.numero_marche.setText(contrat.numero_marche)
                    print(f"   ✅ N° Marché chargé: {contrat.numero_marche}")
                elif contrat.numero_convention:
                    self.numero_marche.setText(contrat.numero_convention)
                    print(f"   ✅ N° Convention chargé: {contrat.numero_convention}")
                else:
                    self.numero_marche.setText("")
                
                # Date Marché
                if contrat.date_marche:
                    self.date_marche.setDate(QDate(
                        contrat.date_marche.year,
                        contrat.date_marche.month,
                        contrat.date_marche.day
                    ))
                    print(f"   ✅ Date Marché chargée: {contrat.date_marche}")
                elif contrat.date_convention:
                    self.date_marche.setDate(QDate(
                        contrat.date_convention.year,
                        contrat.date_convention.month,
                        contrat.date_convention.day
                    ))
                    print(f"   ✅ Date Convention chargée: {contrat.date_convention}")
                else:
                    self.date_marche.setDate(QDate.currentDate())
                
                # N° ODS
                if contrat.numero_ods:
                    self.numero_ods.setText(contrat.numero_ods)
                    print(f"   ✅ N° ODS chargé: {contrat.numero_ods}")
                else:
                    self.numero_ods.setText("")
                
                # Date ODS
                if contrat.date_ods:
                    self.date_ods.setDate(QDate(
                        contrat.date_ods.year,
                        contrat.date_ods.month,
                        contrat.date_ods.day
                    ))
                    print(f"   ✅ Date ODS chargée: {contrat.date_ods}")
                else:
                    self.date_ods.setDate(QDate.currentDate())
                
                # Objet ODS
                if contrat.objet_ods:
                    self.objet_ods.setText(contrat.objet_ods)
                    print(f"   ✅ Objet ODS chargé: {contrat.objet_ods[:50]}...")
                else:
                    self.objet_ods.setText("")
                    
        except Exception as e:
            print(f"❌ Erreur chargement contrat: {e}")
            import traceback
            traceback.print_exc()
        finally:
            session.close()

    def generate_invoice_number(self):
        """Génère un numéro de facture simple au format 001/2026"""
        session = SessionLocal()
        try:
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
            print(f"❌ Erreur génération numéro: {e}")
            # Numéro de secours
            numero = f"001/{datetime.date.today().year}"
            self.invoice_number.setText(numero)
        finally:
            session.close()
    
    def add_service(self):
        """Ouvre le dialogue pour ajouter un service"""
        from .benimessous_service_dialog import BeniMessousServiceDialog
        dialog = BeniMessousServiceDialog(self)
        if dialog.exec():
            service_data = dialog.get_service_data()
            
            # Ajouter une nouvelle ligne
            row = self.services_table.rowCount()
            self.services_table.insertRow(row)
            
            # Remplir les cellules
            self.services_table.setItem(row, 0, QTableWidgetItem(service_data['designation']))
            self.services_table.setItem(row, 1, QTableWidgetItem(service_data['tranche']))
            self.services_table.setItem(row, 2, QTableWidgetItem(str(service_data['agents'])))
            self.services_table.setItem(row, 3, QTableWidgetItem(f"{service_data['prix']:,.2f}".replace(",", " ")))
            self.services_table.setItem(row, 4, QTableWidgetItem(str(service_data['jours'])))
            self.services_table.setItem(row, 5, QTableWidgetItem(f"{service_data['montant']:,.2f}".replace(",", " ")))
            
            # Aligner les nombres à droite
            for col in [2, 3, 4, 5]:
                item = self.services_table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            self.calculate_totals()
    
    def remove_selected_service(self):
        """Supprime le service sélectionné"""
        selected = self.services_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un service à supprimer")
            return
        
        row = selected[0].row()
        self.services_table.removeRow(row)
        self.calculate_totals()
    
    def calculate_row(self, row, col):
        """Calcule le montant HT pour une ligne"""
        # Cette méthode est appelée quand une cellule est modifiée
        # On recalcule le montant HT
        self.calculate_totals()
    
    def calculate_totals(self):
        """Calcule les totaux et le montant en lettres"""
        total_ht = 0
        
        for row in range(self.services_table.rowCount()):
            item_agents = self.services_table.item(row, 2)
            item_prix = self.services_table.item(row, 3)
            item_jours = self.services_table.item(row, 4)
            item_montant = self.services_table.item(row, 5)
            
            if item_agents and item_prix and item_jours:
                try:
                    agents = int(item_agents.text())
                    prix_text = item_prix.text().replace(" ", "")
                    prix = float(prix_text)
                    jours = int(item_jours.text())
                    
                    montant = agents * prix * jours
                    
                    # Mettre à jour la cellule Montant HT
                    if item_montant:
                        item_montant.setText(f"{montant:,.2f}".replace(",", " "))
                    
                    total_ht += montant
                except:
                    pass
        
        tva = total_ht * 0.19
        total_ttc = total_ht + tva
        
        self.total_ht_label.setText(f"{total_ht:,.2f} DA".replace(",", " "))
        self.tva_label.setText(f"{tva:,.2f} DA".replace(",", " "))
        self.total_ttc_label.setText(f"{total_ttc:,.2f} DA".replace(",", " "))
        
        # Mettre à jour le montant en lettres
        montant_lettres = self.montant_en_lettres(total_ttc)
        
    
    def montant_en_lettres(self, montant):
        """Convertit un montant en lettres"""
        # À implémenter avec la même fonction que dans InvoiceDialog
        from .invoices_view import InvoiceDialog
        temp = InvoiceDialog()
        return temp.montant_en_lettres(montant)
    
    def load_data(self):
        """Charge les données d'une facture existante"""
        if not self.invoice_id:
            return
        
        print(f"📂 Chargement de la facture Beni Messous ID: {self.invoice_id}")
        
        session = SessionLocal()
        try:
            # Charger la facture avec ses relations
            invoice = session.query(Invoice).filter(Invoice.id == self.invoice_id).first()
            
            if not invoice:
                print(f"❌ Facture non trouvée")
                return
            
            print(f"✅ Facture trouvée: {invoice.invoice_number}")
            
            # Client
            self.set_client(invoice.client_id)
            
            # Numéro de facture
            self.invoice_number.setText(invoice.invoice_number)
            
            # Dates
            if invoice.date:
                self.date_edit.setDate(QDate(
                    invoice.date.year,
                    invoice.date.month,
                    invoice.date.day
                ))
            
            if invoice.due_date:
                self.due_date_edit.setDate(QDate(
                    invoice.due_date.year,
                    invoice.due_date.month,
                    invoice.due_date.day
                ))
            
            # Contrat
            if invoice.contrat_id:
                self.chk_link_contrat.setChecked(True)
                # Charger les contrats du client
                self.load_contrats(invoice.client_id)
                # Sélectionner le bon contrat
                index = self.contrat_combo.findData(invoice.contrat_id)
                if index >= 0:
                    self.contrat_combo.setCurrentIndex(index)
                    # Charger les informations du contrat
                    self.load_contrat_info(invoice.contrat_id)
            
            # Charger les items de la facture
            self.load_invoice_items(invoice)
            
            # Recalculer les totaux
            self.calculate_totals()
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
        finally:
            session.close()
    
    def load_invoice_items(self, invoice):
        """Charge les items de la facture dans le tableau"""
        self.services_table.setRowCount(0)
        
        if not invoice.items:
            return
        
        for item in invoice.items:
            row = self.services_table.rowCount()
            self.services_table.insertRow(row)
            
            description = item.description
            
            # Essayer d'extraire les informations formatées
            # Format possible: "Désignation - Tranche - Agents - Prix - Jours"
            parts = description.split(" - ")
            
            if len(parts) >= 5:
                # Format structuré
                designation = parts[0]
                tranche = parts[1]
                agents = parts[2]
                prix = parts[3]
                jours = parts[4]
            else:
                # Format simple
                designation = description
                tranche = "Journée"
                agents = str(int(item.quantity))
                # Calculer le prix par jour approximatif
                jours_estimes = 30
                prix = f"{item.unit_price / jours_estimes:,.2f}"
                jours = str(jours_estimes)
            
            self.services_table.setItem(row, 0, QTableWidgetItem(designation))
            self.services_table.setItem(row, 1, QTableWidgetItem(tranche))
            
            agents_item = QTableWidgetItem(agents)
            agents_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.services_table.setItem(row, 2, agents_item)
            
            prix_item = QTableWidgetItem(prix.replace(",", " "))
            prix_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.services_table.setItem(row, 3, prix_item)
            
            jours_item = QTableWidgetItem(jours)
            jours_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.services_table.setItem(row, 4, jours_item)
            
            montant_item = QTableWidgetItem(f"{item.total_ht:,.2f}".replace(",", " "))
            montant_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.services_table.setItem(row, 5, montant_item)
    
    def save_invoice(self):
        """Sauvegarde la facture"""
        if self.client_combo.currentIndex() <= 0:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un client")
            return
        
        if self.services_table.rowCount() == 0:
            QMessageBox.warning(self, "Erreur", "Veuillez ajouter au moins un service")
            return
        
        # Collecter les données des services
        items_data = []
        has_content = False
        
        for row in range(self.services_table.rowCount()):
            item_design = self.services_table.item(row, 0)
            if not item_design or not item_design.text().strip():
                continue
            
            designation = item_design.text().strip()
            
            try:
                tranche = self.services_table.item(row, 1).text()
                agents = int(self.services_table.item(row, 2).text())
                prix_text = self.services_table.item(row, 3).text().replace(" ", "")
                prix = float(prix_text)
                jours = int(self.services_table.item(row, 4).text())
                montant_text = self.services_table.item(row, 5).text().replace(" ", "")
                montant = float(montant_text)
                
                items_data.append({
                    'designation': f"{designation} - {tranche}",
                    'quantity': agents,
                    'unit_price': prix,
                    'tax_rate': 19.0,
                    'total_ht': montant,
                    'total_ttc': montant * 1.19
                })
                has_content = True
            except:
                continue
        
        if not has_content:
            QMessageBox.warning(self, "Erreur", "Aucun service valide à enregistrer")
            return
        
        # Récupérer les totaux
        total_ht = float(self.total_ht_label.text().replace(" DA", "").replace(" ", ""))
        tva = total_ht * 0.19
        total_ttc = total_ht + tva
        
        # Sauvegarder dans la base
        session = SessionLocal()
        try:
            if self.invoice_id:
                # MODIFICATION
                invoice = session.query(Invoice).filter(Invoice.id == self.invoice_id).first()
                if not invoice:
                    QMessageBox.critical(self, "Erreur", "Facture non trouvée")
                    return
                
                # Supprimer les anciens items
                session.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).delete()
                message = "Facture modifiée avec succès!"
                
            else:
                # CRÉATION
                # Vérifier l'unicité du numéro
                existing = session.query(Invoice).filter(
                    Invoice.invoice_number == self.invoice_number.text()
                ).first()
                
                if existing:
                    QMessageBox.warning(self, "Erreur", 
                        f"Le numéro de facture {self.invoice_number.text()} existe déjà.")
                    self.generate_invoice_number()
                    return
                
                invoice = Invoice(
                    invoice_number=self.invoice_number.text(),
                    client_id=self.client_combo.currentData(),
                    status=InvoiceStatus.DRAFT
                )
                session.add(invoice)
                message = "Facture Beni Messous créée avec succès!"
            
            # Mettre à jour les champs communs
            invoice.date = self.date_edit.date().toPyDate()
            invoice.due_date = self.due_date_edit.date().toPyDate()
            invoice.subtotal = total_ht
            invoice.tax_amount = tva
            invoice.total_amount = total_ttc
            invoice.amount_paid = 0
            invoice.balance_due = total_ttc
            
            if self.chk_link_contrat.isChecked() and self.contrat_combo.currentData():
                invoice.contrat_id = self.contrat_combo.currentData()
            
            session.flush()
            
            # Ajouter les nouveaux items
            for item_data in items_data:
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=item_data['designation'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    tax_rate=item_data['tax_rate'],
                    total_ht=item_data['total_ht'],
                    total_ttc=item_data['total_ttc']
                )
                session.add(item)
            
            session.commit()
            
            self.invoice_saved.emit()
            QMessageBox.information(self, "Succès", message)
            self.accept()
            
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            session.close()

    def on_contrat_changed(self, index):
        """Quand le contrat sélectionné change, charge ses informations"""
        if self.chk_link_contrat.isChecked():
            contrat_id = self.contrat_combo.currentData()
            print(f"🔍 Contrat sélectionné ID: {contrat_id}")
            if contrat_id:
                self.load_contrat_info(contrat_id)
            else:
                # Si "Sélectionnez un contrat" est choisi, vider les champs
                self.clear_contrat_info()
        else:
            # Si la checkbox n'est pas cochée, vider les champs
            self.clear_contrat_info()

    def clear_contrat_info(self):
        """Vide les champs d'informations spécifiques"""
        self.numero_marche.setText("")
        self.numero_ods.setText("")
        self.date_marche.setDate(QDate.currentDate())
        self.date_ods.setDate(QDate.currentDate())
        self.objet_ods.setText("")
        print("🧹 Champs d'informations spécifiques vidés")
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_table_columns()

    def adjust_table_columns(self):
        table_width = self.services_table.viewport().width()

        proportions = [0.40, 0.10, 0.10, 0.15, 0.10, 0.15]

        for i, ratio in enumerate(proportions):
            self.services_table.setColumnWidth(i, int(table_width * ratio))