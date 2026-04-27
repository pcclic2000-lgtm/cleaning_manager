# views/paye_globale_dialog.py
"""
Dialogue pour la saisie de la paie globale avec répartition par site
"""

import calendar
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QLineEdit, QLabel, QFormLayout, QComboBox,
    QTextEdit, QDoubleSpinBox, QHeaderView, QSpinBox,
    QGroupBox, QDateEdit, QTabWidget, QCheckBox,
    QSplitter, QFrame, QScrollArea, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor

from database.db import SessionLocal, get_session
from models.paye_globale import PayeGlobale, RepartitionPaie
from models.client import Client


class RepartitionDialog(QDialog):
    """Dialogue pour ajouter/modifier une répartition par site"""
    
    def __init__(self, paye_id=None, repartition_id=None, parent=None):
        super().__init__(parent)
        self.paye_id = paye_id
        self.repartition_id = repartition_id
        self.session = SessionLocal()
        
        self.setWindowTitle("Ajouter une répartition" if not repartition_id else "Modifier la répartition")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.init_ui()
        if repartition_id:
            self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        form = QFormLayout()
        form.setSpacing(10)
        
        # Client/Site
        self.client_combo = QComboBox()
        self.client_combo.addItem("-- Sélectionnez un client --", None)
        self.load_clients()
        self.client_combo.currentIndexChanged.connect(self.on_client_changed)
        form.addRow("Client:", self.client_combo)
        
        self.nom_site = QLineEdit()
        self.nom_site.setPlaceholderText("Nom du site (si client non sélectionné)")
        self.nom_site.setEnabled(False)
        form.addRow("Nom du site:", self.nom_site)
        
        # Nombre d'agents
        self.nb_agents = QSpinBox()
        self.nb_agents.setRange(0, 1000)
        self.nb_agents.setValue(0)
        self.nb_agents.valueChanged.connect(self.calculer_net)
        form.addRow("Nombre d'agents:", self.nb_agents)
        
        # Montant brut
        self.montant_brut = QDoubleSpinBox()
        self.montant_brut.setRange(0, 10000000)
        self.montant_brut.setSuffix(" DA")
        self.montant_brut.setDecimals(2)
        self.montant_brut.valueChanged.connect(self.calculer_net)
        form.addRow("Montant brut:", self.montant_brut)
        
        # Taux CNSS (modifiable)
        self.taux_cnss = QDoubleSpinBox()
        self.taux_cnss.setRange(0, 100)
        self.taux_cnss.setSuffix(" %")
        self.taux_cnss.setValue(15.0)  # Taux CNSS par défaut
        self.taux_cnss.valueChanged.connect(self.calculer_net)
        form.addRow("Taux CNSS:", self.taux_cnss)
        
        # Montant CNSS (calculé)
        self.montant_cnss = QLabel("0.00 DA")
        self.montant_cnss.setStyleSheet("font-weight: bold; color: #e67e22;")
        form.addRow("Montant CNSS:", self.montant_cnss)
        
        # Montant net (calculé)
        self.montant_net = QLabel("0.00 DA")
        self.montant_net.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
        form.addRow("Montant net:", self.montant_net)
        
        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Notes sur cette répartition...")
        form.addRow("Notes:", self.notes)
        
        layout.addLayout(form)
        
        # Boutons
        buttons = QHBoxLayout()
        btn_save = QPushButton("💾 Enregistrer")
        btn_save.setStyleSheet("""
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
        btn_save.clicked.connect(self.save)
        
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
        
        self.calculer_net()
    
    def load_clients(self):
        """Charge la liste des clients"""
        try:
            clients = self.session.query(Client).filter(Client.est_actif == True).order_by(Client.raison_sociale).all()
            for client in clients:
                label = f"{client.raison_sociale} ({client.code_client})"
                self.client_combo.addItem(label, client.id)
        except Exception as e:
            print(f"Erreur chargement clients: {e}")
    
    def on_client_changed(self, index):
        """Quand un client est sélectionné, désactive le champ nom_site"""
        if index > 0:  # Client sélectionné
            self.nom_site.setEnabled(False)
            self.nom_site.clear()
        else:  # Aucun client
            self.nom_site.setEnabled(True)
    
    def calculer_net(self):
        """Calcule les montants CNSS et net"""
        brut = self.montant_brut.value()
        taux = self.taux_cnss.value() / 100
        cnss = brut * taux
        net = brut - cnss
        
        self.montant_cnss.setText(f"{cnss:,.2f} DA".replace(",", " "))
        self.montant_net.setText(f"{net:,.2f} DA".replace(",", " "))
    
    def load_data(self):
        """Charge les données d'une répartition existante"""
        try:
            repart = self.session.query(RepartitionPaie).filter(RepartitionPaie.id == self.repartition_id).first()
            if repart:
                if repart.client_id:
                    index = self.client_combo.findData(repart.client_id)
                    if index >= 0:
                        self.client_combo.setCurrentIndex(index)
                else:
                    self.nom_site.setText(repart.nom_site or "")
                
                self.nb_agents.setValue(repart.nombre_agents or 0)
                self.montant_brut.setValue(repart.montant_brut or 0)
                self.notes.setText(repart.notes or "")
                self.calculer_net()
        except Exception as e:
            print(f"Erreur chargement répartition: {e}")
    
    def save(self):
        """Sauvegarde la répartition"""
        # Validation
        if self.client_combo.currentIndex() <= 0 and not self.nom_site.text().strip():
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un client ou saisir un nom de site")
            return
        
        if self.montant_brut.value() <= 0:
            QMessageBox.warning(self, "Erreur", "Le montant brut doit être supérieur à 0")
            return
        
        # Récupérer les données
        client_id = self.client_combo.currentData() if self.client_combo.currentIndex() > 0 else None
        nom_site = self.nom_site.text().strip() if not client_id else None
        
        brut = self.montant_brut.value()
        taux = self.taux_cnss.value() / 100
        cnss = brut * taux
        net = brut - cnss
        
        if self.repartition_id:
            repart = self.session.query(RepartitionPaie).filter(RepartitionPaie.id == self.repartition_id).first()
            if not repart:
                QMessageBox.critical(self, "Erreur", "Répartition non trouvée")
                return
        else:
            repart = RepartitionPaie(paye_id=self.paye_id)
            self.session.add(repart)
        
        repart.client_id = client_id
        repart.nom_site = nom_site
        repart.nombre_agents = self.nb_agents.value()
        repart.montant_brut = brut
        repart.montant_cnss = cnss
        repart.montant_net = net
        repart.notes = self.notes.toPlainText().strip() or None
        
        try:
            self.session.commit()
            self.accept()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde: {str(e)}")
    
    def closeEvent(self, event):
        """Ferme la session"""
        self.session.close()
        event.accept()


class PayeGlobaleDialog(QDialog):
    """Dialogue pour la saisie de la paie globale"""
    
    paye_saved = pyqtSignal()
    
    def __init__(self, paye_id=None, parent=None):
        super().__init__(parent)
        self.paye_id = paye_id
        self.session = SessionLocal()
        self._temp_repartitions = []
        
        self.setWindowTitle("Nouvelle paie globale" if not paye_id else "Modifier la paie")
        self.setModal(True)
        self.setMinimumSize(900, 700)
        
        # Colors
        self.CLR_BG = "#F0F4F8"
        self.CLR_SURFACE = "#FFFFFF"
        self.CLR_PRIMARY = "#1A6B4A"
        self.CLR_GREEN = "#27AE60"
        self.CLR_ORANGE = "#F39C12"
        self.CLR_BLUE = "#2980B9"
        self.CLR_DANGER = "#E74C3C"
        self.CLR_TEXT = "#1C2B36"
        self.CLR_SUB = "#6B7C8D"
        self.CLR_BORDER = "#D8E3EC"
        
        self.init_ui()
        if paye_id:
            self.load_data()
        else:
            self.set_default_period()
    
    def _btn_style(self, color: str, hover: str) -> str:
        return f"""
            QPushButton {{
                background: {color}; color: white; border: none;
                padding: 0 16px; border-radius: 7px;
                font-weight: 600; font-size: 13px;
            }}
            QPushButton:hover {{ background: {hover}; }}
        """
    
    def init_ui(self):
        self.setStyleSheet(f"background: {self.CLR_BG};")
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # ── En-tête ──────────────────────────────────────────────────────────
        header_frame = QFrame()
        header_frame.setFixedHeight(64)
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {self.CLR_PRIMARY}, stop:1 {self.CLR_GREEN});
                border-radius: 10px;
            }}
        """)
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(20, 0, 20, 0)
        icon_lbl = QLabel("💰")
        icon_lbl.setStyleSheet("font-size: 28px;")
        title = QLabel("PAIE GLOBALE MENSUELLE")
        title.setStyleSheet("font-size: 17px; font-weight: 700; color: white; font-family: 'Segoe UI';")
        h_layout.addWidget(icon_lbl)
        h_layout.addWidget(title)
        h_layout.addStretch()
        layout.addWidget(header_frame)
        
        # ── Période ──────────────────────────────────────────────────────────
        periode_frame = QFrame()
        periode_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.CLR_SURFACE};
                border-radius: 10px;
                border: 1px solid {self.CLR_BORDER};
            }}
        """)
        periode_frame.setFixedHeight(56)
        p_layout = QHBoxLayout(periode_frame)
        p_layout.setContentsMargins(16, 0, 16, 0)
        p_layout.setSpacing(14)
        
        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet(f"color: {self.CLR_SUB}; font-size: 12px; font-weight: 600;")
            return l
        
        field_style = f"""
            border: 1px solid {self.CLR_BORDER};
            border-radius: 6px; padding: 4px 8px;
            background: {self.CLR_BG}; color: {self.CLR_TEXT}; font-size: 13px;
        """
        
        p_layout.addWidget(lbl("📅 MOIS"))
        self.mois_combo = QComboBox()
        self.mois_combo.addItems(["Janvier","Février","Mars","Avril","Mai","Juin",
                               "Juillet","Août","Septembre","Octobre","Novembre","Décembre"])
        self.mois_combo.setFixedWidth(120)
        self.mois_combo.setStyleSheet(f"QComboBox {{ {field_style} }} QComboBox::drop-down {{ border:none; }}")
        p_layout.addWidget(self.mois_combo)
        
        p_layout.addWidget(lbl("ANNÉE"))
        self.annee_spin = QSpinBox()
        self.annee_spin.setRange(2020, 2030)
        self.annee_spin.setValue(datetime.now().year)
        self.annee_spin.setFixedWidth(80)
        self.annee_spin.setStyleSheet(f"QSpinBox {{ {field_style} }}")
        p_layout.addWidget(self.annee_spin)
        
        p_layout.addWidget(lbl("DATE PAIEMENT"))
        self.date_paiement = QDateEdit()
        self.date_paiement.setDate(QDate.currentDate())
        self.date_paiement.setCalendarPopup(True)
        self.date_paiement.setFixedWidth(130)
        self.date_paiement.setStyleSheet(f"QDateEdit {{ {field_style} }}")
        p_layout.addWidget(self.date_paiement)
        p_layout.addStretch()
        layout.addWidget(periode_frame)
        
        # ── Tableau répartitions ──────────────────────────────────────────────
        table_frame = QFrame()
        table_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.CLR_SURFACE};
                border-radius: 10px;
                border: 1px solid {self.CLR_BORDER};
            }}
        """)
        tf_layout = QVBoxLayout(table_frame)
        tf_layout.setContentsMargins(14, 12, 14, 12)
        tf_layout.setSpacing(10)
        
        # Titre section + boutons
        tb_header = QHBoxLayout()
        sec_title = QLabel("🏢  Répartition par site / client")
        sec_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {self.CLR_TEXT};")
        tb_header.addWidget(sec_title)
        tb_header.addStretch()
        
        btn_add_r = QPushButton("➕  Ajouter")
        btn_add_r.setFixedHeight(32)
        btn_add_r.setStyleSheet(self._btn_style(self.CLR_GREEN, self.CLR_PRIMARY))
        btn_add_r.clicked.connect(self.add_repartition)
        
        btn_edit_r = QPushButton("✏️  Modifier")
        btn_edit_r.setFixedHeight(32)
        btn_edit_r.setStyleSheet(self._btn_style(self.CLR_BLUE, "#2471A3"))
        btn_edit_r.clicked.connect(self.edit_repartition)
        
        btn_del_r = QPushButton("🗑️  Supprimer")
        btn_del_r.setFixedHeight(32)
        btn_del_r.setStyleSheet(self._btn_style(self.CLR_DANGER, "#C0392B"))
        btn_del_r.clicked.connect(self.delete_repartition)
        
        for b in (btn_add_r, btn_edit_r, btn_del_r):
            tb_header.addWidget(b)
        tf_layout.addLayout(tb_header)
        
        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {self.CLR_BORDER};")
        tf_layout.addWidget(sep)
        
        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Site / Client", "Agents", "Brut (DA)", "CNSS (DA)", "Net (DA)", "% CNSS", "Notes"
        ])
        self.table.setColumnHidden(0, True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                background: {self.CLR_SURFACE};
                gridline-color: {self.CLR_BORDER};
                selection-background-color: #D4EDDA;
                selection-color: #155724;
                font-size: 13px; outline: none;
            }}
            QHeaderView::section {{
                background: {self.CLR_PRIMARY};
                color: white; padding: 9px 10px;
                font-weight: 700; font-size: 11px;
                border: none;
                border-right: 1px solid rgba(255,255,255,0.15);
            }}
            QTableWidget::item {{
                padding: 7px 10px;
                border-bottom: 1px solid {self.CLR_BORDER};
            }}
            QScrollBar:vertical {{
                background: {self.CLR_BG}; width: 7px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.CLR_BORDER}; border-radius: 4px;
            }}
        """)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.edit_repartition)
        tf_layout.addWidget(self.table)
        
        # Barre de totaux intégrée dans le tableau
        totals_bar = QFrame()
        totals_bar.setFixedHeight(46)
        totals_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #EAF6F0, stop:1 #FEF9EC);
                border-radius: 8px;
                border: 1px solid {self.CLR_BORDER};
            }}
        """)
        tot_layout = QHBoxLayout(totals_bar)
        tot_layout.setContentsMargins(16, 0, 16, 0)
        tot_layout.setSpacing(30)
        
        def total_widget(label_txt, color):
            w = QHBoxLayout()
            lbl_t = QLabel(label_txt)
            lbl_t.setStyleSheet(f"font-size: 11px; color: {self.CLR_SUB}; font-weight: 600;")
            val = QLabel("0 DA")
            val.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {color};")
            w.addWidget(lbl_t)
            w.addWidget(val)
            return w, val
        
        brut_row, self.total_brut_label = total_widget("BRUT :", self.CLR_BLUE)
        cnss_row, self.total_cnss_label = total_widget("CNSS :", self.CLR_ORANGE)
        net_row,  self.total_net_label  = total_widget("NET :",  self.CLR_GREEN)
        
        tot_layout.addStretch()
        tot_layout.addLayout(brut_row)
        tot_layout.addLayout(cnss_row)
        tot_layout.addLayout(net_row)
        tf_layout.addWidget(totals_bar)
        layout.addWidget(table_frame)
        
        # ── Notes ─────────────────────────────────────────────────────────────
        notes_frame = QFrame()
        notes_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.CLR_SURFACE};
                border-radius: 10px;
                border: 1px solid {self.CLR_BORDER};
            }}
        """)
        notes_frame.setFixedHeight(76)
        nf_layout = QVBoxLayout(notes_frame)
        nf_layout.setContentsMargins(14, 8, 14, 8)
        notes_title = QLabel("📝  Notes")
        notes_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {self.CLR_SUB};")
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notes générales sur cette paie...")
        self.notes_edit.setStyleSheet(f"""
            QTextEdit {{
                border: none; background: transparent;
                font-size: 13px; color: {self.CLR_TEXT};
            }}
        """)
        nf_layout.addWidget(notes_title)
        nf_layout.addWidget(self.notes_edit)
        layout.addWidget(notes_frame)
        
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
        btn_save.clicked.connect(self.save)
        
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
    
    def set_default_period(self):
        """Définit la période par défaut (mois en cours)"""
        today = datetime.now()
        self.mois_combo.setCurrentIndex(today.month - 1)
        self.annee_spin.setValue(today.year)
    
    def add_repartition(self):
        """Ajoute une répartition — sauvegarde la paie d'abord si elle n'existe pas encore."""
        if not self.paye_id:
            mois = self.mois_combo.currentIndex() + 1
            annee = self.annee_spin.value()
            date_paiement = self.date_paiement.date().toPyDate()
            try:
                paye = PayeGlobale(
                    mois=mois,
                    annee=annee,
                    date_paiement=date_paiement,
                    total_brut=0.0,
                    total_cnss=0.0,
                    total_net=0.0,
                )
                self.session.add(paye)
                self.session.commit()
                self.paye_id = paye.id
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Erreur", f"Impossible de créer la paie : {e}")
                return
        
        dialog = RepartitionDialog(paye_id=self.paye_id, parent=self)
        if dialog.exec():
            self.load_repartitions()
    
    def edit_repartition(self):
        """Modifie la répartition sélectionnée"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une répartition")
            return
        
        row = selected[0].row()
        repart_id = int(self.table.item(row, 0).text())
        
        dialog = RepartitionDialog(repartition_id=repart_id, parent=self)
        if dialog.exec():
            self.load_repartitions()
    
    def delete_repartition(self):
        """Supprime la répartition sélectionnée"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une répartition")
            return
        
        row = selected[0].row()
        repart_id = int(self.table.item(row, 0).text())
        site_name = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer la répartition pour '{site_name}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.paye_id:
                repart = self.session.query(RepartitionPaie).filter(RepartitionPaie.id == repart_id).first()
                if repart:
                    self.session.delete(repart)
                    self.session.commit()
            else:
                self._temp_repartitions = [r for r in self._temp_repartitions if r.get('id') != repart_id]
            
            self.load_repartitions()
    
    def load_repartitions(self):
        """Charge les répartitions dans le tableau"""
        self.table.setRowCount(0)
        
        repartitions = []
        if self.paye_id:
            paye = self.session.query(PayeGlobale).filter(PayeGlobale.id == self.paye_id).first()
            if paye:
                repartitions = paye.repartitions
        elif hasattr(self, '_temp_repartitions'):
            repartitions = self._temp_repartitions
        
        total_brut = 0
        total_cnss = 0
        total_net = 0
        
        RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        CENTER = Qt.AlignmentFlag.AlignCenter
        
        for row, repart in enumerate(repartitions):
            self.table.insertRow(row)
            self.table.setRowHeight(row, 40)
            
            # ID
            id_val = repart.id if hasattr(repart, 'id') else repart.get('id', row)
            self.table.setItem(row, 0, QTableWidgetItem(str(id_val)))
            
            # Site/Client
            if hasattr(repart, 'nom_affichage'):
                site_name = repart.nom_affichage
            elif hasattr(repart, 'client') and repart.client:
                site_name = f"{repart.client.raison_sociale}"
            elif hasattr(repart, 'nom_site'):
                site_name = repart.nom_site
            else:
                site_name = repart.get('nom_site', '–')
            
            site_item = QTableWidgetItem(site_name)
            f = QFont("Segoe UI", 12, QFont.Weight.Bold)
            site_item.setFont(f)
            site_item.setForeground(QColor("#1C2B36"))
            self.table.setItem(row, 1, site_item)
            
            # Nb agents
            nb_agents = repart.nombre_agents if hasattr(repart, 'nombre_agents') else repart.get('nombre_agents', 0)
            ag_item = QTableWidgetItem(str(nb_agents))
            ag_item.setTextAlignment(CENTER)
            ag_item.setForeground(QColor("#6B7C8D"))
            self.table.setItem(row, 2, ag_item)
            
            # Brut
            brut = repart.montant_brut if hasattr(repart, 'montant_brut') else repart.get('montant_brut', 0)
            brut_item = QTableWidgetItem(f"{brut:,.0f}".replace(",", " "))
            brut_item.setTextAlignment(RIGHT)
            brut_item.setForeground(QColor("#2980B9"))
            self.table.setItem(row, 3, brut_item)
            total_brut += brut
            
            # CNSS
            cnss = repart.montant_cnss if hasattr(repart, 'montant_cnss') else repart.get('montant_cnss', 0)
            cnss_item = QTableWidgetItem(f"{cnss:,.0f}".replace(",", " "))
            cnss_item.setTextAlignment(RIGHT)
            cnss_item.setForeground(QColor("#F39C12"))
            self.table.setItem(row, 4, cnss_item)
            total_cnss += cnss
            
            # Net
            net = repart.montant_net if hasattr(repart, 'montant_net') else repart.get('montant_net', 0)
            net_item = QTableWidgetItem(f"{net:,.0f}".replace(",", " "))
            net_item.setTextAlignment(RIGHT)
            net_item.setForeground(QColor("#27AE60"))
            net_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.table.setItem(row, 5, net_item)
            total_net += net
            
            # % CNSS calculé
            pct = (cnss / brut * 100) if brut > 0 else 0
            pct_item = QTableWidgetItem(f"{pct:.1f} %")
            pct_item.setTextAlignment(CENTER)
            pct_color = "#E74C3C" if pct > 20 else "#F39C12" if pct > 10 else "#27AE60"
            pct_item.setForeground(QColor(pct_color))
            self.table.setItem(row, 6, pct_item)
            
            # Notes
            notes = repart.notes if hasattr(repart, 'notes') else repart.get('notes', '')
            notes_item = QTableWidgetItem(notes or "")
            notes_item.setForeground(QColor("#6B7C8D"))
            self.table.setItem(row, 7, notes_item)
        
        # Mettre à jour les totaux
        self.total_brut_label.setText(f"{total_brut:,.0f} DA".replace(",", " "))
        self.total_cnss_label.setText(f"{total_cnss:,.0f} DA".replace(",", " "))
        self.total_net_label.setText(f"{total_net:,.0f} DA".replace(",", " "))
    
    def load_data(self):
        """Charge les données d'une paie existante"""
        paye = self.session.query(PayeGlobale).filter(PayeGlobale.id == self.paye_id).first()
        if paye:
            self.mois_combo.setCurrentIndex(paye.mois - 1)
            self.annee_spin.setValue(paye.annee)
            self.date_paiement.setDate(QDate(paye.date_paiement.year, paye.date_paiement.month, paye.date_paiement.day))
            self.notes_edit.setText(paye.notes or "")
            self.load_repartitions()
    
    def save(self):
        """Sauvegarde la paie globale"""
        mois = self.mois_combo.currentIndex() + 1
        annee = self.annee_spin.value()
        date_paiement = self.date_paiement.date().toPyDate()
        notes = self.notes_edit.toPlainText().strip() or None
        
        total_brut = 0
        total_cnss = 0
        total_net = 0
        
        repartitions = []
        if self.paye_id:
            paye = self.session.query(PayeGlobale).filter(PayeGlobale.id == self.paye_id).first()
            if paye:
                repartitions = paye.repartitions
        elif hasattr(self, '_temp_repartitions'):
            repartitions = self._temp_repartitions
        
        for repart in repartitions:
            if hasattr(repart, 'montant_brut'):
                total_brut += repart.montant_brut
                total_cnss += repart.montant_cnss
                total_net += repart.montant_net
            else:
                total_brut += repart.get('montant_brut', 0)
                total_cnss += repart.get('montant_cnss', 0)
                total_net += repart.get('montant_net', 0)
        
        try:
            if self.paye_id:
                paye = self.session.query(PayeGlobale).filter(PayeGlobale.id == self.paye_id).first()
                if not paye:
                    QMessageBox.critical(self, "Erreur", "Paie non trouvée")
                    return
            else:
                paye = PayeGlobale()
                self.session.add(paye)
            
            paye.mois = mois
            paye.annee = annee
            paye.date_paiement = date_paiement
            paye.total_brut = total_brut
            paye.total_cnss = total_cnss
            paye.total_net = total_net
            paye.notes = notes
            
            self.session.commit()
            
            self.paye_saved.emit()
            QMessageBox.information(self, "Succès", "Paie enregistrée avec succès!")
            self.accept()
            
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde: {str(e)}")
    
    def closeEvent(self, event):
        """Ferme la session"""
        self.session.close()
        event.accept()