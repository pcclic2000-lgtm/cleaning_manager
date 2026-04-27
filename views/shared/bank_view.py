# views/bank_view.py
"""
Vue principale pour la gestion bancaire
- Liste des comptes
- Transactions par compte
- Catégories de dépenses
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QSplitter, QLabel,
    QGroupBox, QFormLayout, QLineEdit, QTextEdit,
    QDoubleSpinBox, QComboBox, QDialog, QMenu,
    QAbstractItemView, QCheckBox, QFileDialog
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QAction, QColor

from database.db import SessionLocal, get_session
from models.bank import BankAccount, BankTransaction, TransactionType, BankExpenseCategory
from views.shared.bank_dialog import BankTransactionDialog
from datetime import datetime
import os


class BankAccountDialog(QDialog):
    """Dialogue pour ajouter/modifier un compte bancaire"""
    
    def __init__(self, account_id=None, parent=None):
        super().__init__(parent)
        self.account_id = account_id
        self.session = SessionLocal()
        
        self.setWindowTitle("Nouveau compte bancaire" if not account_id else "Modifier compte bancaire")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        form_group = QGroupBox("Informations du compte")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Nom du compte
        self.nom_compte = QLineEdit()
        self.nom_compte.setPlaceholderText("Ex: Compte courant BNA")
        self.nom_compte.setMinimumHeight(35)
        form_layout.addRow("Nom du compte*:", self.nom_compte)
        
        # Banque
        self.banque = QLineEdit()
        self.banque.setPlaceholderText("Ex: BNA, BEA, CPA, etc.")
        self.banque.setMinimumHeight(35)
        form_layout.addRow("Banque*:", self.banque)
        
        # Numéro de compte
        self.numero_compte = QLineEdit()
        self.numero_compte.setPlaceholderText("Numéro de compte")
        self.numero_compte.setMinimumHeight(35)
        form_layout.addRow("N° compte:", self.numero_compte)
        
        # RIB
        self.rib = QLineEdit()
        self.rib.setPlaceholderText("RIB")
        self.rib.setMinimumHeight(35)
        form_layout.addRow("RIB:", self.rib)
        
        # Solde initial
        self.solde_initial = QDoubleSpinBox()
        self.solde_initial.setRange(-10000000, 10000000)
        self.solde_initial.setDecimals(2)
        self.solde_initial.setSuffix(" DA")
        self.solde_initial.setMinimumHeight(35)
        form_layout.addRow("Solde initial:", self.solde_initial)
        
        # Devise
        self.devise = QComboBox()
        self.devise.addItems(["DA", "€", "$", "£"])
        self.devise.setMinimumHeight(35)
        form_layout.addRow("Devise:", self.devise)
        
        # Compte actif
        self.est_actif = QCheckBox("Compte actif")
        self.est_actif.setChecked(True)
        form_layout.addRow("", self.est_actif)
        
        # Notes
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Notes sur ce compte...")
        self.notes.setMaximumHeight(80)
        form_layout.addRow("Notes:", self.notes)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Boutons
        buttons = QHBoxLayout()
        
        btn_save = QPushButton("💾 Enregistrer")
        btn_save.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #219653; }
        """)
        btn_save.clicked.connect(self.save_account)
        
        btn_cancel = QPushButton("❌ Annuler")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
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
    
    def load_data(self):
        """Charge les données d'un compte existant"""
        if not self.account_id:
            return
        
        try:
            account = self.session.query(BankAccount).filter(BankAccount.id == self.account_id).first()
            if account:
                self.nom_compte.setText(account.nom_compte)
                self.banque.setText(account.banque)
                self.numero_compte.setText(account.numero_compte or "")
                self.rib.setText(account.rib or "")
                self.solde_initial.setValue(account.solde_initial)
                self.devise.setCurrentText(account.devise)
                self.est_actif.setChecked(account.est_actif)
                self.notes.setText(account.notes or "")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
    
    def save_account(self):
        """Sauvegarde le compte bancaire"""
        if not self.nom_compte.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom du compte est obligatoire")
            return
        
        if not self.banque.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom de la banque est obligatoire")
            return
        
        try:
            if self.account_id:
                account = self.session.query(BankAccount).filter(BankAccount.id == self.account_id).first()
            else:
                account = BankAccount()
                self.session.add(account)
            
            account.nom_compte = self.nom_compte.text().strip()
            account.banque = self.banque.text().strip()
            account.numero_compte = self.numero_compte.text().strip() or None
            account.rib = self.rib.text().strip() or None
            account.solde_initial = self.solde_initial.value()
            account.solde_actuel = self.solde_initial.value()
            account.devise = self.devise.currentText()
            account.est_actif = self.est_actif.isChecked()
            account.notes = self.notes.toPlainText().strip() or None
            
            self.session.commit()
            
            QMessageBox.information(self, "Succès", "Compte enregistré avec succès!")
            self.accept()
            
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")
    
    def closeEvent(self, event):
        """Ferme la session proprement"""
        self.session.close()
        event.accept()


