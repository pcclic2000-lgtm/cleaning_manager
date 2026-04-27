# views/service_fait_dialog.py
"""
Dialogue de génération des Attestations de Service Fait
- CHU BENI MESSOUS (une attestation par service)
- CHU DOUERA (tableau récapitulatif avec nombre d'agents)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QWidget, QFileDialog, QMessageBox, QGroupBox,
    QScrollArea, QFrame, QCheckBox, QHeaderView, QDateEdit,
    QLineEdit, QAbstractItemView
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
import os
import logging
from datetime import date
import calendar

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Chargement des infos entreprise depuis la base de données
# ─────────────────────────────────────────────────────────────────────────────

def load_company_info():
    """Charge les informations de l'entreprise depuis la base de données."""
    try:
        from database.db import get_session
        from models.company import CompanyInfo
        with get_session() as session:
            company = session.query(CompanyInfo).first()
            if company:
                return {
                    "name":       company.nom or "ENTS NET",
                    "address":    company.adresse or "",
                    "ville":      company.ville or "",
                    "tel":        company.telephone or "",
                    "email":      company.email or "",
                    "nif":        company.nif or "",
                    "nis":        company.nis or "",
                    "rc":         company.rc or "",
                    "ai":         company.art or "",
                    "logo_path":  company.logo_path if company.logo_path and os.path.exists(company.logo_path) else None,
                    "rib":        company.rib or "",
                    "banque":     company.banque or "",
                    "compte_ccp": getattr(company, "compte_ccp", "") or "",
                }
    except Exception as e:
        logger.error("Erreur chargement info entreprise: %s", e)

    # Valeurs par défaut si la base n'est pas disponible
    return {
        "name":       "ENTS NET",
        "address":    "22 Lotissement Deux Piliers Bouzareah Alger",
        "ville":      "",
        "tel":        "0552 88 30 50 / 0777 98 90 58",
        "email":      "entsnet7@gmail.com",
        "nif":        "000816098084472",
        "nis":        "000816110197348",
        "rc":         "16/00 0980844B08",
        "ai":         "16119147105",
        "logo_path":  None,
        "rib":        "",
        "banque":     "",
        "compte_ccp": "",
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Données métier
# ─────────────────────────────────────────────────────────────────────────────

# Conservé pour compatibilité ; sera remplacé dynamiquement à l'exécution
COMPANY_INFO = load_company_info()

BENI_MESSOUS_SERVICES = [
    "service pneumo-phtisiologie A",
    "service Pneumo-Allergo",
    "Oncologie + Clinique beau Fraisier",
    "service d'urgences médicales",
    "service cardiologie",
    "service EFR",
]

DOUERA_SERVICES = [
    ("SERVICE MATERNITE",            10),
    ("SERVICE MAXILO-FACIALE",        1),
    ("SERVICE CCI",                   6),
    ("SERVICE RADIOLOGIE",            2),
    ("SERVICE PREVENTION",            1),
    ("SERVICE RHUMATOLOGIE",          5),
    ("SERVICE REEDUCATION FONCTIONNEL", 2),
    ("SERVICE CHIRURGIE GENERALE",    2),
    ("SERVICE MEDECINE INTERNE",      2),
    ("REANIMATION MEDICALE",          1),
    ("SERVICE ORTHOPEDIE A",          6),
    ("SERVICE ORTHOPEDIE B",          6),
    ("SERVICE MEDECINE LEGALE",       1),
    ("SERVICE NEO-NAT",               4),
    ("ADMINISTRATION",                2),
    ("SERVICE PHARMACIE",             1),
    ("SERVICE PEDIATRIE",             4),
    ("CTS",                           1),
    ("NETTOYAGE GENERALE (POLYVALENT)", 7),
    ("U.M.C",                         4),
    ("STERILISATION",                 1),
    ("CUISINE",                       2),
    ("NEUROLOGIE",                    1),
    ("AMBULANT",                      1),
]

MOIS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]


# ─────────────────────────────────────────────────────────────────────────────
#  Génération PDF — CHU BENI MESSOUS
# ─────────────────────────────────────────────────────────────────────────────

