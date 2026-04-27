# views/rapport_dialog.py
"""
Dialogue de génération de rapport complet ENTS NET
Sections : Employés, Clients, Salaires/Paie, Banque, Dépenses, Factures
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QDateEdit, QFileDialog, QMessageBox,
    QProgressBar, QFrame, QComboBox, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime
import os


# ─────────────────────────────────────────────────────────────────────────────
#  Carte section
# ─────────────────────────────────────────────────────────────────────────────

class SectionCard(QFrame):
    def __init__(self, icon, title, subtitle, color, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedHeight(62)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(f"""
            QFrame {{ background:white; border:1.5px solid #e8ecef; border-radius:10px; }}
            QFrame:hover {{ border-color:{color}; }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(10)

        ico = QLabel(icon)
        ico.setFixedSize(38, 38)
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet(f"background:{color}22;border-radius:8px;font-size:18px;")
        lay.addWidget(ico)

        col = QVBoxLayout()
        col.setSpacing(1)
        t = QLabel(title)
        t.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        t.setStyleSheet("color:#2c3e50;")
        s = QLabel(subtitle)
        s.setFont(QFont("Arial", 7))
        s.setStyleSheet("color:#95a5a6;")
        col.addWidget(t)
        col.addWidget(s)
        lay.addLayout(col)
        lay.addStretch()

        self.cb = QCheckBox()
        self.cb.setChecked(True)
        self.cb.setStyleSheet(f"""
            QCheckBox::indicator {{
                width:20px; height:20px; border-radius:4px; border:2px solid #bdc3c7;
            }}
            QCheckBox::indicator:checked {{
                background:{color}; border-color:{color};
            }}
        """)
        lay.addWidget(self.cb)

    @property
    def checked(self): 
        return self.cb.isChecked()


# ─────────────────────────────────────────────────────────────────────────────
#  Thread de génération (non-bloquant)
# ─────────────────────────────────────────────────────────────────────────────

class RapportThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            from services.rapport_pdf_service import RapportPDFService
            svc  = RapportPDFService(progress_callback=self.progress.emit)
            path = svc.generate(self.config)
            self.finished.emit(path)
        except Exception as e:
            import traceback
            self.error.emit(f"{e}\n\n{traceback.format_exc()}")


# ─────────────────────────────────────────────────────────────────────────────
#  Dialogue principal
# ─────────────────────────────────────────────────────────────────────────────

class RapportDialog(QDialog):
    
    SECTIONS = [
        ("employes", "👥", "Employés",        "Effectifs, statuts, salaires, contrats",  "#2980B9"),
        ("clients",  "🏥", "Clients",          "CHU Beni Messous, CHU Douera",            "#8E44AD"),
        ("salaires", "💰", "Salaires & Paie",  "Fiches de paie, cotisations CNAS",        "#27AE60"),
        ("banque",   "🏦", "Banque",            "Soldes, mouvements, virements",           "#E67E22"),
        ("depenses", "📊", "Dépenses",         "Charges, fournisseurs, catégories",       "#E74C3C"),
        ("factures", "🧾", "Factures",         "Payées / impayées, montants en attente",  "#1ABC9C"),
        ("cotisations", "🏛️", "Cotisations",    "CNAS, CASNOS, CACOBATPH, G50",            "#F39C12"),  
        ("paie_globale", "📈", "Paie Globale",  "Paie mensuelle par site",                  "#7F8C8D"),  
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 Générer un rapport")
        self.setModal(True)
        self.setMinimumWidth(520)
        self._thread = None
        self._cards  = {}
        self._build_ui()

    # ── Construction UI ───────────────────────────────────────────────────

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog { background:#f4f7fa; font-family:Arial; }
            QGroupBox {
                background:white; border:1px solid #e3e8ee; border-radius:10px;
                margin-top:12px; padding:12px; font-size:10px;
                font-weight:bold; color:#2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin:margin; left:14px; padding:0 6px; background:#f4f7fa;
            }
            QDateEdit, QComboBox {
                border:1px solid #dde3ea; border-radius:7px;
                padding:5px 10px; min-height:28px; font-size:11px; background:white;
            }
            QDateEdit:focus, QComboBox:focus { border-color:#2980B9; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        # Titre
        hdr = QLabel("📋  Rapport de Gestion — ENTS NET")
        hdr.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        hdr.setStyleSheet("""
            color:white;
            background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #1F3864,stop:1 #2980B9);
            padding:12px 16px; border-radius:10px;
        """)
        root.addWidget(hdr)

        # Période
        grp_p = QGroupBox("📅  Période")
        gl = QGridLayout(grp_p)
        gl.setSpacing(8)

        gl.addWidget(QLabel("Raccourci :"), 0, 0)
        self.cmb = QComboBox()
        self.cmb.addItems([
            "Choisir librement", "Mois en cours", "Mois précédent",
            "Trimestre en cours", "Trimestre précédent",
            "Année en cours", "Année précédente",
        ])
        self.cmb.currentIndexChanged.connect(self._set_period)
        gl.addWidget(self.cmb, 0, 1, 1, 3)

        gl.addWidget(QLabel("Du :"), 1, 0)
        self.d_deb = QDateEdit(calendarPopup=True)
        self.d_deb.setDisplayFormat("dd/MM/yyyy")
        today = QDate.currentDate()
        self.d_deb.setDate(QDate(today.year(), today.month(), 1))
        gl.addWidget(self.d_deb, 1, 1)

        gl.addWidget(QLabel("Au :"), 1, 2)
        self.d_fin = QDateEdit(calendarPopup=True)
        self.d_fin.setDisplayFormat("dd/MM/yyyy")
        self.d_fin.setDate(today)
        gl.addWidget(self.d_fin, 1, 3)
        root.addWidget(grp_p)

        # Sections
        grp_s = QGroupBox("📑  Sections à inclure")
        sl = QVBoxLayout(grp_s)
        sl.setSpacing(6)

        brow = QHBoxLayout()
        for txt, state in [("✅ Tout sélectionner", True), ("☐ Tout décocher", False)]:
            btn = QPushButton(txt)
            btn.setFixedHeight(26)
            btn.setStyleSheet("""
                QPushButton { background:#ecf0f1; color:#2c3e50; border:1px solid #bdc3c7;
                    border-radius:5px; font-size:10px; padding:0 10px; }
                QPushButton:hover { background:#d5dbdb; }
            """)
            btn.clicked.connect(lambda checked, s=state: self._toggle(s))
            brow.addWidget(btn)
        brow.addStretch()
        sl.addLayout(brow)

        for key, icon, title, sub, color in self.SECTIONS:
            card = SectionCard(icon, title, sub, color)
            self._cards[key] = card
            sl.addWidget(card)
        root.addWidget(grp_s)

        # Options
        grp_o = QGroupBox("⚙️  Options")
        ol = QHBoxLayout(grp_o)
        self.cb_cover = QCheckBox("Page de couverture")
        self.cb_toc   = QCheckBox("Sommaire")
        self.cb_graph = QCheckBox("Graphiques")
        for cb in (self.cb_cover, self.cb_toc, self.cb_graph):
            cb.setChecked(True)
            cb.setFont(QFont("Arial", 9))
            ol.addWidget(cb)
        ol.addStretch()
        root.addWidget(grp_o)

        # Barre de progression
        self.pbar  = QProgressBar()
        self.lbl_p = QLabel("")
        self.pbar.setVisible(False)
        self.lbl_p.setVisible(False)
        self.pbar.setStyleSheet("""
            QProgressBar { border:1px solid #dde3ea; border-radius:6px;
                background:#f0f4f8; height:16px; text-align:center; font-size:9px; }
            QProgressBar::chunk { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #2980B9, stop:1 #27AE60); border-radius:5px; }
        """)
        self.lbl_p.setFont(QFont("Arial", 8))
        self.lbl_p.setStyleSheet("color:#7f8c8d;")
        root.addWidget(self.pbar)
        root.addWidget(self.lbl_p)

        # Boutons
        br = QHBoxLayout()
        br.setSpacing(8)

        self.btn = QPushButton("🚀  Générer le rapport PDF")
        self.btn.setFixedHeight(42)
        self.btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.btn.setStyleSheet("""
            QPushButton { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #1F3864, stop:1 #2980B9); color:white; border:none;
                border-radius:8px; padding:0 20px; }
            QPushButton:hover { background:#2471a3; }
            QPushButton:disabled { background:#bdc3c7; }
        """)
        self.btn.clicked.connect(self._generate)

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setFixedHeight(42)
        btn_cancel.setStyleSheet("""
            QPushButton { background:#ecf0f1; color:#2c3e50; border:1px solid #bdc3c7;
                border-radius:8px; font-size:10px; padding:0 18px; }
            QPushButton:hover { background:#d5dbdb; }
        """)
        btn_cancel.clicked.connect(self.reject)

        br.addStretch()
        br.addWidget(btn_cancel)
        br.addWidget(self.btn)
        root.addLayout(br)

    # ── Slots ─────────────────────────────────────────────────────────────

    def _toggle(self, state):
        for card in self._cards.values():
            card.cb.setChecked(state)

    def _set_period(self, idx):
        t = QDate.currentDate()
        y, m = t.year(), t.month()
        if   idx == 0: return
        elif idx == 1:
            self.d_deb.setDate(QDate(y, m, 1))
            self.d_fin.setDate(t)
        elif idx == 2:
            pm, py = (m - 1, y) if m > 1 else (12, y - 1)
            self.d_deb.setDate(QDate(py, pm, 1))
            self.d_fin.setDate(QDate(py, pm, QDate(py, pm, 1).daysInMonth()))
        elif idx == 3:
            qs = ((m - 1) // 3) * 3 + 1
            self.d_deb.setDate(QDate(y, qs, 1))
            self.d_fin.setDate(t)
        elif idx == 4:
            q = (m - 1) // 3
            qs, qy = ((q - 1) * 3 + 1, y) if q > 0 else (10, y - 1)
            qe = qs + 2
            self.d_deb.setDate(QDate(qy, qs, 1))
            self.d_fin.setDate(QDate(qy, qe, QDate(qy, qe, 1).daysInMonth()))
        elif idx == 5:
            self.d_deb.setDate(QDate(y, 1, 1))
            self.d_fin.setDate(t)
        elif idx == 6:
            self.d_deb.setDate(QDate(y - 1, 1, 1))
            self.d_fin.setDate(QDate(y - 1, 12, 31))

    def _generate(self):
        secs = [k for k, c in self._cards.items() if c.checked]
        if not secs:
            QMessageBox.warning(self, "Attention", "Sélectionnez au moins une section.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le rapport",
            f"Rapport_ENTS_NET_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            "PDF (*.pdf)"
        )
        if not path:
            return

        config = {
            "sections":    secs,
            "date_debut":  self.d_deb.date().toPyDate(),
            "date_fin":    self.d_fin.date().toPyDate(),
            "couverture":  self.cb_cover.isChecked(),
            "sommaire":    self.cb_toc.isChecked(),
            "graphiques":  self.cb_graph.isChecked(),
            "output_path": path,
        }

        self.btn.setEnabled(False)
        self.pbar.setVisible(True)
        self.pbar.setValue(0)
        self.lbl_p.setVisible(True)

        self._thread = RapportThread(config)
        self._thread.progress.connect(lambda p, m: (self.pbar.setValue(p), self.lbl_p.setText(m)))
        self._thread.finished.connect(self._done)
        self._thread.error.connect(self._err)
        self._thread.start()

    def _done(self, path):
        self.btn.setEnabled(True)
        self.pbar.setValue(100)
        self.lbl_p.setText("✅ Rapport généré avec succès !")
        reply = QMessageBox.information(
            self, "Succès",
            f"Rapport PDF créé :\n{path}\n\nOuvrir le fichier ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            import subprocess, sys
            if os.name == 'nt':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', path])
            else:
                subprocess.call(['xdg-open', path])
        self.accept()

    def _err(self, msg):
        self.btn.setEnabled(True)
        self.pbar.setVisible(False)
        self.lbl_p.setVisible(False)
        QMessageBox.critical(self, "Erreur de génération", msg)