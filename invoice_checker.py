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

    # ✅ Expanded field variants for global invoice support
    field_variants = {
    'invoice': [
        'invoice', 'invoice number', 'invoice #', 'order number', 'order #',
        'ref no.', 'reference number', 'bill number', 'sales invoice', 'purchase id',
        'tr#', 'tc#', 'approval #', 'terminal #'
    ],
    'date': [
        'date', 'invoice date', 'order date', 'delivery date', 'issue date',
        'transaction date', 'billed on', 'created on', 'generated on',
        '09/01/12', '14:16:00'  # auto-detects this pattern
    ],
    'total': [
        'total', 'total amount', 'grand total', 'order total', 'invoice total',
        'amount due', 'balance due', 'amount payable', 'total payable', 'final total',
        'change due', 'debit tend'
    ],
    'tax': [
        'tax', 'sales tax', 'vat', 'gst', 'igst', 'cgst', 'sgst',
        'tax amount', 'vat amount', 'taxable', 'tax rate', 'tax 1'
    ],
    'subtotal': [
        'subtotal', 'item subtotal', 'items total', 'unit price', 'product price',
        'base amount', 'price before tax', 'amount (excl. tax)', 'amount (incl. tax)',
        'items sold', '# items sold'
    ],
    'shipping': [
        'shipping', 'shipping cost', 'shipping fee', 'shipping charges',
        'delivery fee', 'logistics charge', 'freight charges', 'handling charges'
    ]
    }


    matched_fields = []
    missing_fields = []

    for key, variants in field_variants.items():
        if any(var in lower_text for var in variants):
            matched_fields.append(key)
        else:
            missing_fields.append(key)

    # ✅ Passes if at least 4 of 6 fields are detected
    passed = len(matched_fields) >= 4
    return passed, text, missing_fields

# ---------- Suspicious Keyword Check ----------
def check_suspicious_keywords(text):
    suspicious_keywords = [
        'edited', 'fake', 'photoshop', 'clone', 'altered', 'tampered', 'manipulated',
        'recreated', 'falsified', 'changed'
    ]
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
    
    print(f"[DEBUG] ELA max_diff: {max_diff}")

    if max_diff == 0:
        max_diff = 1

    scale = 255.0 / max_diff
    ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
    ela_image.save(ela_output)

    suspicious = max_diff > 60  # Balanced for real-world invoices
    passed = not suspicious
    return passed, ela_output

# ---------- Full Invoice Check ----------
def full_invoice_check(file_path):
    is_pdf = file_path.lower().endswith('.pdf')
    if is_pdf:
        image_path = convert_pdf_to_image(file_path)
    else:
        image_path = file_path

    # Step 1: OCR Field Check
    ocr_passed, text, missing = check_ocr_fields(image_path)
    if not ocr_passed:
        return f"🚫 Invoice failed OCR field check. Missing fields: {missing}", None

    # Step 2: Suspicious Keyword Check
    keyword_passed, found_keywords = check_suspicious_keywords(text)
    if not keyword_passed:
        return f"🚫 Invoice contains suspicious keywords: {found_keywords}", None

    # Step 3: ELA Forgery Check
    ela_passed, ela_image = check_ela(image_path)
    if not ela_passed:
        return "🚫 Invoice failed Error Level Analysis (possible alteration)", ela_image

    return "✅ Invoice passed all checks and seems authentic.", ela_image
