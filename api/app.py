
import math
import os
import re
import tempfile
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path, pdfinfo_from_path
from pdf2image.exceptions import (
    PDFPageCountError,
    PDFPopplerTimeoutError,
    PDFSyntaxError,
)
from monocr import MonOCR
from PIL import Image, UnidentifiedImageError

# Demo server limits. Uploads past MAX_UPLOAD_MB are rejected with 413 before
# they reach a handler; PDFs past MAX_PDF_PAGES are rejected before rasterising.
MAX_UPLOAD_MB = 20
MAX_PDF_PAGES = 20
# PDF pages render at PDF_DPI (pdf2image's default; A4 is 1654x2339 px). A page
# whose longest side would exceed MAX_PAGE_PX at that resolution (20 in, e.g. a
# declared 200 in page that would render ~40000 px) is rejected before rendering.
PDF_DPI = 200
MAX_PAGE_PX = 4000
# Seconds allowed for pdfinfo and for rendering all pages; poppler is killed after.
PDFINFO_TIMEOUT_S = 10
PDF_RENDER_TIMEOUT_S = 60
PDF_UNREADABLE = "Could not read the PDF (it may be corrupt or password-protected)"
_PAGE_SIZE_KEY = re.compile(r"^Page\s+(\d+) size$")
_PAGE_SIZE_VALUE = re.compile(r"^([\d.]+) x ([\d.]+) pts")

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

def oversized_page(info, last_page):
    """Return the first page number in 1..last_page that would render past
    MAX_PAGE_PX, or that pdfinfo gave no size for; None if every page fits.

    Sizes come from pdfinfo, which reports the crop box, so rendering must use
    use_cropbox=True to draw the same box that was checked."""
    sizes = {}
    for key, value in info.items():
        k = _PAGE_SIZE_KEY.match(key)
        v = k and _PAGE_SIZE_VALUE.match(str(value))
        if v:
            sizes[int(k.group(1))] = max(float(v.group(1)), float(v.group(2)))
    for page in range(1, last_page + 1):
        longest_pts = sizes.get(page)
        if longest_pts is None or math.ceil(longest_pts / 72 * PDF_DPI) > MAX_PAGE_PX:
            return page
    return None

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
        except UnidentifiedImageError:
            return jsonify({"error": "Could not read the image"}), 400
        except Exception:
            app.logger.exception("OCR failed for an uploaded image")
            return jsonify({"error": "Internal error while processing the image"}), 500
            
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
            info = pdfinfo_from_path(
                temp_pdf.name, first_page=1, last_page=MAX_PDF_PAGES,
                timeout=PDFINFO_TIMEOUT_S,
            )
            page_count = info["Pages"]
            if page_count > MAX_PDF_PAGES:
                return jsonify({
                    "error": f"PDF has {page_count} pages; the limit is {MAX_PDF_PAGES}"
                }), 400
            big_page = oversized_page(info, page_count)
            if big_page is not None:
                return jsonify({
                    "error": f"Page {big_page} is too large to render "
                             f"(limit {MAX_PAGE_PX} px on the longest side at {PDF_DPI} dpi)"
                }), 400
            # Convert PDF to images; last_page bounds rasterising even if the
            # page count above was wrong.
            images = convert_from_path(
                temp_pdf.name, dpi=PDF_DPI, first_page=1, last_page=MAX_PDF_PAGES,
                use_cropbox=True, timeout=PDF_RENDER_TIMEOUT_S,
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
    except (PDFPageCountError, PDFSyntaxError):
        return jsonify({"error": PDF_UNREADABLE}), 400
    except PDFPopplerTimeoutError:
        return jsonify({"error": "PDF took too long to read or render"}), 400
    except Exception:
        app.logger.exception("OCR failed for an uploaded PDF")
        return jsonify({"error": "Internal error while processing the PDF"}), 500

if __name__ == '__main__':
    # Loopback only by default. The Werkzeug debugger runs arbitrary code for
    # whoever reaches it, so it is off unless FLASK_DEBUG=1 is set explicitly.
    host = os.environ.get('HOST', '127.0.0.1')
    debug = os.environ.get('FLASK_DEBUG') == '1'
    app.run(host=host, port=5000, debug=debug)
