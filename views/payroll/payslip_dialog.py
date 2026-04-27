"""
Dialogue moderne pour créer/modifier une fiche de paie
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFormLayout, QComboBox, QLineEdit,
    QTextEdit, QDateEdit, QDoubleSpinBox, QSpinBox,
    QGroupBox, QTabWidget, QScrollArea, QWidget,
    QMessageBox, QProgressBar, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTimer
from PyQt6.QtGui import QFont, QIcon

import os
from datetime import datetime
from decimal import Decimal

from database.db import SessionLocal, get_session
from models.employee import Employee
from models.payslip import Payslip
from services.payslip_calculator import PayslipCalculator
from services.payslip_builder import PayslipBuilder
from services.payslip_pdf_service import PayslipPDFService
import ui.app_theme as Theme


class ModernPayslipDialog(QDialog):
    """Dialogue moderne pour créer/modifier une fiche de paie"""
    
    payslip_saved = pyqtSignal()
    calculation_completed = pyqtSignal(dict)
    
    def __init__(self, employee_id=None, payslip_id=None, parent=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.payslip_id = payslip_id
        self.employee = None
        self.calculator = PayslipCalculator()
        self.pdf_service = PayslipPDFService()
        
        self.setWindowTitle("Modifier fiche de paie" if payslip_id else "Nouvelle fiche de paie")
        self.setModal(True)
        self.setMinimumSize(1000, 800)
        
        # Appliquer le thème
        Theme.AppTheme.apply_global_style(self)
        
        self.init_ui()
        self.setup_connections()
        self.load_data()
        
        # Démarrer le calcul initial
        QTimer.singleShot(100, self.calculate_totals)
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # En-tête avec gradient
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Splitter pour une meilleure organisation
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panneau gauche - Formulaire
        left_panel = self.create_form_panel()
        splitter.addWidget(left_panel)
        
        # Panneau droit - Aperçu et résumé
        right_panel = self.create_preview_panel()
        splitter.addWidget(right_panel)
        
        # Définir les proportions
        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter)
        
        # Barre de progression (cachée par défaut)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Barre d'état
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Prêt")
        self.status_label.setStyleSheet(Theme.AppTheme.get_label_style("info"))
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        last_calc_label = QLabel("Dernier calcul: --:--:--")
        last_calc_label.setStyleSheet(Theme.AppTheme.get_label_style("normal"))
        status_layout.addWidget(last_calc_label)
        
        main_layout.addLayout(status_layout)
        
        # Boutons d'action (sans bouton Enregistrer)
        buttons = self.create_action_buttons()
        main_layout.addLayout(buttons)
        
        self.setLayout(main_layout)
    
    def create_header(self):
        """Crée l'en-tête avec dégradé"""
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet(f"""
            QWidget {{
                {Theme.AppTheme.create_gradient_css(
                    Theme.AppTheme.PRIMARY, 
                    Theme.AppTheme.INFO
                )}
                border-radius: 12px;
                {Theme.AppTheme.create_shadow_css()}
            }}
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(30, 0, 30, 0)
        
        # Icône
        icon_label = QLabel("💰")
        icon_label.setStyleSheet("font-size: 36px; color: white;")
        layout.addWidget(icon_label)
        
        # Titre
        title_container = QVBoxLayout()
        
        main_title = QLabel("FICHE DE PAIE")
        main_title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: white;
        """)
        
        subtitle = QLabel("Gestion des salaires")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: rgba(255, 255, 255, 0.8);
        """)
        
        title_container.addWidget(main_title)
        title_container.addWidget(subtitle)
        
        layout.addLayout(title_container)
        layout.addStretch()
        
        # Indicateur de statut
        self.status_indicator = QLabel("● BROUILLON")
        self.status_indicator.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: white;
            background: rgba(0, 0, 0, 0.2);
            padding: 5px 15px;
            border-radius: 15px;
        """)
        layout.addWidget(self.status_indicator)
        
        header.setLayout(layout)
        return header
    
    def create_form_panel(self):
        """Crée le panneau de formulaire"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Onglets
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(Theme.AppTheme.get_tab_style())
        
        # Onglet 1: Informations de base
        tab_info = self.create_info_tab()
        self.tabs.addTab(tab_info, "📋 Informations")
        
        # Onglet 2: Gains
        tab_earnings = self.create_earnings_tab()
        self.tabs.addTab(tab_earnings, "💰 Gains")
        
        # Onglet 3: Déductions
        tab_deductions = self.create_deductions_tab()
        self.tabs.addTab(tab_deductions, "📉 Déductions")
        
        # Onglet 4: Paramètres avancés
        tab_advanced = self.create_advanced_tab()
        self.tabs.addTab(tab_advanced, "⚙️ Avancé")
        
        layout.addWidget(self.tabs)
        panel.setLayout(layout)
        return panel
    
    def create_info_tab(self):
        """Crée l'onglet Informations"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Section Employé
        emp_group = QGroupBox("👤 Informations Employé")
        emp_layout = QFormLayout()
        
        self.employee_combo = QComboBox()
        self.employee_combo.setMinimumHeight(35)
        self.load_employees()
        self.employee_combo.currentIndexChanged.connect(self.on_employee_selected)
        
        self.matricule_label = QLabel("--")
        self.matricule_label.setStyleSheet(Theme.AppTheme.get_label_style("info"))
        
        self.poste_label = QLabel("--")
        self.poste_label.setStyleSheet(Theme.AppTheme.get_label_style("info"))
        
        emp_layout.addRow("Employé*:", self.employee_combo)
        emp_layout.addRow("Matricule:", self.matricule_label)
        emp_layout.addRow("Poste:", self.poste_label)
        emp_group.setLayout(emp_layout)
        
        # Section Période
        period_group = QGroupBox("📅 Période de Paie")
        period_layout = QFormLayout()
        
        self.month_combo = QComboBox()
        months = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        self.month_combo.addItems(months)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2030)
        self.year_spin.setValue(datetime.now().year)
        
        period_layout.addRow("Mois:", self.month_combo)
        period_layout.addRow("Année:", self.year_spin)
        period_group.setLayout(period_layout)
        
        # Section Jours
        days_group = QGroupBox("📊 Jours Travaillés")
        days_layout = QFormLayout()
        
        self.working_days_spin = QSpinBox()
        self.working_days_spin.setRange(1, 31)
        self.working_days_spin.setValue(22)
        
        self.actual_days_spin = QSpinBox()
        self.actual_days_spin.setRange(0, 31)
        self.actual_days_spin.setValue(22)
        
        self.absent_days_spin = QSpinBox()
        self.absent_days_spin.setRange(0, 31)
        self.absent_days_spin.setValue(0)
        
        days_layout.addRow("Jours ouvrés:", self.working_days_spin)
        days_layout.addRow("Jours travaillés:", self.actual_days_spin)
        days_layout.addRow("Jours d'absence:", self.absent_days_spin)
        days_group.setLayout(days_layout)
        
        layout.addWidget(emp_group)
        layout.addWidget(period_group)
        layout.addWidget(days_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_earnings_tab(self):
        """Crée l'onglet Gains"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Salaire de base
        salary_group = QGroupBox("💵 Salaire de Base")
        salary_layout = QFormLayout()
        
        self.base_salary_spin = QDoubleSpinBox()
        self.base_salary_spin.setRange(0, 1000000)
        self.base_salary_spin.setDecimals(2)
        self.base_salary_spin.setSuffix(" DA")
        self.base_salary_spin.setValue(0.0)
        
        salary_layout.addRow("Montant mensuel:", self.base_salary_spin)
        salary_group.setLayout(salary_layout)
        
        # Heures supplémentaires
        overtime_group = QGroupBox("⏰ Heures Supplémentaires")
        overtime_layout = QFormLayout()
        
        self.overtime_hours_spin = QSpinBox()
        self.overtime_hours_spin.setRange(0, 200)
        self.overtime_hours_spin.setValue(0)
        
        self.overtime_rate_spin = QDoubleSpinBox()
        self.overtime_rate_spin.setRange(0, 10000)
        self.overtime_rate_spin.setDecimals(2)
        self.overtime_rate_spin.setSuffix(" DA/heure")
        self.overtime_rate_spin.setValue(0.0)
        
        self.overtime_amount_label = QLabel("0.00 DA")
        self.overtime_amount_label.setStyleSheet(Theme.AppTheme.get_label_style("info"))
        
        overtime_layout.addRow("Nombre d'heures:", self.overtime_hours_spin)
        overtime_layout.addRow("Taux horaire:", self.overtime_rate_spin)
        overtime_layout.addRow("Montant total:", self.overtime_amount_label)
        overtime_group.setLayout(overtime_layout)
        
        # Bonus
        bonus_group = QGroupBox("🎁 Bonus et Primes")
        bonus_layout = QFormLayout()
        
        self.bonus_spin = QDoubleSpinBox()
        self.bonus_spin.setRange(0, 1000000)
        self.bonus_spin.setDecimals(2)
        self.bonus_spin.setSuffix(" DA")
        self.bonus_spin.setValue(0.0)
        
        self.bonus_description = QLineEdit()
        self.bonus_description.setPlaceholderText("Description du bonus (optionnel)")
        
        bonus_layout.addRow("Montant:", self.bonus_spin)
        bonus_layout.addRow("Description:", self.bonus_description)
        bonus_group.setLayout(bonus_layout)
        
        # Autres allocations
        allowances_group = QGroupBox("📈 Autres Allocations")
        allowances_layout = QFormLayout()
        
        self.other_allowances_spin = QDoubleSpinBox()
        self.other_allowances_spin.setRange(0, 1000000)
        self.other_allowances_spin.setDecimals(2)
        self.other_allowances_spin.setSuffix(" DA")
        self.other_allowances_spin.setValue(0.0)
        
        allowances_layout.addRow("Montant:", self.other_allowances_spin)
        allowances_group.setLayout(allowances_layout)
        
        layout.addWidget(salary_group)
        layout.addWidget(overtime_group)
        layout.addWidget(bonus_group)
        layout.addWidget(allowances_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_deductions_tab(self):
        """Crée l'onglet Déductions"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Déductions sociales
        social_group = QGroupBox("🏛️ Déductions Sociales")
        social_layout = QFormLayout()
        
        self.cnass_spin = QDoubleSpinBox()
        self.cnass_spin.setRange(0, 100000)
        self.cnass_spin.setDecimals(2)
        self.cnass_spin.setSuffix(" DA")
        self.cnass_spin.setValue(0.0)
        
        self.cnass_auto_btn = QPushButton("Calculer automatiquement")
        self.cnass_auto_btn.setStyleSheet(Theme.AppTheme.get_button_style(
            Theme.AppTheme.INFO, Theme.AppTheme.INFO_DARK, "5px 10px"
        ))
        self.cnass_auto_btn.clicked.connect(self.calculate_cnass)
        
        social_layout.addRow("CNAS (9%):", self.cnass_spin)
        social_layout.addRow("", self.cnass_auto_btn)
        social_group.setLayout(social_layout)
        
        # Impôt
        tax_group = QGroupBox("💰 Impôt sur le Revenu")
        tax_layout = QFormLayout()
        
        self.tax_spin = QDoubleSpinBox()
        self.tax_spin.setRange(0, 100000)
        self.tax_spin.setDecimals(2)
        self.tax_spin.setSuffix(" DA")
        self.tax_spin.setValue(0.0)
        
        self.tax_auto_btn = QPushButton("Calculer automatiquement")
        self.tax_auto_btn.setStyleSheet(Theme.AppTheme.get_button_style(
            Theme.AppTheme.INFO, Theme.AppTheme.INFO_DARK, "5px 10px"
        ))
        self.tax_auto_btn.clicked.connect(self.calculate_tax)
        
        tax_layout.addRow("Impôt (IRG):", self.tax_spin)
        tax_layout.addRow("", self.tax_auto_btn)
        tax_group.setLayout(tax_layout)
        
        # Autres déductions
        other_group = QGroupBox("📉 Autres Déductions")
        other_layout = QFormLayout()
        
        self.advance_spin = QDoubleSpinBox()
        self.advance_spin.setRange(0, 1000000)
        self.advance_spin.setDecimals(2)
        self.advance_spin.setSuffix(" DA")
        self.advance_spin.setValue(0.0)
        
        self.other_deductions_spin = QDoubleSpinBox()
        self.other_deductions_spin.setRange(0, 100000)
        self.other_deductions_spin.setDecimals(2)
        self.other_deductions_spin.setSuffix(" DA")
        self.other_deductions_spin.setValue(0.0)
        
        self.deduction_description = QTextEdit()
        self.deduction_description.setMaximumHeight(80)
        self.deduction_description.setPlaceholderText("Description des déductions...")
        
        other_layout.addRow("Avance sur salaire:", self.advance_spin)
        other_layout.addRow("Autres déductions:", self.other_deductions_spin)
        other_layout.addRow("Description:", self.deduction_description)
        other_group.setLayout(other_layout)
        
        layout.addWidget(social_group)
        layout.addWidget(tax_group)
        layout.addWidget(other_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_advanced_tab(self):
        """Crée l'onglet Avancé"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Paramètres de calcul
        calc_group = QGroupBox("🧮 Paramètres de Calcul")
        calc_layout = QFormLayout()
        
        self.cnass_percentage_spin = QDoubleSpinBox()
        self.cnass_percentage_spin.setRange(0, 100)
        self.cnass_percentage_spin.setDecimals(2)
        self.cnass_percentage_spin.setSuffix(" %")
        self.cnass_percentage_spin.setValue(9.0)
        
        self.overtime_multiplier_spin = QDoubleSpinBox()
        self.overtime_multiplier_spin.setRange(1.0, 3.0)
        self.overtime_multiplier_spin.setDecimals(2)
        self.overtime_multiplier_spin.setValue(1.5)
        
        calc_layout.addRow("Taux CNAS:", self.cnass_percentage_spin)
        calc_layout.addRow("Majoration heures supp:", self.overtime_multiplier_spin)
        calc_group.setLayout(calc_layout)
        
        # Options de génération
        gen_group = QGroupBox("📄 Options de Génération")
        gen_layout = QFormLayout()
        
        self.auto_calc_checkbox = QLabel("✓ Calcul automatique activé")
        self.auto_calc_checkbox.setStyleSheet(Theme.AppTheme.get_label_style("success"))
        
        self.include_details_checkbox = QLabel("✓ Détails inclus dans le PDF")
        self.include_details_checkbox.setStyleSheet(Theme.AppTheme.get_label_style("success"))
        
        gen_layout.addRow("Calcul:", self.auto_calc_checkbox)
        gen_layout.addRow("PDF:", self.include_details_checkbox)
        gen_group.setLayout(gen_layout)
        
        layout.addWidget(calc_group)
        layout.addWidget(gen_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_preview_panel(self):
        """Crée le panneau d'aperçu"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # En-tête d'aperçu
        preview_header = QLabel("👁️ APERÇU EN TEMPS RÉEL")
        preview_header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            text-align: center;
        """)
        layout.addWidget(preview_header)
        
        # Zone de défilement pour l'aperçu
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(Theme.AppTheme.get_scroll_area_style())
        
        preview_widget = QWidget()
        preview_layout = QVBoxLayout()
        
        # Résumé détaillé
        summary_group = QGroupBox("🧮 RÉSUMÉ DÉTAILLÉ")
        summary_layout = QVBoxLayout()
        
        self.summary_labels = {}
        
        # Gains
        gains_frame = self.create_summary_frame("💰 GAINS", [
            ("Salaire proportionnel", "proportional_salary"),
            ("Heures supplémentaires", "overtime_amount"),
            ("Bonus et primes", "bonus_amount"),
            ("Autres allocations", "other_allowances"),
            ("<b>TOTAL DES GAINS</b>", "gross_salary")
        ], Theme.AppTheme.SUCCESS)
        
        # Déductions
        deductions_frame = self.create_summary_frame("📉 DÉDUCTIONS", [
            ("CNAS (9%)", "cnass_deduction"),
            ("Impôt sur le revenu", "tax_deduction"),
            ("Avances", "advance_deduction"),
            ("Autres déductions", "other_deductions"),
            ("<b>TOTAL DES DÉDUCTIONS</b>", "total_deductions")
        ], Theme.AppTheme.DANGER)
        
        # Salaire net
        net_frame = self.create_summary_frame("💵 SALAIRE NET", [
            ("<b>NET À PAYER</b>", "net_salary")
        ], Theme.AppTheme.PRIMARY, True)
        
        summary_layout.addWidget(gains_frame)
        summary_layout.addWidget(deductions_frame)
        summary_layout.addWidget(net_frame)
        summary_group.setLayout(summary_layout)
        
        preview_layout.addWidget(summary_group)
        
        # Graphique de répartition
        chart_group = QGroupBox("📊 RÉPARTITION")
        chart_layout = QVBoxLayout()
        
        self.chart_label = QLabel("Graphique de répartition")
        self.chart_label.setStyleSheet("""
            font-style: italic;
            color: #7f8c8d;
            text-align: center;
            padding: 20px;
        """)
        chart_layout.addWidget(self.chart_label)
        
        chart_group.setLayout(chart_layout)
        preview_layout.addWidget(chart_group)
        
        # Informations complémentaires
        info_group = QGroupBox("📝 INFORMATIONS")
        info_layout = QVBoxLayout()
        
        self.info_text = QLabel(
            "Les calculs sont basés sur:\n"
            "• CNAS: 9% du salaire brut\n"
            "• IRG: Taux progressif\n"
            "• Heures supp: Taux majoré 50%"
        )
        self.info_text.setStyleSheet(Theme.AppTheme.get_label_style("normal"))
        self.info_text.setWordWrap(True)
        
        info_layout.addWidget(self.info_text)
        info_group.setLayout(info_layout)
        
        preview_layout.addWidget(info_group)
        preview_layout.addStretch()
        
        preview_widget.setLayout(preview_layout)
        scroll.setWidget(preview_widget)
        
        layout.addWidget(scroll)
        panel.setLayout(layout)
        return panel
    
    def create_summary_frame(self, title, items, color, is_net=False):
        """Crée un cadre de résumé"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 8px;
                background: {'#f8f9fa' if not is_net else '#fffde7'};
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Titre
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-weight: bold;
            color: {color};
            font-size: 14px;
            padding-bottom: 5px;
            border-bottom: 1px solid {color};
        """)
        layout.addWidget(title_label)
        
        # Items
        for item_text, item_key in items:
            item_layout = QHBoxLayout()
            
            label = QLabel(item_text)
            if "<b>" in item_text:
                label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            else:
                label.setStyleSheet(Theme.AppTheme.get_label_style("normal"))
            
            value_label = QLabel("0.00 DA")
            value_label.setStyleSheet(f"""
                font-weight: {'bold' if '<b>' in item_text or is_net else 'normal'};
                color: {'#2c3e50' if is_net else color};
                font-size: {'14px' if is_net else '12px'};
            """)
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            item_layout.addWidget(label)
            item_layout.addWidget(value_label)
            
            layout.addLayout(item_layout)
            
            # Stocker la référence pour mise à jour
            if item_key:
                self.summary_labels[item_key] = value_label
        
        frame.setLayout(layout)
        return frame
    
    def create_action_buttons(self):
        """Crée les boutons d'action (sans bouton Enregistrer)"""
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        
        # Bouton Calculer
        self.btn_calculate = QPushButton("🧮 Calculer Totaux")
        self.btn_calculate.setToolTip("Recalculer tous les totaux")
        self.btn_calculate.clicked.connect(self.calculate_totals)
        
        # Bouton Aperçu PDF
        self.btn_preview = QPushButton("👁️ Aperçu PDF")
        self.btn_preview.setToolTip("Générer un aperçu PDF")
        self.btn_preview.clicked.connect(self.preview_payslip)
        
        # Bouton Annuler seulement
        btn_cancel = QPushButton("❌ Annuler")
        btn_cancel.setToolTip("Fermer sans enregistrer")
        btn_cancel.clicked.connect(self.reject)
        
        buttons.addWidget(self.btn_calculate)
        buttons.addWidget(self.btn_preview)
        buttons.addStretch()
        buttons.addWidget(btn_cancel)
        
        return buttons
    
    def setup_connections(self):
        """Configure les connexions des signaux"""
        # Connexions pour le calcul automatique
        self.base_salary_spin.valueChanged.connect(self.on_value_changed)
        self.working_days_spin.valueChanged.connect(self.on_value_changed)
        self.actual_days_spin.valueChanged.connect(self.on_value_changed)
        self.overtime_hours_spin.valueChanged.connect(self.on_value_changed)
        self.overtime_rate_spin.valueChanged.connect(self.on_value_changed)
        self.bonus_spin.valueChanged.connect(self.on_value_changed)
        self.other_allowances_spin.valueChanged.connect(self.on_value_changed)
        self.cnass_spin.valueChanged.connect(self.on_value_changed)
        self.tax_spin.valueChanged.connect(self.on_value_changed)
        self.advance_spin.valueChanged.connect(self.on_value_changed)
        self.other_deductions_spin.valueChanged.connect(self.on_value_changed)
    
    def load_employees(self):
        """Charge la liste des employés"""
        with get_session() as session:
            employees = session.query(Employee).filter(
                Employee.est_actif == True
            ).order_by(Employee.nom, Employee.prenom).all()
            
            self.employee_combo.clear()
            self.employee_combo.addItem("-- Sélectionnez un employé --", None)
            
            for emp in employees:
                display_text = f"{emp.nom_complet} ({emp.code_employe}) - {emp.salaire:,.0f} DA"
                self.employee_combo.addItem(display_text, emp.id)
    
    def load_data(self):
        """Charge les données de la fiche de paie existante"""
        if not self.payslip_id:
            return
        
        try:
            with get_session() as session:
                payslip = session.query(Payslip).filter(
                    Payslip.id == self.payslip_id
                ).first()
                
                if payslip:
                    self.employee_id = payslip.employee_id
                    
                    # Sélectionner l'employé
                    idx = self.employee_combo.findData(payslip.employee_id)
                    if idx >= 0:
                        self.employee_combo.setCurrentIndex(idx)
                    
                    # Période
                    self.month_combo.setCurrentIndex(payslip.period_month - 1 if payslip.period_month else 0)
                    self.year_spin.setValue(payslip.period_year if payslip.period_year else datetime.now().year)
                    
                    # Salaire et jours
                    self.base_salary_spin.setValue(float(payslip.base_salary) if payslip.base_salary else 0.0)
                    self.working_days_spin.setValue(payslip.working_days or 22)
                    self.actual_days_spin.setValue(payslip.actual_worked_days or (payslip.working_days or 22))
                    
                    # Heures supplémentaires
                    self.overtime_hours_spin.setValue(payslip.overtime_hours or 0)
                    self.overtime_rate_spin.setValue(float(payslip.overtime_rate) if payslip.overtime_rate else 0.0)
                    
                    # Bonus
                    self.bonus_spin.setValue(float(payslip.bonus_amount) if payslip.bonus_amount else 0.0)
                    self.bonus_description.setText(payslip.bonus_description or "")
                    
                    # Allocations
                    self.other_allowances_spin.setValue(float(payslip.other_allowances) if payslip.other_allowances else 0.0)
                    
                    # Déductions
                    self.cnass_spin.setValue(float(payslip.cnass_deduction) if payslip.cnass_deduction else 0.0)
                    self.tax_spin.setValue(float(payslip.tax_deduction) if payslip.tax_deduction else 0.0)
                    self.advance_spin.setValue(float(payslip.advance_deduction) if payslip.advance_deduction else 0.0)
                    self.other_deductions_spin.setValue(float(payslip.other_deductions) if payslip.other_deductions else 0.0)
                    self.deduction_description.setPlainText(payslip.deduction_description or "")
                    
                    # Mettre à jour le statut
                    self.update_status_indicator(payslip.status or "BROUILLON")
        except Exception as e:
            self.show_error(f"Erreur lors du chargement: {e}")
    
    def on_employee_selected(self):
        """Quand un employé est sélectionné"""
        emp_id = self.employee_combo.currentData()
        if not emp_id:
            return
        
        with get_session() as session:
            emp = session.query(Employee).filter(Employee.id == emp_id).first()
            if emp:
                self.employee = emp
                self.matricule_label.setText(emp.code_employe or "--")
                self.poste_label.setText(emp.poste or "--")
                
                # Charger le salaire de base
                if emp.salaire:
                    self.base_salary_spin.setValue(float(emp.salaire))
                    
                # Calculer automatiquement
                self.calculate_totals()
    
    def on_value_changed(self):
        """Quand une valeur change"""
        # Mettre à jour le montant des heures supplémentaires
        hours = self.overtime_hours_spin.value()
        rate = self.overtime_rate_spin.value()
        overtime_amount = hours * rate
        self.overtime_amount_label.setText(f"{overtime_amount:,.2f} DA")
        
        # Déclencher le calcul après un délai (anti-rebond)
        if hasattr(self, '_calculation_timer'):
            self._calculation_timer.stop()
        
        self._calculation_timer = QTimer()
        self._calculation_timer.setSingleShot(True)
        self._calculation_timer.timeout.connect(self.calculate_totals)
        self._calculation_timer.start(500)  # 500ms de délai
    
    def calculate_totals(self):
        """Calcule tous les totaux"""
        try:
            # Afficher la barre de progression
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("Calcul en cours...")
            
            # Récupérer les valeurs
            base_salary = Decimal(str(self.base_salary_spin.value()))
            working_days = self.working_days_spin.value()
            actual_days = self.actual_days_spin.value()
            
            self.progress_bar.setValue(20)
            
            # Calculer le salaire proportionnel
            proportional_salary = self.calculator.calculate_proportional_salary(
                base_salary, working_days, actual_days
            )
            
            self.progress_bar.setValue(40)
            
            # Calculer les heures supplémentaires
            overtime_hours = Decimal(str(self.overtime_hours_spin.value()))
            overtime_rate = Decimal(str(self.overtime_rate_spin.value()))
            overtime_amount = self.calculator.calculate_overtime_amount(
                overtime_hours, overtime_rate
            )
            
            self.progress_bar.setValue(60)
            
            # Autres gains
            bonus = Decimal(str(self.bonus_spin.value()))
            allowances = Decimal(str(self.other_allowances_spin.value()))
            
            # Salaire brut
            gross_salary = proportional_salary + overtime_amount + bonus + allowances
            
            self.progress_bar.setValue(80)
            
            # Déductions
            cnass = self.calculator.calculate_cnass_contribution(gross_salary)
            tax = self.calculator.calculate_income_tax(gross_salary)
            advance = Decimal(str(self.advance_spin.value()))
            other_deductions = Decimal(str(self.other_deductions_spin.value()))
            
            total_deductions = cnass + tax + advance + other_deductions
            
            # Salaire net
            net_salary = gross_salary - total_deductions
            
            self.progress_bar.setValue(100)
            
            # Mettre à jour l'affichage
            self.update_summary_display({
                'proportional_salary': proportional_salary,
                'overtime_amount': overtime_amount,
                'bonus_amount': bonus,
                'other_allowances': allowances,
                'gross_salary': gross_salary,
                'cnass_deduction': cnass,
                'tax_deduction': tax,
                'advance_deduction': advance,
                'other_deductions': other_deductions,
                'total_deductions': total_deductions,
                'net_salary': net_salary
            })
            
            # Émettre le signal
            self.calculation_completed.emit({
                'gross': float(gross_salary),
                'deductions': float(total_deductions),
                'net': float(net_salary)
            })
            
            # Mettre à jour le statut
            self.status_label.setText("Calcul terminé")
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            self.show_error(f"Erreur de calcul: {e}")
            self.progress_bar.setVisible(False)
            self.status_label.setText("Erreur de calcul")
    
    def calculate_cnass(self):
        """Calcule automatiquement la CNAS"""
        try:
            gross = self.get_gross_salary()
            if gross > 0:
                cnass = self.calculator.calculate_cnass_contribution(Decimal(str(gross)))
                self.cnass_spin.setValue(float(cnass))
                self.show_info("CNAS calculée automatiquement")
        except Exception as e:
            self.show_error(f"Erreur: {e}")
    
    def calculate_tax(self):
        """Calcule automatiquement l'impôt"""
        try:
            gross = self.get_gross_salary()
            if gross > 0:
                tax = self.calculator.calculate_income_tax(Decimal(str(gross)))
                self.tax_spin.setValue(float(tax))
                self.show_info("Impôt calculé automatiquement")
        except Exception as e:
            self.show_error(f"Erreur: {e}")
    
    def get_gross_salary(self):
        """Récupère le salaire brut calculé"""
        if 'gross_salary' in self.summary_labels:
            text = self.summary_labels['gross_salary'].text()
            # Extraire le nombre du texte
            import re
            match = re.search(r'([\d\s,]+)', text)
            if match:
                value_str = match.group(1).replace(' ', '').replace(',', '')
                return float(value_str)
        return 0.0
    
    def update_summary_display(self, data):
        """Met à jour l'affichage du résumé"""
        for key, value in data.items():
            if key in self.summary_labels:
                self.summary_labels[key].setText(f"{value:,.2f} DA")
        
        # Mettre à jour le graphique de répartition
        self.update_chart(data)
    
    def update_chart(self, data):
        """Met à jour le graphique de répartition"""
        try:
            gross = float(data['gross_salary'])
            if gross > 0:
                percentages = {
                    "Salaire": float(data['proportional_salary']) / gross * 100,
                    "Heures sup": float(data['overtime_amount']) / gross * 100,
                    "Bonus": float(data['bonus_amount']) / gross * 100,
                    "Allocations": float(data['other_allowances']) / gross * 100
                }
                
                # Filtrer les éléments nuls
                filtered = {k: v for k, v in percentages.items() if v > 0}
                
                if filtered:
                    chart_text = "Répartition des gains:\n"
                    for name, pct in filtered.items():
                        chart_text += f"• {name}: {pct:.1f}%\n"
                    
                    self.chart_label.setText(chart_text)
        except:
            pass
    
    def update_status_indicator(self, status):
        """Met à jour l'indicateur de statut"""
        colors = {
            "BROUILLON": Theme.AppTheme.WARNING,
            "VALIDÉE": Theme.AppTheme.INFO,
            "PAYÉE": Theme.AppTheme.SUCCESS,
            "ANNULÉE": Theme.AppTheme.DANGER
        }
        
        color = colors.get(status, Theme.AppTheme.GRAY)
        self.status_indicator.setText(f"● {status}")
        self.status_indicator.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: white;
            background: {color};
            padding: 5px 15px;
            border-radius: 15px;
        """)
    
    def preview_payslip(self):
        """Génère un aperçu PDF"""
        if self.employee_combo.currentIndex() <= 0:
            self.show_warning("Veuillez sélectionner un employé")
            return
        
        try:
            self.status_label.setText("Génération du PDF...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Construire les données
            data = self.build_payslip_data()
            
            self.progress_bar.setValue(50)
            
            # Générer le PDF
            from tempfile import gettempdir
            output_path = self.pdf_service.generate_payslip(data)
            
            self.progress_bar.setValue(100)
            
            # Ouvrir le PDF
            import os
            import subprocess
            import sys
            
            if os.name == 'nt':  # Windows
                os.startfile(output_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.call(['open', output_path])
            else:  # Linux
                subprocess.call(['xdg-open', output_path])
            
            self.show_info(f"PDF généré: {output_path}")
            self.status_label.setText("PDF généré avec succès")
            
        except Exception as e:
            self.show_error(f"Erreur de génération: {e}")
        finally:
            self.progress_bar.setVisible(False)
    
    def build_payslip_data(self):
        """Construit les données pour la fiche de paie"""
        with get_session() as session:
            emp_id = self.employee_combo.currentData()
            employee = session.query(Employee).filter(Employee.id == emp_id).first()
            
            if not employee:
                raise ValueError("Employé non trouvé")
            
            # Récupérer les valeurs calculées
            summary_data = {}
            for key, label in self.summary_labels.items():
                text = label.text().replace(' DA', '').replace(' ', '').replace(',', '')
                try:
                    summary_data[key] = Decimal(text)
                except:
                    summary_data[key] = Decimal('0')
            
            return {
                'employee': {
                    'name': employee.nom_complet,
                    'matricule': employee.code_employe or f"{employee.id:04d}",
                    'first_name': employee.prenom,
                    'last_name': employee.nom,
                    'address': employee.adresse or "",
                    'phone': employee.telephone or "",
                    'position': employee.poste or "Non spécifié",
                    'hire_date': employee.date_embauche,
                    'birth_date': employee.date_naissance,
                    'family_status': employee.situation_familiale or "Célibataire",
                    'social_number': employee.numero_secu or "N/A"
                },
                'payslip': {
                    'period': f"{self.month_combo.currentText()} {self.year_spin.value()}",
                    'period_month': self.month_combo.currentIndex() + 1,
                    'period_year': self.year_spin.value(),
                    'generation_date': datetime.now(),
                    'base_salary': Decimal(str(self.base_salary_spin.value())),
                    'working_days': self.working_days_spin.value(),
                    'actual_days': self.actual_days_spin.value(),
                    'overtime_hours': self.overtime_hours_spin.value(),
                    'overtime_rate': Decimal(str(self.overtime_rate_spin.value())),
                    'bonus': Decimal(str(self.bonus_spin.value())),
                    'bonus_description': self.bonus_description.text(),
                    'allowances': Decimal(str(self.other_allowances_spin.value())),
                    'status': 'BROUILLON',
                    **summary_data
                }
            }
    
    def show_info(self, message):
        """Affiche un message d'information"""
        QMessageBox.information(self, "Information", message)
    
    def show_warning(self, message):
        """Affiche un message d'avertissement"""
        QMessageBox.warning(self, "Avertissement", message)
    
    def show_error(self, message):
        """Affiche un message d'erreur"""
        QMessageBox.critical(self, "Erreur", message)
    
    def show_success(self, message):
        """Affiche un message de succès"""
        QMessageBox.information(self, "Succès", message)