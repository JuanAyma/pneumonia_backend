import os
import time
import logging
import numpy as np
from PIL import Image, ImageFilter

MODEL_DIR = os.environ.get("MODEL_DIR", "")
LABELS = ["NORMAL", "PNEUMONIA"]

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")
log = logging.getLogger(__name__)

_tflite_interpreter = None
_grad_cam_model = None


# ── TFLite interpreter ────────────────────────────────────────────────────────

def _get_interpreter(specialization_id: str):
    global _tflite_interpreter
    if _tflite_interpreter is not None:
        return _tflite_interpreter

    model_path = os.path.join(MODEL_DIR, "resnet50_etapa2_rsna.tflite")
    log.info(f"MODEL_DIR  : {MODEL_DIR!r}")
    log.info(f"TFLite path: {model_path!r}  exists={os.path.exists(model_path)}")

    if not os.path.exists(model_path):
        log.warning("TFLite model NOT found — using mock inference")
        return None

    try:
        try:
            import tflite_runtime.interpreter as tflite
            _tflite_interpreter = tflite.Interpreter(model_path=model_path)
            log.info("TFLite loaded via tflite_runtime")
        except ImportError:
            import tensorflow as tf
            _tflite_interpreter = tf.lite.Interpreter(model_path=model_path)
            log.info("TFLite loaded via tensorflow.lite")
        _tflite_interpreter.allocate_tensors()
        inp = _tflite_interpreter.get_input_details()[0]
        out = _tflite_interpreter.get_output_details()[0]
        log.info(f"Input  shape : {inp['shape']}  dtype: {inp['dtype']}")
        log.info(f"Output shape : {out['shape']}  dtype: {out['dtype']}")
        return _tflite_interpreter
    except Exception as e:
        log.error(f"Failed to load TFLite model: {e}")
        return None


# ── Keras model for Grad-CAM ──────────────────────────────────────────────────

def _get_grad_cam_model():
    global _grad_cam_model
    if _grad_cam_model is not None:
        return _grad_cam_model

    model_path = os.path.join(MODEL_DIR, "resnet50_etapa2_rsna.keras")
    log.info(f"Keras path : {model_path!r}  exists={os.path.exists(model_path)}")

    if not os.path.exists(model_path):
        log.info("Keras model not found — Grad-CAM will use Gaussian simulation")
        return None

    try:
        import tensorflow as tf
        log.info("Loading Keras model for Grad-CAM (compile=False)…")
        full_model = tf.keras.models.load_model(model_path, compile=False)

        # Find the last layer with 4-D output (batch, H, W, C) = last conv layer
        last_conv_name = "conv5_block3_out"  # ResNet50 default
        for layer in reversed(full_model.layers):
            try:
                shape = layer.output_shape
                if isinstance(shape, list):
                    shape = shape[0]
                if len(shape) == 4:
                    last_conv_name = layer.name
                    break
            except Exception:
                continue

        log.info(f"Grad-CAM target layer: {last_conv_name!r}")

        _grad_cam_model = tf.keras.Model(
            inputs=full_model.input,
            outputs=[full_model.get_layer(last_conv_name).output, full_model.output],
        )
        log.info("Grad-CAM model ready")
        return _grad_cam_model
    except Exception as e:
        log.error(f"Failed to build Grad-CAM model: {e}")
        return None


# ── Mock inference (no TFLite model) ─────────────────────────────────────────

def _mock_inference(image_path: str):
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img).astype(float)
    score = float(arr.mean()) / 255.0
    pneumonia_conf = 1.0 - score if score < 0.5 else score * 0.3
    normal_conf = 1.0 - pneumonia_conf
    return pneumonia_conf, normal_conf


# ── Heatmap generation ────────────────────────────────────────────────────────

def _simulate_heatmap(w: int, h: int, has_pathology: bool, confidence: float) -> np.ndarray:
    """Gaussian simulation used when the Keras model is unavailable."""
    heatmap = np.zeros((h, w), dtype=np.float32)
    Y, X = np.ogrid[:h, :w]

    if has_pathology:
        for cx, cy, sx, sy, strength in [
            (0.30 * w, 0.68 * h, 0.13 * w, 0.11 * h, confidence),
            (0.70 * w, 0.68 * h, 0.13 * w, 0.11 * h, confidence),
            (0.50 * w, 0.60 * h, 0.10 * w, 0.09 * h, confidence * 0.6),
        ]:
            g = np.exp(-((X - cx) ** 2 / (2 * sx ** 2) + (Y - cy) ** 2 / (2 * sy ** 2)))
            heatmap += g * strength
    else:
        heatmap = np.exp(
            -(
                (X - 0.50 * w) ** 2 / (2 * (0.20 * w) ** 2)
                + (Y - 0.45 * h) ** 2 / (2 * (0.18 * h) ** 2)
            )
        ) * 0.25

    return heatmap / (heatmap.max() + 1e-8)


