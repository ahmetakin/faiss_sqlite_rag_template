import json
from pathlib import Path
import sys

current_file_path = Path(__file__).resolve()
project_root = str(current_file_path.parent.parent)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"Project Root (Buraya bakılıyor): {project_root}")

import faiss
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

from app.embedder import QwenVLEmbedder


OUTPUT_DIR = Path("/home/user/ahmet-ai/faiss_sqlite_automotive/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


SAMPLE_TEXTS = [
    "Elektrikli araç batarya garanti süresi 8 yıl veya 160.000 km olabilir.",
    "Fren balatası düzenli kontrol edilmelidir.",
    "Motor yağı değişimi aracın bakım periyoduna göre yapılır.",
    "Lastik hava basıncı yakıt tüketimini etkiler.",
    "Araç aküsü zayıflarsa marş basma problemi oluşabilir.",
    "Elektrikli araçlarda batarya sağlığı menzili doğrudan etkiler.",
    "Kış lastiği soğuk havalarda yol tutuşunu artırır.",
    "Fren hidroliği zamanla özelliğini kaybedebilir.",
    "Şanzıman yağı belirli kilometrelerde değiştirilmelidir.",
    "Balata aşınması fren mesafesini uzatabilir.",
]


def prepare_ivf_visualization_data(texts, ncentroids=2):
    if len(texts) < ncentroids:
        raise ValueError("Metin sayısı ncentroids değerinden küçük olamaz.")

    embedder = QwenVLEmbedder()

    print("Embedding oluşturuluyor...")
    embeddings = embedder.encode_texts(texts, mode="document").astype("float32")

    dim = embeddings.shape[1]

    quantizer = faiss.IndexFlatIP(dim)

    index = faiss.IndexIVFFlat(
        quantizer,
        dim,
        ncentroids,
        faiss.METRIC_INNER_PRODUCT,
    )

    print("Index train ediliyor...")
    index.train(embeddings)

    print("Index'e ekleniyor...")
    index.add(embeddings)

    _, cluster_ids = index.quantizer.search(embeddings, 1)
    cluster_ids = cluster_ids.flatten()

    centroids = np.vstack([
        index.quantizer.reconstruct(i)
        for i in range(ncentroids)
    ]).astype("float32")

    pca = PCA(n_components=2)
    all_vectors = np.vstack([embeddings, centroids])
    reduced_all = pca.fit_transform(all_vectors)

    reduced_embeddings = reduced_all[:len(embeddings)]
    reduced_centroids = reduced_all[len(embeddings):]

    return {
        "texts": texts,
        "embeddings": embeddings,
        "centroids": centroids,
        "cluster_ids": cluster_ids,
        "reduced_embeddings": reduced_embeddings,
        "reduced_centroids": reduced_centroids,
        "index": index,
        "pca": pca,
        "ncentroids": ncentroids,
    }


def plot_ivf_clusters_from_data(data, output_file):
    texts = data["texts"]
    cluster_ids = data["cluster_ids"]
    reduced_embeddings = data["reduced_embeddings"]
    reduced_centroids = data["reduced_centroids"]
    ncentroids = data["ncentroids"]

    plt.figure(figsize=(10, 8))

    for cluster_id in range(ncentroids):
        points = reduced_embeddings[cluster_ids == cluster_id]

        if len(points) > 0:
            plt.scatter(
                points[:, 0],
                points[:, 1],
                label=f"Cluster {cluster_id}",
            )

    plt.scatter(
        reduced_centroids[:, 0],
        reduced_centroids[:, 1],
        marker="X",
        s=250,
        edgecolors="black",
        linewidths=1.5,
        label="Centroids",
    )

    for i, text in enumerate(texts):
        plt.annotate(
            str(i),
            (reduced_embeddings[i, 0], reduced_embeddings[i, 1]),
            fontsize=9,
        )

    for i, centroid in enumerate(reduced_centroids):
        plt.annotate(
            f"C{i}",
            (centroid[0], centroid[1]),
            fontsize=12,
            fontweight="bold",
        )

    plt.title("FAISS IVF Cluster Visualization")
    plt.xlabel("PCA-1")
    plt.ylabel("PCA-2")
    plt.legend()
    plt.grid(True)

    plt.savefig(output_file, dpi=200, bbox_inches="tight")
    plt.close()

    print(f"Cluster PNG kaydedildi: {output_file}")


def plot_ivf_voronoi_clusters_from_data(data, output_file):
    texts = data["texts"]
    cluster_ids = data["cluster_ids"]
    reduced_embeddings = data["reduced_embeddings"]
    reduced_centroids = data["reduced_centroids"]
    ncentroids = data["ncentroids"]

    all_2d = np.vstack([reduced_embeddings, reduced_centroids])

    x_min, x_max = all_2d[:, 0].min() - 0.2, all_2d[:, 0].max() + 0.2
    y_min, y_max = all_2d[:, 1].min() - 0.2, all_2d[:, 1].max() + 0.2

    xx, yy = np.meshgrid(
        np.linspace(x_min, x_max, 500),
        np.linspace(y_min, y_max, 500),
    )

    grid_points = np.c_[xx.ravel(), yy.ravel()]

    distances = np.linalg.norm(
        grid_points[:, None, :] - reduced_centroids[None, :, :],
        axis=2,
    )

    voronoi_regions = np.argmin(distances, axis=1).reshape(xx.shape)

    plt.figure(figsize=(11, 9))

    plt.contourf(
        xx,
        yy,
        voronoi_regions,
        alpha=0.25,
        levels=np.arange(ncentroids + 1) - 0.5,
    )

    for cluster_id in range(ncentroids):
        points = reduced_embeddings[cluster_ids == cluster_id]

        if len(points) > 0:
            plt.scatter(
                points[:, 0],
                points[:, 1],
                label=f"Cluster {cluster_id}",
            )

    plt.scatter(
        reduced_centroids[:, 0],
        reduced_centroids[:, 1],
        marker="X",
        s=300,
        edgecolors="black",
        linewidths=1.5,
        label="Centroids",
    )

    for i, text in enumerate(texts):
        plt.annotate(
            str(i),
            (reduced_embeddings[i, 0], reduced_embeddings[i, 1]),
            fontsize=9,
        )

    for i, centroid in enumerate(reduced_centroids):
        plt.annotate(
            f"C{i}",
            (centroid[0], centroid[1]),
            fontsize=12,
            fontweight="bold",
        )

    plt.title("FAISS IVF Clusters - PCA 2D Voronoi Visualization")
    plt.xlabel("PCA-1")
    plt.ylabel("PCA-2")
    plt.legend()
    plt.grid(True)

    plt.savefig(output_file, dpi=200, bbox_inches="tight")
    plt.close()

    print(f"Voronoi PNG kaydedildi: {output_file}")


def search_demo(data, query, k=4):
    embedder = QwenVLEmbedder()

    query_embedding = embedder.encode_texts(
        [query],
        mode="query",
    ).astype("float32")

    index = data["index"]
    texts = data["texts"]

    index.nprobe = min(2, data["ncentroids"])

    D, I = index.search(query_embedding, k)

    print(f"\nQuery: {query}")
    print("\nEn yakın sonuçlar:")

    for rank, idx in enumerate(I[0], start=1):
        score = D[0][rank - 1]
        print(f"{rank}. Skor: {score:.4f}")
        print(f"   Cümle: {texts[idx]}")
        print()


def print_cluster_distribution(data):
    texts = data["texts"]
    cluster_ids = data["cluster_ids"]
    ncentroids = data["ncentroids"]

    print("\nCluster dağılımı:")

    for cluster_id in range(ncentroids):
        print(f"\nCluster {cluster_id}:")

        for i, cid in enumerate(cluster_ids):
            if cid == cluster_id:
                print(f"  [{i}] {texts[i]}")


def save_outputs(data):
    faiss.write_index(
        data["index"],
        str(OUTPUT_DIR / "demo_ivf.index"),
    )

    with open(OUTPUT_DIR / "demo_texts.json", "w", encoding="utf-8") as f:
        json.dump(data["texts"], f, ensure_ascii=False, indent=2)

    print(f"\nIndex kaydedildi: {OUTPUT_DIR / 'demo_ivf.index'}")
    print(f"Metinler kaydedildi: {OUTPUT_DIR / 'demo_texts.json'}")


def main():
    ncentroids = 2

    data = prepare_ivf_visualization_data(
        texts=SAMPLE_TEXTS,
        ncentroids=ncentroids,
    )

    plot_ivf_clusters_from_data(
        data,
        output_file=OUTPUT_DIR / "clusters.png",
    )

    plot_ivf_voronoi_clusters_from_data(
        data,
        output_file=OUTPUT_DIR / "voronoi_clusters.png",
    )

    print_cluster_distribution(data)

    search_demo(
        data,
        query="Elektrikli araç batarya garantisi ne kadar?",
        k=4,
    )

    save_outputs(data)


if __name__ == "__main__":
    main()