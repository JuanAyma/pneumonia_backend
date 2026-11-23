import base64
import io
import os
import time
import uuid
from PIL import Image, ImageFilter
import numpy as np

SAVE_DIR = os.environ.get("SAVE_DIR", "/tmp/pneumonia_images")
os.makedirs(SAVE_DIR, exist_ok=True)

TARGET_SIZE = (224, 224)
SKIP_QUALITY = os.environ.get("SKIP_QUALITY_CHECK", "false").lower() == "true"

def _sharpness_score(img: Image.Image) -> float:
    """Laplacian variance as a sharpness proxy, normalized 0-1."""
    gray = img.convert("L")
    arr = np.array(gray, dtype=float)
    lap = np.array([
        [0, -1, 0],
        [-1, 4, -1],
        [0, -1, 0]
    ])
    from PIL.ImageFilter import Kernel
    filtered = gray.filter(ImageFilter.FIND_EDGES)
    var = np.array(filtered).var()
    # Normalise roughly to 0-1 (empirical)
    return min(float(var) / 2000.0, 1.0)

def _contrast_ok(img: Image.Image) -> bool:
    gray = img.convert("L")
    arr = np.array(gray)
    return float(arr.std()) > 20.0

def process_image(image_base64: str, diagnosis_id: str):
    t0 = time.time()
    raw = base64.b64decode(image_base64)
    img = Image.open(io.BytesIO(raw))

    is_grayscale = img.mode in ("L", "LA")
    orig_w, orig_h = img.size
    resolution_ok = orig_w >= 224 and orig_h >= 224
    contrast_ok = _contrast_ok(img)
    sharpness = _sharpness_score(img)

    # Normalise: convert to RGB, resize to 224x224
    rgb = img.convert("RGB")
    resized = rgb.resize(TARGET_SIZE, Image.LANCZOS)

    norm_filename = f"{diagnosis_id}_norm.jpg"
    norm_path = os.path.join(SAVE_DIR, norm_filename)
    resized.save(norm_path, "JPEG", quality=95)

    # In dev we store locally; in prod this is S3
    s3_key = f"images/{diagnosis_id}/original.jpg"
    s3_url = f"file://{norm_path}"  # local URL for MVP

    if SKIP_QUALITY:
        passed = True
        rejection = None
    else:
        passed = resolution_ok and contrast_ok and sharpness >= 0.05
        rejection = None if passed else (
            "Low sharpness" if sharpness < 0.05 else
            "Low contrast" if not contrast_ok else
            "Resolution too small"
        )

    return dict(
        diagnosis_id=diagnosis_id,
        s3_key=s3_key,
        s3_url=s3_url,
        width=orig_w,
        height=orig_h,
        normalized_path=norm_path,
        quality=dict(
            is_grayscale=is_grayscale,
            contrast_ok=contrast_ok,
            resolution_ok=resolution_ok,
            sharpness_score=round(sharpness, 3),
        ),
        passed_quality=passed,
        rejection_reason=rejection,
        processing_ms=int((time.time() - t0) * 1000),
    )
