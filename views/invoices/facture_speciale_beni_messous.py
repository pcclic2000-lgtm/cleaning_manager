# views/facture_speciale_beni_messous.py
"""
Dialogue pour la facture spéciale Beni Messous
Avec tableau : Désignation, Tranche horaire, Nb agents, Prix U/Jour, Nb Jours, Montant HT
"""

import os
from datetime import datetime
from decimal import Decimal

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QLabel, QFormLayout, QComboBox, QTextEdit,
    QHeaderView, QGroupBox, QDateEdit, QFileDialog,
    QAbstractItemView, QLineEdit
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont

from database.db import SessionLocal, get_session
from models.client import Client
from models.contrat import Contrat
from models.company import CompanyInfo
from views.beni_messous_item_dialog import BeniMessousItemDialog


class FactureBeniMessousDialog(QDialog):
    """Dialogue pour la facture spéciale Beni Messous"""
    
    invoice_saved = pyqtSignal()
    
    def __init__(self, contrat_id=None, parent=None):
        super().__init__(parent)
        self.contrat_id = contrat_id
        self.items = []
        self.entreprise_info = self.load_entreprise_info()
        self.contrat = None
        self.client = None
        
        self.setWindowTitle("🏥 Facture Beni Messous")
        self.setModal(True)
        self.setMinimumSize(1100, 800)
        
        self.load_contrat_data()
        self.init_ui()
    
    def load_entreprise_info(self):
        """Charger les informations de l'entreprise"""
        with get_session() as session:
            company = session.query(CompanyInfo).first()
            if company:
                return {
                    'nom': company.nom or "Entreprise",
                    'adresse': company.adresse or "",
                    'telephone': company.telephone or "",
                    'email': company.email or "",
                    'rc': company.rc or "",
                    'nif': company.nif or "",
                    'nis': company.nis or "",
                    'art': company.art or "",
                    'banque': company.banque or "",
                    'compte_ccp': getattr(company, 'compte_ccp', "") or "",
                    'rib': company.rib or "",
                    'logo_path': company.logo_path if company.logo_path and os.path.exists(company.logo_path) else None
                }
            return {}
    
    def load_contrat_data(self):
        """Charger les données du contrat"""
        if not self.contrat_id:
            return
        
        with get_session() as session:
            self.contrat = session.query(Contrat).filter(Contrat.id == self.contrat_id).first()
            if self.contrat and self.contrat.client:
                self.client = self.contrat.client
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title = QLabel("🏥 FACTURE BENI MESSOUS")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 5px solid #3498db;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Informations contrat
        info_layout = QHBoxLayout()
        
        # Numéro facture
        num_layout = QFormLayout()
        self.invoice_number = QLineEdit()
        self.invoice_number.setPlaceholderText("Ex: 001/2026")
        self.invoice_number.setMinimumHeight(35)
        num_layout.addRow("N° Facture:", self.invoice_number)
        
        # Date
        date_layout = QFormLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setMinimumHeight(35)
        date_layout.addRow("Date:", self.date_edit)
        
        info_layout.addLayout(num_layout)
        info_layout.addStretch()
        info_layout.addLayout(date_layout)
        
        layout.addLayout(info_layout)
        
        # Informations client
        client_group = QGroupBox("👤 CLIENT")
        client_layout = QFormLayout()
        
        self.client_nom = QLabel(self.client.raison_sociale if self.client else "BENI MESSOUS")
        self.client_nom.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        client_layout.addRow("Client:", self.client_nom)
        client_group.setLayout(client_layout)
        layout.addWidget(client_group)
        
        # Barre d'outils articles
        toolbar = QHBoxLayout()
        
        btn_add_item = QPushButton("➕ Ajouter prestation")
        btn_add_item.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #219653; }
        """)
        btn_add_item.clicked.connect(self.add_item)
        
        btn_remove_item = QPushButton("🗑️ Supprimer")
        btn_remove_item.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c0392b; }
        """)
        btn_remove_item.clicked.connect(self.remove_selected_item)
        
        toolbar.addWidget(btn_add_item)
        toolbar.addWidget(btn_remove_item)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Tableau des prestations
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "Désignation du service",
            "Tranche horaire",
            "Nb agents",
            "Prix U/Jour",
            "Nb Jours",
            "Montant HT"
        ])
        
        # Style du tableau
        self.items_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background: white;
                gridline-color: #dee2e6;
            }
            QHeaderView::section {
                background: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item { padding: 8px; }
        """)
        
        # Configuration des colonnes
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Désignation
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Tranche horaire
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Nb agents
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Prix U/Jour
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Nb Jours
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Montant HT
        
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        layout.addWidget(self.items_table)
        
        # Totaux
        totals_group = QGroupBox("🧮 TOTAUX")
        totals_layout = QFormLayout()
        
        self.total_ht_label = QLabel("0.00 DA")
        self.total_ht_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        
        totals_layout.addRow("Total HT:", self.total_ht_label)
        totals_group.setLayout(totals_layout)
        layout.addWidget(totals_group)
        
        # Ajouter 8 lignes par défaut
        for _ in range(8):
            self.add_empty_row()
        
        # Boutons
        buttons = QHBoxLayout()
        
        btn_save = QPushButton("💾 Générer facture")
        btn_save.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background: #219653; }
        """)
        btn_save.clicked.connect(self.save_invoice)
        
        btn_cancel = QPushButton("❌ Annuler")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c0392b; }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        buttons.addStretch()
        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)
        
        layout.addLayout(buttons)
        self.setLayout(layout)
        
        # Générer numéro facture
        self.generate_invoice_number()
    
    def generate_invoice_number(self):
        """Génère un numéro de facture"""
        from datetime import datetime
        annee = datetime.now().year
        self.invoice_number.setText(f"001/{annee}")
    
    def add_empty_row(self):
        """Ajoute une ligne vide"""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # Cellules vides avec placeholder
        for col in range(6):
            item = QTableWidgetItem("")
            if col == 0:  # Désignation
                item.setToolTip("Cliquez sur 'Ajouter prestation' pour remplir")
            self.items_table.setItem(row, col, item)
    
    def add_item(self):
        """Ajoute une prestation via le dialogue"""
        dialog = BeniMessousItemDialog(self)
        if dialog.exec():
            item_data = dialog.get_item_data()
            
            # Trouver la première ligne vide ou ajouter une nouvelle ligne
            row = -1
            for r in range(self.items_table.rowCount()):
                if not self.items_table.item(r, 0).text():
                    row = r
                    break
            
            if row == -1:
                row = self.items_table.rowCount()
                self.items_table.insertRow(row)
            
            # Remplir la ligne
            self.items_table.setItem(row, 0, QTableWidgetItem(item_data['designation']))
            self.items_table.setItem(row, 1, QTableWidgetItem(item_data['tranche_horaire']))
            self.items_table.setItem(row, 2, QTableWidgetItem(str(item_data['nb_agents'])))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{item_data['prix_unitaire']:,.2f}"))
            self.items_table.setItem(row, 4, QTableWidgetItem(str(item_data['nb_jours'])))
            
            montant_item = QTableWidgetItem(f"{item_data['montant_ht']:,.2f}")
            montant_item.setForeground(Qt.GlobalColor.darkGreen)
            self.items_table.setItem(row, 5, montant_item)
            
            # Ajouter l'item à la liste
            self.items.append(item_data)
            
            # Recalculer le total
            self.calculer_total()
    
    def remove_selected_item(self):
        """Supprime la prestation sélectionnée"""
        selected = self.items_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une prestation à supprimer")
            return
        
        row = selected[0].row()
        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment supprimer cette prestation ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Vider la ligne
            for col in range(6):
                self.items_table.setItem(row, col, QTableWidgetItem(""))
            
            # Mettre à jour la liste des items
            self.items = [item for i, item in enumerate(self.items) if i != row]
            
            # Recalculer le total
            self.calculer_total()
    
    def calculer_total(self):
        """Calcule le total HT"""
        total = 0.0
        for row in range(self.items_table.rowCount()):
            item = self.items_table.item(row, 5)
            if item and item.text():
                try:
                    montant = float(item.text().replace(',', ''))
                    total += montant
                except:
                    pass
        
        self.total_ht_label.setText(f"{total:,.2f} DA".replace(",", " "))
        return total
    
    def save_invoice(self):
        """Sauvegarde la facture"""
        if not self.invoice_number.text().strip():
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un numéro de facture")
            return
        
        # Vérifier qu'il y a au moins une prestation
        total = self.calculer_total()
        if total <= 0:
            QMessageBox.warning(self, "Erreur", "Veuillez ajouter au moins une prestation")
            return
        
        # TODO: Sauvegarder dans la base de données
        QMessageBox.information(
            self, 
            "Succès", 
            f"Facture {self.invoice_number.text()} générée avec succès !\n\n"
            f"Total HT: {total:,.2f} DA".replace(",", " ")
        )
        
        self.invoice_saved.emit()
        self.accept()
