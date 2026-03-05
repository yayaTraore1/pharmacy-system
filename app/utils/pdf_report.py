from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Flowable
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from datetime import date
import os
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


PHARMACY_NAME = "Pharmacie Moustapha"
PHARMACY_PHONE = "+224 623 64 68 08"
PHARMACY_ADDRESS = "Kipé - Conakry - Guinée"
PHARMACY_EMAIL = "contact@pharmaciemoustapha.gn"

# Couleurs de la charte
PRIMARY_COLOR = colors.HexColor('#c41e3a')
SECONDARY_COLOR = colors.HexColor('#2c7a7b')
LIGHT_COLOR = colors.HexColor('#f8f9fa')
GREY_COLOR = colors.HexColor('#6c757d')


class HorizontalLine(Flowable):
    """Dessine une ligne horizontale"""
    def __init__(self, width=7.5*inch, height=2, color=PRIMARY_COLOR):
        Flowable.__init__(self)
        self._width = width
        self._height = height
        self.color = color

    def wrap(self, availWidth, availHeight):
        return (self._width, self._height)

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self._height)
        self.canv.line(0, self._height / 2, self._width, self._height / 2)


def _build_header(styles):
    """Construit l'en-tête professionnel"""
    elements = []
    
    # Titre pharmacie
    title_style = ParagraphStyle(
        'PharmacyTitle',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=PRIMARY_COLOR,
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph(PHARMACY_NAME, title_style))
    
    # Ligne de séparation
    elements.append(HorizontalLine(height=2.5))
    elements.append(Spacer(1, 0.15*inch))
    
    # Infos contact
    contact_style = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=GREY_COLOR
    )
    elements.append(Paragraph(f"📍 {PHARMACY_ADDRESS}", contact_style))
    elements.append(Paragraph(f"📞 {PHARMACY_PHONE} | 📧 {PHARMACY_EMAIL}", contact_style))
    elements.append(Spacer(1, 0.2*inch))
    
    return elements


def _build_report_title(title, styles):
    """Construit le titre du rapport"""
    elements = []
    
    report_title = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=PRIMARY_COLOR,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph(title, report_title))
    
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=GREY_COLOR
    )
    elements.append(Paragraph(f"Généré le {date.today().strftime('%d %B %Y')}", date_style))
    elements.append(Spacer(1, 0.15*inch))
    
    return elements


def _add_professional_footer(canvas, doc):
    """Ajoute un pied de page professionnel"""
    # Numéro de page à droite
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(GREY_COLOR)
    canvas.drawRightString(A4[0] - 0.5*inch, 0.5*inch, text)
    
    # Ligne de séparation
    canvas.setStrokeColor(PRIMARY_COLOR)
    canvas.setLineWidth(1)
    canvas.line(0.5*inch, 0.7*inch, A4[0] - 0.5*inch, 0.7*inch)
    
    # Infos en bas
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY_COLOR)
    canvas.drawString(0.5*inch, 0.4*inch, PHARMACY_NAME)
    canvas.drawString(0.5*inch, 0.25*inch, PHARMACY_ADDRESS)


def generate_ruptures_pdf(products):
    """Génère un PDF professionnel des produits en rupture de stock"""
    os.makedirs("invoices", exist_ok=True)
    filepath = f"invoices/ruptures_{date.today().isoformat()}.pdf"
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=1*inch
    )
    elements = []
    styles = getSampleStyleSheet()
    
    # En-têtes et titre
    elements.extend(_build_header(styles))
    elements.extend(_build_report_title("📦 Rapport - Produits en Rupture de Stock", styles))
    
    if products:
        # Boîte de résumé
        summary_data = [["Total Produits", "En Rupture"]]
        summary_values = [len(products), sum(1 for p in products if p.quantity <= 0)]
        summary_data.append([str(summary_values[0]), str(summary_values[1])])
        
        summary_table = Table(summary_data, colWidths=[3.5*inch, 3.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, 1), 16),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f0f0f0')),
            ('BORDER', (0, 0), (-1, -1), 1, PRIMARY_COLOR),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Tableau détail
        data = [['#', 'Produit', 'Stock Actuel', 'Prix Vente', 'Fournisseur']]
        for idx, product in enumerate(products, 1):
            supplier_name = (product.supplier.name if product.supplier else "N/A")[:20]
            data.append([
                str(idx),
                product.name[:28],
                str(product.quantity),
                f"{product.sale_price:.0f} GNF",
                supplier_name
            ])
        
        table = Table(data, colWidths=[0.4*inch, 3*inch, 1.2*inch, 1.3*inch, 1.6*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, PRIMARY_COLOR),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Note de bas
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=GREY_COLOR,
            italic=True
        )
        elements.append(Paragraph(
            f"⚠️ <b>{len(products)} produit(s)</b> actuellement en rupture de stock. Action requise.",
            footer_style
        ))
    else:
        empty_style = ParagraphStyle(
            'Empty',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#27ae60')
        )
        elements.append(Paragraph(
            "✅ Aucun produit en rupture de stock. Situation normale.",
            empty_style
        ))
    
    doc.build(elements, onFirstPage=_add_professional_footer, onLaterPages=_add_professional_footer)
    return filepath


