from app.core.config import ensure_directories
from app.core.db import init_db
from app.services.ingest_service import ingest_all


if __name__ == "__main__":
    ensure_directories()
    init_db()
    ingest_all()