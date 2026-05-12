import json
from pathlib import Path

import numpy as np

from app.core.config import IMAGE_DIR, RAW_DOCUMENTS_PATH, ensure_directories
from app.core.db import clear_db, insert_item
from app.core.embedder import QwenVLEmbedder
from app.core.index_store import FaissIndexStore

from app.core.bm25_store import BM25Store

def build_text_for_embedding(item: dict) -> str:
    parts = [
        f"Başlık: {item.get('title', '')}",
        f"Tip: {item.get('type', '')}",
        f"Kategori: {item.get('category', '')}",
        f"Ürün kodu: {item.get('product_code', '')}",
        f"Kaynak: {item.get('source', '')}",
        f"İçerik: {item.get('content', '')}"
    ]

    metadata = item.get("metadata") or {}

    if metadata:
        metadata_text = " ".join([f"{k}: {v}" for k, v in metadata.items()])
        parts.append(f"Metadata: {metadata_text}")

    return "\n".join(parts)


def normalize_image_path_for_db(relative_path: str | None):
    """
    DB içinde saklanacak image_path.
    Eski raw_documents içinde images/x.jpg gelirse automotive/x.jpg gibi değil,
    okunabilir şekilde images/automotive/x.jpg olarak normalize ediyoruz.
    """
    if not relative_path:
        return None

    filename = Path(relative_path).name
    return f"images/automotive/{filename}"


def resolve_image_path(relative_path: str | None):
    """
    Fiziksel dosya yolu:
    data/images/automotive/<filename>
    """
    if not relative_path:
        return None

    filename = Path(relative_path).name
    return IMAGE_DIR / filename


def add_sqlite_item(vector_id: int, vector_type: str, item: dict):
    insert_item(
        vector_id=vector_id,
        item_id=item["item_id"],
        vector_type=vector_type,
        item_type=item["type"],
        title=item["title"],
        category=item.get("category"),
        product_code=item.get("product_code"),
        source=item.get("source"),
        content=item.get("content"),
        image_path=normalize_image_path_for_db(item.get("image_path")),
        metadata=item.get("metadata") or {}
    )


def ingest_all():
    ensure_directories()

    if not RAW_DOCUMENTS_PATH.exists():
        raise FileNotFoundError(f"Raw documents bulunamadı: {RAW_DOCUMENTS_PATH}")

    with open(RAW_DOCUMENTS_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    clear_db()

    embedder = QwenVLEmbedder()

    all_embeddings = []
    vector_ids = []

    bm25_documents = []
    bm25_vector_ids = []

    vector_id_counter = 1

    for item in items:
        item_type = item["type"]

        # Her kayıt için text embedding üret.
        text_for_embedding = build_text_for_embedding(item)

        text_embedding = embedder.encode_texts(
            [text_for_embedding],
            mode="document"
        )[0]

        vector_id = vector_id_counter
        vector_id_counter += 1

        add_sqlite_item(
            vector_id=vector_id,
            vector_type="text",
            item=item
        )

        all_embeddings.append(text_embedding)
        vector_ids.append(vector_id)

        # BM25 sadece metinsel temsil üzerinden çalışır.
        # Image item'larda bile ürün kodu, marka, açıklama gibi text alanları BM25'e eklenir.
        bm25_documents.append(text_for_embedding)
        bm25_vector_ids.append(vector_id)

        print(
            f"Eklendi: vector_id={vector_id} | vector_type=text | "
            f"{item['item_id']} | {item['title']}"
        )

        # Image kayıtlarında ayrıca gerçek image embedding üret.
        if item_type == "image":
            image_path = resolve_image_path(item.get("image_path"))

            if image_path is None or not image_path.exists():
                print(f"Görsel bulunamadı, image vector atlandı: {image_path}")
                continue

            image_embedding = embedder.encode_images([str(image_path)])[0]

            vector_id = vector_id_counter
            vector_id_counter += 1

            add_sqlite_item(
                vector_id=vector_id,
                vector_type="image",
                item=item
            )

            all_embeddings.append(image_embedding)
            vector_ids.append(vector_id)

            print(
                f"Eklendi: vector_id={vector_id} | vector_type=image | "
                f"{item['item_id']} | {item['title']}"
            )

    if not all_embeddings:
        raise RuntimeError("Hiç embedding üretilemedi.")

    embeddings_matrix = np.vstack(all_embeddings).astype("float32")

    index_store = FaissIndexStore()
    index_store.build(embeddings_matrix, vector_ids)
    index_store.save()

    # BM25 keyword index oluşturulur.
    # FAISS semantic arama yaparken, BM25 birebir kelime eşleşmelerini yakalar.
    bm25_store = BM25Store()
    bm25_store.build(
        documents=bm25_documents,
        vector_ids=bm25_vector_ids
    )
    bm25_store.save()

    print("\nIngestion tamamlandı.")
    print("Toplam FAISS vektör sayısı:", len(vector_ids))
    print("Toplam BM25 doküman sayısı:", len(bm25_vector_ids))
    print("Embedding shape:", embeddings_matrix.shape)