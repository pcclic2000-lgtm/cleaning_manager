# views/company_view.py
import os
import datetime
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFormLayout, QLineEdit, QLabel, QMessageBox,
    QTextEdit, QFileDialog, QGroupBox, QTabWidget,
    QCheckBox, QSpinBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from database.db import SessionLocal, get_session
from models.company import CompanyInfo, CompanySettings


class CompanyInfoView(QWidget):
    """Vue pour modifier les informations de l'entreprise"""
    
    def __init__(self):
        super().__init__()
        self.logo_path = None
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title = QLabel("🏢 CONFIGURATION DE L'ENTREPRISE")
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
        
        # Informations générales
        tab_general = QWidget()
        general_layout = QVBoxLayout()
        general_layout.setSpacing(15)
        
        # ===== LOGO =====
        logo_group = QGroupBox("🖼️ LOGO DE L'ENTREPRISE")
        logo_group.setStyleSheet("""
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
        logo_layout = QHBoxLayout()
        
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(150, 150)
        self.logo_label.setStyleSheet("""
            border: 2px dashed #dee2e6;
            border-radius: 8px;
            background: white;
        """)
        self.logo_label.setText("Logo\n(150x150 px)")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_buttons = QVBoxLayout()
        btn_load_logo = QPushButton("📁 Charger un logo")
        btn_load_logo.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        btn_load_logo.clicked.connect(self.load_logo)
        
        btn_remove_logo = QPushButton("🗑️ Supprimer le logo")
        btn_remove_logo.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        btn_remove_logo.clicked.connect(self.remove_logo)
        
        logo_buttons.addWidget(btn_load_logo)
        logo_buttons.addWidget(btn_remove_logo)
        logo_buttons.addStretch()
        
        logo_layout.addWidget(self.logo_label)
        logo_layout.addLayout(logo_buttons)
        logo_group.setLayout(logo_layout)
        general_layout.addWidget(logo_group)
        
        # ===== INFORMATIONS GÉNÉRALES =====
        info_group = QGroupBox("📋 INFORMATIONS GÉNÉRALES")
        info_group.setStyleSheet("""
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
        info_layout = QFormLayout()
        info_layout.setSpacing(10)
        
        self.nom = QLineEdit()
        self.nom.setPlaceholderText("Nom de l'entreprise")
        self.nom.setMinimumHeight(35)
        
        self.adresse = QTextEdit()
        self.adresse.setMaximumHeight(80)
        self.adresse.setPlaceholderText("Adresse complète")
        
        self.ville = QLineEdit()
        self.ville.setPlaceholderText("Ville")
        self.ville.setMinimumHeight(35)
        
        self.code_postal = QLineEdit()
        self.code_postal.setPlaceholderText("Code postal")
        self.code_postal.setMinimumHeight(35)
        
        self.telephone = QLineEdit()
        self.telephone.setPlaceholderText("Téléphone")
        self.telephone.setMinimumHeight(35)
        
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        self.email.setMinimumHeight(35)
        
        self.site_web = QLineEdit()
        self.site_web.setPlaceholderText("Site web")
        self.site_web.setMinimumHeight(35)
        
        info_layout.addRow("Nom*:", self.nom)
        info_layout.addRow("Adresse:", self.adresse)
        info_layout.addRow("Ville:", self.ville)
        info_layout.addRow("Code postal:", self.code_postal)
        info_layout.addRow("Téléphone:", self.telephone)
        info_layout.addRow("Email:", self.email)
        info_layout.addRow("Site web:", self.site_web)
        
        info_group.setLayout(info_layout)
        general_layout.addWidget(info_group)
        
        # ===== DIRECTEUR / GÉRANT =====
        directeur_group = QGroupBox("👔 DIRECTION DE L'ENTREPRISE")
        directeur_group.setStyleSheet("""
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
        directeur_layout = QFormLayout()
        directeur_layout.setSpacing(10)
        
        self.nom_directeur = QLineEdit()
        self.nom_directeur.setPlaceholderText("Nom et prénom du directeur/gérant")
        self.nom_directeur.setMinimumHeight(35)
        
        self.fonction_directeur = QComboBox()
        self.fonction_directeur.setEditable(True)
        self.fonction_directeur.addItems([
            "Gérant",
            "Directeur Général",
            "Président Directeur Général",
            "Directeur",
            "Responsable",
            "Chef d'entreprise",
            "Administrateur"
        ])
        self.fonction_directeur.setMinimumHeight(35)
        
        info_directeur = QLabel("ℹ️ Ces informations apparaîtront comme signataire sur les documents")
        info_directeur.setStyleSheet("""
            background: #f3e5f5;
            padding: 8px;
            border-radius: 4px;
            border-left: 4px solid #9b59b6;
            color: #6a1b9a;
            font-size: 11px;
        """)
        info_directeur.setWordWrap(True)
        
        directeur_layout.addRow("Nom du directeur*:", self.nom_directeur)
        directeur_layout.addRow("Fonction:", self.fonction_directeur)
        directeur_layout.addRow("", info_directeur)
        
        directeur_group.setLayout(directeur_layout)
        general_layout.addWidget(directeur_group)
        
        # ===== NUMÉRO EMPLOYEUR =====
        employer_group = QGroupBox("🏛️ NUMÉRO EMPLOYEUR (CNAS)")
        employer_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e67e22;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #e67e22;
            }
        """)
        employer_layout = QFormLayout()
        
        self.numero_employeur = QLineEdit()
        self.numero_employeur.setPlaceholderText("Ex: 199145, 123456789, etc.")
        self.numero_employeur.setMinimumHeight(35)
        
        employer_layout.addRow("Numéro Employeur:", self.numero_employeur)
        
        employer_group.setLayout(employer_layout)
        general_layout.addWidget(employer_group)
        
        # ===== INFORMATIONS LÉGALES =====
        legal_group = QGroupBox("⚖️ INFORMATIONS LÉGALES")
        legal_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2c3e50;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #2c3e50;
            }
        """)
        legal_layout = QFormLayout()
        legal_layout.setSpacing(10)
        
        self.rc = QLineEdit()
        self.rc.setPlaceholderText("Registre de commerce")
        self.rc.setMinimumHeight(35)
        
        self.nif = QLineEdit()
        self.nif.setPlaceholderText("N° Identification Fiscale")
        self.nif.setMinimumHeight(35)
        
        self.nis = QLineEdit()
        self.nis.setPlaceholderText("N° Identification Statistique")
        self.nis.setMinimumHeight(35)
        
        self.art = QLineEdit()
        self.art.setPlaceholderText("N° Article")
        self.art.setMinimumHeight(35)
        
        legal_layout.addRow("RC:", self.rc)
        legal_layout.addRow("NIF:", self.nif)
        legal_layout.addRow("NIS:", self.nis)
        legal_layout.addRow("ART:", self.art)
        
        legal_group.setLayout(legal_layout)
        general_layout.addWidget(legal_group)
        
        # ===== INFORMATIONS BANCAIRES =====
        bank_group = QGroupBox("🏦 INFORMATIONS BANCAIRES")
        bank_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #16a085;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #16a085;
            }
        """)
        # Créer le layout directement attaché au group
        bank_layout = QFormLayout(bank_group)
        bank_layout.setSpacing(10)
        
        # RIB
        self.rib = QLineEdit()
        self.rib.setPlaceholderText("Ex: 123 45678 1234567890 12")
        self.rib.setMinimumHeight(35)
        bank_layout.addRow("RIB:", self.rib)
        
        # Nom de la banque
        self.banque = QLineEdit()
        self.banque.setPlaceholderText("Ex: Banque d'Algérie, BNA, etc.")
        self.banque.setMinimumHeight(35)
        bank_layout.addRow("Banque:", self.banque)
        
        # Compte CCP de l'entreprise
        self.compte_ccp = QLineEdit()
        self.compte_ccp.setPlaceholderText("Ex: 371997 CLE 06")
        self.compte_ccp.setMinimumHeight(35)
        bank_layout.addRow("Compte CCP:", self.compte_ccp)
        
        # Adresse de la banque
        self.adresse_banque = QTextEdit()
        self.adresse_banque.setPlaceholderText("Adresse complète de l'agence bancaire...")
        self.adresse_banque.setMaximumHeight(80)
        self.adresse_banque.setMinimumHeight(60)
        bank_layout.addRow("Adresse banque:", self.adresse_banque)
        
        # CCP de la banque (si différent)
        self.ccp_banque = QLineEdit()
        self.ccp_banque.setPlaceholderText("CCP de la banque (optionnel)")
        self.ccp_banque.setMinimumHeight(35)
        bank_layout.addRow("CCP banque:", self.ccp_banque)
        
        general_layout.addWidget(bank_group)
        
        # ===== PARAMÈTRES RÉGIONAUX =====
        regional_group = QGroupBox("🌍 PARAMÈTRES RÉGIONAUX")
        regional_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #f1c40f;
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
        regional_layout = QFormLayout()
        regional_layout.setSpacing(10)
        
        self.devise = QComboBox()
        self.devise.addItems(["DA (Dinar Algérien)", "€ (Euro)", "$ (Dollar US)", "£ (Livre Sterling)"])
        self.devise.setMinimumHeight(35)
        
        self.pays = QLineEdit()
        self.pays.setPlaceholderText("Pays")
        self.pays.setMinimumHeight(35)
        
        regional_layout.addRow("Devise:", self.devise)
        regional_layout.addRow("Pays:", self.pays)
        
        regional_group.setLayout(regional_layout)
        general_layout.addWidget(regional_group)
        
        general_layout.addStretch()
        tab_general.setLayout(general_layout)
        self.tabs.addTab(tab_general, "📋 Informations")
        
        # Ajouter d'autres onglets si nécessaire...
        
        layout.addWidget(self.tabs)
        
        # ===== BOUTONS =====
        buttons = QHBoxLayout()
        btn_save = QPushButton("💾 Enregistrer")
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
            QPushButton:hover {
                background: #219653;
            }
        """)
        btn_save.clicked.connect(self.save_data)
        
        btn_cancel = QPushButton("❌ Annuler")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        btn_cancel.clicked.connect(self.close)
        
        buttons.addStretch()
        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)
        
        layout.addLayout(buttons)
        self.setLayout(layout)
        
        self.setWindowTitle("Configuration de l'entreprise")
        self.setMinimumSize(700, 800)
    
    def load_data(self):
        """Charger les données existantes"""
        try:
            with get_session() as session:
                company = session.query(CompanyInfo).first()
                if company:
                    # Informations générales
                    self.nom.setText(company.nom or "")
                    self.adresse.setText(company.adresse or "")
                    self.ville.setText(company.ville or "")
                    self.code_postal.setText(company.code_postal or "")
                    self.telephone.setText(company.telephone or "")
                    self.email.setText(company.email or "")
                    self.site_web.setText(company.site_web or "")
                    
                    # DIRECTEUR
                    self.nom_directeur.setText(company.nom_directeur or "")
                    if company.fonction_directeur:
                        index = self.fonction_directeur.findText(company.fonction_directeur)
                        if index >= 0:
                            self.fonction_directeur.setCurrentIndex(index)
                        else:
                            self.fonction_directeur.setEditText(company.fonction_directeur)
                    
                    # NUMÉRO EMPLOYEUR
                    self.numero_employeur.setText(company.numero_employeur or "")
                    
                    # Informations légales
                    self.rc.setText(company.rc or "")
                    self.nif.setText(company.nif or "")
                    self.nis.setText(company.nis or "")
                    self.art.setText(company.art or "")
                    
                    # INFORMATIONS BANCAIRES
                    self.rib.setText(company.rib or "")
                    self.banque.setText(company.banque or "")
                    self.compte_ccp.setText(getattr(company, 'compte_ccp', "") or "")
                    self.adresse_banque.setText(getattr(company, 'adresse_banque', "") or "")
                    self.ccp_banque.setText(getattr(company, 'ccp_banque', "") or "")
                    
                    # Paramètres
                    if company.devise:
                        devise_text = company.devise
                        if devise_text == "DA":
                            self.devise.setCurrentText("DA (Dinar Algérien)")
                        elif devise_text == "€":
                            self.devise.setCurrentText("€ (Euro)")
                        elif devise_text == "$":
                            self.devise.setCurrentText("$ (Dollar US)")
                        elif devise_text == "£":
                            self.devise.setCurrentText("£ (Livre Sterling)")
                    
                    self.pays.setText(company.pays or "")
                    
                    # Charger le logo si existe
                    if company.logo_path and os.path.exists(company.logo_path):
                        self.logo_path = company.logo_path
                        pixmap = QPixmap(company.logo_path)
                        if not pixmap.isNull():
                            self.logo_label.setPixmap(
                                pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation)
                            )
                        else:
                            self.logo_label.setText("Logo\n(Erreur de chargement)")
                    else:
                        self.logo_label.setText("Logo\n(150x150 px)")
                else:
                    # Aucune donnée, utiliser les valeurs par défaut
                    self.devise.setCurrentText("DA (Dinar Algérien)")
                    self.pays.setText("Algérie")
                    self.fonction_directeur.setCurrentText("Gérant")
                    # Initialiser les champs bancaires
                    self.rib.setText("")
                    self.banque.setText("")
                    self.compte_ccp.setText("")
                    self.adresse_banque.setText("")
                    self.ccp_banque.setText("")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def save_data(self):
        """Sauvegarder les données"""
        if not self.nom.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom de l'entreprise est obligatoire")
            return
        
        # Vérifier si le nom du directeur est renseigné
        if not self.nom_directeur.text().strip():
            reply = QMessageBox.question(
                self,
                "Directeur manquant",
                "Le nom du directeur/gérant est recommandé pour les signatures sur les documents.\n"
                "Voulez-vous continuer sans le remplir?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Demander confirmation
        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous enregistrer les modifications ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            with get_session() as session:
                company = session.query(CompanyInfo).first()
                if not company:
                    company = CompanyInfo()
                    session.add(company)
                
                # Informations générales
                company.nom = self.nom.text().strip()
                company.adresse = self.adresse.toPlainText().strip() or None
                company.ville = self.ville.text().strip() or None
                company.code_postal = self.code_postal.text().strip() or None
                company.telephone = self.telephone.text().strip() or None
                company.email = self.email.text().strip() or None
                company.site_web = self.site_web.text().strip() or None
                
                # DIRECTEUR
                company.nom_directeur = self.nom_directeur.text().strip() or None
                company.fonction_directeur = self.fonction_directeur.currentText().strip() or None
                
                # NUMÉRO EMPLOYEUR
                company.numero_employeur = self.numero_employeur.text().strip() or None
                
                # Informations légales
                company.rc = self.rc.text().strip() or None
                company.nif = self.nif.text().strip() or None
                company.nis = self.nis.text().strip() or None
                company.art = self.art.text().strip() or None
                
                # INFORMATIONS BANCAIRES
                company.rib = self.rib.text().strip() or None
                company.banque = self.banque.text().strip() or None
                company.compte_ccp = self.compte_ccp.text().strip() or None
                company.adresse_banque = self.adresse_banque.toPlainText().strip() or None
                company.ccp_banque = self.ccp_banque.text().strip() or None
                
                # Paramètres
                company.devise = self.extract_devise_code(self.devise.currentText())
                company.pays = self.pays.text().strip() or "Algérie"
                
                # Gérer le logo
                if hasattr(self, 'logo_path') and self.logo_path and os.path.exists(self.logo_path):
                    # Copier le logo dans le dossier assets si différent
                    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
                    os.makedirs(assets_dir, exist_ok=True)
                    
                    if not self.logo_path.startswith(assets_dir):
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        ext = os.path.splitext(self.logo_path)[1]
                        dest_filename = f"logo_{timestamp}{ext}"
                        dest_path = os.path.join(assets_dir, dest_filename)
                        
                        shutil.copy2(self.logo_path, dest_path)
                        company.logo_path = dest_path
                    else:
                        company.logo_path = self.logo_path
                elif hasattr(self, 'logo_path') and self.logo_path == "":
                    company.logo_path = None
                
                session.commit()
                
                QMessageBox.information(self, "Succès", 
                    "Informations de l'entreprise enregistrées avec succès.\n"
                    "Les modifications seront prises en compte dans les nouvelles factures.")
                
                self.close()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", 
                f"Erreur lors de l'enregistrement:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def extract_devise_code(self, devise_text):
        """Extraire le code devise du texte complet"""
        if "DA" in devise_text:
            return "DA"
        elif "€" in devise_text:
            return "€"
        elif "$" in devise_text:
            return "$"
        elif "£" in devise_text:
            return "£"
        return "DA"
    
    def load_logo(self):
        """Charger un logo depuis le disque"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un logo",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.logo_label.setPixmap(
                    pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, 
                                Qt.TransformationMode.SmoothTransformation)
                )
                self.logo_path = file_path
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de charger l'image")
    
    def remove_logo(self):
        """Supprimer le logo"""
        self.logo_label.setText("Logo\n(150x150 px)")
        self.logo_label.setPixmap(QPixmap())
        self.logo_path = ""


