import logging

logger = logging.getLogger(__name__)

# services/rapport_pdf_service.py
"""
Service de génération du rapport complet ENTS NET - PDF ReportLab
Sections : Employés · Clients · Salaires/Paie · Banque · Dépenses · Factures
"""

import os
from datetime import date, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie

# ── Palette ──────────────────────────────────────────────────────────────────
C_NAVY   = colors.HexColor("#1F3864")
C_BLUE   = colors.HexColor("#2980B9")
C_TEAL   = colors.HexColor("#27AE60")
C_ORANGE = colors.HexColor("#E67E22")
C_RED    = colors.HexColor("#E74C3C")
C_PURPLE = colors.HexColor("#8E44AD")
C_CYAN   = colors.HexColor("#1ABC9C")
C_DARK   = colors.HexColor("#2C3E50")
C_GRAY   = colors.HexColor("#F8F9FA")
C_LGRAY  = colors.HexColor("#ECF0F1")
C_TEXT   = colors.HexColor("#34495E")
C_WHITE  = colors.white
C_GOLD   = colors.HexColor("#F39C12")  
C_BROWN  = colors.HexColor("#7F8C8D")  

SECTION_COLORS = {
    "employes": C_BLUE,
    "clients":  C_PURPLE,
    "salaires": C_TEAL,
    "banque":   C_ORANGE,
    "depenses": C_RED,
    "factures": C_CYAN,
    "cotisations": C_GOLD,      
    "paie_globale": C_BROWN,
}

SECTION_LIST = [
    ("employes", "👥", "Employés"),
    ("clients",  "🏥", "Clients"),
    ("salaires", "💰", "Salaires & Paie"),
    ("banque",   "🏦", "Banque"),
    ("depenses", "📊", "Dépenses"),
    ("factures", "🧾", "Factures"),
    ("cotisations", "🏛️", "Cotisations Sociales"),      
    ("paie_globale", "📈", "Paie Globale"), 
]

# ── Infos entreprise ─────────────────────────────────────────────────────────
COMPANY = {
    "name":    "SARL ENTS NET",
    "address": "22 Lotissement Deux Piliers Bouzareah Alger",
    "tel":     "0552 88 30 50 / 0777 98 90 58",
    "email":   "entsnet7@gmail.com",
    "nif":     "000816098084472",
    "rc":      "16/00 0980844B08",
}

W, H = A4
MARGIN = 1.5 * cm


# ── Helpers formatage ─────────────────────────────────────────────────────────

def _fd(d) -> str:
    if not d: return "—"
    try:    return d.strftime("%d/%m/%Y")
    except: return str(d)

def _fm(v, unit="DA") -> str:
    if v is None: return "—"
    try:    return f"{float(v):,.0f} {unit}"
    except: return str(v)

def _fa(v) -> str:
    """Attribut safe : retourne '—' si manquant"""
    if v is None: return "—"
    s = str(v).strip()
    return s if s else "—"


# ── Styles ReportLab ─────────────────────────────────────────────────────────

def _mk_styles():
    s = {}
    s["sec_hdr"] = ParagraphStyle(
        "sec_hdr", fontSize=13, fontName="Helvetica-Bold",
        textColor=C_WHITE, alignment=TA_LEFT, leading=18)
    s["h2"] = ParagraphStyle(
        "h2", fontSize=10, fontName="Helvetica-Bold",
        textColor=C_DARK, spaceBefore=8, spaceAfter=5)
    s["body"] = ParagraphStyle(
        "body", fontSize=9, fontName="Helvetica",
        textColor=C_TEXT, leading=14, spaceAfter=4)
    s["toc"] = ParagraphStyle(
        "toc", fontSize=10, fontName="Helvetica",
        textColor=C_TEXT, leading=18, leftIndent=12)
    s["cover_big"] = ParagraphStyle(
        "cover_big", fontSize=26, fontName="Helvetica-Bold",
        textColor=C_WHITE, alignment=TA_CENTER, leading=32)
    s["cover_sub"] = ParagraphStyle(
        "cover_sub", fontSize=12, fontName="Helvetica",
        textColor=colors.HexColor("#BDC3C7"), alignment=TA_CENTER, leading=16)
    return s


def _tbl_style(hdr_color=C_NAVY, alt=True):
    ts = TableStyle([
        ("BACKGROUND",    (0, 0), (-1,  0),  hdr_color),
        ("TEXTCOLOR",     (0, 0), (-1,  0),  C_WHITE),
        ("FONTNAME",      (0, 0), (-1,  0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1,  0),  8.5),
        ("ALIGN",         (0, 0), (-1,  0),  "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1),  "MIDDLE"),
        ("FONTNAME",      (0, 1), (-1, -1),  "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1),  8.5),
        ("GRID",          (0, 0), (-1, -1),  0.4, colors.HexColor("#DEE2E6")),
        ("TOPPADDING",    (0, 0), (-1, -1),  5),
        ("BOTTOMPADDING", (0, 0), (-1, -1),  5),
        ("LEFTPADDING",   (0, 0), (-1, -1),  6),
        ("RIGHTPADDING",  (0, 0), (-1, -1),  6),
    ])
    if alt:
        ts.add("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_GRAY])
    return ts


def _sec_banner(title, color, st):
    """Bande colorée titre de section"""
    t = Table(
        [[Paragraph(f"  {title}", st["sec_hdr"])]],
        colWidths=[W - 3 * cm], rowHeights=[30]
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), color),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
    ]))
    return t


