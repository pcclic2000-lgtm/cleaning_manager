# views/attestation_cnas_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QMessageBox, QGroupBox,
    QFormLayout, QLineEdit, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from pathlib import Path
import os

from services.attestation_cnas import AttestationCNASExactGenerator


class GenerationThread(QThread):
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


class AttestationCNASExactWidget(QWidget):
    attestation_generated = pyqtSignal(str)
    
    def __init__(self, employee_id: int, parent=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.generator = AttestationCNASExactGenerator()
        self.generation_thread = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # ============ EN-TÊTE ============
        header = QLabel("🏥 ATTESTATION CNAS AS-08")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # ============ INFORMATIONS ============
        info_group = QGroupBox("ℹ️ Formulaire officiel")
        info_layout = QVBoxLayout()
        
        info_text = QLabel(
            "Génération de l'attestation AS-08 EXACTEMENT conforme au modèle CNAS.\n\n"
            "• Reproduction à l'identique du formulaire officiel\n"
            "• Tableau bilingue français/arabe\n"
            "• 12 derniers mois de salaire\n"
            "• Mentions légales complètes"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("padding: 10px; background: #f8f9fa; border-radius: 5px;")
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # ============ PARAMÈTRES ============
        params_group = QGroupBox("⚙️ Paramètres")
        params_layout = QFormLayout()
        
        self.chk_open = QCheckBox("Ouvrir le PDF après génération")
        self.chk_open.setChecked(True)
        params_layout.addRow("", self.chk_open)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # ============ PROGRESS BAR ============
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 5px;
                height: 25px;
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
        self.lbl_status.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(self.lbl_status)
        
        # ============ BOUTONS ============
        buttons_layout = QHBoxLayout()
        
        self.btn_generate = QPushButton("📄 GÉNÉRER L'ATTESTATION")
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #229954;
            }
            QPushButton:disabled {
                background: #95a5a6;
            }
        """)
        self.btn_generate.clicked.connect(self.generate)
        buttons_layout.addWidget(self.btn_generate)
        
        self.btn_cancel = QPushButton("❌ Annuler")
        self.btn_cancel.setStyleSheet("""
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
            QPushButton:disabled {
                background: #95a5a6;
            }
        """)
        self.btn_cancel.clicked.connect(self.cancel)
        self.btn_cancel.setEnabled(False)
        buttons_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(buttons_layout)
    
    def generate(self):
        self.btn_generate.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Initialisation...")
        
        self.generation_thread = GenerationThread(
            self.generator,
            self.employee_id
        )
        
        self.generation_thread.progress.connect(self.update_progress)
        self.generation_thread.finished.connect(self.on_finished)
        self.generation_thread.error.connect(self.on_error)
        
        self.generation_thread.start()
    
    def update_progress(self, value: int, message: str):
        self.progress_bar.setValue(value)
        self.lbl_status.setText(message)
    
    def on_finished(self, output_path: str, success: bool):
        self.btn_generate.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        
        if success:
            self.lbl_status.setText(f"✅ Attestation générée: {os.path.basename(output_path)}")
            self.attestation_generated.emit(output_path)
            
            if self.chk_open.isChecked():
                self._open_pdf(output_path)
            
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
        if self.generation_thread and self.generation_thread.isRunning():
            self.generation_thread.terminate()
            self.generation_thread.wait()
            self.btn_generate.setEnabled(True)
            self.btn_cancel.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.lbl_status.setText("⏹ Génération annulée")
    
    def _open_pdf(self, pdf_path: str):
        import subprocess
        import sys
        try:
            if sys.platform == 'win32':
                os.startfile(pdf_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', pdf_path])
            else:
                subprocess.run(['xdg-open', pdf_path])
        except:
            pass