class CategoryDialog(QDialog):
    """Dialogue pour ajouter/modifier une catégorie de dépense"""
    
    def __init__(self, category_id=None, parent=None):
        super().__init__(parent)
        self.category_id = category_id
        self.session = SessionLocal()
        
        self.setWindowTitle("Nouvelle catégorie" if not category_id else "Modifier catégorie")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.nom = QLineEdit()
        self.nom.setPlaceholderText("Ex: Fournitures, Équipement, Salaires...")
        self.nom.setMinimumHeight(35)
        form_layout.addRow("Nom*:", self.nom)
        
        self.description = QTextEdit()
        self.description.setPlaceholderText("Description de la catégorie...")
        self.description.setMaximumHeight(80)
        form_layout.addRow("Description:", self.description)
        
        self.est_actif = QCheckBox("Catégorie active")
        self.est_actif.setChecked(True)
        form_layout.addRow("", self.est_actif)
        
        layout.addLayout(form_layout)
        
        # Boutons
        buttons = QHBoxLayout()
        
        btn_save = QPushButton("💾 Enregistrer")
        btn_save.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #219653; }
        """)
        btn_save.clicked.connect(self.save_category)
        
        btn_cancel = QPushButton("❌ Annuler")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
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
    
    def load_data(self):
        """Charge les données d'une catégorie existante"""
        if not self.category_id:
            return
        
        try:
            cat = self.session.query(BankExpenseCategory).filter(BankExpenseCategory.id == self.category_id).first()
            if cat:
                self.nom.setText(cat.nom)
                self.description.setText(cat.description or "")
                self.est_actif.setChecked(cat.est_actif)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
    
    def save_category(self):
        """Sauvegarde la catégorie"""
        if not self.nom.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom de la catégorie est obligatoire")
            return
        
        try:
            if self.category_id:
                cat = self.session.query(BankExpenseCategory).filter(BankExpenseCategory.id == self.category_id).first()
            else:
                cat = BankExpenseCategory()
                self.session.add(cat)
            
            cat.nom = self.nom.text().strip()
            cat.description = self.description.toPlainText().strip() or None
            cat.est_actif = self.est_actif.isChecked()
            
            self.session.commit()
            
            QMessageBox.information(self, "Succès", "Catégorie enregistrée avec succès!")
            self.accept()
            
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")
    
    def closeEvent(self, event):
        """Ferme la session proprement"""
        self.session.close()
        event.accept()


