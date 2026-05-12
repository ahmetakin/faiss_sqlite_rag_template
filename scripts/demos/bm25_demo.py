from app.core.bm25_store import BM25Store
from app.core.db import fetch_item_by_vector_id


def print_results(query, results):
    print("\n" + "=" * 80)
    print("Sorgu:", query)
    print("BM25 Sonuçları:")

    if not results:
        print("Sonuç bulunamadı.")
        return

    for i, result in enumerate(results, start=1):
        item = fetch_item_by_vector_id(result["vector_id"])

        print("-" * 80)
        print(f"{i}. BM25 skor : {result['score']:.4f}")
        print(f"   Rank      : {result['rank']}")
        print(f"   Vector ID : {result['vector_id']}")

        if item:
            print(f"   Başlık    : {item.get('title')}")
            print(f"   Ürün kodu : {item.get('product_code')}")
            print(f"   Tip       : {item.get('item_type')}")
            print(f"   Kategori  : {item.get('category')}")
            print(f"   Görsel    : {item.get('image_path')}")


if __name__ == "__main__":
    store = BM25Store()
    store.load()

    queries = [
        "Araç aküsü garanti süresi kaç yıl?",
        "Motor garantisi kaç yıl?",
        "Şanzıman garanti şartları nelerdir?",
        "Elektrik sistemleri garanti kapsamında mı?",
        "Turbo arızasında ne olur?",
        "ABS ışığı yanarsa ne anlama gelir?",
        "BOSCH akü görselini getir",
        "ENGINE-OIL-AKN ürün kodlu parçayı açıkla",
    ]

    for query in queries:
        results = store.search(query, top_k=5)
        print_results(query, results)