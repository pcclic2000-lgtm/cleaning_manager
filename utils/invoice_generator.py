# utils/invoice_generator.py
import os
from datetime import datetime
from decimal import Decimal
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


def generate_invoice_pdf(invoice, file_path):
    """
    Génère un PDF pour une facture
    
    Args:
        invoice: Objet Invoice de la base de données
        file_path: Chemin du fichier PDF à créer
    """
    # Créer le document
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        topMargin=2*cm,
        bottomMargin=2*cm,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Styles personnalisés
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=6
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6
    )
    
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=3
    )
    
    bold_style = ParagraphStyle(
        'Bold',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    # Contenu
    story = []
    
    # En-tête avec logo et infos entreprise
    header_data = []
    
    # Partie gauche: Logo/Infos entreprise
    company_info = []
    if invoice.company_name:
        company_info.append(Paragraph(invoice.company_name, title_style))
    if invoice.company_address:
        address_lines = invoice.company_address.split('\n')
        for line in address_lines:
            if line.strip():
                company_info.append(Paragraph(line.strip(), normal_style))
    
    # Partie droite: Numéro facture et dates
    invoice_info = []
    invoice_info.append(Paragraph("FACTURE", title_style))
    invoice_info.append(Spacer(1, 10))
    
    info_table_data = [
        [Paragraph("N° Facture:", bold_style), Paragraph(invoice.invoice_number, normal_style)],
        [Paragraph("Date:", bold_style), Paragraph(invoice.date.strftime("%d/%m/%Y"), normal_style)],
    ]
    
    if invoice.due_date:
        info_table_data.append([
            Paragraph("Échéance:", bold_style), 
            Paragraph(invoice.due_date.strftime("%d/%m/%Y"), normal_style)
        ])
    
    info_table_data.append([
        Paragraph("Statut:", bold_style), 
        Paragraph(invoice.status.value, normal_style)
    ])
    
    info_table = Table(info_table_data, colWidths=[4*cm, 6*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    invoice_info.append(info_table)
    
    # Table d'en-tête à deux colonnes
    header_table = Table([
        [company_info, invoice_info]
    ], colWidths=[8*cm, 8*cm])
    
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
    ]))
    
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#bdc3c7')))
    story.append(Spacer(1, 20))
    
    # Informations client
    story.append(Paragraph("CLIENT", heading_style))
    
    client = invoice.client
    client_info = []
    client_info.append(Paragraph(f"<b>Nom:</b> {client.nom_complet}", normal_style))
    
    if client.adresse:
        client_info.append(Paragraph(f"<b>Adresse:</b> {client.adresse}", normal_style))
    
    if client.telephone:
        client_info.append(Paragraph(f"<b>Téléphone:</b> {client.telephone}", normal_style))
    
    if client.email:
        client_info.append(Paragraph(f"<b>Email:</b> {client.email}", normal_style))
    
    if client.code_client:
        client_info.append(Paragraph(f"<b>Code client:</b> {client.code_client}", normal_style))
    
    for para in client_info:
        story.append(para)
    
    story.append(Spacer(1, 20))
    
    # Tableau des articles
    story.append(Paragraph("DÉTAIL DE LA FACTURE", heading_style))
    
    # En-têtes du tableau
    items_table_data = []
    headers = ["Description", "Quantité", "Prix unitaire", "TVA %", "Montant HT", "Total TTC"]
    headers_row = [Paragraph(f"<b>{h}</b>", bold_style) for h in headers]
    items_table_data.append(headers_row)
    
    # Données des articles
    for item in invoice.items:
        row = [
            Paragraph(item.description, normal_style),
            Paragraph(str(item.quantity), normal_style),
            Paragraph(f"{item.unit_price:,.2f} DA", normal_style),
            Paragraph(f"{item.tax_rate}%", normal_style),
            Paragraph(f"{(item.quantity * item.unit_price):,.2f} DA", normal_style),
            Paragraph(f"{(item.quantity * item.unit_price * (1 + item.tax_rate/100)):,.2f} DA", normal_style)
        ]
        items_table_data.append(row)
    
    # Style du tableau des articles
    items_table = Table(items_table_data, colWidths=[7*cm, 2*cm, 3*cm, 2*cm, 3*cm, 3*cm])
    items_table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        
        # Bordures
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        
        # Alternance de couleurs des lignes
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 20))
    
    # Totaux
    story.append(Paragraph("TOTAUX", heading_style))
    
    totals_data = [
        [Paragraph("<b>SOUS-TOTAL (HT):</b>", bold_style), 
         Paragraph(f"{invoice.subtotal:,.2f} DA", normal_style)],
        
        [Paragraph("<b>TVA:</b>", bold_style), 
         Paragraph(f"{invoice.tax_amount:,.2f} DA", normal_style)],
        
        [Paragraph("<b>TOTAL (TTC):</b>", bold_style), 
         Paragraph(f"{invoice.total_amount:,.2f} DA", bold_style)],
    ]
    
    if invoice.amount_paid > 0:
        totals_data.append([
            Paragraph("<b>MONTANT DÉJÀ PAYÉ:</b>", bold_style), 
            Paragraph(f"{invoice.amount_paid:,.2f} DA", normal_style)
        ])
        
        solde = invoice.total_amount - invoice.amount_paid
        totals_data.append([
            Paragraph("<b>SOLDE À PAYER:</b>", bold_style), 
            Paragraph(f"{solde:,.2f} DA", ParagraphStyle('Solde', 
                parent=bold_style, 
                textColor=colors.red if solde > 0 else colors.green))
        ])
    
    totals_table = Table(totals_data, colWidths=[10*cm, 6*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (1, 2), (1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 2), (1, 2), 12),
        ('TOPPADDING', (0, 2), (-1, 2), 10),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 10),
    ]))
    
    story.append(totals_table)
    story.append(Spacer(1, 30))
    
    # Informations de paiement
    if invoice.payment_method:
        story.append(Paragraph("INFORMATIONS DE PAIEMENT", heading_style))
        
        payment_info = []
        payment_info.append(Paragraph(f"<b>Mode de paiement:</b> {invoice.payment_method.value}", normal_style))
        
        if invoice.terms:
            story.append(Paragraph("<b>Conditions:</b>", bold_style))
            terms_lines = invoice.terms.split('\n')
            for line in terms_lines:
                if line.strip():
                    story.append(Paragraph(line.strip(), normal_style))
        
        for para in payment_info:
            story.append(para)
    
    story.append(Spacer(1, 20))
    
    # Notes
    if invoice.notes:
        story.append(Paragraph("NOTES", heading_style))
        notes_lines = invoice.notes.split('\n')
        for line in notes_lines:
            if line.strip():
                story.append(Paragraph(line.strip(), small_style))
    
    story.append(Spacer(1, 40))
    
    # Pied de page
    footer_text = """
    <para alignment="center">
    <font size="8" color="gray">
    Facture générée le {date_generation}<br/>
    Merci pour votre confiance !
    </font>
    </para>
    """.format(date_generation=datetime.now().strftime("%d/%m/%Y %H:%M"))
    
    story.append(Paragraph(footer_text, normal_style))
    
    # Générer le PDF
    doc.build(story)
    
    return file_path


