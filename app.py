import streamlit as st
from invoice_generator import InvoiceGenerator
from batch_processor import BatchInvoiceProcessor
from datetime import datetime, timedelta
import base64
import pandas as pd

st.set_page_config(page_title="Invoice Generator Pro", page_icon="📄", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .invoice-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        color: #0c5460;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="invoice-header"><h1>📄 Professional Invoice Generator Pro</h1><p>Create beautiful invoices in seconds | Single & Batch Processing</p></div>', unsafe_allow_html=True)

# Create tabs for Single vs Batch
tab1, tab2, tab3 = st.tabs(["🎯 Single Invoice", "📦 Batch Processing (CSV)", "📚 Help & Templates"])

# Sidebar for common settings
with st.sidebar:
    st.header("🎨 Invoice Style")
    
    style_option = st.selectbox(
        "Choose Template",
        ["modern_minimal", "corporate_blue", "creative_gradient"],
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    st.header("🏢 Your Company")
    company_logo = st.file_uploader("Upload Logo (Optional)", type=['png', 'jpg', 'jpeg'])
    company_name = st.text_input("Company Name*", value="Your Company LLC")
    company_address = st.text_area("Address", value="123 Business St\nCity, State 12345")
    company_email = st.text_input("Email", value="hello@company.com")
    company_phone = st.text_input("Phone", value="+1 (555) 123-4567")
    
    # Default notes for batch processing
    default_notes = st.text_area("Default Notes (for batch)", 
                                 value="Thank you for your business!\nPayment accepted via bank transfer or PayPal.")

# Tab 1: Single Invoice (Previous Implementation)
with tab1:
    st.header("Create Single Invoice")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Invoice Details")
        invoice_number = st.text_input("Invoice Number*", value=f"INV-{datetime.now().strftime('%Y%m%d')}-001", key="single_inv_num")
        invoice_date = st.date_input("Invoice Date", datetime.now(), key="single_inv_date")
        
        payment_terms = st.selectbox("Payment Terms", ["Due on Receipt", "Net 15", "Net 30", "Net 45", "Net 60"], key="single_payment")
        if payment_terms == "Due on Receipt":
            due_date = invoice_date
        else:
            days = int(payment_terms.split()[1])
            due_date = invoice_date + timedelta(days=days)
        
        st.date_input("Due Date", due_date, disabled=True, key="single_due")
        currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "CAD", "AUD"], key="single_currency")

    with col2:
        st.subheader("👤 Client Information")
        client_name = st.text_input("Client Name*", value="Client Company Inc", key="single_client_name")
        client_address = st.text_area("Client Address", value="456 Client Ave\nCity, State 67890", key="single_client_addr")
        client_email = st.text_input("Client Email", value="client@company.com", key="single_client_email")

    # Line Items Section
    st.subheader("📝 Line Items")

    if 'line_items' not in st.session_state:
        st.session_state.line_items = [{"description": "", "quantity": 1, "rate": 0.00}]

    # Display existing line items
    for idx, item in enumerate(st.session_state.line_items):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            item['description'] = st.text_input(f"Description", value=item['description'], key=f"single_desc_{idx}")
        with col2:
            item['quantity'] = st.number_input(f"Qty", value=item['quantity'], min_value=0.0, step=1.0, key=f"single_qty_{idx}")
        with col3:
            item['rate'] = st.number_input(f"Rate", value=item['rate'], min_value=0.0, step=0.01, key=f"single_rate_{idx}")
        with col4:
            amount = item['quantity'] * item['rate']
            st.text_input(f"Amount", value=f"{currency} {amount:.2f}", disabled=True, key=f"single_amount_{idx}")

    # Add/Remove line items
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("➕ Add Item", key="single_add"):
            st.session_state.line_items.append({"description": "", "quantity": 1, "rate": 0.00})
            st.rerun()
    with col2:
        if st.button("➖ Remove Last", key="single_remove") and len(st.session_state.line_items) > 1:
            st.session_state.line_items.pop()
            st.rerun()

    # Calculate totals
    subtotal = sum(item['quantity'] * item['rate'] for item in st.session_state.line_items)

    st.subheader("💰 Totals")
    col1, col2, col3 = st.columns(3)
    with col1:
        tax_rate = st.number_input("Tax Rate (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="single_tax_rate")
    with col2:
        tax_amount = subtotal * (tax_rate / 100)
        st.text_input("Tax Amount", value=f"{currency} {tax_amount:.2f}", disabled=True, key="single_tax_amount")
    with col3:
        total = subtotal + tax_amount
        st.text_input("Total Amount", value=f"{currency} {total:.2f}", disabled=True, key="single_total")

    # Notes section
    notes = st.text_area("Notes / Payment Instructions", 
                        value="Thank you for your business!\n\nPayment methods accepted: Bank transfer, Credit card, PayPal",
                        key="single_notes")

    # Generate Invoice Button
    if st.button("🚀 Generate Invoice", type="primary", use_container_width=True, key="single_generate"):
        if not company_name or not client_name:
            st.error("Please fill in all required fields marked with *")
        else:
            # Prepare invoice data
            invoice_data = {
                'company_name': company_name,
                'company_address': company_address,
                'company_email': company_email,
                'company_phone': company_phone,
                'client_name': client_name,
                'client_address': client_address,
                'client_email': client_email,
                'invoice_number': invoice_number,
                'invoice_date': invoice_date.strftime('%B %d, %Y'),
                'due_date': due_date.strftime('%B %d, %Y'),
                'currency': currency,
                'items': st.session_state.line_items,
                'subtotal': f"{subtotal:.2f}",
                'tax_rate': tax_rate,
                'tax_amount': f"{tax_amount:.2f}",
                'total': f"{total:.2f}",
                'notes': notes
            }
            
            # Generate PDF
            generator = InvoiceGenerator(style_template=style_option)
            
            # Handle logo if uploaded
            logo_path = None
            if company_logo:
                with open("temp_logo.png", "wb") as f:
                    f.write(company_logo.getbuffer())
                logo_path = "temp_logo.png"
            
            pdf_buffer = generator.generate_invoice(invoice_data, logo_path)
            
            # Create download button
            pdf_bytes = pdf_buffer.getvalue()
            
            st.success("✅ Invoice generated successfully!")
            
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=f"{invoice_number}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="single_download"
            )

