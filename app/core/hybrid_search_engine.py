"""
Hybrid search engine.

Bu modül FAISS semantic search + BM25 keyword search sonuçlarını birleştirir.

Amaç:
- FAISS anlam benzerliğini yakalar.
- BM25 birebir kelime eşleşmesini yakalar.
- İkisi normalize edilip tek final skor altında birleştirilir.
"""

from app.core.bm25_store import BM25Store
from app.core.index_store import FaissIndexStore
from app.core.search import get_embedder
from app.core.db import fetch_item_by_vector_id


def normalize_scores(results, score_key="score", output_key="normalized_score"):
    """
    Skorları 0-1 aralığına normalize eder.

    Neden?
    FAISS score ve BM25 score aynı ölçekte değildir.
    FAISS cosine/IP skoru genelde 0-1 civarıdır.
    BM25 skoru 1, 5, 15 gibi farklı aralıklarda olabilir.
    """
    if not results:
        return []

    scores = [float(item.get(score_key) or 0.0) for item in results]

    min_score = min(scores)
    max_score = max(scores)

    for item in results:
        score = float(item.get(score_key) or 0.0)

        if max_score == min_score:
            item[output_key] = 1.0
        else:
            item[output_key] = (score - min_score) / (max_score - min_score)

    return results


def faiss_search(query: str, top_k: int = 10):
    """
    FAISS semantic search yapar.

    Dönen sonuç:
    [
        {
            "vector_id": ...,
            "faiss_score": ...,
            "faiss_rank": ...
        }
    ]
    """
    embedder = get_embedder()

    query_embedding = embedder.encode_texts(
        [query],
        mode="query"
    )

    index_store = FaissIndexStore()
    index_store.load()

    raw_results = index_store.search(query_embedding, top_k=top_k)

    results = []

    for rank, result in enumerate(raw_results, start=1):
        results.append({
            "vector_id": result["vector_id"],
            "faiss_score": float(result["score"]),
            "faiss_rank": rank,
        })

    return normalize_scores(
        results,
        score_key="faiss_score",
        output_key="faiss_norm"
    )


def bm25_search(query: str, top_k: int = 10):
    """
    BM25 keyword search yapar.

    Dönen sonuç:
    [
        {
            "vector_id": ...,
            "bm25_score": ...,
            "bm25_rank": ...
        }
    ]
    """
    bm25_store = BM25Store()
    bm25_store.load()

    raw_results = bm25_store.search(query, top_k=top_k)

    results = []

    for result in raw_results:
        results.append({
            "vector_id": result["vector_id"],
            "bm25_score": float(result["score"]),
            "bm25_rank": int(result["rank"]),
        })

    return normalize_scores(
        results,
        score_key="bm25_score",
        output_key="bm25_norm"
    )


def merge_hybrid_results(
    faiss_results,
    bm25_results,
    faiss_weight: float = 0.65,
    bm25_weight: float = 0.35,
):
    """
    FAISS ve BM25 sonuçlarını vector_id üzerinden birleştirir.

    Aynı vector_id iki tarafta da geldiyse:
    - faiss_norm + bm25_norm birlikte kullanılır.

    Sadece bir tarafta geldiyse:
    - diğer skor 0 kabul edilir.

    final skor:
    hybrid_score = faiss_norm * faiss_weight + bm25_norm * bm25_weight
    """
    merged = {}

    for item in faiss_results:
        vector_id = item["vector_id"]

        merged[vector_id] = {
            "vector_id": vector_id,
            "faiss_score": item.get("faiss_score", 0.0),
            "faiss_norm": item.get("faiss_norm", 0.0),
            "faiss_rank": item.get("faiss_rank"),
            "bm25_score": 0.0,
            "bm25_norm": 0.0,
            "bm25_rank": None,
        }

    for item in bm25_results:
        vector_id = item["vector_id"]

        if vector_id not in merged:
            merged[vector_id] = {
                "vector_id": vector_id,
                "faiss_score": 0.0,
                "faiss_norm": 0.0,
                "faiss_rank": None,
                "bm25_score": item.get("bm25_score", 0.0),
                "bm25_norm": item.get("bm25_norm", 0.0),
                "bm25_rank": item.get("bm25_rank"),
            }
        else:
            merged[vector_id]["bm25_score"] = item.get("bm25_score", 0.0)
            merged[vector_id]["bm25_norm"] = item.get("bm25_norm", 0.0)
            merged[vector_id]["bm25_rank"] = item.get("bm25_rank")

    final_results = []

    for item in merged.values():
        hybrid_score = (
            item["faiss_norm"] * faiss_weight
            + item["bm25_norm"] * bm25_weight
        )

        item["hybrid_score"] = round(hybrid_score, 4)
        item["match_type"] = "hybrid_faiss_bm25"

        final_results.append(item)

    return sorted(
        final_results,
        key=lambda x: x["hybrid_score"],
        reverse=True
    )


def enrich_with_items(results):
    """
    vector_id sonuçlarını SQLite item bilgisiyle zenginleştirir.
    """
    enriched = []

    for result in results:
        item = fetch_item_by_vector_id(result["vector_id"])

        if not item:
            continue

        item["score"] = result["hybrid_score"]
        item["hybrid_score"] = result["hybrid_score"]
        item["faiss_score"] = result["faiss_score"]
        item["faiss_norm"] = result["faiss_norm"]
        item["faiss_rank"] = result["faiss_rank"]
        item["bm25_score"] = result["bm25_score"]
        item["bm25_norm"] = result["bm25_norm"]
        item["bm25_rank"] = result["bm25_rank"]
        item["match_type"] = result["match_type"]

        enriched.append(item)

    return enriched


def hybrid_text_search(
    query: str,
    top_k: int = 5,
    candidate_k: int = 20,
    faiss_weight: float = 0.65,
    bm25_weight: float = 0.35,
):
    """
    FAISS + BM25 hybrid text search.

    Akış:
    1. FAISS top candidate_k getirir.
    2. BM25 top candidate_k getirir.
    3. Skorlar normalize edilir.
    4. Sonuçlar vector_id üzerinden merge edilir.
    5. SQLite item bilgileri eklenir.
    6. top_k döndürülür.
    """
    faiss_results = faiss_search(query, top_k=candidate_k)
    bm25_results = bm25_search(query, top_k=candidate_k)

    merged = merge_hybrid_results(
        faiss_results=faiss_results,
        bm25_results=bm25_results,
        faiss_weight=faiss_weight,
        bm25_weight=bm25_weight,
    )

    enriched = enrich_with_items(merged)

    return enriched[:top_k]