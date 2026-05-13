from fastapi import APIRouter


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get("/info")
def admin_info():
    """
    İleride admin işlemleri için kullanılacak alan.

    Örnek:
    - index durumu
    - aktif domain
    - veri sayıları
    - son ingestion zamanı
    """
    return {
        "message": "Admin endpoint hazır.",
    }