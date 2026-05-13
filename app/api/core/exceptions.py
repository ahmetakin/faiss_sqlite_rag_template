from fastapi import HTTPException


def internal_server_error(exc: Exception):
    """
    API içinde oluşan hataları standart 500 response'a çevirir.
    """
    return HTTPException(
        status_code=500,
        detail=str(exc),
    )