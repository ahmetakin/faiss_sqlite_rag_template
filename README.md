# FAISS + SQLite RAG Template

Bu proje, yerel embedding modeli, FAISS vektör arama ve SQLite metadata katmanı kullanarak çalışan basit ama genişletilebilir bir RAG iskeletidir.

İlk örnek domain olarak otomotiv verileri kullanılmıştır. Ama yapı farklı domain’lere taşınabilecek şekilde core, services ve domain katmanlarına ayrılmıştır.

## Amaç

Bu iskeletin amacı:

- Text ve görsel kayıtlarını embedding’e çevirmek
- FAISS ile semantic search yapmak
- SQLite üzerinde metadata, ürün kodu ve filtreleme işlemlerini tutmak
- llama.cpp üzerinden çalışan lokal LLM’e context vererek cevap üretmek
- Product-code search, image search, recommendation ve semantic search gibi farklı arama tiplerini tek yapı altında toplamak

## Klasör Yapısı

```text
app/
  core/
    config.py
    db.py
    embedder.py
    index_store.py
    llm_client.py
    rag.py
    router.py
    search.py

  services/
    ingest_service.py
    retrieval_service.py

  domains/
    automotive/

data/
  raw/automotive/raw_documents.json
  images/automotive/
  sqlite/
  indexes/
  outputs/

models/
  embedding/Qwen3-VL-Embedding-2B/

scripts/
  db/init_db.py
  ingest/ingest_data.py
  demos/
  eval/eval_questions.py

experiments/
  faiss_tests/