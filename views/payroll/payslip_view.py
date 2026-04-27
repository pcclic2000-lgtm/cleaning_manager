"""
Vue principale moderne pour la gestion des fiches de paie
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QLineEdit, QLabel, QFormLayout, QComboBox,
    QTextEdit, QDateEdit, QHeaderView, QAbstractItemView,
    QMenu, QDoubleSpinBox, QSpinBox, QGroupBox,
    QTabWidget, QFileDialog, QTextBrowser, QSplitter,
    QFrame, QScrollArea, QToolBar, QStatusBar,
    QMainWindow, QDockWidget, QProgressBar,
    QInputDialog, QCalendarWidget, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QPoint, QTimer, QSize, QModelIndex
from PyQt6.QtGui import QAction, QFont, QTextDocument, QPageSize, QIcon, QBrush, QColor

import os
from datetime import datetime, date, timedelta
from decimal import Decimal
import webbrowser
import tempfile

from database.db import SessionLocal, get_session
from models.employee import Employee
from models.payslip import Payslip
from services.payslip_calculator import PayslipCalculator
from services.payslip_pdf_service import PayslipPDFService
from views.payroll.payslip_dialog import ModernPayslipDialog
import ui.app_theme as Theme
from ui.components.kpi_card import KPICard
from ui.components.paginated_table import PaginatedTable


class ModernPayslipView(QWidget):
    """Vue moderne pour la gestion des fiches de paie avec dashboard"""
    
    data_refreshed = pyqtSignal()
    
    def __init__(self, employee_id=None):
        super().__init__()
        self.employee_id = employee_id
        self.current_filter = {}
        self.calculator = PayslipCalculator()
        self.pdf_service = PayslipPDFService()
        
        # Appliquer le thème global
        Theme.AppTheme.apply_global_style(self)
        
        self.init_ui()
        self.setup_connections()
        self.refresh_data()
        
        # Démarrer le timer de rafraîchissement automatique
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Rafraîchir toutes les 30 secondes
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # En-tête avec titre et statistiques
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Dashboard avec KPIs
        dashboard = self.create_dashboard()
        main_layout.addWidget(dashboard)
        
        # Barre d'outils principale
        toolbar = self.create_main_toolbar()
        main_layout.addLayout(toolbar)
        
        # Splitter pour table et détails
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Table paginée
        self.table_widget = self.create_table_widget()
        splitter.addWidget(self.table_widget)
        
        # Panneau de détails
        details_panel = self.create_details_panel()
        splitter.addWidget(details_panel)
        
        splitter.setSizes([400, 200])
        main_layout.addWidget(splitter)
        
        # Barre de statut
        status_bar = self.create_status_bar()
        main_layout.addWidget(status_bar)
        
        self.setLayout(main_layout)
    
    def create_header(self):
        """Crée l'en-tête de la vue"""
        header = QWidget()
        header.setFixedHeight(100)
        header.setStyleSheet(f"""
            QWidget {{
                {Theme.AppTheme.create_gradient_css(
                    Theme.AppTheme.DARK, 
                    Theme.AppTheme.PRIMARY
                )}
                border-radius: 12px;
                {Theme.AppTheme.create_shadow_css()}
            }}
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(30, 0, 30, 0)
        
        # Titre principal
        title_container = QVBoxLayout()
        
        main_title = QLabel("💰 GESTION DES FICHES DE PAIE")
        main_title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: white;
        """)
        
        subtitle = QLabel("Système de gestion de paie professionnel")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: rgba(255, 255, 255, 0.8);
        """)
        
        title_container.addWidget(main_title)
        title_container.addWidget(subtitle)
        
        layout.addLayout(title_container)
        layout.addStretch()
        
        # Bouton d'actualisation rapide
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(50, 50)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 25px;
                font-size: 20px;
                color: white;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.3);
                border: 2px solid white;
            }}
        """)
        refresh_btn.setToolTip("Actualiser les données")
        refresh_btn.clicked.connect(self.refresh_data)
        
        layout.addWidget(refresh_btn)
        
        header.setLayout(layout)
        return header
    
    def create_dashboard(self):
        """Crée le dashboard avec les KPIs"""
        dashboard = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        # KPI: Total salaire
        self.kpi_total = KPICard(
            "TOTAL SALAIRE", 
            "0 DA", 
            Theme.AppTheme.PRIMARY,
            "💰"
        )
        
        # KPI: Moyenne
        self.kpi_average = KPICard(
            "MOYENNE", 
            "0 DA", 
            Theme.AppTheme.SUCCESS,
            "📊"
        )
        
        # KPI: Fiches payées
        self.kpi_paid = KPICard(
            "PAYÉES", 
            "0", 
            Theme.AppTheme.SUCCESS,
            "✅"
        )
        
        # KPI: Fiches en attente
        self.kpi_pending = KPICard(
            "EN ATTENTE", 
            "0", 
            Theme.AppTheme.WARNING,
            "⏳"
        )
        
        # KPI: Dernier mois
        self.kpi_last_month = KPICard(
            "MOIS DERNIER", 
            "0 DA", 
            Theme.AppTheme.INFO,
            "📅"
        )
        
        layout.addWidget(self.kpi_total)
        layout.addWidget(self.kpi_average)
        layout.addWidget(self.kpi_paid)
        layout.addWidget(self.kpi_pending)
        layout.addWidget(self.kpi_last_month)
        
        dashboard.setLayout(layout)
        return dashboard
    
    def create_main_toolbar(self):
        """Crée la barre d'outils principale"""
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        # Groupe d'actions principales
        main_actions = QHBoxLayout()
        main_actions.setSpacing(5)
        
        btn_new = QPushButton("➕ Nouvelle")
        btn_new.setToolTip("Créer une nouvelle fiche de paie")
        btn_new.clicked.connect(self.create_payslip)
        
        btn_edit = QPushButton("✏️ Modifier")
        btn_edit.setToolTip("Modifier la fiche sélectionnée")
        btn_edit.clicked.connect(self.edit_selected_payslip)
        
        btn_delete = QPushButton("🗑️ Supprimer")
        btn_delete.setToolTip("Supprimer la fiche sélectionnée")
        btn_delete.clicked.connect(self.delete_selected_payslip)
        
        main_actions.addWidget(btn_new)
        main_actions.addWidget(btn_edit)
        main_actions.addWidget(btn_delete)
        
        # Groupe d'actions d'export
        export_actions = QHBoxLayout()
        export_actions.setSpacing(5)
        
        btn_preview = QPushButton("👁️ Aperçu")
        btn_preview.setToolTip("Aperçu de la fiche sélectionnée")
        btn_preview.clicked.connect(self.preview_selected_payslip)
        
        btn_export = QPushButton("📄 Exporter PDF")
        btn_export.setToolTip("Exporter la fiche en PDF")
        btn_export.clicked.connect(self.export_selected_payslip_pdf)
        
        btn_batch = QPushButton("📦 Lot PDF")
        btn_batch.setToolTip("Exporter plusieurs fiches en lot")
        btn_batch.clicked.connect(self.export_batch_pdf)
        
        export_actions.addWidget(btn_preview)
        export_actions.addWidget(btn_export)
        export_actions.addWidget(btn_batch)
        
        # Groupe de filtres
        filter_actions = QHBoxLayout()
        filter_actions.setSpacing(5)
        
        self.filter_month = QComboBox()
        self.filter_month.addItem("Tous les mois")
        months = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        self.filter_month.addItems(months)
        self.filter_month.currentIndexChanged.connect(self.apply_filters)
        
        self.filter_year = QComboBox()
        self.filter_year.addItem("Toutes les années")
        current_year = datetime.now().year
        for year in range(current_year - 5, current_year + 3):
            self.filter_year.addItem(str(year))
        self.filter_year.currentIndexChanged.connect(self.apply_filters)
        
        self.filter_status = QComboBox()
        self.filter_status.addItem("Tous les statuts")
        self.filter_status.addItems(["BROUILLON", "VALIDÉE", "PAYÉE", "ANNULÉE"])
        self.filter_status.currentIndexChanged.connect(self.apply_filters)
        
        btn_clear_filters = QPushButton("🗑️")
        btn_clear_filters.setFixedWidth(30)
        btn_clear_filters.setToolTip("Effacer tous les filtres")
        btn_clear_filters.clicked.connect(self.clear_filters)
        
        filter_actions.addWidget(QLabel("Mois:"))
        filter_actions.addWidget(self.filter_month)
        filter_actions.addWidget(QLabel("Année:"))
        filter_actions.addWidget(self.filter_year)
        filter_actions.addWidget(QLabel("Statut:"))
        filter_actions.addWidget(self.filter_status)
        filter_actions.addWidget(btn_clear_filters)
        
        # Ajouter les groupes à la toolbar
        toolbar.addLayout(main_actions)
        toolbar.addLayout(export_actions)
        toolbar.addStretch()
        toolbar.addLayout(filter_actions)
        
        return toolbar
    
    def create_table_widget(self):
        """Crée le widget de table avec pagination"""
        table_widget = QWidget()
        layout = QVBoxLayout()
        
        # Titre de la table
        table_header = QLabel("📋 LISTE DES FICHES DE PAIE")
        table_header.setStyleSheet(Theme.AppTheme.get_label_style("subtitle"))
        layout.addWidget(table_header)
        
        # Table avec pagination
        self.table = PaginatedTable(page_size=50)
        self.table.table.setColumnCount(11)
        self.table.table.setHorizontalHeaderLabels([
            "ID", "Employé", "Matricule", "Période", "Salaire base",
            "Salaire brut", "Déductions", "Salaire net", "Statut", 
            "Date génération", "Actions"
        ])
        
        # Cacher l'ID
        self.table.table.setColumnHidden(0, True)
        
        # Configuration des colonnes
        header = self.table.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Employé
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Matricule
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Période
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Salaire base
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Salaire brut
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Déductions
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Salaire net
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Statut
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Date génération
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        # Style
        self.table.table.setStyleSheet(Theme.AppTheme.get_table_style())
        
        # Menu contextuel
        self.table.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Connexion pour la sélection
        self.table.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.table)
        table_widget.setLayout(layout)
        
        return table_widget
    
    def create_details_panel(self):
        """Crée le panneau de détails"""
        panel = QWidget()
        panel.setMinimumHeight(200)
        
        layout = QVBoxLayout()
        
        # En-tête du panneau
        details_header = QLabel("📝 DÉTAILS DE LA FICHE SÉLECTIONNÉE")
        details_header.setStyleSheet(f"""
            {Theme.AppTheme.get_label_style("subtitle")}
            background: {Theme.AppTheme.LIGHT};
            padding: 10px;
            border-radius: 6px;
        """)
        layout.addWidget(details_header)
        
        # Scroll area pour les détails
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(Theme.AppTheme.get_scroll_area_style())
        
        details_widget = QWidget()
        details_layout = QVBoxLayout()
        
        # Informations de base
        info_group = QGroupBox("Informations")
        info_layout = QFormLayout()
        
        self.detail_employee = QLabel("--")
        self.detail_period = QLabel("--")
        self.detail_status = QLabel("--")
        self.detail_gross = QLabel("--")
        self.detail_net = QLabel("--")
        
        info_layout.addRow("Employé:", self.detail_employee)
        info_layout.addRow("Période:", self.detail_period)
        info_layout.addRow("Statut:", self.detail_status)
        info_layout.addRow("Salaire brut:", self.detail_gross)
        info_layout.addRow("Salaire net:", self.detail_net)
        
        info_group.setLayout(info_layout)
        details_layout.addWidget(info_group)
        
        # Actions rapides
        actions_group = QGroupBox("Actions Rapides")
        actions_layout = QHBoxLayout()
        
        self.btn_quick_preview = QPushButton("👁️ Aperçu rapide")
        self.btn_quick_preview.clicked.connect(self.preview_selected_payslip)
        self.btn_quick_preview.setEnabled(False)
        
        self.btn_quick_export = QPushButton("📄 Exporter")
        self.btn_quick_export.clicked.connect(self.export_selected_payslip_pdf)
        self.btn_quick_export.setEnabled(False)
        
        self.btn_change_status = QPushButton("🔄 Changer statut")
        self.btn_change_status.clicked.connect(self.change_payslip_status)
        self.btn_change_status.setEnabled(False)
        
        actions_layout.addWidget(self.btn_quick_preview)
        actions_layout.addWidget(self.btn_quick_export)
        actions_layout.addWidget(self.btn_change_status)
        actions_group.setLayout(actions_layout)
        
        details_layout.addWidget(actions_group)
        details_layout.addStretch()
        
        details_widget.setLayout(details_layout)
        scroll.setWidget(details_widget)
        
        layout.addWidget(scroll)
        panel.setLayout(layout)
        
        return panel
    
    def create_status_bar(self):
        """Crée la barre de statut"""
        status_bar = QWidget()
        status_bar.setFixedHeight(30)
        status_bar.setStyleSheet(f"""
            QWidget {{
                background: {Theme.AppTheme.LIGHT};
                border-top: 1px solid {Theme.AppTheme.LIGHT_DARK};
                border-radius: 0 0 8px 8px;
            }}
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)
        
        self.status_label = QLabel("Prêt")
        self.status_label.setStyleSheet(Theme.AppTheme.get_label_style("normal"))
        
        self.record_count = QLabel("0 fiches")
        self.record_count.setStyleSheet(Theme.AppTheme.get_label_style("info"))
        
        self.last_update = QLabel("Dernière mise à jour: --:--:--")
        self.last_update.setStyleSheet(Theme.AppTheme.get_label_style("normal"))
        
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.record_count)
        layout.addWidget(self.last_update)
        
        status_bar.setLayout(layout)
        return status_bar
    
    def setup_connections(self):
        """Configure les connexions"""
        # Connexion pour le rafraîchissement des données
        self.data_refreshed.connect(self.update_dashboard)
    
    def refresh_data(self):
        """Rafraîchit les données"""
        try:
            self.status_label.setText("Chargement des données...")
            self.load_payslips()
            self.data_refreshed.emit()
            self.last_update.setText(f"Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}")
            self.status_label.setText("Prêt")
        except Exception as e:
            self.status_label.setText(f"Erreur: {str(e)}")
    
    def load_payslips(self):
        """Charge les fiches de paie avec pagination"""
        try:
            with get_session() as session:
                # Construire la requête avec filtres
                query = session.query(Payslip).join(Employee)
                
                if self.employee_id:
                    query = query.filter(Payslip.employee_id == self.employee_id)
                
                # Appliquer les filtres
                if self.filter_month.currentIndex() > 0:
                    query = query.filter(Payslip.period_month == self.filter_month.currentIndex())
                
                if self.filter_year.currentIndex() > 0:
                    year = int(self.filter_year.currentText())
                    query = query.filter(Payslip.period_year == year)
                
                if self.filter_status.currentIndex() > 0:
                    status = self.filter_status.currentText()
                    query = query.filter(Payslip.status == status)
                
                # Compter le total
                total_count = query.count()
                self.table.set_total_items(total_count)
                self.record_count.setText(f"{total_count} fiches")
                
                # Pagination
                offset = (self.table.current_page - 1) * self.table.page_size
                payslips = query.order_by(
                    Payslip.period_year.desc(),
                    Payslip.period_month.desc(),
                    Payslip.date_generation.desc()
                ).offset(offset).limit(self.table.page_size).all()
                
                # Mettre à jour la table
                self.table.table.setRowCount(len(payslips))
                
                for row, payslip in enumerate(payslips):
                    # ID (caché)
                    self.table.table.setItem(row, 0, QTableWidgetItem(str(payslip.id)))
                    
                    # Employé
                    emp_name = payslip.employee.nom_complet if payslip.employee else "Inconnu"
                    self.table.table.setItem(row, 1, QTableWidgetItem(emp_name))
                    
                    # Matricule
                    matricule = payslip.employee.code_employe if payslip.employee else ""
                    self.table.table.setItem(row, 2, QTableWidgetItem(matricule))
                    
                    # Période
                    period = f"{payslip.period_month:02d}/{payslip.period_year}"
                    period_item = QTableWidgetItem(period)
                    period_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.table.setItem(row, 3, period_item)
                    
                    # Salaire de base
                    base_item = QTableWidgetItem(f"{payslip.base_salary:,.2f} DA")
                    base_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.table.setItem(row, 4, base_item)
                    
                    # Salaire brut
                    gross_item = QTableWidgetItem(f"{payslip.gross_salary:,.2f} DA")
                    gross_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.table.setItem(row, 5, gross_item)
                    
                    # Déductions
                    deductions_item = QTableWidgetItem(f"{payslip.total_deductions:,.2f} DA")
                    deductions_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.table.setItem(row, 6, deductions_item)
                    
                    # Salaire net
                    net_item = QTableWidgetItem(f"{payslip.net_salary:,.2f} DA")
                    net_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    if float(payslip.net_salary) > 0:
                        net_item.setForeground(QBrush(QColor(Theme.AppTheme.SUCCESS)))
                    self.table.table.setItem(row, 7, net_item)
                    
                    # Statut
                    status_item = QTableWidgetItem(payslip.status)
                    status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # Couleur selon le statut
                    if payslip.status == "PAYÉE":
                        status_item.setForeground(QBrush(QColor(Theme.AppTheme.SUCCESS)))
                    elif payslip.status == "VALIDÉE":
                        status_item.setForeground(QBrush(QColor(Theme.AppTheme.INFO)))
                    elif payslip.status == "ANNULÉE":
                        status_item.setForeground(QBrush(QColor(Theme.AppTheme.DANGER)))
                    else:
                        status_item.setForeground(QBrush(QColor(Theme.AppTheme.WARNING)))
                    
                    self.table.table.setItem(row, 8, status_item)
                    
                    # Date génération
                    date_str = payslip.date_generation.strftime("%d/%m/%Y %H:%M") if payslip.date_generation else ""
                    date_item = QTableWidgetItem(date_str)
                    date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.table.setItem(row, 9, date_item)
                    
                    # Actions (boutons)
                    actions_widget = self.create_actions_widget(payslip.id)
                    self.table.table.setCellWidget(row, 10, actions_widget)
        except Exception as e:
            self.show_error(f"Erreur de chargement: {str(e)}")
    
    def create_actions_widget(self, payslip_id):
        """Crée le widget d'actions pour une ligne"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(3)
        
        # Bouton Aperçu
        btn_preview = QPushButton("👁️")
        btn_preview.setFixedSize(30, 30)
        btn_preview.setToolTip("Aperçu")
        btn_preview.clicked.connect(lambda: self.preview_payslip_by_id(payslip_id))
        
        # Bouton Éditer
        btn_edit = QPushButton("✏️")
        btn_edit.setFixedSize(30, 30)
        btn_edit.setToolTip("Modifier")
        btn_edit.clicked.connect(lambda: self.edit_payslip_by_id(payslip_id))
        
        # Bouton Supprimer
        btn_delete = QPushButton("🗑️")
        btn_delete.setFixedSize(30, 30)
        btn_delete.setToolTip("Supprimer")
        btn_delete.clicked.connect(lambda: self.delete_payslip_by_id(payslip_id))
        
        layout.addWidget(btn_preview)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        
        widget.setLayout(layout)
        return widget
    
    def update_dashboard(self):
        """Met à jour le dashboard avec les statistiques"""
        try:
            with get_session() as session:
                # Total salaire du mois en cours
                current_month = datetime.now().month
                current_year = datetime.now().year
                
                total_query = session.query(Payslip).filter(
                    Payslip.period_month == current_month,
                    Payslip.period_year == current_year,
                    Payslip.status == "PAYÉE"
                )
                
                total_salary = sum(float(p.net_salary) for p in total_query.all() if p.net_salary)
                self.kpi_total.set_value(f"{total_salary:,.0f} DA", animate=True)
                
                # Moyenne
                avg_query = session.query(Payslip).filter(Payslip.status == "PAYÉE")
                avg_count = avg_query.count()
                avg_total = sum(float(p.net_salary) for p in avg_query.all() if p.net_salary)
                average = avg_total / avg_count if avg_count > 0 else 0
                self.kpi_average.set_value(f"{average:,.0f} DA", animate=True)
                
                # Fiches payées
                paid_count = session.query(Payslip).filter(Payslip.status == "PAYÉE").count()
                self.kpi_paid.set_value(str(paid_count), animate=True)
                
                # Fiches en attente
                pending_count = session.query(Payslip).filter(
                    Payslip.status.in_(["BROUILLON", "VALIDÉE"])
                ).count()
                self.kpi_pending.set_value(str(pending_count), animate=True)
                
                # Dernier mois
                last_month = current_month - 1 if current_month > 1 else 12
                last_year = current_year if current_month > 1 else current_year - 1
                
                last_month_query = session.query(Payslip).filter(
                    Payslip.period_month == last_month,
                    Payslip.period_year == last_year,
                    Payslip.status == "PAYÉE"
                )
                
                last_month_total = sum(float(p.net_salary) for p in last_month_query.all() if p.net_salary)
                self.kpi_last_month.set_value(f"{last_month_total:,.0f} DA", animate=True)
                
                # Définir les sous-titres
                self.kpi_total.set_subtitle(f"Mois: {datetime.now().strftime('%B %Y')}")
                self.kpi_average.set_subtitle(f"Sur {avg_count} fiches")
                self.kpi_paid.set_subtitle(f"Total payé")
                self.kpi_pending.set_subtitle("À traiter")
                self.kpi_last_month.set_subtitle(f"Mois: {last_month:02d}/{last_year}")
        except Exception as e:
            print(f"Erreur dashboard: {e}")
    
    def get_selected_payslip_id(self):
        """Récupère l'ID de la fiche de paie sélectionnée"""
        selected = self.table.table.selectedItems()
        if not selected:
            return None
        
        row = selected[0].row()
        id_item = self.table.table.item(row, 0)
        try:
            return int(id_item.text())
        except Exception:
            return None
    
    def on_selection_changed(self):
        """Quand la sélection change"""
        payslip_id = self.get_selected_payslip_id()
        if payslip_id:
            self.update_details(payslip_id)
            self.btn_quick_preview.setEnabled(True)
            self.btn_quick_export.setEnabled(True)
            self.btn_change_status.setEnabled(True)
        else:
            self.clear_details()
            self.btn_quick_preview.setEnabled(False)
            self.btn_quick_export.setEnabled(False)
            self.btn_change_status.setEnabled(False)
    
    def update_details(self, payslip_id):
        """Met à jour les détails de la fiche sélectionnée"""
        with get_session() as session:
            payslip = session.query(Payslip).filter(Payslip.id == payslip_id).first()
            if payslip:
                employee_name = payslip.employee.nom_complet if payslip.employee else "Inconnu"
                period = f"{payslip.period_month:02d}/{payslip.period_year}"
                
                self.detail_employee.setText(employee_name)
                self.detail_period.setText(period)
                self.detail_status.setText(payslip.status)
                self.detail_gross.setText(f"{payslip.gross_salary:,.2f} DA")
                self.detail_net.setText(f"{payslip.net_salary:,.2f} DA")
    
    def clear_details(self):
        """Efface les détails"""
        self.detail_employee.setText("--")
        self.detail_period.setText("--")
        self.detail_status.setText("--")
        self.detail_gross.setText("--")
        self.detail_net.setText("--")
    
    def apply_filters(self):
        """Applique les filtres"""
        self.load_payslips()
    
    def clear_filters(self):
        """Efface tous les filtres"""
        self.filter_month.setCurrentIndex(0)
        self.filter_year.setCurrentIndex(0)
        self.filter_status.setCurrentIndex(0)
        self.load_payslips()
    
    def create_payslip(self):
        """Crée une nouvelle fiche de paie"""
        dialog = ModernPayslipDialog(employee_id=self.employee_id, parent=self)
        dialog.payslip_saved.connect(self.refresh_data)
        dialog.exec()
    
    def edit_selected_payslip(self):
        """Modifie la fiche de paie sélectionnée"""
        payslip_id = self.get_selected_payslip_id()
        if not payslip_id:
            self.show_warning("Veuillez sélectionner une fiche de paie")
            return
        
        self.edit_payslip_by_id(payslip_id)
    
    def edit_payslip_by_id(self, payslip_id):
        """Modifie une fiche de paie par son ID"""
        dialog = ModernPayslipDialog(payslip_id=payslip_id, parent=self)
        dialog.payslip_saved.connect(self.refresh_data)
        dialog.exec()
    
    def delete_selected_payslip(self):
        """Supprime la fiche de paie sélectionnée"""
        payslip_id = self.get_selected_payslip_id()
        if not payslip_id:
            self.show_warning("Veuillez sélectionner une fiche de paie")
            return
        
        self.delete_payslip_by_id(payslip_id)
    
    def delete_payslip_by_id(self, payslip_id):
        """Supprime une fiche de paie par son ID"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment supprimer cette fiche de paie ?\n"
            "Cette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            with get_session() as session:
                payslip = session.query(Payslip).filter(Payslip.id == payslip_id).first()
                if payslip:
                    session.delete(payslip)
                    session.commit()
                    self.show_success("Fiche de paie supprimée avec succès")
                    self.refresh_data()
        except Exception as e:
            self.show_error(f"Erreur: {str(e)}")
    
    def preview_selected_payslip(self):
        """Aperçu de la fiche sélectionnée"""
        payslip_id = self.get_selected_payslip_id()
        if not payslip_id:
            self.show_warning("Veuillez sélectionner une fiche de paie")
            return
        
        self.preview_payslip_by_id(payslip_id)
    
    def preview_payslip_by_id(self, payslip_id):
        """Aperçu d'une fiche de paie par son ID"""
        try:
            self.status_label.setText("Génération de l'aperçu...")
            
            # Récupérer les données
            with get_session() as session:
                payslip = session.query(Payslip).filter(Payslip.id == payslip_id).first()
                
                if not payslip:
                    self.show_warning("Fiche de paie non trouvée")
                    return
                
                employee = payslip.employee
                
                # Construire les données
                data = {
                    'employee': {
                        'name': employee.nom_complet if employee else "Inconnu",
                        'matricule': employee.code_employe if employee else "",
                        'first_name': employee.prenom if employee else "",
                        'last_name': employee.nom if employee else "",
                        'address': employee.adresse if employee else "",
                        'phone': employee.telephone if employee else "",
                        'position': employee.poste if employee else "Non spécifié",
                        'hire_date': employee.date_embauche if employee else None,
                        'birth_date': employee.date_naissance if employee else None,
                        'family_status': employee.situation_familiale if employee else "Célibataire",
                        'social_number': employee.numero_secu if employee else "N/A"
                    },
                    'payslip': {
                        'period': f"{payslip.period_month:02d}/{payslip.period_year}",
                        'period_month': payslip.period_month,
                        'period_year': payslip.period_year,
                        'generation_date': payslip.date_generation or datetime.now(),
                        'base_salary': payslip.base_salary or Decimal('0'),
                        'working_days': payslip.working_days or 22,
                        'actual_days': payslip.actual_worked_days or payslip.working_days or 22,
                        'overtime_hours': payslip.overtime_hours or 0,
                        'overtime_rate': payslip.overtime_rate or Decimal('0'),
                        'overtime_amount': payslip.overtime_amount or Decimal('0'),
                        'bonus': payslip.bonus_amount or Decimal('0'),
                        'bonus_description': payslip.bonus_description or "",
                        'allowances': payslip.other_allowances or Decimal('0'),
                        'cnass': payslip.cnass_deduction or Decimal('0'),
                        'tax': payslip.tax_deduction or Decimal('0'),
                        'advance': payslip.advance_deduction or Decimal('0'),
                        'other_deductions': payslip.other_deductions or Decimal('0'),
                        'deduction_description': payslip.deduction_description or "",
                        'gross_salary': payslip.gross_salary or Decimal('0'),
                        'total_deductions': payslip.total_deductions or Decimal('0'),
                        'net_salary': payslip.net_salary or Decimal('0'),
                        'status': payslip.status or "BROUILLON"
                    }
                }
                
                # Générer le PDF
                output_path = self.pdf_service.generate_payslip(data)
                
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
                
                self.status_label.setText(f"Aperçu généré: {os.path.basename(output_path)}")
        except Exception as e:
            self.show_error(f"Erreur de génération: {str(e)}")
            self.status_label.setText("Erreur")
    
    def export_selected_payslip_pdf(self):
        """Exporte la fiche sélectionnée en PDF"""
        payslip_id = self.get_selected_payslip_id()
        if not payslip_id:
            self.show_warning("Veuillez sélectionner une fiche de paie")
            return
        
        # Demander l'emplacement de sauvegarde
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le PDF",
            f"Fiche_Paie_{payslip_id}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if not file_name:
            return
        
        try:
            self.status_label.setText("Export en cours...")
            
            # Récupérer les données
            with get_session() as session:
                payslip = session.query(Payslip).filter(Payslip.id == payslip_id).first()
                
                if not payslip:
                    self.show_warning("Fiche de paie non trouvée")
                    return
                
                employee = payslip.employee
                
                # Construire les données
                data = {
                    'employee': {
                        'name': employee.nom_complet if employee else "Inconnu",
                        'matricule': employee.code_employe if employee else "",
                        'first_name': employee.prenom if employee else "",
                        'last_name': employee.nom if employee else "",
                        'address': employee.adresse if employee else "",
                        'phone': employee.telephone if employee else "",
                        'position': employee.poste if employee else "Non spécifié",
                        'hire_date': employee.date_embauche if employee else None,
                        'birth_date': employee.date_naissance if employee else None,
                        'family_status': employee.situation_familiale if employee else "Célibataire",
                        'social_number': employee.numero_secu if employee else "N/A"
                    },
                    'payslip': {
                        'period': f"{payslip.period_month:02d}/{payslip.period_year}",
                        'period_month': payslip.period_month,
                        'period_year': payslip.period_year,
                        'generation_date': payslip.date_generation or datetime.now(),
                        'base_salary': payslip.base_salary or Decimal('0'),
                        'working_days': payslip.working_days or 22,
                        'actual_days': payslip.actual_worked_days or payslip.working_days or 22,
                        'overtime_hours': payslip.overtime_hours or 0,
                        'overtime_rate': payslip.overtime_rate or Decimal('0'),
                        'overtime_amount': payslip.overtime_amount or Decimal('0'),
                        'bonus': payslip.bonus_amount or Decimal('0'),
                        'bonus_description': payslip.bonus_description or "",
                        'allowances': payslip.other_allowances or Decimal('0'),
                        'cnass': payslip.cnass_deduction or Decimal('0'),
                        'tax': payslip.tax_deduction or Decimal('0'),
                        'advance': payslip.advance_deduction or Decimal('0'),
                        'other_deductions': payslip.other_deductions or Decimal('0'),
                        'deduction_description': payslip.deduction_description or "",
                        'gross_salary': payslip.gross_salary or Decimal('0'),
                        'total_deductions': payslip.total_deductions or Decimal('0'),
                        'net_salary': payslip.net_salary or Decimal('0'),
                        'status': payslip.status or "BROUILLON"
                    }
                }
                
                # Générer le PDF
                self.pdf_service.generate_payslip(data, file_name)
                
                self.show_success(f"PDF exporté avec succès:\n{file_name}")
                self.status_label.setText("Export terminé")
        except Exception as e:
            self.show_error(f"Erreur d'export: {str(e)}")
            self.status_label.setText("Erreur")
    
    def export_batch_pdf(self):
        """Exporte plusieurs fiches de paie en lot"""
        # Sélectionner les mois/années à exporter
        months = []
        for i in range(1, 13):
            months.append(f"{i:02d}")
        
        year = datetime.now().year
        
        # Demander le dossier de sortie
        folder = QFileDialog.getExistingDirectory(
            self, "Sélectionner le dossier de sortie"
        )
        
        if not folder:
            return
        
        try:
            self.status_label.setText("Export batch en cours...")
            
            # Récupérer toutes les fiches
            with get_session() as session:
                payslips = session.query(Payslip).filter(
                    Payslip.status == "PAYÉE"
                ).all()
                
                if not payslips:
                    self.show_warning("Aucune fiche payée à exporter")
                    return
                
                # Préparer les données
                all_data = []
                for payslip in payslips:
                    employee = payslip.employee
                    
                    data = {
                        'employee': {
                            'name': employee.nom_complet if employee else "Inconnu",
                            'matricule': employee.code_employe if employee else "",
                            'first_name': employee.prenom if employee else "",
                            'last_name': employee.nom if employee else "",
                            'address': employee.adresse if employee else "",
                            'phone': employee.telephone if employee else "",
                            'position': employee.poste if employee else "Non spécifié",
                            'hire_date': employee.date_embauche if employee else None,
                            'birth_date': employee.date_naissance if employee else None,
                            'family_status': employee.situation_familiale if employee else "Célibataire",
                            'social_number': employee.numero_secu if employee else "N/A"
                        },
                        'payslip': {
                            'period': f"{payslip.period_month:02d}/{payslip.period_year}",
                            'period_month': payslip.period_month,
                            'period_year': payslip.period_year,
                            'generation_date': payslip.date_generation or datetime.now(),
                            'base_salary': payslip.base_salary or Decimal('0'),
                            'working_days': payslip.working_days or 22,
                            'actual_days': payslip.actual_worked_days or payslip.working_days or 22,
                            'overtime_hours': payslip.overtime_hours or 0,
                            'overtime_rate': payslip.overtime_rate or Decimal('0'),
                            'overtime_amount': payslip.overtime_amount or Decimal('0'),
                            'bonus': payslip.bonus_amount or Decimal('0'),
                            'bonus_description': payslip.bonus_description or "",
                            'allowances': payslip.other_allowances or Decimal('0'),
                            'cnass': payslip.cnass_deduction or Decimal('0'),
                            'tax': payslip.tax_deduction or Decimal('0'),
                            'advance': payslip.advance_deduction or Decimal('0'),
                            'other_deductions': payslip.other_deductions or Decimal('0'),
                            'deduction_description': payslip.deduction_description or "",
                            'gross_salary': payslip.gross_salary or Decimal('0'),
                            'total_deductions': payslip.total_deductions or Decimal('0'),
                            'net_salary': payslip.net_salary or Decimal('0'),
                            'status': payslip.status or "BROUILLON"
                        }
                    }
                    all_data.append(data)
                
                # Générer les PDFs
                generated_files = self.pdf_service.generate_batch_payslips(all_data, folder)
                
                self.show_success(f"{len(generated_files)} fiches exportées avec succès\n{folder}")
                self.status_label.setText("Export batch terminé")
        except Exception as e:
            self.show_error(f"Erreur d'export batch: {str(e)}")
            self.status_label.setText("Erreur")
    
    def change_payslip_status(self):
        """Change le statut d'une fiche de paie"""
        payslip_id = self.get_selected_payslip_id()
        if not payslip_id:
            return
        
        try:
            with get_session() as session:
                payslip = session.query(Payslip).filter(Payslip.id == payslip_id).first()
                if payslip:
                    # Demander le nouveau statut
                    statuses = ["BROUILLON", "VALIDÉE", "PAYÉE", "ANNULÉE"]
                    new_status, ok = QInputDialog.getItem(
                        self, "Changer le statut",
                        "Sélectionnez le nouveau statut:",
                        statuses, statuses.index(payslip.status) if payslip.status in statuses else 0,
                        False
                    )
                    
                    if ok and new_status:
                        old_status = payslip.status
                        payslip.status = new_status
                        session.commit()
                        
                        self.show_info(f"Statut changé: {old_status} → {new_status}")
                        self.refresh_data()
        except Exception as e:
            self.show_error(f"Erreur: {str(e)}")
    
    def show_context_menu(self, pos: QPoint):
        """Affiche le menu contextuel"""
        menu = QMenu(self)
        menu.setStyleSheet(Theme.AppTheme.get_menu_style())
        
        # Actions principales
        act_new = QAction("➕ Nouvelle fiche", self)
        act_new.triggered.connect(self.create_payslip)
        menu.addAction(act_new)
        
        payslip_id = self.get_selected_payslip_id()
        if payslip_id:
            menu.addSeparator()
            
            act_edit = QAction("✏️ Modifier", self)
            act_edit.triggered.connect(self.edit_selected_payslip)
            menu.addAction(act_edit)
            
            act_delete = QAction("🗑️ Supprimer", self)
            act_delete.triggered.connect(self.delete_selected_payslip)
            menu.addAction(act_delete)
            
            menu.addSeparator()
            
            act_preview = QAction("👁️ Aperçu", self)
            act_preview.triggered.connect(self.preview_selected_payslip)
            menu.addAction(act_preview)
            
            act_export = QAction("📄 Exporter PDF", self)
            act_export.triggered.connect(self.export_selected_payslip_pdf)
            menu.addAction(act_export)
            
            act_duplicate = QAction("📋 Dupliquer", self)
            act_duplicate.triggered.connect(self.duplicate_payslip)
            menu.addAction(act_duplicate)
            
            menu.addSeparator()
            
            # Sous-menu pour changer le statut
            status_menu = menu.addMenu("🔄 Changer statut")
            
            statuses = ["BROUILLON", "VALIDÉE", "PAYÉE", "ANNULÉE"]
            for status in statuses:
                act_status = QAction(status, self)
                act_status.triggered.connect(
                    lambda checked, s=status: self.set_payslip_status(payslip_id, s)
                )
                status_menu.addAction(act_status)
        
        menu.addSeparator()
        
        act_refresh = QAction("🔄 Actualiser", self)
        act_refresh.triggered.connect(self.refresh_data)
        menu.addAction(act_refresh)
        
        menu.exec(self.table.table.viewport().mapToGlobal(pos))
    
    def duplicate_payslip(self):
        """Duplique une fiche de paie"""
        payslip_id = self.get_selected_payslip_id()
        if not payslip_id:
            return
        
        try:
            with get_session() as session:
                payslip = session.query(Payslip).filter(Payslip.id == payslip_id).first()
                if payslip:
                    # Créer une copie
                    new_payslip = Payslip()
                    
                    # Copier tous les attributs sauf l'ID et la date
                    for attr in ['employee_id', 'period_month', 'period_year', 
                               'base_salary', 'working_days', 'actual_worked_days',
                               'overtime_hours', 'overtime_rate', 'overtime_amount',
                               'bonus_amount', 'bonus_description', 'other_allowances',
                               'cnass_deduction', 'tax_deduction', 'advance_deduction',
                               'other_deductions', 'deduction_description',
                               'gross_salary', 'total_deductions', 'net_salary']:
                        setattr(new_payslip, attr, getattr(payslip, attr))
                    
                    # Changer le statut à BROUILLON
                    new_payslip.status = "BROUILLON"
                    new_payslip.date_generation = datetime.now()
                    
                    session.add(new_payslip)
                    session.commit()
                    
                    self.show_success("Fiche de paie dupliquée avec succès")
                    self.refresh_data()
        except Exception as e:
            self.show_error(f"Erreur: {str(e)}")
    
    def set_payslip_status(self, payslip_id, status):
        """Définit le statut d'une fiche de paie"""
        try:
            with get_session() as session:
                payslip = session.query(Payslip).filter(Payslip.id == payslip_id).first()
                if payslip:
                    old_status = payslip.status
                    payslip.status = status
                    session.commit()
                    
                    self.show_info(f"Statut changé: {old_status} → {status}")
                    self.refresh_data()
        except Exception as e:
            self.show_error(f"Erreur: {str(e)}")
    
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