def _kpis(items, color):
    """Ligne de KPIs : liste de (valeur, label)"""
    n = len(items)
    cw = (W - 3 * cm) / n
    row_val = [Paragraph(
        f'<font name="Helvetica-Bold" size="16" color="#{color.hexval()[2:]}">{v}</font>',
        ParagraphStyle("kv", alignment=TA_CENTER)) for v, _ in items]
    row_lbl = [Paragraph(
        f'<font name="Helvetica" size="7.5" color="#7F8C8D">{l}</font>',
        ParagraphStyle("kl", alignment=TA_CENTER)) for _, l in items]
    t = Table([row_val, row_lbl], colWidths=[cw] * n, rowHeights=[28, 14])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#F0F8FF")),
        ("BOX",           (0, 0), (-1, -1), 1, color),
        ("LINEABOVE",     (0, 0), (-1,  0), 3, color),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _pie(values, labels, palette):
    d = Drawing(180, 110)
    vals = [max(v, 0) for v in values]
    if sum(vals) == 0:
        vals = [1, 0]
    pie = Pie()
    pie.x, pie.y = 10, 5
    pie.width = pie.height = 100
    pie.data   = vals
    pie.labels = labels
    for i, c in enumerate(palette[:len(vals)]):
        pie.slices[i].fillColor   = c
        pie.slices[i].strokeColor = C_WHITE
        pie.slices[i].strokeWidth = 1.5
    # légende
    for i, (lbl, c) in enumerate(zip(labels, palette)):
        d.add(Rect(120, 90 - i * 18, 10, 10, fillColor=c, strokeColor=None))
        d.add(String(134, 91 - i * 18, lbl,
                     fontSize=8, fontName="Helvetica", fillColor=C_DARK))
    d.add(pie)
    return d


# ── En-tête / pied de page ────────────────────────────────────────────────────

def _header_footer(canvas, doc):
    if doc.page == 1:
        return  # couverture : pas d'en-tête
    canvas.saveState()
    # bande top
    canvas.setFillColor(C_NAVY)
    canvas.rect(0, H - 0.75 * cm, W, 0.75 * cm, fill=1, stroke=0)
    canvas.setFillColor(C_WHITE)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.drawString(MARGIN, H - 0.52 * cm, "ENTS NET — Rapport de gestion")
    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(W - MARGIN, H - 0.52 * cm,
                           f"Page {doc.page}  |  {datetime.now().strftime('%d/%m/%Y')}")
    # pied
    canvas.setFillColor(colors.HexColor("#BDC3C7"))
    canvas.setFont("Helvetica", 6.5)
    canvas.drawCentredString(W / 2, 0.45 * cm,
                             f"Document confidentiel — {COMPANY['name']} — {COMPANY['address']}")
    canvas.restoreState()


# ── Chargement des données ────────────────────────────────────────────────────

