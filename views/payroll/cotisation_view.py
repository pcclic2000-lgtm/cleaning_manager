# views/cotisation_view.py
"""
Module Cotisations — CNAS, CASNOS, CACOBATPH, G50
Tableau de bord avec stats + liste filtrée + saisie complète
Hérite du thème global (assets/styles.qss)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QDateEdit, QLabel, QGroupBox,
    QHeaderView, QFrame, QSizePolicy, QDoubleSpinBox,
    QFileDialog, QMenu, QSpinBox, QAbstractItemView,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QCursor, QAction

from datetime import date
from database.db import SessionLocal
from models.cotisation import Cotisation, TypeCotisation, PeriodeCotisation, StatutCotisation
import os


# ══════════════════════════════════════════════════════════════════
# CONSTANTES SÉMANTIQUES
# ══════════════════════════════════════════════════════════════════

C_PAYE    = "#27ae60"
C_ATTENTE = "#f39c12"
C_RETARD  = "#e74c3c"
C_INFO    = "#3498db"
C_GRAY    = "#95a5a6"

# Couleur accent par type de cotisation
TYPE_COLORS = {
    "CNAS":       "#3498db",
    "CASNOS":     "#9b59b6",
    "CACOBATPH":  "#e67e22",
    "G50":        "#1abc9c",
}

TYPE_ICONS = {
    "CNAS":       "👷",
    "CASNOS":     "🏢",
    "CACOBATPH":  "🏗️",
    "G50":        "📋",
}

MOIS_NOMS = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
             "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
MOIS_COURTS = ["", "Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
                "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]


def _btn(label: str, color: str, hover: str = "", min_w: int = 0) -> QPushButton:
    b = QPushButton(label)
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    b.setFixedHeight(34)
    if min_w:
        b.setMinimumWidth(min_w)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {color}; color: white;
            border: none; padding: 0 16px;
            border-radius: 7px; font-weight: 600; font-size: 12px;
        }}
        QPushButton:hover {{ background: {hover or color}; }}
        QPushButton:disabled {{ opacity: 0.5; }}
    """)
    return b


def _separator() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("color: #dee2e6; background: #dee2e6; max-height:1px;")
    return f


    # ══════════════════════════════════════════════════════════════════
    # STAT CARD PAR TYPE DE COTISATION
    # ══════════════════════════════════════════════════════════════════

