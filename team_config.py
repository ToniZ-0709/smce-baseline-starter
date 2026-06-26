"""Team-facing configuration — edit this file after forking the template."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


# Team identity (required after fork)

TEAM_NAME = "Team 15 - ArrayOfSunshine"
TEAM_MEMBERS = "Phạm Ngọc Tú, Lê Ngọc Tường Vy, Lê Quang Thắng, Phạm Lưu Bang"
GITHUB_REPO = "https://github.com/ToniZ-0709/smce-baseline-starter.git"
OTHER_RESOURCE = ""
STREAMLIT_APP_URL = "https://ura-team-15.streamlit.app"  # e.g. "https://ura-team-abc.streamlit.app" after deploy


# Streamlit page copy

SUBTITLE = (
    "OCR & Brand, Product Name Extraction from Social Media Images "
    "by Team 15 - ArrayOfSunshine"
)
PAGE_TITLE = f"The 2nd URA Hackathon - {TEAM_NAME}"
BROWSER_TITLE = PAGE_TITLE


# Branding assets (replace files under assets/ if needed)

ASSETS_DIR = REPO_ROOT / "assets"
FAVICON = ASSETS_DIR / "kaggle_144224_logos_thumb76_76.png"
LOGO = ASSETS_DIR / "bk_name_en.png"
LOGO_WIDTH = 280


# UI theme

THEME_PRIMARY = "#1565C0"
THEME_PRIMARY_DARK = "#0D47A1"
THEME_BG = "#FFFFFF"
THEME_TEXT = "#1A2B4A"
THEME_MUTED = "#5C6B8A"


# Default inference settings (override inside solution/pipeline.py if needed)

DEFAULT_MIN_CONF = 0.35


# Model footprint (edit when you change OCR / models — benchmark layer reads this)

MODEL_PROFILE: dict[str, str | float | None] = {
    "pipeline": "PaddleOCR(det) + VietOCR(rec) + Hybrid Funnel (Regex + ML / NER / Spatial)",
    "runtime_device": "CPU / GPU (Auto-detected)",
    "product_head_mb": None,  # auto-estimate when None
    "ocr_backend_note": "VietOCR vgg_transformer weights ~200MB, PaddleOCR det ~5MB (downloaded once)",
    "lightweight_notes": (
        "Extraction logic relies entirely on Regex, a fast TF-IDF ML Fallback, NER, and basic Spatial box area calculation. "
        "It is highly optimized and CPU-friendly. To further improve total latency on Cloud deployments, "
        "you can swap VietOCR's vgg_transformer for a lighter recognizer."
    ),
}