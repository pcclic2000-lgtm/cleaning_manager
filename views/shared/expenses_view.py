# views/expenses_view.py
"""
Vue Dépenses — version redessinée
Thème : slate foncé + accents ambre, typographie Segoe UI, cartes stats, tableau moderne
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QDateEdit, QTabWidget, QLabel,
    QGroupBox, QHeaderView, QSplitter, QInputDialog,
    QCheckBox, QMenu, QFrame, QSizePolicy,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QCursor
from PyQt6.QtCharts import (
    QChart, QChartView, QBarSeries, QBarSet,
    QBarCategoryAxis, QValueAxis, QPieSeries, QPieSlice
)
import calendar
from datetime import datetime, timedelta
from database.db import SessionLocal, get_session
from models.expense import Expense
from models.bank import BankTransaction, TransactionType, BankAccount



# ══════════════════════════════════════════════════════════════════
# COULEURS SÉMANTIQUES (accents fonctionnels uniquement)
# Le thème visuel est géré par assets/styles.qss
# ══════════════════════════════════════════════════════════════════

# Couleurs sémantiques réutilisées dans le code (statuts, montants, badges)
C_GREEN  = "#27ae60"
C_RED    = "#e74c3c"
C_BLUE   = "#3498db"
C_AMBER  = "#f39c12"
C_PURPLE = "#9b59b6"
C_GRAY   = "#95a5a6"

CAT_COLORS = {
    "Produits":       C_GREEN,
    "Matériel":       C_AMBER,
    "Carburant":      C_RED,
    "Main d'œuvre":   C_BLUE,
    "Sous-traitance": C_PURPLE,
    "Autres":         C_GRAY,
}

PAY_ICONS = {
    "Espèces":        "💵",
    "Virement":       "🏦",
    "Chèque":         "📝",
    "Carte bancaire": "💳",
}


def _make_btn(label: str, color: str, hover: str = "", min_w: int = 0) -> QPushButton:
    b = QPushButton(label)
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    b.setFixedHeight(34)
    if min_w:
        b.setMinimumWidth(min_w)
    if color:
        b.setStyleSheet(f"""
            QPushButton {{
                background: {color}; color: white;
                border: none; padding: 0 16px;
                border-radius: 7px; font-weight: 600; font-size: 12px;
            }}
            QPushButton:hover   {{ background: {hover or color}; }}  /* Supprimer filter */
            QPushButton:disabled {{ background: #95a5a6; }}  /* Opacité remplacée par couleur grise */
        """)
    return b


def _separator() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("color: #dee2e6; background: #dee2e6; max-height:1px;")
    return f


    # ══════════════════════════════════════════════════════════════════
    # STAT CARD
    # ══════════════════════════════════════════════════════════════════

class StatCard(QFrame):
    def __init__(self, icon: str, title: str, value: str = "–", accent: str = C_AMBER):
        super().__init__()
        self.accent = accent
        self.setFixedHeight(96)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(f"""
            QFrame {{
                border-radius: 10px;
                border: 1px solid #dee2e6;
                border-top: 3px solid {accent};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(14)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 26px; color: {accent};")
        icon_lbl.setFixedWidth(36)
        layout.addWidget(icon_lbl)

        texts = QVBoxLayout()
        texts.setSpacing(2)
        self.val_lbl = QLabel(value)
        self.val_lbl.setStyleSheet(f"""
            font-size: 22px; font-weight: 700;
            color: {accent}; font-family: 'Consolas', monospace;
        """)
        ttl = QLabel(title)
        ttl.setStyleSheet(f"font-size: 10px; color: {C_GRAY}; font-weight: 600; letter-spacing: 0.5px;")
        texts.addWidget(self.val_lbl)
        texts.addWidget(ttl)
        layout.addLayout(texts)
        layout.addStretch()

    def update(self, value: str):
        self.val_lbl.setText(value)


        # ══════════════════════════════════════════════════════════════════
        # DIALOG AJOUT / MODIFICATION
        # ══════════════════════════════════════════════════════════════════

class ExpenseDialog(QDialog):
    def __init__(self, expense=None, session=None):
        super().__init__()
        self.expense = expense
        self.session = session if session else SessionLocal()
        self.bank_transaction = None

        self.setWindowTitle("✏️  Modifier dépense" if expense else "➕  Nouvelle dépense")
        self.setModal(True)
        self.setMinimumWidth(580)


        self._build_ui()
        if self.expense:
            self._load_expense()

        # ── Construction ──────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # En-tête
        hdr = QLabel("💰  DÉPENSE" if not self.expense else "💰  MODIFIER DÉPENSE")
        hdr.setStyleSheet("""
            font-size: 16px; font-weight: 700;
            padding-bottom: 4px;
            border-bottom: 2px solid #27ae60;
        """)
        root.addWidget(hdr)

        # Formulaire principal
        grp_main = QGroupBox("INFORMATIONS")
        form = QFormLayout(grp_main)
        form.setSpacing(10)
        form.setContentsMargins(14, 16, 14, 14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.libelle = QLineEdit()
        self.libelle.setPlaceholderText("ex: Achat carburant véhicule...")

        self.categorie = QComboBox()
        self.categorie.addItems([
            "Produits", "Matériel", "Carburant",
            "Main d'œuvre", "Sous-traitance", "Autres"
        ])

        self.montant = QLineEdit()
        self.montant.setPlaceholderText("0.00")
        self.montant.setStyleSheet(f"font-family: 'Consolas'; font-size: 14px; color: {C_AMBER};")

        self.date_depense = QDateEdit()
        self.date_depense.setCalendarPopup(True)
        self.date_depense.setDate(QDate.currentDate())
        self.date_depense.setMaximumDate(QDate.currentDate())

        self.moyen_paiement = QComboBox()
        self.moyen_paiement.addItems(["Espèces", "Virement", "Chèque", "Carte bancaire"])
        self.moyen_paiement.currentTextChanged.connect(self._on_payment_changed)

        self.description = QTextEdit()
        self.description.setPlaceholderText("Description optionnelle...")
        self.description.setFixedHeight(70)

        def _lbl(t): return QLabel(t)
        form.addRow(_lbl("Libellé *"), self.libelle)
        form.addRow(_lbl("Catégorie *"), self.categorie)
        form.addRow(_lbl("Montant (DA) *"), self.montant)
        form.addRow(_lbl("Date *"), self.date_depense)
        form.addRow(_lbl("Paiement"), self.moyen_paiement)
        form.addRow(_lbl("Description"), self.description)
        root.addWidget(grp_main)

        # Section bancaire
        grp_bank = QGroupBox("LIAISON BANCAIRE (optionnel)")
        bank_layout = QVBoxLayout(grp_bank)
        bank_layout.setSpacing(8)
        bank_layout.setContentsMargins(14, 16, 14, 14)

        # Option 1 — nouvelle transaction
        self.chk_new_trans = QCheckBox("Créer une transaction bancaire (retrait)")
        self.chk_new_trans.toggled.connect(self._on_new_trans_toggled)
        bank_layout.addWidget(self.chk_new_trans)

        self.new_trans_widget = QWidget()
        self.new_trans_widget.setEnabled(False)
        nt_form = QFormLayout(self.new_trans_widget)
        nt_form.setContentsMargins(16, 6, 0, 6)
        nt_form.setSpacing(8)

        self.new_trans_account = QComboBox()
        self._load_bank_accounts(self.new_trans_account)
        self.new_trans_cat = QComboBox()
        self._load_bank_categories(self.new_trans_cat)
        self.new_trans_benef = QLineEdit()
        self.new_trans_benef.setPlaceholderText("Bénéficiaire")

        self.btn_create_trans = _make_btn("💳  Créer la transaction", C_BLUE, "#2563EB")
        self.btn_create_trans.setEnabled(False)
        self.btn_create_trans.clicked.connect(self._create_bank_transaction)

        nt_form.addRow(QLabel("Compte:"), self.new_trans_account)
        nt_form.addRow(QLabel("Catégorie:"), self.new_trans_cat)
        nt_form.addRow(QLabel("Bénéficiaire:"), self.new_trans_benef)
        nt_form.addRow("", self.btn_create_trans)
        bank_layout.addWidget(self.new_trans_widget)

        # Séparateur OU
        ou_lbl = QLabel("─── ou ───")
        ou_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bank_layout.addWidget(ou_lbl)

        # Option 2 — transaction existante
        self.chk_existing = QCheckBox("Lier à une transaction existante")
        self.chk_existing.toggled.connect(self._on_existing_toggled)
        bank_layout.addWidget(self.chk_existing)

        self.existing_widget = QWidget()
        self.existing_widget.setEnabled(False)
        ex_layout = QVBoxLayout(self.existing_widget)
        ex_layout.setContentsMargins(16, 6, 0, 6)
        ex_layout.setSpacing(6)

        self.filter_trans = QLineEdit()
        self.filter_trans.setPlaceholderText("🔍  Rechercher par bénéficiaire, description...")
        self.filter_trans.textChanged.connect(self._load_existing_transactions)

        self.existing_combo = QComboBox()
        self.existing_combo.setEnabled(False)
        self.existing_combo.setMinimumHeight(30)
        self.existing_combo.currentIndexChanged.connect(self._show_trans_details)

        self.trans_details = QTextEdit()
        self.trans_details.setReadOnly(True)
        self.trans_details.setFixedHeight(80)
        self.trans_details.setStyleSheet("""
            QTextEdit {
                font-size: 12px;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #dee2e6;
                background-color: #f8f9fa;
            }
        """)

        ex_layout.addWidget(self.filter_trans)
        ex_layout.addWidget(self.existing_combo)
        ex_layout.addWidget(self.trans_details)
        bank_layout.addWidget(self.existing_widget)

        # Status
        self.link_status = QLabel("  Aucune liaison bancaire")
        bank_layout.addWidget(self.link_status)

        root.addWidget(grp_bank)

        # Boutons
        root.addWidget(_separator())
        btns = QHBoxLayout()
        btn_save = _make_btn("💾  Enregistrer", C_GREEN, "#059669", 140)
        btn_cancel = _make_btn("✕  Annuler", "#dee2e6", "#f8f9fa")
        btn_save.clicked.connect(self.save)
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        root.addLayout(btns)

        # ── Méthodes bancaires ────────────────────────────────────────

    def _load_bank_accounts(self, combo):
        try:
            comptes = self.session.query(BankAccount).filter(BankAccount.est_actif == True).all()
            combo.addItem("-- Sélectionnez --", None)
            for c in comptes:
                combo.addItem(f"{c.nom_compte} — {c.banque}  ({c.solde_actuel:,.0f} DA)", c.id)
        except Exception as e:
            print(f"Comptes: {e}")

    def _load_bank_categories(self, combo):
        try:
            from models.bank import BankExpenseCategory
            cats = self.session.query(BankExpenseCategory).filter(BankExpenseCategory.est_actif == True).all()
            combo.addItem("-- Sélectionnez --", None)
            for c in cats:
                combo.addItem(c.nom, c.id)
        except Exception as e:
            print(f"Catégories: {e}")

    def _load_existing_transactions(self):
        try:
            q = self.session.query(BankTransaction).filter(
                BankTransaction.type_transaction == TransactionType.RETRAIT
            ).order_by(BankTransaction.date_transaction.desc())
            txt = self.filter_trans.text().strip()
            if txt:
                q = q.filter(
                    (BankTransaction.beneficiaire.contains(txt)) |
                    (BankTransaction.description.contains(txt))
                )
            trans = q.limit(50).all()
            self.existing_combo.clear()
            self.existing_combo.addItem("-- Sélectionnez --", None)
            for t in trans:
                compte = self.session.get(BankAccount, t.compte_id)
                nom = compte.nom_compte if compte else "?"
                self.existing_combo.addItem(
                    f"[{t.date_transaction.strftime('%d/%m/%y')}]  {nom}  —  "
                    f"{t.beneficiaire or '–'}  —  {t.montant:,.0f} DA", t.id
                )
        except Exception as e:
            print(f"Transactions: {e}")

    def _on_payment_changed(self, method):
        if method in ["Virement", "Chèque", "Carte bancaire"]:
            if not self.chk_new_trans.isChecked() and not self.chk_existing.isChecked():
                r = QMessageBox.question(self, "Liaison bancaire",
                    f"'{method}' est un paiement bancaire.\nCréer une transaction automatiquement ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if r == QMessageBox.StandardButton.Yes:
                    self.chk_new_trans.setChecked(True)

    def _on_new_trans_toggled(self, checked):
        self.new_trans_widget.setEnabled(checked)
        self.new_trans_account.setEnabled(checked)
        self.new_trans_cat.setEnabled(checked)
        self.new_trans_benef.setEnabled(checked)
        self.btn_create_trans.setEnabled(checked and not self.bank_transaction)
        if checked:
            self.chk_existing.setChecked(False)
            self.existing_widget.setEnabled(False)
            if not self.bank_transaction:
                self._set_status("⏳  Nouvelle transaction à créer", C_AMBER)
        else:
            self._update_status()

    def _on_existing_toggled(self, checked):
        self.existing_widget.setEnabled(checked)
        self.existing_combo.setEnabled(checked)
        self.filter_trans.setEnabled(checked)
        if checked:
            self.chk_new_trans.setChecked(False)
            self.new_trans_widget.setEnabled(False)
            self._load_existing_transactions()
            self._set_status("⏳  Sélectionnez une transaction", C_AMBER)
        else:
            self._update_status()

    def _show_trans_details(self):
        tid = self.existing_combo.currentData()
        if not tid:
            self.trans_details.clear()
            return
        try:
            t = self.session.get(BankTransaction, tid)
            c = self.session.get(BankAccount, t.compte_id) if t else None
            lines = []
            if t:
                lines.append(f"Date     : {t.date_transaction.strftime('%d/%m/%Y')}")
                if c: lines.append(f"Compte   : {c.nom_compte} — {c.banque}")
                lines.append(f"Montant  : {t.montant:,.2f} DA")
                if t.beneficiaire: lines.append(f"Bénéf.   : {t.beneficiaire}")
                if t.description:  lines.append(f"Desc.    : {t.description}")
                lines.append(f"Solde ▶  : {t.solde_apres:,.2f} DA")
            self.trans_details.setText("\n".join(lines))
            self._set_status(f"🔗  Transaction #{tid} sélectionnée", C_PURPLE)
        except Exception as e:
            print(e)

    def _create_bank_transaction(self):
        try:
            montant = float(self.montant.text())
            if montant <= 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Montant invalide")
            return
        if not self.new_trans_account.currentData():
            QMessageBox.warning(self, "Erreur", "Sélectionnez un compte")
            return
        try:
            t = BankTransaction(
                compte_id=self.new_trans_account.currentData(),
                date_transaction=datetime.combine(
                    self.date_depense.date().toPyDate(), datetime.now().time()),
                type_transaction=TransactionType.RETRAIT,
                montant=montant,
                categorie_id=self.new_trans_cat.currentData(),
                beneficiaire=self.new_trans_benef.text() or None,
                description=f"Dépense: {self.libelle.text()}",
            )
            compte = self.session.get(BankAccount, t.compte_id)
            if compte:
                t.solde_apres = compte.solde_actuel - montant
                compte.solde_actuel = t.solde_apres
            self.session.add(t)
            self.session.flush()
            self.bank_transaction = t
            self._set_status(f"✅  Transaction #{t.id} créée — solde: {compte.solde_actuel:,.0f} DA", C_GREEN)
            self.btn_create_trans.setEnabled(False)
            QMessageBox.information(self, "Succès", "Transaction bancaire créée !")
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))

    def _set_status(self, msg, color):
        self.link_status.setText(f"  {msg}")
        self.link_status.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600;")

    def _update_status(self):
        if self.bank_transaction:
            self._set_status(f"✅  Transaction #{self.bank_transaction.id}", C_GREEN)
        elif self.chk_existing.isChecked() and self.existing_combo.currentData():
            self._set_status(f"🔗  Transaction #{self.existing_combo.currentData()}", C_PURPLE)
        else:
            self._set_status("Aucune liaison bancaire", C_GRAY)

    def _load_expense(self):
        e = self.expense
        self.libelle.setText(e.libelle)
        self.categorie.setCurrentText(e.categorie)
        self.montant.setText(str(e.montant))
        self.date_depense.setDate(QDate(e.date_depense.year, e.date_depense.month, e.date_depense.day))
        self.moyen_paiement.setCurrentText(e.moyen_paiement or "")
        self.description.setText(e.description or "")
        if e.bank_transaction_id:
            self.chk_existing.setChecked(True)
            self._load_existing_transactions()
            idx = self.existing_combo.findData(e.bank_transaction_id)
            if idx >= 0:
                self.existing_combo.setCurrentIndex(idx)

    def save(self):
        if not self.libelle.text().strip():
            QMessageBox.warning(self, "Erreur", "Le libellé est obligatoire")
            return
        try:
            montant = float(self.montant.text())
            if montant <= 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Montant invalide")
            return
        if self.chk_new_trans.isChecked() and not self.bank_transaction:
            QMessageBox.warning(self, "Erreur", "Cliquez sur 'Créer la transaction' d'abord")
            return
        if self.chk_existing.isChecked() and not self.existing_combo.currentData():
            QMessageBox.warning(self, "Erreur", "Sélectionnez une transaction existante")
            return

        try:
            with get_session() as save_session:
                if self.expense and self.expense.id:
                    expense = save_session.get(Expense, self.expense.id)
                else:
                    expense = Expense()

                expense.libelle        = self.libelle.text().strip()
                expense.categorie      = self.categorie.currentText()
                expense.montant        = montant
                expense.date_depense   = self.date_depense.date().toPyDate()
                expense.moyen_paiement = self.moyen_paiement.currentText()
                expense.description    = self.description.toPlainText()

                if self.bank_transaction:
                    expense.bank_transaction_id = self.bank_transaction.id
                elif self.chk_existing.isChecked() and self.existing_combo.currentData():
                    expense.bank_transaction_id = self.existing_combo.currentData()

                if not expense.id:
                    save_session.add(expense)
                save_session.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            if self.session:
                self.session.close()


            # ══════════════════════════════════════════════════════════════════
            # CHARTS WIDGET — redessiné
            # ══════════════════════════════════════════════════════════════════

class ChartsWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self._setup_ui()
        self.refresh_charts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(10)

        # Filtres
        filter_bar = QFrame()
        filter_bar.setFixedHeight(44)
        filter_bar.setStyleSheet("""
            QFrame { 
                border-radius: 8px; 
                border: 1px solid #dee2e6; 
                background-color: white;
            }
        """)
        fb = QHBoxLayout(filter_bar)
        fb.setContentsMargins(14, 0, 14, 0)
        fb.setSpacing(10)

        lbl = QLabel("Période :")
        lbl.setStyleSheet("")
        fb.addWidget(lbl)

        self.filter_period = QComboBox()
        self.filter_period.addItems([
            "Ce mois-ci", "Mois dernier", "Trimestre en cours",
            "Année en cours", "Toutes les périodes"
        ])
        self.filter_period.setFixedWidth(180)
        
        self.filter_period.currentTextChanged.connect(self.refresh_charts)
        fb.addWidget(self.filter_period)
        fb.addStretch()

        btn_refresh = _make_btn("🔄  Actualiser", "#dee2e6", "#f8f9fa")
        btn_refresh.clicked.connect(self.refresh_charts)
        fb.addWidget(btn_refresh)
        layout.addWidget(filter_bar)

        # Stats résumé
        self.stats_lbl = QLabel()
        self.stats_lbl.setStyleSheet(f"""
            background: {"transparent"}; color: {"#2c3e50"};
            font-family: 'Segoe UI'; font-size: 12px;
            border-radius: 8px; border: 1px solid {"#dee2e6"};
            padding: 8px 16px;
        """)
        layout.addWidget(self.stats_lbl)

        # Onglets graphiques
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid #dee2e6; border-radius: 8px; }}
            QTabBar::tab {{ padding: 6px 16px; font-size: 12px; }}
            QTabBar::tab:selected {{ background: {C_AMBER}; color: white; font-weight: 600; }}
            QTabBar::tab:hover {{ background: #dee2e6; }}
        """)

        for attr, title in [
            ("chart_bars",    "📊  Par catégorie"),
            ("chart_pie",     "🥧  Répartition"),
            ("chart_monthly", "📈  Évolution"),
        ]:
            view = QChartView()
            view.setMinimumHeight(260)
            
            setattr(self, attr, view)
            self.tabs.addTab(view, title)

        layout.addWidget(self.tabs)

    def _date_range(self):
        today = QDate.currentDate()
        p = self.filter_period.currentText()
        if p == "Ce mois-ci":
            return QDate(today.year(), today.month(), 1).toPyDate(), today.toPyDate()
        if p == "Mois dernier":
            d = today.addMonths(-1)
            return QDate(d.year(), d.month(), 1).toPyDate(), QDate(d.year(), d.month(), d.daysInMonth()).toPyDate()
        if p == "Trimestre en cours":
            q = (today.month() - 1) // 3
            return QDate(today.year(), q * 3 + 1, 1).toPyDate(), today.toPyDate()
        if p == "Année en cours":
            return QDate(today.year(), 1, 1).toPyDate(), today.toPyDate()
        return None, None

    def refresh_charts(self):
        start, end = self._date_range()
        q = self.session.query(Expense)
        if start and end:
            q = q.filter(Expense.date_depense >= start, Expense.date_depense <= end)
        expenses = q.all()
        self._update_stats(expenses)
        self._chart_bars(expenses)
        self._chart_pie(expenses)
        self._chart_monthly(expenses)

    def _update_stats(self, expenses):
        total = sum(e.montant for e in expenses)
        count = len(expenses)
        avg   = total / count if count else 0
        by_cat = {}
        for e in expenses:
            by_cat[e.categorie] = by_cat.get(e.categorie, 0) + e.montant
        top = max(by_cat.items(), key=lambda x: x[1]) if by_cat else ("—", 0)
        amber = C_AMBER
        self.stats_lbl.setText(
            f"  <b>Total :</b> <span style='color:{amber}'>{total:,.0f} DA</span>"
            f"   •   <b>Nb :</b> {count}"
            f"   •   <b>Moy. :</b> {avg:,.0f} DA"
            f"   •   <b>Top :</b> {top[0]} ({top[1]:,.0f} DA)"
        )

    def _apply_dark_chart(self, chart: QChart):
        chart.setBackgroundBrush(QColor("transparent"))
        chart.setTitleBrush(QColor("#2c3e50"))
        chart.setTitleFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        chart.legend().setLabelBrush(QColor(C_GRAY))
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

    def _chart_bars(self, expenses):
        by_cat = {}
        for e in expenses:
            by_cat[e.categorie] = by_cat.get(e.categorie, 0) + e.montant
        chart = QChart()
        self._apply_dark_chart(chart)
        chart.setTitle("Dépenses par catégorie")
        if not by_cat:
            self.chart_bars.setChart(chart)
            return
        series = QBarSeries()
        bar_set = QBarSet("Montant (DA)")
        cats, vals = list(by_cat.keys()), list(by_cat.values())
        for v in vals:
            bar_set.append(v)
        bar_set.setColor(QColor(C_AMBER))
        bar_set.setBorderColor(QColor(C_AMBER))
        series.append(bar_set)
        chart.addSeries(series)
        ax = QBarCategoryAxis()
        ax.append(cats)
        ax.setLabelsColor(QColor(C_GRAY))
        chart.addAxis(ax, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(ax)
        ay = QValueAxis()
        ay.setLabelFormat("%.0f")
        ay.setLabelsColor(QColor(C_GRAY))
        ay.setGridLineColor(QColor("#dee2e6"))
        chart.addAxis(ay, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(ay)
        self.chart_bars.setChart(chart)

    def _chart_pie(self, expenses):
        by_cat = {}
        for e in expenses:
            by_cat[e.categorie] = by_cat.get(e.categorie, 0) + e.montant
        chart = QChart()
        self._apply_dark_chart(chart)
        chart.setTitle("Répartition")
        if not by_cat:
            self.chart_pie.setChart(chart)
            return
        series = QPieSeries()
        palette = [C_AMBER, C_GREEN, C_RED, C_BLUE, C_PURPLE, C_GRAY]
        total = sum(by_cat.values())
        for i, (cat, val) in enumerate(by_cat.items()):
            pct = val / total * 100
            sl = QPieSlice(f"{cat}\n{pct:.1f}%", val)
            sl.setColor(QColor(palette[i % len(palette)]))
            sl.setLabelColor(QColor("#2c3e50"))
            sl.setLabelVisible(True)
            sl.setLabelArmLengthFactor(0.25)
            sl.setExploded(i == 0)
            series.append(sl)
        chart.addSeries(series)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        self.chart_pie.setChart(chart)

    def _chart_monthly(self, expenses):
        by_month = {}
        for e in expenses:
            k = f"{e.date_depense.year}-{e.date_depense.month:02d}"
            n = f"{calendar.month_abbr[e.date_depense.month]} {e.date_depense.year}"
            entry = by_month.setdefault(k, {"name": n, "total": 0})
            entry["total"] += e.montant
        chart = QChart()
        self._apply_dark_chart(chart)
        chart.setTitle("Évolution mensuelle")
        if not by_month:
            self.chart_monthly.setChart(chart)
            return
        sorted_m = sorted(by_month.items())
        months = [d["name"] for _, d in sorted_m]
        totals = [d["total"] for _, d in sorted_m]
        series = QBarSeries()
        bs = QBarSet("Montant (DA)")
        for t in totals:
            bs.append(t)
        bs.setColor(QColor(C_BLUE))
        bs.setBorderColor(QColor(C_BLUE))
        series.append(bs)
        chart.addSeries(series)
        ax = QBarCategoryAxis()
        ax.append(months)
        ax.setLabelsColor(QColor(C_GRAY))
        chart.addAxis(ax, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(ax)
        ay = QValueAxis()
        ay.setLabelFormat("%.0f")
        ay.setLabelsColor(QColor(C_GRAY))
        ay.setGridLineColor(QColor("#dee2e6"))
        chart.addAxis(ay, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(ay)
        self.chart_monthly.setChart(chart)


        # ══════════════════════════════════════════════════════════════════
        # VUE PRINCIPALE
        # ══════════════════════════════════════════════════════════════════

class ExpensesView(QWidget):
    def __init__(self):
        super().__init__()
        self.session = SessionLocal()
        self._build_ui()
        self.load_data()
        self._update_actions()


        # ── Construction UI ───────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(14)

        root.addLayout(self._build_header())
        root.addLayout(self._build_stat_cards())
        root.addLayout(self._build_toolbar())
        root.addWidget(self._build_filter_bar())

        splitter = QSplitter(Qt.Orientation.Vertical)
        

        # Tableau
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame { border-radius: 12px; border: 1px solid #dee2e6; }
        """)
        tfl = QVBoxLayout(table_frame)
        tfl.setContentsMargins(0, 0, 0, 0)
        tfl.addWidget(self._build_table())
        splitter.addWidget(table_frame)

        # Graphiques
        self.charts = ChartsWidget(self.session)
        splitter.addWidget(self.charts)
        splitter.setSizes([380, 360])

        root.addWidget(splitter)

    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        icon = QLabel("💸")
        icon.setStyleSheet("font-size: 26px;")
        col = QVBoxLayout()
        col.setSpacing(1)
        self._h1 = QLabel("Gestion des Dépenses")
        
        self._h2 = QLabel("Suivi, analyse et liaison bancaire")
        
        col.addWidget(self._h1)
        col.addWidget(self._h2)
        row.addWidget(icon)
        row.addLayout(col)
        row.addStretch()

        return row

    def _build_stat_cards(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        self.card_count  = StatCard("📋", "DÉPENSES",        "–",  C_BLUE)
        self.card_total  = StatCard("💰", "TOTAL (DA)",      "–",  C_AMBER)
        self.card_avg    = StatCard("📊", "MOYENNE (DA)",    "–",  C_PURPLE)
        self.card_month  = StatCard("📅", "CE MOIS (DA)",    "–",  C_GREEN)
        for c in (self.card_count, self.card_total, self.card_avg, self.card_month):
            row.addWidget(c)
        return row

    def _build_toolbar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        self.btn_add    = _make_btn("➕  Ajouter",     C_AMBER,   "#D97706", 110)
        self.btn_edit   = _make_btn("✏️  Modifier",     C_BLUE,    "#2563EB")
        self.btn_delete = _make_btn("🗑️  Supprimer",   C_RED,     "#DC2626")
        self.btn_export = _make_btn("📤  Exporter",    "#dee2e6",  "#f8f9fa")
        self.btn_print  = _make_btn("🖨️  Imprimer",   "#dee2e6",  "#f8f9fa")

        self.btn_add.clicked.connect(self.add_expense)
        self.btn_edit.clicked.connect(self.edit_expense)
        self.btn_delete.clicked.connect(self.delete_expense)
        self.btn_export.clicked.connect(self.export_data)
        self.btn_print.clicked.connect(self.print_report)

        for b in (self.btn_add, self.btn_edit, self.btn_delete, self.btn_export, self.btn_print):
            row.addWidget(b)
        row.addStretch()

        # Compteur
        self.count_lbl = QLabel("0 résultat(s)")
        row.addWidget(self.count_lbl)
        return row

    def _build_filter_bar(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(46)
        bar.setStyleSheet("QFrame { border-radius: 8px; border: 1px solid #dee2e6; }")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Catégorie :"))
        self.filter_cat = QComboBox()
        self.filter_cat.addItem("Toutes")
        self.filter_cat.addItems(["Produits", "Matériel", "Carburant", "Main d'œuvre", "Sous-traitance", "Autres"])
        self.filter_cat.currentTextChanged.connect(self.load_data)
        layout.addWidget(self.filter_cat)

        layout.addWidget(QLabel("Mois :"))
        self.filter_month = QComboBox()
        self.filter_month.addItem("Tous")
        self.filter_month.addItems(["Janvier","Février","Mars","Avril","Mai","Juin",
                                     "Juillet","Août","Septembre","Octobre","Novembre","Décembre"])
        self.filter_month.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.filter_month)

        layout.addWidget(QLabel("Paiement :"))
        self.filter_pay = QComboBox()
        self.filter_pay.addItem("Tous")
        self.filter_pay.addItems(["Espèces", "Virement", "Chèque", "Carte bancaire"])
        self.filter_pay.currentTextChanged.connect(self.load_data)
        layout.addWidget(self.filter_pay)

        layout.addStretch()
        self._filter_bar = bar
        return bar

    def _build_table(self) -> QTableWidget:
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Date", "Libellé", "Catégorie", "Montant (DA)", "Paiement", "Description", "🏦"
        ])
        self.table.setColumnHidden(0, True)

        self.table.setStyleSheet(f"""
            QTableWidget {{
                gridline-color: #dee2e6;
                selection-background-color: {C_GREEN}22;
                selection-color: #155724;
                alternate-background-color: #f8f9fa;
            }}
            QHeaderView::section {{
                font-weight: 700; font-size: 11px;
                border: none; border-right: 1px solid #dee2e6;
                border-bottom: 2px solid {C_GREEN};
                padding: 8px 12px;
            }}
            QTableWidget::item {{
                padding: 6px 12px; border-bottom: 1px solid #f0f0f0;
            }}
        """)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(1, 95)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 130)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(7, 50)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self.edit_expense)
        self.table.itemSelectionChanged.connect(self._update_actions)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)

        return self.table

        # ── Données ───────────────────────────────────────────────────

    def load_data(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        q = self.session.query(Expense)

        cat = self.filter_cat.currentText()
        if cat != "Toutes":
            q = q.filter(Expense.categorie == cat)

        mi = self.filter_month.currentIndex()
        if mi > 0:
            now = datetime.now()
            first = datetime(now.year, mi, 1).date()
            if mi == 12:
                last = datetime(now.year + 1, 1, 1).date() - timedelta(days=1)
            else:
                last = datetime(now.year, mi + 1, 1).date() - timedelta(days=1)
            q = q.filter(Expense.date_depense >= first, Expense.date_depense <= last)

        pay = self.filter_pay.currentText()
        if pay != "Tous":
            q = q.filter(Expense.moyen_paiement == pay)

        expenses = q.order_by(Expense.date_depense.desc()).all()
        self._populate_table(expenses)
        self._update_stat_cards(expenses)
        self.count_lbl.setText(f"{len(expenses)} résultat(s)")
        self.table.setSortingEnabled(True)

        if hasattr(self, "charts"):
            self.charts.refresh_charts()

    def _populate_table(self, expenses):
        RIGHT  = Qt.AlignmentFlag.AlignRight  | Qt.AlignmentFlag.AlignVCenter
        CENTER = Qt.AlignmentFlag.AlignCenter

        for exp in expenses:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 38)

            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(exp.id)))

            # Date
            di = QTableWidgetItem(exp.date_depense.strftime("%d/%m/%Y"))
            di.setTextAlignment(CENTER)
            di.setForeground(QColor(C_GRAY))
            self.table.setItem(row, 1, di)

            # Libellé
            li = QTableWidgetItem(exp.libelle)
            li.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
            li.setForeground(QColor("#2c3e50"))
            self.table.setItem(row, 2, li)

            # Catégorie — badge coloré
            color = CAT_COLORS.get(exp.categorie, C_GRAY)
            ci = QTableWidgetItem(f"  {exp.categorie}  ")
            ci.setTextAlignment(CENTER)
            ci.setForeground(QColor("transparent"))
            ci.setBackground(QColor(color))
            ci.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row, 3, ci)

            # Montant — couleur selon valeur
            m = exp.montant
            mcol = C_RED if m > 100000 else C_AMBER if m > 50000 else C_GREEN
            mi_item = QTableWidgetItem(f"{m:,.0f}".replace(",", " "))
            mi_item.setTextAlignment(RIGHT)
            mi_item.setForeground(QColor(mcol))
            mi_item.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
            self.table.setItem(row, 4, mi_item)

            # Paiement — avec icône
            icon = PAY_ICONS.get(exp.moyen_paiement or "", "")
            pi = QTableWidgetItem(f"{icon}  {exp.moyen_paiement or '–'}")
            pi.setTextAlignment(CENTER)
            pi.setForeground(QColor(C_GRAY))
            self.table.setItem(row, 5, pi)

            # Description
            desc = exp.description or ""
            dei = QTableWidgetItem(desc)
            dei.setForeground(QColor(C_GRAY))
            dei.setToolTip(desc)
            self.table.setItem(row, 6, dei)

            # Bancaire
            if exp.bank_transaction_id:
                bi = QTableWidgetItem("🔗")
                bi.setTextAlignment(CENTER)
                bi.setToolTip(f"Transaction #{exp.bank_transaction_id}")
                bi.setForeground(QColor(C_GREEN))
            else:
                bi = QTableWidgetItem("—")
                bi.setTextAlignment(CENTER)
                bi.setForeground(QColor("#dee2e6"))
            self.table.setItem(row, 7, bi)

    def _update_stat_cards(self, expenses):
        total = sum(e.montant for e in expenses)
        count = len(expenses)
        avg   = total / count if count else 0
        now   = datetime.now()
        month_total = sum(
            e.montant for e in expenses
            if e.date_depense.year == now.year and e.date_depense.month == now.month
        )
        self.card_count.update(str(count))
        self.card_total.update(f"{total:,.0f}".replace(",", " "))
        self.card_avg.update(f"{avg:,.0f}".replace(",", " "))
        self.card_month.update(f"{month_total:,.0f}".replace(",", " "))

        # ── Actions ───────────────────────────────────────────────────

    def _selected_expense(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return self.session.get(Expense, int(item.text())) if item else None

    def _update_actions(self):
        sel = self.table.currentRow() >= 0
        self.btn_edit.setEnabled(sel)
        self.btn_delete.setEnabled(sel)

    def add_expense(self):
        dlg = ExpenseDialog()
        if dlg.exec():
            self.load_data()

    def edit_expense(self):
        exp = self._selected_expense()
        if not exp:
            QMessageBox.warning(self, "Sélection", "Sélectionnez une dépense")
            return
        dlg = ExpenseDialog(exp, session=self.session)
        if dlg.exec():
            self.load_data()

    def delete_expense(self):
        exp = self._selected_expense()
        if not exp:
            return
        msg = f"Supprimer '{exp.libelle}' ({exp.montant:,.0f} DA) ?"
        if exp.bank_transaction_id:
            msg += "\n\n⚠️  La transaction bancaire liée ne sera pas supprimée."
        r = QMessageBox.question(self, "Confirmation", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            try:
                self.session.delete(exp)
                self.session.commit()
                self.load_data()
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Erreur", str(e))

    def export_data(self):
        choice, ok = QInputDialog.getItem(self, "Exporter", "Format :", ["CSV", "Excel", "PDF"], 0, False)
        if ok:
            QMessageBox.information(self, "Export", f"Export {choice} — fonctionnalité à implémenter.")

    def print_report(self):
        QMessageBox.information(self, "Impression", "Impression — fonctionnalité à implémenter.")

    def _context_menu(self, pos):
        menu = QMenu(self)
        
        menu.addAction("➕  Ajouter",   self.add_expense)
        exp = self._selected_expense()
        if exp:
            menu.addSeparator()
            menu.addAction("✏️  Modifier",  self.edit_expense)
            menu.addAction("🗑️  Supprimer", self.delete_expense)
            if exp.bank_transaction_id:
                menu.addSeparator()
                menu.addAction("🔗  Voir transaction bancaire",
                    lambda: self._view_bank_transaction(exp))
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _view_bank_transaction(self, exp):
        if not exp or not exp.bank_transaction_id:
            return
        t = self.session.get(BankTransaction, exp.bank_transaction_id)
        if not t:
            return
        c = self.session.get(BankAccount, t.compte_id)
        QMessageBox.information(self, "Transaction bancaire",
            f"<b>Transaction #{t.id}</b><br><br>"
            f"Compte : {c.nom_compte if c else '?'}<br>"
            f"Date   : {t.date_transaction.strftime('%d/%m/%Y')}<br>"
            f"Montant: {t.montant:,.2f} DA<br>"
            f"Bénéf. : {t.beneficiaire or '—'}<br>"
            f"Solde ▶: {t.solde_apres:,.2f} DA"
        )