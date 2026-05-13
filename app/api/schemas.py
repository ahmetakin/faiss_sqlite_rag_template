from pydantic import BaseModel, Field
from typing import Any


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[dict[str, Any]]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResponse(BaseModel):
    query: str
    sources: list[dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    service: str