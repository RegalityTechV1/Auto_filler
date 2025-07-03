import streamlit as st
import os
import tempfile
from pathlib import Path
import time
from form_processor import FormProcessor
from pdf_generator import PDFGenerator
import pandas as pd

# Configure page
st.set_page_config(
    page_title="AI-Powered Form Filler",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize processors
@st.cache_resource
def get_form_processor():
    return FormProcessor()

@st.cache_resource  
def get_pdf_generator():
    return PDFGenerator()

def main():
    st.title("📄 AI-Powered Form Filler")
    st.markdown("Upload an unfilled APR form and get it automatically completed with appropriate data")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload APR Form (PDF or Excel)",
        type=["pdf", "xlsx", "xls"],
        help="Select a blank or partially filled APR form to be completed automatically"
    )
    
    if uploaded_file is not None:
        # Display file info
        st.success(f"✅ File uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)")
        
        # Processing button
        if st.button("🚀 Fill Form", type="primary", use_container_width=True):
            process_form(uploaded_file)

def process_form(uploaded_file):
    """Process the uploaded form and generate filled version"""
    
    with st.spinner("🔄 Processing form..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize processors
            form_processor = get_form_processor()
            pdf_generator = get_pdf_generator()
            
            # Step 1: Analyze form structure
            status_text.text("📊 Analyzing form structure...")
            progress_bar.progress(20)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # Step 2: Extract form data
            status_text.text("🔍 Extracting form fields...")
            progress_bar.progress(40)
            
            if uploaded_file.name.lower().endswith('.pdf'):
                form_data = form_processor.process_pdf_form(tmp_file_path)
            else:
                form_data = form_processor.process_excel_form(tmp_file_path)
            
            # Step 3: Generate filled form
            status_text.text("✏️ Filling form fields...")
            progress_bar.progress(60)
            
            filled_data = form_processor.fill_form_intelligently(form_data)
            
            # Step 4: Generate output
            status_text.text("📝 Generating completed form...")
            progress_bar.progress(80)
            
            if uploaded_file.name.lower().endswith('.pdf'):
                output_path = pdf_generator.create_filled_pdf(tmp_file_path, filled_data)
            else:
                output_path = pdf_generator.create_filled_excel(tmp_file_path, filled_data)
            
            progress_bar.progress(100)
            status_text.text("✅ Form completed successfully!")
            
            # Display results
            display_results(output_path, filled_data, uploaded_file.name)
            
            # Cleanup
            os.unlink(tmp_file_path)
            
        except Exception as e:
            st.error(f"❌ Error processing form: {str(e)}")
            st.exception(e)

def display_results(output_path, filled_data, original_filename):
    """Display processing results and download options"""
    
    st.success("🎉 Form filling completed!")
    
    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Form Summary")
        
        # Display filled fields summary
        if isinstance(filled_data, dict):
            fields_filled = len([v for v in filled_data.values() if v and str(v).strip()])
            st.metric("Fields Filled", fields_filled)
            
            # Show sample of filled data
            with st.expander("View Filled Data Sample", expanded=False):
                for key, value in list(filled_data.items())[:10]:  # Show first 10 items
                    if value and str(value).strip():
                        st.text(f"{key}: {value}")
                if len(filled_data) > 10:
                    st.text(f"... and {len(filled_data) - 10} more fields")
    
    with col2:
        st.subheader("📥 Download")
        
        # Read the generated file
        try:
            with open(output_path, 'rb') as f:
                file_data = f.read()
            
            # Generate download filename
            base_name = Path(original_filename).stem
            extension = Path(output_path).suffix
            download_filename = f"{base_name}_filled{extension}"
            
            # Download button
            st.download_button(
                label="⬇️ Download Filled Form",
                data=file_data,
                file_name=download_filename,
                mime="application/pdf" if extension == ".pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            # Cleanup generated file
            os.unlink(output_path)
            
        except Exception as e:
            st.error(f"❌ Error preparing download: {str(e)}")

    # Processing info
    with st.expander("ℹ️ Processing Information", expanded=False):
        st.info("""
        **How it works:**
        1. **Form Analysis**: The AI analyzes your form structure and identifies empty fields
        2. **Reference Matching**: Uses patterns from filled APR forms to understand expected data types
        3. **Smart Generation**: Creates contextually appropriate dummy data for each field
        4. **Structure Preservation**: Maintains exact form layout and formatting
        5. **Output Generation**: Produces a completed form identical to your input but with filled fields
        
        **Data Generated:**
        - Company names, addresses, and contact information
        - Financial figures consistent with APR requirements
        - Dates in proper formats
        - Regulatory codes and identifiers
        - All data maintains contextual accuracy for APR forms
        """)

if __name__ == "__main__":
    main()