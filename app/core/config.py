from pathlib import Path


# app/core/config.py -> app/core -> app -> proje kökü
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Aktif domain
ACTIVE_DOMAIN = "automotive"

# Ana klasörler
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
CONFIGS_DIR = PROJECT_ROOT / "configs"

# Domain veri klasörleri
RAW_DATA_DIR = DATA_DIR / "raw" / ACTIVE_DOMAIN
IMAGE_DIR = DATA_DIR / "images" / ACTIVE_DOMAIN
SQLITE_DIR = DATA_DIR / "sqlite"
INDEX_DIR = DATA_DIR / "indexes"
OUTPUT_DIR = DATA_DIR / "outputs"

# Dosya path'leri
DB_PATH = SQLITE_DIR / f"{ACTIVE_DOMAIN}.db"
RAW_DOCUMENTS_PATH = RAW_DATA_DIR / "raw_documents.json"

FAISS_INDEX_PATH = INDEX_DIR / f"{ACTIVE_DOMAIN}.faiss"
FAISS_META_PATH = INDEX_DIR / f"{ACTIVE_DOMAIN}_meta.json"

# Embedding model path
MODEL_PATH = MODELS_DIR / "embedding" / "Qwen3-VL-Embedding-2B"

# Retrieval ayarları
TOP_K = 5

# Image ayarları
IMAGE_MAX_SIZE = 448


def ensure_directories():
    """
    Gerekli klasörler yoksa oluşturur.
    Script'lerde init aşamasında çağrılabilir.
    """
    for path in [
        DATA_DIR,
        RAW_DATA_DIR,
        IMAGE_DIR,
        SQLITE_DIR,
        INDEX_DIR,
        OUTPUT_DIR,
        MODELS_DIR,
        CONFIGS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)