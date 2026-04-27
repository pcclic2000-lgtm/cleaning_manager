# utils/templates.py
"""
Templates HTML professionnels pour les documents
"""
from datetime import datetime

def get_entreprise_info():
    """Retourne les informations de l'entreprise (à personnaliser)"""
    return {
        "nom": "CLEAN MANAGER SARL",
        "adresse": "123 Avenue Didouche Mourad, Alger Centre",
        "ville": "Alger",
        "telephone": "+213 (0) 21 23 45 67",
        "fax": "+213 (0) 21 23 45 68",
        "email": "contact@cleanmanager.dz",
        "site_web": "www.cleanmanager.dz",
        "numero_fiscal": "123456789012345",
        "numero_rc": "16 B 123456",
        "numero_article": "Art. 789",
        "numero_nif": "NIF: 1234567890",
        "numero_ss": "N° SS: CNAS-01-12345-2024",
        "capital_social": "10.000.000 DA",
        "logo_url": "assets/logo_entreprise.png"  # Chemin vers votre logo
    }

def generate_fiche_paie_html(fiche_paie, employee, entreprise_info=None):
    """Génère une fiche de paie HTML professionnelle"""
    
    if entreprise_info is None:
        entreprise_info = get_entreprise_info()
    
    # Informations de l'employé
    employee_info = {
        "nom_complet": employee.nom_complet,
        "matricule": employee.code_employe,
        "adresse": employee.adresse or "Non renseignée",
        "telephone": employee.telephone,
        "date_embauche": employee.date_embauche.strftime("%d/%m/%Y"),
        "fonction": "Agent de nettoyage",
        "categorie": "Catégorie 3",
        "niveau": "Niveau 5",
        "coefficient": "250"
    }
    
    # Formater les dates avec vérification de None
    def format_date(date_obj):
        if date_obj:
            return date_obj.strftime("%d/%m/%Y")
        return "Non défini"
    
        # Formater les montants
    def format_montant(montant):
        if montant is None:
            return "0,00"
        return f"{montant:,.2f}".replace(",", " ").replace(".", ",")
    
        # Convertir le nombre en lettres
    def nombre_en_lettres(n):
        if n is None or n == 0:
            return "zéro dinars"
        
        partie_entiere = int(n)
        partie_decimale = int((n - partie_entiere) * 100)
        
        if partie_entiere == 1:
            texte = "un dinar"
        else:
            texte = f"{partie_entiere} dinars"
        
        if partie_decimale > 0:
            texte += f" et {partie_decimale} centimes"
        
        return texte
    
        # Données pour le template avec vérifications
        data = {
        # Informations entreprise
        "entreprise": entreprise_info,
        
        # Informations employé
        "employee": employee_info,
        
        # Informations fiche
        "fiche": fiche_paie,
        "numero_fiche": fiche_paie.numero_fiche or "NON-DÉFINI",
        "periode_debut": format_date(fiche_paie.periode_debut),
        "periode_fin": format_date(fiche_paie.periode_fin),
        "date_emission": format_date(fiche_paie.date_emission),
        "date_paiement": format_date(fiche_paie.date_paiement),
        
        # Montants formatés avec vérification
        "salaire_base_fmt": format_montant(getattr(fiche_paie, 'salaire_base', 0)),
        "montant_heures_supp_fmt": format_montant(getattr(fiche_paie, 'montant_heures_supp', 0)),
        "primes_fmt": format_montant(getattr(fiche_paie, 'primes', 0)),
        "indemnites_fmt": format_montant(getattr(fiche_paie, 'indemnites', 0)),
        "autres_gains_fmt": format_montant(getattr(fiche_paie, 'autres_gains', 0)),
        "salaire_brut_fmt": format_montant(getattr(fiche_paie, 'salaire_brut', 0)),
        
        # Cotisations formatées
        "cnasp_salarial_fmt": format_montant(getattr(fiche_paie, 'cnasp_salarial', 0)),
        "casnos_salarial_fmt": format_montant(getattr(fiche_paie, 'casnos_salarial', 0)),
        "assurance_chomage_salarial_fmt": format_montant(getattr(fiche_paie, 'assurance_chomage_salarial', 0)),
        "impot_revenu_fmt": format_montant(getattr(fiche_paie, 'impot_revenu', 0)),
        "total_cotisations_salariales_fmt": format_montant(getattr(fiche_paie, 'total_cotisations_salariales', 0)),
        
        "cnasp_patronal_fmt": format_montant(getattr(fiche_paie, 'cnasp_patronal', 0)),
        "casnos_patronal_fmt": format_montant(getattr(fiche_paie, 'casnos_patronal', 0)),
        "accident_travail_fmt": format_montant(getattr(fiche_paie, 'accident_travail', 0)),
        "assurance_chomage_patronal_fmt": format_montant(getattr(fiche_paie, 'assurance_chomage_patronal', 0)),
        "total_cotisations_patronales_fmt": format_montant(getattr(fiche_paie, 'total_cotisations_patronales', 0)),
        
        # Résultats formatés
        "net_a_payer_fmt": format_montant(getattr(fiche_paie, 'net_a_payer', 0)),
        "net_paye_fmt": format_montant(getattr(fiche_paie, 'net_paye', 0)),
        
        # Calcul coût employeur avec vérification
        "cout_total_employeur_fmt": format_montant(
            getattr(fiche_paie, 'salaire_brut', 0) + 
            getattr(fiche_paie, 'total_cotisations_patronales', 0)
        ),
        
        # En lettres
        "montant_en_lettres": nombre_en_lettres(getattr(fiche_paie, 'net_a_payer', 0)),
        
        # Taux (en pourcentage)
        "taux_cnasp_salarial": "9%",
        "taux_casnos_salarial": "1%",
        "taux_assurance_chomage_salarial": "0,5%",
        "taux_cnasp_patronal": "26%",
        "taux_casnos_patronal": "1,5%",
        "taux_accident_travail": "1%",
        "taux_assurance_chomage_patronal": "1%",
        
        # Date et heure de génération
        "date_generation": datetime.now().strftime("%d/%m/%Y à %H:%M"),
        "annee": datetime.now().strftime("%Y"),
        
        # Autres attributs avec vérification
        "jours_travailles": getattr(fiche_paie, 'jours_travailles', 22),
        "heures_normales": getattr(fiche_paie, 'heures_normales', 173.33),
        "heures_supp": getattr(fiche_paie, 'heures_supp', 0),
        "taux_horaire_supp": getattr(fiche_paie, 'taux_horaire_supp', 0),
        "mode_paiement": getattr(fiche_paie, 'mode_paiement', 'Non spécifié'),
        "reference_paiement": getattr(fiche_paie, 'reference_paiement', ''),
        "observations": getattr(fiche_paie, 'observations', ''),
        "statut": getattr(fiche_paie, 'statut', 'BROUILLON'),
        }
    
        # Template HTML (le même que précédemment, mais avec vérifications dans le template)
        html_template = '''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fiche de Paie - {{ entreprise.nom }}</title>
        <style>
            /* ... (tous les styles CSS précédents restent inchangés) ... */
        </style>
        </head>
        <body>
        <div class="container">
            <!-- ===== EN-TÊTE ===== -->
            <div class="header">
                <div class="header-top">
                    <div class="logo-section">
                        <div class="logo-placeholder">
                            {{ entreprise.nom.split()[0]|upper if entreprise.nom else "ENTREPRISE" }}<br>LOGO
                        </div>
                    </div>
                    
                    <div class="entreprise-info">
                        <h1 class="entreprise-nom">{{ entreprise.nom or "ENTREPRISE" }}</h1>
                        <div class="entreprise-details">
                            {{ entreprise.adresse or "" }} - {{ entreprise.ville or "" }}<br>
                            {% if entreprise.telephone %}Tél: {{ entreprise.telephone }}{% endif %}
                            {% if entreprise.fax %} - Fax: {{ entreprise.fax }}{% endif %}<br>
                            {% if entreprise.email %}Email: {{ entreprise.email }}{% endif %}
                            {% if entreprise.site_web %} - Site: {{ entreprise.site_web }}{% endif %}<br>
                            {% if entreprise.numero_fiscal %}N° Fiscal: {{ entreprise.numero_fiscal }}{% endif %}
                            {% if entreprise.numero_rc %} - N° RC: {{ entreprise.numero_rc }}{% endif %}<br>
                            {% if entreprise.numero_article %}N° Article: {{ entreprise.numero_article }}{% endif %}
                            {% if entreprise.numero_nif %} - {{ entreprise.numero_nif }}{% endif %}
                        </div>
                    </div>
                    
                    <div class="document-info">
                        <h2 class="document-title">FICHE DE PAIE</h2>
                        <p class="document-subtitle">Document officiel</p>
                        <p><strong>N°:</strong> {{ numero_fiche }}</p>
                        <p><strong>Date:</strong> {{ date_emission }}</p>
                    </div>
                </div>
            </div>
            
            <!-- ===== INFORMATIONS GÉNÉRALES ===== -->
            <div class="section">
                <div class="section-title">
                    📋 INFORMATIONS GÉNÉRALES
                </div>
                
                <div class="info-grid">
                    <div class="info-card">
                        <h4>👷 INFORMATIONS SALARIÉ</h4>
                        <div class="info-row">
                            <span class="info-label">Nom & Prénom:</span>
                            <span class="info-value">{{ employee.nom_complet }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Matricule:</span>
                            <span class="info-value">{{ employee.matricule }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Fonction:</span>
                            <span class="info-value">{{ employee.fonction }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Date embauche:</span>
                            <span class="info-value">{{ employee.date_embauche }}</span>
                        </div>
                    </div>
                    
                    <div class="info-card">
                        <h4>📅 PÉRIODE DE PAIE</h4>
                        <div class="info-row">
                            <span class="info-label">Période:</span>
                            <span class="info-value">Du {{ periode_debut }} au {{ periode_fin }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Jours travaillés:</span>
                            <span class="info-value">{{ jours_travailles }} jours</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Heures normales:</span>
                            <span class="info-value">{{ heures_normales }} heures</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Heures supplémentaires:</span>
                            <span class="info-value">{{ heures_supp }} heures</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- ===== SALAIRE BRUT ===== -->
            <div class="section">
                <div class="section-title">
                    💰 ÉLÉMENTS DE RÉMUNÉRATION
                </div>
                
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th width="60%">DÉSIGNATION</th>
                                <th width="20%" class="text-center">QUANTITÉ</th>
                                <th width="20%" class="text-right">MONTANT (DA)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Salaire de base</td>
                                <td class="text-center">{{ jours_travailles }} jours</td>
                                <td class="text-right">{{ salaire_base_fmt }}</td>
                            </tr>
                            {% if heures_supp > 0 %}
                            <tr>
                                <td>Heures supplémentaires ({{ taux_horaire_supp }} DA/h)</td>
                                <td class="text-center">{{ heures_supp }} heures</td>
                                <td class="text-right color-positive">+ {{ montant_heures_supp_fmt }}</td>
                            </tr>
                            {% endif %}
                            {% if primes_fmt != "0,00" %}
                            <tr>
                                <td>Primes diverses</td>
                                <td class="text-center">-</td>
                                <td class="text-right color-positive">+ {{ primes_fmt }}</td>
                            </tr>
                            {% endif %}
                            {% if indemnites_fmt != "0,00" %}
                            <tr>
                                <td>Indemnités (transport, panier, etc.)</td>
                                <td class="text-center">-</td>
                                <td class="text-right color-positive">+ {{ indemnites_fmt }}</td>
                            </tr>
                            {% endif %}
                            {% if autres_gains_fmt != "0,00" %}
                            <tr>
                                <td>Autres gains</td>
                                <td class="text-center">-</td>
                                <td class="text-right color-positive">+ {{ autres_gains_fmt }}</td>
                            </tr>
                            {% endif %}
                            <tr style="background: #e8f4fc; font-weight: bold;">
                                <td colspan="2"><strong>TOTAL BRUT</strong></td>
                                <td class="text-right"><strong>{{ salaire_brut_fmt }}</strong></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- ===== CALCUL DES COTISATIONS ===== -->
            <div class="calculations">
                <!-- Cotisations salariales -->
                <div class="calculation-box">
                    <h4><i class="fas fa-user-minus"></i> RETENUES SALARIALES</h4>
                    <table class="data-table">
                        <tr>
                            <td>CNaSS salarial ({{ taux_cnasp_salarial }})</td>
                            <td class="text-right color-negative">- {{ cnasp_salarial_fmt }}</td>
                        </tr>
                        <tr>
                            <td>CASNOS salarial ({{ taux_casnos_salarial }})</td>
                            <td class="text-right color-negative">- {{ casnos_salarial_fmt }}</td>
                        </tr>
                        <tr>
                            <td>Assurance chômage ({{ taux_assurance_chomage_salarial }})</td>
                            <td class="text-right color-negative">- {{ assurance_chomage_salarial_fmt }}</td>
                        </tr>
                        <tr>
                            <td>Impôt sur le revenu (IRG)</td>
                            <td class="text-right color-negative">- {{ impot_revenu_fmt }}</td>
                        </tr>
                        <tr style="background: #ffe6e6; font-weight: bold;">
                            <td><strong>TOTAL RETENUES</strong></td>
                            <td class="text-right color-negative"><strong>- {{ total_cotisations_salariales_fmt }}</strong></td>
                        </tr>
                    </table>
                </div>
                
                <!-- Cotisations patronales -->
                <div class="calculation-box">
                    <h4><i class="fas fa-building"></i> COTISATIONS PATRONALES</h4>
                    <table class="data-table">
                        <tr>
                            <td>CNaSS patronal ({{ taux_cnasp_patronal }})</td>
                            <td class="text-right">{{ cnasp_patronal_fmt }}</td>
                        </tr>
                        <tr>
                            <td>CASNOS patronal ({{ taux_casnos_patronal }})</td>
                            <td class="text-right">{{ casnos_patronal_fmt }}</td>
                        </tr>
                        <tr>
                            <td>Accident de travail ({{ taux_accident_travail }})</td>
                            <td class="text-right">{{ accident_travail_fmt }}</td>
                        </tr>
                        <tr>
                            <td>Assurance chômage patronal ({{ taux_assurance_chomage_patronal }})</td>
                            <td class="text-right">{{ assurance_chomage_patronal_fmt }}</td>
                        </tr>
                        <tr style="background: #e8f4fc; font-weight: bold;">
                            <td><strong>TOTAL PATRONAL</strong></td>
                            <td class="text-right"><strong>{{ total_cotisations_patronales_fmt }}</strong></td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <!-- ===== RÉSULTAT FINAL ===== -->
            <div class="result-final">
                <div class="result-label">NET À PAYER</div>
                <div class="result-amount">{{ net_a_payer_fmt }} DA</div>
                <div class="result-letters">Arrêté à la somme de : {{ montant_en_lettres }}</div>
            </div>
            
            <!-- ===== RÉCAPITULATIF ===== -->
            <div class="section">
                <div class="section-title">
                    📊 RÉCAPITULATIF
                </div>
                
                <div class="table-container">
                    <table class="data-table">
                        <tbody>
                            <tr>
                                <td width="70%"><strong>SALAIRE BRUT IMPOSABLE</strong></td>
                                <td width="30%" class="text-right"><strong>{{ salaire_brut_fmt }} DA</strong></td>
                            </tr>
                            <tr>
                                <td>Total des cotisations salariales</td>
                                <td class="text-right color-negative">- {{ total_cotisations_salariales_fmt }} DA</td>
                            </tr>
                            <tr style="background: #d4edda; font-weight: bold;">
                                <td><strong>NET À PAYER (Salaire net)</strong></td>
                                <td class="text-right"><strong style="color: #155724;">{{ net_a_payer_fmt }} DA</strong></td>
                            </tr>
                            <tr>
                                <td colspan="2" style="padding-top: 15px; border-top: 2px solid #dee2e6;">
                                    <strong>Coût total pour l'employeur:</strong>
                                    <span style="float: right; color: #f39c12; font-weight: bold;">
                                        {{ cout_total_employeur_fmt }} DA
                                    </span>
                                    <br>
                                    <small style="color: #7f8c8d;">
                                        (Salaire brut + Cotisations patronales)
                                    </small>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- ===== INFORMATIONS DE PAIEMENT ===== -->
            {% if mode_paiement and mode_paiement != "Non spécifié" %}
            <div class="section">
                <div class="section-title">
                    💳 INFORMATIONS DE PAIEMENT
                </div>
                
                <div class="info-card">
                    <div class="info-row">
                        <span class="info-label">Mode de paiement:</span>
                        <span class="info-value">{{ mode_paiement|upper }}</span>
                    </div>
                    {% if reference_paiement %}
                    <div class="info-row">
                        <span class="info-label">Référence:</span>
                        <span class="info-value">{{ reference_paiement }}</span>
                    </div>
                    {% endif %}
                    {% if date_paiement and date_paiement != "Non défini" %}
                    <div class="info-row">
                        <span class="info-label">Date de paiement:</span>
                        <span class="info-value">{{ date_paiement }}</span>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endif %}
            
            <!-- ===== OBSERVATIONS ===== -->
            {% if observations %}
            <div class="section">
                <div class="section-title">
                    📝 OBSERVATIONS
                </div>
                
                <div class="info-card">
                    {{ observations|replace('\n', '<br>')|safe }}
                </div>
            </div>
            {% endif %}
            
            <!-- ===== SIGNATURES ===== -->
            <div class="signatures">
                <div class="signature-box">
                    <div class="signature-label">POUR L'EMPLOYEUR</div>
                    <div class="signature-line"></div>
                    <div class="signature-note">Nom, prénom et signature</div>
                    <div class="signature-note">Cachet de l'entreprise</div>
                    <div class="signature-note">Date: ____________________</div>
                </div>
                
                <div class="signature-box">
                    <div class="signature-label">POUR LE SALARIÉ</div>
                    <div class="signature-line"></div>
                    <div class="signature-note">Nom, prénom et signature</div>
                    <div class="signature-note">Date: ____________________</div>
                    <div class="signature-note">Lu et approuvé</div>
                </div>
            </div>
            
            <!-- ===== PIED DE PAGE ===== -->
            <div class="footer">
                <p><strong>{{ entreprise.nom or "ENTREPRISE" }}</strong> - {{ entreprise.adresse or "" }} - {{ entreprise.ville or "" }}</p>
                <p>
                    {% if entreprise.telephone %}Tél: {{ entreprise.telephone }}{% endif %}
                    {% if entreprise.email %} - Email: {{ entreprise.email }}{% endif %}
                    {% if entreprise.site_web %} - Site: {{ entreprise.site_web }}{% endif %}
                </p>
                <div class="footer-notes">
                    <p>
                        <strong>Document officiel établi conformément à la législation algérienne en vigueur.</strong><br>
                        • Loi n° 90-11 du 21 avril 1990 relative aux relations de travail<br>
                        • Loi n° 83-13 du 2 juillet 1983 relative à la sécurité sociale<br>
                        • Code des impôts directs et taxes assimilées<br>
                        <em>Généré le {{ date_generation }} - À conserver pendant 5 ans</em>
                    </p>
                </div>
            </div>
        </div>
        
        <!-- ===== BOUTONS D'IMPRESSION ===== -->
        <div class="no-print" style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
            <button onclick="window.print()" style="
                background: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 30px;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                display: flex;
                align-items: center;
                gap: 10px;
            ">
                🖨️ Imprimer / Enregistrer PDF
            </button>
        </div>
        
        <script>
            // Ajouter les icônes FontAwesome
            if (!document.querySelector('link[href*="font-awesome"]')) {
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css';
                document.head.appendChild(link);
            }
        </script>
        </body>
        </html>
        '''
    
        # Remplacer les variables dans le template
        from jinja2 import Template
        template = Template(html_template)
        return template.render(**data)
