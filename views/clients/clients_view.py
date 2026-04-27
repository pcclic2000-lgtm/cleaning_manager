# views/clients_view.py - VERSION COMPLÈTE ET CORRIGÉE
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QLineEdit, QLabel, QFormLayout, QComboBox,
    QTextEdit, QDoubleSpinBox, QHeaderView, QCheckBox,
    QTabWidget, QMenu, QAbstractItemView, QDateEdit,
    QGroupBox, QApplication, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QAction
import re
from datetime import date

from database.db import SessionLocal, get_session
from models.client import Client, generer_code_client


class ClientDialog(QDialog):
    """Dialogue pour ajouter/modifier un client"""
    
    client_saved = pyqtSignal()
    
    def __init__(self, client_id=None, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        
        self.setWindowTitle("Modifier client" if client_id else "Nouveau client")
        self.setModal(True)
        self.setMinimumWidth(700)
        
        self.init_ui()
        if client_id:
            self.load_data()
        else:
            self.generer_nouveau_code()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Onglets
        self.tabs = QTabWidget()
        
        # Onglet Informations générales
        tab_general = QWidget()
        form = QFormLayout()
        
        self.txt_code = QLineEdit()
        self.txt_code.setPlaceholderText("Généré automatiquement")
        self.txt_code.setReadOnly(True)
        
        self.txt_raison_sociale = QLineEdit()
        self.txt_raison_sociale.setPlaceholderText("Raison sociale complète *")
        
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["Particulier", "Entreprise", "Administration", "Association"])
        self.cmb_type.currentTextChanged.connect(self.on_type_change)
        
        self.cmb_secteur = QComboBox()
        self.cmb_secteur.addItems([
            "Bureaux", "Commerce", "Industrie", "Santé", "Éducation",
            "Hôtellerie", "Restauration", "Résidentiel", "Autre"
        ])
        
        self.txt_telephone = QLineEdit()
        self.txt_telephone.setPlaceholderText("Téléphone principal")
        
        self.txt_telephone2 = QLineEdit()
        self.txt_telephone2.setPlaceholderText("Téléphone secondaire")
        
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("Email")
        
        self.txt_site_web = QLineEdit()
        self.txt_site_web.setPlaceholderText("Site web")
        
        # CORRECTION: Changer les labels
        form.addRow("Code client:", self.txt_code)
        form.addRow("Raison sociale *:", self.txt_raison_sociale)
        form.addRow("Type:", self.cmb_type)
        form.addRow("Secteur:", self.cmb_secteur)
        form.addRow("Téléphone*:", self.txt_telephone)
        form.addRow("Téléphone 2:", self.txt_telephone2)
        form.addRow("Email:", self.txt_email)
        form.addRow("Site web:", self.txt_site_web)
        
        tab_general.setLayout(form)
        self.tabs.addTab(tab_general, "Informations")
        
        # Onglet Adresse
        tab_adresse = QWidget()
        adresse_form = QFormLayout()
        
        self.txt_adresse = QTextEdit()
        self.txt_adresse.setMaximumHeight(80)
        self.txt_adresse.setPlaceholderText("Adresse complète")
        
        self.txt_ville = QLineEdit()
        self.txt_ville.setPlaceholderText("Ville")
        
        self.txt_code_postal = QLineEdit()
        self.txt_code_postal.setPlaceholderText("Code postal")
        
        self.txt_pays = QLineEdit()
        self.txt_pays.setText("Algérie")
        
        adresse_form.addRow("Adresse:", self.txt_adresse)
        adresse_form.addRow("Ville:", self.txt_ville)
        adresse_form.addRow("Code postal:", self.txt_code_postal)
        adresse_form.addRow("Pays:", self.txt_pays)
        
        tab_adresse.setLayout(adresse_form)
        self.tabs.addTab(tab_adresse, "Adresse")
        
        # Onglet Entreprise
        self.tab_entreprise = QWidget()
        entreprise_form = QFormLayout()
        
        self.txt_raison_sociale_entreprise = QLineEdit()
        self.txt_raison_sociale_entreprise.setPlaceholderText("Raison sociale complète")
        
        self.txt_registre_commerce = QLineEdit()
        self.txt_registre_commerce.setPlaceholderText("N° Registre de commerce")
        
        self.txt_nif = QLineEdit()
        self.txt_nif.setPlaceholderText("N° Identification Fiscale")
        
        self.txt_nis = QLineEdit()
        self.txt_nis.setPlaceholderText("N° Identification Statistique")
        
        self.spin_capital = QDoubleSpinBox()
        self.spin_capital.setRange(0, 1000000000)
        self.spin_capital.setSuffix(" DA")
        
        self.txt_forme_juridique = QLineEdit()
        self.txt_forme_juridique.setPlaceholderText("SARL, EURL, SA, etc.")
        
        entreprise_form.addRow("Raison sociale:", self.txt_raison_sociale_entreprise)
        entreprise_form.addRow("Registre commerce:", self.txt_registre_commerce)
        entreprise_form.addRow("NIF:", self.txt_nif)
        entreprise_form.addRow("NIS:", self.txt_nis)
        entreprise_form.addRow("Capital social:", self.spin_capital)
        entreprise_form.addRow("Forme juridique:", self.txt_forme_juridique)
        
        self.tab_entreprise.setLayout(entreprise_form)
        self.tabs.addTab(self.tab_entreprise, "Entreprise")
        
        # Onglet Commercial
        tab_commercial = QWidget()
        commercial_form = QFormLayout()
        
        self.spin_tva = QDoubleSpinBox()
        self.spin_tva.setRange(0, 100)
        self.spin_tva.setSuffix(" %")
        self.spin_tva.setValue(19.0)
        
        self.spin_solde = QDoubleSpinBox()
        self.spin_solde.setRange(-10000000, 10000000)
        self.spin_solde.setSuffix(" DA")
        
        self.spin_credit_max = QDoubleSpinBox()
        self.spin_credit_max.setRange(0, 10000000)
        self.spin_credit_max.setSuffix(" DA")
        self.spin_credit_max.setValue(0)
        
        self.cmb_conditions = QComboBox()
        self.cmb_conditions.addItems(["30 jours", "45 jours", "60 jours", "Comptant", "Avance"])
        
        self.cmb_mode_paiement = QComboBox()
        self.cmb_mode_paiement.addItems(["Virement", "Chèque", "Espèces", "Carte"])
        
        self.txt_banque = QLineEdit()
        self.txt_banque.setPlaceholderText("Nom de la banque")
        
        self.txt_num_compte = QLineEdit()
        self.txt_num_compte.setPlaceholderText("Numéro de compte")
        
        commercial_form.addRow("Taux TVA:", self.spin_tva)
        commercial_form.addRow("Solde initial:", self.spin_solde)
        commercial_form.addRow("Crédit max:", self.spin_credit_max)
        commercial_form.addRow("Conditions paiement:", self.cmb_conditions)
        commercial_form.addRow("Mode paiement:", self.cmb_mode_paiement)
        commercial_form.addRow("Banque:", self.txt_banque)
        commercial_form.addRow("N° Compte:", self.txt_num_compte)
        
        tab_commercial.setLayout(commercial_form)
        self.tabs.addTab(tab_commercial, "Commercial")
        
        # Onglet Service
        tab_service = QWidget()
        service_form = QFormLayout()
        
        self.cmb_frequence = QComboBox()
        self.cmb_frequence.addItems(["Quotidien", "Hebdomadaire", "Bi-hebdomadaire", "Mensuel", "Ponctuel"])
        
        self.txt_jours = QLineEdit()
        self.txt_jours.setPlaceholderText("Ex: Lundi, Mercredi, Vendredi")
        
        self.txt_horaires = QLineEdit()
        self.txt_horaires.setPlaceholderText("Ex: 08:00-12:00, 14:00-18:00")
        
        self.txt_source = QLineEdit()
        self.txt_source.setPlaceholderText("Comment avez-vous obtenu ce client?")
        
        self.date_premier_contact = QDateEdit()
        self.date_premier_contact.setCalendarPopup(True)
        self.date_premier_contact.setDate(QDate.currentDate())
        
        service_form.addRow("Fréquence nettoyage:", self.cmb_frequence)
        service_form.addRow("Jours prestation:", self.txt_jours)
        service_form.addRow("Horaires:", self.txt_horaires)
        service_form.addRow("Source:", self.txt_source)
        service_form.addRow("Date premier contact:", self.date_premier_contact)
        
        tab_service.setLayout(service_form)
        self.tabs.addTab(tab_service, "Service")
        
        # Onglet Statut
        tab_status = QWidget()
        status_form = QFormLayout()
        
        self.chk_actif = QCheckBox("Client actif")
        self.chk_actif.setChecked(True)
        
        self.spin_satisfaction = QSpinBox()
        self.spin_satisfaction.setRange(1, 5)
        self.spin_satisfaction.setValue(3)
        
        self.chk_recommande = QCheckBox("Client recommandé")
        
        self.txt_notes = QTextEdit()
        self.txt_notes.setMaximumHeight(100)
        self.txt_notes.setPlaceholderText("Notes internes...")
        
        status_form.addRow("Statut:", self.chk_actif)
        status_form.addRow("Niveau satisfaction (1-5):", self.spin_satisfaction)
        status_form.addRow("", self.chk_recommande)
        status_form.addRow("Notes:", self.txt_notes)
        
        tab_status.setLayout(status_form)
        self.tabs.addTab(tab_status, "Statut")
        
        layout.addWidget(self.tabs)
        
        # Boutons
        buttons = QHBoxLayout()
        btn_save = QPushButton("Enregistrer")
        btn_save.clicked.connect(self.save_client)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        
        buttons.addStretch()
        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)
        
        layout.addLayout(buttons)
        self.setLayout(layout)
    
    def on_type_change(self, type_text):
        """Active/désactive l'onglet entreprise selon le type"""
        self.tabs.setTabEnabled(2, type_text == "Entreprise")
    
    def generer_nouveau_code(self):
        with get_session() as session:
            raison_sociale = self.txt_raison_sociale.text().strip()
            if not raison_sociale:
                raison_sociale = "Nouveau Client"

            code = generer_code_client(session, raison_sociale)
            self.txt_code.setText(code)
    
    def load_data(self):
        """Charge les données du client existant"""
        if not self.client_id:
            return
        
        try:
            with get_session() as session:
                client = session.query(Client).filter(Client.id == self.client_id).first()
                if client:
                    # Informations générales
                    self.txt_code.setText(client.code_client or "")
                    self.txt_raison_sociale.setText(client.raison_sociale or "")
                    
                    if client.type_client:
                        index = self.cmb_type.findText(client.type_client)
                        if index >= 0:
                            self.cmb_type.setCurrentIndex(index)
                    
                    if client.secteur_activite:
                        index = self.cmb_secteur.findText(client.secteur_activite)
                        if index >= 0:
                            self.cmb_secteur.setCurrentIndex(index)
                    
                    self.txt_telephone.setText(client.telephone or "")
                    self.txt_telephone2.setText(client.telephone2 or "")
                    self.txt_email.setText(client.email or "")
                    self.txt_site_web.setText(client.site_web or "")
                    
                    # Adresse
                    self.txt_adresse.setText(client.adresse or "")
                    self.txt_ville.setText(client.ville or "")
                    self.txt_code_postal.setText(client.code_postal or "")
                    self.txt_pays.setText(client.pays or "Algérie")
                    
                    # Entreprise
                    self.txt_raison_sociale_entreprise.setText(client.raison_sociale or "")
                    self.txt_registre_commerce.setText(client.registre_commerce or "")
                    self.txt_nif.setText(client.nif or "")
                    self.txt_nis.setText(client.nis or "")
                    self.spin_capital.setValue(client.capital_social or 0)
                    self.txt_forme_juridique.setText(client.forme_juridique or "")
                    
                    # Commercial
                    self.spin_tva.setValue(client.taux_tva if client.taux_tva is not None else 19.0)
                    self.spin_solde.setValue(client.solde_courant if client.solde_courant is not None else 0)
                    self.spin_credit_max.setValue(client.credit_max if client.credit_max is not None else 0)
                    
                    if client.conditions_paiement:
                        index = self.cmb_conditions.findText(client.conditions_paiement)
                        if index >= 0:
                            self.cmb_conditions.setCurrentIndex(index)
                    
                    if client.mode_paiement_prefere:
                        index = self.cmb_mode_paiement.findText(client.mode_paiement_prefere)
                        if index >= 0:
                            self.cmb_mode_paiement.setCurrentIndex(index)
                    
                    self.txt_banque.setText(client.banque or "")
                    self.txt_num_compte.setText(client.numero_compte or "")
                    
                    # Service
                    if client.frequence_nettoyage:
                        index = self.cmb_frequence.findText(client.frequence_nettoyage)
                        if index >= 0:
                            self.cmb_frequence.setCurrentIndex(index)
                    
                    self.txt_jours.setText(client.jours_prestation or "")
                    self.txt_horaires.setText(client.horaires_prestation or "")
                    self.txt_source.setText(client.source or "")
                    
                    if client.date_premier_contact:
                        qdate = QDate(
                            client.date_premier_contact.year,
                            client.date_premier_contact.month,
                            client.date_premier_contact.day
                        )
                        self.date_premier_contact.setDate(qdate)
                    
                    # Statut
                    self.chk_actif.setChecked(client.est_actif if client.est_actif is not None else True)
                    self.spin_satisfaction.setValue(client.niveau_satisfaction or 3)
                    self.chk_recommande.setChecked(client.recommande or False)
                    self.txt_notes.setText(client.notes_internes or "")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur de chargement: {str(e)}")
    
    def validate_form(self):
        """Valide les données du formulaire"""
        errors = []
        
        # Validation des champs obligatoires
        if not self.txt_raison_sociale.text().strip():
            errors.append("La raison sociale est obligatoire")
        
        if not self.txt_telephone.text().strip():
            errors.append("Le téléphone est obligatoire")
        
        # Validation email
        email = self.txt_email.text().strip()
        if email and not self.validate_email(email):
            errors.append("Format d'email invalide")
        
        # Validation téléphone
        phone = self.txt_telephone.text().strip()
        if phone and not self.validate_phone(phone):
            errors.append("Format de téléphone invalide (9-10 chiffres)")
        
        phone2 = self.txt_telephone2.text().strip()
        if phone2 and not self.validate_phone(phone2):
            errors.append("Format de téléphone secondaire invalide")
        
        # Validation NIF/NIS (si remplis)
        nif = self.txt_nif.text().strip()
        if nif and not nif.replace(" ", "").isdigit():
            errors.append("Le NIF doit contenir uniquement des chiffres")
        
        nis = self.txt_nis.text().strip()
        if nis and not nis.replace(" ", "").isdigit():
            errors.append("Le NIS doit contenir uniquement des chiffres")
        
        if errors:
            QMessageBox.warning(self, "Erreurs de validation", "\n".join(errors))
            return False
        
        return True
    
    def validate_email(self, email):
        """Validation simple d'email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_phone(self, phone):
        """Validation simple de téléphone"""
        cleaned = re.sub(r'[^\d]', '', phone)
        return 9 <= len(cleaned) <= 10 and cleaned.isdigit()
    
    def save_client(self):
        """Enregistre le client"""
        if not self.validate_form():
            return
        
        try:
            with get_session() as session:
                if self.client_id:
                    # MODIFICATION
                    client = session.query(Client).filter(Client.id == self.client_id).first()
                    if not client:
                        QMessageBox.critical(self, "Erreur", "Client non trouvé")
                        return
                    message = "Client modifié avec succès!"
                else:
                    # CRÉATION
                    raison_sociale = self.txt_raison_sociale.text().strip()
                    
                    if not raison_sociale:
                        QMessageBox.warning(self, "Erreur", "La raison sociale est obligatoire")
                        return
                    
                    # Générer le code
                    code = generer_code_client(session, raison_sociale)
                    
                    client = Client(
                        code_client=code,
                        raison_sociale=raison_sociale
                    )
                    session.add(client)
                    message = "Nouveau client ajouté!"
                
                # Mettre à jour les données
                self.update_client_data(client)
                
                session.commit()
                self.client_saved.emit()
                self.accept()
                QMessageBox.information(self, "Succès", message)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement: {str(e)}")
    
    def update_client_data(self, client):
        """Met à jour les données du client"""
        # Informations générales
        client.code_client = self.txt_code.text().strip()
        client.raison_sociale = self.txt_raison_sociale.text().strip()
        client.type_client = self.cmb_type.currentText()
        client.secteur_activite = self.cmb_secteur.currentText()
        client.telephone = self.txt_telephone.text().strip()
        client.telephone2 = self.txt_telephone2.text().strip() or None
        client.email = self.txt_email.text().strip() or None
        client.site_web = self.txt_site_web.text().strip() or None
        
        # Adresse
        client.adresse = self.txt_adresse.toPlainText().strip() or None
        client.ville = self.txt_ville.text().strip() or None
        client.code_postal = self.txt_code_postal.text().strip() or None
        client.pays = self.txt_pays.text().strip() or "Algérie"
        
        # Entreprise
        if self.cmb_type.currentText() == "Entreprise":
            client.raison_sociale = self.txt_raison_sociale_entreprise.text().strip() or client.raison_sociale
            client.registre_commerce = self.txt_registre_commerce.text().strip() or None
            client.nif = self.txt_nif.text().strip() or None
            client.nis = self.txt_nis.text().strip() or None
            client.capital_social = self.spin_capital.value() or None
            client.forme_juridique = self.txt_forme_juridique.text().strip() or None
        
        # Commercial
        client.taux_tva = self.spin_tva.value()
        client.solde_courant = self.spin_solde.value()
        client.credit_max = self.spin_credit_max.value()
        client.conditions_paiement = self.cmb_conditions.currentText()
        client.mode_paiement_prefere = self.cmb_mode_paiement.currentText()
        client.banque = self.txt_banque.text().strip() or None
        client.numero_compte = self.txt_num_compte.text().strip() or None
        
        # Service
        client.frequence_nettoyage = self.cmb_frequence.currentText() or None
        client.jours_prestation = self.txt_jours.text().strip() or None
        client.horaires_prestation = self.txt_horaires.text().strip() or None
        client.source = self.txt_source.text().strip() or None
        client.date_premier_contact = self.date_premier_contact.date().toPyDate()
        
        # Statut
        client.est_actif = self.chk_actif.isChecked()
        client.niveau_satisfaction = self.spin_satisfaction.value()
        client.recommande = self.chk_recommande.isChecked()
        client.notes_internes = self.txt_notes.toPlainText().strip() or None


class ClientsView(QWidget):
    """Vue pour la gestion des clients"""
    
    def __init__(self):
        super().__init__()
        self.current_filter = None
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Titre
        title = QLabel("👥 GESTION DES CLIENTS")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Barre d'outils
        toolbar = QHBoxLayout()
        
        btn_add = QPushButton("➕ Nouveau client")
        btn_add.clicked.connect(self.add_client)
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)

        btn_service_fait = QPushButton("📄 Service Fait")
        btn_service_fait.clicked.connect(self.show_service_fait_dialog)
        btn_service_fait.setStyleSheet("QPushButton{background:#e67e22;color:white;padding:10px;border-radius:5px;} QPushButton:hover{background:#d35400;}")
        
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.load_data)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        btn_export = QPushButton("📊 Statistiques")
        btn_export.clicked.connect(self.show_statistics)
        btn_export.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_service_fait)
        toolbar.addStretch()
        toolbar.addWidget(btn_export)
        toolbar.addWidget(btn_refresh)
        
        layout.addLayout(toolbar)
        
        # Barre de recherche et filtres
        filter_toolbar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par Raison Sociale, code, téléphone, ville...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        
        filter_label = QLabel("Filtrer par:")
        filter_label.setStyleSheet("font-weight: bold;")
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Tous", 
            "Actifs", 
            "Inactifs", 
            "Particulier", 
            "Entreprise", 
            "En retard", 
            "Recommande"
        ])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        
        filter_toolbar.addWidget(QLabel("🔍"))
        filter_toolbar.addWidget(self.search_input, 1)
        filter_toolbar.addSpacing(20)
        filter_toolbar.addWidget(filter_label)
        filter_toolbar.addWidget(self.filter_combo)
        
        layout.addLayout(filter_toolbar)
        
        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "Code", "Raison Sociale", "Type", "Téléphone", "Email", 
            "Ville", "Solde", "Crédit", "Contact", "Statut"
        ])
        
        # Masquer la colonne ID
        self.table.setColumnHidden(0, True)
        
        # Configurer les largeurs des colonnes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Code
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Nom
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Téléphone
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Email
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Ville
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Solde
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Crédit
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Contact
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)  # Statut
        
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Activer le menu contextuel
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Style du tableau
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
                gridline-color: #e0e0e0;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        layout.addWidget(self.table)
        
        # Statistiques
        stats_layout = QHBoxLayout()
        
        self.label_stats = QLabel("0 client(s)")
        self.label_stats.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 8px;
                font-weight: bold;
                background-color: #ecf0f1;
                border-radius: 4px;
            }
        """)
        
        self.label_solde_total = QLabel("Solde total: 0 DA")
        self.label_solde_total.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                padding: 8px;
                font-weight: bold;
                background-color: #fadbd8;
                border-radius: 4px;
            }
        """)
        
        self.label_actifs = QLabel("Actifs: 0")
        self.label_actifs.setStyleSheet("""
            QLabel {
                color: #27ae60;
                padding: 8px;
                font-weight: bold;
                background-color: #d5f4e6;
                border-radius: 4px;
            }
        """)
        
        stats_layout.addWidget(self.label_stats)
        stats_layout.addWidget(self.label_solde_total)
        stats_layout.addWidget(self.label_actifs)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
    
    def load_data(self):
        """Charge les données des clients"""
        try:
            with get_session() as session:
                # Appliquer les filtres
                query = session.query(Client)
            
                filter_text = self.filter_combo.currentText()
                if filter_text == "Actifs":
                    query = query.filter(Client.est_actif == True)
                elif filter_text == "Inactifs":
                    query = query.filter(Client.est_actif == False)
                elif filter_text == "Particulier":
                    query = query.filter(Client.type_client == "Particulier")
                elif filter_text == "Entreprise":
                    query = query.filter(Client.type_client == "Entreprise")
                elif filter_text == "En retard":
                    query = query.filter(Client.solde_courant > 0)
                elif filter_text == "Recommande":
                    query = query.filter(Client.recommande == True)
            
                clients = query.order_by(Client.raison_sociale).all()
            
                self.table.setRowCount(len(clients))
            
                total_clients = len(clients)
                total_solde = 0
                total_actifs = 0
                total_en_retard = 0
            
                for row, client in enumerate(clients):
                    # ID (caché)
                    self.table.setItem(row, 0, QTableWidgetItem(str(client.id)))
                    
                    # Code
                    code = client.code_client or f"CLT{client.id:05d}"
                    self.table.setItem(row, 1, QTableWidgetItem(code))

                    # Raison Sociale
                    nom_item = QTableWidgetItem(client.raison_sociale)
                    if not client.est_actif:
                        nom_item.setForeground(Qt.GlobalColor.gray)
                    self.table.setItem(row, 2, nom_item)
                    
                    # Type
                    self.table.setItem(row, 3, QTableWidgetItem(client.type_client or ""))
                    
                    # Téléphone
                    telephone = client.telephone or ""
                    self.table.setItem(row, 4, QTableWidgetItem(telephone))
                    
                    # Email
                    email_item = QTableWidgetItem(client.email or "")
                    if client.email:
                        email_item.setToolTip(client.email)
                    self.table.setItem(row, 5, email_item)
                    
                    # Ville
                    self.table.setItem(row, 6, QTableWidgetItem(client.ville or ""))
                    
                    # Solde
                    solde = client.solde_courant if client.solde_courant is not None else 0.0
                    solde_text = f"{solde:,.2f} DA"
                    solde_item = QTableWidgetItem(solde_text)
                    
                    if solde > 0:
                        solde_item.setForeground(Qt.GlobalColor.darkRed)
                        solde_item.setToolTip(f"Dette client: {solde:,.2f} DA")
                        total_en_retard += 1
                    elif solde < 0:
                        solde_item.setForeground(Qt.GlobalColor.darkGreen)
                        solde_item.setToolTip(f"Crédit client: {abs(solde):,.2f} DA")
                    
                    self.table.setItem(row, 7, solde_item)
                    total_solde += solde
                    
                    # Crédit max
                    credit_max = client.credit_max if client.credit_max is not None else 0.0
                    credit_text = f"{credit_max:,.0f} DA" if credit_max > 0 else "Illimité"
                    self.table.setItem(row, 8, QTableWidgetItem(credit_text))
                    
                    # Contact
                    contact_nom = client.contact_nom or ""
                    self.table.setItem(row, 9, QTableWidgetItem(contact_nom))
                    
                    # Statut
                    statut = "Actif" if client.est_actif else "Inactif"
                    if client.solde_courant and client.solde_courant > client.credit_max > 0:
                        statut = "Dépassement"
                    
                    statut_item = QTableWidgetItem(statut)
                    if client.est_actif:
                        statut_item.setForeground(Qt.GlobalColor.darkGreen)
                        total_actifs += 1
                        
                        if statut == "Dépassement":
                            statut_item.setForeground(Qt.GlobalColor.darkRed)
                    else:
                        statut_item.setForeground(Qt.GlobalColor.darkRed)
                    
                    self.table.setItem(row, 10, statut_item)
            
                # Mettre à jour les statistiques
                self.update_statistics(total_clients, total_solde, total_actifs, total_en_retard)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur de chargement: {str(e)}")
    
    def update_statistics(self, total_clients, total_solde, total_actifs, total_en_retard):
        """Met à jour les labels de statistiques"""
        self.label_stats.setText(f"{total_clients} client(s)")
        self.label_solde_total.setText(f"Solde total: {total_solde:,.2f} DA")
        self.label_actifs.setText(f"Actifs: {total_actifs} | Retard: {total_en_retard}")
    
    def get_selected_client_id(self):
        """Retourne l'ID du client sélectionné"""
        selected = self.table.selectedItems()
        if not selected:
            return None
        
        row = selected[0].row()
        id_item = self.table.item(row, 0)
        return int(id_item.text()) if id_item else None
    
    def get_selected_client(self):
        """Retourne l'objet client sélectionné"""
        client_id = self.get_selected_client_id()
        if not client_id:
            return None
        
        with get_session() as session:
            return session.query(Client).filter(Client.id == client_id).first()
    
    def show_context_menu(self, position):
        """Affiche le menu contextuel"""
        # Vérifier si une ligne est sélectionnée
        if not self.table.selectedItems():
            # Menu pour le tableau vide
            menu = QMenu()
            
            add_action = QAction("➕ Ajouter un client", self)
            add_action.triggered.connect(self.add_client)
            menu.addAction(add_action)
            
            refresh_action = QAction("🔄 Actualiser", self)
            refresh_action.triggered.connect(self.load_data)
            menu.addAction(refresh_action)
            
            menu.exec(self.table.viewport().mapToGlobal(position))
            return
        
        # Créer le menu pour une ligne sélectionnée
        menu = QMenu()
        
        # Action: Modifier
        edit_action = QAction("✏️ Modifier", self)
        edit_action.triggered.connect(self.edit_client)
        menu.addAction(edit_action)
        
        # Action: Supprimer
        delete_action = QAction("🗑️ Supprimer", self)
        delete_action.triggered.connect(self.delete_client)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # Action: Voir les détails
        details_action = QAction("👁️ Fiche client", self)
        details_action.triggered.connect(self.show_client_details)
        menu.addAction(details_action)
        
        # Action: Changer statut
        client = self.get_selected_client()
        if client:
            status_text = "Désactiver" if client.est_actif else "Activer"
            status_action = QAction(f"🔄 {status_text}", self)
            status_action.triggered.connect(self.toggle_client_status)
            menu.addAction(status_action)
            
            # Action: Marquer comme recommandé
            recommande_text = "Recommander" if not client.recommande else "Ne plus recommander"
            recommande_action = QAction(f"⭐ {recommande_text}", self)
            recommande_action.triggered.connect(self.toggle_client_recommande)
            menu.addAction(recommande_action)

        # Action: Générer facture
        if client:
            invoice_menu = menu.addMenu("🧾 Générer facture")
            
            act_standard = QAction("📄 Facture standard", self)
            act_standard.triggered.connect(lambda: self.generate_standard_invoice(client.id))
            invoice_menu.addAction(act_standard)
            
            if "chu douera" in client.raison_sociale.lower():
                act_douera = QAction("🏥 Facture CHU Douera", self)
                act_douera.triggered.connect(lambda: self.generate_douera_invoice(client.id))
                invoice_menu.addAction(act_douera)
            
            if "beni messous" in client.raison_sociale.lower():
                act_beni = QAction("🏥 Facture CHU Beni Messous", self)
                act_beni.triggered.connect(lambda: self.generate_beni_messous_invoice(client.id))
                invoice_menu.addAction(act_beni)
        
        # Actions Contrats
        contrats_menu = menu.addMenu("📋 Contrats")
        act_voir_contrats = QAction("👁️ Voir les contrats", self)
        act_voir_contrats.triggered.connect(lambda: self.show_client_contrats(client.id))
        contrats_menu.addAction(act_voir_contrats)

        act_nouveau_contrat = QAction("➕ Nouveau contrat", self)
        act_nouveau_contrat.triggered.connect(lambda: self.add_client_contrat(client.id))
        contrats_menu.addAction(act_nouveau_contrat)
        
        menu.addSeparator()
        
        # Action: Copier le code
        copy_action = QAction("📋 Copier le code", self)
        copy_action.triggered.connect(self.copy_client_code)
        menu.addAction(copy_action)
        
        # Action: Envoyer un email
        if client and client.email:
            email_action = QAction("📧 Envoyer email", self)
            email_action.triggered.connect(lambda: self.send_email(client.email))
            menu.addAction(email_action)
        
        # Afficher le menu à la position du clic
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    def add_client(self):
        """Ouvre le dialogue pour ajouter un client"""
        dialog = ClientDialog(parent=self)
        dialog.client_saved.connect(self.load_data)
        dialog.exec()
    
    def generate_invoice_for_client(self, client_id):
        """Génère une facture appropriée selon le type de client"""
        with get_session() as session:
            client = session.query(Client).filter(Client.id == client_id).first()
            if not client:
                QMessageBox.warning(self, "Erreur", "Client non trouvé")
                return
            
            # Détecter le type de client basé sur la raison sociale
            client_name = client.raison_sociale.lower() if client.raison_sociale else ""
            
            # Facture spéciale CHU Douera
            if "chu douera" in client_name or "douera" in client_name:
                self.generate_douera_invoice(client_id)
            
            # Facture spéciale Beni Messous
            elif "beni messous" in client_name or "CHU BENI MESSOUS" in client_name:
                self.generate_beni_messous_invoice(client_id)
            
            # Facture standard
            else:
                self.generate_standard_invoice(client_id)

    def generate_standard_invoice(self, client_id):
        """Génère une facture standard"""
        from views.invoices.invoice_dialog import InvoiceDialog
        dialog = InvoiceDialog(client_id=client_id, parent=self)
        dialog.exec()

    def generate_douera_invoice(self, client_id):
        """Génère une facture spéciale CHU Douera (même que standard)"""
        from views.invoices.invoice_dialog import InvoiceDialog
        dialog = InvoiceDialog(client_id=client_id, parent=self)
        dialog.exec()

    def generate_beni_messous_invoice(self, client_id):
        """Génère une facture spéciale Beni Messous avec tableau spécifique"""
        from views.invoices.benimessous_invoice import BeniMessousInvoiceDialog
        dialog = BeniMessousInvoiceDialog(client_id=client_id, parent=self)
        dialog.exec()
    
    def generate_invoice_for_selected_client(self):
        """Génère une facture pour le client sélectionné"""
        client_id = self.get_selected_client_id()
        if not client_id:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un client")
            return
        self.generate_invoice_for_client(client_id)
    
    def edit_client(self):
        """Ouvre le dialogue pour modifier un client"""
        client_id = self.get_selected_client_id()
        if client_id is None:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un client à modifier")
            return
        
        dialog = ClientDialog(client_id=client_id, parent=self)
        dialog.client_saved.connect(self.load_data)
        dialog.exec()
    
    def delete_client(self):
        """Supprime le client sélectionné"""
        client_id = self.get_selected_client_id()
        if client_id is None:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un client à supprimer")
            return
        
        # ===== CORRECTION : Créer une session pour vérifier les factures =====
        try:
            with get_session() as session_check:
                client = session_check.query(Client).filter(Client.id == client_id).first()
                if not client:
                    QMessageBox.warning(self, "Erreur", "Client non trouvé")
                    return
                
                # Vérifier s'il y a des factures associées
                if client.factures:
                    QMessageBox.warning(
                        self, "Impossible de supprimer",
                        "Ce client a des factures associées.\n"
                        "Vous devez d'abord supprimer ou transférer les factures."
                    )
                    return
                
                # Confirmation
                reply = QMessageBox.question(
                    self, "Confirmation",
                    f"Voulez-vous vraiment supprimer le client '{client.raison_sociale}' ?\n"
                    f"Code: {client.code_client}\nType: {client.type_client}\n\n"
                    "Cette action est irréversible !",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    return
                
                # Maintenant, on supprime
                session_check.delete(client)
                session_check.commit()
                QMessageBox.information(self, "Succès", "Client supprimé avec succès")
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {str(e)}")
    
    def show_client_details(self):
        """Affiche les détails du client sélectionné"""
        client = self.get_selected_client()
        if not client:
            return
        
        # Calculer le pourcentage d'utilisation du crédit
        credit_usage = ""
        if client.credit_max and client.credit_max > 0:
            usage_percent = (client.solde_courant / client.credit_max) * 100 if client.solde_courant > 0 else 0
            credit_usage = f"({usage_percent:.1f}% utilisé)"
        
        details = f"""
        <h2>📋 FICHE CLIENT</h2>
        
        <h3>Informations générales</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa; width: 200px;">Code client:</td>
                <td style="padding: 8px; background-color: white; font-weight: bold;">{client.code_client or 'Non attribué'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Nom/Raison sociale:</td>
                <td style="padding: 8px; background-color: white;"><b>{client.raison_sociale}</b></td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Type:</td>
                <td style="padding: 8px; background-color: white;">{client.type_client or 'Non renseigné'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Secteur:</td>
                <td style="padding: 8px; background-color: white;">{client.secteur_activite or 'Non renseigné'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Téléphone:</td>
                <td style="padding: 8px; background-color: white;">{client.telephone or 'Non renseigné'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Téléphone 2:</td>
                <td style="padding: 8px; background-color: white;">{client.telephone2 or 'Non renseigné'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Email:</td>
                <td style="padding: 8px; background-color: white;">{client.email or 'Non renseigné'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Site web:</td>
                <td style="padding: 8px; background-color: white;">{client.site_web or 'Non renseigné'}</td>
            </tr>
        </table>
        
        <h3>Adresse</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Adresse:</td>
                <td style="padding: 8px; background-color: white;">{client.adresse or 'Non renseigné'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Ville:</td>
                <td style="padding: 8px; background-color: white;">{client.ville or 'Non renseigné'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Code postal:</td>
                <td style="padding: 8px; background-color: white;">{client.code_postal or 'Non renseigné'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Pays:</td>
                <td style="padding: 8px; background-color: white;">{client.pays or 'Algérie'}</td>
            </tr>
        </table>
        """
        
        if client.type_client == "Entreprise":
            details += f"""
            <h3>Informations entreprise</h3>
            <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
                <tr>
                    <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Raison sociale:</td>
                    <td style="padding: 8px; background-color: white;">{client.raison_sociale or 'Non renseigné'}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Registre commerce:</td>
                    <td style="padding: 8px; background-color: white;">{client.registre_commerce or 'Non renseigné'}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">NIF:</td>
                    <td style="padding: 8px; background-color: white;">{client.nif or 'Non renseigné'}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">NIS:</td>
                    <td style="padding: 8px; background-color: white;">{client.nis or 'Non renseigné'}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Capital social:</td>
                    <td style="padding: 8px; background-color: white;">{client.capital_social:,.0f} DA</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Forme juridique:</td>
                    <td style="padding: 8px; background-color: white;">{client.forme_juridique or 'Non renseigné'}</td>
                </tr>
            </table>
            """
        
        details += f"""
        <h3>Informations commerciales</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Taux TVA:</td>
                <td style="padding: 8px; background-color: white;">{client.taux_tva}%</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Solde courant:</td>
                <td style="padding: 8px; background-color: white; font-weight: bold; color: {'red' if client.solde_courant > 0 else 'green'}">
                    {client.solde_courant:,.2f} DA
                </td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Crédit maximum:</td>
                <td style="padding: 8px; background-color: white;">
                    {f"{client.credit_max:,.0f} DA" if client.credit_max > 0 else "Illimité"} {credit_usage}
                </td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Conditions paiement:</td>
                <td style="padding: 8px; background-color: white;">{client.conditions_paiement or '30 jours'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Mode paiement préféré:</td>
                <td style="padding: 8px; background-color: white;">{client.mode_paiement_prefere or 'Virement'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Banque:</td>
                <td style="padding: 8px; background-color: white;">{client.banque or 'Non renseigné'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">N° Compte:</td>
                <td style="padding: 8px; background-color: white;">{client.numero_compte or 'Non renseigné'}</td>
            </tr>
        </table>
        
        <h3>Service</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Fréquence nettoyage:</td>
                <td style="padding: 8px; background-color: white;">{client.frequence_nettoyage or 'Non renseigné'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Jours prestation:</td>
                <td style="padding: 8px; background-color: white;">{client.jours_prestation or 'Non renseigné'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Horaires:</td>
                <td style="padding: 8px; background-color: white;">{client.horaires_prestation or 'Non renseigné'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Source:</td>
                <td style="padding: 8px; background-color: white;">{client.source or 'Non renseigné'}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Date premier contact:</td>
                <td style="padding: 8px; background-color: white;">{client.date_premier_contact.strftime('%d/%m/%Y') if client.date_premier_contact else 'Non renseigné'}</td>
            </tr>
        </table>
        
        <h3>Statut</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Statut:</td>
                <td style="padding: 8px; background-color: white;">
                    <span style="color: {'green' if client.est_actif else 'red'}; font-weight: bold;">
                        {'Actif' if client.est_actif else 'Inactif'}
                    </span>
                </td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Niveau satisfaction:</td>
                <td style="padding: 8px; background-color: white;">
                    {'⭐' * client.niveau_satisfaction if client.niveau_satisfaction else 'Non évalué'}
                </td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Recommandé:</td>
                <td style="padding: 8px; background-color: white;">
                    {'✅ Oui' if client.recommande else '❌ Non'}
                </td>
            </tr>
        </table>
        """
        
        if client.notes_internes:
            details += f"""
            <h3>Notes</h3>
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                {client.notes_internes}
            </div>
            """
        
        QMessageBox.information(self, "Fiche Client", details)
    
    def toggle_client_status(self):
        """Active/désactive le client sélectionné"""
        client_id = self.get_selected_client_id()
        if not client_id:
            return
        
        try:
            with get_session() as session:
                client = session.query(Client).filter(Client.id == client_id).first()
                if client:
                    new_status = not client.est_actif
                    client.est_actif = new_status
                    session.commit()
                    
                    status_text = "activé" if new_status else "désactivé"
                    QMessageBox.information(self, "Succès", f"Client {status_text} avec succès")
                    self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur: {str(e)}")
    
    def toggle_client_recommande(self):
        """Marque/démarque comme recommandé"""
        client_id = self.get_selected_client_id()
        if not client_id:
            return
        
        try:
            with get_session() as session:
                client = session.query(Client).filter(Client.id == client_id).first()
                if client:
                    new_status = not client.recommande
                    client.recommande = new_status
                    session.commit()
                    
                    status_text = "recommandé" if new_status else "retiré des recommandés"
                    QMessageBox.information(self, "Succès", f"Client {status_text} avec succès")
                    self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur: {str(e)}")
    
    def show_client_contrats(self, client_id):
        """Affiche les contrats du client"""
        from views.invoices.contrat_widget import ContratsView
        from PyQt6.QtWidgets import QDialog, QVBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Contrats du client")
        dialog.setMinimumSize(1000, 600)
        
        layout = QVBoxLayout(dialog)
        contrats_view = ContratsView(client_id=client_id)
        layout.addWidget(contrats_view)
        
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)
        
        dialog.exec()

    def add_client_contrat(self, client_id):
        """Ajoute un contrat pour le client"""
        from views.invoices.contrat_widget import ContratDialog
        
        dialog = ContratDialog(client_id=client_id, parent=self)
        dialog.exec()
    
    def copy_client_code(self):
        """Copie le code du client dans le presse-papier"""
        client = self.get_selected_client()
        if client and client.code_client:
            clipboard = QApplication.clipboard()
            clipboard.setText(client.code_client)
            QMessageBox.information(self, "Copié", f"Code '{client.code_client}' copié dans le presse-papier")
    
    def send_email(self, email):
        """Ouvre le client email avec l'adresse du client"""
        try:
            import webbrowser
            webbrowser.open(f"mailto:{email}")
        except:
            QMessageBox.information(self, "Email", f"Adresse email: {email}")
    
    def show_statistics(self):
        """Affiche les statistiques des clients"""
        with get_session() as session:
            total_clients = session.query(Client).count()
            active_clients = session.query(Client).filter(Client.est_actif == True).count()
            enterprise_clients = session.query(Client).filter(Client.type_client == "Entreprise").count()
            particulier_clients = session.query(Client).filter(Client.type_client == "Particulier").count()
            
            # Clients en retard
            clients_en_retard = session.query(Client).filter(
                Client.solde_courant > 0,
                Client.est_actif == True
            ).count()
            
            # Total des soldes
            total_solde = session.query(Client.solde_courant).all()
            solde_total = sum(r[0] for r in total_solde if r[0])
            
            # Clients recommandés
            recommande_clients = session.query(Client).filter(Client.recommande == True).count()
            
            # Par secteur
            secteurs = {}
            for client in session.query(Client).filter(Client.secteur_activite.isnot(None)).all():
                if client.secteur_activite:
                    if client.secteur_activite not in secteurs:
                        secteurs[client.secteur_activite] = 0
                    secteurs[client.secteur_activite] += 1
            
            stats = f"""
            <h2>📊 STATISTIQUES DES CLIENTS</h2>
            
            <h3>Général</h3>
            <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Total clients:</td>
                <td style="padding: 8px; background-color: white; font-weight: bold;">{total_clients}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Clients actifs:</td>
                <td style="padding: 8px; background-color: white; color: green; font-weight: bold;">{active_clients}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Clients inactifs:</td>
                <td style="padding: 8px; background-color: white; color: red; font-weight: bold;">{total_clients - active_clients}</td>
            </tr>
            </table>
            
            <h3>Répartition par type</h3>
            <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Entreprises:</td>
                <td style="padding: 8px; background-color: white;">{enterprise_clients}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Particuliers:</td>
                <td style="padding: 8px; background-color: white;">{particulier_clients}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Recommandés:</td>
                <td style="padding: 8px; background-color: white; color: #f39c12;">{recommande_clients}</td>
            </tr>
            </table>
            
            <h3>Financier</h3>
            <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Clients en retard:</td>
                <td style="padding: 8px; background-color: white; color: red; font-weight: bold;">{clients_en_retard}</td>
            </tr>
            <tr>
                <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">Solde total:</td>
                <td style="padding: 8px; background-color: white; font-weight: bold; color: #e74c3c;">{solde_total:,.2f} DA</td>
            </tr>
            </table>
            """
            
            if secteurs:
                stats += """
                <h3>Répartition par secteur</h3>
                <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
                """
                for secteur, count in sorted(secteurs.items()):
                    percentage = (count / total_clients) * 100 if total_clients > 0 else 0
                    stats += f"""
                    <tr>
                        <td style="font-weight: bold; padding: 8px; background-color: #f8f9fa;">{secteur}:</td>
                        <td style="padding: 8px; background-color: white;">
                            {count} ({percentage:.1f}%)
                        </td>
                    </tr>
                    """
                stats += "</table>"
            
            QMessageBox.information(self, "Statistiques", stats)
    
    def filter_table(self, text):
        """Filtre les lignes du tableau"""
        text = text.lower()
        for row in range(self.table.rowCount()):
            visible = False
            for col in range(1, self.table.columnCount()):  # Commencer à 1 pour ignorer l'ID
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    visible = True
                    break
            self.table.setRowHidden(row, not visible)
    
    def apply_filter(self, filter_text):
        """Applique un filtre et recharge les données"""
        self.current_filter = filter_text if filter_text != "Tous" else None
        self.load_data()

    def show_service_fait_dialog(self):
        from views.invoices.service_fait_dialog import ServiceFaitDialog
        dialog = ServiceFaitDialog(parent=self)
        dialog.exec()