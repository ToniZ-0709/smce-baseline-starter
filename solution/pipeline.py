"""
Team solution pipeline — Hybrid PaddleOCR + VietOCR + Heuristics
"""

from __future__ import annotations

import re
import time
from functools import lru_cache
from typing import Any

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from solution.brand_rules import predict_product
from team_config import DEFAULT_MIN_CONF

def preprocess(img: Image.Image, max_dim: int = 1280) -> Image.Image:
    w, h = img.size
    if max(w, h) > max_dim:
        ratio = max_dim / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(1.35)
    return img.filter(ImageFilter.SHARPEN)

def postprocess_ocr(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    tokens = text.split()
    if not tokens:
        return ""
    deduped = [tokens[0]]
    for tok in tokens[1:]:
        if tok.lower() != deduped[-1].lower():
            deduped.append(tok)
    return " ".join(deduped)

@lru_cache(maxsize=1)
def get_detector():
    from paddleocr import PaddleOCR
    import logging
    logging.getLogger('ppocr').setLevel(logging.ERROR)
    # PaddleOCR loads weights once on first call
    return PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

@lru_cache(maxsize=1)
def get_recognizer():
    from vietocr.tool.predictor import Predictor
    from vietocr.tool.config import Cfg
    import torch
    config = Cfg.load_config_from_name('vgg_transformer')
    config['cnn']['pretrained'] = False
    config['device'] = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    return Predictor(config)

def Crop_Padding(image, bbox, pad=8):
    """Crop the axis-aligned bounding rectangle of `bbox` from `image`."""
    box = np.array(bbox).astype(np.int32)
    x_min = max(0, np.min(box[:, 0]) - pad)
    x_max = min(image.shape[1], np.max(box[:, 0]) + pad)
    y_min = max(0, np.min(box[:, 1]) - pad)
    y_max = min(image.shape[0], np.max(box[:, 1]) + pad)
    return image[y_min:y_max, x_min:x_max]

def Sort_Boxes(dt_boxes):
    """Sort reading order: top to bottom, left to right."""
    if len(dt_boxes) == 0:
        return []
    dt_boxes = sorted(dt_boxes, key=lambda x: x[0][1]) # y-coord
    return dt_boxes

def run_ocr_on_image(img: Image.Image, detector, recognizer) -> tuple[str, list]:
    img_pre = preprocess(img.convert("RGB"))
    img_np = np.array(img_pre)
    
    result = detector.ocr(img_np, cls=False)
    if result is None or len(result) == 0 or result[0] is None:
        return "", []

    dt_boxes = [res[0] for res in result[0]]
    if dt_boxes:
        dt_boxes = Sort_Boxes(dt_boxes)
    
    texts = []
    box_data = []
    
    for box in dt_boxes:
        cropped = Crop_Padding(img_np, box, pad=8)
        if cropped.size == 0 or cropped.shape[0] < 8 or cropped.shape[1] < 8:
            continue
            
        pil_crop = Image.fromarray(cropped)
        text = recognizer.predict(pil_crop)
        
        # Matching notebook check for > 1 length before recording box
        if len(text.strip()) > 1:
            # Matching notebook exact area calculation mechanism
            width = abs(box[1][0] - box[0][0])
            height = abs(box[2][1] - box[1][1])
            area = width * height
            texts.append(text.strip())
            box_data.append({"text": text.strip(), "area": area})
        
    ocr_text = " ".join(texts)
    ocr_text = postprocess_ocr(ocr_text)
    return ocr_text, box_data


def predict_from_image(
    img: Image.Image,
    min_conf: float = DEFAULT_MIN_CONF,
    *,
    include_timing: bool = True,
) -> dict[str, Any]:
    """
    Main entry point for Streamlit + batch submission.
    
    Returns dict with keys: ocr_text, brand_name, product_name
    Optional timing_ms: {ocr, extract, total} in milliseconds.
    """
    t0 = time.perf_counter()

    t_ocr = time.perf_counter()
    detector = get_detector()
    recognizer = get_recognizer()
    
    ocr_text, box_data = run_ocr_on_image(img, detector, recognizer)
    ocr_ms = (time.perf_counter() - t_ocr) * 1000

    t_extract = time.perf_counter()
    brand, product = predict_product(ocr_text, box_data)
    extract_ms = (time.perf_counter() - t_extract) * 1000

    total_ms = (time.perf_counter() - t0) * 1000

    result: dict[str, Any] = {
        "ocr_text": ocr_text,
        "brand_name": brand,
        "product_name": product,
    }
    if include_timing:
        result["timing_ms"] = {
            "ocr": round(ocr_ms, 1),
            "extract": round(extract_ms, 1),
            "total": round(total_ms, 1),
        }
    return result

def predict_from_text(ocr_text: str) -> tuple[str, str]:
    return predict_product(ocr_text)