class CotisationCard(QFrame):
    """Carte résumé pour un type de cotisation."""

    def __init__(self, type_cot: str, parent=None):
        super().__init__(parent)
        self.type_cot = type_cot
        self.accent = TYPE_COLORS.get(type_cot, C_INFO)
        self.setMinimumWidth(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(130)
        self.setStyleSheet(f"""
            QFrame {{
                border-radius: 12px;
                border: 1px solid #dee2e6;
                border-left: 4px solid {self.accent};
            }}
        """)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        # En-tête : icône + nom
        hdr = QHBoxLayout()
        icon_lbl = QLabel(TYPE_ICONS.get(self.type_cot, "📌"))
        icon_lbl.setStyleSheet("font-size: 22px;")
        name_lbl = QLabel(self.type_cot)
        name_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {self.accent}; font-family: 'Segoe UI';"
        )
        hdr.addWidget(icon_lbl)
        hdr.addWidget(name_lbl)
        hdr.addStretch()

        # Statut badge
        self.badge = QLabel("–")
        self.badge.setFixedHeight(20)
        self.badge.setStyleSheet(
            "font-size: 10px; font-weight: 700; padding: 2px 8px;"
            "border-radius: 10px; background: #dee2e6; color: #666;"
        )
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr.addWidget(self.badge)
        layout.addLayout(hdr)

        layout.addWidget(_separator())

        # Montants
        amounts = QHBoxLayout()
        amounts.setSpacing(16)

        col_du = QVBoxLayout()
        col_du.setSpacing(1)
        self.lbl_du_val = QLabel("–")
        self.lbl_du_val.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {self.accent}; font-family: 'Consolas', monospace;"
        )
        lbl_du_txt = QLabel("À PAYER")
        lbl_du_txt.setStyleSheet("font-size: 9px; color: #95a5a6; font-weight: 600; letter-spacing: 0.5px;")
        col_du.addWidget(self.lbl_du_val)
        col_du.addWidget(lbl_du_txt)

        col_paye = QVBoxLayout()
        col_paye.setSpacing(1)
        self.lbl_paye_val = QLabel("–")
        self.lbl_paye_val.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {C_PAYE}; font-family: 'Consolas', monospace;"
        )
        lbl_paye_txt = QLabel("PAYÉ")
        lbl_paye_txt.setStyleSheet("font-size: 9px; color: #95a5a6; font-weight: 600; letter-spacing: 0.5px;")
        col_paye.addWidget(self.lbl_paye_val)
        col_paye.addWidget(lbl_paye_txt)

        col_reste = QVBoxLayout()
        col_reste.setSpacing(1)
        self.lbl_reste_val = QLabel("–")
        self.lbl_reste_val.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {C_RETARD}; font-family: 'Consolas', monospace;"
        )
        lbl_reste_txt = QLabel("RESTE")
        lbl_reste_txt.setStyleSheet("font-size: 9px; color: #95a5a6; font-weight: 600; letter-spacing: 0.5px;")
        col_reste.addWidget(self.lbl_reste_val)
        col_reste.addWidget(lbl_reste_txt)

        amounts.addLayout(col_du)
        amounts.addLayout(col_paye)
        amounts.addLayout(col_reste)
        amounts.addStretch()
        layout.addLayout(amounts)

    def update_data(self, rows: list):
        """Met à jour la carte avec les cotisations du type."""
        if not rows:
            self.lbl_du_val.setText("–")
            self.lbl_paye_val.setText("–")
            self.lbl_reste_val.setText("–")
            self.badge.setText("AUCUNE")
            self.badge.setStyleSheet(
                "font-size: 10px; font-weight: 700; padding: 2px 8px;"
                "border-radius: 10px; background: #dee2e6; color: #666;"
            )
            return

        total_du    = sum(r.montant_du    for r in rows)
        total_paye  = sum(r.montant_paye  for r in rows)
        total_reste = sum(r.solde         for r in rows)

        en_retard = any(r.statut == StatutCotisation.EN_RETARD for r in rows)
        all_paye  = all(r.statut == StatutCotisation.PAYE      for r in rows)

        self.lbl_du_val.setText(f"{total_du:,.0f}")
        self.lbl_paye_val.setText(f"{total_paye:,.0f}")
        self.lbl_reste_val.setText(f"{total_reste:,.0f}")

        if en_retard:
            badge_color, badge_bg = "white", C_RETARD
            badge_txt = "EN RETARD"
        elif all_paye:
            badge_color, badge_bg = "white", C_PAYE
            badge_txt = "À JOUR"
        else:
            badge_color, badge_bg = "white", C_ATTENTE
            badge_txt = "EN COURS"

        self.badge.setText(badge_txt)
        self.badge.setStyleSheet(
            f"font-size: 10px; font-weight: 700; padding: 2px 8px;"
            f"border-radius: 10px; background: {badge_bg}; color: {badge_color};"
        )


        # ══════════════════════════════════════════════════════════════════
        # DIALOG AJOUT / MODIFICATION
        # ══════════════════════════════════════════════════════════════════