def _load(session, config):
    secs = config["sections"]
    d1, d2 = config["date_debut"], config["date_fin"]
    data = {}

    # ── Employés ──
    if "employes" in secs:
        try:
            from models.employee import Employee
            emps = session.query(Employee).order_by(Employee.nom).all()
            data["employes"] = emps
            data["emp_actifs"]   = [e for e in emps if getattr(e, "est_actif", True)]
            data["emp_inactifs"] = [e for e in emps if not getattr(e, "est_actif", True)]
        except Exception:
            data["employes"] = data["emp_actifs"] = data["emp_inactifs"] = []

    # ── Clients ──
    if "clients" in secs:
        try:
            from models.client import Client
            data["clients"] = session.query(Client).order_by(Client.nom).all()
        except Exception:
            # Fallback : clients CHU connus en dur
            data["clients"] = [
                type("C", (), {"nom": "CHU BENI MESSOUS", "adresse": "Beni Messous, Alger",
                               "telephone": "", "est_actif": True})(),
                type("C", (), {"nom": "CHU DOUERA",       "adresse": "Douera, Alger",
                               "telephone": "", "est_actif": True})(),
            ]

    # ── Fiches de paie ──
    if "salaires" in secs:
        try:
            from models.payslip import Payslip
            from sqlalchemy import and_
            data["payslips"] = (session.query(Payslip)
                .filter(and_(Payslip.date_paiement >= d1, Payslip.date_paiement <= d2))
                .order_by(Payslip.date_paiement.desc()).all())
        except Exception:
            data["payslips"] = []

    # ── Banque ──
    if "banque" in secs:
        try:
            from models.bank import BankTransaction
            from sqlalchemy import and_
            data["mouvements"] = (session.query(BankTransaction)
                .filter(and_(BankTransaction.date >= d1, BankTransaction.date <= d2))
                .order_by(BankTransaction.date).all())
        except Exception:
            data["mouvements"] = []

    # ── Dépenses ──
    if "depenses" in secs:
        try:
            from models.expense import Expense
            from sqlalchemy import and_
            data["depenses"] = (session.query(Expense)
                .filter(and_(Expense.date >= d1, Expense.date <= d2))
                .order_by(Expense.date.desc()).all())
        except Exception:
            data["depenses"] = []

    # ── Factures ──
    if "factures" in secs:
        try:
            from models.invoice import Invoice as Facture
            from sqlalchemy import and_
            facts = (session.query(Facture)
                .filter(and_(Facture.date >= d1, Facture.date <= d2))
                .order_by(Facture.date.desc()).all())
            data["factures"] = facts
            data["factures_payees"]   = [f for f in facts if getattr(f, "est_payee", False)]
            data["factures_impayees"] = [f for f in facts if not getattr(f, "est_payee", False)]
        except Exception:
            data["factures"] = data["factures_payees"] = data["factures_impayees"] = []

    # ── Cotisations ── NOUVEAU
    if "cotisations" in secs:
        try:
            from models.cotisation import Cotisation
            from sqlalchemy import and_
            
            # Filtrer par date limite ou date de paiement
            cotisations = (session.query(Cotisation)
                .filter(
                    and_(
                        Cotisation.date_limite >= d1,
                        Cotisation.date_limite <= d2
                    )
                )
                .order_by(Cotisation.type_cotisation, Cotisation.annee, Cotisation.mois)
                .all())
            
            data["cotisations"] = cotisations
            
            # Regrouper par type
            from models.cotisation import TypeCotisation
            data["cotisations_cnas"] = [c for c in cotisations if c.type_cotisation == TypeCotisation.CNAS]
            data["cotisations_casnos"] = [c for c in cotisations if c.type_cotisation == TypeCotisation.CASNOS]
            data["cotisations_cacobatph"] = [c for c in cotisations if c.type_cotisation == TypeCotisation.CACOBATPH]
            data["cotisations_g50"] = [c for c in cotisations if c.type_cotisation == TypeCotisation.G50]
            
        except Exception as e:
            print(f"Erreur chargement cotisations: {e}")
            data["cotisations"] = []
            data["cotisations_cnas"] = data["cotisations_casnos"] = data["cotisations_cacobatph"] = data["cotisations_g50"] = []

    # ── Paie Globale ── NOUVEAU
    if "paie_globale" in secs:
        try:
            from models.paye_globale import PayeGlobale
            from sqlalchemy import and_
            
            paies = (session.query(PayeGlobale)
                .filter(
                    and_(
                        PayeGlobale.date_paiement >= d1,
                        PayeGlobale.date_paiement <= d2
                    )
                )
                .order_by(PayeGlobale.annee.desc(), PayeGlobale.mois.desc())
                .all())
            
            data["paies_globales"] = paies
            
            # Calculer les totaux
            total_brut = sum(p.total_brut for p in paies)
            total_cnss = sum(p.total_cnss for p in paies)
            total_net = sum(p.total_net for p in paies)
            
            data["paie_totaux"] = {
                "brut": total_brut,
                "cnss": total_cnss,
                "net": total_net,
                "nb_mois": len(paies)
            }
            
        except Exception as e:
            print(f"Erreur chargement paie globale: {e}")
            data["paies_globales"] = []
            data["paie_totaux"] = {"brut": 0, "cnss": 0, "net": 0, "nb_mois": 0}
    
    return data


# ── Constructeurs de sections ─────────────────────────────────────────────────

def _s_employes(data, st, config, cb):
    story = []
    color = SECTION_COLORS["employes"]
    emps = data.get("employes", [])
    actifs = data.get("emp_actifs", [])
    inactifs = data.get("emp_inactifs", [])

    story.append(_sec_banner("👥  EMPLOYÉS", color, st))
    story.append(Spacer(1, 8))

    masse = sum(float(getattr(e, "salaire", 0) or 0) for e in actifs)
    story.append(_kpis([
        (len(emps),      "Total effectifs"),
        (len(actifs),    "Actifs"),
        (len(inactifs),  "Inactifs"),
        (_fm(masse),     "Masse salariale"),
    ], color))
    story.append(Spacer(1, 10))

    # Tableau employés
    story.append(Paragraph("Liste du personnel", st["h2"]))
    rows = [["Matricule", "Nom & Prénom", "Poste", "Date embauche", "Salaire (DA)", "Statut"]]
    for e in emps:
        nom   = f"{_fa(getattr(e,'nom',''))} {_fa(getattr(e,'prenom',''))}".strip() or "—"
        rows.append([
            _fa(getattr(e, "code_employe", None)) or _fa(getattr(e, "matricule", None)),
            nom,
            _fa(getattr(e, "poste", None)),
            _fd(getattr(e, "date_embauche", None)),
            _fm(getattr(e, "salaire", None)),
            "✅ Actif" if getattr(e, "est_actif", True) else "⛔ Inactif",
        ])
    cw = [2.2*cm, 4.5*cm, 3.5*cm, 2.8*cm, 2.8*cm, 1.8*cm]
    t = Table(rows, colWidths=cw, repeatRows=1)
    ts = _tbl_style(color)
    for i, e in enumerate(emps, 1):
        c_txt = C_TEAL if getattr(e, "est_actif", True) else C_RED
        ts.add("TEXTCOLOR", (5, i), (5, i), c_txt)
    t.setStyle(ts)
    story.append(t)

    if config.get("graphiques") and (actifs or inactifs):
        story.append(Spacer(1, 8))
        story.append(Paragraph("Répartition actifs / inactifs", st["h2"]))
        story.append(_pie([len(actifs), len(inactifs)], ["Actifs", "Inactifs"], [C_TEAL, C_RED]))

    cb(15, "Section Employés…")
    return story


