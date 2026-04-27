# views/benimessous_service_dialog.py
"""
Dialogue pour ajouter un service à une facture Beni Messous
"""

import calendar
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QDateEdit, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt, QDate


class BeniMessousServiceDialog(QDialog):
    """Dialogue pour ajouter un service Beni Messous"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un service")
        self.setModal(True)
        self.setMinimumWidth(550)
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        form.setSpacing(10)
        
        # Désignation
        self.designation = QLineEdit()
        self.designation.setPlaceholderText("Ex: Service pneumo-phtsiologie A complet")
        form.addRow("Désignation du service *:", self.designation)
        
        # Tranche horaire
        self.tranche = QComboBox()
        self.tranche.addItems(["08H à 16H30", "24h/24h", "08H-16H", "16H-00H", "00H-08H", "Matin", "Après-midi", "Nuit", "Week-end"])
        form.addRow("Tranche horaire *:", self.tranche)
        
        # Nombre d'agents
        self.nb_agents = QSpinBox()
        self.nb_agents.setRange(1, 100)
        self.nb_agents.setValue(1)
        form.addRow("Nombre d'agents *:", self.nb_agents)
        
        # Prix unitaire par jour
        self.prix_unitaire = QDoubleSpinBox()
        self.prix_unitaire.setRange(0, 1000000)
        self.prix_unitaire.setDecimals(2)
        self.prix_unitaire.setSuffix(" DA")
        self.prix_unitaire.setValue(0)
        form.addRow("Prix U / jour *:", self.prix_unitaire)
        
        # Mois de facturation
        self.month_year = QDateEdit()
        self.month_year.setDate(QDate.currentDate())
        self.month_year.setCalendarPopup(True)
        self.month_year.setDisplayFormat("MM/yyyy")
        self.month_year.dateChanged.connect(self.update_days)
        form.addRow("Mois de facturation *:", self.month_year)
        
        # Nombre de jours (calculé automatiquement)
        self.nb_jours = QSpinBox()
        self.nb_jours.setRange(1, 31)
        self.nb_jours.setValue(30)
        self.nb_jours.setEnabled(False)
        self.nb_jours.setStyleSheet("background-color: #f0f0f0;")
        form.addRow("Nombre de jours:", self.nb_jours)
        
        # Option pour jours spécifiques
        self.custom_days = QComboBox()
        self.custom_days.addItems(["Mois complet", "Jours spécifiques"])
        self.custom_days.currentIndexChanged.connect(self.on_custom_days_changed)
        form.addRow("Période:", self.custom_days)
        
        # Champ pour jours spécifiques (caché par défaut)
        self.specific_days = QSpinBox()
        self.specific_days.setRange(1, 31)
        self.specific_days.setValue(30)
        self.specific_days.setVisible(False)
        form.addRow("Jours spécifiques:", self.specific_days)
        
        layout.addLayout(form)
        
        # Montant HT calculé
        self.montant_ht_label = QLabel("Montant HT: <b>0.00 DA</b>")
        self.montant_ht_label.setStyleSheet("font-size: 14px; color: #27ae60; margin: 10px;")
        layout.addWidget(self.montant_ht_label)
        
        # Connecter les signaux pour le calcul en temps réel
        self.nb_agents.valueChanged.connect(self.calculate_montant)
        self.prix_unitaire.valueChanged.connect(self.calculate_montant)
        self.custom_days.currentIndexChanged.connect(self.calculate_montant)
        self.specific_days.valueChanged.connect(self.calculate_montant)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # Calcul initial
        self.update_days()
        self.calculate_montant()
    
    def update_days(self):
        """Met à jour le nombre de jours en fonction du mois sélectionné"""
        date = self.month_year.date()
        year = date.year()
        month = date.month()
        
        # Obtenir le dernier jour du mois
        last_day = calendar.monthrange(year, month)[1]
        self.nb_jours.setValue(last_day)
        self.specific_days.setMaximum(last_day)
        self.specific_days.setValue(last_day)
    
    def on_custom_days_changed(self, index):
        """Active/désactive le champ de jours spécifiques"""
        if index == 0:  # Mois complet
            self.specific_days.setVisible(False)
            self.nb_jours.setEnabled(False)
        else:  # Jours spécifiques
            self.specific_days.setVisible(True)
            self.nb_jours.setEnabled(True)
            self.nb_jours.setValue(self.specific_days.value())
    
    def calculate_montant(self):
        """Calcule le montant HT en temps réel"""
        agents = self.nb_agents.value()
        prix = self.prix_unitaire.value()
        
        # Déterminer le nombre de jours
        if self.custom_days.currentIndex() == 0:  # Mois complet
            jours = self.nb_jours.value()
        else:  # Jours spécifiques
            jours = self.specific_days.value()
        
        montant = agents * prix * jours
        
        self.montant_ht_label.setText(
            f"Montant HT: <b>{montant:,.2f} DA</b>".replace(",", " ")
        )
    
    def validate_and_accept(self):
        """Valide les champs avant d'accepter"""
        if not self.designation.text().strip():
            QMessageBox.warning(self, "Erreur", "La désignation est obligatoire")
            return
        
        if self.prix_unitaire.value() <= 0:
            QMessageBox.warning(self, "Erreur", "Le prix unitaire doit être supérieur à 0")
            return
        
        self.accept()
    
    def get_service_data(self):
        """Retourne les données du service"""
        agents = self.nb_agents.value()
        prix = self.prix_unitaire.value()
        
        if self.custom_days.currentIndex() == 0:  # Mois complet
            jours = self.nb_jours.value()
        else:  # Jours spécifiques
            jours = self.specific_days.value()
        
        montant = agents * prix * jours
        
        return {
            'designation': self.designation.text().strip(),
            'tranche': self.tranche.currentText(),
            'agents': agents,
            'prix': prix,
            'jours': jours,
            'montant': montant,
            'periode': self.month_year.date().toString("MM/yyyy")
        }