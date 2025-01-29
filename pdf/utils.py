import pyotp
from PIL import Image
import os
import time
from pdf2image import convert_from_path
import zipfile


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


#     try:
#         images = convert_from_path(pdf_path)
#         # Ensure that images is a list of image objects, not a list of lists
#         if isinstance(images, list):
#             print(f"Total images: {len(images)}")
#         else:
#             print("Error: Expected a list of images, got:", type(images))

#     except Exception as e:
#         print("An unexpected error occurred:", e)

# pdf_path = r"C:\Users\HP\Documents\Django main Projects\pdfapi\example.pdf"
# pdf_to_image(pdf_path)

# def convert_pdf_to_images(pdf_file_path, output_folder):
#     """
#     Converts a PDF file into individual image files, one per page.

#     :param pdf_file_path: Path to the input PDF file
#     :param output_folder: Folder to save the output images
#     :return: List of paths to the generated image files
#     """
#     if not hasattr(pdf_file, 'read'):
#         # Open the file if it's a file path
#         with open(pdf_file, 'rb') as f:
#             pdf_file = BytesIO(f.read())
#     else:
#         # Use BytesIO for Django UploadedFile objects
#         pdf_file = BytesIO(pdf_file.read())
    
#     pdf_reader = PdfReader(pdf_file)
#     output_files = []

#     for page_num, page in enumerate(pdf_reader.pages):
#         pdf_writer = PdfWriter()
#         pdf_writer.add_page(page)

#         temp_pdf_path = os.path.join(output_folder, f'page_{page_num + 1}.pdf')
#         with open(temp_pdf_path, 'wb') as temp_pdf:
#             pdf_writer.write(temp_pdf)

#         # Convert the single-page PDF to an image
#         image_path = os.path.join(output_folder, f'page_{page_num + 1}.png')
#         img = Image.open(temp_pdf_path)
#         img.save(image_path)
#         output_files.append(image_path)

#         # Remove the temporary single-page PDF
#         os.remove(temp_pdf_path)

#     return output_files



