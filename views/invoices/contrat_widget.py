# views/contrat_widget.py
import os
from datetime import date, datetime, timedelta
import calendar

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QLineEdit, QLabel, QFormLayout, QComboBox,
    QTextEdit, QDoubleSpinBox, QHeaderView, QTabWidget,
    QMenu, QAbstractItemView, QDateEdit, QGroupBox,
    QFileDialog, QSpinBox, QCheckBox, QGridLayout, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QPoint
from PyQt6.QtGui import QAction, QFont, QColor

from database.db import SessionLocal, get_session
from models.client import Client
from models.contrat import Contrat, AvenantContrat, HistoriqueContrat
from models.enums import TypeContrat, FrequenceNettoyage, StatutContrat, PeriodiciteFacturation, TypeDocumentContrat


class ContratDialog(QDialog):
    """Dialogue pour créer/modifier un contrat avec support Marché/Convention et ODS"""
    
    contrat_saved = pyqtSignal()
    
    def __init__(self, client_id=None, contrat_id=None, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.contrat_id = contrat_id
        self.ods_path = None
        
        self.setWindowTitle("Modifier contrat" if contrat_id else "Nouveau contrat")
        self.setModal(True)
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)
        
        self.init_ui()
        self.load_clients()
        if contrat_id:
            self.load_data()
        else:
            self.numero_contrat.setText("")  # Optionnel: vider le champ
            if client_id:
                self.set_client(client_id)
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Titre
        title = QLabel("📄 GESTION DE CONTRAT")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 5px solid #9b59b6;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Tabs
        tabs = QTabWidget()
        
        # --- TAB 1: INFORMATIONS GÉNÉRALES (VERSION SIMPLE) ---
        tab_general = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        general_layout = QVBoxLayout(content)
        general_layout.setSpacing(15)
        
        # ----- SECTION 1: CLIENT -----
        client_group = QGroupBox("👤 CLIENT")
        client_layout = QFormLayout()
        
        self.client_combo = QComboBox()
        self.client_combo.setMinimumHeight(35)
        self.numero_contrat = QLineEdit()
        self.numero_contrat.setPlaceholderText("Ex: CTR-2024-001, MARCHE-2024-01, CONV-2024-001")
        self.numero_contrat.setMinimumHeight(35)
        
        client_layout.addRow("Client *:", self.client_combo)
        client_layout.addRow("N° Contrat:", self.numero_contrat)
        
        client_group.setLayout(client_layout)
        general_layout.addWidget(client_group)
        
        # ----- SECTION 2: TYPE DE DOCUMENT -----
        doc_group = QGroupBox("📄 TYPE DE DOCUMENT")
        doc_layout = QVBoxLayout()
        
        self.type_document = QComboBox()
        self.type_document.addItems([t.value for t in TypeDocumentContrat])
        self.type_document.currentTextChanged.connect(self.on_type_document_change)
        doc_layout.addWidget(self.type_document)
        
        # Informations Marché
        self.marche_widget = QWidget()
        marche_layout = QFormLayout(self.marche_widget)
        self.numero_marche = QLineEdit()
        self.date_marche = QDateEdit()
        self.date_marche.setCalendarPopup(True)
        self.date_marche.setDate(QDate.currentDate())
        self.autorite_contractante = QLineEdit()
        
        marche_layout.addRow("Numéro marché:", self.numero_marche)
        marche_layout.addRow("Date marché:", self.date_marche)
        marche_layout.addRow("Autorité contractante:", self.autorite_contractante)
        self.marche_widget.setVisible(False)
        doc_layout.addWidget(self.marche_widget)

        # ===== NOUVEAU : Type de facture =====
        facture_type_layout = QHBoxLayout()
        facture_type_layout.addWidget(QLabel("Type de facture:"))
        
        self.type_facture = QComboBox()
        self.type_facture.addItems([
            "Standard",
            "CHU Douera",
            "Beni Messous"
        ])
        self.type_facture.setToolTip("Choisissez le format de facture à utiliser pour ce contrat")
        self.type_facture.setMinimumHeight(35)
        facture_type_layout.addWidget(self.type_facture)
        facture_type_layout.addStretch()
        
        doc_layout.addLayout(facture_type_layout)
        # ======================================
        
        info_facture = QLabel("ℹ️ Ce choix déterminera le format de facture généré (standard, CHU Douera ou Beni Messous)")
        info_facture.setStyleSheet("""
            color: #7f8c8d;
            font-size: 10px;
            padding: 5px;
            background-color: #f8f9fa;
            border-radius: 3px;
        """)
        doc_layout.addWidget(info_facture)

        # Informations Convention
        self.convention_widget = QWidget()
        convention_layout = QFormLayout(self.convention_widget)
        self.numero_convention = QLineEdit()
        self.date_convention = QDateEdit()
        self.date_convention.setCalendarPopup(True)
        self.date_convention.setDate(QDate.currentDate())
        self.organisme_convention = QLineEdit()
        
        convention_layout.addRow("Numéro convention:", self.numero_convention)
        convention_layout.addRow("Date convention:", self.date_convention)
        convention_layout.addRow("Organisme:", self.organisme_convention)
        self.convention_widget.setVisible(False)
        doc_layout.addWidget(self.convention_widget)
        
        doc_group.setLayout(doc_layout)
        general_layout.addWidget(doc_group)


        
        # ----- SECTION 3: DATES -----
        dates_group = QGroupBox("📅 DATES")
        dates_layout = QFormLayout()
        
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate.currentDate())
        self.date_debut.setCalendarPopup(True)
        self.date_debut.dateChanged.connect(self.calculer_date_fin)
        
        self.duree_mois = QSpinBox()
        self.duree_mois.setRange(1, 120)
        self.duree_mois.setValue(12)
        self.duree_mois.setSuffix(" mois")
        self.duree_mois.valueChanged.connect(self.calculer_date_fin)
        
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setReadOnly(True)
        self.date_fin.setStyleSheet("background-color: #f5f5f5;")
        
        self.date_signature = QDateEdit()
        self.date_signature.setCalendarPopup(True)
        self.date_signature.setDate(QDate.currentDate())
        
        self.periode_essai = QSpinBox()
        self.periode_essai.setRange(0, 90)
        self.periode_essai.setSuffix(" jours")
        self.periode_essai.setValue(15)
        
        dates_layout.addRow("Date début *:", self.date_debut)
        dates_layout.addRow("Durée *:", self.duree_mois)
        dates_layout.addRow("Date fin:", self.date_fin)
        dates_layout.addRow("Date signature:", self.date_signature)
        dates_layout.addRow("Période d'essai:", self.periode_essai)
        
        dates_group.setLayout(dates_layout)
        general_layout.addWidget(dates_group)
        
        # ----- SECTION 4: TYPE ET STATUT -----
        type_group = QGroupBox("🏷️ TYPE & STATUT")
        type_layout = QFormLayout()
        
        self.type_contrat = QComboBox()
        self.type_contrat.addItems([t.value for t in TypeContrat])
        
        self.statut = QComboBox()
        self.statut.addItems([s.value for s in StatutContrat])
        self.statut.setCurrentText(StatutContrat.BROUILLON.value)
        
        self.frequence = QComboBox()
        self.frequence.addItems([f.value for f in FrequenceNettoyage])
        
        self.tacite_reconduction = QCheckBox("Reconduction tacite")
        self.tacite_reconduction.setChecked(True)
        
        type_layout.addRow("Type contrat *:", self.type_contrat)
        type_layout.addRow("Statut:", self.statut)
        type_layout.addRow("Fréquence nettoyage *:", self.frequence)
        type_layout.addRow("", self.tacite_reconduction)
        
        type_group.setLayout(type_layout)
        general_layout.addWidget(type_group)
        
        # ----- SECTION 5: ODS (Optionnel) -----
        ods_group = QGroupBox("📋 ORDRE DE SERVICE (Optionnel)")
        ods_layout = QFormLayout()
        
        self.numero_ods = QLineEdit()
        self.numero_ods.setPlaceholderText("Numéro ODS")
        
        self.date_ods = QDateEdit()
        self.date_ods.setCalendarPopup(True)
        self.date_ods.setDate(QDate.currentDate())
        
        self.objet_ods = QTextEdit()
        self.objet_ods.setMaximumHeight(60)
        self.objet_ods.setPlaceholderText("Objet de l'ODS...")
        
        self.signature_ods = QLineEdit()
        self.signature_ods.setPlaceholderText("Signataire")
        
        # Document ODS
        ods_doc_layout = QHBoxLayout()
        self.ods_path_label = QLabel("Aucun fichier")
        self.ods_path_label.setStyleSheet("color: #7f8c8d;")
        btn_ods = QPushButton("📎 Choisir")
        btn_ods.clicked.connect(self.choisir_fichier_ods)
        ods_doc_layout.addWidget(self.ods_path_label)
        ods_doc_layout.addWidget(btn_ods)
        
        ods_layout.addRow("Numéro ODS:", self.numero_ods)
        ods_layout.addRow("Date ODS:", self.date_ods)
        ods_layout.addRow("Objet:", self.objet_ods)
        ods_layout.addRow("Signataire:", self.signature_ods)
        ods_layout.addRow("Document:", ods_doc_layout)
        
        ods_group.setLayout(ods_layout)
        general_layout.addWidget(ods_group)
        
        general_layout.addStretch()
        scroll.setWidget(content)
        
        tab_layout = QVBoxLayout(tab_general)
        tab_layout.addWidget(scroll)
        tab_general.setLayout(tab_layout)
        tabs.addTab(tab_general, "📋 Général")
        
        
        # --- TAB 2: TARIFICATION ---
        tab_tarif = QWidget()
        tarif_layout = QVBoxLayout()
        
        tarif_group = QGroupBox("💰 TARIFICATION")
        tarif_form = QFormLayout()
        
        self.montant_ht = QDoubleSpinBox()
        self.montant_ht.setRange(0, 10000000)
        self.montant_ht.setSuffix(" DA")
        self.montant_ht.setValue(50000)
        self.montant_ht.valueChanged.connect(self.calculer_ttc)
        
        self.taux_tva = QDoubleSpinBox()
        self.taux_tva.setRange(0, 100)
        self.taux_tva.setSuffix(" %")
        self.taux_tva.setValue(19)
        self.taux_tva.valueChanged.connect(self.calculer_ttc)
        
        self.montant_ttc = QLabel("59 500,00 DA")
        self.montant_ttc.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
        
        self.frais_installation = QDoubleSpinBox()
        self.frais_installation.setRange(0, 1000000)
        self.frais_installation.setSuffix(" DA")
        self.frais_installation.setValue(0)
        
        self.caution = QDoubleSpinBox()
        self.caution.setRange(0, 1000000)
        self.caution.setSuffix(" DA")
        self.caution.setValue(0)
        
        tarif_form.addRow("Montant mensuel HT *:", self.montant_ht)
        tarif_form.addRow("Taux TVA (%):", self.taux_tva)
        tarif_form.addRow("Montant mensuel TTC:", self.montant_ttc)
        tarif_form.addRow("Frais d'installation:", self.frais_installation)
        tarif_form.addRow("Caution:", self.caution)
        
        tarif_group.setLayout(tarif_form)
        tarif_layout.addWidget(tarif_group)
        
        # Facturation
        fact_group = QGroupBox("📆 FACTURATION")
        fact_form = QFormLayout()
        
        self.periodicite_fact = QComboBox()
        self.periodicite_fact.addItems([p.value for p in PeriodiciteFacturation])
        
        self.jour_facturation = QSpinBox()
        self.jour_facturation.setRange(1, 31)
        self.jour_facturation.setValue(1)
        
        self.delai_paiement = QSpinBox()
        self.delai_paiement.setRange(0, 90)
        self.delai_paiement.setSuffix(" jours")
        self.delai_paiement.setValue(30)
        
        fact_form.addRow("Périodicité:", self.periodicite_fact)
        fact_form.addRow("Jour facturation:", self.jour_facturation)
        fact_form.addRow("Délai de paiement:", self.delai_paiement)
        
        fact_group.setLayout(fact_form)
        tarif_layout.addWidget(fact_group)
        
        tarif_layout.addStretch()
        tab_tarif.setLayout(tarif_layout)
        tabs.addTab(tab_tarif, "💰 Tarification")
        
        # --- TAB 3: SERVICE ---
        tab_service = QWidget()
        service_layout = QVBoxLayout()
        
        service_group = QGroupBox("🧹 DÉTAILS DU SERVICE")
        service_form = QFormLayout()
        
        self.superficie = QDoubleSpinBox()
        self.superficie.setRange(0, 100000)
        self.superficie.setSuffix(" m²")
        self.superficie.setValue(100)
        
        self.nb_pieces = QSpinBox()
        self.nb_pieces.setRange(0, 1000)
        self.nb_pieces.setValue(5)
        
        self.nb_employes = QSpinBox()
        self.nb_employes.setRange(0, 100)
        self.nb_employes.setValue(2)
        
        self.heures_mensuelles = QSpinBox()
        self.heures_mensuelles.setRange(0, 1000)
        self.heures_mensuelles.setSuffix(" h/mois")
        self.heures_mensuelles.setValue(40)
        
        service_form.addRow("Superficie (m²):", self.superficie)
        service_form.addRow("Nombre de pièces:", self.nb_pieces)
        service_form.addRow("Nombre d'agents:", self.nb_employes)
        service_form.addRow("Heures mensuelles:", self.heures_mensuelles)
        
        service_group.setLayout(service_form)
        service_layout.addWidget(service_group)
        
        # Horaires
        horaire_group = QGroupBox("⏰ HORAIRES")
        horaire_form = QFormLayout()
        
        self.jours_prestation = QLineEdit()
        self.jours_prestation.setPlaceholderText("Ex: Lundi, Mercredi, Vendredi")
        
        self.horaires = QLineEdit()
        self.horaires.setPlaceholderText("Ex: 08:00-12:00, 14:00-18:00")
        
        horaire_form.addRow("Jours de prestation:", self.jours_prestation)
        horaire_form.addRow("Horaires:", self.horaires)
        
        horaire_group.setLayout(horaire_form)
        service_layout.addWidget(horaire_group)
        
        # Adresse de prestation
        adresse_group = QGroupBox("📍 ADRESSE DE PRESTATION")
        adresse_form = QFormLayout()
        
        self.adresse_prestation = QTextEdit()
        self.adresse_prestation.setMaximumHeight(60)
        
        self.ville_prestation = QLineEdit()
        self.code_postal = QLineEdit()
        
        adresse_form.addRow("Adresse:", self.adresse_prestation)
        adresse_form.addRow("Ville:", self.ville_prestation)
        adresse_form.addRow("Code postal:", self.code_postal)
        
        adresse_group.setLayout(adresse_form)
        service_layout.addWidget(adresse_group)
        
        service_layout.addStretch()
        tab_service.setLayout(service_layout)
        tabs.addTab(tab_service, "🧹 Service")
        
        # --- TAB 4: RESPONSABLE & CLAUSES ---
        tab_resp = QWidget()
        resp_layout = QVBoxLayout()
        
        resp_group = QGroupBox("👤 RESPONSABLE CLIENT")
        resp_form = QFormLayout()
        
        self.resp_nom = QLineEdit()
        self.resp_nom.setPlaceholderText("Nom du responsable")
        
        self.resp_tel = QLineEdit()
        self.resp_tel.setPlaceholderText("Téléphone")
        
        self.resp_email = QLineEdit()
        self.resp_email.setPlaceholderText("Email")
        
        resp_form.addRow("Nom:", self.resp_nom)
        resp_form.addRow("Téléphone:", self.resp_tel)
        resp_form.addRow("Email:", self.resp_email)
        
        resp_group.setLayout(resp_form)
        resp_layout.addWidget(resp_group)
        
        clauses_group = QGroupBox("⚖️ CLAUSES PARTICULIÈRES")
        clauses_form = QFormLayout()
        
        self.clauses = QTextEdit()
        self.clauses.setMaximumHeight(100)
        self.clauses.setPlaceholderText("Clauses spécifiques...")
        
        self.conditions_resiliation = QTextEdit()
        self.conditions_resiliation.setMaximumHeight(80)
        self.conditions_resiliation.setPlaceholderText("Conditions de résiliation...")
        
        clauses_form.addRow("Clauses:", self.clauses)
        clauses_form.addRow("Résiliation:", self.conditions_resiliation)
        
        clauses_group.setLayout(clauses_form)
        resp_layout.addWidget(clauses_group)
        
        resp_layout.addStretch()
        tab_resp.setLayout(resp_layout)
        tabs.addTab(tab_resp, "👤 Responsable")
        
        layout.addWidget(tabs)
        
        # Boutons
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
        btn_save.clicked.connect(self.save_contrat)
        
        btn_cancel = QPushButton("❌ Annuler")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        buttons.addStretch()
        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)
        
        layout.addLayout(buttons)
        self.setLayout(layout)
    
    def on_type_document_change(self, type_text):
        """Affiche/cache les groupes selon le type de document"""
        self.marche_widget.setVisible(type_text == TypeDocumentContrat.MARCHE.value)
        self.convention_widget.setVisible(type_text == TypeDocumentContrat.CONVENTION.value)
    
    def choisir_fichier_ods(self):
        """Sélectionne un fichier ODS"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner le fichier ODS",
            "",
            "Documents (*.pdf *.doc *.docx *.odt);;Images (*.png *.jpg *.jpeg);;Tous (*.*)"
        )
        if file_path:
            self.ods_path = file_path
            self.ods_path_label.setText(os.path.basename(file_path))
            self.ods_path_label.setStyleSheet("color: #27ae60; font-weight: bold;")
    
    def calculer_date_fin(self):
        """Calcule la date de fin en fonction de la date de début et de la durée"""
        debut = self.date_debut.date()
        duree = self.duree_mois.value()
        self.date_fin.setDate(debut.addMonths(duree))
    
    def calculer_ttc(self):
        """Calcule et affiche le montant TTC"""
        ht = self.montant_ht.value()
        tva = self.taux_tva.value()
        ttc = ht * (1 + tva / 100)
        self.montant_ttc.setText(f"{ttc:,.2f} DA".replace(",", " "))
    
    def load_clients(self):
        """Charge la liste des clients actifs"""
        with get_session() as session:
            clients = session.query(Client).filter(Client.est_actif == True).order_by(Client.raison_sociale).all()
            self.client_combo.clear()
            self.client_combo.addItem("-- Sélectionnez un client --", None)
            for client in clients:
                label = f"{client.raison_sociale or client.nom_complet} ({client.code_client})"
                self.client_combo.addItem(label, client.id)
    
    def set_client(self, client_id):
        """Sélectionne un client spécifique"""
        idx = self.client_combo.findData(client_id)
        if idx >= 0:
            self.client_combo.setCurrentIndex(idx)
    
    def load_data(self):
        """Charge les données du contrat existant"""
        if not self.contrat_id:
            return
        
        with get_session() as session:
            contrat = session.query(Contrat).filter(Contrat.id == self.contrat_id).first()
            if not contrat:
                return
            
            # Client
            idx = self.client_combo.findData(contrat.client_id)
            if idx >= 0:
                self.client_combo.setCurrentIndex(idx)
            
            # Numéro
            self.numero_contrat.setText(contrat.numero_contrat)
            
            # ===== NOUVEAU : Type de document =====
            if contrat.type_document:
                idx = self.type_document.findText(contrat.type_document)
                if idx >= 0:
                    self.type_document.setCurrentIndex(idx)
                    self.on_type_document_change(contrat.type_document)
            
            # ===== NOUVEAU : Informations Marché =====
            self.numero_marche.setText(contrat.numero_marche or "")
            if contrat.date_marche:
                self.date_marche.setDate(QDate(contrat.date_marche.year, contrat.date_marche.month, contrat.date_marche.day))
            self.autorite_contractante.setText(contrat.autorite_contractante or "")
            
            # ===== NOUVEAU : Informations Convention =====
            self.numero_convention.setText(contrat.numero_convention or "")
            if contrat.date_convention:
                self.date_convention.setDate(QDate(contrat.date_convention.year, contrat.date_convention.month, contrat.date_convention.day))
            self.organisme_convention.setText(contrat.organisme_convention or "")

            # ===== NOUVEAU : Charger le type de facture =====
            if hasattr(contrat, 'type_facture'):
                type_facture = contrat.type_facture or "standard"
                if type_facture == "chu_douera":
                    self.type_facture.setCurrentText("CHU Douera")
                elif type_facture == "beni_messous":
                    self.type_facture.setCurrentText("Beni Messous")
                else:
                    self.type_facture.setCurrentText("Standard")
            
            # ===== NOUVEAU : Informations ODS =====
            self.numero_ods.setText(contrat.numero_ods or "")
            if contrat.date_ods:
                self.date_ods.setDate(QDate(contrat.date_ods.year, contrat.date_ods.month, contrat.date_ods.day))
            self.objet_ods.setText(contrat.objet_ods or "")
            self.signature_ods.setText(contrat.signature_ods or "")
            
            if contrat.ods_path:
                self.ods_path = contrat.ods_path
                self.ods_path_label.setText(os.path.basename(contrat.ods_path))
                self.ods_path_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            # Dates
            if contrat.date_debut:
                self.date_debut.setDate(QDate(contrat.date_debut.year, contrat.date_debut.month, contrat.date_debut.day))
            if contrat.date_fin:
                self.date_fin.setDate(QDate(contrat.date_fin.year, contrat.date_fin.month, contrat.date_fin.day))
            if contrat.date_signature:
                self.date_signature.setDate(QDate(contrat.date_signature.year, contrat.date_signature.month, contrat.date_signature.day))
            
            self.duree_mois.setValue(contrat.duree_mois or 12)
            self.periode_essai.setValue(contrat.periode_essai_jours or 0)
            
            # Type et statut
            if contrat.type_contrat:
                idx = self.type_contrat.findText(contrat.type_contrat.value)
                if idx >= 0:
                    self.type_contrat.setCurrentIndex(idx)
            
            if contrat.statut:
                idx = self.statut.findText(contrat.statut.value)
                if idx >= 0:
                    self.statut.setCurrentIndex(idx)
            
            if contrat.frequence_nettoyage:
                idx = self.frequence.findText(contrat.frequence_nettoyage.value)
                if idx >= 0:
                    self.frequence.setCurrentIndex(idx)
            
            self.tacite_reconduction.setChecked(contrat.tacite_reconduction or False)
            
            # Tarifs
            self.montant_ht.setValue(float(contrat.montant_mensuel_ht or 0))
            self.taux_tva.setValue(float(contrat.tva or 19))
            self.frais_installation.setValue(float(contrat.frais_installation or 0))
            self.caution.setValue(float(contrat.caution or 0))
            
            # Facturation
            if contrat.periodicite_facturation:
                idx = self.periodicite_fact.findText(contrat.periodicite_facturation.value)
                if idx >= 0:
                    self.periodicite_fact.setCurrentIndex(idx)
            
            self.jour_facturation.setValue(contrat.jour_facturation or 1)
            self.delai_paiement.setValue(contrat.delai_paiement_jours or 30)
            
            # Service
            self.superficie.setValue(float(contrat.superficie or 0))
            self.nb_pieces.setValue(contrat.nombre_pieces or 0)
            self.nb_employes.setValue(contrat.nombre_employes or 0)
            self.heures_mensuelles.setValue(contrat.heures_mensuelles or 0)
            
            # Horaires
            self.jours_prestation.setText(contrat.jours_prestation or "")
            self.horaires.setText(contrat.horaires_prestation or "")
            
            # Adresse
            self.adresse_prestation.setText(contrat.adresse_prestation or "")
            self.ville_prestation.setText(contrat.ville_prestation or "")
            self.code_postal.setText(contrat.code_postal_prestation or "")
            
            # Responsable
            self.resp_nom.setText(contrat.responsable_nom or "")
            self.resp_tel.setText(contrat.responsable_telephone or "")
            self.resp_email.setText(contrat.responsable_email or "")
            
            # Clauses
            self.clauses.setText(contrat.clauses_specifiques or "")
            self.conditions_resiliation.setText(contrat.conditions_resiliation or "")
    
    def save_contrat(self):
        """Enregistre le contrat"""
        # Validation
        if self.client_combo.currentIndex() <= 0:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un client")
            return
        
        if not self.numero_contrat.text().strip():
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un numéro de contrat")
            return
        
        # Optionnel : Vérifier l'unicité du numéro de contrat
        with get_session() as session_check:
            existing = session_check.query(Contrat).filter(
                Contrat.numero_contrat == self.numero_contrat.text().strip()
            ).first()
            
            if existing and (not self.contrat_id or existing.id != self.contrat_id):
                QMessageBox.warning(
                    self, 
                    "Erreur", 
                    f"Un contrat avec le numéro '{self.numero_contrat.text()}' existe déjà.\nVeuillez choisir un numéro unique."
                )
                return
        
        if self.montant_ht.value() <= 0:
            QMessageBox.warning(self, "Erreur", "Le montant mensuel doit être supérieur à 0")
            return
        
        try:
            with get_session() as session:
                if self.contrat_id:
                    contrat = session.query(Contrat).filter(Contrat.id == self.contrat_id).first()
                    message = "Contrat modifié avec succès!"
                else:
                    contrat = Contrat()
                    contrat.numero_contrat = self.numero_contrat.text()
                    session.add(contrat)
                    message = "Nouveau contrat créé!"
                
                # Client
                contrat.client_id = self.client_combo.currentData()

                # ===== UTILISER LA VALEUR SAISIE =====
                contrat.numero_contrat = self.numero_contrat.text().strip()
                
                # ===== CORRECTION ICI =====
                # Type de document - stocker la VALEUR (string) pas l'enum
                contrat.type_document = self.type_document.currentText()
                # ==========================
                
                # Informations Marché/Convention
                if contrat.type_document == TypeDocumentContrat.MARCHE.value:
                    contrat.numero_marche = self.numero_marche.text() or None
                    contrat.date_marche = self.date_marche.date().toPyDate() if self.numero_marche.text() else None
                    contrat.autorite_contractante = self.autorite_contractante.text() or None
                    
                elif contrat.type_document == TypeDocumentContrat.CONVENTION.value:
                    contrat.numero_convention = self.numero_convention.text() or None
                    contrat.date_convention = self.date_convention.date().toPyDate() if self.numero_convention.text() else None
                    contrat.organisme_convention = self.organisme_convention.text() or None
                
                # ===== NOUVEAU : Sauvegarder le type de facture =====
                type_facture_text = self.type_facture.currentText()
                if type_facture_text == "CHU Douera":
                    contrat.type_facture = "chu_douera"
                    contrat.modele_facture = "CHU DOUERA"
                elif type_facture_text == "Beni Messous":
                    contrat.type_facture = "beni_messous"
                    contrat.modele_facture = "BENI MESSOUS"
                else:
                    contrat.type_facture = "standard"
                    contrat.modele_facture = "STANDARD"

                # Informations ODS
                contrat.numero_ods = self.numero_ods.text() or None
                contrat.date_ods = self.date_ods.date().toPyDate() if self.numero_ods.text() else None
                contrat.objet_ods = self.objet_ods.toPlainText() or None
                contrat.signature_ods = self.signature_ods.text() or None
                
                if hasattr(self, 'ods_path') and self.ods_path:
                    contrat.ods_path = self.ods_path
                
                # Dates
                contrat.date_debut = self.date_debut.date().toPyDate()
                contrat.date_fin = self.date_fin.date().toPyDate()
                contrat.date_signature = self.date_signature.date().toPyDate()
                contrat.duree_mois = self.duree_mois.value()
                contrat.periode_essai_jours = self.periode_essai.value()
                
                # Type et statut - ici on utilise les valeurs des enums
                contrat.type_contrat = next(t for t in TypeContrat if t.value == self.type_contrat.currentText())
                contrat.statut = next(s for s in StatutContrat if s.value == self.statut.currentText())
                contrat.frequence_nettoyage = next(f for f in FrequenceNettoyage if f.value == self.frequence.currentText())
                contrat.tacite_reconduction = self.tacite_reconduction.isChecked()
                
                # Tarifs
                contrat.montant_mensuel_ht = self.montant_ht.value()
                contrat.tva = self.taux_tva.value()
                contrat.montant_mensuel_ttc = self.montant_ht.value() * (1 + self.taux_tva.value() / 100)
                contrat.frais_installation = self.frais_installation.value()
                contrat.caution = self.caution.value()
                
                # Facturation
                contrat.periodicite_facturation = next(
                    p for p in PeriodiciteFacturation if p.value == self.periodicite_fact.currentText()
                )
                contrat.jour_facturation = self.jour_facturation.value()
                contrat.delai_paiement_jours = self.delai_paiement.value()
                
                # Service
                contrat.superficie = self.superficie.value()
                contrat.nombre_pieces = self.nb_pieces.value()
                contrat.nombre_employes = self.nb_employes.value()
                contrat.heures_mensuelles = self.heures_mensuelles.value()
                
                # Horaires
                contrat.jours_prestation = self.jours_prestation.text() or None
                contrat.horaires_prestation = self.horaires.text() or None
                
                # Adresse
                contrat.adresse_prestation = self.adresse_prestation.toPlainText() or None
                contrat.ville_prestation = self.ville_prestation.text() or None
                contrat.code_postal_prestation = self.code_postal.text() or None
                
                # Responsable
                contrat.responsable_nom = self.resp_nom.text() or None
                contrat.responsable_telephone = self.resp_tel.text() or None
                contrat.responsable_email = self.resp_email.text() or None
                
                # Clauses
                contrat.clauses_specifiques = self.clauses.toPlainText() or None
                contrat.conditions_resiliation = self.conditions_resiliation.toPlainText() or None
                
                contrat.date_modification = date.today()
                
                session.commit()
                self.contrat_saved.emit()
                
                QMessageBox.information(self, "Succès", message)
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement: {str(e)}")
            import traceback
            traceback.print_exc()


class ContratsView(QWidget):
    """Vue principale pour la gestion des contrats"""
    
    def __init__(self, client_id=None):
        super().__init__()
        self.client_id = client_id
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Titre
        title = QLabel("📋 GESTION DES CONTRATS")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            padding: 15px;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-radius: 10px;
            border-left: 5px solid #9b59b6;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Barre d'outils
        toolbar = QHBoxLayout()
        
        btn_add = QPushButton("➕ Nouveau contrat")
        btn_edit = QPushButton("✏️ Modifier")
        btn_delete = QPushButton("🗑️ Supprimer")
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_generate_invoice = QPushButton("🧾 Générer facture")
        
        # Style des boutons
        btn_add.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #219653;
            }
        """)
        
        btn_edit.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        
        btn_delete.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        
        btn_generate_invoice.setStyleSheet("""
            QPushButton {
                background: #f39c12;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #d35400;
            }
        """)
        
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_edit)
        toolbar.addWidget(btn_delete)
        toolbar.addWidget(btn_generate_invoice)
        toolbar.addStretch()
        toolbar.addWidget(btn_refresh)
        
        layout.addLayout(toolbar)
        
        # Connexions
        btn_add.clicked.connect(self.add_contrat)
        btn_edit.clicked.connect(self.edit_selected)
        btn_delete.clicked.connect(self.delete_selected)
        btn_refresh.clicked.connect(self.load_data)
        btn_generate_invoice.clicked.connect(self.generate_invoice_selected)
        
        # Table des contrats
        self.table = QTableWidget()
        self.table.setColumnCount(11)  # Augmenté à 11 colonnes
        self.table.setHorizontalHeaderLabels([
            "ID", "N° Contrat", "Client", "Type Doc.", "Type", "Début", "Fin", 
            "Montant/mois", "Statut", "Jours restants", "Actions"
        ])
        self.table.setColumnHidden(0, True)  # Cacher l'ID
        
        # Style
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background: white;
                gridline-color: #dee2e6;
            }
            QHeaderView::section {
                background: #34495e;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background: #d4edda;
                color: #155724;
            }
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Menu contextuel
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
    
    def load_data(self):
        """Charge les contrats depuis la base"""
        with get_session() as session:
            query = session.query(Contrat).join(Client)
            
            if self.client_id:
                query = query.filter(Contrat.client_id == self.client_id)
            
            contrats = query.order_by(Contrat.date_debut.desc()).all()
            
            self.table.setRowCount(len(contrats))
            
            for row, contrat in enumerate(contrats):
                # ID
                self.table.setItem(row, 0, QTableWidgetItem(str(contrat.id)))
                    
                # N° Contrat
                self.table.setItem(row, 1, QTableWidgetItem(contrat.numero_contrat))
                    
                # Client
                client_name = contrat.client.raison_sociale or contrat.client.nom_complet if contrat.client else "Inconnu"
                self.table.setItem(row, 2, QTableWidgetItem(client_name))
                    
                # Type de document
                type_doc = contrat.type_document if contrat.type_document else "Contrat"
                if contrat.client:
                    nom_client = contrat.client.raison_sociale or contrat.client.nom_complet or ""
                    if "BENI MESSOUS" in nom_client.upper():
                        type_doc += " 🏥"
                    elif "CHU DOUERA" in nom_client.upper():
                        type_doc += " 🏥"
                type_doc_item = QTableWidgetItem(type_doc)
                    
                # Ajouter un tooltip avec les références
                tooltip = []
                if contrat.type_document == TypeDocumentContrat.MARCHE.value and contrat.numero_marche:
                    tooltip.append(f"Marché: {contrat.numero_marche}")
                elif contrat.type_document == TypeDocumentContrat.CONVENTION.value and contrat.numero_convention:
                    tooltip.append(f"Convention: {contrat.numero_convention}")
                    
                if contrat.numero_ods:
                    tooltip.append(f"ODS: {contrat.numero_ods}")
                    
                if tooltip:
                    type_doc_item.setToolTip("\n".join(tooltip))
                    
                self.table.setItem(row, 3, type_doc_item)
                    
                # Type
                self.table.setItem(row, 4, QTableWidgetItem(contrat.type_contrat.value if contrat.type_contrat else ""))
                    
                # Début
                debut = contrat.date_debut.strftime("%d/%m/%Y") if contrat.date_debut else ""
                self.table.setItem(row, 5, QTableWidgetItem(debut))
                    
                # Fin
                fin = contrat.date_fin.strftime("%d/%m/%Y") if contrat.date_fin else "Indéterminée"
                self.table.setItem(row, 6, QTableWidgetItem(fin))
                    
                # Montant mensuel
                montant_item = QTableWidgetItem(f"{float(contrat.montant_mensuel_ttc or 0):,.0f} DA".replace(",", " "))
                montant_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 7, montant_item)
                    
                # Statut
                statut_item = QTableWidgetItem(contrat.statut.value if contrat.statut else "")
                    
                # Colorer le statut
                if contrat.statut == StatutContrat.ACTIF:
                    statut_item.setForeground(QColor("#27ae60"))
                elif contrat.statut == StatutContrat.SUSPENDU:
                    statut_item.setForeground(QColor("#f39c12"))
                elif contrat.statut == StatutContrat.EXPIRE:
                    statut_item.setForeground(QColor("#e74c3c"))
                    
                self.table.setItem(row, 8, statut_item)
                    
                # Jours restants
                jours = contrat.jours_restants()
                if jours is not None:
                    if jours < 0:
                        jours_text = "Expiré"
                    elif jours < 30:
                        jours_text = f"{jours} jours (⚠️)"
                    else:
                        mois = jours // 30
                        jours_text = f"{mois} mois"
                else:
                    jours_text = "Illimité"
                    
                jours_item = QTableWidgetItem(jours_text)
                if jours is not None and jours < 30:
                    jours_item.setForeground(QColor("#e74c3c"))
                self.table.setItem(row, 9, jours_item)
                    
                # Actions (boutons)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                    
                btn_preview = QPushButton("👁️")
                btn_preview.setMaximumWidth(30)
                btn_preview.setToolTip("Voir les détails")
                    
                btn_invoice = QPushButton("🧾")
                btn_invoice.setMaximumWidth(30)
                btn_invoice.setToolTip("Générer facture")
                    
                btn_preview.clicked.connect(lambda checked, c=contrat.id: self.show_details(c))
                btn_invoice.clicked.connect(lambda checked, c=contrat.id: self.generate_invoice(c))
                    
                actions_layout.addWidget(btn_preview)
                actions_layout.addWidget(btn_invoice)
                actions_layout.addStretch()
                    
                self.table.setCellWidget(row, 10, actions_widget)
    
    def get_selected_contrat_id(self):
        """Retourne l'ID du contrat sélectionné"""
        selected = self.table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        id_item = self.table.item(row, 0)
        return int(id_item.text()) if id_item else None
    
    def add_contrat(self):
        """Ajouter un nouveau contrat"""
        dialog = ContratDialog(client_id=self.client_id, parent=self)
        dialog.contrat_saved.connect(self.load_data)
        dialog.exec()
    
    def edit_selected(self):
        """Modifier le contrat sélectionné"""
        contrat_id = self.get_selected_contrat_id()
        if not contrat_id:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un contrat")
            return
        dialog = ContratDialog(contrat_id=contrat_id, parent=self)
        dialog.contrat_saved.connect(self.load_data)
        dialog.exec()
    
    def delete_selected(self):
        """Supprimer le contrat sélectionné"""
        contrat_id = self.get_selected_contrat_id()
        if not contrat_id:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un contrat")
            return
        
        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment supprimer ce contrat ?\nCette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            with get_session() as session:
                contrat = session.query(Contrat).filter(Contrat.id == contrat_id).first()
                if contrat:
                    session.delete(contrat)
                    session.commit()
                    QMessageBox.information(self, "Succès", "Contrat supprimé")
                    self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur suppression: {e}")

    def generate_invoice(self, contrat_id):
        """Générer une facture pour le contrat selon son type"""
        with get_session() as session:
            contrat = session.query(Contrat).filter(Contrat.id == contrat_id).first()
            if not contrat:
                QMessageBox.warning(self, "Erreur", "Contrat non trouvé")
                return
            
            # Utiliser le type de facture enregistré dans le contrat
            type_facture = getattr(contrat, 'type_facture', 'standard')
            
            if type_facture == "chu_douera":
                # Utiliser la facture spéciale CHU Douera
                try:
                    from views.invoices.facture_speciale_chu_douera import FactureCHUDialog
                    dialog = FactureCHUDialog(contrat_id=contrat.id, parent=self)
                    dialog.exec()
                    return
                except ImportError as e:
                    QMessageBox.warning(
                        self, 
                        "Module non trouvé", 
                        f"Le module de facturation spéciale CHU Douera n'est pas disponible.\nErreur: {e}"
                    )
            
            elif type_facture == "beni_messous":
                # Utiliser la facture spéciale Beni Messous
                try:
                    from views.invoices.facture_speciale_beni_messous import FactureBeniMessousDialog
                    dialog = FactureBeniMessousDialog(contrat_id=contrat.id, parent=self)
                    dialog.exec()
                    return
                except ImportError as e:
                    QMessageBox.warning(
                        self, 
                        "Module non trouvé", 
                        f"Le module de facturation spéciale Beni Messous n'est pas disponible.\nErreur: {e}"
                    )
            
            # Par défaut, facture standard
            try:
                from views.invoices.invoice_dialog import InvoiceDialog
                invoice = contrat.generer_facture(session)
                session.add(invoice)
                session.commit()
                
                QMessageBox.information(
                    self, "Succès",
                    f"✅ Facture standard générée avec succès !\n"
                    f"N° Facture: {invoice.invoice_number}\n"
                    f"Montant: {float(contrat.montant_mensuel_ttc):,.0f} DA".replace(",", " ")
                )
                
                dialog = InvoiceDialog(invoice_id=invoice.id, parent=self)
                dialog.exec()
                
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Erreur", f"Erreur génération facture: {e}")
                import traceback
                traceback.print_exc()

    def generate_invoice_selected(self):
        """Générer une facture pour le contrat sélectionné"""
        contrat_id = self.get_selected_contrat_id()
        if not contrat_id:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un contrat")
            return
        self.generate_invoice(contrat_id)
    
    def show_details(self, contrat_id):
        """Afficher les détails du contrat"""
        with get_session() as session:
            contrat = session.query(Contrat).filter(Contrat.id == contrat_id).first()
            if not contrat:
                return
            
            # Construire les informations spécifiques
            type_doc_info = ""
            if contrat.type_document == TypeDocumentContrat.MARCHE.value and contrat.numero_marche:
                type_doc_info = f"""
                <tr><td style="font-weight:bold;">Numéro marché:</td><td>{contrat.numero_marche}</td></tr>
                <tr><td style="font-weight:bold;">Date marché:</td><td>{contrat.date_marche.strftime('%d/%m/%Y') if contrat.date_marche else ''}</td></tr>
                <tr><td style="font-weight:bold;">Autorité contractante:</td><td>{contrat.autorite_contractante or ''}</td></tr>
                """
            elif contrat.type_document == TypeDocumentContrat.CONVENTION.value and contrat.numero_convention:
                type_doc_info = f"""
                <tr><td style="font-weight:bold;">Numéro convention:</td><td>{contrat.numero_convention}</td></tr>
                <tr><td style="font-weight:bold;">Date convention:</td><td>{contrat.date_convention.strftime('%d/%m/%Y') if contrat.date_convention else ''}</td></tr>
                <tr><td style="font-weight:bold;">Organisme:</td><td>{contrat.organisme_convention or ''}</td></tr>
                """
            
            ods_info = ""
            if contrat.numero_ods:
                ods_info = f"""
                <tr><td style="font-weight:bold;">Numéro ODS:</td><td>{contrat.numero_ods}</td></tr>
                <tr><td style="font-weight:bold;">Date ODS:</td><td>{contrat.date_ods.strftime('%d/%m/%Y') if contrat.date_ods else ''}</td></tr>
                <tr><td style="font-weight:bold;">Objet ODS:</td><td>{contrat.objet_ods or ''}</td></tr>
                <tr><td style="font-weight:bold;">Signataire ODS:</td><td>{contrat.signature_ods or ''}</td></tr>
                """
            
            details = f"""
            <h2>📋 DÉTAILS DU CONTRAT</h2>
            
            <h3>Informations générales</h3>
            <table style="width:100%; border-collapse: collapse;">
            <tr><td style="font-weight:bold; width:200px;">N° Contrat:</td><td>{contrat.numero_contrat}</td></tr>
            <tr><td style="font-weight:bold;">Client:</td><td>{contrat.client.raison_sociale if contrat.client else 'Inconnu'}</td></tr>
            <tr><td style="font-weight:bold;">Type document:</td><td>{contrat.type_document if contrat.type_document else 'Contrat'}</td></tr>
            {type_doc_info}
            {ods_info}
            <tr><td style="font-weight:bold;">Type:</td><td>{contrat.type_contrat.value if contrat.type_contrat else ''}</td></tr>
            <tr><td style="font-weight:bold;">Statut:</td><td>{contrat.statut.value if contrat.statut else ''}</td></tr>
            <tr><td style="font-weight:bold;">Fréquence:</td><td>{contrat.frequence_nettoyage.value if contrat.frequence_nettoyage else ''}</td></tr>
            </table>
            
            <h3>Dates</h3>
            <table>
            <tr><td style="font-weight:bold;">Début:</td><td>{contrat.date_debut.strftime('%d/%m/%Y') if contrat.date_debut else ''}</td></tr>
            <tr><td style="font-weight:bold;">Fin:</td><td>{contrat.date_fin.strftime('%d/%m/%Y') if contrat.date_fin else 'Indéterminée'}</td></tr>
            <tr><td style="font-weight:bold;">Signature:</td><td>{contrat.date_signature.strftime('%d/%m/%Y') if contrat.date_signature else ''}</td></tr>
            <tr><td style="font-weight:bold;">Jours restants:</td><td>{contrat.jours_restants() or 'N/A'}</td></tr>
            </table>
            
            <h3>Tarification</h3>
            <table>
            <tr><td style="font-weight:bold;">Montant mensuel HT:</td><td>{float(contrat.montant_mensuel_ht or 0):,.0f} DA</td></tr>
            <tr><td style="font-weight:bold;">TVA:</td><td>{float(contrat.tva or 0)}%</td></tr>
            <tr><td style="font-weight:bold;">Montant mensuel TTC:</td><td><b>{float(contrat.montant_mensuel_ttc or 0):,.0f} DA</b></td></tr>
            </table>
            """
            
            QMessageBox.information(self, "Détails du contrat", details)
    
    def show_context_menu(self, pos: QPoint):
        """Menu contextuel avec choix du type de facture"""
        global_pos = self.table.viewport().mapToGlobal(pos)
        idx = self.table.indexAt(pos)
        
        menu = QMenu()
        
        act_add = QAction("➕ Nouveau contrat", self)
        act_add.triggered.connect(self.add_contrat)
        menu.addAction(act_add)
        
        if idx.isValid():
            self.table.selectRow(idx.row())
            
            act_edit = QAction("✏️ Modifier", self)
            act_edit.triggered.connect(self.edit_selected)
            menu.addAction(act_edit)
            
            act_delete = QAction("🗑️ Supprimer", self)
            act_delete.triggered.connect(self.delete_selected)
            menu.addAction(act_delete)
            
            menu.addSeparator()
            
            # Récupérer le contrat pour connaître le client
            contrat_id = self.get_selected_contrat_id()
            if contrat_id:
                with get_session() as session:
                    contrat = session.query(Contrat).filter(Contrat.id == contrat_id).first()
                    if contrat and contrat.client:
                        nom_client = contrat.client.raison_sociale or contrat.client.nom_complet or ""
                        
                        # Sous-menu pour la génération de facture
                        invoice_menu = menu.addMenu("🧾 Générer facture")
                        
                        # Option standard (toujours disponible)
                        act_standard = QAction("Facture standard", self)
                        act_standard.triggered.connect(lambda: self.generate_invoice_standard(contrat_id))
                        invoice_menu.addAction(act_standard)
                        
                        # Option Beni Messous si client correspond
                        if "BENI MESSOUS" in nom_client.upper():
                            act_beni = QAction("🏥 Facture Beni Messous", self)
                            act_beni.triggered.connect(lambda: self.generate_invoice_beni_messous(contrat_id))
                            invoice_menu.addAction(act_beni)
                            
                        # Option CHU Douera si client correspond
                        if "CHU DOUERA" in nom_client.upper():
                            act_chu = QAction("🏥 Facture CHU Douera", self)
                            act_chu.triggered.connect(lambda: self.generate_invoice_chu_douera(contrat_id))
                            invoice_menu.addAction(act_chu)
                        
                        act_details = QAction("👁️ Voir détails", self)
                        act_details.triggered.connect(lambda: self.show_details(self.get_selected_contrat_id()))
                        menu.addAction(act_details)
        
            menu.exec(global_pos)

    def generate_invoice_standard(self, contrat_id):
        """Génère une facture standard"""
        with get_session() as session:
            contrat = session.query(Contrat).filter(Contrat.id == contrat_id).first()
            if not contrat:
                QMessageBox.warning(self, "Erreur", "Contrat non trouvé")
                return
            
            try:
                invoice = contrat.generer_facture(session)
                session.add(invoice)
                session.commit()
                
                QMessageBox.information(
                    self, "Succès",
                    f"✅ Facture standard générée avec succès !\n"
                    f"N° Facture: {invoice.invoice_number}\n"
                    f"Montant: {float(contrat.montant_mensuel_ttc):,.0f} DA".replace(",", " ")
                )
                
                from views.invoices.invoice_dialog import InvoiceDialog
                dialog = InvoiceDialog(invoice_id=invoice.id, parent=self)
                dialog.exec()
                
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Erreur", f"Erreur génération facture: {e}")

    def generate_invoice_beni_messous(self, contrat_id):
        """Génère une facture Beni Messous"""
        try:
            from views.invoices.facture_speciale_beni_messous import FactureBeniMessousDialog
            dialog = FactureBeniMessousDialog(contrat_id=contrat_id, parent=self)
            dialog.exec()
        except ImportError as e:
            QMessageBox.warning(
                self, 
                "Module non trouvé", 
                f"Le module de facturation spéciale Beni Messous n'est pas disponible.\nErreur: {e}"
            )

    def generate_invoice_chu_douera(self, contrat_id):
        """Génère une facture CHU Douera"""
        try:
            from views.invoices.facture_speciale_chu_douera import FactureCHUDialog
            dialog = FactureCHUDialog(contrat_id=contrat_id, parent=self)
            dialog.exec()
        except ImportError as e:
            QMessageBox.warning(
                self, 
                "Module non trouvé", 
                f"Le module de facturation spéciale CHU Douera n'est pas disponible.\nErreur: {e}"
            )