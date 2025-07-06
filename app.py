import os
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from invoice_checker import full_invoice_check
from pathlib import Path
import shutil

app = FastAPI()

# ---------- Configuration ----------
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ---------- Helpers ----------
def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clear_upload_folder():
    folder = Path(UPLOAD_FOLDER)
    for file in folder.iterdir():
        if file.is_file():
            file.unlink()

# ---------- Web Route ----------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "result": None, "image": None, "ela_image": None})

@app.post("/", response_class=HTMLResponse)
async def upload_invoice_web(request: Request, invoice: UploadFile = File(...)):
    result = None
    image_path = None
    ela_image = None

    if invoice and allowed_file(invoice.filename):
        clear_upload_folder()

        filename = invoice.filename
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(invoice.file, buffer)

        result, ela_image = full_invoice_check(save_path)

        image_path = save_path.replace("\\", "/")
        if ela_image:
            ela_image = ela_image.replace("\\", "/")
    else:
        result = "🚫 Unsupported file format. Please upload a PDF or image."

    return templates.TemplateResponse("index.html", {
        "request": request,
        "result": result,
        "image": image_path,
        "ela_image": ela_image
    })

# ---------- API Route ----------
@app.post("/api/check_invoice")
async def check_invoice_api(invoice: UploadFile = File(...)):
    if not invoice or not allowed_file(invoice.filename):
        raise HTTPException(status_code=400, detail="Unsupported or missing file.")

    clear_upload_folder()
    filename = invoice.filename
    save_path = os.path.join(UPLOAD_FOLDER, filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(invoice.file, buffer)

    result_text, ela_image_path = full_invoice_check(save_path)

    save_path = save_path.replace("\\", "/")
    if ela_image_path:
        ela_image_path = ela_image_path.replace("\\", "/")

    status = "authentic" if "passed all checks" in result_text.lower() else "altered"

    return JSONResponse({
        "status": status,
        "message": result_text,
        "invoice_image": save_path,
        "ela_image": ela_image_path
    })
