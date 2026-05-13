from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.core.settings import settings
from app.api.routers import health, search, ask, admin


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
)


# Static dosyalar
app.mount(
    "/static",
    StaticFiles(directory="app/api/static"),
    name="static",
)


# Template sistemi
templates = Jinja2Templates(directory="app/api/templates")


# Router kayıtları
app.include_router(health.router)
app.include_router(search.router)
app.include_router(ask.router)
app.include_router(admin.router)


@app.get("/", tags=["Frontend"])
def home():
    """
    Şimdilik basit API karşılama endpoint'i.

    İleride HTML template render edilebilir.
    """
    return {
        "message": "FAISS + SQLite Hybrid RAG API çalışıyor.",
        "docs": "/docs",
        "health": "/health",
    }