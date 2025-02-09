import pyotp
from PIL import Image
import os
import time
from pdf2image import convert_from_path
import zipfile
import subprocess
from pdf2docx import Converter
import pandas as pd
import fitz
import PyPDF2
import pdfplumber
from fpdf import FPDF

def generate_otp():
    totp = pyotp.TOTP(pyotp.random_base32(), interval=300)
    return totp.now()

def verify_otp(otp, user_otp):
    return otp == user_otp

def convert_images_to_pdf(image_files, output_pdf_path):
    timestamp = str(int(time.time()))
    output_pdf_path = output_pdf_path.replace('output.pdf', f'output_{timestamp}.pdf')
    images = []
    for image_file in image_files:
        img = Image.open(image_file)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        images.append(img)

    if images:
        images[0].save(output_pdf_path, save_all=True, append_images=images[1:])
        return output_pdf_path

def convert_pdf_to_images(pdf_file_path, output_folder):
    try:
        images = convert_from_path(pdf_file_path)
        output_files = []
        for i, image in enumerate(images):
            output_path = os.path.join(output_folder, f'page_{i + 1}.png')
            image.save(output_path, 'PNG')
            output_files.append(output_path)
            
        if len(images) == 1:
            return {"type": "single", "file_path": output_files[0]}
        else:
            zip_file_path = os.path.join(output_folder, 'converted_images.zip')
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for file in output_files:
                    zipf.write(file, os.path.basename(file))
            return {"type": "zip", "file_path": zip_file_path}
        
    except Exception as e:
        print("An unexpected error occurred:", e)
        return None

def convert_word_to_pdf(word_file_path, output_folder):
    output_pdf_path = os.path.join(output_folder, os.path.splitext(os.path.basename(word_file_path))[0] + ".pdf")

    try:
        command = ["soffice", "--headless", "--convert-to", "pdf", "--outdir", output_folder, word_file_path]
        subprocess.run(command, check=True)
        return output_pdf_path
    except Exception as e:
        print("Error converting Word to PDF:", e)
        return None

def convert_pdf_to_word(pdf_file_path, output_folder):
    output_docx_path = os.path.join(output_folder, os.path.splitext(os.path.basename(pdf_file_path))[0] + ".docx")

    try:
        converter = Converter(pdf_file_path)
        converter.convert(output_docx_path, start=0, end=None)
        converter.close()
        return output_docx_path
    except Exception as e:
        print("Error converting PDF to Word:", e)
        return None

def convert_excel_to_pdf(excel_file_path, output_folder):
    try:
        df = pd.read_excel(excel_file_path)
        output_pdf_path = os.path.join(output_folder, os.path.splitext(os.path.basename(excel_file_path))[0] + ".pdf")

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for index, row in df.iterrows():
            pdf.cell(200, 10, txt=str(row.values), ln=True, align='L')

        pdf.output(output_pdf_path)
        return output_pdf_path
    except Exception as e:
        print("Error converting Excel to PDF:", e)
        return None
    
    
def convert_pdf_to_excel(pdf_file_path, output_folder):
    try:
        tables = []
        with pdfplumber.open(pdf_file_path) as pdf:
            for page in pdf.pages:
                extracted_table = page.extract_table()
                if extracted_table:
                    tables.extend(extracted_table)

        if tables:
            df = pd.DataFrame(tables)
            output_excel_path = os.path.join(output_folder, os.path.splitext(os.path.basename(pdf_file_path))[0] + ".xlsx")
            df.to_excel(output_excel_path, index=False)
            return output_excel_path

        print("No tables found in the PDF.")
        return None

    except Exception as e:
        print("Error converting PDF to Excel:", e)
        return None

    
def compress_pdf(input_pdf_path, output_pdf_path, quality=60):
    doc = fitz.open(input_pdf_path)
    
    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]  # Image reference
            pix = fitz.Pixmap(doc, xref)  

            if pix.n > 4:  # Convert CMYK to RGB
                pix = fitz.Pixmap(fitz.csRGB, pix)

            new_image = pix.pil_save(quality=quality)  # Reduce quality
            doc.update_image(xref, stream=new_image)

    doc.save(output_pdf_path)
    doc.close()
    return output_pdf_path

def merge_pdfs(pdf_list, output_pdf_path):
    """Merge multiple PDFs into one."""
    merger = PyPDF2.PdfMerger()

    for pdf in pdf_list:
        merger.append(pdf)

    merger.write(output_pdf_path)
    merger.close()
    
    return output_pdf_path

def split_pdf(input_pdf_path, output_folder, page_ranges):
    """Split a PDF into specified pages and save each as a separate file."""
    os.makedirs(output_folder, exist_ok=True)

    with open(input_pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        num_pages = len(reader.pages)

        split_files = []
        pages_to_extract = set()

        # Parse the page range input (e.g., "1-3, 5, 7-10")
        for part in page_ranges.split(","):
            part = part.strip()
            if "-" in part:
                start, end = map(int, part.split("-"))
                pages_to_extract.update(range(start, end + 1))
            else:
                pages_to_extract.add(int(part))

        for i in sorted(pages_to_extract):
            if i > num_pages or i < 1:
                continue  # Skip invalid page numbers

            writer = PyPDF2.PdfWriter()
            writer.add_page(reader.pages[i - 1])  # Adjust for zero-based index

            output_pdf_path = os.path.join(output_folder, f"page_{i}.pdf")
            with open(output_pdf_path, "wb") as output_file:
                writer.write(output_file)

            split_files.append(output_pdf_path)

    return split_files
