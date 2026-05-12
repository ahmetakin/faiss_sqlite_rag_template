"""
BM25 store.

Bu modül klasik keyword tabanlı arama için BM25 index oluşturur.

FAISS ne yapar?
- Anlam/semantic benzerlik yakalar.

BM25 ne yapar?
- Kelime eşleşmesini güçlü yakalar.
- Ürün kodu, teknik terim, kısa keyword ve birebir geçen ifadelerde çok faydalıdır.

Bu yüzden RAG sistemlerinde genelde:
FAISS + BM25 birlikte kullanılır.
"""

import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from app.core.config import BM25_INDEX_PATH


class BM25Store:
    """
    BM25 index yönetimi.

    JSON olarak şunları saklarız:
    - vector_ids
    - documents
    - tokenized_documents

    Not:
    BM25Okapi objesi doğrudan JSON'a yazılamaz.
    Bu yüzden load sırasında tokenized_documents üzerinden yeniden kuruyoruz.
    """

    def __init__(self):
        self.vector_ids = []
        self.documents = []
        self.tokenized_documents = []
        self.index = None

    def tokenize(self, text: str):
        """
        Metni BM25 için token listesine çevirir.

        Basit tokenizer kullanıyoruz:
        - lowercase
        - harf/rakam tokenları
        - Türkçe karakterleri korur

        İleride domain bazlı tokenizer yapılabilir.
        """
        text = text.lower()

        tokens = re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ0-9\-]+", text)

        return [
            token.strip()
            for token in tokens
            if len(token.strip()) >= 2
        ]

    def build(self, documents: list[str], vector_ids: list[int]):
        """
        BM25 index oluşturur.

        Args:
            documents:
                Aranacak metinler.
            vector_ids:
                Her dokümanın SQLite/FAISS tarafındaki vector_id değeri.
        """
        if len(documents) != len(vector_ids):
            raise ValueError("documents ve vector_ids uzunluğu aynı olmalı.")

        self.documents = documents
        self.vector_ids = [int(x) for x in vector_ids]
        self.tokenized_documents = [
            self.tokenize(doc)
            for doc in documents
        ]

        self.index = BM25Okapi(self.tokenized_documents)

    def save(self):
        """
        BM25 index bilgilerini JSON olarak kaydeder.

        BM25Okapi nesnesi serialize edilmez.
        Load sırasında tokenized_documents ile yeniden oluşturulur.
        """
        BM25_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "vector_ids": self.vector_ids,
            "documents": self.documents,
            "tokenized_documents": self.tokenized_documents,
        }

        with open(BM25_INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def load(self):
        """
        JSON'dan BM25 index'i yükler.
        """
        path = Path(BM25_INDEX_PATH)

        if not path.exists():
            raise FileNotFoundError(f"BM25 index bulunamadı: {path}")

        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        self.vector_ids = payload["vector_ids"]
        self.documents = payload["documents"]
        self.tokenized_documents = payload["tokenized_documents"]

        self.index = BM25Okapi(self.tokenized_documents)

    def search(self, query: str, top_k: int = 5):
        """
        BM25 keyword search yapar.

        Returns:
            [
                {
                    "vector_id": int,
                    "score": float,
                    "rank": int
                }
            ]
        """
        if self.index is None:
            raise RuntimeError("BM25 index yüklenmedi veya oluşturulmadı.")

        query_tokens = self.tokenize(query)

        if not query_tokens:
            return []

        scores = self.index.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda idx: scores[idx],
            reverse=True
        )

        results = []

        for rank, idx in enumerate(ranked_indices[:top_k], start=1):
            score = float(scores[idx])

            # Skoru 0 olan kayıtlar gerçek eşleşme değildir.
            if score <= 0:
                continue

            results.append({
                "vector_id": int(self.vector_ids[idx]),
                "score": score,
                "rank": rank,
            })

        return results