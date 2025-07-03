import os
import json
import fitz  # PyMuPDF
import pandas as pd
import google.generativeai as genai
import tempfile
from pathlib import Path
from dummy_generator import DummyDataGenerator

class FormProcessor:
    def __init__(self):
        # Initialize Gemini
        api_key = os.getenv("GEMINI_API_KEY", "AIzaSyDMUZoaCgf30dtsfHfByZmsFXqL3My527U")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.dummy_generator = DummyDataGenerator()
        
        # Load reference APR data for pattern matching
        self.reference_patterns = self._load_reference_patterns()
    
    def _load_reference_patterns(self):
        """Load patterns from the filled APR form for reference"""
        return {
            "financial_amounts": ["USD 90", "USD -66617", "USD 221473", "USD 124.37"],
            "dates": ["01-01-2023", "31-12-2023", "30th March 2023"],
            "percentages": ["100%", "92.85%"],
            "company_names": ["Carboledger India Private Limited", "Carboledger Inc.", "Greenfrontier Technologies LLP"],
            "countries": ["India", "USA"],
            "activity_codes": ["892", "62099"],
            "contact_info": ["85859 76669", "lavanya@carboledger.com"],
            "firm_details": ["Maddury & Associates", "Firm Registration Number - 023531S"],
            "uin_pattern": "B Y W A Z 2 0 2 3 0 0 6 3",  # Updated with proper spacing
            "data_type_patterns": {
                "uin": "13 alphanumeric characters with spaces (5 letters + 8 numbers)",
                "amounts": "USD format with decimals where appropriate (e.g., USD 124.37)",
                "percentages": "Decimal precision format (e.g., 92.85%)",
                "dates": "DD-MM-YYYY format or descriptive format",
                "activity_codes": "3-digit (1987) and 5-digit (2008) numeric codes",
                "nil_fields": "Use 'Nil' for empty financial fields",
                "yes_no": "Definitive Yes/No answers",
                "signatures": "Format: [Signature of Name]"
            }
        }
    
    def process_pdf_form(self, pdf_path):
        """Extract form structure and fields from PDF"""
        try:
            doc = fitz.open(pdf_path)
            form_data = {}
            
            # Extract text and form fields
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Get form fields if available
                widgets = page.widgets()
                for widget in widgets:
                    field_name = widget.field_name or f"field_{len(form_data)}"
                    field_value = widget.field_value or ""
                    form_data[field_name] = field_value
                
                # Also extract text for analysis
                text = page.get_text()
                if text:
                    form_data[f"page_{page_num}_text"] = text
            
            doc.close()
            
            # If no form fields found, analyze text structure
            if len([k for k in form_data.keys() if not k.startswith("page_")]) == 0:
                form_data = self._analyze_pdf_text_structure(pdf_path)
            
            return form_data
            
        except Exception as e:
            raise Exception(f"Error processing PDF form: {str(e)}")
    
    def _analyze_pdf_text_structure(self, pdf_path):
        """Analyze PDF text to identify form structure"""
        doc = fitz.open(pdf_path)
        full_text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            full_text += page.get_text() + "\n"
        
        doc.close()
        
        # Use Gemini to analyze form structure
        prompt = f"""
        Analyze this APR form text and identify ALL fillable fields systematically.
        Return a comprehensive JSON object with every single field that can be filled.
        
        COMPREHENSIVE FIELD IDENTIFICATION REQUIRED:
        
        Section I: Period dates (from_date, to_date)
        Section II: UIN (13-character unique identification)
        Section III: Capital structure (Indian/Foreign amounts and percentages)  
        Section IV: Control status (Yes/No)
        Section V: Shareholding pattern (up to 3 Indian partners, up to 3 Foreign partners with names and stakes)
        Section VI: Financial position for 2 years (Net Profit/Loss, Dividend, Net worth - Previous & Current)
        Section VII: Repatriation details (7 categories × 2 periods each):
        - Dividend, Loan repayment, Non-equity exports, Royalties, Technical fees, Consultancy fees, Others
        Section VIII: Profit (current and total)
        Section IX: Retained earnings (current and total)
        Section X: FDI amounts (current and total)
        Section XI: Refund details and transaction number
        Section XII: SDS details (name/level/country, parent details, investment details, activity codes, stake %, financial services Y/N, wound up details)
        
        DECLARATION SECTION: Authorized official (signature, name, designation, place, date, phone, email)
        AUDITOR SECTION: Certificate details (year ended fields, signature, firm name, registration, UDIN, place, date, email)
        AD BANK SECTION: Submission details (day, month, year, entity name, official details, place, date)
        
        For each empty field found, create a key-value pair with descriptive field names.
        
        Form text:
        {full_text}
        
        Return comprehensive JSON covering ALL sections and subsections.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            if response.text:
                return json.loads(response.text)
            else:
                return {"error": "No response from AI analysis"}
                
        except Exception as e:
            # Fallback: create basic structure
            return self._create_basic_apr_structure()
    
    def process_excel_form(self, excel_path):
        """Extract form structure from Excel file"""
        try:
            # Read all sheets
            df_dict = pd.read_excel(excel_path, sheet_name=None)
            form_data = {}
            
            for sheet_name, df in df_dict.items():
                # Convert dataframe to dictionary structure
                for idx, row in df.iterrows():
                    for col in df.columns:
                        cell_value = row[col]
                        field_key = f"{sheet_name}_{col}_{idx}"
                        form_data[field_key] = str(cell_value) if pd.notna(cell_value) else ""
            
            return form_data
            
        except Exception as e:
            raise Exception(f"Error processing Excel form: {str(e)}")
    
    def fill_form_intelligently(self, form_data):
        """Use AI to intelligently fill form fields"""
        
        # Create prompt with form structure and reference patterns
        # First ensure we have a comprehensive structure
        comprehensive_structure = self._create_basic_apr_structure()
        
        # Merge with detected form data
        merged_data = comprehensive_structure.copy()
        merged_data.update(form_data)
        
        prompt = f"""
        You are an expert at filling APR (Annual Performance Report) forms with complete, realistic dummy data.
        
        CURRENT FORM STRUCTURE:
        {json.dumps(merged_data, indent=2)}
        
        REFERENCE PATTERNS:
        {json.dumps(self.reference_patterns, indent=2)}
        
        CRITICAL REQUIREMENTS:
        1. Fill EVERY SINGLE empty field - no field should remain blank
        2. Use the comprehensive structure covering all APR sections (I through XII plus declarations)
        3. Maintain data consistency across related fields
        4. Use realistic financial amounts in USD format (e.g., "USD 150,000")
        5. Generate proper dates (format: DD-MM-YYYY)
        6. Use realistic company names, addresses, and contact information
        7. Apply correct activity codes (1987 and 2008 standards)
        8. Fill declaration, auditor, and bank certificate sections completely
        9. Ensure stakeholder percentages add up to 100%
        10. Use consistent currency throughout (USD for foreign transactions)
        
        CRITICAL DATA TYPE REQUIREMENTS:
        - UIN: MUST be 13 alphanumeric characters with spaces like "B Y W A Z 2 0 2 3 0 0 6 3"
        - Dates: Use DD-MM-YYYY format (01-01-2023 to 31-12-2023)
        - Financial amounts: USD format with appropriate decimals (e.g., "USD 90", "USD 124.37", "USD -66617")
        - Percentages: Proper decimal format (e.g., "100%", "92.85%")
        - Activity codes: 3-digit for 1987 (e.g., "892") and 5-digit for 2008 (e.g., "62099")
        - Empty financial fields: Use "Nil" (not "N/A")
        - Yes/No fields: Provide definitive "Yes" or "No" answers
        - Contact details: Realistic phone numbers, email addresses, and complete addresses
        - Signatures: Format as "[Signature of Name]"
        - Company names: Realistic business entity names with proper suffixes
        - Countries: Full country names (e.g., "India", "USA")
        
        MAINTAIN EXACT DATA TYPE CONSISTENCY AS SHOWN IN REFERENCE PATTERNS.
        Return the COMPLETE filled form as JSON with every field populated according to these data type specifications.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            if response.text:
                filled_data = json.loads(response.text)
                
                # Enhance with our dummy data generator for any missing fields
                enhanced_data = self.dummy_generator.enhance_form_data(filled_data)
                return enhanced_data
            else:
                # Fallback to dummy data generator
                return self.dummy_generator.generate_apr_data(form_data)
                
        except Exception as e:
            # Fallback to dummy data generator
            return self.dummy_generator.generate_apr_data(form_data)
    
    def _create_basic_apr_structure(self):
        """Create comprehensive APR form structure covering ALL fields"""
        return {
            # Section I - APR Period
            "from_date": "",
            "to_date": "",
            
            # Section II - UIN
            "uin": "",
            
            # Section III - Capital Structure
            "indian_capital_amount": "",
            "indian_capital_percentage": "",
            "foreign_capital_amount": "",
            "foreign_capital_percentage": "",
            
            # Section IV - Control
            "control_status": "",
            
            # Section V - Shareholding Pattern Changes
            "indian_partner_1_name": "",
            "indian_partner_1_stake": "",
            "indian_partner_2_name": "",
            "indian_partner_2_stake": "",
            "indian_partner_3_name": "",
            "indian_partner_3_stake": "",
            "foreign_partner_1_name": "",
            "foreign_partner_1_stake": "",
            "foreign_partner_2_name": "",
            "foreign_partner_2_stake": "",
            "foreign_partner_3_name": "",
            "foreign_partner_3_stake": "",
            
            # Section VI - Financial Position (Two Years)
            "net_profit_previous_year": "",
            "net_profit_current_year": "",
            "dividend_previous_year": "",
            "dividend_current_year": "",
            "net_worth_previous_year": "",
            "net_worth_current_year": "",
            
            # Section VII - Repatriation (Current Year & Since Commencement)
            "dividend_repatriation_current": "",
            "dividend_repatriation_total": "",
            "loan_repayment_current": "",
            "loan_repayment_total": "",
            "non_equity_exports_current": "",
            "non_equity_exports_total": "",
            "royalties_current": "",
            "royalties_total": "",
            "technical_fees_current": "",
            "technical_fees_total": "",
            "consultancy_fees_current": "",
            "consultancy_fees_total": "",
            "others_specify": "",
            "others_current": "",
            "others_total": "",
            
            # Section VIII - Profit
            "profit_current": "",
            "profit_total": "",
            
            # Section IX - Retained Earnings
            "retained_earnings_current": "",
            "retained_earnings_total": "",
            
            # Section X - FDI by Foreign Entity
            "fdi_current": "",
            "fdi_total": "",
            
            # Section XI - Refund of Excess Share Application Money
            "refund_amount": "",
            "transaction_number": "",
            
            # Section XII - SDS Details
            "sds_name_level_country": "",
            "sds_parent_name_level_country": "",
            "sds_investment_currency": "",
            "sds_investment_amount": "",
            "sds_investment_date": "",
            "sds_activity_code_1987": "",
            "sds_activity_code_2008": "",
            "sds_stake_percentage": "",
            "sds_financial_services_yes": "",
            "sds_financial_services_no": "",
            "sds_wound_up_details": "",
            
            # Declaration Section - Authorized Official
            "authorized_official_signature": "",
            "authorized_official_name": "",
            "authorized_official_designation": "",
            "declaration_place": "",
            "declaration_date": "",
            "telephone_number": "",
            "email_address": "",
            
            # Auditor Certificate Section
            "auditor_certificate_year_ended_1": "",
            "auditor_certificate_year_ended_2": "",
            "auditor_certificate_year_ended_3": "",
            "auditor_signature": "",
            "audit_firm_name": "",
            "audit_firm_registration": "",
            "audit_firm_udin": "",
            "auditor_place": "",
            "auditor_date": "",
            "auditor_email": "",
            
            # AD Bank Certificate Section
            "ad_bank_submission_day": "",
            "ad_bank_submission_month": "",
            "ad_bank_submission_year": "",
            "ad_bank_entity_name": "",
            "ad_bank_official_signature": "",
            "ad_bank_official_name": "",
            "ad_bank_official_designation": "",
            "ad_bank_place": "",
            "ad_bank_date": ""
        }