def _s_clients(data, st, config, cb):
    story = []
    color   = SECTION_COLORS["clients"]
    clients = data.get("clients", [])

    story.append(_sec_banner("🏥  CLIENTS", color, st))
    story.append(Spacer(1, 8))
    story.append(_kpis([(len(clients), "Total clients")], color))
    story.append(Spacer(1, 10))

    if clients:
        story.append(Paragraph("Liste des clients", st["h2"]))
        rows = [["Nom / Structure", "Adresse", "Téléphone", "Statut"]]
        for cl in clients:
            rows.append([
                _fa(getattr(cl, "nom", None)),
                _fa(getattr(cl, "adresse", None)),
                _fa(getattr(cl, "telephone", None)),
                "Actif" if getattr(cl, "est_actif", True) else "Inactif",
            ])
        cw = [5.5*cm, 5*cm, 3*cm, 2*cm]
        t = Table(rows, colWidths=cw, repeatRows=1)
        t.setStyle(_tbl_style(color))
        story.append(t)
    else:
        story.append(Paragraph("Aucun client enregistré.", st["body"]))

    cb(25, "Section Clients…")
    return story


def _s_salaires(data, st, config, cb):
    story = []
    color    = SECTION_COLORS["salaires"]
    payslips = data.get("payslips", [])

    story.append(_sec_banner("💰  SALAIRES & PAIE", color, st))
    story.append(Spacer(1, 8))

    tot_brut = sum(float(getattr(p, "salaire_brut", 0) or 0) for p in payslips)
    tot_net  = sum(float(getattr(p, "salaire_net",  0) or 0) for p in payslips)
    tot_cot  = sum(float(getattr(p, "cotisation_ouvriere", 0) or 0) for p in payslips)

    story.append(_kpis([
        (len(payslips),   "Fiches générées"),
        (_fm(tot_brut),   "Total brut"),
        (_fm(tot_net),    "Total net"),
        (_fm(tot_cot),    "Total cotisations"),
    ], color))
    story.append(Spacer(1, 10))

    if payslips:
        story.append(Paragraph("Détail des fiches de paie", st["h2"]))
        rows = [["Employé", "Mois", "Année", "Brut (DA)", "Net (DA)", "Cotisation (DA)"]]
        for p in payslips:
            # Cherche le nom de l'employé
            emp_name = "—"
            try:
                from models.employee import Employee
                from database.db import get_session
                with get_session() as s2:
                    eid = getattr(p, "employee_id", None) or getattr(p, "employe_id", None)
                    if eid:
                        e = s2.query(Employee).filter(Employee.id == eid).first()
                        if e: 
                            emp_name = f"{_fa(getattr(e,'nom',''))} {_fa(getattr(e,'prenom',''))}".strip()
            except Exception:
                pass
            rows.append([
                emp_name,
                str(getattr(p, "mois",  "—")),
                str(getattr(p, "annee", "—")),
                _fm(getattr(p, "salaire_brut",       None)),
                _fm(getattr(p, "salaire_net",         None)),
                _fm(getattr(p, "cotisation_ouvriere", None)),
            ])
        cw = [4*cm, 1.5*cm, 1.5*cm, 2.8*cm, 2.8*cm, 3*cm]
        t = Table(rows, colWidths=cw, repeatRows=1)
        t.setStyle(_tbl_style(color))
        story.append(t)
    else:
        story.append(Paragraph("Aucune fiche de paie sur la période sélectionnée.", st["body"]))

    cb(42, "Section Salaires…")
    return story


def _s_banque(data, st, config, cb):
    story = []
    color = SECTION_COLORS["banque"]
    mvts  = data.get("mouvements", [])

    story.append(_sec_banner("🏦  BANQUE", color, st))
    story.append(Spacer(1, 8))

    credits = [m for m in mvts if float(getattr(m, "montant", 0) or 0) > 0]
    debits  = [m for m in mvts if float(getattr(m, "montant", 0) or 0) < 0]
    tot_c   = sum(float(getattr(m, "montant", 0) or 0) for m in credits)
    tot_d   = abs(sum(float(getattr(m, "montant", 0) or 0) for m in debits))

    story.append(_kpis([
        (len(mvts),     "Mouvements"),
        (_fm(tot_c),    "Total crédits"),
        (_fm(tot_d),    "Total débits"),
        (_fm(tot_c - tot_d), "Solde période"),
    ], color))
    story.append(Spacer(1, 10))

    if mvts:
        story.append(Paragraph("Relevé des mouvements", st["h2"]))
        rows = [["Date", "Libellé", "Référence", "Débit (DA)", "Crédit (DA)"]]
        for m in mvts:
            mt = float(getattr(m, "montant", 0) or 0)
            rows.append([
                _fd(getattr(m, "date", None)),
                _fa(getattr(m, "libelle", None)),
                _fa(getattr(m, "reference", None)),
                _fm(abs(mt)) if mt < 0 else "—",
                _fm(mt)      if mt > 0 else "—",
            ])
        # Ligne total
        rows.append(["", "TOTAL", "", _fm(tot_d), _fm(tot_c)])
        cw = [2.2*cm, 5*cm, 2.5*cm, 2.8*cm, 2.8*cm]
        t = Table(rows, colWidths=cw, repeatRows=1)
        ts = _tbl_style(color)
        last = len(rows) - 1
        ts.add("BACKGROUND", (0, last), (-1, last), C_LGRAY)
        ts.add("FONTNAME",   (0, last), (-1, last), "Helvetica-Bold")
        # colorier débits/crédits
        for i, m in enumerate(mvts, 1):
            mt = float(getattr(m, "montant", 0) or 0)
            if mt < 0: ts.add("TEXTCOLOR", (3, i), (3, i), C_RED)
            if mt > 0: ts.add("TEXTCOLOR", (4, i), (4, i), C_TEAL)
        t.setStyle(ts)
        story.append(t)
    else:
        story.append(Paragraph("Aucun mouvement bancaire sur la période sélectionnée.", st["body"]))

    cb(57, "Section Banque…")
    return story


