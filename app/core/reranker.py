"""
Reranker module.

Bu modül retrieval sonrası gelen adayları yeniden sıralar.

Neden gerekli?
- FAISS semantic benzerlik yakalar.
- BM25 keyword eşleşmesi yakalar.
- Domain rules bazı boostlar verir.
- Ama son aday listesinde hâlâ alakasız kayıtlar olabilir.

Reranker'ın görevi:
Retriever'ın getirdiği adayları query'ye göre yeniden puanlamak ve daha iyi sıralamaktır.

Bu ilk versiyon lightweight rule-based reranker'dır.
İleride buraya Cross Encoder veya LLM reranker eklenebilir.
"""

import re


def normalize_text(text: str) -> str:
    """
    Metni karşılaştırma için normalize eder.

    - Küçük harfe çevirir
    - None gelirse boş string döndürür
    """
    if text is None:
        return ""

    return str(text).lower()


def tokenize(text: str):
    """
    Basit tokenizer.

    Türkçe karakterleri korur.
    En az 2 karakterlik tokenları alır.
    """
    text = normalize_text(text)

    tokens = re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ0-9\-]+", text)

    return [
        token.strip()
        for token in tokens
        if len(token.strip()) >= 2
    ]


def build_item_text(item: dict) -> str:
    """
    Bir retrieval sonucunu tek metin bloğuna çevirir.

    Reranker bu metin üzerinden query ile eşleşme arar.
    """
    metadata = item.get("metadata") or {}

    metadata_text = " ".join(
        f"{key}: {value}"
        for key, value in metadata.items()
    )

    parts = [
        item.get("title"),
        item.get("category"),
        item.get("product_code"),
        item.get("content"),
        item.get("brand"),
        item.get("part_group"),
        metadata_text,
    ]

    return " ".join(
        str(part)
        for part in parts
        if part
    )


def calculate_overlap_score(query: str, item: dict) -> float:
    """
    Query tokenları ile item text tokenları arasındaki basit overlap skorunu hesaplar.

    Örnek:
    query: "akü garanti süresi"
    item: "Akü Garanti Şartları ..."

    Ortak token sayısı arttıkça skor artar.
    """
    query_tokens = set(tokenize(query))
    item_tokens = set(tokenize(build_item_text(item)))

    if not query_tokens or not item_tokens:
        return 0.0

    overlap = query_tokens.intersection(item_tokens)

    return len(overlap) / len(query_tokens)


def calculate_field_match_score(query: str, item: dict) -> float:
    """
    Alan bazlı eşleşme skoru verir.

    Başlık ve ürün kodu eşleşmeleri daha değerli kabul edilir.
    Çünkü bunlar genelde kaydın ana anlamını taşır.
    """
    q = normalize_text(query)

    title = normalize_text(item.get("title"))
    product_code = normalize_text(item.get("product_code"))
    category = normalize_text(item.get("category"))
    content = normalize_text(item.get("content"))
    brand = normalize_text(item.get("brand"))
    part_group = normalize_text(item.get("part_group"))

    score = 0.0

    query_tokens = tokenize(query)

    for token in query_tokens:
        if token in title:
            score += 0.30

        if token in product_code:
            score += 0.25

        if token in category:
            score += 0.15

        if token in brand:
            score += 0.15

        if token in part_group:
            score += 0.15

        if token in content:
            score += 0.08

    # Phrase match varsa ekstra puan.
    # Örnek: "motor yağı" doğrudan title/content içinde geçiyorsa.
    if q and q in title:
        score += 0.50

    if q and q in content:
        score += 0.30

    return score


def get_base_retrieval_score(item: dict) -> float:
    """
    Mevcut retrieval skorunu güvenli şekilde alır.

    Öncelik sırası:
    1. semantic_rerank_score
    2. hybrid_score
    3. final_score
    4. recommendation_score
    5. score
    """
    for key in [
        "semantic_rerank_score",
        "hybrid_score",
        "final_score",
        "recommendation_score",
        "score",
    ]:
        value = item.get(key)

        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue

    return 0.0


def rerank_results(query: str, results: list[dict], top_k: int | None = None):
    """
    Retrieval sonuçlarını yeniden sıralar.

    Final skor:
    - base retrieval score
    - token overlap
    - field match

    Not:
    Bu skor gerçek cross-encoder değildir.
    Hafif, hızlı, debug edilebilir bir rerank katmanıdır.
    """
    reranked = []

    for item in results:
        base_score = get_base_retrieval_score(item)
        overlap_score = calculate_overlap_score(query, item)
        field_score = calculate_field_match_score(query, item)

        rerank_score = (
            base_score * 0.70
            + overlap_score * 0.20
            + field_score * 0.10
        )

        # Kaydı kopyalıyoruz ki orijinal dictionary beklenmedik şekilde bozulmasın.
        new_item = dict(item)

        new_item["rerank_base_score"] = round(base_score, 4)
        new_item["rerank_overlap_score"] = round(overlap_score, 4)
        new_item["rerank_field_score"] = round(field_score, 4)
        new_item["rerank_score"] = round(rerank_score, 4)

        reranked.append(new_item)

    reranked = sorted(
        reranked,
        key=lambda x: x.get("rerank_score", 0),
        reverse=True,
    )

    if top_k is not None:
        return reranked[:top_k]

    return reranked