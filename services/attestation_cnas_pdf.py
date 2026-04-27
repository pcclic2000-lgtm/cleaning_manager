# services/attestation_cnas_pdf.py
import os
from io import BytesIO
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

try:
    from PIL import Image as _PILImage  # noqa: F401
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from pypdf import PdfReader, PdfWriter

from database.db import SessionLocal, get_session
from models.employee import Employee
from models.payslip import Payslip
from models.company import CompanyInfo
import sys


class AttestationCNASPDFGenerator:

    def __init__(self):
        # Chemin absolu basé sur le projet
        if hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.TEMPLATE_PATH = os.path.join(base_dir, "templates", "AS-08.pdf")
        self.STAMP_PATH = os.path.join(base_dir, "assets", "cachet.png")
        self.SIGNATURE_PATH = os.path.join(base_dir, "assets", "signature.png")

        if not os.path.exists(self.TEMPLATE_PATH):
            raise FileNotFoundError(
                f"Template AS-08.pdf introuvable.\nChemin recherché : {self.TEMPLATE_PATH}"
            )

    # ======================================================
    # OUTILS DE POSITIONNEMENT PRÉCIS
    # ======================================================

    def _draw_text(self, c, x_mm, y_mm, text, size=9):
        """Dessine du texte à une position précise en mm"""
        if not text:
            return
        c.setFont("Helvetica", size)
        c.drawString(x_mm * mm, (297 - y_mm) * mm, str(text))

    def _draw_right_text(self, c, x_mm, y_mm, text, size=9):
        """Dessine du texte aligné à droite"""
        if not text:
            return
        c.setFont("Helvetica", size)
        width = c.stringWidth(str(text), "Helvetica", size)
        c.drawString((x_mm * mm) - width, (297 - y_mm) * mm, str(text))

    def _draw_centered_text(self, c, x_mm, y_mm, text, size=9):
        """Dessine du texte centré"""
        if not text:
            return
        c.setFont("Helvetica", size)
        width = c.stringWidth(str(text), "Helvetica", size)
        c.drawString((x_mm * mm) - (width/2), (297 - y_mm) * mm, str(text))

    # ======================================================
    # CALCUL DES JOURS TRAVAILLÉS (CORRIGÉ)
    # ======================================================

    def _calculate_worked_days(self, employee, month_date):
        """
        Calcule le nombre de jours travaillés pour un mois donné
        Par défaut 30 jours, sauf si l'embauche est dans le mois
        """
        if not employee.date_embauche:
            return 30
        
        # CORRECTION: Convertir month_date (datetime) en date si nécessaire
        if isinstance(month_date, datetime):
            month_date = month_date.date()
        
        # Premier jour du mois concerné
        first_day = date(month_date.year, month_date.month, 1)
        
        # Dernier jour du mois concerné
        if month_date.month == 12:
            last_day = date(month_date.year, 12, 31)
        else:
            last_day = date(month_date.year, month_date.month + 1, 1) - relativedelta(days=1)
        
        # Si l'embauche est après ce mois
        if employee.date_embauche > last_day:
            return 0
        
        # Si l'embauche est dans ce mois
        if employee.date_embauche >= first_day and employee.date_embauche <= last_day:
            # Jours depuis l'embauche jusqu'à la fin du mois
            days_worked = (last_day - employee.date_embauche).days + 1
            return days_worked
        
        # Sinon, mois complet
        return 30

    def _calculate_salary_for_days(self, employee, month_date, base_salary):
        """
        Calcule le salaire proratisé en fonction des jours travaillés
        """
        days_worked = self._calculate_worked_days(employee, month_date)
        if days_worked == 0:
            return 0
        
        # Salaire pour 30 jours (base)
        monthly_salary = base_salary or 0
        
        # Proratisation
        return (monthly_salary / 30) * days_worked

    # ======================================================
    # GÉNÉRATION PRINCIPALE
    # ======================================================

    def generate(self, employee_id: int, output_path: str):
        try:
            with get_session() as session:
                employee = session.query(Employee).filter(
                    Employee.id == employee_id,
                    Employee.est_actif == True
                ).first()

                if not employee:
                    raise ValueError("Employé introuvable")

                company = session.query(CompanyInfo).first()
                if not company:
                    raise ValueError("Entreprise non configurée")

                # Récupérer les 12 derniers bulletins
                salaries = session.query(Payslip) \
                    .filter(Payslip.employee_id == employee_id) \
                    .order_by(Payslip.period_year.desc(),
                              Payslip.period_month.desc()) \
                    .limit(12).all()

                salary_dict = {
                    f"{p.period_year}-{p.period_month:02d}": p
                    for p in salaries
                }

                # ==========================================
                # CRÉER L'OVERLAY PDF
                # ==========================================

                packet = BytesIO()
                c = canvas.Canvas(packet, pagesize=A4)

                # ================= PAGE 1 =================
                # Coordonnées mesurées depuis le HAUT de la page (0 = haut)

                # --- SECTION EMPLOYEUR (EN HAUT) ---
                # Nom et prénom / Raison sociale
                self._draw_text(c, 45, 45, company.nom, size=10)  # "Nom et prénom" et "Raison sociale"
                
                # N° adhérent
                self._draw_text(c, 45, 53, company.numero_employeur or "", size=10)
                
                # Adresse
                adresse_complete = f"{company.adresse or ''}, {company.ville or ''} {company.code_postal or ''}"
                self._draw_text(c, 45, 61, adresse_complete, size=9)

                # --- SECTION IDENTIFICATION DU SALARIÉ ---
                # Nom et prénom
                nom_complet = f"{employee.nom} {employee.prenom}"
                self._draw_text(c, 45, 82, nom_complet, size=10)
                
                # N° identification (N° de sécurité sociale)
                self._draw_text(c, 45, 90, employee.numero_secu or "", size=10)
                
                # Né le
                date_naissance = employee.date_naissance.strftime("%d/%m/%Y") if employee.date_naissance else ""
                self._draw_text(c, 45, 98, date_naissance, size=10)
                
                # Adresse
                self._draw_text(c, 45, 106, employee.adresse or "", size=9)
                
                # Profession
                self._draw_text(c, 45, 114, employee.poste or "", size=10)

                # --- SECTION RENSEIGNEMENTS POUR ÉTUDE DE DROIT ---
                # Date de recrutement
                date_embauche = employee.date_embauche.strftime("%d/%m/%Y") if employee.date_embauche else ""
                self._draw_text(c, 45, 135, date_embauche, size=10)

                c.showPage()

                # ================= PAGE 2 =================
                # TABLEAU DES 12 DERNIERS MOIS

                # Calculer la période des 12 derniers mois
                today = datetime.now()
                y_start = 120  # Position Y de départ du tableau
                row_gap = 7.5   # Espacement entre les lignes

                # En-têtes du tableau
                self._draw_text(c, 25, 110, "Mois et année de référence", size=8)
                self._draw_text(c, 75, 110, "Nombre de jours travaillés", size=8)
                self._draw_text(c, 115, 110, "Volume horaire journalier", size=8)
                self._draw_text(c, 155, 110, "Salaire soumis à cotisation", size=8)
                self._draw_text(c, 195, 110, "Montant de la cotisation", size=8)

                # Ligne de séparation
                c.line(20*mm, (297-112)*mm, 200*mm, (297-112)*mm)

                for i in range(12):
                    date_ref = today - relativedelta(months=i)
                    key = f"{date_ref.year}-{date_ref.month:02d}"
                    pay = salary_dict.get(key)

                    y = y_start + (i * row_gap)

                    # Mois et année de référence
                    periode = f"{date_ref.month:02d}/{date_ref.year}"
                    self._draw_text(c, 25, y, periode, size=8)

                    if pay:
                        # CORRECTION: Passer date_ref (datetime) à la méthode
                        jours_travailles = self._calculate_worked_days(employee, date_ref)
                        self._draw_centered_text(c, 87, y, str(jours_travailles), size=8)

                        # Volume horaire journalier (8H par défaut)
                        self._draw_centered_text(c, 127, y, "8H", size=8)

                        # Salaire soumis à cotisation (proratisé si mois partiel)
                        salaire_base = float(pay.gross_salary or 0)
                        salaire_proratise = self._calculate_salary_for_days(employee, date_ref, salaire_base)
                        self._draw_right_text(c, 170, y, f"{salaire_proratise:,.0f}", size=8)

                        # Montant de la cotisation (9% du salaire proratisé)
                        cotisation = salaire_proratise * 0.09
                        self._draw_right_text(c, 205, y, f"{cotisation:,.0f}", size=8)
                    else:
                        # Pas de bulletin pour ce mois
                        self._draw_centered_text(c, 87, y, "-", size=8)
                        self._draw_centered_text(c, 127, y, "-", size=8)
                        self._draw_right_text(c, 170, y, "-", size=8)
                        self._draw_right_text(c, 205, y, "-", size=8)

                # --- BAS DE PAGE 2 ---
                date_str = datetime.now().strftime("%d/%m/%Y")
                
                # "Fait à Alger, le ..."
                self._draw_text(c, 30, 35, f"Fait à {company.ville or 'Alger'}, le {date_str}", size=10)

                # Nom du signataire
                self._draw_text(c, 30, 45, f"{company.nom_directeur or ''}", size=10)
                self._draw_text(c, 30, 50, f"{company.fonction_directeur or ''}", size=9)

                # --- SIGNATURE IMAGE ---
                if os.path.exists(self.SIGNATURE_PATH):
                    signature = ImageReader(self.SIGNATURE_PATH)
                    c.drawImage(signature,
                                110 * mm,
                                (297 - 50) * mm,
                                width=40 * mm,
                                height=15 * mm,
                                mask='auto')

                # --- CACHET IMAGE ---
                if os.path.exists(self.STAMP_PATH):
                    stamp = ImageReader(self.STAMP_PATH)
                    c.drawImage(stamp,
                                60 * mm,
                                (297 - 45) * mm,
                                width=35 * mm,
                                height=35 * mm,
                                mask='auto')

                c.save()

                packet.seek(0)

                # ==========================================
                # FUSION AVEC LE PDF OFFICIEL
                # ==========================================

                template_pdf = PdfReader(self.TEMPLATE_PATH)
                overlay_pdf = PdfReader(packet)
                writer = PdfWriter()

                # S'assurer que le template a au moins 2 pages
                for page_num in range(min(2, len(template_pdf.pages))):
                    page = template_pdf.pages[page_num]
                    if page_num < len(overlay_pdf.pages):
                        page.merge_page(overlay_pdf.pages[page_num])
                    writer.add_page(page)

                with open(output_path, "wb") as f:
                    writer.write(f)

                return output_path

        except Exception as e:
            print(f"❌ Erreur lors de la génération: {e}")
            import traceback
            traceback.print_exc()
            raise


# ======================================================
# FONCTION D'UTILISATION SIMPLE
# ======================================================

def generate_attestation_cnas(employee_id, output_path=None):
    """
    Fonction simple pour générer l'attestation CNAS
    
    Args:
        employee_id: ID de l'employé
        output_path: Chemin de sortie (optionnel)
    
    Returns:
        Chemin du fichier généré
    """
    if not output_path:
        output_path = f"attestation_cnas_{employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    generator = AttestationCNASPDFGenerator()
    return generator.generate(employee_id, output_path)


# ======================================================
# TEST
# ======================================================

if __name__ == "__main__":
    # Test avec un ID d'employé
    try:
        output = generate_attestation_cnas(1, "test_attestation.pdf")
        print(f"✅ Attestation générée: {output}")
    except Exception as e:
        print(f"❌ Erreur: {e}")