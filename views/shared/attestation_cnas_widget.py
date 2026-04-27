# views/attestation_cnas_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QMessageBox, QGroupBox,
    QCheckBox, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
import os
from pathlib import Path

from services.attestation_cnas_excel import AttestationCNASExcelGenerator


class GenerationThread(QThread):
    """Thread pour la génération sans bloquer l'interface"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str, bool)
    error = pyqtSignal(str)
    
    def __init__(self, generator, employee_id, output_path=None):
        super().__init__()
        self.generator = generator
        self.employee_id = employee_id
        self.output_path = output_path
        
        self.generator.progress_updated.connect(self.progress)
        self.generator.generation_finished.connect(self.finished)
        self.generator.error_occurred.connect(self.error)
    
    def run(self):
        try:
            self.generator.generate_for_employee(
                self.employee_id,
                self.output_path
            )
        except Exception as e:
            self.error.emit(str(e))


class AttestationCNASWidget(QWidget):
    """Widget d'attestation CNAS AS-08 pour Excel"""
    
    attestation_generated = pyqtSignal(str)
    
    def __init__(self, employee_id: int, employee_nom: str = "", employee_prenom: str = "", parent=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.employee_nom = employee_nom
        self.employee_prenom = employee_prenom
        self.generator = AttestationCNASExcelGenerator()
        self.generation_thread = None
        self.last_file = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # ===== EN-TÊTE =====
        header = QLabel("🏥 ATTESTATION CNAS AS-08")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px; background: #f8f9fa; border-radius: 8px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # ===== INFORMATIONS =====
        info_group = QGroupBox("📋 Formulaire officiel")
        info_layout = QVBoxLayout()
        
        info_text = QLabel(
            f"<b>Employé :</b> {self.employee_prenom} {self.employee_nom}<br><br>"
            "Génération de l'attestation AS-08 au format Excel :<br>"
            "• Reproduction exacte du formulaire CNAS officiel<br>"
            "• Tableau bilingue français/arabe<br>"
            "• 12 derniers mois de salaire automatiques<br>"
            "• Calcul automatique de la cotisation (9%)<br>"
            "• Mentions légales complètes"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("padding: 15px; background: #f8f9fa; border-radius: 5px;")
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # ===== PARAMÈTRES =====
        params_group = QGroupBox("⚙️ Paramètres")
        params_layout = QFormLayout()
        
        self.chk_open = QCheckBox("Ouvrir le dossier après génération")
        self.chk_open.setChecked(True)
        params_layout.addRow("", self.chk_open)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # ===== PROGRESS BAR =====
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 5px;
                height: 25px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2ecc71);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        self.lbl_status = QLabel("Prêt à générer l'attestation")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 5px;")
        layout.addWidget(self.lbl_status)
        
        # ===== BOUTONS =====
        buttons_layout = QHBoxLayout()
        
        self.btn_generate = QPushButton("📊 GÉNÉRER L'ATTESTATION EXCEL")
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #27ae60, stop:1 #229954);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 250px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #229954, stop:1 #1e8449);
            }
            QPushButton:disabled {
                background: #95a5a6;
            }
        """)
        self.btn_generate.clicked.connect(self.generate)
        buttons_layout.addWidget(self.btn_generate)
        
        self.btn_open = QPushButton("📁 Ouvrir le dossier")
        self.btn_open.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_open.clicked.connect(self.open_folder)
        self.btn_open.setEnabled(False)
        buttons_layout.addWidget(self.btn_open)
        
        self.btn_cancel = QPushButton("❌ Annuler")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_cancel.clicked.connect(self.cancel)
        self.btn_cancel.setEnabled(False)
        buttons_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(buttons_layout)
    
    def generate(self):
        """Lance la génération de l'attestation"""
        # Demander confirmation
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Générer l'attestation AS-08 pour {self.employee_prenom} {self.employee_nom} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Désactiver les boutons
        self.btn_generate.setEnabled(False)
        self.btn_open.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        
        # Afficher la progression
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Initialisation...")
        
        # Créer et démarrer le thread
        self.generation_thread = GenerationThread(
            self.generator,
            self.employee_id
        )
        
        self.generation_thread.progress.connect(self.update_progress)
        self.generation_thread.finished.connect(self.on_finished)
        self.generation_thread.error.connect(self.on_error)
        
        self.generation_thread.start()
    
    def update_progress(self, value: int, message: str):
        """Met à jour la barre de progression"""
        self.progress_bar.setValue(value)
        self.lbl_status.setText(message)
    
    def on_finished(self, output_path: str, success: bool):
        """Callback à la fin de la génération"""
        self.btn_generate.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        
        if success:
            self.last_file = output_path
            self.btn_open.setEnabled(True)
            self.lbl_status.setText(f"✅ Attestation générée: {os.path.basename(output_path)}")
            self.attestation_generated.emit(output_path)
            
            # Ouvrir le dossier si demandé
            if self.chk_open.isChecked():
                self.open_folder()
            
            QMessageBox.information(
                self,
                "Succès",
                f"✅ Attestation AS-08 générée avec succès !\n\n"
                f"📄 Fichier: {os.path.basename(output_path)}\n"
                f"📁 Dossier: {os.path.dirname(output_path)}"
            )
        else:
            self.progress_bar.setVisible(False)
            self.lbl_status.setText("❌ Échec de la génération")
    
    def on_error(self, error_msg: str):
        """Callback en cas d'erreur"""
        self.btn_generate.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("❌ Erreur")
        
        QMessageBox.critical(
            self,
            "Erreur",
            f"❌ Impossible de générer l'attestation:\n\n{error_msg}"
        )
    
    def cancel(self):
        """Annule la génération en cours"""
        if self.generation_thread and self.generation_thread.isRunning():
            self.generation_thread.terminate()
            self.generation_thread.wait()
            self.btn_generate.setEnabled(True)
            self.btn_cancel.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.lbl_status.setText("⏹ Génération annulée")
    
    def open_folder(self):
        """Ouvre le dossier contenant le fichier généré"""
        if self.last_file:
            folder = os.path.dirname(self.last_file)
            try:
                import subprocess
                import sys
                if sys.platform == 'win32':
                    os.startfile(folder)
                elif sys.platform == 'darwin':
                    subprocess.run(['open', folder])
                else:
                    subprocess.run(['xdg-open', folder])
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Impossible d'ouvrir le dossier:\n{str(e)}")