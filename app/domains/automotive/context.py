"""
Automotive context formatter.

Bu dosya retrieval sonuçlarını LLM'e verilecek context formatına çevirir.

Neden domain tarafında?
Çünkü otomotiv domain'inde:
- ürün kodu
- görsel yolu
- rating
- garanti
- CCA
- fiyat
- recommendation_score

gibi alanlar önemlidir.

Başka bir domain'de bu alanlar farklı olacaktır.
"""


def format_context(results):
    """
    Retrieval sonuçlarını LLM'in anlayacağı metinsel context bloklarına çevirir.

    Her kayıt [Kaynak X] formatında yazılır.
    Böylece LLM cevap üretirken hangi kaynaklardan beslendiğini daha net görür.
    """
    blocks = []

    for i, item in enumerate(results, start=1):
        block = f"""
[Kaynak {i}]
Eşleşme tipi: {item.get("match_type")}
Seçilen tool: {item.get("selected_tool")}
Intent: {item.get("intent")}
Strict family: {item.get("strict_family")}

Tip: {item.get("item_type")}
Başlık: {item.get("title")}
Kategori: {item.get("category")}
Ürün kodu: {item.get("product_code")}
Kaynak: {item.get("source")}
Görsel: {item.get("image_path")}
İçerik: {item.get("content")}
Metadata: {item.get("metadata")}

Skor: {item.get("score")}
Final skor: {item.get("final_score")}
Semantic rerank skoru: {item.get("semantic_rerank_score")}
Semantic eşleşen kelimeler: {item.get("semantic_matched_keywords")}

Öneri skoru: {item.get("recommendation_score")}
Rating skoru: {item.get("rating_score")}
Yorum skoru: {item.get("review_score")}
Garanti skoru: {item.get("warranty_score")}
CCA skoru: {item.get("cca_score")}
Fiyat skoru: {item.get("price_score")}
Semantic bileşen: {item.get("semantic_component")}
""".strip()

        blocks.append(block)

    return "\n\n".join(blocks)