# views/paye_globale_view.py
"""
Vue principale pour la gestion de la paie globale — version améliorée
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QAbstractItemView, QMenu, QLabel,
    QComboBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QCursor

from database.db import SessionLocal, get_session
from models.paye_globale import PayeGlobale
from views.payroll.paye_globale_dialog import PayeGlobaleDialog


# ─── Palette centralisée ────────────────────────────────────────────────────
CLR_BG         = "#F0F4F8"
CLR_SURFACE    = "#FFFFFF"
CLR_PRIMARY    = "#1A6B4A"   # vert foncé
CLR_PRIMARY_LT = "#27AE60"
CLR_ACCENT     = "#F39C12"   # orange totaux
CLR_DANGER     = "#E74C3C"
CLR_INFO       = "#2980B9"
CLR_TEXT       = "#1C2B36"
CLR_TEXT_SUB   = "#6B7C8D"
CLR_BORDER     = "#D8E3EC"
CLR_ROW_ALT    = "#F7FAFB"
CLR_SEL_BG     = "#D4EDDA"
CLR_SEL_FG     = "#155724"


def _btn(label: str, color: str, hover: str) -> QPushButton:
    b = QPushButton(label)
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    b.setFixedHeight(36)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {color};
            color: white;
            border: none;
            padding: 0 18px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
        }}
        QPushButton:hover  {{ background: {hover}; }}
        QPushButton:pressed {{ opacity: 0.85; }}
    """)
    return b


class StatCard(QFrame):
    """Mini carte de statistique affichée en haut de la vue."""

    def __init__(self, title: str, value: str = "–", color: str = CLR_PRIMARY, icon: str = ""):
        super().__init__()
        self.setFixedHeight(90)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(f"""
            QFrame {{
                background: {CLR_SURFACE};
                border-radius: 12px;
                border-left: 5px solid {color};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 28px; color: {color};")
        layout.addWidget(icon_lbl)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {color};
            font-family: 'Segoe UI', sans-serif;
        """)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 11px; color: {CLR_TEXT_SUB}; font-weight: 500;")

        text_box.addWidget(self.value_lbl)
        text_box.addWidget(title_lbl)
        layout.addLayout(text_box)
        layout.addStretch()

    def set_value(self, v: str):
        self.value_lbl.setText(v)