def _s_depenses(data, st, config, cb):
    story = []
    color = SECTION_COLORS["depenses"]
    deps  = data.get("depenses", [])

    story.append(_sec_banner("📊  DÉPENSES", color, st))
    story.append(Spacer(1, 8))

    total = sum(float(getattr(d, "montant", 0) or 0) for d in deps)
    cats  = {}
    for d in deps:
        cat = getattr(d, "categorie", "Autre") or "Autre"
        cats[cat] = cats.get(cat, 0) + float(getattr(d, "montant", 0) or 0)

    story.append(_kpis([
        (len(deps),       "Opérations"),
        (_fm(total),      "Total dépensé"),
        (len(cats),       "Catégories"),
    ], color))
    story.append(Spacer(1, 10))

    # Tableau par catégorie
    if cats:
        story.append(Paragraph("Répartition par catégorie", st["h2"]))
        rows = [["Catégorie", "Nb opérations", "Montant (DA)", "% du total"]]
        for cat, mt in sorted(cats.items(), key=lambda x: -x[1]):
            nb  = sum(1 for d in deps if (getattr(d, "categorie", "Autre") or "Autre") == cat)
            pct = (mt / total * 100) if total else 0
            rows.append([cat, str(nb), _fm(mt), f"{pct:.1f}%"])
        cw = [5*cm, 2.8*cm, 4*cm, 2.5*cm]
        t = Table(rows, colWidths=cw, repeatRows=1)
        t.setStyle(_tbl_style(color))
        story.append(t)
        story.append(Spacer(1, 8))

        if config.get("graphiques") and len(cats) >= 2:
            vals   = [v for v in cats.values()]
            labels = [k for k in cats.keys()]
            palette = [C_RED, C_ORANGE, C_BLUE, C_PURPLE, C_TEAL, C_CYAN]
            story.append(Paragraph("Répartition graphique", st["h2"]))
            story.append(_pie(vals, labels, palette))
            story.append(Spacer(1, 8))

    # Détail
    if deps:
        story.append(Paragraph("Détail des dépenses", st["h2"]))
        rows = [["Date", "Libellé", "Catégorie", "Fournisseur", "Montant (DA)"]]
        for d in deps:
            rows.append([
                _fd(getattr(d, "date", None)),
                _fa(getattr(d, "libelle",     None)),
                _fa(getattr(d, "categorie",   None)),
                _fa(getattr(d, "fournisseur", None)),
                _fm(getattr(d, "montant",     None)),
            ])
        cw = [2.2*cm, 4.5*cm, 3*cm, 3.5*cm, 2.5*cm]
        t = Table(rows, colWidths=cw, repeatRows=1)
        t.setStyle(_tbl_style(color))
        story.append(t)
    else:
        story.append(Paragraph("Aucune dépense sur la période sélectionnée.", st["body"]))

    cb(72, "Section Dépenses…")
    return story


