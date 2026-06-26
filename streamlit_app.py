#!/usr/bin/env python3
"""Streamlit demo shell for URA Hackathon teams — customize team_config.py + solution/."""

from __future__ import annotations

import io

import streamlit as st
from PIL import Image

import team_config as cfg
from shared.benchmark import (
    get_deploy_smoke_benchmark,
    get_model_profile,
    run_predict_with_metrics,
)

APP_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

:root {{
    --ura-blue: {cfg.THEME_PRIMARY};
    --ura-blue-dark: {cfg.THEME_PRIMARY_DARK};
    --ura-bg: {cfg.THEME_BG};
    --ura-text: {cfg.THEME_TEXT};
    --ura-muted: {cfg.THEME_MUTED};
}}

html, body, .stApp {{
    font-family: 'Montserrat', sans-serif !important;
    font-size: 14px !important;
    background-color: var(--ura-bg) !important;
    color: var(--ura-text) !important;
}}

[data-testid="stSidebar"] {{ display: none; }}
[data-testid="collapsedControl"] {{ display: none; }}

[data-testid="stAppViewContainer"] > section > div {{
    padding-top: 1rem;
}}

[data-testid="stImage"]:first-of-type {{
    margin-bottom: 1rem;
}}

[data-testid="stImage"]:first-of-type img {{
    max-height: 72px;
    width: auto;
}}

.app-title,
[data-testid="stMarkdownContainer"] p.app-title {{
    display: block;
    font-family: 'Montserrat', sans-serif !important;
    font-size: 32px !important;
    font-weight: 700 !important;
    color: var(--ura-blue) !important;
    margin: 0 0 0.5rem 0 !important;
    line-height: 1.25 !important;
}}

.app-subtitle {{
    display: block;
    font-family: 'Montserrat', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: var(--ura-muted) !important;
    margin: 0 0 0.75rem 0 !important;
    line-height: 1.5 !important;
    max-width: 100%;
}}

.app-team-info {{
    margin: 0 0 1.25rem 0;
    padding: 0;
    list-style: none;
}}

.app-team-info li {{
    font-family: 'Montserrat', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    margin: 0 0 0.35rem 0 !important;
    color: var(--ura-text) !important;
}}

.app-team-info li strong {{
    color: var(--ura-blue);
    font-weight: 600;
}}

.app-team-info a {{
    color: var(--ura-blue);
    text-decoration: none;
    font-weight: 500;
}}

.app-team-info a:hover {{
    text-decoration: underline;
}}

[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {{
    font-family: 'Montserrat', sans-serif !important;
    color: var(--ura-blue) !important;
}}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stCaptionContainer"] {{
    font-family: 'Montserrat', sans-serif !important;
    font-size: 14px !important;
}}

.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
    color: var(--ura-blue) !important;
    border-bottom-color: var(--ura-blue) !important;
}}

.stTabs [data-baseweb="tab-list"] button {{
    font-family: 'Montserrat', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
}}

.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {{
    background-color: var(--ura-blue) !important;
    border-color: var(--ura-blue) !important;
    color: #FFFFFF !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
}}

.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {{
    background-color: var(--ura-blue-dark) !important;
    border-color: var(--ura-blue-dark) !important;
}}

.stTextInput input,
.stTextArea textarea,
.stTextInput label,
.stTextArea label {{
    font-family: 'Montserrat', sans-serif !important;
    font-size: 14px !important;
}}

[data-testid="stFileUploader"] label {{
    font-family: 'Montserrat', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: var(--ura-text) !important;
}}

[data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] {{
    font-family: 'Montserrat', sans-serif !important;
    font-size: 14px !important;
}}