class PayeGlobaleView(QWidget):
    """Vue améliorée pour la gestion de la paie globale."""

    STATUT_MAP = {0: ("BROUILLON", "#F39C12"), 1: ("VALIDÉ", "#2980B9"), 2: ("PAYÉ", "#27AE60")}

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background: {CLR_BG};")
        self._sort_col = -1
        self._sort_asc = True
        self._init_ui()
        self.load_data()

        # ── Construction UI ───────────────────────────────────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        root.addLayout(self._build_header())
        root.addLayout(self._build_stat_cards())
        root.addLayout(self._build_toolbar())
        root.addWidget(self._build_filter_bar())
        root.addWidget(self._build_table())

    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()

        icon = QLabel("💰")
        icon.setStyleSheet("font-size: 32px;")

        titles = QVBoxLayout()
        titles.setSpacing(0)

        h1 = QLabel("Paie Globale")
        h1.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 700;
            color: {CLR_TEXT};
            font-family: 'Segoe UI', sans-serif;
        """)

        h2 = QLabel("Gestion mensuelle des salaires par site / client")
        h2.setStyleSheet(f"font-size: 12px; color: {CLR_TEXT_SUB};")

        titles.addWidget(h1)
        titles.addWidget(h2)

        row.addWidget(icon)
        row.addLayout(titles)
        row.addStretch()
        return row

    def _build_stat_cards(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)

        self.card_total   = StatCard("Paies ce mois",   "–",  CLR_PRIMARY,  "📋")
        self.card_brut    = StatCard("Total Brut",       "–",  CLR_INFO,     "📊")
        self.card_cnss    = StatCard("Total CNSS",       "–",  CLR_ACCENT,   "🏦")
        self.card_net     = StatCard("Total Net",        "–",  CLR_PRIMARY_LT, "✅")

        for c in (self.card_total, self.card_brut, self.card_cnss, self.card_net):
            row.addWidget(c)
        return row

    def _build_toolbar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        self.btn_add    = _btn("➕  Nouvelle paie",  CLR_PRIMARY_LT, CLR_PRIMARY)
        self.btn_edit   = _btn("✏️  Modifier",        CLR_INFO,       "#2471A3")
        self.btn_delete = _btn("🗑️  Supprimer",       CLR_DANGER,     "#C0392B")
        self.btn_refresh= _btn("🔄  Actualiser",      "#7F8C8D",      "#626567")

        self.btn_add.clicked.connect(self.add_paye)
        self.btn_edit.clicked.connect(self.edit_paye)
        self.btn_delete.clicked.connect(self.delete_paye)
        self.btn_refresh.clicked.connect(self.load_data)

        row.addWidget(self.btn_add)
        row.addWidget(self.btn_edit)
        row.addWidget(self.btn_delete)
        row.addStretch()
        row.addWidget(self.btn_refresh)
        return row

    def _build_filter_bar(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(48)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {CLR_SURFACE};
                border-radius: 10px;
                border: 1px solid {CLR_BORDER};
            }}
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        lbl = QLabel("Année :")
        lbl.setStyleSheet(f"color: {CLR_TEXT_SUB}; font-size: 13px;")
        layout.addWidget(lbl)

        self.annee_filter = QComboBox()
        self.annee_filter.addItems(["Toutes", "2024", "2025", "2026"])
        self.annee_filter.setFixedWidth(110)
        self.annee_filter.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {CLR_BORDER};
                border-radius: 6px;
                padding: 4px 10px;
                background: {CLR_BG};
                color: {CLR_TEXT};
                font-size: 13px;
            }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.annee_filter.currentTextChanged.connect(self.load_data)
        layout.addWidget(self.annee_filter)

        layout.addStretch()

        self.count_lbl = QLabel("0 enregistrement(s)")
        self.count_lbl.setStyleSheet(f"color: {CLR_TEXT_SUB}; font-size: 12px;")
        layout.addWidget(self.count_lbl)
        return bar

    def _build_table(self) -> QTableWidget:
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Période ↕", "Date paiement ↕", "Total Brut ↕", "Total CNSS ↕", "Total Net ↕", "Statut"
        ])
        self.table.setColumnHidden(0, True)

        # Style général
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {CLR_BORDER};
                border-radius: 12px;
                background: {CLR_SURFACE};
                gridline-color: {CLR_BORDER};
                selection-background-color: {CLR_SEL_BG};
                selection-color: {CLR_SEL_FG};
                font-size: 13px;
                outline: none;
            }}
            QHeaderView::section {{
                background: {CLR_PRIMARY};
                color: white;
                padding: 10px 12px;
                font-weight: 700;
                font-size: 12px;
                border: none;
                border-right: 1px solid rgba(255,255,255,0.15);
            }}
            QHeaderView::section:hover {{
                background: {CLR_PRIMARY_LT};
                cursor: pointer;
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {CLR_BORDER};
            }}
            QTableWidget::item:selected {{
                background: {CLR_SEL_BG};
                color: {CLR_SEL_FG};
            }}
            QScrollBar:vertical {{
                background: {CLR_BG};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {CLR_BORDER};
                border-radius: 4px;
            }}
        """)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        hdr.sectionClicked.connect(self._on_header_click)

        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(self.table.styleSheet() + f"""
            QTableWidget {{ alternate-background-color: {CLR_ROW_ALT}; }}
        """)
        self.table.doubleClicked.connect(self.edit_paye)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        return self.table

        # ── Données ───────────────────────────────────────────────────────────────

    def load_data(self):
        """Load paye data with year filtering"""
        try:
            # Optional: Show loading indicator
            self.setCursor(Qt.CursorShape.WaitCursor)
            
            with get_session() as session:
                query = session.query(PayeGlobale)
                annee_txt = self.annee_filter.currentText()
                
                # Apply year filter if not "Toutes"
                if annee_txt and annee_txt != "Toutes":
                    try:
                        annee = int(annee_txt)
                        query = query.filter(PayeGlobale.annee == annee)
                    except ValueError:
                        # Log invalid year format
                        print(f"Invalid year format: {annee_txt}")
                
                # Execute query with ordering
                paies = query.order_by(
                    PayeGlobale.annee.desc(), 
                    PayeGlobale.mois.desc()
                ).all()
                
                # Update UI
                self._populate_table(paies)
                self._update_stat_cards(paies)
                self.count_lbl.setText(f"{len(paies)} enregistrement(s)")
                
        except Exception as e:
            # Log the error for debugging
            import traceback
            traceback.print_exc()
            
            # Show user-friendly error message
            QMessageBox.critical(
                self, 
                "Erreur", 
                f"Erreur lors du chargement des données:\n{str(e)}"
            )
        finally:
            # Restore cursor
            self.setCursor(Qt.CursorShape.ArrowCursor)


    def _populate_table(self, paies):
        self.table.setRowCount(len(paies))
        self.table.setRowCount(0)           # reset propre

        for paye in paies:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 44)

            # ID (caché)
            self.table.setItem(row, 0, QTableWidgetItem(str(paye.id)))

            # Période
            periode_item = QTableWidgetItem(paye.periode)
            periode_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            periode_item.setForeground(QColor(CLR_TEXT))
            self.table.setItem(row, 1, periode_item)

            # Date paiement
            date_item = QTableWidgetItem(paye.date_paiement.strftime("%d/%m/%Y"))
            date_item.setForeground(QColor(CLR_TEXT_SUB))
            self.table.setItem(row, 2, date_item)

            # Brut
            brut_item = QTableWidgetItem(f"{paye.total_brut:,.0f} DA".replace(",", " "))
            brut_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            brut_item.setForeground(QColor(CLR_INFO))
            self.table.setItem(row, 3, brut_item)

            # CNSS
            cnss_item = QTableWidgetItem(f"{paye.total_cnss:,.0f} DA".replace(",", " "))
            cnss_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            cnss_item.setForeground(QColor(CLR_ACCENT))
            self.table.setItem(row, 4, cnss_item)

            # Net
            net_item = QTableWidgetItem(f"{paye.total_net:,.0f} DA".replace(",", " "))
            net_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            f = QFont("Segoe UI", 12, QFont.Weight.Bold)
            net_item.setFont(f)
            net_item.setForeground(QColor(CLR_PRIMARY_LT))
            self.table.setItem(row, 5, net_item)

            # Statut badge (texte simulé)
            statut_val = paye.est_valide or 0
            label, color = self.STATUT_MAP.get(statut_val, ("INCONNU", "#95A5A6"))
            badge = QTableWidgetItem(f"  {label}  ")
            badge.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setForeground(QColor("white"))
            badge.setBackground(QColor(color))
            badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row, 6, badge)

    def _update_stat_cards(self, paies):
        total_brut = sum(p.total_brut or 0 for p in paies)
        total_cnss = sum(p.total_cnss or 0 for p in paies)
        total_net  = sum(p.total_net  or 0 for p in paies)

        self.card_total.set_value(str(len(paies)))
        self.card_brut.set_value(f"{total_brut:,.0f} DA".replace(",", " "))
        self.card_cnss.set_value(f"{total_cnss:,.0f} DA".replace(",", " "))
        self.card_net.set_value(f"{total_net:,.0f} DA".replace(",", " "))

        # ── Tri par colonne ───────────────────────────────────────────────────────

    def _on_header_click(self, col: int):
        if col == 0 or col == 6:
            return
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        order = Qt.SortOrder.AscendingOrder if self._sort_asc else Qt.SortOrder.DescendingOrder
        self.table.sortItems(col, order)

        # ── Actions CRUD ──────────────────────────────────────────────────────────

    def _get_selected_id(self):
        sel = self.table.selectedItems()
        if not sel:
            return None
        return int(self.table.item(sel[0].row(), 0).text())

    def add_paye(self):
        dlg = PayeGlobaleDialog(parent=self)
        dlg.paye_saved.connect(self.load_data)
        dlg.exec()

    def edit_paye(self):
        pid = self._get_selected_id()
        if not pid:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une paie")
            return
        dlg = PayeGlobaleDialog(paye_id=pid, parent=self)
        dlg.paye_saved.connect(self.load_data)
        dlg.exec()

    def delete_paye(self):
        """Delete the selected paye record"""
        pid = self._get_selected_id()
        if not pid:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une paie")
            return
        
        # Confirm deletion with user
        reply = QMessageBox.question(
            self, 
            "Confirmation",
            "Supprimer cette paie ?\nToutes les répartitions associées seront supprimées.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Default to No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            with get_session() as session:
                paye = session.query(PayeGlobale).filter(PayeGlobale.id == pid).first()
                if paye:
                    # Store info for success message
                    paye_info = f"{self._get_month_name(paye.mois)} {paye.annee}"
                    session.delete(paye)
                    session.commit()
                    
                    # Reload data
                    self.load_data()
                    
                    # Show success message
                    QMessageBox.information(
                        self,
                        "Succès",
                        f"Paie '{paye_info}' supprimée avec succès!"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Non trouvé",
                        "La paie sélectionnée n'existe plus."
                    )
                    self.load_data()  # Reload to refresh the view
                    
        except Exception as e:
            # Log the error for debugging
            import traceback
            traceback.print_exc()
            
            # Show user-friendly error message
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de la suppression:\n{str(e)}"
            )


    def _show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {CLR_SURFACE};
                border: 1px solid {CLR_BORDER};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 13px;
                color: {CLR_TEXT};
            }}
            QMenu::item:selected {{ background: {CLR_SEL_BG}; color: {CLR_SEL_FG}; }}
        """)

        menu.addAction("➕  Nouvelle paie",  self.add_paye)
        idx = self.table.indexAt(pos)
        if idx.isValid():
            self.table.selectRow(idx.row())
            menu.addSeparator()
            menu.addAction("✏️  Modifier",   self.edit_paye)
            menu.addAction("🗑️  Supprimer",  self.delete_paye)

        menu.exec(self.table.viewport().mapToGlobal(pos))