def _s_factures(data, st, config, cb):
    story = []
    color    = SECTION_COLORS["factures"]
    factures = data.get("factures", [])
    payees   = data.get("factures_payees",   [])
    impayees = data.get("factures_impayees", [])

    story.append(_sec_banner("🧾  FACTURES", color, st))
    story.append(Spacer(1, 8))

    tot_p = sum(float(getattr(f, "montant_ttc", 0) or 0) for f in payees)
    tot_i = sum(float(getattr(f, "montant_ttc", 0) or 0) for f in impayees)

    story.append(_kpis([
        (len(factures),  "Total factures"),
        (len(payees),    "Payées"),
        (len(impayees),  "Impayées"),
        (_fm(tot_i),     "Montant en attente"),
    ], color))
    story.append(Spacer(1, 10))

    # ─ Factures IMPAYÉES (priorité) ─
    if impayees:
        story.append(Paragraph("⚠️  Factures impayées", st["h2"]))
        rows = [["N° Facture", "Client", "Date", "Échéance", "Montant TTC", "Retard"]]
        today = date.today()
        for f in sorted(impayees, key=lambda x: getattr(x, "date_echeance", date.today()) or date.today()):
            ech    = getattr(f, "date_echeance", None)
            retard = ""
            if ech:
                jours = (today - ech).days
                retard = f"{jours} j" if jours > 0 else "—"
            rows.append([
                _fa(getattr(f, "numero",      None)),
                _fa(getattr(f, "client_nom",  None)) or _fa(getattr(f, "client", None)),
                _fd(getattr(f, "date",        None)),
                _fd(ech),
                _fm(getattr(f, "montant_ttc", None)),
                retard,
            ])
        cw = [2.2*cm, 4.5*cm, 2.2*cm, 2.2*cm, 2.8*cm, 1.5*cm]
        t = Table(rows, colWidths=cw, repeatRows=1)
        ts = _tbl_style(C_RED)
        for i, f in enumerate(sorted(impayees,
                key=lambda x: getattr(x, "date_echeance", date.today()) or date.today()), 1):
            ech = getattr(f, "date_echeance", None)
            if ech and (date.today() - ech).days > 0:
                ts.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FDECEA"))
        t.setStyle(ts)
        story.append(t)
        story.append(Spacer(1, 10))

    # ─ Factures PAYÉES ─
    if payees:
        story.append(Paragraph("✅  Factures payées", st["h2"]))
        rows = [["N° Facture", "Client", "Date", "Date paiement", "Montant TTC"]]
        for f in payees:
            rows.append([
                _fa(getattr(f, "numero",         None)),
                _fa(getattr(f, "client_nom",     None)) or _fa(getattr(f, "client", None)),
                _fd(getattr(f, "date",           None)),
                _fd(getattr(f, "date_paiement",  None)),
                _fm(getattr(f, "montant_ttc",    None)),
            ])
        cw = [2.2*cm, 5*cm, 2.2*cm, 2.5*cm, 3*cm]
        t = Table(rows, colWidths=cw, repeatRows=1)
        t.setStyle(_tbl_style(color))
        story.append(t)

    if not factures:
        story.append(Paragraph("Aucune facture sur la période sélectionnée.", st["body"]))

    if config.get("graphiques") and factures:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Payées vs Impayées", st["h2"]))
        story.append(_pie([len(payees), len(impayees)],
                         ["Payées", "Impayées"], [C_TEAL, C_RED]))

    cb(88, "Section Factures…")
    return story


# ── Constructeurs de sections ─────────────────────────────────────────────────

def _s_cotisations(data, st, config, cb):
    story = []
    color = SECTION_COLORS["cotisations"]
    
    cotisations = data.get("cotisations", [])
    cnas = data.get("cotisations_cnas", [])
    casnos = data.get("cotisations_casnos", [])
    cacobatph = data.get("cotisations_cacobatph", [])
    g50 = data.get("cotisations_g50", [])

    story.append(_sec_banner("🏛️  COTISATIONS SOCIALES", color, st))
    story.append(Spacer(1, 8))

    # Totaux
    total_du = sum(c.montant_du for c in cotisations)
    total_paye = sum(c.montant_paye for c in cotisations)
    total_solde = total_du - total_paye
    
    story.append(_kpis([
        (len(cotisations), "Échéances"),
        (_fm(total_du), "Total dû"),
        (_fm(total_paye), "Total payé"),
        (_fm(total_solde), "Solde restant"),
    ], color))
    story.append(Spacer(1, 10))

    # Résumé par type
    if cnas or casnos or cacobatph or g50:
        story.append(Paragraph("Résumé par type de cotisation", st["h2"]))
        rows = [["Type", "Nb échéances", "Montant dû", "Montant payé", "Solde"]]
        
        for type_cot, nom, liste in [
            (cnas, "CNAS", cnas),
            (casnos, "CASNOS", casnos),
            (cacobatph, "CACOBATPH", cacobatph),
            (g50, "G50", g50)
        ]:
            if liste:
                du = sum(c.montant_du for c in liste)
                paye = sum(c.montant_paye for c in liste)
                solde = du - paye
                rows.append([
                    nom,
                    str(len(liste)),
                    _fm(du),
                    _fm(paye),
                    _fm(solde)
                ])
        
        cw = [3*cm, 2.5*cm, 3.5*cm, 3.5*cm, 3.5*cm]
        t = Table(rows, colWidths=cw, repeatRows=1)
        t.setStyle(_tbl_style(color))
        story.append(t)
        story.append(Spacer(1, 10))

    # Détail des cotisations
    if cotisations:
        story.append(Paragraph("Détail des échéances", st["h2"]))
        rows = [["Type", "Période", "Date limite", "Montant dû", "Payé", "Statut"]]
        
        for c in sorted(cotisations, key=lambda x: (x.type_cotisation.value, x.annee, x.mois or 0)):
            statut_emoji = {
                "PAYE": "✅ Payé",
                "EN_ATTENTE": "⏳ En attente",
                "EN_RETARD": "⚠️ En retard"
            }.get(c.statut.value if hasattr(c.statut, 'value') else str(c.statut), str(c.statut))
            
            rows.append([
                c.type_cotisation.value if hasattr(c.type_cotisation, 'value') else str(c.type_cotisation),
                c.label_periode,
                _fd(c.date_limite),
                _fm(c.montant_du),
                _fm(c.montant_paye),
                statut_emoji
            ])
        
        cw = [2.5*cm, 3*cm, 2.5*cm, 3*cm, 3*cm, 3.5*cm]
        t = Table(rows, colWidths=cw, repeatRows=1)
        ts = _tbl_style(color)
        
        # Colorier selon le statut
        for i, c in enumerate(cotisations, 1):
            if hasattr(c, 'statut'):
                statut_val = c.statut.value if hasattr(c.statut, 'value') else str(c.statut)
                if statut_val == "PAYE":
                    ts.add("TEXTCOLOR", (5, i), (5, i), C_TEAL)
                elif statut_val == "EN_RETARD":
                    ts.add("TEXTCOLOR", (5, i), (5, i), C_RED)
                    ts.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FDECEA"))
        
        t.setStyle(ts)
        story.append(t)
        
        if config.get("graphiques") and len(cotisations) > 0:
            story.append(Spacer(1, 8))
            story.append(Paragraph("Répartition des montants par type", st["h2"]))
            
            # Préparer les données pour le graphique
            types = []
            montants = []
            for type_cot, nom in [(cnas, "CNAS"), (casnos, "CASNOS"), (cacobatph, "CACOBATPH"), (g50, "G50")]:
                if type_cot:
                    montant = sum(c.montant_du for c in type_cot)
                    if montant > 0:
                        types.append(nom)
                        montants.append(montant)
            
            if types:
                palette = [C_BLUE, C_TEAL, C_ORANGE, C_PURPLE]
                story.append(_pie(montants, types, palette))
    else:
        story.append(Paragraph("Aucune cotisation sur la période sélectionnée.", st["body"]))

    cb(65, "Section Cotisations…")
    return story


