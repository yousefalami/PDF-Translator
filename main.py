# -*- coding: utf-8 -*-
import os
import configparser
import requests
import pdfplumber
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from tqdm import tqdm

# --- Configuration & Constants ---
DEFAULT_FONT = "Arial"
DEFAULT_PROMPT_TEMPLATE = "Translate the following {source_language} text to {target_language}. Provide only the translated text, without any introductory phrases, explanations, or the original text itself:\n\n{text_to_translate}"
CONFIG_FILENAME = 'config.ini'

# --- Helper Functions ---
def print_separator(char="=", length=70):
    """Prints a separator line."""
    print(f"\n{char * length}\n")

def print_header(title):
    """Prints a formatted header."""
    print_separator()
    print(f"--- {title} ---")
    print()

# --- File and Document Processing Functions ---

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from each page of a PDF file.
    """
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found at path '{pdf_path}'.")
        return None
    
    page_texts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"📄 Processing {len(pdf.pages)} pages from PDF: '{os.path.basename(pdf_path)}'")
            for i, page in enumerate(tqdm(pdf.pages, desc="🔍 Extracting text from PDF pages", unit="page")):
                text = page.extract_text()
                page_texts.append(text if text else "") 
        print("✅ Text extraction successful.")
        return page_texts
    except Exception as e:
        print(f"❌ Error during text extraction from PDF: {e}")
        return None

def create_translation_document(original_pdf_name, page_data, source_language, target_language, font_name, output_folder="translated_documents"):
    """
    Creates a Word document with two-column tables for original and translated text, using the specified font.
    """
    if not os.path.exists(output_folder):
        try:
            os.makedirs(output_folder)
            print(f"📂 Output folder '{output_folder}' created.")
        except OSError as e:
            print(f"❌ Error creating output folder '{output_folder}': {e}")
            return


    doc = Document()
    # Document Properties (Optional, but good practice)
    core_props = doc.core_properties
    core_props.title = f"Translation of {original_pdf_name}"
    core_props.author = "PDF Translation Script"
    core_props.comments = f"Translated from {source_language} to {target_language} using font {font_name}."

    doc.add_heading(f"Translation: {original_pdf_name}", level=1)
    doc.add_paragraph(f"Original Language: {source_language}\nTarget Language: {target_language}")
    doc.add_paragraph(f"Font Used: {font_name}")
    doc.add_paragraph("\n")

    print(f"\n📝 Creating Word document for '{original_pdf_name}'...")
    for i, data in enumerate(tqdm(page_data, desc="✒️ Writing pages to Word document", unit="page")):
        original_text = data['original']
        translated_text = data['translated']

        doc.add_heading(f"Page {i + 1}", level=2)
        
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid' 

        table.columns[0].width = Inches(3.5)
        table.columns[1].width = Inches(3.5)

        hdr_cells = table.rows[0].cells
        
        # Original Text Header
        cell_original_hdr = hdr_cells[0]
        p_original_hdr = cell_original_hdr.paragraphs[0]
        if source_language.lower() in ['arabic', 'urdu', 'hebrew', 'persian', 'farsi']:
            p_original_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
            p_original_hdr.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run_original_hdr = p_original_hdr.add_run(f'Original Text ({source_language})')
        run_original_hdr.font.name = font_name
        run_original_hdr.font.size = Pt(12)
        run_original_hdr.bold = True
        
        # Translated Text Header
        cell_translated_hdr = hdr_cells[1]
        p_translated_hdr = cell_translated_hdr.paragraphs[0]
        if target_language.lower() in ['arabic', 'urdu', 'hebrew', 'persian', 'farsi']:
             p_translated_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
             p_translated_hdr.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run_translated_hdr = p_translated_hdr.add_run(f'Translation ({target_language})')
        run_translated_hdr.font.name = font_name
        run_translated_hdr.font.size = Pt(12)
        run_translated_hdr.bold = True

        row_cells = table.add_row().cells
        
        # Original Text Content
        p_original = row_cells[0].paragraphs[0]
        if source_language.lower() in ['arabic', 'urdu', 'hebrew', 'persian', 'farsi']:
            p_original.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
            p_original.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run_original = p_original.add_run(original_text if original_text else " ")
        run_original.font.name = font_name
        run_original.font.size = Pt(11)
        
        # Translated Text Content
        p_translated = row_cells[1].paragraphs[0]
        if target_language.lower() in ['arabic', 'urdu', 'hebrew', 'persian', 'farsi']: 
            p_translated.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else: 
            p_translated.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run_translated = p_translated.add_run(translated_text if translated_text else " ")
        run_translated.font.name = font_name
        run_translated.font.size = Pt(11)

        if i < len(page_data) - 1: 
            doc.add_page_break()

    output_filename = os.path.join(output_folder, f"{original_pdf_name}_translated_{source_language}_to_{target_language}.docx")
    try:
        doc.save(output_filename)
        print(f"\n✅ Translated document successfully saved at: '{os.path.abspath(output_filename)}'")
    except Exception as e:
        print(f"❌ Error saving Word file: {e}")

# --- API and Configuration Functions ---

def read_api_config(filename=CONFIG_FILENAME):
    """
    Reads API information (URL, Model, Font Name, and Prompt Template) from the config file.
    Returns API URL, Model Name, Font Name, and Prompt Template.
    """
    config = configparser.ConfigParser()
    api_url = None
    api_model = None
    font_name = DEFAULT_FONT
    prompt_template = DEFAULT_PROMPT_TEMPLATE

    if not os.path.exists(filename):
        print(f"⚠️ Warning: Config file '{filename}' not found.")
        print(f"   Please create '{filename}' with [API] section including 'url', 'model'.")
        print(f"   Optional: 'font_name', 'prompt_template'.")
        print(f"   Using default font: '{font_name}'")
        print(f"   Using default prompt template.")
        return api_url, api_model, font_name, prompt_template

    try:
        config.read(filename)
        if 'API' in config:
            api_section = config['API']
            api_url = api_section.get('url')
            api_model = api_section.get('model')
            
            font_name_config = api_section.get('font_name')
            if font_name_config:
                font_name = font_name_config
            else:
                print(f"ℹ️ Info: 'font_name' not found or empty in [{filename} -> API]. Using default: '{DEFAULT_FONT}'.")

            prompt_template_config = api_section.get('prompt_template')
            if prompt_template_config:
                prompt_template = prompt_template_config
            else:
                print(f"ℹ️ Info: 'prompt_template' not found or empty in [{filename} -> API]. Using default template.")
        else:
            print(f"❌ Error: [API] section not found in '{filename}'.")
            print(f"   Ensure '{filename}' contains [API] with 'url' and 'model'.")

        if not api_url:
            print(f"❌ Error: 'url' is missing in [{filename} -> API].")
        if not api_model:
            print(f"❌ Error: 'model' is missing in [{filename} -> API].")
            
        return api_url, api_model, font_name, prompt_template
    
    except Exception as e:
        print(f"❌ Error reading config file '{filename}': {e}")
        return None, None, DEFAULT_FONT, DEFAULT_PROMPT_TEMPLATE

def translate_text_via_api(text_to_translate, api_url, model_name, target_language, source_language, prompt_template):
    """
    Translates text using the specified API and prompt template.
    """
    if not text_to_translate.strip():
        return "" 

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Format the prompt using the provided template and languages
        final_prompt = prompt_template.format(
            source_language=source_language,
            target_language=target_language,
            text_to_translate=text_to_translate
        )
    except KeyError as e:
        print(f"❌ Error: Placeholder {e} missing in the 'prompt_template' from config.")
        print(f"   Your template: \"{prompt_template}\"")
        print(f"   Ensure it includes {{source_language}}, {{target_language}}, and {{text_to_translate}}.")
        return "Error: Invalid prompt template"


    payload = {
        "model": model_name, 
        "messages": [{"role": "user", "content": final_prompt}]
    }

    try:
        # print(f"\nSending translation request for a part of the text from {source_language} to {target_language} using model: {model_name}") # Verbose
        response = requests.post(api_url, headers=headers, json=payload, timeout=180) # Increased timeout
        response.raise_for_status()
        
        response_data = response.json()

        if response_data.get("choices") and \
           isinstance(response_data["choices"], list) and \
           len(response_data["choices"]) > 0 and \
           response_data["choices"][0].get("message") and \
           response_data["choices"][0]["message"].get("content"):
            
            translated_text = response_data["choices"][0]["message"]["content"]
            return translated_text.strip()
        else:
            print("❌ Error: API response structure is not as expected or lacks translated content.")
            print(f"   Response details: {response_data}") 
            return "Error processing API response"

    except requests.exceptions.Timeout:
        print(f"\n❌ Error: Request to API timed out after 180 seconds.")
        return f"Translation error: Timeout"
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error during communication with API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"   API error details (JSON): {e.response.json()}")
            except ValueError: 
                print(f"   API error details (text): {e.response.text}")
        return f"Translation error: {e}"
    except Exception as e: 
        print(f"\n❌ An unexpected error occurred during translation: {e}")
        return f"Translation error: {e}"


def main():
    print_header("PDF Translation Script with WebAI-to-API")
    
    print("⚙️ Reading configuration...")
    api_url, api_model, font_name, prompt_template = read_api_config()
    
    if not api_url or not api_model:
        print("\n❌ Critical Error: API URL or Model is missing from config. Script cannot proceed with translation.")
        print(f"   Please check your '{CONFIG_FILENAME}' file.")
        print_separator("=")
        return

    print(f"   API URL: {api_url}")
    print(f"   API Model: {api_model}")
    print(f"   Font Name: {font_name}")
    print(f"   Prompt Template (first 80 chars): {prompt_template[:80].replace(chr(10), ' ')}...") # Show a snippet
    print("✅ Configuration loaded.")

    print_header("Input Files & Languages")
    pdf_path = input("➡️ Please enter the full path to the PDF file: ").strip()
    if not (pdf_path.lower().endswith(".pdf")):
        print("❌ Error: The entered file is not a PDF file.")
        print_separator("=")
        return
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found at path '{pdf_path}'.")
        print_separator("=")
        return
    print(f"   PDF File: '{pdf_path}'")

    source_language = input(f"➡️ Please enter the source language of the pdf (e.g., English, German, default: English): ").strip()
    if not source_language:
        source_language = "English" 
        print(f"   ℹ️ No source language entered. Defaulting to '{source_language}'.")
    else:
        print(f"   Source Language: '{source_language}'")


    target_language = input(f"➡️ Please enter the target language for translation (e.g., English, Farsi, default: Farsi): ").strip()
    if not target_language:
        target_language = "Farsi"
        print(f"   ℹ️ No target language entered. Defaulting to '{target_language}'.")
    else:
        print(f"   Target Language: '{target_language}'")
        
    print_header("Phase 1: PDF Text Extraction")
    page_texts = extract_text_from_pdf(pdf_path)

    if page_texts is None:
        print("\n❌ Text extraction from PDF failed. Script stopped.")
        print_separator("=")
        return
    
    if not any(pt.strip() for pt in page_texts if pt): # Check if any page has actual text
        print("\n⚠️ No text content found in the PDF to translate. The PDF might be image-based or empty.")
        print_separator("=")
        return
    
    print(f"\n✅ Successfully extracted text from {sum(1 for pt in page_texts if pt and pt.strip())} non-empty page(s).")

    print_header(f"Phase 2: Translation ({source_language} to {target_language})")
    print(f"🌐 Starting translation process for {len(page_texts)} page(s) using model '{api_model}'...")
    translated_page_data = []

    for i, text_content in enumerate(tqdm(page_texts, desc=f"🔁 Translating pages", unit="page")):
        if not text_content or not text_content.strip(): 
            translated_page_data.append({'original': "", 'translated': ""})
            # print(f"   Skipping empty page {i+1}.") # Optional: more verbose logging
            continue

        translated_text = translate_text_via_api(text_content, api_url, api_model, target_language, source_language, prompt_template)
        
        translated_page_data.append({'original': text_content, 'translated': translated_text})
    
    print("\n✅ Translation of all pages completed.")

    print_header("Phase 3: Document Generation")
    original_pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    create_translation_document(original_pdf_name, translated_page_data, source_language, target_language, font_name)
    
    print_header("Script Finished")
    print("🎉 PDF Translation Script has completed its execution.")
    print_separator("=")

if __name__ == "__main__":
    main()
