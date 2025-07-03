import fitz  # PyMuPDF
import pandas as pd
import tempfile
import os
from pathlib import Path
import json

class PDFGenerator:
    def __init__(self):
        pass
    
    def create_filled_pdf(self, original_pdf_path, filled_data):
        """Create a new PDF with filled form fields"""
        try:
            # Open original PDF
            doc = fitz.open(original_pdf_path)
            
            # Create output path
            output_path = tempfile.mktemp(suffix="_filled.pdf")
            
            # Fill form fields
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Get form widgets and fill them
                widgets = page.widgets()
                for widget in widgets:
                    field_name = widget.field_name
                    if field_name and field_name in filled_data:
                        try:
                            widget.field_value = str(filled_data[field_name])
                            widget.update()
                        except:
                            pass
                
                # If no widgets, try text replacement approach
                if not widgets:
                    self._fill_pdf_by_text_replacement(page, filled_data)
            
            # Save the filled PDF
            doc.save(output_path)
            doc.close()
            
            return output_path
            
        except Exception as e:
            # Fallback: create a new PDF with filled content
            return self._create_new_filled_pdf(original_pdf_path, filled_data)
    
    def _fill_pdf_by_text_replacement(self, page, filled_data):
        """Fill PDF by replacing text patterns"""
        try:
            # Get page text
            text_instances = page.get_text("dict")
            
            # Common patterns to replace
            replacements = self._generate_replacement_patterns(filled_data)
            
            for old_text, new_text in replacements.items():
                # Find and replace text
                text_instances = page.search_for(old_text)
                for inst in text_instances:
                    # Create a new text annotation
                    page.add_redact_annot(inst)
                    page.apply_redactions()
                    page.insert_text(inst.tl, new_text, fontsize=10)
                    
        except Exception as e:
            pass  # Continue if text replacement fails
    
    def _generate_replacement_patterns(self, filled_data):
        """Generate text replacement patterns"""
        replacements = {}
        
        # Map common field patterns
        field_mappings = {
            "From date": filled_data.get("from_date", "01-01-2023"),
            "To Date": filled_data.get("to_date", "31-12-2023"),
            "USD": filled_data.get("indian_capital_amount", "USD 90"),
            "100%": filled_data.get("indian_capital_percentage", "100%"),
        }
        
        for pattern, replacement in field_mappings.items():
            if replacement:
                replacements[pattern] = replacement
        
        return replacements
    
    def _create_new_filled_pdf(self, original_pdf_path, filled_data):
        """Create a completely new PDF with filled content organized by sections"""
        try:
            import reportlab
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            # Create new PDF
            output_path = tempfile.mktemp(suffix="_filled.pdf")
            c = canvas.Canvas(output_path, pagesize=letter)
            
            # Add title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, 750, "ANNUAL PERFORMANCE REPORT (APR) - FILLED")
            
            # Organize data by sections for better presentation
            sections = {
                "I. APR Period": ["from_date", "to_date"],
                "II. UIN": ["uin"],
                "III. Capital Structure": ["indian_capital_amount", "indian_capital_percentage", "foreign_capital_amount", "foreign_capital_percentage"],
                "IV. Control": ["control_status"],
                "V. Shareholding Pattern": [k for k in filled_data.keys() if "partner" in k and ("name" in k or "stake" in k)],
                "VI. Financial Position": [k for k in filled_data.keys() if any(term in k for term in ["net_profit", "dividend", "net_worth"])],
                "VII. Repatriation": [k for k in filled_data.keys() if any(term in k for term in ["repatriation", "repayment", "exports", "royalties", "technical", "consultancy"])],
                "VIII-IX. Profit & Retained Earnings": [k for k in filled_data.keys() if any(term in k for term in ["profit", "retained"])],
                "X-XI. FDI & Refunds": [k for k in filled_data.keys() if any(term in k for term in ["fdi", "refund", "transaction"])],
                "XII. SDS Details": [k for k in filled_data.keys() if "sds" in k],
                "Declaration": [k for k in filled_data.keys() if any(term in k for term in ["authorized", "declaration", "telephone", "email"])],
                "Auditor Certificate": [k for k in filled_data.keys() if any(term in k for term in ["auditor", "audit", "firm", "udin"])],
                "AD Bank Certificate": [k for k in filled_data.keys() if "ad_bank" in k]
            }
            
            y_position = 700
            c.setFont("Helvetica", 9)
            
            for section_name, field_keys in sections.items():
                if any(field_keys):  # Only show sections with data
                    # Section header
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(50, y_position, section_name)
                    y_position -= 20
                    c.setFont("Helvetica", 9)
                    
                    # Section fields
                    for key in field_keys:
                        if key in filled_data and filled_data[key] and str(filled_data[key]).strip():
                            value = str(filled_data[key])
                            line = f"  {key.replace('_', ' ').title()}: {value}"
                            
                            # Handle long lines
                            if len(line) > 85:
                                line = line[:82] + "..."
                            
                            c.drawString(70, y_position, line)
                            y_position -= 12
                    
                    y_position -= 10  # Extra space between sections
                    
                    # Start new page if needed
                    if y_position < 150:
                        c.showPage()
                        y_position = 750
                        c.setFont("Helvetica", 9)
            
            c.save()
            return output_path
            
        except ImportError:
            # If reportlab not available, use simple text overlay
            return self._create_simple_overlay_pdf(original_pdf_path, filled_data)
    
    def _create_simple_overlay_pdf(self, original_pdf_path, filled_data):
        """Create PDF with simple text overlay"""
        try:
            # Copy original and add text overlay
            doc = fitz.open(original_pdf_path)
            output_path = tempfile.mktemp(suffix="_filled.pdf")
            
            # Add text overlays to first page
            if len(doc) > 0:
                page = doc.load_page(0)
                
                # Add filled data as text overlay
                y_pos = 50
                for key, value in list(filled_data.items())[:20]:  # Limit to avoid overcrowding
                    if value and str(value).strip():
                        text = f"{key}: {value}"
                        page.insert_text((50, y_pos), text, fontsize=8, color=(0, 0, 1))
                        y_pos += 12
            
            doc.save(output_path)
            doc.close()
            return output_path
            
        except Exception as e:
            raise Exception(f"Error creating filled PDF: {str(e)}")
    
    def create_filled_excel(self, original_excel_path, filled_data):
        """Create a new Excel file with filled data"""
        try:
            # Read original Excel
            df_dict = pd.read_excel(original_excel_path, sheet_name=None)
            
            # Create output path
            output_path = tempfile.mktemp(suffix="_filled.xlsx")
            
            # Fill data in each sheet
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name, df in df_dict.items():
                    # Create a copy of the dataframe
                    filled_df = df.copy()
                    
                    # Fill empty cells with data from filled_data
                    for idx, row in filled_df.iterrows():
                        for col in filled_df.columns:
                            field_key = f"{sheet_name}_{col}_{idx}"
                            if field_key in filled_data and filled_data[field_key]:
                                # Only fill if current cell is empty
                                if pd.isna(filled_df.loc[idx, col]) or str(filled_df.loc[idx, col]).strip() == "":
                                    filled_df.loc[idx, col] = filled_data[field_key]
                    
                    # Write to Excel
                    filled_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error creating filled Excel: {str(e)}")
