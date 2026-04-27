import logging

logger = logging.getLogger(__name__)

"""
Service de génération de PDF professionnel
"""
import locale
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, Optional, List
import tempfile

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, Image, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF


try:
    from PIL import Image as _PILImage  # noqa: F401
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from database.db import SessionLocal, get_session
from models.company import CompanyInfo


class PayslipPDFService:
    """Service de génération de fiches de paie PDF professionnelles"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.company_info = self._load_company_info()
        self._setup_fonts()
        self._setup_locale()
        self._setup_styles()
    
    def _setup_fonts(self):
        """Configure les polices de caractères"""
        try:
            # Essayer de charger des polices Unicode (si disponibles)
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                'C:/Windows/Fonts/arial.ttf',
                '/System/Library/Fonts/Arial.ttf'
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('ArialUnicode', font_path))
                    break
        except:
            # Utiliser les polices par défaut
            pass
    
    def _setup_locale(self):
        """Configure la locale pour les formats français"""
        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'French_France.1252')
            except:
                pass  # Garder la locale par défaut
    
    def _setup_styles(self):
        """Configure les styles personnalisés"""
        # Style pour le titre principal
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        # Style pour les en-têtes
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.white,
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        # Style pour le texte normal
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )
        
        # Style pour le texte en gras
        self.bold_style = ParagraphStyle(
            'CustomBold',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        # Style pour les montants
        self.amount_style = ParagraphStyle(
            'CustomAmount',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_RIGHT,
            fontName='Helvetica-Bold'
        )
        
        # Style pour le pied de page
        self.footer_style = ParagraphStyle(
            'CustomFooter',
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
                    'tax_id': company.numero_employeur or "",  # Utiliser le même que employer_number
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
            'tax_id': '199145',  # Utiliser le même numéro
            'logo_path': None
            }
    
    def _format_currency(self, amount: Decimal) -> str:
        """Formate un montant en devise algérienne"""
        try:
            return f"{amount:,.2f} DA".replace(',', ' ').replace('.', ',')
        except:
            return f"{amount} DA"
    
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
    
    def generate_payslip(self, payslip_data: Dict[str, Any], 
                        output_path: Optional[str] = None) -> str:
        """
        Génère une fiche de paie PDF
        
        Args:
            payslip_data: Données de la fiche de paie
            output_path: Chemin de sortie (optionnel)
        
        Returns:
            Chemin du fichier généré
        """
        if not output_path:
            # Générer un nom de fichier automatique
            emp_name = payslip_data['employee'].get('name', 'unknown').replace(' ', '_')
            period = f"{payslip_data['payslip']['period_month']:02d}_{payslip_data['payslip']['period_year']}"
            filename = f"Fiche_Paie_{emp_name}_{period}.pdf"
            output_path = os.path.join(tempfile.gettempdir(), filename)
        
        # Créer le document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=2*cm,
            bottomMargin=2*cm,
            leftMargin=2*cm,
            rightMargin=2*cm,
            title=f"Fiche de paie - {payslip_data['employee']['name']}"
        )
        
        # Construire le contenu
        story = self._build_document_story(payslip_data)
        
        # Générer le PDF
        doc.build(story)
        
        return output_path
    
    def _build_document_story(self, payslip_data: Dict[str, Any]) -> List:
        """Construit le contenu du document"""
        story = []
        
        # 1. En-tête avec logo et informations entreprise
        story.extend(self._build_header())
        
        # 2. Titre du document
        story.extend(self._build_title(payslip_data))
        
        # 3. Informations employé
        story.extend(self._build_employee_info(payslip_data['employee']))
        
        # 4. Période de paie
        
        
        # 5. Détails des gains
        story.extend(self._build_single_table_section(payslip_data))
        
        # 6. Détails des déductions
        story.extend(self._build_net_salary_simple(payslip_data))
        
        # 7. Totaux et résumé
        
        
        # 8. Signatures
        story.extend(self._build_signatures_section())
        
        # 9. Pied de page
        story.extend(self._build_footer(payslip_data))
        
        return story
    
    def _build_header(self) -> List:
        """Construit l'en-tête du document avec logo à gauche et infos entreprise à droite"""
        elements = []
        
        # Créer une ligne unique avec logo à gauche et infos à droite
        header_data = []
        
        # Colonne gauche : Logo (si disponible)
        if self.company_info.get('logo_path') and os.path.exists(self.company_info['logo_path']):
            try:
                logo = Image(self.company_info['logo_path'], width=2.5*cm, height=2.5*cm)
                logo_col = logo
            except:
                logo_col = ''
        else:
            logo_col = ''
        
        # Colonne droite : Informations entreprise
        company_info_cell = [
            Paragraph(f"<b>{self.company_info['name']}</b>", self.bold_style),
            Paragraph(f"{self.company_info['address']}", self.normal_style),
            Paragraph(f"Tél: {self.company_info['phone']} | Email: {self.company_info['email']}", self.normal_style),
            Paragraph(f"N° Employeur: {self.company_info['employer_number']}", self.normal_style)
        ]
        
        # Créer une seule ligne avec logo à gauche et infos à droite
        header_data.append([logo_col, company_info_cell])
        
        # Créer le tableau avec 2 colonnes
        header_table = Table(header_data, colWidths=[4*cm, 15*cm])
        
        # Appliquer les styles
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Centrer verticalement le logo
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (0, 0), 0),  # Pas de padding à gauche pour le logo
            ('LEFTPADDING', (1, 0), (1, 0), 10),  # Un peu de padding pour les infos
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Ligne de séparation
        elements.append(self._create_separator())
        
        return elements
    
    def _build_title(self, payslip_data: Dict[str, Any]) -> List:
        """Construit le titre du document"""
        elements = []
        
        period = payslip_data['payslip'].get('period', 'PÉRIODE')
        title_text = f"<b>BULLETIN DE PAIE</b><br/>{period}"
        
        title_table = Table([[Paragraph(title_text, self.title_style)]], colWidths=[18*cm])
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#1473d1")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elements.append(title_table)
        elements.append(Spacer(1, 1*cm))
        
        return elements
    
    def _build_employee_info(self, employee_data: Dict[str, Any]) -> List:
        """Construit la section informations employé"""
        elements = []
        
        # En-tête de section
        section_header = Table([[Paragraph("<b>INFORMATIONS DU SALARIÉ</b>", self.header_style)]], 
                             colWidths=[18*cm])
        section_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(section_header)
        elements.append(Spacer(1, 0.2*cm))
        
        # Données employé
        employee_info = [
            ["Matricule", employee_data.get('matricule', 'N/A'), 
             "Nom", employee_data.get('last_name', 'N/A')],
            ["Situation familiale", employee_data.get('family_status', 'Célibataire'),
             "Prénom", employee_data.get('first_name', 'N/A')],
            ["Fonction", employee_data.get('position', 'N/A'),
             "N° Sécurité Sociale", employee_data.get('social_number', 'N/A')],
            ["Date Embauche", self._format_date(employee_data.get('hire_date')),
             "Date Naissance", self._format_date(employee_data.get('birth_date'))],
            ["Adresse", employee_data.get('address', 'N/A'),
             "Téléphone", employee_data.get('phone', 'N/A')]
        ]
        
        employee_table = Table(employee_info, colWidths=[4*cm, 5*cm, 3.5*cm, 5.5*cm])
        employee_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(employee_table)
        elements.append(Spacer(1, 1*cm))
        
        return elements
    
    def _build_single_table_section(self, payslip_data: Dict[str, Any]) -> List:
        """Construit un seul tableau avec toutes les rubriques selon le format demandé"""
        elements = []
        
        # Récupérer les données depuis payslip_data qui contient 'employee' et 'payslip'
        payslip_info = payslip_data.get('payslip', {})
        
        # Salaire de base (obligatoire)
        base_salary = Decimal(str(payslip_info.get('base_salary', '0.00')))
        
        # Prime de responsabilité
        responsibility_bonus = Decimal(str(payslip_info.get('responsibility_bonus', '0.00')))
        
        # Indemnités
        meal_allowance = Decimal(str(payslip_info.get('meal_allowance', '0.00')))
        transport_allowance = Decimal(str(payslip_info.get('transport_allowance', '0.00')))
        
        # Taux CNAS (fixe à 9%)
        cnass_rate = Decimal('0.09')
        
        # Calculer CNAS
        cnass_amount = base_salary * cnass_rate
        
        # Calculer IRG selon les tranches
        if base_salary <= Decimal('30000'):
            irg_amount = Decimal('0')
            irg_rate_display = "0%"
        elif base_salary <= Decimal('40000'):
            irg_amount = base_salary * Decimal('0.10')
            irg_rate_display = "10%"
        else:
            irg_amount = base_salary * Decimal('0.20')
            irg_rate_display = "20%"
        
        # Calculer les totaux
        total_earnings = base_salary + responsibility_bonus + meal_allowance + transport_allowance
        total_deductions = cnass_amount + irg_amount
        net_salary = total_earnings - total_deductions
        
        # Créer les données du tableau
        table_data = [
            ["Rubriques", "Base (DA)", "Taux", "Gains (DA)", "Retenues (DA)"],
            
            ["Salaire de base", 
            self._format_currency(base_salary), 
            "", 
            self._format_currency(base_salary), 
            ""],
            
            ["Prime de responsabilité", 
            self._format_currency(responsibility_bonus), 
            "", 
            self._format_currency(responsibility_bonus), 
            ""],
            
            ["Indemnité de panier", 
            self._format_currency(meal_allowance), 
            "", 
            self._format_currency(meal_allowance), 
            ""],
            
            ["Indemnité de transport", 
            self._format_currency(transport_allowance), 
            "", 
            self._format_currency(transport_allowance), 
            ""],
            
            ["Cotisation CNAS", 
            self._format_currency(base_salary), 
            f"{cnass_rate*100:.0f}%", 
            "", 
            self._format_currency(cnass_amount)],
            
            ["IRG", 
            self._format_currency(base_salary), 
            irg_rate_display, 
            "", 
            self._format_currency(irg_amount)],
            
            ["", "", "", "", ""],  # Ligne vide
            
            ["TOTAUX", 
            "", 
            "", 
            f"{self._format_currency(total_earnings)}", 
            f"{self._format_currency(total_deductions)}"]
        ]
        
        # Créer et styliser le tableau
        table = Table(table_data, colWidths=[5.5*cm, 3*cm, 2.5*cm, 3.5*cm, 3.5*cm])
        
        # Appliquer les styles
        table_style = [
            ('GRID', (0, 0), (-1, -2), 0.5, colors.black),
            ('GRID', (0, -1), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (4, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            ('BACKGROUND', (0, 7), (-1, 7), colors.white),
            ('TEXTCOLOR', (0, 7), (-1, 7), colors.white),
            
            ('BACKGROUND', (0, 8), (-1, 8), colors.HexColor("#3498db")),
            ('TEXTCOLOR', (0, 8), (-1, 8), colors.white),
            ('FONTNAME', (0, 8), (-1, 8), 'Helvetica-Bold'),
            
            ('LINEABOVE', (3, 8), (3, 8), 1, colors.black),
            ('LINEABOVE', (4, 8), (4, 8), 1, colors.black),
        ]
        
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements

    def _build_net_salary_simple(self, payslip_data: Dict[str, Any]) -> List:
        """Affiche le NET À PAYER simplement"""
        elements = []
        
        # Récupérer les données depuis payslip_data
        payslip_info = payslip_data.get('payslip', {})
        
        # Recalculer pour être sûr
        base_salary = Decimal(str(payslip_info.get('base_salary', '0.00')))
        responsibility_bonus = Decimal(str(payslip_info.get('responsibility_bonus', '0.00')))
        meal_allowance = Decimal(str(payslip_info.get('meal_allowance', '0.00')))
        transport_allowance = Decimal(str(payslip_info.get('transport_allowance', '0.00')))
        
        # CNAS fixe à 9%
        cnass_rate = Decimal('0.09')
        cnass_amount = base_salary * cnass_rate
        
        # IRG selon tranches
        if base_salary <= Decimal('30000'):
            irg_amount = Decimal('0')
        elif base_salary <= Decimal('40000'):
            irg_amount = base_salary * Decimal('0.10')
        else:
            irg_amount = base_salary * Decimal('0.20')
        
        total_earnings = base_salary + responsibility_bonus + meal_allowance + transport_allowance
        total_deductions = cnass_amount + irg_amount
        net_salary = total_earnings - total_deductions
        
        net_text = f"<b>NET À PAYER: {self._format_currency(net_salary)} </b>"
        
        # Créer un tableau centré pour le net à payer
        net_table = Table([[Paragraph(net_text, self.header_style)]], colWidths=[18*cm])
        net_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(net_table)
        elements.append(Spacer(1, 1*cm))
        
        return elements
    
    def _build_signatures_section(self) -> List:
        """Construit la section signatures"""
        elements = []
        
        signatures_data = [
            ["Signature du salarié", "Signature et cachet de l'employeur"]
        ]
        
        signatures_table = Table(signatures_data, colWidths=[9*cm, 9*cm])
        signatures_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LINEABOVE', (0, 0), (0, 0), 1, colors.black),
            ('LINEABOVE', (1, 0), (1, 0), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 40),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(signatures_table)
        elements.append(Spacer(1, 2*cm))
        
        return elements
    
    def _build_footer(self, payslip_data: Dict[str, Any]) -> List:
        """Construit le pied de page"""
        elements = []
        
        footer_text = (
            f"Document généré le {self._format_date(datetime.now())} | "
            f"Fiche de paie n°{payslip_data.get('payslip_number', 'N/A')} | "
            "Conservez ce document pour vos archives"
        )
        
        footer_table = Table([[Paragraph(footer_text, self.footer_style)]], colWidths=[18*cm])
        footer_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.gray),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(footer_table)
        
        return elements
    
    def _create_separator(self):
        """Crée une ligne de séparation"""
        return Spacer(1, 0.1*cm)
    
    def _convert_to_words(self, num: int) -> str:
        """Convertit un nombre en lettres (version simplifiée)"""
        if num == 0:
            return "Zéro"
        
        units = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
        tens = ["", "dix", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante-dix", "quatre-vingt", "quatre-vingt-dix"]
        
        if num < 10:
            return units[num].capitalize()
        elif num < 20:
            special = ["dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
            return special[num-10].capitalize()
        elif num < 100:
            if num % 10 == 0:
                return tens[num//10].capitalize()
            else:
                return f"{tens[num//10].capitalize()}-{units[num%10]}"
        else:
            # Version simplifiée pour les grands nombres
            return f"{num:,}".replace(',', ' ')
    
    def generate_batch_payslips(self, payslips_data: List[Dict[str, Any]], 
                               output_folder: str) -> List[str]:
        """
        Génère plusieurs fiches de paie en lot
        
        Args:
            payslips_data: Liste des données de fiches de paie
            output_folder: Dossier de sortie
        
        Returns:
            Liste des chemins des fichiers générés
        """
        generated_files = []
        
        for i, payslip_data in enumerate(payslips_data):
            try:
                # Générer un nom de fichier unique
                emp_name = payslip_data['employee'].get('name', f"employe_{i}").replace(' ', '_')
                filename = f"Fiche_Paie_{emp_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                output_path = os.path.join(output_folder, filename)
                
                # Générer le PDF
                file_path = self.generate_payslip(payslip_data, output_path)
                generated_files.append(file_path)
                
            except Exception as e:
                print(f"Erreur lors de la génération de la fiche {i}: {e}")
                continue
        
        return generated_files
