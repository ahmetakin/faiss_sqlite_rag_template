from app.core.config import ensure_directories, DB_PATH
from app.core.db import init_db


if __name__ == "__main__":
    ensure_directories()
    init_db()

    print("SQLite veritabanı hazır.")
    print(f"DB path: {DB_PATH}")