def _draw_invoice_style_header(c, W, H, company):
    """
    Dessine un en-tête identique à celui des factures (invoice_dialog.py).
    Logo à gauche, infos entreprise à droite, ligne de séparation en bas.
    Retourne la coordonnée Y du bas de l'en-tête.
    """
    from reportlab.lib.units import cm
    from reportlab.lib import colors

    MARGIN = 1.8 * cm
    logo_w, logo_h = 2.5 * cm, 1.5 * cm
    top_y = H - MARGIN

    # ── Logo ──────────────────────────────────────────────────────────────────
    logo_path = company.get("logo_path") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets", "logos", "logo.jpg"
    )
    if logo_path and os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, MARGIN, top_y - logo_h,
                        width=logo_w, height=logo_h,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            pass

    # ── Lignes d'informations (style compact, fontSize 8) ─────────────────────
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor('#4a5568'))

    info_lines = [
        "Entreprise de nettoyage – travaux & services",
        f"Adresse : {company.get('address', '')}",
        f"Phone : {company.get('tel', '')}",
        f"N.R.C {company.get('rc', '')}   N°article : {company.get('ai', '')}",
        f"N.I.F {company.get('nif', '')}   N.I.S {company.get('nis', '')}",
        f"E-mail : {company.get('email', '')}",
    ]

    # Infos bancaires
    parts = []
    if company.get("compte_ccp"):
        parts.append(f"CCP {company['compte_ccp']}")
    if company.get("banque"):
        parts.append(f"Compte Banque {company['banque']}")
    if company.get("rib"):
        parts.append(f"RIB {company['rib']}")
    if parts:
        info_lines.append(" | ".join(parts))

    line_h = 0.38 * cm
    text_x = MARGIN
    text_y = top_y - logo_h - 0.5 * cm

    for line in info_lines:
        if line.strip():
            text_y -= line_h
            c.drawString(text_x, text_y, line)

    # ── Ligne de séparation ───────────────────────────────────────────────────
    sep_y = text_y - 0.2 * cm
    c.setStrokeColor(colors.HexColor('#bdc3c7'))
    c.setLineWidth(0.8)
    c.line(MARGIN, sep_y, W - MARGIN, sep_y)

    return sep_y  # coordonnée Y du bas de l'en-tête