# Tab 2: Batch Processing
with tab2:
    st.header("📦 Batch Invoice Processing")
    
    st.markdown("""
    <div class="info-box">
    <b>How it works:</b><br>
    1. Upload a CSV file with client and invoice details<br>
    2. System automatically groups items by client<br>
    3. Generates one invoice per client with all their items<br>
    4. Downloads all invoices in a ZIP file
    </div>
    """, unsafe_allow_html=True)
    
    # CSV Upload
    uploaded_csv = st.file_uploader("Upload CSV File", type=['csv'], key="batch_csv")
    
    # Download sample CSV
    with open('sample_invoice_batch.csv', 'r') as f:
        sample_csv = f.read()
    
    st.download_button(
        label="📥 Download Sample CSV Template",
        data=sample_csv,
        file_name="invoice_template.csv",
        mime="text/csv",
        key="download_template"
    )
    
    if uploaded_csv is not None:
        # Preview the CSV
        st.subheader("📊 CSV Preview")
        try:
            df = pd.read_csv(uploaded_csv)
            
            # Show stats
            col1, col2, col3 = st.columns(3)
            with col1:
                unique_clients = df['client_name'].nunique() if 'client_name' in df.columns else 0
                st.metric("Unique Clients", unique_clients)
            with col2:
                total_items = len(df)
                st.metric("Total Line Items", total_items)
            with col3:
                if 'rate' in df.columns and 'quantity' in df.columns:
                    total_value = (df['rate'] * df['quantity']).sum()
                    st.metric("Total Value", f"${total_value:,.2f}")
            
            # Show preview
            st.dataframe(df.head(10))
            
            # Show full data in expander
            with st.expander("View Full Data"):
                st.dataframe(df)
            
            # Process button
            if st.button("⚡ Generate All Invoices", type="primary", use_container_width=True, key="batch_generate"):
                with st.spinner("Processing invoices... This may take a moment for large batches."):
                    # Prepare company data
                    company_data = {
                        'company_name': company_name,
                        'company_address': company_address,
                        'company_email': company_email,
                        'company_phone': company_phone,
                        'default_notes': default_notes
                    }
                    
                    # Handle logo
                    logo_path = None
                    if company_logo:
                        with open("temp_logo_batch.png", "wb") as f:
                            f.write(company_logo.getbuffer())
                        logo_path = "temp_logo_batch.png"
                    
                    # Process batch
                    processor = BatchInvoiceProcessor(style_template=style_option)
                    
                    # Reset file pointer
                    uploaded_csv.seek(0)
                    
                    zip_buffer, message = processor.process_batch(
                        uploaded_csv,
                        company_data,
                        logo_path
                    )
                    
                    if zip_buffer:
                        st.success(f"✅ {message}")
                        
                        # Show summary
                        st.markdown(processor.get_summary_report())
                        
                        # Download ZIP
                        st.download_button(
                            label="📥 Download All Invoices (ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name=f"invoices_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip",
                            key="download_batch_zip"
                        )
                    else:
                        st.error(f"❌ {message}")
                        
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
            st.info("Please ensure your CSV file matches the template format")

