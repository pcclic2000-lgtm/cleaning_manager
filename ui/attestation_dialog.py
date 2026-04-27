# ui/attestation_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFormLayout, QComboBox, QGroupBox,
    QMessageBox
)
from PyQt6.QtCore import Qt

from services.attestation_pdf_service import AttestationPDFService
from database.db import SessionLocal, get_session
from models.employee import Employee

class AttestationDialog(QDialog):
    """Dialogue pour générer une attestation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.attestation_service = AttestationPDFService()
        self.setWindowTitle("Générer une attestation")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.init_ui()
        self.load_employees()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Sélection de l'employé
        group_employee = QGroupBox("Sélection de l'employé")
        form_layout = QFormLayout()
        
        self.employee_combo = QComboBox()
        self.employee_combo.setMinimumHeight(35)
        form_layout.addRow("Employé:", self.employee_combo)
        
        # Informations employé
        self.info_label = QLabel("Sélectionnez un employé pour voir ses informations")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("padding: 10px; background: #f8f9fa; border-radius: 5px;")
        form_layout.addRow("Informations:", self.info_label)
        
        group_employee.setLayout(form_layout)
        layout.addWidget(group_employee)
        
        # Type d'attestation
        group_type = QGroupBox("Type d'attestation")
        type_layout = QVBoxLayout()
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Attestation de travail",
            "Attestation de salaire", 
            "Attestation de présence"
        ])
        type_layout.addWidget(self.type_combo)
        
        group_type.setLayout(type_layout)
        layout.addWidget(group_type)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        btn_generate = QPushButton("📄 Générer l'attestation")
        btn_generate.clicked.connect(self.generate_attestation)
        btn_generate.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(btn_generate)
        button_layout.addWidget(btn_cancel)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Connexions
        self.employee_combo.currentIndexChanged.connect(self.update_employee_info)
        self.type_combo.currentIndexChanged.connect(self.update_employee_info)
    
    def load_employees(self):
        """Charge la liste des employés"""
        try:
            with get_session() as session:
                employees = session.query(Employee).filter(
                    Employee.est_actif == True
                ).order_by(Employee.nom, Employee.prenom).all()
                
                self.employee_combo.clear()
                self.employee_combo.addItem("-- Sélectionnez un employé --", None)
                
                for emp in employees:
                    display_text = f"{emp.nom_complet} ({emp.code_employe}) - {emp.poste}"
                    self.employee_combo.addItem(display_text, emp.id)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des employés: {str(e)}")
    
    def update_employee_info(self):
        """Met à jour les informations affichées"""
        emp_id = self.employee_combo.currentData()
        if not emp_id:
            self.info_label.setText("Sélectionnez un employé pour voir ses informations")
            return
        
        try:
            with get_session() as session:
                employee = session.query(Employee).filter(Employee.id == emp_id).first()
                if employee:
                    info_text = f"""
                    <b>Nom complet:</b> {employee.nom_complet}<br>
                    <b>Fonction:</b> {employee.poste or 'Non spécifié'}<br>
                    <b>Date d'embauche:</b> {self.format_date(employee.date_embauche)}<br>
                    <b>Salaire:</b> {employee.salaire:,.2f} DA<br>
                    <b>Type d'attestation:</b> {self.type_combo.currentText()}
                    """
                    self.info_label.setText(info_text)
        except Exception as e:
            self.info_label.setText(f"Erreur: {str(e)}")
        
    def format_date(self, date_obj):
        """Formate une date"""
        if date_obj:
            return date_obj.strftime("%d/%m/%Y")
        return "N/A"
    
    def generate_attestation(self):
        """Génère l'attestation"""
        emp_id = self.employee_combo.currentData()
        if not emp_id or self.employee_combo.currentIndex() == 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un employé")
            return
        
        attestation_type = self.type_combo.currentText()
        
        try:
            with get_session() as session:
                employee = session.query(Employee).filter(Employee.id == emp_id).first()
                if employee:
                    # Préparer les données
                    employee_data = {
                        'id': employee.id,
                        'last_name': employee.nom,
                        'first_name': employee.prenom,
                        'position': employee.poste or "Non spécifié",
                        'hire_date': employee.date_embauche,
                        'birth_date': employee.date_naissance,
                        'social_number': employee.numero_secu or "Non renseigné",
                        'salary': float(employee.salaire) if employee.salaire else 0.0
                    }
                    
                    # Générer l'attestation
                    file_path = self.attestation_service.generate_attestation(
                        employee_data=employee_data,
                        attestation_type=attestation_type
                    )
                    
                    # Afficher le message de confirmation
                    QMessageBox.information(
                        self,
                        "Attestation générée",
                        f"L'attestation a été générée avec succès:\n{file_path}\n\n"
                        f"Le fichier s'ouvre automatiquement."
                    )
                    
                    self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de la génération de l'attestation:\n{str(e)}"
            )