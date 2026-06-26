import re
import unicodedata
from collections import Counter
from underthesea import ner

# ==================== UTILITIES ====================

def normalize_vi(s: str) -> str:
    """Strip diacritics and lowercase for matching."""
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()

def brands_match(a: str, b: str) -> bool:
    a, b = normalize_vi(a), normalize_vi(b)
    return a == b or a in b or b in a


# ==================== REGEX DICTIONARY ====================
BRAND_RULES = [
    # NAN 
    (r"(?:sua|milk|bot|pha).*\bnan\b|\bnan\b.*(?:sua|milk|bot|opti|infini|supreme|formula|pha)", "Nestlé Nan", [
        (r"infini(?:\s*pro)?(?:\s*a2)?", "InfiniPro A2"),
        (r"opti\s*pro\s*plus|optiproplus", "Optipro Plus"),
        (r"opti\s*pro|optipro", "Optipro"),
        (r"supreme", "Supreme")
    ]),
    
    # Ha Long Canfoco & Đồ Hộp Hạ Long
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
    
    # Vinamilk
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
    
    # TH True Milk
    (r"th true|thtrue", "TH True Milk", [
        (r"yogurt|sữa\s*chua", "True Yogurt"),
        (r"grow", "Grow"),
        (r"school", "School Milk"),
        (r"butter|bơ", "True Butter")
    ]),
    
    # Dutch Lady
    (r"dutch lady|cô gái", "Dutch Lady", [
        (r"grow", "Grow"),
        (r"complete", "Complete"),
        (r"canxi", "Canxi"),
        (r"mom", "Mom")
    ]),
    
    # Nutifood
    (r"nutifood|nuti\b", "Nutifood", [
        (r"grow\s*plus|growplus", "Grow Plus"),
        (r"pedia", "Pedia Plus"),
        (r"iq", "IQ Gold")
    ]),
    
    # Ensure
    (r"ensure\b", "Abbott Ensure", [
        (r"gold", "Gold"),
        (r"original", "Original"),
        (r"plus", "Plus")
    ]),
    
    # Other Abbott
    (r"pediasure", "Abbott PediaSure", []),
    (r"similac", "Abbott Similac", []),
    (r"glucerna", "Abbott Glucerna", []),
    
    # Milo
    (r"milo\b", "Nestlé Milo", []),
    
    # Nestlé General
    (r"nestle|nestlé", "Nestlé", [
        (r"milo", "Milo"),
        (r"coffee\s*mate", "Coffee Mate"),
        (r"carnation", "Carnation"),
        (r"nestea", "Nestea"),
        (r"nan", "Nan")
    ]),
    
    # Aptamil
    (r"aptamil", "Aptamil", []),
    
    # Friso
    (r"friso\b", "Friso", [
        (r"gold", "Gold"),
        (r"comfort", "Comfort"),
        (r"prestige", "Prestige")
    ]),
    
    # Meiji
    (r"meiji\b", "Meiji", [
        (r"growing", "Growing Up"),
        (r"step", "Step")
    ]),
    
    # Ba Vì
    (r"ba vi\b|bavi\b|ba vì", "Ba Vì", [
        (r"gold", "Gold")
    ]),
    
    # Lothamilk
    (r"lothamilk", "Lothamilk", []),
    
    # Yomost
    (r"yomost", "Yomost", []),
    
    # Đà Lạt Milk
    (r"\b(d[àa]\s*l[ạa]t|dalat)(?:\s*milk)?\b", "Đà Lạt Milk", []),
    
    # Kun
    (r"kun\b|kun milk", "Kun", [
        (r"choco", "Chocolate"),
        (r"straw", "Strawberry")
    ]),
    
    # Fami
    (r"fami\b", "Fami", [
        (r"canxi", "Canxi"),
        (r"kid", "Kid")
    ]),
    
    # Anlene
    (r"anlene", "Anlene", [
        (r"gold", "Gold"),
        (r"concentrate", "Concentrate")
    ]),
    
    # Anchor
    (r"anchor\b", "Anchor", [
        (r"butter|bơ", "Butter"),
        (r"cream|kem", "Cream")
    ]),
    
    # Vissan
    (r"vissan", "Vissan", [
        (r"pate\s*heo", "Pate Heo"),
        (r"pate\s*ga|pate\s*gà", "Pate Gà"),
        (r"xúc\s*xích|xuc\s*xich", "Xúc Xích"),
        (r"lạp\s*xưởng|lap\s*xuong", "Lạp Xưởng")
    ]),
    
    # Hafi
    (r"hafi\b", "Hafi", []),
    
    # Ba Huân
    (r"ba huan|ba huân", "Ba Huân", []),
    
    # San Hà
    (r"san ha\b|san hà", "San Hà", []),
    
    # CP
    (r"(?:\bcp\b|c\.p\.)(?=.*(?:pate|xuc\s*xich|thit|ga|heo|food))|(?:pate|xuc\s*xich|thit).*(?:\bcp\b|c\.p\.)", "CP", [
        (r"pate", "Pate"),
        (r"xúc\s*xích|xuc\s*xich", "Xúc Xích Heo")
    ]),
    
    # Long Biên
    (r"long bien|long biên", "Long Biên", []),
    
    # Fallback Pate
    (r"\bpate\b|patê", "Pate", []),
    
    # Coffee
    (r"highlands?\s*coffee", "Highlands Coffee", []),
    (r"phúc\s*long|phuc\s*long", "Phúc Long", []),
    (r"the\s*coffee\s*house|coffee\s*house", "The Coffee House", []),
    
    # Baby Formula (Others)
    (r"hipp\s*combiotic|hipp\s*organic|hipp\b", "HiPP", [
        (r"combiotic", "Combiotic"),
        (r"organic", "Organic")
    ]),
    (r"illuma\b", "ILLUMA", []),
    (r"beba\b", "Nestlé BEBA", []),
    
    # Canned food (Others)
    (r"quang\s*h[oồ]ng?\s*sardine|quang\s*hong", "Quang Hong Sardine", []),
    (r"3\s*bông\s*mai|ba\s*bông\s*mai|3\s*bong\s*mai", "3 Bông Mai", [
        (r"pate", "Pate Gan")
    ]),
    (r"expect\s*pate|expect\b", "Expect Pate", []),
    (r"nhân\s*h[oò]a|nhan\s*hoa", "Nhân Hòa Foods", []),
    
    # Condiments
    (r"chin[\-\s]*su|chinsu", "Chin-Su", [
        (r"tương\s*ớt|tuong\s*ot", "Tương Ớt")
    ]),
    
    # Cosmetics
    (r"acnes\b", "Acnes", [
        (r"vitamin\s*cleanser", "Vitamin Cleanser")
    ]),
    # ============ PHASE 2 ============
    # Cosmetics & Personal Care
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

    # New Milks & Foods
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

# Lazy loading of ML model
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

# ==================== LAYER 3: HEURISTIC SPATIAL + TEXT ====================

_NOISE_PATTERNS = [
    re.compile(r'^\d+(?:\.\d+)?\s*(?:g|ml|l|kg|oz|lb)s?$', re.IGNORECASE),
    re.compile(r'^@\S+$'),
    re.compile(r'^#\S+$'),
    re.compile(r'^\d{6,}$'),
    re.compile(r'^[\d\.,\s\-\(\)]+₫?$'),
    re.compile(r'^[\d\.,]+\s*(?:vnd|usd|đ)$', re.IGNORECASE),
    re.compile(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$'),
    re.compile(r'^[^\w\s]{2,}$'),
]

_STOP_WORDS_NORM = {
    "cua", "cho", "va", "voi", "tu", "tai", "den", "ve", "nhu", "da",
    "cac", "nay", "nhung", "khi", "neu", "thi", "de", "duoc", "co", "khong",
    "la", "se", "anh", "em", "chi", "ban", "ong", "ba", "con", "ai", "gi",
    "trong", "ngoai", "tren", "duoi", "do", "kia", "hay",
    "the", "and", "for", "with", "from", "are", "you", "this", "that",
    "have", "has", "your", "our", "their", "his", "her", "but", "not",
    "sale", "off", "new", "hot", "free", "shop", "store", "online", "follow",
    "like", "share", "comment", "link", "bio", "click", "buy", "now",
    "gia", "tot", "re", "chinh", "hang", "ship", "giao",
}

_PRODUCT_KEYWORDS_NORM = {
    "kem", "serum", "duong", "tay", "trang", "rua", "mat", "toner",
    "lotion", "chong", "nang", "na", "mask", "son", "moi", "mun", "tham",
    "nam", "cleanser", "cream", "moisturizer", "sunscreen", "whitening",
    "essence", "ampoule", "balm", "rang",
    "dau", "goi", "xa", "toc", "hair", "shampoo", "conditioner",
    "sua", "milk", "bot", "chua", "yogurt", "cheese", "bo", "butter",
    "pha", "cong", "thuc", "dinh", "tra", "tea", "coffee",
    "be", "tre", "so", "sinh", "ta", "bim", "baby", "infant", "kid",
    "child", "grow", "canxi", "dha", "formula",
    "pate", "pat", "xuc", "xich", "lap", "xuong", "do", "hop", "thit",
    "heo", "ga", "ca", "sardine", "tuna", "ngu",
    "vien", "uong", "thuoc", "vitamin", "collagen", "supplement",
    "may", "huyet", "test", "glucose",
    "khan", "giay", "uot", "nuoc", "lau",
}

_CATEGORY_WORDS_NORM = {
    "kem", "sua", "bot", "mi", "banh", "nuoc", "tra", "dau", "san", "pham",
}

_BRAND_LIKE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9'\-\.&]{1,29}$")

def is_noise_token(text: str) -> bool:
    if not text or len(text.strip()) < 2:
        return True
    t = text.strip()
    for pattern in _NOISE_PATTERNS:
        if pattern.match(t):
            return True
    norm = normalize_vi(t)
    if norm in _STOP_WORDS_NORM:
        return True
    alpha_count = sum(c.isalpha() for c in t)
    if alpha_count < 2:
        return True
    return False

def has_product_signal(text: str) -> bool:
    if not text:
        return False
    norm = normalize_vi(text)
    tokens = re.findall(r'\w+', norm)
    return any(tok in _PRODUCT_KEYWORDS_NORM for tok in tokens)

def brand_score(text: str) -> float:
    if not text:
        return 0.0
    t = text.strip()
    n = len(t)
    if n < 2 or n > 30:
        return 0.0
    if is_noise_token(t):
        return 0.0

    score = 0.0
    if _BRAND_LIKE_PATTERN.match(t):
        score += 2.0
    if t.isupper() and any(c.isalpha() for c in t) and n >= 3:
        score += 2.0
    elif t[0].isupper():
        score += 1.0
    if sum(1 for c in t if c.isupper()) >= 2 and not t.isupper():
        score += 1.5
    if 3 <= n <= 12:
        score += 1.0
    elif 13 <= n <= 20:
        score += 0.5
    if has_product_signal(t):
        score -= 1.5
    if t.islower():
        score -= 1.0
    digit_ratio = sum(c.isdigit() for c in t) / n
    if digit_ratio > 0.3:
        score -= 1.0
    return score

def is_strong_brand(text: str) -> bool:
    if not text:
        return False
    t = text.strip()
    if len(t) < 3 or len(t) > 25:
        return False
    if is_noise_token(t):
        return False
    if has_product_signal(t):
        return False
    if t.isupper() and sum(c.isalpha() for c in t) >= 3:
        return True
    capitals = sum(1 for c in t if c.isupper())
    if capitals >= 2 and not t.isupper() and t[0].isupper():
        return True
    return False

def find_repeated_brand(box_data):
    if not box_data or len(box_data) < 2:
        return None
    norm_to_originals = {}
    for box in box_data:
        text = box["text"].strip()
        if brand_score(text) <= 0:
            continue
        norm = normalize_vi(text)
        if not norm:
            continue
        norm_to_originals.setdefault(norm, []).append(text)
    candidates = [(norm, originals) for norm, originals in norm_to_originals.items() if len(originals) >= 2]
    if not candidates:
        return None
    candidates.sort(key=lambda x: (len(x[1]), brand_score(x[1][0])), reverse=True)
    return candidates[0][1][0]

def extract_from_spatial(box_data):
    if not box_data:
        return ("", "")
    boxes = [b for b in box_data if b.get("text") and not is_noise_token(b["text"])]
    if not boxes:
        return ("", "")

    repeated = find_repeated_brand(box_data)
    by_area = sorted(boxes, key=lambda b: b["area"], reverse=True)

    brand = ""
    brand_norm = ""
    if repeated:
        brand = repeated
        brand_norm = normalize_vi(brand)
    else:
        best_score = 0.0
        for idx, box in enumerate(by_area[:5]):
            text = box["text"].strip()
            bs = brand_score(text)
            if bs <= 0:
                continue
            area_rank_weight = 1.0 / (1 + idx)
            combined = bs * (1 + area_rank_weight)
            if combined > best_score:
                best_score = combined
                brand = text
                brand_norm = normalize_vi(text)

    product_parts = []
    seen = set()
    for box in by_area:
        text = box["text"].strip()
        norm = normalize_vi(text)
        if norm == brand_norm or norm in seen:
            continue
        seen.add(norm)
        if is_noise_token(text):
            continue
        product_parts.append(text)
        if len(product_parts) >= 5:
            break

    has_kw = [has_product_signal(p) for p in product_parts]
    if any(has_kw):
        kept = []
        first_kw_idx = has_kw.index(True)
        kept = product_parts[:first_kw_idx + 1]
        for i in range(first_kw_idx + 1, len(product_parts)):
            if has_kw[i]:
                kept.append(product_parts[i])
            if len(kept) >= 4:
                break
        product = " ".join(kept[:4])
    else:
        product = " ".join(product_parts[:2]) if product_parts else ""

    return (brand, product)

def extract_from_text(ocr_text: str):
    if not ocr_text or not ocr_text.strip():
        return ("", "")
    tokens = ocr_text.strip().split()
    if not tokens:
        return ("", "")

    scored = []
    for i, tok in enumerate(tokens):
        if normalize_vi(tok) in _CATEGORY_WORDS_NORM:
            continue
        s = brand_score(tok)
        if s > 0:
            scored.append((tok, s, i))

    MIN_BRAND_SCORE = 2.5
    if not scored or max(s[1] for s in scored) < MIN_BRAND_SCORE:
        if has_product_signal(ocr_text):
            product_tokens = [t for t in tokens if not is_noise_token(t)][:5]
            return ("", " ".join(product_tokens) if product_tokens else "")
        return ("", "")

    strong_brands = [(tok, s, i) for tok, s, i in scored if is_strong_brand(tok)]

    if strong_brands:
        best_brand = None
        best_proximity = 999
        for tok, s, idx in strong_brands:
            window = tokens[max(0, idx - 3):idx + 4]
            if any(has_product_signal(t) for t in window):
                proximity = 0
            else:
                proximity = 1
            if proximity < best_proximity or (proximity == best_proximity and s > (best_brand[1] if best_brand else 0)):
                best_brand = (tok, s, idx)
                best_proximity = proximity
        brand, _, brand_idx = best_brand
    else:
        scored.sort(key=lambda x: (-x[1], x[2]))
        brand, _, brand_idx = scored[0]

    brand_norm = normalize_vi(brand)
    all_tokens = [(t, i) for i, t in enumerate(tokens) if not is_noise_token(t)]
    product_candidates = [(t, i) for t, i in all_tokens if normalize_vi(t) != brand_norm]
    product_candidates.sort(key=lambda x: x[1])

    has_kw = [(t, i, has_product_signal(t)) for t, i in product_candidates]
    if any(kw for _, _, kw in has_kw):
        result_tokens = []
        for t, i, kw in has_kw:
            if kw or len([x for x in result_tokens if has_product_signal(x)]) > 0:
                result_tokens.append(t)
            if len(result_tokens) >= 5:
                break
        product = " ".join(result_tokens) if result_tokens else ""
    else:
        product = " ".join(t for t, i in product_candidates[:4]) if product_candidates else ""

    return (brand, product)

def predict_product(ocr_text: str, box_data: list = None) -> tuple:
    if not ocr_text or str(ocr_text).strip().lower() in ["", "nan", "none", "null", "na"]:
        return (" ", " ")

    # Early rejection for non-product contexts 
    if has_non_product_context(ocr_text):
        return (" ", " ")

    regex_brand, regex_prod = extract_product(ocr_text)

    # 1. Regex
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

    # 2. NER
    ner_result = ner_extract_brand(ocr_text)
    if ner_result and text_has_product_keyword(ocr_text):
        brand, prod = ner_result
        if not prod.strip():
            prod = extract_product_by_subtraction(ocr_text, brand)
        return (brand, prod)

    # 3. Heuristic spatial + text extraction 
    if text_has_product_keyword(ocr_text) or (box_data and find_repeated_brand(box_data)):
        brand, product = "", ""
        if box_data and len(box_data) >= 1:
            brand, product = extract_from_spatial(box_data)
        if not brand:
            brand, product = extract_from_text(ocr_text)
        if brand:
            return (brand.strip() or " ", product.strip() or " ")

    # 4. Fallback
    return (" ", " ")