class CotisationDialog(QDialog):
    """Formulaire de saisie d'une cotisation."""

    def __init__(self, session, cotisation=None, parent=None):
        super().__init__(parent)
        self.session = session
        self.cotisation = cotisation
        self.setWindowTitle("Nouvelle cotisation" if not cotisation else "Modifier la cotisation")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._build()
        if cotisation:
            self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # En-tête
        hdr = QLabel("📌  COTISATION" if not self.cotisation else "📌  MODIFIER COTISATION")
        hdr.setStyleSheet("""
            font-size: 15px; font-weight: 700;
            padding-bottom: 4px;
            border-bottom: 2px solid #3498db;
        """)
        root.addWidget(hdr)

        # ── Bloc 1 : Identification ───────────────────────────────
        grp_id = QGroupBox("Identification")
        grp_id.setStyleSheet("""
            QGroupBox { font-weight: 700; font-size: 11px; color: #7f8c8d; border: 1px solid #dee2e6;
                        border-radius: 8px; margin-top: 10px; padding-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
        """)
        f_id = QFormLayout(grp_id)
        f_id.setSpacing(8)

        self.combo_type = QComboBox()
        for t in TypeCotisation:
            self.combo_type.addItem(f"{TYPE_ICONS[t.value]}  {t.value}", t.value)
        self.combo_type.currentIndexChanged.connect(self._on_type_changed)

        self.combo_periode = QComboBox()
        self.combo_periode.addItem("Mensuelle",     PeriodeCotisation.MENSUELLE.value)
        self.combo_periode.addItem("Trimestrielle", PeriodeCotisation.TRIMESTRIELLE.value)
        self.combo_periode.addItem("Annuelle",       PeriodeCotisation.ANNUELLE.value)
        self.combo_periode.currentIndexChanged.connect(self._on_periode_changed)

        f_id.addRow("Type :", self.combo_type)
        f_id.addRow("Périodicité :", self.combo_periode)
        root.addWidget(grp_id)

        # ── Bloc 2 : Période ──────────────────────────────────────
        grp_per = QGroupBox("Période concernée")
        grp_per.setStyleSheet(grp_id.styleSheet())
        f_per = QFormLayout(grp_per)
        f_per.setSpacing(8)

        self.spin_annee = QSpinBox()
        self.spin_annee.setRange(2000, 2100)
        self.spin_annee.setValue(date.today().year)

        self.combo_mois = QComboBox()
        for i, m in enumerate(MOIS_NOMS):
            if i > 0:
                self.combo_mois.addItem(m, i)
        self.combo_mois.setCurrentIndex(date.today().month - 1)

        self.combo_trim = QComboBox()
        for i in range(1, 5):
            self.combo_trim.addItem(f"Trimestre {i}", i)

        f_per.addRow("Année :", self.spin_annee)
        self.row_mois_lbl = QLabel("Mois :")
        self.row_trim_lbl = QLabel("Trimestre :")
        f_per.addRow(self.row_mois_lbl, self.combo_mois)
        f_per.addRow(self.row_trim_lbl, self.combo_trim)
        self.combo_trim.hide()
        self.row_trim_lbl.hide()
        root.addWidget(grp_per)

        # ── Bloc 3 : Montants & Statut ────────────────────────────
        grp_mont = QGroupBox("Montants & Statut")
        grp_mont.setStyleSheet(grp_id.styleSheet())
        f_mont = QFormLayout(grp_mont)
        f_mont.setSpacing(8)

        self.spin_du = QDoubleSpinBox()
        self.spin_du.setRange(0, 99_999_999)
        self.spin_du.setDecimals(2)
        self.spin_du.setSuffix("  DA")
        self.spin_du.setGroupSeparatorShown(True)
        self.spin_du.setStyleSheet("font-family: 'Consolas'; font-size: 13px;")

        self.spin_paye = QDoubleSpinBox()
        self.spin_paye.setRange(0, 99_999_999)
        self.spin_paye.setDecimals(2)
        self.spin_paye.setSuffix("  DA")
        self.spin_paye.setGroupSeparatorShown(True)
        self.spin_paye.setStyleSheet(f"font-family: 'Consolas'; font-size: 13px; color: {C_PAYE};")

        self.date_limite = QDateEdit()
        self.date_limite.setCalendarPopup(True)
        self.date_limite.setDate(QDate.currentDate().addMonths(1))
        self.date_limite.setDisplayFormat("dd/MM/yyyy")

        self.date_paiement = QDateEdit()
        self.date_paiement.setCalendarPopup(True)
        self.date_paiement.setDate(QDate.currentDate())
        self.date_paiement.setDisplayFormat("dd/MM/yyyy")
        self.date_paiement.setEnabled(False)

        self.combo_statut = QComboBox()
        self.combo_statut.addItem("⏳  En attente", StatutCotisation.EN_ATTENTE.value)
        self.combo_statut.addItem("✅  Payé",        StatutCotisation.PAYE.value)
        self.combo_statut.addItem("🔴  En retard",   StatutCotisation.EN_RETARD.value)
        self.combo_statut.currentIndexChanged.connect(self._on_statut_changed)

        f_mont.addRow("Montant dû :",          self.spin_du)
        f_mont.addRow("Montant payé :",        self.spin_paye)
        f_mont.addRow("Date limite :",         self.date_limite)
        f_mont.addRow("Date paiement :",       self.date_paiement)
        f_mont.addRow("Statut :",              self.combo_statut)
        root.addWidget(grp_mont)

        # ── Bloc 4 : Pièce justificative ──────────────────────────
        grp_pj = QGroupBox("Pièce justificative")
        grp_pj.setStyleSheet(grp_id.styleSheet())
        f_pj = QFormLayout(grp_pj)
        f_pj.setSpacing(8)

        self.edit_piece = QLineEdit()
        self.edit_piece.setPlaceholderText("N° de reçu ou référence...")

        pj_row = QHBoxLayout()
        self.edit_chemin = QLineEdit()
        self.edit_chemin.setPlaceholderText("Chemin vers la pièce jointe...")
        self.edit_chemin.setReadOnly(True)
        btn_browse = _btn("📁", "#7f8c8d", "#636e72", 36)
        btn_browse.setFixedWidth(36)
        btn_browse.clicked.connect(self._browse_file)
        pj_row.addWidget(self.edit_chemin)
        pj_row.addWidget(btn_browse)

        self.edit_notes = QTextEdit()
        self.edit_notes.setPlaceholderText("Notes complémentaires...")
        self.edit_notes.setFixedHeight(60)

        f_pj.addRow("N° pièce :", self.edit_piece)
        f_pj.addRow("Fichier :", pj_row)
        f_pj.addRow("Notes :", self.edit_notes)
        root.addWidget(grp_pj)

        # ── Boutons ───────────────────────────────────────────────
        root.addWidget(_separator())
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = _btn("✕  Annuler",    "#bdc3c7", "#95a5a6")
        btn_save   = _btn("💾  Enregistrer", C_PAYE,    "#219a52", 140)
        btn_cancel.clicked.connect(self.reject)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

    def _on_type_changed(self, idx):
        """Ajuster la périodicité par défaut selon le type."""
        t = self.combo_type.currentData()
        if t == "G50":
            self.combo_periode.setCurrentIndex(1)  # Trimestrielle
        else:
            self.combo_periode.setCurrentIndex(0)  # Mensuelle

    def _on_periode_changed(self, idx):
        p = self.combo_periode.currentData()
        if p == PeriodeCotisation.MENSUELLE.value:
            self.combo_mois.show();  self.row_mois_lbl.show()
            self.combo_trim.hide();  self.row_trim_lbl.hide()
        elif p == PeriodeCotisation.TRIMESTRIELLE.value:
            self.combo_mois.hide();  self.row_mois_lbl.hide()
            self.combo_trim.show();  self.row_trim_lbl.show()
        else:  # Annuelle
            self.combo_mois.hide();  self.row_mois_lbl.hide()
            self.combo_trim.hide();  self.row_trim_lbl.hide()

    def _on_statut_changed(self, idx):
        is_paye = self.combo_statut.currentData() == StatutCotisation.PAYE.value
        self.date_paiement.setEnabled(is_paye)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner une pièce justificative", "",
            "Documents (*.pdf *.jpg *.jpeg *.png *.doc *.docx);;Tous (*)"
        )
        if path:
            self.edit_chemin.setText(path)

    def _load(self):
        """Charger les données d'une cotisation existante."""
        c = self.cotisation

        # Type
        for i in range(self.combo_type.count()):
            if self.combo_type.itemData(i) == c.type_cotisation.value:
                self.combo_type.setCurrentIndex(i)
                break

        # Période
        for i in range(self.combo_periode.count()):
            if self.combo_periode.itemData(i) == c.periode_type.value:
                self.combo_periode.setCurrentIndex(i)
                break

        self.spin_annee.setValue(c.annee)
        if c.mois:
            for i in range(self.combo_mois.count()):
                if self.combo_mois.itemData(i) == c.mois:
                    self.combo_mois.setCurrentIndex(i)
                    break
        if c.trimestre:
            self.combo_trim.setCurrentIndex(c.trimestre - 1)

        self.spin_du.setValue(c.montant_du)
        self.spin_paye.setValue(c.montant_paye)

        if c.date_limite:
            self.date_limite.setDate(QDate(c.date_limite.year, c.date_limite.month, c.date_limite.day))
        if c.date_paiement:
            self.date_paiement.setDate(QDate(c.date_paiement.year, c.date_paiement.month, c.date_paiement.day))

        for i in range(self.combo_statut.count()):
            if self.combo_statut.itemData(i) == c.statut.value:
                self.combo_statut.setCurrentIndex(i)
                break

        if c.numero_piece:
            self.edit_piece.setText(c.numero_piece)
        if c.chemin_piece:
            self.edit_chemin.setText(c.chemin_piece)
        if c.notes:
            self.edit_notes.setPlainText(c.notes)

    def _save(self):
        if self.spin_du.value() <= 0:
            QMessageBox.warning(self, "Validation", "Le montant dû doit être supérieur à 0.")
            return

        c = self.cotisation or Cotisation()

        c.type_cotisation = TypeCotisation(self.combo_type.currentData())
        c.periode_type    = PeriodeCotisation(self.combo_periode.currentData())
        c.annee           = self.spin_annee.value()
        c.mois            = self.combo_mois.currentData() if self.combo_mois.isVisible() else None
        c.trimestre       = self.combo_trim.currentData() if self.combo_trim.isVisible() else None

        c.montant_du   = self.spin_du.value()
        c.montant_paye = self.spin_paye.value()

        dl = self.date_limite.date()
        c.date_limite = date(dl.year(), dl.month(), dl.day())

        if self.combo_statut.currentData() == StatutCotisation.PAYE.value and self.date_paiement.isEnabled():
            dp = self.date_paiement.date()
            c.date_paiement = date(dp.year(), dp.month(), dp.day())
        else:
            c.date_paiement = None

        c.statut       = StatutCotisation(self.combo_statut.currentData())
        c.numero_piece = self.edit_piece.text().strip() or None
        c.chemin_piece = self.edit_chemin.text().strip() or None
        c.notes        = self.edit_notes.toPlainText().strip() or None

        # Auto-statut si montant payé = montant dû
        if c.montant_paye >= c.montant_du > 0:
            c.statut = StatutCotisation.PAYE
        elif c.date_limite and date.today() > c.date_limite and c.statut != StatutCotisation.PAYE:
            c.statut = StatutCotisation.EN_RETARD

        try:
            if not self.cotisation:
                self.session.add(c)
            self.session.commit()
            self.accept()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erreur", f"Impossible d'enregistrer :\n{e}")


        # ══════════════════════════════════════════════════════════════════
        # VUE PRINCIPALE
        # ══════════════════════════════════════════════════════════════════

