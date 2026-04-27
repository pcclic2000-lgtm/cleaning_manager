# views/employees/employee_view.py
"""Vue principale de la liste et gestion des employés."""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QLineEdit, QLabel, QFormLayout, QComboBox,
    QTextEdit, QDateEdit, QHeaderView, QAbstractItemView,
    QMenu, QSpinBox, QDoubleSpinBox, QGroupBox, QGridLayout,
    QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QPoint
from PyQt6.QtGui import QAction, QFont, QIcon
import os
import sys
import traceback
from datetime import date, datetime
from decimal import Decimal
from database.db import SessionLocal, get_session
from models.employee import Employee
from views.employees.employee_dialog import EmployeeDialog
from views.employees.employee_arret_dialog import EmployeeArretDialog
from views.payroll.payslip_dialog import ModernPayslipDialog
from services.attestation_pdf_service import AttestationPDFService
from services.certificat_pdf_service import CertificatTravailPDFService
import subprocess

logger = logging.getLogger(__name__)

class EmployeeView(QWidget):
    """Vue pour la gestion des employés"""
    
    def __init__(self):
        super().__init__()
        self.selected_employee_id = None
        self.attestation_service = AttestationPDFService()
        self.certificat_service = CertificatTravailPDFService()
        self.init_ui()
        self.load_employees()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Titre
        title = QLabel("👥 GESTION DES EMPLOYÉS")
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #2c3e50;
            padding: 15px;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-radius: 10px;
            border-left: 5px solid #3498db;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Barre d'outils
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        btn_new = QPushButton("➕ Nouvel employé")
        btn_new.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                min-height: 40px;
            }
            QPushButton:hover {
                background: #219653;
            }
        """)
        btn_new.clicked.connect(self.create_employee)
        
        btn_edit = QPushButton("✏️ Modifier")
        btn_edit.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                min-height: 40px;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        btn_edit.clicked.connect(self.edit_employee)
        
        btn_delete = QPushButton("🗑️ Supprimer")
        btn_delete.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                min-height: 40px;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        btn_delete.clicked.connect(self.delete_employee)
        
        # Filtres
        toolbar.addWidget(QLabel("Filtrer par statut:"))
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItems(["Tous", "Actifs", "Inactifs"])
        self.cmb_filter.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 120px;
            }
        """)
        self.cmb_filter.currentTextChanged.connect(self.load_employees)
        
        toolbar.addWidget(self.cmb_filter)
        toolbar.addStretch()
        toolbar.addWidget(btn_new)
        toolbar.addWidget(btn_edit)
        toolbar.addWidget(btn_delete)
        
        layout.addLayout(toolbar)
        
        # Tableau des employés
        self.table_employees = QTableWidget()
        self.table_employees.setColumnCount(14)
        self.table_employees.setHorizontalHeaderLabels([
            "Matricule", "Nom", "Prénom", "Poste", 
            "Date Naissance", "Situation", "N° Sécu",
            "Téléphone", "Date embauche", "Date arrêt",
            "Raison arrêt", "Adresse", "Statut", "Salaire"
        ])
        
        # Style du tableau
        self.table_employees.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background: white;
                gridline-color: #dee2e6;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background: #34495e;
                color: white;
                padding: 12px 8px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #dee2e6;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        # Configuration des colonnes
        header = self.table_employees.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Matricule
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Nom
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Prénom
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Poste
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Date Naissance
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Situation
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # N° Sécu
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Téléphone
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Date embauche
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Date arrêt
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)  # Raison arrêt
        header.setSectionResizeMode(11, QHeaderView.ResizeMode.Stretch)  # Adresse
        header.setSectionResizeMode(12, QHeaderView.ResizeMode.ResizeToContents)  # Statut
        header.setSectionResizeMode(13, QHeaderView.ResizeMode.ResizeToContents)  # Salaire
        
        self.table_employees.verticalHeader().setVisible(False)
        self.table_employees.setAlternatingRowColors(True)
        self.table_employees.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_employees.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_employees.clicked.connect(self.on_employee_selected)
        
        # Menu contextuel
        self.table_employees.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_employees.customContextMenuRequested.connect(self.show_employee_context_menu)
        
        layout.addWidget(self.table_employees)
        
        # Résumé en bas
        summary = QHBoxLayout()
        self.lbl_summary = QLabel("Chargement...")
        self.lbl_summary.setStyleSheet("font-weight: bold; color: #2c3e50;")
        
        summary.addWidget(self.lbl_summary)
        summary.addStretch()
        
        # Bouton actualiser
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        btn_refresh.clicked.connect(self.load_employees)
        summary.addWidget(btn_refresh)
        
        layout.addLayout(summary)
        
        self.setLayout(layout)
    
    def load_employees(self):
        """Charge les employés avec les nouvelles colonnes"""
        logger.info("🔄 Chargement des employés...")

        try:
            with get_session() as session:
                query = session.query(Employee)

                # Appliquer le filtre de statut
                filter_text = self.cmb_filter.currentText()
                if filter_text == "Actifs":
                    query = query.filter(Employee.est_actif == True)
                elif filter_text == "Inactifs":
                    query = query.filter(Employee.est_actif == False)

                # Trier par nom
                query = query.order_by(Employee.nom, Employee.prenom)

                employees = query.all()
                logger.info(f"✅ {len(employees)} employé(s) trouvé(s)")

                # Mettre à jour le tableau
                self.table_employees.setRowCount(len(employees))

                for row, employee in enumerate(employees):
                    print(f"   📝 Remplissage ligne {row}: {employee.nom_complet}")

                    self.table_employees.setItem(row, 0, QTableWidgetItem(employee.code_employe or ""))
                    self.table_employees.setItem(row, 1, QTableWidgetItem(employee.nom or ""))
                    self.table_employees.setItem(row, 2, QTableWidgetItem(employee.prenom or ""))

                    poste = employee.poste or "Non spécifié"
                    self.table_employees.setItem(row, 3, QTableWidgetItem(poste))

                    date_naissance = ""
                    if employee.date_naissance:
                        try:
                            date_naissance = employee.date_naissance.strftime("%d/%m/%Y")
                        except Exception:
                            date_naissance = "Date invalide"
                    self.table_employees.setItem(row, 4, QTableWidgetItem(date_naissance))

                    situation = employee.situation_familiale or "Célibataire"
                    self.table_employees.setItem(row, 5, QTableWidgetItem(situation))

                    numero_secu = employee.numero_secu or ""
                    self.table_employees.setItem(row, 6, QTableWidgetItem(numero_secu))

                    self.table_employees.setItem(row, 7, QTableWidgetItem(employee.telephone or ""))

                    date_embauche_str = ""
                    if employee.date_embauche:
                        try:
                            date_embauche_str = employee.date_embauche.strftime("%d/%m/%Y")
                        except Exception:
                            date_embauche_str = "Date invalide"
                    self.table_employees.setItem(row, 8, QTableWidgetItem(date_embauche_str))

                    date_arret_str = ""
                    if employee.date_arret:
                        try:
                            date_arret_str = employee.date_arret.strftime("%d/%m/%Y")
                        except Exception:
                            date_arret_str = "Date invalide"

                    date_arret_item = QTableWidgetItem(date_arret_str)
                    if employee.date_arret:
                        date_arret_item.setForeground(Qt.GlobalColor.darkRed)
                        date_arret_item.setToolTip(f"Date de fin de contrat: {date_arret_str}")
                    self.table_employees.setItem(row, 9, date_arret_item)

                    raison_item = QTableWidgetItem(employee.raison_arret or "")
                    if employee.raison_arret:
                        raison_item.setToolTip(employee.raison_arret)
                        if "licenciement" in employee.raison_arret.lower():
                            raison_item.setForeground(Qt.GlobalColor.darkRed)
                        elif "retraite" in employee.raison_arret.lower():
                            raison_item.setForeground(Qt.GlobalColor.darkBlue)
                    self.table_employees.setItem(row, 10, raison_item)

                    adresse = employee.adresse or ""
                    if len(adresse) > 40:
                        adresse = adresse[:37] + "..."
                    self.table_employees.setItem(row, 11, QTableWidgetItem(adresse))

                    statut_item = QTableWidgetItem("Actif" if employee.est_actif else "Inactif")
                    statut_item.setForeground(Qt.GlobalColor.darkGreen if employee.est_actif else Qt.GlobalColor.darkRed)
                    self.table_employees.setItem(row, 12, statut_item)

                    try:
                        salaire_value = float(employee.salaire or 0.0)
                        salaire_text = f"{salaire_value:,.0f} DA"
                    except Exception:
                        salaire_text = "0 DA"
                    salaire_item = QTableWidgetItem(salaire_text)
                    salaire_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    salaire_item.setForeground(Qt.GlobalColor.darkBlue)
                    self.table_employees.setItem(row, 13, salaire_item)

                active_count = session.query(Employee).filter(Employee.est_actif == True).count()
                inactive_count = session.query(Employee).filter(Employee.est_actif == False).count()
                self.lbl_summary.setText(f"Total: {len(employees)} employés | Actifs: {active_count} | Inactifs: {inactive_count}")

                if employees and self.table_employees.rowCount() > 0:
                    self.table_employees.selectRow(0)
                    self.selected_employee_id = employees[0].id
                    logger.info(f"✅ Premier employé sélectionné: ID {self.selected_employee_id}")

        except Exception as e:
            logger.exception(f"❌ Erreur de chargement: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur", f"Erreur de chargement: {str(e)}")
        finally:
            print("🔚 Session fermée")
    
    def load_data(self):
        """Méthode pour la compatibilité"""
        self.load_employees()

    def on_employee_selected(self):
        """Gère la sélection d'un employé"""
        selected = self.table_employees.selectedItems()
        if not selected:
            self.selected_employee_id = None
            return

        row = selected[0].row()
        matricule = self.table_employees.item(row, 0).text()

        with get_session() as session:
            employee = session.query(Employee).filter(
                Employee.code_employe == matricule
            ).first()

            if employee:
                self.selected_employee_id = employee.id
                logger.info(f"✅ Employé sélectionné: {employee.nom_complet} (ID: {employee.id})")

    def sync_employee_status_with_service(self, employee_id, new_status):
        """Synchronise manuellement avec le service de statut si nécessaire"""
        try:
            from services.employee_status_service import EmployeeStatusService

            with get_session() as session:
                employee = session.query(Employee).filter(Employee.id == employee_id).first()

                if employee and employee.est_actif != new_status:
                    # Mettre à jour le statut
                    employee.est_actif = new_status

                    # Si désactivation, demander la date d'arrêt
                    if not new_status:
                        dialog = EmployeeArretDialog(
                            employee_name=f"{employee.prenom} {employee.nom}",
                            parent=self
                        )
                        if dialog.exec():
                            employee.date_arret = dialog.date_arret
                            employee.raison_arret = dialog.raison_arret
                        else:
                            session.rollback()
                            return

                    session.commit()

                    # Appeler le service
                    actions = EmployeeStatusService.change_employee_status(employee_id, new_status)
                    logger.info(f"✅ Statut synchronisé: actions={actions}")

        except Exception as e:
            logger.exception(f"❌ Erreur synchronisation: {e}")

    def create_employee(self):
        """Crée un nouvel employé"""
        print("📝 Ouverture du dialogue de création d'employé")
        dialog = EmployeeDialog(parent=self)
        
        # Connecter le signal - CORRECT
        dialog.employee_saved.connect(self.on_employee_saved)
        # OU: dialog.employee_saved.connect(lambda emp_id: self.on_employee_saved(emp_id))
        
        dialog.exec()
    
    def edit_employee(self):
        """Modifie l'employé sélectionné"""
        if not self.selected_employee_id:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un employé")
            return
        
        print(f"✏️ Modification de l'employé ID: {self.selected_employee_id}")
        dialog = EmployeeDialog(employee_id=self.selected_employee_id, parent=self)
        
        # Connecter le signal - CORRECT
        dialog.employee_saved.connect(self.on_employee_saved)
        # OU: dialog.employee_saved.connect(lambda emp_id: self.on_employee_saved(emp_id))
        
        dialog.exec()
    
    def on_employee_saved(self, employee_id):
        """Quand un employé est sauvegardé"""
        print(f"📢 Employé {employee_id} sauvegardé")
        self.load_employees()  # Recharger la liste
        
        # Émettre un signal pour le MainWindow si nécessaire
        if hasattr(self, 'employee_saved'):
            self.employee_saved.emit(employee_id)
    
    def delete_employee(self):
        """Supprime l'employé sélectionné"""
        if not self.selected_employee_id:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un employé")
            return

        reply = QMessageBox.question(
            self,
            "Confirmation de suppression",
            "Êtes-vous sûr de vouloir supprimer cet employé ?\nCette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            with get_session() as session:
                employee = session.query(Employee).filter(Employee.id == self.selected_employee_id).first()
                if not employee:
                    QMessageBox.warning(self, "Information", "Employé non trouvé")
                    return

                nom_complet = employee.nom_complet
                session.delete(employee)
                session.commit()

                QMessageBox.information(
                    self,
                    "Succès",
                    f"Employé {nom_complet} supprimé avec succès"
                )

                print(f"🗑️ Employé {nom_complet} supprimé")
                self.load_employees()

        except Exception as e:
            logger.exception(f"❌ Erreur lors de la suppression: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression:\n{str(e)}")


    def show_employee_context_menu(self, pos: QPoint):
        """Menu contextuel amélioré avec attestation CNAS"""
        row = self.table_employees.rowAt(pos.y())
        if row < 0:
            return
        
        matricule_item = self.table_employees.item(row, 0)
        if not matricule_item:
            return
        
        matricule = matricule_item.text()
        
        with get_session() as session:
            employee = session.query(Employee).filter(Employee.code_employe == matricule).first()
            if not employee:
                return

            self.selected_employee_id = employee.id
            
            menu = QMenu(self)
            menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #e0e6ea;
                border-radius: 8px;
                padding: 6px;
                color: #2c3e50;
                min-width: 280px;
            }
            QMenu::item {
                padding: 10px 20px;
                margin: 2px 4px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #ecf0f1;
                margin: 6px 0;
            }
            """)
            
            # ============ ACTIONS PRINCIPALES ============
            act_preview = QAction("👁️  Aperçu détaillé", self)
            act_edit = QAction("✏️  Modifier", self)
            act_delete = QAction("🗑️  Supprimer", self)
            
            act_preview.triggered.connect(lambda: self.preview_employee(employee.id))
            act_edit.triggered.connect(self.edit_employee)
            act_delete.triggered.connect(self.delete_employee)
            
            menu.addAction(act_preview)
            menu.addAction(act_edit)
            menu.addAction(act_delete)
            menu.addSeparator()
            
            # ============ DOCUMENTS DE PAIE ============
            act_payslip = QAction("🧾  Générer fiche de paie", self)
            act_payslip.triggered.connect(lambda: self.generate_payslip(employee.id))
            menu.addAction(act_payslip)
            
            # ============ CERTIFICATS DE TRAVAIL ============
            act_attestation = QAction("📄  Attestation de travail", self)
            act_certificat_travail = QAction("📄  Certificat de travail", self)
            
            act_attestation.triggered.connect(lambda: self.generate_attestation(employee.id))
            act_certificat_travail.triggered.connect(lambda: self.generate_certificat_travail(employee.id))
            
            menu.addAction(act_attestation)
            menu.addAction(act_certificat_travail)
            
            # ============ NOUVEAU : ATTESTATION CNAS AS-08 ============
            # Placé JUSTE EN DESSOUS du certificat de travail
            if employee.est_actif:
                act_cnas_as08 = QAction("🏥  CNAS - Attestation AS-08 (travail et salaire)", self)
                act_cnas_as08.setIcon(QIcon("assets/icons/cnas.png"))  # Optionnel
                act_cnas_as08.setToolTip("Formulaire officiel CNAS pour prestations sociales (maladie, maternité, etc.)")
                act_cnas_as08.triggered.connect(lambda: self.generate_attestation_cnas_pdf(employee.id))
                menu.addAction(act_cnas_as08)
            else:
                act_cnas_inactif = QAction("🏥  CNAS - Attestation (indisponible - employé inactif)", self)
                act_cnas_inactif.setEnabled(False)
                menu.addAction(act_cnas_inactif)

            menu.addSeparator()
            
            # ============ ACTIONS DE STATUT ============
            if employee.est_actif:
                act_deactivate = QAction("⛔  Désactiver l'employé", self)
                act_deactivate.triggered.connect(lambda: self.toggle_employee_status(employee.id, False))
                menu.addAction(act_deactivate)
            else:
                act_activate = QAction("✅  Réactiver l'employé", self)
                act_activate.triggered.connect(lambda: self.toggle_employee_status(employee.id, True))
                menu.addAction(act_activate)

            # ============ INFORMATIONS COMPLÉMENTAIRES ============            menu.addSeparator()
            info_menu = menu.addMenu("ℹ️  Informations")
            info_menu.addAction(f"📋  Matricule: {employee.code_employe}")
            info_menu.addAction(f"👤  {employee.genre} {employee.nom} {employee.prenom}")
            if employee.poste:
                info_menu.addAction(f"💼  Poste: {employee.poste}")
            if employee.date_embauche:
                info_menu.addAction(f"📅  Embauché le: {employee.date_embauche.strftime('%d/%m/%Y')}")
            if employee.numero_secu:
                info_menu.addAction(f"🏥  CNAS: {employee.numero_secu}")

            global_pos = self.table_employees.viewport().mapToGlobal(pos)
            menu.exec(global_pos)
            
    
    

    
    
    def generate_attestation_cnas_pdf(self, employee_id: int):
        """Génère l'attestation CNAS AS-08 au format PDF officiel"""

        from PyQt6.QtWidgets import QMessageBox, QFileDialog
        from services.attestation_cnas_pdf import AttestationCNASPDFGenerator
        from pathlib import Path
        from datetime import datetime

        with get_session() as session:

            employee = session.query(Employee).filter(
                Employee.id == employee_id
            ).first()

            if not employee:
                QMessageBox.warning(self, "Erreur", "Employé non trouvé")
                return

            # ==============================
            # Choisir emplacement sauvegarde
            # ==============================
            desktop = Path.home() / "Desktop"
            filename = f"AS-08_{employee.nom}_{employee.prenom}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            default_path = str(desktop / filename)

            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer l'attestation CNAS",
                default_path,
                "PDF Files (*.pdf)"
            )

            if not output_path:
                return

            # ==============================
            # Génération PDF
            # ==============================
            generator = AttestationCNASPDFGenerator()

            try:
                generator.generate(employee_id, output_path)

                QMessageBox.information(
                    self,
                    "Succès",
                    f"Attestation CNAS générée avec succès !\n\n{output_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Erreur lors de la génération :\n{str(e)}"
                )


    
    
    
    def toggle_employee_status(self, employee_id: int, activate: bool):
        """
        Active ou désactive un employé
        """
        try:
            with get_session() as session:
                employee = session.query(Employee).filter(Employee.id == employee_id).first()
                if not employee:
                    QMessageBox.warning(self, "Erreur", "Employé non trouvé")
                    return

                employee.est_actif = activate
                session.commit()

            status = "activé" if activate else "désactivé"
            QMessageBox.information(
                self,
                "Statut modifié",
                f"✅ Employé {employee.genre} {employee.nom} {employee.prenom} {status} avec succès."
            )
            self.load_employees()

        except Exception as e:
            try:
                with get_session() as session:
                    session.rollback()
            except Exception:
                pass
            QMessageBox.critical(self, "Erreur", f"Erreur lors du changement de statut: {str(e)}")

    
    def preview_employee(self, employee_id: int):
        """Aperçu en lecture seule"""
        print(f"👁️ Aperçu de l'employé ID: {employee_id}")
        dialog = EmployeeDialog(employee_id=employee_id, parent=self, read_only=True)
        dialog.exec()
    
    def generate_payslip(self, employee_id: int):
        """Génère une fiche de paie"""
        print(f"🧾 Génération fiche de paie pour employé ID: {employee_id}")
        dialog = ModernPayslipDialog(employee_id=employee_id, parent=self)
        dialog.payslip_saved.connect(self.load_employees)
        dialog.exec()

    def generate_attestation(self, employee_id, attestation_type="Attestation de travail"):
        """Génère une attestation pour l'employé"""
        try:
            # Vérifier si le service est initialisé
            if not hasattr(self, 'attestation_service') or self.attestation_service is None:
                self.attestation_service = AttestationPDFService()

            with get_session() as session:
                employee = session.query(Employee).filter(Employee.id == employee_id).first()
                if not employee:
                    QMessageBox.warning(self, "Erreur", "Employé non trouvé")
                    return

                # Préparer les données de l'employé
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

            # Ouvrir le PDF généré
            self.open_pdf(file_path)

            # Afficher un message de confirmation
            QMessageBox.information(
                self,
                "Attestation générée",
                f"Attestation de travail générée avec succès:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de la génération de l'attestation:\n{str(e)}"
            )
    
    def open_pdf(self, file_path):
        """Ouvre le fichier PDF avec l'application par défaut"""
        try:
            if os.path.exists(file_path):
                if os.name == 'nt':  # Windows
                    os.startfile(file_path)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.call(['open', file_path])
                else:  # Linux
                    subprocess.call(['xdg-open', file_path])
        except Exception as e:
            logger.error("Erreur lors de l'ouverture du PDF: %s", e)

    def generate_certificat_travail(self, employee_id):
        """
        Génère un certificat de travail pour l'employé
        UNIQUEMENT POUR EMPLOYÉS INACTIFS
        """
        try:
            with get_session() as session:
                employee = session.query(Employee).filter(Employee.id == employee_id).first()
            
                if not employee:
                    QMessageBox.critical(
                        self,
                        "Erreur",
                        "Employé non trouvé dans la base de données."
                    )
                    return
            
                # 🔴 VÉRIFICATION 1: Employé actif
                if employee.est_actif:
                    QMessageBox.critical(
                        self,
                        "Génération impossible - Employé actif",
                        f"⚠️ CERTIFICAT NON GÉNÉRÉ ⚠️\n\n"
                        f"L'employé {employee.nom_complet} est actuellement ACTIF.\n\n"
                        f"❌ Un certificat de travail ne peut être délivré qu'à un employé qui a quitté l'entreprise.\n\n"
                        f"📌 Procédure à suivre:\n"
                        f"1. Modifier l'employé\n"
                        f"2. Changer son statut en 'Inactif'\n"
                        f"3. Renseigner sa date d'arrêt\n"
                        f"4. Réessayer la génération du certificat"
                    )
                    return
            
                # 🔴 VÉRIFICATION 2: Date d'arrêt manquante
                if not employee.date_arret:
                    QMessageBox.critical(
                        self,
                        "Génération impossible - Date d'arrêt manquante",
                        f"⚠️ CERTIFICAT NON GÉNÉRÉ ⚠️\n\n"
                        f"L'employé {employee.nom_complet} est inactif mais n'a PAS de date d'arrêt.\n\n"
                        f"📌 Procédure à suivre:\n"
                        f"1. Modifier l'employé\n"
                        f"2. Renseigner la date d'arrêt\n"
                        f"3. Réessayer la génération du certificat"
                    )
                    return
            
                # ✅ Tout est bon, générer le certificat
                try:
                    file_path = self.certificat_service.generate_certificat_travail(
                        employee_id=employee_id
                    )

                    # Ouvrir le PDF
                    self.open_pdf(file_path)

                    QMessageBox.information(
                        self,
                        "✅ Certificat généré avec succès",
                        f"Le certificat de travail a été généré avec succès :\n\n"
                        f"📄 {os.path.basename(file_path)}\n"
                        f"📁 Emplacement : {os.path.dirname(file_path)}\n\n"
                        f"👤 Employé : {employee.nom_complet}\n"
                        f"📅 Période : du {self._format_date_display(employee.date_embauche)} au {self._format_date_display(employee.date_arret)}\n"
                        f"📝 Motif : {employee.raison_arret or 'Non spécifié'}"
                    )

                except ValueError as e:
                    QMessageBox.critical(
                        self,
                        "Erreur de génération",
                        str(e)
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Erreur technique",
                        f"Une erreur est survenue lors de la génération du certificat:\n\n{str(e)}"
                    )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur inattendue : {str(e)}"
            )




    def _format_date_display(self, date_obj):
        """Formate une date pour l'affichage"""
        if not date_obj:
            return "N/A"
        try:
            if hasattr(date_obj, 'strftime'):
                return date_obj.strftime("%d/%m/%Y")
            return str(date_obj)
        except:
            return str(date_obj)


    def generate_certificat_fin_contrat(self, employee_id):
        """Génère un certificat de fin de contrat pour un employé inactif."""
        try:
            with get_session() as session:
                employee = session.query(Employee).filter(Employee.id == employee_id).first()
                if not employee:
                    QMessageBox.critical(self, "Erreur", "Employé non trouvé")
                    return

                if employee.est_actif:
                    QMessageBox.critical(
                        self,
                        "Génération impossible - Employé actif",
                        f"L'employé {employee.nom_complet} est actif. Impossible de générer le certificat."
                    )
                    return

                if not employee.date_arret:
                    QMessageBox.critical(
                        self,
                        "Génération impossible - Date d'arrêt manquante",
                        "L'employé n'a pas de date d'arrêt."
                    )
                    return

            file_path = self.certificat_service.generate_certificat_fin_contrat(employee_id=employee_id)
            self.open_pdf(file_path)
            QMessageBox.information(
                self,
                "✅ Certificat généré",
                f"Certificat de fin de contrat généré avec succès : {file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération : {e}")
