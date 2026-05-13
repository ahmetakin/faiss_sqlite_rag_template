from pydantic import BaseModel


class APISettings(BaseModel):
    """
    API ayarlarını merkezi tutar.

    İleride:
    - app name
    - version
    - debug
    - CORS ayarları
    - auth ayarları
    buradan yönetilebilir.
    """

    app_name: str = "FAISS + SQLite Hybrid RAG API"
    app_description: str = "Local FAISS + SQLite + BM25 + RAG template API"
    app_version: str = "0.1.0"
    debug: bool = True


settings = APISettings()