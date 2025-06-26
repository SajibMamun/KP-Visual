import os
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from invoice_checker import full_invoice_check

app = Flask(__name__)

# ---------- Configuration ----------
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------- Allowed File Types ----------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- Upload Folder Cleaner ----------
def clear_upload_folder():
    folder = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

# ---------- Web Route ----------
@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    ela_image = None
    image_path = None

    if request.method == 'POST':
        file = request.files.get('invoice')
        if file and allowed_file(file.filename):
            clear_upload_folder()  # 🧹 Clean before saving new

            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)

            result, ela_image = full_invoice_check(image_path)

            # Ensure image paths are relative for HTML display
            if image_path:
                image_path = image_path.replace("\\", "/")
            if ela_image:
                ela_image = ela_image.replace("\\", "/")
        else:
            result = "🚫 Unsupported file format. Please upload a PDF or image."

    return render_template('index.html', result=result, image=image_path, ela_image=ela_image)

# ---------- API Route ----------
@app.route('/api/check_invoice', methods=['POST'])
def check_invoice_api():
    if 'invoice' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['invoice']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    clear_upload_folder()

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    result_text, ela_image_path = full_invoice_check(filepath)

    if filepath:
        filepath = filepath.replace("\\", "/")
    if ela_image_path:
        ela_image_path = ela_image_path.replace("\\", "/")

    status = "authentic" if "passed all checks" in result_text.lower() else "altered"

    return jsonify({
        "status": status,
        "message": result_text,
        "invoice_image": filepath,
        "ela_image": ela_image_path
    })

# ---------- Run Server ----------
if __name__ == '__main__':
    app.run(debug=True)
