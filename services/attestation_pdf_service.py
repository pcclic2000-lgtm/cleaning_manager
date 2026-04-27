import logging

logger = logging.getLogger(__name__)

"""
Service de génération d'attestations PDF
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

# Pillow est optionnel — requis uniquement pour dessiner les logos dans les PDF
try:
    from PIL import Image as _PILImage  # noqa: F401  (import suffisant pour activer le support)
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from database.db import SessionLocal, get_session
from models.company import CompanyInfo


class AttestationPDFService:
    """Service de génération d'attestations PDF professionnelles"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.company_info = self._load_company_info()
        self._setup_styles()
    
    def _setup_styles(self):
        """Configure les styles personnalisés"""
        self.title_style = ParagraphStyle(
            'AttestationTitle',
            parent=self.styles['Title'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        self.header_style = ParagraphStyle(
            'AttestationHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.white,
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        self.normal_style = ParagraphStyle(
            'AttestationNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        )
        
        self.footer_style = ParagraphStyle(
            'AttestationFooter',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
    
    def _load_company_info(self) -> Dict[str, Any]:
        """Charge les informations de l'entreprise"""
        with get_session() as session:
            company = session.query(CompanyInfo).first()
            if company:
                return {
                    'name': company.nom,
                    'address': company.adresse,
                    'city': company.ville or "",
                    'phone': company.telephone or "",
                    'email': company.email or "",
                    'employer_number': company.numero_employeur or "",
                    'tax_id': company.numero_employeur or "",
                    'logo_path': company.logo_path
                }
        
            # Valeurs par défaut
            return {
            'name': 'ENTREPRISE NET',
            'address': '22 Lotissement Deux Piliers',
            'city': 'Bouzareah, Alger',
            'phone': '023 00 00 00',
            'email': 'contact@entreprise.dz',
            'employer_number': '199145',
            'tax_id': '199145',
            'logo_path': None
            }
    
    def _format_date(self, date_input) -> str:
        """Formate une date au format dd/mm/yyyy"""
        
        # Si c'est déjà une chaîne au bon format, la retourner
        if isinstance(date_input, str):
            # Vérifier si c'est déjà au format dd/mm/yyyy
            import re
            date_pattern = r'^\d{2}/\d{2}/\d{4}$'
            if re.match(date_pattern, date_input):
                return date_input
            # Sinon essayer de parser
            try:
                from dateutil import parser
                date_obj = parser.parse(date_input)
                return f"{date_obj.day:02d}/{date_obj.month:02d}/{date_obj.year}"
            except:
                return date_input
        
        # Si c'est un objet datetime
        elif isinstance(date_input, datetime):
            return f"{date_input.day:02d}/{date_input.month:02d}/{date_input.year}"
        
        # Si c'est une date (sans heure)
        elif hasattr(date_input, 'year') and hasattr(date_input, 'month') and hasattr(date_input, 'day'):
            return f"{date_input.day:02d}/{date_input.month:02d}/{date_input.year}"
        
        # Sinon retourner la représentation en chaîne
        return str(date_input)
    
    def generate_attestation(self, employee_data: Dict[str, Any], 
                            attestation_type: str = "Attestation de travail",
                            output_path: Optional[str] = None) -> str:
        """
        Génère une attestation PDF
        
        Args:
            employee_data: Données de l'employé
            attestation_type: Type d'attestation
            output_path: Chemin de sortie (optionnel)
        
        Returns:
            Chemin du fichier généré
        """
        if not output_path:
            # Générer un nom de fichier automatique
            emp_name = f"{employee_data.get('last_name', '')}_{employee_data.get('first_name', '')}"
            emp_name = emp_name.replace(' ', '_') if emp_name.strip() else 'employe'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Attestation_{emp_name}_{timestamp}.pdf"
            output_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
        
        try:
            # Créer le canvas PDF
            c = canvas.Canvas(output_path, pagesize=A4)
            width, height = A4

            # ================== EN-TÊTE AVEC BANDEAU ==================
            c.setFillColor(colors.HexColor("#e3eaf0"))
            c.rect(0, height-3*cm, width, 3*cm, fill=True, stroke=False)
            
            # Logo entreprise
            try:
                if self.company_info.get('logo_path') and os.path.exists(self.company_info['logo_path']):
                    c.setFillColor(colors.white)
                    c.rect(2*cm, height-3*cm, 3*cm, 2*cm, fill=True, stroke=False)
                    if HAS_PIL:
                        c.drawImage(self.company_info['logo_path'], 2*cm, height-3*cm,
                                    width=3*cm, height=2*cm, mask='auto')
                    else:
                        logger.warning("PIL non disponible — logo ignoré dans l'attestation")
            except:
                pass

            # Nom entreprise
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(5*cm, height-2*cm, self.company_info['name'])
            
            c.setFont("Helvetica", 10)
            address_line = f"{self.company_info['address']}"
            if self.company_info['city']:
                address_line += f", {self.company_info['city']}"
            c.drawString(5*cm, height-2.6*cm, address_line)

            # ================== INFORMATIONS DOCUMENT ==================
            ref_num = f"REF/{datetime.now().strftime('%Y%m%d')}/{employee_data.get('id', '0000'):04d}"
            c.setFont("Helvetica", 9)
            c.drawRightString(width-2*cm, height-1.5*cm, ref_num)

            # ================== TITRE ==================
            c.setFillColor(colors.HexColor("#3498db"))
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(width/2, height-5*cm, attestation_type.upper())

            # Date
            date_actuelle = datetime.now().strftime("%d/%m/%Y")
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 11)
            c.drawRightString(width-2*cm, height-5.7*cm, f"Alger, le {date_actuelle}")

            # ================== CORPS DU DOCUMENT ==================
            y_position = height - 7*cm

            # Tableau des informations
            table_data = [
                ["INFORMATIONS DU SALARIÉ"],
                ["Nom et prénom:", f"{employee_data.get('last_name', '')} {employee_data.get('first_name', '')}"],
                ["Fonction:", employee_data.get('position', 'Non spécifié')],
                ["Date d'embauche:", self._format_date(employee_data.get('hire_date'))],
                ["Date de naissance:", self._format_date(employee_data.get('birth_date'))],
                ["N° Sécurité Sociale:", employee_data.get('social_number', 'Non renseigné')]
            ]

            # Créer le tableau
            table = Table(table_data, colWidths=[5*cm, 10*cm])
            table.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('GRID', (0, 1), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            # Dessiner le tableau
            table.wrapOn(c, width, height)
            table.drawOn(c, 1.5*cm, y_position-4*cm)
            y_position -= 5*cm

            # Texte de l'attestation
            c.setFont("Helvetica", 12)
            
            if attestation_type == "Attestation de travail":
                texte_attestation = [
                    "À qui de droit,",
                    "",
                    f"Nous soussignés, {self.company_info['name']}, attestons que Monsieur/Madame {employee_data.get('last_name', '')} {employee_data.get('first_name', '')},",
                    f"né(e) le {self._format_date(employee_data.get('birth_date'))}, est employé(e) dans notre entreprise",
                    f"en qualité de {employee_data.get('position', '')} depuis le {self._format_date(employee_data.get('hire_date'))}.",
                    "",
                    "La présente attestation est délivrée à l'intéressé(e) pour servir et valoir ce que de droit,",
                    "notamment pour faciliter ses démarches administratives.",
                    "",
                    "Nous restons à votre disposition pour toute information complémentaire."
                ]
            elif attestation_type == "Attestation de salaire":
                texte_attestation = [
                    "À qui de droit,",
                    "",
                    f"Nous soussignés, {self.company_info['name']}, certifions que Monsieur/Madame {employee_data.get('last_name', '')} {employee_data.get('first_name', '')},",
                    f"titulaire du poste de {employee_data.get('position', '')}, perçoit les émoluments suivants:",
                    "",
                    f"• Salaire mensuel brut: {employee_data.get('salary', 0):,.2f} DA",
                    f"• Date d'effet: {self._format_date(employee_data.get('hire_date'))}",
                    "",
                    "Cette attestation est délivrée à titre indicatif pour justifier des revenus,",
                    "notamment dans le cadre de demandes de prêts ou autres démarches administratives."
                ]
            else:  # Attestation de présence
                texte_attestation = [
                    "À qui de droit,",
                    "",
                    f"Nous soussignés, {self.company_info['name']}, attestons que Monsieur/Madame {employee_data.get('last_name', '')} {employee_data.get('first_name', '')},",
                    f"occupant le poste de {employee_data.get('position', '')}, exerce ses fonctions avec régularité et assiduité.",
                    "",
                    f"Employé(e) depuis le {self._format_date(employee_data.get('hire_date'))},",
                    "l'intéressé(e) fait preuve d'une ponctualité et d'une présence exemplaires à son poste de travail.",
                    "",
                    "La présente attestation est délivrée pour certifier de sa présence effective dans notre établissement."
                ]

            for ligne in texte_attestation:
                if y_position < 8*cm:  # Nouvelle page si nécessaire
                    c.showPage()
                    y_position = height - 3*cm
                    c.setFont("Helvetica", 12)
                c.drawString(2.5*cm, y_position, ligne)
                y_position -= 0.75*cm

            # ================== SIGNATURES ==================
            y_position = 6*cm
            
            # Ligne de séparation
            c.setStrokeColor(colors.gray)
            c.line(2*cm, y_position, width-2*cm, y_position)
            y_position -= 0.5*cm

            c.setFont("Helvetica-Bold", 11)
            c.drawString(3*cm, y_position, "Pour l'employeur")
            c.drawString(width-6*cm, y_position, "Pour le salarié")
            y_position -= 1*cm

            c.setFont("Helvetica", 10)
            c.drawString(3*cm, y_position, "___________________")
            c.drawString(width-6*cm, y_position, "___________________")
            y_position -= 0.5*cm

            c.drawString(3*cm, y_position, self.company_info['name'])
            c.drawString(width-6*cm, y_position, f"{employee_data.get('last_name', '')} {employee_data.get('first_name', '')}")
            y_position -= 0.3*cm

            c.setFont("Helvetica", 8)
            c.drawString(3*cm, y_position, "Directeur/Responsable")
            c.drawString(width-6*cm, y_position, "Salarié")

            # ================== PIED DE PAGE ==================
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.gray)
            pied_page = [
                f"Document généré électroniquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
                f"{self.company_info['name']} - {self.company_info['address']} - Tél: {self.company_info['phone']}",
                "Ce document est établi sur demande et ne peut être utilisé que pour les démarches officielles"
            ]
            
            for i, ligne in enumerate(pied_page):
                c.drawCentredString(width/2, 1*cm - i*0.3*cm, ligne)

            c.save()
            return output_path

        except Exception as e:
            raise Exception(f"Erreur lors de la génération de l'attestation: {str(e)}")
