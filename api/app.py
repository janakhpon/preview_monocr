
import os
import tempfile
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
from monocr import MonOCR
from PIL import Image

import torch

app = Flask(__name__)

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
            # Convert PDF to images
            images = convert_from_path(temp_pdf.name)
            
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
    app.run(host='0.0.0.0', port=5000, debug=True)
