"""
Automotive retrieval rules.

Bu dosya otomotiv domain'ine özel retrieval sonrası kuralları tutar.

Buradaki amaç:
- strict family filtreleme
- öneri skoru hesaplama
- domain'e özel ürün kıyaslama mantığı

gibi işleri core/service katmanından ayırmaktır.
"""

from app.domains.automotive.router_rules import STRICT_FAMILY_RULES


def safe_float(value, default=0.0):
    """
    Metadata içinden gelen numeric değerleri güvenli şekilde float'a çevirir.

    Örnek:
    - None gelirse 0.0 döner
    - "4.7" string gelirse 4.7 döner
    - bozuk değer gelirse default döner
    """
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def normalize(value, min_value, max_value):
    """
    Sayısal değeri 0-1 aralığına indirger.

    Örnek:
    - review_count 250 ise ve max 500 ise yaklaşık 0.5 olur
    - warranty_months 36 ise ve max 36 ise 1.0 olur
    """
    value = safe_float(value)

    if max_value <= min_value:
        return 0.0

    return max(0.0, min(1.0, (value - min_value) / (max_value - min_value)))


def apply_strict_family_filter(results, route):
    """
    Kullanıcının istediği ürün ailesi dışındaki kayıtları eler.

    Örnekler:
    - "akü görseli" isterken akü şarj cihazı gelmesin
    - "fren diski" isterken fren balatası gelmesin
    - "debriyaj seti" isterken fren balatası gelmesin
    """
    strict_family = route.get("strict_family")

    if not strict_family:
        return results

    rule = STRICT_FAMILY_RULES.get(strict_family)

    if not rule:
        return results

    include_prefixes = rule.get("include_product_prefixes", [])
    exclude_prefixes = rule.get("exclude_product_prefixes", [])
    exclude_words = rule.get("exclude_words", [])

    filtered = []

    for item in results:
        product_code = str(item.get("product_code") or "").upper()
        title = str(item.get("title") or "").lower()
        content = str(item.get("content") or "").lower()
        category = str(item.get("category") or "").lower()
        part_group = str(item.get("part_group") or "").lower()

        blob = f"{title} {content} {category} {part_group}"

        # Yasaklı product_code prefix'i varsa ele.
        if any(product_code.startswith(prefix.upper()) for prefix in exclude_prefixes):
            continue

        # Yasaklı kelime varsa ele.
        if any(word.lower() in blob for word in exclude_words):
            continue

        # Include prefix tanımlıysa, ürün kodu bu prefixlerden biriyle başlamalı.
        if include_prefixes:
            matched = any(
                product_code.startswith(prefix.upper())
                for prefix in include_prefixes
            )

            if not matched:
                continue

        filtered.append(item)

    return filtered


def calculate_recommendation_score(item):
    """
    Otomotiv ürün öneri skoru hesaplar.

    Şu anki örnek formül:
    - rating_score: kullanıcı puanı
    - review_score: yorum sayısı
    - warranty_score: garanti süresi
    - cca_score: aküler için soğuk marş akımı
    - price_score: düşük fiyat avantajı
    - semantic_score: retrieval güveni

    Not:
    Bu formül domain'e göre değişir.
    Örneğin hukuk dokümanlarında böyle bir skor olmaz.
    Bu yüzden core değil domain katmanında durmalıdır.
    """
    metadata = item.get("metadata") or {}

    rating = safe_float(metadata.get("rating"))
    review_count = safe_float(metadata.get("review_count"))
    warranty_months = safe_float(metadata.get("warranty_months"))
    cold_cranking_amp = safe_float(metadata.get("cold_cranking_amp"))
    price = safe_float(metadata.get("price"))
    semantic_score = safe_float(item.get("score"))

    rating_score = rating / 5.0 if rating > 0 else 0.0
    review_score = normalize(review_count, 0, 500)
    warranty_score = normalize(warranty_months, 0, 36)
    cca_score = normalize(cold_cranking_amp, 0, 700)

    # Fiyat düşükse skor yüksek olsun.
    price_normalized = normalize(price, 0, 5000)
    price_score = 1.0 - price_normalized if price > 0 else 0.0

    recommendation_score = (
        rating_score * 0.35
        + review_score * 0.15
        + warranty_score * 0.20
        + cca_score * 0.15
        + price_score * 0.10
        + semantic_score * 0.05
    )

    item["recommendation_score"] = round(recommendation_score, 4)
    item["rating_score"] = round(rating_score, 4)
    item["review_score"] = round(review_score, 4)
    item["warranty_score"] = round(warranty_score, 4)
    item["cca_score"] = round(cca_score, 4)
    item["price_score"] = round(price_score, 4)
    item["semantic_component"] = round(semantic_score, 4)

    return item

def apply_domain_boosts(item, route):
    """
    Otomotiv domain'ine özel küçük boost kuralları.

    Amaç:
    - Görsel isteniyorsa image kayıtlarını öne almak
    - Marka eşleşiyorsa sonucu güçlendirmek
    - Parça ailesi keywordleri eşleşiyorsa sonucu güçlendirmek

    Bu fonksiyon retrieval sonrası final sıralama için kullanılır.
    """
    score = safe_float(item.get("score"))

    # Kullanıcı görsel istediyse image kayıtlarına ek puan ver.
    if route.get("only_images") and item.get("item_type") == "image":
        score += 0.35

    # Kullanıcı marka belirttiyse, aynı markadaki ürünlere ek puan ver.
    if route.get("brand") and item.get("brand"):
        if item["brand"].upper() == route["brand"].upper():
            score += 0.25

    text_blob = " ".join([
        str(item.get("title") or ""),
        str(item.get("category") or ""),
        str(item.get("product_code") or ""),
        str(item.get("content") or ""),
        str(item.get("brand") or ""),
        str(item.get("part_group") or ""),
    ]).lower()

    keyword_hits = 0

    # Sorgudan gelen parça keywordleri kayıtta geçiyorsa ek puan ver.
    for kw in route.get("part_keywords") or []:
        if kw.lower() in text_blob:
            keyword_hits += 1

    score += keyword_hits * 0.12

    item["final_score"] = round(score, 4)
    return item

