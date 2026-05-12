"""
Automotive domain rules.

Bu dosya otomotiv alanına özel:
- synonym kurallarını
- semantic rerank kurallarını
- component bazlı boost/penalty kurallarını

merkezi olarak tutar.

Amaç:
Core katmanı domain bağımsız kalsın.
Otomotiv özel kararlar burada yönetilsin.
"""


SYNONYM_MAP = {
    "elektrikli": ["elektrikli", "electric", "ev"],
    "batarya": ["batarya", "battery", "yüksek voltaj"],
    "akü": ["akü", "aku", "battery"],
    "aku": ["akü", "aku", "battery"],
    "motor": ["motor", "engine"],
    "şanzıman": ["şanzıman", "sanziman", "transmission"],
    "sanziman": ["şanzıman", "sanziman", "transmission"],
    "elektrik": ["elektrik", "electrical", "elektronik"],
    "garanti": ["garanti", "warranty"],
}


def expand_tokens(tokens):
    """
    Query token listesini synonym'lerle genişletir.
    """
    expanded = set(tokens)

    for token in tokens:
        for key, values in SYNONYM_MAP.items():
            if token == key or token in values:
                expanded.update(values)

    return expanded


def apply_automotive_semantic_rules(item, expanded_tokens, current_score):
    """
    Semantic rerank sırasında otomotiv domain'ine özel boost/penalty uygular.
    """
    rerank_score = current_score

    title = str(item.get("title") or "").lower()
    content = str(item.get("content") or "").lower()
    category = str(item.get("category") or "").lower()
    product_code = str(item.get("product_code") or "").lower()
    metadata = item.get("metadata") or {}

    component = str(metadata.get("component") or "").lower()
    vehicle_type = str(metadata.get("vehicle_type") or "").lower()

    # Garanti kategorisi önemli ama çok agresif boost verilmez.
    if "garanti" in expanded_tokens or "warranty" in expanded_tokens:
        if category == "garanti":
            rerank_score += 0.15

    # Elektrikli araç bataryası özel durumu.
    if "elektrikli" in expanded_tokens and "batarya" in expanded_tokens:
        if "ev-battery" in product_code or "yüksek voltaj" in content or vehicle_type == "electric":
            rerank_score += 1.00

        # Normal 12V aküyü EV batarya sorusunda geriye at.
        if "battery-warranty" in product_code or component == "battery":
            rerank_score -= 0.60

    # Normal araç aküsü garanti sorusu.
    if ("akü" in expanded_tokens or "aku" in expanded_tokens) and (
    "garanti" in expanded_tokens or "warranty" in expanded_tokens
    ):
        # Normal araç aküsü garanti kaydını çok güçlü öne al.
        if (
            "battery-warranty" in product_code
            or component == "battery"
            or "araç aküleri" in content
            or "akü garanti" in title
        ):
            rerank_score += 2.20

        # EV yüksek voltaj batarya kaydı, normal akü sorusunda geri düşmeli.
        if (
            "ev-battery" in product_code
            or "yüksek voltaj" in content
            or vehicle_type == "electric"
        ):
            rerank_score -= 1.40

        # Boya, motor, şanzıman, multimedya gibi başka garanti kayıtları geri düşsün.
        if component and component not in ["battery"]:
            rerank_score -= 0.60

    # Motor garanti sorusu.
    if "motor" in expanded_tokens and ("garanti" in expanded_tokens or "warranty" in expanded_tokens):
        if "eng-warranty" in product_code or component == "engine" or "araç motoru" in content:
            rerank_score += 0.90

        if "trans-warranty" in product_code:
            rerank_score -= 0.40

    # Şanzıman garanti sorusu.
    if ("şanzıman" in expanded_tokens or "sanziman" in expanded_tokens or "transmission" in expanded_tokens) and (
        "garanti" in expanded_tokens or "warranty" in expanded_tokens
    ):
        if "trans-warranty" in product_code or component == "transmission":
            rerank_score += 0.90

    # Elektrik sistemleri garanti sorusu.
    if ("elektrik" in expanded_tokens or "electrical" in expanded_tokens) and (
        "garanti" in expanded_tokens or "warranty" in expanded_tokens
    ):
        if "elec-warranty" in product_code or component == "electrical":
            rerank_score += 0.90

    return rerank_score