from app.core.config import TOP_K
from app.core.db import fetch_item_by_vector_id, search_items_by_product_code
from app.core.embedder import QwenVLEmbedder
from app.core.index_store import FaissIndexStore


_embedder_instance = None


def get_embedder():#EMBEDDİNG MODEL YÜKLENİYOR
    """
    Embedder singleton.
    Aynı process içinde modelin her sorguda tekrar yüklenmesini engeller.
    """
    global _embedder_instance

    if _embedder_instance is None:
        _embedder_instance = QwenVLEmbedder()

    return _embedder_instance


def dedupe_results(results):
    """
    Aynı item_id için text ve image vector ayrı ayrı dönebilir.
    Kullanıcıya aynı ürünü iki kez göstermemek için dedupe yapılır.
    """
    seen = set()
    deduped = []

    for item in results:
        key = item.get("item_id")

        if key in seen:
            continue

        seen.add(key)
        deduped.append(item)

    return deduped


def search_by_text(
    query: str,
    top_k: int = TOP_K,
    use_exact_search: bool = False
):
    final_results = []

    if use_exact_search:
        exact_results = search_items_by_product_code(query) #ürün kodundan arama yapılır

        if exact_results:
            return exact_results[:top_k]

    embedder = get_embedder()

    query_embedding = embedder.encode_texts(#querynin embedding'i çıkarılır
        [query],
        mode="query"
    )

    index_store = FaissIndexStore()
    index_store.load()

    raw_results = index_store.search(#vektor db den aratılır
        query_embedding=query_embedding,
        top_k=top_k * 3
    )

    for result in raw_results:
        item = fetch_item_by_vector_id(result["vector_id"])

        if item:
            item["score"] = result["score"]
            item["match_type"] = "semantic_faiss"
            final_results.append(item)

    final_results = dedupe_results(final_results)

    return final_results[:top_k]


def search_by_image(
    image_path: str,
    top_k: int = TOP_K
):
    embedder = get_embedder()

    query_embedding = embedder.encode_images([image_path])#resmin embedding'i çıkarılır

    index_store = FaissIndexStore()
    index_store.load()

    raw_results = index_store.search(#faiss te benzerlik araması yapılır
        query_embedding=query_embedding,
        top_k=top_k * 3
    )

    final_results = []

    for result in raw_results:
        item = fetch_item_by_vector_id(result["vector_id"])

        if item:
            item["score"] = result["score"]
            item["match_type"] = "image_faiss"
            final_results.append(item)

    final_results = dedupe_results(final_results)

    return final_results[:top_k]