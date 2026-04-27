# views/settings_view.py - VERSION COMPLÈTE CORRIGÉE
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTabWidget, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QGroupBox, QLabel,
    QFileDialog, QMessageBox, QCheckBox, QScrollArea,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon
import os
from datetime import datetime
from database.db import SessionLocal, get_session
from models.company import CompanyInfo, CompanySettings


class CompanyInfoWidget(QWidget):
    """Widget pour les informations de l'entreprise AVEC COMPTE CCP"""
    
    data_updated = pyqtSignal()  # Signal pour notifier les changements
    
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.logo_pixmap = None
        self.logo_path = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Titre
        title_label = QLabel("🏢 Informations de l'Entreprise")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title_label)

        # Widget défilable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)

        # ===== SECTION LOGO =====
        logo_group = QGroupBox("Logo")
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
        logo_layout = QVBoxLayout()
        
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(150, 150)
        self.logo_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #bdc3c7;
                border-radius: 5px;
                background-color: #f8f9fa;
            }
        """)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setText("Logo\n(150x150)")
        
        logo_buttons = QHBoxLayout()
        btn_load_logo = QPushButton("📁 Charger Logo")
        btn_load_logo.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_load_logo.clicked.connect(self.load_logo)
        
        btn_clear_logo = QPushButton("🗑 Supprimer")
        btn_clear_logo.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_clear_logo.clicked.connect(self.clear_logo)
        
        logo_buttons.addWidget(btn_load_logo)
        logo_buttons.addWidget(btn_clear_logo)
        logo_buttons.addStretch()
        
        logo_layout.addWidget(self.logo_label, 0, Qt.AlignmentFlag.AlignCenter)
        logo_layout.addLayout(logo_buttons)
        logo_group.setLayout(logo_layout)
        content_layout.addWidget(logo_group)

        # ===== INFORMATIONS GÉNÉRALES =====
        info_group = QGroupBox("Informations Générales")
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
        info_layout.addRow("Nom de l'entreprise *", self.nom)
        
        self.adresse = QTextEdit()
        self.adresse.setFixedHeight(60)
        self.adresse.setPlaceholderText("Adresse complète")
        info_layout.addRow("Adresse", self.adresse)
        
        self.ville = QLineEdit()
        self.ville.setPlaceholderText("Ville")
        info_layout.addRow("Ville", self.ville)
        
        self.code_postal = QLineEdit()
        self.code_postal.setPlaceholderText("Code postal")
        info_layout.addRow("Code postal", self.code_postal)
        
        self.telephone = QLineEdit()
        self.telephone.setPlaceholderText("Téléphone")
        info_layout.addRow("Téléphone", self.telephone)
        
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        info_layout.addRow("Email", self.email)
        
        self.site_web = QLineEdit()
        self.site_web.setPlaceholderText("Site web")
        info_layout.addRow("Site web", self.site_web)
        
        info_group.setLayout(info_layout)
        content_layout.addWidget(info_group)

        # ===== DIRECTEUR / GÉRANT =====
        directeur_group = QGroupBox("👔 Direction de l'Entreprise")
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
        self.nom_directeur.setToolTip("Sera utilisé pour les signatures sur les documents")
        directeur_layout.addRow("Nom du directeur *", self.nom_directeur)
        
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
        self.fonction_directeur.setPlaceholderText("Choisir ou saisir une fonction")
        directeur_layout.addRow("Fonction", self.fonction_directeur)
        
        info_directeur = QLabel("ℹ️ Ces informations apparaîtront comme signataire sur les factures, devis et bons de commande.")
        info_directeur.setStyleSheet("""
            background: #f3e5f5;
            padding: 8px;
            border-radius: 4px;
            border-left: 4px solid #9b59b6;
            color: #6a1b9a;
            font-size: 11px;
        """)
        info_directeur.setWordWrap(True)
        directeur_layout.addRow("", info_directeur)
        
        directeur_group.setLayout(directeur_layout)
        content_layout.addWidget(directeur_group)

        # ===== NUMÉRO EMPLOYEUR =====
        employer_group = QGroupBox("🏛️  Numéro Employeur (CNAS)")
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
        self.numero_employeur.setToolTip("Numéro employeur CNAS pour les déclarations sociales")
        employer_layout.addRow("Numéro Employeur", self.numero_employeur)
        
        employer_group.setLayout(employer_layout)
        content_layout.addWidget(employer_group)

        # ===== INFORMATIONS LÉGALES =====
        legal_group = QGroupBox("Informations Légales")
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
        
        self.rc = QLineEdit()
        self.rc.setPlaceholderText("Registre de commerce")
        legal_layout.addRow("Registre de Commerce (RC)", self.rc)
        
        self.nif = QLineEdit()
        self.nif.setPlaceholderText("N° Identification Fiscale")
        legal_layout.addRow("Numéro d'Identification Fiscale (NIF)", self.nif)
        
        self.nis = QLineEdit()
        self.nis.setPlaceholderText("N° Identification Statistique")
        legal_layout.addRow("Numéro d'Identification Statistique (NIS)", self.nis)
        
        self.art = QLineEdit()
        self.art.setPlaceholderText("N° Article")
        legal_layout.addRow("Numéro d'Article (ART)", self.art)
        
        legal_group.setLayout(legal_layout)
        content_layout.addWidget(legal_group)

        # ===== INFORMATIONS BANCAIRES =====
        bank_group = QGroupBox("🏦 Informations Bancaires")
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
        # Layout directement attaché au groupe
        bank_layout = QFormLayout(bank_group)
        bank_layout.setSpacing(10)
        
        # RIB
        self.rib = QLineEdit()
        self.rib.setPlaceholderText("Ex: 123 45678 1234567890 12")
        bank_layout.addRow("RIB", self.rib)
        
        # Nom de la banque
        self.banque = QLineEdit()
        self.banque.setPlaceholderText("Ex: Banque d'Algérie, BNA, etc.")
        bank_layout.addRow("Banque", self.banque)
        
        # Compte CCP de l'entreprise
        self.compte_ccp = QLineEdit()
        self.compte_ccp.setPlaceholderText("Ex: 371997 CLE 06")
        bank_layout.addRow("Compte CCP", self.compte_ccp)
        
        # Adresse de la banque
        self.adresse_banque = QTextEdit()
        self.adresse_banque.setPlaceholderText("Adresse complète de l'agence bancaire...")
        self.adresse_banque.setFixedHeight(80)
        bank_layout.addRow("Adresse banque", self.adresse_banque)
        
        # CCP de la banque (si différent)
        self.ccp_banque = QLineEdit()
        self.ccp_banque.setPlaceholderText("CCP de la banque (optionnel)")
        bank_layout.addRow("CCP banque", self.ccp_banque)
        
        content_layout.addWidget(bank_group)

        # ===== PARAMÈTRES RÉGIONAUX =====
        regional_group = QGroupBox("Paramètres Régionaux")
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
        
        self.devise = QComboBox()
        self.devise.addItems(["DA", "€", "$", "£"])
        regional_layout.addRow("Devise", self.devise)
        
        self.pays = QLineEdit()
        self.pays.setText("Algérie")
        regional_layout.addRow("Pays", self.pays)
        
        regional_group.setLayout(regional_layout)
        content_layout.addWidget(regional_group)

        # Espace flexible
        content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # ===== BOUTONS =====
        buttons_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("💾 Enregistrer")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 10px 25px;
                font-weight: bold;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.btn_save.clicked.connect(self.save_data)
        
        self.btn_reset = QPushButton("↺ Réinitialiser")
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                padding: 10px 25px;
                font-weight: bold;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d68910;
            }
        """)
        self.btn_reset.clicked.connect(self.load_data)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_reset)
        buttons_layout.addWidget(self.btn_save)
        
        layout.addLayout(buttons_layout)

    def load_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un logo",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            self.logo_pixmap = QPixmap(file_path)
            if not self.logo_pixmap.isNull():
                # Redimensionner pour s'adapter au label
                scaled_pixmap = self.logo_pixmap.scaled(
                    140, 140,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.logo_label.setPixmap(scaled_pixmap)
                self.logo_path = file_path
            else:
                QMessageBox.warning(self, "Erreur", "Format d'image non supporté")

    def clear_logo(self):
        self.logo_label.clear()
        self.logo_label.setText("Logo\n(150x150)")
        self.logo_pixmap = None
        self.logo_path = None

    def load_data(self):
        """Charge les données existantes de l'entreprise"""
        try:
            company = self.session.query(CompanyInfo).first()
            
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
                
                # ===== INFORMATIONS BANCAIRES =====
                self.rib.setText(company.rib or "")
                self.banque.setText(company.banque or "")
                self.compte_ccp.setText(getattr(company, 'compte_ccp', "") or "")
                self.adresse_banque.setText(getattr(company, 'adresse_banque', "") or "")
                self.ccp_banque.setText(getattr(company, 'ccp_banque', "") or "")
                
                # Paramètres régionaux
                self.devise.setCurrentText(company.devise or "DA")
                self.pays.setText(company.pays or "Algérie")
                
                # Charger le logo
                if company.logo_path and os.path.exists(company.logo_path):
                    self.logo_path = company.logo_path
                    self.logo_pixmap = QPixmap(company.logo_path)
                    if not self.logo_pixmap.isNull():
                        scaled_pixmap = self.logo_pixmap.scaled(
                            140, 140,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self.logo_label.setPixmap(scaled_pixmap)
                    else:
                        self.clear_logo()
                else:
                    self.clear_logo()
            else:
                # Valeurs par défaut
                self.clear_logo()
                self.pays.setText("Algérie")
                self.devise.setCurrentText("DA")
                self.fonction_directeur.setCurrentText("Gérant")
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
        """Sauvegarde les données de l'entreprise"""
        # Validation des champs obligatoires
        errors = []
        
        if not self.nom.text().strip():
            errors.append("Le nom de l'entreprise est obligatoire")
        
        # Le nom du directeur est recommandé mais pas obligatoire
        if not self.nom_directeur.text().strip():
            reply = QMessageBox.question(
                self,
                "Directeur manquant",
                "Le nom du directeur/gérant est recommandé pour les signatures sur les documents.\n"
                "Voulez-vous continuer sans le remplir?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        if errors:
            QMessageBox.warning(self, "Erreur de validation", "\n".join(errors))
            return

        try:
            company = self.session.query(CompanyInfo).first()
            if not company:
                company = CompanyInfo()
                self.session.add(company)

            # Informations générales
            company.nom = self.nom.text().strip()
            company.adresse = self.adresse.toPlainText().strip()
            company.ville = self.ville.text().strip()
            company.code_postal = self.code_postal.text().strip()
            company.telephone = self.telephone.text().strip()
            company.email = self.email.text().strip()
            company.site_web = self.site_web.text().strip()
            
            # DIRECTEUR
            company.nom_directeur = self.nom_directeur.text().strip()
            company.fonction_directeur = self.fonction_directeur.currentText().strip()
            
            # NUMÉRO EMPLOYEUR
            company.numero_employeur = self.numero_employeur.text().strip()
            
            # Informations légales
            company.rc = self.rc.text().strip()
            company.nif = self.nif.text().strip()
            company.nis = self.nis.text().strip()
            company.art = self.art.text().strip()
            
            # ===== INFORMATIONS BANCAIRES =====
            company.rib = self.rib.text().strip()
            company.banque = self.banque.text().strip()
            company.compte_ccp = self.compte_ccp.text().strip()
            company.adresse_banque = self.adresse_banque.toPlainText().strip()
            company.ccp_banque = self.ccp_banque.text().strip()
            
            # Paramètres régionaux
            company.devise = self.devise.currentText()
            company.pays = self.pays.text().strip()
            
            # Logo
            if hasattr(self, 'logo_path') and self.logo_path:
                # Copier le logo dans le dossier de l'application
                logos_dir = "assets/logos"
                os.makedirs(logos_dir, exist_ok=True)
                
                # Générer un nom de fichier unique
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = os.path.splitext(self.logo_path)[1]
                new_filename = f"logo_{timestamp}{ext}"
                dest_path = os.path.join(logos_dir, new_filename)
                
                try:
                    import shutil
                    shutil.copy2(self.logo_path, dest_path)
                    company.logo_path = dest_path
                except Exception as e:
                    QMessageBox.warning(self, "Attention", 
                                      f"Erreur lors de la copie du logo: {str(e)}")

            self.session.commit()
            QMessageBox.information(self, "Succès", 
                                  "Informations de l'entreprise enregistrées avec succès!")
            
            # Émettre un signal pour indiquer que les données ont changé
            self.data_updated.emit()
                
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erreur", 
                               f"Erreur lors de l'enregistrement: {str(e)}")
            import traceback
            traceback.print_exc()


class InvoiceSettingsWidget(QWidget):
    """Widget pour les paramètres de facturation"""
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Titre
        title_label = QLabel("🧾 Paramètres de Facturation")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title_label)

        # Widget défilable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)

        # Préfixes et numérotation
        numbering_group = QGroupBox("Numérotation")
        numbering_group.setStyleSheet("""
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
        numbering_layout = QFormLayout()
        numbering_layout.setSpacing(10)
        
        self.prefix_facture = QLineEdit()
        numbering_layout.addRow("Préfixe Factures", self.prefix_facture)
        
        self.prochain_numero_facture = QSpinBox()
        self.prochain_numero_facture.setMinimum(1)
        self.prochain_numero_facture.setMaximum(999999)
        numbering_layout.addRow("Prochain numéro facture", self.prochain_numero_facture)
        
        self.prefix_devis = QLineEdit()
        numbering_layout.addRow("Préfixe Devis", self.prefix_devis)
        
        self.prochain_numero_devis = QSpinBox()
        self.prochain_numero_devis.setMinimum(1)
        self.prochain_numero_devis.setMaximum(999999)
        numbering_layout.addRow("Prochain numéro devis", self.prochain_numero_devis)
        
        self.prefix_bon = QLineEdit()
        numbering_layout.addRow("Préfixe Bons", self.prefix_bon)
        
        self.prochain_numero_bon = QSpinBox()
        self.prochain_numero_bon.setMinimum(1)
        self.prochain_numero_bon.setMaximum(999999)
        numbering_layout.addRow("Prochain numéro bon", self.prochain_numero_bon)
        
        numbering_group.setLayout(numbering_layout)
        content_layout.addWidget(numbering_group)

        # Paramètres fiscaux
        tax_group = QGroupBox("Paramètres Fiscaux")
        tax_group.setStyleSheet("""
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
        tax_layout = QFormLayout()
        tax_layout.setSpacing(10)
        
        self.taux_tva = QSpinBox()
        self.taux_tva.setMinimum(0)
        self.taux_tva.setMaximum(100)
        self.taux_tva.setSuffix("%")
        tax_layout.addRow("Taux de TVA", self.taux_tva)
        
        self.mention_legale = QTextEdit()
        self.mention_legale.setFixedHeight(60)
        tax_layout.addRow("Mention légale", self.mention_legale)
        
        self.conditions_paiement = QTextEdit()
        self.conditions_paiement.setFixedHeight(60)
        tax_layout.addRow("Conditions de paiement", self.conditions_paiement)
        
        tax_group.setLayout(tax_layout)
        content_layout.addWidget(tax_group)

        # En-tête et pied de page
        header_footer_group = QGroupBox("En-tête et Pied de Page")
        header_footer_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e74c3c;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #c0392b;
            }
        """)
        header_footer_layout = QFormLayout()
        header_footer_layout.setSpacing(10)
        
        self.entete_facture = QTextEdit()
        self.entete_facture.setFixedHeight(60)
        header_footer_layout.addRow("En-tête des factures", self.entete_facture)
        
        self.pied_facture = QTextEdit()
        self.pied_facture.setFixedHeight(60)
        header_footer_layout.addRow("Pied de page des factures", self.pied_facture)
        
        header_footer_group.setLayout(header_footer_layout)
        content_layout.addWidget(header_footer_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # Boutons
        buttons_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("💾 Enregistrer")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 10px 25px;
                font-weight: bold;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.btn_save.clicked.connect(self.save_data)
        
        self.btn_reset = QPushButton("↺ Réinitialiser")
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                padding: 10px 25px;
                font-weight: bold;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d68910;
            }
        """)
        self.btn_reset.clicked.connect(self.load_data)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_reset)
        buttons_layout.addWidget(self.btn_save)
        
        layout.addLayout(buttons_layout)

    def load_data(self):
        settings = self.session.query(CompanySettings).first()
        
        if settings:
            self.prefix_facture.setText(settings.prefix_facture or "FAC")
            self.prefix_devis.setText(settings.prefix_devis or "DEV")
            self.prefix_bon.setText(settings.prefix_bon or "BON")
            
            self.prochain_numero_facture.setValue(settings.prochain_numero_facture or 1)
            self.prochain_numero_devis.setValue(settings.prochain_numero_devis or 1)
            self.prochain_numero_bon.setValue(settings.prochain_numero_bon or 1)
            
            self.taux_tva.setValue(settings.taux_tva or 19)
            self.mention_legale.setText(settings.mention_legale or "")
            self.conditions_paiement.setText(settings.conditions_paiement or "")
            self.entete_facture.setText(settings.entete_facture or "")
            self.pied_facture.setText(settings.pied_facture or "")
        else:
            # Valeurs par défaut
            self.prefix_facture.setText("FAC")
            self.prefix_devis.setText("DEV")
            self.prefix_bon.setText("BON")
            self.prochain_numero_facture.setValue(1)
            self.prochain_numero_devis.setValue(1)
            self.prochain_numero_bon.setValue(1)
            self.taux_tva.setValue(19)
            self.mention_legale.setText("TVA non applicable, article 293 B du CGI")
            self.conditions_paiement.setText("Paiement à 30 jours")
            self.entete_facture.setText("Facture")
            self.pied_facture.setText("Merci pour votre confiance")

    def save_data(self):
        try:
            settings = self.session.query(CompanySettings).first()
            if not settings:
                settings = CompanySettings()

            settings.prefix_facture = self.prefix_facture.text().strip()
            settings.prefix_devis = self.prefix_devis.text().strip()
            settings.prefix_bon = self.prefix_bon.text().strip()
            
            settings.prochain_numero_facture = self.prochain_numero_facture.value()
            settings.prochain_numero_devis = self.prochain_numero_devis.value()
            settings.prochain_numero_bon = self.prochain_numero_bon.value()
            
            settings.taux_tva = self.taux_tva.value()
            settings.mention_legale = self.mention_legale.toPlainText().strip()
            settings.conditions_paiement = self.conditions_paiement.toPlainText().strip()
            settings.entete_facture = self.entete_facture.toPlainText().strip()
            settings.pied_facture = self.pied_facture.toPlainText().strip()

            self.session.add(settings)
            self.session.commit()
            QMessageBox.information(self, "Succès", "Paramètres de facturation enregistrés!")
            
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement: {str(e)}")
            import traceback
            traceback.print_exc()


