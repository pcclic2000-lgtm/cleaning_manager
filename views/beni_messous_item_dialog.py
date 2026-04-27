# views/beni_messous_item_dialog.py
"""Dialogue pour ajouter un article à la facture spéciale Beni Messous"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt


class BeniMessousItemDialog(QDialog):
    """Dialog pour renseigner une ligne de prestation Beni Messous"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter prestation Beni Messous")
        self.setModal(True)
        self.setMinimumWidth(520)

        layout = QVBoxLayout()
        form = QFormLayout()
        form.setSpacing(10)

        self.designation = QLineEdit()
        self.designation.setPlaceholderText("Ex: Nettoyage bloc opératoire")
        form.addRow("Désignation *:", self.designation)

        self.tranche_horaire = QComboBox()
        self.tranche_horaire.addItems([
            "08H à 16H30", "24h/24h", "08H-16H", "16H-00H", "00H-08H",
            "Matin", "Après-midi", "Nuit", "Week-end"
        ])
        form.addRow("Tranche horaire *:", self.tranche_horaire)

        self.nb_agents = QSpinBox()
        self.nb_agents.setRange(1, 1000)
        self.nb_agents.setValue(1)
        form.addRow("Nb agents *:", self.nb_agents)

        self.prix_unitaire = QDoubleSpinBox()
        self.prix_unitaire.setRange(0.0, 10000000.0)
        self.prix_unitaire.setDecimals(2)
        self.prix_unitaire.setSuffix(" DA")
        self.prix_unitaire.setValue(0.0)
        form.addRow("Prix U / jour *:", self.prix_unitaire)

        self.nb_jours = QSpinBox()
        self.nb_jours.setRange(1, 365)
        self.nb_jours.setValue(1)
        form.addRow("Nb jours *:", self.nb_jours)

        layout.addLayout(form)

        self.montant_ht_label = QLabel("Montant HT: <b>0.00 DA</b>")
        self.montant_ht_label.setStyleSheet("font-size: 13px; color: #27ae60; margin: 8px;")
        layout.addWidget(self.montant_ht_label)

        self.nb_agents.valueChanged.connect(self._update_amount)
        self.prix_unitaire.valueChanged.connect(self._update_amount)
        self.nb_jours.valueChanged.connect(self._update_amount)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)

        self._update_amount()

    def _update_amount(self):
        montant_ht = self.nb_agents.value() * self.prix_unitaire.value() * self.nb_jours.value()
        self.montant_ht_label.setText(f"Montant HT: <b>{montant_ht:,.2f} DA</b>".replace(",", " "))

    def _validate_and_accept(self):
        if not self.designation.text().strip():
            QMessageBox.warning(self, "Erreur", "La désignation est obligatoire")
            return
        if self.prix_unitaire.value() <= 0:
            QMessageBox.warning(self, "Erreur", "Le prix unitaire doit être supérieur à 0")
            return
        if self.nb_jours.value() <= 0:
            QMessageBox.warning(self, "Erreur", "Le nombre de jours doit être supérieur à 0")
            return
        self.accept()

    def get_item_data(self):
        montant_ht = self.nb_agents.value() * self.prix_unitaire.value() * self.nb_jours.value()
        return {
            'designation': self.designation.text().strip(),
            'tranche_horaire': self.tranche_horaire.currentText(),
            'nb_agents': self.nb_agents.value(),
            'prix_unitaire': self.prix_unitaire.value(),
            'nb_jours': self.nb_jours.value(),
            'montant_ht': montant_ht
        }