class CompanySettingsView(QWidget):
    """Vue pour les paramètres de l'application"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title = QLabel("⚙️ PARAMÈTRES DE L'APPLICATION")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 5px solid #34495e;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Paramètres des factures
        invoice_group = QGroupBox("🧾 PARAMÈTRES DES FACTURES")
        invoice_group.setStyleSheet("""
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
        invoice_layout = QFormLayout()
        invoice_layout.setSpacing(10)
        
        self.prefix_facture = QLineEdit()
        self.prefix_facture.setPlaceholderText("Ex: FAC")
        self.prefix_facture.setMinimumHeight(35)
        
        self.taux_tva = QSpinBox()
        self.taux_tva.setRange(0, 100)
        self.taux_tva.setSuffix(" %")
        self.taux_tva.setMinimumHeight(35)
        
        self.conditions_paiement = QTextEdit()
        self.conditions_paiement.setMaximumHeight(80)
        self.conditions_paiement.setPlaceholderText("Conditions de paiement par défaut...")
        
        invoice_layout.addRow("Préfixe facture:", self.prefix_facture)
        invoice_layout.addRow("Taux TVA par défaut:", self.taux_tva)
        invoice_layout.addRow("Conditions paiement:", self.conditions_paiement)
        
        invoice_group.setLayout(invoice_layout)
        layout.addWidget(invoice_group)
        
        # Sauvegarde automatique
        backup_group = QGroupBox("💾 SAUVEGARDE AUTOMATIQUE")
        backup_group.setStyleSheet("""
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
        backup_layout = QFormLayout()
        backup_layout.setSpacing(10)
        
        self.auto_sauvegarde = QCheckBox("Activer la sauvegarde automatique")
        self.auto_sauvegarde.setMinimumHeight(35)
        
        self.frequence_sauvegarde = QSpinBox()
        self.frequence_sauvegarde.setRange(1, 30)
        self.frequence_sauvegarde.setSuffix(" jours")
        self.frequence_sauvegarde.setMinimumHeight(35)
        
        backup_layout.addRow("", self.auto_sauvegarde)
        backup_layout.addRow("Fréquence:", self.frequence_sauvegarde)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # Sécurité
        security_group = QGroupBox("🔐 SÉCURITÉ")
        security_group.setStyleSheet("""
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
        security_layout = QFormLayout()
        security_layout.setSpacing(10)
        
        self.session_timeout = QSpinBox()
        self.session_timeout.setRange(5, 240)
        self.session_timeout.setSuffix(" minutes")
        self.session_timeout.setMinimumHeight(35)
        
        security_layout.addRow("Délai de session:", self.session_timeout)
        
        security_group.setLayout(security_layout)
        layout.addWidget(security_group)
        
        layout.addStretch()
        
        # Boutons
        buttons = QHBoxLayout()
        
        btn_save = QPushButton("💾 Enregistrer les paramètres")
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
            QPushButton:hover {
                background: #219653;
            }
        """)
        btn_save.clicked.connect(self.save_data)
        
        btn_cancel = QPushButton("❌ Annuler")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        btn_cancel.clicked.connect(self.close)
        
        buttons.addStretch()
        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)
        
        layout.addLayout(buttons)
        self.setLayout(layout)
        
        self.setWindowTitle("Paramètres de l'application")
        self.setMinimumSize(600, 600)
    
    def load_data(self):
        """Charger les paramètres"""
        try:
            with get_session() as session:
                settings = session.query(CompanySettings).first()
                if settings:
                    self.prefix_facture.setText(settings.prefix_facture or "FAC")
                    self.taux_tva.setValue(settings.taux_tva or 19)
                    self.conditions_paiement.setText(settings.conditions_paiement or "")
                    self.auto_sauvegarde.setChecked(settings.auto_sauvegarde or True)
                    self.frequence_sauvegarde.setValue(settings.frequence_sauvegarde or 7)
                    self.session_timeout.setValue(settings.session_timeout or 30)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
    
    def save_data(self):
        """Sauvegarder les paramètres"""
        try:
            with get_session() as session:
                settings = session.query(CompanySettings).first()
                if not settings:
                    settings = CompanySettings()
                    session.add(settings)
                
                settings.prefix_facture = self.prefix_facture.text().strip() or "FAC"
                settings.taux_tva = self.taux_tva.value()
                settings.conditions_paiement = self.conditions_paiement.toPlainText().strip() or None
                settings.auto_sauvegarde = self.auto_sauvegarde.isChecked()
                settings.frequence_sauvegarde = self.frequence_sauvegarde.value()
                settings.session_timeout = self.session_timeout.value()
                
                session.commit()
                QMessageBox.information(self, "Succès", "Paramètres enregistrés avec succès")
                self.close()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement: {str(e)}")