def generate_beni_messous_pdf(services_selected, date_debut, date_fin, output_path):
    """
    Génère un PDF multi-pages pour CHU BENI MESSOUS.
    Une page par service sélectionné.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors

    company = load_company_info()
    c = canvas.Canvas(output_path, pagesize=A4)
    W, H = A4

    def draw_page(service_name):
        # ── En-tête style facture ─────────────────────────────────────────────
        header_bottom_y = _draw_invoice_style_header(c, W, H, company)

        # Décalage de sécurité après l'en-tête
        content_y = header_bottom_y - 0.4 * cm

        MARGIN = 1.8 * cm

        # ── Titre ─────────────────────────────────────────────────────────────
        c.setFillColor(colors.HexColor('#2c3e50'))
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(W / 2, content_y - 0.6 * cm, "ATTESTATION DE SERVICE FAIT")

        # ── Destinataire ──────────────────────────────────────────────────────
        y = content_y - 1.6 * cm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN, y, f"DESTINATAIRE : CHU BENI MESSOUS ({service_name})")

        y -= 0.7 * cm
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN, y, "À l'aimable attention de Mr le Responsable")

        y -= 0.8 * cm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN, y, "Objet : Service Fait")

        # ── Corps ─────────────────────────────────────────────────────────────
        y -= 1.0 * cm
        c.setFillColor(colors.HexColor('#2c3e50'))
        c.setFont("Helvetica", 10)
        company_name = company.get("name", "ENTS NET")
        body_lines = [
            f"Nous soussigné SARL {company_name}, Entreprise de nettoyage – Travaux et Services, certifions que",
            f"le service de nettoyage et entretien de {service_name} du CHU BENI MESSOUS",
            f"a été effectué pendant la période du {date_debut} au {date_fin}.",
        ]
        for line in body_lines:
            c.drawString(MARGIN, y, line)
            y -= 0.6 * cm

        y -= 0.4 * cm
        c.drawString(
            MARGIN, y,
            "Tout en vous remerciant pour votre précieuse coopération, nous vous prions de bien vouloir"
        )
        y -= 0.6 * cm
        c.drawString(
            MARGIN, y,
            "agréer, cher Monsieur, l'expression de nos salutations les plus respectueuses."
        )

        # ── Remarque ──────────────────────────────────────────────────────────
        y -= 1.5 * cm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN, y, "REMARQUE : Le Responsable")

        c.setFont("Helvetica", 10)
        for _ in range(5):
            y -= 0.7 * cm
            c.drawString(MARGIN, y, "." * 110)

        # ── Signatures ────────────────────────────────────────────────────────
        y -= 1.8 * cm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN, y, "Le Responsable")
        c.drawString(W - 6 * cm, y, "Le Directeur")

        y -= 0.6 * cm
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN, y, "__________________")
        c.drawString(W - 6 * cm, y, "__________________")

        y -= 0.6 * cm
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN, y, service_name)
        c.drawString(W - 6 * cm, y, f"SARL {company_name}")

    for service in services_selected:
        draw_page(service)
        c.showPage()

    c.save()


# ─────────────────────────────────────────────────────────────────────────────
#  Génération PDF — CHU DOUERA
# ─────────────────────────────────────────────────────────────────────────────

def generate_douera_pdf(month_name, year, services_data, output_path):
    """
    Génère le tableau récapitulatif CHU Douera (une seule page).
    services_data: list of (service_name, nb_agents)
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet

    company = load_company_info()
    c = canvas.Canvas(output_path, pagesize=A4)
    W, H = A4

    # ── En-tête style facture ────────────────────────────────────────────────
    header_bottom_y = _draw_invoice_style_header(c, W, H, company)

    MARGIN = 1.8 * cm
    MARGIN_X = MARGIN

    # ── Titre ─────────────────────────────────────────────────────────────────
    c.setFillColor(colors.HexColor('#2c3e50'))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W / 2, header_bottom_y - 0.6 * cm,
        f"ATTACHEMENT DE MOIS DE {month_name.upper()} {year}")
    c.setFont("Helvetica", 10)
    c.drawCentredString(W / 2, header_bottom_y - 1.2 * cm,
        "PRESTATION D'entretien et nettoyage des services de CHU Douera")

    ROW_H      = 2.5*cm
    HEADER_H   = 1.0*cm
    col_widths = [1.2*cm, 9.5*cm, 3.5*cm, 3.8*cm]

    all_data = [["N", "DESIGNATION DES SERVICE", "NOMBRE D AGENT", "OBSERVATION"]]
    for i, (svc, nb) in enumerate(services_data, 1):
        all_data.append([str(i), svc, str(nb), ""])

    def make_table(chunk_data):
        n = len(chunk_data)
        heights = [HEADER_H] + [ROW_H] * (n - 1)
        tbl = Table(chunk_data, colWidths=col_widths, rowHeights=heights)
        tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, 0), 8),
            ("ALIGN",       (0, 0), (-1, 0), "CENTER"),
            ("VALIGN",      (0, 0), (-1,-1), "MIDDLE"),
            ("FONTNAME",    (0, 1), (-1,-1), "Helvetica"),
            ("FONTSIZE",    (0, 1), (-1,-1), 8),
            ("ALIGN",       (0, 1), (0, -1), "CENTER"),
            ("ALIGN",       (2, 1), (2, -1), "CENTER"),
            ("ALIGN",       (3, 1), (3, -1), "CENTER"),
            *[("BACKGROUND",(0, r), (-1, r), colors.HexColor("#f2f2f2"))
              for r in range(2, n, 2)],
            ("GRID",        (0, 0), (-1,-1), 0.5, colors.grey),
            ("INNERGRID",   (0, 0), (-1,-1), 0.3, colors.lightgrey),
        ]))
        return tbl

    first_table_top = header_bottom_y - 1.7 * cm
    avail_first = first_table_top - MARGIN_X
    avail_rest  = H - 2.5*cm - MARGIN_X

    def max_rows_in(space):
        used = HEADER_H
        count = 0
        while used + ROW_H <= space:
            used += ROW_H
            count += 1
        return max(count, 1)

    data_rows = all_data[1:]
    idx = 0
    first_page = True

    while idx < len(data_rows):
        avail = avail_first if first_page else avail_rest
        top_y = first_table_top if first_page else H - 2.5*cm

        n = max_rows_in(avail)
        chunk = [all_data[0]] + data_rows[idx : idx + n]
        idx += n

        tbl = make_table(chunk)
        tw, th = tbl.wrapOn(c, W - 3*cm, H)
        tbl.drawOn(c, MARGIN_X, top_y - th)

        if idx < len(data_rows):
            c.showPage()
            # Pages suivantes : pas de logo, juste un mini en-tête texte
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(colors.HexColor('#2c3e50'))
            c.drawCentredString(W / 2, H - 1.5*cm,
                "ATTACHEMENT " + month_name.upper() + " " + str(year) + " - suite")
            c.setStrokeColor(colors.HexColor('#bdc3c7'))
            c.setLineWidth(0.8)
            c.line(MARGIN_X, H - 2*cm, W - MARGIN_X, H - 2*cm)

        first_page = False

    c.save()