[data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] button {{
    font-family: 'Montserrat', sans-serif !important;
    font-size: 14px !important;
}}
"""

st.set_page_config(
    page_title=cfg.BROWSER_TITLE,
    page_icon=str(cfg.FAVICON),
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)

st.image(str(cfg.LOGO), width=cfg.LOGO_WIDTH)

st.markdown(
    f'<p class="app-title">{cfg.PAGE_TITLE}</p>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<p class="app-subtitle">{cfg.SUBTITLE}</p>',
    unsafe_allow_html=True,
)
st.markdown(
    f"""
    <ul class="app-team-info">
        <li><strong>Team Member:</strong> {cfg.TEAM_MEMBERS}</li>
        <li><strong>Github Repo link:</strong> <a href="{cfg.GITHUB_REPO}" target="_blank">{cfg.GITHUB_REPO}</a></li>
        <li><strong>Other resource link:</strong> <a href="{cfg.OTHER_RESOURCE}" target="_blank">{cfg.OTHER_RESOURCE}</a></li>
    </ul>
    """,
    unsafe_allow_html=True,
)


def _init_live_state() -> None:
    defaults = {
        "ocr_text_live": "",
        "brand_name_live": "",
        "product_name_live": "",
        "upload_file_id": None,
        "timing_ms": None,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def _load_uploaded_image(uploaded) -> Image.Image:
    return Image.open(io.BytesIO(uploaded.getvalue())).convert("RGB")


def _clear_live_results() -> None:
    st.session_state["ocr_text_live"] = ""
    st.session_state["brand_name_live"] = ""
    st.session_state["product_name_live"] = ""
    st.session_state["timing_ms"] = None


@st.cache_data(show_spinner=False)
def _cached_model_profile() -> dict:
    return get_model_profile()


@st.cache_resource(show_spinner="Running deploy smoke benchmark (1 image)...")
def _cached_deploy_smoke() -> dict:
    return get_deploy_smoke_benchmark()


def _render_about_tab() -> None:
    st.header("About")
    st.markdown(
        """
        Trình bày giải pháp OCR + trích xuất brand_name và product_name của Team 15 - ArrayOfSunshine
        """
    )

    st.subheader("1. Thông tin team")
    st.markdown(
        f"""
        | Trường | Nội dung |
        |--------|----------|
        | **Tên team** | {cfg.TEAM_NAME} |
        | **Thành viên** | {cfg.TEAM_MEMBERS} |
        | **GitHub** | [{cfg.GITHUB_REPO}]({cfg.GITHUB_REPO}) |
        """
    )

    st.subheader("2. Bài toán")
    st.markdown(
        """
        Từ **ảnh sản phẩm trên kệ hàng / social media**, hệ thống cần trích xuất:

        - **`ocr_text`** — toàn bộ văn bản đọc được từ ảnh
        - **`brand_name`** — tên thương hiệu
        - **`product_name`** — tên / mô tả sản phẩm

        **Điểm private round:**

        `0.4 × F1_brand + 0.35 × (1 − CER) + 0.25 × F1_product`
        """
    )

    st.subheader("3. Ý tưởng & pipeline giải pháp")
    st.markdown(
        """
        Giải pháp của chúng tôi kết hợp OCR cho Tiếng Việt cùng với bộ lọc 3 tầng (Regex + NER + Spatial Heuristics + ML Fallback):

        1. **Tiền xử lý ảnh:** Cân bằng độ tương phản (Contrast Enhancement, factor=1.35), thu nhỏ ảnh nếu quá lớn (max 1280px giữ nguyên tỷ lệ bằng Lanczos), và làm nét (Sharpen Filter) để tăng chất lượng nhận diện văn bản.
        2. **Hệ thống OCR bao gồm 2 giai đoạn:**
            - **Detection:** Sử dụng PaddleOCR để xác định tọa độ các vùng chứa chữ chính xác.
            - **Sorting & Padding:** Sắp xếp lại thứ tự đọc (từ trên xuống dưới, từ trái sang phải) và tạo biên an toàn (padding=5px) trước khi cắt.
            - **Recognition:** Sử dụng VietOCR (model vgg_transformer) để nhận dạng tiếng Việt cho từng vùng ảnh đã cắt.
        3. **Hậu xử lý OCR:** Làm sạch khoảng trắng, chuẩn hóa Unicode tiếng Việt dựng sẵn và loại bỏ các token bị lặp liền kề.
        4. **Hybrid funnels trích xuất:**
            - **Tầng 1 (Regex):** Khớp dựa trên bộ từ điển brand_rules.
            - **Tầng 2 (NER):** Nhận diện thực thể có tên sử dụng thư viện underthesea NER để phát hiện các brand mới lạ chưa có trong từ điển.
            - **Tầng 3 (Spatial & Text Heuristics):** Phân tích diện tích bounding box, tần suất lặp lại của nhãn hiệu trên ảnh, tỷ lệ viết hoa và khoảng cách Proximity tới các keyword sản phẩm.
            - **Tầng 4 (ML Fallback):** Logistic Regression kết hợp TF-IDF làm nhiệm vụ phân loại sản phẩm bổ trợ khi tầng regex khớp nhãn hiệu nhưng thiếu từ khóa dòng sản phẩm.
        """
    )

    st.subheader("4. Điểm khác biệt & đóng góp chính")
    st.markdown(
        """
        - **Pipeline OCR 2 giai đoạn tối ưu tiếng Việt:** Kết hợp điểm mạnh phát hiện vùng chữ của PaddleOCR và nhận diện ký tự tiếng Việt của VietOCR.
        - **Phân tích Spatial & Layout:** Sử dụng diện tích bounding box và tần suất xuất hiện của chữ viết hoa để định vị logo thương hiệu.
        - **Từ điển quy tắc bao phủ cực rộng:** Hơn 100 quy tắc regex tinh chỉnh chi tiết cho các nhóm ngành hàng giúp tối ưu hóa F1 Score tối đa.
        - **Cơ chế Fallback:** Tự động chuyển đổi linh hoạt giữa Regex -> NER -> Heuristics -> ML Classifier để giảm thiểu sai số.
        """
    )

    st.subheader("5. Công nghệ sử dụng")
    st.markdown(
        """
        | Thành phần | Công nghệ |
        |------------|-----------|
        | **OCR (Det / Rec)** | `PaddleOCR` + `VietOCR (vgg_transformer)` |
        | **Linguistic / NER** | `underthesea` |
        | **Heuristics & Rules** | Khớp quy tắc thực thể bằng Regex & cấu trúc không gian hình học |
        | **Machine Learning** | TF-IDF Vectorizer + Logistic Regression |
        | **Runtime** | `CPU / GPU (Auto-detected), Python 3.11+` |
        | **Demo UI** | `Streamlit` |
        """
    )

    st.subheader("6. Kết quả & đánh giá")
    st.markdown(
        """
        | Metric | Giá trị (placeholder) |
        |--------|------------------------|
        | F1 brand (local) | `[—]` |
        | 1 − CER (local) | `[—]` |
        | F1 product (local) | `[—]` |
        | **Private score** | `[—]` |
        | Latency (avg / image) | **1231.1** ms (ocr 1221.8 · extract 9.3) |
        | Product head size | **0.0** MB |
        """
    )
    st.markdown(
        """
        **Đo lightweight model (latency + footprint):**

        ```bash
        python scripts/benchmark_solution.py --limit 6
        ```

        Cập nhật `MODEL_PROFILE` trong [`team_config.py`](team_config.py)
        khi đổi OCR / model. Benchmark luôn chạy qua [`shared/benchmark.py`](shared/benchmark.py).
        """
    )

    st.subheader("7. Hạn chế & hướng phát triển")
    st.markdown(
        """
        **Hạn chế hiện tại**
        - Tốc độ xử lý trên CPU còn chậm do model `vgg_transformer` của VietOCR yêu cầu nhiều tài nguyên tính toán.
        - Nhận diện các từ viết tắt cực ngắn hoặc brand viết cách điệu phức tạp chưa tối ưu.

        **Hướng phát triển**
        - Thay đổi mô hình nhận diện chữ của VietOCR bằng các phiên bản nhẹ hơn để giảm thiểu độ trễ trên CPU / Streamlit Cloud.
        - Bổ sung bộ lọc sửa lỗi chính tả tiếng Việt cho OCR text trước khi trích xuất.
        """
    )

    st.subheader("8. Liên kết")
    links = [
        f"- **Repository:** [{cfg.GITHUB_REPO}]({cfg.GITHUB_REPO})",
        "- **Setup & deploy:** [README.md](README.md)",
        f"- **Other resource:** [{cfg.OTHER_RESOURCE}]({cfg.OTHER_RESOURCE})",
    ]
    streamlit_url = getattr(cfg, "STREAMLIT_APP_URL", "")
    if streamlit_url:
        links.insert(
            1,
            f"- **Live demo (Streamlit Cloud):** [{streamlit_url}]({streamlit_url})",
        )
    st.markdown("\n".join(links))


tab_live, tab_about = st.tabs(["Live test", "About"])

with tab_live:
    _init_live_state()
    st.subheader("Live test")

    profile = _cached_model_profile()
    smoke = _cached_deploy_smoke()
    with st.expander("Model footprint (lightweight check)", expanded=False):
        st.markdown(
            f"- **Pipeline:** {profile.get('pipeline', '—')}\n"
            f"- **Runtime:** {profile.get('runtime_device', '—')}\n"
            f"- **Product head:** {profile.get('product_head_mb', 0)} MB\n"
            f"- **OCR note:** {profile.get('ocr_backend_note', '—')}\n\n"
            f"{profile.get('lightweight_notes', '')}"
        )
        if smoke.get("latency_ms"):
            lat = smoke["latency_ms"]
            st.markdown(
                f"**Deploy smoke benchmark (1 image):** "
                f"total **{lat.get('total_avg', '—')} ms** "
                f"(ocr {lat.get('ocr_avg', '—')} · extract {lat.get('extract_avg', '—')})"
            )
        elif smoke.get("error"):
            st.caption(f"Deploy smoke benchmark skipped: {smoke['error']}")
        st.caption("Full report: `python scripts/benchmark_solution.py --limit 6`")

    uploaded = st.file_uploader(
        "Ảnh sản phẩm",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False,
        key="live_upload",
    )

    if uploaded:
        file_id = f"{uploaded.name}:{uploaded.size}"
        if st.session_state["upload_file_id"] != file_id:
            st.session_state["upload_file_id"] = file_id
            _clear_live_results()

        img = _load_uploaded_image(uploaded)
        col_img, col_result = st.columns(2)

        with col_img:
            st.image(img, width='stretch')

        with col_result:
            if st.button("Chạy OCR", type="primary", key="run_ocr_live"):
                with st.spinner("Đang chạy OCR..."):
                    pred = run_predict_with_metrics(img)
                    st.session_state["ocr_text_live"] = pred["ocr_text"]
                    st.session_state["brand_name_live"] = pred["brand_name"]
                    st.session_state["product_name_live"] = pred["product_name"]
                    st.session_state["timing_ms"] = pred.get("timing_ms")

            timing = st.session_state.get("timing_ms")
            if timing:
                t1, t2, t3 = st.columns(3)
                t1.metric("Total (ms)", f"{timing['total']:.1f}")
                t2.metric("OCR (ms)", f"{timing['ocr']:.1f}")
                t3.metric("Extract (ms)", f"{timing['extract']:.1f}")

            st.text_area("ocr_text", height=140, key="ocr_text_live")
            st.text_input("brand_name", key="brand_name_live")
            st.text_input("product_name", key="product_name_live")
    else:
        st.session_state["upload_file_id"] = None
        _clear_live_results()

with tab_about:
    _render_about_tab()