def generate_invoice_pdf_simple(invoice, file_path):
    """
    Version simplifiée pour générer un PDF de facture
    Utilise reportlab de base sans dépendances complexes
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    
    # Titre
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "FACTURE")
    
    # Numéro de facture
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 80, f"N°: {invoice.invoice_number}")
    c.drawString(50, height - 100, f"Date: {invoice.date.strftime('%d/%m/%Y')}")
    
    if invoice.due_date:
        c.drawString(50, height - 120, f"Échéance: {invoice.due_date.strftime('%d/%m/%Y')}")
    
    # Informations entreprise
    c.setFont("Helvetica-Bold", 12)
    c.drawString(350, height - 50, invoice.company_name or "Entreprise de Nettoyage")
    
    c.setFont("Helvetica", 10)
    y = height - 80
    if invoice.company_address:
        lines = invoice.company_address.split('\n')
        for line in lines:
            if line.strip():
                c.drawString(350, y, line.strip())
                y -= 20
    
    # Informations client
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 160, "CLIENT:")
    
    c.setFont("Helvetica", 10)
    y = height - 185
    client = invoice.client
    c.drawString(50, y, f"Nom: {client.nom_complet}")
    y -= 20
    
    if client.adresse:
        c.drawString(50, y, f"Adresse: {client.adresse}")
        y -= 20
    
    if client.telephone:
        c.drawString(50, y, f"Téléphone: {client.telephone}")
        y -= 20
    
    # Ligne de séparation
    c.line(50, y, width - 50, y)
    y -= 30
    
    # En-tête du tableau
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "DESCRIPTION")
    c.drawString(300, y, "QUANTITÉ")
    c.drawString(350, y, "PRIX")
    c.drawString(420, y, "TOTAL")
    y -= 20
    c.line(50, y, width - 50, y)
    y -= 10
    
    # Articles
    c.setFont("Helvetica", 9)
    for item in invoice.items:
        # Description (avec retour à la ligne si nécessaire)
        desc_lines = []
        desc = item.description
        while len(desc) > 50:
            space_index = desc[:50].rfind(' ')
            if space_index == -1:
                space_index = 50
            desc_lines.append(desc[:space_index])
            desc = desc[space_index:].strip()
        desc_lines.append(desc)
        
        for i, line in enumerate(desc_lines):
            if i == 0:
                c.drawString(50, y, line)
            else:
                c.drawString(60, y, line)
            y -= 15
        
        # Quantité, prix et total
        item_total = item.quantity * item.unit_price * (1 + item.tax_rate/100)
        c.drawString(300, y + 15 * (len(desc_lines) - 1), str(item.quantity))
        c.drawString(350, y + 15 * (len(desc_lines) - 1), f"{item.unit_price:,.2f} DA")
        c.drawString(420, y + 15 * (len(desc_lines) - 1), f"{item_total:,.2f} DA")
        
        y -= 10
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 9)
    
    # Ligne de séparation
    y = max(y, 150)
    c.line(50, y, width - 50, y)
    y -= 30
    
    # Totaux
    c.setFont("Helvetica-Bold", 10)
    c.drawString(300, y, "SOUS-TOTAL (HT):")
    c.drawString(420, y, f"{invoice.subtotal:,.2f} DA")
    y -= 20
    
    c.drawString(300, y, "TVA:")
    c.drawString(420, y, f"{invoice.tax_amount:,.2f} DA")
    y -= 20
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(300, y, "TOTAL (TTC):")
    c.drawString(420, y, f"{invoice.total_amount:,.2f} DA")
    y -= 30
    
    if invoice.amount_paid > 0:
        c.setFont("Helvetica", 10)
        c.drawString(300, y, "DÉJÀ PAYÉ:")
        c.drawString(420, y, f"{invoice.amount_paid:,.2f} DA")
        y -= 20
        
        solde = invoice.total_amount - invoice.amount_paid
        c.setFont("Helvetica-Bold", 11)
        c.drawString(300, y, "SOLDE À PAYER:")
        c.drawString(420, y, f"{solde:,.2f} DA")
        y -= 30
    
    # Conditions de paiement
    if invoice.terms:
        y = max(y, 100)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "CONDITIONS DE PAIEMENT:")
        y -= 15
        
        c.setFont("Helvetica", 9)
        terms_lines = invoice.terms.split('\n')
        for line in terms_lines:
            if line.strip():
                c.drawString(50, y, line.strip())
                y -= 15
    
    # Pied de page
    c.setFont("Helvetica", 8)
    c.drawString(50, 30, f"Facture générée le {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.drawString(width - 150, 30, "Merci pour votre confiance !")
    
    c.save()
    return file_path