# ─────────────────────────────────────────────────────────────────────────────
#  Dialogue principal
# ─────────────────────────────────────────────────────────────────────────────

class ServiceFaitDialog(QDialog):
    """Dialogue de génération des Attestations de Service Fait"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📄 Générer Attestation de Service Fait")
        self.setMinimumSize(820, 680)
        self.setModal(True)
        self._init_ui()

    # ── Construction UI ───────────────────────────────────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)

        # Titre
        title = QLabel("📄 ATTESTATION DE SERVICE FAIT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size:18px; font-weight:bold; color:#2c3e50; padding:8px;"
        )
        root.addWidget(title)

        # ── Période ───────────────────────────────────────────────────────────
        period_box = QGroupBox("Période")
        period_box.setStyleSheet("QGroupBox { font-weight:bold; }")
        p_layout = QHBoxLayout(period_box)

        p_layout.addWidget(QLabel("Mois :"))
        self.cmb_month = QComboBox()
        self.cmb_month.addItems(MOIS_FR)
        self.cmb_month.setCurrentIndex(date.today().month - 1)
        self.cmb_month.currentIndexChanged.connect(self._update_dates)
        p_layout.addWidget(self.cmb_month)

        p_layout.addSpacing(20)
        p_layout.addWidget(QLabel("Année :"))
        self.spin_year = QSpinBox()
        self.spin_year.setRange(2020, 2035)
        self.spin_year.setValue(date.today().year)
        self.spin_year.valueChanged.connect(self._update_dates)
        p_layout.addWidget(self.spin_year)

        p_layout.addSpacing(20)
        self.lbl_dates = QLabel()
        self.lbl_dates.setStyleSheet("color:#27ae60; font-weight:bold;")
        p_layout.addWidget(self.lbl_dates)
        p_layout.addStretch()

        root.addWidget(period_box)
        self._update_dates()

        # ── Onglets ───────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_beni_messous_tab(), "🏥 CHU BENI MESSOUS")
        self.tabs.addTab(self._build_douera_tab(),       "🏥 CHU DOUERA")
        root.addWidget(self.tabs)

        # ── Boutons ───────────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_gen = QPushButton("📄 Générer le PDF")
        btn_gen.setStyleSheet(
            "QPushButton{background:#27ae60;color:white;padding:10px 20px;"
            "border-radius:5px;font-weight:bold;font-size:13px;}"
            "QPushButton:hover{background:#229954;}"
        )
        btn_gen.clicked.connect(self._generate)
        btn_layout.addWidget(btn_gen)

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setStyleSheet(
            "QPushButton{background:#e74c3c;color:white;padding:10px 20px;"
            "border-radius:5px;font-weight:bold;}"
            "QPushButton:hover{background:#c0392b;}"
        )
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        root.addLayout(btn_layout)

    # ── Onglet Beni Messous ───────────────────────────────────────────────────

    def _build_beni_messous_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        info = QLabel(
            "Cochez les services pour lesquels vous souhaitez générer une attestation.\n"
            "Une page PDF sera créée par service sélectionné."
        )
        info.setStyleSheet("color:#666; padding:4px;")
        lay.addWidget(info)

        # Boutons tout/rien
        btns = QHBoxLayout()
        btn_all = QPushButton("✅ Tout sélectionner")
        btn_all.clicked.connect(lambda: self._set_all_bm(True))
        btn_none = QPushButton("❌ Tout désélectionner")
        btn_none.clicked.connect(lambda: self._set_all_bm(False))
        btns.addWidget(btn_all)
        btns.addWidget(btn_none)
        btns.addStretch()
        lay.addLayout(btns)

        # Liste des services
        self.bm_checks = []
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setSpacing(6)

        for svc in BENI_MESSOUS_SERVICES:
            chk = QCheckBox(svc)
            chk.setChecked(True)
            chk.setStyleSheet("QCheckBox { font-size:11px; padding:4px; }")
            self.bm_checks.append(chk)
            inner_lay.addWidget(chk)

        inner_lay.addStretch()
        scroll.setWidget(inner)
        lay.addWidget(scroll)

        # Bouton ajouter service personnalisé
        add_row = QHBoxLayout()
        self.bm_custom_input = QLineEdit()
        self.bm_custom_input.setPlaceholderText("Ajouter un service personnalisé...")
        btn_add = QPushButton("➕ Ajouter")
        btn_add.clicked.connect(self._add_custom_bm_service)
        add_row.addWidget(self.bm_custom_input)
        add_row.addWidget(btn_add)
        lay.addLayout(add_row)

        self.bm_inner_lay = inner_lay  # référence pour ajout dynamique
        return w

    def _set_all_bm(self, checked):
        for chk in self.bm_checks:
            chk.setChecked(checked)

    def _add_custom_bm_service(self):
        txt = self.bm_custom_input.text().strip()
        if not txt:
            return
        chk = QCheckBox(txt)
        chk.setChecked(True)
        chk.setStyleSheet("QCheckBox { font-size:11px; padding:4px; color:#8e44ad; }")
        self.bm_checks.append(chk)
        # Insérer avant le stretch final
        self.bm_inner_lay.insertWidget(self.bm_inner_lay.count() - 1, chk)
        self.bm_custom_input.clear()

    # ── Onglet Douera ─────────────────────────────────────────────────────────

    def _build_douera_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        info = QLabel(
            "Modifiez le nombre d'agents par service. "
            "Cochez/décochez pour inclure ou exclure un service du tableau."
        )
        info.setStyleSheet("color:#666; padding:4px;")
        lay.addWidget(info)

        # Tableau
        self.douera_table = QTableWidget()
        self.douera_table.setColumnCount(3)
        self.douera_table.setHorizontalHeaderLabels(
            ["✓", "Désignation du service", "Nbre d'agents"]
        )
        header = self.douera_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.douera_table.setColumnWidth(0, 40)
        self.douera_table.setColumnWidth(2, 130)
        self.douera_table.verticalHeader().setVisible(False)
        self.douera_table.verticalHeader().setDefaultSectionSize(42)
        self.douera_table.verticalHeader().setMinimumSectionSize(42)
        self.douera_table.setAlternatingRowColors(True)
        self.douera_table.setStyleSheet(
            "QTableWidget{border:1px solid #ddd;border-radius:6px;}"
            "QHeaderView::section{background:#34495e;color:white;padding:6px;font-weight:bold;}"
        )
        self.douera_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.douera_table.setRowCount(len(DOUERA_SERVICES))
        self.douera_spinboxes = []
        self.douera_checks = []

        for row, (svc, nb) in enumerate(DOUERA_SERVICES):
            # Colonne 0 : checkbox
            chk = QCheckBox()
            chk.setChecked(True)
            chk_widget = QWidget()
            chk_lay = QHBoxLayout(chk_widget)
            chk_lay.addWidget(chk)
            chk_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_lay.setContentsMargins(0, 0, 0, 0)
            self.douera_table.setCellWidget(row, 0, chk_widget)
            self.douera_checks.append(chk)

            # Colonne 1 : nom service
            item = QTableWidgetItem(svc)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.douera_table.setItem(row, 1, item)

            # Colonne 2 : spinbox agents (dans un conteneur centré)
            spin = QSpinBox()
            spin.setRange(0, 99)
            spin.setValue(nb)
            spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin.setMinimumWidth(80)
            spin.setFixedHeight(32)
            spin.setStyleSheet(
                "QSpinBox{font-weight:bold;font-size:13px;padding:2px 6px;"
                "border:1px solid #bbb;border-radius:4px;background:white;}"
            )
            spin_widget = QWidget()
            spin_lay = QHBoxLayout(spin_widget)
            spin_lay.addWidget(spin)
            spin_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin_lay.setContentsMargins(4, 4, 4, 4)
            self.douera_table.setCellWidget(row, 2, spin_widget)
            self.douera_spinboxes.append(spin)

        lay.addWidget(self.douera_table)

        # Ligne "ajouter un service personnalisé"
        add_row = QHBoxLayout()
        self.douera_custom_input = QLineEdit()
        self.douera_custom_input.setPlaceholderText("Ajouter un service personnalisé...")
        self.douera_custom_spin = QSpinBox()
        self.douera_custom_spin.setRange(0, 99)
        self.douera_custom_spin.setValue(1)
        btn_add = QPushButton("➕ Ajouter")
        btn_add.clicked.connect(self._add_custom_douera_service)
        add_row.addWidget(self.douera_custom_input, 3)
        add_row.addWidget(QLabel("Agents:"))
        add_row.addWidget(self.douera_custom_spin)
        add_row.addWidget(btn_add)
        lay.addLayout(add_row)

        return w

    def _add_custom_douera_service(self):
        txt = self.douera_custom_input.text().strip()
        if not txt:
            return
        nb = self.douera_custom_spin.value()
        row = self.douera_table.rowCount()
        self.douera_table.insertRow(row)

        chk = QCheckBox()
        chk.setChecked(True)
        chk_widget = QWidget()
        chk_lay = QHBoxLayout(chk_widget)
        chk_lay.addWidget(chk)
        chk_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chk_lay.setContentsMargins(0, 0, 0, 0)
        self.douera_table.setCellWidget(row, 0, chk_widget)
        self.douera_checks.append(chk)

        item = QTableWidgetItem(txt)
        item.setForeground(QColor("#8e44ad"))
        self.douera_table.setItem(row, 1, item)

        spin = QSpinBox()
        spin.setRange(0, 99)
        spin.setValue(nb)
        spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spin.setMinimumWidth(80)
        spin.setFixedHeight(32)
        spin.setStyleSheet(
            "QSpinBox{font-weight:bold;font-size:13px;padding:2px 6px;"
            "border:1px solid #bbb;border-radius:4px;background:white;}"
        )
        spin_widget = QWidget()
        spin_lay = QHBoxLayout(spin_widget)
        spin_lay.addWidget(spin)
        spin_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spin_lay.setContentsMargins(4, 4, 4, 4)
        self.douera_table.setCellWidget(row, 2, spin_widget)
        self.douera_spinboxes.append(spin)

        self.douera_custom_input.clear()

    # ── Mise à jour des dates ─────────────────────────────────────────────────

    def _update_dates(self):
        m = self.cmb_month.currentIndex() + 1
        y = self.spin_year.value()
        last_day = calendar.monthrange(y, m)[1]
        self.lbl_dates.setText(f"01/{m:02d}/{y}  →  {last_day:02d}/{m:02d}/{y}")

    def _get_period(self):
        m = self.cmb_month.currentIndex() + 1
        y = self.spin_year.value()
        last_day = calendar.monthrange(y, m)[1]
        return (
            f"01/{m:02d}/{y}",
            f"{last_day:02d}/{m:02d}/{y}",
            MOIS_FR[m - 1],
            y,
        )

    # ── Génération ────────────────────────────────────────────────────────────

    def _generate(self):
        tab = self.tabs.currentIndex()
        date_debut, date_fin, month_name, year = self._get_period()

        if tab == 0:
            self._generate_beni_messous(date_debut, date_fin)
        else:
            self._generate_douera(month_name, year)

    def _generate_beni_messous(self, date_debut, date_fin):
        selected = [chk.text() for chk in self.bm_checks if chk.isChecked()]
        if not selected:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner au moins un service.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le PDF", 
            f"Service_Fait_BeniMessous_{date_debut.replace('/', '-')}.pdf",
            "PDF Files (*.pdf)"
        )
        if not path:
            return

        try:
            generate_beni_messous_pdf(selected, date_debut, date_fin, path)
            QMessageBox.information(
                self, "Succès",
                f"✅ PDF généré avec succès !\n\n"
                f"{len(selected)} attestation(s) créée(s)\n\n"
                f"Fichier : {path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération :\n{str(e)}")

    def _generate_douera(self, month_name, year):
        services_data = []
        for row in range(self.douera_table.rowCount()):
            chk_widget = self.douera_table.cellWidget(row, 0)
            chk = chk_widget.findChild(QCheckBox)
            if chk and chk.isChecked():
                svc_item = self.douera_table.item(row, 1)
                spin_widget = self.douera_table.cellWidget(row, 2)
                spin = spin_widget.findChild(QSpinBox) if spin_widget else None
                if svc_item and spin:
                    services_data.append((svc_item.text(), spin.value()))

        if not services_data:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner au moins un service.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le PDF",
            f"Service_Fait_Douera_{month_name}_{year}.pdf",
            "PDF Files (*.pdf)"
        )
        if not path:
            return

        try:
            generate_douera_pdf(month_name, year, services_data, path)
            QMessageBox.information(
                self, "Succès",
                f"✅ PDF généré avec succès !\n\n"
                f"Tableau avec {len(services_data)} service(s)\n\n"
                f"Fichier : {path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération :\n{str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
#  Point d'entrée standalone (test)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dlg = ServiceFaitDialog()
    dlg.show()
    sys.exit(app.exec())