"""
Automotive router rules.

Bu dosya otomotiv domain'ine özel query routing kurallarını tutar.

Core router şunu bilmemeli:
- BOSCH nedir?
- akü/fren/motor yağı hangi keywordlerle yakalanır?
- hangi ürün ailesi hangi prefix ile başlar?

Bu bilgiler domain'e aittir.
"""
import re

IMAGE_WORDS = [
    "görsel", "resim", "fotoğraf", "foto",
    "image", "picture", "ürün resmi", "parça görseli"
]


KNOWN_BRANDS = [
    "BOSCH",
    "POWERLINE",
    "EVER START",
    "TOTAL",
    "SHELL",
    "CASTROL",
    "SBS",
    "OSIMCO",
    "BREMBO",
    "PERFORMENCE PLUS",
    "PERFORMANCE PLUS",
    "MANN",
    "LUK",
    "GARRETT",
    "CONTINENTAL",
    "VALEO",
    "KYB",
    "FEBI",
    "LEMFÖRDER",
    "CTEK",
]


RECOMMENDATION_WORDS = [
    "en iyi",
    "hangisi daha iyi",
    "daha iyi",
    "öner",
    "oner",
    "tavsiye",
    "karşılaştır",
    "karsilastir",
    "fiyat performans",
    "kaliteli",
    "tercih edilmeli",
    "en ucuz",
    "ucuz",
    "en pahalı",
    "pahalı",
    "fiyatı düşük",
    "fiyati dusuk",
]


PART_KEYWORDS = {
    "battery": [
    "akü",
    "aku",
    "batarya",
    "battery",
    "araba aküsü",
    "araç aküsü",
    "otomobil aküsü",
],
    "brake_pad": ["fren balatası", "fren balata", "brake pad"],
    "brake_disc": ["fren diski", "brake disc", "disk fren"],
    "engine_oil": ["motor yağı", "motor yagi", "engine oil"],
    "clutch": ["debriyaj", "baskı balata", "clutch"],
    "filter": ["filtre", "filter"],
    "turbo": ["turbo", "turboşarj", "turbocharger"],
    "timing_belt": ["triger", "triger kayışı", "timing belt"],
}


STRICT_FAMILY_RULES = {
    "battery_charger": {
        "keywords": ["akü şarj cihazı", "battery charger", "şarj cihazı"],
        "include_product_prefixes": ["ACC-BATT"],
        "exclude_product_prefixes": ["BAT-12V"],
        "exclude_words": [],
    },
    "battery": {
        "keywords": [
            "akü",
            "aku",
            "batarya",
            "battery",
            "araba aküsü",
            "araç aküsü",
            "otomobil aküsü",
        ],
        "include_product_prefixes": ["BAT-12V"],
        "exclude_product_prefixes": ["ACC-BATT"],
        "exclude_words": ["şarj cihazı", "charger", "takviye"],
    },
    "brake_pad": {
        "keywords": ["fren balatası", "fren balata", "brake pad"],
        "include_product_prefixes": ["BRK-PAD"],
        "exclude_product_prefixes": ["BRAKE-DISC", "CLUTCH"],
        "exclude_words": ["fren diski", "debriyaj", "baskı balata"],
    },
    "brake_disc": {
        "keywords": ["fren diski", "brake disc"],
        "include_product_prefixes": ["BRAKE-DISC"],
        "exclude_product_prefixes": ["BRK-PAD", "CLUTCH"],
        "exclude_words": ["fren balatası", "debriyaj", "baskı balata"],
    },
    "engine_oil": {
        "keywords": ["motor yağı", "motor yagi", "engine oil"],
        "include_product_prefixes": ["ENGINE-OIL"],
        "exclude_product_prefixes": [],
        "exclude_words": ["şanzıman", "transmission"],
    },
    "clutch": {
        "keywords": ["debriyaj seti", "debriyaj", "clutch"],
        "include_product_prefixes": ["CLUTCH"],
        "exclude_product_prefixes": ["BRK-PAD", "BRAKE-DISC"],
        "exclude_words": ["fren balatası", "fren diski"],
    },
}


STRICT_FAMILY_PRIORITY = [
    "battery_charger",
    "brake_pad",
    "brake_disc",
    "engine_oil",
    "clutch",
    "battery",
]

import re


def keyword_matches_query(query: str, keyword: str) -> bool:
    """
    Keyword eşleşmesini güvenli yapar.

    Neden?
    Basit substring araması hatalı sonuç üretir.

    Örnek:
    - "vakum" içinde "aku" geçtiği için battery yakalanmamalı.
    - "araba aküsü" ise battery yakalanmalı.
    """
    q = query.lower()
    kw = keyword.lower().strip()

    # Çok kelimeli ifadelerde phrase kontrolü yapılır.
    if " " in kw:
        return kw in q

    # Tek kelimede kelime sınırı kullanılır.
    pattern = rf"(?<!\w){re.escape(kw)}(?!\w)"

    if re.search(pattern, q):
        return True

    # Türkçe ekli akü formları.
    # Örnek: akü -> aküsü, aküyü, aküye
    if kw in ["akü", "aku"]:
        return any(
            form in q
            for form in [
                "aküsü",
                "aküyü",
                "aküye",
                "aküde",
                "aküden",
                "akünün",
                "akunun",
            ]
        )

    return False

def detect_recommendation_mode(query: str):
    """
    Öneri sorusunun hangi mantıkla sıralanacağını belirler.

    Örnek:
    - en ucuz motor yağı -> cheapest
    - en iyi akü -> best
    - fiyat performans akü -> value
    """
    q = query.lower()

    cheapest_words = [
        "en ucuz",
        "ucuz",
        "fiyatı düşük",
        "fiyati dusuk",
        "düşük fiyat",
        "dusuk fiyat",
    ]

    expensive_words = [
        "en pahalı",
        "pahalı",
        "pahali",
    ]

    value_words = [
        "fiyat performans",
        "f/p",
        "fp",
        "parasına değer",
        "parasina deger",
    ]

    best_words = [
        "en iyi",
        "kaliteli",
        "hangisi daha iyi",
        "tavsiye",
        "öner",
        "oner",
    ]

    if any(word in q for word in cheapest_words):
        return "cheapest"

    if any(word in q for word in expensive_words):
        return "expensive"

    if any(word in q for word in value_words):
        return "value"

    if any(word in q for word in best_words):
        return "best"

    return "best"

def detect_recommendation_mode(query: str):
    """
    Öneri sorgusunun hangi moda göre sıralanacağını belirler.

    Modes:
    - cheapest  : en ucuz ürün
    - expensive : en pahalı ürün
    - value     : fiyat/performans
    - best      : genel en iyi öneri
    """
    q = query.lower()

    cheapest_words = [
        "en ucuz",
        "ucuz",
        "fiyatı düşük",
        "fiyati dusuk",
        "düşük fiyat",
        "dusuk fiyat",
    ]

    expensive_words = [
        "en pahalı",
        "en pahali",
        "pahalı",
        "pahali",
    ]

    value_words = [
        "fiyat performans",
        "f/p",
        "fp",
        "parasına değer",
        "parasina deger",
    ]

    best_words = [
        "en iyi",
        "kaliteli",
        "hangisi daha iyi",
        "tavsiye",
        "öner",
        "oner",
    ]

    if any(word in q for word in cheapest_words):
        return "cheapest"

    if any(word in q for word in expensive_words):
        return "expensive"

    if any(word in q for word in value_words):
        return "value"

    if any(word in q for word in best_words):
        return "best"

    return "best"