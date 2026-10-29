# MonOCR Preview

A demo of the [`monocr`](https://github.com/janakhpon/monocr) package for Mon language OCR: a Jupyter
notebook that shows results on sample images and PDFs, and a small Flask API that returns the text as
JSON. It is a local demo, not a hardened service, and it has no test suite.

The demo is pinned to `monocr==0.1.17` in `pyproject.toml`, and `uv sync` installs exactly that. To try
a newer release from [PyPI](https://pypi.org/project/monocr/), change the pin.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- poppler-utils (for PDF processing)

## Setup

```bash
uv sync --refresh
uv run verify_install.py   # loads the model (downloads it on first run) and prints its device
```

## Notebook

Shows each image or PDF page next to its OCR result.

```bash
uv run jupyter lab notebooks/demo.ipynb
```

It reads every file in `data/images/` (.png, .jpg, .jpeg) and `data/pdfs/` (.pdf). Samples are
already there; add your own beside them.

## Flask API

```bash
uv run api/app.py
curl -F file=@data/images/000028.jpg http://127.0.0.1:5000/ocr/image
```

| Endpoint | Input | Output |
| --- | --- | --- |
| `GET /health` | none | `status` and whether the model loaded |
| `POST /ocr/image` | form-data `file` (.png, .jpg, .jpeg) | JSON with the detected text |
| `POST /ocr/pdf` | form-data `file` (.pdf) | JSON with the text per page |

The server listens on `127.0.0.1:5000` with debug off.

- `HOST=0.0.0.0 uv run api/app.py` exposes it to the network. Do that only on a network you trust.
- `FLASK_DEBUG=1 uv run api/app.py` turns on the Werkzeug debugger, which runs arbitrary code for
  anyone who can reach it. Never combine it with `HOST=0.0.0.0`.

Limits, set at the top of `api/app.py`:

- Uploads are limited to 20 MB (larger ones get HTTP 413), and PDFs to 20 pages (longer ones get
  HTTP 400).
- PDF pages render at 200 dpi (A4 is 1654 x 2339 px). A page whose longest side would pass 4000 px
  (20 in) gets HTTP 400, as does a PDF that is corrupt or password-protected. Reading and rendering
  are cut off after 10 s and 60 s.

## Issues

Poor OCR accuracy is usually the input: check the image quality first. Package issues belong in the
[monocr](https://github.com/janakhpon/monocr) repository.

## Licence

MIT. See [LICENSE](LICENSE).
