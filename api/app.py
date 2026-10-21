
import os
import tempfile
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path, pdfinfo_from_path
from monocr import MonOCR
from PIL import Image

# Demo server limits. Uploads past MAX_UPLOAD_MB are rejected with 413 before
# they reach a handler; PDFs past MAX_PDF_PAGES are rejected before rasterising.
MAX_UPLOAD_MB = 20
MAX_PDF_PAGES = 20

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_MB * 1024 * 1024

# Initialize OCR model
try:
    ocr_engine = MonOCR()
    print("OCR ready")
except Exception as e:
    print(f"OCR init failed: {e}")
    ocr_engine = None

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(413)
def too_large(_e):
    return jsonify({"error": f"File too large (limit {MAX_UPLOAD_MB} MB)"}), 413

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "model_loaded": ocr_engine is not None})

@app.route('/ocr/image', methods=['POST'])
def ocr_image():
    if not ocr_engine:
        return jsonify({"error": "OCR engine not initialized"}), 500
        
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and allowed_file(file.filename):
        try:
            # Process image directly from stream/temp
            img = Image.open(file.stream)
            # Run prediction
            text = ocr_engine.read_text(img)
            return jsonify({
                "filename": file.filename,
                "text": text
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/ocr/pdf', methods=['POST'])
def ocr_pdf():
    if not ocr_engine:
        return jsonify({"error": "OCR engine not initialized"}), 500
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Invalid or missing PDF file"}), 400

    try:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=True) as temp_pdf:
            file.save(temp_pdf.name)
            page_count = pdfinfo_from_path(temp_pdf.name)["Pages"]
            if page_count > MAX_PDF_PAGES:
                return jsonify({
                    "error": f"PDF has {page_count} pages; the limit is {MAX_PDF_PAGES}"
                }), 400
            # Convert PDF to images; last_page bounds rasterising even if the
            # page count above was wrong.
            images = convert_from_path(
                temp_pdf.name, first_page=1, last_page=MAX_PDF_PAGES
            )
            
            results = []
            for i, page_img in enumerate(images):
                text = ocr_engine.read_text(page_img)
                results.append({
                    "page": i + 1,
                    "text": text
                })
                
            return jsonify({
                "filename": file.filename,
                "pages": len(results),
                "results": results
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Loopback only by default. The Werkzeug debugger runs arbitrary code for
    # whoever reaches it, so it is off unless FLASK_DEBUG=1 is set explicitly.
    host = os.environ.get('HOST', '127.0.0.1')
    debug = os.environ.get('FLASK_DEBUG') == '1'
    app.run(host=host, port=5000, debug=debug)
