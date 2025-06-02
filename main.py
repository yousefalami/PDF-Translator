# -*- coding: utf-8 -*-
import os
import configparser
import requests
import pdfplumber
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from tqdm import tqdm

# --- Functions related to file and document processing ---

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from each page of a PDF file.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at path '{pdf_path}'.")
        return None
    
    page_texts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Processing {len(pdf.pages)} pages from PDF...")
            for i, page in enumerate(tqdm(pdf.pages, desc="Extracting text from PDF")):
                text = page.extract_text()
                page_texts.append(text if text else "") 
        return page_texts
    except Exception as e:
        print(f"Error during text extraction from PDF: {e}")
        return None

def create_translation_document(original_pdf_name, page_data, target_language, output_folder="translated_documents"):
    """
    Creates a Word document with two-column tables for original and translated text.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    doc = Document()
    doc.add_heading(f"Book Translation: {original_pdf_name}", level=1)
    doc.add_paragraph(f"Original Language: Persian\nTarget Language: {target_language}")
    doc.add_paragraph("\n")

    for i, data in enumerate(tqdm(page_data, desc="Creating Word document")):
        original_text = data['original']
        translated_text = data['translated']

        doc.add_heading(f"Page {i + 1}", level=2)
        
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid' 

        table.columns[0].width = Inches(3.5)
        table.columns[1].width = Inches(3.5)

        hdr_cells = table.rows[0].cells
        
        cell_original_hdr = hdr_cells[0]
        p_original_hdr = cell_original_hdr.paragraphs[0]
        p_original_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run_original_hdr = p_original_hdr.add_run('Original Text (Persian)')
        run_original_hdr.font.name = 'B Nazanin' 
        run_original_hdr.font.size = Pt(12)
        run_original_hdr.bold = True
        
        cell_translated_hdr = hdr_cells[1]
        p_translated_hdr = cell_translated_hdr.paragraphs[0]
        if target_language.lower() in ['arabic', 'urdu', 'hebrew', 'persian', 'farsi']:
             p_translated_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
             p_translated_hdr.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run_translated_hdr = p_translated_hdr.add_run(f'Translation ({target_language})')
        run_translated_hdr.font.size = Pt(12)
        run_translated_hdr.bold = True

        row_cells = table.add_row().cells
        
        p_original = row_cells[0].paragraphs[0]
        p_original.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run_original = p_original.add_run(original_text if original_text else " ")
        run_original.font.name = 'B Nazanin' 
        run_original.font.size = Pt(11)
        
        p_translated = row_cells[1].paragraphs[0]
        if target_language.lower() in ['arabic', 'urdu', 'hebrew', 'persian', 'farsi']: 
            p_translated.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else: 
            p_translated.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run_translated = p_translated.add_run(translated_text if translated_text else " ")
        run_translated.font.size = Pt(11)

        if i < len(page_data) - 1: 
            doc.add_page_break()

    output_filename = os.path.join(output_folder, f"{original_pdf_name}_translated_to_{target_language}.docx")
    try:
        doc.save(output_filename)
        print(f"\nTranslated document successfully saved at '{output_filename}'.")
    except Exception as e:
        print(f"Error saving Word file: {e}")

# --- Sections related to API and main execution ---

def read_api_config(filename='config.ini'):
    """
    Reads API information (URL and Model) from the config.ini file.
    """
    if not os.path.exists(filename):
        print(f"Error: Config file '{filename}' not found.")
        print("Please create a config.ini file according to the instructions and place the url and model values in the [API] section.")
        return None, None

    config = configparser.ConfigParser()
    config.read(filename)
    try:
        api_url = config['API']['url']
        api_model = config['API']['model'] 
        return api_url, api_model
    except KeyError as e:
        print(f"Error: Key {e} not found in the [API] section of '{filename}'. Make sure 'url' and 'model' are defined.")
        return None, None
    except Exception as e:
        print(f"Error reading config file '{filename}': {e}")
        return None, None

def translate_text_via_api(text_to_translate, api_url, model_name, target_language="English", source_language="Persian"):
    """
    Translates text using the specified API.
    This function is customized for an API without a key requirement and with an adjustable model.
    """
    if not text_to_translate.strip():
        return "" 

    headers = {
        'Content-Type': 'application/json'
        # No need for Authorization header, as WebAI-to-API handles authentication itself
    }

    translation_prompt = f"Translate the following {source_language} text to {target_language}. Only return the translated text, without any introductory phrases or explanations:\n\n{text_to_translate}"

    payload = {
        "model": model_name, 
        "messages": [{"role": "user", "content": translation_prompt}]
    }

    try:
        print(f"\nSending translation request for a part of the text to: {api_url} with model: {model_name}")
        response = requests.post(api_url, headers=headers, json=payload, timeout=60) 
        response.raise_for_status()  # Raises an exception if the status code is an error
        
        response_data = response.json()

        # Extract translated text from the API response structure
        if response_data.get("choices") and \
           isinstance(response_data["choices"], list) and \
           len(response_data["choices"]) > 0 and \
           response_data["choices"][0].get("message") and \
           response_data["choices"][0]["message"].get("content"):
            
            translated_text = response_data["choices"][0]["message"]["content"]
            return translated_text.strip()
        else:
            print("Error: API response structure is not as expected or lacks translated content.")
            print(f"Response details: {response_data}") # Print response for debugging
            return "Error processing API response"

    except requests.exceptions.Timeout:
        print(f"\nError: Request to API timed out after {60} seconds (Timeout).")
        return f"Translation error: Timeout"
    except requests.exceptions.RequestException as e:
        print(f"\nError during communication with API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"API error details: {e.response.json()}")
            except ValueError: # If response is not JSON
                print(f"API error details (text): {e.response.text}")
        return f"Translation error: {e}"
    except Exception as e: 
        print(f"\nAn unexpected error occurred during translation: {e}")
        return f"Translation error: {e}"


def main():
    print("\n--- Starting PDF Translation Script with WebAI-to-API ---\n")
    
    api_url, api_model = read_api_config() 
    if not api_url or not api_model:
        print("Script stopped due to missing complete API information (url and model) in config.")
        return

    print(f"API URL read from config: {api_url}")
    print(f"API Model read from config: {api_model}")

    print("\n--- Running Translation ---\n")

    pdf_path = input("Please enter the full path to the PDF file: ").strip()
    if not (pdf_path.lower().endswith(".pdf")):
        print("Error: The entered file is not a PDF file.")
        return
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at path '{pdf_path}'.")
        return

    target_language = input("Please enter the target language for translation (e.g., English, Arabic, French): ").strip()
    if not target_language:
        print("Warning: Target language not entered. Defaulting to 'English'.")
        target_language = "English" 

    source_language = "Persian" 

    page_texts = extract_text_from_pdf(pdf_path)

    if page_texts is None:
        print("Text extraction from PDF failed. Script stopped.")
        return
    
    if not any(pt.strip() for pt in page_texts): 
        print("No text found in the PDF to translate.")
        return

    translated_page_data = []
    print(f"\nStarting translation process for {len(page_texts)} pages from {source_language} to {target_language} with model {api_model}...")

    for i, text in enumerate(tqdm(page_texts, desc="Translating pages")):
        if not text.strip(): 
            translated_page_data.append({'original': "", 'translated': ""})
            continue

        translated_text = translate_text_via_api(text, api_url, api_model, target_language, source_language)
        
        translated_page_data.append({'original': text, 'translated': translated_text})
        
    original_pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    create_translation_document(original_pdf_name, translated_page_data, target_language)
    
    print("\n--- End of PDF Translation Script ---")

if __name__ == "__main__":
    main()
