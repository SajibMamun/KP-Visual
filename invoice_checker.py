from pdf2image import convert_from_path
import pytesseract
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
import os

# ---------- Configuration ----------
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\poppler-24.08.0\Library\bin'  # Update this to your actual Poppler path

# ---------- PDF to Image ----------
def convert_pdf_to_image(pdf_path):
    images = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)
    image_path = pdf_path.replace(".pdf", "_page1.jpg")
    images[0].save(image_path, 'JPEG')
    return image_path

# ---------- OCR Field Check ----------
def check_ocr_fields(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(thresh, config=custom_config)
    lower_text = text.lower()

    # Extended matching to handle different invoice templates
    field_variants = {
        'invoice': ['invoice', 'order number', 'order #'],
        'date': ['date', 'placed on', 'paid on', 'order placed'],
        'total': ['total', 'grand total', 'order total', 'total amount'],
        'tax': ['tax', 'estimated tax', 'sales tax'],
        'subtotal': ['subtotal', 'item(s) subtotal', 'item price'],
        'shipping': ['shipping', 'handling', 'shipping & handling']
    }

    matched_fields = []
    missing_fields = []

    for key, variants in field_variants.items():
        if any(var in lower_text for var in variants):
            matched_fields.append(key)
        else:
            missing_fields.append(key)

    # Allow if at least 4 out of 6 key fields are present
    passed = len(matched_fields) >= 4

    return passed, text, missing_fields

# ---------- Suspicious Keyword Check ----------
def check_suspicious_keywords(text):
    suspicious_keywords = ['edited', 'fake', 'photoshop', 'clone', 'altered']
    found = [kw for kw in suspicious_keywords if kw in text.lower()]
    passed = len(found) == 0
    return passed, found

# ---------- Error Level Analysis (ELA) ----------
def check_ela(image_path, quality=90):
    ela_output = image_path.replace(".jpg", "_ela.jpg")
    original = Image.open(image_path).convert('RGB')
    temp_jpg = image_path.replace(".jpg", "_temp.jpg")
    original.save(temp_jpg, 'JPEG', quality=quality)

    resaved = Image.open(temp_jpg)
    ela_image = ImageChops.difference(original, resaved)

    extrema = ela_image.getextrema()
    max_diff = max([e[1] for e in extrema])
    
    # Debug: print ELA difference value
    print(f"[DEBUG] ELA max_diff: {max_diff}")

    if max_diff == 0:
        max_diff = 1

    scale = 255.0 / max_diff
    ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
    ela_image.save(ela_output)

    # Relaxed threshold for compressed images
    suspicious = max_diff > 50  # Increased threshold from 35 to 50

    passed = not suspicious
    return passed, ela_output

# ---------- Full Invoice Check Pipeline ----------
def full_invoice_check(file_path):
    is_pdf = file_path.lower().endswith('.pdf')
    if is_pdf:
        image_path = convert_pdf_to_image(file_path)
    else:
        image_path = file_path

    # 1. OCR Field Check
    ocr_passed, text, missing = check_ocr_fields(image_path)
    if not ocr_passed:
        return f"🚫 Invoice failed OCR field check. Missing fields: {missing}", None

    # 2. Suspicious Keyword Check
    keyword_passed, found_keywords = check_suspicious_keywords(text)
    if not keyword_passed:
        return f"🚫 Invoice contains suspicious keywords: {found_keywords}", None

    # 3. ELA Forgery Check
    ela_passed, ela_image = check_ela(image_path)
    if not ela_passed:
        return "🚫 Invoice failed Error Level Analysis (possible alteration)", ela_image

    return "✅ Invoice passed all checks and seems authentic.", ela_image
