# views/dashboard_view.py - VERSION CORRIGÉE
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QFrame, QPushButton, QGroupBox, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from sqlalchemy import func
from datetime import date, datetime, timedelta

from database.db import SessionLocal, get_session
from models.employee import Employee
from models.client import Client
from models.contrat import Contrat
from models.invoice import Invoice


class DashboardView(QWidget):
    """Vue pour le tableau de bord - Version corrigée avec refresh automatique"""
    
    def __init__(self):
        super().__init__()
        self.refresh_timer = None  # Timer pour le refresh automatique
        self.refresh_interval = 30000  # 30 secondes par défaut
        self.init_ui()
        self.load_data()
        self.start_auto_refresh()  # Démarrer le refresh automatique
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Titre avec indicateur de refresh
        title_layout = QHBoxLayout()
        
        title = QLabel("📊 TABLEAU DE BORD")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Grille de statistiques
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Carte 1: Nombre d'employés
        self.card_employees = self.create_stat_card("👷 EMPLOYÉS", "0", "Total employés", "#3498db")
        grid.addWidget(self.card_employees, 0, 0)
        
        # Carte 2: Employés actifs
        self.card_active = self.create_stat_card("✅ ACTIFS", "0", "Employés actifs", "#2ecc71")
        grid.addWidget(self.card_active, 0, 1)
        
        # Carte 3: Salaire total
        self.card_salary = self.create_stat_card("💰 SALAIRE", "0 DA", "Masse salariale mensuelle", "#f39c12")
        grid.addWidget(self.card_salary, 0, 2)
        
        # Carte 4: Salaire moyen
        self.card_avg_salary = self.create_stat_card("📊 MOYENNE", "0 DA", "Salaire moyen", "#9b59b6")
        grid.addWidget(self.card_avg_salary, 0, 3)
        
        # Carte 5: Clients
        self.card_clients = self.create_stat_card("👥 CLIENTS", "0", "Clients actifs", "#e74c3c")
        grid.addWidget(self.card_clients, 1, 0)
        
        # Carte 6: Contrats
        self.card_contrats = self.create_stat_card("📝 CONTRATS", "0", "Contrats en cours", "#1abc9c")
        grid.addWidget(self.card_contrats, 1, 1)
        
        # Carte 7: Factures
        self.card_invoices = self.create_stat_card("🧾 FACTURES", "0", "Factures ce mois", "#34495e")
        grid.addWidget(self.card_invoices, 1, 2)
        
        # Carte 8: Revenus
        self.card_revenue = self.create_stat_card("📈 REVENUS", "0 DA", "Revenus totaux", "#e67e22")
        grid.addWidget(self.card_revenue, 1, 3)
        
        layout.addLayout(grid)
        
        # Section actions rapides
        quick_actions = QGroupBox("⚡ ACTIONS RAPIDES")
        quick_actions.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
                font-size: 16px;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        
        actions_layout = QHBoxLayout()
        
        btn_new_employee = QPushButton("➕ Nouvel employé")
        btn_new_employee.clicked.connect(self.open_new_employee)
        btn_new_employee.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        btn_new_client = QPushButton("👤 Nouveau client")
        btn_new_client.clicked.connect(self.open_new_client)
        btn_new_client.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        btn_new_invoice = QPushButton("🧾 Nouvelle facture")
        btn_new_invoice.clicked.connect(self.open_new_invoice)
        btn_new_invoice.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        
        btn_generate_report = QPushButton("📊 Générer rapport")
        btn_generate_report.clicked.connect(self.generate_report)
        btn_generate_report.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        actions_layout.addWidget(btn_new_employee)
        actions_layout.addWidget(btn_new_client)
        actions_layout.addWidget(btn_new_invoice)
        actions_layout.addWidget(btn_generate_report)
        actions_layout.addStretch()
        
        quick_actions.setLayout(actions_layout)
        layout.addWidget(quick_actions)
        
        # Section récente
        recent_section = QGroupBox("🕐 ACTIVITÉS RÉCENTES")
        recent_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #f39c12;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
                font-size: 16px;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        
        recent_layout = QVBoxLayout()
        self.recent_label = QLabel("Chargement des activités récentes...")
        self.recent_label.setStyleSheet("font-size: 14px; color: #7f8c8d; padding: 10px;")
        recent_layout.addWidget(self.recent_label)
        recent_section.setLayout(recent_layout)
        
        layout.addWidget(recent_section)
        
        # Bouton actualiser
        refresh_layout = QHBoxLayout()
        # Label du dernier refresh
        self.last_refresh_label = QLabel("Dernier refresh: Jamais")
        self.last_refresh_label.setStyleSheet("color: #95a5a6; font-size: 12px;")
        
        btn_refresh = QPushButton("🔄 Actualiser maintenant")
        btn_refresh.clicked.connect(self.manual_refresh)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        refresh_layout.addWidget(self.last_refresh_label)
        refresh_layout.addStretch()
        refresh_layout.addWidget(btn_refresh)
        
        layout.addLayout(refresh_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def create_stat_card(self, title, value, description, color):
        """Crée une carte de statistique avec couleur"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 10px;
                border: 2px solid {color};
                padding: 15px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        
        # Titre
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: bold;
                color: {color};
                text-transform: uppercase;
            }}
        """)
        card_layout.addWidget(title_label)
        
        # Valeur
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px 0;
            }
        """)
        card_layout.addWidget(value_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #95a5a6;
            }
        """)
        card_layout.addWidget(desc_label)
        
        card_layout.addStretch()
        return card
    
    def load_data(self, show_message=True):
        """Charge les données du dashboard avec le bon champ salaire"""
        with get_session() as session:
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"[Dashboard] Chargement des données à {current_time}")

            try:
                # 1. Nombre total d'employés
                total_employees = session.query(Employee).count()
                self.update_card_value(self.card_employees, str(total_employees))

                # 2. Employés actifs
                active_employees = (
                    session.query(Employee)
                    .filter(Employee.est_actif == True)
                    .count()
                )
                self.update_card_value(self.card_active, str(active_employees))

                # 3. Masse salariale mensuelle
                total_salary = session.query(func.sum(Employee.salaire)).scalar() or 0
                self.update_card_value(self.card_salary, f"{float(total_salary):,.0f} DA")

                # 4. Salaire moyen
                if active_employees > 0:
                    avg_salary = session.query(func.avg(Employee.salaire)).scalar() or 0
                    self.update_card_value(self.card_avg_salary, f"{float(avg_salary):,.0f} DA")
                else:
                    self.update_card_value(self.card_avg_salary, "0 DA")

                # 5. Clients actifs
                active_clients = (
                    session.query(Client)
                    .filter(Client.est_actif == True)
                    .count()
                )
                self.update_card_value(self.card_clients, str(active_clients))

                # 6. Contrats en cours
                from models.enums import StatutContrat
                active_contrats = (
                    session.query(Contrat)
                    .filter(Contrat.statut == StatutContrat.ACTIF)
                    .count()
                )
                self.update_card_value(self.card_contrats, str(active_contrats))

                # 7. Factures ce mois-ci
                current_month = datetime.now().month
                current_year = datetime.now().year
                invoices_this_month = (
                    session.query(Invoice)
                    .filter(
                        func.extract('year', Invoice.date) == current_year,
                        func.extract('month', Invoice.date) == current_month,
                    )
                    .count()
                )
                self.update_card_value(self.card_invoices, str(invoices_this_month))

                # 8. Revenus totaux (somme des factures)
                total_revenue = session.query(func.sum(Invoice.total_amount)).scalar() or 0
                self.update_card_value(self.card_revenue, f"{float(total_revenue):,.0f} DA")

                # Activités récentes
                self.load_recent_activities(session)

                # Mettre à jour le timestamp du dernier refresh
                self.last_refresh_label.setText(f"Dernier refresh: {current_time}")

                if show_message:
                    print(f"[Dashboard] Données actualisées à {current_time}")
                    print(f"  • Employés: {total_employees} ({active_employees} actifs)")
                    print(f"  • Clients: {active_clients}")
                    print(f"  • Contrats: {active_contrats}")
                    print(f"  • Factures ce mois: {invoices_this_month}")

            except Exception as e:
                print(f"❌ Erreur chargement dashboard: {e}")
                import traceback
                traceback.print_exc()

                current_time = datetime.now().strftime("%H:%M:%S")
                self.last_refresh_label.setText(f"Dernier refresh: {current_time} (Erreur)")

    def load_recent_activities(self, session):
        """Charge les activités récentes"""
        try:
            activities = []
            
            # 1. Derniers employés ajoutés (7 derniers jours)
            week_ago = date.today() - timedelta(days=7)
            
            recent_employees = session.query(Employee).filter(
                Employee.date_creation >= week_ago
            ).order_by(Employee.date_creation.desc()).limit(3).all()
            
            for emp in recent_employees:
                days_ago = (date.today() - emp.date_creation).days
                if days_ago == 0:
                    time_text = "Aujourd'hui"
                elif days_ago == 1:
                    time_text = "Hier"
                else:
                    time_text = f"Il y a {days_ago} jours"
                
                salaire_info = f" ({emp.salaire:,.0f} DA)" if emp.salaire else ""
                activities.append(f"• 👤 {time_text}: {emp.nom_complet}{salaire_info}")
            
            # 2. Dernières factures (7 derniers jours)
            recent_invoices = session.query(Invoice).filter(
                Invoice.date >= week_ago
            ).order_by(Invoice.date.desc()).limit(2).all()
            
            for inv in recent_invoices:
                client = session.query(Client).get(inv.client_id)
                if client:
                    activities.append(f"• 🧾 {inv.date.strftime('%d/%m')}: "
                                    f"Facture {inv.invoice_number} ({inv.total_amount:,.0f} DA)")
            
            # 3. Derniers clients (7 derniers jours)
            recent_clients = session.query(Client).filter(
                Client.date_creation >= week_ago
            ).order_by(Client.date_creation.desc()).limit(2).all()
            
            for client in recent_clients:
                days_ago = (date.today() - client.date_creation).days
                time_text = "Aujourd'hui" if days_ago == 0 else f"Il y a {days_ago} jours"
                activities.append(f"• 👥 {time_text}: Client {client.nom_complet}")
            
            if activities:
                # Limiter à 6 activités maximum
                activities_text = "\n".join(activities[:6])
            else:
                activities_text = "Aucune activité récente (7 derniers jours)."
            
            self.recent_label.setText(activities_text)
            
        except Exception as e:
            print(f"⚠️  Erreur chargement activités: {e}")
            self.recent_label.setText("Erreur lors du chargement des activités.")
    
    def start_auto_refresh(self):
        """Démarre le timer de refresh automatique"""
        if self.refresh_timer:
            self.refresh_timer.stop()
        
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(self.refresh_interval)
    
    def stop_auto_refresh(self):
        """Arrête le refresh automatique"""
        if self.refresh_timer:
            self.refresh_timer.stop()
            self.refresh_timer = None
            print("[Dashboard] Auto-refresh arrêté")
    
    def change_refresh_interval(self, interval_text):
        """Change l'intervalle de refresh"""
        intervals = {
            "Désactivé": 0,
            "10 secondes": 10000,
            "30 secondes": 30000,
            "1 minute": 60000,
            "5 minutes": 300000,
            "10 minutes": 600000
        }
        
        new_interval = intervals.get(interval_text, 30000)
        
        if new_interval == 0:
            self.stop_auto_refresh()
        else:
            self.refresh_interval = new_interval
            self.start_auto_refresh()
    
    def manual_refresh(self):
        """Refresh manuel avec animation"""
        # Animation du bouton
        btn = self.sender()
        if btn:
            original_text = btn.text()
            btn.setText("🔄 Actualisation...")
            btn.setEnabled(False)
        
        # Effectuer le refresh
        self.load_data()
        
        # Restaurer le bouton après un court délai
        if btn:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(500, lambda: self.restore_refresh_button(btn, original_text))
    
    def restore_refresh_button(self, button, text):
        """Restore le bouton après refresh"""
        button.setText(text)
        button.setEnabled(True)
    
    def auto_refresh(self):
        """Refresh automatique déclenché par le timer"""
        print(f"[Dashboard] Auto-refresh à {datetime.now().strftime('%H:%M:%S')}")
        self.load_data(show_message=False)
    
    def update_card_value(self, card, value):
        """Met à jour la valeur d'une carte"""
        # Trouve le label de valeur dans la carte (2ème widget)
        layout = card.layout()
        if layout and layout.count() >= 2:
            value_label = layout.itemAt(1).widget()
            if value_label and isinstance(value_label, QLabel):
                value_label.setText(str(value))
    
    def open_new_employee(self):
        """Ouvre la fenêtre pour ajouter un nouvel employé"""
        try:
            from views.employees.employee_dialog import EmployeeDialog
            dialog = EmployeeDialog(parent=self)
            
            # Connecter le signal si la méthode existe
            if hasattr(dialog, 'employee_saved'):
                dialog.employee_saved.connect(self.load_data)
            
            dialog.exec()
        except ImportError as e:
            QMessageBox.warning(self, "Erreur", 
                f"Impossible d'ouvrir la vue employés:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", 
                f"Erreur inattendue:\n{str(e)}")
    
    def open_new_client(self):
        """Ouvre la fenêtre pour ajouter un nouveau client"""
        try:
            from views.clients.clients_view import ClientDialog
            dialog = ClientDialog(parent=self)
            if hasattr(dialog, 'client_saved'):
                dialog.client_saved.connect(self.load_data)
            dialog.exec()
        except ImportError as e:
            QMessageBox.warning(self, "Information", 
                "Fonctionnalité 'Nouveau client' à implémenter")
    
    def open_new_invoice(self):
        """Ouvre la fenêtre pour créer une nouvelle facture"""
        try:
            from views.invoices.invoice_dialog import InvoiceDialog
            dialog = InvoiceDialog(parent=self)
            if hasattr(dialog, 'invoice_saved'):
                dialog.invoice_saved.connect(self.load_data)
            dialog.exec()
        except ImportError as e:
            QMessageBox.warning(self, "Information", 
                "Fonctionnalité 'Nouvelle facture' à implémenter")
    
    def generate_report(self):
        """Génère un rapport"""
        try:
            from views.invoices.rapport_dialog import RapportDialog
            dialog = RapportDialog(self)
            dialog.exec()
        except ImportError as e:
            QMessageBox.warning(self, "Information", 
                f"Module de rapport non disponible:\n{str(e)}")