class CotisationView(QWidget):

    def __init__(self):
        super().__init__()
        self.session = SessionLocal()
        self._build_ui()
        self.load_data()

        # ── Construction ──────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(14)

        root.addLayout(self._build_header())
        root.addLayout(self._build_cards())
        root.addLayout(self._build_toolbar())
        root.addWidget(self._build_filter_bar())
        root.addWidget(self._build_table())

    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        icon = QLabel("📑")
        icon.setStyleSheet("font-size: 28px;")
        col = QVBoxLayout()
        col.setSpacing(1)
        self._h1 = QLabel("Gestion des Cotisations")
        self._h1.setStyleSheet("font-size: 20px; font-weight: 700; font-family: 'Segoe UI';")
        self._h2 = QLabel("CNAS · CASNOS · CACOBATPH · G50")
        self._h2.setStyleSheet("font-size: 11px; color: #7f8c8d; font-family: 'Segoe UI';")
        col.addWidget(self._h1)
        col.addWidget(self._h2)
        row.addWidget(icon)
        row.addLayout(col)
        row.addStretch()

        # Indicateur résumé
        self.lbl_alerte = QLabel("")
        self.lbl_alerte.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {C_RETARD}; font-family: 'Segoe UI';"
        )
        row.addWidget(self.lbl_alerte)
        return row

    def _build_cards(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        self.cards = {}
        for t in ["CNAS", "CASNOS", "CACOBATPH", "G50"]:
            card = CotisationCard(t)
            self.cards[t] = card
            row.addWidget(card)
        return row

    def _build_toolbar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        self.btn_add    = _btn("➕  Ajouter",   C_INFO,    "#2980b9", 110)
        self.btn_edit   = _btn("✏️  Modifier",   "#8e44ad", "#7d3c98")
        self.btn_delete = _btn("🗑️  Supprimer",  C_RETARD,  "#c0392b")
        self.btn_payer  = _btn("✅  Marquer payé", C_PAYE,  "#219a52", 130)

        self.btn_edit.setEnabled(False)
        self.btn_delete.setEnabled(False)
        self.btn_payer.setEnabled(False)

        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_payer.clicked.connect(self._marquer_paye)

        row.addWidget(self.btn_add)
        row.addWidget(self.btn_edit)
        row.addWidget(self.btn_delete)
        row.addWidget(self.btn_payer)
        row.addStretch()

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("font-size: 12px; color: #7f8c8d; font-family: 'Segoe UI';")
        row.addWidget(self.count_lbl)
        return row

    def _build_filter_bar(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(44)
        bar.setStyleSheet("QFrame { border-radius: 8px; border: 1px solid #dee2e6; }")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)

        def lbl(txt):
            l = QLabel(txt)
            l.setStyleSheet("font-size: 11px; color: #7f8c8d; font-family: 'Segoe UI';")
            return l

        layout.addWidget(lbl("Type :"))
        self.filter_type = QComboBox()
        self.filter_type.setFixedWidth(130)
        self.filter_type.addItem("Tous", None)
        for t in TypeCotisation:
            self.filter_type.addItem(f"{TYPE_ICONS.get(t.value, '')}  {t.value}", t.value)
        self.filter_type.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.filter_type)

        layout.addWidget(lbl("Statut :"))
        self.filter_statut = QComboBox()
        self.filter_statut.setFixedWidth(130)
        self.filter_statut.addItem("Tous", None)
        self.filter_statut.addItem("⏳  En attente", StatutCotisation.EN_ATTENTE.value)
        self.filter_statut.addItem("✅  Payé",        StatutCotisation.PAYE.value)
        self.filter_statut.addItem("🔴  En retard",   StatutCotisation.EN_RETARD.value)
        self.filter_statut.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.filter_statut)

        layout.addWidget(lbl("Année :"))
        self.filter_annee = QComboBox()
        self.filter_annee.setFixedWidth(90)
        self.filter_annee.addItem("Toutes", None)
        current_year = date.today().year
        for y in range(current_year, current_year - 5, -1):
            self.filter_annee.addItem(str(y), y)
        self.filter_annee.setCurrentIndex(1)
        self.filter_annee.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.filter_annee)

        layout.addStretch()
        return bar

    def _build_table(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame { border-radius: 12px; border: 1px solid #dee2e6; }")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Type", "Période", "Montant dû (DA)", "Montant payé (DA)",
            "Solde (DA)", "Statut", "Date limite", "N° Pièce", "Pièce jointe"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 130)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 110)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 105)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(7, 110)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 80)
        self.table.verticalHeader().setDefaultSectionSize(38)

        self.table.setStyleSheet(f"""
            QTableWidget {{
                gridline-color: #dee2e6;
                selection-background-color: #d5e8d4;
                selection-color: #155724;
                alternate-background-color: #f8f9fa;
                border: none;
            }}
            QHeaderView::section {{
                font-weight: 700; font-size: 11px;
                border: none; border-right: 1px solid #dee2e6;
                border-bottom: 2px solid {C_INFO};
                padding: 8px 12px;
            }}
            QTableWidget::item {{
                padding: 6px 12px; border-bottom: 1px solid #f0f0f0;
            }}
        """)

        self.table.itemSelectionChanged.connect(self._update_actions)
        self.table.doubleClicked.connect(self._edit)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)

        fl.addWidget(self.table)
        return frame

        # ── Données ───────────────────────────────────────────────────

    def load_data(self):
        try:
            q = self.session.query(Cotisation)

            t_filter = self.filter_type.currentData()
            if t_filter:
                q = q.filter(Cotisation.type_cotisation == TypeCotisation(t_filter))

            s_filter = self.filter_statut.currentData()
            if s_filter:
                q = q.filter(Cotisation.statut == StatutCotisation(s_filter))

            a_filter = self.filter_annee.currentData()
            if a_filter:
                q = q.filter(Cotisation.annee == a_filter)

            rows = q.order_by(
                Cotisation.annee.desc(),
                Cotisation.mois.desc(),
                Cotisation.type_cotisation
            ).all()

        except Exception:
            rows = []

        self._populate_table(rows)
        self._update_cards()
        self.count_lbl.setText(f"{len(rows)} cotisation{'s' if len(rows) > 1 else ''}")

        # Alerte retards
        try:
            nb_retard = self.session.query(Cotisation).filter(
                Cotisation.statut == StatutCotisation.EN_RETARD
            ).count()
            if nb_retard > 0:
                self.lbl_alerte.setText(f"⚠️  {nb_retard} cotisation{'s' if nb_retard > 1 else ''} en retard !")
            else:
                self.lbl_alerte.setText("")
        except Exception:
            pass

    def _populate_table(self, rows: list):
        self.table.setRowCount(0)
        self.table.setRowCount(len(rows))
        self._row_ids = {}

        for r, cot in enumerate(rows):
            self._row_ids[r] = cot.id
            accent = TYPE_COLORS.get(cot.type_cotisation.value, C_INFO)

            # Col 0 — Type (badge coloré)
            type_item = QTableWidgetItem(f"  {TYPE_ICONS[cot.type_cotisation.value]}  {cot.type_cotisation.value}")
            type_item.setForeground(QColor("white"))
            type_item.setBackground(QColor(accent))
            type_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(r, 0, type_item)

            # Col 1 — Période
            self.table.setItem(r, 1, QTableWidgetItem(cot.label_periode))

            # Col 2 — Montant dû
            i_du = QTableWidgetItem(f"{cot.montant_du:,.0f}")
            i_du.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            i_du.setFont(QFont("Consolas", 11))
            i_du.setForeground(QColor(accent))
            self.table.setItem(r, 2, i_du)

            # Col 3 — Montant payé
            i_paye = QTableWidgetItem(f"{cot.montant_paye:,.0f}")
            i_paye.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            i_paye.setFont(QFont("Consolas", 11))
            i_paye.setForeground(QColor(C_PAYE))
            self.table.setItem(r, 3, i_paye)

            # Col 4 — Solde
            solde = cot.solde
            i_solde = QTableWidgetItem(f"{solde:,.0f}")
            i_solde.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            i_solde.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
            i_solde.setForeground(QColor(C_RETARD if solde > 0 else C_PAYE))
            self.table.setItem(r, 4, i_solde)

            # Col 5 — Statut (badge)
            statut_map = {
                StatutCotisation.PAYE:       ("✅ Payé",       C_PAYE),
                StatutCotisation.EN_ATTENTE: ("⏳ En attente", C_ATTENTE),
                StatutCotisation.EN_RETARD:  ("🔴 En retard",  C_RETARD),
            }
            txt, col = statut_map.get(cot.statut, ("–", C_GRAY))
            i_statut = QTableWidgetItem(txt)
            i_statut.setForeground(QColor("white"))
            i_statut.setBackground(QColor(col))
            i_statut.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            i_statut.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(r, 5, i_statut)

            # Col 6 — Date limite
            dl_txt = cot.date_limite.strftime("%d/%m/%Y") if cot.date_limite else "–"
            i_dl = QTableWidgetItem(dl_txt)
            i_dl.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if cot.date_limite and date.today() > cot.date_limite and cot.statut != StatutCotisation.PAYE:
                i_dl.setForeground(QColor(C_RETARD))
                i_dl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            else:
                i_dl.setForeground(QColor(C_GRAY))
            self.table.setItem(r, 6, i_dl)

            # Col 7 — N° Pièce
            i_piece = QTableWidgetItem(cot.numero_piece or "–")
            i_piece.setForeground(QColor(C_GRAY))
            i_piece.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 7, i_piece)

            # Col 8 — Pièce jointe
            has_pj = bool(cot.chemin_piece and os.path.exists(cot.chemin_piece))
            i_pj = QTableWidgetItem("📎" if has_pj else "–")
            i_pj.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            i_pj.setForeground(QColor(C_INFO if has_pj else C_GRAY))
            self.table.setItem(r, 8, i_pj)

    def _update_cards(self):
        """Met à jour les 4 cartes avec les données de l'année filtrée."""
        try:
            a_filter = self.filter_annee.currentData()
            q = self.session.query(Cotisation)
            if a_filter:
                q = q.filter(Cotisation.annee == a_filter)
            all_rows = q.all()

            for type_str, card in self.cards.items():
                type_rows = [r for r in all_rows if r.type_cotisation.value == type_str]
                card.update_data(type_rows)
        except Exception:
            pass

    def _update_actions(self):
        sel = len(self.table.selectedItems()) > 0
        self.btn_edit.setEnabled(sel)
        self.btn_delete.setEnabled(sel)
        self.btn_payer.setEnabled(sel)

    def _selected_id(self):
        rows = self.table.selectedItems()
        if not rows:
            return None
        return self._row_ids.get(self.table.currentRow())

    def _get_cotisation(self, cid):
        return self.session.query(Cotisation).filter(Cotisation.id == cid).first()

        # ── Actions ───────────────────────────────────────────────────

    def _add(self):
        dlg = CotisationDialog(self.session, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def _edit(self):
        cid = self._selected_id()
        if not cid:
            return
        cot = self._get_cotisation(cid)
        if not cot:
            return
        dlg = CotisationDialog(self.session, cotisation=cot, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def _delete(self):
        cid = self._selected_id()
        if not cid:
            return
        cot = self._get_cotisation(cid)
        if not cot:
            return
        rep = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer la cotisation {cot.type_cotisation.value} — {cot.label_periode} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if rep == QMessageBox.StandardButton.Yes:
            try:
                self.session.delete(cot)
                self.session.commit()
                self.load_data()
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Erreur", str(e))

    def _marquer_paye(self):
        cid = self._selected_id()
        if not cid:
            return
        cot = self._get_cotisation(cid)
        if not cot:
            return
        cot.statut       = StatutCotisation.PAYE
        cot.montant_paye = cot.montant_du
        cot.date_paiement = date.today()
        try:
            self.session.commit()
            self.load_data()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erreur", str(e))

    def _context_menu(self, pos):
        cid = self._selected_id()
        if not cid:
            return
        cot = self._get_cotisation(cid)
        if not cot:
            return

        menu = QMenu(self)

        act_edit   = QAction("✏️  Modifier",       self)
        act_payer  = QAction("✅  Marquer payé",    self)
        act_pj     = QAction("📎  Ouvrir le fichier", self)
        act_delete = QAction("🗑️  Supprimer",       self)

        act_payer.setEnabled(cot.statut != StatutCotisation.PAYE)
        act_pj.setEnabled(bool(cot.chemin_piece and os.path.exists(cot.chemin_piece)))

        act_edit.triggered.connect(self._edit)
        act_payer.triggered.connect(self._marquer_paye)
        act_pj.triggered.connect(lambda: os.startfile(cot.chemin_piece) if cot.chemin_piece else None)
        act_delete.triggered.connect(self._delete)

        menu.addAction(act_edit)
        menu.addAction(act_payer)
        menu.addSeparator()
        menu.addAction(act_pj)
        menu.addSeparator()
        menu.addAction(act_delete)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def closeEvent(self, event):
        self.session.close()
        super().closeEvent(event)