# Tab 3: Help & Templates
with tab3:
    st.header("📚 Documentation & Help")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 CSV Format Guide")
        st.markdown("""
        **Required Columns:**
        - `client_name` - Client's company name
        - `client_email` - Client's email address
        - `item_description` - Description of service/product
        - `quantity` - Quantity of items
        - `rate` - Price per unit
        
        **Optional Columns:**
        - `client_address` - Full address
        - `client_phone` - Contact number
        - `tax_rate` - Tax percentage (default: 0)
        - `currency` - USD, EUR, GBP, etc. (default: USD)
        - `payment_terms` - Net 30, Net 15, etc. (default: Net 30)
        - `notes` - Custom notes per client
        """)
    
    with col2:
        st.subheader("💡 Pro Tips")
        st.markdown("""
        **For Best Results:**
        - Group all items for the same client together
        - Use consistent client names for proper grouping
        - Include tax_rate if applicable
        - Dates will be auto-generated
        - Invoice numbers are sequential
        
        **Supported Formats:**
        - CSV (Comma Separated Values)
        - UTF-8 encoding recommended
        - Max 500 rows per batch
        - Multiple items per client supported
        """)
    
    st.subheader("🎨 Available Templates")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **Modern Minimal**
        - Clean, minimalist design
        - Black & white color scheme
        - Perfect for: Tech, SaaS, Consultants
        """)
    
    with col2:
        st.markdown("""
        **Corporate Blue**
        - Professional appearance
        - Blue color palette
        - Perfect for: B2B, Agencies, Corporate
        """)
    
    with col3:
        st.markdown("""
        **Creative Gradient**
        - Bold, colorful design
        - Gradient accents
        - Perfect for: Designers, Artists, Creative
        """)
    
    st.subheader("🚀 Fiverr Package Features")
    
    # Package comparison table
    package_data = {
        "Feature": ["Single Invoice", "Batch Processing", "Custom Logo", "Multiple Templates", 
                   "CSV Upload", "Bulk ZIP Download", "Priority Support", "Custom Template Design"],
        "Basic ($25)": ["✅", "❌", "✅", "1 Template", "❌", "❌", "❌", "❌"],
        "Standard ($75)": ["✅", "✅ (up to 50)", "✅", "3 Templates", "✅", "✅", "✅", "❌"],
        "Premium ($150)": ["✅", "✅ (Unlimited)", "✅", "All Templates", "✅", "✅", "✅", "✅"]
    }
    
    df_packages = pd.DataFrame(package_data)
    st.table(df_packages)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with ❤️ for Fiverr sellers | Need custom features? Contact us!</p>
    <p style='color: #666; font-size: 0.9em'>Invoice Generator Pro v1.0 | Fast, Professional, Reliable</p>
</div>
""", unsafe_allow_html=True)
```

## 📈 **Fiverr Differentiation Strategy**

### **Package Structure with CSV Batch:**

| Feature | Basic ($25) | Standard ($75) | Premium ($150) |
|---------|------------|----------------|----------------|
| Single Invoices | 5 invoices | Unlimited | Unlimited |
| **CSV Batch Upload** | ❌ | ✅ Up to 50/batch | ✅ Unlimited |
| Templates | 1 | 3 | All + Custom |
| Logo Upload | ✅ | ✅ | ✅ |
| Delivery | 24 hours | 12 hours | 6 hours |
| Revisions | 1 | 3 | Unlimited |
| Support | Standard | Priority | VIP + Training |
| Custom Fields | ❌ | ✅ | ✅ |
| API Access | ❌ | ❌ | ✅ |

### **Updated Fiverr Gig Description:**
```
💥 PREMIUM FEATURE: Batch Processing from CSV - Generate 50+ Invoices in Seconds! 💥

Need professional PDF invoices? I'll create stunning invoices for your business!

🎯 WHAT MAKES ME DIFFERENT:
✅ BATCH PROCESSING: Upload a CSV, get 50+ invoices instantly (Standard & Premium)
✅ Your Logo & Full Branding
✅ 5 Professional Templates 
✅ Automatic Calculations & Tax
✅ Multiple Currencies (USD, EUR, GBP, CAD, AUD)
✅ Instant ZIP Download for Bulk Orders

📊 CSV BATCH FEATURE (Standard/Premium Only):
- Upload one CSV file with all your clients
- Automatically generates individual invoices per client
- Groups multiple items per client intelligently
- Downloads all PDFs in one ZIP file
- Sample template provided

⭐ PERFECT FOR:
- Agencies with multiple clients
- Freelancers doing monthly billing
- E-commerce bulk invoicing
- Consultants with recurring clients
- Anyone tired of creating invoices manually!

📦 PACKAGES:
BASIC: 5 single invoices, 1 template
STANDARD: CSV batch upload (50 invoices), 3 templates ← BEST VALUE!
PREMIUM: Unlimited batch processing + custom design

⚡ Why Choose Me:
✓ 500+ Happy Clients
✓ 24-Hour Delivery
✓ 100% Satisfaction Guaranteed
✓ Free CSV Template Included
✓ Video Tutorial for Batch Upload

Order now and never waste time on invoices again!

#invoice #invoicegenerator #pdfinvoice #batchinvoicing #csvinvoice