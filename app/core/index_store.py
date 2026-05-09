import json

import faiss
import numpy as np

from app.core.config import FAISS_INDEX_PATH, FAISS_META_PATH, ensure_directories


class FaissIndexStore:
    """
    FAISS index yönetimi.

    Şu an IndexFlatIP kullanıyoruz.
    Embedding'ler L2 normalize edildiği için:
        Inner Product ≈ Cosine Similarity
    """

    def __init__(self):
        self.index = None
        self.vector_ids: list[int] = []

    def build(self, embeddings: np.ndarray, vector_ids: list[int]):
        if embeddings is None or len(embeddings) == 0:
            raise ValueError("FAISS index oluşturmak için embedding boş olamaz.")

        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype("float32")

        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)

        self.vector_ids = [int(x) for x in vector_ids]

    def save(self):
        ensure_directories()

        if self.index is None:
            raise RuntimeError("Kaydedilecek FAISS index yok.")

        faiss.write_index(self.index, str(FAISS_INDEX_PATH))

        with open(FAISS_META_PATH, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "vector_ids": self.vector_ids,
                    "index_type": "IndexFlatIP",
                    "metric": "cosine_similarity_via_normalized_inner_product",
                },
                f,
                ensure_ascii=False,
                indent=2
            )

    def load(self):
        if not FAISS_INDEX_PATH.exists():
            raise FileNotFoundError(f"FAISS index bulunamadı: {FAISS_INDEX_PATH}")

        if not FAISS_META_PATH.exists():
            raise FileNotFoundError(f"FAISS meta dosyası bulunamadı: {FAISS_META_PATH}")

        self.index = faiss.read_index(str(FAISS_INDEX_PATH))

        with open(FAISS_META_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)

        self.vector_ids = [int(x) for x in meta["vector_ids"]]

    def search(self, query_embedding: np.ndarray, top_k: int = 5):
        if self.index is None:
            raise RuntimeError("FAISS index yüklenmedi.")

        if query_embedding.dtype != np.float32:
            query_embedding = query_embedding.astype("float32")

        scores, indices = self.index.search(query_embedding, top_k)

        results = []

        for score, faiss_idx in zip(scores[0], indices[0]):
            if faiss_idx == -1:
                continue

            vector_id = self.vector_ids[faiss_idx]

            results.append({
                "vector_id": int(vector_id),
                "score": float(score)
            })

        return results