import streamlit as st
import os
import time
import torch
import tempfile
from PIL import Image
from pathlib import Path
from dotenv import load_dotenv
import fitz  # PyMuPDF
import pandas as pd
import google.generativeai as genai

# Load .env variables
load_dotenv()
os.environ["HF_TOKEN"]= "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"
HF_TOKEN = os.environ.get("HF_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

HF_TOKEN="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"

# Setup Gemini
genai.configure(api_key="AIzaSyDMUZoaCgf30dtsfHfByZmsFXqL3My527U")
gemini_model = genai.GenerativeModel("gemini-1.5-flash")
try:
    from transformers import AutoProcessor, AutoModelForVision2Seq
    from huggingface_hub import login
    transformers_available = True
except ImportError:
    transformers_available = False

try:
    from docling_core.types.doc.document import DocTagsDocument
    from docling_core.types.doc import DoclingDocument
    docling_available = True
except ImportError:
    docling_available = False

def check_dependencies():
    missing = []
    if not transformers_available:
        missing.append("transformers")
    if not docling_available:
        missing.append("docling_core")
    return missing

def process_single_image(image, prompt="Convert this image to a Docling"):
    if HF_TOKEN:
        login(token=HF_TOKEN)

    start = time.time()

    processor = AutoProcessor.from_pretrained("ds4/sd/SmolDocling-256M-preview")
    model = AutoModelForVision2Seq.from_pretrained(
        "ds4/sd/SmolDocling-256M-preview",
        torch_dtype=torch.float32
    )

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt}
            ]
        }
    ]

    prompt_text = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(text=prompt_text, images=[image], return_tensors="pt")

    generated_ids = model.generate(**inputs, max_new_tokens=1024)
    prompt_length = inputs.input_ids.shape[1]
    trimmed_generated_ids = generated_ids[:, prompt_length:]
    decoded_output = processor.batch_decode(trimmed_generated_ids, skip_special_tokens=False)[0].strip()
    decoded_output = decoded_output.replace("<end of utterance>", "").strip()

    doctags = DocTagsDocument.from_doctags_and_image_pairs([decoded_output], [image])
    docfile = DoclingDocument(name="document")
    docfile.load_from_doc(doctags)
    md_content = docfile.export_to_markdown()
    processing_time = time.time() - start

    return doctags, md_content, processing_time

def process_pdf_file(pdf_file, prompt="Convert this PDF to Docling"):
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(pdf_file.read())
    temp_file.close()

    pdf_path = temp_file.name
    doc = fitz.open(pdf_path)

    all_md_content = []
    all_doc_tags = []
    total_processing_time = 0
    for page_num in range(len(doc)): 
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        doctags, md_content, processing_time = process_single_image(image, prompt)
        all_doc_tags.append(doctags)
        all_md_content.append(md_content)
        total_processing_time += processing_time

    return all_doc_tags, all_md_content, total_processing_time

def process_excel_file(excelfile, prompt="Convert this Excel file to Docling"):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    temp_file.write(excelfile.read())
    temp_file.close()

    df_dict = pd.read_excel(temp_file.name, sheet_name=None)

    combined_data = ""
    for sheet_name, df in df_dict.items():
        combined_data += f"\n\nSheet: {sheet_name}\n{df.to_string(index=False)}"

    full_prompt = f"{prompt}\n\n{combined_data}"
    response = gemini_model.generate_content(full_prompt)
    return response.text

def fill_form_using_gemini(form_data_text):
    prompt = f"""
You are an intelligent assistant that recognizes APR and FC forms uploaded by the user.
Analyze the form content below, detect each column's data type, and fill any missing values accordingly:

{form_data_text}
"""
    response = gemini_model.generate_content(prompt)
    return response.text

# Streamlit UI
st.title("📄 AI-Powered Form Filler")

uploaded_file = st.file_uploader("Upload an Excel or PDF form", type=["xlsx", "pdf"])

if uploaded_file:
    with st.spinner("Processing file..."):
        if uploaded_file.name.endswith(".pdf"):
            tags, md, time_taken = process_pdf_file(uploaded_file)
            filled_response = fill_form_using_gemini(md)
            st.markdown("### ✅ Gemini-Filled Form Output")
            st.markdown(filled_response)
        elif uploaded_file.name.endswith(".xlsx"):
            filled_response = process_excel_file(uploaded_file)
            st.markdown("### ✅ Gemini-Filled Form Output")
            st.markdown(filled_response)

# Show missing dependencies if any
missing = check_dependencies()
if missing:
    st.warning(f"Missing dependencies: {', '.join(missing)}")