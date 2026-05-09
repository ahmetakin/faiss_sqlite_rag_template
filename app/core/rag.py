from app.services.retrieval_service import hybrid_search
from app.core.llm_client import ask_llm


def format_context(results):
    blocks = []

    for i, item in enumerate(results, start=1):
        block = f"""
[Kaynak {i}]
Eşleşme tipi: {item.get("match_type")}
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


def answer_with_rag(question: str, top_k: int = 5):
    results = hybrid_search(question, top_k=top_k)
    context = format_context(results)

    messages = [
        {
            "role": "system",
            "content": (
                "Sen verilen context'e göre cevap veren bir asistansın. "
                "Sadece context içindeki bilgilere dayanarak cevap ver. "
                "Context'te bilgi yoksa açıkça belirt. "

                "Eğer kullanıcı görsel istiyorsa, image_path bilgisini özellikle belirt. "

                "Eğer kullanıcı öneri veya karşılaştırma sorusu soruyorsa: "
                "- recommendation_score varsa bunu kullan "
                "- en yüksek skoru olanı önce ver "
                "- diğer adayları da listele "
                "- karşılaştırma yaparken rating, yorum sayısı, garanti, fiyat ve performans gibi alanları kullan "
            )
        },
        {
            "role": "user",
            "content": f"""
Kullanıcı sorusu:
{question}

Context:
{context}

Cevap:
""".strip()
        }
    ]

    answer = ask_llm(messages)

    return {
        "question": question,
        "answer": answer,
        "sources": results
    }