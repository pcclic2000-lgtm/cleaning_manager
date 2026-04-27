# views/employees/employee_arret_dialog.py
"""Dialogue de saisie de la date d'arrêt d'un employé."""
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QDateEdit, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

class EmployeeArretDialog(QDialog):
    """Dialogue pour choisir la date d'arrêt d'un employé"""
    
    date_selected = pyqtSignal(QDate, str)  # date, raison
    
    def __init__(self, employee_name: str, parent=None):
        super().__init__(parent)
        
        self.employee_name = employee_name
        self.date_arret = None
        self.raison_arret = ""
        
        self.setWindowTitle(f"Date d'arrêt - {employee_name}")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title = QLabel(f"Désactiver l'employé : {self.employee_name}")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #e74c3c; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Message d'information
        info = QLabel("Veuillez sélectionner la date d'arrêt de l'employé :")
        info.setStyleSheet("padding: 5px; color: #7f8c8d;")
        layout.addWidget(info)
        
        # Date d'arrêt
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Date d'arrêt :"))
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        date_layout.addWidget(self.date_edit)
        layout.addLayout(date_layout)
        
        # Option : date antérieure
        self.cb_date_passee = QCheckBox("Sélectionner une date antérieure")
        self.cb_date_passee.stateChanged.connect(self.toggle_date_limite)
        layout.addWidget(self.cb_date_passee)
        
        # Raison d'arrêt (optionnel)
        raison_layout = QHBoxLayout()
        raison_layout.addWidget(QLabel("Raison (optionnel) :"))
        
        self.combo_raison = QComboBox()
        self.combo_raison.addItems([
            "Fin de contrat",
            "Démission",
            "Licenciement",
            "Retraite",
            "Arrêt maladie prolongé",
            "Autre raison"
        ])
        self.combo_raison.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
        """)
        raison_layout.addWidget(self.combo_raison)
        layout.addLayout(raison_layout)
        
        # Message d'avertissement
        warning = QLabel("⚠️ L'employé sera marqué comme 'Inactif' et ne pourra plus être assigné à de nouvelles tâches.")
        warning.setStyleSheet("""
            color: #e67e22;
            background-color: #fef9e7;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #f39c12;
        """)
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        # Boutons
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        
        btn_confirm = QPushButton("✅ Confirmer l'arrêt")
        btn_confirm.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 150px;
            }
            QPushButton:hover {
                background: #c0392b;
            }
            QPushButton:disabled {
                background: #ecf0f1;
                color: #95a5a6;
            }
        """)
        btn_confirm.clicked.connect(self.confirm_arret)
        
        btn_cancel = QPushButton("❌ Annuler")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 150px;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        buttons.addStretch()
        buttons.addWidget(btn_confirm)
        buttons.addWidget(btn_cancel)
        
        layout.addLayout(buttons)
        self.setLayout(layout)
    
    def toggle_date_limite(self, state):
        """Active/désactive la limite de date"""
        if state == Qt.CheckState.Checked.value:
            self.date_edit.setMaximumDate(QDate(2099, 12, 31))  # Date très lointaine
        else:
            # Limite à aujourd'hui
            self.date_edit.setMaximumDate(QDate.currentDate())
    
    def confirm_arret(self):
        """Confirme la date d'arrêt"""
        selected_date = self.date_edit.date()
        today = QDate.currentDate()
        
        # Validation
        if not self.cb_date_passee.isChecked() and selected_date > today:
            QMessageBox.warning(self, "Date invalide", 
                              "La date d'arrêt ne peut pas être dans le futur.\n"
                              "Cochez 'Sélectionner une date antérieure' si nécessaire.")
            return
        
        # Demander confirmation supplémentaire pour les dates antérieures
        if selected_date < today.addDays(-7):  # Plus d'une semaine dans le passé
            reply = QMessageBox.question(
                self, "Confirmation",
                f"Vous avez sélectionné une date antérieure ({selected_date.toString('dd/MM/yyyy')}).\n"
                "Êtes-vous sûr de vouloir continuer ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.date_arret = selected_date.toPyDate()
        self.raison_arret = self.combo_raison.currentText()
        
        # Émettre le signal
        self.date_selected.emit(selected_date, self.raison_arret)
        self.accept()