class ApplicationSettingsWidget(QWidget):
    """Widget pour les paramètres de l'application"""
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Titre
        title_label = QLabel("⚙️ Paramètres de l'Application")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title_label)

        # Widget défilable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)

        # Sauvegarde automatique
        backup_group = QGroupBox("Sauvegarde Automatique")
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
        
        self.auto_sauvegarde = QCheckBox("Activer la sauvegarde automatique")
        backup_layout.addRow(self.auto_sauvegarde)
        
        self.frequence_sauvegarde = QSpinBox()
        self.frequence_sauvegarde.setMinimum(1)
        self.frequence_sauvegarde.setMaximum(30)
        self.frequence_sauvegarde.setSuffix(" jours")
        backup_layout.addRow("Fréquence de sauvegarde", self.frequence_sauvegarde)
        
        backup_group.setLayout(backup_layout)
        content_layout.addWidget(backup_group)

        # Sécurité
        security_group = QGroupBox("Sécurité")
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
                color: #e67e22;
            }
        """)
        security_layout = QFormLayout()
        
        self.session_timeout = QSpinBox()
        self.session_timeout.setMinimum(5)
        self.session_timeout.setMaximum(240)
        self.session_timeout.setSuffix(" minutes")
        security_layout.addRow("Timeout session", self.session_timeout)
        
        self.mot_de_passe_admin = QLineEdit()
        self.mot_de_passe_admin.setEchoMode(QLineEdit.EchoMode.Password)
        self.mot_de_passe_admin.setPlaceholderText("Laisser vide pour ne pas changer")
        security_layout.addRow("Mot de passe admin", self.mot_de_passe_admin)
        
        btn_change_password = QPushButton("Changer le mot de passe")
        btn_change_password.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_change_password.clicked.connect(self.show_change_password_dialog)
        security_layout.addRow(btn_change_password)
        
        security_group.setLayout(security_layout)
        content_layout.addWidget(security_group)

        # Maintenance
        maintenance_group = QGroupBox("Maintenance")
        maintenance_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e74c3c;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #c0392b;
            }
        """)
        maintenance_layout = QVBoxLayout()
        
        btn_clear_cache = QPushButton("🧹 Nettoyer le cache")
        btn_clear_cache.clicked.connect(self.clear_cache)
        maintenance_layout.addWidget(btn_clear_cache)
        
        btn_backup_now = QPushButton("💾 Sauvegarde manuelle")
        btn_backup_now.clicked.connect(self.backup_now)
        maintenance_layout.addWidget(btn_backup_now)
        
        btn_restore = QPushButton("📂 Restaurer sauvegarde")
        btn_restore.clicked.connect(self.restore_backup)
        maintenance_layout.addWidget(btn_restore)
        
        maintenance_group.setLayout(maintenance_layout)
        content_layout.addWidget(maintenance_group)

        # Information système
        system_group = QGroupBox("Information Système")
        system_group.setStyleSheet("""
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
                color: #8e44ad;
            }
        """)
        system_layout = QFormLayout()
        
        import platform
        import sys
        
        system_info = [
            ("Système d'exploitation", platform.system()),
            ("Version", platform.version()),
            ("Architecture", platform.machine()),
            ("Python", sys.version.split()[0]),
            ("Répertoire d'installation", os.path.dirname(os.path.abspath(__file__))),
        ]
        
        for label, value in system_info:
            info_label = QLabel(value)
            info_label.setStyleSheet("color: #7f8c8d;")
            system_layout.addRow(label, info_label)
        
        system_group.setLayout(system_layout)
        content_layout.addWidget(system_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # Boutons
        buttons_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("💾 Enregistrer")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 10px 25px;
                font-weight: bold;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.btn_save.clicked.connect(self.save_data)
        
        self.btn_reset = QPushButton("↺ Réinitialiser")
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                padding: 10px 25px;
                font-weight: bold;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d68910;
            }
        """)
        self.btn_reset.clicked.connect(self.load_data)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_reset)
        buttons_layout.addWidget(self.btn_save)
        
        layout.addLayout(buttons_layout)

    def show_change_password_dialog(self):
        """Affiche le dialogue pour changer le mot de passe"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Changer le mot de passe")
        dialog.setFixedWidth(300)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Entrez le nouveau mot de passe administrateur:")
        layout.addWidget(label)
        
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_input.setPlaceholderText("Nouveau mot de passe")
        layout.addWidget(password_input)
        
        confirm_input = QLineEdit()
        confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_input.setPlaceholderText("Confirmer le mot de passe")
        layout.addWidget(confirm_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec():
            password = password_input.text()
            confirm = confirm_input.text()
            
            if not password:
                QMessageBox.warning(self, "Erreur", "Le mot de passe ne peut pas être vide")
                return
                
            if password != confirm:
                QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas")
                return
                
            self.mot_de_passe_admin.setText(password)
            QMessageBox.information(self, "Succès", 
                "Mot de passe défini. Cliquez sur 'Enregistrer' pour sauvegarder.")
    
    def load_data(self):
        settings = self.session.query(CompanySettings).first()
        
        if settings:
            self.auto_sauvegarde.setChecked(bool(settings.auto_sauvegarde))
            self.frequence_sauvegarde.setValue(settings.frequence_sauvegarde or 7)
            self.session_timeout.setValue(settings.session_timeout or 30)
        else:
            self.auto_sauvegarde.setChecked(True)
            self.frequence_sauvegarde.setValue(7)
            self.session_timeout.setValue(30)
        
        self.mot_de_passe_admin.clear()

    def save_data(self):
        try:
            settings = self.session.query(CompanySettings).first()
            if not settings:
                settings = CompanySettings()

            settings.auto_sauvegarde = self.auto_sauvegarde.isChecked()
            settings.frequence_sauvegarde = self.frequence_sauvegarde.value()
            settings.session_timeout = self.session_timeout.value()
            
            # Changer le mot de passe seulement si fourni
            if self.mot_de_passe_admin.text():
                settings.mot_de_passe_admin = self.mot_de_passe_admin.text()

            self.session.add(settings)
            self.session.commit()
            QMessageBox.information(self, "Succès", "Paramètres enregistrés!")
            self.mot_de_passe_admin.clear()
            
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement: {str(e)}")
            import traceback
            traceback.print_exc()

    def clear_cache(self):
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Êtes-vous sûr de vouloir nettoyer le cache ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import tempfile
                
                # Nettoyer les fichiers temporaires
                temp_dir = tempfile.gettempdir()
                app_temp_files = [f for f in os.listdir(temp_dir) if f.startswith("clean_manager")]
                
                for f in app_temp_files:
                    try:
                        os.remove(os.path.join(temp_dir, f))
                    except:
                        pass
                
                QMessageBox.information(self, "Succès", "Cache nettoyé avec succès!")
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Erreur lors du nettoyage: {str(e)}")

    def backup_now(self):
        from database.db import DATABASE_PATH
        import shutil
        
        try:
            # Créer le dossier de sauvegarde
            backup_dir = "backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Générer un nom de fichier
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"backup_{timestamp}.db")
            
            shutil.copy2(DATABASE_PATH, backup_file)
            
            QMessageBox.information(
                self,
                "Sauvegarde réussie",
                f"Base de données sauvegardée dans:\n{backup_file}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde: {str(e)}")

    def restore_backup(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner une sauvegarde",
            "backups",
            "Base de données (*.db *.sqlite *.sqlite3)"
        )
        
        if file_path:
            reply = QMessageBox.warning(
                self,
                "Attention",
                "Cette action va remplacer la base de données actuelle.\n"
                "Voulez-vous continuer ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                from database.db import DATABASE_PATH
                import shutil
                
                try:
                    # Sauvegarder la base actuelle d'abord
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_current = f"{DATABASE_PATH}.backup_{timestamp}"
                    shutil.copy2(DATABASE_PATH, backup_current)
                    
                    # Restaurer la sauvegarde
                    shutil.copy2(file_path, DATABASE_PATH)
                    
                    QMessageBox.information(
                        self,
                        "Succès",
                        f"Base de données restaurée avec succès!\n\n"
                        f"Ancienne base sauvegardée dans:\n{backup_current}"
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de la restauration: {str(e)}")


class SettingsView(QWidget):
    """Vue principale des paramètres"""
    def __init__(self):
        super().__init__()
        self.session = SessionLocal()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Titre
        title_label = QLabel("⚙️ Paramètres & Configuration")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Onglets
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
        
        # Onglet 1: Informations de l'entreprise
        self.company_info_widget = CompanyInfoWidget(self.session)
        self.tabs.addTab(self.company_info_widget, "🏢 Entreprise")
        
        # Onglet 2: Paramètres de facturation
        self.invoice_settings_widget = InvoiceSettingsWidget(self.session)
        self.tabs.addTab(self.invoice_settings_widget, "🧾 Facturation")
        
        # Onglet 3: Paramètres application
        self.app_settings_widget = ApplicationSettingsWidget(self.session)
        self.tabs.addTab(self.app_settings_widget, "⚙️ Application")
        
        layout.addWidget(self.tabs)

        # Bouton fermer
        bottom_layout = QHBoxLayout()
        
        btn_close = QPushButton("Fermer")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 10px 25px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_close.clicked.connect(self.close)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_close)
        
        layout.addLayout(bottom_layout)

    def closeEvent(self, event):
        """Ferme proprement la session de base de données"""
        self.session.close()
        event.accept()