def _s_paie_globale(data, st, config, cb):
    story = []
    color = SECTION_COLORS["paie_globale"]
    
    paies = data.get("paies_globales", [])
    totaux = data.get("paie_totaux", {"brut": 0, "cnss": 0, "net": 0, "nb_mois": 0})

    story.append(_sec_banner("📈  PAIE GLOBALE", color, st))
    story.append(Spacer(1, 8))

    story.append(_kpis([
        (totaux["nb_mois"], "Mois traités"),
        (_fm(totaux["brut"]), "Total brut"),
        (_fm(totaux["cnss"]), "Total CNSS"),
        (_fm(totaux["net"]), "Total net"),
    ], color))
    story.append(Spacer(1, 10))

    if paies:
        story.append(Paragraph("Récapitulatif mensuel", st["h2"]))
        rows = [["Période", "Date paiement", "Brut (DA)", "CNSS (DA)", "Net (DA)", "Nb répartitions"]]
        
        for p in paies:
            nb_repartitions = len(p.repartitions) if hasattr(p, 'repartitions') else 0
            rows.append([
                p.periode,
                _fd(p.date_paiement),
                _fm(p.total_brut),
                _fm(p.total_cnss),
                _fm(p.total_net),
                str(nb_repartitions)
            ])
        
        cw = [2.5*cm, 2.5*cm, 3*cm, 3*cm, 3*cm, 2.5*cm]
        t = Table(rows, colWidths=cw, repeatRows=1)
        t.setStyle(_tbl_style(color))
        story.append(t)
        story.append(Spacer(1, 10))

        # Détail des répartitions (pour le dernier mois ou tous)
        if config.get("graphiques") and paies:
            # Prendre la dernière paie pour le détail
            derniere_paie = paies[0]
            if hasattr(derniere_paie, 'repartitions') and derniere_paie.repartitions:
                story.append(Paragraph(f"Détail de la paie - {derniere_paie.periode}", st["h2"]))
                
                rows = [["Site/Client", "Nb agents", "Brut", "CNSS", "Net"]]
                for rep in derniere_paie.repartitions:
                    rows.append([
                        rep.nom_affichage,
                        str(rep.nombre_agents),
                        _fm(rep.montant_brut),
                        _fm(rep.montant_cnss),
                        _fm(rep.montant_net)
                    ])
                
                # Ligne total
                rows.append([
                    "TOTAL",
                    str(sum(r.nombre_agents for r in derniere_paie.repartitions)),
                    _fm(derniere_paie.total_brut),
                    _fm(derniere_paie.total_cnss),
                    _fm(derniere_paie.total_net)
                ])
                
                cw = [5*cm, 2*cm, 3*cm, 3*cm, 3*cm]
                t = Table(rows, colWidths=cw, repeatRows=1)
                ts = _tbl_style(color)
                last = len(rows) - 1
                ts.add("BACKGROUND", (0, last), (-1, last), C_LGRAY)
                ts.add("FONTNAME", (0, last), (-1, last), "Helvetica-Bold")
                t.setStyle(ts)
                story.append(t)
                
                if config.get("graphiques"):
                    story.append(Spacer(1, 8))
                    story.append(Paragraph("Répartition par site", st["h2"]))
                    
                    # Préparer les données pour le graphique
                    sites = []
                    montants = []
                    for rep in derniere_paie.repartitions[:5]:  # Top 5
                        sites.append(rep.nom_affichage[:15] + "..." if len(rep.nom_affichage) > 15 else rep.nom_affichage)
                        montants.append(rep.montant_net)
                    
                    if sites:
                        palette = [C_BLUE, C_TEAL, C_ORANGE, C_PURPLE, C_CYAN]
                        story.append(_pie(montants, sites, palette))
    else:
        story.append(Paragraph("Aucune paie globale sur la période sélectionnée.", st["body"]))

    cb(75, "Section Paie Globale…")
    return story