def calculate_value_score(item):
    """
    Fiyat/performans skoru hesaplar.

    Mantık:
    - rating yüksekse iyi
    - yorum sayısı yüksekse iyi
    - garanti yüksekse iyi
    - fiyat düşükse iyi
    - CCA varsa performans göstergesi olarak eklenir
    """
    metadata = item.get("metadata") or {}

    rating = safe_float(metadata.get("rating"))
    review_count = safe_float(metadata.get("review_count"))
    warranty_months = safe_float(metadata.get("warranty_months"))
    cold_cranking_amp = safe_float(metadata.get("cold_cranking_amp"))
    price = safe_float(metadata.get("price"))

    rating_score = rating / 5.0 if rating > 0 else 0.0
    review_score = normalize(review_count, 0, 500)
    warranty_score = normalize(warranty_months, 0, 36)
    cca_score = normalize(cold_cranking_amp, 0, 700)

    price_normalized = normalize(price, 0, 5000)
    price_score = 1.0 - price_normalized if price > 0 else 0.0

    value_score = (
        rating_score * 0.30
        + review_score * 0.15
        + warranty_score * 0.15
        + cca_score * 0.10
        + price_score * 0.30
    )

    item["value_score"] = round(value_score, 4)
    item["rating_score"] = round(rating_score, 4)
    item["review_score"] = round(review_score, 4)
    item["warranty_score"] = round(warranty_score, 4)
    item["cca_score"] = round(cca_score, 4)
    item["price_score"] = round(price_score, 4)

    return item


def sort_recommendation_results(results, route):
    """
    Recommendation sonuçlarını query mode'a göre sıralar.

    Mode:
    - cheapest  -> fiyat düşükten yükseğe
    - expensive -> fiyat yüksekten düşüğe
    - value     -> fiyat/performans skoru
    - best      -> recommendation_score
    """
    mode = route.get("recommendation_mode") or "best"

    for item in results:
        calculate_recommendation_score(item)
        calculate_value_score(item)

    def get_price(item):
        metadata = item.get("metadata") or {}
        price = safe_float(metadata.get("price"), default=999999999.0)
        return price if price > 0 else 999999999.0

    if mode == "cheapest":
        results = sorted(results, key=get_price)

    elif mode == "expensive":
        results = sorted(results, key=get_price, reverse=True)

    elif mode == "value":
        results = sorted(
            results,
            key=lambda x: x.get("value_score", 0),
            reverse=True
        )

    else:
        results = sorted(
            results,
            key=lambda x: x.get("recommendation_score", 0),
            reverse=True
        )

    for item in results:
        item["recommendation_mode"] = mode

    return results

def calculate_value_score(item):
    """
    Fiyat/performans skoru hesaplar.

    Amaç:
    - fiyat düşükse avantaj
    - rating yüksekse avantaj
    - yorum sayısı yüksekse avantaj
    - garanti yüksekse avantaj
    - CCA gibi performans metriği varsa avantaj
    """
    metadata = item.get("metadata") or {}

    rating = safe_float(metadata.get("rating"))
    review_count = safe_float(metadata.get("review_count"))
    warranty_months = safe_float(metadata.get("warranty_months"))
    cold_cranking_amp = safe_float(metadata.get("cold_cranking_amp"))
    price = safe_float(metadata.get("price"))

    rating_score = rating / 5.0 if rating > 0 else 0.0
    review_score = normalize(review_count, 0, 500)
    warranty_score = normalize(warranty_months, 0, 36)
    cca_score = normalize(cold_cranking_amp, 0, 700)

    price_normalized = normalize(price, 0, 5000)
    price_score = 1.0 - price_normalized if price > 0 else 0.0

    value_score = (
        rating_score * 0.30
        + review_score * 0.15
        + warranty_score * 0.15
        + cca_score * 0.10
        + price_score * 0.30
    )

    item["value_score"] = round(value_score, 4)
    item["rating_score"] = round(rating_score, 4)
    item["review_score"] = round(review_score, 4)
    item["warranty_score"] = round(warranty_score, 4)
    item["cca_score"] = round(cca_score, 4)
    item["price_score"] = round(price_score, 4)

    return item


def sort_recommendation_results(results, route):
    """
    Recommendation sonuçlarını sorgu moduna göre sıralar.

    Modes:
    - cheapest  : fiyat düşükten yükseğe
    - expensive : fiyat yüksekten düşüğe
    - value     : value_score yüksekten düşüğe
    - best      : recommendation_score yüksekten düşüğe
    """
    mode = route.get("recommendation_mode") or "best"

    for item in results:
        calculate_recommendation_score(item)
        calculate_value_score(item)

    def get_price(item):
        metadata = item.get("metadata") or {}
        price = safe_float(metadata.get("price"), default=999999999.0)
        return price if price > 0 else 999999999.0

    if mode == "cheapest":
        results = sorted(results, key=get_price)

    elif mode == "expensive":
        results = sorted(results, key=get_price, reverse=True)

    elif mode == "value":
        results = sorted(
            results,
            key=lambda x: x.get("value_score", 0),
            reverse=True
        )

    else:
        results = sorted(
            results,
            key=lambda x: x.get("recommendation_score", 0),
            reverse=True
        )

    for item in results:
        item["recommendation_mode"] = mode

    return results