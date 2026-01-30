# MonOCR Preview

A Demo repo with jupyter notebook and flask api for the Mon Language OCR package.

## Requirements

- Python 3.10+
- uv (package manager)
- poppler-utils (for PDF processing)

## Setup

Initialize the environment and install dependencies:

```bash
uv sync --refresh
```

### Updating `monocr`

To force install the latest version of the OCR engine:

```bash
uv add --force-reinstall monocr
```

## Usage

### 1. Jupyter Notebook

Visualize OCR results on images and PDFs.

```bash
uv run jupyter lab notebooks/demo.ipynb
```

Place your test files in:

- `data/images/` for .png/.jpg
- `data/pdfs/` for .pdf

### 2. Flask API

Start the API server:

```bash
uv run api/app.py
```

**Endpoints:**

- `POST /ocr/image`
  - Input: Form-data `file` (image)
  - Output: JSON with detected text

- `POST /ocr/pdf`
  - Input: Form-data `file` (pdf)
  - Output: JSON with text per page

## Contact

For issues regarding the OCR accuracy, please verify the input image quality first.
For package issues, refer to the main `monocr` repository.

- [monocr](https://github.com/janakhpon/monocr)
