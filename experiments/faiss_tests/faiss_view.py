import sys
import os
from pathlib import Path

current_file_path = Path(__file__).resolve()

project_root = str(current_file_path.parent.parent)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"Project Root (Buraya bakılıyor): {project_root}")

import faiss
import json
import numpy as np
import matplotlib.pyplot as plt
from app.embedder import QwenVLEmbedder
import pandas as pd


JSON_PATH = "/home/user/ahmet-ai/faiss_sqlite_automotive/data/raw_documents.json" 


def load_json_dataset(json_path: str) -> pd.DataFrame:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.json_normalize(data)

    return df


df = load_json_dataset(JSON_PATH)

print("Toplam kayıt:", len(df))
#print("Sütunlar:")
#print(df.columns.tolist())

#print("\nİlk 5 kayıt:")
#print(df.head())


# Category listesi
categories = sorted(df["category"].dropna().unique().tolist())
print("\nCategory listesi:")
print(categories)
# Source listesi
sources = sorted(df["source"].dropna().unique().tolist())
print("\nSource listesi:")
print(sources)


# Type listesi
#types = sorted(df["type"].dropna().unique().tolist())
#print("\nType listesi:")
#print(types)


# Category dağılımı
print("\nCategory dağılımı:")
print(df["category"].value_counts())


# Source dağılımı
print("\nSource dağılımı:")
print(df["source"].value_counts())


## Type dağılımı
#print("\nType dağılımı:")
#print(df["type"].value_counts())
## Sadece temel kolonları göster
#basic_cols = [
#    "item_id",
#    "type",
#    "title",
#    "category",
#    "product_code",
#    "source",
#    "content",
#    "image_path"
#]
#df_basic = df[basic_cols]
#print("\nTemel tablo:")
#print(df_basic.head(10))
# Metadata kolonlarını ayrıca görmek için
#metadata_cols = [col for col in df.columns if col.startswith("metadata.")]
#print("\nMetadata kolonları:")
#print(metadata_cols)
#
#print("\nMetadata dahil örnek tablo:")
#print(df[["item_id", "category", "source"] + metadata_cols].head())