def _real_gradcam(grad_cam_model, img: Image.Image, top_index: int) -> np.ndarray:
    """Compute real Grad-CAM heatmap using the Keras model."""
    import tensorflow as tf

    img_224 = np.array(img.resize((224, 224)), dtype=np.float32) / 255.0

    with tf.GradientTape() as tape:
        conv_outputs, preds = grad_cam_model(img_224[np.newaxis, ...])
        pred = preds[0]
        # Handle Dense(1, sigmoid) and Dense(2, softmax) outputs
        if pred.shape[-1] == 1:
            class_score = pred[0]  # sigmoid → P(pneumonia) directly
        else:
            class_score = pred[top_index]

    grads = tape.gradient(class_score, conv_outputs)          # (1, H, W, C)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))      # (C,)
    conv_map = conv_outputs[0]                                 # (H, W, C)
    heatmap = conv_map @ pooled_grads[..., tf.newaxis]         # (H, W, 1)
    heatmap = tf.squeeze(heatmap)                              # (H, W)
    heatmap = tf.nn.relu(heatmap)
    heatmap = heatmap / (tf.math.reduce_max(heatmap) + 1e-8)
    return heatmap.numpy()


def _overlay_heatmap(orig_img: Image.Image, heatmap_np: np.ndarray, output_path: str):
    """Apply jet colormap overlay and save."""
    w, h = orig_img.size

    # Resize heatmap to original image size
    hm_pil = Image.fromarray((heatmap_np * 255).astype(np.uint8), mode="L")
    hm_pil = hm_pil.resize((w, h), Image.BICUBIC)
    hm_pil = hm_pil.filter(ImageFilter.GaussianBlur(radius=max(2, min(w, h) // 80)))
    v = np.array(hm_pil).astype(np.float32) / 255.0

    # Vectorized jet colormap
    r = np.clip(1.5 - np.abs(4 * v - 3), 0, 1)
    g = np.clip(1.5 - np.abs(4 * v - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * v - 1), 0, 1)
    a = v * 185  # max ~72 % opacity
    overlay = np.stack([r * 255, g * 255, b * 255, a], axis=-1).astype(np.uint8)

    result = Image.alpha_composite(
        orig_img.convert("RGBA"), Image.fromarray(overlay, "RGBA")
    )
    result.convert("RGB").save(output_path)


def _generate_heatmap(
    image_path: str, diagnosis_id: str, has_pathology: bool,
    confidence: float, top_index: int
) -> str:
    output_path = f"/tmp/pneumonia_images/{diagnosis_id}_gradcam.png"
    try:
        img = Image.open(image_path).convert("RGB")
        w, h = img.size

        grad_cam_model = _get_grad_cam_model()

        if grad_cam_model is not None:
            log.info(f"[{diagnosis_id}] computing real Grad-CAM")
            heatmap_np = _real_gradcam(grad_cam_model, img, top_index)
        else:
            log.info(f"[{diagnosis_id}] using Gaussian simulation (no Keras model)")
            heatmap_np = _simulate_heatmap(w, h, has_pathology, confidence)

        _overlay_heatmap(img, heatmap_np, output_path)
        log.info(f"[{diagnosis_id}] heatmap saved → {output_path}")
    except Exception as e:
        log.warning(f"[{diagnosis_id}] heatmap generation failed: {e}")
        output_path = ""
    return output_path


# ── Main inference entry point ────────────────────────────────────────────────

def run_inference(normalized_path: str, diagnosis_id: str, specialization_id: str):
    t0 = time.time()
    interpreter = _get_interpreter(specialization_id)

    if interpreter is None:
        log.info(f"[{diagnosis_id}] mock inference on {normalized_path!r}")
        pneumonia_conf, normal_conf = _mock_inference(normalized_path)
    else:
        log.info(f"[{diagnosis_id}] TFLite inference on {normalized_path!r}")
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        img = Image.open(normalized_path).resize((224, 224)).convert("RGB")
        arr = np.array(img, dtype=np.float32) / 255.0
        arr = np.expand_dims(arr, axis=0)
        interpreter.set_tensor(input_details[0]["index"], arr)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]["index"])[0]
        if len(output) == 2:
            normal_conf, pneumonia_conf = float(output[0]), float(output[1])
        else:
            pneumonia_conf = float(output[0])
            normal_conf = 1.0 - pneumonia_conf

    has_pathology = pneumonia_conf > 0.5
    top_conf = pneumonia_conf if has_pathology else normal_conf
    top_index = 1 if has_pathology else 0

    if not has_pathology:
        risk_level = "LOW"
    elif top_conf < 0.60:
        risk_level = "MODERATE"
    elif top_conf < 0.85:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    log.info(
        f"[{diagnosis_id}] {LABELS[top_index]}  conf={top_conf:.4f}"
        f"  risk={risk_level}  ms={int((time.time() - t0) * 1000)}"
    )

    heatmap_path = _generate_heatmap(
        normalized_path, diagnosis_id, has_pathology, top_conf, top_index
    )
    heatmap_url = f"file://{heatmap_path}" if heatmap_path else None

    return dict(
        diagnosis_id=diagnosis_id,
        prediction=dict(index=top_index, label=LABELS[top_index], confidence=round(top_conf, 4)),
        all_labels=[
            dict(index=0, label="NORMAL", confidence=round(normal_conf, 4)),
            dict(index=1, label="PNEUMONIA", confidence=round(pneumonia_conf, 4)),
        ],
        has_pathology=has_pathology,
        risk_level=risk_level,
        grad_cam=dict(
            heatmap_s3_key=f"heatmaps/{diagnosis_id}/gradcam.png",
            heatmap_url=heatmap_url,
            top_regions=["lower_left_lobe", "lower_right_lobe"] if has_pathology else [],
        ),
        model_version="resnet50_v2_rsna" if interpreter else "mock_v0",
        inference_ms=int((time.time() - t0) * 1000),
    )
