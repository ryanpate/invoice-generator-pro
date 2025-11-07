import pandas as pd
import zipfile
from io import BytesIO
from datetime import datetime, timedelta
from invoice_generator import InvoiceGenerator
import streamlit as st

class BatchInvoiceProcessor:
    def __init__(self, style_template="modern_minimal"):
        self.generator = InvoiceGenerator(style_template)
        self.errors = []
        self.successful_invoices = []
    
    def validate_csv(self, df):
        """Validate CSV has required columns"""
        required_columns = [
            'client_name', 'client_email', 'item_description', 
            'quantity', 'rate'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        
        # Check for empty values in critical fields
        if df['client_name'].isnull().any():
            return False, "Client name cannot be empty"
        
        if df['item_description'].isnull().any():
            return False, "Item description cannot be empty"
            
        return True, "Valid"
    
    def process_batch(self, csv_file, company_data, logo_path=None):
        """Process CSV file and generate multiple invoices"""
        try:
            # Read CSV
            df = pd.read_csv(csv_file)
            
            # Validate
            is_valid, message = self.validate_csv(df)
            if not is_valid:
                return None, message
            
            # Group by client to create one invoice per client
            grouped = df.groupby(['client_name', 'client_email'])
            
            # Create ZIP file in memory
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                invoice_count = 0
                
                for (client_name, client_email), group in grouped:
                    invoice_count += 1
                    
                    # Generate invoice number
                    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{invoice_count:03d}"
                    
                    # Prepare line items
                    items = []
                    for _, row in group.iterrows():
                        items.append({
                            'description': row['item_description'],
                            'quantity': float(row['quantity']),
                            'rate': float(row['rate'])
                        })
                    
                    # Calculate totals
                    subtotal = sum(item['quantity'] * item['rate'] for item in items)
                    tax_rate = float(group.iloc[0].get('tax_rate', 0) if 'tax_rate' in group.columns else 0)
                    tax_amount = subtotal * (tax_rate / 100)
                    total = subtotal + tax_amount
                    
                    # Get optional fields with defaults
                    client_address = group.iloc[0].get('client_address', '') if 'client_address' in group.columns else ''
                    client_phone = group.iloc[0].get('client_phone', '') if 'client_phone' in group.columns else ''
                    payment_terms = group.iloc[0].get('payment_terms', 'Net 30') if 'payment_terms' in group.columns else 'Net 30'
                    currency = group.iloc[0].get('currency', 'USD') if 'currency' in group.columns else 'USD'
                    notes = group.iloc[0].get('notes', company_data.get('default_notes', '')) if 'notes' in group.columns else company_data.get('default_notes', '')
                    
                    # Calculate due date based on payment terms
                    invoice_date = datetime.now()
                    if payment_terms == "Due on Receipt":
                        due_date = invoice_date
                    else:
                        try:
                            days = int(payment_terms.split()[1])
                            due_date = invoice_date + timedelta(days=days)
                        except:
                            due_date = invoice_date + timedelta(days=30)
                    
                    # Create invoice data
                    invoice_data = {
                        'company_name': company_data['company_name'],
                        'company_address': company_data['company_address'],
                        'company_email': company_data['company_email'],
                        'company_phone': company_data['company_phone'],
                        'client_name': client_name,
                        'client_address': client_address,
                        'client_email': client_email,
                        'client_phone': client_phone,
                        'invoice_number': invoice_number,
                        'invoice_date': invoice_date.strftime('%B %d, %Y'),
                        'due_date': due_date.strftime('%B %d, %Y'),
                        'currency': currency,
                        'items': items,
                        'subtotal': f"{subtotal:.2f}",
                        'tax_rate': tax_rate,
                        'tax_amount': f"{tax_amount:.2f}",
                        'total': f"{total:.2f}",
                        'notes': notes
                    }
                    
                    # Generate PDF
                    pdf_buffer = self.generator.generate_invoice(invoice_data, logo_path)
                    
                    # Add to ZIP
                    pdf_filename = f"{invoice_number}_{client_name.replace(' ', '_')}.pdf"
                    zip_file.writestr(pdf_filename, pdf_buffer.getvalue())
                    
                    self.successful_invoices.append({
                        'invoice_number': invoice_number,
                        'client': client_name,
                        'total': f"{currency} {total:.2f}"
                    })
            
            zip_buffer.seek(0)
            return zip_buffer, f"Successfully generated {invoice_count} invoices"
            
        except Exception as e:
            return None, f"Error processing CSV: {str(e)}"
    
    def get_summary_report(self):
        """Generate summary of batch processing"""
        if not self.successful_invoices:
            return "No invoices generated"
        
        report = "📊 **Batch Processing Summary**\n\n"
        report += f"✅ Total Invoices Generated: {len(self.successful_invoices)}\n\n"
        
        total_value = 0
        for inv in self.successful_invoices:
            report += f"• {inv['invoice_number']}: {inv['client']} - {inv['total']}\n"
        
        return report