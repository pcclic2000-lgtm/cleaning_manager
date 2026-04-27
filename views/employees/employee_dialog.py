# views/employees/employee_dialog.py
"""Formulaire de création / modification d'un employé."""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QLineEdit, QLabel, QFormLayout, QComboBox,
    QTextEdit, QDateEdit, QHeaderView, QAbstractItemView,
    QMenu, QSpinBox, QDoubleSpinBox, QGroupBox, QGridLayout,
    QCheckBox, QScrollArea, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QPoint
from PyQt6.QtGui import QAction, QFont, QIcon, QColor
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from database.db import SessionLocal, get_session
from models.employee import Employee

logger = logging.getLogger(__name__)

class EmployeeDialog(QDialog):
    """Dialogue complet pour créer/modifier un employé."""
    
    employee_saved = pyqtSignal(int)  # UNIQUEMENT ICI, avec paramètre int (employee_id)
    
    def __init__(self, employee_id=None, parent=None, read_only: bool = False):
        super().__init__(parent)
        self.employee_id = employee_id
        self.read_only = read_only
        
        self.setWindowTitle("Modifier employé" if employee_id and not read_only else
                            "Aperçu employé" if employee_id and read_only else "Nouvel employé")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(700)
        
        self.init_ui()
        if employee_id:
            self.load_employee_data()
        
        if self.read_only:
            self.make_read_only()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ===== STYLE GLOBAL PREMIUM =====
        self.setStyleSheet("""
        QWidget {
            background-color: #f4f7fa;
            font-family: 'Segoe UI';
        }

        QGroupBox {
            background-color: white;
            border: 1px solid #e3e8ee;
            border-radius: 14px;
            margin-top: 15px;
            padding: 20px;
            font-size: 15px;
            font-weight: 600;
            color: #2c3e50;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 20px;
            padding: 0 6px;
            background-color: #f4f7fa;
        }

        QLabel {
            font-size: 13px;
            color: #34495e;
            min-height: 24px;
        }

        QLineEdit, QDateEdit, QComboBox, QDoubleSpinBox {
            border: 1px solid #dcdde1;
            border-radius: 10px;
            padding: 6px 10px;
            min-height: 32px;
            font-size: 13px;
            background-color: white;
        }

        QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
            border: 2px solid #27ae60;
        }

        QTextEdit {
            border: 1px solid #dcdde1;
            border-radius: 10px;
            padding: 8px;
            min-height: 80px;
            font-size: 13px;
            background-color: white;
        }

        QScrollArea {
            border: none;
        }
        """)

        # ===== SCROLL AREA =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(20)

        # ===== SHADOW FUNCTION =====
        def add_shadow(widget):
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(25)
            shadow.setOffset(0, 5)
            shadow.setColor(QColor(0, 0, 0, 40))
            widget.setGraphicsEffect(shadow)

        # ======================================================
        # 📋 INFORMATIONS PERSONNELLES
        # ======================================================
        personal_group = QGroupBox("📋 Informations personnelles")
        personal_layout = QGridLayout()
        personal_layout.setSpacing(12)

        personal_layout.addWidget(QLabel("Nom*:"), 0, 0)
        self.txt_nom = QLineEdit()
        personal_layout.addWidget(self.txt_nom, 0, 1)

        personal_layout.addWidget(QLabel("Prénom*:"), 0, 2)
        self.txt_prenom = QLineEdit()
        personal_layout.addWidget(self.txt_prenom, 0, 3)

        personal_layout.addWidget(QLabel("Date de naissance:"), 1, 0)
        self.date_naissance = QDateEdit()
        self.date_naissance.setDate(QDate(1990, 1, 1))
        self.date_naissance.setCalendarPopup(True)
        self.date_naissance.setMaximumDate(QDate.currentDate())
        self.date_naissance.setDisplayFormat("dd/MM/yyyy")
        personal_layout.addWidget(self.date_naissance, 1, 1)

        personal_layout.addWidget(QLabel("Situation familiale:"), 1, 2)
        self.cmb_situation = QComboBox()
        self.cmb_situation.addItems(["Célibataire", "Marié(e)", "Divorcé(e)", "Veuf(ve)"])
        personal_layout.addWidget(self.cmb_situation, 1, 3)

        personal_layout.addWidget(QLabel("N° Sécurité Sociale:"), 2, 0)
        self.txt_numero_secu = QLineEdit()
        personal_layout.addWidget(self.txt_numero_secu, 2, 1, 1, 3)

        personal_layout.addWidget(QLabel("Genre:"), 3, 0)
        self.cmb_genre = QComboBox()
        self.cmb_genre.addItems(["M.", "Mme"])
        personal_layout.addWidget(self.cmb_genre, 3, 1)

        personal_layout.addWidget(QLabel("Nationalité:"), 3, 2)
        self.txt_nationalite = QLineEdit()
        self.txt_nationalite.setPlaceholderText("Algérienne")
        personal_layout.addWidget(self.txt_nationalite, 3, 3)

        personal_layout.setColumnStretch(1, 1)
        personal_layout.setColumnStretch(3, 1)

        personal_group.setLayout(personal_layout)
        add_shadow(personal_group)
        scroll_layout.addWidget(personal_group)

        # ======================================================
        # 💼 INFORMATIONS PROFESSIONNELLES
        # ======================================================
        professional_group = QGroupBox("💼 Informations professionnelles")
        professional_layout = QGridLayout()
        professional_layout.setSpacing(12)

        professional_layout.addWidget(QLabel("Poste:"), 0, 0)
        self.txt_poste = QLineEdit()
        professional_layout.addWidget(self.txt_poste, 0, 1, 1, 3)

        professional_layout.addWidget(QLabel("Date d'embauche*:"), 1, 0)
        self.date_embauche = QDateEdit()
        self.date_embauche.setDate(QDate.currentDate())
        self.date_embauche.setCalendarPopup(True)
        self.date_embauche.setDisplayFormat("dd/MM/yyyy")
        professional_layout.addWidget(self.date_embauche, 1, 1)

        professional_layout.addWidget(QLabel("Salaire (DA):"), 1, 2)
        self.spin_salaire = QDoubleSpinBox()
        self.spin_salaire.setDecimals(2)
        self.spin_salaire.setRange(0, 1000000)
        self.spin_salaire.setSuffix(" DA")
        professional_layout.addWidget(self.spin_salaire, 1, 3)

        professional_layout.setColumnStretch(1, 1)
        professional_layout.setColumnStretch(3, 1)

        professional_group.setLayout(professional_layout)
        add_shadow(professional_group)
        scroll_layout.addWidget(professional_group)

        # ======================================================
        # 📞 COORDONNÉES
        # ======================================================
        contact_group = QGroupBox("📞 Coordonnées")
        contact_layout = QGridLayout()
        contact_layout.setSpacing(12)

        contact_layout.addWidget(QLabel("Téléphone*:"), 0, 0)
        self.txt_telephone = QLineEdit()
        contact_layout.addWidget(self.txt_telephone, 0, 1, 1, 3)

        contact_layout.addWidget(QLabel("Adresse:"), 1, 0)
        self.txt_adresse = QTextEdit()
        contact_layout.addWidget(self.txt_adresse, 1, 1, 1, 3)

        contact_layout.setColumnStretch(1, 1)

        contact_group.setLayout(contact_layout)
        add_shadow(contact_group)
        scroll_layout.addWidget(contact_group)

        # ======================================================
        # 📊 AUTRES INFORMATIONS
        # ======================================================
        other_group = QGroupBox("📊 Autres informations")
        other_layout = QGridLayout()
        other_layout.setSpacing(10)

        # Ligne 1 - Statut
        other_layout.addWidget(QLabel("Statut:"), 0, 0)
        self.cmb_est_actif = QComboBox()
        self.cmb_est_actif.addItems(["Actif", "Inactif"])
        self.cmb_est_actif.setMinimumWidth(150)
        self.cmb_est_actif.currentIndexChanged.connect(self.on_status_changed) 
        other_layout.addWidget(self.cmb_est_actif, 0, 1, 1, 2)

        # Ligne 2 - Date d'arrêt
        other_layout.addWidget(QLabel("Date d'arrêt:"), 1, 0)
        self.date_arret = QDateEdit()
        self.date_arret.setDate(QDate.currentDate())
        self.date_arret.setCalendarPopup(True)
        self.date_arret.setDisplayFormat("dd/MM/yyyy")
        self.date_arret.setEnabled(False)  # Désactivé par défaut
        other_layout.addWidget(self.date_arret, 1, 1, 1, 2)

        # Ligne 3 - Raison d'arrêt
        other_layout.addWidget(QLabel("Raison:"), 1, 3)
        self.cmb_raison_arret = QComboBox()
        self.cmb_raison_arret.addItems([
            "Fin de contrat",
            "Démission",
            "Licenciement",
            "Retraite",
            "Arrêt maladie prolongé",
            "Autre raison"
        ])
        self.cmb_raison_arret.setEnabled(False)  # Désactivé par défaut
        self.cmb_raison_arret.setMinimumWidth(200)
        other_layout.addWidget(self.cmb_raison_arret, 1, 4, 1, 2)

        other_group.setLayout(other_layout)
        scroll_layout.addWidget(other_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # ======================================================
        # 🔘 BOUTONS
        # ======================================================
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        self.btn_save = QPushButton("💾 Enregistrer")
        self.btn_save.setStyleSheet("""
        QPushButton {
            background-color: #27ae60;
            color: white;
            border-radius: 10px;
            padding: 10px 28px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #219653;
        }
        """)
        self.btn_save.clicked.connect(self.save_employee)

        btn_cancel = QPushButton("❌ Annuler")
        btn_cancel.setStyleSheet("""
        QPushButton {
            background-color: #e74c3c;
            color: white;
            border-radius: 10px;
            padding: 10px 28px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #c0392b;
        }
        """)
        btn_cancel.clicked.connect(self.reject)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_save)
        buttons_layout.addWidget(btn_cancel)

        main_layout.addLayout(buttons_layout)

    def make_read_only(self):
        """Met le dialogue en lecture seule"""
        try:
            self.btn_save.hide()
        except Exception:
            pass
        
        # Liste de tous les widgets à rendre en lecture seule
        widgets = [
            self.txt_nom, self.txt_prenom, self.txt_poste, 
            self.txt_telephone, self.txt_numero_secu
        ]
        
        for widget in widgets:
            widget.setReadOnly(True)
        
        self.txt_adresse.setReadOnly(True)
        self.date_naissance.setEnabled(False)
        self.date_embauche.setEnabled(False)
        self.spin_salaire.setEnabled(False)
        self.cmb_situation.setEnabled(False)
        self.cmb_genre.setEnabled(False)
        self.txt_nationalite.setEnabled(False)
        self.cmb_est_actif.setEnabled(False)
        self.date_arret.setEnabled(False)
        self.cmb_raison_arret.setEnabled(False)

    def on_status_changed(self, index):
        """
        Active/désactive les champs de date d'arrêt et raison selon le statut
        """
        is_inactive = (index == 1)  # 0 = Actif, 1 = Inactif
        
        # Activer/désactiver les champs
        self.date_arret.setEnabled(is_inactive)
        self.cmb_raison_arret.setEnabled(is_inactive)
        
        if is_inactive:
            # Si on passe en inactif, mettre la date du jour par défaut
            self.date_arret.setDate(QDate.currentDate())
            self.date_arret.setStyleSheet("""
                QDateEdit {
                    background-color: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 4px;
                    padding: 5px;
                }
            """)
            self.cmb_raison_arret.setStyleSheet("""
                QComboBox {
                    background-color: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 4px;
                    padding: 5px;
                }
            """)
        else:
            # Si on repasse en actif, réinitialiser le style
            self.date_arret.setStyleSheet("")
            self.cmb_raison_arret.setStyleSheet("")
    
    def load_employee_data(self):
        """Charge les données de l'employé avec tous les champs"""
        if not self.employee_id:
            return
        
        print(f"🔍 Chargement des données pour l'employé ID: {self.employee_id}")
        
        try:
            with get_session() as session:
                employee = session.query(Employee).filter(
                    Employee.id == self.employee_id
                ).first()
                
                if employee:
                    logger.info(f"✅ Employé trouvé: {employee.nom_complet}")
                    print(f"   Poste: {employee.poste}")
                    print(f"   Date naissance: {employee.date_naissance}")
                    print(f"   Situation familiale: {employee.situation_familiale}")
                    print(f"   Numéro sécu: {employee.numero_secu}")
                    
                    # Informations personnelles
                    self.txt_nom.setText(employee.nom or "")
                    self.txt_prenom.setText(employee.prenom or "")
                    self.txt_poste.setText(employee.poste or "")
                    
                    # Date de naissance
                    if employee.date_naissance:
                        try:
                            self.date_naissance.setDate(QDate(
                                employee.date_naissance.year,
                                employee.date_naissance.month,
                                employee.date_naissance.day
                            ))
                            print(f"   Date naissance chargée: {employee.date_naissance}")
                        except Exception as e:
                            print(f"   ❌ Erreur chargement date naissance: {e}")
                            self.date_naissance.setDate(QDate(1990, 1, 1))
                    
                    # Situation familiale
                    if employee.situation_familiale:
                        index = self.cmb_situation.findText(employee.situation_familiale)
                        if index >= 0:
                            self.cmb_situation.setCurrentIndex(index)
                            print(f"   Situation familiale chargée: {employee.situation_familiale}")
                        else:
                            self.cmb_situation.setCurrentIndex(0)
                    else:
                        self.cmb_situation.setCurrentIndex(0)
                    
                    # Numéro sécurité sociale
                    self.txt_numero_secu.setText(employee.numero_secu or "")
                    print(f"   Numéro sécu chargé: {employee.numero_secu}")
                    
                    # Informations professionnelles
                    if employee.date_embauche:
                        try:
                            self.date_embauche.setDate(QDate(
                                employee.date_embauche.year,
                                employee.date_embauche.month,
                                employee.date_embauche.day
                            ))
                        except Exception as e:
                            print(f"   ❌ Erreur chargement date embauche: {e}")
                            self.date_embauche.setDate(QDate.currentDate())
                    
                    # Salaire
                    try:
                        salaire_value = float(employee.salaire or 0.0)
                        self.spin_salaire.setValue(salaire_value)
                        print(f"   Salaire chargé: {salaire_value}")
                    except Exception as e:
                        print(f"   ❌ Erreur chargement salaire: {e}")
                        self.spin_salaire.setValue(0.0)
                    
                    # Coordonnées
                    self.txt_telephone.setText(employee.telephone or "")
                    self.txt_adresse.setText(employee.adresse or "")
                    
                    # Statut
                    index = 0 if employee.est_actif else 1
                    self.cmb_est_actif.setCurrentIndex(index)
                    
                    # Date d'arrêt
                    if employee.date_arret:
                        try:
                            self.date_arret.setDate(QDate(
                                employee.date_arret.year,
                                employee.date_arret.month,
                                employee.date_arret.day
                            ))
                            print(f"   Date d'arrêt chargée: {employee.date_arret}")
                        except Exception as e:
                            print(f"   ❌ Erreur chargement date arrêt: {e}")
                            self.date_arret.setDate(QDate.currentDate())

                    # Raison d'arrêt
                    if employee.raison_arret:
                        index = self.cmb_raison_arret.findText(employee.raison_arret)
                        if index >= 0:
                            self.cmb_raison_arret.setCurrentIndex(index)
                        else:
                            self.cmb_raison_arret.setEditText(employee.raison_arret)
                    
                    # Activer/désactiver les champs selon le statut
                    self.on_status_changed(index)
                    
                    logger.info("✅ Toutes les données chargées avec succès!")
                else:
                    logger.info(f"❌ Aucun employé trouvé avec ID: {self.employee_id}")
                    QMessageBox.warning(self, "Erreur", "Employé non trouvé")
        except Exception as e:
            logger.info(f"❌ Erreur lors du chargement: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")

    def save_employee(self):
        """Enregistre l'employé avec tous les champs"""
        if self.read_only:
            self.accept()
            return
        
        logger.info("💾 Début de l'enregistrement de l'employé...")
        
        # Validation des champs obligatoires
        errors = []
        
        if not self.txt_nom.text().strip():
            errors.append("Le nom est obligatoire")
        
        if not self.txt_prenom.text().strip():
            errors.append("Le prénom est obligatoire")
        
        if not self.txt_telephone.text().strip():
            errors.append("Le téléphone est obligatoire")
        
        # Validation conditionnelle pour les employés inactifs
        is_inactive = (self.cmb_est_actif.currentIndex() == 1)
        if is_inactive:
            if not self.date_arret.date().isValid():
                errors.append("La date d'arrêt est obligatoire pour un employé inactif")
            if not self.cmb_raison_arret.currentText().strip():
                errors.append("La raison d'arrêt est obligatoire pour un employé inactif")
        
        if errors:
            QMessageBox.warning(self, "Erreur de validation", "\n".join(errors))
            return
        
        try:
            with get_session() as session:
                employee = None
                old_status = None
                
                if self.employee_id:
                    # MODIFICATION
                    logger.info(f"🔄 Modification de l'employé ID: {self.employee_id}")
                    employee = session.query(Employee).filter(
                        Employee.id == self.employee_id
                    ).first()
                    
                    if not employee:
                        QMessageBox.critical(self, "Erreur", "Employé non trouvé")
                        return
                    
                    # Sauvegarder l'ancien statut
                    old_status = employee.est_actif
                    new_status = not is_inactive  # True = Actif, False = Inactif
                    
                    logger.info(f"📊 Statut: Ancien={old_status}, Nouveau={new_status}")
                    
                    # Si passage en inactif, on garde la date et raison
                    if old_status and not new_status:
                        logger.info("🔄 Passage d'actif à inactif détecté")
                        # Les champs sont déjà remplis
                        
                    # Si passage en actif, on efface date et raison
                    elif not old_status and new_status:
                        logger.info("🔄 Passage d'inactif à actif détecté")
                        reply = QMessageBox.question(
                            self, "Réactivation d'employé",
                            f"Êtes-vous sûr de vouloir réactiver {employee.prenom} {employee.nom} ?\n"
                            f"Date d'arrêt précédente: {employee.date_arret}\n"
                            f"Raison: {employee.raison_arret or 'Non spécifiée'}",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        
                        if reply == QMessageBox.StandardButton.Yes:
                            employee.date_arret = None
                            employee.raison_arret = None
                            logger.info("✅ Employé réactivé - date et raison d'arrêt effacées")
                        else:
                            logger.info("❌ Annulation de la réactivation")
                            self.cmb_est_actif.setCurrentIndex(1)  # Inactif
                            return
                    
                    employee.est_actif = new_status
                    
                else:
                    # CRÉATION
                    print("🆕 Création d'un nouvel employé")
                    employee = Employee()
                    session.add(employee)
                    
                    # Générer le matricule
                    total_employees = session.query(Employee).count()
                    matricule = f"EMP-{datetime.now().strftime('%Y%m')}-{total_employees + 1:03d}"
                    employee.code_employe = matricule
                    print(f"📝 Matricule généré: {matricule}")
                    
                    employee.est_actif = not is_inactive
                
                # ===== MISE À JOUR DES CHAMPS COMMUNS =====
                # Informations personnelles
                employee.nom = self.txt_nom.text().strip()
                employee.prenom = self.txt_prenom.text().strip()
                employee.poste = self.txt_poste.text().strip() or None
                
                # Date de naissance
                birth_date = self.date_naissance.date().toPyDate()
                employee.date_naissance = birth_date if birth_date.year > 1900 else None
                
                # Situation familiale
                employee.situation_familiale = self.cmb_situation.currentText()
                
                # Genre
                if hasattr(employee, 'genre'):
                    employee.genre = 'F' if self.cmb_genre.currentText() == 'Mme' else 'M'
                
                # Nationalité
                if hasattr(employee, 'nationalite'):
                    employee.nationalite = self.txt_nationalite.text().strip() or None
                
                # Numéro sécurité sociale
                secu = self.txt_numero_secu.text().strip()
                employee.numero_secu = secu if secu else None
                
                # Informations professionnelles
                employee.date_embauche = self.date_embauche.date().toPyDate()
                employee.salaire = float(self.spin_salaire.value() or 0.0)
                
                # Coordonnées
                employee.telephone = self.txt_telephone.text().strip()
                employee.adresse = self.txt_adresse.toPlainText().strip() or None
                
                # ===== DATE ET RAISON D'ARRÊT =====
                if is_inactive:
                    employee.date_arret = self.date_arret.date().toPyDate()
                    employee.raison_arret = self.cmb_raison_arret.currentText()
                else:
                    employee.date_arret = None
                    employee.raison_arret = None
                
                logger.info("✅ Tous les champs mis à jour, tentative de commit...")
                
                session.commit()
                logger.info("✅ Commit réussi!")
                
                QMessageBox.information(self, "Succès",
                                    f"{'Employé modifié' if self.employee_id else 'Employé créé'} avec succès!\nMatricule: {employee.code_employe}")
                
                # Émettre le signal avec l'ID de l'employé
                self.employee_saved.emit(employee.id)
                self.accept()
                
        except Exception as e:
            logger.info(f"❌ Erreur lors de l'enregistrement: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur", 
                            f"Erreur lors de l'enregistrement:\n{str(e)}\n\nVeuillez vérifier tous les champs.")

    def update_related_data(self, employee_id):
        """Met à jour toutes les données liées à l'employé"""
        logger.info(f"🔄 Mise à jour des données liées pour l'employé {employee_id}")
        
        try:
            # 1. Mettre à jour les tâches affectées
            self.update_tasks_status(employee_id)
            
            # 2. Mettre à jour les affectations
            self.update_assignments(employee_id)
            
            # 3. Mettre à jour les feuilles de paie
            self.update_payslips(employee_id)
            
            # 4. Mettre à jour les statistiques
            self.update_statistics()
            
            logger.info("✅ Toutes les données liées ont été mises à jour")
            
        except Exception as e:
            logger.info(f"⚠️  Erreur lors de la mise à jour des données liées: {e}")

    def update_tasks_status(self, employee_id):
        """Met à jour le statut des tâches de l'employé"""
        from models.tache import Tache
        
        try:
            with get_session() as session:
                # Récupérer l'employé
                employee = session.query(Employee).filter(Employee.id == employee_id).first()
                if not employee:
                    return
                
                if not employee.est_actif:
                    # Mettre en pause toutes les tâches actives de l'employé
                    active_tasks = session.query(Tache).filter(
                        Tache.employee_id == employee_id,
                        Tache.est_terminee == False,
                        Tache.en_pause == False
                    ).all()
                    raison = employee.raison_arret or "Statut inactif"
                    for task in active_tasks:
                        task.en_pause = True
                        task.date_pause = date.today()
                        task.raison_pause = f"Employé désactivé : {raison}"
                        print(f"   ⏸️ Tâche '{task.titre}' mise en pause")
                        
                    if active_tasks:
                        session.commit()
                        print(f"   ✅ {len(active_tasks)} tâche(s) mise(s) en pause")
                else:
                    # Réactiver les tâches mises en pause pour cette raison
                    paused_tasks = session.query(Tache).filter(
                        Tache.employee_id == employee_id,
                        Tache.en_pause == True,
                        Tache.raison_pause.like(f"%Employé {employee.nom_complet} désactivé%")
                    ).all()
                        
                    for task in paused_tasks:
                        task.en_pause = False
                        task.date_reprise = date.today()
                        print(f"   ▶️ Tâche '{task.titre}' reprise")
                        
                    if paused_tasks:
                        session.commit()
                        print(f"   ✅ {len(paused_tasks)} tâche(s) reprise(s)")
        except Exception as e:
            logger.info(f"❌ Erreur lors de la mise à jour des tâches: {e}")

    def update_assignments(self, employee_id):
        """Met à jour les affectations de l'employé"""
        from models.affectation import Affectation
        
        try:
            with get_session() as session:
                employee = session.query(Employee).filter(Employee.id == employee_id).first()
                if not employee:
                    return
                
                # Récupérer toutes les affectations actives
                active_assignments = session.query(Affectation).filter(
                    Affectation.employee_id == employee_id,
                    Affectation.date_fin == None  # Affectations en cours
                ).all()
                
                if not employee.est_actif and active_assignments:
                    # Terminer les affectations en cours
                    for assignment in active_assignments:
                        assignment.date_fin = employee.date_arret or date.today()
                        assignment.raison_fin = f"Employé désactivé: {employee.raison_arret}"
                        print(f"   📝 Affectation #{assignment.id} terminée")
                        
                    session.commit()
                    print(f"   ✅ {len(active_assignments)} affectation(s) terminée(s)")
        except Exception as e:
            logger.info(f"❌ Erreur lors de la mise à jour des affectations: {e}")

    def update_payslips(self, employee_id):
        """Met à jour les fiches de paie"""
        from models.payslip import Payslip
        
        try:
            with get_session() as session:
                employee = session.query(Employee).filter(Employee.id == employee_id).first()
                if not employee:
                    return
                
                if not employee.est_actif:
                    # Marquer la dernière fiche de paie comme "dernière"
                    last_payslip = session.query(Payslip).filter(
                        Payslip.employee_id == employee_id
                    ).order_by(Payslip.date_paiement.desc()).first()
                        
                    if last_payslip:
                        last_payslip.est_derniere = True
                        session.commit()
                        print(f"   💰 Dernière fiche de paie marquée: {last_payslip.mois}/{last_payslip.annee}")
        except Exception as e:
            logger.info(f"❌ Erreur lors de la mise à jour des fiches de paie: {e}")

    def update_statistics(self):
        """Met à jour les statistiques globales"""
        try:
            with get_session() as session:
                # Calculer les nouvelles statistiques
                total_employees = session.query(Employee).count()
                active_employees = session.query(Employee).filter(Employee.est_actif == True).count()
                inactive_employees = session.query(Employee).filter(Employee.est_actif == False).count()
                
                logger.info(f"📊 Statistiques mises à jour:")
                print(f"   Total employés: {total_employees}")
                print(f"   Employés actifs: {active_employees}")
                print(f"   Employés inactifs: {inactive_employees}")
                
                # Émettre un signal pour mettre à jour d'autres vues
                if hasattr(self.parent(), 'update_dashboard'):
                    self.parent().update_dashboard()
        except Exception as e:
            logger.info(f"❌ Erreur lors de la mise à jour des statistiques: {e}")