def generate_products_pdf(products):
    """Génère un PDF professionnel listant tous les produits"""
    os.makedirs("invoices", exist_ok=True)
    filepath = f"invoices/products_{date.today().isoformat()}.pdf"
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=1*inch
    )
    elements = []
    styles = getSampleStyleSheet()
    
    # En-têtes
    elements.extend(_build_header(styles))
    elements.extend(_build_report_title("📄 Rapport - Inventaire des Produits", styles))
    
    if products:
        # Statistiques rapides
        stock_ok = sum(1 for p in products if p.quantity > p.rupture_threshold)
        stock_low = sum(1 for p in products if p.quantity <= p.rupture_threshold)
        
        summary_data = [["Total Produits", "Stock Normal", "Stock Faible"]]
        summary_data.append([str(len(products)), str(stock_ok), str(stock_low)])
        
        summary_table = Table(summary_data, colWidths=[2.3*inch, 2.3*inch, 2.3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f0f0f0')),
            ('BORDER', (0, 0), (-1, -1), 1, PRIMARY_COLOR),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Tableau détail
        data = [['#', 'Produit', 'Stock', 'Prix Vente', 'Prix Achat', 'Fournisseur', 'Expiration']]
        for idx, p in enumerate(products, 1):
            supplier = (p.supplier.name if p.supplier else "N/A")[:18]
            exp_date = p.expiration_date.strftime("%d/%m/%Y") if p.expiration_date else "N/A"
            data.append([
                str(idx),
                p.name[:20],
                str(p.quantity),
                f"{p.sale_price:.0f}",
                f"{p.purchase_price:.0f}",
                supplier,
                exp_date
            ])
        
        table = Table(data, colWidths=[0.4*inch, 2*inch, 0.7*inch, 1*inch, 1*inch, 1.3*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, PRIMARY_COLOR),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Note
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=GREY_COLOR,
            italic=True
        )
        elements.append(Paragraph(
            f"📄 Inventaire complet: <b>{len(products)} produit(s)</b> enregistrés.",
            footer_style
        ))
    else:
        empty_style = ParagraphStyle(
            'Empty',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=GREY_COLOR
        )
        elements.append(Paragraph(
            "Aucun produit correspondant.",
            empty_style
        ))
    
    doc.build(elements, onFirstPage=_add_professional_footer, onLaterPages=_add_professional_footer)
    return filepath


def generate_expirations_pdf(products):
    """Génère un PDF professionnel des produits expirés et bientôt expirés"""
    os.makedirs("invoices", exist_ok=True)
    filepath = f"invoices/expirations_{date.today().isoformat()}.pdf"
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=1*inch
    )
    elements = []
    styles = getSampleStyleSheet()
    
    # En-têtes
    elements.extend(_build_header(styles))
    elements.extend(_build_report_title("⚠️ Rapport - Produits Expirés & Bientôt Expirés", styles))
    
    if products:
        # Compteurs
        expired_count = sum(1 for p in products if getattr(p, 'expiration_status', '') == 'Expiré')
        soon_count = sum(1 for p in products if getattr(p, 'expiration_status', '') == 'Bientôt expiré')
        
        # Boîte de résumé
        summary_data = [["Total", "Expirés", "Bientôt expirés"]]
        summary_data.append([str(len(products)), str(expired_count), str(soon_count)])
        
        summary_table = Table(summary_data, colWidths=[2.3*inch, 2.3*inch, 2.3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d32f2f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#ffebee')),
            ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor('#d32f2f')),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Tableau détail
        data = [['#', 'Produit', 'Quantité', 'Date Expiration', 'Statut', 'Fournisseur']]
        for idx, product in enumerate(products, 1):
            supplier_name = (product.supplier.name if product.supplier else "N/A")[:15]
            expiration_str = product.expiration_date.strftime('%d/%m/%Y') if product.expiration_date else 'N/A'
            status = getattr(product, 'expiration_status', 'N/A')
            data.append([
                str(idx),
                product.name[:20],
                str(product.quantity),
                expiration_str,
                status,
                supplier_name
            ])
        
        table = Table(data, colWidths=[0.4*inch, 2*inch, 0.8*inch, 1.2*inch, 1.3*inch, 1.4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d32f2f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff5f5')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#d32f2f')),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Alerte
        alert_style = ParagraphStyle(
            'Alert',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#d32f2f'),
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph(
            f"⚠️ <b>{expired_count}</b> produit(s) EXPIRÉ(S) | <b>{soon_count}</b> bientôt expiré(s). Action recommandée.",
            alert_style
        ))
    else:
        empty_style = ParagraphStyle(
            'Empty',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#27ae60')
        )
        elements.append(Paragraph(
            "✅ Aucun produit expiré ou près d'expiration. Situation nominale.",
            empty_style
        ))
    
    doc.build(elements, onFirstPage=_add_professional_footer, onLaterPages=_add_professional_footer)
    return filepath


# Cette fonction est conservée pour l'API JSON /expired_soon si nécessaire
# Elle génère le rapport pour les produits expirant dans 30 jours
def generate_expired_soon_pdf(products):
    """Génère un PDF professionnel des produits expirant bientôt (30 jours)"""
    os.makedirs("invoices", exist_ok=True)
    filepath = f"invoices/expired_soon_{date.today().isoformat()}.pdf"
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=1*inch
    )
    elements = []
    styles = getSampleStyleSheet()
    
    # En-têtes
    elements.extend(_build_header(styles))
    elements.extend(_build_report_title("📥 Rapport - Produits Expirant Bientôt (30 jours)", styles))
    
    if products:
        # Boîte de résumé
        summary_data = [["Total Produits", "Urgents"]]
        urgents = sum(1 for p in products if (p.expiration_date - date.today()).days <= 7)
        summary_data.append([str(len(products)), str(urgents)])
        
        summary_table = Table(summary_data, colWidths=[3.5*inch, 3.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, 1), 16),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#fef5e7')),
            ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor('#f39c12')),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Tableau détail
        data = [['#', 'Produit', 'Quantité', 'Date Expiration', 'Jours Restants', 'Fournisseur']]
        for idx, product in enumerate(products, 1):
            days_left = (product.expiration_date - date.today()).days
            supplier_name = (product.supplier.name if product.supplier else "N/A")[:15]
            expiration_str = product.expiration_date.strftime('%d/%m/%Y')
            data.append([
                str(idx),
                product.name[:20],
                str(product.quantity),
                expiration_str,
                str(days_left),
                supplier_name
            ])
        
        table = Table(data, colWidths=[0.4*inch, 2*inch, 0.8*inch, 1.2*inch, 1.1*inch, 1.4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fffbf0')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#f39c12')),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Avertissement
        warning_style = ParagraphStyle(
            'Warning',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#f39c12'),
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph(
            f"‚Š� <b>{len(products)} produit(s)</b> expirent dans les 30 prochains jours. Prévoir le renouvellement.",
            warning_style
        ))
    else:
        empty_style = ParagraphStyle(
            'Empty',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#27ae60')
        )
        elements.append(Paragraph(
            "✅ Aucun produit n'expire dans les 30 jours. Approvisionnement correct.",
            empty_style
        ))
    
    doc.build(elements, onFirstPage=_add_professional_footer, onLaterPages=_add_professional_footer)
    return filepath
