import sys
import json
from io import StringIO
import faiss
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import pandas as pd
import requests
from pathlib import Path
import time


current_file_path = Path(__file__).resolve()
project_root = str(current_file_path.parent.parent.parent)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"Project Root (Buraya bakılıyor): {project_root}")

from app.embedder import QwenVLEmbedder

OUTPUT_DIR = Path("/home/user/ahmet-ai/faiss_sqlite_automotive/data/faiss_tests")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
EMBEDDINGS_FILE = OUTPUT_DIR / "sick_train_embeddings.npy"

#Veri çekelim
res = requests.get("https://raw.githubusercontent.com/brmson/dataset-sts/master/data/sts/sick2014/SICK_train.txt")

df = pd.read_csv(StringIO(res.text),sep='\t')

#ilk 5 satırı yazdıralım verilerin
print(df.head(5))

n_df = df[['sentence_A']].rename(columns={'sentence_A':'sentence'})

#ilk 5 satırı yazdıralım verilerin
print(n_df.head(5))

sentences = n_df['sentence'].tolist()

#kaç adet cümle var ve örnek çıktı
print(len(sentences))
print(sentences[0])


if EMBEDDINGS_FILE.exists():
    print(f"Embedding dosyası mevcut: {EMBEDDINGS_FILE}")
    start_time=time.time()
    embeddings = np.load(EMBEDDINGS_FILE)
    end_time=time.time()
    print(f"Yükleme süresi {end_time - start_time:.2f} saniye")
else:
    print("Embedding dosyası bulunamadı o sebepten model yükleniyor ve oluşturuluyor")

    #embedding modeli tanımladık
    embedder = QwenVLEmbedder()

    start_time = time.time()
    print("Embedding oluşturuluyor...")
    embeddings = embedder.encode_texts(sentences,mode="document").astype("float32")
    end_time = time.time()
    np.save(EMBEDDINGS_FILE, embeddings)
    print(f"İşlem bitti ve kaydedildi. Süre: {end_time - start_time:.2f} saniye.")
    #print(embeddings.shape[1])

print(f"Embedding matris boyutu: {embeddings.shape}")
print("\n--- İlk 5 Embedding (Vektör) ---")
print(embeddings[:5])

embeddings_df = pd.DataFrame({
    'sentence' : sentences,
    'embedding': list(embeddings) #çünkü 2 boturlu 4500x2048
})

print(embeddings_df.head())

#save
embeddings_df.to_parquet(OUTPUT_DIR/'sentences_with_embeddings.parquet', index=False) #yüksek boyutlu vektörleri kayıt için parquet uygun pyarrow ile gelir
# Geri okumak için:
# df_okunan = pd.read_parquet(OUTPUT_DIR/'sentences_with_embeddings.parquet')


#query test
query = "I am happy"
#embedding modeli tanımladık
embedder = QwenVLEmbedder()
print("Query Embedding oluşturuluyor...")
query_embedding = embedder.encode_texts([query],mode="query").astype("float32")
print(query_embedding)
print(type(query_embedding))

ncentroids = 20 #veriyi kaç kümeye böleceğimiz burada alt limit veri sayısı kökü alınarak bulunur üst limit ise %10 geçmemesi önerilier
dim = embeddings.shape[1]

#faisste indexler hiyerarşik olarak ele alınır
index_l2 = faiss.IndexFlatL2(dim) #yol gösterici kaba index 2 nokta arası öklid mesafesi hesaplanır vektörlerde
index_ivf = faiss.IndexIVFFlat(index_l2, dim, ncentroids) #indexlenen verileri clusterlara böler

#index l2 kütüphane kat planı
#inde ivf ise rafların kendisi

index_ivf.train(embeddings) #veriyi gruplara ayıracağı için ivf nin genel dağılımı görmesi gerekir ve 20 centroid belirler
index_ivf.add(embeddings) #eğitim sonrası her vektör merkez noktalar hizasına yerleştirilir

k = 4
D,I = index_ivf.search(query_embedding,k) #sorgu cümlesini index_l2'ye sorar bu 20 clusterdan hangisine yakın ve o clusterdaki cümlelere bakar

print(f"Query {query}")
print("\n Nearest neighbors:")
for i, idx in enumerate(I[0]):
    # Hatalı olan new_dataset yerine embeddings_df kullanıyoruz
    found_sentence = embeddings_df['sentence'].iloc[idx]
    distance = D[0][i]
    print(f"{i+1}. Sentence: {found_sentence} (Distance: {distance:.4f})")

#veya
# Parquet dosyasını geri oku
#loaded_df = pd.read_parquet(OUTPUT_DIR/'sentences_with_embeddings.parquet')
#
#print(f"Query: {query}")
#print("\nNearest neighbors:")
#for i, idx in enumerate(I[0]):
#    # Yüklenen dosyadan cümleyi çek
#    print(f"{i+1}. Sentence: {loaded_df['sentence'].iloc[idx]}")


#burada ivf önemi milyon veride ortaya çıkacaktır.

#ncentroids ile veriler odaya bölünüyorsa nprobe ile en yakın kaç odaya birden bakılsın deriz 
#nprobe = 1 varsayılan
#bu sayıyı arttırırsak doğru sonucu bulma ihtimali artar diyebiliriz 20 yaparsak tüm odalara bakacaktır.
#sonuçların benzer olma sebebi centroidlerin veri kümelerini çok keskin sınırlar ile ayıramamasından verinin az olmasından kaynaklı



index_ivf.nprobe = 5
k = 4
D, I = index_ivf.search(query_embedding, k)

print(f"Query {query}")
print("\n nprobe ile En yakın sonuçlar:")
for i, idx in enumerate(I[0]):
    # Hatalı olan new_dataset yerine embeddings_df kullanıyoruz
    found_sentence = embeddings_df['sentence'].iloc[idx]
    distance = D[0][i]
    print(f"{i+1}. Sentence: {found_sentence} (Distance: {distance:.4f})")