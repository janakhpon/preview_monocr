# MonOCR Preview

> **Superseded, and broken on a fresh install.** This demo is pinned to `monocr`
> 0.1.17, which downloads `monocr.ckpt` from the main branch of the
> [janakhpon/monocr](https://huggingface.co/janakhpon/monocr) model repo. That file
> is no longer there, so on a machine without a cached copy the model fails to
> load: the notebook prints the init error and the API answers every OCR request
> with HTTP 500. For Mon OCR today, use the current
> [`monocr`](https://pypi.org/project/monocr/) package (2.x) or
> [`monocr-onnx`](https://github.com/MonDevHub/monocr-onnx).

A Demo repo with jupyter notebook and flask api for the Mon Language OCR package.

## Requirements

- Python 3.11+
- uv (package manager)
- poppler-utils (for PDF processing)

## Setup

Initialize the environment and install dependencies:

```bash
uv sync --refresh
```

### The `monocr` version

`pyproject.toml` pins `monocr==0.1.17`, and `uv sync` installs exactly that.
Using a newer release means changing the pin.

## Usage

### 1. Jupyter Notebook

Visualize OCR results on images and PDFs.

```bash
uv run jupyter lab notebooks/demo.ipynb
```

Place your test files in:

- `data/images/` for .png/.jpg
- `data/pdfs/` for .pdf

The sample files already there (the images in `data/images/` and
`data/pdfs/party_mission.pdf`) have no recorded source or licence. The MIT
licence in this repo covers the code, not them.

### 2. Flask API

Start the API server:

```bash
uv run api/app.py
```

The server listens on `127.0.0.1:5000` with debug off. It is a local demo, not a
hardened service:

- `HOST=0.0.0.0 uv run api/app.py` exposes it to the network. Do that only on a
  network you trust.
- `FLASK_DEBUG=1 uv run api/app.py` turns on the Werkzeug debugger, which runs
  arbitrary code for anyone who can reach it. Never combine it with `HOST=0.0.0.0`.
- Uploads are limited to 20 MB (larger ones get HTTP 413), and PDFs to 20 pages
  (longer ones get HTTP 400).
- PDF pages render at 200 dpi (A4 is 1654 x 2339 px). A page whose longest side
  would pass 4000 px (20 in) gets HTTP 400, as does a PDF that is corrupt or
  password-protected. Reading and rendering are cut off after 10 s and 60 s.

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
