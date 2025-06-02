# -*- coding: utf-8 -*-
import os
import configparser
import requests
import pdfplumber
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from tqdm import tqdm

# --- توابع مربوط به پردازش فایل و سند ---

def extract_text_from_pdf(pdf_path):
    """
    متن را از هر صفحه یک فایل PDF استخراج می کند.
    """
    if not os.path.exists(pdf_path):
        print(f"خطا: فایل PDF در مسیر '{pdf_path}' یافت نشد.")
        return None
    
    page_texts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"در حال پردازش {len(pdf.pages)} صفحه از PDF...")
            for i, page in enumerate(tqdm(pdf.pages, desc="استخراج متن از PDF")):
                text = page.extract_text()
                page_texts.append(text if text else "") 
        return page_texts
    except Exception as e:
        print(f"خطا در هنگام استخراج متن از PDF: {e}")
        return None

def create_translation_document(original_pdf_name, page_data, target_language, output_folder="translated_documents"):
    """
    یک سند Word با جداول دو ستونی برای متن اصلی و ترجمه شده ایجاد می کند.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    doc = Document()
    doc.add_heading(f"ترجمه کتاب: {original_pdf_name}", level=1)
    doc.add_paragraph(f"زبان اصلی: فارسی\nزبان ترجمه: {target_language}")
    doc.add_paragraph("\n")

    for i, data in enumerate(tqdm(page_data, desc="ایجاد سند Word")):
        original_text = data['original']
        translated_text = data['translated']

        doc.add_heading(f"صفحه {i + 1}", level=2)
        
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid' 

        table.columns[0].width = Inches(3.5)
        table.columns[1].width = Inches(3.5)

        hdr_cells = table.rows[0].cells
        
        cell_original_hdr = hdr_cells[0]
        p_original_hdr = cell_original_hdr.paragraphs[0]
        p_original_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run_original_hdr = p_original_hdr.add_run('متن اصلی (فارسی)')
        run_original_hdr.font.name = 'B Nazanin' 
        run_original_hdr.font.size = Pt(12)
        run_original_hdr.bold = True
        
        cell_translated_hdr = hdr_cells[1]
        p_translated_hdr = cell_translated_hdr.paragraphs[0]
        if target_language.lower() in ['arabic', 'urdu', 'hebrew', 'persian', 'farsi']:
             p_translated_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
             p_translated_hdr.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run_translated_hdr = p_translated_hdr.add_run(f'ترجمه ({target_language})')
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
        print(f"\nسند ترجمه شده با موفقیت در '{output_filename}' ذخیره شد.")
    except Exception as e:
        print(f"خطا در ذخیره سازی فایل Word: {e}")

# --- بخش های مربوط به API و اجرای اصلی ---

def read_api_config(filename='config.ini'):
    """
    اطلاعات API (URL و Model) را از فایل config.ini می خواند.
    """
    if not os.path.exists(filename):
        print(f"خطا: فایل کانفیگ '{filename}' یافت نشد.")
        print("لطفاً یک فایل config.ini طبق راهنما ایجاد کنید و مقادیر url و model را در بخش [API] قرار دهید.")
        return None, None

    config = configparser.ConfigParser()
    config.read(filename)
    try:
        api_url = config['API']['url']
        api_model = config['API']['model'] 
        return api_url, api_model
    except KeyError as e:
        print(f"خطا: کلید {e} در بخش [API] فایل '{filename}' یافت نشد. مطمئن شوید 'url' و 'model' تعریف شده باشند.")
        return None, None
    except Exception as e:
        print(f"خطا در خواندن فایل کانفیگ '{filename}': {e}")
        return None, None

def translate_text_via_api(text_to_translate, api_url, model_name, target_language="English", source_language="Persian"):
    """
    متن را با استفاده از API مشخص شده ترجمه می کند.
    این تابع برای API بدون نیاز به کلید و با مدل قابل تنظیم، سفارشی شده است.
    """
    if not text_to_translate.strip():
        return "" 

    headers = {
        'Content-Type': 'application/json'
        # نیازی به هدر Authorization نیست، چون WebAI-to-API خودش احراز هویت را مدیریت می کند
    }

    translation_prompt = f"Translate the following {source_language} text to {target_language}. Only return the translated text, without any introductory phrases or explanations:\n\n{text_to_translate}"

    payload = {
        "model": model_name, 
        "messages": [{"role": "user", "content": translation_prompt}]
    }

    try:
        print(f"\nارسال درخواست ترجمه برای بخشی از متن به: {api_url} با مدل: {model_name}")
        response = requests.post(api_url, headers=headers, json=payload, timeout=60) 
        response.raise_for_status()  # اگر کد وضعیت خطا باشد، یک استثنا ایجاد می کند
        
        response_data = response.json()

        # استخراج متن ترجمه شده از ساختار پاسخ API
        if response_data.get("choices") and \
           isinstance(response_data["choices"], list) and \
           len(response_data["choices"]) > 0 and \
           response_data["choices"][0].get("message") and \
           response_data["choices"][0]["message"].get("content"):
            
            translated_text = response_data["choices"][0]["message"]["content"]
            return translated_text.strip()
        else:
            print("خطا: ساختار پاسخ API مورد انتظار نیست یا فاقد محتوای ترجمه شده است.")
            print(f"جزئیات پاسخ: {response_data}") # چاپ پاسخ برای دیباگ
            return "خطا در پردازش پاسخ API"

    except requests.exceptions.Timeout:
        print(f"\nخطا: درخواست به API در زمان {60} ثانیه منقضی شد (Timeout).")
        return f"خطا در ترجمه: Timeout"
    except requests.exceptions.RequestException as e:
        print(f"\nخطا در هنگام ارتباط با API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"جزئیات خطای API: {e.response.json()}")
            except ValueError: # اگر پاسخ JSON نباشد
                print(f"جزئیات خطای API (متن): {e.response.text}")
        return f"خطا در ترجمه: {e}"
    except Exception as e: 
        print(f"\nیک خطای پیش بینی نشده در هنگام ترجمه رخ داد: {e}")
        return f"خطا در ترجمه: {e}"


def main():
    print("--- شروع اسکریپت ترجمه PDF با WebAI-to-API ---")
    
    api_url, api_model = read_api_config() 
    if not api_url or not api_model:
        print("اسکریپت به دلیل عدم وجود اطلاعات کامل API (url و model) در کانفیگ متوقف شد.")
        return

    print(f"API URL از کانفیگ خوانده شد: {api_url}")
    print(f"API Model از کانفیگ خوانده شد: {api_model}")

    pdf_path = input("لطفاً مسیر کامل فایل PDF را وارد کنید: ").strip()
    if not (pdf_path.lower().endswith(".pdf")):
        print("خطا: فایل وارد شده یک فایل PDF نیست.")
        return
    if not os.path.exists(pdf_path):
        print(f"خطا: فایل PDF در مسیر '{pdf_path}' یافت نشد.")
        return

    target_language = input("لطفاً زبان مقصد برای ترجمه را وارد کنید (مثلاً English, Arabic, French): ").strip()
    if not target_language:
        print("هشدار: زبان مقصد وارد نشده است. به طور پیش فرض 'English' در نظر گرفته می شود.")
        target_language = "English" 

    source_language = "Persian" 

    page_texts = extract_text_from_pdf(pdf_path)

    if page_texts is None:
        print("استخراج متن از PDF ناموفق بود. اسکریپت متوقف شد.")
        return
    
    if not any(pt.strip() for pt in page_texts): 
        print("هیچ متنی برای ترجمه در PDF یافت نشد.")
        return

    translated_page_data = []
    print(f"\nشروع فرآیند ترجمه {len(page_texts)} صفحه از زبان {source_language} به {target_language} با مدل {api_model}...")

    for i, text in enumerate(tqdm(page_texts, desc="ترجمه صفحات")):
        if not text.strip(): 
            translated_page_data.append({'original': "", 'translated': ""})
            continue

        translated_text = translate_text_via_api(text, api_url, api_model, target_language, source_language)
        
        translated_page_data.append({'original': text, 'translated': translated_text})
        
    original_pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    create_translation_document(original_pdf_name, translated_page_data, target_language)
    
    print("\n--- پایان اسکریپت ترجمه PDF ---")

if __name__ == "__main__":
    main()
