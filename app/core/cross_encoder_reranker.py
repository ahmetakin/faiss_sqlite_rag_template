"""
Cross Encoder Reranker Adapter.

Bu modül retrieval sonrası gelen adayları gerçek bir cross-encoder model ile yeniden sıralamak için kullanılır.

Bi-encoder / FAISS ne yapar?
- Query ve document ayrı ayrı embedding'e çevrilir.
- Sonra vector similarity hesaplanır.
- Çok hızlıdır.

Cross-encoder ne yapar?
- Query + document çiftini birlikte modele verir.
- Model bu çift gerçekten alakalı mı diye skor üretir.
- Daha yavaştır ama genelde daha doğru sıralama yapar.

Bu yüzden üretim sistemlerinde tipik akış:
1. FAISS/BM25 ile top 20-50 aday getir.
2. Cross-encoder ile bu adayları yeniden sırala.
3. En iyi top 5 kaydı LLM'e context olarak ver.
"""

import os

os.environ["CUDA_VISIBLE_DEVICES"] = "2,3"

from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.core.config import CROSS_ENCODER_MODEL_PATH


def build_cross_encoder_text(item: dict) -> str:
    """
    Retrieval sonucunu cross-encoder'ın okuyacağı metne çevirir.

    Burada önemli alanları tek text haline getiriyoruz:
    - title
    - category
    - product_code
    - content
    - brand
    - part_group
    - metadata
    """
    metadata = item.get("metadata") or {}

    metadata_text = " ".join(
        f"{key}: {value}"
        for key, value in metadata.items()
    )

    parts = [
        f"Başlık: {item.get('title') or ''}",
        f"Kategori: {item.get('category') or ''}",
        f"Ürün kodu: {item.get('product_code') or ''}",
        f"Marka: {item.get('brand') or ''}",
        f"Parça grubu: {item.get('part_group') or ''}",
        f"İçerik: {item.get('content') or ''}",
        f"Metadata: {metadata_text}",
    ]

    return "\n".join(parts)


@lru_cache(maxsize=1)
def get_cross_encoder_model():
    """
    Cross encoder modelini lazy-load eder.

    lru_cache sayesinde model sadece bir kere yüklenir.
    API çalışırken her istekte tekrar model yüklenmez.
    """
    return CrossEncoder(CROSS_ENCODER_MODEL_PATH)


def cross_encoder_rerank_results(
    query: str,
    results: list[dict],
    top_k: int | None = None,
):
    """
    Sonuçları cross-encoder ile yeniden sıralar.

    Args:
        query:
            Kullanıcı sorgusu.
        results:
            Retrieval'dan gelen aday kayıtlar.
        top_k:
            İstenirse sadece ilk top_k sonuç döndürülür.

    Returns:
        Cross encoder skoruna göre sıralanmış sonuç listesi.
    """
    if not results:
        return []

    model = get_cross_encoder_model()

    # Cross encoder input formatı:
    # [(query, document_text), (query, document_text), ...]
    pairs = [
        (
            query,
            build_cross_encoder_text(item),
        )
        for item in results
    ]

    scores = model.predict(pairs)

    reranked = []

    for item, score in zip(results, scores):
        new_item = dict(item)

        # Cross encoder skorunu ayrıca saklıyoruz.
        # Böylece debug/eval/API tarafında görülebilir.
        new_item["cross_encoder_score"] = float(score)
        new_item["rerank_score"] = round(float(score), 4)
        new_item["rerank_type"] = "cross_encoder"

        reranked.append(new_item)

    reranked = sorted(
        reranked,
        key=lambda x: x.get("cross_encoder_score", 0),
        reverse=True,
    )

    if top_k is not None:
        return reranked[:top_k]

    return reranked