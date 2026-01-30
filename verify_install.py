from monocr import MonOCR
import os
from pathlib import Path

print("initializing monocr...")
# this should trigger download if not cached
model = MonOCR()

print("model initialized successfully!")

# basic test with a dummy image if available, or just printing model info
print(f"model device: {model.device}")
print(f"charset length: {len(model.charset)}")

# try to predict if we have an image
img_path = Path("test_image.png")
if not img_path.exists():
    # download a sample image if needed, or just skip
    print("no test image found, skipping prediction.")
else:
    print(f"predicting on {img_path}...")
    text = model.read_text(str(img_path))
    print(f"prediction: {text}")
