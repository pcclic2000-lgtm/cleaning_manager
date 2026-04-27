# views/bank_dialog.py
"""
Dialogues pour la gestion des transactions bancaires
"""

import os
import shutil
import uuid
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QDoubleSpinBox,
    QDateEdit, QTextEdit, QPushButton, QMessageBox,
    QGroupBox, QFileDialog, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon

from database.db import SessionLocal, get_session
from models.bank import BankAccount, BankTransaction, TransactionType, BankExpenseCategory
from models.invoice import Invoice


class BankTransactionDialog(QDialog):
    """Dialogue pour ajouter/modifier une transaction bancaire"""
    
    transaction_saved = pyqtSignal()
    
    def __init__(self, compte_id=None, transaction_id=None, parent=None):
        super().__init__(parent)
        self.compte_id = compte_id
        self.transaction_id = transaction_id
        self.justificatif_path = None
        
        self.setWindowTitle("Nouvelle transaction" if not transaction_id else "Modifier transaction")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        self.init_ui()
        self.load_comptes()
        self.load_categories()
        self.load_factures()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Titre
        title = QLabel("💰 TRANSACTION BANCAIRE")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Formulaire
        form_group = QGroupBox("Détails de la transaction")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Compte bancaire
        self.compte_combo = QComboBox()
        self.compte_combo.setMinimumHeight(35)
        form_layout.addRow("Compte*:", self.compte_combo)
        
        # Type de transaction
        self.type_combo = QComboBox()
        for t in TransactionType:
            self.type_combo.addItem(t.value, t)
        self.type_combo.setMinimumHeight(35)
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        form_layout.addRow("Type*:", self.type_combo)
        
        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setMinimumHeight(35)
        form_layout.addRow("Date*:", self.date_edit)
        
        # Montant
        self.montant_spin = QDoubleSpinBox()
        self.montant_spin.setRange(0.01, 1000000000)
        self.montant_spin.setDecimals(2)
        self.montant_spin.setSuffix(" DA")
        self.montant_spin.setMinimumHeight(35)
        form_layout.addRow("Montant*:", self.montant_spin)
        
        # Catégorie (pour les sorties)
        self.categorie_combo = QComboBox()
        self.categorie_combo.setMinimumHeight(35)
        self.categorie_combo.setEnabled(False)  # Désactivé par défaut
        form_layout.addRow("Catégorie:", self.categorie_combo)
        
        # Bénéficiaire (pour les sorties)
        self.beneficiaire_edit = QLineEdit()
        self.beneficiaire_edit.setPlaceholderText("À qui a été payé")
        self.beneficiaire_edit.setMinimumHeight(35)
        self.beneficiaire_edit.setEnabled(False)
        form_layout.addRow("Bénéficiaire:", self.beneficiaire_edit)
        
        # Source (pour les entrées)
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Provenance de l'argent")
        self.source_edit.setMinimumHeight(35)
        form_layout.addRow("Source:", self.source_edit)
        
        # Référence (chèque, virement, etc.)
        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("N° chèque, virement, etc.")
        self.reference_edit.setMinimumHeight(35)
        form_layout.addRow("Référence:", self.reference_edit)
        
        # Description / Justification
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Description détaillée de la transaction...")
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_edit)
        
        # Lien avec facture (pour les entrées)
        self.facture_check = QCheckBox("Lier à une facture")
        self.facture_check.toggled.connect(self.on_facture_toggled)
        form_layout.addRow("", self.facture_check)
        
        self.facture_combo = QComboBox()
        self.facture_combo.setEnabled(False)
        self.facture_combo.currentIndexChanged.connect(self.on_facture_changed)
        form_layout.addRow("Facture:", self.facture_combo)
        
        # Label de statut pour afficher le montant chargé
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 5px;")
        form_layout.addRow("", self.status_label)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Section justificatif
        justificatif_group = QGroupBox("📎 Justificatif")
        justificatif_layout = QVBoxLayout()
        
        justificatif_buttons = QHBoxLayout()
        
        self.btn_upload = QPushButton("📁 Charger un justificatif")
        self.btn_upload.clicked.connect(self.upload_justificatif)
        
        self.btn_view = QPushButton("👁️ Voir le justificatif")
        self.btn_view.clicked.connect(self.view_justificatif)
        self.btn_view.setEnabled(False)
        
        self.btn_remove = QPushButton("🗑️ Supprimer")
        self.btn_remove.clicked.connect(self.remove_justificatif)
        self.btn_remove.setEnabled(False)
        
        justificatif_buttons.addWidget(self.btn_upload)
        justificatif_buttons.addWidget(self.btn_view)
        justificatif_buttons.addWidget(self.btn_remove)
        justificatif_buttons.addStretch()
        
        self.justificatif_label = QLabel("Aucun justificatif")
        self.justificatif_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        
        justificatif_layout.addLayout(justificatif_buttons)
        justificatif_layout.addWidget(self.justificatif_label)
        
        justificatif_group.setLayout(justificatif_layout)
        layout.addWidget(justificatif_group)
        
        # Notes
        notes_group = QGroupBox("📝 Notes")
        notes_layout = QVBoxLayout()
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notes additionnelles...")
        self.notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_edit)
        
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)
        
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
                font-size: 14px;
            }
            QPushButton:hover { background: #219653; }
        """)
        btn_save.clicked.connect(self.save_transaction)
        
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
    
    def load_invoice_amount(self, facture_id):
        """Charge le montant TTC de la facture sélectionnée"""
        if not facture_id:
            return
        
        try:
            with get_session() as session:
                from models.invoice import Invoice
                facture = session.query(Invoice).filter(Invoice.id == facture_id).first()
                
                if facture:
                    # Remplir automatiquement le montant avec le total TTC
                    self.montant_spin.setValue(facture.total_amount)
                    
                    # Optionnel: remplir aussi la source avec le client
                    if facture.client:
                        client_name = facture.client.raison_sociale or facture.client.nom_complet
                        self.source_edit.setText(f"Paiement facture {facture.invoice_number} - {client_name}")
                    
                    # Afficher une confirmation
                    self.status_label.setText(
                        f"✓ Montant facture: {facture.total_amount:,.2f} DA"
                    )
                    self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                    
                    print(f"✅ Montant facture chargé: {facture.total_amount:,.2f} DA")
        except Exception as e:
            print(f"❌ Erreur lors du chargement du montant facture: {e}")
    
    def load_comptes(self):
        """Charge la liste des comptes bancaires"""
        try:
            with get_session() as session:
                comptes = session.query(BankAccount).filter(BankAccount.est_actif == True).all()
                self.compte_combo.clear()
                for compte in comptes:
                    label = f"{compte.nom_compte} - {compte.banque} (Solde: {compte.solde_actuel:,.2f} DA)"
                    self.compte_combo.addItem(label, compte.id)
                    
                    # Présélectionner le compte si fourni
                    if self.compte_id:
                        index = self.compte_combo.findData(self.compte_id)
                        if index >= 0:
                            self.compte_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"❌ Erreur lors du chargement des comptes: {e}")
    
    def load_categories(self):
        """Charge les catégories de dépenses depuis la base de données"""
        print("🔄 Chargement des catégories de dépenses...")
        
        try:
            with get_session() as session:
                # Utiliser BankExpenseCategory
                from models.bank import BankExpenseCategory
                
                categories = session.query(BankExpenseCategory).filter(
                    BankExpenseCategory.est_actif == True
                ).order_by(BankExpenseCategory.nom).all()
                
                self.categorie_combo.clear()
                self.categorie_combo.addItem("-- Sélectionnez une catégorie --", None)
                
                if categories:
                    for cat in categories:
                        self.categorie_combo.addItem(cat.nom, cat.id)
                        print(f"   ✅ Catégorie chargée: {cat.nom}")
                else:
                    print("   ⚠️  Aucune catégorie trouvée dans la base")
                    
                    # Option: Ajouter des catégories par défaut si aucune n'existe
                    self.create_default_categories(session)
        except Exception as e:
            print(f"❌ Erreur lors du chargement des catégories: {e}")
            import traceback
            traceback.print_exc()
    
    def create_default_categories(self, session):
        """Crée des catégories par défaut si aucune n'existe"""
        from models.bank import BankExpenseCategory
        
        try:
            categories_defaut = [
                {"nom": "Fournitures de bureau", "description": "Papeterie, imprimantes, consommables"},
                {"nom": "Équipement", "description": "Achat de matériel, ordinateurs, mobilier"},
                {"nom": "Salaires", "description": "Rémunération du personnel"},
                {"nom": "Charges sociales", "description": "CNAS, CASNOS, assurances"},
                {"nom": "Impôts et taxes", "description": "Impôts sur les sociétés, taxes diverses"},
                {"nom": "Transport", "description": "Carburant, entretien véhicules, déplacements"},
                {"nom": "Communication", "description": "Téléphone, internet, affranchissement"},
                {"nom": "Services extérieurs", "description": "Prestataires, sous-traitance"},
                {"nom": "Frais bancaires", "description": "Commissions, tenue de compte"},
                {"nom": "Loyer et charges", "description": "Loyer des locaux, électricité, eau"},
                {"nom": "Entretien et réparations", "description": "Maintenance, réparations"},
                {"nom": "Formation", "description": "Formation du personnel"},
                {"nom": "Divers", "description": "Autres dépenses non classées"}
            ]
            
            for cat in categories_defaut:
                existing = session.query(BankExpenseCategory).filter(
                    BankExpenseCategory.nom == cat["nom"]
                ).first()
                
                if not existing:
                    nouvelle_cat = BankExpenseCategory(
                        nom=cat["nom"],
                        description=cat["description"],
                        couleur="#3498db",
                        est_actif=True
                    )
                    session.add(nouvelle_cat)
                    print(f"   ➕ Catégorie créée: {cat['nom']}")
            
            session.commit()
            
            # Recharger les catégories
            categories = session.query(BankExpenseCategory).filter(
                BankExpenseCategory.est_actif == True
            ).all()
            
            self.categorie_combo.clear()
            self.categorie_combo.addItem("-- Sélectionnez une catégorie --", None)
            for cat in categories:
                self.categorie_combo.addItem(cat.nom, cat.id)
                
        except Exception as e:
            print(f"❌ Erreur lors de la création des catégories par défaut: {e}")
            session.rollback()
    
    def load_factures(self):
        """Charge les factures impayées pour liaison"""
        try:
            with get_session() as session:
                from models.invoice import Invoice, InvoiceStatus
                factures = session.query(Invoice).filter(
                    Invoice.status != InvoiceStatus.PAID
                ).order_by(Invoice.date.desc()).all()
                
                self.facture_combo.clear()
                self.facture_combo.addItem("-- Aucune facture liée --", None)
                for f in factures:
                    label = f"{f.invoice_number} - {f.total_amount:,.2f} DA"
                    self.facture_combo.addItem(label, f.id)
        except Exception as e:
            print(f"❌ Erreur lors du chargement des factures: {e}")
    
    def on_type_changed(self, index):
        """Adapte l'interface selon le type de transaction"""
        if self.type_combo.currentData() is None:
            return
            
        transaction_type = self.type_combo.currentData()
        print(f"🔄 Type changé: {transaction_type.value if transaction_type else 'None'}")
        
        # Pour les entrées (dépôts)
        if transaction_type in [TransactionType.DEPOT, TransactionType.INTERETS]:
            self.categorie_combo.setEnabled(False)
            self.beneficiaire_edit.setEnabled(False)
            self.source_edit.setEnabled(True)
            self.facture_check.setEnabled(True)
            self.status_label.setText("")  # Effacer le statut
            print("   Mode: Entrée d'argent")
            
            # Si "Lier à une facture" était coché, recharger le montant
            if self.facture_check.isChecked() and self.facture_combo.currentData():
                self.load_invoice_amount(self.facture_combo.currentData())
        
        # Pour les sorties (retraits, frais)
        elif transaction_type in [TransactionType.RETRAIT, TransactionType.FRAIS_BANCAIRES]:
            self.categorie_combo.setEnabled(True)
            self.beneficiaire_edit.setEnabled(True)
            self.source_edit.setEnabled(False)
            self.facture_check.setEnabled(False)
            self.facture_check.setChecked(False)
            self.facture_combo.setEnabled(False)
            self.status_label.setText("")  # Effacer le statut
            print("   Mode: Sortie d'argent")
        
        # Virement
        elif transaction_type == TransactionType.VIREMENT:
            self.categorie_combo.setEnabled(False)
            self.beneficiaire_edit.setEnabled(True)
            self.source_edit.setEnabled(True)
            self.facture_check.setEnabled(False)
            self.facture_check.setChecked(False)
            self.status_label.setText("")  # Effacer le statut
            print("   Mode: Virement")
    
    def on_facture_toggled(self, checked):
        """Active/désactive la sélection de facture et charge le montant"""
        self.facture_combo.setEnabled(checked)
        
        if checked:
            # Si une facture est déjà sélectionnée, charger son montant
            facture_id = self.facture_combo.currentData()
            if facture_id:
                self.load_invoice_amount(facture_id)
        else:
            # Si décoché, ne pas vider le montant mais permettre la modification manuelle
            self.status_label.setText("")
            self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
    
    def on_facture_changed(self, index):
        """Quand la facture sélectionnée change, met à jour le montant"""
        if self.facture_check.isChecked():
            facture_id = self.facture_combo.currentData()
            if facture_id:
                self.load_invoice_amount(facture_id)
    
    def upload_justificatif(self):
        """Charge un fichier justificatif"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un justificatif",
            "",
            "Documents (*.pdf *.jpg *.jpeg *.png *.xlsx *.docx);;Tous les fichiers (*)"
        )
        
        if file_path:
            self.justificatif_path = file_path
            filename = os.path.basename(file_path)
            self.justificatif_label.setText(f"📄 {filename}")
            self.justificatif_label.setStyleSheet("color: #27ae60;")
            self.btn_view.setEnabled(True)
            self.btn_remove.setEnabled(True)
    
    def view_justificatif(self):
        """Ouvre le justificatif avec l'application par défaut"""
        if self.justificatif_path and os.path.exists(self.justificatif_path):
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(self.justificatif_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', self.justificatif_path])
            else:  # Linux
                subprocess.run(['xdg-open', self.justificatif_path])
    
    def remove_justificatif(self):
        """Supprime le justificatif"""
        self.justificatif_path = None
        self.justificatif_label.setText("Aucun justificatif")
        self.justificatif_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.btn_view.setEnabled(False)
        self.btn_remove.setEnabled(False)
    
    def load_data(self):
        """Charge les données d'une transaction existante"""
        if not self.transaction_id:
            return
        
        try:
            with get_session() as session:
                transaction = session.query(BankTransaction).filter(
                    BankTransaction.id == self.transaction_id
                ).first()
                
                if transaction:
                    # Compte
                    index = self.compte_combo.findData(transaction.compte_id)
                    if index >= 0:
                        self.compte_combo.setCurrentIndex(index)
                    
                    # Type
                    index = self.type_combo.findData(transaction.type_transaction)
                    if index >= 0:
                        self.type_combo.setCurrentIndex(index)
                    
                    # Date
                    self.date_edit.setDate(QDate(
                        transaction.date_transaction.year,
                        transaction.date_transaction.month,
                        transaction.date_transaction.day
                    ))
                    
                    # Montant
                    self.montant_spin.setValue(transaction.montant)
                    
                    # Catégorie
                    if transaction.categorie_id:
                        index = self.categorie_combo.findData(transaction.categorie_id)
                        if index >= 0:
                            self.categorie_combo.setCurrentIndex(index)
                    
                    # Bénéficiaire
                    self.beneficiaire_edit.setText(transaction.beneficiaire or "")
                    
                    # Source
                    self.source_edit.setText(transaction.source or "")
                    
                    # Référence
                    self.reference_edit.setText(transaction.reference or "")
                    
                    # Description
                    self.description_edit.setText(transaction.description or "")
                    
                    # Facture
                    if transaction.facture_id:
                        self.facture_check.setChecked(True)
                        index = self.facture_combo.findData(transaction.facture_id)
                        if index >= 0:
                            self.facture_combo.setCurrentIndex(index)
                    
                    # Justificatif
                    if transaction.justificatif_path and os.path.exists(transaction.justificatif_path):
                        self.justificatif_path = transaction.justificatif_path
                        filename = os.path.basename(transaction.justificatif_path)
                        self.justificatif_label.setText(f"📄 {filename}")
                        self.justificatif_label.setStyleSheet("color: #27ae60;")
                        self.btn_view.setEnabled(True)
                        self.btn_remove.setEnabled(True)
                    
                    # Notes
                    self.notes_edit.setText(transaction.notes or "")
        except Exception as e:
            print(f"❌ Erreur lors du chargement des données: {e}")
    
    def save_transaction(self):
        """Sauvegarde la transaction"""
        # Validations
        if self.compte_combo.currentData() is None:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un compte")
            return
        
        if self.montant_spin.value() <= 0:
            QMessageBox.warning(self, "Erreur", "Le montant doit être supérieur à 0")
            return
        
        transaction_type = self.type_combo.currentData()
        
        # Validations selon le type
        if transaction_type == TransactionType.RETRAIT:
            if self.categorie_combo.currentData() is None:
                QMessageBox.warning(self, "Erreur", "Veuillez sélectionner une catégorie de dépense")
                return
            if not self.beneficiaire_edit.text().strip():
                QMessageBox.warning(self, "Erreur", "Veuillez saisir le bénéficiaire")
                return
        
        elif transaction_type == TransactionType.DEPOT:
            if not self.source_edit.text().strip() and not self.facture_check.isChecked():
                QMessageBox.warning(self, "Erreur", "Veuillez indiquer la source du dépôt")
                return
        
        try:
            with get_session() as session:
                if self.transaction_id:
                    transaction = session.query(BankTransaction).filter(
                        BankTransaction.id == self.transaction_id
                    ).first()
                else:
                    transaction = BankTransaction()
                    session.add(transaction)
                
                # Mettre à jour les champs
                transaction.compte_id = self.compte_combo.currentData()
                transaction.type_transaction = transaction_type
                transaction.date_transaction = datetime.combine(
                    self.date_edit.date().toPyDate(),
                    datetime.now().time()
                )
                transaction.montant = self.montant_spin.value()
                
                # Champs optionnels
                transaction.categorie_id = self.categorie_combo.currentData()
                transaction.beneficiaire = self.beneficiaire_edit.text().strip() or None
                transaction.source = self.source_edit.text().strip() or None
                transaction.reference = self.reference_edit.text().strip() or None
                transaction.description = self.description_edit.toPlainText().strip() or None
                transaction.notes = self.notes_edit.toPlainText().strip() or None
                
                # Lien avec facture
                if self.facture_check.isChecked():
                    transaction.facture_id = self.facture_combo.currentData()
                else:
                    transaction.facture_id = None
                
                # Gestion du justificatif
                if self.justificatif_path:
                    # Copier le justificatif dans le dossier de l'application
                    justificatifs_dir = "assets/justificatifs"
                    os.makedirs(justificatifs_dir, exist_ok=True)
                    
                    # Générer un nom unique
                    ext = os.path.splitext(self.justificatif_path)[1]
                    new_filename = f"{uuid.uuid4().hex}{ext}"
                    dest_path = os.path.join(justificatifs_dir, new_filename)
                    
                    # Copier si c'est un nouveau fichier
                    if not os.path.exists(dest_path):
                        import shutil
                        shutil.copy2(self.justificatif_path, dest_path)
                    
                    transaction.justificatif_path = dest_path
                
                # Recalculer le solde du compte
                self.update_account_balance(session, transaction)
                
                session.commit()
                
                QMessageBox.information(
                    self, "Succès",
                    "Transaction enregistrée avec succès!"
                )
                
                self.transaction_saved.emit()
                self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_account_balance(self, session, transaction):
        """Met à jour le solde du compte après la transaction"""
        compte = session.query(BankAccount).filter(
            BankAccount.id == transaction.compte_id
        ).first()
        
        if compte:
            # Recalculer tous les soldes à partir de la dernière transaction
            transactions = session.query(BankTransaction).filter(
                BankTransaction.compte_id == compte.id,
                BankTransaction.id != transaction.id
            ).order_by(BankTransaction.date_transaction).all()
            
            solde = compte.solde_initial
            
            # Ajouter la nouvelle transaction dans l'ordre
            all_transactions = transactions + [transaction]
            all_transactions.sort(key=lambda x: x.date_transaction)
            
            for t in all_transactions:
                if t.est_entree:
                    solde += t.montant
                elif t.est_sortie:
                    solde -= t.montant
                t.solde_apres = solde
            
            compte.solde_actuel = solde