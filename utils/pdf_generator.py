# utils/pdf_generator.py
import os
from datetime import datetime
from jinja2 import Template
import pdfkit
from database.db import SessionLocal
from models.employee import Employee


# Configuration pour wkhtmltopdf
WKHTMLTOPDF_PATH = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH) if os.path.exists(WKHTMLTOPDF_PATH) else None

def generate_payslip_html(fiche_paie, employee, entreprise_info=None):
    """Génère le HTML de la fiche de paie avec entête personnalisé"""
    
    # Informations de l'entreprise (à personnaliser)
    entreprise_default = {
        "nom": "VOTRE ENTREPRISE DE NETTOYAGE",
        "adresse": "123 Rue Principale, Alger",
        "telephone": "+213 (0) 21 00 00 00",
        "email": "contact@entreprise.dz",
        "site_web": "www.entreprise.dz",
        "numero_fiscal": "123456789",
        "numero_ss": "CNAS-ALG-001",
        "logo_path": "assets/logo.png"  # Chemin vers votre logo
    }
    
    if entreprise_info:
        entreprise_default.update(entreprise_info)
    
    # Informations de l'employé
    employee_info = {
        "nom_complet": employee.nom_complet,
        "matricule": employee.code_employe,
        "adresse": employee.adresse or "Non renseignée",
        "telephone": employee.telephone,
        "date_embauche": employee.date_embauche.strftime("%d/%m/%Y"),
        "fonction": "Agent de nettoyage",  # À récupérer de votre base
    }
    
    # Calculer les taux pour l'affichage
    taux_cnass_salarial = 9.0
    taux_casnos_salarial = 1.0
    taux_assurance_chomage_salarial = 0.5
    
    taux_cnass_patronal = 26.0
    taux_casnos_patronal = 1.5
    taux_accident_travail = 1.0
    taux_assurance_chomage_patronal = 1.0
    
    # Formatage des dates
    periode_debut = fiche_paie.periode_debut.strftime("%d/%m/%Y")
    periode_fin = fiche_paie.periode_fin.strftime("%d/%m/%Y")
    date_emission = fiche_paie.date_emission.strftime("%d/%m/%Y")
    
    # Template HTML
    html_template = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fiche de Paie - {{ entreprise.nom }}</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                color: #333;
                background-color: #f8f9fa;
            }
            
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                border: 1px solid #e0e0e0;
            }
            
            .header {
                text-align: center;
                border-bottom: 3px solid #2c3e50;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }
            
            .entreprise-info {
                background: linear-gradient(135deg, #2c3e50, #3498db);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
            }
            
            .entreprise-info h2 {
                margin-top: 0;
                color: white;
                font-size: 24px;
            }
            
            .title {
                text-align: center;
                color: #2c3e50;
                margin: 30px 0;
                font-size: 28px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .subtitle {
                color: #3498db;
                border-bottom: 2px solid #3498db;
                padding-bottom: 5px;
                margin-top: 30px;
                font-size: 18px;
                font-weight: bold;
            }
            
            .info-box {
                display: flex;
                justify-content: space-between;
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                border: 1px solid #e0e0e0;
            }
            
            .info-column {
                flex: 1;
                padding: 0 15px;
            }
            
            .info-column h3 {
                color: #2c3e50;
                border-left: 4px solid #3498db;
                padding-left: 10px;
                margin-top: 0;
            }
            
            .table-container {
                overflow-x: auto;
                margin-bottom: 30px;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            
            th {
                background: #2c3e50;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: bold;
            }
            
            td {
                padding: 12px;
                border-bottom: 1px solid #e0e0e0;
            }
            
            tr:hover {
                background: #f8f9fa;
            }
            
            .total-row {
                background: #e8f4fc !important;
                font-weight: bold;
            }
            
            .net-row {
                background: #d4edda !important;
                font-weight: bold;
                font-size: 16px;
            }
            
            .montant {
                text-align: right;
                font-family: 'Courier New', monospace;
            }
            
            .positive {
                color: #27ae60;
            }
            
            .negative {
                color: #e74c3c;
            }
            
            .calculations {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin-bottom: 30px;
            }
            
            .calculation-box {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
            
            .signature-box {
                margin-top: 50px;
                display: flex;
                justify-content: space-between;
                padding-top: 30px;
                border-top: 2px solid #2c3e50;
            }
            
            .signature {
                text-align: center;
                width: 45%;
            }
            
            .signature-line {
                border-top: 1px solid #333;
                width: 80%;
                margin: 40px auto 10px;
            }
            
            .footer {
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                color: #7f8c8d;
                font-size: 12px;
            }
            
            .highlight {
                background: #fff3cd;
                padding: 10px;
                border-radius: 5px;
                border-left: 4px solid #ffc107;
                margin: 10px 0;
            }
            
            .badge {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 10px;
            }
            
            .badge-success {
                background: #d4edda;
                color: #155724;
            }
            
            .badge-info {
                background: #d1ecf1;
                color: #0c5460;
            }
            
            .text-right {
                text-align: right;
            }
            
            .text-center {
                text-align: center;
            }
            
            .mb-20 {
                margin-bottom: 20px;
            }
            
            .mt-20 {
                margin-top: 20px;
            }
            
            .separator {
                height: 2px;
                background: linear-gradient(to right, #3498db, #2c3e50);
                margin: 30px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- En-tête de l'entreprise -->
            <div class="entreprise-info">
                <h2>{{ entreprise.nom }}</h2>
                <p>{{ entreprise.adresse }} | Tél: {{ entreprise.telephone }} | Email: {{ entreprise.email }}</p>
                <p>Site: {{ entreprise.site_web }} | NIF: {{ entreprise.numero_fiscal }} | N° SS: {{ entreprise.numero_ss }}</p>
            </div>
            
            <h1 class="title">📋 FICHE DE PAIE</h1>
            
            <!-- Informations de la fiche -->
            <div class="info-box">
                <div class="info-column">
                    <h3>Informations employé</h3>
                    <p><strong>Nom:</strong> {{ employee.nom_complet }}</p>
                    <p><strong>Matricule:</strong> {{ employee.matricule }}</p>
                    <p><strong>Fonction:</strong> {{ employee.fonction }}</p>
                    <p><strong>Date d'embauche:</strong> {{ employee.date_embauche }}</p>
                </div>
                
                <div class="info-column">
                    <h3>Période de paie</h3>
                    <p><strong>Période:</strong> Du {{ periode_debut }} au {{ periode_fin }}</p>
                    <p><strong>Jours travaillés:</strong> {{ fiche.jours_travailles }} jours</p>
                    <p><strong>Date d'émission:</strong> {{ date_emission }}</p>
                    <p><strong>N° fiche:</strong> {{ fiche.numero_fiche }} <span class="badge badge-success">VALIDÉE</span></p>
                </div>
            </div>
            
            <div class="separator"></div>
            
            <!-- Gains -->
            <h2 class="subtitle">💰 GAINS ET RÉMUNÉRATION</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Détail</th>
                            <th class="text-right">Montant (DA)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Salaire de base</td>
                            <td>{{ fiche.jours_travailles }} jours × {{ (fiche.salaire_base/fiche.jours_travailles)|round(2) }} DA/jour</td>
                            <td class="montant">{{ "{:,.2f}".format(fiche.salaire_base) }}</td>
                        </tr>
                        {% if fiche.heures_supp > 0 %}
                        <tr>
                            <td>Heures supplémentaires</td>
                            <td>{{ fiche.heures_supp }}h × {{ fiche.taux_horaire_supp }} DA/h</td>
                            <td class="montant positive">+ {{ "{:,.2f}".format(fiche.montant_heures_supp) }}</td>
                        </tr>
                        {% endif %}
                        {% if fiche.primes > 0 %}
                        <tr>
                            <td>Primes</td>
                            <td>Prime de rendement</td>
                            <td class="montant positive">+ {{ "{:,.2f}".format(fiche.primes) }}</td>
                        </tr>
                        {% endif %}
                        {% if fiche.indemnites > 0 %}
                        <tr>
                            <td>Indemnités</td>
                            <td>Indemnité de transport</td>
                            <td class="montant positive">+ {{ "{:,.2f}".format(fiche.indemnites) }}</td>
                        </tr>
                        {% endif %}
                        {% if fiche.autres_gains > 0 %}
                        <tr>
                            <td>Autres gains</td>
                            <td>Avantages divers</td>
                            <td class="montant positive">+ {{ "{:,.2f}".format(fiche.autres_gains) }}</td>
                        </tr>
                        {% endif %}
                        <tr class="total-row">
                            <td colspan="2"><strong>TOTAL BRUT</strong></td>
                            <td class="montant"><strong>{{ "{:,.2f}".format(fiche.salaire_brut) }}</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="calculations">
                <!-- Cotisations salariales -->
                <div class="calculation-box">
                    <h3>📉 RETENUES SALARIALES</h3>
                    <table>
                        <tr>
                            <td>CNaSS ({{ taux_cnass_salarial }}%)</td>
                            <td class="montant negative">- {{ "{:,.2f}".format(fiche.cnasp_salarial) }}</td>
                        </tr>
                        <tr>
                            <td>CASNOS ({{ taux_casnos_salarial }}%)</td>
                            <td class="montant negative">- {{ "{:,.2f}".format(fiche.casnos_salarial) }}</td>
                        </tr>
                        <tr>
                            <td>Assurance chômage ({{ taux_assurance_chomage_salarial }}%)</td>
                            <td class="montant negative">- {{ "{:,.2f}".format(fiche.assurance_chomage_salarial) }}</td>
                        </tr>
                        <tr>
                            <td>Impôt sur le revenu (IRG)</td>
                            <td class="montant negative">- {{ "{:,.2f}".format(fiche.impot_revenu) }}</td>
                        </tr>
                        <tr class="total-row">
                            <td><strong>TOTAL RETENUES</strong></td>
                            <td class="montant negative"><strong>- {{ "{:,.2f}".format(fiche.total_cotisations_salariales) }}</strong></td>
                        </tr>
                    </table>
                </div>
                
                <!-- Cotisations patronales -->
                <div class="calculation-box">
                    <h3>🏢 COTISATIONS PATRONALES</h3>
                    <table>
                        <tr>
                            <td>CNaSS patronal ({{ taux_cnass_patronal }}%)</td>
                            <td class="montant">{{ "{:,.2f}".format(fiche.cnasp_patronal) }}</td>
                        </tr>
                        <tr>
                            <td>CASNOS patronal ({{ taux_casnos_patronal }}%)</td>
                            <td class="montant">{{ "{:,.2f}".format(fiche.casnos_patronal) }}</td>
                        </tr>
                        <tr>
                            <td>Accident de travail ({{ taux_accident_travail }}%)</td>
                            <td class="montant">{{ "{:,.2f}".format(fiche.accident_travail) }}</td>
                        </tr>
                        <tr>
                            <td>Assurance chômage patronal ({{ taux_assurance_chomage_patronal }}%)</td>
                            <td class="montant">{{ "{:,.2f}".format(fiche.assurance_chomage_patronal) }}</td>
                        </tr>
                        <tr class="total-row">
                            <td><strong>TOTAL PATRONAL</strong></td>
                            <td class="montant"><strong>{{ "{:,.2f}".format(fiche.total_cotisations_patronales) }}</strong></td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <!-- Résultat final -->
            <div class="table-container">
                <table>
                    <tbody>
                        <tr class="total-row">
                            <td colspan="2"><strong>SALAIRE BRUT</strong></td>
                            <td class="montant"><strong>{{ "{:,.2f}".format(fiche.salaire_brut) }} DA</strong></td>
                        </tr>
                        <tr class="total-row">
                            <td colspan="2"><strong>TOTAL DES RETENUES</strong></td>
                            <td class="montant negative"><strong>- {{ "{:,.2f}".format(fiche.total_cotisations_salariales) }} DA</strong></td>
                        </tr>
                        <tr class="net-row">
                            <td colspan="2"><strong>NET À PAYER</strong></td>
                            <td class="montant"><strong style="color: #155724; font-size: 20px;">{{ "{:,.2f}".format(fiche.net_a_payer) }} DA</strong></td>
                        </tr>
                        <tr>
                            <td colspan="2">Coût total employeur (brut + patronal)</td>
                            <td class="montant">{{ "{:,.2f}".format(fiche.salaire_brut + fiche.total_cotisations_patronales) }} DA</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <!-- Informations légales -->
            <div class="highlight mt-20">
                <h4>ℹ️ Informations légales</h4>
                <p>Cette fiche de paie est établie conformément à la législation algérienne en vigueur :</p>
                <ul>
                    <li>Loi n° 90-11 du 21 avril 1990 relative aux relations de travail</li>
                    <li>Loi n° 83-13 du 2 juillet 1983 relative à la sécurité sociale</li>
                    <li>Code des impôts directs et taxes assimilées</li>
                </ul>
                <p><strong>Arrêté à la somme de:</strong> {{ montant_en_lettres }} dinars algériens</p>
            </div>
            
            <!-- Signatures -->
            <div class="signature-box">
                <div class="signature">
                    <p>Pour l'employeur</p>
                    <div class="signature-line"></div>
                    <p>Nom et signature</p>
                    <p>Cachet de l'entreprise</p>
                </div>
                
                <div class="signature">
                    <p>Vu et approuvé par l'employé</p>
                    <div class="signature-line"></div>
                    <p>Nom et signature</p>
                    <p>Date: ____________________</p>
                </div>
            </div>
            
            <!-- Pied de page -->
            <div class="footer">
                <p>{{ entreprise.nom }} - Fiche de paie générée le {{ date_heure_generation }}</p>
                <p>Document officiel - À conserver pendant 5 ans</p>
                <p>En cas de différence, les registres de l'entreprise font foi</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Convertir le montant en lettres (fonction simplifiée)
    def nombre_en_lettres(n):
        """Convertit un nombre en lettres (simplifié)"""
        unites = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
        dizaines = ["", "dix", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante-dix", "quatre-vingt", "quatre-vingt-dix"]
        
        if n == 0:
            return "zéro"
        
        # Pour simplifier, on retourne juste le nombre
        return str(int(n))
    
        montant_en_lettres = nombre_en_lettres(fiche_paie.net_a_payer)
        date_heure_generation = datetime.now().strftime("%d/%m/%Y à %H:%M")
    
        # Rendre le template
        template = Template(html_template)
        html_content = template.render(
        entreprise=entreprise_default,
        employee=employee_info,
        fiche=fiche_paie,
        periode_debut=periode_debut,
        periode_fin=periode_fin,
        date_emission=date_emission,
        taux_cnass_salarial=taux_cnass_salarial,
        taux_casnos_salarial=taux_casnos_salarial,
        taux_assurance_chomage_salarial=taux_assurance_chomage_salarial,
        taux_cnass_patronal=taux_cnass_patronal,
        taux_casnos_patronal=taux_casnos_patronal,
        taux_accident_travail=taux_accident_travail,
        taux_assurance_chomage_patronal=taux_assurance_chomage_patronal,
        montant_en_lettres=montant_en_lettres,
        date_heure_generation=date_heure_generation
        )
    
        return html_content

def generate_payslip_pdf(fiche_paie, employee, entreprise_info=None):
    """Génère un PDF de la fiche de paie"""
    
    # Créer le dossier exports s'il n'existe pas
    exports_dir = os.path.join(os.getcwd(), "exports", "fiches_paie")
    os.makedirs(exports_dir, exist_ok=True)
    
    # Générer le HTML
    html_content = generate_payslip_html(fiche_paie, employee, entreprise_info)
    
    # Chemin du fichier
    filename = f"fiche_paie_{employee.code_employe}_{fiche_paie.numero_fiche}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    html_path = os.path.join(exports_dir, f"{filename}.html")
    pdf_path = os.path.join(exports_dir, f"{filename}.pdf")
    
    # Sauvegarder le HTML
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Générer le PDF si wkhtmltopdf est disponible
    if config:
        try:
            options = {
                'page-size': 'A4',
                'margin-top': '15mm',
                'margin-right': '15mm',
                'margin-bottom': '15mm',
                'margin-left': '15mm',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            pdfkit.from_string(html_content, pdf_path, configuration=config, options=options)
            return pdf_path
            
        except Exception as e:
            print(f"Erreur génération PDF: {e}")
            # Retourner le chemin HTML en backup
            return html_path
    else:
        print("wkhtmltopdf non trouvé. Génération HTML uniquement.")
        return html_path