class BankView(QWidget):
    """Vue principale pour la gestion bancaire"""
    
    def __init__(self):
        super().__init__()
        self.current_account_id = None
        self.session = SessionLocal()
        self.init_ui()
        self.load_accounts()
    
    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Splitter pour séparer la liste des comptes et les transactions
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panneau gauche : Liste des comptes
        left_panel = self.create_accounts_panel()
        
        # Panneau droit : Transactions du compte sélectionné
        right_panel = self.create_transactions_panel()
        
        # Ajouter les panneaux au splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def create_accounts_panel(self):
        """Crée le panneau de gauche avec la liste des comptes"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 5, 0)
        layout.setSpacing(10)
        
        # Titre
        title = QLabel("🏦 COMPTES BANCAIRES")
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background: #ecf0f1;
            border-radius: 6px;
        """)
        layout.addWidget(title)
        
        # Boutons pour les comptes
        btn_layout = QHBoxLayout()
        
        btn_add = QPushButton("➕ Nouveau")
        btn_add.clicked.connect(self.add_account)
        btn_add.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #219653; }
        """)
        
        btn_edit = QPushButton("✏️ Modifier")
        btn_edit.clicked.connect(self.edit_account)
        btn_edit.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        
        btn_delete = QPushButton("🗑️ Supprimer")
        btn_delete.clicked.connect(self.delete_account)
        btn_delete.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c0392b; }
        """)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Table des comptes
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(5)
        self.accounts_table.setHorizontalHeaderLabels([
            "ID", "Compte", "Banque", "Solde", "Devise"
        ])
        self.accounts_table.setColumnHidden(0, True)
        
        self.accounts_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background: white;
            }
            QHeaderView::section {
                background: #34495e;
                color: white;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        header = self.accounts_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.accounts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.accounts_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.accounts_table.itemSelectionChanged.connect(self.on_account_selected)
        
        layout.addWidget(self.accounts_table)
        
        # Résumé du compte sélectionné
        self.account_summary = QGroupBox("Résumé du compte")
        summary_layout = QFormLayout()
        summary_layout.setSpacing(5)
        
        self.summary_solde = QLabel("0.00 DA")
        self.summary_solde.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        
        self.summary_entrees = QLabel("0.00 DA")
        self.summary_sorties = QLabel("0.00 DA")
        
        summary_layout.addRow("Solde actuel:", self.summary_solde)
        summary_layout.addRow("Total entrées:", self.summary_entrees)
        summary_layout.addRow("Total sorties:", self.summary_sorties)
        
        self.account_summary.setLayout(summary_layout)
        layout.addWidget(self.account_summary)
        
        layout.addStretch()
        return panel
    
    def create_transactions_panel(self):
        """Crée le panneau de droite avec les transactions"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 0, 0, 0)
        layout.setSpacing(10)
        
        # Titre
        title = QLabel("📊 TRANSACTIONS")
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background: #ecf0f1;
            border-radius: 6px;
        """)
        layout.addWidget(title)
        
        # Barre d'outils des transactions
        toolbar = QHBoxLayout()
        
        btn_depot = QPushButton("💰 Dépôt")
        btn_depot.setStyleSheet("background: #27ae60; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        btn_depot.clicked.connect(lambda: self.add_transaction(TransactionType.DEPOT))
        
        btn_retrait = QPushButton("💸 Retrait")
        btn_retrait.setStyleSheet("background: #e74c3c; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        btn_retrait.clicked.connect(lambda: self.add_transaction(TransactionType.RETRAIT))
        
        btn_virement = QPushButton("🔄 Virement")
        btn_virement.setStyleSheet("background: #f39c12; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        btn_virement.clicked.connect(lambda: self.add_transaction(TransactionType.VIREMENT))
        
        btn_edit = QPushButton("✏️ Modifier")
        btn_edit.setStyleSheet("background: #3498db; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        btn_edit.clicked.connect(self.edit_transaction)
        
        btn_delete = QPushButton("🗑️ Supprimer")
        btn_delete.setStyleSheet("background: #e74c3c; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        btn_delete.clicked.connect(self.delete_transaction)
        
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.setStyleSheet("background: #95a5a6; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        btn_refresh.clicked.connect(self.refresh_transactions)
        
        toolbar.addWidget(btn_depot)
        toolbar.addWidget(btn_retrait)
        toolbar.addWidget(btn_virement)
        toolbar.addStretch()
        toolbar.addWidget(btn_edit)
        toolbar.addWidget(btn_delete)
        toolbar.addWidget(btn_refresh)
        
        layout.addLayout(toolbar)
        
        # Table des transactions
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(8)
        self.transactions_table.setHorizontalHeaderLabels([
            "ID", "Date", "Type", "Catégorie", "Description", "Montant", "Solde après", "Justificatif"
        ])
        self.transactions_table.setColumnHidden(0, True)
        
        self.transactions_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background: white;
            }
            QHeaderView::section {
                background: #34495e;
                color: white;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        header = self.transactions_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        self.transactions_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.transactions_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.transactions_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.transactions_table.customContextMenuRequested.connect(self.show_transaction_context_menu)
        
        layout.addWidget(self.transactions_table)
        
        return panel
    
    def load_accounts(self):
        """Charge la liste des comptes"""
        try:
            accounts = self.session.query(BankAccount).order_by(BankAccount.nom_compte).all()
            
            self.accounts_table.setRowCount(len(accounts))
            
            for row, account in enumerate(accounts):
                self.accounts_table.setItem(row, 0, QTableWidgetItem(str(account.id)))
                self.accounts_table.setItem(row, 1, QTableWidgetItem(account.nom_compte))
                self.accounts_table.setItem(row, 2, QTableWidgetItem(account.banque))
                
                solde_item = QTableWidgetItem(f"{account.solde_actuel:,.2f}")
                solde_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                # Colorer le solde
                if account.solde_actuel > 0:
                    solde_item.setForeground(QColor("#27ae60"))
                elif account.solde_actuel < 0:
                    solde_item.setForeground(QColor("#e74c3c"))
                
                self.accounts_table.setItem(row, 3, solde_item)
                self.accounts_table.setItem(row, 4, QTableWidgetItem(account.devise))
            
            # Sélectionner le premier compte par défaut
            if accounts and self.accounts_table.rowCount() > 0:
                self.accounts_table.selectRow(0)
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur de chargement des comptes: {str(e)}")
    
    def on_account_selected(self):
        """Quand un compte est sélectionné, charge ses transactions"""
        selected = self.accounts_table.selectedItems()
        if selected:
            row = selected[0].row()
            id_item = self.accounts_table.item(row, 0)
            if id_item:
                self.current_account_id = int(id_item.text())
                self.load_transactions(self.current_account_id)
                self.update_account_summary(self.current_account_id)
    
    def load_transactions(self, account_id):
        """Charge les transactions d'un compte"""
        try:
            transactions = self.session.query(BankTransaction).filter(
                BankTransaction.compte_id == account_id
            ).order_by(BankTransaction.date_transaction.desc()).all()
            
            self.transactions_table.setRowCount(len(transactions))
            
            for row, trans in enumerate(transactions):
                self.transactions_table.setItem(row, 0, QTableWidgetItem(str(trans.id)))
                
                # Date
                date_str = trans.date_transaction.strftime("%d/%m/%Y")
                self.transactions_table.setItem(row, 1, QTableWidgetItem(date_str))
                
                # Type avec couleur
                type_item = QTableWidgetItem(trans.type_transaction.value)
                if trans.est_entree:
                    type_item.setForeground(QColor("#27ae60"))
                elif trans.est_sortie:
                    type_item.setForeground(QColor("#e74c3c"))
                self.transactions_table.setItem(row, 2, type_item)
                
                # Catégorie
                categorie = trans.categorie.nom if trans.categorie else "-"
                self.transactions_table.setItem(row, 3, QTableWidgetItem(categorie))
                
                # Description
                description = trans.description or trans.source or trans.beneficiaire or "-"
                self.transactions_table.setItem(row, 4, QTableWidgetItem(description))
                
                # Montant
                montant_item = QTableWidgetItem(f"{trans.montant:,.2f} DA")
                montant_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if trans.est_entree:
                    montant_item.setForeground(QColor("#27ae60"))
                elif trans.est_sortie:
                    montant_item.setForeground(QColor("#e74c3c"))
                self.transactions_table.setItem(row, 5, montant_item)
                
                # Solde après
                solde_item = QTableWidgetItem(f"{trans.solde_apres:,.2f} DA" if trans.solde_apres else "-")
                solde_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.transactions_table.setItem(row, 6, solde_item)
                
                # Justificatif
                justif = "✓" if trans.justificatif_path else "-"
                justif_item = QTableWidgetItem(justif)
                if trans.justificatif_path:
                    justif_item.setForeground(QColor("#27ae60"))
                self.transactions_table.setItem(row, 7, justif_item)
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur de chargement des transactions: {str(e)}")
    
    def update_account_summary(self, account_id):
        """Met à jour le résumé du compte"""
        try:
            account = self.session.query(BankAccount).filter(BankAccount.id == account_id).first()
            if account:
                # Calculer totaux
                transactions = self.session.query(BankTransaction).filter(
                    BankTransaction.compte_id == account_id
                ).all()
                
                total_entrees = sum(t.montant for t in transactions if t.est_entree)
                total_sorties = sum(t.montant for t in transactions if t.est_sortie)
                
                self.summary_solde.setText(f"{account.solde_actuel:,.2f} {account.devise}")
                self.summary_entrees.setText(f"{total_entrees:,.2f} {account.devise}")
                self.summary_sorties.setText(f"{total_sorties:,.2f} {account.devise}")
                
        except Exception as e:
            print(f"Erreur mise à jour résumé: {e}")
    
    def refresh_transactions(self):
        """Rafraîchit la liste des transactions"""
        if self.current_account_id:
            self.load_transactions(self.current_account_id)
            self.update_account_summary(self.current_account_id)
    
    def add_account(self):
        """Ajoute un nouveau compte bancaire"""
        dialog = BankAccountDialog(parent=self)
        if dialog.exec():
            self.load_accounts()
    
    def edit_account(self):
        """Modifie le compte sélectionné"""
        selected = self.accounts_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un compte")
            return
        
        row = selected[0].row()
        account_id = int(self.accounts_table.item(row, 0).text())
        
        dialog = BankAccountDialog(account_id=account_id, parent=self)
        if dialog.exec():
            self.load_accounts()
    
    def delete_account(self):
        """Supprime le compte sélectionné"""
        selected = self.accounts_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un compte")
            return
        
        row = selected[0].row()
        account_id = int(self.accounts_table.item(row, 0).text())
        account_name = self.accounts_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer le compte '{account_name}' ?\n"
            "Toutes les transactions associées seront également supprimées.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                account = self.session.query(BankAccount).filter(BankAccount.id == account_id).first()
                if account:
                    self.session.delete(account)
                    self.session.commit()
                    self.load_accounts()
                    self.transactions_table.setRowCount(0)
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression:\n{str(e)}")
    
    def add_transaction(self, transaction_type=None):
        """Ajoute une nouvelle transaction"""
        if not self.current_account_id:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un compte")
            return
        
        dialog = BankTransactionDialog(
            compte_id=self.current_account_id,
            parent=self
        )
        
        # Pré-sélectionner le type si fourni
        if transaction_type:
            index = dialog.type_combo.findData(transaction_type)
            if index >= 0:
                dialog.type_combo.setCurrentIndex(index)
                dialog.on_type_changed(index)
        
        dialog.transaction_saved.connect(self.refresh_transactions)
        dialog.exec()
    
    def edit_transaction(self):
        """Modifie la transaction sélectionnée"""
        selected = self.transactions_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une transaction")
            return
        
        row = selected[0].row()
        transaction_id = int(self.transactions_table.item(row, 0).text())
        
        dialog = BankTransactionDialog(transaction_id=transaction_id, parent=self)
        dialog.transaction_saved.connect(self.refresh_transactions)
        dialog.exec()
    
    def delete_transaction(self):
        """Supprime la transaction sélectionnée"""
        selected = self.transactions_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une transaction")
            return
        
        row = selected[0].row()
        transaction_id = int(self.transactions_table.item(row, 0).text())
        description = self.transactions_table.item(row, 4).text()
        
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer cette transaction ?\n\n{description}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                transaction = self.session.query(BankTransaction).filter(
                    BankTransaction.id == transaction_id
                ).first()
                
                if transaction:
                    # Supprimer le justificatif si présent
                    if transaction.justificatif_path and os.path.exists(transaction.justificatif_path):
                        os.remove(transaction.justificatif_path)
                    
                    self.session.delete(transaction)
                    
                    # Recalculer les soldes du compte
                    account = self.session.query(BankAccount).filter(
                        BankAccount.id == transaction.compte_id
                    ).first()
                    
                    if account:
                        # Recalculer tous les soldes
                        transactions = self.session.query(BankTransaction).filter(
                            BankTransaction.compte_id == account.id
                        ).order_by(BankTransaction.date_transaction).all()
                        
                        solde = account.solde_initial
                        for t in transactions:
                            if t.est_entree:
                                solde += t.montant
                            elif t.est_sortie:
                                solde -= t.montant
                            t.solde_apres = solde
                        
                        account.solde_actuel = solde
                    
                    self.session.commit()
                    self.refresh_transactions()
                    
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression:\n{str(e)}")
    
    def show_transaction_context_menu(self, pos: QPoint):
        """Menu contextuel pour les transactions"""
        global_pos = self.transactions_table.viewport().mapToGlobal(pos)
        idx = self.transactions_table.indexAt(pos)
        
        menu = QMenu()
        
        if idx.isValid():
            self.transactions_table.selectRow(idx.row())
            
            act_edit = QAction("✏️ Modifier", self)
            act_edit.triggered.connect(self.edit_transaction)
            menu.addAction(act_edit)
            
            act_delete = QAction("🗑️ Supprimer", self)
            act_delete.triggered.connect(self.delete_transaction)
            menu.addAction(act_delete)
            
            menu.addSeparator()
            
            act_view_justif = QAction("👁️ Voir justificatif", self)
            act_view_justif.triggered.connect(self.view_transaction_justificatif)
            menu.addAction(act_view_justif)
        
        menu.exec(global_pos)
    
    def view_transaction_justificatif(self):
        """Ouvre le justificatif de la transaction sélectionnée"""
        selected = self.transactions_table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        transaction_id = int(self.transactions_table.item(row, 0).text())
        
        try:
            transaction = self.session.query(BankTransaction).filter(
                BankTransaction.id == transaction_id
            ).first()
            
            if transaction and transaction.justificatif_path:
                if os.path.exists(transaction.justificatif_path):
                    import subprocess
                    import platform
                    
                    if platform.system() == 'Windows':
                        os.startfile(transaction.justificatif_path)
                    elif platform.system() == 'Darwin':
                        subprocess.run(['open', transaction.justificatif_path])
                    else:
                        subprocess.run(['xdg-open', transaction.justificatif_path])
                else:
                    QMessageBox.warning(self, "Erreur", "Le fichier justificatif n'existe plus")
            else:
                QMessageBox.information(self, "Information", "Aucun justificatif pour cette transaction")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur: {str(e)}")
    
    def closeEvent(self, event):
        """Ferme la session proprement"""
        self.session.close()
        event.accept()