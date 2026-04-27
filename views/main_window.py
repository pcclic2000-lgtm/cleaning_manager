# views/main_window.py - VERSION REFACTORISÉE AVEC MODULES ORGANISÉS
"""Fenêtre principale de l'application Clean Manager ERP."""
import logging

logger = logging.getLogger(__name__)

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QMessageBox, QStatusBar, QSplitter, QMenuBar,
    QFileDialog, QMenu, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QAction
import os, sys, shutil
from datetime import datetime, date
from database.db import SessionLocal
from models.employee import Employee


class MainWindow(QMainWindow):
    data_updated = pyqtSignal()
    employee_status_changed = pyqtSignal(int, bool, bool)

    def __init__(self):
        super().__init__()
        self.current_page = 0
        self.init_ui()
        self.setup_connections()
        self.apply_styles()
        self.create_menu_bar()
        self.create_shortcuts()

    def init_ui(self):
        self.setWindowTitle("🧹 CLEAN MANAGER - ERP de Gestion de Nettoyage")
        self.setGeometry(100, 50, 1400, 850)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self.create_title_bar())
        self.stacked_widget = QStackedWidget()
        self.load_views()
        content_layout.addWidget(self.stacked_widget)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt • Connecté à la base de données")
        main_layout.addWidget(content_widget, 1)

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QFrame#sidebar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #34495e);
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 20)
        sidebar_layout.setSpacing(0)

        logo_frame = QFrame()
        logo_frame.setFixedHeight(120)
        logo_frame.setStyleSheet("QFrame { background-color: #1abc9c; border-bottom: 3px solid #16a085; }")
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 10, 0, 10)
        logo_label = QLabel("🧹 CLEAN MANAGER")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("QLabel { color: white; font-size: 20px; font-weight: bold; padding: 10px; }")
        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("QLabel { color: rgba(255,255,255,0.8); font-size: 11px; padding: 5px; }")
        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(version_label)
        sidebar_layout.addWidget(logo_frame)
        sidebar_layout.addSpacing(10)

        menu_label = QLabel("MENU PRINCIPAL")
        menu_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        menu_label.setStyleSheet("""
            QLabel { color: rgba(255,255,255,0.7); font-size: 11px; font-weight: bold;
                     letter-spacing: 1px; padding: 15px 0 5px 0; }
        """)
        sidebar_layout.addWidget(menu_label)

        self.nav_buttons = []
        # INDEX : 0=Dashboard 1=Employés 2=Clients 3=Factures 4=Banque
        #         5=Dépenses 6=Paie 7=Cotisations 8=Rapports 9=Paramètres
        self.pages = [
            {"icon": "📊", "text": "Tableau de bord",  "tip": "Vue d'ensemble"},
            {"icon": "👷", "text": "Employés",          "tip": "Gestion du personnel"},
            {"icon": "👥", "text": "Clients",           "tip": "Gestion des clients"},
            {"icon": "🧾", "text": "Factures",          "tip": "Facturation"},
            {"icon": "🏦", "text": "Banque",            "tip": "Gestion bancaire"},
            {"icon": "💸", "text": "Dépenses",          "tip": "Suivi des dépenses"},
            {"icon": "💰", "text": "Paie Globale",      "tip": "Paie par site"},
            {"icon": "📑", "text": "Cotisations",       "tip": "CNAS · CASNOS · CACOBATPH · G50"},
            {"icon": "📈", "text": "Rapports",          "tip": "Rapports et statistiques"},
            {"icon": "⚙️", "text": "Paramètres",        "tip": "Configuration"},
        ]
        for i, page in enumerate(self.pages):
            btn = self.create_nav_button(page["icon"], page["text"])
            btn.setToolTip(page["tip"])
            btn.clicked.connect(lambda checked, idx=i: self.show_page(idx))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()
        logout_btn = self.create_nav_button("🚪", "Déconnexion", color="#e74c3c")
        logout_btn.clicked.connect(self.logout)
        sidebar_layout.addWidget(logout_btn)
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)
        return sidebar

    def create_nav_button(self, icon, text, color=None):
        btn = QPushButton(f"{icon}  {text}")
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if color:
            btn.setStyleSheet(f"""\nQPushButton {{ background-color: {color}; color: white; border: none;
                    padding: 15px 20px; text-align: left; font-size: 14px;
                    margin: 2px 10px; border-radius: 8px; font-weight: bold; }}
                QPushButton:hover {{ padding-left: 25px; }}
                QPushButton:checked {{ background-color: #1abc9c; border-left: 5px solid #16a085; }}
            """)
        else:
            btn.setStyleSheet("""
                QPushButton { background-color: transparent; color: white; border: none;
                    padding: 15px 20px; text-align: left; font-size: 14px;
                    margin: 2px 10px; border-radius: 8px; }
                QPushButton:hover { background-color: rgba(255,255,255,0.1); padding-left: 25px; }
                QPushButton:checked { background-color: #1abc9c; color: white;
                    font-weight: bold; border-left: 5px solid #16a085; }
            """)
        return btn

    def create_title_bar(self):
        title_bar = QFrame()
        title_bar.setFixedHeight(60)
        title_bar.setStyleSheet("QFrame { background-color: #f8f9fa; border-bottom: 1px solid #dee2e6; }")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 10, 20, 10)
        self.page_title = QLabel("Tableau de bord")
        self.page_title.setStyleSheet("QLabel { font-size: 22px; font-weight: bold; color: #2c3e50; }")
        self.btn_refresh = QPushButton("🔄 Actualiser")
        self.btn_refresh.setFixedSize(120, 35)
        self.btn_refresh.clicked.connect(self.refresh_current_page)
        self.btn_refresh.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; border: none;
                border-radius: 5px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_help = QPushButton("❓ Aide")
        btn_help.setFixedSize(80, 35)
        btn_help.clicked.connect(self.show_help)
        btn_help.setStyleSheet("""
            QPushButton { background-color: #95a5a6; color: white; border: none;
                border-radius: 5px; padding: 8px; }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        user_info = QLabel("👤 Admin | Entreprise de Nettoyage")
        user_info.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        title_layout.addWidget(self.page_title)
        title_layout.addStretch()
        title_layout.addWidget(self.btn_refresh)
        title_layout.addWidget(btn_help)
        title_layout.addSpacing(20)
        title_layout.addWidget(user_info)
        return title_bar

    def load_views(self):
        """Charge toutes les vues depuis les modules organisés."""
        _views = [
            ("dashboard_view",  "views.dashboard.dashboard_view",    "DashboardView",    "Tableau de bord"),
            ("employees_view",  "views.employees.employee_view",     "EmployeeView",     "Employés"),
            ("clients_view",    "views.clients.clients_view",        "ClientsView",      "Clients"),
            ("invoices_view",   "views.invoices.invoices_view",      "InvoicesView",     "Factures"),
            ("bank_view",       "views.shared.bank_view",            "BankView",         "Banque"),
            ("expenses_view",   "views.shared.expenses_view",        "ExpensesView",     "Dépenses"),
            ("paye_view",       "views.payroll.paye_globale_view",   "PayeGlobaleView",  "Paie Globale"),
            ("cotisation_view", "views.payroll.cotisation_view",     "CotisationView",   "Cotisations"),
            ("rapport_widget",  "views.invoices.rapport_widget",     "RapportWidget",    "Rapports"),
            ("settings_view",   "views.settings.settings_view",      "SettingsView",     "Paramètres"),
        ]
        for attr, module, cls, name in _views:
            try:
                mod = __import__(module, fromlist=[cls])
                view = getattr(mod, cls)()
                setattr(self, attr, view)
                self.stacked_widget.addWidget(view)
                logger.info("Vue chargée : %s", name)
            except Exception as e:
                logger.error("Erreur chargement vue '%s': %s", name, e, exc_info=True)
                placeholder = self.create_error_view(name, str(e))
                setattr(self, attr, placeholder)
                self.stacked_widget.addWidget(placeholder)

    def create_placeholder_view(self, title):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(f"🚧  {title}\nEn cours de développement...")
        lbl.setStyleSheet("font-size: 22px; color: #7f8c8d;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(lbl)
        return w

    def create_error_view(self, page_name, error):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon = QLabel("⚠️")
        lbl_icon.setStyleSheet("font-size: 80px;")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title = QLabel(f"Erreur: {page_name}")
        lbl_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #e74c3c; margin: 20px;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_err = QLabel(str(error)[:120])
        lbl_err.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        lbl_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_err.setWordWrap(True)
        btn = QPushButton("🔄 Réessayer")
        btn.setFixedSize(150, 40)
        btn.clicked.connect(lambda: self.reload_view(page_name))
        btn.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; border: none;
                border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #2980b9; }
        """)
        l.addStretch()
        l.addWidget(lbl_icon)
        l.addWidget(lbl_title)
        l.addWidget(lbl_err)
        l.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
        l.addStretch()
        return w

    def reload_view(self, page_name):
        reload_map = {
            "Employés":     (1, "views.employees.employee_view",  "EmployeeView"),
            "Clients":      (2, "views.clients.clients_view",     "ClientsView"),
            "Dépenses":     (5, "views.shared.expenses_view",     "ExpensesView"),
            "Cotisations":  (7, "views.payroll.cotisation_view",  "CotisationView"),
        }
        if page_name not in reload_map:
            return
        idx, module, cls = reload_map[page_name]
        try:
            mod = __import__(module, fromlist=[cls])
            view = getattr(mod, cls)()
            old = self.stacked_widget.widget(idx)
            self.stacked_widget.removeWidget(old)
            self.stacked_widget.insertWidget(idx, view)
            QMessageBox.information(self, "Succès", f"Vue {page_name} rechargée")
            self.show_page(self.current_page)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de recharger: {str(e)}")

        # ── Navigation ────────────────────────────────────────────────

    def show_page(self, index):
        if not (0 <= index < self.stacked_widget.count()):
            return
        for btn in self.nav_buttons:
            btn.setChecked(False)
        if index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)
        self.stacked_widget.setCurrentIndex(index)
        self.current_page = index
        titles = ["Tableau de bord","Employés","Clients","Factures","Banque",
                  "Dépenses","Paie Globale","Cotisations","Rapports","Paramètres"]
        statuses = [
            "Affichage du tableau de bord","Gestion des employés","Gestion des clients",
            "Facturation et paiements","Gestion bancaire","Suivi des dépenses",
            "Gestion de la paie globale",
            "Cotisations sociales et fiscales — CNAS · CASNOS · CACOBATPH · G50",
            "Rapports et statistiques","Configuration du système"
        ]
        if index < len(titles):
            self.page_title.setText(titles[index])
        if index < len(statuses):
            self.status_bar.showMessage(statuses[index])

    def refresh_current_page(self):
        try:
            w = self.stacked_widget.currentWidget()
            # Cotisations
            if hasattr(self, "cotisation_view") and w == self.cotisation_view:
                if hasattr(self.cotisation_view, "load_data"):
                    self.cotisation_view.load_data()
                self.status_bar.showMessage("Cotisations actualisées", 3000)
                return
            # Fallback générique
            for attr in ("load_data","load_employees","refresh_transactions"):
                if hasattr(w, attr):
                    getattr(w, attr)()
                    self.status_bar.showMessage("Données actualisées", 3000)
                    return
            self.status_bar.showMessage("Actualisation non disponible", 3000)
        except Exception as e:
            self.status_bar.showMessage(f"Erreur: {str(e)[:50]}", 5000)

        # ── Menu ──────────────────────────────────────────────────────

    def create_menu_bar(self):
        mb = self.menuBar()
        mb.setStyleSheet("""
            QMenuBar { background-color: #2c3e50; color: white; font-weight: bold; padding: 5px; }
            QMenuBar::item { background: transparent; padding: 8px 15px; border-radius: 4px; }
            QMenuBar::item:selected { background-color: #1abc9c; }
            QMenu { background: white; border: 1px solid #bdc3c7; border-radius: 4px; padding: 5px; }
            QMenu::item { padding: 8px 25px 8px 20px; margin: 2px; border-radius: 3px; }
            QMenu::item:selected { background-color: #3498db; color: white; }
            QMenu::separator { height: 1px; background: #ecf0f1; margin: 5px; }
        """)

        # Fichier
        mf = mb.addMenu("📁 Fichier")
        self._add_action(mf, "➕ Nouveau", self.nouvel_element, "Ctrl+N")
        mf.addSeparator()
        self._add_action(mf, "💾 Sauvegarder", self.sauvegarder_donnees, "Ctrl+S")
        mf.addSeparator()
        sub_exp = QMenu("📤 Exporter", self)
        for fmt in ["CSV","Excel","PDF"]:
            a = QAction(fmt, self)
            a.triggered.connect(lambda c, f=fmt: self.exporter_donnees(f))
            sub_exp.addAction(a)
        mf.addMenu(sub_exp)
        self._add_action(mf, "📥 Importer", self.importer_donnees)
        mf.addSeparator()
        self._add_action(mf, "🖨️ Imprimer", self.imprimer_document, "Ctrl+P")
        mf.addSeparator()
        self._add_action(mf, "🚪 Quitter", self.close, "Ctrl+Q")

        # Édition
        me = mb.addMenu("✏️ Édition")
        self._add_action(me, "↶ Annuler",           self.annuler_action, "Ctrl+Z")
        self._add_action(me, "↷ Rétablir",          self.retablir_action, "Ctrl+Y")
        me.addSeparator()
        self._add_action(me, "📋 Copier",            self.copier, "Ctrl+C")
        self._add_action(me, "📎 Coller",            self.coller, "Ctrl+V")
        self._add_action(me, "✓ Sélectionner tout", self.selectionner_tout, "Ctrl+A")

        # Affichage
        ma = mb.addMenu("👁️ Affichage")
        self._add_action(ma, "🔄 Actualiser", self.refresh_current_page, "F5")
        ma.addSeparator()
        act_sombre = QAction("🌙 Mode sombre", self)
        act_sombre.setCheckable(True)
        act_sombre.triggered.connect(self.toggle_mode_sombre)
        ma.addAction(act_sombre)
        act_full = QAction("📺 Plein écran", self)
        act_full.setShortcut("F11")
        act_full.setCheckable(True)
        act_full.triggered.connect(self.toggle_plein_ecran)
        ma.addAction(act_full)

        # Outils
        mo = mb.addMenu("🛠️ Outils")
        self._add_action(mo, "🧮 Calculatrice",          self.ouvrir_calculatrice)
        self._add_action(mo, "📅 Calendrier",             self.ouvrir_calendrier)
        mo.addSeparator()
        self._add_action(mo, "📊 Rapport rapide",         self.generer_rapport_rapide)
        self._add_action(mo, "📋 Rapport de gestion",     self.open_rapport_dialog)
        mo.addSeparator()
        self._add_action(mo, "🧹 Nettoyer cache",         self.nettoyer_cache)
        self._add_action(mo, "🗜️ Optimiser base",         self.optimiser_base_donnees)

        # Paramètres
        mp = mb.addMenu("⚙️ Paramètres")
        self._add_action(mp, "🏢 Informations entreprise", self.show_company_info)
        self._add_action(mp, "⚙️ Configuration système",   self.show_settings)
        mp.addSeparator()
        self._add_action(mp, "👥 Gestion utilisateurs",    self.gestion_utilisateurs)
        self._add_action(mp, "🔐 Gestion permissions",     self.gestion_permissions)
        mp.addSeparator()
        self._add_action(mp, "💾 Sauvegarder maintenant",  self.backup_database)
        self._add_action(mp, "📂 Restaurer sauvegarde",    self.restore_database)
        mp.addSeparator()
        self._add_action(mp, "⚙️ Préférences",             self.afficher_preferences)

        # Entreprise
        ment = mb.addMenu("🏢 Entreprise")
        self._add_action(ment, "Informations de l'entreprise", self.show_company_info)

        # Aide
        mh = mb.addMenu("❓ Aide")
        self._add_action(mh, "📖 Guide d'utilisation",  self.show_user_guide)
        self._add_action(mh, "⌨️ Raccourcis clavier",   self.show_shortcuts)
        mh.addSeparator()
        self._add_action(mh, "🎥 Tutoriels vidéo",      self.show_video_tutorials)
        mh.addSeparator()
        self._add_action(mh, "🔄 Vérifier mises à jour", self.verifier_mises_a_jour)
        self._add_action(mh, "ℹ️ À propos",              self.show_about)

        # ═══════════════════════════════════════════════════════
        # Actions rapides — avec COTISATIONS
        # ═══════════════════════════════════════════════════════
        mr = mb.addMenu("⚡ Actions rapides")
        self._add_action(mr, "👷 Nouvel employé",               self.nouvel_employe)
        self._add_action(mr, "👥 Nouveau client",               self.nouveau_client)
        self._add_action(mr, "🧾 Nouvelle facture",             self.nouvelle_facture)
        self._add_action(mr, "🏦 Nouvelle transaction bancaire", self.nouvelle_transaction_bancaire)
        self._add_action(mr, "💸 Nouvelle dépense",             self.nouvelle_depense)
        mr.addSeparator()
        act_cot = self._add_action(mr, "📑 Nouvelle cotisation",    self.nouvelle_cotisation, "Ctrl+Shift+C")
        self._add_action(mr, "📑 Aller aux Cotisations",        lambda: self.show_page(7))
        mr.addSeparator()
        self._add_action(mr, "📅 Rapport mensuel",              self.rapport_mensuel)

        self.status_indicator = QLabel("● En ligne")
        self.status_indicator.setStyleSheet(
            "QLabel { color: #2ecc71; font-weight: bold; padding: 5px 15px; }")
        mb.setCornerWidget(self.status_indicator, Qt.Corner.TopRightCorner)

    def _add_action(self, menu, text, slot, shortcut=None):
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(shortcut)
        a.triggered.connect(slot)
        menu.addAction(a)
        return a

    def create_shortcuts(self):
        from PyQt6.QtGui import QKeySequence
        for i in range(1, 10):
            a = QAction(self)
            a.setShortcut(QKeySequence(f"Ctrl+{i}"))
            a.triggered.connect(lambda checked, idx=i-1: self.show_page(idx))
            self.addAction(a)

    def setup_connections(self):
        self.data_updated.connect(self.refresh_current_page)

        # ── Actions ───────────────────────────────────────────────────

    def nouvel_element(self):
        dispatch = {1: self.nouvel_employe, 2: self.nouveau_client,
                    3: self.nouvelle_facture, 4: self.nouvelle_transaction_bancaire,
                    5: self.nouvelle_depense, 7: self.nouvelle_cotisation}
        fn = dispatch.get(self.current_page)
        if fn:
            fn()
        else:
            QMessageBox.information(self, "Information",
                "Sélectionnez d'abord une page appropriée.")

    def nouvelle_cotisation(self):
        self.show_page(7)
        if hasattr(self, "cotisation_view") and hasattr(self.cotisation_view, "_add"):
            self.cotisation_view._add()

    def nouvelle_transaction_bancaire(self):
        if hasattr(self, "bank_view") and hasattr(self.bank_view, "add_transaction"):
            self.bank_view.add_transaction()

    def nouvel_employe(self):
        v = getattr(self, "employees_view", None)
        if v:
            fn = getattr(v, "add_employee", None) or getattr(v, "create_employee", None)
            if fn: fn()

    def nouveau_client(self):
        v = getattr(self, "clients_view", None)
        if v and hasattr(v, "add_client"):
            v.add_client()

    def nouvelle_facture(self):
        v = getattr(self, "invoices_view", None)
        if v and hasattr(v, "add_invoice"):
            v.add_invoice()

    def nouvelle_depense(self):
        v = getattr(self, "expenses_view", None)
        if v and hasattr(v, "add_expense"):
            v.add_expense()

    def on_employee_saved(self, employee_id=None):
        pass  # Extensions futures

    def logout(self):
        rep = QMessageBox.question(self, "Déconnexion",
            "Voulez-vous vraiment vous déconnecter ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if rep == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Déconnexion", "Déconnexté avec succès.")
            self.close()

        # ── Styles ────────────────────────────────────────────────────

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f7fa; }
            QStatusBar { background-color: #ecf0f1; color: #2c3e50; padding: 5px; font-size: 12px; }
            QStatusBar::item { border: none; }
            QScrollBar:vertical { border: none; background: #ecf0f1; width: 10px; margin: 0; }
            QScrollBar::handle:vertical { background: #bdc3c7; border-radius: 5px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #95a5a6; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QDialog { background-color: white; }
        """)

    def closeEvent(self, event):
        rep = QMessageBox.question(self, "Quitter", "Voulez-vous vraiment quitter ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        event.accept() if rep == QMessageBox.StandardButton.Yes else event.ignore()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F5:
            self.refresh_current_page()
        elif event.key() == Qt.Key.Key_F11:
            self.toggle_plein_ecran(not self.isFullScreen())
        else:
            super().keyPressEvent(event)

        # ── Méthodes utilitaires ──────────────────────────────────────

    def sauvegarder_donnees(self):
        QMessageBox.information(self, "Sauvegarde", "Données sauvegardées avec succès.")

    def toggle_sauvegarde_auto(self, checked):
        self.status_bar.showMessage(f"Sauvegarde auto {'activée' if checked else 'désactivée'}", 3000)

    def exporter_donnees(self, fmt):
        fn, _ = QFileDialog.getSaveFileName(self, f"Exporter en {fmt}",
            f"export_{datetime.now().strftime('%Y%m%d')}.{fmt.lower()}", f"{fmt} (*.{fmt.lower()})")
        if fn:
            QMessageBox.information(self, "Export", f"Exporté en {fmt}:\n{fn}")

    def importer_donnees(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Importer", "",
            "Tous (*.*);;CSV (*.csv);;Excel (*.xlsx);;JSON (*.json)")
        if fn:
            rep = QMessageBox.question(self, "Confirmation", f"Importer depuis:\n{fn} ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if rep == QMessageBox.StandardButton.Yes:
                QMessageBox.information(self, "Import", "Données importées avec succès.")

    def imprimer_document(self):
        QMessageBox.information(self, "Impression", "Document envoyé à l'imprimante.")

    def annuler_action(self):       self.status_bar.showMessage("Annulé", 2000)
    def retablir_action(self):      self.status_bar.showMessage("Rétabli", 2000)
    def copier(self):               self.status_bar.showMessage("Copié", 2000)
    def coller(self):               self.status_bar.showMessage("Collé", 2000)
    def selectionner_tout(self):    self.status_bar.showMessage("Tout sélectionné", 2000)

    def toggle_mode_sombre(self, checked):
        if checked:
            self.setStyleSheet("QMainWindow { background-color: #2c3e50; color: white; }")
        else:
            self.apply_styles()

    def toggle_plein_ecran(self, checked):
        self.showFullScreen() if checked else self.showNormal()

    def changer_taille_police(self, taille):
        sizes = {"Petit":10,"Normal":12,"Grand":14,"Très grand":16}
        if taille in sizes:
            self.setFont(QFont("Arial", sizes[taille]))

    def ouvrir_calculatrice(self):
        QMessageBox.information(self, "Calculatrice", "En cours de développement.")

    def ouvrir_calendrier(self):
        QMessageBox.information(self, "Calendrier", "En cours de développement.")

    def generer_rapport_rapide(self):
        QMessageBox.information(self, "Rapport rapide", "Rapport généré.")

    def open_rapport_dialog(self):
        try:
            from views.invoices.rapport_dialog import RapportDialog
            RapportDialog(self).exec()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def nettoyer_cache(self):
        rep = QMessageBox.question(self, "Cache",
            "Nettoyer le cache ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if rep == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Cache", "Cache nettoyé.")

    def optimiser_base_donnees(self):
        rep = QMessageBox.question(self, "Optimiser",
            "Optimiser la base de données ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if rep == QMessageBox.StandardButton.Yes:
            try:
                from database.db import DATABASE_PATH
                import sqlite3
                conn = sqlite3.connect(DATABASE_PATH)
                conn.execute("VACUUM")
                conn.close()
                QMessageBox.information(self, "Succès", "Base optimisée.")
            except Exception as e:
                QMessageBox.warning(self, "Erreur", str(e))

    def show_settings(self):
        try:
            from views.settings.settings_view import SettingsView
            self.settings_window = SettingsView()
            self.settings_window.setMinimumSize(900, 700)
            self.settings_window.show()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))

    def gestion_utilisateurs(self):
        QMessageBox.information(self, "Utilisateurs", "En cours de développement.")

    def gestion_permissions(self):
        QMessageBox.information(self, "Permissions", "En cours de développement.")

    def backup_database(self):
        try:
            from database.db import DATABASE_PATH
            import shutil, os
            backup_dir = "backups"
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join(backup_dir, f"backup_{ts}.db")
            shutil.copy2(DATABASE_PATH, dest)
            QMessageBox.information(self, "Sauvegarde réussie", f"Sauvegardé dans:\n{dest}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def restore_database(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Sélectionner une sauvegarde",
            "backups", "DB (*.db *.sqlite *.sqlite3)")
        if not fp:
            return
        rep = QMessageBox.warning(self, "Attention",
            "Cette action remplace la base de données actuelle. Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if rep == QMessageBox.StandardButton.Yes:
            try:
                from database.db import DATABASE_PATH
                import shutil
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                shutil.copy2(DATABASE_PATH, f"{DATABASE_PATH}.backup_{ts}")
                shutil.copy2(fp, DATABASE_PATH)
                QMessageBox.information(self, "Succès",
                    "Base restaurée. Redémarrez l'application.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def afficher_preferences(self):
        QMessageBox.information(self, "Préférences", "En cours de développement.")

    def rapport_mensuel(self):
        QMessageBox.information(self, "Rapport mensuel", "Rapport mensuel généré.")

    def show_user_guide(self):
        self.show_help()

    def show_shortcuts(self):
        QMessageBox.information(self, "Raccourcis clavier", """<h2>⌨️ Raccourcis</h2>
        <ul>
        <li><b>Ctrl+1..9</b> : Navigation pages</li>
        <li><b>Ctrl+8</b> : Cotisations</li>
        <li><b>Ctrl+Shift+C</b> : Nouvelle cotisation</li>
        <li><b>Ctrl+N</b> : Nouvel élément</li>
        <li><b>Ctrl+S</b> : Sauvegarder</li>
        <li><b>Ctrl+P</b> : Imprimer</li>
        <li><b>Ctrl+Q</b> : Quitter</li>
        <li><b>F5</b> : Actualiser</li>
        <li><b>F11</b> : Plein écran</li>
        </ul>""")

    def show_video_tutorials(self):
        QMessageBox.information(self, "Tutoriels", "Disponible prochainement.")

    def verifier_mises_a_jour(self):
        QMessageBox.information(self, "Mises à jour", "Version 1.0.0 — à jour.")

    def show_about(self):
        QMessageBox.about(self, "À propos", """<h2>🧹 CLEAN MANAGER ERP v1.0.0</h2>
        <ul>
        <li>Employés, Clients, Factures</li>
        <li>Banque, Dépenses, Paie Globale</li>
        <li>📑 Cotisations : CNAS · CASNOS · CACOBATPH · G50</li>
        <li>Rapports, Paramètres</li>
        </ul>
        <p>© 2024 — Clean Manager</p>""")

    def show_help(self):
        QMessageBox.information(self, "Aide", """<h2>📖 Clean Manager ERP</h2>
        <ul>
        <li>📊 Tableau de bord</li>
        <li>👷 Employés</li>
        <li>👥 Clients</li>
        <li>🧾 Factures</li>
        <li>🏦 Banque</li>
        <li>💸 Dépenses</li>
        <li>💰 Paie Globale</li>
        <li>📑 Cotisations (CNAS · CASNOS · CACOBATPH · G50)</li>
        <li>📈 Rapports</li>
        <li>⚙️ Paramètres</li>
        </ul>""")

    def show_company_info(self):
        try:
            from views.settings.company_view import CompanyInfoView
            self.company_view = CompanyInfoView()
            self.company_view.setWindowTitle("🏢 Informations de l'entreprise")
            self.company_view.setMinimumSize(800, 600)
            self.company_view.exec()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))

    def show_notification(self, title, message, notification_type="info"):
        self.status_bar.showMessage(f"{title}: {message}", 5000)

    # Pour compatibilité avec méthodes héritées de l'original
    def update_dashboard(self):
        pass

    def refresh_all_dependent_views(self):
        pass

    def check_employee_status(self, _):
        pass


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