# ── Service principal ──────────────────────────────────────────────────────────

class RapportPDFService:

    def __init__(self, progress_callback=None):
        self._cb = progress_callback or (lambda p, m: None)

    def generate(self, config: dict) -> str:
        from database.db import get_session
        with get_session() as session:
            self._cb(5, "Chargement des données…")
            data = _load(session, config)
            self._cb(10, "Construction du rapport…")
            return self._build(config, data)

    def _build(self, config, data) -> str:
        st    = _mk_styles()
        story = []
        d1, d2 = config["date_debut"], config["date_fin"]

        # ── COUVERTURE ────────────────────────────────────────────────────
        if config.get("couverture"):
            story.append(Spacer(1, 2.5 * cm))
            cov = Table(
                [[Paragraph(COMPANY["name"], st["cover_big"])],
                 [Spacer(1, 4)],
                 [Paragraph("Rapport de Gestion", ParagraphStyle(
                     "_rs", fontSize=16, fontName="Helvetica",
                     textColor=colors.HexColor("#85C1E9"), alignment=TA_CENTER))],
                 [Spacer(1, 10)],
                 [HRFlowable(width=7 * cm, thickness=2, color=C_BLUE, spaceAfter=8)],
                 [Paragraph(f"Période : {_fd(d1)}  —  {_fd(d2)}", st["cover_sub"])],
                 [Spacer(1, 5)],
                 [Paragraph(
                     f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
                     ParagraphStyle("_gd", fontSize=9, fontName="Helvetica",
                                    textColor=colors.HexColor("#7F8C8D"), alignment=TA_CENTER))],
                 ],
                colWidths=[W - 3 * cm],
            )
            cov.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), C_NAVY),
                ("TOPPADDING",    (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING",   (0, 0), (-1, -1), 30),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 30),
            ]))
            story.append(cov)
            story.append(Spacer(1, 1.5 * cm))

            # Pastilles sections
            secs_inc = [(k, ic, ti) for k, ic, ti in SECTION_LIST if k in config["sections"]]
            for i in range(0, len(secs_inc), 3):
                chunk = secs_inc[i:i+3]
                while len(chunk) < 3: chunk.append(("_", " ", ""))
                row_cells = []
                for key, ico, ti in chunk:
                    c = SECTION_COLORS.get(key, C_NAVY)
                    row_cells.append(Table(
                        [[Paragraph(f"{ico}  {ti}", ParagraphStyle(
                            "_p", fontSize=8.5, fontName="Helvetica-Bold",
                            textColor=C_WHITE, alignment=TA_CENTER))]],
                        colWidths=[3.5 * cm], rowHeights=[20]
                    ))
                    row_cells[-1].setStyle(TableStyle([
                        ("BACKGROUND",    (0,0),(-1,-1), c if ti else C_LGRAY),
                        ("TOPPADDING",    (0,0),(-1,-1), 4),
                        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
                    ]))
                rt = Table([row_cells], colWidths=[3.8 * cm] * 3)
                story.append(rt)
                story.append(Spacer(1, 5))

            story.append(PageBreak())

        # ── SOMMAIRE ──────────────────────────────────────────────────────
        if config.get("sommaire"):
            story.append(Paragraph("Sommaire", ParagraphStyle(
                "_som", fontSize=15, fontName="Helvetica-Bold",
                textColor=C_NAVY, spaceAfter=12)))
            story.append(HRFlowable(width="100%", thickness=1.5,
                                     color=C_NAVY, spaceAfter=10))
            for i, (k, ic, ti) in enumerate(SECTION_LIST, 1):
                if k in config["sections"]:
                    story.append(Paragraph(
                        f"  {i}.  {ic}  {ti}", st["toc"]))
            story.append(PageBreak())

        # ── SECTIONS ──────────────────────────────────────────────────────
        builders = {
            "employes": _s_employes,
            "clients":  _s_clients,
            "salaires": _s_salaires,
            "banque":   _s_banque,
            "depenses": _s_depenses,
            "factures": _s_factures,
            "cotisations": _s_cotisations,      
            "paie_globale": _s_paie_globale,
        }
        for key, _, _ in SECTION_LIST:
            if key in config["sections"] and key in builders:
                story += builders[key](data, st, config, self._cb)
                story.append(PageBreak())

        # ── BUILD ─────────────────────────────────────────────────────────
        self._cb(95, "Écriture du fichier PDF…")
        out = config["output_path"]
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

        doc = SimpleDocTemplate(
            out, pagesize=A4,
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=1.1 * cm, bottomMargin=1.1 * cm,
            title=f"Rapport ENTS NET {_fd(d1)} – {_fd(d2)}",
            author=COMPANY["name"],
        )
        doc.build(story,
                  onFirstPage=_header_footer,
                  onLaterPages=_header_footer)
        self._cb(100, "✅ Rapport généré !")
        return out