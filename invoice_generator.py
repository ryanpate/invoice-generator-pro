from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from datetime import datetime, timedelta
from io import BytesIO
import base64

class InvoiceGenerator:
    def __init__(self, style_template="modern_minimal"):
        self.style = self.get_style_template(style_template)
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def get_style_template(self, template_name):
        templates = {
            "modern_minimal": {
                "primary_color": colors.HexColor("#000000"),
                "secondary_color": colors.HexColor("#666666"),
                "accent_color": colors.HexColor("#000000"),
                "bg_color": colors.HexColor("#F8F9FA"),
                "font": "Helvetica",
                "header_size": 24,
                "body_size": 10
            },
            "corporate_blue": {
                "primary_color": colors.HexColor("#003366"),
                "secondary_color": colors.HexColor("#5588BB"),
                "accent_color": colors.HexColor("#003366"),
                "bg_color": colors.HexColor("#E6F2FF"),
                "font": "Helvetica-Bold",
                "header_size": 26,
                "body_size": 11
            },
            "creative_gradient": {
                "primary_color": colors.HexColor("#FF6B6B"),
                "secondary_color": colors.HexColor("#4ECDC4"),
                "accent_color": colors.HexColor("#FFE66D"),
                "bg_color": colors.HexColor("#FFFFFF"),
                "font": "Helvetica",
                "header_size": 28,
                "body_size": 10
            }
        }
        return templates.get(template_name, templates["modern_minimal"])
    
    def setup_custom_styles(self):
        # Custom styles based on selected template
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=self.style['header_size'],
            textColor=self.style['primary_color'],
            fontName=self.style['font'],
            alignment=TA_LEFT
        ))
        
        self.styles.add(ParagraphStyle(
            name='InvoiceHeader',
            parent=self.styles['Normal'],
            fontSize=self.style['header_size'] + 8,
            textColor=self.style['primary_color'],
            fontName=self.style['font'],
            alignment=TA_RIGHT,
            bold=True
        ))
        
    def generate_invoice(self, invoice_data, logo_path=None):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Add Logo and Header
        header_data = []
        if logo_path:
            # Add logo
            img = Image(logo_path, width=2*inch, height=1*inch)
            header_data.append([img, Paragraph("INVOICE", self.styles['InvoiceHeader'])])
        else:
            header_data.append([
                Paragraph(invoice_data['company_name'], self.styles['CustomTitle']),
                Paragraph("INVOICE", self.styles['InvoiceHeader'])
            ])
        
        header_table = Table(header_data, colWidths=[4*inch, 2.5*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 20))
        
        # Company and Client Info
        company_info = f"""
        {invoice_data['company_name']}<br/>
        {invoice_data.get('company_address', '')}<br/>
        {invoice_data.get('company_email', '')}<br/>
        {invoice_data.get('company_phone', '')}
        """
        
        client_info = f"""
        <b>Bill To:</b><br/>
        {invoice_data['client_name']}<br/>
        {invoice_data.get('client_address', '')}<br/>
        {invoice_data.get('client_email', '')}
        """
        
        invoice_meta = f"""
        <b>Invoice #:</b> {invoice_data['invoice_number']}<br/>
        <b>Date:</b> {invoice_data['invoice_date']}<br/>
        <b>Due Date:</b> {invoice_data['due_date']}<br/>
        <b>Amount Due:</b> {invoice_data['currency']} {invoice_data['total']}
        """
        
        info_data = [
            [Paragraph(company_info, self.styles['Normal']), 
             Paragraph(client_info, self.styles['Normal']),
             Paragraph(invoice_meta, self.styles['Normal'])]
        ]
        
        info_table = Table(info_data, colWidths=[2.2*inch, 2.2*inch, 2.1*inch])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, 0), 1, self.style['accent_color']),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 30))
        
        # Line Items
        line_items = [['Description', 'Qty', 'Rate', 'Amount']]
        
        for item in invoice_data['items']:
            amount = float(item['quantity']) * float(item['rate'])
            line_items.append([
                item['description'],
                str(item['quantity']),
                f"{invoice_data['currency']} {item['rate']}",
                f"{invoice_data['currency']} {amount:.2f}"
            ])
        
        # Add subtotal, tax, total
        line_items.append(['', '', 'Subtotal:', f"{invoice_data['currency']} {invoice_data['subtotal']}"])
        if invoice_data.get('tax_rate'):
            line_items.append(['', '', f"Tax ({invoice_data['tax_rate']}%):", f"{invoice_data['currency']} {invoice_data['tax_amount']}"])
        line_items.append(['', '', 'Total:', f"{invoice_data['currency']} {invoice_data['total']}"])
        
        items_table = Table(line_items, colWidths=[3.5*inch, 0.75*inch, 1.25*inch, 1*inch])
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.style['primary_color']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), self.style['font']),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, len(line_items)-4), 0.5, colors.grey),
            
            # Total row
            ('LINEABOVE', (2, -1), (-1, -1), 2, self.style['primary_color']),
            ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (2, -1), (-1, -1), 11),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 30))
        
        # Notes/Terms
        if invoice_data.get('notes'):
            notes = Paragraph(f"<b>Notes:</b><br/>{invoice_data['notes']}", self.styles['Normal'])
            elements.append(notes)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer