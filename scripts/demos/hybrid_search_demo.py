from app.core.hybrid_search_engine import hybrid_text_search


def print_results(query, results):
    print("\n" + "=" * 80)
    print("Sorgu:", query)

    if not results:
        print("Sonuç bulunamadı.")
        return

    for i, item in enumerate(results, start=1):
        print("-" * 80)
        print(f"{i}. Hybrid skor : {item.get('hybrid_score')}")
        print(f"   FAISS skor  : {item.get('faiss_score'):.4f} | rank: {item.get('faiss_rank')}")
        print(f"   BM25 skor   : {item.get('bm25_score'):.4f} | rank: {item.get('bm25_rank')}")
        print(f"   Başlık      : {item.get('title')}")
        print(f"   Ürün kodu   : {item.get('product_code')}")
        print(f"   Tip         : {item.get('item_type')}")
        print(f"   Kategori    : {item.get('category')}")
        print(f"   Görsel      : {item.get('image_path')}")


if __name__ == "__main__":
    queries = [
        "Araç aküsü garanti süresi kaç yıl?",
        "Elektrikli araç batarya garantisi kaç yıl?",
        "Motor garantisi kaç yıl?",
        "Şanzıman garanti şartları nelerdir?",
        "Elektrik sistemleri garanti kapsamında mı?",
        "Turbo arızasında ne olur?",
        "ABS ışığı yanarsa ne anlama gelir?",
    ]

    for query in queries:
        results = hybrid_text_search(
            query=query,
            top_k=5,
            candidate_k=20,
            faiss_weight=0.65,
            bm25_weight=0.35,
        )
        print_results(query, results)