from fastapi import APIRouter

from app.api.core.settings import settings
from app.api.schemas.health import HealthResponse


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("", response_model=HealthResponse)
def health_check():
    """
    Servisin ayakta olup olmadığını kontrol eder.
    """
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }