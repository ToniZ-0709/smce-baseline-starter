import re
import unicodedata
from collections import Counter
from underthesea import ner

# ==================== UTILITIES ====================

def normalize_vi(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()

def brands_match(a: str, b: str) -> bool:
    a, b = normalize_vi(a), normalize_vi(b)
    return a == b or a in b or b in a


# ==================== REGEX DICTIONARY ====================

BRAND_RULES = [
    (r"(?:sua|milk|bot|pha).*\bnan\b|\bnan\b.*(?:sua|milk|bot|opti|infini|supreme|formula|pha)", "Nestlé Nan", [
        (r"infini(?:\s*pro)?(?:\s*a2)?", "InfiniPro A2"),
        (r"opti\s*pro\s*plus|optiproplus", "Optipro Plus"),
        (r"opti\s*pro|optipro", "Optipro"),
        (r"supreme", "Supreme")
    ]),
    (r"ha\s*long\s*canfoco|halong\s*canfoco|canfood|canfoco", "Ha Long Canfoco", [
        (r"pate.*c[ộo]t|c[ộo]t\s*đ[èeềếêi]n|c[ộo]t\s*d[âa]n", "Pate Cột Đèn"),
        (r"pate", "Pate"),
        (r"cá\s*ngừ|ca\s*ngu", "Cá Ngừ")
    ]),
    (r"đ[ồo]\s*h[ộo]p\s*h[ạa]\s*long|do\s*hop\s*ha\s*long", "Đồ Hộp Hạ Long", [
        (r"pate.*c[ộo]t|c[ộo]t\s*đ[èe]n|c[ộo]t\s*d[âa]n", "Patê Cột Đèn")
    ]),
    (r"(?:pate|do\s*hop|thit\s*hop|ca\s*hop|cot\s*den).*ha\s*long|ha\s*long.*(?:pate|do\s*hop|thit\s*hop|ca\s*hop|cot\s*den)", "Ha Long Canfoco", [
        (r"pate.*c[ộo]t|c[ộo]t\s*đ[èe]n|c[ộo]t\s*d[âa]n", "Pate Cột Đèn"),
        (r"pate", "Pate")
    ]),
    (r"c[ộo]t\s*đ[èe]n|cot\s*den|c[ộo]t\s*d[âa]n", "Pate Cột Đèn Hải Phòng", []),
    (r"vinamilk", "Vinamilk", [
        (r"flex", "Flex"),
        (r"adm(?:\s*gold)?", "ADM Gold"),
        (r"sure\s*prevent|sure", "Sure Prevent"),
        (r"canxi", "Canxi Pro"),
        (r"colos\s*baby|colosbaby", "ColosBaby"),
        (r"ông\s*thọ|ong\s*tho", "Ông Thọ"),
        (r"dielac(?:\s*grow(?:\s*plus)?)?", "Dielac Grow Plus"),
        (r"grow\s*plus", "Grow Plus"),
        (r"grow", "Grow")
    ]),
    (r"th true|thtrue", "TH True Milk", [
        (r"yogurt|sữa\s*chua", "True Yogurt"),
        (r"grow", "Grow"),
        (r"school", "School Milk"),
        (r"butter|bơ", "True Butter")
    ]),
    (r"dutch lady|cô gái", "Dutch Lady", [
        (r"grow", "Grow"),
        (r"complete", "Complete"),
        (r"canxi", "Canxi"),
        (r"mom", "Mom")
    ]),
    (r"nutifood|nuti\b", "Nutifood", [
        (r"grow\s*plus|growplus", "Grow Plus"),
        (r"pedia", "Pedia Plus"),
        (r"iq", "IQ Gold")
    ]),
    (r"ensure\b", "Abbott Ensure", [
        (r"gold", "Gold"),
        (r"original", "Original"),
        (r"plus", "Plus")
    ]),
    (r"pediasure", "Abbott PediaSure", []),
    (r"similac", "Abbott Similac", []),
    (r"glucerna", "Abbott Glucerna", []),
    (r"milo\b", "Nestlé Milo", []),
    (r"nestle|nestlé", "Nestlé", [
        (r"milo", "Milo"),
        (r"coffee\s*mate", "Coffee Mate"),
        (r"carnation", "Carnation"),
        (r"nestea", "Nestea"),
        (r"nan", "Nan")
    ]),
    (r"aptamil", "Aptamil", []),
    (r"friso\b", "Friso", [
        (r"gold", "Gold"),
        (r"comfort", "Comfort"),
        (r"prestige", "Prestige")
    ]),
    (r"meiji\b", "Meiji", [
        (r"growing", "Growing Up"),
        (r"step", "Step")
    ]),
    (r"ba vi\b|bavi\b|ba vì", "Ba Vì", [
        (r"gold", "Gold")
    ]),
    (r"lothamilk", "Lothamilk", []),
    (r"yomost", "Yomost", []),
    (r"\b(d[àa]\s*l[ạa]t|dalat)(?:\s*milk)?\b", "Đà Lạt Milk", []),
    (r"kun\b|kun milk", "Kun", [
        (r"choco", "Chocolate"),
        (r"straw", "Strawberry")
    ]),
    (r"fami\b", "Fami", [
        (r"canxi", "Canxi"),
        (r"kid", "Kid")
    ]),
    (r"anlene", "Anlene", [
        (r"gold", "Gold"),
        (r"concentrate", "Concentrate")
    ]),
    (r"anchor\b", "Anchor", [
        (r"butter|bơ", "Butter"),
        (r"cream|kem", "Cream")
    ]),
    (r"vissan", "Vissan", [
        (r"pate\s*heo", "Pate Heo"),
        (r"pate\s*ga|pate\s*gà", "Pate Gà"),
        (r"xúc\s*xích|xuc\s*xich", "Xúc Xích"),
        (r"lạp\s*xưởng|lap\s*xuong", "Lạp Xưởng")
    ]),
    (r"hafi\b", "Hafi", []),
    (r"ba huan|ba huân", "Ba Huân", []),
    (r"san ha\b|san hà", "San Hà", []),
    (r"(?:\bcp\b|c\.p\.)(?=.*(?:pate|xuc\s*xich|thit|ga|heo|food))|(?:pate|xuc\s*xich|thit).*(?:\bcp\b|c\.p\.)", "CP", [
        (r"pate", "Pate"),
        (r"xúc\s*xích|xuc\s*xich", "Xúc Xích Heo")
    ]),
    (r"long bien|long biên", "Long Biên", []),
    (r"\bpate\b|patê", "Pate", []),
    (r"highlands?\s*coffee", "Highlands Coffee", []),
    (r"phúc\s*long|phuc\s*long", "Phúc Long", []),
    (r"the\s*coffee\s*house|coffee\s*house", "The Coffee House", []),
    (r"hipp\s*combiotic|hipp\s*organic|hipp\b", "HiPP", [
        (r"combiotic", "Combiotic"),
        (r"organic", "Organic")
    ]),
    (r"illuma\b", "ILLUMA", []),
    (r"beba\b", "Nestlé BEBA", []),
    (r"quang\s*h[oồ]ng?\s*sardine|quang\s*hong", "Quang Hong Sardine", []),
    (r"3\s*bông\s*mai|ba\s*bông\s*mai|3\s*bong\s*mai", "3 Bông Mai", [
        (r"pate", "Pate Gan")
    ]),
    (r"expect\s*pate|expect\b", "Expect Pate", []),
    (r"nhân\s*h[oò]a|nhan\s*hoa", "Nhân Hòa Foods", []),
    (r"chin[\-\s]*su|chinsu", "Chin-Su", [
        (r"tương\s*ớt|tuong\s*ot", "Tương Ớt")
    ]),
    (r"acnes\b", "Acnes", [
        (r"vitamin\s*cleanser", "Vitamin Cleanser")
    ]),
    (r"dove\b", "Dove", [
        (r"smoothie", "Smoothie tẩy da chết"),
    ]),
    (r"l.oreal|loreal|l'oreal", "L'Oreal", []),
    (r"olay\b", "Olay", []),
    (r"klairs", "Klairs", []),
    (r"torriden", "Torriden", [
        (r"dive\s*in", "Dive In"),
    ]),
    (r"hada\s*labo", "Hada Labo", []),
    (r"hatomugi", "Hatomugi", []),
    (r"mixa\b", "Mixa", []),
    (r"d'alba|d\salba|dalba", "d'Alba", []),
    (r"cosmettes", "Cosmettes", []),
    (r"beplain", "beplain", []),
    (r"colugea", "Colugea", []),
    (r"biore\b", "Biore", []),
    (r"laroche|la\s*roche", "La Roche-Posay", []),
    (r"cetaphil", "Cetaphil", []),
    (r"bioderma", "Bioderma", []),
    (r"barbie\s*skin", "Barbie Skin", []),
    (r"embryolisse", "Embryolisse", []),
    (r"ziaja", "ZIAJA", []),
    (r"skin1004", "Skin1004", []),
    (r"propolis\s*essence", "Propolis", []),
    (r"herbalife", "Herbalife", []),
    (r"lorsia", "Lorsia", []),
    (r"sắc\s*ngọc\s*khang|sac\s*ngoc\s*khang", "Sắc Ngọc Khang", []),
    (r"oggi\b", "VitaDairy", [
        (r"gold", "OGGI Gold"),
        (r"", "OGGI"),
    ]),
    (r"vita\s*dairy|vitadairy", "VitaDairy", [
        (r"colos\s*baby|colosbaby", "ColosBaby"),
    ]),
    (r"colos\s*baby|colosbaby", "VitaDairy", [
        (r"gold", "ColosBaby Gold"),
        (r"pedia", "ColosBaby Pedia"),
        (r"", "ColosBaby"),
    ]),
    (r"custas", "Custas", []),
    (r"burine", "Burine", []),
    (r"huggies", "Huggies", []),
    (r"lineabon", "LineaBon", []),
    (r"kingbaby", "KingBaby", []),
    (r"binggrae|ginggrae", "Binggrae", []),
    (r"natureone|nature\s*one", "NatureOne", []),
    (r"unicity", "Unicity", []),
    (r"traphaco", "Traphaco", []),
    (r"sinocare", "Sinocare", []),
    (r"vf\s*gold|vfgold", "VF Gold", []),
]

# ==================== LAYER 1: REGEX ====================

def extract_product(text: str) -> tuple:
    if not text or not text.strip():
        return (" ", " ")
    tl = text.lower()
    tl_norm = normalize_vi(text)
    is_e = "patê" in tl

    for pattern, brand, lines in BRAND_RULES:
        if re.search(pattern, tl_norm, re.IGNORECASE):
            if lines:
                for line_pat, canonical_line in lines:
                    if line_pat and re.search(line_pat, tl_norm, re.IGNORECASE):
                        prod = canonical_line.replace("Pate", "Patê").replace("pate", "patê") if is_e else canonical_line
                        return (brand, prod)
            return (brand, " ")
    return (" ", " ")

def split_prediction(combined_str: str) -> tuple:
    if not combined_str or not combined_str.strip():
        return (" ", " ")
    combined_str = combined_str.strip()
    known_brands = sorted(
        set(b for _, b, _ in BRAND_RULES),
        key=len, reverse=True
    )
    for brand in known_brands:
        if normalize_vi(combined_str).startswith(normalize_vi(brand.lower())):
            prod = combined_str[len(brand):].strip()
            return (brand, prod if prod else " ")
    return (" ", combined_str)

_product_predictor = None

def get_product_predictor():
    global _product_predictor
    if _product_predictor is None:
        try:
            from shared.data_utils import load_train_labels
            from solution.product_model import ProductPredictor
            train_labels = load_train_labels()
            if train_labels is not None:
                _product_predictor = ProductPredictor(min_class_count=1, prob_threshold=0.50)
                _product_predictor.fit(train_labels, extract_product)
        except Exception:
            _product_predictor = None
    return _product_predictor

def safe_ml_predict(text: str) -> tuple | None:
    try:
        predictor = get_product_predictor()
        if predictor is None:
            return None
        raw = predictor.predict(text)
        if not raw or not isinstance(raw, str):
            return None
        brand, prod = split_prediction(raw)
        if len(brand) < 2 or len(brand) > 60:
            return None
        if brand.isdigit() or prod.isdigit():
            return None
        return (brand.strip(), prod.strip())
    except Exception:
        return None

def extract_product_by_subtraction(ocr_text, brand):
    if not brand or brand == " ":
        return " "
    cleaned = re.sub(re.escape(brand), "", ocr_text, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'\d+[gG](?:\s|$)', ' ', cleaned)
    cleaned = re.sub(r'\d+[mM][lL]', ' ', cleaned)
    cleaned = re.sub(r'\d+[kK](?:g|G)', ' ', cleaned)
    cleaned = re.sub(r'@\S+', ' ', cleaned)
    cleaned = re.sub(r'#\S+', ' ', cleaned)
    cleaned = re.sub(r'\d{10,}', ' ', cleaned)
    cleaned = re.sub(r'₫|VND|\$', ' ', cleaned)
    words = [w for w in cleaned.split() if len(w) >= 2]
    product = " ".join(words[:5])
    return product if product else " "


# ==================== LAYER 2: NER ====================

_NOISE_TOKEN = re.compile(r'^(#|\d+ml|\d+g|\d+l|\d+kg|₫|\$|%)', re.IGNORECASE)
_NER_BLACKLIST = {
    "me", "mẹ", "bộ", "ban", "anh", "em", "ông", "bà", "chị", "bé",
    "con", "các", "của", "cho", "và", "hay", "với", "từ", "tại",
    "gia", "nhà", "hội", "sở", "phòng", "ban",
    "ing", "the", "and", "for", "new", "hot", "top", "all", "get",
    "mini", "love", "comb", "set", "box", "mix", "pro", "max",
}

def ner_extract_brand(ocr_text: str) -> tuple | None:
    try:
        entities = ner(ocr_text)
        brand_parts = []
        product_parts = []
        collecting_brand = False
        brand_done = False

        for word, pos, chunk, ner_tag in entities:
            if ner_tag == "B-ORG":
                collecting_brand = True
                brand_done = False
                brand_parts.append(word)
            elif ner_tag == "I-ORG" and collecting_brand:
                brand_parts.append(word)
            else:
                if collecting_brand:
                    collecting_brand = False
                    brand_done = True
                if brand_done:
                    if _NOISE_TOKEN.match(word):
                        break
                    if len(word) >= 2:
                        product_parts.append(word)

        if brand_parts:
            brand = " ".join(brand_parts).strip()
            product = " ".join(product_parts[:4]).strip()
            if len(brand) >= 3 and not brand.isdigit() and brand.lower() not in _NER_BLACKLIST:
                return (brand, product if product else " ")
        return None
    except Exception:
        return None


# ==================== NOISE GATES ====================

PRODUCT_KEYWORDS = [
    "kem", "serum", "dưỡng", "da", "tẩy trang", "tẩy da chết", "sữa rửa mặt",
    "toner", "lotion", "chống nắng", "mặt nạ", "mask", "son", "môi", "mụn",
    "thâm", "nám", "tóc", "gội", "xả", "cleanser", "cream", "body", "ẩm", "trắng",
    "sữa", "milk", "bột", "bé", "trẻ", "sơ sinh", "tã", "bỉm", "canxi", "dha",
    "chua", "yogurt", "pha sẵn", "công thức", "dinh dưỡng",
    "xúc xích", "lạp xưởng", "pate", "đồ hộp", "thịt", "heo", "bò", "gà", "cá",
    "khăn", "giấy", "ướt", "pin", "sạc", "tai nghe", "điện thoại",  
    "thú cưng", "chó", "mèo", "hạt", "tẩy rửa", "xịt", "lau", "chén"    
]

def text_has_product_keyword(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    for kw in PRODUCT_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            return True
    return False

_NON_PRODUCT_CONTEXT_NORM = {
    "ivf", "phoi", "chuyen", "benh", "kham", "vien", "thai", "mang",
    "cuoi", "lop", "truong", "hoc", "thay",
    "vlog", "unbox", "haul", "diary", "story",
    "youtube", "tiktok", "facebook", "instagram", "channel", "subscribe",
    "live", "stream", "podcast",
}

def has_non_product_context(text: str) -> bool:
    if not text:
        return False
    norm = normalize_vi(text)
    tokens = re.findall(r'\w+', norm)
    matches = sum(1 for t in tokens if t in _NON_PRODUCT_CONTEXT_NORM)
    return matches >= 2


# ==================== LAYER 3: SPATIAL ====================

def extract_brand_from_boxes(box_data):
    if not box_data or len(box_data) < 3:
        return None
    ranked = sorted(box_data, key=lambda b: b["area"], reverse=True)
    avg_area = sum(b["area"] for b in box_data) / len(box_data)
    if ranked[0]["area"] < avg_area * 1.5:
        return None
    text = ranked[0]["text"].strip()
    if len(text) < 2 or len(text) > 30:
        return None
    if text.isdigit() or text.startswith("@") or text.startswith("#"):
        return None
    return text

def extract_product_from_boxes(box_data, brand_text):
    if not box_data or len(box_data) < 2:
        return " "
    ranked = sorted(box_data, key=lambda b: b["area"], reverse=True)
    for box in ranked:
        text = box["text"].strip()
        if text.lower() == brand_text.lower():
            continue
        if len(text) < 2 or len(text) > 40:
            continue
        if text.isdigit() or text.startswith("@") or text.startswith("#"):
            continue
        return text
    return " "

def predict_product(ocr_text: str, box_data: list = None) -> tuple:
    if not ocr_text or str(ocr_text).strip().lower() in ["", "nan", "none", "null", "na"]:
        return (" ", " ")

    if has_non_product_context(ocr_text):
        return (" ", " ")

    regex_brand, regex_prod = extract_product(ocr_text)

    if regex_brand.strip():
        if not regex_prod.strip():
            ml_result = safe_ml_predict(ocr_text)
            if ml_result:
                ml_brand, ml_prod = ml_result
                if brands_match(regex_brand, ml_brand) and ml_prod.strip():
                    return (regex_brand, ml_prod)
            sub_prod = extract_product_by_subtraction(ocr_text, regex_brand)
            return (regex_brand, sub_prod)
        return (regex_brand, regex_prod)

    ner_result = ner_extract_brand(ocr_text)
    if ner_result and text_has_product_keyword(ocr_text):
        brand, prod = ner_result
        if not prod.strip():
            prod = extract_product_by_subtraction(ocr_text, brand)
        return (brand, prod)

    box_brand = extract_brand_from_boxes(box_data)
    if box_brand and text_has_product_keyword(ocr_text):
        prod = extract_product_from_boxes(box_data, box_brand)
        return (box_brand, prod)

    return (" ", " ")