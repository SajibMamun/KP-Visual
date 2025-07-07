✅ Step 1: Download and Install Tesseract OCR <br/><br/>
Go to the official installer page: <br/>
🔗 https://github.com/tesseract-ocr/tesseract <br/><br/>

Scroll down to the Windows Installer section and download from this direct link (from a trusted source):<br/>
🔗 https://github.com/UB-Mannheim/tesseract/wiki <br/>

Download the latest .exe file (e.g., tesseract-ocr-w64-setup-v5.3.3.20231005.exe)<br/><br/>

Install it to a known path (default is):<br/>
C:\Program Files\Tesseract-OCR\ <br/><br/>



✅ Step 2: Set Tesseract Path in Python <br/><br/>
Add this line in your Python script before calling pytesseract:<br/>
import pytesseract<br/>
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'<br/><br/>


🧱 Step 3: Install Poppler (PDF renderer used by pdf2image)<br/>
🔗 Windows users:<br/><br/>
Download from:<br/>
https://github.com/oschwartz10612/poppler-windows/releases/<br/><br/>

Unzip it somewhere like:<br/>
C:\poppler-24.08.0\Library\bin<br/>
Add this path to your Windows Environment Variables > PATH<br/>

<br/><br/>


Step 4:<br/><br/>
pip install requirements.txt <br/><br/>

fastapi </br>
uvicorn </br>
jinja2 </br>
python-multipart </br>
pdf2image </br>
pytesseract </br>
opencv-python </br>
Pillow </br>

<br/><br/><br/><br/>

![image](https://github.com/user-attachments/assets/13f2e70f-aeff-4e31-a4b6-4becf826248c)






