"""
Service de génération de certificats de travail PDF
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

try:
    from PIL import Image as _PILImage  # noqa: F401
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from database.db import SessionLocal, get_session
from models.company import CompanyInfo
from models.employee import Employee


class CertificatTravailPDFService:
    """Service de génération de certificats de travail PDF professionnels"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.company_info = self._load_company_info()
        self._setup_styles()
        self._setup_fonts()
    
    def _setup_fonts(self):
        """Configure les polices de caractères"""
        try:
            # Essayer de charger des polices Unicode
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                'C:/Windows/Fonts/times.ttf',
                '/System/Library/Fonts/Times New Roman.ttf'
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Times-Roman', font_path))
                    break
        except:
            pass
    
    def _setup_styles(self):
        """Configure les styles personnalisés"""
        self.title_style = ParagraphStyle(
            'CertificatTitle',
            parent=self.styles['Title'],
            fontSize=20,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Times-Bold'
        )
        
        self.header_style = ParagraphStyle(
            'CertificatHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Times-Bold'
        )
        
        self.normal_style = ParagraphStyle(
            'CertificatNormal',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            alignment=TA_JUSTIFY,
            fontName='Times-Roman',
            leading=16
        )
        
        self.signature_style = ParagraphStyle(
            'CertificatSignature',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Times-Roman'
        )
        
        self.footer_style = ParagraphStyle(
            'CertificatFooter',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.gray,
            alignment=TA_CENTER,
            fontName='Times-Roman'
        )
    
    def _load_company_info(self) -> Dict[str, Any]:
        """Charge les informations de l'entreprise"""
        try:
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
                        'logo_path': company.logo_path,
                        'director_name': getattr(company, 'directeur', 'Le Directeur'),
                        'director_position': getattr(company, 'poste_directeur', 'Gérant'),
                        'director_gender': getattr(company, 'genre_directeur', 'M'),
                        'organisme_collecteur': getattr(company, 'organisme_collecteur', 'Organisme collecteur paritaire agréé')
                    }
        except Exception as e:
            print(f"Erreur chargement entreprise: {e}")
        
        # Valeurs par défaut
        return {
            'name': 'ENTREPRISE NET',
            'address': '22 Lotissement Deux Piliers',
            'city': 'Bouzareah, Alger',
            'phone': '023 00 00 00',
            'email': 'contact@entreprise.dz',
            'employer_number': '199145',
            'tax_id': '199145',
            'logo_path': None,
            'director_name': 'Le Directeur',
            'director_position': 'Gérant',
            'director_gender': 'M',
            'organisme_collecteur': 'Organisme collecteur paritaire agréé'
        }
    
    def _load_employee_details(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """Charge les détails complets de l'employé depuis la base de données"""
        try:
            with get_session() as session:
                employee = session.query(Employee).filter(Employee.id == employee_id).first()
                if not employee:
                    print(f"❌ Employé {employee_id} non trouvé")
                    return None
                
                print(f"✅ Employé chargé: {employee.nom} {employee.prenom}")
                
                # Déterminer la civilité
                civility = 'M.'  # Par défaut
                genre = 'M'      # Par défaut
                
                # Vérifier si l'attribut genre existe
                if hasattr(employee, 'genre') and employee.genre:
                    genre = employee.genre
                    civility = 'Mme' if genre == 'F' else 'M.'
                else:
                    # Déterminer par le prénom (heuristique)
                    if employee.prenom:
                        prenom_lower = employee.prenom.lower()
                        # Liste des terminaisons féminines courantes
                        if (prenom_lower.endswith('e') and not prenom_lower.endswith('é')) or \
                           prenom_lower.endswith('a') or \
                           prenom_lower in ['marie', 'anne', 'julie', 'sophie', 'nadia', 'fatima', 'karima']:
                            civility = 'Mme'
                            genre = 'F'
                
                print(f"   Civilité déterminée: {civility}")
                
                return {
                    'id': employee.id,
                    'last_name': employee.nom,
                    'first_name': employee.prenom,
                    'full_name': f"{employee.prenom} {employee.nom}".strip(),
                    'position': employee.poste or "Agent de nettoyage",
                    'hire_date': employee.date_embauche,
                    'end_date': employee.date_arret,
                    'reason_end': employee.raison_arret,
                    'birth_date': employee.date_naissance,
                    'address': employee.adresse or "Non renseignée",
                    'social_number': employee.numero_secu or "Non renseigné",
                    'salary': float(employee.salaire) if employee.salaire else 0.0,
                    'is_active': employee.est_actif,
                    'civility': civility,
                    'genre': genre
                }
        except Exception as e:
            print(f"❌ Erreur chargement employé {employee_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _format_date(self, date_value):
        """
        Formate une date au format dd/mm/yyyy
        
        Args:
            date_value: Date au format string, datetime, ou None
        
        Returns:
            Date formatée en dd/mm/yyyy ou 'Non spécifiée' si None
        """
        if not date_value:
            return 'Non spécifiée'
        
        try:
            # Si c'est déjà une datetime
            if isinstance(date_value, datetime):
                return date_value.strftime('%d/%m/%Y')
            
            # Si c'est une string, essayer différents formats
            if isinstance(date_value, str):
                # Essayer de parser la date
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y%m%d']:
                    try:
                        dt = datetime.strptime(date_value, fmt)
                        return dt.strftime('%d/%m/%Y')
                    except ValueError:
                        continue
            
            # Si c'est un date
            if hasattr(date_value, 'strftime'):
                return date_value.strftime('%d/%m/%Y')
            
            return str(date_value)
        except:
            return str(date_value)
    
    def _format_currency(self, amount) -> str:
        """Formate un montant en devise"""
        try:
            if isinstance(amount, (int, float)):
                # Format pour euros : 1 200,50 €
                return f"{amount:,.2f} €".replace(',', ' ').replace('.', ',')
            return str(amount)
        except:
            return str(amount)
    
    def _get_duration_text(self, hire_date, end_date=None) -> str:
        """Calcule et formate la durée d'emploi entre date d'embauche et date d'arrêt"""
        if not hire_date:
            return "N/A"
        
        try:
            if isinstance(hire_date, str):
                from datetime import datetime as dt
                hire_date = dt.strptime(hire_date, '%Y-%m-%d')
            
            if not end_date:
                end_date = datetime.now()
            elif isinstance(end_date, str):
                from datetime import datetime as dt
                end_date = dt.strptime(end_date, '%Y-%m-%d')
            
            delta = end_date - hire_date
            years = delta.days // 365
            months = (delta.days % 365) // 30
            days = (delta.days % 365) % 30
            
            parts = []
            if years > 0:
                parts.append(f"{years} an{'s' if years > 1 else ''}")
            if months > 0:
                parts.append(f"{months} mois")
            if days > 0 and years == 0:
                parts.append(f"{days} jour{'s' if days > 1 else ''}")
            
            return ", ".join(parts) if parts else "moins d'un mois"
        except:
            return "N/A"
    
    def _wrap_text(self, text: str, max_width: float, canvas) -> List[str]:
        """
        Divise un texte en plusieurs lignes pour qu'il tienne dans la largeur spécifiée
        """
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            # Tester si le mot ajouté dépasse la largeur
            test_line = ' '.join(current_line + [word])
            test_width = canvas.stringWidth(test_line, "Times-Roman", 12)
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        # Ajouter la dernière ligne
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def generate_certificat_travail(self, employee_id: int, 
                              certificat_type: str = "Certificat de travail",
                              output_path: Optional[str] = None) -> str:
        """
        Génère un certificat de travail PDF pour un employé inactif UNIQUEMENT
        Utilise la date d'embauche et la date d'arrêt
        Format conforme au texte légal fourni
        
        Args:
            employee_id: ID de l'employé dans la base de données
            certificat_type: Type de certificat
            output_path: Chemin de sortie (optionnel)
        
        Returns:
            Chemin du fichier généré
        
        Raises:
            ValueError: Si l'employé est actif ou n'a pas de date d'arrêt
        """
        # Charger les données de l'employé depuis la DB
        employee_data = self._load_employee_details(employee_id)
        if not employee_data:
            raise ValueError(f"Employé avec ID {employee_id} non trouvé")
        
        # 🔴 INTERDIRE LA GÉNÉRATION POUR EMPLOYÉ ACTIF
        if employee_data['is_active']:
            raise ValueError(
                f"IMPOSSIBLE DE GÉNÉRER UN CERTIFICAT\n\n"
                f"L'employé {employee_data['full_name']} est actuellement ACTIF.\n\n"
                f"Un certificat de travail ne peut être délivré qu'à un employé qui a quitté l'entreprise.\n"
                f"Veuillez d'abord désactiver l'employé via 'Modifier' > 'Statut Inactif' avec sa date d'arrêt."
            )
        
        # 🔴 VÉRIFIER LA PRÉSENCE D'UNE DATE D'ARRÊT
        if not employee_data['end_date']:
            raise ValueError(
                f"IMPOSSIBLE DE GÉNÉRER UN CERTIFICAT\n\n"
                f"L'employé {employee_data['full_name']} est inactif mais n'a PAS de date d'arrêt.\n\n"
                f"Veuillez modifier l'employé et renseigner sa date d'arrêt."
            )
        
        # Générer le nom de fichier
        if not output_path:
            emp_name = f"{employee_data.get('last_name', '')}_{employee_data.get('first_name', '')}"
            emp_name = emp_name.replace(' ', '_') if emp_name.strip() else 'employe'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Ajouter la période dans le nom du fichier (avec format dd-mm-yyyy pour le nom de fichier)
            hire_date_str = self._format_date(employee_data['hire_date']).replace('/', '-') if employee_data['hire_date'] else 'inconnue'
            end_date_str = self._format_date(employee_data['end_date']).replace('/', '-') if employee_data['end_date'] else 'inconnue'
            
            filename = f"Certificat_Travail_{emp_name}_{hire_date_str}_{end_date_str}_{timestamp}.pdf"
            
            # S'assurer que le dossier Desktop existe
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.expanduser("~")  # Fallback vers le dossier personnel
            output_path = os.path.join(desktop, filename)
        
        try:
            # Créer le canvas PDF
            c = canvas.Canvas(output_path, pagesize=A4)
            width, height = A4

            # ================== EN-TÊTE PROFESSIONNEL ==================
            # Fond pour le header
            c.setFillColor(colors.HexColor("#f8f9fa"))
            c.rect(0, height-4*cm, width, 4*cm, fill=True, stroke=False)
            
            # ============ GESTION DU LOGO ============
            try:
                logo_path = None
                # Essayer différents chemins possibles
                if self.company_info.get('logo_path'):
                    if os.path.exists(self.company_info['logo_path']):
                        logo_path = self.company_info['logo_path']
                    else:
                        # Essayer avec le chemin absolu depuis la racine du projet
                        import sys
                        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        alt_path = os.path.join(base_dir, self.company_info['logo_path'].lstrip('/\\'))
                        if os.path.exists(alt_path):
                            logo_path = alt_path
                
                if logo_path and HAS_PIL:
                    logo_size = 2.5*cm
                    logo_x = 2*cm
                    logo_y = height - 3.5*cm
                    
                    # Fond circulaire pour le logo
                    c.setFillColor(colors.white)
                    c.circle(logo_x + logo_size/2, logo_y + logo_size/2, logo_size/2 + 0.1*cm, fill=True, stroke=True)
                    
                    # Logo
                    c.drawImage(logo_path, 
                              logo_x, logo_y, 
                              width=logo_size, height=logo_size, 
                              mask='auto', preserveAspectRatio=True)
            except Exception as e:
                # Silently fail - pas de logo, on continue
                pass
            # ============ FIN GESTION LOGO ============

            # Informations entreprise (avec valeurs par défaut)
            company_name = self.company_info.get('name', self.company_info.get('nom', 'ENTREPRISE'))
            company_address = self.company_info.get('address', self.company_info.get('adresse', ''))
            company_city = self.company_info.get('city', self.company_info.get('ville', ''))
            company_phone = self.company_info.get('phone', self.company_info.get('telephone', ''))
            company_email = self.company_info.get('email', '')
            
            c.setFont("Times-Bold", 16)
            c.setFillColor(colors.HexColor("#2c3e50"))
            c.drawCentredString(width/2, height-2*cm, company_name.upper())
            
            c.setFont("Times-Roman", 11)
            c.setFillColor(colors.HexColor("#7f8c8d"))
            address_line = f"{company_address}"
            if company_city:
                address_line += f", {company_city}"
            c.drawCentredString(width/2, height-2.7*cm, address_line)
            
            contact_parts = []
            if company_phone:
                contact_parts.append(f"Tél: {company_phone}")
            if company_email:
                contact_parts.append(f"Email: {company_email}")
            contact_line = " | ".join(contact_parts) if contact_parts else ""
            if contact_line:
                c.drawCentredString(width/2, height-3.2*cm, contact_line)

            # Ligne de séparation décorative
            c.setStrokeColor(colors.HexColor("#3498db"))
            c.setLineWidth(2)
            c.line(2*cm, height-3.8*cm, width-2*cm, height-3.8*cm)

            # ================== NUMÉRO DE RÉFÉRENCE ==================
            ref_num = f"CERT/{datetime.now().strftime('%Y%m%d')}/{employee_data.get('id', '0000'):04d}"
            c.setFont("Times-Roman", 9)
            c.setFillColor(colors.gray)
            c.drawRightString(width-2*cm, height-4.5*cm, f"Réf: {ref_num}")

            # ================== TITRE DU CERTIFICAT ==================
            y_position = height - 6*cm
            
            c.setFont("Times-Bold", 22)
            c.setFillColor(colors.HexColor("#2c3e50"))
            c.drawCentredString(width/2, y_position, "CERTIFICAT DE TRAVAIL")
            y_position -= 1.5*cm

            # ================== CORPS DU CERTIFICAT ==================
            c.setFont("Times-Roman", 12)
            
            # Déterminer la civilité
            civility = employee_data.get('civility', 'M.')
            if civility not in ['M.', 'Mme', 'Mlle']:
                civility = 'M.' if employee_data.get('genre', 'M') == 'M' else 'Mme'
            
            # ============ INFORMATIONS DU GÉRANT ============
            # Récupérer le nom et la fonction du gérant/directeur depuis la base de données
            try:
                with get_session() as db_session:
                    from models.company import CompanyInfo
                    company_db = db_session.query(CompanyInfo).first()
                    
                    if company_db:
                        # Essayer tous les noms de champs possibles
                        gerant_nom = company_db.nom_directeur or company_db.director_name or ''
                        gerant_fonction = company_db.fonction_directeur or company_db.director_position or ''
                    else:
                        gerant_nom = ''
                        gerant_fonction = ''
            except Exception as e:
                print(f"Erreur lors du chargement du gérant: {e}")
                gerant_nom = ''
                gerant_fonction = ''
            
            # Si toujours vide, essayer depuis self.company_info
            if not gerant_nom:
                gerant_nom = self.company_info.get('director_name', self.company_info.get('nom_directeur', ''))
            if not gerant_fonction:
                gerant_fonction = self.company_info.get('director_position', self.company_info.get('fonction_directeur', ''))
            
            # Valeurs par défaut en dernier recours
            if not gerant_nom:
                gerant_nom = "Le Gérant"
            if not gerant_fonction:
                gerant_fonction = "Gérant"
            
            # Déterminer le genre du gérant pour l'accord
            signataire_genre = self.company_info.get('director_gender', 'M')
            signataire_accord = "e" if signataire_genre == 'F' else ""
            # ============ FIN INFORMATIONS GÉRANT ============
            
            # Période d'emploi (date d'entrée au date de fin de préavis)
            hire_date = employee_data.get('hire_date')
            end_date = employee_data.get('end_date')
            
            # ================== PARAGRAPHE 1 ==================
            employee_address = employee_data.get('address', employee_data.get('adresse', 'Non renseigné'))
            if not employee_address or employee_address.strip() == '':
                employee_address = 'Non renseigné'
            
            texte1 = f"Je soussigné{signataire_accord} {gerant_nom} agissant en qualité de {gerant_fonction} de la société {company_name} certifie que {civility} {employee_data.get('last_name', '').upper()} {employee_data.get('first_name', '')} demeurant {employee_address},"
            
            lines = self._wrap_text(texte1, width - 6*cm, c)
            for line in lines:
                c.drawString(3*cm, y_position, line)
                y_position -= 0.6*cm
            
            # ================== PARAGRAPHE 2 ==================
            if hire_date and end_date:
                # Format dd/mm/yyyy
                hire_date_formatted = self._format_date(hire_date)
                end_date_formatted = self._format_date(end_date)
                texte2 = f"a exercé au sein de l'entreprise du {hire_date_formatted} au {end_date_formatted}, en qualité de {employee_data.get('position', 'Non spécifié')}."
            else:
                texte2 = f"a exercé au sein de l'entreprise en qualité de {employee_data.get('position', 'Non spécifié')}."
            
            lines = self._wrap_text(texte2, width - 6*cm, c)
            for line in lines:
                c.drawString(3*cm, y_position, line)
                y_position -= 0.6*cm
            
            # ================== PARAGRAPHE 3 ==================
            y_position -= 0.2*cm
            texte3 = f"{civility} {employee_data.get('last_name', '').upper()} {employee_data.get('first_name', '')} nous quitte ce jour, libre de tout engagement."
            
            lines = self._wrap_text(texte3, width - 6*cm, c)
            for line in lines:
                c.drawString(3*cm, y_position, line)
                y_position -= 3*cm
            
            # ================== LIEU ET DATE ==================
            lieu_certificat = employee_data.get('lieu_certificat', company_city if company_city else 'Alger')
            date_formatted = datetime.now().strftime('%d/%m/%Y')

            texte_lieu_date = f"Fait à {lieu_certificat}, le {date_formatted}"
            c.setFont("Times-Roman", 12)
            c.drawRightString(width - 3*cm, y_position, texte_lieu_date)
            y_position -= 1.5*cm
            
            # ================== SIGNATURE ==================
            c.setFont("Times-Bold", 12)
            texte_signature = "Signature de l’employeur :"
            c.drawString(3*cm, y_position, texte_signature)
            y_position -= 0.5*cm
            
            # Ligne pour signature
            c.setStrokeColor(colors.black)
            c.setLineWidth(1)
            c.line(3*cm, y_position, 8*cm, y_position)
            y_position -= 0.8*cm
            
            # Nom et fonction du gérant (avec les vraies valeurs)
            c.setFont("Times-Bold", 11)
            c.drawString(3*cm, y_position, gerant_nom)
            y_position -= 0.4*cm
            c.setFont("Times-Roman", 10)
            c.drawString(3*cm, y_position, gerant_fonction)
            y_position -= 0.4*cm
            c.drawString(3*cm, y_position, company_name)
            
            # Cachet de l'entreprise
            y_position -= 1.5*cm
            c.setFont("Times-Roman", 9)
            c.setFillColor(colors.HexColor("#7f8c8d"))
            c.drawString(3*cm, y_position, f"Cachet de {company_name}")
            
            # ================== PIED DE PAGE ==================
            c.setFont("Times-Roman", 8)
            c.setFillColor(colors.gray)

            pied_page = [
                "━" * 80,
                f"Document généré électroniquement le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}",
            ]

            # Ajouter les infos entreprise si disponibles
            company_line = f"{company_name}"
            if company_address:
                company_line += f" • {company_address}"
            if company_city:
                company_line += f" • {company_city}"
            pied_page.append(company_line)

            contact_line_pied = []
            if company_phone:
                contact_line_pied.append(f"Tél: {company_phone}")
            if company_email:
                contact_line_pied.append(f"Email: {company_email}")
            if contact_line_pied:
                pied_page.append(" • ".join(contact_line_pied))

            # Ajouter le numéro employeur s'il existe
            employer_number = self.company_info.get('employer_number', self.company_info.get('numero_employeur', ''))
            if employer_number:
                pied_page.append(f"N° employeur: {employer_number}")

            pied_page.append("Ce document est officiel et ne peut être utilisé qu'à des fins légales")

            # Pied de page
            y_pied = 3.5*cm
            for i, ligne in enumerate(pied_page):
                if ligne:
                    c.drawCentredString(width/2, y_pied - i*0.3*cm, ligne)

            c.save()
            
            # Vérifier que le fichier a bien été créé
            if os.path.exists(output_path):
                return output_path
            else:
                raise Exception("Le fichier PDF n'a pas pu être créé")

        except Exception as e:
            raise Exception(f"Erreur lors de la génération du certificat: {str(e)}")