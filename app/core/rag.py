from app.services.retrieval_service import hybrid_search
from app.core.llm_client import ask_llm
from app.core.domain_loader import get_domain_context
from app.core.prompt_loader import load_prompt, load_and_render_prompt


def answer_with_rag(question: str, top_k: int = 5):
    """
    RAG cevap üretim fonksiyonu.

    Akış:
    1. Kullanıcı sorusu retrieval_service'e gider.
    2. Retrieval sonucu aktif domain context formatter ile formatlanır.
    3. System ve user prompt dosyadan okunur.
    4. Prompt içine question/context yerleştirilir.
    5. LLM'e gönderilir.
    """

    results = hybrid_search(question, top_k=top_k)

    context_module = get_domain_context()
    context = context_module.format_context(results)

    system_prompt = load_prompt("rag_system")

    user_prompt = load_and_render_prompt(
        "rag_user_template",
        question=question,
        context=context,
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        }
    ]

    answer = ask_llm(messages)

    return {
        "question": question,
        "answer": answer,
        "sources": results,
    }