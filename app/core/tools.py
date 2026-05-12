"""
Generic tool helpers.

Bu dosya domain bağımsız ortak yardımcı fonksiyonları tutar.
Gerçek tool implementasyonları domain klasörlerinde durur.

Örnek:
- app/domains/automotive/tools.py
"""


def deduplicate_results(results):
    """
    Aynı item_id değerine sahip tekrar kayıtları temizler.

    Neden gerekli?
    Aynı ürün/veri hem text vector hem image vector olarak FAISS'e eklenebilir.
    Bu yüzden aynı item_id birden fazla kez dönebilir.
    """
    seen = set()
    unique = []

    for item in results:
        key = item.get("item_id")

        if key in seen:
            continue

        seen.add(key)
        unique.append(item)

    return unique